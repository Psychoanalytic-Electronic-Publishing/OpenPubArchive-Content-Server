FROM tiangolo/uvicorn-gunicorn-fastapi:python3.7-2021-10-02
COPY ./requirements.txt /app/requirements.txt
RUN pip install --trusted-host pypi.python.org -r /app/requirements.txt
RUN pip install fastapi
COPY ./app /app
RUN chmod 750 /app
ENV LOG_LEVEL=warning
ENV ACCESS_LOG=
ENV TIMEOUT=180
ENV GRACEFUL_TIMEOUT=180
# Expose ports
EXPOSE 80