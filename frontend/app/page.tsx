import Link from "next/link";

export default function Home() {
  return (
    <div className="page" style={{ background: "var(--gradient-surface)" }}>
      {/* Hero Section */}
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          textAlign: "center",
          padding: "var(--space-8)",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Background glow effect */}
        <div
          style={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "800px",
            height: "800px",
            background: "var(--gradient-glow)",
            pointerEvents: "none",
          }}
        />

        <div style={{ position: "relative", zIndex: 1 }}>
          {/* Logo */}
          <div
            className="animate-fade-in animate-wave"
            style={{
              fontSize: "5rem",
              marginBottom: "var(--space-6)",
              display: "inline-block",
            }}
          >
            🦥
          </div>

          {/* Title */}
          <h1
            style={{
              fontSize: "clamp(2.5rem, 8vw, 4.5rem)",
              fontWeight: 700,
              marginBottom: "var(--space-4)",
              background: "var(--gradient-accent)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              backgroundClip: "text",
            }}
            className="animate-slide-up"
          >
            LazyAgents
          </h1>

          {/* Tagline */}
          <p
            style={{
              fontSize: "var(--font-size-xl)",
              color: "var(--color-text-secondary)",
              maxWidth: "600px",
              marginBottom: "var(--space-8)",
            }}
            className="animate-slide-up"
          >
            Let your agents do the work while you vibe.
            <br />
            <span style={{ fontSize: "var(--font-size-base)" }}>
              Self-hostable AI agent orchestration for indie developers.
            </span>
          </p>

          {/* CTA Buttons */}
          <div
            className="flex gap-4 justify-center animate-slide-up"
            style={{ animationDelay: "150ms" }}
          >
            <Link href="/dashboard" className="btn btn-primary btn-lg">
              <span>🚀</span>
              <span>Get Started</span>
            </Link>
            <a
              href="https://github.com/lazydevtools/lazy-agents"
              target="_blank"
              rel="noopener noreferrer"
              className="btn btn-secondary btn-lg"
            >
              <span>⭐</span>
              <span>Star on GitHub</span>
            </a>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <section
        style={{
          padding: "var(--space-20) var(--space-8)",
          background: "var(--color-bg-secondary)",
        }}
      >
        <div className="container">
          <h2
            style={{
              textAlign: "center",
              marginBottom: "var(--space-4)",
            }}
          >
            Everything you need to orchestrate AI agents
          </h2>
          <p
            style={{
              textAlign: "center",
              color: "var(--color-text-secondary)",
              maxWidth: "600px",
              margin: "0 auto var(--space-12)",
            }}
          >
            Think OpenAI Frontier, but for vibecoders. Self-hosted, open source,
            and designed for indie developers.
          </p>

          <div className="grid grid-cols-3">
            <FeatureCard
              icon="🗣️"
              title="Chat-to-Agent"
              description="Create agents using natural language. Just describe what you want, and LazyAgents builds it."
            />
            <FeatureCard
              icon="🔧"
              title="Skills System"
              description="Reusable actions your agents can perform. Built-in skills for GitHub, Discord, HTTP, and more."
            />
            <FeatureCard
              icon="🔗"
              title="Integrations"
              description="Connect to GitHub, Discord, Slack, Notion, webhooks, and more. Agents work across your tools."
            />
            <FeatureCard
              icon="🧠"
              title="Agent Memory"
              description="Agents remember context across executions. Build agents that learn and improve over time."
            />
            <FeatureCard
              icon="📊"
              title="Observability"
              description="Full visibility into what your agents are doing. Logs, metrics, and audit trails."
            />
            <FeatureCard
              icon="🤖"
              title="Multi-Model"
              description="Use OpenAI, Anthropic, Google, or local LLMs. Switch models per agent."
            />
          </div>
        </div>
      </section>

      {/* How it Works Section */}
      <section
        style={{
          padding: "var(--space-20) var(--space-8)",
        }}
      >
        <div className="container">
          <h2
            style={{
              textAlign: "center",
              marginBottom: "var(--space-12)",
            }}
          >
            How it works
          </h2>

          <div
            className="grid grid-cols-3"
            style={{ maxWidth: "900px", margin: "0 auto" }}
          >
            <StepCard
              number={1}
              title="Describe"
              description='Tell LazyAgents what you want: "Monitor my GitHub repo and summarize new issues in Discord every morning"'
            />
            <StepCard
              number={2}
              title="Connect"
              description="Link your tools. Add your GitHub token, Discord bot, or any integration you need."
            />
            <StepCard
              number={3}
              title="Relax"
              description="Your agent runs automatically. Check the dashboard when you want to see what's happening."
            />
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section
        style={{
          padding: "var(--space-20) var(--space-8)",
          background: "var(--color-bg-secondary)",
          textAlign: "center",
        }}
      >
        <div className="container">
          <h2 style={{ marginBottom: "var(--space-4)" }}>
            Ready to get lazy?
          </h2>
          <p
            style={{
              color: "var(--color-text-secondary)",
              marginBottom: "var(--space-8)",
              maxWidth: "500px",
              margin: "0 auto var(--space-8)",
            }}
          >
            Start orchestrating AI agents in minutes. Self-host with Docker or
            run locally.
          </p>
          <Link href="/dashboard" className="btn btn-primary btn-lg">
            <span>🦥</span>
            <span>Launch Dashboard</span>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer
        style={{
          padding: "var(--space-8)",
          borderTop: "1px solid var(--color-border)",
          textAlign: "center",
        }}
      >
        <p className="text-sm text-muted">
          Made with 🦥 by{" "}
          <a
            href="https://lazydevtools.com"
            target="_blank"
            rel="noopener noreferrer"
          >
            Lazy Dev Tools
          </a>
        </p>
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: string;
  title: string;
  description: string;
}) {
  return (
    <div className="card">
      <div style={{ fontSize: "2rem", marginBottom: "var(--space-4)" }}>
        {icon}
      </div>
      <h3
        style={{
          fontSize: "var(--font-size-lg)",
          marginBottom: "var(--space-2)",
        }}
      >
        {title}
      </h3>
      <p
        style={{
          color: "var(--color-text-secondary)",
          fontSize: "var(--font-size-sm)",
          margin: 0,
        }}
      >
        {description}
      </p>
    </div>
  );
}

function StepCard({
  number,
  title,
  description,
}: {
  number: number;
  title: string;
  description: string;
}) {
  return (
    <div style={{ textAlign: "center" }}>
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "50%",
          background: "var(--gradient-accent)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: "var(--font-size-xl)",
          fontWeight: 700,
          color: "white",
          margin: "0 auto var(--space-4)",
        }}
      >
        {number}
      </div>
      <h3
        style={{
          fontSize: "var(--font-size-lg)",
          marginBottom: "var(--space-2)",
        }}
      >
        {title}
      </h3>
      <p
        style={{
          color: "var(--color-text-secondary)",
          fontSize: "var(--font-size-sm)",
          margin: 0,
        }}
      >
        {description}
      </p>
    </div>
  );
}
