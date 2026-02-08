# MCP Integration Plan for LazyAgents

## Objective
Enable LazyAgents to connect to and utilize any standard **Model Context Protocol (MCP)** server. This transforms the platform from having a fixed set of integrations to an extensible ecosystem where users can plug in tools like Linear, Obsidian, PostgreSQL, Filesystem, and more simply by providing a command or URL.

## Architecture

### 1. Database Schema
We need a new table to store MCP server configurations.

**Table: `mcp_servers`**
- `id`: UUID (Primary Key)
- `name`: String (e.g., "Linear", "Obsidian")
- `description`: Text (Optional)
- `command`: String (e.g., `npx`, `python`, `uv`)
- `args`: JSON List (e.g., `["-y", "@modelcontextprotocol/server-linear"]`)
- `env`: JSON Dict (Environment variables like `LINEAR_API_KEY`)
- `enabled`: Boolean (default: true)
- `status`: String (stopped, starting, running, error)
- `tools_detected`: JSON (Cache of tool definitions discovered from this server)
- `created_at`: DateTime
- `updated_at`: DateTime

### 2. Backend Architecture (`backend/app/mcp/`)

#### A. MCP Server Manager (`manager.py`)
- Responsible for the lifecycle of MCP server processes.
- **Start**: Spawns the subprocess (e.g., `subprocess.Popen`) with the correct environment.
- **Stop**: Terminates the subprocess.
- **Health Check**: Monitors if the process is alive.
- **Stdio/SSE Handling**: Manages the communication, preferably using an existing Python MCP SDK or a lightweight implementation to handle JSON-RPC over stdio.

#### B. Tool Registry (`registry.py`)
- When a server starts, the backend queries `tools/list`.
- The detected tools map to LazyAgent "Skills" dynamically.
- **Naming Convention**: `mcp::{server_name}::{tool_name}` (e.g., `mcp::linear::create_issue`).

#### C. Runtime Integration (`executor.py`)
- When an Agent calls a tool like `mcp::linear::create_issue`:
  1. The `SkillsExecutor` identifies the prefix `mcp::`.
  2. Routes the call to the active process managed by `MCPServerManager`.
  3. Awaits the JSON-RPC response `tools/call`.
  4. Returns the result to the LLM.

### 3. API Endpoints (`backend/app/api/mcp.py`)
- `GET /mcp/servers`: List configured servers.
- `POST /mcp/servers`: Add a new server config.
- `GET /mcp/servers/{id}`: Get details and status.
- `PUT /mcp/servers/{id}`: Update config.
- `POST /mcp/servers/{id}/restart`: Force restart.
- `POST /mcp/servers/{id}/sync`: Force tool rediscovery.
- `DELETE /mcp/servers/{id}`: Remove server.

### 4. Frontend UI (`frontend/app/integrations/mcp/`)

#### A. Server List (Dashboard)
- A specialized section in the "Integrations" or "Settings" page.
- Lists all configured servers with status indicators (Green/Red dots).
- Actions: Edit, Delete, Restart.

#### B. Configuration Form
- **Presets**: Dropdown for common servers ("Linear", "Postgres", "Obsidian").
  - Selecting "Linear" pre-fills `npx -y @modelcontextprotocol/server-linear`.
- **Custom**: Manual entry for Command, Args, and Env Vars.
- **Environment Helper**: Secure inputs for API Keys (masked).

#### C. Tool Browser
- A view to see "What tools does this server provide?"
- Lists discovered tools (e.g., `linear_create_issue`) and their schemas.

### 5. Packaging & Distribution
To ensure portability (making it work on other users' machines):
- **Dependencies**: The Docker image must include `nodejs` and `npm` (for `npx` servers) and `python` (for python servers).
- **Environment**: The `manager.py` must handle path resolution correctly across OS types (Linux/Mac/Windows), though Docker standardizes this.

## Implementation Steps

### Phase 1: Backend Foundation
1.  Add `sqlalchemy` model for `MCPServer`.
2.  Implement `MCPServerManager` to spawn text-based stdio processes.
3.  Implement basic JSON-RPC handshake (`initialize`, `tools/list`).
4.  Create API endpoints for CRUD.

### Phase 2: Runtime Connection
1.  Update `SkillLoader` to include dynamic MCP tools.
2.  Update `SkillsExecutor` to route calls to the MCP Manager.

### Phase 3: Frontend Interface
1.  Build the Management UI.
2.  Add status polling (WebSocket or SWR).

### Phase 4: Testing & Packaging
1.  Verify with "Hello World" MCP server.
2.  Verify with a complex server (Linear or Obsidian).
3.  Update Dockerfile to support Node/Python runtimes for subprocesses.

## Example User Flow (Adding Obsidian)
1.  User goes to **Settings > Integrations**.
2.  Clicks **"Add MCP Server"**.
3.  Selects **"Obsidian (Local)"**.
4.  Enters Command: `npx -y @modelcontextprotocol/server-obsidian` (or equivalent).
5.  Enters Args: `/path/to/my/vault`.
6.  Clicks **Save**.
7.  Backend starts the process, handshakes, and finds tools: `read_note`, `append_note`, `search_vault`.
8.  User goes to **Agents**, selects "Researcher Agent".
9.  In "Skills", selects "Obsidian".
10. Agent runs: "Read my daily note from yesterday..." -> Calls `obsidian_read_note`.
