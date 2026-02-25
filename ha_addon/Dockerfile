ARG BUILD_FROM=ghcr.io/hassio-addons/base:14.3.2
FROM ${BUILD_FROM}

# Install Python + pip dependencies
RUN apk add --no-cache python3 py3-pip && \
    pip3 install --no-cache-dir flask requests

# Copy the web application
COPY app/ /app/

WORKDIR /app

# Copy the startup script
COPY run.sh /run.sh
RUN chmod +x /run.sh

CMD ["/run.sh"]
