# LazyAgents - Product Requirements Document

> **Version:** 1.0.0
> **Last Updated:** 2026-02-07
> **Status:** Draft
> **Author:** LazyDevTools

---

## Executive Summary

**LazyAgents** is an open-source, self-hostable AI agent orchestration platform designed for indie developers, hobbyists, and small teams. It brings enterprise-grade agent management capabilities (inspired by OpenAI Frontier) to the individual developer—without the complexity, cost, or corporate overhead.

### Vision Statement
*"Let your agents do the work while you vibe."*

### Target Users
- Solo developers automating personal workflows
- Indie hackers building AI-powered products
- "Vibecoders" who want AI to handle repetitive tasks
- Small teams needing lightweight agent infrastructure
- Developers learning AI agent development

---

## Problem Statement

### The Gap in the Market

| Enterprise Solutions | Current Indie Options |
|---------------------|----------------------|
| OpenAI Frontier, Azure AI, Google Vertex | Raw API calls, one-off scripts |
| $10k-100k+/year | Free but unmanaged |
| SOC 2, complex IAM | No observability |
| Dedicated support | Stack Overflow |

**The Problem:** There's no middle ground. Individual developers either:
1. Pay enterprise prices for features they don't need
2. Build fragile, unobservable agent scripts from scratch
3. Piece together multiple tools (LangChain + cron + logging + dashboards)

**LazyAgents fills this gap** by providing a unified, self-hostable platform that makes agent management *feel* enterprise-grade while remaining accessible to solo developers.

---

## Core Features

### 1. Agent Management

#### 1.1 Chat-Based Agent Creation
- Create agents using natural language: *"Make an agent that monitors my GitHub repo and summarizes new issues in Discord every morning"*
- LLM interprets intent and generates agent configuration
- No code required for basic agents; full code access for power users

#### 1.2 Agent Dashboard
- View all agents, their status, and last activity
- Start/stop/pause agents
- View execution history and logs
- Edit agent configuration

#### 1.3 Agent Identity & Permissions
- Each agent has a unique ID and name
- Scoped permissions per integration (read-only GitHub, write Discord, etc.)
- Secret management for API keys and tokens

---

### 2. Skills System

#### 2.1 Pre-built Skills
Skills are reusable actions agents can perform:
- `github.list_issues` - List issues from a repository
- `github.create_issue` - Create a new issue
- `discord.send_message` - Send a message to a channel
- `notion.create_page` - Create a Notion page
- `http.request` - Make arbitrary HTTP requests
- `file.read` / `file.write` - Local file operations
- `shell.execute` - Run shell commands (sandboxed)

#### 2.2 Custom Skills
- Define skills in YAML or JSON
- Skills can call other skills (composition)
- Skills can include LLM reasoning steps
- Import/export skills for sharing

#### 2.3 Skill Marketplace (Future)
- Browse community-created skills
- One-click install
- Version management

---

### 3. Integrations

#### 3.1 First-Party Integrations (MVP)
| Integration | Read | Write | Webhooks |
|-------------|------|-------|----------|
| GitHub | ✅ | ✅ | ✅ |
| Discord | ✅ | ✅ | ✅ |
| Slack | ✅ | ✅ | ✅ |
| Notion | ✅ | ✅ | ❌ |
| Webhooks (generic) | ✅ | ✅ | ✅ |
| Local Files | ✅ | ✅ | N/A |
| Shell/Terminal | ✅ | ✅ | N/A |

#### 3.2 Integration Framework
- Standardized integration interface
- OAuth2 flow support
- API key storage
- Rate limiting and retry logic

#### 3.3 Future Integrations
- Linear, Jira (issue tracking)
- Google Workspace (Docs, Sheets, Calendar)
- Vercel, Netlify (deployments)
- Postgres, MongoDB (databases)
- Email (SMTP/IMAP)

---

### 4. Agent Runtime

#### 4.1 Execution Modes
- **On-demand:** Triggered manually or via API
- **Scheduled:** Cron-style scheduling (e.g., "every day at 9am")
- **Event-driven:** Triggered by webhooks or integration events
- **Continuous:** Long-running agents with polling

