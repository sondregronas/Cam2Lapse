import os
import re
from pathlib import Path

import requests
from flask import Flask, render_template, request, abort

# A simple webui for Cam2Lapse.py

app = Flask(__name__)

if Path("config_override.py").exists():
    import config_override as config
else:
    import config

import config as default_config

cfg = {
    "RTSP_URL": config.RTSP_URL,
    "CAM": config.CAM,
    "FREQUENCY_HOUR": config.FREQUENCY_HOUR,
    "FREQUENCY_MIN": config.FREQUENCY_MIN,
    "FREQUENCY_SEC": config.FREQUENCY_SEC,
    "ARCHIVE": bool(config.ARCHIVE),
    "SEND": bool(config.SEND),
    "TOKEN": config.TOKEN,
    "RECEIVER_URL": "" if not hasattr(config, "RECEIVER_URL") else config.RECEIVER_URL,
    "URL": config.URL,
    "IMG_FOLDER": config.IMG_FOLDER,
    "DRAW_TIMESTAMP": config.DRAW_TIMESTAMP,
    "FONT": config.FONT,
    "TEXT_STYLE": config.TEXT_STYLE,
    "PREVIEW_URL": "" if not hasattr(config, "PREVIEW_URL") else config.PREVIEW_URL,
}

if cfg.get("URL") and not cfg.get("RECEIVER_URL"):
    cfg["RECEIVER_URL"] = re.search(r"(https?://.+)/", cfg["URL"]).group(1)

email_url = f'{cfg["RECEIVER_URL"]}/email/{cfg.get("CAM", "latest")}'
if not cfg.get("CAM"):
    email_url += "latest"
if cfg.get("TOKEN"):
    email_url += f"?token={cfg['TOKEN']}"


def get_emails():
    try:
        emails = requests.get(email_url).json().get(cfg["CAM"] or "latest", [])
    except requests.exceptions.RequestException:
        emails = {}
    return emails


@app.route("/")
def config_page():
    return render_template("config.html", config=cfg, emails=get_emails())


@app.route("/", methods=["POST"])
def update_settings():
    global cfg
    # Get the request form data (a post request)
    form_data = request.form

    # Reload the config file
    cfg = {
        "RTSP_URL": form_data.get("RTSP_URL", default_config.RTSP_URL),
        "CAM": form_data.get("CAM", default_config.CAM),
        "FREQUENCY_HOUR": form_data.get(
            "FREQUENCY_HOUR", default_config.FREQUENCY_HOUR
        ),
        "FREQUENCY_MIN": form_data.get("FREQUENCY_MIN", default_config.FREQUENCY_MIN),
        "FREQUENCY_SEC": form_data.get("FREQUENCY_SEC", default_config.FREQUENCY_SEC),
        "ARCHIVE": form_data.get("ARCHIVE", default_config.ARCHIVE) == "true",
        "SEND": form_data.get("SEND", default_config.SEND) == "true",
        "TOKEN": form_data.get("TOKEN", default_config.TOKEN),
        "RECEIVER_URL": form_data.get("RECEIVER_URL", "http://localhost:5000"),
        "URL": form_data.get("RECEIVER_URL", default_config.URL)
        + f"/{form_data.get('CAM')}",
        "IMG_FOLDER": form_data.get("IMG_FOLDER", default_config.IMG_FOLDER),
        "DRAW_TIMESTAMP": form_data.get(
            "DRAW_TIMESTAMP", default_config.DRAW_TIMESTAMP
        ),
        "FONT": form_data.get("FONT", default_config.FONT),
        "TEXT_STYLE": form_data.get("TEXT_STYLE", default_config.TEXT_STYLE),
        "PREVIEW_URL": form_data.get("PREVIEW_URL", ""),
    }

    if cfg.get("TOKEN"):
        cfg["URL"] = f"{cfg['URL']}?token={cfg['TOKEN']}"

    # Get the camera ip (:// <ip> :
    cam_ip = re.search(r"//(.+):?", cfg["RTSP_URL"])
    if not cam_ip:
        abort(400, "Invalid RTSP URL")
    cam_ip = cam_ip.group(1)

    if "@" in cam_ip:
        cam_ip = f"{cam_ip.split('://')[0]}://{cam_ip.split('@')[1]}"

    # Update settings (write a new config_override.py file)
    with open("config_override.py", "w") as f:
        for k, v in cfg.items():
            f.write(f"{k} = {repr(v)}\n")

    cam_ip = cam_ip.split("://")[-1].split(":")[0]
    # Update the camera url in nginx
    if os.path.exists("/etc/nginx/sites-enabled"):
        os.system("rm /etc/nginx/sites-enabled/myproxy.conf")
        with open("/etc/nginx/sites-enabled/myproxy.conf", "w+") as file:
            file.write(
                f"server {{ listen 8080; location / {{ proxy_pass https://{cam_ip}:443; }} }}"
            )

        router_ip = ".".join(cam_ip.split(".")[0:3]) + ".1"
        os.system("rm /etc/nginx/sites-enabled/router.conf")
        with open("/etc/nginx/sites-enabled/router.conf", "w+") as file:
            file.write(
                f"server {{ listen 8081; location / {{ proxy_pass http://{router_ip}/; proxy_set_header Referer http://{router_ip}/; }} }}"
            )
        os.system("service nginx restart")

    return render_template("config.html", config=cfg)


@app.route("/restart")
def restart():
    os._exit(0)
    return "Restarted!"


@app.route("/email", methods=["POST"])
def email():
    email_list = []
    for v in request.json.get("emails", {}):
        if v.strip():
            email_list += [v.strip()]

    requests.post(
        email_url,
        json={"emails": email_list},
    )

    # TODO: add a notification toast
    return "Emails updated!"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
