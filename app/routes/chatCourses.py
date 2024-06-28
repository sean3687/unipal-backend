from flask import Blueprint, request, jsonify, redirect, url_for, session
from flask_login import login_required
from pymongo import MongoClient
from dotenv import load_dotenv
import cachetools.func
import os, io
import json
import ast
from prompt import courseSuggestionChat, app_calendar
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder
)
from langchain_core.messages import SystemMessage
from flask_login import current_user as cu
from flask import session
from dotenv import load_dotenv
load_dotenv()
import sys


courseSuggestion = courseSuggestionChat.courseSuggestion()
chat = Blueprint("chatCourses", __name__)
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGODB_NAME")]
user_profile = db.userProfile
courses = db.Courses

@chat.route("/chat", methods=["POST"])
@login_required
def chatWithAgent():
    data = request.get_json(silent=True)
    question = data['question']
    keywords = ['add', 'insert', 'calendar']
    statement = question.lower()
    found_keywords = [keyword for keyword in keywords if keyword.lower() in statement]
    if found_keywords is not None and len(found_keywords)!=0:
        flag = add_coursetoLib(question)
        if flag==2:
            return jsonify({"message": "Course Added successfully"}), 500
        elif flag==1:
            return jsonify({"message": "The terms information is not available for the course"}), 500
        else:
            return jsonify({"message": "The course is already added or there is no information on courses."}), 500
    else:
        username = session.get('username')
    # Use the correct endpoint with the blueprint name prefix
        return redirect(url_for("chatCourses.ask", question=question))


@chat.route('/<question>')
def ask(question):
    response = courseSuggestion.askQuestion(session.get('username'), question)
    return jsonify({"message": response[0]}), 201

def add_coursetoLib(question):
    prompt = """You are an intelligent AI Assistant who can do sematic search for the user interactions.
    You can understand the question and extract the courseId that is given in the query.The output should
    just be the courseId extracted from the question. No need to use any human statements.Just the courseId extracted.
    SAMPLE: The courseIds are something like "COMPSCI223P","ACENG139W", "ACENG201","AFAM111A"
    If there are spaces in the courseID, remove the spaces.
    You can use the sample above to understand the way the courseId could be.
    """
    system_prompt =  prompt
    flag = 0
    memory = ConversationBufferWindowMemory(
            k=10, memory_key="chat_history", return_messages=True
        )
    user_question = question
    llm = ChatOpenAI(model="gpt-4", temperature=0.6)
    if user_question:
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessage(
                    content=system_prompt
                ),
                MessagesPlaceholder(
                    variable_name="chat_history"
                ),
                HumanMessagePromptTemplate.from_template(
                    "{human_input}"
                ),
            ]
        )
        conversation = LLMChain(
            llm=llm,
            prompt=prompt,
            memory=memory,
        )
        chat_history = []
        for message in chat_history:
            memory.save_context(
                {"input": message["human"]}, {"output": message["AI"]}
            )
        response = conversation.predict(human_input=user_question)
        user_id = session.get('username')
        user = user_profile.find_one({"username": user_id})
        course = courses.find_one({"id": response})
        if not user or not course:
            return jsonify({"error": "User or Course not found"}), 404
        latest_quarter = app_calendar.get_latest_quarter(course.get('terms'))
        print(latest_quarter)
        if latest_quarter is None:
            return 1

        if 'courses_taken' not in user:
            user['courses_taken'] = {"Fall": [], "Winter": [], "Spring": [], "Summer": []}

        if response not in user['courses_taken'][latest_quarter]:
            user['courses_taken'][latest_quarter].append(response)
            flag = 2
        user_profile.update_one({"username": user_id}, {"$set":{"courses_taken": user['courses_taken']}})
        #print(f'Courses taken are {user['courses_taken']}')
        return flag
        
