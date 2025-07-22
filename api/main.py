

# Import your chatbot logic wrapper
# IMPORTANT: Ensure this file (chatbot_api_logic.py) exists in the same directory
# and contains the functions 'load_and_initialize_chatbot' and 'get_chatbot_response'
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel

from chatbot_api_logic import load_and_initialize_chatbot, get_chatbot_response

load_dotenv()

app = FastAPI(
    title="RAG PDF Chatbot API",
    description="API for chatting with your PDF documents using RAG.",
    version="1.0.0"
)

# Directory to store uploaded PDFs
PDF_STORAGE_DIR = "uploaded_pdfs"
# Create the directory if it doesn't exist
Path(PDF_STORAGE_DIR).mkdir(parents=True, exist_ok=True)


# Pydantic models for request and response data validation
class LoadPdfRequest(BaseModel):
    pdf_filename: str


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    answer: str


# --- API Endpoints ---

@app.get("/")
async def root():
    """
    Root endpoint for the API. Provides a welcome message and directs to docs.
    """
    return {"message": "Welcome to the RAG PDF Chatbot API! Use /docs for API documentation."}


@app.post("/upload_pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    """
    Uploads a PDF file to the server's storage directory.
    - **file**: The PDF file to upload.
    """
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Only PDF files are allowed.")

    file_path = os.path.join(PDF_STORAGE_DIR, file.filename)
    try:
        # Write the uploaded file to the specified path
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return {"message": f"File '{file.filename}' uploaded successfully.", "file_path": file_path}
    except Exception as e:
        # Handle potential errors during file upload
        raise HTTPException(
            status_code=500, detail=f"Failed to upload file: {e}")


@app.post("/load_pdf/")
async def load_pdf_for_chat(request: LoadPdfRequest):
    """
    Loads and initializes the RAG pipeline for a specific PDF by its filename.
    The PDF must have been previously uploaded to the server via `/upload_pdf/`
    or exist in the `uploaded_pdfs` directory.
    - **pdf_filename**: The name of the PDF file to load (e.g., "my_document.pdf").
    """
    pdf_path = os.path.join(PDF_STORAGE_DIR, request.pdf_filename)
    if not os.path.exists(pdf_path):
        # Return 404 if the specified PDF is not found
        raise HTTPException(
            status_code=404, detail=f"PDF file '{request.pdf_filename}' not found in {PDF_STORAGE_DIR}.")

    try:
        # Call the function from chatbot_api_logic to initialize the RAG pipeline
        load_and_initialize_chatbot(pdf_path)
        return {"message": f"Chatbot initialized for PDF: {request.pdf_filename}"}
    except Exception as e:
        # Handle errors during the RAG pipeline initialization
        raise HTTPException(
            status_code=500, detail=f"Error initializing chatbot for PDF: {e}")


@app.post("/chat/", response_model=ChatResponse)
async def chat_with_pdf(request: ChatRequest):
    """
    Sends a question to the loaded PDF chatbot and gets an answer.
    A PDF must be loaded via `/load_pdf/` endpoint first.
    - **question**: The query string for the chatbot.
    """
    try:
        # Call the function from chatbot_api_logic to get the chatbot's response
        answer = get_chatbot_response(request.question)
        return ChatResponse(answer=answer)
    except ValueError as e:
        # Specific error for when the chatbot hasn't been initialized
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # General error for other issues during chat
        raise HTTPException(
            status_code=500, detail=f"Error getting chatbot response: {e}")


@app.get("/list_pdfs/")
async def list_pdfs():
    """
    Lists all PDF files currently available in the server's storage directory.
    """
    try:
        # List all files in the storage directory that end with .pdf
        pdfs = [f for f in os.listdir(PDF_STORAGE_DIR) if f.endswith(".pdf")]
        return {"available_pdfs": pdfs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing PDFs: {e}")
