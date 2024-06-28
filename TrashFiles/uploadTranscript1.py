# from flask import Flask, request, jsonify, render_template_string
# from pymongo import MongoClient
# import gridfs
# from dotenv import load_dotenv
# import os
#
# load_dotenv()
#
# app = Flask(__name__)
# app.secret_key = os.getenv("SECRET_KEY")
#
# # Initialize PyMongo and GridFS
# client = MongoClient(os.getenv("MONGO_URI"))
# db = client[os.getenv("MONGODB_NAME")]
# fs = gridfs.GridFS(db)
#
# @app.route("/upload", methods=["GET", "POST"])
# def upload():
#     if request.method == "POST":
#         if "file" not in request.files:
#             return jsonify({"status": "No file part"}), 400
#         file = request.files["file"]
#         if file.filename == "":
#             return jsonify({"status": "No selected file"}), 400
#
#         # Save file to GridFS
#         file_id = fs.put(file, filename=file.filename)
#
#         # Append file details to the user's profile
#         file_info = {
#             "file_id": str(file_id),  # Store the GridFS file ID
#             "filename": file.filename,
#         }
#         try:
#         # Update the user's profile
#             db.userProfile.update_one(
#                 {"username": "safaumatia@gmail.com"},
#                 {"$push": {"files": file_info}},
#             )
#
#             return jsonify({"status": "File saved successfully", "file_info": file_info}), 200
#         except Exception as e:
#             return jsonify("status": "File is not saved"), 500
#
#
#
#     # Render HTML form if GET request
#     return render_template_string(
#         """
#     <!DOCTYPE html>
#     <html lang="en">
#     <head>
#         <meta charset="UTF-8">
#         <title>File Upload</title>
#     </head>
#     <body>
#         <h1>Upload a File</h1>
#         <form action="/upload" method="post" enctype="multipart/form-data">
#             <input type="file" name="file" required>
#             <button type="submit">Upload</button>
#         </form>
#     </body>
#     </html>
#     """
#     )
#
# if __name__ == "__main__":
#     app.run(debug=True)
