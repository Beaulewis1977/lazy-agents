# Getting Started with LazyAgents

This guide will help you run LazyAgents on a single VM with production-safe defaults.

## Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** for manual setup:
  - Python 3.11+
  - Node.js 20+
  - Redis (optional)

## Quick Start (Single-VM Production Profile)

```bash
# Clone the repository
git clone https://github.com/lazydevtools/lazy-agents.git
cd lazy-agents

# Copy environment template
cp .env.example .env

# Edit .env and set secure values
nano .env
# Required: SECRET_KEY (strong random), API_KEY, and at least one LLM provider key

# Validate merged compose config (optional, recommended)
docker compose -f docker-compose.yml -f compose.production.yaml config > /tmp/lazy-agents.compose.merged.yaml

# Start production profile
docker compose -f docker-compose.yml -f compose.production.yaml up -d

# View logs
docker compose -f docker-compose.yml -f compose.production.yaml logs -f

# Open the dashboard
open http://localhost:3000
```

## Manual Development Setup

### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run the dev server
npm run dev
```

## Required Production Configuration

In `.env`, these values are required for non-development startup:
- `APP_ENV=production`
- `APP_DEBUG=false`
- `SECRET_KEY=<strong random value>` (at least 32 chars, not default)
- `API_KEY=<random API key>` (used for protected API routes)
- At least one provider key, such as `OPENAI_API_KEY`

If `APP_ENV` is not `development`, backend startup fails fast when `SECRET_KEY` or `API_KEY` is insecure/missing.

### Optional LLM Providers
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic/Claude API key
- `GOOGLE_API_KEY` - Google AI API key
- `OLLAMA_BASE_URL` - URL for local Ollama instance

### Optional Integrations
- `GITHUB_TOKEN` - Personal access token for GitHub
- `DISCORD_BOT_TOKEN` - Discord bot token
- `SLACK_BOT_TOKEN` - Slack bot token

## Verify Installation Baseline

Run these checks after startup:

```bash
# Backend health
curl -sS http://localhost:8000/health

# Backend readiness (includes database check)
curl -sS http://localhost:8000/health/ready

# Dashboard (expect HTTP 200)
curl -I http://localhost:3000
```

Expected:
- `/health` returns `"status":"healthy"`
- `/health/ready` returns `"status":"ready"`
- Dashboard responds with HTTP `200`

## Troubleshooting

- **Backend exits immediately**
  - Check `.env` values for `APP_ENV`, `APP_DEBUG`, `SECRET_KEY`, and `API_KEY`.
  - In production mode, insecure/missing values fail startup by design.
- **Dashboard loads but API calls fail with 401**
  - Ensure API requests include `X-API-Key` matching `.env` `API_KEY`.
- **Compose command fails**
  - Ensure Docker Compose v2 is installed and available as `docker compose`.

## Next Steps

- [Create your first agent](./agents.md)
- [Connect integrations](./integrations.md)
- [Browse available skills](./skills.md)
