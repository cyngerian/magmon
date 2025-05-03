# Stage 1: Build the React application
FROM node:20-alpine AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
# Use package*.json to capture both files
COPY package*.json ./

# Install dependencies using npm ci for cleaner installs
# Use --only=production if you have separate devDependencies not needed for the build
# RUN npm ci --only=production
# If build scripts require devDependencies, use:
RUN npm ci

# Copy the rest of the application source code
COPY . .

# Build the application for production
# Ensure your package.json has a "build" script (e.g., "vite build")
RUN npm run build

# Stage 2: Serve the built application with Nginx
FROM nginx:stable-alpine

# Remove default Nginx configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom Nginx configuration from the context
# This file configures Nginx to serve the React app and proxy API requests
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy the built static assets from the 'builder' stage
# The build output directory might be 'dist', 'build', etc. - adjust if needed
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port 80 for Nginx
EXPOSE 80

# Nginx image's default command starts the server, so no CMD needed here
# CMD ["nginx", "-g", "daemon off;"] is the default