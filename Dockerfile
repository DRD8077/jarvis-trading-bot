FROM python:3.12-slim
WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . /app

# Health check via a simple python script
HEALTHCHECK --interval=60s --timeout=10s --retries=3 \
  CMD python -c "import requests; r=requests.get('https://api.telegram.org/bot'+'$TELEGRAM_BOT_TOKEN'+'/getMe'); exit(0 if r.status_code==200 else 1)" || exit 1

# Run the polling bot (NOT webhook server)
CMD ["python", "telegram_bot.py"]
