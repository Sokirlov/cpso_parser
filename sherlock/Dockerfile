FROM python:3.7-alpine as build
WORKDIR /wheels
RUN apk add --no-cache \
    g++ \
    gcc \
    git \
    libxml2 \
    libxml2-dev \
    libxslt-dev \
    linux-headers
COPY ./sherlock/requirements.txt /opt/sherlock/
RUN pip3 wheel -r /opt/sherlock/requirements.txt


FROM python:3.7-alpine
WORKDIR /opt/sherlock
ARG VCS_REF
ARG VCS_URL="https://github.com/sherlock-project/sherlock"
LABEL org.label-schema.vcs-ref=$VCS_REF \
      org.label-schema.vcs-url=$VCS_URL
COPY --from=build /wheels /wheels
COPY ./sherlock /opt/sherlock/
RUN pip3 install -r requirements.txt -f /wheels \
  && rm -rf /wheels \
  && rm -rf /root/.cache/pip/*
WORKDIR /opt/sherlock/sherlock
COPY ./sh_server.py /opt/sherlock/sherlock/sh_server.py
RUN pip3 install redis && \
    pip3 install asgiref


ENTRYPOINT ["python", "sh_server.py"]
