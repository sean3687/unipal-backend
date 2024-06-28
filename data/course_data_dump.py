from pymongo import MongoClient
import requests

from dotenv import load_dotenv
import os


load_dotenv()
mongo_uri = os.getenv("MONGO_URI")


try:
    client = MongoClient(mongo_uri)
    database = client["Course-Database"]
    collection_list = database.list_collection_names()

    print("Successfully connected to MongoDB!")
    print("Available collections:", collection_list)

    # Pulling from PeterPortal API
    response = requests.get("https://api.peterportal.org/rest/v0/courses/all")
    courseData = response.json()

    collName = database["Courses"]
    result = collName.insert_many(courseData)
    print("Documents Inserted: ", len(result.inserted_ids))

    client.close()

except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
