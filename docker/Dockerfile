# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Metadata
LABEL maintainer="Nabil-Fareed Alikhan <nabil@happykhan.com>"
LABEL description="A bioinformatics tool for quality control based on species criteria"
LABEL version="1.1.1"

# Set the working directory in the container
WORKDIR /app

# Copy only necessary files for installation first (better caching)
COPY pyproject.toml README.md LICENSE ./
COPY speccheck/ ./speccheck/

# Install the package (creates 'speccheck' command)
RUN pip install --no-cache-dir -e .

# Copy templates and criteria
COPY templates/ ./templates/
COPY criteria.csv ./criteria.csv

# Create directories for data
RUN mkdir -p /data /output

# Declare volumes
VOLUME ["/data", "/output"]

# Set the working directory for data processing
WORKDIR /data
