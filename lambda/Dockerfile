ARG FUNCTION_DIR="/function"

FROM python:3.7-bullseye as build-image

ARG LAMBDA_HANDLER_PATH

RUN apt-get update && \
  apt-get install -y \
  g++ \
  make \
  cmake \
  unzip \
  libcurl4-openssl-dev

# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

# Copy function code
COPY lambda/data-utility/index.py ${FUNCTION_DIR}

# Copy local deps
COPY ./app/libs/ ${FUNCTION_DIR}/libs/
COPY ./app/config/ ${FUNCTION_DIR}/config/

# Copy OPAS tools
COPY ./app/opasDataLoader/ ${FUNCTION_DIR}/opasDataLoader/
COPY ./app/opasDataUpdateStat/ ${FUNCTION_DIR}/opasDataUpdateStat/
COPY ./app/opasEndnoteExport/ ${FUNCTION_DIR}/opasEndnoteExport/
COPY ./app/opasGoogleMetadataExport/ ${FUNCTION_DIR}/opasGoogleMetadataExport/
COPY ./app/opasPushSettings/ ${FUNCTION_DIR}/opasPushSettings/
COPY ./app/opasSiteMapper/ ${FUNCTION_DIR}/opasSiteMapper/

# Install the runtime interface client
RUN pip3 install \
        --target ${FUNCTION_DIR} \
        awslambdaric

# Multi-stage build: grab a fresh copy of the base image
FROM python:3.7-bullseye

# Include global arg in this stage of the build
ARG FUNCTION_DIR
# Set working directory to function root directory
WORKDIR ${FUNCTION_DIR}

# Copy in the build image dependencies
COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

# Install the function's dependencies using file requirements.txt
COPY ./requirements.txt .
RUN  pip install -r requirements.txt

ENTRYPOINT [ "/usr/local/bin/python", "-m", "awslambdaric" ]
CMD [ "index.handler" ]