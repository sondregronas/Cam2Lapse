# Temporary dockerfile for testing purposes

FROM python:3.7

RUN mkdir /app
WORKDIR /app
COPY Receiver.py /app

RUN pip install flask
RUN mkdir /app/img

VOLUME /app/img
RUN echo '<html><head><meta http-equiv="Refresh" content="0; url="latest.jpg" /></head><body></body></html>' > /app/img/index.html
EXPOSE 5000

CMD ["python", "Receiver.py"]