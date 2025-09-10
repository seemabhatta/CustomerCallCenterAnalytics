import { Link, useLocation } from "wouter";

export default function SidebarNav() {
  const [location] = useLocation();

  const navItems = [
    { path: "/dashboard", label: "🏠 Dashboard", id: "dashboard" },
    { path: "/transcripts", label: "📞 Transcripts", id: "transcripts" },
    { path: "/ai-analysis", label: "🧠 AI Analysis", id: "ai-analysis" },
    { path: "/action-plans", label: "📋 Action Plans", id: "action-plans" },
    { path: "/governance", label: "🛡️ Governance", id: "governance" },
    { path: "/execution", label: "⚡ Execution", id: "execution" },
    { path: "/artifacts", label: "📄 Artifacts", id: "artifacts" },
    { path: "/observer", label: "🔬 Observer & Learning", id: "observer" },
    { path: "/live-processing", label: "🔴 Live Processing", id: "live-processing" },
  ];

  const isActive = (path: string, id: string) => {
    if (path === "/dashboard" && (location === "/" || location === "/dashboard")) return true;
    if (id === "case-detail" && location.startsWith("/case/")) return true;
    return location === path;
  };

  return (
    <nav className="w-64 bg-card border-r border-border p-6" data-testid="sidebar-nav">
      <div className="mb-8">
        <h1 className="text-xl font-semibold text-foreground" data-testid="app-title">AI Decision Support</h1>
        <p className="text-sm text-muted-foreground" data-testid="app-subtitle">Mortgage Intelligence</p>
      </div>
      
      <div className="space-y-2">
        {navItems.map((item) => (
          <Link key={item.id} href={item.path}>
            <button
              className={`w-full text-left px-3 py-2 rounded-lg hover:bg-accent transition-colors ${
                isActive(item.path, item.id)
                  ? "bg-primary text-primary-foreground"
                  : "text-foreground"
              }`}
              data-testid={`nav-${item.id}`}
            >
              {item.label}
            </button>
          </Link>
        ))}
      </div>
    </nav>
  );
}
