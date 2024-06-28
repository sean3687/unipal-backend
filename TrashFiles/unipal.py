# 


#route for signup page
from flask import jsonify, request, session

def init_app(app, users, bcrypt):

    @app.route('/')
    def home():
        return "Welcome to the Homepage!"

    @app.route('/signup', methods=['POST'])
    def signup():
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
            return jsonify({"error": "Invalid credentials"}), 401


    
    # @app.route('/logout')
    # def logout():
    #     session.clear()
    #     return jsonify({"message": "Logged out successfully!"})
        


