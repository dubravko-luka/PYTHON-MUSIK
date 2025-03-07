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