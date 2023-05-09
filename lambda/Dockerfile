ARG LAMBDA_HANDLER_PATH

FROM public.ecr.aws/lambda/python:3.7

# Install the function's dependencies using file requirements.txt
# from your project folder.
COPY ./requirements.txt  .
RUN  pip3 install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY $LAMBDA_HANDLER_PATH ${LAMBDA_TASK_ROOT}

# Copy local deps
COPY ./app/libs/ ${LAMBDA_TASK_ROOT}/libs/
COPY ./app/config/ ${LAMBDA_TASK_ROOT}/config/

# Copy OPAS tools
COPY ./app/opasDataLoader/ ${LAMBDA_TASK_ROOT}/opasDataLoader/
COPY ./app/opasDataUpdateStat/ ${LAMBDA_TASK_ROOT}/opasDataUpdateStat/
COPY ./app/opasEndnoteExport/ ${LAMBDA_TASK_ROOT}/opasEndnoteExport/
COPY ./app/opasGoogleMetadataExport/ ${LAMBDA_TASK_ROOT}/opasGoogleMetadataExport/
COPY ./app/opasPushSettings/ ${LAMBDA_TASK_ROOT}/opasPushSettings/
COPY ./app/opasSiteMapper/ ${LAMBDA_TASK_ROOT}/opasSiteMapper/

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "index.handler" ]