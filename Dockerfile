FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir playwright
RUN python -m playwright install --with-deps chromium

COPY scraper.py /app/scraper.py
COPY sample-urls.txt /app/sample-urls.txt

CMD ["sleep", "infinity"]
