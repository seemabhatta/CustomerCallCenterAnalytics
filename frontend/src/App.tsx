import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import {
  MessageSquare,
  ClipboardList,
  Settings,
  Workflow as WorkflowIcon,
  PlayCircle,
  Lightbulb,
  Activity,
  Rocket,
  Settings2,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  Plus,
} from "lucide-react";

import { TranscriptsView } from "@/views/TranscriptsView";
import { AnalysisView } from "@/views/AnalysisView";
import { PlanView } from "@/views/PlanView";
import { WorkflowView } from "@/views/WorkflowView";
import { ExecutionView } from "@/views/ExecutionView";
import { Dashboard } from "@/views/Dashboard";
import { InsightsView } from "@/views/InsightsView";
import { RunsExplorer } from "@/views/RunsExplorer";
import { GovernanceSimulator } from "@/views/GovernanceSimulator";
import { TranscriptGeneratorView } from "@/views/TranscriptGeneratorView";

import { TabValue, Environment } from "@/types";

// Mock data - will be replaced with real API calls
const mockRun = {
  id: "RUN_CALL_27FF315B",
  started_at: "2025-09-12T16:41:34Z",
  durations: [
    { stage: "analysis", seconds: 9.7 },
    { stage: "plan", seconds: 24.4 },
    { stage: "workflows", seconds: 110.4 },
    { stage: "approval", seconds: 0.0 },
    { stage: "execution", seconds: 0.0 },
  ],
  funnel: { generated: 10, approved: 0, executed: 0, failed: 0 },
};

export default function App() {
  const [tab, setTab] = useState<TabValue>("dashboard");
  const [env, setEnv] = useState<Environment>("dev");

  // Dialog state for transcript details
  const [isTranscriptDialogOpen, setIsTranscriptDialogOpen] = useState(false);
  const [activeTranscriptId, setActiveTranscriptId] = useState<string | null>(null);

  useEffect(() => {
    // Load initial data for environment
    console.log(`Environment changed to: ${env}`);
  }, [env]);

  const handleOpenTranscript = (id: string) => {
    setActiveTranscriptId(id);
    setIsTranscriptDialogOpen(true);
  };

  const navigateToTab = (tabValue: TabValue) => {
    setTab(tabValue);
  };

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
          <TabsTrigger value="dashboard">
            <Activity className="h-3.5 w-3.5 mr-1" />
            Dashboard
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
          <TabsTrigger value="workflow_1">
            <Settings2 className="h-3.5 w-3.5 mr-1" />
            workflow_1
          </TabsTrigger>
          <TabsTrigger value="execution">
            <PlayCircle className="h-3.5 w-3.5 mr-1" />
            Execution
          </TabsTrigger>
          <TabsTrigger value="insights">
            <Lightbulb className="h-3.5 w-3.5 mr-1" />
            Insights
          </TabsTrigger>
          <TabsTrigger value="runs">Runs</TabsTrigger>
          <TabsTrigger value="governance">Governance</TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <Dashboard />
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
          <WorkflowView />
        </TabsContent>

        <TabsContent value="workflow_1">
          <WorkflowView goToPlan={(planId) => navigateToTab("plan")} />
        </TabsContent>

        <TabsContent value="execution">
          <ExecutionView />
        </TabsContent>

        <TabsContent value="insights">
          <InsightsView />
        </TabsContent>

        <TabsContent value="runs">
          <RunsExplorer />
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