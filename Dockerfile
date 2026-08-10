FROM node:20-alpine

# Install Python 3 and pip
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Create a virtual environment and update PATH
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements.txt and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Node.js configurations and install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application files
COPY . .

EXPOSE 3000

# Start the application
CMD ["npx", "tsx", "main/server.ts"]