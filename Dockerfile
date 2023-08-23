FROM python:3.11-slim

LABEL maintainer="Mehrad Dadgar <mehraddadgar116@gmail.com>"
LABEL description="Async HTTP service uptime monitor with Telegram and Discord alerting"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

RUN useradd -u 10001 -m -s /bin/bash prober && \
    chown -R prober:prober /app

USER prober

ENTRYPOINT ["api-uptime-probe"]
CMD ["-c", "/etc/api-uptime-probe/config.yaml"]
