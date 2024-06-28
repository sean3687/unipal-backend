from flask_login import (
    login_user,
    logout_user,
    LoginManager,
    login_required
)
from flask_session import Session
from flask import Blueprint, request, jsonify, make_response
from .validators import register_validator, login_validator
from .models.mongoModels import User
from flask import url_for, redirect, session
from prompt import courseSuggestionChat

courseSuggestion = courseSuggestionChat.courseSuggestion()

appAuth = Blueprint("appAuth", __name__)
server_session = Session()
login_manager = LoginManager()


# userProfile = courseSuggestionChat(session.get("username"))

@login_manager.user_loader
def load_user(user_id: int):
    if user_id is not None:
        return User.get_by_id(user_id)
    return None


@login_manager.unauthorized_handler
def unauthorized() -> tuple:
    return jsonify({'message': 'Access denied!'}), 401


@appAuth.route('/getUser', methods=['GET'])
def getUser():
    username = session.get("username")
    if not username:
        return build_cors_response(jsonify({"error": "unauthorized"}), 401)
    return build_cors_response(jsonify({"message": username}))


@appAuth.route('/signup', methods=['POST'])
def register() -> tuple:
    if request.method == 'OPTIONS':
        return build_cors_response()
    data = request.get_json(silent=True)
    # try:
    #     register_validator(data)
    # except Exception as e:
    #     return build_cors_response(jsonify({'message': e.args[0]['message']}), e.args[0]['code'])
    email = data['email']
    password = data['password']
    username = email
    firstname = data['firstname']
    lastname = data['lastname']
    try:
        User.register(email, username, password, firstname, lastname)
        print('done!')
        return build_cors_response(jsonify({'message': "Successfully created!"}, 200))
    except Exception as e:
        return build_cors_response(jsonify({'message': 'Email address already exists!'}, 409))


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


@appAuth.route('/login', methods=['POST', 'OPTIONS'])
def login() -> tuple:
    if request.method == 'OPTIONS':
        return build_cors_response()
    data = request.get_json(silent=True)
    # try:
    #     login_validator(data)
    # except Exception as e:
    #     return jsonify({'message': e.args[0]['message']}), e.args[0]['code']

    email_or_username = data['email']
    password = data['password']
    session["username"] = email_or_username
    try:
        user = User.get_verified(email_or_username, password)
        login_user(user)
        return build_cors_response(jsonify({'message': 'Successfully Logged in'}, 200))
    except Exception as e:
        return build_cors_response(jsonify({'error': 'Invalid credentials!'}, 404))


@appAuth.route('/profile', methods=['POST', 'OPTIONS'])
@login_required
def profile():
    # if not session.get("username").is_authenticated:
    #     return jsonify({'message': 'User not authenticated'}), 401
    if request.method == 'OPTIONS':
        return build_cors_response()
    data = request.get_json(silent=True)
    course_level = data['course_level']
    title = data.get('title', [])
    department_name = data['department_name']
    courseId = data.get('courseId', [])
    username = session.get("username")  # Using session.get("username") to access username
    # username = "jina@gmail.com"
    studentId = data['studentId']

    try:
        profile_data = User.profileDetails(username, studentId, title, course_level, department_name, courseId)
        return build_cors_response(jsonify({'message': "Profile updated!"}, 201))
    except Exception as e:
        # jsonify({'message': str(e)}), 409
        return build_cors_response(jsonify({'message': 'Profile update not successful' + str(e)}, 409))


@appAuth.route('/currentUser', methods=['GET'])
@login_required
def currentUser() -> tuple:
    if request.method == 'OPTIONS':
        return build_cors_response()
    username = session.get("username")
    return build_cors_response(jsonify({'message': username}, 201))


@appAuth.route('/logout', methods=['POST'])
@login_required
def logout() -> tuple:
    logout_user()
    return build_cors_response(jsonify('User logout'), 200)
