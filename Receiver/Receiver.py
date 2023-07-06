"""
A simple Endpoint to receive images from a POST request.

This is a temporary solution that isn't really implemented in the Cam2Lapse.py script yet, but is planned to be.

NOTE: This MUST be run through a reverse proxy (like Nginx) to be secure. Otherwise, anyone can send images to this endpoint.
One should also add some sort of authentication to the endpoint, like a basic username/password combo over Nginx. I will add some
sort of authentication to this script in the future, like a token or something.
"""
import os
import shutil
import flask
from datetime import datetime
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix


app = flask.Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)


def save_file(image, name='latest.jpg', directory='1') -> None:
    """Save the file to the specified directory."""
    if name == '.jpg':
        name = 'latest.jpg'

    if not directory:
        directory = '1'

    if not os.path.exists(f'img/{directory}'):
        os.makedirs(f'img/{directory}')

    timestamp = datetime.now().strftime("%H'%M'%S %Y-%m-%d")
    date = datetime.now().strftime("%Y-%m-%d")

    # Ensure date dir exists
    if not os.path.exists(f'img/{directory}/{date}'):
        os.makedirs(f'img/{directory}/{date}')

    # Save the file
    image.save(Path(f'img/{name}'))

    # Copy the file to the date dir
    shutil.copy(Path(f'img/{name}'), Path(f'img/{directory}/{date}/{timestamp}.jpg'))


@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def index(path) -> flask.Response:
    """Save the image to the local filesystem."""
    # TODO: Add authentication here

    if not os.path.exists('img'):
        os.makedirs('img')

    save_file(flask.request.files['file'], f'{path}.jpg', path)

    return flask.Response(status=200)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)