#### 4.2 Memory & Context
- Agents maintain conversation history
- Persistent memory across executions (SQLite/Postgres)
- Shared context between agents (optional)
- Memory search and retrieval

#### 4.3 Multi-Model Support
| Provider | Models |
|----------|--------|
| OpenAI | GPT-4o, GPT-4o-mini, o1, o3-mini |
| Anthropic | Claude 3.5 Sonnet, Claude 3 Opus |
| Google | Gemini 2.0 Flash, Gemini 2.0 Pro |
| Local | Ollama (Llama, Mistral, etc.) |
| OpenRouter | Any supported model |

---

### 5. Observability

#### 5.1 Logging
- Structured logs for all agent actions
- Log levels: DEBUG, INFO, WARN, ERROR
- Log retention policies
- Log search and filtering

#### 5.2 Metrics Dashboard
- Agent execution count
- Success/failure rates
- Average execution time
- Token usage and costs
- Integration call counts

#### 5.3 Audit Trail
- Every action logged with timestamp
- Who/what triggered the action
- Full request/response capture (optional)
- Export for compliance

---

### 6. User Interface

#### 6.1 Web Dashboard
- Dark mode by default (light mode available)
- Responsive design (desktop-first, mobile-friendly)
- Real-time updates via WebSocket
- Keyboard shortcuts for power users

#### 6.2 Key Pages
| Page | Purpose |
|------|---------|
| `/` | Dashboard overview |
| `/agents` | List and manage agents |
| `/agents/new` | Create new agent (chat interface) |
| `/agents/:id` | Agent detail, logs, settings |
| `/skills` | Browse and manage skills |
| `/integrations` | Connect external services |
| `/logs` | Unified log viewer |
| `/settings` | App configuration |

#### 6.3 CLI (Future)
```bash
lazy-agents list
lazy-agents run <agent-name>
lazy-agents logs <agent-name> --follow
lazy-agents create "Monitor my GitHub and..."
```

---

## Technical Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Dashboard                            │
│                    (Next.js / React + TypeScript)                │
└──────────────────────────────┬──────────────────────────────────┘
                               │ HTTP/WebSocket
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API Server                              │
│                      (FastAPI / Python)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Agents    │  │   Skills    │  │   Integr.   │              │
│  │   Router    │  │   Router    │  │   Router    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└──────────────────────────────┬──────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   Agent Runtime  │ │     Database     │ │   Job Queue      │
│   (LangGraph)    │ │ (SQLite/Postgres)│ │ (Redis/SQLite)   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Integration Layer                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐        │
│  │ GitHub │ │Discord │ │ Slack  │ │ Notion │ │Webhooks│        │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology | Rationale |
|-----------|------------|-----------|
| Frontend | Next.js 14+ (App Router) | Modern React, great DX, API routes |
| Styling | Vanilla CSS + CSS Variables | Maximum control, no dependencies |
| Backend | Python 3.11+ / FastAPI | Best LLM ecosystem, async support |
| Agent Framework | LangGraph | Flexible, well-documented |
| Database | SQLite (default) / Postgres | Zero-config start, scale when needed |
| Queue | SQLite-based (default) / Redis | Simple job scheduling |
| Auth | API Keys (default) / NextAuth | Start simple, add OAuth later |
| Container | Docker + Docker Compose | Easy self-hosting |

### Data Models

#### Agent
```python
class Agent:
    id: UUID
    name: str
    description: str
    status: Literal["active", "paused", "error"]
    model: str  # e.g., "gpt-4o"
    system_prompt: str
    skills: List[str]  # skill IDs
    integrations: List[str]  # integration IDs
    schedule: Optional[str]  # cron expression
    memory_enabled: bool
    created_at: datetime
    updated_at: datetime
```

#### Skill
```python
class Skill:
    id: str  # e.g., "github.list_issues"
    name: str
    description: str
    category: str
    parameters: Dict[str, ParameterSchema]
    integration_required: Optional[str]
    code: str  # Python function or reference
```

