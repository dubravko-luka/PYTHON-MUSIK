import os
import time
from datetime import datetime
from flask import request, jsonify
from werkzeug.utils import secure_filename
import jwt
from ..db.db import mysql

UPLOAD_FOLDER = 'uploads/music'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}
SECRET_KEY = "your_secret_key_here"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def music_routes(app):
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.route('/upload_music', methods=['POST'])
    def upload_music():
        # Ensure the directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        if 'file' not in request.files:
            return jsonify({"message": "No file part"}), 400

        file = request.files['file']
        description = request.form.get('description')

        if file.filename == '':
            return jsonify({"message": "No selected file"}), 400

        if file and allowed_file(file.filename):
            # Change filename to timestamp
            file_extension = file.filename.rsplit('.', 1)[1].lower()
            timestamp = str(int(time.time()))
            filename = f"{timestamp}.{file_extension}"
            
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)

            cursor = mysql.connection.cursor()
            query = "INSERT INTO music (file_path, description, created_at, user_id) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (file_path, description, datetime.utcnow(), user_id))
            mysql.connection.commit()
            cursor.close()

            return jsonify({"message": "Music uploaded successfully"}), 201
        else:
            return jsonify({"message": "File type not allowed"}), 400