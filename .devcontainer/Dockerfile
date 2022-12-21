FROM python:3.9-bullseye
RUN apt-get update
COPY requirements.txt /PTSW/
WORKDIR /PTSW
RUN pip install -r requirements.txt
RUN playwright install