from flask import request, jsonify
import jwt
from ..db.db import mysql

SECRET_KEY = "your_secret_key_here"

def favourite_routes(app):

    @app.route('/like_music/<int:music_id>', methods=['POST'])
    def like_music(music_id):
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

        cursor = mysql.connection.cursor()
        
        # Prevent duplicate likes
        check_query = "SELECT id FROM favourites WHERE user_id = %s AND music_id = %s"
        cursor.execute(check_query, (user_id, music_id))
        existing = cursor.fetchone()

        if existing:
            return jsonify({"message": "Music already liked"}), 409

        # Add the like entry
        insert_query = "INSERT INTO favourites (user_id, music_id) VALUES (%s, %s)"
        cursor.execute(insert_query, (user_id, music_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Music liked successfully"}), 201
    
    @app.route('/unlike_music/<int:music_id>', methods=['POST'])
    def unlike_music(music_id):
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

        cursor = mysql.connection.cursor()
        
        # Check if the like exists
        check_query = "SELECT id FROM favourites WHERE user_id = %s AND music_id = %s"
        cursor.execute(check_query, (user_id, music_id))
        existing = cursor.fetchone()

        if not existing:
            return jsonify({"message": "Music not liked yet"}), 404

        # Remove the like entry
        delete_query = "DELETE FROM favourites WHERE user_id = %s AND music_id = %s"
        cursor.execute(delete_query, (user_id, music_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Music unliked successfully"}), 200
    
    @app.route('/liked_music', methods=['GET'])
    def liked_music():
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
        
        cursor = mysql.connection.cursor()
        query = """
            SELECT 
                music.id, 
                music.file_path, 
                music.description, 
                music.created_at, 
                users.name AS user_name
            FROM favourites
            JOIN music ON favourites.music_id = music.id
            JOIN users ON music.user_id = users.id
            WHERE favourites.user_id = %s
            ORDER BY music.created_at DESC
        """
        cursor.execute(query, (user_id,))
        liked_music_list = cursor.fetchall()
        cursor.close()

        # Convert the list of liked music into a serializable format
        result = []
        for music in liked_music_list:
            result.append({
                "id": music['id'],
                "file_path": music['file_path'],
                "description": music['description'],
                "created_at": music['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                "user_name": music['user_name']
            })

        return jsonify(result), 200