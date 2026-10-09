FROM python:3.11-bookworm@sha256:b99029c95d3d37fb1e4e76d287f7984373dca77c665885986e31b2c95260c13c
# No Claude CLI, provider SDK, API key, SSH key, or login is installed in this image.
RUN apt-get update && apt-get install -y --no-install-recommends git fonts-liberation ca-certificates \
    && rm -rf /var/lib/apt/lists/*
COPY docker/requirements.txt /tmp/replication-requirements.txt
RUN pip install --no-cache-dir -r /tmp/replication-requirements.txt
# Layout-only font substitute. We do not redistribute proprietary Arial files.
RUN mkdir /opt/replication-fonts \
    && ln -s /usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf '/opt/replication-fonts/Arial.ttf' \
    && ln -s /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf '/opt/replication-fonts/Arial Bold.ttf'
WORKDIR /package
ENTRYPOINT ["python", "analysis/reproduce.py"]
