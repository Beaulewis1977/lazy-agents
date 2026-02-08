"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import Link from "next/link";
import { agentsAPI, executionsAPI, Agent, Execution } from "@/lib/api";

interface Stats {
  totalAgents: number;
  activeAgents: number;
  totalExecutions: number;
  successRate: number;
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats>({ totalAgents: 0, activeAgents: 0, totalExecutions: 0, successRate: 0 });
  const [agents, setAgents] = useState<Agent[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [agentsList, execsList, execStats] = await Promise.all([
          agentsAPI.list(),
          executionsAPI.list(undefined, undefined, 10),
          executionsAPI.stats(),
        ]);
        
        setAgents(agentsList);
        setExecutions(execsList);
        setStats({
          totalAgents: agentsList.length,
          activeAgents: agentsList.filter(a => a.status === 'active').length,
          totalExecutions: execStats.total,
          successRate: execStats.success_rate,
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load data');
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return (
    <DashboardLayout>
      <div className="container" style={{ padding: "var(--space-8)", textAlign: "center" }}>
        <div style={{ fontSize: "2rem", marginBottom: "var(--space-4)" }}>⏳</div>
        <p className="text-secondary">Loading dashboard...</p>
      </div>
    </DashboardLayout>
  );

  return (
    <DashboardLayout>
      <div className="header">
        <div>
          <h1 className="header-title">Dashboard</h1>
          <p className="text-sm text-secondary mt-2">
            {agents.length === 0 
              ? "Create your first agent to get started!" 
              : `You have ${stats.activeAgents} active agent${stats.activeAgents !== 1 ? 's' : ''}`}
          </p>
        </div>
        <div className="header-actions">
          <Link href="/agents/new" className="btn btn-primary">
            <span>✨</span>
            <span>Create Agent</span>
          </Link>
        </div>
      </div>

      <div className="container" style={{ padding: "var(--space-8)" }}>
        {error && (
          <div className="card mb-6" style={{ background: "var(--color-error-muted)", borderColor: "var(--color-error)" }}>
            <p style={{ color: "var(--color-error)" }}>⚠️ {error}</p>
          </div>
        )}

        {/* Stats Grid */}
        <div className="grid grid-cols-4 mb-8">
          <StatCard label="Total Agents" value={stats.totalAgents.toString()} icon="🤖" />
          <StatCard label="Active Agents" value={stats.activeAgents.toString()} icon="✅" />
          <StatCard label="Total Executions" value={stats.totalExecutions.toString()} icon="⚡" />
          <StatCard label="Success Rate" value={`${stats.successRate.toFixed(1)}%`} icon="📈" />
        </div>

        <div className="grid grid-cols-2 gap-6">
          {/* Recent Agents */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Your Agents</h3>
              <Link href="/agents" className="btn btn-ghost btn-sm">View All →</Link>
            </div>

            {agents.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">🤖</div>
                <h4>No agents yet</h4>
                <p>Create your first AI agent to automate tasks</p>
                <Link href="/agents/new" className="btn btn-primary mt-4">Create Agent</Link>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {agents.slice(0, 4).map((agent) => (
                  <Link key={agent.id} href={`/agents/${agent.id}`} className="agent-list-item flex items-center justify-between p-4 rounded">
                    <div className="flex items-center gap-4">
                      <div style={{ width: 40, height: 40, borderRadius: "var(--radius-lg)", background: "var(--color-accent-muted)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.25rem" }}>
                        🤖
                      </div>
                      <div>
                        <div style={{ fontWeight: 500, color: "var(--color-text-primary)" }}>{agent.name}</div>
                        <div className="text-xs text-muted">
                          {agent.last_run_at ? `Last run: ${formatRelativeTime(agent.last_run_at)}` : 'Never run'}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`badge ${agent.status === "active" ? "badge-success" : "badge-neutral"}`}>
                        {agent.status}
                      </span>
                      <span className="text-sm text-muted">{agent.total_runs} runs</span>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </div>

          {/* Recent Executions */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">Recent Executions</h3>
              <Link href="/executions" className="btn btn-ghost btn-sm">View All →</Link>
            </div>

            {executions.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">⚡</div>
                <h4>No executions yet</h4>
                <p>Run an agent to see its execution history</p>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {executions.slice(0, 4).map((exec) => (
                  <div key={exec.id} className="flex items-center justify-between p-4 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
                    <div className="flex items-center gap-4">
                      <span className={`badge ${exec.status === "success" ? "badge-success" : exec.status === "failed" ? "badge-error" : "badge-neutral"}`}>
                        {exec.status === "success" ? "✓" : exec.status === "failed" ? "✗" : "◎"}
                      </span>
                      <div>
                        <div style={{ fontWeight: 500, color: "var(--color-text-primary)" }}>
                          {exec.agent_name || `Agent ${exec.agent_id.slice(0, 8)}...`}
                        </div>
                        <div className="text-xs text-muted">{formatRelativeTime(exec.created_at)}</div>
                      </div>
                    </div>
                    <div className="text-sm text-muted">
                      {exec.tokens_input + exec.tokens_output} tokens
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card mt-8">
          <h3 className="card-title mb-4">Quick Actions</h3>
          <div className="flex gap-4">
            <Link href="/agents/new" className="btn btn-secondary">
              <span>✨</span>
              <span>Create Agent</span>
            </Link>
            <Link href="/integrations" className="btn btn-secondary">
              <span>🔗</span>
              <span>Add Integration</span>
            </Link>
            <Link href="/skills" className="btn btn-secondary">
              <span>🔧</span>
              <span>Browse Skills</span>
            </Link>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

function StatCard({ label, value, icon }: { label: string; value: string; icon: string }) {
  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-card-label">{label}</span>
        <span className="stat-card-icon">{icon}</span>
      </div>
      <div className="stat-card-value">{value}</div>
    </div>
  );
}

function formatRelativeTime(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);
  
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}
