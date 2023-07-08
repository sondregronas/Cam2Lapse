# Temporary dockerfile for testing purposes
# NOTE: This is not the final dockerfile, it is only for testing purposes
# Don't run in production unless you know what you are doing (it is not secure)

FROM python:3.7

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/Oslo
ENV TOKEN=""
RUN apt-get update && apt-get install -y tzdata
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir /app
WORKDIR /app
COPY Receiver.py /app

RUN pip install flask
RUN pip install Pillow
RUN mkdir /app/img

VOLUME /app/img
RUN echo '<html><head><meta http-equiv="Refresh" content="0; url="latest.webp" /></head><body></body></html>' > /app/img/index.html
EXPOSE 5000

CMD ["python", "Receiver.py"]
