# Use official Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copy requirements if exists
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set environment variables for Flask (Cloud Run expects listening on 0.0.0.0)
ENV FLASK_APP=main.py
ENV FLASK_RUN_PORT=8080
ENV PORT=8080

# Expose Cloud Run port
EXPOSE 8080

# Start the app
CMD ["python", "main.py"]