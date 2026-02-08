"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";

import DashboardLayout from "@/components/DashboardLayout";
import {
  MCPServer,
  MCPServerCreateInput,
  MCPServerUpdateInput,
  mcpServersAPI,
} from "@/lib/api";

type FormMode = "create" | "edit";

interface FormState {
  name: string;
  description: string;
  command: string;
  argsText: string;
  envText: string;
  enabled: boolean;
}

const initialFormState: FormState = {
  name: "",
  description: "",
  command: "",
  argsText: "",
  envText: "",
  enabled: true,
};

function parseArgs(argsText: string): string[] {
  return argsText
    .split(/\r?\n|,/)
    .map((arg) => arg.trim())
    .filter(Boolean);
}

function parseEnv(envText: string): Record<string, string> {
  const env: Record<string, string> = {};
  const lines = envText
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);

  for (const line of lines) {
    const idx = line.indexOf("=");
    if (idx <= 0) {
      throw new Error(`Invalid env line: \"${line}\". Use KEY=VALUE format.`);
    }

    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1);

    if (!key) {
      throw new Error("Environment variable keys must not be blank.");
    }

    env[key] = value;
  }

  return env;
}

function statusBadgeClass(status: MCPServer["status"]): string {
  if (status === "running") return "badge badge-success";
  if (status === "starting") return "badge badge-info";
  if (status === "error") return "badge badge-error";
  return "badge badge-neutral";
}

