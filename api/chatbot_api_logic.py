import os
from dotenv import load_dotenv

# Langchain imports
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA


def initialize_rag_pipeline(pdf_path: str):
    """
    Initializes the RAG pipeline (vector store, LLM, chain) for a given PDF.
    """
    load_dotenv()

    print(f"Initializing RAG pipeline for PDF: {pdf_path}")

    # 1. Create Vector Store from PDF
    loaders = [PyPDFLoader(pdf_path)]
    index = VectorstoreIndexCreator(
        embedding=HuggingFaceEmbeddings(model_name="all-MiniLM-L12-v2"),
        text_splitter=RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100),
    ).from_loaders(loaders)
    vectorstore = index.vectorstore

    # 2. Setup LLM with Google Gemini
    # Make sure GOOGLE_API_KEY is set in your .env file or environment variables
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not found. Please set it in your environment.")

    model = "gemini-pro"
    llm = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        convert_system_message_to_human=True
    )

    # 3. Create QA Chain
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )

    return chain


# Global variable to hold the initialized RAG chain
# This simple approach holds one PDF context at a time.
rag_pipeline = None
current_pdf_path = None


def load_and_initialize_chatbot(pdf_file_path: str):
    """
    Loads and initializes the chatbot for a specific PDF.
    This function will be called by the API.
    """
    global rag_pipeline, current_pdf_path
    # Reload the pipeline if it's not initialized or if a different PDF is requested
    if rag_pipeline is None or current_pdf_path != pdf_file_path:
        print(f"Loading/reloading RAG pipeline for {pdf_file_path}...")
        rag_pipeline = initialize_rag_pipeline(pdf_file_path)
        current_pdf_path = pdf_file_path
        print("RAG pipeline initialized.")
    else:
        print(f"RAG pipeline for {pdf_file_path} already loaded.")
    return rag_pipeline


def get_chatbot_response(question: str) -> str:
    """
    Gets a response from the initialized chatbot.
    Assumes `rag_pipeline` is already loaded.
    """
    global rag_pipeline
    if rag_pipeline is None:
        raise ValueError(
            "Chatbot not initialized. Please load a PDF first via the /load_pdf/ endpoint.")

    # The chain expects a dictionary with a "query" key
    result = rag_pipeline({"query": question})

    # The result is a dictionary containing the 'result'
    return result.get("result", "No answer found.")
