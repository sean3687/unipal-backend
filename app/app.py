from dotenv import load_dotenv
from flask import (
    Flask,
    request,
    make_response,
    jsonify,
    send_file,
    render_template_string,session
)
from flask_cors import CORS
# from profile import profile
from flask_pymongo import PyMongo
from auth0.appAuth import server_session, login_manager, appAuth
from professor_review.professor import professor
from routes.chatCourses import chat
from routes.courseDataRoute import courseData
from prompt.app_calendar import calendarRoute
from auth0.models.mongoModels import client, bcrypt
from bson.objectid import ObjectId
from flask_login import (
    login_user,
    logout_user,
    current_user,
    LoginManager,
    login_required,
)
# END MongoDb
import gridfs
from io import BytesIO
import os
from pymongo import MongoClient


load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
app.config["PERMANENT_SESSION_LIFETIME"] = int(os.environ.get("SESSION_LIFETIME"))
# print(type(os.getenv('MONGODB_NAME')))
app.config["SESSION_TYPE"] = "mongodb"
app.config["SESSION_MONGODB"] = client
app.config["SESSION_MONGODB_DB"] = "Course-Database"
app.config["SESSION_MONGODB_COLLECT"] = "SessionTable"
app.config['SESSION_COOKIE_SAMESITE'] = 'None'
app.config['SESSION_COOKIE_SECURE'] = True

app.config["MONGO_URI"] = os.getenv("MONGO_URI")
app.secret_key = os.getenv("SECRET_KEY")


app.register_blueprint(appAuth)
app.register_blueprint(chat)
app.register_blueprint(courseData)
app.register_blueprint(professor)
app.register_blueprint(calendarRoute)
bcrypt.init_app(app)
server_session.init_app(app)
login_manager.init_app(app)


login_manager = LoginManager()
client = MongoClient(os.getenv("MONGO_URI"))
db = client[os.getenv("MONGODB_NAME")]
fs = gridfs.GridFS(db)


# @app.route('/getUser', methods = ['GET'])
# def getUser():
#     username = session.get("username")
#     if not username:
#         return jsonify({"error":"unauthorized"}), 401
#     return jsonify({"message": username})


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            return jsonify({"status": "No file part"}), 400
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"status": "No selected file"}), 400
        # Save file to GridFS
        file_id = fs.put(file, filename=file.filename)

        # Append file details to the user's profile
        file_info = {
            "file_id": str(file_id),  # Store the GridFS file ID
            "filename": file.filename,
        }
        try:
            # Update the user's profile
            db.userProfile.update_one(
                {"username": session.get("username")},  # current_user.username},
                {"$push": {"files": file_info}},
            )

            return (
                jsonify({"status": "File saved successfully", "file_info": file_info}),
                200,
            )
        except Exception as e:
            return jsonify({"status": "File is not saved"}), 500

    # return render_template_string(
    #     """
    # <!DOCTYPE html>
    # <html lang="en">
    # <head>
    #     <meta charset="UTF-8">
    #     <title>File Upload</title>
    # </head>
    # <body>
    #     <h1>Upload a File</h1>
    #     <form action="/upload" method="post" enctype="multipart/form-data">
    #         <input type="file" name="file" required>
    #         <button type="submit">Upload</button>
    #     </form>
    # </body>
    # </html>
    # """
    # )


@app.route("/deleteFile", methods=["GET", "POST"])
@login_required
def delete_file():
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            fileName = data.get("fileName")
            if not fileName:
                return jsonify({"status": "File Name is required"}), 400
            # Find the user in the database
            user = db.userProfile.find_one(
                {
                    "username": session.get("username")
                }
            )
            for file in user["files"]:
                if file["filename"] == fileName:
                    file_info = file
                    break
            if not file_info:
                return jsonify({"status": "File not found"}), 404
            try:
                fs.delete(ObjectId(file_info["file_id"]))
            except Exception as e:
                return (
                    jsonify(
                        {
                            "status": "Failed to delete file from the gridFS",
                            "error": str(e),
                        }
                    ),
                    500,
                )
            result = db.userProfile.update_one(
                {
                    "username": session.get("username")
                },  # Adjust as needed for current_user
                {"$pull": {"files": {"filename": fileName}}},
            )
            if result.modified_count == 0:
                return (
                    jsonify(
                        {"status": "Failed to delete the file from the user profile"}
                    ),
                    500,
                )
            return jsonify({"status": "File deleted successfully"}), 200


@app.route("/viewFile/<fileName>", methods=["GET"])
@login_required
def viewFile(fileName):
    # Seeing the current user
    user = db.userProfile.find_one(
        {"username": session.get("username")}
    )
    try:
        file_info = None
        for file in user["files"]:
            if file["filename"] == fileName:
                file_info = file
                break
        if not file_info:
            return jsonify({"status": "File not found"}), 404
        # print(f"ile found: {file}")
        # Get data from GridFS
        grid_out = fs.get(ObjectId(file_info["file_id"]))
        if grid_out is None:
            return jsonify({"status": "Not able to find the file"}), 500

        file_data = grid_out.read()
        # Create a BytesIO
        file_object = BytesIO(file_data)
        # Sending file to client to see the file
        return send_file(
            file_object,
            mimetype=grid_out.content_type,
            as_attachment=False,
            download_name=fileName,
        )
    except Exception as e:
        return (
            jsonify({"status": "Unable to process the request", "error": str(e)}),
            500,
        )


@app.errorhandler(404)
@app.errorhandler(405)
def uri_not_found(e) -> tuple:
    return jsonify([]), 404


if __name__ == "__main__":
    app.run(debug=True)
