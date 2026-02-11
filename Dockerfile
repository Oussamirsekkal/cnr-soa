FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all service files
COPY main.py .
COPY service_etat_civil.py .
COPY service_cnas.py .

# Expose all possible ports
EXPOSE 8000 8001 8002

# Default command (will be overridden by docker-compose)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]