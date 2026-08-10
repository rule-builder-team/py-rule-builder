FROM python:3.11-slim

WORKDIR /app

# Prevent Python from writing .pyc files and enable instant log streaming
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Set PYTHONPATH so Python can resolve imports from src
ENV PYTHONPATH=/app

# Start the Python application
CMD ["python", "-m", "src.main"]