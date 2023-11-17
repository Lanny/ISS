FROM node:18 as statics
COPY ./src/statics /static-builder
WORKDIR /static-builder
RUN npm ci
RUN npm run build

FROM python:3.10
COPY ./pyproject.toml /opt/ISS/
COPY ./docs/ /opt/ISS/docs/
COPY ./src/ /opt/ISS/src
COPY --from=statics /static-builder/dist/* /opts/ISS/src/ISS/static/
WORKDIR /opt/ISS
RUN python -m pip install .
