FROM python:3.12-slim
WORKDIR /app

# Install system dependencies including Node.js for bot + frontend
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl nodejs npm && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (cached layer)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL app code first
COPY . /app

# Install Node.js bot dependencies
RUN cd /app/telegram-ai-app && npm install --production 2>/dev/null || true

# Install frontend dependencies and build
RUN cd /app/telegram-mini-app && npm install 2>/dev/null || true
RUN cd /app/telegram-mini-app && npm run build 2>/dev/null || true

# Create data directory
RUN mkdir -p /app/data

# Expose web server port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Start script
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]
