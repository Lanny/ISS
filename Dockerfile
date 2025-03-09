FROM node:18 AS statics
USER node
COPY --chown=node ./src/statics /home/node/static-builder
WORKDIR /home/node/static-builder
RUN npm ci
RUN npm run build

FROM python:3.11 AS web
COPY ./requirements.txt /opt/ISS/
WORKDIR /opt/ISS

RUN python -m pip install -r /opt/ISS/requirements.txt

COPY ./src/ISS /opt/ISS/src/ISS
ENV PYTHONSTARTUP=/opt/ISS/src/ISS/shell_startup.py
COPY ./src/manage.py /opt/ISS/src/manage.py
COPY ./src/startup.sh /opt/ISS/src/startup.sh
COPY --from=statics /home/node/static-builder/dist /opt/ISS/src/ISS/static
RUN mkdir -p /opt/ISS/statics_and_media/statics && mkdir /opt/ISS/statics_and_media/media
