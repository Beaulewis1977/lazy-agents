"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";

import DashboardLayout from "@/components/DashboardLayout";
import SchemaRenderer from "@/components/SchemaRenderer";
import { MCPServer, mcpServersAPI } from "@/lib/api";

export default function MCPToolsPage() {
  const params = useParams();
  const serverId = params.id as string;

  const [server, setServer] = useState<MCPServer | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedTools, setExpandedTools] = useState<Set<string>>(new Set());
  const [syncing, setSyncing] = useState(false);

  const loadServer = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await mcpServersAPI.get(serverId);
      setServer(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load server');
    } finally {
      setLoading(false);
    }
  }, [serverId]);

  useEffect(() => {
    loadServer();
  }, [loadServer]);

  async function handleSync() {
    if (!server) return;

    try {
      setSyncing(true);
      setError(null);
      const updated = await mcpServersAPI.sync(serverId);
      setServer(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync server');
    } finally {
      setSyncing(false);
    }
  }

  function toggleTool(toolName: string) {
    setExpandedTools(prev => {
      const next = new Set(prev);
      if (next.has(toolName)) {
        next.delete(toolName);
      } else {
        next.add(toolName);
      }
      return next;
    });
  }

  function getStatusBadgeClass(status: string): string {
    switch (status) {
      case 'running':
        return 'badge-success';
      case 'error':
        return 'badge-error';
      case 'starting':
        return 'badge-info';
      case 'stopped':
      default:
        return 'badge-neutral';
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="container" style={{ paddingTop: 'var(--space-8)' }}>
          <div style={{ color: 'var(--color-text-secondary)' }}>Loading tools...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !server) {
    return (
      <DashboardLayout>
        <div className="container" style={{ paddingTop: 'var(--space-8)' }}>
          <div className="card" style={{ padding: 'var(--space-6)' }}>
            <h2 style={{ color: 'var(--color-error)', marginBottom: 'var(--space-4)' }}>Error</h2>
            <p style={{ color: 'var(--color-text-secondary)', marginBottom: 'var(--space-6)' }}>
              {error || 'Server not found'}
            </p>
            <button onClick={loadServer} className="btn btn-secondary">
              Retry
            </button>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  const tools = server.tools_detected || [];
  const toolCount = tools.length;

  return (
    <DashboardLayout>
      <div className="container" style={{ paddingTop: 'var(--space-8)', paddingBottom: 'var(--space-8)' }}>
        {/* Header */}
        <div style={{ marginBottom: 'var(--space-6)' }}>
          <Link href="/integrations/mcp" className="btn btn-ghost btn-sm" style={{ marginBottom: 'var(--space-4)' }}>
            ← Back to MCP Servers
          </Link>

          <div className="flex items-center gap-4" style={{ marginBottom: 'var(--space-2)' }}>
            <h1 className="header-title">{server.name} — Tools</h1>
            <span className={`badge ${getStatusBadgeClass(server.status)}`}>
              {server.status}
            </span>
          </div>

          <p className="text-secondary" style={{ fontSize: 'var(--font-size-sm)' }}>
            {toolCount} {toolCount === 1 ? 'tool' : 'tools'} discovered
          </p>
        </div>

        {/* Empty state */}
        {toolCount === 0 && (
          <div className="card">
            <div className="empty-state">
              <div className="empty-state-icon">🔧</div>
              <h3 className="empty-state-title">No Tools Detected</h3>
              <p className="empty-state-description">
                Try syncing the server to discover available tools.
              </p>
              <button
                onClick={handleSync}
                disabled={syncing}
                className="btn btn-primary"
              >
                {syncing ? 'Syncing...' : 'Sync Now'}
              </button>
            </div>
          </div>
        )}

        {/* Tool list */}
        {toolCount > 0 && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {tools.map((tool, index) => {
              // Access tool properties defensively since tools_detected is loosely typed
              const toolName = (tool.name as string) || `tool-${index}`;
              const toolTitle = tool.title as string | undefined;
              const toolDescription = tool.description as string | undefined;
              const inputSchema = tool.inputSchema as Record<string, unknown> | undefined;
              const outputSchema = tool.outputSchema as Record<string, unknown> | undefined;
              const isExpanded = expandedTools.has(toolName);

              return (
                <div key={toolName} className="card">
                  {/* Tool header */}
                  <div className="card-header">
                    <div>
                      <div className="flex items-center gap-2" style={{ marginBottom: 'var(--space-1)' }}>
                        <code
                          style={{
                            fontFamily: 'var(--font-mono)',
                            color: 'var(--color-accent)',
                            fontSize: 'var(--font-size-base)',
                            fontWeight: 'var(--font-weight-medium)',
                          }}
                        >
                          {toolName}
                        </code>
                        {toolTitle && (
                          <span style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
                            — {toolTitle}
                          </span>
                        )}
                      </div>
                      {toolDescription && (
                        <p className="card-description" style={{ margin: 0 }}>
                          {toolDescription}
                        </p>
                      )}
                    </div>

                    <button
                      onClick={() => toggleTool(toolName)}
                      className="btn btn-ghost btn-sm"
                    >
                      {isExpanded ? 'Collapse' : 'Expand Schema'}
                    </button>
                  </div>

                  {/* Expanded schema view */}
                  {isExpanded && (
                    <div style={{ marginTop: 'var(--space-4)' }}>
                      {/* Input schema */}
                      <div style={{ marginBottom: 'var(--space-6)' }}>
                        <h4
                          style={{
                            fontSize: 'var(--font-size-sm)',
                            fontWeight: 'var(--font-weight-semibold)',
                            color: 'var(--color-text-secondary)',
                            textTransform: 'uppercase',
                            letterSpacing: '0.05em',
                            marginBottom: 'var(--space-3)',
                          }}
                        >
                          Input Schema
                        </h4>
                        {inputSchema ? (
                          <SchemaRenderer schema={inputSchema} />
                        ) : (
                          <div style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>
                            No input schema defined
                          </div>
                        )}
                      </div>

                      {/* Output schema (optional per MCP spec) */}
                      {outputSchema && (
                        <div>
                          <h4
                            style={{
                              fontSize: 'var(--font-size-sm)',
                              fontWeight: 'var(--font-weight-semibold)',
                              color: 'var(--color-text-secondary)',
                              textTransform: 'uppercase',
                              letterSpacing: '0.05em',
                              marginBottom: 'var(--space-3)',
                            }}
                          >
                            Output Schema
                          </h4>
                          <SchemaRenderer schema={outputSchema} />
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Error display (if sync fails) */}
        {error && (
          <div
            className="card"
            style={{
              marginTop: 'var(--space-4)',
              borderColor: 'var(--color-error)',
              background: 'var(--color-error-muted)',
            }}
          >
            <p style={{ color: 'var(--color-error)', margin: 0 }}>{error}</p>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
