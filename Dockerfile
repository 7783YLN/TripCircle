# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies first
COPY requirements.txt .

# Install dependencies + gunicorn
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn

# Copy app files
COPY . .

# Expose Flask port
EXPOSE 5000

# Run app with Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
