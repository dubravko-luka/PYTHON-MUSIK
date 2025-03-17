import eventlet
eventlet.monkey_patch()

from app import create_app
from app.helpers.helpers import get_env

app, socketio = create_app()

if __name__ == '__main__':
    if get_env("PYTHON_ENV") == "production":
        socketio.run(app, host="0.0.0.0", port=get_env("PORT"))
    else:
        socketio.run(app, host="0.0.0.0", port=get_env("PORT"), debug=True)
