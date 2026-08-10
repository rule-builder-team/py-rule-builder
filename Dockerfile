FROM node:20-alpine

WORKDIR /app

# Copy package manifests from src directory
COPY src/package*.json ./

# Install Node dependencies
RUN npm install

# Copy application source code
COPY . .

EXPOSE 3000

# Start the TypeScript server
CMD ["npx", "tsx", "src/main/server.ts"]