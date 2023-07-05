# Folder to store images
IMG_FOLDER = "Cam2Lapse"

# RTSP URL, which camera to use
RTSP_URL = "rtsp://<Your RTSP URL here>"

# Frequency of image updates
FREQUENCY_HOUR = 0
FREQUENCY_MIN = 30
FREQUENCY_SEC = 0

# Port for the Flask server (What port to serve the images on, needs to be forwarded in your router for external access)
PORT = 5000

# Host for the Flask server, you can leave this as is
# (0.0.0.0 means "all interfaces", aka publically accessible)
HOST = '0.0.0.0'