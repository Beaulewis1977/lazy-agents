"use client";
import { useEffect, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { skillsAPI, integrationsAPI, Skill, Integration } from "@/lib/api";

// Zod schema for agent form validation
const agentFormSchema = z.object({
  name: z.string().min(1, "Name is required").max(255, "Name must be under 255 characters"),
  description: z.string().optional().or(z.literal("")),
  model: z.string().min(1, "Model is required"),
  system_prompt: z.string().optional().or(z.literal("")),
  temperature: z.number().min(0, "Temperature must be at least 0").max(2, "Temperature must be at most 2"),
  skills: z.array(z.string()),
  integrations: z.array(z.string()),
  schedule: z.string().optional().or(z.literal("")),
  memory_enabled: z.boolean(),
});

export type AgentFormData = z.infer<typeof agentFormSchema>;

const MODELS = [
  { id: "gpt-4o-mini", name: "GPT-4o Mini", provider: "OpenAI" },
  { id: "gpt-4o", name: "GPT-4o", provider: "OpenAI" },
  { id: "claude-3-5-sonnet-20241022", name: "Claude 3.5 Sonnet", provider: "Anthropic" },
  { id: "claude-3-5-haiku-20241022", name: "Claude 3.5 Haiku", provider: "Anthropic" },
];

interface AgentFormProps {
  initialData?: Partial<AgentFormData>;
  onSubmit: (data: AgentFormData) => Promise<void>;
  submitLabel?: string;
}

export default function AgentForm({ initialData, onSubmit, submitLabel = "Save Agent" }: AgentFormProps) {
  const [availableSkills, setAvailableSkills] = useState<Skill[]>([]);
  const [availableIntegrations, setAvailableIntegrations] = useState<Integration[]>([]);
  const [loadingSkills, setLoadingSkills] = useState(true);
  const [loadingIntegrations, setLoadingIntegrations] = useState(true);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    control,
    handleSubmit,
    formState: { errors, isSubmitting },
    reset,
  } = useForm<AgentFormData>({
    resolver: zodResolver(agentFormSchema),
    defaultValues: {
      name: "",
      description: "",
      model: "gpt-4o-mini",
      system_prompt: "",
      temperature: 0.7,
      skills: [],
      integrations: [],
      schedule: "",
      memory_enabled: true,
      ...initialData,
    },
  });

  // Load skills and integrations on mount
  useEffect(() => {
    async function loadData() {
      try {
        const [skills, integrations] = await Promise.all([
          skillsAPI.list(),
          integrationsAPI.list(),
        ]);
        setAvailableSkills(skills);
        setAvailableIntegrations(integrations);
      } catch (err) {
        console.error("Failed to load skills/integrations", err);
      } finally {
        setLoadingSkills(false);
        setLoadingIntegrations(false);
      }
    }
    loadData();
  }, []);

  // Reset form when initialData changes (important for edit mode)
  useEffect(() => {
    if (initialData) {
      reset({
        name: initialData.name ?? "",
        description: initialData.description ?? "",
        model: initialData.model ?? "gpt-4o-mini",
        system_prompt: initialData.system_prompt ?? "",
        temperature: initialData.temperature ?? 0.7,
        skills: initialData.skills ?? [],
        integrations: initialData.integrations ?? [],
        schedule: initialData.schedule ?? "",
        memory_enabled: initialData.memory_enabled ?? true,
      });
    }
  }, [initialData, reset]);

  // Group skills by category
  const skillsByCategory = availableSkills.reduce((acc, skill) => {
    const category = skill.category || "Other";
    if (!acc[category]) acc[category] = [];
    acc[category].push(skill);
    return acc;
  }, {} as Record<string, Skill[]>);

  const onFormSubmit = async (data: AgentFormData) => {
    try {
      setSubmitError(null);
      await onSubmit(data);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Failed to save agent");
    }
  };

  return (
    <form onSubmit={handleSubmit(onFormSubmit)} className="flex flex-col gap-6">
      {submitError && (
        <div className="card" style={{ background: "var(--color-error-muted)", borderColor: "var(--color-error)" }}>
          <p style={{ color: "var(--color-error)" }}>⚠️ {submitError}</p>
        </div>
      )}

      {/* Basic Info Section */}
      <div className="card">
        <h3 className="mb-4">Basic Information</h3>

        <div className="flex flex-col gap-4">
          <Controller
            name="name"
            control={control}
            render={({ field }) => (
              <div className="input-group">
                <label className="input-label">Agent Name *</label>
                <input {...field} className="input" placeholder="My Awesome Agent" />
                {errors.name && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.name.message}</p>}
              </div>
            )}
          />

          <Controller
            name="description"
            control={control}
            render={({ field }) => (
              <div className="input-group">
                <label className="input-label">Description</label>
                <textarea
                  {...field}
                  className="input"
                  placeholder="Describe what this agent does..."
                  style={{ minHeight: 80, resize: "vertical" }}
                />
                {errors.description && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.description.message}</p>}
              </div>
            )}
          />
        </div>
      </div>

      {/* Model Configuration Section */}
      <div className="card">
        <h3 className="mb-4">Model Configuration</h3>

        <div className="flex flex-col gap-4">
          <Controller
            name="model"
            control={control}
            render={({ field }) => (
              <div className="input-group">
                <label className="input-label">Model *</label>
                <select {...field} className="input">
                  {MODELS.map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.name} ({m.provider})
                    </option>
                  ))}
                </select>
                {errors.model && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.model.message}</p>}
              </div>
            )}
          />

          <Controller
            name="temperature"
            control={control}
            render={({ field }) => (
              <div className="input-group">
                <label className="input-label">Temperature</label>
                <input
                  {...field}
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  className="input"
                  onChange={(e) => {
                    const v = e.target.value.trim();
                    if (v === '') {
                      field.onChange(undefined);
                    } else {
                      const parsed = parseFloat(v);
                      if (Number.isNaN(parsed)) {
                        field.onChange(undefined);
                      } else {
                        field.onChange(parsed);
                      }
                    }
                  }}
                />
                <p className="text-xs text-secondary mt-1">Controls randomness (0 = deterministic, 2 = very creative)</p>
                {errors.temperature && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.temperature.message}</p>}
              </div>
            )}
          />

          <Controller
            name="system_prompt"
            control={control}
            render={({ field }) => (
              <div className="input-group">
                <label className="input-label">System Prompt</label>
                <textarea
                  {...field}
                  className="input"
                  placeholder="You are a helpful AI agent that..."
                  style={{ minHeight: 120, resize: "vertical" }}
                />
                <p className="text-xs text-secondary mt-1">Instructions that define the agent&apos;s behavior and personality</p>
                {errors.system_prompt && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.system_prompt.message}</p>}
              </div>
            )}
          />
        </div>
      </div>

      {/* Skills Section */}
      <div className="card">
        <h3 className="mb-4">Skills</h3>

        {loadingSkills ? (
          <p className="text-secondary">Loading skills...</p>
        ) : availableSkills.length === 0 ? (
          <p className="text-secondary">No skills available. Create skills to assign them to agents.</p>
        ) : (
          <Controller
            name="skills"
            control={control}
            render={({ field }) => (
              <div className="flex flex-col gap-4">
                {Object.entries(skillsByCategory).map(([category, skills]) => (
                  <div key={category}>
                    <h4 className="text-sm font-medium mb-2" style={{ color: "var(--color-text-secondary)" }}>
                      {category}
                    </h4>
                    <div className="flex flex-col gap-2 p-4 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
                      {skills.map((skill) => (
                        <label key={skill.id} className="flex items-start gap-3 cursor-pointer hover:opacity-80">
                          <input
                            type="checkbox"
                            checked={field.value.includes(skill.id)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                field.onChange([...field.value, skill.id]);
                              } else {
                                field.onChange(field.value.filter((id) => id !== skill.id));
                              }
                            }}
                            className="mt-1"
                            style={{ width: 16, height: 16, cursor: "pointer" }}
                          />
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className="text-sm font-medium">{skill.name}</span>
                              <span className="badge badge-neutral text-xs">{skill.category}</span>
                            </div>
                            {skill.description && (
                              <p className="text-xs mt-1" style={{ color: "var(--color-text-secondary)" }}>
                                {skill.description}
                              </p>
                            )}
                          </div>
                        </label>
                      ))}
                    </div>
                  </div>
                ))}
                {errors.skills && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.skills.message}</p>}
              </div>
            )}
          />
        )}
      </div>

      {/* Integrations Section */}
      <div className="card">
        <h3 className="mb-4">Integrations</h3>

        {loadingIntegrations ? (
          <p className="text-secondary">Loading integrations...</p>
        ) : availableIntegrations.length === 0 ? (
          <p className="text-secondary">No integrations configured. Set up integrations to connect external services.</p>
        ) : (
          <Controller
            name="integrations"
            control={control}
            render={({ field }) => (
              <div className="flex flex-col gap-2 p-4 rounded" style={{ background: "var(--color-bg-tertiary)" }}>
                {availableIntegrations.map((integration) => (
                  <label key={integration.id} className="flex items-start gap-3 cursor-pointer hover:opacity-80">
                    <input
                      type="checkbox"
                      checked={field.value.includes(integration.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          field.onChange([...field.value, integration.id]);
                        } else {
                          field.onChange(field.value.filter((id) => id !== integration.id));
                        }
                      }}
                      className="mt-1"
                      style={{ width: 16, height: 16, cursor: "pointer" }}
                    />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{integration.name}</span>
                        <span className="badge badge-neutral text-xs">{integration.type}</span>
                        <span
                          className={`text-xs ${
                            integration.status === "connected"
                              ? "text-success"
                              : integration.status === "error"
                              ? "text-error"
                              : "text-muted"
                          }`}
                        >
                          ● {integration.status}
                        </span>
                      </div>
                    </div>
                  </label>
                ))}
                {errors.integrations && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.integrations.message}</p>}
              </div>
            )}
          />
        )}
      </div>

      {/* Advanced Section */}
      <div className="card">
        <h3 className="mb-4">Advanced Settings</h3>

        <div className="flex flex-col gap-4">
          <Controller
            name="schedule"
            control={control}
            render={({ field }) => (
              <div className="input-group">
                <label className="input-label">Schedule (Cron Expression)</label>
                <input
                  {...field}
                  type="text"
                  className="input"
                  placeholder="0 9 * * *"
                  style={{ fontFamily: "var(--font-mono)" }}
                />
                <p className="text-xs text-secondary mt-1">
                  Examples: <code>0 9 * * *</code> (daily at 9am), <code>*/15 * * * *</code> (every 15 min), <code>0 * * * 1-5</code> (hourly on weekdays)
                </p>
                {errors.schedule && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.schedule.message}</p>}
              </div>
            )}
          />

          <Controller
            name="memory_enabled"
            control={control}
            render={({ field }) => (
              <div className="input-group">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={field.value}
                    onChange={(e) => field.onChange(e.target.checked)}
                    style={{ width: 18, height: 18, cursor: "pointer" }}
                  />
                  <span className="input-label mb-0">Enable Memory</span>
                </label>
                <p className="text-xs text-secondary mt-1">Allow the agent to remember context across executions</p>
                {errors.memory_enabled && <p className="text-sm mt-1" style={{ color: "var(--color-error)" }}>{errors.memory_enabled.message}</p>}
              </div>
            )}
          />
        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isSubmitting}
        className="btn btn-primary btn-lg"
        style={{ width: "100%" }}
      >
        {isSubmitting ? "🔄 Saving..." : `✨ ${submitLabel}`}
      </button>
    </form>
  );
}
