FROM python:3.9

RUN apt-get install && \
    apt-get update &&\
    apt-get -y upgrade && \
    pip install websockets && \
    pip install asgiref && \
    pip install redis && \
    pip3 install selenium && \
    pip3 install selenium-wire


WORKDIR /wsserver
COPY . .

EXPOSE 8765
EXPOSE 8087

CMD python -u socket-server.py