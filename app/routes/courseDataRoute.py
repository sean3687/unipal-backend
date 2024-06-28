import csv
from flask import jsonify, Blueprint, make_response, request

courseData = Blueprint('courseData', __name__)

def build_cors_response(response=None):
    """
    Builds a response for both OPTIONS and POST requests with the necessary CORS headers.
    """
    if not response:
        response = make_response()
    response.headers.set('Access-Control-Allow-Origin', 'http://localhost:5173')
    response.headers.set('Access-Control-Allow-Methods', 'POST, OPTIONS')
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    response.headers.set('Access-Control-Allow-Credentials', 'true')
    return response

@courseData.route('/courseData', methods=['GET'])
def get_course_data():
    csv_file_path = './routes/Courses.csv'  # Adjusted relative path
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        data = [row for row in reader]
    return jsonify(data),200
