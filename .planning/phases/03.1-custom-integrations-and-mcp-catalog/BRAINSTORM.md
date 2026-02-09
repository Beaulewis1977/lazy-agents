# Phase 3.1 Brainstorm: Custom Integration Types and MCP JSON Import

**Status:** Ideas captured, needs discussion before planning
**Date:** 2026-02-08

## Core Ideas

### 1. Pre-built Integration Catalog (Toggle-on)

Ship a catalog of known integration types users can browse and enable. Each preset defines credential schema, icon, and validation rules. User picks one, fills in credentials, done.

**Named so far:**
- Slack
- Linear
- Telegram
- OpenClaw
- *(User has more to add)*

**Existing types in codebase:** GitHub, Discord, Slack, Notion, Webhook, plus model providers (OpenAI, Anthropic, Google, Ollama, Groq)

**Open questions:**
- How many integrations ship in v1 catalog?
- What metadata per catalog entry? (icon, description, credential fields, docs URL, category?)
- Categories/grouping? (Communication, Project Management, AI/Models, Custom, etc.)
- Does "toggle on" mean one-click enable or enable + configure credentials?
- Can users still create fully custom integration types not in the catalog?

### 2. MCP Server Preset Catalog (Toggle-on)

Similar catalog but for MCP servers. Pre-filled command/args/env patterns for common MCP servers. User toggles one on and fills in any required env vars.

**Open questions:**
- Which MCP servers to include as presets?
- How to keep presets current as MCP ecosystem evolves?
- Does toggling on auto-start the server or just create the config?
- Where do presets live? (hardcoded JSON, fetched from remote, user-contributed?)

### 3. MCP JSON Config Import

Let users paste or upload MCP config JSON (e.g. from `claude_desktop_config.json`) and have the platform create server entries automatically.

**Open questions:**
- Which JSON formats to support? (Claude Desktop format, others?)
- Import as one-shot or keep synced?
- How to handle env vars / secrets in imported JSON?
- Bulk import (whole config file) vs single server import?

## Current System Context

- `Integration` model has freeform `type` string field, no catalog validation
- Integration types endpoint (`integrationsAPI.types()`) already returns a list — could be extended with catalog metadata
- MCP servers are fully CRUD with lifecycle management (Phase 2 complete)
- Frontend has "Available Integrations" grid that shows types with icons

## Discussion Needed

- Full list of integrations to include
- Full list of MCP server presets to include
- UX flow for catalog browsing (cards grid? categories? search?)
- Whether custom/user-defined types coexist with catalog
- Priority ordering if this becomes multiple plans

---
*To resume: `/brainstorming Phase 3.1 scope` and reference this file*
