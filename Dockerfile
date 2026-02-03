FROM python:3.11-slim

WORKDIR /app

# Install Flask
RUN pip install --no-cache-dir flask

# Copy application files
COPY app.py .
COPY templates/ templates/

# Create data directory for SQLite database
RUN mkdir -p /data

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
