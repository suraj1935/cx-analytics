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
