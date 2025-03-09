from flask import Flask
from .db.db import init_db
from .routes.user_routes import user_routes
from .routes.auth_routes import auth_routes
from .routes.music_routes import music_routes
from .routes.favourite_routes import favourite_routes
from .routes.album_routes import album_routes
from .routes.friends_routes import friends_routes
from flask_cors import CORS

def create_app():
    app = Flask(__name__)

    CORS(app)

    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'root'
    app.config['MYSQL_DB'] = 'musik'
    app.config['MYSQL_HOST'] = '127.0.0.1'
    app.config['MYSQL_PORT'] = 3307
    app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

    init_db(app)
    user_routes(app)
    auth_routes(app)
    music_routes(app)
    favourite_routes(app)
    album_routes(app)
    friends_routes(app)

    return app