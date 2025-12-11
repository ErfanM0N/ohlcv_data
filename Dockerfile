FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy project files
COPY . .

# Create non-root user
RUN useradd -m -u 1000 coinai && \
    chown -R coinai:coinai /app

# Create directories with proper permissions
RUN mkdir -p /app/staticfiles /app/media && \
    chown -R coinai:coinai /app/staticfiles /app/media

USER coinai

# Expose port
EXPOSE 8000