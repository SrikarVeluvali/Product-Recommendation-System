import ollama

query = input("Enter your query: ")
response = ollama.chat(model='hf.co/srikar-v05/Llama3-Medical-Chat-GGUF', messages=[{
        'role': 'user',
        'content': f"""{query}""",
    }])
print(response['message']['content'])