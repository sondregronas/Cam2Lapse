"""
Web.py is a simple Flask server that serves the latest image from the Cam2Lapse folder.

This must be run while Cam2Lapse.py is running.

Adjust the config.py file to your liking, then run this script.
"""
import flask
from pathlib import Path
from config import *

app = flask.Flask(__name__)

LATEST = Path(f'{IMG_FOLDER}/latest.jpg')


@app.route('/')
def index() -> flask.Response:
    """Return the latest image."""
    return flask.send_file(LATEST, mimetype='image/jpeg')


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)