"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

interface NavItemProps {
  href: string;
  icon: string;
  label: string;
}

function NavItem({ href, icon, label }: NavItemProps) {
  const pathname = usePathname();
  const isActive = pathname === href || pathname.startsWith(href + "/");

  return (
    <Link href={href} className={`nav-item ${isActive ? "active" : ""}`}>
      <span className="nav-item-icon">{icon}</span>
      <span>{label}</span>
    </Link>
  );
}

interface DashboardLayoutProps {
  children: ReactNode;
}

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  return (
    <div className="page">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <span className="sidebar-logo-icon">🦥</span>
            <span>LazyAgents</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <div className="nav-section">
            <div className="nav-section-title">Overview</div>
            <NavItem href="/dashboard" icon="📊" label="Dashboard" />
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Agents</div>
            <NavItem href="/agents" icon="🤖" label="All Agents" />
            <NavItem href="/agents/new" icon="✨" label="Create Agent" />
          </div>

          <div className="nav-section">
            <div className="nav-section-title">Configuration</div>
            <NavItem href="/skills" icon="🔧" label="Skills" />
            <NavItem href="/integrations" icon="🔗" label="Integrations" />
            <NavItem href="/integrations/mcp" icon="🧩" label="MCP Servers" />
          </div>

          <div className="nav-section">
            <div className="nav-section-title">History</div>
            <NavItem href="/executions" icon="📜" label="Executions" />
            <NavItem href="/logs" icon="📋" label="Logs" />
          </div>

          <div className="nav-section">
            <div className="nav-section-title">System</div>
            <NavItem href="/settings" icon="⚙️" label="Settings" />
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="text-xs text-muted">Version 0.1.0</div>
        </div>
      </aside>

      {/* Main content */}
      <div className="with-sidebar">
        <main className="main">{children}</main>
      </div>
    </div>
  );
}
