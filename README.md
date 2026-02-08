# 🦥 LazyAgents

> Let your agents do the work while you vibe.

**LazyAgents** is an open-source, self-hostable AI agent orchestration platform for indie developers. Think OpenAI Frontier, but for vibecoders.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](http://makeapullrequest.com)

---

## ✨ Features

- 🗣️ **Chat-to-Agent** - Create agents using natural language
- 🔧 **Skills System** - Reusable actions your agents can perform
- 🔗 **Integrations** - GitHub, Discord, Slack, Notion, webhooks, and more
- 🧠 **Agent Memory** - Persistent context across executions
- 📊 **Observability** - Logs, metrics, and audit trails
- 🤖 **Multi-Model** - OpenAI, Anthropic, Google, local LLMs
- 🐳 **Self-Hostable** - Docker Compose, runs anywhere
- 🌙 **Dark Mode** - Because we're not savages

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- An API key for at least one LLM provider

### Installation

```bash
# Clone the repo
git clone https://github.com/lazydevtools/lazy-agents.git
cd lazy-agents

# Copy environment template
cp .env.example .env

# Add your API keys to .env
nano .env

# Start everything
docker compose up -d

# Open the dashboard
open http://localhost:3000
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Web Dashboard                         │
│                  (Next.js + React)                       │
└─────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────┐
│                     API Server                           │
│                (Python + FastAPI)                        │
└─────────────────────────────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Agent Runtime│  │   Database   │  │  Job Queue   │
│  (LangGraph) │  │   (SQLite)   │  │   (Redis)    │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [PRD.md](./PRD.md) | Product Requirements Document |
| [docs/getting-started.md](./docs/getting-started.md) | Full setup guide |
| [docs/agents.md](./docs/agents.md) | Creating and managing agents |
| [docs/skills.md](./docs/skills.md) | Built-in and custom skills |
| [docs/integrations.md](./docs/integrations.md) | Connecting external services |
| [docs/api.md](./docs/api.md) | REST API reference |
| [docs/MCP_INTEGRATION_PLAN.md](./docs/MCP_INTEGRATION_PLAN.md) | Universal Integration Architecture |

---

## 🛠️ Development

### Local Development Setup

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

### Project Structure

```
lazy-agents/
├── frontend/          # Next.js dashboard
│   ├── app/           # App router pages
│   ├── components/    # React components
│   └── lib/           # Utilities
├── backend/           # Python API server
│   ├── app/           # FastAPI application
│   │   ├── api/       # Route handlers
│   │   ├── core/      # Config, security
│   │   ├── models/    # Data models
│   │   ├── services/  # Business logic
│   │   └── skills/    # Skill implementations
│   └── tests/         # Test suite
├── docker/            # Docker configurations
├── docs/              # Documentation
└── scripts/           # Utility scripts
```

---

## 🗺️ Roadmap

- [x] Project foundation
- [ ] Agent CRUD API
- [ ] Chat-based agent creation
- [ ] Skills system
- [ ] GitHub integration
- [ ] Discord integration
- [ ] Web dashboard
- [ ] Scheduling (cron)
- [ ] Multi-model support
- [ ] CLI tool
- [ ] Skill marketplace
- [ ] MCP Integration (Model Context Protocol) 🚀

See [PRD.md](./PRD.md) for the full roadmap.

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](./CONTRIBUTING.md) first.

```bash
# Fork the repo
# Create your feature branch
git checkout -b feature/amazing-feature

# Commit your changes
git commit -m 'Add amazing feature'

# Push to the branch
git push origin feature/amazing-feature

# Open a Pull Request
```

---

## 📜 License

MIT License - see [LICENSE](./LICENSE) for details.

---

## 🙏 Acknowledgments

- Inspired by [OpenAI Frontier](https://openai.com/frontier)
- Built with [LangGraph](https://langchain-ai.github.io/langgraph/)
- Part of the [Lazy Dev Tools](https://lazydevtools.com) family

---

<p align="center">
  Made with 🦥 by lazy developers, for lazy developers
</p>
