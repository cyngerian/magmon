# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# Set FLASK_DEBUG to 1 for development debugging if needed
ENV FLASK_DEBUG=0
# Point FLASK_APP to the app object in the root wsgi.py
ENV FLASK_APP=wsgi:app

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., for psycopg2)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy requirements, wsgi.py, and .env file first
# Note: Paths are relative to the build context (project root)
COPY backend/requirements.txt ./requirements.txt
COPY wsgi.py ./wsgi.py
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (specifically the backend package)
# Note: Ensure .dockerignore is set up to avoid copying unnecessary files
COPY backend/ ./backend/

# Install the local package (located in ./backend) in editable mode
# This makes imports like 'from backend.app import ...' work
RUN pip install --no-cache-dir -e ./backend

# Expose the port the app runs on
EXPOSE 5004

# Define the command to run the application using Gunicorn
# Bind to 0.0.0.0 to make it accessible outside the container
# Point to the 'app' object within the 'wsgi' module (wsgi.py at the root)
# Increase timeout to allow for potentially slow initialization
CMD ["gunicorn", "--bind", "0.0.0.0:5004", "--timeout", "120", "wsgi:app"]