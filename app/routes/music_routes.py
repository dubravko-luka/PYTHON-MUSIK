import os
import time
from datetime import datetime
from flask import request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import jwt
from ..db.db import mysql

UPLOAD_FOLDER = 'uploads/music'
AVATAR_FOLDER = 'uploads/avatars'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}
SECRET_KEY = "your_secret_key_here"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def music_routes(app):
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.route('/upload_music', methods=['POST'])
    def upload_music():
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
        
    @app.route('/list_music', methods=['GET'])
    def list_music():
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
                users.name AS user_name,
                users.id AS user_id,
                users.avatar AS user_avatar,
                CASE 
                    WHEN favourites.id IS NOT NULL THEN TRUE 
                    ELSE FALSE 
                END AS liked,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM album_music 
                        JOIN albums ON album_music.album_id = albums.id 
                        WHERE album_music.music_id = music.id 
                        AND albums.user_id = %s
                    ) THEN TRUE 
                    ELSE FALSE 
                END AS in_album,
                album_music.album_id
            FROM music
            JOIN users ON music.user_id = users.id
            LEFT JOIN favourites ON music.id = favourites.music_id AND favourites.user_id = %s
            LEFT JOIN album_music ON music.id = album_music.music_id
            ORDER BY music.created_at DESC
        """
        cursor.execute(query, (user_id, user_id))
        music_list = cursor.fetchall()
        cursor.close()

        result = []
        for music in music_list:
            result.append({
                "id": music['id'],
                "file_path": music['file_path'],
                "description": music['description'],
                "created_at": music['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                "user_name": music['user_name'],
                "user_id": music['user_id'],
                "user_avatar": music['user_avatar'],  # Include user_avatar in the response
                "liked": music['liked'],
                "in_album": music['in_album'],
                "album_id": music['album_id']
            })

        return jsonify(result), 200

    @app.route('/my_music', methods=['GET'])
    def my_music():
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
            SELECT music.id, music.file_path, music.description, music.created_at, users.name as name, users.id as user_id, users.avatar as user_avatar
            FROM music 
            JOIN users ON music.user_id = users.id
            WHERE music.user_id = %s
            ORDER BY music.created_at DESC
        """
        cursor.execute(query, (user_id,))
        music_list = cursor.fetchall()
        cursor.close()

        return jsonify(music_list), 200

    @app.route('/music/<int:music_id>', methods=['GET'])
    def music_detail(music_id):
        cursor = mysql.connection.cursor()
        query = """
            SELECT music.id, music.file_path, music.description, music.created_at, users.id as user_id, users.avatar as user_avatar 
            FROM music 
            JOIN users ON music.user_id = users.id 
            WHERE music.id = %s
        """
        cursor.execute(query, (music_id,))
        music_detail = cursor.fetchone()
        cursor.close()

        if music_detail:
            return jsonify(music_detail), 200
        else:
            return jsonify({"message": "Music not found"}), 404

    @app.route('/delete_music/<int:music_id>', methods=['DELETE'])
    def delete_music(music_id):
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
        
        query = "SELECT user_id, file_path FROM music WHERE id = %s"
        cursor.execute(query, (music_id,))
        music = cursor.fetchone()

        if not music:
            cursor.close()
            return jsonify({"message": "Music not found"}), 404

        if music['user_id'] != user_id:
            cursor.close()
            return jsonify({"message": "Unauthorized action"}), 403

        try:
            delete_favourites_query = "DELETE FROM favourites WHERE music_id = %s"
            cursor.execute(delete_favourites_query, (music_id,))

            delete_album_music_query = "DELETE FROM album_music WHERE music_id = %s"
            cursor.execute(delete_album_music_query, (music_id,))

            if os.path.exists(music['file_path']):
                os.remove(music['file_path'])
            else:
                cursor.close()
                return jsonify({"message": "Music file not found on server"}), 404

            delete_music_query = "DELETE FROM music WHERE id = %s"
            cursor.execute(delete_music_query, (music_id,))

            mysql.connection.commit()
        except Exception as e:
            mysql.connection.rollback()
            cursor.close()
            return jsonify({"message": f"Failed to delete music: {str(e)}"}), 500

        cursor.close()
        return jsonify({"message": "Music deleted successfully"}), 200

    @app.route('/get_music_file/<int:music_id>', methods=['GET'])
    def get_music_file(music_id):
        print(f"Requested music_id: {music_id}")
        
        cursor = mysql.connection.cursor()
        query = "SELECT file_path FROM music WHERE id = %s"
        cursor.execute(query, (music_id,))
        music = cursor.fetchone()
        cursor.close()

        if music:
            try:
                file_path = music['file_path']
                print(f"Database file path: {file_path}")

                file_dir, file_name = os.path.split(file_path)
                absolute_file_dir = os.path.abspath(file_dir)
                print(f"Absolute File directory: {absolute_file_dir}")
                
                return send_from_directory(absolute_file_dir, file_name, as_attachment=True)
            
            except FileNotFoundError:
                print("FileNotFoundError reached")
                return jsonify({"message": "Music file not found on server"}), 404
        else:
            return jsonify({"message": "Music file not found"}), 404
        
    @app.route('/user_music/<int:user_id>', methods=['GET'])
    def user_music(user_id):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            current_user_id = data['user_id']
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
                users.name AS user_name,
                users.id AS user_id,
                users.avatar AS user_avatar,
                CASE 
                    WHEN favourites.id IS NOT NULL THEN TRUE 
                    ELSE FALSE 
                END AS liked,
                CASE 
                    WHEN EXISTS (
                        SELECT 1 FROM album_music 
                        JOIN albums ON album_music.album_id = albums.id 
                        WHERE album_music.music_id = music.id 
                        AND albums.user_id = %s
                    ) THEN TRUE 
                    ELSE FALSE 
                END AS in_album,
                album_music.album_id
            FROM music
            JOIN users ON music.user_id = users.id
            LEFT JOIN favourites ON music.id = favourites.music_id AND favourites.user_id = %s
            LEFT JOIN album_music ON music.id = album_music.music_id
            WHERE music.user_id = %s
            ORDER BY music.created_at DESC
        """
        cursor.execute(query, (current_user_id, current_user_id, user_id))
        music_list = cursor.fetchall()
        cursor.close()

        if not music_list:
            return jsonify({"message": "No music found for this user"}), 404

        result = []
        for music in music_list:
            result.append({
                "id": music['id'],
                "file_path": music['file_path'],
                "description": music['description'],
                "created_at": music['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                "user_name": music['user_name'],
                "user_id": music['user_id'],
                "user_avatar": music['user_avatar'],
                "liked": music['liked'],
                "in_album": music['in_album'],
                "album_id": music['album_id']
            })

        return jsonify(result), 200