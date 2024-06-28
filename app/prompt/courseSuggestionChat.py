from pymongo import MongoClient
from dotenv import load_dotenv
import cachetools.func
import os, io
import json
import ast
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
from .profileData import userProfileDetail
from flask import session

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
client = MongoClient(os.getenv("MONGO_URI"))


class courseSuggestion:
    def __init__(self):
            self.llm = ChatOpenAI(model="gpt-4", temperature=0.6)
            self.db = client["Course-Database"]
            self.currentUser = session
            self.userProfile = self.db.userProfile

    def askQuestion(self, username, question):
        self.currentUser = session
        response = self.questionPrompt(username, question)
        print(response)
        return response
        
    def questionPrompt(self, username, question):
        queryResult = []
        prompt = """You are an intelligent AI Assistant who can do sematic search for the user interactions. You will convert the questions asked by the user into a noSQL MongoDB query and you also have an intelligence to know which collection you should query upon.
                Note: I want you to return an array of length 2. The first index should be: The collection it has to fetch the data from.
                The second index is the query to use in aggregation pipeline. Do not return anything else in the second index except for the query.
                Please use the below schema to write the mongodb queries , dont use any other queries.
                I expect you to return a list with 2 indexes. One has the Collection name and other has query.
                I do not need list of list. The structure should be [Index1,Index2]
                *...*: Anything mentioned in this must be followed strictly.
                *Do not give out anything else except for the list. Not even Sure, I can assist you. I need no statements.*
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
                **title**: Name of the course
                **department_name**: Name of the department that offers the course
                **course_level**: Year/Level to which the course is being offered.
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
                *Strictly use the schema that is mentioned above, including the case. Those are the only fields accessible.*

                sample_questions:
                Below are several sample user questions related to the MongoDB document provided, 
                and the corresponding MongoDB aggregation pipeline queries that can be used to fetch the desired data.
                Use them wisely.

                Question 1: What are the pre-requisites for the course "COMPSCI 223P"?
                Answer:
                [
                    "CoursePrerequisiteTree",
                    [
                        {
                            "$match": {
                                "id": {
                                    "$regex": "^COMPSCI223P$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$project": {
                                "prerequisites": 1,
                                "_id": 0
                            }
                        }
                    ]
                ]

                Question 2: In which terms the course "COMPSCI 223P" is offered?
                Answer: 
                [
                    "Courses",
                    [
                        {
                            "$match": {
                                "id": {
                                    "$regex": "^COMPSCI223P$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$project": {
                                "terms": 1,
                                "_id": 0
                            }
                        }
                    ]
                ]

                Question 3: What are the pre-requisites for course "COMPSCI 223P" and when are they offered?
                Answer:
                [
                    "Courses",
                    [
                        {
                            "$match": {
                                "id": {
                                    "$regex": "^COMPSCI223P$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$lookup": {
                                "from": "CoursePrerequisiteTree",
                                "localField": "id",
                                "foreignField": "id",
                                "as": "prerequisites"
                            }
                        },
                        {
                            "$project": {
                                "terms": 1,
                                "prerequisites": 1,
                                "_id": 0
                            }
                        }
                    ]
                ]

                Question 4: Which courses should I take first to do COMPSCI 223P later?
                Answer:
                [
                    "CoursePrerequisiteTree",
                    [
                        {
                            "$match": {
                                "id": {
                                    "$regex": "^COMPSCI223P$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$project": {
                                "prerequisites": 1,
                                "_id": 0
                            }
                        }
                    ]
                ]



                Question 6: I"m planning to take course: "ANTHRO 132A" and I have already taken a course "PSYCH 7A", what are the other pre-requisites for taking the course?
                Answer:
                [
                    "CoursePrerequisiteTree",
                    [
                        {
                            "$match": {
                                "id": {
                                    "$regex": "^ANTHRO132A$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$unwind": "$prerequisites"
                        },
                        {
                            "$unwind": "$prerequisites"
                        },
                        {
                            "$match": {
                                "prerequisites": {
                                    "$regex": "PSYCH 7A",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$group": {
                                "_id": "$_id",
                                "id": { "$first": "$id" },
                                "filteredPrerequisites": { "$push": "$prerequisites" }
                            }
                        },
                        {
                            "$project": {
                                "id": 1,
                                "prerequisites": "$filteredPrerequisites",
                                "_id": 0
                            }
                        }
                    ]
                ]

                Question 7: Are there any pre-requisite details for the course "AC ENG 23A"?
                Answer: 
                [
                    "CoursePrerequisiteTree",
                    [
                        {
                            "$match": {
                                "id": {
                                    "$regex": "^ACENG23A$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$project": {
                                "preRequisiteDetails": 1,
                                "_id": 0
                            }
                        }
                    ]
                ]

                Question 8: What was the last term the course "COMPSCI 223P" is offered?
                Answer: 
                [
                    "Courses",
                    [
                        {
                            "$match": {
                                "id": {
                                    "$regex": "^COMPSCI223P$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$unwind": "$terms"
                        },
                        {
                            "$sort": {
                                "terms": -1
                            }
                        },
                        {
                            "$group": {
                                "_id": "$id",
                                "latestTerm": { "$first": "$terms" }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "id": "$_id",
                                "latestTerm": 1
                            }
                        }
                    ]
                ]


                Question 11: When will the COMPSCI 222 is being offered?
                Answer: 
                [
                    "Courses",
                    [
                        {
                            "$match": {
                                "id": {
                                    "$regex": "^COMPSCI222P$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$unwind": "$terms"
                        },
                        {
                            "$sort": {
                                "terms": -1
                            }
                        },
                        {
                            "$group": {
                                "_id": "$id",
                                "latestTerm": { "$first": "$terms" }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "id": "$_id",
                                "latestTerm": 1
                            }
                        }
                    ]
                ]

                Question 12: When is Principles of Data Management being offered?
                Answer:
                [
                    "Courses",
                    [
                        {
                            "$match": {
                                "title": {
                                    "$regex": "^Principles of Data Management$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$unwind": "$terms"
                        },
                        {
                            "$sort": {
                                "terms": -1
                            }
                        },
                        {
                            "$group": {
                                "_id": "$id",
                                "latestTerm": { "$first": "$terms" }
                            }
                        },
                        {
                            "$project": {
                                "_id": 0,
                                "id": "$_id",
                                "latestTerm": 1
                            }
                        }
                    ]
                ]

                Question 12: When are prerequisites needed for Principles of Data Management ?
                Answer:
                [
                    "CoursePrerequisiteTree",
                    [
                        {
                            "$match": {
                                "title": {
                                    "$regex": "^Principles of Data Management$",
                                    "$options": "i"
                                }
                            }
                        },
                        {
                            "$project": {
                                "prerequisites": 1,
                                "_id": 0
                            }
                        }
                    ]
                ]

            Each of these queries is designed to give the output of the collection name from the MongoDB based on the question asked by the user.
            As an expert you must use them whenever required.   
            Note: You will have to return a list. The first index is the collection to fetch the data from, and the second index is the corresponding aggregation pipeline query that can be used to 
            fetch the desired data.
            If there is any ambiguity in the question or is not related to courses, ask the user to ask a valid question in a friendly way.
            You can understand the questions that user give and can interpret that to the fields based on the schema.
            The user can ask any course related questions.
            If the user gives the courseId, removed the spaces from it.
            For eg: If the user gives 'COMPSCI 223P', your search query on mongoDB should be 'COMPSCI223P' by removing any spaces.
            *Your output should be two values:
            1. The collection that it must use.
            2. The MongoDB query on the collection to fetch the details.*
            Make sure you return the collection you return has same cases as described to you in the schema.
            I need you to give the output in an array where the first index be the name of collection to query on and second is the query.
            The output you give should be properly formatted as an *array* so that I can convert that string of lists to a valid json, and has Removed the Trailing Comma,
            Ensured Proper Quoting.
            If the user is asking on top of their previous question, use your memory wisely. Make sure you do it right.
            Use the sample file for reference on the format of output.
            Note: Your response should only return an array. The first index is the collection to fetch the data from, and the second index is the corresponding aggregation pipeline query that can be used to 
            fetch the desired data. There is not need to describe it. It should just be a list with 'length 2'. 
            Index 1 is the collection, and Index 2 is the query to run on the collection 
            *No need to say that it is an output too.*
            It should not be list inside another list.Check the samples given for output format. Return a valid array format as output.
            *In the query, make sure there is no space between at the start and end of the string literals.*
            *strictly follow the formatting from the sample given to you*   
            *Do not return list of lists. Need only 1 list with 2 indices.*
            *The sample is just given for you to refer. Not to copy paste from it.*    
            If you are not sure about what the user is asking you, let them know to give more information before doing anything, and send message "Can you please give more information?"
            Like this [index1, index2] 
            *Do not output the anything else other than the array. Don't even mention as output*   
            *..* : The information in this has to be strictly followed. Give nothing else except the array. No other sentences or words.
            *Do not include any natural language output*
            input: {input}"""
            
        system_prompt =  prompt
        memory = ConversationBufferWindowMemory(
            k=10, memory_key="chat_history", return_messages=True
        )
        user_question = question
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
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
                llm=self.llm,
                prompt=prompt,
                memory=memory,
            )
            chat_history = []
            for message in chat_history:
                memory.save_context(
                    {"input": message["human"]}, {"output": message["AI"]}
                )
            response = conversation.predict(human_input=user_question)
            try:
                data_array = ast.literal_eval(response)
                if isinstance(data_array, list) and len(data_array) == 2:
                    message = {"human": user_question, "AI": response}
                    chat_history.append(message)
                    collection_name = data_array[0]
                    query = data_array[1]
                    collection = self.db[collection_name]
                    result = collection.aggregate(query)
                    for i in result:
                        queryResult.append(i)
                    if len(queryResult) == 1:
                        answer_dict = {}
                        for result in queryResult:
                            answer_dict = result
                        result = self.humanInterpreter(user_question, answer_dict)
                        return result, chat_history
                    else:
                        #print('Hit this as there are multiple courses')
                        profileData = userProfileDetail(username, collection_name, query)
                        keys = set(key for d in queryResult for key in d.keys())
                        answer_dict = profileData.get_user_course(keys)
                        #print(f'From user profile: {answer_dict}')
                        if len(answer_dict) == 0:
                            result = "The mentioned course is not part of your school!"
                        else:
                            result = self.humanInterpreter(user_question, answer_dict)
                else:
                    result =  "Unable to cater your request now, please try after sometime with some course related questions."
            except Exception as e:
                result = f"Error processing the response: {e}"
            return result, chat_history
        
        
    
    # Create a conversation chain using the LangChain LLM (Language Learning Model)
    def humanInterpreter(self, question, answer_dict):
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
        You just have to send the user answer. 
        """
        prompt = PromptTemplate(  
            template=prompt_template, 
            input_variables=["question", "answer_dict"]
        )
        llmchain = LLMChain(llm=self.llm, prompt=prompt)
        response1 = llmchain.invoke({"question": question, "answer_dict": answer_dict})
        return response1['text']
        

# course_Suggestion = courseSuggestion()
# # course_Suggestion.askQuestion("I want to take introduction to programming. What are the courses I should do first that I can take that course.")
# course_Suggestion.askQuestion("I want to take introduction to programming. What are the details of it")
# # course_Suggestion.askQuestion("I have already taken COMPSCI 222. I want to take COMPSCI 223P, are there any other courses that I must complete")