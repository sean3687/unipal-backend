from flask import Flask, request, jsonify, render_template_string, Response
from flask_pymongo import PyMongo, ObjectId
from flask_login import login_user, logout_user, current_user, LoginManager, login_required
import gridfs

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb+srv://uciventureunipal:unipal2024vc@unipal.bnx1cu8.mongodb.net/Course-Database"
#app.secret_key = 'supersecretkey'
mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return mongo.db.userProfile.find_one({"_id": ObjectId(user_id)})

# Initialize GridFS
fs = gridfs.GridFS(mongo.db)

@app.route('/deleteFile', methods=['GET', 'POST'])
def delete_file():
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
            fileName = data.get('fileName')

            # Print the file name to the console
            print(f"File name received: {fileName}")

            if not fileName:
                return jsonify({'status': 'File Name is required'}), 400

            # Find the user in the database
            user = mongo.db.userProfile.find_one({"username": "safaumatia@gmail.com"})  # Adjust as needed for current_user
            print(f'{user}')
            # For debugging: return the entire user object as JSON
            if not user:
                return jsonify({'status': 'User not found'}), 404
            else:
                for file in user['files']:
                    if file['filename'] == fileName:
                        file_info = file
                        break
                if not file_info:
                    return jsonify({'status': 'File not found'}), 404
            
                try:
                    fs.delete(ObjectId(file_info['file_id']))
                except Exception as e:
                    return jsonify({'status': 'Failed to delete file fm the gridFS','error':str(e)}),500
                
                result = mongo.db.userProfile.update_one(
                {"username": "safaumatia@gmail.com"},  # Adjust as needed for current_user
                {"$pull": {"files": {"filename": fileName}}}
                )
                if result.modified_count == 0:
                    return jsonify({'status': 'Failed to delete the file from the user profile'}), 500
                
                return jsonify({'status': 'File deleted successfully'}), 200

                    
if __name__ == '__main__':
    app.run(debug=True, port = 8080)
