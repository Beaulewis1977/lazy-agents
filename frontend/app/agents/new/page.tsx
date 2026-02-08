"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import DashboardLayout from "@/components/DashboardLayout";
import { agentsAPI } from "@/lib/api";

const EXAMPLE_PROMPTS = [
  "Monitor my GitHub repo for new PRs and post a summary to Slack every morning",
  "Watch for messages in Discord #support and create GitHub issues for bug reports",
  "Every Friday at 5pm, compile a weekly summary of completed tasks from Notion",
  "When a new issue is created in GitHub, analyze it and suggest a priority label",
];

const MODELS = [
  { id: "gpt-4o-mini", name: "GPT-4o Mini", provider: "OpenAI" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { id: "claude-3-5-haiku-20241022", name: "Claude 3.5 Haiku", provider: "Anthropic" },
];

export default function NewAgentPage() {
  const router = useRouter();
  const [step, setStep] = useState<'describe' | 'configure'>('describe');
  const [description, setDescription] = useState("");
  const [name, setName] = useState("");
  const [model, setModel] = useState("gpt-4o-mini");
  const [systemPrompt, setSystemPrompt] = useState("");
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleCreate() {
    if (!name.trim()) {
      setError("Please enter a name for your agent");
      return;
    }

    setIsCreating(true);
    setError(null);

    try {
      const agent = await agentsAPI.create({
        name: name.trim(),
        description: description.trim() || undefined,
        model,
        system_prompt: systemPrompt.trim() || undefined,
      });
      router.push(`/agents/${agent.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create agent');
      setIsCreating(false);
    }
  }

  function handleDescribeContinue() {
    if (!description.trim()) {
      setError("Please describe what your agent should do");
      return;
    }
    // Generate a name from the description
    const words = description.split(' ').slice(0, 3).join(' ');
    setName(words.length > 30 ? words.slice(0, 30) + '...' : words);
    // Generate a system prompt from the description
    setSystemPrompt(`You are an AI agent that helps with the following task:\n\n${description}\n\nFollow these guidelines:\n1. Be concise and accurate\n2. Ask for clarification if instructions are unclear\n3. Report any errors or issues you encounter`);
    setStep('configure');
  }

  return (
    <DashboardLayout>
      <div className="header">
        <h1 className="header-title">Create Agent</h1>
      </div>

      <div className="container" style={{ padding: "var(--space-8)", maxWidth: 800 }}>
        {error && (
          <div className="card mb-6" style={{ background: "var(--color-error-muted)" }}>
            <p style={{ color: "var(--color-error)" }}>⚠️ {error}</p>
          </div>
        )}

        {step === 'describe' ? (
          <div className="card">
            <div style={{ textAlign: "center", marginBottom: "var(--space-8)" }}>
              <div style={{ fontSize: "3rem", marginBottom: "var(--space-4)" }}>✨</div>
              <h2>What would you like your agent to do?</h2>
              <p className="text-secondary">
                Describe what you want in natural language. Be specific about triggers, actions, and outputs.
              </p>
            </div>

            <div className="input-group mb-6">
              <textarea
                className="input textarea"
                placeholder='Example: "Monitor my GitHub repo owner/repo for new issues. Every morning at 9am, summarize any new issues from the past 24 hours and post the summary to my Discord channel #dev-updates."'
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                style={{ minHeight: 180 }}
              />
            </div>

            <button
              onClick={handleDescribeContinue}
              className="btn btn-primary btn-lg"
              style={{ width: "100%" }}
              disabled={!description.trim()}
            >
              Continue →
            </button>

            <div style={{ marginTop: "var(--space-8)", paddingTop: "var(--space-6)", borderTop: "1px solid var(--color-border)" }}>
              <h4 className="mb-4">Example prompts:</h4>
              <div className="flex flex-col gap-2">
                {EXAMPLE_PROMPTS.map((example, i) => (
                  <button
                    key={i}
                    onClick={() => setDescription(example)}
                    className="btn btn-ghost text-left"
                    style={{ justifyContent: "flex-start", padding: "var(--space-3)" }}
                  >
                    <span className="text-muted">→</span> {example}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="card">
            <div style={{ marginBottom: "var(--space-6)" }}>
              <button onClick={() => setStep('describe')} className="btn btn-ghost btn-sm mb-4">
                ← Back
              </button>
              <h2>Configure Your Agent</h2>
              <p className="text-secondary">Review and customize your agent settings</p>
            </div>

            <div className="flex flex-col gap-6">
              <div className="input-group">
                <label className="input-label">Agent Name *</label>
                <input
                  type="text"
                  className="input"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="My Awesome Agent"
                />
              </div>

              <div className="input-group">
                <label className="input-label">Description</label>
                <textarea
                  className="input textarea"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  style={{ minHeight: 100 }}
                />
              </div>

              <div className="input-group">
                <label className="input-label">Model</label>
                <select
                  className="input"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                >
                  {MODELS.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.provider})
                    </option>
                  ))}
                </select>
              </div>

              <div className="input-group">
                <label className="input-label">System Prompt</label>
                <textarea
                  className="input textarea"
                  value={systemPrompt}
                  onChange={(e) => setSystemPrompt(e.target.value)}
                  style={{ minHeight: 160 }}
                  placeholder="Instructions for the agent..."
                />
              </div>

              <button
                onClick={handleCreate}
                className="btn btn-primary btn-lg"
                style={{ width: "100%" }}
                disabled={!name.trim() || isCreating}
              >
                {isCreating ? "🔄 Creating..." : "🚀 Create Agent"}
              </button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
