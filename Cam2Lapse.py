"""
Cam2Lapse is a Python script that takes a screenshot of an RTSP stream at a given frequency and saves it
to local storage sorted by date. It also saves the latest image as "latest.jpg" for easy access.

Web.py in the same folder is a simple Flask server that serves the latest capture from this script.

Adjust the config.py file to your liking, then run this script.
"""
import os
import shutil
import datetime
import time
from pathlib import Path
from config import *


def capture_frame() -> None:
    """Takes a screenshot of the RTSP stream and saves it to the local filesystem."""
    # Create a timestamped file (in a folder named with today's date)
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.datetime.now().strftime("%H'%M'%S %Y-%m-%d")

    # Filepath to save the images to
    filename = Path(f'{IMG_FOLDER}/{date}/{timestamp}.jpg')
    latest = Path(f'{IMG_FOLDER}/latest.jpg')

    # Ensure the folder exists
    if not os.path.exists(f'{IMG_FOLDER}/{date}'):
        os.makedirs(f'{IMG_FOLDER}/{date}')

    # Create the command to take the screenshot
    if USE_TIMESTAMP:
        text_ffmpeg = timestamp.replace("'", "\:")
        command = f'ffmpeg -i {RTSP_URL} -vframes 1 -vf "drawtext=fontfile={FONT}: text=\'{text_ffmpeg}\': {TEXT_STYLE}" "{filename}"'
    else:
        command = f'ffmpeg -i {RTSP_URL} -vframes 1 "{filename}"'

    # Take the screenshot
    os.system(command)

    # Copy filename as "latest.jpg"
    shutil.copy(filename, latest)


def main() -> None:
    # Create the images folder if it doesn't exist
    if not os.path.exists(IMG_FOLDER):
        os.makedirs(IMG_FOLDER)

    # Set the frequency of image updates
    frequency = FREQUENCY_HOUR * 3600 + FREQUENCY_MIN * 60 + FREQUENCY_SEC

    # Start the image capture loop
    while True:
        capture_frame()
        time.sleep(frequency)


if __name__ == "__main__":
    main()
