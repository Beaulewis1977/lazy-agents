"use client";
import { useEffect, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { skillsAPI, Skill } from "@/lib/api";

const CATEGORIES = ["all", "github", "discord", "slack", "notion", "http", "file", "custom"];

const CATEGORY_ICONS: Record<string, string> = {
  github: "🐙",
  discord: "💬",
  slack: "📱",
  notion: "📝",
  http: "🌐",
  file: "📁",
  shell: "💻",
  custom: "🔧",
};

interface ImportScanResult {
  id: string;
  status: string;
  error?: string;
}

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState("all");
  
  // Create State
  const [showCreate, setShowCreate] = useState(false);
  const [newSkill, setNewSkill] = useState({ id: "", name: "", description: "", category: "custom" });
  const [creating, setCreating] = useState(false);

  // Import State
  const [showImport, setShowImport] = useState(false);
  const [importPath, setImportPath] = useState("");
  const [importType, setImportType] = useState<'file' | 'directory'>('file');
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<{
    message?: string;
    skills_found?: number;
    results?: ImportScanResult[];
  } | null>(null);

  useEffect(() => {
    loadSkills();
  }, []);

  async function loadSkills() {
    try {
      const data = await skillsAPI.list();
      setSkills(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skills');
    } finally {
      setLoading(false);
    }
  }

  async function handleCreateSkill() {
    if (!newSkill.id || !newSkill.name) {
      setError("ID and Name are required");
      return;
    }
    setCreating(true);
    setError(null);
    try {
      const skill = await skillsAPI.create({
        id: newSkill.id,
        name: newSkill.name,
        description: newSkill.description || undefined,
        category: newSkill.category,
      });
      setSkills([...skills, skill]);
      setShowCreate(false);
      setNewSkill({ id: "", name: "", description: "", category: "custom" });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create skill');
    } finally {
      setCreating(false);
    }
  }

  async function handleImport() {
    if (!importPath) return;
    setImporting(true);
    setImportResult(null);
    setError(null);
    try {
      if (importType === 'file') {
        const result = await skillsAPI.loadFromPath(importPath);
        setImportResult({ message: result.message });
        loadSkills(); // Refresh list
      } else {
        const result = await skillsAPI.scanDirectory(importPath);
        setImportResult(result);
        loadSkills(); // Refresh list
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setImporting(false);
    }
  }

  const filteredSkills = activeCategory === "all" 
    ? skills 
    : skills.filter(s => s.category === activeCategory);

  if (loading) return (
    <DashboardLayout>
      <div className="container p-8 text-center">
        <div className="text-4xl mb-4 animate-bounce">⏳</div>
        <p className="text-secondary">Loading skills...</p>
      </div>
    </DashboardLayout>
  );

  return (
    <DashboardLayout>
      <div className="header backdrop-blur-md bg-white/5 supports-[backdrop-filter]:bg-white/5">
        <div>
          <h1 className="header-title">Skills</h1>
          <p className="text-sm text-secondary mt-2">
            {skills.length} skill{skills.length !== 1 ? 's' : ''} available
          </p>
        </div>
        <div className="flex gap-2">
           <button onClick={() => setShowImport(true)} className="btn btn-secondary">
            📥 Import from Disk
          </button>
          <button onClick={() => setShowCreate(true)} className="btn btn-primary">
            🔧 Create Skill
          </button>
        </div>
      </div>

      <div className="container p-8">
        {error && (
          <div className="card mb-6 bg-error/10 border-error/20">
            <p className="text-error">⚠️ {error}</p>
            <button onClick={() => setError(null)} className="btn btn-ghost btn-sm mt-2">Dismiss</button>
          </div>
        )}

        {/* Import Modal */}
        {showImport && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="card w-full max-w-lg shadow-2xl animate-in fade-in zoom-in duration-200">
               <div className="flex justify-between items-center mb-4">
                <h3>Import Skills</h3>
                <button onClick={() => setShowImport(false)} className="btn btn-ghost btn-sm">✕</button>
              </div>

              <div className="tabs flex gap-4 mb-4 border-b border-border">
                <button 
                  className={`pb-2 px-2 ${importType === 'file' ? 'border-b-2 border-primary font-bold' : 'text-muted'}`}
                  onClick={() => { setImportType('file'); setImportResult(null); }}
                >
                  Single File (MD)
                </button>
                <button 
                  className={`pb-2 px-2 ${importType === 'directory' ? 'border-b-2 border-primary font-bold' : 'text-muted'}`}
                  onClick={() => { setImportType('directory'); setImportResult(null); }}
                >
                  Scan Directory
                </button>
              </div>

              <div className="space-y-4">
                <div className="input-group">
                  <label className="input-label">
                    {importType === 'file' ? 'File Path (absolute)' : 'Directory Path (absolute)'}
                  </label>
                  <input
                    type="text"
                    className="input font-mono text-sm"
                    value={importPath}
                    onChange={(e) => setImportPath(e.target.value)}
                    placeholder={importType === 'file' ? "/home/user/skills/my_skill.md" : "/home/user/skills/"}
                  />
                  <p className="text-xs text-muted mt-1">
                    {importType === 'file' 
                      ? "Current machine path to a markdown skill file." 
                      : "Recursive scan for skill files in this folder."}
                  </p>
                </div>

                {importResult && (
                  <div className="bg-neutral-muted p-3 rounded text-sm">
                    {importResult.message && <p className="text-success">✅ {importResult.message}</p>}
                    {importResult.skills_found !== undefined && (
                      <div>
                        <p className="font-bold">Scanned {importResult.skills_found} skills</p>
                        <ul className="list-disc pl-4 mt-1 text-xs max-h-32 overflow-auto">
                          {importResult.results?.map((r) => (
                            <li key={r.id} className={r.status === 'error' ? 'text-error' : 'text-success'}>
                              {r.id}: {r.status} {r.error ? `(${r.error})` : ''}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                <div className="flex gap-2 justify-end">
                  <button onClick={() => setShowImport(false)} className="btn btn-ghost">Close</button>
                  <button onClick={handleImport} className="btn btn-primary" disabled={importing || !importPath}>
                    {importing ? 'Importing...' : 'Import'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Create Modal */}
        {showCreate && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="card w-full max-w-lg shadow-2xl animate-in fade-in zoom-in duration-200">
              <h3 className="mb-4">Create Custom Skill</h3>
              <div className="flex flex-col gap-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="input-group">
                    <label className="input-label">Skill ID *</label>
                    <input
                      type="text"
                      className="input"
                      value={newSkill.id}
                      onChange={(e) => setNewSkill({ ...newSkill, id: e.target.value })}
                      placeholder="my_custom.skill"
                    />
                  </div>
                  <div className="input-group">
                    <label className="input-label">Name *</label>
                    <input
                      type="text"
                      className="input"
                      value={newSkill.name}
                      onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })}
                      placeholder="My Custom Skill"
                    />
                  </div>
                </div>
                <div className="input-group">
                  <label className="input-label">Description</label>
                  <input
                    type="text"
                    className="input"
                    value={newSkill.description}
                    onChange={(e) => setNewSkill({ ...newSkill, description: e.target.value })}
                    placeholder="What does this skill do?"
                  />
                </div>
                <div className="input-group">
                  <label className="input-label">Category</label>
                  <select
                    className="input"
                    value={newSkill.category}
                    onChange={(e) => setNewSkill({ ...newSkill, category: e.target.value })}
                  >
                    {CATEGORIES.filter(c => c !== 'all').map(cat => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2 justify-end mt-4">
                  <button onClick={() => setShowCreate(false)} className="btn btn-ghost">Cancel</button>
                  <button onClick={handleCreateSkill} className="btn btn-primary" disabled={creating}>
                    {creating ? 'Creating...' : 'Create Skill'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Category Filter */}
        <div className="flex gap-2 mb-6 flex-wrap">
          {CATEGORIES.map((cat) => (
            <button
              key={cat}
              onClick={() => setActiveCategory(cat)}
              className={`btn btn-sm transition-all duration-200 ${activeCategory === cat ? "btn-secondary scale-105 shadow-md" : "btn-ghost hover:bg-neutral-muted"}`}
            >
              {cat !== 'all' && CATEGORY_ICONS[cat]} {cat.charAt(0).toUpperCase() + cat.slice(1)}
            </button>
          ))}
        </div>

        {filteredSkills.length === 0 ? (
          <div className="card text-center py-12">
            <div className="text-6xl mb-4">🔧</div>
            <h3 className="text-xl font-bold mb-2">No skills found</h3>
            <p className="text-secondary mb-6">{activeCategory === 'all' ? 'Create your first custom skill or import from disk' : `No ${activeCategory} skills available`}</p>
            <div className="flex gap-4 justify-center">
              <button onClick={() => setShowCreate(true)} className="btn btn-primary">
                Create Skill
              </button>
              <button onClick={() => setShowImport(true)} className="btn btn-secondary">
                Import from Disk
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSkills.map((skill) => (
              <div key={skill.id} className="card group hover:shadow-lg hover:border-primary/50 transition-all duration-300 transform hover:-translate-y-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-neutral-muted flex items-center justify-center text-xl group-hover:scale-110 transition-transform">
                    {CATEGORY_ICONS[skill.category] || "🔧"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-bold truncate">{skill.name}</h4>
                    <div className="flex gap-2 mt-1">
                      <span className="badge badge-neutral text-[10px]">{skill.category}</span>
                      {skill.is_builtin && <span className="badge badge-success text-[10px]">built-in</span>}
                    </div>
                  </div>
                </div>
                <p className="text-sm text-secondary line-clamp-2 min-h-[2.5rem]">{skill.description || 'No description'}</p>
                {skill.integration_required && (
                  <div className="mt-3 text-xs text-muted flex items-center gap-1">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    Requires: {skill.integration_required}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
