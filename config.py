# RTSP URL, which camera to use
RTSP_URL = "rtsp://<Your RTSP URL here>"

# Update the latest image on each Flask request
# (This will slow down the Flask server, but allows you to always see the latest image)
CAPTURE_ON_REQUEST = True

# Folder to store images
IMG_FOLDER = "Cam2Lapse"

# Print timestamp on image (Affects both the latest image and the saved images)
DRAW_TIMESTAMP = True
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
TEXT_STYLE = "fontcolor=white: fontsize=24: box=1: boxcolor=black@0.5: boxborderw=5: x=10: y=10"

# Frequency of image updates
FREQUENCY_HOUR = 0
FREQUENCY_MIN = 30
FREQUENCY_SEC = 0

# Port for the Flask server (What port to serve the images on, needs to be forwarded in your router for external access / embedding)
PORT = 5000

# Host for the Flask server, you can leave this as is (0.0.0.0 stands for "all interfaces", a.k.a. it will be publicly accessible, as long as your firewall allows it)
HOST = '0.0.0.0'
