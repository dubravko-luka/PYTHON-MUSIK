from flask import request, jsonify
import bcrypt
import jwt
from datetime import datetime, timedelta
from ..db.db import mysql

# Your secret key
SECRET_KEY = "your_secret_key_here"

def auth_routes(app):
    @app.route('/register', methods=['POST'])
    def register():
        name = request.json.get('name')
        email = request.json.get('email')
        password = request.json.get('password')
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        cursor = mysql.connection.cursor()
        query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
        cursor.execute(query, (name, email, hashed_password))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "User registered successfully"}), 201
    
    @app.route('/login', methods=['POST'])
    def login():
        email = request.json.get('email')
        password = request.json.get('password')

        cursor = mysql.connection.cursor()
        query = "SELECT id, password FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()
        cursor.close()

        if user is not None:
            # Assuming user['password'] is a bytes-like object from the DB
            if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8') if isinstance(user['password'], str) else user['password']):
                # Generate token
                token = jwt.encode({
                    'user_id': user['id'],
                    'exp': datetime.utcnow() + timedelta(days=1)  # Token expiry
                }, SECRET_KEY, algorithm='HS256')

                return jsonify({"message": "Login successful", "token": token}), 200
            else:
                return jsonify({"message": "Invalid email or password"}), 401
        else:
            return jsonify({"message": "User not found"}), 404