export default function MCPIntegrationsPage() {
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [formMode, setFormMode] = useState<FormMode | null>(null);
  const [editingServerId, setEditingServerId] = useState<string | null>(null);
  const [formState, setFormState] = useState<FormState>(initialFormState);

  const [submitting, setSubmitting] = useState(false);
  const [actionServerId, setActionServerId] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<MCPServer | null>(null);
  const deleteDialogRef = useRef<HTMLDivElement | null>(null);
  const cancelDeleteRef = useRef<HTMLButtonElement | null>(null);
  const confirmDeleteRef = useRef<HTMLButtonElement | null>(null);
  const deleteConfirmResolverRef = useRef<((value: boolean) => void) | null>(null);

  const editingServer = useMemo(
    () => servers.find((server) => server.id === editingServerId) ?? null,
    [servers, editingServerId]
  );

  useEffect(() => {
    // Initial server fetch runs once when this page mounts.
    void loadServers();
  }, []);

  useEffect(() => {
    if (!deleteTarget) {
      return;
    }

    const previouslyFocused = document.activeElement as HTMLElement | null;
    const focusables = () =>
      Array.from(
        deleteDialogRef.current?.querySelectorAll<HTMLElement>(
          "button,[href],input,select,textarea,[tabindex]:not([tabindex='-1'])"
        ) ?? []
      ).filter((element) => !element.hasAttribute("disabled"));

    cancelDeleteRef.current?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (!deleteTarget) {
        return;
      }

      if (event.key === "Escape") {
        event.preventDefault();
        resolveDeleteConfirmation(false);
        return;
      }

      if (event.key !== "Tab") {
        return;
      }

      const nodes = focusables();
      if (nodes.length === 0) {
        event.preventDefault();
        return;
      }

      const first = nodes[0];
      const last = nodes[nodes.length - 1];
      const active = document.activeElement as HTMLElement | null;

      if (event.shiftKey && active === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      previouslyFocused?.focus();
    };
  }, [deleteTarget]);

  async function loadServers() {
    setError(null);
    try {
      const data = await mcpServersAPI.list();
      setServers(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load MCP servers.");
    } finally {
      setLoading(false);
    }
  }

  function openCreate() {
    setFormMode("create");
    setEditingServerId(null);
    setFormState(initialFormState);
    setError(null);
  }

  function openEdit(server: MCPServer) {
    setFormMode("edit");
    setEditingServerId(server.id);
    setFormState({
      name: server.name,
      description: server.description ?? "",
      command: server.command,
      argsText: (server.args || []).join("\n"),
      envText: "",
      enabled: server.enabled,
    });
    setError(null);
  }

  function closeForm() {
    setFormMode(null);
    setEditingServerId(null);
    setFormState(initialFormState);
  }

  function requestDeleteConfirmation(server: MCPServer): Promise<boolean> {
    setDeleteTarget(server);
    return new Promise((resolve) => {
      deleteConfirmResolverRef.current = resolve;
    });
  }

  function resolveDeleteConfirmation(confirmed: boolean) {
    const resolver = deleteConfirmResolverRef.current;
    deleteConfirmResolverRef.current = null;
    setDeleteTarget(null);
    resolver?.(confirmed);
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    try {
      const parsedArgs = parseArgs(formState.argsText);
      const payloadBase = {
        name: formState.name,
        description: formState.description || null,
        command: formState.command,
        args: parsedArgs,
        enabled: formState.enabled,
      };

      if (formMode === "create") {
        const payload: MCPServerCreateInput = {
          ...payloadBase,
          env: parseEnv(formState.envText),
        };
        await mcpServersAPI.create(payload);
      } else if (formMode === "edit" && editingServer) {
        const payload: MCPServerUpdateInput = payloadBase;
        if (formState.envText.trim()) {
          payload.env = parseEnv(formState.envText);
          payload.merge_env = true;
        }
        await mcpServersAPI.update(editingServer.id, payload);
      }

      await loadServers();
      closeForm();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save MCP server.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDelete(server: MCPServer) {
    const confirmed = await requestDeleteConfirmation(server);
    if (!confirmed) {
      return;
    }

    setActionServerId(server.id);
    setError(null);

    try {
      await mcpServersAPI.remove(server.id);
      await loadServers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete MCP server.");
    } finally {
      setActionServerId(null);
    }
  }

  async function handleLifecycleAction(server: MCPServer, action: "restart" | "sync") {
    setActionServerId(server.id);
    setError(null);

    try {
      if (action === "restart") {
        await mcpServersAPI.restart(server.id);
      } else {
        await mcpServersAPI.sync(server.id);
      }
      await loadServers();
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action} MCP server.`);
    } finally {
      setActionServerId(null);
    }
  }

  return (
    <DashboardLayout>
      <div className="header">
        <div>
          <h1 className="header-title">MCP Servers</h1>
          <p className="text-sm text-secondary mt-2">
            Manage MCP server configs and lifecycle operations.
          </p>
        </div>
        <button className="btn btn-primary" onClick={openCreate}>
          + Add MCP Server
        </button>
      </div>

      <div className="container" style={{ padding: "var(--space-8)" }}>
        {error && (
          <div className="card mb-6" style={{ background: "var(--color-error-muted)" }}>
            <p style={{ color: "var(--color-error)", marginBottom: 0 }}>{error}</p>
          </div>
        )}

        {formMode && (
          <form className="card mb-6" onSubmit={handleSubmit}>
            <div className="flex items-center justify-between mb-4">
              <h3>{formMode === "create" ? "Create MCP Server" : "Edit MCP Server"}</h3>
              <button type="button" className="btn btn-ghost btn-sm" onClick={closeForm}>
                Close
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="input-group">
                <label className="input-label" htmlFor="mcp-server-name">
                  Name
                </label>
                <input
                  id="mcp-server-name"
                  className="input"
                  value={formState.name}
                  onChange={(event) =>
                    setFormState((state) => ({ ...state, name: event.target.value }))
                  }
                  required
                />
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="mcp-server-command">
                  Command
                </label>
                <input
                  id="mcp-server-command"
                  className="input"
                  value={formState.command}
                  onChange={(event) =>
                    setFormState((state) => ({ ...state, command: event.target.value }))
                  }
                  placeholder="npx"
                  required
                />
              </div>

              <div className="input-group" style={{ gridColumn: "1 / -1" }}>
                <label className="input-label" htmlFor="mcp-server-description">
                  Description
                </label>
                <input
                  id="mcp-server-description"
                  className="input"
                  value={formState.description}
                  onChange={(event) =>
                    setFormState((state) => ({ ...state, description: event.target.value }))
                  }
                  placeholder="Optional description"
                />
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="mcp-server-args">
                  Args (comma or newline separated)
                </label>
                <textarea
                  id="mcp-server-args"
                  className="input textarea"
                  value={formState.argsText}
                  onChange={(event) =>
                    setFormState((state) => ({ ...state, argsText: event.target.value }))
                  }
                  placeholder="@modelcontextprotocol/server-filesystem\n/tmp"
                />
              </div>

              <div className="input-group">
                <label className="input-label" htmlFor="mcp-server-env">
                  Env vars (KEY=VALUE per line)
                </label>
                <textarea
                  id="mcp-server-env"
                  className="input textarea"
                  value={formState.envText}
                  onChange={(event) =>
                    setFormState((state) => ({ ...state, envText: event.target.value }))
                  }
                  placeholder="API_TOKEN=your-token"
                />
                {formMode === "edit" && (
                  <p className="text-xs text-secondary" style={{ marginBottom: 0 }}>
                    Leave env empty to keep existing values. Entered keys merge with stored env.
                  </p>
                )}
              </div>
            </div>

            <div className="flex items-center gap-2 mt-4">
              <label
                className="input-label"
                htmlFor="mcp-server-enabled"
                style={{ marginBottom: 0 }}
              >
                <input
                  id="mcp-server-enabled"
                  type="checkbox"
                  checked={formState.enabled}
                  onChange={(event) =>
                    setFormState((state) => ({ ...state, enabled: event.target.checked }))
                  }
                  style={{ marginRight: "var(--space-2)" }}
                />
                Enabled
              </label>
            </div>

            <div className="flex gap-2 mt-6">
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? "Saving..." : formMode === "create" ? "Create" : "Update"}
              </button>
              <button type="button" className="btn btn-ghost" onClick={closeForm}>
                Cancel
              </button>
            </div>
          </form>
        )}

        {loading ? (
          <div className="card">
            <p className="text-secondary" style={{ marginBottom: 0 }}>
              Loading MCP servers...
            </p>
          </div>
        ) : servers.length === 0 ? (
          <div className="empty-state card">
            <div className="empty-state-icon">🧩</div>
            <h3 className="empty-state-title">No MCP servers configured</h3>
            <p className="empty-state-description">
              Add your first MCP server to start managing tools in the control plane.
            </p>
            <button className="btn btn-primary" onClick={openCreate}>
              Add MCP Server
            </button>
          </div>
        ) : (
          <div className="table-wrapper">
            <table className="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Command</th>
                  <th>Status</th>
                  <th>Tools</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {servers.map((server) => {
                  const busy = actionServerId === server.id;
                  return (
                    <tr key={server.id}>
                      <td>
                        <strong>{server.name}</strong>
                        {server.description ? (
                          <p className="text-xs text-secondary mt-1" style={{ marginBottom: 0 }}>
                            {server.description}
                          </p>
                        ) : null}
                      </td>
                      <td>
                        <code>{server.command}</code>
                      </td>
                      <td>
                        <span className={statusBadgeClass(server.status)}>
                          {server.status}
                        </span>
                      </td>
                      <td>{server.tools_detected?.length ?? 0}</td>
                      <td>
                        <div className="flex gap-2">
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => void handleLifecycleAction(server, "restart")}
                            disabled={busy}
                          >
                            Restart
                          </button>
                          <button
                            className="btn btn-secondary btn-sm"
                            onClick={() => void handleLifecycleAction(server, "sync")}
                            disabled={busy}
                          >
                            Sync
                          </button>
                          <button
                            className="btn btn-ghost btn-sm"
                            onClick={() => openEdit(server)}
                            disabled={busy}
                          >
                            Edit
                          </button>
                          <button
                            className="btn btn-danger btn-sm"
                            onClick={() => void handleDelete(server)}
                            disabled={busy}
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {servers.some((server) => server.status === "error" && server.last_error) && (
          <div className="card mt-6" style={{ border: "1px solid var(--color-error)" }}>
            <h3 className="mb-4">Server Errors</h3>
            <div className="flex flex-col gap-4">
              {servers
                .filter((server) => server.status === "error" && server.last_error)
                .map((server) => (
                  <div
                    key={`error-${server.id}`}
                    style={{
                      background: "var(--color-error-muted)",
                      borderRadius: "var(--radius-lg)",
                      padding: "var(--space-4)",
                    }}
                  >
                    <p style={{ marginBottom: "var(--space-2)" }}>
                      <strong>{server.name}</strong>
                    </p>
                    <p className="text-sm" style={{ marginBottom: "var(--space-2)" }}>
                      {server.last_error}
                    </p>
                    <p className="text-xs text-secondary" style={{ marginBottom: 0 }}>
                      Guidance: verify command/env configuration, then run Restart or Sync.
                    </p>
                  </div>
                ))}
            </div>
          </div>
        )}

        {deleteTarget && (
          <div
            role="presentation"
            style={{
              position: "fixed",
              inset: 0,
              background: "rgba(0, 0, 0, 0.45)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              zIndex: 50,
              padding: "var(--space-4)",
            }}
            onMouseDown={(event) => {
              if (event.target === event.currentTarget) {
                resolveDeleteConfirmation(false);
              }
            }}
          >
            <div
              ref={deleteDialogRef}
              role="dialog"
              aria-modal="true"
              aria-labelledby="delete-mcp-server-title"
              aria-describedby="delete-mcp-server-description"
              className="card"
              style={{ width: "100%", maxWidth: 560 }}
            >
              <h3 id="delete-mcp-server-title" className="mb-3">
                Delete MCP server
              </h3>
              <p id="delete-mcp-server-description" className="text-sm text-secondary mb-4">
                Delete <strong>{deleteTarget.name}</strong>? This removes the saved configuration
                and runtime state.
              </p>
              <div className="flex gap-2 justify-end">
                <button
                  ref={cancelDeleteRef}
                  type="button"
                  className="btn btn-ghost"
                  onClick={() => resolveDeleteConfirmation(false)}
                >
                  Cancel
                </button>
                <button
                  ref={confirmDeleteRef}
                  type="button"
                  className="btn btn-danger"
                  onClick={() => resolveDeleteConfirmation(true)}
                >
                  Delete
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
