FROM python:3.12-slim
WORKDIR /AstrBot

COPY . /AstrBot/

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc build-essential python3-dev libffi-dev libssl-dev \
        ca-certificates bash ffmpeg git ripgrep curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir socksio pilk

EXPOSE 6185

CMD ["bash", "start.sh"]
