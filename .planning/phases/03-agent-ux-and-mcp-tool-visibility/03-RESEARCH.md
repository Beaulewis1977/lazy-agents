# Phase 3: Agent UX and MCP Tool Visibility - Research

**Researched:** 2026-02-08
**Domain:** Agent management UI, MCP tool visualization, Next.js App Router forms
**Confidence:** HIGH

## Summary

Phase 3 focuses on completing operator-facing agent workflows and implementing MCP tool browsing. The existing codebase has strong foundations with complete backend APIs (agents, executions, skills, integrations, MCP servers) and typed frontend API clients. The primary gaps are in the UI layer: enhanced agent list views with execution context, comprehensive agent creation/editing forms with skill/integration assignment, execution result displays, and MCP tool schema browsing.

Modern agent platforms (2026) emphasize visual builders, clear status indicators, and real-time feedback. For this phase, we'll leverage Next.js App Router with React Hook Form for complex forms, implement collapsible JSON Schema viewers for MCP tools, and add WebSocket-based real-time execution status updates. The existing design system (dark-mode first with CSS custom properties) provides all necessary components; we'll extend it with multi-select patterns and schema tree renderers.

**Primary recommendation:** Build on existing patterns (fetchAPI client, "use client" pages, DashboardLayout wrapper) and add three focused enhancements: (1) agent list with last execution summary cards, (2) agent form with skill/integration multi-select using React Hook Form, (3) MCP tool browser with collapsible JSON Schema tree view. Keep components simple and avoid introducing new dependencies beyond what's already in use.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Next.js | 16.1.6 | App Router framework | Already in use, official React framework, server component support |
| React | 19.2.3 | UI library | Already in use, stable release with useActionState for forms |
| TypeScript | strict | Type safety | Already in use, existing typed API client provides foundation |
| Tailwind CSS | v4 | Styling framework | Already in use with @theme directive, CSS-first config |
| React Hook Form | latest | Form state management | Industry standard for complex forms, minimal re-renders |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Zod | latest | Schema validation | Form validation alongside React Hook Form |
| react-json-tree | 0.18+ | JSON viewer | Displaying MCP tool schemas in tree format |
| WebSocket API | Native | Real-time updates | Execution status streaming (already used in logs tab) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| React Hook Form | Formik | RHF has better performance for large forms, smaller bundle |
| react-json-tree | custom tree renderer | Pre-built component reduces development time, handles edge cases |
| Native WebSocket | Socket.io | Native WS is simpler for existing use case, no extra dependency |

**Installation:**
```bash
npm install react-hook-form zod @hookform/resolvers react-json-tree
```

## Architecture Patterns

### Recommended Project Structure (Frontend Pages)
```
frontend/app/
├── agents/
│   ├── page.tsx              # ENHANCE: Add last execution summary
│   ├── new/page.tsx          # ENHANCE: Add skill/integration multi-select
│   ├── [id]/
│   │   ├── page.tsx          # ENHANCE: Add execution results tab
│   │   └── edit/page.tsx     # NEW: Full agent editing form
├── integrations/
│   └── mcp/
│       ├── page.tsx          # ENHANCE: Add tool browser link
│       └── [id]/tools/       # NEW: MCP tool browser page
│           └── page.tsx
```

### Pattern 1: Agent List with Last Execution Summary (CTRL-01)
**What:** Enhanced agent card showing most recent execution result summary
**When to use:** Agent list page to satisfy "user can view recent execution result summary"
**Example:**
```typescript
// Extend existing agentsAPI to include last execution
export const agentsAPI = {
  // ... existing methods
  listWithExecutions: () =>
    fetchAPI<Array<Agent & { last_execution?: ExecutionSummary }>>('/api/agents?include_last_execution=true')
}

// Agent card component
function AgentCard({ agent }: { agent: Agent & { last_execution?: ExecutionSummary } }) {
  return (
    <div className="card">
      {/* Existing agent info */}

      {/* NEW: Last execution summary */}
      {agent.last_execution && (
        <div className="mt-4 p-3 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-secondary">Last Run</span>
            <span className={`badge badge-${statusBadge(agent.last_execution.status)}`}>
              {agent.last_execution.status}
            </span>
          </div>
          <p className="text-sm text-muted">
            {formatRelativeTime(agent.last_execution.completed_at)} ·
            {agent.last_execution.tokens_input + agent.last_execution.tokens_output} tokens
          </p>
        </div>
      )}
    </div>
  );
}
```

