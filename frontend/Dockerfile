<<<<<<< HEAD
# Frontend Dockerfile – builds the Vite React app and serves it via nginx
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
# Build the production assets
RUN npm run build

# Stage 2 – serve with nginx
FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
# Expose port 80 for the web server
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
=======
FROM node:20-slim

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies
RUN npm install

# Copy application code
COPY . .

EXPOSE 3000

# Run Vite dev server exposed to 0.0.0.0
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
>>>>>>> 9fb4312dc700c99c624d5fce54210a36a09db088
