import os
import torch # <-- ADD THIS LINE
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
import ollama

# Force PyTorch to use the CPU to prevent MPS memory crashes
torch.device("cpu") # <-- ADD THIS LINE

# 1. CONFIGURATION
# This path matches the exact folder structure on your Mac
PDF_FOLDER = "/Users/rayagewealth/Documents/SOLVITY DOCS/RAG DOCS" 
DB_FOLDER = "solvity_chroma_db"

def build_database():
    print("📚 Reading PDFs and building the database (this takes a minute)...")
    documents = []
    
    # Load all PDFs in the folder
    for file in os.listdir(PDF_FOLDER):
        if file.endswith(".pdf"):
            print(f"Reading: {file}")
            loader = PyPDFLoader(os.path.join(PDF_FOLDER, file))
            documents.extend(loader.load())

    # Split the text into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(documents)

    # Create the database
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_db = Chroma.from_documents(chunks, embeddings, persist_directory=DB_FOLDER)
    print("✅ Database built successfully!")
    return vector_db

def ask_solvity(question, vector_db):
    print(f"\nUser Question: {question}")
    
    # 1. Search the database for the most relevant paragraphs
    print("🔍 Searching legal documents...")
    docs = vector_db.similarity_search(question, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])

    # 2. Feed the context to the AI
    prompt = f"""
    You are the Solvity AI Legal Assistant for gender-based violence survivors in South Africa.
    Use ONLY the following context from South African law and referral lists to answer the user's question. 
    If the answer is not in the context, say "I don't have that information in my documents."
    If the user asks for help, give them the specific phone numbers from the documents.
    
    Context:
    {context}
    
    User Question: {question}
    """
    
    print("🧠 Solvity AI is reading the documents...")
    response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': prompt},
    ])
    
    print("\n--- 🚨 SOLVITY AI RESPONSE ---")
    print(response['message']['content'])
    print("------------------------------\n")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # If the database doesn't exist, build it. If it does, load it.
    if not os.path.exists(DB_FOLDER):
        db = build_database()
    else:
        print("⏩ Loading existing database...")
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        db = Chroma(persist_directory=DB_FOLDER, embedding_function=embeddings)

    # ASK TEST QUESTIONS
    ask_solvity("What is the phone number for the GBV Command Centre?", db)
    ask_solvity("If my partner locks me in the house, is that domestic violence?", db)
    