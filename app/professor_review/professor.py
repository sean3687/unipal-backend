import pandas as pd
from pymongo import MongoClient, ASCENDING
from flask import Blueprint, Flask, jsonify, make_response, request, session
import os
from dotenv import load_dotenv
from flask_login import login_required

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
client = MongoClient(os.getenv("MONGO_URI"))
professor = Blueprint("professor", __name__)
db = client[os.getenv("MONGODB_NAME")]

professor_reviews_collection = db["professor_reviews"]
# Create indexes for faster aggregation
professor_reviews_collection.create_index([("Name_of_professor", ASCENDING)])

@professor.route("/professorNames", methods=["GET"])
def professorName():
    result = professor_reviews_collection.find({}, {'Name_of_professor': 1})
    professorNames = set()
    for item in result:
        professorNames.add(item["Name_of_professor"])
    names = {'professorNames': list(professorNames)}
    return jsonify(names)

@professor.route("/professor_reviews/<professor_name>", methods=["GET"])
@login_required
def get_professor_reviews(professor_name):
    pipeline_numerical = [
        {"$match": {"Name_of_professor": professor_name}},
        {
            "$group": {
                "_id": "$Name_of_professor",
                "average_quality": {"$avg": "$Quality_of_course"},
                "average_difficulty": {"$avg": "$Difficulty_level_of_course"},
                "average_grade": {"$avg": "$Grade_received_in_course"},
                "would_take_again": {
                    "$max": {
                        "$sum": {"$cond": [{"$eq": ["$Would_take_again", "Yes"]}, 1, 0]}
                    }
                },
            }
        },
        {
            "$project": {
                "name_of_professor": "$_id",
                "average_quality": 1,
                "average_difficulty": 1,
                "average_grade": 1,
                "would_take_again": 1,
                "_id": 0,
            }
        },
    ]
    results = list(professor_reviews_collection.aggregate(pipeline_numerical))
    pipeline_Data = [
        {"$match": {"Name_of_professor": professor_name}},
        {
            "$project": {
                "Name_of_reviewer": 1,
                "Review_feedback_paragraph": 1,
                "_id": 0,
            }
        },
    ]
    result_Data = professor_reviews_collection.aggregate(pipeline_Data)
    if not result_Data and not results:
        return jsonify({"message": "No reviews available"})
    professorReview = []
    finalResult = {}
    for item in results:
        finalResult = item
    for item in result_Data:
        professorReview.append(item)
    finalResult['average_quality'] = round(finalResult['average_quality'], 1)
    finalResult['average_difficulty'] = round(finalResult['average_difficulty'], 1)
    finalResult['average_grade'] = round(finalResult['average_grade'],1)
    finalResult["reviews"] = professorReview
    #print(finalResult)
    return jsonify({"message":finalResult})



@professor.route("/professor_reviews", methods=["POST"])
@login_required
def add_professor_review():
    try:
        # Get the review data from the request body
        review_data = request.get_json()
        # Ensure all required fields are present
        Name_of_reviewer = session.get("username")
        required_fields = [
            "Name_of_professor",
            "Quality_of_course",
            "Difficulty_level_of_course",
            "Would_take_again",
            "Grade_received_in_course",
            Name_of_reviewer,
            "Review_feedback_paragraph",
        ]
        result = db.userLoginDetails.find({"username": Name_of_reviewer})
        firstname = ""
        lastname = ""
        for item in result:
            firstname = item['firstname']
            lastname = item['lastname']
            print(firstname, lastname)
        print(review_data, Name_of_reviewer)
        Name_of_reviewer = firstname + " " + lastname
        print(Name_of_reviewer)
        review_data['Name_of_reviewer'] = Name_of_reviewer
        professor_reviews_collection.insert_one(review_data)
        return jsonify({"message": "Review added successfully!"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}),400
    

