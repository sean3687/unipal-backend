from flask import Flask, request, render_template, url_for, redirect
from flask import jsonify, request, session
from course_suggestion import courseSuggestion

from flask_bcrypt import Bcrypt
from pymongo import MongoClient
from flask_cors import CORS

import os

app = Flask(__name__)
course_suggestion = courseSuggestion()
CORS(app)



app = Flask(__name__)
bcrypt = Bcrypt(app)
client = MongoClient("mongodb+srv://uciventureunipal:unipal2024vc@unipal.bnx1cu8.mongodb.net/")
db = client['user_database']  # 'user_database' is the name of the database
users = db.users  # 'users' is the collection where user data will be stored

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'safe_default_key')
app.config['SESSION_TYPE'] = os.getenv('SESSION_TYPE', 'filesystem')

@app.route('/')
def home():
    return "Welcome to the Homepage!"

@app.route('/signup/', methods=['POST'])
def signup():
    # first_name = user
    # print(first_name)
    first_name = request.json['first_name']
    last_name = request.json['last_name']
    email = request.json['email']
    password = request.json['password']
    if users.find_one({"email": email}):
        return jsonify({"error": "Email already exists"}), 409
    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    user_data = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "password": hashed_password
    }
    users.insert_one(user_data)
    return jsonify({"message": "User registered successfully!"}), 201


@app.route('/login', methods=['POST'])
def login():
    email = request.json['email']
    password = request.json['password']
    user = users.find_one({"email": email})
    if user and bcrypt.check_password_hash(user['password'], password):
        session['user_id'] = str(user['_id'])
        return jsonify({"message": "Login successful!"}), 200
    else:
        return jsonify({"error": "Invalid credentials"}),401


if __name__ == "__main__":
    #app.run(debug=True, port=8080)  # Adjust port as necessary
    app.run(ssl_context=('/etc/ssl/certs/selfsigned.crt', '/etc/ssl/private/selfsigned.key'))
