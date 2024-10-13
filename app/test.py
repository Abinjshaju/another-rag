import fitz
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import CharacterTextSplitter
from dotenv import load_dotenv
import os
from openai import OpenAI
import weaviate
from weaviate.classes.query import MetadataQuery
from weaviate.classes.init import AdditionalConfig, Timeout
from weaviate.classes.config import Configure, Property, DataType
from weaviate.util import generate_uuid5

PDF_PATH = "files/file.pdf"

# Load environment variables from a .env file
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
weaviate_url = os.getenv("WEAVIATE_URL")

def extract_text_from_pdf(pdf_path):
    # Open the PDF document
    doc = fitz.open(pdf_path)
    text = ""
    # Iterate over each page and extract text
    for page in doc:
        text += page.get_text("text")
    return text

def vectorize_text(text_chunk, api_key):
    # Create an instance of OpenAIEmbeddings with the provided API key
    embedding_model = OpenAIEmbeddings(api_key=api_key)
    # Vectorize the text chunk
    embedding = embedding_model.embed_query(text_chunk)
    return embedding

def setup_weaviate():
    # Connect to Weaviate using the gRPC port and additional config
    client = weaviate.connect_to_local(
        port=8080,
        grpc_port=50051,
        additional_config=AdditionalConfig(
            timeout=Timeout(init=30, query=60, insert=120)  # Set timeout configurations
        ),
        headers={
            "X-OpenAI-Api-Key": os.getenv("OPENAI_API_KEY")  # Use dotenv to load API key
        }
    )

    collection_name = "PdfEmbedding"

    try:
        # Check if the collection already exists
        collection = client.collections.get(collection_name)

        if not collection:
            # Create the collection (class) if it does not exist
            client.collections.create(
                name=collection_name,
                vectorizer_config=Configure.Vectorizer.text2vec_openai(),  # Using text2vec_openai
                properties=[
                    Property(name="text", data_type=DataType.TEXT),  # "text" field
                    Property(name="id", data_type=DataType.TEXT),    # "id" field
                ]
            )
            print(f"Collection '{collection_name}' created successfully.")
        else:
            print(f"Collection '{collection_name}' already exists.")

        return client, collection_name

    except weaviate.exceptions.WeaviateException as e:
        print(f"An error occurred while setting up Weaviate: {e}")
        raise

def insert_embeddings_to_weaviate(client, class_name, text):
    try:
        # Get the collection (class) from Weaviate
        collection = client.collections.get(class_name)

        # Use the collection's batch mode for dynamic object insertion
        with collection.batch.dynamic() as batch:
            batch.add_object(
                properties={"text": text},
                uuid=generate_uuid5(text)  # Assign a unique identifier
            )
        print(f"Inserted text chunk into Weaviate.")
    except Exception as e:
        print(f"Error inserting data into Weaviate: {e}")

def query_weaviate(client, class_name, query_text, api_key):
    try:
        # Access the collection object
        collection = client.collections.get(class_name)

        # Perform the near_text query
        response = collection.query.near_text(
            query=query_text,
            limit=5,  # Limit number of results
            return_metadata=MetadataQuery(distance=True)  # Requesting distance in metadata
        )

        context_text = ""
        for item in response.objects:
            context_text += item.properties['text'] + " "  # Access 'text' property of the objects

        if context_text:
            # Call the OpenAI API to generate an answer based on the context
            answer = generate_answer_with_openai(context_text, query_text, api_key)
            print(f"Generated Answer: {answer}")
        else:
            print("No relevant text found to generate an answer.")

    except Exception as e:
        print(f"Error querying Weaviate: {e}")

def generate_answer_with_openai(context_text, query_text, api_key):
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    # Call OpenAI API to generate a response
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that answers questions based on the given context."},
            {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {query_text}"}
        ],
        max_tokens=150  # Define max tokens for response
    )
    return response.choices[0].message.content.strip()

def main():
    pdf_text = extract_text_from_pdf(PDF_PATH)
    print("PDF text extracted successfully.")

    # Split the extracted text into chunks
    splitter = CharacterTextSplitter(chunk_size=384, chunk_overlap=30)
    text_chunks = splitter.split_text(pdf_text)

    client = None  # Initialize the client here

    try:
        # Setup Weaviate client and collection
        client, class_name = setup_weaviate()
        print("Weaviate setup successfully.")

        # Insert each chunk into Weaviate
        for chunk in text_chunks:
            insert_embeddings_to_weaviate(client, class_name, chunk)
        print("Embeddings inserted into Weaviate successfully.")

        # Query Weaviate for a summary
        query_weaviate(client, class_name, "summarize the document", api_key)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Close the Weaviate client connection
        if client:
            client.close()
            print("Weaviate client connection closed.")

if __name__ == "__main__":
    main()
