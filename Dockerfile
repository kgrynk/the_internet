FROM mcr.microsoft.com/playwright/python:v1.64.1-noble

USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Keep dependency installation cached when only tests change.
COPY requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir -r /tmp/requirements.txt \
    && python -m pip check

# Jenkins or docker run mounts the current test sources here at runtime.
WORKDIR /work
