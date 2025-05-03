# MagMon - Deployment Plan (AWS Elastic Beanstalk)

This document outlines the high-level steps for deploying the MagMon application to AWS Elastic Beanstalk using Docker containers.

## Target Architecture

*   **Platform:** AWS Elastic Beanstalk (Docker platform)
*   **Database:** AWS RDS (PostgreSQL instance)
*   **Containers:**
    *   One container for the Flask backend (running with Gunicorn/Waitress).
    *   One container for the React frontend (static files served by Nginx).
*   **Deployment:** Elastic Beanstalk handles provisioning EC2 instances, load balancing, auto-scaling (optional), and application updates.

## Prerequisites

1.  AWS Account setup.
2.  AWS CLI installed and configured locally (optional but helpful).
3.  EB CLI installed locally (optional but helpful for command-line deployment).
4.  Docker installed locally.

## Deployment Steps

### 1. Containerize the Application

*   **Backend (`backend/Dockerfile`):**
    *   Use an official Python base image (e.g., `python:3.11-slim`).
    *   Set working directory (`/app`).
    *   Copy `requirements.txt`.
    *   Install dependencies (`pip install --no-cache-dir -r requirements.txt`).
        *   **TODO:** Add a production WSGI server (e.g., `gunicorn` or `waitress`) to `requirements.txt`.
    *   Copy the rest of the backend code.
    *   Expose the port the WSGI server will run on (e.g., 8000).
    *   Define the `CMD` to run the WSGI server (e.g., `gunicorn --bind 0.0.0.0:8000 wsgi:app`).
*   **Frontend (`frontend/Dockerfile`):**
    *   Use a multi-stage build.
    *   **Stage 1 (Build):**
        *   Use a Node.js base image (e.g., `node:18-alpine`).
        *   Set working directory (`/app`).
        *   Copy `package.json` and `package-lock.json`.
        *   Run `npm ci` (clean install).
        *   Copy the rest of the frontend code.
        *   Run `npm run build` to generate static files in `/app/dist`.
    *   **Stage 2 (Serve):**
        *   Use an Nginx base image (e.g., `nginx:stable-alpine`).
        *   Copy the static build output from Stage 1 (`/app/dist`) to Nginx's HTML directory (e.g., `/usr/share/nginx/html`).
        *   **TODO:** Add an Nginx configuration file (`nginx.conf`) to handle serving static files and potentially proxying API requests if not using separate containers/load balancer rules. Copy this config into the image.
        *   Expose port 80.
*   **Docker Compose (`docker-compose.yml` - for local testing):**
    *   Update to define `backend` and `frontend` services based on the Dockerfiles.
    *   Keep the `db` service for local testing.
    *   Ensure ports are mapped correctly.
    *   Test thoroughly locally: `docker-compose up --build`.

### 2. Prepare for AWS

*   **RDS Database:**
    *   Create a PostgreSQL instance on AWS RDS.
    *   Configure security groups to allow connections from the Elastic Beanstalk environment.
    *   Note the DB endpoint, username, password, and database name.
*   **Elastic Beanstalk Application:**
    *   Create an Elastic Beanstalk application via the AWS console or EB CLI.
*   **Environment Variables:**
    *   Plan how to securely provide `DATABASE_URL` and `SECRET_KEY` to the backend container running on Beanstalk (e.g., using Beanstalk environment properties, potentially integrated with AWS Secrets Manager for production). Set `FLASK_CONFIG=production`.

### 3. Deploy to Elastic Beanstalk

*   **Option A (EB CLI):**
    *   Navigate to the project root directory.
    *   Initialize EB CLI: `eb init -p Docker <YourAppName>`
    *   Create environment: `eb create <YourEnvironmentName> --database.engine postgres --database.instance <RDSInstanceType> ...` (Configure RDS via CLI or link existing).
    *   Configure environment variables: `eb setenv VAR_NAME=value ...`
    *   Deploy: `eb deploy`
*   **Option B (AWS Console - Zip Upload):**
    *   Create a `.zip` archive containing:
        *   `backend/` directory (with its Dockerfile)
        *   `frontend/` directory (with its Dockerfile)
        *   `docker-compose.yml` (Beanstalk can use this to understand multi-container setups) OR a `Dockerrun.aws.json` file (v2 for multi-container).
    *   Create a Beanstalk environment via the console, selecting the "Multi-container Docker" platform.
    *   Upload the `.zip` file as the application version.
    *   Configure environment variables and RDS settings through the console.
    *   Launch/Update the environment.

### 4. Post-Deployment

*   **Verify:** Check Beanstalk environment health and logs. Access the application URL.
*   **DNS:** Configure custom domain name (optional).
*   **HTTPS:** Configure HTTPS using AWS Certificate Manager and Load Balancer listeners (Beanstalk often handles this).
*   **Monitoring/Alerts:** Set up CloudWatch monitoring and alarms.

## Key Considerations

*   **WSGI Server:** Flask's built-in server is not suitable for production. Gunicorn or Waitress must be used.
*   **Static Files:** Nginx is typically used to serve the React build output efficiently.
*   **Database:** Use RDS for managed PostgreSQL.
*   **Security:** Securely manage secrets (DB credentials, SECRET_KEY). Configure Security Groups appropriately. Use HTTPS.
*   **Logging:** Configure application logging to be sent to CloudWatch.
*   **CI/CD:** For future updates, set up a CI/CD pipeline (e.g., using AWS CodePipeline, GitHub Actions) to automate builds and deployments.
