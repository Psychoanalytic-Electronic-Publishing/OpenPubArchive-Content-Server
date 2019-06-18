FROM python:2.7-alpine

COPY . .

RUN apk add --update --no-cache --virtual .build-deps \
        g++ \
        python-dev \
        libxml2 \
        libxml2-dev && \
    apk add libxslt-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

#COPY . .
CMD ["sh"]