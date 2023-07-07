# Map /app/img to the root folder of the receiver (where .webp files are stored)
FROM python:3.10
ARG DEBIAN_FRONTEND=noninteractive
ENV DISCORD_TOKEN=""
ENV TZ=Europe/Oslo
RUN apt-get update && apt-get install -y tzdata
RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
RUN mkdir /app
WORKDIR /app
COPY DiscordBot.py /app
VOLUME /app/img
RUN pip install discord.py
CMD ["python", "DiscordBot.py"]
