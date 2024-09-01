from os import getenv
from dotenv import load_dotenv

load_dotenv()

# Settings
RTSP_URL = getenv('RTSP_URL')
CAM = getenv('CAM', '')   # None = latest, else = cam name
FREQUENCY_HOUR = int(getenv('FREQUENCY_HOUR', 0))
FREQUENCY_MIN = int(getenv('FREQUENCY_MIN', 10))
FREQUENCY_SEC = int(getenv('FREQUENCY_SEC', 0))
ARCHIVE = getenv('ARCHIVE', False)
SEND = getenv('SEND', False)
TOKEN = getenv('TOKEN', '')
URL = f'{getenv("URL", "http://localhost:5000")}/{CAM}?token={TOKEN}'

# Folder to store images
IMG_FOLDER = 'Cam2Lapse'

# Print timestamp on image (Affects both the latest image and the saved images)
DRAW_TIMESTAMP = getenv('DRAW_TIMESTAMP', False)
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TEXT_STYLE = "fontcolor=white: fontsize=24: box=1: boxcolor=black@0.5: boxborderw=5: x=10: y=10"

# Flask
CAPTURE_ON_REQUEST = False  # (This will slow down the Flask server, but allows you to always see the latest image)
PORT = 5000
HOST = '0.0.0.0'
