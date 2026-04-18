# Use official Python image
FROM python:3.10-slim

# Set up working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y curl wget gnupg ca-certificates libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxrandr2 libxdamage1 libgbm1 libasound2 libpangocairo-1.0-0 libpango-1.0-0

# Install Playwright and Python dependencies
RUN pip install --upgrade pip
RUN pip install playwright

# Install Playwright browsers
RUN playwright install

RUN playwright install-deps

# Allow bash to run interactively
#CMD ["/bin/bash"]