### Pattern 2: Agent Form with Multi-Select (CTRL-02)
**What:** Create/update agent form with skill and integration assignment using React Hook Form
**When to use:** Agent creation and editing pages for comprehensive configuration
**Example:**
```typescript
// Source: React Hook Form + shadcn/ui patterns (2026)
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const agentSchema = z.object({
  name: z.string().min(1).max(255),
  description: z.string().optional(),
  model: z.string(),
  system_prompt: z.string().optional(),
  temperature: z.number().min(0).max(2),
  skills: z.array(z.string()),
  integrations: z.array(z.string()),
  schedule: z.string().optional(),
  memory_enabled: z.boolean(),
});

type AgentFormData = z.infer<typeof agentSchema>;

function AgentForm({ initialData, onSubmit }: { initialData?: Partial<AgentFormData>, onSubmit: (data: AgentFormData) => Promise<void> }) {
  const { control, handleSubmit, formState: { errors, isSubmitting } } = useForm<AgentFormData>({
    resolver: zodResolver(agentSchema),
    defaultValues: initialData || { skills: [], integrations: [], memory_enabled: true, temperature: 0.7 },
  });

  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [availableIntegrations, setAvailableIntegrations] = useState<Integration[]>([]);

  useEffect(() => {
    skillsAPI.list().then(setAvailableSkills);
    integrationsAPI.list().then(setAvailableIntegrations);
  }, []);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">
      {/* Basic fields */}
      <Controller
        name="name"
        control={control}
        render={({ field }) => (
          <div className="input-group">
            <label className="input-label">Agent Name *</label>
            <input {...field} className="input" />
            {errors.name && <p className="text-sm text-error mt-1">{errors.name.message}</p>}
          </div>
        )}
      />

      {/* Multi-select for skills */}
      <Controller
        name="skills"
        control={control}
        render={({ field }) => (
          <div className="input-group">
            <label className="input-label">Skills</label>
            <div className="flex flex-col gap-2 p-4 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
              {availableSkills.map(skill => (
                <label key={skill.id} className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={field.value.includes(skill.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        field.onChange([...field.value, skill.id]);
                      } else {
                        field.onChange(field.value.filter(id => id !== skill.id));
                      }
                    }}
                    className="checkbox"
                  />
                  <div>
                    <div className="text-sm font-medium">{skill.name}</div>
                    {skill.description && <div className="text-xs text-secondary">{skill.description}</div>}
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}
      />

      {/* Similar pattern for integrations */}

      <button type="submit" disabled={isSubmitting} className="btn btn-primary">
        {isSubmitting ? 'Saving...' : 'Save Agent'}
      </button>
    </form>
  );
}
```

