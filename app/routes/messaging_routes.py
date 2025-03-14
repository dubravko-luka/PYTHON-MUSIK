from flask import request, jsonify
import jwt
from datetime import datetime
from ..db.db import mysql
from flask_socketio import join_room, leave_room

SECRET_KEY = "your_secret_key_here"
connected_users = {}

def messaging_routes(app, socketio):
    @socketio.on('connect')
    def handle_connect():
        user_id = request.args.get('user_id')
        print(user_id)
        if user_id:
            join_room(str(user_id))
            connected_users[user_id] = request.sid

    @socketio.on('disconnect')
    def handle_disconnect():
        # Clean up the connected users dictionary
        user_id = [key for key, value in connected_users.items() if value == request.sid]
        if user_id:
            user_id = user_id[0]
            leave_room(user_id)
            del connected_users[user_id]

    @app.route('/list_rooms', methods=['GET'])
    def list_rooms():
        return {"connected_users": list(connected_users.keys())}, 200
    
    @app.route('/send_message', methods=['POST'])
    def send_message():
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            sender_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        recipient_id = request.json.get('recipient_id')
        content = request.json.get('content')

        if not recipient_id or not content:
            return jsonify({"message": "Recipient ID and content are required"}), 400

        cursor = mysql.connection.cursor()
        query = "INSERT INTO messages (sender_id, recipient_id, content) VALUES (%s, %s, %s)"
        cursor.execute(query, (sender_id, recipient_id, content))
        mysql.connection.commit()
        cursor.close()
        print(f"sender_id: {sender_id}"),
        print(f"recipient_id: {recipient_id}")
        socketio.emit('new_message', {'content': content, 'sender_id': sender_id}, room=str(recipient_id))
        return jsonify({"message": "Message sent successfully"}), 201
    
    @app.route('/messages/<int:user_id>', methods=['GET'])
    def get_messages(user_id):
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
            SELECT id, sender_id, recipient_id, content, created_at 
            FROM messages
            WHERE (sender_id = %s AND recipient_id = %s) OR (sender_id = %s AND recipient_id = %s)
            ORDER BY created_at DESC
        """
        cursor.execute(query, (current_user_id, user_id, user_id, current_user_id))
        messages = cursor.fetchall()
        cursor.close()

        result = []
        for message in messages:
            result.append({
                "id": message['id'],
                "sender_id": message['sender_id'],
                "recipient_id": message['recipient_id'],
                "content": message['content'],
                "created_at": message['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                "is_me": message['sender_id'] == current_user_id
            })

        return jsonify(result), 200
    
    @app.route('/sent_messages', methods=['GET'])
    def sent_messages():
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
            SELECT m.id, m.sender_id, m.recipient_id, m.content, m.created_at,
                u1.name AS sender_name, u2.name AS recipient_name
            FROM messages m
            JOIN users u1 ON m.sender_id = u1.id
            JOIN users u2 ON m.recipient_id = u2.id
            INNER JOIN (
                SELECT GREATEST(sender_id, recipient_id) as s, LEAST(sender_id, recipient_id) as r, MAX(created_at) as last_message_time
                FROM messages
                GROUP BY s, r
            ) sub ON (
                (GREATEST(m.sender_id, m.recipient_id) = sub.s AND LEAST(m.sender_id, m.recipient_id) = sub.r)
                AND m.created_at = sub.last_message_time
            )
            WHERE m.sender_id = %s OR m.recipient_id = %s
            ORDER BY m.created_at DESC
        """
        
        cursor.execute(query, (current_user_id, current_user_id))
        messages = cursor.fetchall()
        cursor.close()

        result = []
        for message in messages:
            name = message['recipient_name'] if message['sender_id'] == current_user_id else message['sender_name']
            result.append({
                "id": message['id'],
                "sender_id": message['sender_id'],
                "recipient_id": message['recipient_id'],
                "name": name,
                "content": message['content'],
                "created_at": message['created_at'].strftime('%Y-%m-%d %H:%M:%S'),
                "is_me": message['sender_id'] == current_user_id 
            })

        return jsonify(result), 200

        return jsonify(result), 200