FROM python:3.8-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install build-essential libssl-dev libffi-dev python-dev -y
RUN pip3 install -r requirements.txt
RUN apt-get install ffmpeg -y
COPY . .
CMD [ "python3", "main.py" ]
