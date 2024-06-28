from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI"))

class userProfileDetail:
    def __init__(self, email, collectionName, query):
        self.currentUser = email
        self.db = client["Course-Database"]
        self.userCollectionName = self.db.userProfile
        self.Course_collection = collectionName
        self.courseQuery = query

    def get_Data_for_User(self):
        result = {}
        queryResult = []
        user_profile = self.userCollectionName.find_one(
            {"username": self.currentUser},
            {"department_name": 1, "course_level": 1, "_id": 0},
        )
        if user_profile is None:
            return "User profile not found."
        user_department_name = user_profile["department_name"]
        user_course_level = user_profile["course_level"]
        # remove $project from the pipeline
        #print(f'Query sent is:{self.courseQuery}\n')
        new_pipeline = [stage for stage in self.courseQuery if "$project" not in stage]
        collection = self.db[self.Course_collection]
        # Getting all results
        queryResult = collection.aggregate(new_pipeline)
        for item in queryResult:
            if (
                item["department_name"] == user_department_name
                and item["course_level"] == user_course_level
            ):
                result = item
                break
        #print(f'query result: {result}')
        return result

    def get_user_course(self, keys):
        answer = self.get_Data_for_User()
        # print("Received keys:", keys)
        # print("Data for User:", answer)            
        # Check if answer is a dictionary and not an error message or empty
        #Checking if the user has asked the question as per his courselevel and department.
        if len(answer) == 0:
            #print('returning here')
            return answer
        answerDict = {}
        if keys:  # Ensure keys is not empty
            key_list = list(keys)
            # Check if the key is present in the answer
            if len(key_list)>1:
                return answer
            elif key_list[0] in answer:
                answerDict[key_list[0]] = answer[key_list[0]]
            else:
                return "Error: Key not found in the data."
        else:
            return "Error: No keys provided."
        return answerDict



# Return None if no matching course is found
