FROM python:3.9

RUN apt-get install && \
    apt-get update && \
    apt-get -y upgrade && \
    pip3 install selenium && \
    pip3 install redis


WORKDIR /wsserver
COPY . .

CMD python -u wapp_server.py