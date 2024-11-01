from flask import Flask, request, jsonify
from flask_cors import CORS
from langchain_chroma import Chroma
from langchain.prompts import ChatPromptTemplate
from langchain_huggingface import HuggingFaceEmbeddings
from uuid import uuid4
from langchain_core.documents import Document
import warnings
import requests
from bs4 import BeautifulSoup
from autoscraper import AutoScraper
import pandas as pd
import ollama
# from scrape_web import scrape_products

warnings.filterwarnings("ignore")

embeddings = HuggingFaceEmbeddings()

vector_store = Chroma(
    collection_name="productdb",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

SIMILARITY_THRESHOLD = 0.2

def addDocument(content, link, image, rating, review_count, price, availability):
    product = Document(
        page_content=content,
        metadata={
            "link": link,
            "image": image,
            "rating": rating,
            "review_count": review_count,
            "price": price,
            "availability": availability
        }
    )
    vector_store.add_documents([product])
    print(f"Document added: {content}, {link}, {rating}")

def findItems(query: str, numItems: int):
    results_with_scores = vector_store.similarity_search_with_score(
        query=query,
        k=numItems
    )

    for result, score in results_with_scores:
        print(f"Found: {result.page_content}, Score: {score}")  # Debugging line

    relevant_results = [
        result for result, score in results_with_scores if score >= SIMILARITY_THRESHOLD
    ]

    # if not relevant_results:
    #     print("Results not found, scraping the web. Please wait")
    #     scraped_products = scrape_products(query)
    #     if scraped_products:
    #         for product in scraped_products:
    #             print("Adding the result into the database.")
    #             addDocument(
    #                 content=product['title'],
    #                 link=product['link'],
    #                 image=product['image'],
    #                 rating=product['rating'],
    #                 review_count=product['review_count'] if product['review_count'] else "No reviews",
    #                 price=product['price'],
    #                 availability=product['availability']
    #             )
    #         relevant_results = findItems(query, numItems)
    #     print("Webscraping is done!")
    # print(f"Total results found: {len(results_with_scores)}")
    # print(f"Relevant results after filtering: {len(relevant_results)}")

    return relevant_results


def add_all_products_to_db(dataframe):
    for index, row in dataframe.iterrows():
        content = row['product_name']
        link = row['product_link']
        image = row['img_link']
        rating = row['rating']
        review_count = row['rating_count']
        price = row['discounted_price']
        availability = "Available"
        addDocument(content, link, image, rating, review_count, price, availability)
    print("All products added and saved to Chroma DB.")

def add_all_products_to_db_v2(dataframe):
    for index, row in dataframe.iterrows():
        content = row['product_name']
        link = row['product_url']
        image = row['image']
        rating = row['overall_rating']
        review_count = row['product_rating']
        price = row['discounted_price'] if pd.notnull(row['discounted_price']) else row['retail_price']
        availability = "Available"

        rating = rating if pd.notnull(rating) else "No rating available"
        review_count = review_count if pd.notnull(review_count) else "No reviews"

        addDocument(content, link, image, rating, review_count, price, availability)
        print(f"Product '{content}' added successfully.")
    print("All products added and saved to Chroma DB.")

if __name__ == "__main__":
    query = input("Enter your query: ")
    response = ollama.chat(model='phi3-recom', messages=[{
        'role': 'user',
        'content': f"""<|user|>
Here's a product I would like to buy. Your task is to generate similar product recommendations to this product in comma separated values only and nothing else. Just answer in csv. Here's the product :  {query}<|end|>
<|assistant|>""",
    }])
    print(response['message']['content'])
    resp = response['message']['content']
    for item in resp.split(", "):
        results = findItems(item, 5)
        print(f"Results ({item}): \n\n")
        if results:
            for i in results:
                print(f"Name: {i.page_content}\nPrice: {i.metadata['price']}\n\n")
        else:
            print("No results found.")
