/**
 * API client for LazyAgents backend
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined>;
}

async function fetchAPI<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, ...init } = options;

  let url = `${API_BASE}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) searchParams.append(key, String(value));
    });
    const qs = searchParams.toString();
    if (qs) url += `?${qs}`;
  }

  const response = await fetch(url, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  // No-content responses are only expected for void endpoints (for example DELETE).
  if (response.status === 204 || response.status === 205) {
    return undefined as T;
  }

  return response.json();
}

// Types
export interface Agent {
  id: string;
  name: string;
  description: string | null;
  status: 'active' | 'paused' | 'error';
  model: string;
  system_prompt: string | null;
  temperature: number;
  skills: string[];
  integrations: string[];
  schedule: string | null;
  memory_enabled: boolean;
  created_at: string;
  updated_at: string;
  last_run_at: string | null;
  total_runs: number;
  successful_runs: number;
}

export interface Skill {
  id: string;
  name: string;
  description: string | null;
  category: string;
  parameters: Record<string, unknown>;
  integration_required: string | null;
  is_builtin: boolean;
}

export interface Integration {
  id: string;
  type: string;
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  permissions: string[];
  config: Record<string, unknown>;
  created_at: string;
  last_used_at: string | null;
}

export interface Execution {
  id: string;
  agent_id: string;
  agent_name?: string;
  trigger: 'manual' | 'schedule' | 'webhook' | 'event';
  status: 'pending' | 'running' | 'success' | 'failed' | 'cancelled';
  started_at: string | null;
  completed_at: string | null;
  tokens_input: number;
  tokens_output: number;
  cost_cents: number;
  error_message: string | null;
  created_at: string;
}

export interface ExecutionStats {
  total: number;
  successful: number;
  failed: number;
  success_rate: number;
  total_tokens: number;
  total_cost_cents: number;
}

export type MCPServerStatus = 'stopped' | 'starting' | 'running' | 'error';

export interface MCPServer {
  id: string;
  name: string;
  description: string | null;
  command: string;
  args: string[];
  env: Record<string, string>;
  enabled: boolean;
  status: MCPServerStatus;
  tools_detected: Array<Record<string, unknown>>;
  last_error: string | null;
  created_at: string;
  updated_at: string;
}

export interface MCPServerCreateInput {
  name: string;
  description?: string | null;
  command: string;
  args?: string[];
  env?: Record<string, string>;
  enabled?: boolean;
}

export interface MCPServerUpdateInput {
  name?: string;
  description?: string | null;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  merge_env?: boolean;
  enabled?: boolean;
}

export interface DashboardStats {
  total_agents: number;
  active_agents: number;
  total_executions: number;
  success_rate: number;
}

export interface AgentConfig {
  id: string;
  name: string;
  description: string | null;
  status: string;
  model: string;
  system_prompt: string | null;
  temperature: number;
  memory_enabled: boolean;
  schedule: string | null;
  next_scheduled_run: string | null;
  skills: Array<{
    id: string;
    name: string;
    description: string;
    category: string;
    parameters: Record<string, unknown>;
  }>;
  integrations: Array<{
    id: string;
    name: string;
    type: string;
    status: string;
  }>;
  stats: {
    total_runs: number;
    successful_runs: number;
    success_rate: number;
    last_run_at: string | null;
  };
}

// Agents API
export const agentsAPI = {
  list: (skip = 0, limit = 100) =>
    fetchAPI<Agent[]>('/api/agents', { params: { skip, limit } }),

  get: (id: string) =>
    fetchAPI<Agent>(`/api/agents/${id}`),

  getConfig: (id: string) =>
    fetchAPI<AgentConfig>(`/api/agents/${id}/config`),

  create: (data: { name: string; description?: string; model?: string; system_prompt?: string }) =>
    fetchAPI<Agent>('/api/agents', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: Partial<Agent>) =>
    fetchAPI<Agent>(`/api/agents/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  delete: (id: string) =>
    fetchAPI<void>(`/api/agents/${id}`, { method: 'DELETE' }),

  run: (id: string, input?: Record<string, unknown>) =>
    fetchAPI<Execution>(`/api/agents/${id}/run`, { method: 'POST', body: JSON.stringify({ input: input || {} }) }),
};

// Skills API
export const skillsAPI = {
  list: (category?: string) =>
    fetchAPI<Skill[]>('/api/skills', { params: { category } }),

  get: (id: string) =>
    fetchAPI<Skill>(`/api/skills/${id}`),

  getConfig: (id: string) =>
    fetchAPI<{
      id: string;
      name: string;
      description: string;
      category: string;
      parameters: Record<string, unknown>;
      integration_required: string | null;
      is_builtin: boolean;
      implementation_type: string;
      implementation: string | null;
      templates: Record<string, string>;
      references: string[];
      source_path: string | null;
    }>(`/api/skills/${id}/config`),

  create: (data: { id: string; name: string; description?: string; category: string; parameters?: Record<string, unknown>; implementation?: string }) =>
    fetchAPI<Skill>('/api/skills', { method: 'POST', body: JSON.stringify(data) }),

  update: (id: string, data: Record<string, unknown>) =>
    fetchAPI<Skill>(`/api/skills/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

  delete: (id: string) =>
    fetchAPI<void>(`/api/skills/${id}`, { method: 'DELETE' }),

  loadFromPath: (path: string) =>
    fetchAPI<{ message: string; skill: Skill }>('/api/skills/load-from-path', {
      method: 'POST',
      params: { path }
    }),

  scanDirectory: (directory: string) =>
    fetchAPI<{ directory: string; skills_found: number; results: { id: string; status: string; error?: string }[] }>('/api/skills/scan-directory', {
      method: 'POST',
      params: { directory }
    }),

  categories: () =>
    fetchAPI<string[]>('/api/skills/categories/list'),
};

// Integrations API
export const integrationsAPI = {
  list: () =>
    fetchAPI<Integration[]>('/api/integrations'),

  types: () =>
    fetchAPI<{ type: string; name: string; description: string; required_credentials: string[] }[]>('/api/integrations/types'),

  create: (data: { type: string; name: string; credentials: Record<string, string> }) =>
    fetchAPI<Integration>('/api/integrations', { method: 'POST', body: JSON.stringify(data) }),

  delete: (id: string) =>
    fetchAPI<void>(`/api/integrations/${id}`, { method: 'DELETE' }),

  test: (id: string) =>
    fetchAPI<{ success: boolean; message: string }>(`/api/integrations/${id}/test`, { method: 'POST' }),
};

export const mcpServersAPI = {
  list: () =>
    fetchAPI<MCPServer[]>('/api/mcp/servers'),

  get: (id: string) =>
    fetchAPI<MCPServer>(`/api/mcp/servers/${id}`),

  create: (data: MCPServerCreateInput) =>
    fetchAPI<MCPServer>('/api/mcp/servers', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  update: (id: string, data: MCPServerUpdateInput) =>
    fetchAPI<MCPServer>(`/api/mcp/servers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  remove: (id: string) =>
    fetchAPI<void>(`/api/mcp/servers/${id}`, {
      method: 'DELETE',
    }),

  restart: (id: string) =>
    fetchAPI<MCPServer>(`/api/mcp/servers/${id}/restart`, {
      method: 'POST',
    }),

  sync: (id: string) =>
    fetchAPI<MCPServer>(`/api/mcp/servers/${id}/sync`, {
      method: 'POST',
    }),
};

// Executions API
export const executionsAPI = {
  list: (agentId?: string, status?: string, limit = 50) =>
    fetchAPI<Execution[]>('/api/executions', { params: { agent_id: agentId, status, limit } }),

  get: (id: string) =>
    fetchAPI<Execution & { steps: unknown[] }>(`/api/executions/${id}`),

  stats: () =>
    fetchAPI<ExecutionStats>('/api/executions/stats'),

  cancel: (id: string) =>
    fetchAPI<Execution>(`/api/executions/${id}/cancel`, { method: 'POST' }),
};

// Health API
export const healthAPI = {
  check: () =>
    fetchAPI<{ status: string; version: string }>('/health'),

  ready: () =>
    fetchAPI<{ status: string; database: string; timestamp: string }>('/health/ready'),
};

// Combined API object for convenience
export const api = {
  agents: agentsAPI,
  skills: skillsAPI,
  integrations: integrationsAPI,
  mcpServers: mcpServersAPI,
  executions: executionsAPI,
  health: healthAPI,
};
