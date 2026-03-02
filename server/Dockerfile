FROM python:3.12-slim

WORKDIR /app/server

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && rm -rf /var/lib/apt/lists/*

# Python deps (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy server code
COPY . .

# Create data/logs dirs
RUN mkdir -p data logs

# Non-root user for security
RUN useradd -m -r jarvis && chown -R jarvis:jarvis /app
USER jarvis

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run
CMD ["python", "main.py"]
