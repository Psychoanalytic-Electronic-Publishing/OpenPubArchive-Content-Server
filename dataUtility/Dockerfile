ARG ROOT_DIRECTORY="/tools"

FROM python:3.7-bullseye as build-image

# Include global arg in this stage of the build
ARG ROOT_DIRECTORY

# Create function directory
RUN mkdir -p ${ROOT_DIRECTORY}

# Set working directory to function root directory
WORKDIR ${ROOT_DIRECTORY}

# Install the function's dependencies using file requirements.txt
COPY ./requirements.txt .
RUN  pip install -r requirements.txt

# Copy local deps
COPY ./app/libs/ ${ROOT_DIRECTORY}/libs/
COPY ./app/config/ ${ROOT_DIRECTORY}/config/

# Copy OPAS tools
COPY ./app/opasDataLoader/ ${ROOT_DIRECTORY}/opasDataLoader/
COPY ./app/opasDataUpdateStat/ ${ROOT_DIRECTORY}/opasDataUpdateStat/
COPY ./app/opasEndnoteExport/ ${ROOT_DIRECTORY}/opasEndnoteExport/
COPY ./app/opasGoogleMetadataExport/ ${ROOT_DIRECTORY}/opasGoogleMetadataExport/
COPY ./app/opasPushSettings/ ${ROOT_DIRECTORY}/opasPushSettings/
COPY ./app/opasSiteMapper/ ${ROOT_DIRECTORY}/opasSiteMapper/
COPY ./app/opasDatabaseArchival/ ${ROOT_DIRECTORY}/opasDatabaseArchival/

RUN mkdir -p ${ROOT_DIRECTORY}/opasDataLoader/data_update_logs

RUN apt-get update && apt-get install -y lsb-release inetutils-tools
RUN apt-get install -y default-mysql-client

# Copy runner
COPY ./dataUtility/runner.sh ${ROOT_DIRECTORY}/runner.sh

CMD ["bash", "runner.sh"]