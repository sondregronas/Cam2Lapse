# Cam2Lapse off-site RTSP to "live"stream / timelapse storage (WIP)
### NOTE: This project is not ready for public use, and will probably not meet your needs as-is.
A simple python script to capture timelapse images from an RTSP stream. Plus a webserver, in order to embed the latest capture in a webpage.

There's a couple of docker containers in folders for temporary use that currently don't work with the script as-is, will work on implementing this properly later (maybe).

Status: needs work, not ready for public use - but feel free to use it if you want to :), code's a bit messy and needs a rewrite.

## Requirements
* Python 3 (https://www.python.org/)
* FFmpeg (https://ffmpeg.org/)

## Installation
* Clone the repository
* `pip install -r requirements.txt`
* Run both `Cam2Lapse.py` and `Web.py` at the same time (or use the provided start script

## Configuration
The configuration is done in the `config.py` file. It's important that you update the `RTSP_URL` variable with the URL of your camera stream. Use environment variables to override the values in `config.py`.

Using Receiver.py you can also get a frontend to view the latest image + extra archival of images - just serve the folder it provides with a webserver like nginx or apache.

## Usage with Receiver running (web server to receive images)
* Run `Receiver.py` on the receiver machine

On the sender machines (where the cameras are connected):

```sh
# NOTE: CAM set to '' will result in "latest" being used, saves in folder "1" in the receiver
export RTSP_URL="rtsp://<CAMERA-IP>"
export SEND_TO_RECEIVER="y"
export CAM="CAM1"
export URL="https://<RECEIVER-IP>"
export TOKEN="1234567890"

docker run -d \
    -e RTSP_URL=$RTSP_URL \
    -e SEND=$SEND_TO_RECEIVER \
    -e CAM=$CAM \
    -e URL=$URL \
    -e TOKEN=$TOKEN \
    --restart unless-stopped \
    ghcr.io/sondregronas/cam2lapse:latest
```

Alt: `curl -fsSL https://raw.githubusercontent.com/sondregronas/Cam2Lapse/main/setup-client.sh | sh`
