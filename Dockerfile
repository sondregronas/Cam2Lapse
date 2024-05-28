FROM python:3.9

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ="Europe/Oslo"
RUN apt-get update && apt-get install -y ffmpeg tzdata
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
COPY Cam2Lapse.py .
COPY config.py .

CMD ["python", "Cam2Lapse.py"]
