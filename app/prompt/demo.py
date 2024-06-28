import streamlit as st
from courseSuggestionChat import courseSuggestion
from flask_login import current_user 


st.title("UniPal")
cr = courseSuggestion(current_user.email)

with st.chat_message("assistant"):
    st.write("Hello 👋, ask anything related to your UniPal")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if question := st.chat_input("Ask any course related questions!"):
    # Display user message in chat message container
    st.session_state.messages.append({"role": "user", "content": question})
    st.chat_message("user").markdown(question)
    answer, chat_history = cr.askQuestion(question)
    # Add user message to chat history
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = answer
    message_placeholder.markdown(full_response)
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})