# Gunakan Python 3.10 sebagai base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download NLTK data
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p database/wordlists \
    && mkdir -p static/uploads \
    && mkdir -p static/models

# Set environment variables
ENV FLASK_APP=run.py
ENV FLASK_DEBUG=0
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 5000

# Run the application with Gunicorn using wsgi.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "120", "wsgi:app"] 