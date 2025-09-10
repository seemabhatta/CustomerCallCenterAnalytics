import { Switch, Route } from "wouter";
import { queryClient } from "./lib/queryClient";
import { QueryClientProvider } from "@tanstack/react-query";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/not-found";
import SidebarNav from "@/components/ui/sidebar-nav";
import DashboardPage from "@/pages/dashboard";
import ApprovalQueuePage from "@/pages/approval-queue";
import CaseDetailPage from "@/pages/case-detail";

function Router() {
  return (
    <div className="min-h-screen flex">
      <SidebarNav />
      <main className="flex-1 overflow-auto">
        <Switch>
          <Route path="/" component={DashboardPage} />
          <Route path="/dashboard" component={DashboardPage} />
          <Route path="/approval-queue" component={ApprovalQueuePage} />
          <Route path="/case/:caseId" component={CaseDetailPage} />
          <Route component={NotFound} />
        </Switch>
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Router />
      </TooltipProvider>
    </QueryClientProvider>
  );
}

export default App;
