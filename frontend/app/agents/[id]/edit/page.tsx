"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import DashboardLayout from "@/components/DashboardLayout";
import AgentForm, { AgentFormData } from "@/components/AgentForm";
import { agentsAPI } from "@/lib/api";

export default function EditAgentPage() {
  const params = useParams();
  const router = useRouter();
  const id = params?.id as string;

  const [initialData, setInitialData] = useState<Partial<AgentFormData> | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadAgent() {
      try {
        const agent = await agentsAPI.getConfig(id);

        // Transform agent config to form data shape
        // Map skill/integration objects to ID arrays
        const formData: Partial<AgentFormData> = {
          name: agent.name,
          description: agent.description || "",
          model: agent.model,
          system_prompt: agent.system_prompt || "",
          temperature: agent.temperature,
          skills: agent.skills.map((s) => s.id),
          integrations: agent.integrations.map((i) => i.id),
          schedule: agent.schedule || "",
          memory_enabled: agent.memory_enabled,
        };

        setInitialData(formData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load agent');
      } finally {
        setLoading(false);
      }
    }

    if (id) {
      loadAgent();
    }
  }, [id]);

  async function handleUpdate(data: AgentFormData) {
    try {
      await agentsAPI.update(id, data);
      router.push(`/agents/${id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update agent');
      throw err; // Re-throw so AgentForm can handle it
    }
  }

  if (loading) {
    return (
      <DashboardLayout>
        <div className="container p-8 text-center">
          <div style={{ fontSize: "2rem", marginBottom: "var(--space-4)" }}>⏳</div>
          <p className="text-secondary">Loading agent...</p>
        </div>
      </DashboardLayout>
    );
  }

  if (error && !initialData) {
    return (
      <DashboardLayout>
        <div className="container p-8">
          <div className="card" style={{ background: "var(--color-error-muted)" }}>
            <p style={{ color: "var(--color-error)" }}>⚠️ {error}</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="header">
        <div className="flex items-center gap-4">
          <Link href={`/agents/${id}`} className="btn btn-ghost btn-sm">
            ← Back to Agent
          </Link>
          <h1 className="header-title">Edit Agent</h1>
        </div>
      </div>

      <div className="container" style={{ padding: "var(--space-8)", maxWidth: 900 }}>
        {initialData && (
          <AgentForm
            initialData={initialData}
            onSubmit={handleUpdate}
            submitLabel="Update Agent"
          />
        )}
      </div>
    </DashboardLayout>
  );
}