#### Integration
```python
class Integration:
    id: UUID
    type: str  # e.g., "github", "discord"
    name: str  # user-defined name
    credentials: EncryptedDict
    permissions: List[str]
    created_at: datetime
```

#### Execution Log
```python
class ExecutionLog:
    id: UUID
    agent_id: UUID
    trigger: Literal["manual", "schedule", "webhook", "event"]
    status: Literal["running", "success", "failed"]
    started_at: datetime
    completed_at: Optional[datetime]
    input: Dict
    output: Optional[Dict]
    error: Optional[str]
    token_usage: Optional[Dict]
    steps: List[StepLog]
```

---

## Security Considerations

### Threat Model
- **Self-hosted:** User is responsible for network security
- **Credentials:** All secrets encrypted at rest (Fernet/AES-256)
- **Sandboxing:** Shell execution in Docker containers (optional)
- **Input validation:** All user inputs sanitized
- **Rate limiting:** Prevent runaway agents

### Security Features
- API key authentication (bearer tokens)
- Encrypted credential storage
- Audit logging for all actions
- Configurable execution timeouts
- Memory limits per agent

### Out of Scope (v1)
- Multi-user/multi-tenant
- SSO/SAML
- Role-based access control
- End-to-end encryption

---

## Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [x] Project setup and scaffolding
- [ ] Database schema and migrations
- [ ] Basic API endpoints (agents CRUD)
- [ ] Agent runtime with LangGraph
- [ ] Simple web dashboard (list agents)

### Phase 2: Core Features (Weeks 3-4)
- [ ] Chat-based agent creation
- [ ] Skills system implementation
- [ ] GitHub integration
- [ ] Discord integration
- [ ] Execution logging

### Phase 3: Polish (Weeks 5-6)
- [ ] Full dashboard UI
- [ ] Scheduling (cron)
- [ ] Webhook triggers
- [ ] Multi-model support
- [ ] Docker deployment

### Phase 4: Launch (Week 7-8)
- [ ] Documentation site
- [ ] Demo video
- [ ] lazy-dev-tools integration
- [ ] Community feedback loop

### Future Phases
- CLI tool
- Skill marketplace
- More integrations
- Team/collaboration features
- Cloud hosted option

---

## Success Metrics

### Adoption
- GitHub stars (target: 500 in first month)
- Downloads/installs
- Discord community size
- Active agents running (telemetry opt-in)

### Quality
- <5 critical bugs at launch
- <2s dashboard load time
- 99% agent execution success rate
- Positive user feedback (surveys)

### Engagement
- Agents created per user
- Custom skills created
- Integrations connected
- Return user rate (weekly)

---

## Competitive Analysis

| Feature | LazyAgents | n8n | Zapier | LangFlow |
|---------|------------|-----|--------|----------|
| Self-hosted | ✅ | ✅ | ❌ | ✅ |
| Free | ✅ | ✅ | ❌ | ✅ |
| AI-native | ✅ | ❌ | ❌ | ✅ |
| Chat-to-agent | ✅ | ❌ | ❌ | ❌ |
| Multi-model | ✅ | ❌ | ❌ | ✅ |
| Agent memory | ✅ | ❌ | ❌ | ⚠️ |
| Skills system | ✅ | ⚠️ | ✅ | ❌ |
| Dev-friendly | ✅ | ⚠️ | ❌ | ⚠️ |

---

## Appendix

### Glossary
- **Agent:** An AI entity that performs tasks autonomously
- **Skill:** A reusable action or workflow an agent can execute
- **Integration:** A connection to an external service
- **Execution:** A single run of an agent
- **Memory:** Persistent context an agent retains between executions

### References
- [OpenAI Frontier Announcement](https://openai.com/index/introducing-openai-frontier/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Next.js Documentation](https://nextjs.org/docs)

### Open Questions
1. Should we support agent-to-agent communication in v1?
2. What's the right default for memory retention?
3. Should shell execution be enabled by default?
4. Pricing model for potential hosted version?

---

*This document is a living specification and will be updated as development progresses.*
