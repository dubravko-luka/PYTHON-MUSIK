from flask import request, jsonify
import jwt
from ..db.db import mysql

SECRET_KEY = "your_secret_key_here"

def friends_routes(app):
    @app.route('/list_friends', methods=['GET'])
    def list_friends():
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
            SELECT users.id, users.name, users.email FROM friends
            JOIN users ON friends.friend_id = users.id
            WHERE friends.user_id = %s
        """
        cursor.execute(query, (user_id,))
        friends = cursor.fetchall()
        cursor.close()

        return jsonify(friends), 200
    
    @app.route('/send_friend_request', methods=['POST'])
    def send_friend_request():
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"message": "Token is missing!"}), 403

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            requester_id = data['user_id']
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired!"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token!"}), 401

        recipient_id = request.json.get('recipient_id')
        if not recipient_id:
            return jsonify({"message": "Recipient ID is required"}), 400

        cursor = mysql.connection.cursor()
        # Check if request already exists
        check_query = "SELECT id FROM friend_requests WHERE requester_id = %s AND recipient_id = %s"
        cursor.execute(check_query, (requester_id, recipient_id))
        existing_request = cursor.fetchone()

        if existing_request:
            return jsonify({"message": "Friend request already sent"}), 409

        # Insert new friend request
        insert_query = "INSERT INTO friend_requests (requester_id, recipient_id) VALUES (%s, %s)"
        cursor.execute(insert_query, (requester_id, recipient_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Friend request sent"}), 201
    
    @app.route('/delete_friend_request', methods=['DELETE'])
    def delete_friend_request():
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

        request_id = request.json.get('request_id')
        if not request_id:
            return jsonify({"message": "Request ID is required"}), 400

        cursor = mysql.connection.cursor()
        # Ensure user is part of the friend request
        check_query = "SELECT * FROM friend_requests WHERE id = %s AND (requester_id = %s OR recipient_id = %s)"
        cursor.execute(check_query, (request_id, user_id, user_id))
        friend_request = cursor.fetchone()

        if not friend_request:
            return jsonify({"message": "Friend request not found or not authorized"}), 404

        delete_query = "DELETE FROM friend_requests WHERE id = %s"
        cursor.execute(delete_query, (request_id,))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Friend request deleted"}), 200
    
    @app.route('/delete_friend', methods=['DELETE'])
    def delete_friend():
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

        friend_id = request.json.get('friend_id')
        if not friend_id:
            return jsonify({"message": "Friend ID is required"}), 400

        cursor = mysql.connection.cursor()
        # Ensure user is friends with the target
        delete_query = """
            DELETE FROM friends 
            WHERE (user_id = %s AND friend_id = %s) OR (user_id = %s AND friend_id = %s)
        """
        cursor.execute(delete_query, (user_id, friend_id, friend_id, user_id))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Friend deleted"}), 200
    
    @app.route('/accept_friend_request', methods=['POST'])
    def accept_friend_request():
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

        request_id = request.json.get('request_id')
        if not request_id:
            return jsonify({"message": "Request ID is required"}), 400

        cursor = mysql.connection.cursor()
        # Ensure the request exists and is intended for the user
        query = "SELECT requester_id FROM friend_requests WHERE id = %s AND recipient_id = %s"
        cursor.execute(query, (request_id, user_id))
        request_friend = cursor.fetchone()

        if not request_friend:
            return jsonify({"message": "Friend request not found"}), 404

        # Add friend relationships in both directions
        add_friend_query = "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s), (%s, %s)"
        cursor.execute(add_friend_query, (user_id, request_friend['requester_id'], request_friend['requester_id'], user_id))

        # Delete the friend request now that it's been accepted
        delete_request_query = "DELETE FROM friend_requests WHERE id = %s"
        cursor.execute(delete_request_query, (request_id,))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Friend request accepted"}), 201
    
    @app.route('/decline_friend_request', methods=['POST'])
    def decline_friend_request():
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

        request_id = request.json.get('request_id')
        if not request_id:
            return jsonify({"message": "Request ID is required"}), 400

        cursor = mysql.connection.cursor()
        # Ensure the request exists and is intended for the user
        query = "SELECT id FROM friend_requests WHERE id = %s AND recipient_id = %s"
        cursor.execute(query, (request_id, user_id))
        request_friend = cursor.fetchone()

        if not request_friend:
            return jsonify({"message": "Friend request not found"}), 404

        # Delete the friend request
        delete_request_query = "DELETE FROM friend_requests WHERE id = %s"
        cursor.execute(delete_request_query, (request_id,))
        mysql.connection.commit()
        cursor.close()

        return jsonify({"message": "Friend request declined"}), 200
    
    @app.route('/list_friend_requests', methods=['GET'])
    def list_friend_requests():
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

        # Query to find all friend requests where the current user is the recipient
        query = """
            SELECT friend_requests.id AS request_id, users.id AS requester_id, users.name AS requester_name, users.email AS requester_email
            FROM friend_requests
            JOIN users ON friend_requests.requester_id = users.id
            WHERE friend_requests.recipient_id = %s
            ORDER BY friend_requests.created_at DESC
        """
        
        cursor.execute(query, (user_id,))
        request_list = cursor.fetchall()
        cursor.close()

        # Convert the friend request list into a serializable format
        result = []
        for request_frriend in request_list:
            result.append({
                "request_id": request_frriend['request_id'],
                "requester_id": request_frriend['requester_id'],
                "requester_name": request_frriend['requester_name'],
                "requester_email": request_frriend['requester_email']
            })

        return jsonify(result), 200
    
    @app.route('/list_sent_friend_requests', methods=['GET'])
    def list_sent_friend_requests():
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

        # Query to find all friend requests sent by the user
        query = """
            SELECT friend_requests.id AS request_id, users.id AS recipient_id, users.name AS recipient_name, users.email AS recipient_email
            FROM friend_requests
            JOIN users ON friend_requests.recipient_id = users.id
            WHERE friend_requests.requester_id = %s
            ORDER BY friend_requests.created_at DESC
        """
        
        cursor.execute(query, (user_id,))
        request_list = cursor.fetchall()
        cursor.close()

        result = []
        for request_friend in request_list:
            result.append({
                "request_id": request_friend['request_id'],
                "recipient_id": request_friend['recipient_id'],
                "recipient_name": request_friend['recipient_name'],
                "recipient_email": request_friend['recipient_email']
            })

        return jsonify(result), 200