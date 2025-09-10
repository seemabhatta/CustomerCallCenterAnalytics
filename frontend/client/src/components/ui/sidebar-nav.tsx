import { Link, useLocation } from "wouter";

export default function SidebarNav() {
  const [location] = useLocation();

  const navGroups = [
    {
      title: "Command Center",
      icon: "🏢",
      items: [
        { path: "/dashboard", label: "Dashboard", id: "dashboard" },
        { path: "/approval-queue", label: "Pipeline & Approvals", id: "approval-queue" },
        { path: "/ai-assistant", label: "AI Assistant", id: "ai-assistant" },
      ]
    },
    {
      title: "Case Workflow", 
      icon: "📋",
      items: [
        { path: "/transcripts", label: "Transcripts", id: "transcripts" },
        { path: "/ai-analysis", label: "AI Analysis", id: "ai-analysis" },
        { path: "/action-plans", label: "Action Plans", id: "action-plans" },
        { path: "/execution", label: "Execution", id: "execution" },
      ]
    },
    {
      title: "Oversight",
      icon: "⚖️", 
      items: [
        { path: "/governance", label: "Governance", id: "governance" },
        { path: "/observer", label: "Observer & Learning", id: "observer" },
      ]
    },
    {
      title: "Tools",
      icon: "🔧",
      items: [
        { path: "/live-processing", label: "Live Processing", id: "live-processing" },
        { path: "/generate", label: "Generate", id: "generate" },
      ]
    }
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
      
      <div className="space-y-6">
        {navGroups.map((group, groupIndex) => (
          <div key={group.title} className="space-y-2">
            {/* Group Header */}
            <div className="flex items-center gap-2 px-2 py-1">
              <span className="text-sm">{group.icon}</span>
              <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                {group.title}
              </h3>
            </div>
            
            {/* Group Items */}
            <div className="space-y-1">
              {group.items.map((item) => (
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
            
            {/* Separator after each group except the last */}
            {groupIndex < navGroups.length - 1 && (
              <div className="border-t border-border mt-4"></div>
            )}
          </div>
        ))}
      </div>
    </nav>
  );
}
