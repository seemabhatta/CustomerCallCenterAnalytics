import { Link, useLocation } from "wouter";

export default function SidebarNav() {
  const [location] = useLocation();

  const navGroups = [
    {
      title: "Command Center",
      icon: "🏢",
      items: [
        { path: "/dashboard", label: "Dashboard", id: "dashboard" },
        { path: "/approval-queue", label: "Queue", id: "approval-queue" },
        { path: "/ai-assistant", label: "AI Assistant", id: "ai-assistant" },
      ]
    },
    {
      title: "Case Workflow", 
      icon: "📋",
      items: [
        { path: "/transcripts", label: "Transcripts", id: "transcripts" },
        { path: "/ai-analysis", label: "Analysis", id: "ai-analysis" },
        { path: "/action-plans", label: "Action Plans", id: "action-plans" },
        { path: "/execution", label: "Execution", id: "execution" },
      ]
    },
    {
      title: "Oversight",
      icon: "⚖️", 
      items: [
        { path: "/governance", label: "Governance", id: "governance" },
        { path: "/observer", label: "Analytics", id: "observer" },
      ]
    },
    {
      title: "Tools",
      icon: "🔧",
      items: [
        { path: "/live-processing", label: "Live Processing", id: "live-processing" },
      ]
    },
    {
      title: "Utilities",
      icon: "🔧",
      items: [
        { path: "/generate", label: "Data Generator", id: "generate" },
      ]
    }
  ];

  const isActive = (path: string, id: string) => {
    if (path === "/dashboard" && (location === "/" || location === "/dashboard")) return true;
    if (id === "case-detail" && location.startsWith("/case/")) return true;
    return location === path;
  };

  return (
    <nav className="w-56 bg-card border-r border-border container-pad text-sm leading-5" data-testid="sidebar-nav">
      <div className="mb-6">
        <h1 className="h1 text-foreground" data-testid="app-title">AI Decision Support</h1>
        <p className="text-xs text-muted-foreground mt-1" data-testid="app-subtitle">Mortgage Intelligence</p>
      </div>
      
      <div className="grid-gap">
        {navGroups.map((group, groupIndex) => (
          <div key={group.title}>
            {/* Group Items */}
            <div className="space-y-0.5">
              {group.items.map((item) => (
                <Link key={item.id} href={item.path}>
                  <button
                    className={`w-full text-left h-8 px-3 rounded-xl text-sm hover:bg-accent transition-colors ${
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
              <div className="border-t border-border/60 my-3"></div>
            )}
          </div>
        ))}
      </div>
    </nav>
  );
}
