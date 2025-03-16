import bcrypt
import os
import time
from datetime import datetime
from flask import send_from_directory, abort
import jwt
from werkzeug.utils import secure_filename
from flask import request, jsonify
from ..db.db import mysql

SECRET_KEY = "your_secret_key_here"
AVATAR_UPLOAD_FOLDER = 'uploads/avatar'
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def is_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def user_routes(app):
    app.config['UPLOAD_FOLDER_AVATAR'] = AVATAR_UPLOAD_FOLDER

    @app.route('/user_info', methods=['GET'])
    def get_user_info():
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            user_id = data['user_id']
            print(f"Decoded user_id: {user_id}")  # Debugging line
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        cursor = mysql.connection.cursor()
        query = "SELECT id, name, email, avatar FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        cursor.close()

        if user is None:
            return jsonify({"message": "User not found"}), 404

        return jsonify({
            "id": user['id'],
            "name": user['name'],
            "email": user['email'],
            "avatar": user['avatar']  # Add avatar to the response
        }), 200
    
    @app.route('/get_user_profile/<int:profile_user_id>', methods=['GET'])
    def get_user_profile(profile_user_id):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            logged_user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        cursor = mysql.connection.cursor()

        # Get the profile info
        user_query = "SELECT id, name, email, avatar FROM users WHERE id = %s"
        cursor.execute(user_query, (profile_user_id,))
        user_profile = cursor.fetchone()

        if not user_profile:
            cursor.close()
            return jsonify({"message": "User not found"}), 404

        # Determine if this is the user's own profile
        my_profile = logged_user_id == profile_user_id

        # Check if they are friends
        friend_query = """
            SELECT id FROM friends 
            WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)
        """
        cursor.execute(friend_query, (logged_user_id, profile_user_id, profile_user_id, logged_user_id))
        friendship = cursor.fetchone()
        is_friend = friendship is not None

        # Check if there is a pending friend request and get its direction and id
        friend_request_query = """
            SELECT requester_id, recipient_id, id FROM friend_requests 
            WHERE (requester_id = %s AND recipient_id = %s) OR (requester_id = %s AND recipient_id = %s)
        """
        cursor.execute(friend_request_query, (logged_user_id, profile_user_id, profile_user_id, logged_user_id))
        friend_request = cursor.fetchone()

        is_friend_request = friend_request is not None
        friend_request_id = friend_request['id'] if friend_request else None
        friend_request_direction = None
        if is_friend_request:
            if friend_request['requester_id'] == logged_user_id:
                friend_request_direction = "sent"    # User sent the friend request
            else:
                friend_request_direction = "received"  # User received the friend request

        cursor.close()

        user_data = {
            "id": user_profile['id'],
            "name": user_profile['name'],
            "email": user_profile['email'],
            "avatar": user_profile['avatar'],  # Add avatar to the response
            "my_profile": my_profile,
            "is_friend": is_friend,
            "is_friend_request": is_friend_request,
            "friend_request_id": friend_request_id,
            "friend_request_direction": friend_request_direction
        }

        return jsonify(user_data), 200
    
    @app.route('/update_user_info', methods=['PUT'])
    def update_user_info():
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

        # Getting user details from request
        name = request.json.get('name')
        email = request.json.get('email')

        # Basic validation
        if not name or not email:
            return jsonify({"message": "Name and email are required"}), 400

        cursor = mysql.connection.cursor()
        update_query = "UPDATE users SET name = %s, email = %s WHERE id = %s"
        cursor.execute(update_query, (name, email, user_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "User information updated successfully"}), 200
    
    @app.route('/upload_avatar', methods=['POST'])
    def upload_avatar():
        if 'avatar' not in request.files:
            return jsonify({"message": "No file part"}), 400

        avatar = request.files['avatar']

        if avatar.filename == '':
            return jsonify({"message": "No file selected"}), 400

        if not avatar or not is_allowed_file(avatar.filename):
            return jsonify({"message": "File type not allowed"}), 400

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

        os.makedirs(AVATAR_UPLOAD_FOLDER, exist_ok=True)

        # Generate a secure filename with a timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{user_id}_{timestamp}"
        file_path = os.path.join(AVATAR_UPLOAD_FOLDER, filename)
        avatar.save(file_path)

        cursor = mysql.connection.cursor()
        update_query = "UPDATE users SET avatar = %s WHERE id = %s"
        cursor.execute(update_query, (file_path, user_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Avatar uploaded successfully", "avatar_path": file_path}), 201
        
    @app.route('/get_avatar/<int:user_id>', methods=['GET'])
    def get_avatar(user_id):
        # Retrieve the avatar path from the database
        cursor = mysql.connection.cursor()
        query = "SELECT avatar FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        cursor.close()
        
        if user and user['avatar']:
            try:
                print(user['avatar'])
                file_path = user['avatar']
                file_dir, file_name = os.path.split(file_path)
                absolute_file_dir = os.path.abspath(file_dir)
                
                print(absolute_file_dir)

                return send_from_directory(absolute_file_dir, file_name)
            
            except FileNotFoundError:
                return jsonify({"message": "Avatar file not found on server"}), 409
        else:
            return jsonify({"message": "User or avatar not found"}), 400
        
    @app.route('/search_users', methods=['GET'])
    def search_users():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            # You can extract user_id if needed: user_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        # Get the search query parameter
        query = request.args.get('query')
        if not query:
            return jsonify({"message": "Query parameter is missing"}), 400

        cursor = mysql.connection.cursor()
        search_query = f"SELECT id, name, email, avatar FROM users WHERE name LIKE %s"
        like_pattern = f"%{query}%"  # to perform a partial match
        cursor.execute(search_query, (like_pattern,))
        users = cursor.fetchall()
        cursor.close()

        if not users:
            return jsonify([]), 200

        # Convert the fetched data to a list of dictionaries
        users_list = []
        for user in users:
            user_data = {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "avatar": user['avatar']
            }
            users_list.append(user_data)

        return jsonify(users_list), 200