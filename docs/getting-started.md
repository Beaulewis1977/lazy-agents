# Getting Started with LazyAgents

This guide will help you set up and run LazyAgents locally.

## Prerequisites

- **Docker & Docker Compose** (recommended)
- **OR** for manual setup:
  - Python 3.11+
  - Node.js 20+
  - Redis (optional)

## Quick Start with Docker

```bash
# Clone the repository
git clone https://github.com/lazydevtools/lazy-agents.git
cd lazy-agents

# Copy environment template
cp .env.example .env

# Edit .env and add your API keys
nano .env  # At minimum, add OPENAI_API_KEY

# Start all services
docker compose up -d

# View logs
docker compose logs -f

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

## Configuration

Edit `.env` to configure:

### Required
- `OPENAI_API_KEY` - Your OpenAI API key

### Optional LLM Providers
- `ANTHROPIC_API_KEY` - Anthropic/Claude API key
- `GOOGLE_API_KEY` - Google AI API key
- `OLLAMA_BASE_URL` - URL for local Ollama instance

### Optional Integrations
- `GITHUB_TOKEN` - Personal access token for GitHub
- `DISCORD_BOT_TOKEN` - Discord bot token
- `SLACK_BOT_TOKEN` - Slack bot token

## Verify Installation

1. Open http://localhost:3000 for the dashboard
2. Open http://localhost:8000/docs for API documentation
3. Open http://localhost:8000/health for health check

## Next Steps

- [Create your first agent](./agents.md)
- [Connect integrations](./integrations.md)
- [Browse available skills](./skills.md)
