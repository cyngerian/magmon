# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies if needed (e.g., for psycopg2)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies from requirements.txt first
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code (including pyproject.toml)
COPY . .

# Install the local package in editable mode to make 'app' importable
# This should use the already installed dependencies from the previous step.
RUN pip install --no-cache-dir -e .

# Expose the port the app runs on
EXPOSE 5004

# Define the command to run the application
# Use 0.0.0.0 to make it accessible outside the container
# Run Flask as a module to ensure it's found regardless of PATH specifics
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5004"]