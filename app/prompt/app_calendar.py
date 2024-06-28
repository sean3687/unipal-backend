import os
from flask import Flask, request, jsonify, session, Blueprint
from pymongo import MongoClient
from dotenv import load_dotenv
from flask_login import login_required

load_dotenv()
# Load environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGODB_NAME")]
user_profile = db.userProfile
courses = db.Courses
calendarRoute = Blueprint("app_calendar",__name__)
# Helper function to determine the latest quarter for a course
#helper function previous
def get_latest_quarter(terms):
    if not terms or len(terms) == 0:
        return None
    latest_term = terms[-1]
    _, quarter = latest_term.split(' ')
    return quarter

# GET endpoint to retrieve the latest term for a course
@calendarRoute.route('/calendar/<course_id>', methods=['GET'])
def get_latest_term(course_id):
    print(course_id)
    course = courses.find_one({"id": course_id})
    print(course)
    if not course:
        return jsonify({"error": "Course not found"}), 404
    latest_quarter = get_latest_quarter(course.get('terms'))
    if not latest_quarter:
        return jsonify({"error": "Invalid term or quarter"}), 400
    return jsonify({"latest_term": latest_quarter}), 200

# POST endpoint to add and save a course to user's courses_taken
@calendarRoute.route('/calendar/save', methods=['POST'])
@login_required
def add_course():
    user_id =session.get("username")
    data = request.get_json()
    user = user_profile.find_one({"username": user_id})
    if not user:
        return jsonify({"error": "User not found"}), 404
    if 'courses_taken' not in user:
        user['courses_taken'] = {"Fall": [], "Winter": [], "Spring": [], "Summer": []}
    user_profile.update_one({"username": user_id}, {"$set": {"courses_taken": data}})
    user = user_profile.find_one({"username": user_id})
    return jsonify({"message":"The plan is saved"}), 200

# GET endpoint to retrieve the user's current courses_taken
@calendarRoute.route('/calendar', methods=['GET'])
@login_required
def get_courses_taken():
    user_id = session.get("username")
    print(user_id)
    user = user_profile.find_one({"username": user_id}, {"courses_taken": 1, "_id": 0})
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.get('courses_taken', {})), 200