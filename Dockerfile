FROM python:3.10

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ="Europe/Oslo"
RUN apt-get update && apt-get install -y ffmpeg tzdata nginx
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV RTSP_URL=""
ENV CAM=""
ENV ARCHIVE=""
ENV DRAW_TIMESTAMP=""

ENV FREQUENCY_HOUR=0
ENV FREQUENCY_MINUTE=3
ENV FREQUENCY_SECOND=0

ENV SEND=""
ENV TOKEN=""
ENV URL=""

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Forward 80 and 443 from the camera to the container to make it easier to access the camera
RUN echo "export IP=\"\$(echo \${RTSP_URL} | grep -oP '\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')\"" > /app/start.sh \
    && echo "rm /etc/nginx/sites-enabled/default" >> /app/start.sh \
    && echo "echo \"server { listen 80; location / { proxy_pass https://\${IP}:443; } }\" > /etc/nginx/sites-enabled/myproxy.conf" >> /app/start.sh \
    && echo "echo \"server { listen 443; location / { proxy_pass https://\${IP}:443; } }\" >> /etc/nginx/sites-enabled/myproxy.conf" >> /app/start.sh \
    && echo "service nginx restart" >> /app/start.sh \
    && echo "python Cam2Lapse.py" >> /app/start.sh

COPY Cam2Lapse.py .
COPY config.py .

EXPOSE 80
EXPOSE 443
CMD ["sh", "/app/start.sh"]

