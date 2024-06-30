from flask import Flask, request, jsonify, render_template_string, Response, send_file
from flask_pymongo import PyMongo, ObjectId
from flask_login import (
    login_user,
    logout_user,
    current_user,
    LoginManager,
    login_required,
)
import gridfs
from io import BytesIO
from dotenv import load_dotenv
import os


load_dotenv()

app = Flask(__name__)
app.config["MONGO_URI"] = os.getenv("MONGOURI_Database")
app.secret_key = os.getenv("SECRET_KEY")


mongo = PyMongo(app)
db = mongo.db
fs = gridfs.GridFS(db)


@app.route("/upload", methods=["GET", "POST"])
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
        
        # Update the user's profile
        db.userProfile.update_one(
            {"username": "tanujabetha123456@gmail.com"},
            {"$push": {"files": file_info}},
        )

        return jsonify({"status": "File saved successfully", "file_info": file_info}), 200

    # Render HTML form if GET request
    return render_template_string(
        """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>File Upload</title>
    </head>
    <body>
        <h1>Upload a File</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit">Upload</button>
        </form>
    </body>
    </html>
    """
    )


@app.route("/deleteFile", methods=["GET", "POST"])
#@login_required
def delete_file():
    if request.method == "POST":
        if request.is_json:
            data = request.get_json()
            fileName = data.get("fileName")
            if not fileName:
                return jsonify({"status": "File Name is required"}), 400

            # Find the user in the database
            user = mongo.db.userProfile.find_one(
                {"username": "tanujabetha123456@gmail.com"}#current_user.username}#"safaumatia@gmail.com"}
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
                    "username": "tanujabetha123456@gmail.com"#current_user.username
                },  # Adjust as needed for current_user
                {"$pull": {"files": {"filename": fileName}}},
            )
            if result.modified_count == 0:
                return (
                    jsonify(
                        {
                            "status": "Failed to delete the file from the user profile"
                        }
                    ),
                    500,
                )
            return jsonify({"status": "File deleted successfully"}), 200


@app.route("/viewFile/<fileName>", methods=["GET"])
#@login_required
def viewFile(fileName):
    # Seeing the current user
    user = mongo.db.userProfile.find_one(
            {"username": "tanujabetha123456@gmail.com"}#current_user.username}  
    )
    try:
        file_info = None
        for file in user["files"]:
            if file["filename"] == fileName:
                file_info = file
                break
        if not file_info:
            return jsonify({"status": "File not found"}), 404
        #print(f"ile found: {file}")
        # Get data from GridFS
        grid_out = fs.get(ObjectId(file_info["file_id"]))
        if grid_out is None:
            return jsonify({"status": "Not able to find the file"}), 500

        file_data = grid_out.read()
        # Create a BytesIO
        file_object = BytesIO(file_data)
        # Sending file to client to see the file
        return send_file(file_object, mimetype=grid_out.content_type, as_attachment=False, download_name=fileName)
    except Exception as e:
        return jsonify({"status": "Unable to process the request", "error": str(e)}), 500
    
    
    
if __name__ == "__main__":
    app.run(ssl_context=('/etc/ssl/certs/selfsigned.crt', '/etc/ssl/private/selfsigned.key'))
