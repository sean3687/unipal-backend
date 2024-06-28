from pymongo import MongoClient
from dotenv import load_dotenv
import os
from langchain.prompts import ChatPromptTemplate, PromptTemplate
import streamlit as st
import os
import json
import ast
from langchain.chains import ConversationChain, LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_groq import ChatGroq

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))
openai_api_key = os.getenv("OPENAI_API_KEY")
db = client["Course-Database"]
client = MongoClient(os.getenv("MONGO_URI"))
groq_api_key = os.getenv("groq_api_key")
chat = ChatGroq(temperature=0, model_name="mixtral-8x7b-32768")
client = MongoClient(os.getenv("MONGO_URI"))
