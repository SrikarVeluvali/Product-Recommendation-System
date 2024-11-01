from flask import Flask, jsonify, request
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import urllib
import certifi
import ssl


HEADERS = ({'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0', 'Accept-Language':'en-US, en;q=0.5','Accept-Encoding': 'gzip, deflate, br',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Referer': 'https://www.google.com/'})
# Helper Functions
# Function to extract Product Title
def get_title(product, source):
    
    if source == "amazon":
        try:
            # Outer Tag Object
            title = product.find("span", attrs={'class':'a-size-medium a-color-base a-text-normal'})
            
            # Inner NavigatableString Object
            title_value = title.text

            # Title as a string value
            title_string = title_value.strip()

        except AttributeError:
            title_string = ""

        return title_string
    
    elif source == "flipkart":
        try:
            
            title_string = product.find("a", attrs={'class':'wjcEIp'}).get('title')
            
        except AttributeError:
            title_string = ""

        return title_string

# Function to extract Product Price
def get_price(product, source):

    if source == "amazon":
        try:
            price = product.find("span", attrs={'class':'a-price-whole'}).text

        except AttributeError:

            price = ""

        return "Rs."+price
    

    elif source == "flipkart":
        try:
            price = product.find("div", attrs={'class':'Nx9bqj'}).text

        except AttributeError:

            price = "Rs."

        return price

# Function to extract Product Rating
def get_rating(product, source):

    if source == "amazon":
        try:
            rating = product.find("span", attrs={'class':'a-icon-alt'}).string.strip()
        
        except AttributeError:
            try:
                rating = product.find("i", attrs={'class':'a-icon a-icon-star a-star-4-5'}).string.strip()
            except:
                rating = ""	

        return rating
    

    elif source == "flipkart":
        try:
            rating = product.find("div", attrs={'class':'XQDdHH'}).text.strip()
        
        except AttributeError:
            rating = ""	

        return rating

# Function to extract Number of User Reviews
def get_review_count(product, source):
        
    if source == "amazon":
        try:
            review_count = product.find("span", attrs={'class':'a-size-base s-underline-text'}).string.strip()

        except AttributeError:
            review_count = ""	

        return review_count
    

    elif source == "flipkart":
        try:
            review_count = product.find("span", attrs={'class':'Wphh3N'}).get_text(strip=True).replace('(', '').replace(')', '')

        except AttributeError:
            review_count = ""	

        return review_count

def get_image(product, source):
        
    if source == "amazon":
        try:
            image = product.find("img", attrs={'class':'s-image'}).get('src')

        except AttributeError:
            image = ""

        return image
    

    elif source == "flipkart":
        try:
            image = product.find("img", attrs={'class':'DByuf4'}).get('src')

        except AttributeError:
            image = ""

        return image

def get_link(product, source):
    
    if source == "amazon":
        try:
            raw_link = product.find("a", attrs={'class': 'a-link-normal s-underline-text s-underline-link-text s-link-style a-text-normal'})
            link = "https://www.amazon.in" + raw_link.get('href')

        except AttributeError:
            link = ""

        return link
    
    elif source == "flipkart":
        try:
            raw_link = product.find("a", attrs={'class': 'VJA3rP'})
            link = "https://www.flipkart.com" + raw_link.get('href')

        except AttributeError:
            link = ""

        return link

async def fetch_page(session, url):
    # Use the certifi package to get the proper SSL certificate bundle
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    try:
        async with session.get(url, ssl=ssl_context) as response:
            if response.status == 200:
                return await response.text()
            else:
                print(f"Failed to fetch page: {response.status}")
                return None
    except Exception as e:
        print(f"Error fetching page: {e}")
        return None
    
    
# Scrape Amazon
async def scrape_amazon(session, search_query):
    base_url = "https://www.amazon.in/s?k={}"
    formatted_query = urllib.parse.quote_plus(search_query)
    formatted_url = base_url.format(formatted_query)

    webpage = await fetch_page(session, formatted_url)
    if not webpage:
        return []

    soup = BeautifulSoup(webpage, "html.parser")
    product_list = []
    for product in soup.findAll("div",attrs={'data-component-type':'s-search-result'}):
        
        product_data = {
                'source':"amazon",
                'title': get_title(product,"amazon"),
                'link': get_link(product,"amazon"),
                'image': get_image(product,"amazon"),
                'rating': get_rating(product,"amazon"),
                'review_count': get_review_count(product,"amazon"),
                'price': get_price(product,"amazon")
                # 'availability': get_availability(product,"amazon")
            }
        
        if product_data['title']:
            product_list.append(product_data)
        
    return product_list

# Scrape Flipkart (you will need to adjust this based on Flipkart's page structure)
async def scrape_flipkart(session, search_query):
    base_url = "https://www.flipkart.com/search?q={}"
    formatted_query = urllib.parse.quote_plus(search_query)
    formatted_url = base_url.format(formatted_query)

    webpage = await fetch_page(session, formatted_url)
    if not webpage:
        return []

    soup = BeautifulSoup(webpage, "html.parser")
    product_list = []
    for product in soup.findAll("div",attrs={'class':'slAVV4'}):
    
        product_data = {
                'source':"flipkart",
                'title': get_title(product,"flipkart"),
                'link': get_link(product,"flipkart"),
                'image': get_image(product,"flipkart"),
                'rating': get_rating(product,"flipkart"),
                'review_count': get_review_count(product,"flipkart"),
                'price': get_price(product,"flipkart"),
                # 'availability': get_availability(product,"flipkart")
            }
        
        if product_data['title']:
            product_list.append(product_data)

    return product_list

# Asynchronous scraping of both Amazon and Flipkart
async def scrape_amazon_and_flipkart(search_query):
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        amazon_task = scrape_amazon(session, search_query)
        flipkart_task = scrape_flipkart(session, search_query)

        # Run both tasks concurrently
        amazon_products, flipkart_products = await asyncio.gather(amazon_task, flipkart_task)
        return amazon_products + flipkart_products

async def scrape(query):
    # Scrape both Amazon and Flipkart asynchronously
    products = await scrape_amazon_and_flipkart(query)

    return products

if __name__ == '__main__':
    # Run the scrape function asynchronously using asyncio.run
    result = asyncio.run(scrape("Pokemon"))
    print(f"{len(result)} Results found")
    for i in result:
        print("Source:", i["source"])
        print("Title:", i["title"])
        print("Price:", i["price"])
        print()
    
