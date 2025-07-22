import streamlit as st
import os
import hashlib
import time
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA

# 🔹 Set Page Title
st.set_page_config(page_title="RAG Chatbot", layout="wide")
st.title("🤖 RAG Chatbot with PDF Support & Authentication")

# ✅ Step 1: User Authentication
# Update this for real authentication
USER_CREDENTIALS = {"admin": "admin123", "user": "user123"}


def hash_password(password):
    """Hash password for security."""
    return hashlib.sha256(password.encode()).hexdigest()


def login():
    """Simple Login System."""
    st.sidebar.title("🔑 Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        if username in USER_CREDENTIALS and hash_password(password) == hash_password(USER_CREDENTIALS[username]):
            st.session_state["authenticated"] = True
            st.session_state["user"] = username
            time.sleep(0.5)
            st.rerun()
        else:
            st.sidebar.error("❌ Invalid Username or Password")


def logout():
    """Logout Function."""
    st.session_state["authenticated"] = False
    st.rerun()


if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
    st.stop()

st.sidebar.button("Logout", on_click=logout)  # Logout Button

# ✅ Step 2: PDF Upload & Vector Store Creation
st.sidebar.header("📂 Upload a PDF")
uploaded_file = st.sidebar.file_uploader(
    "Upload a PDF for processing", type=["pdf"])


@st.cache_resource
def get_vectorstore(pdf_file):
    """Process the uploaded PDF and create a vector store."""
    if pdf_file:
        with open("uploaded_pdf.pdf", "wb") as f:
            f.write(pdf_file.getvalue())  # Save the uploaded PDF locally

        pdf_name = "uploaded_pdf.pdf"
        loaders = [PyPDFLoader(pdf_name)]
        index = VectorstoreIndexCreator(
            embedding=HuggingFaceEmbeddings(model_name="all-MiniLM-L12-v2"),
            text_splitter=RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=100),
        ).from_loaders(loaders)
        return index.vectorstore
    return None


if uploaded_file:
    vectorstore = get_vectorstore(uploaded_file)
    if vectorstore:
        st.success("✅ PDF uploaded successfully!")
    else:
        st.error("❌ Failed to process the PDF.")

# ✅ Step 3: Chatbot UI
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    st.chat_message(message["role"]).markdown(message["content"])

prompt = st.chat_input("💬 Ask something about the PDF or any general topic...")

if prompt:
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    gemini_system_prompt = ChatPromptTemplate.from_template(
        "You are very smart at everything, you always give the best, the most accurate and most precise answers. Answer the following question: {user_prompt}. Start the answer directly. No small talk please."
    )

    model = "gemini-pro"
    gemini_chat = ChatGoogleGenerativeAI(
        model=model,
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        convert_system_message_to_human=True
    )

    try:
        vectorstore = get_vectorstore(uploaded_file)
        if vectorstore is None:
            st.error("⚠️ Vectorstore not found or failed to load vectorstore.")

        chain = RetrievalQA.from_chain_type(
            llm=gemini_chat,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"top_k": 3}),
            return_source_documents=True
        )

        result = chain({"query": prompt})
        response = result["result"]

        st.chat_message("assistant").markdown(response)
        st.session_state.messages.append(
            {"role": "assistant", "content": response})

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
