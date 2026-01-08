# Use Python 3.10 slim image for lightweight footprint
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# Using --no-install-recommends to minimize image size
# Clean up apt cache to reduce image size and avoid Hash Sum mismatch errors
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements.txt first for Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose the application port
EXPOSE 5000

# Environment variables can be passed via docker-compose.yml or --env-file
# Example: ENV DB_HOST=localhost
# For database credentials, use --env-file or docker-compose environment section

# Run the Flask application
# Ensure the app binds to the specified host and port (127.0.0.1:5500)
# Note: For production, consider using gunicorn instead of Flask's development server
CMD ["python", "app.py"]