### Pattern 3: Execution Result Display (CTRL-03)
**What:** Display agent run completion status and final output with real-time updates
**When to use:** Agent detail page execution tab, post-run results
**Example:**
```typescript
// Source: WebSocket patterns for React real-time updates (2026)
function ExecutionResultView({ executionId }: { executionId: string }) {
  const [execution, setExecution] = useState<ExecutionResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // Initial fetch
    executionsAPI.get(executionId).then(setExecution).finally(() => setLoading(false));

    // Real-time updates via WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/executions/${executionId}`);
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setExecution(prev => prev ? { ...prev, ...update } : update);
    };
    wsRef.current = ws;

    return () => ws.close();
  }, [executionId]);

  if (loading) return <div>Loading...</div>;
  if (!execution) return <div>Not found</div>;

  return (
    <div className="flex flex-col gap-6">
      {/* Status header */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3>Execution {execution.id.slice(0, 8)}</h3>
          <span className={`badge badge-${execution.status}`}>{execution.status}</span>
        </div>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-secondary">Started</span>
            <div className="font-medium">{formatDateTime(execution.started_at)}</div>
          </div>
          <div>
            <span className="text-secondary">Duration</span>
            <div className="font-medium">{formatDuration(execution.started_at, execution.completed_at)}</div>
          </div>
          <div>
            <span className="text-secondary">Tokens</span>
            <div className="font-medium">{execution.tokens_input + execution.tokens_output}</div>
          </div>
        </div>
      </div>

      {/* Final output */}
      {execution.output_data && (
        <div className="card">
          <h4 className="mb-3">Final Output</h4>
          <pre className="p-4 rounded text-sm overflow-x-auto" style={{ background: "var(--color-bg-tertiary)" }}>
            {JSON.stringify(execution.output_data, null, 2)}
          </pre>
        </div>
      )}

      {/* Execution steps */}
      <div className="card">
        <h4 className="mb-3">Execution Steps</h4>
        <div className="flex flex-col gap-3">
          {execution.steps.map(step => (
            <div key={step.id} className="p-3 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
              <div className="flex items-center justify-between mb-2">
                <span className="font-medium">{step.name}</span>
                <span className={`badge badge-${step.status}`}>{step.status}</span>
              </div>
              <div className="text-sm text-secondary">{step.step_type}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Error display if failed */}
      {execution.error_message && (
        <div className="card" style={{ background: "var(--color-error-muted)" }}>
          <h4 className="mb-2" style={{ color: "var(--color-error)" }}>Error</h4>
          <pre className="text-sm" style={{ color: "var(--color-error)" }}>{execution.error_message}</pre>
        </div>
      )}
    </div>
  );
}
```

### Pattern 4: MCP Tool Schema Browser (MCP-05)
**What:** Browsable list of MCP tools with collapsible JSON Schema input visualization
**When to use:** MCP server detail page to display discovered tools and required inputs
**Example:**
```typescript
// Source: MCP specification + react-json-tree for schema rendering
import JSONTree from 'react-json-tree';

function MCPToolBrowser({ serverId }: { serverId: string }) {
  const [server, setServer] = useState<MCPServer | null>(null);
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());

  useEffect(() => {
    mcpServersAPI.get(serverId).then(setServer);
  }, [serverId]);

  if (!server) return <div>Loading...</div>;

  return (
    <div className="flex flex-col gap-4">
      <div className="header">
        <h2>{server.name} - Tools</h2>
        <p className="text-secondary">{server.tools_detected.length} tools discovered</p>
      </div>

      {server.tools_detected.length === 0 ? (
        <div className="card">
          <div className="empty-state">
            <div className="empty-state-icon">🔧</div>
            <h3>No tools detected</h3>
            <p>This MCP server has not exposed any tools yet.</p>
          </div>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {server.tools_detected.map((tool: any) => {
            const isExpanded = expandedTools.has(tool.name);
            return (
              <div key={tool.name} className="card">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <code className="text-sm font-mono" style={{ color: "var(--color-accent)" }}>
                        {tool.name}
                      </code>
                      {tool.title && (
                        <span className="text-sm text-muted">· {tool.title}</span>
                      )}
                    </div>
                    {tool.description && (
                      <p className="text-sm text-secondary">{tool.description}</p>
                    )}
                  </div>
                  <button
                    onClick={() => {
                      const next = new Set(expandedTools);
                      if (isExpanded) next.delete(tool.name);
                      else next.add(tool.name);
                      setExpandedTools(next);
                    }}
                    className="btn btn-ghost btn-sm"
                  >
                    {isExpanded ? '▼ Collapse' : '▶ Expand Schema'}
                  </button>
                </div>

                {isExpanded && tool.inputSchema && (
                  <div className="mt-4 p-4 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
                    <h5 className="text-sm font-medium mb-3">Input Schema</h5>
                    <SchemaRenderer schema={tool.inputSchema} />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// Custom schema renderer for better readability than raw JSON tree
function SchemaRenderer({ schema }: { schema: any }) {
  if (schema.type === 'object') {
    return (
      <div className="flex flex-col gap-2">
        {Object.entries(schema.properties || {}).map(([key, prop]: [string, any]) => (
          <div key={key} className="flex items-start gap-3 p-2 rounded" style={{ background: "var(--color-bg-secondary)" }}>
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <code className="text-sm font-mono">{key}</code>
                <span className="badge badge-neutral text-xs">{prop.type}</span>
                {schema.required?.includes(key) && (
                  <span className="badge badge-error text-xs">required</span>
                )}
              </div>
              {prop.description && (
                <p className="text-xs text-secondary">{prop.description}</p>
              )}
              {prop.enum && (
                <div className="mt-1 text-xs text-muted">
                  Allowed: {prop.enum.map((v: string) => `"${v}"`).join(', ')}
                </div>
              )}
              {prop.default !== undefined && (
                <div className="mt-1 text-xs text-muted">
                  Default: {JSON.stringify(prop.default)}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Fallback to JSON tree for complex schemas
  return (
    <JSONTree
      data={schema}
      theme={{
        scheme: 'monokai',
        author: 'wimer hazenberg (http://www.monokai.nl)',
        base00: 'var(--color-bg-secondary)',
        base01: '#383830',
        base02: '#49483e',
        base03: '#75715e',
        base04: '#a59f85',
        base05: '#f8f8f2',
        base06: '#f5f4f1',
        base07: '#f9f8f5',
        base08: '#f92672',
        base09: '#fd971f',
        base0A: '#f4bf75',
        base0B: '#a6e22e',
        base0C: '#a1efe4',
        base0D: '#66d9ef',
        base0E: '#ae81ff',
        base0F: '#cc6633',
      }}
      invertTheme={false}
      hideRoot={true}
      shouldExpandNodeInitially={() => false}
    />
  );
}
```

### Anti-Patterns to Avoid
- **Fetching on every render:** Use useEffect with proper dependencies, not raw fetch calls in component body
- **Inline form validation:** Use React Hook Form + Zod schema, not ad-hoc useState checks
- **Deep prop drilling:** Create focused components that fetch their own data when possible
- **Uncontrolled WebSocket connections:** Always clean up WebSocket in useEffect return, track connection state
- **Manual JSON formatting:** Use JSONTree or custom renderers, not recursive divs

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Form state management | Custom useState for each field | React Hook Form | Handles validation, dirty tracking, submission state, minimal re-renders |
| Form validation | Manual error state + conditionals | Zod + @hookform/resolvers | Type-safe schemas, automatic error messages, reusable across client/server |
| JSON Schema rendering | Recursive div tree builder | react-json-tree or custom flat renderer | Handles edge cases (circular refs, large objects), theme support, collapsible nodes |
| WebSocket reconnection | Manual retry loops | Custom hook with exponential backoff | Production reliability, memory leak prevention, state cleanup |
| Multi-select UI | Custom checkbox state array | Controller + checkboxes pattern | Integrates with form validation, accessible, standard pattern |

**Key insight:** Form handling and real-time updates have subtle edge cases (validation timing, memory leaks, race conditions). Using proven libraries (React Hook Form, established WebSocket patterns) prevents production bugs and reduces code complexity. Custom solutions often miss accessibility, performance, and error recovery requirements.

## Common Pitfalls

### Pitfall 1: Agent Form Not Showing Current Skill/Integration Assignments
**What goes wrong:** When editing an agent, the skill/integration checkboxes don't reflect current assignments
**Why it happens:** React Hook Form defaultValues only apply on mount; editing pages need to use reset() when data loads
**How to avoid:** Call form.reset(loadedData) in useEffect after fetching agent details
**Warning signs:** Checkboxes are always unchecked when opening edit form, or form shows stale data after navigation

```typescript
// WRONG: defaultValues set once, never updates
const form = useForm({ defaultValues: { skills: [] } });
useEffect(() => {
  agentsAPI.get(id).then(setAgent); // Form doesn't update
}, [id]);

// CORRECT: Reset form when data loads
const form = useForm({ defaultValues: { skills: [] } });
useEffect(() => {
  agentsAPI.get(id).then(agent => {
    setAgent(agent);
    form.reset({ skills: agent.skills, integrations: agent.integrations, ...agent });
  });
}, [id, form]);
```

### Pitfall 2: Last Execution Summary Causing N+1 Query Problem
**What goes wrong:** Fetching last execution for each agent separately causes slow page loads
**Why it happens:** Looping through agents and calling executionsAPI.list(agentId) for each one
**How to avoid:** Add backend endpoint that joins agents with their last execution in a single query, or use GraphQL-style field inclusion
**Warning signs:** Agent list page loads slowly with many agents, network tab shows dozens of execution requests

```typescript
// WRONG: N+1 queries
const agents = await agentsAPI.list();
for (const agent of agents) {
  agent.last_execution = await executionsAPI.list(agent.id, undefined, 1)[0];
}

// CORRECT: Single query with join or aggregation
// Backend: GET /api/agents?include_last_execution=true
const agents = await agentsAPI.listWithExecutions();
```

### Pitfall 3: WebSocket Memory Leak on Page Navigation
**What goes wrong:** WebSocket connections stay open after navigating away from execution result page
**Why it happens:** Missing cleanup in useEffect return statement
**How to avoid:** Always return cleanup function that closes WebSocket; use ref to track connection
**Warning signs:** Browser shows increasing number of open connections, console errors about closed sockets

```typescript
// WRONG: No cleanup
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/executions');
  ws.onmessage = (e) => setData(JSON.parse(e.data));
}, []);

// CORRECT: Cleanup on unmount
useEffect(() => {
  const ws = new WebSocket('ws://localhost:8000/ws/executions');
  ws.onmessage = (e) => setData(JSON.parse(e.data));
  return () => ws.close(); // Cleanup
}, []);
```

### Pitfall 4: MCP Tool Schema Not Handling Missing or Invalid Fields
**What goes wrong:** MCP tool browser crashes when tool schema is malformed or missing properties
**Why it happens:** Assuming all tools follow perfect MCP spec format without defensive checks
**How to avoid:** Add null checks, fallback to raw JSON display if schema doesn't match expected structure
**Warning signs:** Page crashes when certain MCP servers are selected, errors about "cannot read property 'properties' of undefined"

```typescript
// WRONG: Assumes perfect schema structure
function renderSchema(schema) {
  return Object.entries(schema.properties).map(...); // Crashes if no properties
}

// CORRECT: Defensive checks with fallback
function renderSchema(schema) {
  if (!schema || typeof schema !== 'object') {
    return <JSONTree data={schema} />;
  }
  if (schema.type === 'object' && schema.properties) {
    return Object.entries(schema.properties).map(...);
  }
  return <JSONTree data={schema} />; // Fallback for non-standard schemas
}
```

### Pitfall 5: Form Submission Not Handling Validation Errors
**What goes wrong:** User clicks submit, form seems to freeze, no error feedback
**Why it happens:** Not checking formState.errors or providing user feedback on validation failures
**How to avoid:** Display validation errors inline, prevent submission when form is invalid, show loading state
**Warning signs:** Users report "form doesn't work," submit button does nothing on click

```typescript
// WRONG: No error display, no submit state
<form onSubmit={handleSubmit(onSubmit)}>
  <input {...register('name')} />
  <button type="submit">Save</button>
</form>

// CORRECT: Error display, disabled state, loading feedback
<form onSubmit={handleSubmit(onSubmit)}>
  <div className="input-group">
    <input {...register('name')} className={errors.name ? 'input input-error' : 'input'} />
    {errors.name && <p className="text-error text-sm">{errors.name.message}</p>}
  </div>
  <button type="submit" disabled={isSubmitting}>
    {isSubmitting ? 'Saving...' : 'Save'}
  </button>
</form>
```

## Code Examples

Verified patterns from codebase and official sources:

### Agent API Client Pattern (Existing)
```typescript
// Source: /home/kngpnn/dev/lazy-agents/frontend/lib/api.ts
export const agentsAPI = {
  list: (skip = 0, limit = 100) =>
    fetchAPI<Agent[]>('/api/agents', { params: { skip, limit } }),

  get: (id: string) =>
    fetchAPI<Agent>(`/api/agents/${id}`),

  create: (data: { name: string; description?: string; model?: string; system_prompt?: string }) =>
    fetchAPI<Agent>('/api/agents', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: Partial<Agent>) =>
    fetchAPI<Agent>(`/api/agents/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  run: (id: string, input?: Record<string, unknown>) =>
    fetchAPI<Execution>(`/api/agents/${id}/run`, { method: 'POST', body: JSON.stringify({ input: input || {} }) }),
};
```

### MCP Tool Schema Structure (MCP Specification)
```typescript
// Source: https://modelcontextprotocol.io/specification/draft/server/tools
interface MCPTool {
  name: string; // Unique identifier, 1-128 chars, alphanumeric + _-.
  title?: string; // Human-readable display name
  description: string; // Human-readable functionality description
  icons?: Array<{ src: string; mimeType: string; sizes?: string[] }>;
  inputSchema: {
    type: 'object';
    properties: Record<string, {
      type: 'string' | 'number' | 'boolean' | 'array' | 'object';
      description?: string;
      enum?: string[];
      default?: any;
      items?: any; // For array type
      properties?: Record<string, any>; // For nested objects
    }>;
    required?: string[];
    additionalProperties?: boolean;
  };
  outputSchema?: { /* Same structure as inputSchema */ };
  annotations?: Record<string, any>;
}

// Example from MCP spec
const weatherTool: MCPTool = {
  name: "get_weather",
  title: "Weather Information Provider",
  description: "Get current weather information for a location",
  inputSchema: {
    type: "object",
    properties: {
      location: {
        type: "string",
        description: "City name or zip code"
      }
    },
    required: ["location"]
  }
};
```

### WebSocket Pattern for Real-Time Updates (Existing)
```typescript
// Source: /home/kngpnn/dev/lazy-agents/frontend/app/agents/[id]/page.tsx
useEffect(() => {
  if (activeTab === 'logs') {
    const ws = new WebSocket('ws://localhost:8000/ws/logs');

    ws.onopen = () => {
      console.log('Connected to logs');
    };

    ws.onmessage = (event) => {
      try {
        const log = JSON.parse(event.data);
        setLogs(prev => [log, ...prev].slice(0, 100)); // Keep last 100
      } catch (e) {
        console.error('Error parsing log', e);
      }
    };

    wsRef.current = ws;

    return () => {
      ws.close(); // Cleanup
    };
  }
}, [activeTab]);
```

### Existing Design System Component Classes
```css
/* Source: /home/kngpnn/dev/lazy-agents/frontend/app/globals.css */

/* Card component */
.card {
  background: var(--color-bg-secondary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-6);
}

/* Button variants */
.btn-primary {
  background: var(--color-accent);
  color: white;
}

.btn-secondary {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.btn-ghost {
  background: transparent;
  color: var(--color-text-secondary);
}

/* Badge variants */
.badge-success { background: var(--color-success-muted); color: var(--color-success); }
.badge-error { background: var(--color-error-muted); color: var(--color-error); }
.badge-info { background: var(--color-info-muted); color: var(--color-info); }
.badge-neutral { background: var(--color-bg-tertiary); color: var(--color-text-secondary); }

/* Input components */
.input {
  background: var(--color-bg-tertiary);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3) var(--space-4);
  color: var(--color-text-primary);
}

.input:focus {
  outline: none;
  border-color: var(--color-border-focus);
}

/* Grid system */
.grid { display: grid; }
.grid-cols-2 { grid-template-columns: repeat(2, 1fr); }
.grid-cols-3 { grid-template-columns: repeat(3, 1fr); }
.gap-4 { gap: var(--space-4); }
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Formik for forms | React Hook Form + Zod | 2023-2024 | Better performance (fewer re-renders), TypeScript-first validation |
| JavaScript Tailwind config | @theme directive in CSS | Tailwind v4 (2024) | CSS-first configuration, better build performance, simpler theming |
| Socket.io for WebSockets | Native WebSocket API | 2025-2026 | Simpler for basic use cases, no dependency overhead, adequate for current needs |
| Pages Router | App Router | Next.js 13+ (2023) | Server components, improved data fetching, better TypeScript support |
| Controlled inputs everywhere | React Hook Form uncontrolled | 2022+ | Performance improvement for large forms, less boilerplate |

**Deprecated/outdated:**
- **Formik:** Still works but React Hook Form has better performance and TypeScript support (2026 consensus)
- **Manual form validation:** Zod provides type-safe validation that works client and server side
- **Class-based components for forms:** Hooks-based approach (React Hook Form) is modern standard
- **tailwind.config.js for themes:** Tailwind v4 uses @theme directive in CSS files

## Open Questions

1. **Should we add backend endpoint for agents with last execution included?**
   - What we know: Current API requires separate call to get executions per agent (N+1 problem)
   - What's unclear: Whether to add query param `?include_last_execution=true` or create new endpoint
   - Recommendation: Add query param to existing GET /api/agents endpoint for backward compatibility

2. **Do we need WebSocket endpoint for individual execution updates?**
   - What we know: Existing WebSocket for global logs works well (agent detail page uses it)
   - What's unclear: Whether execution-specific updates warrant dedicated endpoint or can use existing pattern
   - Recommendation: Start with polling (executionsAPI.get every 2s while status is running), add WebSocket if polling proves insufficient

3. **Should MCP tool browser be on server detail page or separate route?**
   - What we know: MCP server page already shows tools_detected count
   - What's unclear: Whether to expand inline or navigate to dedicated tool browser page
   - Recommendation: Add "View Tools" button that navigates to `/integrations/mcp/[id]/tools` for dedicated focus area

4. **Do we validate agent form on backend when skills/integrations don't exist?**
   - What we know: Backend accepts string[] for skills and integrations
   - What's unclear: Whether backend validates that skill/integration IDs exist in database
   - Recommendation: Add backend validation to return 400 if non-existent IDs are submitted; document in PLAN tasks

## Sources

### Primary (HIGH confidence)
- MCP Specification - Tools: https://modelcontextprotocol.io/specification/draft/server/tools
- Codebase API client: /home/kngpnn/dev/lazy-agents/frontend/lib/api.ts
- Codebase agent model: /home/kngpnn/dev/lazy-agents/backend/app/models/agent.py
- Codebase execution model: /home/kngpnn/dev/lazy-agents/backend/app/models/execution.py
- Codebase MCP server model: /home/kngpnn/dev/lazy-agents/backend/app/models/mcp_server.py
- Codebase design system: /home/kngpnn/dev/lazy-agents/frontend/app/globals.css

### Secondary (MEDIUM confidence)
- [React Hook Form Advanced Usage](https://www.react-hook-form.com/advanced-usage/)
- [Next.js Forms Management with App Router](https://www.pronextjs.dev/tutorials/forms-management-with-next-js-app-router)
- [React Hook Form with React 19 and Next.js 15](https://markus.oberlehner.net/blog/using-react-hook-form-with-react-19-use-action-state-and-next-js-15-app-router)
- [Tailwind CSS v4 Migration Guide](https://typescript.tv/hands-on/upgrading-to-tailwind-css-v4-a-migration-guide/)
- [WebSockets in React for Real-Time Applications](https://oneuptime.com/blog/post/2026-01-15-websockets-react-real-time-applications/view)
- [Real-time Updates with WebSockets and React Hooks](https://www.geeksforgeeks.org/reactjs/real-time-updates-with-websockets-and-react-hooks/)

### Tertiary (LOW confidence - for awareness)
- [Top AI Agent Platforms for Enterprises (2026)](https://www.stack-ai.com/blog/the-best-ai-agent-and-workflow-builder-platforms-2026-guide) - UI inspiration
- [Best AI Agent Builders in 2026](https://www.lindy.ai/blog/best-ai-agent-builders) - Market trends
- [React JSON Viewer Components (2026)](https://reactscript.com/best-json-viewer/) - Library options
- [Shadcn Multi-Select Component](https://shadcn-multi-select-component.vercel.app/) - Pattern reference
- [MCP Tool Schema Guide](https://www.merge.dev/blog/mcp-tool-schema) - Additional examples

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Existing codebase patterns verified, official docs confirmed
- Architecture: HIGH - Patterns adapted from working codebase examples
- Pitfalls: HIGH - Common issues documented in official guides and codebase patterns
- MCP tool schema: HIGH - Official MCP specification provides exact structure
- Form patterns: MEDIUM-HIGH - React Hook Form is industry standard, verified with official docs

**Research date:** 2026-02-08
**Valid until:** 2026-03-08 (30 days - stable ecosystem)

**Notes:**
- All existing backend APIs are complete and typed; no backend changes required for basic functionality
- Design system is comprehensive; no new CSS framework needed
- Main work is frontend UI enhancement using existing patterns
- MCP tool schema format is stable (official spec); browser implementation is straightforward
