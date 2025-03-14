from flask import Flask
from .db.db import init_db
from .routes.user_routes import user_routes
from .routes.auth_routes import auth_routes
from .routes.music_routes import music_routes
from .routes.favourite_routes import favourite_routes
from .routes.album_routes import album_routes
from .routes.friends_routes import friends_routes
from .routes.messaging_routes import messaging_routes
from flask_cors import CORS
from flask_socketio import SocketIO, emit

def create_app():
    app = Flask(__name__)

    CORS(app)
    socketio = SocketIO(app, cors_allowed_origins="*")

    init_db(app)
    user_routes(app)
    auth_routes(app)
    music_routes(app)
    favourite_routes(app)
    album_routes(app)
    friends_routes(app)
    messaging_routes(app, socketio)

    return app, socketio