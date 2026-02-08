"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import Link from "next/link";
import { agentsAPI, AgentWithExecution } from "@/lib/api";

export default function AgentsPage() {
  const [agents, setAgents] = useState<AgentWithExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadAgents();
  }, []);

  async function loadAgents() {
    try {
      const data = await agentsAPI.list(0, 100, true);
      setAgents(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agents');
    } finally {
      setLoading(false);
    }
  }

  // Helper to format relative time
  function formatRelativeTime(timestamp: string | null): string {
    if (!timestamp) return "Never";
    const now = new Date();
    const then = new Date(timestamp);
    const seconds = Math.floor((now.getTime() - then.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
    return then.toLocaleDateString();
  }

  async function handleDelete(id: string) {
    if (!confirm('Are you sure you want to delete this agent?')) return;
    setDeleting(id);
    try {
      await agentsAPI.delete(id);
      setAgents(agents.filter(a => a.id !== id));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to delete agent');
    } finally {
      setDeleting(null);
    }
  }

  async function handleRun(id: string) {
    try {
      await agentsAPI.run(id);
      loadAgents(); // Refresh to show updated stats
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to run agent');
    }
  }

  async function handleToggleStatus(agent: AgentWithExecution) {
    const newStatus = agent.status === 'active' ? 'paused' : 'active';
    try {
      await agentsAPI.update(agent.id, { status: newStatus });
      setAgents(agents.map(a => a.id === agent.id ? { ...a, status: newStatus } : a));
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update agent');
    }
  }

  if (loading) return (
    <DashboardLayout>
      <div className="container" style={{ padding: "var(--space-8)", textAlign: "center" }}>
        <div style={{ fontSize: "2rem", marginBottom: "var(--space-4)" }}>⏳</div>
        <p className="text-secondary">Loading agents...</p>
      </div>
    </DashboardLayout>
  );

  return (
    <DashboardLayout>
      <div className="header">
        <div>
          <h1 className="header-title">Agents</h1>
          <p className="text-sm text-secondary mt-2">
            {agents.length} agent{agents.length !== 1 ? 's' : ''} configured
          </p>
        </div>
        <Link href="/agents/new" className="btn btn-primary">
          <span>✨</span>
          <span>Create Agent</span>
        </Link>
      </div>

      <div className="container" style={{ padding: "var(--space-8)" }}>
        {error && (
          <div className="card mb-6" style={{ background: "var(--color-error-muted)" }}>
            <p style={{ color: "var(--color-error)" }}>⚠️ {error}</p>
          </div>
        )}

        {agents.length === 0 ? (
          <div className="card">
            <div className="empty-state">
              <div className="empty-state-icon">🤖</div>
              <h3>No agents yet</h3>
              <p>Create your first AI agent to start automating tasks.</p>
              <Link href="/agents/new" className="btn btn-primary mt-4">
                ✨ Create Your First Agent
              </Link>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {agents.map((agent) => (
              <div key={agent.id} className="card">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div style={{ width: 48, height: 48, borderRadius: "var(--radius-lg)", background: "var(--color-accent-muted)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.5rem" }}>
                      🤖
                    </div>
                    <div>
                      <h3 style={{ fontSize: "var(--font-size-lg)", marginBottom: 4 }}>{agent.name}</h3>
                      <div className="flex items-center gap-2">
                        <span className={`badge ${agent.status === 'active' ? 'badge-success' : 'badge-neutral'}`}>
                          {agent.status}
                        </span>
                        <span className="badge badge-neutral">{agent.model}</span>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => handleToggleStatus(agent)}
                    className={`btn btn-sm ${agent.status === 'active' ? 'btn-ghost' : 'btn-secondary'}`}
                  >
                    {agent.status === 'active' ? '⏸️ Pause' : '▶️ Activate'}
                  </button>
                </div>

                {agent.description && (
                  <p className="text-secondary text-sm mb-4">{agent.description}</p>
                )}

                <div className="flex items-center gap-6 text-sm text-muted mb-4">
                  <span>🏃 {agent.total_runs} runs</span>
                  <span>✅ {agent.total_runs > 0 ? ((agent.successful_runs / agent.total_runs) * 100).toFixed(0) : 0}% success</span>
                  {agent.schedule && <span>⏰ {agent.schedule}</span>}
                </div>

                {/* Last Execution Summary */}
                {agent.last_execution && (
                  <div className="mb-4 p-3 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm" style={{ color: "var(--color-text-secondary)" }}>Last Run</span>
                      <span className={`badge ${
                        agent.last_execution.status === 'success' ? 'badge-success' :
                        agent.last_execution.status === 'failed' ? 'badge-error' :
                        agent.last_execution.status === 'running' ? 'badge-info' :
                        'badge-neutral'
                      }`}>
                        {agent.last_execution.status}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm" style={{ color: "var(--color-text-muted)" }}>
                      <span>{formatRelativeTime(agent.last_execution.completed_at || agent.last_execution.started_at)}</span>
                      <span>•</span>
                      <span>{(agent.last_execution.tokens_input + agent.last_execution.tokens_output).toLocaleString()} tokens</span>
                    </div>
                    {agent.last_execution.error_message && agent.last_execution.status === 'failed' && (
                      <p className="text-xs mt-2 truncate" style={{ color: "var(--color-error)" }}>
                        {agent.last_execution.error_message}
                      </p>
                    )}
                  </div>
                )}

                <div className="flex gap-2">
                  <button onClick={() => handleRun(agent.id)} className="btn btn-primary btn-sm flex-1">
                    ▶️ Run Now
                  </button>
                  <Link href={`/agents/${agent.id}`} className="btn btn-secondary btn-sm">
                    📊 View
                  </Link>
                  <Link href={`/agents/${agent.id}/edit`} className="btn btn-secondary btn-sm">
                    ✏️ Edit
                  </Link>
                  <button
                    onClick={() => handleDelete(agent.id)}
                    className="btn btn-ghost btn-sm"
                    disabled={deleting === agent.id}
                  >
                    {deleting === agent.id ? '...' : '🗑️'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
