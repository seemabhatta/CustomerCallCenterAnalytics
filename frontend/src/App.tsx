import React, { useState, useEffect } from "react";
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

import { TabValue, Environment } from "@/types";

export default function App() {
  const [tab, setTab] = useState<TabValue>("pipeline");
  const [env, setEnv] = useState<Environment>("dev");
  const [workflowFocusId, setWorkflowFocusId] = useState<string | null>(null);

  // Dialog state for transcript details
  const [isTranscriptDialogOpen, setIsTranscriptDialogOpen] = useState(false);
  const [activeTranscriptId, setActiveTranscriptId] = useState<string | null>(null);

  useEffect(() => {
    console.log(`Environment changed to: ${env}`);
  }, [env]);

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
    <div className="p-6 space-y-6 min-h-screen bg-background">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Customer Call Center Analytics</h1>
          <p className="text-sm text-slate-500">
            Linear Tables: Transcript → Analysis → Plan → Workflow → Execution
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select value={env} onValueChange={(value: Environment) => setEnv(value)}>
            <SelectTrigger className="w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="dev">Dev</SelectItem>
              <SelectItem value="staging">Staging</SelectItem>
              <SelectItem value="prod">Prod</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Main Content */}
      <Tabs value={tab} onValueChange={(value: TabValue) => setTab(value)}>
        <TabsList className="inline-flex flex-wrap gap-2">
          <TabsTrigger value="pipeline">
            <Settings2 className="h-3.5 w-3.5 mr-1" />
            Pipeline
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <Activity className="h-3.5 w-3.5 mr-1" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="generator">
            <Plus className="h-3.5 w-3.5 mr-1" />
            Generator
          </TabsTrigger>
          <TabsTrigger value="transcripts">
            <MessageSquare className="h-3.5 w-3.5 mr-1" />
            Transcripts
          </TabsTrigger>
          <TabsTrigger value="analysis">
            <ClipboardList className="h-3.5 w-3.5 mr-1" />
            Analysis
          </TabsTrigger>
          <TabsTrigger value="plan">
            <Settings className="h-3.5 w-3.5 mr-1" />
            Plan
          </TabsTrigger>
          <TabsTrigger value="workflow">
            <WorkflowIcon className="h-3.5 w-3.5 mr-1" />
            Workflow
          </TabsTrigger>
          <TabsTrigger value="execution">
            <PlayCircle className="h-3.5 w-3.5 mr-1" />
            Execution
          </TabsTrigger>
          <TabsTrigger value="governance">Governance</TabsTrigger>
        </TabsList>

        <TabsContent value="analytics">
          <AnalyticsView />
        </TabsContent>

        <TabsContent value="generator">
          <TranscriptGeneratorView 
            goToTranscripts={() => navigateToTab("transcripts")}
          />
        </TabsContent>

        <TabsContent value="transcripts">
          <TranscriptsView 
            onOpenTranscript={handleOpenTranscript}
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
            goToPlan={(planId) => navigateToTab("plan")}
            focusWorkflowId={workflowFocusId}
          />
        </TabsContent>

        <TabsContent value="execution">
          <ExecutionView />
        </TabsContent>

        <TabsContent value="pipeline">
          <NewPipeline2View />
        </TabsContent>

        <TabsContent value="governance">
          <GovernanceSimulator />
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
