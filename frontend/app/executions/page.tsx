"use client";
import { useEffect, useState, useCallback } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { executionsAPI, agentsAPI, Execution, Agent } from "@/lib/api";

export default function ExecutionsPage() {
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [agents, setAgents] = useState<Record<string, Agent>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [agentFilter, setAgentFilter] = useState<string>("");

  const loadData = useCallback(async () => {
    try {
      const [execsList, agentsList] = await Promise.all([
        executionsAPI.list(agentFilter || undefined, statusFilter || undefined, 100),
        agentsAPI.list(),
      ]);
      setExecutions(execsList);
      // Create agent lookup
      const agentMap: Record<string, Agent> = {};
      agentsList.forEach(a => { agentMap[a.id] = a; });
      setAgents(agentMap);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load executions');
    } finally {
      setLoading(false);
    }
  }, [agentFilter, statusFilter]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  async function handleCancel(id: string) {
    try {
      await executionsAPI.cancel(id);
      loadData();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to cancel execution');
    }
  }

  function getStatusBadgeClass(status: string): string {
    switch (status) {
      case 'success': return 'badge-success';
      case 'failed': return 'badge-error';
      case 'running': return 'badge-warning';
      default: return 'badge-neutral';
    }
  }

  function formatDuration(started: string | null, completed: string | null): string {
    if (!started) return '-';
    const start = new Date(started).getTime();
    const end = completed ? new Date(completed).getTime() : Date.now();
    const seconds = (end - start) / 1000;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    return `${Math.floor(seconds / 60)}m ${Math.floor(seconds % 60)}s`;
  }

  if (loading) return (
    <DashboardLayout>
      <div className="container" style={{ padding: "var(--space-8)", textAlign: "center" }}>
        <div style={{ fontSize: "2rem", marginBottom: "var(--space-4)" }}>⏳</div>
        <p className="text-secondary">Loading executions...</p>
      </div>
    </DashboardLayout>
  );

  const agentList = Object.values(agents);

  return (
    <DashboardLayout>
      <div className="header">
        <div>
          <h1 className="header-title">Executions</h1>
          <p className="text-sm text-secondary mt-2">
            {executions.length} execution{executions.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>

      <div className="container" style={{ padding: "var(--space-8)" }}>
        {error && (
          <div className="card mb-6" style={{ background: "var(--color-error-muted)" }}>
            <p style={{ color: "var(--color-error)" }}>⚠️ {error}</p>
          </div>
        )}

        {/* Filters */}
        <div className="flex gap-4 mb-6">
          <div className="input-group" style={{ marginBottom: 0 }}>
            <select
              className="input"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ minWidth: 150 }}
            >
              <option value="">All Statuses</option>
              <option value="pending">Pending</option>
              <option value="running">Running</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
          <div className="input-group" style={{ marginBottom: 0 }}>
            <select
              className="input"
              value={agentFilter}
              onChange={(e) => setAgentFilter(e.target.value)}
              style={{ minWidth: 200 }}
            >
              <option value="">All Agents</option>
              {agentList.map(agent => (
                <option key={agent.id} value={agent.id}>{agent.name}</option>
              ))}
            </select>
          </div>
          <button onClick={() => { setStatusFilter(""); setAgentFilter(""); }} className="btn btn-ghost">
            Clear Filters
          </button>
        </div>

        {executions.length === 0 ? (
          <div className="card">
            <div className="empty-state">
              <div className="empty-state-icon">📜</div>
              <h3>No executions found</h3>
              <p>Run an agent to see its execution history here</p>
            </div>
          </div>
        ) : (
          <div className="card">
            <div className="table-wrapper">
              <table className="table">
                <thead>
                  <tr>
                    <th>Agent</th>
                    <th>Status</th>
                    <th>Trigger</th>
                    <th>Duration</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                    <th>Started</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {executions.map((exec) => {
                    const agent = agents[exec.agent_id];
                    return (
                      <tr key={exec.id}>
                        <td style={{ fontWeight: 500 }}>
                          {agent?.name || `Agent ${exec.agent_id.slice(0, 8)}...`}
                        </td>
                        <td>
                          <span className={`badge ${getStatusBadgeClass(exec.status)}`}>
                            {exec.status}
                          </span>
                        </td>
                        <td>
                          <span className="badge badge-neutral">{exec.trigger}</span>
                        </td>
                        <td>{formatDuration(exec.started_at, exec.completed_at)}</td>
                        <td>{(exec.tokens_input + exec.tokens_output).toLocaleString()}</td>
                        <td>${(exec.cost_cents / 100).toFixed(4)}</td>
                        <td className="text-muted">
                          {exec.started_at ? new Date(exec.started_at).toLocaleString() : '-'}
                        </td>
                        <td>
                          {(exec.status === 'running' || exec.status === 'pending') && (
                            <button
                              onClick={() => handleCancel(exec.id)}
                              className="btn btn-ghost btn-sm"
                            >
                              ⏹️ Cancel
                            </button>
                          )}
                          {exec.error_message && (
                            <button
                              onClick={() => alert(exec.error_message)}
                              className="btn btn-ghost btn-sm"
                            >
                              ⚠️ View Error
                            </button>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
