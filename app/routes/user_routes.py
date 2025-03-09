import bcrypt
import jwt
from flask import request, jsonify
from ..db.db import mysql

SECRET_KEY = "your_secret_key_here"

def user_routes(app):
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
        query = "SELECT id, name, email FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        cursor.close()

        if user is None:
            return jsonify({"message": "User not found"}), 404

        return jsonify({
            "id": user['id'],
            "name": user['name'],
            "email": user['email']
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
        user_query = "SELECT id, name, email FROM users WHERE id = %s"
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
            "my_profile": my_profile,
            "is_friend": is_friend,
            "is_friend_request": is_friend_request,
            "friend_request_id": friend_request_id,
            "friend_request_direction": friend_request_direction  # Add direction field
        }

        return jsonify(user_data), 200