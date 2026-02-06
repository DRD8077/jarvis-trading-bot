Deployment & Secrets Checklist
==============================

Required environment variables / GitHub secrets
- `DOCKERHUB_USERNAME` — Docker Hub username
- `DOCKERHUB_TOKEN` — Docker Hub access token (or password)
- `VPS_HOST` — IP or hostname of your VPS
- `VPS_USER` — SSH user for deploy on VPS
- `VPS_SSH_KEY` — Private SSH key (use as a GitHub secret; name it `VPS_SSH_KEY`)
- `VPS_DEPLOY_DIR` — Directory on VPS to copy files to (e.g. `/home/ubuntu/bot`)
- `HEALTHCHECK_URL` — Public URL to the `/health` endpoint (used by scheduled check)
- `HEALTHCHECK_TELEGRAM_TOKEN` — Bot token to send alerts from GitHub Actions
- `HEALTHCHECK_TELEGRAM_CHAT_ID` — Chat ID to receive alerts

Local `.env` (create from `.env.example`)
- `TELEGRAM_BOT_TOKEN` — Telegram bot token
- `WEBHOOK_URL` — Public webhook URL if using Telegram webhooks
- `WATCHLIST` — Optional (RELIANCE by default)

Quick commands
- Validate Docker Compose config:

```bash
docker compose config
```

- Build and run locally:

```bash
docker compose up -d --build
docker compose logs -f
```

- Check health locally (after container is running):

```bash
curl -fsS http://localhost:8000/health
```

How to add GitHub secrets using `gh` CLI

```bash
gh secret set DOCKERHUB_USERNAME --body "your-username"
gh secret set DOCKERHUB_TOKEN --body "<token>"
gh secret set VPS_HOST --body "1.2.3.4"
gh secret set VPS_USER --body "ubuntu"
gh secret set VPS_SSH_KEY --body "$(cat ~/.ssh/id_rsa)"
gh secret set VPS_DEPLOY_DIR --body "/home/ubuntu/bot"
gh secret set HEALTHCHECK_URL --body "https://your-host.example.com/health"
gh secret set HEALTHCHECK_TELEGRAM_TOKEN --body "<bot-token>"
gh secret set HEALTHCHECK_TELEGRAM_CHAT_ID --body "<chat-id>"
```

Notes
- Ensure your server has Docker Compose v2 (`docker compose`) available.
- If using Render/Railway, set environment variables in the service dashboard instead of GitHub secrets.
