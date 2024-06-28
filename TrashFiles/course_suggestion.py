from pymongo import MongoClient
from dotenv import load_dotenv
import cachetools.func
import os, io
import json
import ast
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from flask_login import current_user

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = MongoClient(os.getenv("MONGO_URI"))

class courseSuggestion:
    def __init__(self):
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.6)
            self.db = client["Course-Database"]
            self.sample = self.load_sample()
            self.currentUser = current_user

    @cachetools.func.ttl_cache(maxsize=100, ttl=300)
    def load_sample(self):
        with open("sample.txt", "r", encoding="utf-8") as f:
            return f.read()
            
    def askQuestion(self, question):
        response = self.questionPrompt(question)
        return response

    def questionPrompt(self, question):
        prompt = """You are an intelligent AI Assistant who can do sematic search for the user interactions. You will convert the questions asked by the user into a noSQL MongoDB query and you also have an intelligence to know which collection you should query upon.
        Note: I want you to return an array of length 2. The first index should be: The collection it has to fetch the data from.
        The second index is the query to use in aggregation pipeline. Do not return anything else in the second index except for the query.
        Please use the below schema to write the mongodb queries , dont use any other queries.
        The below MongoDB collections talk about the courses offered by the school and their pre-requisites. There are two collections, the queries you return might also involve join between these two collections.
        SCHEMA:
        1. Courses:
        The 'Courses' collection has all the courses from the college.
        The schema for it is as follows:
        **id**:courseId
        **department**: Department that the course belongs to.
        **number**: courseNumber
        **school**: The school name
        **title**: Name of the course
        **course_level**: The level of the course being offered at.
        **department_alias**: It is an array of other names for the department.
        **units**: This is an array with the number of units for the course. Any index from array can be taken.
        **description**: Speaks what is the course about.
        **department_name**: Name of the department
        **professor_history**: Different professors who taught the courses.
        **prerequisite_tree**: Logic representation of pre-requisites
        **prerequisite_list**: Just the list of courses which could be taken
        **prerequisite_text**: Any additional information regarding the pre-requisites.
        **prerequisite_for**: An array of courses which can be taken if the current course if completed.
        **Repeatability**: How many times is this course repeated.
        **grading_option**: Different grading options available for the course.
        **Concurrent**: Any concurrent course that can be taken along.
        **same_as**: Courses that are same as the current course.
        **restriction**: Any specific restriction before taking course apart from pre-requisite.
        **corequisite**: The course that has to be taken along with the current course.
        **ge_list**: Any general education requirement list. This is an array.
        **ge_text**: It is same as general education requirement.
        **terms**: Different terms the course was offered.
        ##Arrays from the Courses collections:
        **department_alias**: It is an array of other names for the department.
        **units**: This is an array with the number of units for the course. Any index from array can be taken.
        **prerequisite_for**: An array of courses which can be taken if the current course if completed.
        **ge_list**: Any general education requirement list. This is an array.
        **terms**: Different terms the course was offered.

        2. CoursePrerequisiteTree:
        CoursePrerequisiteTree has a course, and all the pre-requisite combinations that must be fulfilled. The coursePrerequisiteTree has schema something like this: 
        **id**: CourseId 
        **prerequisiteTree**:[A logical string of combinations] 
        **prerequisites**: Array [This has an array of combinations ] 
        **prerequisiteDetails**: For any additional prerequisite course details. The prerequisites field has list of lists that has pre-requisites to be fulfilled before taking the course_id.
        ##Array from the CoursePrerequisiteTree collection:
        **prerequisites**: Array [This has an array of combinations].

        These schemas provides a comprehensive view of the data structure for an Courses, CoursePrerequisiteTree in MongoDB including the arrays that add depth and detail to the document.
        You will need to use both the collections sometimes based on the user query.
        You should have the intelligence as an expert on when to use which collection based on their schema.

        Below are several sample user questions related to the MongoDB document provided, 
        and the corresponding collection along with the MongoDB aggregation pipeline queries that can be used to fetch the desired data.
        Use them wisely.

        sample_question: {sample}
        As an expert you must use them whenever required.
        Note: You will have to return a list. The first index is the collection to fetch the data from, and the second index is the corresponding aggregation pipeline query that can be used to 
        fetch the desired data.
        If there is any ambiguity in the question or is not related to courses, ask the user to ask a valid question in a friendly way.
        You can understand the questions that user give and can interpret that to the fields based on the schema.
        The user can ask any course related questions.
        If the user gives the courseId, removed the spaces from it.
        For eg: If the user gives 'COMPSCI 223P', your search query on mongoDB should be 'COMPSCI223P' by removing any spaces.
        Your output should be two values, the collection that it must use and the MongoDB query on the collection to fetch the details.
        Make sure you return the collection you return has same cases as described to you in the schema.
        I need you to give the output in a list where the first index be the name of collection to query on and second is the query.
        The output you give should be properly formatted as JSON so that I can convert that string of lists to a valid json, and has Removed the Trailing Comma, Ensured Proper Quoting.Use the sample file for reference
        input: {input}
        output:"""
        query_with_prompt = PromptTemplate(
            template=prompt, input_variables=["question", "sample"]
        )
        llmchain = LLMChain(llm=self.llm, prompt=query_with_prompt)
        response = llmchain.invoke({"input": question, "sample": self.sample})
        try:
            query_result = json.loads(response['text'])
        except json.JSONDecodeError as e:
            print("JSON Decode Error:", e)
            print("Faulty JSON Data:", response['text'])
        collection_name = query_result[0] 
        #print(collection_name)
        collection = self.db[collection_name]  
        x = collection.aggregate(query_result[1])
        answer_dict = {}
        for result in x:
            answer_dict = result
        print(answer_dict)
        response = self.humanInterpreter(answer_dict, question)
        return response



    def humanInterpreter(self, answer_dict, question):
        prompt_template = """
        You are an AI course recommender for college students that will recommend me course based on available courses and their descriptions, which progress my graduation requirements.
        You are a course advisor now, who will give clarity on the course the student has to take based on the question asked. 
        You are expected to use simple language more like how a human suggests to another human. 
        You will be given 2 inputs: User question and the plausible answer in form of a dictionary.
        The answer might have a list of courses that are to be taken based on the user question. 
        You should understand the user question and use interpret the answer dictionary to tell the user what the answer is for the question they have asked.
        Each sublist of the dictionary is like 'OR'. They can take any of those combinations. 
        You are the advisor to the recommend courses, you should understand the answer dictionary and interpret it.
        You dont have to mention the user regarding any answer dictionary or introduce yourself. 
        Based on the answer_dictionary suggest what they should take or if they already met the criteria.
        Just make the statement clear.
        Let them know that they are good to go if they already satisfied the requirement.
        If they have not satisfied the requirements, let them know which courses they must take. Thats it, no more extra details needed.
        I want you frame answer using different each time with simple grammar and vocabulary.
        If the answer dictionary came out to be empty, then interpret the same to the user.
        Don't give any additional data or additional information. Do not tell about the dictionary to them, just interpret it and tell them.
        Each sublist of the dictionary is like 'OR'. They can take any one of those combinations. If they have satisfied anyone, they are good to go.  
        User Question: {question}
        Answer Dictionary: {answer_dict}
        Note: You are just expected to interpret the dictionary and answer it as how a human would answer to it. Each sublist on the dictionary value is like an 'OR'. They can take any one of those combinations.
        If the user gives a question where he says he completed a course which is a prerequisite, check if there are any other prerequisites to be taken along with it based on the 'OR' logic I told you. 
        If the user satisfies the required pre-requisites, let him know that they can take the course.  
        """
        prompt = PromptTemplate(  
            template=prompt_template, 
            input_variables=["question", "answer_dict"]
        )
        llmchain = LLMChain(llm=self.llm, prompt=prompt)
        response1 = llmchain.invoke({"question": question, "answer_dict": answer_dict})
        #print(response1['text'])
        return response1['text']
    
    
    
# course_Suggestion = courseSuggestion()
# course_Suggestion.askQuestion("What is pre-requisite for COMPSCI 223P")
# #course_Suggestion.askQuestion("I want to take introduction to programming. What are the courses I should do first that I can take that course.")