import streamlit as st
import os
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

st.title('RAG Chatbot!')

if 'messages' not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    st.chat_message(message['role']).markdown(message['content'])

prompt = st.chat_input('Pass your prompt here!')

if prompt:
    st.chat_message('user').markdown(prompt)
    st.session_state.messages.append({'role': 'user', 'content': prompt})

    groq_system_prompt = ChatPromptTemplate.from_template(
        "You are very smart at everything, you always give the best, the most accurate and most precise answers. Answer the following question: {user_prompt}. Start the answer directly. No small talk please."
    )

    model = 'llama3-8b-8192'
    groq_chat = ChatGroq(
        api_key=os.environ.get('GROQ_API_KEY'),  
        model_name=model
    )

    chain = groq_system_prompt | groq_chat | StrOutputParser()
    response = chain.invoke({"user_prompt": prompt}) 

    st.chat_message('assistant').markdown(response)
    st.session_state.messages.append({'role': 'assistant', 'content': response})
