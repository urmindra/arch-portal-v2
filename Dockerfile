# Use Python 3.11-slim as base image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python requirements
RUN pip install --no-cache-dir streamlit psycopg2-binary pyvis

# Expose port 5000
EXPOSE 5000

# Set entry point
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=5000", "--server.address=0.0.0.0"]
