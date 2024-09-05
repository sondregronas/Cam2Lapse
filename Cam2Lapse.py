"""
Cam2Lapse is a Python script that takes a screenshot of an RTSP stream at a given frequency and saves it
to local storage sorted by date. It also saves the latest image as "latest.jpg" for easy access.

Web.py in the same folder is a simple Flask server that serves the latest capture from this script.

Adjust the config.py file to your liking, then run this script.
"""

import datetime
import os
import shutil
import time
from pathlib import Path

import requests

if Path("config_override.py").exists():
    from config_override import *
else:
    from config import *
import logging

logging.basicConfig(
    filename="cam2lapse.log", level=logging.INFO, format="%(asctime)s %(message)s"
)
log = logging.Logger("cam2lapse")
log.addHandler(logging.StreamHandler())


def send_to_receiver(filename: Path):
    body = {"file": open(filename, "rb")}
    while True:
        log.info("Sending latest image to server...")
        try:
            req = requests.post(URL, files=body)
            if req.status_code == 200:
                break
            else:
                log.error(
                    "Failed to send latest image to server. Retrying in 5 seconds..."
                )
        except requests.exceptions.ConnectionError:
            log.error("Connection to server failed. Retrying in 5 seconds...")
            time.sleep(5)
            continue
        except requests.exceptions.RequestException as e:
            log.error(f"{e}. Retrying in 5 seconds...")
        time.sleep(5)
        capture_frame()
        return
    log.info("Sent latest image to server!")


def capture_frame() -> None:
    """Takes a screenshot of the RTSP stream and saves it to the local filesystem."""
    # Create a timestamped file (in a folder named with today's date)
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.datetime.now().strftime("%H'%M'%S %Y-%m-%d")

    # Filepath to save the images to
    latest = Path(f"{IMG_FOLDER}/latest.jpg")
    filename = Path(f"{IMG_FOLDER}/{date}/{timestamp}.jpg")

    # Create the command to take the screenshot
    if DRAW_TIMESTAMP:
        text_ffmpeg = timestamp.replace("'", "\:")
        command = f'ffmpeg -y -i {RTSP_URL} -vframes 1 -vf "drawtext=fontfile={FONT}: text=\'{text_ffmpeg}\': {TEXT_STYLE}" "{latest}"'
    else:
        command = f'ffmpeg -y -i {RTSP_URL} -vframes 1 "{latest}"'

    # Take the screenshot
    log.info("Saving image...")

    if os.system(command) != 0:
        log.critical("Failed to save image! Is the camera running?")
        time.sleep(5)
        return capture_frame()

    if ARCHIVE:
        # Ensure the date folder exists
        if not os.path.exists(f"{IMG_FOLDER}/{date}"):
            os.makedirs(f"{IMG_FOLDER}/{date}")
        shutil.copy(latest, filename)

    log.info("Saved!")

    if SEND:
        send_to_receiver(latest)


def main() -> None:
    # Create the image folder if it doesn't exist
    if not os.path.exists(IMG_FOLDER):
        os.makedirs(IMG_FOLDER)

    # Set the frequency of image updates
    frequency = (
        float(FREQUENCY_HOUR) * 3600 + float(FREQUENCY_MIN) * 60 + float(FREQUENCY_SEC)
    )

    start = time.time()
    capture_frame()

    # Start the image capture loop
    while True:
        # Wait 10 seconds before checking if it's time to take a screenshot again
        # (Just to save some CPU cycles)
        time.sleep(10)
        if time.time() - start >= float(frequency):
            start = time.time()
            capture_frame()


if __name__ == "__main__":
    log.info("Starting Cam2Lapse with the following settings:")
    log.info(f"RTSP_URL: {RTSP_URL}")
    log.info(f"CAM: {CAM}")
    log.info(f"DRAW_TIMESTAMP: {bool(DRAW_TIMESTAMP)}")
    log.info(f"FREQUENCY_HOUR: {FREQUENCY_HOUR}")
    log.info(f"FREQUENCY_MIN: {FREQUENCY_MIN}")
    log.info(f"FREQUENCY_SEC: {FREQUENCY_SEC}")
    log.info(f"ARCHIVE: {bool(ARCHIVE)}")
    log.info(f"SEND: {bool(SEND)}")
    log.info(f"URL: {URL}")

    from webui import app

    # Start app in a separate thread
    import threading

    t = threading.Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 80})
    t.start()
    print("Starting Cam2Lapse...")
    main()
    print("Exiting...")
    os._exit(0)  # Ensure the Flask server is killed
