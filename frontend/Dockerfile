# Use an official Node runtime as a parent image
FROM node:20-alpine

# Set the working directory in the container
WORKDIR /app

# Copy package.json and package-lock.json (or yarn.lock)
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend application code
COPY . .

# Expose the port the Vite dev server runs on (default is 5173)
EXPOSE 5173

# Define the command to run the Vite dev server
# Use --host to make it accessible outside the container
CMD ["npm", "run", "dev", "--", "--host"]