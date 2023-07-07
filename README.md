# Cam2Lapse
A simple python script to capture timelapse images from an RTSP stream. Plus a webserver, in order to embed the latest capture in a webpage.

There's a couple of docker containers in folders for temporary use that currently don't work with the script as-is, will work on implementing this properly later (maybe).

## Requirements
* Python 3 (https://www.python.org/)
* FFmpeg (https://ffmpeg.org/)

## Installation
* Clone the repository
* `pip install -r requirements.txt`
* Run both `Cam2Lapse.py` and `Web.py` at the same time (or use the provided start script)

## Configuration
The configuration is done in the `config.py` file. It's important that you update the `RTSP_URL` variable with the URL of your camera stream. Here you can also adjust the capture interval and the port of the web server.

## Embedding the latest capture
The web server will serve the latest capture at the `/` endpoint. You can embed this in a webpage simply by using the following HTML:
```html
<img src="http://<Web-Server-IP>:5000"/>
```

Example:
```html
<img src="http://example.com:5000"/>
```

> **NOTE:** You may need to forward port 5000 (or whichever value is configured) on your router, in order to access the web server from outside your local network (if you want to).
