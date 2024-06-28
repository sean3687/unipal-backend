from pymongo import MongoClient
import os
from dotenv import load_dotenv
load_dotenv()


client = MongoClient(os.getenv("MONGO_URI"))

class profileFilter:
    def __init__(self, current_user):
        self.currentUser = current_user
        self.db = client["Course-Database"]
        self.collectionName = self.db.userProfile
        
    def get_Data_for_User(self):
    # Query the database for the department field where username matches
        user_profile = self.collectionName.find_one({'username': self.currentUser}, {'department_name': 1, '_id': 0})
        for x in user_profile:
            print(x)

