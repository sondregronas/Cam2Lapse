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

from PIL import Image, UnidentifiedImageError
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get('TOKEN')

app = flask.Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1)


def save_file(image_bytes, name='latest.jpg', directory='1') -> None:
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
    image_bytes.save(Path(f'img/{name}'))

    # Copy the file to the date dir
    shutil.copy(Path(f'img/{name}'), Path(f'img/{directory}/{date}/{timestamp}.jpg'))

    # Create a webp version of the image at half the resolution
    new_name = name.replace('.jpg', '.webp')
    try:
        image = Image.open(Path(f'img/{name}'))
    except UnidentifiedImageError:
        raise UnidentifiedImageError(f'Could not open image {name}')
    image = image.resize((int(image.width / 2), int(image.height / 2)), Image.LANCZOS)
    image.save(Path(f'img/{new_name}'), 'webp', quality=80, method=6)

    # Update index.html
    html = f'<a href="{new_name}"><img class="cam2lapse" src="{new_name}" alt="Timelapse"/></a>'
    if html in open(Path('img/index.html')).read():
        return
    with open(Path('img/index.html'), 'r+') as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if '<div class="timelapse-container">' in line:
                lines.insert(i + 1, html)
                break
        f.seek(0)
        f.writelines(lines)


@app.route('/', defaults={'path': ''}, methods=['POST'])
@app.route('/<path:path>', methods=['POST'])
def index(path) -> flask.Response:
    """Save the image to the local filesystem."""
    token = flask.request.args.get('token')
    if not token == TOKEN:
        return flask.Response(status=401)

    if not os.path.exists('img'):
        os.makedirs('img')

    try:
        save_file(flask.request.files['file'], f'{path}.jpg', path)
    except UnidentifiedImageError:
        return flask.Response(status=400)

    return flask.Response(status=200)


if __name__ == '__main__':
    if not TOKEN:
        raise ValueError('TOKEN environment variable not set.')
    if not os.path.exists('img'):
        os.makedirs('img')
    if not os.path.exists('img/index.html'):
        with open(Path('img/index.html'), 'w+') as f:
            f.write("""<!DOCTYPE html>
<html><head><title>Cam2Lapse</title><link rel="stylesheet" href="https://unpkg.com/@picocss/pico@latest/css/pico.classless.min.css"/>
<style>xmp{background-color:#0e0e0e;text-align:left;padding:5px;}</style></head>
<body>
<main>
<center>
<div class="timelapse-container">
</div>
<br><hr><br>
<p>To embed a livefeed, use the following HTML:</p>
<xmp><img class="cam2lapse" src="<link-to-image>" alt="Timelapse"/></xmp>
<p>For live updates on embedded pictures you need to add the following snippet:</p>
<xmp><script>
  let timelapse_class = "cam2lapse";
  setInterval(() => {
    for (let element of document.getElementsByClassName(timelapse_class)) {
      element.src = `${element.src.split("?")[0]}?${new Date().getTime()}`
    }
  }, 30000); // 30s
</script>
</xmp>
<script>let timelapse_class = "cam2lapse";setInterval(() => {for (let element of document.getElementsByClassName(timelapse_class)) {element.src = `${element.src.split("?")[0]}?${new Date().getTime()}`}}, 30000);</script>
</center>
</main>
</body>
</html>""")

    app.run(host='0.0.0.0', port=5000)
