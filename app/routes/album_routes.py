from flask import request, jsonify
import jwt
from ..db.db import mysql

SECRET_KEY = "your_secret_key_here"

def album_routes(app):
    @app.route('/create_album', methods=['POST'])
    def create_album():
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

        album_name = request.json.get('name')
        if not album_name:
            return jsonify({"message": "Album name is required"}), 400

        cursor = mysql.connection.cursor()
        query = "INSERT INTO albums (name, user_id) VALUES (%s, %s)"
        cursor.execute(query, (album_name, user_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Album created successfully"}), 201
    
    @app.route('/add_music_to_album', methods=['POST'])
    def add_music_to_album():
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

        album_id = request.json.get('album_id')
        music_id = request.json.get('music_id')

        if not album_id or not music_id:
            return jsonify({"message": "Album ID and Music ID are required"}), 400

        cursor = mysql.connection.cursor()
        query = "INSERT INTO album_music (album_id, music_id) VALUES (%s, %s)"
        cursor.execute(query, (album_id, music_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Music added to album successfully"}), 201
    
    @app.route('/remove_music_from_album', methods=['DELETE'])
    def remove_music_from_album():
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
        
        album_id = request.json.get('album_id')
        music_id = request.json.get('music_id')

        if not album_id or not music_id:
            return jsonify({"message": "Album ID and Music ID are required"}), 400

        cursor = mysql.connection.cursor()

        # Ensure that the album belongs to the user
        verify_query = "SELECT id FROM albums WHERE id = %s AND user_id = %s"
        cursor.execute(verify_query, (album_id, user_id))
        album = cursor.fetchone()

        if not album:
            cursor.close()
            return jsonify({"message": "Album not found or does not belong to the user"}), 404

        # Attempt to remove the music from the album
        delete_query = "DELETE FROM album_music WHERE album_id = %s AND music_id = %s"
        cursor.execute(delete_query, (album_id, music_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Music removed from album successfully"}), 200
    
    @app.route('/edit_album_name', methods=['PUT'])
    def edit_album_name():
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

        album_id = request.json.get('album_id')
        new_name = request.json.get('name')

        if not album_id or not new_name:
            return jsonify({"message": "Album ID and new name are required"}), 400

        cursor = mysql.connection.cursor()
        query = "UPDATE albums SET name = %s WHERE id = %s AND user_id = %s"
        cursor.execute(query, (new_name, album_id, user_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Album name updated successfully"}), 200
    
    @app.route('/list_albums', methods=['GET'])
    def list_albums():
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

        # Modified query to count the number of tracks in each album
        query = """
            SELECT 
                albums.id, 
                albums.name, 
                albums.created_at, 
                COUNT(album_music.music_id) AS track_count  
            FROM albums
            LEFT JOIN album_music ON albums.id = album_music.album_id
            WHERE albums.user_id = %s
            GROUP BY albums.id, albums.name, albums.created_at  -- Group by these columns to apply COUNT correctly
            ORDER BY albums.created_at DESC
        """
        
        cursor.execute(query, (user_id,))
        albums = cursor.fetchall()
        cursor.close()

        # Convert album list into a serializable format
        result = []
        for album in albums:
            result.append({
                "id": album['id'],
                "name": album['name'],
                "created_at": album['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                "track_count": album['track_count']  # Add the track count to the response
            })

        return jsonify(result), 200
    
    @app.route('/list_album_music/<int:album_id>', methods=['GET'])
    def list_album_music(album_id):
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
                music.id, music.file_path, music.description, music.created_at,
                music.user_id as user_id, uploaders.name as user_name, uploaders.email as user_email, uploaders.avatar as user_avatar
            FROM album_music
            JOIN music ON album_music.music_id = music.id
            JOIN albums ON album_music.album_id = albums.id
            JOIN users as uploaders ON music.user_id = uploaders.id
            WHERE album_music.album_id = %s AND albums.user_id = %s
            ORDER BY music.created_at DESC
        """
        cursor.execute(query, (album_id, user_id))
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
                "user_email": music['user_email'],
                "user_id": music['user_id'],
                "user_avatar": music['user_avatar'],
            })

        return jsonify(result), 200