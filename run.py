from app import create_app
from app.helpers.helpers import get_env
import eventlet

app, socketio = create_app()

if __name__ == '__main__':
    if get_env("PYTHON_ENV") == "production":
        eventlet.monkey_patch()
        socketio.run(app, host="0.0.0.0", port=get_env("PORT"), server='eventlet')
    else:
        socketio.run(app, host="0.0.0.0", port=get_env("PORT"), debug=True)