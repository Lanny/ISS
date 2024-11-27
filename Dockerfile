FROM node:18 as statics
COPY ./src/statics /static-builder
WORKDIR /static-builder
RUN npm ci
RUN npm run build

FROM python:3.10 as web
COPY ./requirements.txt /opt/ISS/

WORKDIR /opt/ISS
RUN python -m pip install -r /opt/ISS/requirements.txt

COPY ./src/ISS /opt/ISS/src/ISS
COPY ./src/manage.py /opt/ISS/src/manage.py
COPY --from=statics /static-builder/dist/* /opts/ISS/src/ISS/static/
