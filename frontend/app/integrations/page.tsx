"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { integrationsAPI, Integration } from "@/lib/api";

interface IntegrationType {
  type: string;
  name: string;
  description: string;
  required_credentials: string[];
}

const INTEGRATION_ICONS: Record<string, string> = {
  github: "🐙",
  discord: "💬",
  slack: "📱",
  notion: "📝",
  webhook: "🔗",
  openai: "🤖",
  anthropic: "🧠",
};

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [types, setTypes] = useState<IntegrationType[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState<string | null>(null);
  const [credentials, setCredentials] = useState<Record<string, string>>({});
  const [integrationName, setIntegrationName] = useState("");
  const [creating, setCreating] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    try {
      const [integsList, typesList] = await Promise.all([
        integrationsAPI.list(),
        integrationsAPI.types(),
      ]);
      setIntegrations(integsList);
      setTypes(typesList);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load integrations');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate() {
    if (!showCreate || !integrationName) return;
    const typeInfo = types.find(t => t.type === showCreate);
    if (!typeInfo) return;

    // Check required fields
    const missing = typeInfo.required_credentials.filter((f: string) => !credentials[f]);
    if (missing.length > 0) {
      setError(`Missing required fields: ${missing.join(', ')}`);
      return;
    }

    setCreating(true);
    setError(null);
    try {
      const integration = await integrationsAPI.create({
        type: showCreate,
        name: integrationName,
        credentials,
      });
      setIntegrations([...integrations, integration]);
      setShowCreate(null);
      setCredentials({});
      setIntegrationName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create integration');
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm('Remove this integration?')) return;
    try {
      await integrationsAPI.delete(id);
      setIntegrations(integrations.filter(i => i.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete integration');
    }
  }

  async function handleTest(id: string) {
    setTesting(id);
    try {
      const result = await integrationsAPI.test(id);
      alert(result.success ? '✅ Connection successful!' : `❌ ${result.message}`);
    } catch (err) {
      alert(`❌ ${err instanceof Error ? err.message : 'Test failed'}`);
    } finally {
      setTesting(null);
    }
  }

  function startCreate(type: string) {
    const typeInfo = types.find(t => t.type === type);
    setShowCreate(type);
    setIntegrationName(typeInfo?.name || type);
    setCredentials({});
    setError(null);
  }

  if (loading) return (
    <DashboardLayout>
      <div className="container" style={{ padding: "var(--space-8)", textAlign: "center" }}>
        <div style={{ fontSize: "2rem", marginBottom: "var(--space-4)" }}>⏳</div>
        <p className="text-secondary">Loading integrations...</p>
      </div>
    </DashboardLayout>
  );

  const activeType = types.find(t => t.type === showCreate);

  return (
    <DashboardLayout>
      <div className="header">
        <div>
          <h1 className="header-title">Integrations</h1>
          <p className="text-sm text-secondary mt-2">
            {integrations.length} integration{integrations.length !== 1 ? 's' : ''} connected
          </p>
        </div>
      </div>

      <div className="container" style={{ padding: "var(--space-8)" }}>
        {error && (
          <div className="card mb-6" style={{ background: "var(--color-error-muted)" }}>
            <p style={{ color: "var(--color-error)" }}>⚠️ {error}</p>
            <button onClick={() => setError(null)} className="btn btn-ghost btn-sm mt-2">Dismiss</button>
          </div>
        )}

        {/* Create Modal */}
        {showCreate && activeType && (
          <div className="card mb-6" style={{ border: "2px solid var(--color-accent)" }}>
            <div className="flex items-center justify-between mb-4">
              <h3>Connect {activeType.name}</h3>
              <button onClick={() => setShowCreate(null)} className="btn btn-ghost btn-sm">✕</button>
            </div>
            <div className="flex flex-col gap-4">
              <div className="input-group">
                <label className="input-label">Name</label>
                <input
                  type="text"
                  className="input"
                  value={integrationName}
                  onChange={(e) => setIntegrationName(e.target.value)}
                  placeholder="My GitHub"
                />
              </div>
              {activeType.required_credentials.map((field: string) => (
                <div key={field} className="input-group">
                  <label className="input-label">{field.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())} *</label>
                  <input
                    type={field.includes('token') || field.includes('secret') || field.includes('key') ? 'password' : 'text'}
                    className="input"
                    value={credentials[field] || ''}
                    onChange={(e) => setCredentials({ ...credentials, [field]: e.target.value })}
                    placeholder={`Enter ${field}`}
                  />
                </div>
              ))}
              <div className="flex gap-2">
                <button onClick={handleCreate} className="btn btn-primary" disabled={creating}>
                  {creating ? 'Connecting...' : 'Connect'}
                </button>
                <button onClick={() => setShowCreate(null)} className="btn btn-ghost">Cancel</button>
              </div>
            </div>
          </div>
        )}

        {/* Connected Integrations */}
        {integrations.length > 0 && (
          <div className="mb-8">
            <h3 className="mb-4">Connected</h3>
            <div className="grid grid-cols-2 gap-4">
              {integrations.map((integration) => (
                <div key={integration.id} className="card flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div style={{
                      width: 48, height: 48, borderRadius: "var(--radius-lg)",
                      background: integration.status === 'connected' ? "var(--color-success-muted)" : "var(--color-bg-tertiary)",
                      display: "flex", alignItems: "center", justifyContent: "center", fontSize: "1.5rem"
                    }}>
                      {INTEGRATION_ICONS[integration.type] || "🔗"}
                    </div>
                    <div>
                      <h4>{integration.name}</h4>
                      <span className={`badge ${integration.status === 'connected' ? 'badge-success' : 'badge-error'}`}>
                        {integration.status}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleTest(integration.id)}
                      className="btn btn-ghost btn-sm"
                      disabled={testing === integration.id}
                    >
                      {testing === integration.id ? '...' : '🔍 Test'}
                    </button>
                    <button onClick={() => handleDelete(integration.id)} className="btn btn-ghost btn-sm">
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Available Integrations */}
        <h3 className="mb-4">Available Integrations</h3>
        <div className="grid grid-cols-3 gap-4">
          {types.map((type) => {
            const isConnected = integrations.some(i => i.type === type.type);
            return (
              <div key={type.type} className="card">
                <div className="flex items-center gap-3 mb-3">
                  <div style={{ fontSize: "2rem" }}>{INTEGRATION_ICONS[type.type] || "🔗"}</div>
                  <div>
                    <h4>{type.name}</h4>
                    {isConnected && <span className="badge badge-success">connected</span>}
                  </div>
                </div>
                <p className="text-sm text-secondary mb-4">{type.description}</p>
                <button
                  onClick={() => startCreate(type.type)}
                  className="btn btn-secondary btn-sm"
                  style={{ width: "100%" }}
                >
                  {isConnected ? '+ Add Another' : 'Connect'}
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}
