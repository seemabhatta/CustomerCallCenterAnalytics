import { useState, useEffect } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import {
  MessageSquare,
  ClipboardList,
  Settings,
  Workflow as WorkflowIcon,
  PlayCircle,
  Activity,
  Settings2,
  Plus,
  Shield,
  Headphones,
  Database,
  BarChart3,
  MessageCircle,
  CheckCircle,
  Eye,
  Target,
} from "lucide-react";

import { TranscriptsView } from "@/views/TranscriptsView";
import { AnalysisView } from "@/views/AnalysisView";
import { PlanView } from "@/views/PlanView";
import { WorkflowView } from "@/views/WorkflowView";
import { ExecutionView } from "@/views/ExecutionView";
import { GovernanceSimulator } from "@/views/GovernanceSimulator";
import { TranscriptGeneratorView } from "@/views/TranscriptGeneratorView";
import { NewPipeline2View } from "@/views/NewPipeline2View";
import { AnalyticsView } from "@/views/AnalyticsView";
import { InsightsView } from "@/views/InsightsView";

import { TabValue, UserRole } from "@/types";

export default function App() {
  const [tab, setTab] = useState<TabValue>("analytics");
  const [userRole, setUserRole] = useState<UserRole>("admin");
  const [workflowFocusId, setWorkflowFocusId] = useState<string | null>(null);

  // Dialog state for transcript details
  const [isTranscriptDialogOpen, setIsTranscriptDialogOpen] = useState(false);
  const [activeTranscriptId, setActiveTranscriptId] = useState<string | null>(null);


  // Switch to appropriate default tab when role changes
  useEffect(() => {
    const roleDefaultTabs: Record<UserRole, TabValue> = {
      leadership: "analytics",
      supervisor: "dashboard",
      advisor: "calls",
      admin: "pipeline"
    };

    setTab(roleDefaultTabs[userRole]);
  }, [userRole]);

  const handleOpenTranscript = (id: string) => {
    setActiveTranscriptId(id);
    setIsTranscriptDialogOpen(true);
  };

  const navigateToTab = (tabValue: TabValue) => {
    setTab(tabValue);
  };

  useEffect(() => {
    const handleWorkflowOpen = (event: Event) => {
      const detail = (event as CustomEvent<{ workflowId?: string }>).detail;
      if (detail?.workflowId) {
        setWorkflowFocusId(detail.workflowId);
        setTab("workflow");
      }
    };

    window.addEventListener(
      "ccan:open-workflow-details",
      handleWorkflowOpen as EventListener
    );

    return () => {
      window.removeEventListener(
        "ccan:open-workflow-details",
        handleWorkflowOpen as EventListener
      );
    };
  }, []);

  return (
    <div className="page-shell min-h-screen">
      {/* Header */}
      <div className="app-header">
        <div>
          <h1 className="app-header-title">Customer Call Center Analytics</h1>
          <p className="app-header-subtitle">AI-powered mortgage servicing analytics and workflow automation</p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={userRole} onValueChange={(value: UserRole) => setUserRole(value)}>
            <SelectTrigger className="role-selector">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="leadership">Leadership</SelectItem>
              <SelectItem value="supervisor">Supervisor</SelectItem>
              <SelectItem value="advisor">Advisor</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={tab} onValueChange={(value) => setTab(value as TabValue)}>
        <TabsList className="inline-flex flex-wrap gap-1 bg-slate-100 p-1 rounded-lg text-xs">
          {/* Leadership View: Analytics, Insights, Governance */}
          {userRole === "leadership" && (
            <>
              <TabsTrigger value="analytics" className="tab-trigger">
                <BarChart3 className="h-3 w-3 mr-1" />
                Analytics
              </TabsTrigger>
              <TabsTrigger value="insights" className="tab-trigger">
                <MessageCircle className="h-3 w-3 mr-1" />
                Insights
              </TabsTrigger>
              <TabsTrigger value="governance" className="tab-trigger">
                <Shield className="h-3 w-3 mr-1" />
                Governance
              </TabsTrigger>
            </>
          )}

          {/* Supervisor View: Dashboard, Approvals, Reviews, Monitoring */}
          {userRole === "supervisor" && (
            <>
              <TabsTrigger value="dashboard" className="tab-trigger">
                <Database className="h-3 w-3 mr-1" />
                Dashboard
              </TabsTrigger>
              <TabsTrigger value="approvals" className="tab-trigger">
                <CheckCircle className="h-3 w-3 mr-1" />
                Approvals
              </TabsTrigger>
              <TabsTrigger value="reviews" className="tab-trigger">
                <Eye className="h-3 w-3 mr-1" />
                Reviews
              </TabsTrigger>
              <TabsTrigger value="monitoring" className="tab-trigger">
                <Activity className="h-3 w-3 mr-1" />
                Monitoring
              </TabsTrigger>
            </>
          )}

          {/* Advisor View: My Calls, Actions, Execute */}
          {userRole === "advisor" && (
            <>
              <TabsTrigger value="calls" className="tab-trigger">
                <Headphones className="h-3 w-3 mr-1" />
                My Calls
              </TabsTrigger>
              <TabsTrigger value="actions" className="tab-trigger">
                <Target className="h-3 w-3 mr-1" />
                Actions
              </TabsTrigger>
              <TabsTrigger value="execution" className="tab-trigger">
                <PlayCircle className="h-3 w-3 mr-1" />
                Execute
              </TabsTrigger>
            </>
          )}

          {/* Admin View: All tabs available */}
          {userRole === "admin" && (
            <>
              <TabsTrigger value="pipeline" className="tab-trigger">
                <Settings2 className="h-3 w-3 mr-1" />
                Pipeline
              </TabsTrigger>
              <TabsTrigger value="analytics" className="tab-trigger">
                <Activity className="h-3 w-3 mr-1" />
                Analytics
              </TabsTrigger>
              <TabsTrigger value="generator" className="tab-trigger ml-3">
                <Plus className="h-3 w-3 mr-1" />
                Generator
              </TabsTrigger>
              <TabsTrigger value="transcripts" className="tab-trigger">
                <MessageSquare className="h-3 w-3 mr-1" />
                Transcripts
              </TabsTrigger>
              <TabsTrigger value="analysis" className="tab-trigger">
                <ClipboardList className="h-3 w-3 mr-1" />
                Analysis
              </TabsTrigger>
              <TabsTrigger value="plan" className="tab-trigger">
                <Settings className="h-3 w-3 mr-1" />
                Plan
              </TabsTrigger>
              <TabsTrigger value="workflow" className="tab-trigger">
                <WorkflowIcon className="h-3 w-3 mr-1" />
                Workflow
              </TabsTrigger>
              <TabsTrigger value="execution" className="tab-trigger">
                <PlayCircle className="h-3 w-3 mr-1" />
                Execution
              </TabsTrigger>
              <TabsTrigger value="governance" className="tab-trigger ml-3">
                <Shield className="h-3 w-3 mr-1" />
                Governance
              </TabsTrigger>
            </>
          )}
        </TabsList>

        {/* Analytics - Available for Leadership and Admin */}
        <TabsContent value="analytics">
          <AnalyticsView />
        </TabsContent>

        {/* Insights - Leadership only */}
        <TabsContent value="insights">
          <InsightsView />
        </TabsContent>

        {/* Governance - Leadership and Admin */}
        <TabsContent value="governance">
          <GovernanceSimulator />
        </TabsContent>

        {/* Dashboard - Supervisor only (reuse Analytics) */}
        <TabsContent value="dashboard">
          <AnalyticsView />
        </TabsContent>

        {/* Approvals - Supervisor only (reuse Workflow) */}
        <TabsContent value="approvals">
          <WorkflowView
            goToPlan={() => navigateToTab("plan")}
            focusWorkflowId={workflowFocusId}
          />
        </TabsContent>

        {/* Reviews - Supervisor only (reuse Analysis) */}
        <TabsContent value="reviews">
          <AnalysisView
            goToPlan={() => navigateToTab("plan")}
          />
        </TabsContent>

        {/* Monitoring - Supervisor only (reuse Execution) */}
        <TabsContent value="monitoring">
          <ExecutionView />
        </TabsContent>

        {/* My Calls - Advisor only (reuse Transcripts) */}
        <TabsContent value="calls">
          <TranscriptsView
            goToAnalysis={() => navigateToTab("analysis")}
          />
        </TabsContent>

        {/* Actions - Advisor only (reuse Workflow) */}
        <TabsContent value="actions">
          <WorkflowView
            goToPlan={() => navigateToTab("plan")}
            focusWorkflowId={workflowFocusId}
          />
        </TabsContent>

        {/* Execute - Advisor and Admin (reuse Execution) */}
        <TabsContent value="execution">
          <ExecutionView />
        </TabsContent>

        {/* Admin-only tabs */}
        <TabsContent value="pipeline">
          <NewPipeline2View />
        </TabsContent>

        <TabsContent value="generator">
          <TranscriptGeneratorView
            goToTranscripts={() => navigateToTab("transcripts")}
          />
        </TabsContent>

        <TabsContent value="transcripts">
          <TranscriptsView
            goToAnalysis={() => navigateToTab("analysis")}
          />
        </TabsContent>

        <TabsContent value="analysis">
          <AnalysisView
            goToPlan={() => navigateToTab("plan")}
          />
        </TabsContent>

        <TabsContent value="plan">
          <PlanView
            goToWorkflow={() => navigateToTab("workflow")}
          />
        </TabsContent>

        <TabsContent value="workflow">
          <WorkflowView
            goToPlan={() => navigateToTab("plan")}
            focusWorkflowId={workflowFocusId}
          />
        </TabsContent>
      </Tabs>

      {/* Transcript Detail Dialog */}
      <Dialog open={isTranscriptDialogOpen} onOpenChange={setIsTranscriptDialogOpen}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>Transcript • {activeTranscriptId}</DialogTitle>
            <DialogDescription>
              {activeTranscriptId ? (
                <>Customer transcript details and conversation flow</>
              ) : (
                <span className="text-slate-500">No transcript selected</span>
              )}
            </DialogDescription>
          </DialogHeader>
          {activeTranscriptId ? (
            <div className="max-h-[70vh] overflow-auto rounded-xl border">
              <div className="p-4 text-sm text-slate-600">
                Hook this to <code>GET /api/v1/transcripts/{activeTranscriptId}</code> for live segments.
              </div>
            </div>
          ) : (
            <div className="text-sm text-slate-600">
              No transcript data available.
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
