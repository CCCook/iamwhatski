import time
import streamlit as st
from openai import OpenAI

# Set up the Streamlit page
st.set_page_config(page_title="WhatSki - AI Ski Advisor", layout="centered")

# Display logo centered
st.image("logo.webp", width=200)

# Show title and description
st.title("I am WhatSki 🎿")
st.write(
    "Your AI-powered ski expert! Let’s find you the perfect skis based on your style, terrain, and preferences. "
    "Just start chatting, and I'll ask you a few questions before making a recommendation."
)

# Load OpenAI credentials from secrets
openai_api_key = st.secrets["OPENAI_API_KEY"]
assistant_id = st.secrets["ASSISTANT_ID"]

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# Create a thread if not already in session
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# Initialize chat history if not already in session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input field
if prompt := st.chat_input("Ask me about skis!"):
    # Store and display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Send user message to OpenAI thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    # Call the assistant to process the message without streaming
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id,
        tools=[{"type": "file_search"}]  # ✅ Use correct retrieval tool
    )
    
    # Wait for completion
    response_text = ""
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id, 
            run_id=run.id  # ✅ Now correctly using run.id
        )
        if run_status.status == "completed":
            break
        elif run_status.status in ["failed", "cancelled"]:
            response_text = "Error: Assistant response failed."
            with st.chat_message("assistant"):
                st.markdown(response_text)
            st.session_state.messages.append({"role": "assistant", "content": response_text})
            break
        time.sleep(1)  # Wait before checking again

    # Fetch the latest response from the assistant
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id, 
        order="desc",  # Retrieve newest messages first
        limit=5  # Reduce the number of messages fetched
    )
    
    for msg in messages.data:
        if msg.role == "assistant" and msg.content[0].text.value not in [m["content"] for m in st.session_state.messages]:
            response_text = msg.content[0].text.value  # Extract response text
            break

    # Display and store assistant response
    with st.chat_message("assistant"):
        st.markdown(response_text)
    
    st.session_state.messages.append({"role": "assistant", "content": response_text})