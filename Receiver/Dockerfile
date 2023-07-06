# Temporary dockerfile for testing purposes
# NOTE: This is not the final dockerfile, it is only for testing purposes
# Don't run in production unless you know what you are doing (it is not secure)

FROM python:3.7

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