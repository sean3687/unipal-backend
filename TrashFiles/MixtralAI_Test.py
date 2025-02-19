from pymongo import MongoClient
from dotenv import load_dotenv
import os
from langchain.prompts import ChatPromptTemplate, PromptTemplate
import streamlit as st
import os
import ast
from langchain.chains import ConversationChain, LLMChain
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain_core.messages import SystemMessage
from langchain.chains.conversation.memory import ConversationBufferWindowMemory
from humanInterpreter import interpretAnswer
from langchain_openai import ChatOpenAI


class courseRecommender:
    def __init__(self):
        load_dotenv()
        self.client = MongoClient(os.getenv("MONGO_URI"))
        openai_api_key = os.getenv("OPENAI_API_KEY")
        self.db = self.client["Course-Database"]
        self.api_key = os.getenv("groq_api_key")
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.6)
        self.db = self.client["Course-Database"]
        x = []


    def queryGenerator(self,question):
        prompt = """You are an intelligent AI Assistant who can do sematic search for the user interactions. You will convert the questions asked by the user into a noSQL MongoDB query and you also have an intelligence to know which collection you should query upon.
            Note: I want you to return an array of length 2. The first index should be: The collection it has to fetch the data from.
            The second index is the query to use in aggregation pipeline. Do not return anything else in the second index except for the query.
            Please use the below schema to write the mongodb queries , dont use any other queries.
            I expect you to return a list with 2 indexes. One has the Collection name and other has query.
            I do not need list of list. The structure should be [Index1,Index2]
            *...*: Anything mentioned in this must be followed strictly.
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

            Question 5: Number of students who have taken this course before whenever it was offered?

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

            Question 9: What are the courses offered in fall 2022?
            Answer:

            Question 10: Recommend me classes that will help me graduate?
            Answer:

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
        input: {input}
        
    """
        system_prompt = prompt
        memory = ConversationBufferWindowMemory(
            k=10, memory_key="chat_history", return_messages=True
        )
        user_question = question
        # llama3-8b-8192
        # mixtral-8x7b-32768
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
            if response.lower() != "can you please give more information?":  
                data_array = ast.literal_eval(response)
                message = {"human": user_question, "AI": response}
                chat_history.append(message)
                collection_name = data_array[0]
                query = data_array[1]
                collection = self.db[collection_name]
                x = collection.aggregate(query)
                answer_dict = {}
                for result in x:
                    answer_dict = result
                result = interpretAnswer.humanInterpreter(user_question, answer_dict)
            else:
                result = "I'm unable to render your ask now, please try again by adding some more details on the question."
            return result, chat_history