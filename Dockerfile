FROM python:3.11-slim

WORKDIR /app

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY templates/ templates/

# Create data directory for SQLite database
RUN mkdir -p /data

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]

