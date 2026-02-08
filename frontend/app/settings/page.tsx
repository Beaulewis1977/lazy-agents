"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { healthAPI } from "@/lib/api";

interface Settings {
  openai_key: string;
  anthropic_key: string;
  google_key: string;
  default_model: string;
  api_key: string;
}

const SETTINGS_STORAGE_KEY = "lazyagents_settings";
const REDACTED_VALUE = "***REDACTED***";
const DEFAULT_SETTINGS: Settings = {
  openai_key: "",
  anthropic_key: "",
  google_key: "",
  default_model: "gpt-4o-mini",
  api_key: "",
};

interface PersistedSettings {
  default_model: string;
}

const MODELS = [
  { id: "gpt-4o-mini", name: "GPT-4o Mini (OpenAI)" },
  { id: "gpt-4o", name: "GPT-4o (OpenAI)" },
  { id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet (Anthropic)" },
  { id: "claude-3-5-haiku-20241022", name: "Claude 3.5 Haiku (Anthropic)" },
  { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro (Google)" },
];

export default function SettingsPage() {
  const [settings, setSettings] = useState<Settings>(() => {
    if (typeof window === "undefined") {
      return { ...DEFAULT_SETTINGS };
    }

    const persisted = localStorage.getItem(SETTINGS_STORAGE_KEY);
    if (!persisted) {
      return { ...DEFAULT_SETTINGS };
    }

    try {
      const parsed = JSON.parse(persisted) as Partial<Settings>;
      if (
        typeof parsed.openai_key === "string" ||
        typeof parsed.anthropic_key === "string" ||
        typeof parsed.google_key === "string" ||
        typeof parsed.api_key === "string"
      ) {
        localStorage.removeItem(SETTINGS_STORAGE_KEY);
        return { ...DEFAULT_SETTINGS };
      }
      if (typeof parsed.default_model === "string") {
        return { ...DEFAULT_SETTINGS, default_model: parsed.default_model };
      }
    } catch {
      localStorage.removeItem(SETTINGS_STORAGE_KEY);
    }

    return { ...DEFAULT_SETTINGS };
  });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [health, setHealth] = useState<{ status: string; version: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  function getPersistedSettings(next: Settings): PersistedSettings {
    return {
      default_model: next.default_model,
    };
  }

  function redactForExport(next: Settings): Settings {
    return {
      ...next,
      openai_key: next.openai_key ? REDACTED_VALUE : "",
      anthropic_key: next.anthropic_key ? REDACTED_VALUE : "",
      google_key: next.google_key ? REDACTED_VALUE : "",
      api_key: next.api_key ? REDACTED_VALUE : "",
    };
  }

  useEffect(() => {
    // Check health
    healthAPI.check()
      .then(setHealth)
      .catch(() => setError('Cannot connect to backend'));
  }, []);

  function handleSave() {
    setSaving(true);
    setSaved(false);

    // Persist only non-sensitive settings.
    localStorage.setItem(
      SETTINGS_STORAGE_KEY,
      JSON.stringify(getPersistedSettings(settings))
    );

    // In a real app, you'd also save to the backend
    setTimeout(() => {
      setSaving(false);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    }, 500);
  }

  function generateApiKey() {
    const key = 'la-' + Array.from(crypto.getRandomValues(new Uint8Array(24)))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('');
    setSettings({ ...settings, api_key: key });
  }

  function copyApiKey() {
    navigator.clipboard.writeText(settings.api_key);
    alert('API key copied to clipboard!');
  }

  return (
    <DashboardLayout>
      <div className="header">
        <h1 className="header-title">Settings</h1>
      </div>

      <div className="container" style={{ padding: "var(--space-8)", maxWidth: 800 }}>
        {error && (
          <div className="card mb-6" style={{ background: "var(--color-error-muted)" }}>
            <p style={{ color: "var(--color-error)" }}>⚠️ {error}</p>
          </div>
        )}

        {saved && (
          <div className="card mb-6" style={{ background: "var(--color-success-muted)" }}>
            <p style={{ color: "var(--color-success)" }}>✅ Settings saved successfully!</p>
          </div>
        )}

        {/* Backend Status */}
        <div className="card mb-6">
          <h3 className="mb-4">System Status</h3>
          <div className="flex items-center gap-4">
            <div className={`badge ${health ? 'badge-success' : 'badge-error'}`}>
              {health ? '● Connected' : '○ Disconnected'}
            </div>
            {health && (
              <>
                <span className="text-sm text-muted">Backend v{health.version}</span>
                <span className="text-sm text-muted">Status: {health.status}</span>
              </>
            )}
          </div>
        </div>

        {/* LLM Providers */}
        <div className="card mb-6">
          <h3 className="mb-4">LLM Providers</h3>
          <p className="text-sm text-secondary mb-6">
            Configure API keys for this session. Secret values stay masked and are not persisted in browser storage.
          </p>
          <div className="flex flex-col gap-4">
            <div className="input-group">
              <label className="input-label">OpenAI API Key</label>
              <input
                type="password"
                className="input"
                placeholder="sk-..."
                value={settings.openai_key}
                onChange={(e) => setSettings({ ...settings, openai_key: e.target.value })}
              />
            </div>
            <div className="input-group">
              <label className="input-label">Anthropic API Key</label>
              <input
                type="password"
                className="input"
                placeholder="sk-ant-..."
                value={settings.anthropic_key}
                onChange={(e) => setSettings({ ...settings, anthropic_key: e.target.value })}
              />
            </div>
            <div className="input-group">
              <label className="input-label">Google AI API Key</label>
              <input
                type="password"
                className="input"
                placeholder="AIza..."
                value={settings.google_key}
                onChange={(e) => setSettings({ ...settings, google_key: e.target.value })}
              />
            </div>
            <div className="input-group">
              <label className="input-label">Default Model</label>
              <select
                className="input"
                value={settings.default_model}
                onChange={(e) => setSettings({ ...settings, default_model: e.target.value })}
              >
                {MODELS.map((m) => (
                  <option key={m.id} value={m.id}>{m.name}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* API Access */}
        <div className="card mb-6">
          <h3 className="mb-4">API Access</h3>
          <p className="text-sm text-secondary mb-4">
            Use this key to authenticate API requests to your LazyAgents instance.
          </p>
          <div className="input-group">
            <label className="input-label">API Key</label>
            <div className="flex gap-2">
              <input
                type="password"
                className="input"
                value={settings.api_key || 'Not generated'}
                readOnly
                style={{ flex: 1 }}
              />
              <button onClick={copyApiKey} className="btn btn-secondary" disabled={!settings.api_key}>
                📋 Copy
              </button>
              <button onClick={generateApiKey} className="btn btn-ghost">
                🔄 Regenerate
              </button>
            </div>
          </div>
        </div>

        {/* Data & Privacy */}
        <div className="card mb-6">
          <h3 className="mb-4">Data & Privacy</h3>
          <p className="text-sm text-secondary mb-4">
            LazyAgents is self-hosted. All your data stays on your machine.
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => {
                if (confirm('Export all your data as JSON?')) {
                  const data = {
                    settings: redactForExport(settings),
                    preferences: getPersistedSettings(settings),
                    exportedAt: new Date().toISOString(),
                  };
                  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = 'lazyagents-export.json';
                  a.click();
                }
              }}
              className="btn btn-secondary"
            >
              📥 Export Data
            </button>
            <button
              onClick={() => {
                if (confirm('Clear all local settings? This cannot be undone.')) {
                  localStorage.removeItem(SETTINGS_STORAGE_KEY);
                  setSettings({ ...DEFAULT_SETTINGS });
                }
              }}
              className="btn btn-ghost"
            >
              🗑️ Clear Local Data
            </button>
          </div>
        </div>

        <button onClick={handleSave} className="btn btn-primary btn-lg" style={{ width: "100%" }} disabled={saving}>
          {saving ? '💾 Saving...' : '💾 Save Settings'}
        </button>
      </div>
    </DashboardLayout>
  );
}
