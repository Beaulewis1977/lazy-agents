"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { api } from "@/lib/api";

interface SkillParameter {
  type?: string;
  description?: string;
  default?: unknown;
  enum?: string[];
}

interface SkillConfig {
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
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Request failed";
}

export default function SkillDetailPage() {
  const params = useParams();
  const router = useRouter();
  const skillId = params.id as string;

  const [skill, setSkill] = useState<SkillConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [editData, setEditData] = useState({
    name: "",
    description: "",
    category: "",
    implementation: "",
  });
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<"overview" | "parameters" | "implementation" | "files">("overview");

  const loadSkill = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.skills.getConfig(skillId);
      setSkill(data);
      setEditData({
        name: data.name,
        description: data.description || "",
        category: data.category,
        implementation: data.implementation || "",
      });
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [skillId]);

  useEffect(() => {
    void loadSkill();
  }, [loadSkill]);

  async function handleSave() {
    try {
      setSaving(true);
      await api.skills.update(skillId, editData);
      await loadSkill();
      setEditing(false);
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete() {
    if (!confirm("Are you sure you want to delete this skill?")) return;

    try {
      await api.skills.delete(skillId);
      router.push("/skills");
    } catch (err: unknown) {
      setError(getErrorMessage(err));
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Loading skill...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !skill) {
    return (
      <DashboardLayout>
        <div className="error-container">
          <h2>Error</h2>
          <p>{error || "Skill not found"}</p>
          <button onClick={() => router.push("/skills")} className="btn-secondary">
            Back to Skills
          </button>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="skill-detail-page">
        {/* Header */}
        <div className="page-header">
          <div className="header-left">
            <button onClick={() => router.push("/skills")} className="back-btn">
              ← Back
            </button>
            <div className="header-info">
              <h1>{skill.name}</h1>
              <div className="header-badges">
                <span className={`badge badge-${skill.category}`}>{skill.category}</span>
                {skill.is_builtin && <span className="badge badge-builtin">Built-in</span>}
                {skill.integration_required && (
                  <span className="badge badge-integration">Requires: {skill.integration_required}</span>
                )}
              </div>
            </div>
          </div>
          <div className="header-actions">
            {!skill.is_builtin && (
              <>
                <button onClick={() => setEditing(!editing)} className="btn-secondary">
                  {editing ? "Cancel" : "Edit"}
                </button>
                <button onClick={handleDelete} className="btn-danger">
                  Delete
                </button>
              </>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs">
          <button
            className={`tab ${activeTab === "overview" ? "active" : ""}`}
            onClick={() => setActiveTab("overview")}
          >
            Overview
          </button>
          <button
            className={`tab ${activeTab === "parameters" ? "active" : ""}`}
            onClick={() => setActiveTab("parameters")}
          >
            Parameters
          </button>
          <button
            className={`tab ${activeTab === "implementation" ? "active" : ""}`}
            onClick={() => setActiveTab("implementation")}
          >
            Implementation
          </button>
          {(skill.source_path || Object.keys(skill.templates).length > 0) && (
            <button
              className={`tab ${activeTab === "files" ? "active" : ""}`}
              onClick={() => setActiveTab("files")}
            >
              Files
            </button>
          )}
        </div>

        {/* Content */}
        <div className="tab-content">
          {activeTab === "overview" && (
            <div className="overview-section">
              {editing ? (
                <div className="edit-form">
                  <div className="form-group">
                    <label>Name</label>
                    <input
                      type="text"
                      value={editData.name}
                      onChange={(e) => setEditData({ ...editData, name: e.target.value })}
                    />
                  </div>
                  <div className="form-group">
                    <label>Description</label>
                    <textarea
                      value={editData.description}
                      onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                      rows={4}
                    />
                  </div>
                  <div className="form-group">
                    <label>Category</label>
                    <input
                      type="text"
                      value={editData.category}
                      onChange={(e) => setEditData({ ...editData, category: e.target.value })}
                    />
                  </div>
                  <div className="form-actions">
                    <button onClick={handleSave} className="btn-primary" disabled={saving}>
                      {saving ? "Saving..." : "Save Changes"}
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <div className="info-card">
                    <h3>Description</h3>
                    <p>{skill.description || "No description provided"}</p>
                  </div>
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="label">ID</span>
                      <code>{skill.id}</code>
                    </div>
                    <div className="info-item">
                      <span className="label">Category</span>
                      <span>{skill.category}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">Type</span>
                      <span>{skill.is_builtin ? "Built-in" : "Custom"}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">Implementation</span>
                      <span>{skill.implementation_type}</span>
                    </div>
                    {skill.integration_required && (
                      <div className="info-item">
                        <span className="label">Required Integration</span>
                        <span>{skill.integration_required}</span>
                      </div>
                    )}
                    {skill.source_path && (
                      <div className="info-item full-width">
                        <span className="label">Source Path</span>
                        <code>{skill.source_path}</code>
                      </div>
                    )}
                  </div>
                </>
              )}
            </div>
          )}

          {activeTab === "parameters" && (
            <div className="parameters-section">
              <h3>Parameters</h3>
              {Object.keys(skill.parameters).length === 0 ? (
                <p className="empty-message">This skill has no parameters</p>
              ) : (
                <div className="parameters-list">
                  {Object.entries(skill.parameters).map(([name, rawParam]) => {
                    const param: SkillParameter =
                      rawParam && typeof rawParam === "object"
                        ? (rawParam as SkillParameter)
                        : {};
                    const enumValues = Array.isArray(param.enum) ? param.enum : [];

                    return (
                      <div key={name} className="parameter-card">
                        <div className="param-header">
                          <code className="param-name">{name}</code>
                          <span className="param-type">{param.type ?? "unknown"}</span>
                        </div>
                        <p className="param-description">
                          {param.description ?? "No description"}
                        </p>
                        {param.default !== undefined && (
                          <div className="param-default">
                            Default: <code>{JSON.stringify(param.default)}</code>
                          </div>
                        )}
                        {enumValues.length > 0 && (
                          <div className="param-enum">
                            Options: {enumValues.map((value) => (
                              <code key={value}>{value}</code>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          )}

          {activeTab === "implementation" && (
            <div className="implementation-section">
              <h3>Implementation</h3>
              {skill.is_builtin ? (
                <div className="builtin-notice">
                  <p>This is a built-in skill implemented natively in the backend.</p>
                </div>
              ) : editing ? (
                <div className="edit-form">
                  <div className="form-group">
                    <label>Instructions</label>
                    <textarea
                      value={editData.implementation}
                      onChange={(e) => setEditData({ ...editData, implementation: e.target.value })}
                      rows={20}
                      className="code-editor"
                    />
                  </div>
                  <div className="form-actions">
                    <button onClick={handleSave} className="btn-primary" disabled={saving}>
                      {saving ? "Saving..." : "Save Changes"}
                    </button>
                  </div>
                </div>
              ) : (
                <pre className="implementation-code">
                  {skill.implementation || "No implementation details"}
                </pre>
              )}
            </div>
          )}

          {activeTab === "files" && (
            <div className="files-section">
              {skill.source_path && (
                <div className="source-info">
                  <h3>Source Location</h3>
                  <code>{skill.source_path}</code>
                </div>
              )}

              {Object.keys(skill.templates).length > 0 && (
                <div className="templates-section">
                  <h3>Templates</h3>
                  <div className="templates-list">
                    {Object.entries(skill.templates).map(([name, content]) => (
                      <div key={name} className="template-card">
                        <div className="template-header">
                          <span className="template-name">{name}</span>
                        </div>
                        <pre className="template-content">{content}</pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {skill.references.length > 0 && (
                <div className="references-section">
                  <h3>References ({skill.references.length})</h3>
                  <div className="references-list">
                    {skill.references.map((ref, i) => (
                      <div key={i} className="reference-card">
                        <pre>{ref.substring(0, 500)}...</pre>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .skill-detail-page {
          padding: 0;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          margin-bottom: 2rem;
          padding-bottom: 1.5rem;
          border-bottom: 1px solid var(--border-color);
        }

        .header-left {
          display: flex;
          align-items: flex-start;
          gap: 1rem;
        }

        .back-btn {
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          padding: 0.5rem;
          font-size: 1rem;
          transition: color 0.2s;
        }

        .back-btn:hover {
          color: var(--text-primary);
        }

        .header-info h1 {
          margin: 0 0 0.5rem 0;
          font-size: 1.75rem;
        }

        .header-badges {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .badge {
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
          font-size: 0.75rem;
          font-weight: 500;
        }

        .badge-github { background: #24292e; color: white; }
        .badge-discord { background: #5865f2; color: white; }
        .badge-http { background: #ff6b6b; color: white; }
        .badge-file { background: #ffd43b; color: #333; }
        .badge-custom { background: var(--primary); color: white; }
        .badge-builtin { background: linear-gradient(135deg, #667eea, #764ba2); color: white; }
        .badge-integration { background: rgba(var(--primary-rgb), 0.15); color: var(--primary); }

        .header-actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn-primary,
        .btn-secondary,
        .btn-danger {
          padding: 0.5rem 1rem;
          border-radius: 8px;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          border: none;
        }

        .btn-primary {
          background: var(--primary);
          color: white;
        }

        .btn-secondary {
          background: var(--bg-tertiary);
          color: var(--text-primary);
          border: 1px solid var(--border-color);
        }

        .btn-danger {
          background: #dc3545;
          color: white;
        }

        .btn-primary:hover { filter: brightness(1.1); }
        .btn-secondary:hover { background: var(--bg-secondary); }
        .btn-danger:hover { filter: brightness(1.1); }

        .tabs {
          display: flex;
          gap: 0.25rem;
          background: var(--bg-tertiary);
          border-radius: 12px;
          padding: 0.25rem;
          margin-bottom: 1.5rem;
        }

        .tab {
          flex: 1;
          padding: 0.75rem 1rem;
          background: none;
          border: none;
          color: var(--text-secondary);
          cursor: pointer;
          border-radius: 10px;
          transition: all 0.2s;
          font-weight: 500;
        }

        .tab:hover {
          color: var(--text-primary);
        }

        .tab.active {
          background: var(--bg-primary);
          color: var(--text-primary);
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .tab-content {
          background: var(--bg-secondary);
          border-radius: 12px;
          padding: 1.5rem;
        }

        .info-card {
          margin-bottom: 1.5rem;
        }

        .info-card h3 {
          margin: 0 0 0.5rem 0;
          color: var(--text-secondary);
          font-size: 0.875rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .info-card p {
          margin: 0;
          line-height: 1.6;
        }

        .info-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 1rem;
        }

        .info-item {
          padding: 1rem;
          background: var(--bg-tertiary);
          border-radius: 8px;
        }

        .info-item.full-width {
          grid-column: 1 / -1;
        }

        .info-item .label {
          display: block;
          color: var(--text-secondary);
          font-size: 0.75rem;
          text-transform: uppercase;
          margin-bottom: 0.25rem;
        }

        .info-item code {
          font-size: 0.875rem;
          word-break: break-all;
        }

        .parameters-section h3,
        .implementation-section h3,
        .files-section h3 {
          margin: 0 0 1rem 0;
        }

        .parameters-list {
          display: grid;
          gap: 1rem;
        }

        .parameter-card {
          padding: 1rem;
          background: var(--bg-tertiary);
          border-radius: 8px;
          border-left: 3px solid var(--primary);
        }

        .param-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .param-name {
          font-size: 1rem;
          font-weight: 600;
        }

        .param-type {
          padding: 0.125rem 0.5rem;
          background: rgba(var(--primary-rgb), 0.15);
          color: var(--primary);
          border-radius: 4px;
          font-size: 0.75rem;
        }

        .param-description {
          margin: 0 0 0.5rem 0;
          color: var(--text-secondary);
          font-size: 0.875rem;
        }

        .param-default,
        .param-enum {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        .param-enum code {
          margin-left: 0.25rem;
          padding: 0.125rem 0.375rem;
          background: var(--bg-primary);
          border-radius: 4px;
        }

        .implementation-code {
          background: var(--bg-tertiary);
          padding: 1rem;
          border-radius: 8px;
          overflow-x: auto;
          white-space: pre-wrap;
          font-size: 0.875rem;
          line-height: 1.6;
        }

        .builtin-notice {
          padding: 1rem;
          background: rgba(var(--primary-rgb), 0.1);
          border-radius: 8px;
          border: 1px solid rgba(var(--primary-rgb), 0.2);
        }

        .edit-form {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .form-group label {
          font-weight: 500;
          color: var(--text-secondary);
        }

        .form-group input,
        .form-group textarea {
          padding: 0.75rem;
          background: var(--bg-tertiary);
          border: 1px solid var(--border-color);
          border-radius: 8px;
          color: var(--text-primary);
          font-size: 1rem;
        }

        .form-group input:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: var(--primary);
        }

        .code-editor {
          font-family: 'Monaco', 'Menlo', monospace;
          font-size: 0.875rem;
        }

        .form-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 0.5rem;
        }

        .templates-list,
        .references-list {
          display: grid;
          gap: 1rem;
        }

        .template-card,
        .reference-card {
          background: var(--bg-tertiary);
          border-radius: 8px;
          overflow: hidden;
        }

        .template-header {
          padding: 0.75rem 1rem;
          background: var(--bg-primary);
          border-bottom: 1px solid var(--border-color);
        }

        .template-name {
          font-weight: 500;
        }

        .template-content,
        .reference-card pre {
          padding: 1rem;
          margin: 0;
          font-size: 0.75rem;
          max-height: 200px;
          overflow: auto;
        }

        .source-info {
          margin-bottom: 1.5rem;
        }

        .source-info code {
          display: block;
          padding: 0.75rem;
          background: var(--bg-tertiary);
          border-radius: 8px;
          margin-top: 0.5rem;
        }

        .empty-message {
          color: var(--text-secondary);
          text-align: center;
          padding: 2rem;
        }

        .loading-container,
        .error-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 300px;
          gap: 1rem;
        }

        .loading-spinner {
          width: 40px;
          height: 40px;
          border: 3px solid var(--bg-tertiary);
          border-top-color: var(--primary);
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </DashboardLayout>
  );
}
