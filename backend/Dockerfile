FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    ca-certificates \
    libcurl4-openssl-dev \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv --no-cache-dir

COPY pyproject.toml ./
RUN uv export --no-dev --no-hashes --format requirements-txt -o requirements.txt \
    && uv pip install --system --no-cache -r requirements.txt

COPY . .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]