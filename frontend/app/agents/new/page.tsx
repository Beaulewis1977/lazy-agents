"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import AgentForm, { AgentFormData } from "@/components/AgentForm";
import { agentsAPI } from "@/lib/api";

export default function NewAgentPage() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  async function handleCreate(data: AgentFormData) {
    try {
      setError(null);
      const agent = await agentsAPI.create(data);
      router.push(`/agents/${agent.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
      throw err; // Re-throw so AgentForm can handle it
    }
  }

  return (
    <DashboardLayout>
      <div className="header">
        <h1 className="header-title">Create Agent</h1>
      </div>

      <div className="container" style={{ padding: "var(--space-8)", maxWidth: 900 }}>
        {error && (
          <div className="card mb-6" style={{ background: "var(--color-error-muted)" }}>
            <p style={{ color: "var(--color-error)" }}>⚠️ {error}</p>
          </div>
        )}

        <AgentForm onSubmit={handleCreate} submitLabel="Create Agent" />
      </div>
    </DashboardLayout>
  );
}
