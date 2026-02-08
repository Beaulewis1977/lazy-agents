"use client";
import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { agentsAPI, executionsAPI, AgentConfig, Execution } from "@/lib/api";
import Link from "next/link";

export default function AgentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [agent, setAgent] = useState<AgentConfig | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'skills' | 'schedule' | 'logs' | 'history'>('overview');
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [selectedExecutionDetails, setSelectedExecutionDetails] = useState<{
    id: string;
    status: string;
    started_at: string | null;
    completed_at: string | null;
    tokens_input: number;
    tokens_output: number;
    output_data: Record<string, unknown> | null;
    error_message: string | null;
    steps: Array<{
      id: string;
      step_number: number;
      name: string;
      step_type: string;
      status: string;
      error_message: string | null;
    }>;
  } | null>(null);
  const [loadingExecution, setLoadingExecution] = useState(false);

  // Schedule state
  const [schedule, setSchedule] = useState<string>("");
  const [savingSchedule, setSavingSchedule] = useState(false);

  // Logs state
  const [logs, setLogs] = useState<Array<{ timestamp: string; level: string; message: string; source: string; execution_id?: string }>>([]);
  const wsRef = useRef<WebSocket | null>(null);

  const loadAgent = useCallback(async () => {
    try {
      setError(null);
      setLoading(true);
      const data = await agentsAPI.getConfig(id);
      setAgent(data);
      setSchedule(data.schedule || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load agent');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const loadExecutions = useCallback(async () => {
    try {
      const data = await executionsAPI.list(id, undefined, 50);
      setExecutions(data);
    } catch (err) {
      console.error('Failed to load executions', err);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      loadAgent();
    }
  }, [id, loadAgent]);

  useEffect(() => {
    // Load executions when history tab is active
    if (activeTab === 'history' && id) {
      loadExecutions();
    }

    // Connect to global logs when Logs tab is active
    if (activeTab === 'logs') {
      // Use standard WebSocket - assuming straightforward localhost default for now
      // In production, use window.location.host
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
        ws.close();
      };
    }
  }, [activeTab, id, loadExecutions]);

  async function handleToggleStatus() {
    if (!agent) return;
    const newStatus = agent.status === 'active' ? 'paused' : 'active';
    try {
      await agentsAPI.update(agent.id, { status: newStatus });
      setAgent({ ...agent, status: newStatus });
    } catch (err) {
      console.error('Failed to update status', err);
      alert('Failed to update status');
    }
  }

  async function handleRun() {
    if (!agent) return;
    try {
      await agentsAPI.run(agent.id);
      // Switch to history tab to see execution
      setActiveTab('history');
      // Reload executions
      await loadExecutions();
      // Set up polling for status updates
      const pollInterval = setInterval(async () => {
        const data = await executionsAPI.list(id, undefined, 50);
        setExecutions(data);
        // Stop polling if latest execution is complete
        if (data[0] && data[0].status !== 'pending' && data[0].status !== 'running') {
          clearInterval(pollInterval);
          loadAgent(); // Refresh stats
        }
      }, 3000);
      // Clear interval after 5 minutes max
      setTimeout(() => clearInterval(pollInterval), 300000);
    } catch (err) {
      console.error('Failed to run agent', err);
      alert('Failed to run agent');
    }
  }

  async function handleExecutionClick(executionId: string) {
    if (selectedExecutionId === executionId) {
      // Collapse
      setSelectedExecutionId(null);
      setSelectedExecutionDetails(null);
      return;
    }

    setSelectedExecutionId(executionId);
    setLoadingExecution(true);
    try {
      const details = await executionsAPI.get(executionId);
      setSelectedExecutionDetails(details);
    } catch (err) {
      console.error('Failed to load execution details', err);
      alert('Failed to load execution details');
    } finally {
      setLoadingExecution(false);
    }
  }

  async function handleDelete() {
    if (!agent || !confirm('Delete this agent?')) return;
    try {
      await agentsAPI.delete(agent.id);
      router.push('/agents');
    } catch (err) {
      console.error('Failed to delete agent', err);
      alert('Failed to delete agent');
    }
  }

  async function handleSaveSchedule() {
    if (!agent) return;
    try {
      setSavingSchedule(true);
      const newSchedule = schedule.trim() || null;
      await agentsAPI.update(agent.id, { schedule: newSchedule });
      // Refresh to get next run time
      const updated = await agentsAPI.getConfig(agent.id);
      setAgent(updated);
      alert('Schedule updated!');
    } catch (err) {
      console.error('Failed to update schedule', err);
      alert('Failed to update schedule');
    } finally {
      setSavingSchedule(false);
    }
  }

  if (loading) return (
    <DashboardLayout>
      <div className="container p-8 text-center">Loading...</div>
    </DashboardLayout>
  );

  if (error || !agent) return (
    <DashboardLayout>
      <div className="container p-8 text-error">Error: {error}</div>
    </DashboardLayout>
  );

  return (
    <DashboardLayout>
      <div className="header">
        <div className="flex items-center gap-4">
          <Link href="/agents" className="btn btn-ghost btn-sm">← Back</Link>
          <h1 className="header-title">{agent.name}</h1>
          <span className={`badge ${agent.status === 'active' ? 'badge-success' : 'badge-neutral'}`}>
            {agent.status}
          </span>
        </div>
        <div className="flex gap-2">
          <button onClick={handleRun} className="btn btn-primary">▶️ Run Now</button>
          <Link href={`/agents/${agent.id}/edit`} className="btn btn-secondary">✏️ Edit</Link>
          <button onClick={handleToggleStatus} className="btn btn-secondary">
            {agent.status === 'active' ? '⏸️ Pause' : '▶️ Activate'}
          </button>
          <button onClick={handleDelete} className="btn btn-ghost text-error">🗑️</button>
        </div>
      </div>

      <div className="container" style={{ padding: "var(--space-8)" }}>

        {/* Tabs */}
        <div className="tabs mb-6 border-b border-border flex gap-4 overflow-x-auto">
          {(['overview', 'skills', 'schedule', 'logs', 'history'] as const).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`pb-2 px-4 whitespace-nowrap ${activeTab === tab ? 'border-b-2 border-primary font-bold' : 'text-muted'}`}
              style={{ textTransform: 'capitalize' }}
            >
              {tab}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="md:col-span-2 space-y-6">
              <div className="card">
                <h3 className="mb-4">Description</h3>
                <p className="text-secondary whitespace-pre-wrap">{agent.description || "No description provided."}</p>
              </div>
              <div className="card">
                <h3 className="mb-4">System Prompt</h3>
                <pre className="bg-neutral-muted p-4 rounded text-sm whitespace-pre-wrap overflow-auto" style={{ maxHeight: 300 }}>
                  {agent.system_prompt}
                </pre>
              </div>
            </div>

            <div className="space-y-6">
              <div className="card">
                <h3 className="mb-4">Configuration</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted">Model</span>
                    <span>{agent.model}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Temperature</span>
                    <span>{agent.temperature}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Memory</span>
                    <span>{agent.memory_enabled ? 'Enabled' : 'Disabled'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted">Created</span>
                    <span>{new Date(agent.stats.last_run_at || Date.now()).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              <div className="card">
                <h3 className="mb-4">Stats</h3>
                <div className="grid grid-cols-2 gap-4 text-center">
                  <div className="p-2 bg-neutral-muted rounded">
                    <div className="text-2xl font-bold">{agent.stats.total_runs}</div>
                    <div className="text-xs text-muted">Total Runs</div>
                  </div>
                  <div className="p-2 bg-neutral-muted rounded">
                    <div className="text-2xl font-bold text-success">{agent.stats.success_rate.toFixed(0)}%</div>
                    <div className="text-xs text-muted">Success Rate</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === 'skills' && (
          <div className="space-y-6">
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h3 className="mb-0">Enabled Skills ({agent.skills.length})</h3>
                <Link href={`/skills`} className="btn btn-sm btn-ghost">Manage Skills →</Link>
              </div>

              {agent.skills.length === 0 ? (
                <p className="text-muted">No skills enabled.</p>
              ) : (
                <div className="grid grid-cols-1 gap-4">
                  {agent.skills.map(skill => (
                    <div key={skill.id} className="p-4 border border-border rounded flex justify-between items-center">
                      <div>
                        <div className="font-bold flex items-center gap-2">
                          {skill.name}
                          <span className="text-xs font-mono text-muted bg-neutral-muted px-1 rounded">{skill.id}</span>
                        </div>
                        <div className="text-sm text-muted">{skill.description}</div>
                      </div>
                      <div className="badge badge-neutral">{skill.category}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <h3 className="mb-4">Integrations ({agent.integrations.length})</h3>
              {agent.integrations.length === 0 ? (
                <p className="text-muted">No integrations connected.</p>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {agent.integrations.map(int => (
                    <div key={int.id} className="p-3 bg-neutral-muted rounded flex items-center justify-between">
                      <span className="font-medium">{int.name}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted">{int.type}</span>
                        <span className={`text-xs ${int.status === 'connected' ? 'text-success' : 'text-error'}`}>
                          ● {int.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Schedule Tab */}
        {activeTab === 'schedule' && (
          <div className="card max-w-2xl">
            <h3 className="mb-4">Automated Schedule</h3>
            <p className="text-secondary mb-6">
              Configure a cron schedule for this agent to run automatically.
            </p>

            <div className="input-group mb-6">
              <label className="input-label">Cron Expression</label>
              <input
                type="text"
                className="input font-mono"
                value={schedule}
                onChange={(e) => setSchedule(e.target.value)}
                placeholder="0 9 * * 1-5" // At 09:00 on every day-of-week from Monday through Friday.
              />
              <p className="text-xs text-muted mt-2">
                Examples: <br/>
                <code>0 * * * *</code> (Every hour)<br/>
                <code>0 9 * * *</code> (Every day at 9am)<br/>
                <code>*/15 * * * *</code> (Every 15 minutes)
              </p>
            </div>

            <div className="flex justify-between items-center pt-4 border-t border-border mt-4">
              <div>
                {agent.next_scheduled_run ? (
                  <p className="text-sm">
                    <span className="text-muted">Next run: </span>
                    <span className="text-success font-medium">{new Date(agent.next_scheduled_run).toLocaleString()}</span>
                  </p>
                ) : (
                  <p className="text-sm text-muted">No active schedule</p>
                )}
              </div>
              <button
                onClick={handleSaveSchedule}
                className="btn btn-primary"
                disabled={savingSchedule}
              >
                {savingSchedule ? 'Saving...' : 'Save Schedule'}
              </button>
            </div>
          </div>
        )}

        {/* Logs Tab */}
        {activeTab === 'logs' && (
          <div className="card h-[600px] flex flex-col p-0 overflow-hidden">
            <div className="p-4 border-b border-border bg-neutral-muted flex justify-between items-center">
              <h3 className="text-sm font-bold">Live System Logs</h3>
              <div className="flex gap-2 items-center">
                <span className="w-2 h-2 rounded-full bg-success animate-pulse"></span>
                <span className="text-xs text-muted">Connected</span>
              </div>
            </div>
            <div className="flex-1 overflow-auto p-4 font-mono text-xs space-y-1 bg-[#1e1e1e] text-gray-300">
              {logs.length === 0 && (
                <div className="text-muted text-center mt-10">Waiting for logs...</div>
              )}
              {logs.map((log, i) => (
                <div key={i} className="flex gap-3 hover:bg-white/5 p-1 rounded">
                  <span className="text-gray-500 shrink-0 w-24">{new Date(log.timestamp).toLocaleTimeString()}</span>
                  <span className={`shrink-0 w-16 font-bold ${
                    log.level === 'error' ? 'text-red-400' :
                    log.level === 'warn' ? 'text-yellow-400' : 'text-blue-400'
                  }`}>
                    {log.level.toUpperCase()}
                  </span>
                  <span className="text-gray-400 shrink-0 w-24">[{log.source}]</span>
                  <span className="break-all whitespace-pre-wrap">{log.message}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* History Tab */}
        {activeTab === 'history' && (
           <div className="card">
            {executions.length === 0 ? (
              <div className="empty-state">
                <div className="empty-state-icon">📜</div>
                <h3>No execution history</h3>
                <p>Run the agent to generate history.</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="border-b border-border text-sm text-muted">
                      <th className="p-3 font-medium">Status</th>
                      <th className="p-3 font-medium">Trigger</th>
                      <th className="p-3 font-medium">Started At</th>
                      <th className="p-3 font-medium">Duration</th>
                      <th className="p-3 font-medium">Tokens</th>
                      <th className="p-3 font-medium">Cost</th>
                      <th className="p-3 font-medium"></th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {executions.map((exec) => (
                      <>
                        <tr
                          key={exec.id}
                          className="border-b border-border/50 hover:bg-neutral-muted/50 cursor-pointer"
                          onClick={() => handleExecutionClick(exec.id)}
                        >
                          <td className="p-3">
                            <span className={`badge ${exec.status === 'success' ? 'badge-success' : exec.status === 'failed' ? 'badge-error' : 'badge-neutral'}`}>
                              {exec.status}
                            </span>
                          </td>
                          <td className="p-3"><span className="badge badge-neutral text-xs">{exec.trigger}</span></td>
                          <td className="p-3 text-secondary">{exec.started_at ? new Date(exec.started_at).toLocaleString() : '-'}</td>
                          <td className="p-3 text-secondary">
                            {exec.completed_at && exec.started_at ?
                              `${((new Date(exec.completed_at).getTime() - new Date(exec.started_at).getTime()) / 1000).toFixed(1)}s`
                              : '-'}
                          </td>
                          <td className="p-3 text-secondary">{(exec.tokens_input + exec.tokens_output).toLocaleString()}</td>
                          <td className="p-3 text-secondary">${(exec.cost_cents / 100).toFixed(4)}</td>
                          <td className="p-3 text-right">
                            <span className="text-xs text-muted">
                              {selectedExecutionId === exec.id ? '▼' : '▶'}
                            </span>
                          </td>
                        </tr>
                        {selectedExecutionId === exec.id && (
                          <tr>
                            <td colSpan={7} className="p-0">
                              <div className="p-6 border-t border-border" style={{ background: "var(--color-bg-primary)" }}>
                                {loadingExecution ? (
                                  <p className="text-secondary text-center">Loading execution details...</p>
                                ) : selectedExecutionDetails ? (
                                  <div className="flex flex-col gap-6">
                                    {/* Metadata */}
                                    <div className="grid grid-cols-4 gap-4 text-sm">
                                      <div>
                                        <span className="text-muted">Execution ID</span>
                                        <div className="font-mono text-xs mt-1">{selectedExecutionDetails.id.slice(0, 8)}</div>
                                      </div>
                                      <div>
                                        <span className="text-muted">Started</span>
                                        <div className="mt-1">{selectedExecutionDetails.started_at ? new Date(selectedExecutionDetails.started_at).toLocaleString() : '-'}</div>
                                      </div>
                                      <div>
                                        <span className="text-muted">Duration</span>
                                        <div className="mt-1">
                                          {selectedExecutionDetails.completed_at && selectedExecutionDetails.started_at ?
                                            `${((new Date(selectedExecutionDetails.completed_at).getTime() - new Date(selectedExecutionDetails.started_at).getTime()) / 1000).toFixed(1)}s`
                                            : '-'}
                                        </div>
                                      </div>
                                      <div>
                                        <span className="text-muted">Total Tokens</span>
                                        <div className="mt-1">{(selectedExecutionDetails.tokens_input + selectedExecutionDetails.tokens_output).toLocaleString()}</div>
                                      </div>
                                    </div>

                                    {/* Output Data */}
                                    {selectedExecutionDetails.output_data && (
                                      <div>
                                        <h4 className="mb-3 font-medium">Final Output</h4>
                                        <pre className="p-4 rounded text-sm overflow-x-auto" style={{ background: "var(--color-bg-tertiary)", maxHeight: 400 }}>
                                          {JSON.stringify(selectedExecutionDetails.output_data, null, 2)}
                                        </pre>
                                      </div>
                                    )}

                                    {/* Execution Steps */}
                                    {selectedExecutionDetails.steps && selectedExecutionDetails.steps.length > 0 && (
                                      <div>
                                        <h4 className="mb-3 font-medium">Execution Steps</h4>
                                        <div className="flex flex-col gap-3">
                                          {selectedExecutionDetails.steps.map((step) => (
                                            <div key={step.id} className="p-3 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
                                              <div className="flex items-center justify-between mb-2">
                                                <div className="flex items-center gap-2">
                                                  <span className="text-xs text-muted">#{step.step_number}</span>
                                                  <span className="font-medium">{step.name}</span>
                                                  <span className="badge badge-neutral text-xs">{step.step_type}</span>
                                                </div>
                                                <span className={`badge ${
                                                  step.status === 'success' ? 'badge-success' :
                                                  step.status === 'failed' ? 'badge-error' :
                                                  'badge-neutral'
                                                } text-xs`}>
                                                  {step.status}
                                                </span>
                                              </div>
                                              {step.error_message && (
                                                <p className="text-xs mt-2" style={{ color: "var(--color-error)" }}>
                                                  {step.error_message}
                                                </p>
                                              )}
                                            </div>
                                          ))}
                                        </div>
                                      </div>
                                    )}

                                    {/* Error Display */}
                                    {selectedExecutionDetails.error_message && (
                                      <div className="p-4 rounded" style={{ background: "var(--color-error-muted)" }}>
                                        <h4 className="mb-2 font-medium" style={{ color: "var(--color-error)" }}>Error</h4>
                                        <pre className="text-sm whitespace-pre-wrap" style={{ color: "var(--color-error)" }}>
                                          {selectedExecutionDetails.error_message}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <p className="text-error">Failed to load execution details</p>
                                )}
                              </div>
                            </td>
                          </tr>
                        )}
                      </>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
           </div>
        )}

      </div>
    </DashboardLayout>
  );
}
