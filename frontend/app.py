import os
import uuid

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Multi Agent AI Assistant",
    page_icon="🤖"
)

st.title("🤖 Multi-Agent AI Assistant")

st.write("This is the Multi Agent AI Assistant Application, built with Langchain, Langgraph with FastAPI and Streamlit")

# THREAD ID

if "thread_id" not in st.session_state:

    st.session_state.thread_id = str(
        uuid.uuid4()
    )

if st.sidebar.button("New Chat"):

    st.session_state.thread_id = str(
        uuid.uuid4()    
    )

    st.session_state.messages = []

    st.rerun()

# UI CHAT HISTORY


if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )

# CHAT INPUT

user_message = st.chat_input(
    "Ask something..."
)

if user_message:

    st.session_state.messages.append({
        "role": "user",
        "content": user_message
    })

    with st.chat_message("user"):

        st.markdown(
            user_message
        )
    
    try:

        response = requests.post(
            f"{API_URL}/chat",

            json={
                "message": user_message,
                "thread_id": st.session_state.thread_id
            },

            timeout=60
        )

        if response.status_code == 200:

            data = response.json()

            answer = data["answer"]

        else:

            answer = f"Backend error (status {response.status_code})."

    except requests.exceptions.RequestException:

        answer = "Could not reach the backend. Make sure the FastAPI server is running."

    
    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })


    with st.chat_message("assistant"):

        st.markdown(
            answer
        )