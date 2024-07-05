from groq import Groq
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import chromadb
import os


def contextualize(query, chat_history):
    #contextualizes the query wrt to chat_history and returns it
    client = Groq(api_key = "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")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role" : "system",
                "content" : """Given a chat history and the latest user question which might reference context in the chat history, formulate a standalone question  which can be understood without the chat history. Do NOT answer the question, just reformulate it if needed and otherwise return it as is. Return just the reformulated question, without any notes. If given chat history is empty, simply return the query."""
            },

            {
                "role" : "user",
                "content" : "Chat history is : " + chat_history + "\n\n" + "Latest user question is : " + query
            }
        ],
        model="llama3-70b-8192"
    )

    return chat_completion.choices[0].message.content

def generate_response(con_query, sim_docs):
    #calls groq and creates a response, using query and similar docs
    client = Groq(api_key = "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")
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role" : "system",
                "content" : """You are a very helpful assistant. Given a question, generate the appropriate answer of the question in the given context only. If no relevant answer is found return that the answer does not exists in the given context."""
            },

            {
                "role" : "user",
                "content" : "Question :" + con_query + "\n\n Context : " + sim_docs['documents'][0][0]
            }
        ],
        model="llama3-70b-8192"
    )

    return chat_completion.choices[0].message.content

def generate_chat_history(old_chat_history, query, response):
    #why not simply append the question and answer to old chat history
    temp = old_chat_history + "\n\nQuestion :" + query + "\n Answer : " + response
    return temp

def process_files(pdf):
    pdf_content = extract_text(pdf)
    chunks = create_chunks(pdf_content)
    embeddings = create_store_embeddings(chunks)

def sim_search(query):
    #loads collection from local
    client = chromadb.PersistentClient(path = os.getcwd())
    collection = client.get_collection(name = "temp_collection")

    model = SentenceTransformer("all-mpnet-base-v2")
    query_embed = model.encode([query])

    sim_docs = collection.query(
        query_embeddings = query_embed,
        n_results=1
    )

    return sim_docs

def extract_text(pdf):
    text = ""
    reader = PyPDF2.PdfReader(pdf)
    for page in reader.pages:
        text += page.extract_text() + "\n\n"
    return text

def create_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 100)
    chunks = text_splitter.split_text(text)
    return chunks

def create_store_embeddings(chunks):
    model = SentenceTransformer("all-mpnet-base-v2")
    embeds = model.encode(chunks)

    client = chromadb.PersistentClient(path = os.getcwd())
    #reset collection
    collection = client.get_or_create_collection(name = "temp_collection")
    client.delete_collection(name = "temp_collection")
    collection = client.create_collection("temp_collection")

    collection.add(
        documents=chunks,
        embeddings=embeds,
        ids = ["id" + str(i) for i in range(len(chunks))]
    )

