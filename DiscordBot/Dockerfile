# Map /app/img to the root folder of the receiver (where .webp files are stored)
FROM python:3.8
ENV DISCORD_TOKEN=""
RUN mkdir /app
WORKDIR /app
COPY DiscordBot.py /app
VOLUME /app/img
RUN pip install discord.py
CMD ["python", "DiscordBot.py"]