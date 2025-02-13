import openai
import os

openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Please set your OPENAI_API_KEY environment variable.")

def get_embedding(text, model="text-embedding-ada-002"):
    client = openai.OpenAI()
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding

def main():
    openai.api_key = openai_api_key
    user_input = input("Enter text to generate embedding: ")
    
    embedding = get_embedding(user_input)
    print("\nGenerated Embedding:")
    print(embedding)

if __name__ == "__main__":
    main()
