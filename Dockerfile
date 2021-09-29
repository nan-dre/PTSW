FROM python:3.6-slim-buster
RUN apt-get update
ADD . /PTSW
WORKDIR /PTSW
RUN pip install -r requirements.txt
RUN python main.py