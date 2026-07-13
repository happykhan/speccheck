FROM python:3.13-slim

ARG VERSION=1.3.0

LABEL maintainer="Nabil-Fareed Alikhan <nabil@happykhan.com>"
LABEL description="A bioinformatics tool for quality control based on species criteria"
LABEL version="${VERSION}"

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md LICENSE ./
COPY speccheck/ ./speccheck/

RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir .

RUN mkdir -p /data /output

VOLUME ["/data", "/output"]

WORKDIR /data

ENTRYPOINT ["speccheck"]
CMD ["--help"]
