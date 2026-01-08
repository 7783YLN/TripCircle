# Use an official lightweight Python image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port (Render uses $PORT environment variable)
EXPOSE 10000

# Run the app using Gunicorn
# app:app refers to app.py and the Flask instance named 'app'
CMD ["gunicorn", "-b", "0.0.0.0:10000", "app:app"]
