import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { orchestrationApi, transcriptApi, workflowApi } from "@/api/client";
import { OrchestrationRun, Transcript, Workflow } from "@/types";

interface WorkflowGroup {
  type: string;
  items: WorkflowWithContext[];
}

interface WorkflowWithContext extends Workflow {
  txId?: string;
  analyzeStatus?: string;
  planStatus?: string;
}

interface Panel {
  id: string;
  mode: 'analyze' | 'plan';
}

export function PipelineView() {
  const queryClient = useQueryClient();

  // State management
  const [selectedTranscripts, setSelectedTranscripts] = useState<string[]>([]);
  const [activeRun, setActiveRun] = useState<string | null>(null);
  const [panel, setPanel] = useState<Panel | null>(null);
  const [visible, setVisible] = useState({
    Borrower: true,
    Advisor: true,
    Supervisor: true,
    Leadership: true,
  });
  const [onlyPending, setOnlyPending] = useState(false);

  // Data fetching
  const { data: transcripts = [] } = useQuery({
    queryKey: ['transcripts'],
    queryFn: transcriptApi.list,
  });

  const { data: runsData } = useQuery({
    queryKey: ['orchestration-runs'],
    queryFn: orchestrationApi.listRuns,
  });

  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: workflowApi.list,
  });

  // Status polling for active run
  const { data: runStatus } = useQuery({
    queryKey: ['run-status', activeRun],
    queryFn: () => orchestrationApi.getStatus(activeRun!),
    enabled: !!activeRun,
    refetchInterval: 2000, // Poll every 2 seconds
  });

  // Pipeline execution mutation
  const runPipeline = useMutation({
    mutationFn: (params: { transcript_ids: string[]; auto_approve: boolean }) =>
      orchestrationApi.runPipeline(params.transcript_ids, params.auto_approve),
    onSuccess: (data) => {
      setActiveRun(data.run_id);
      queryClient.invalidateQueries({ queryKey: ['orchestration-runs'] });
    },
  });

  // Stop polling when run completes
  useEffect(() => {
    if (runStatus && (runStatus.status === 'COMPLETED' || runStatus.status === 'FAILED')) {
      setActiveRun(null);
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      queryClient.invalidateQueries({ queryKey: ['orchestration-runs'] });
    }
  }, [runStatus, queryClient]);

  // Helper functions
  const wfTypes = ["Borrower", "Advisor", "Supervisor", "Leadership"];

  const toggleTranscript = (id: string) => {
    setSelectedTranscripts(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const countsByType = workflows.reduce((acc: Record<string, number>, w) => {
    const type = w.workflow_type || 'Unknown';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {});

  const openPanel = (id: string, mode: 'analyze' | 'plan') => setPanel({ id, mode });
  const closePanel = () => setPanel(null);

  // Group workflows by type
  const grouped: WorkflowGroup[] = wfTypes.map((t) => ({
    type: t,
    items: workflows
      .filter((w) => w.workflow_type?.toUpperCase() === t.toUpperCase())
      .filter(() => visible[t as keyof typeof visible])
      .filter((w) => !onlyPending || w.status === 'PENDING')
      .map((w) => ({
        ...w,
        txId: findTranscriptIdForWorkflow(w),
        analyzeStatus: 'done', // Simplified for now
        planStatus: 'done',
      })),
  }));

  // Helper to find transcript ID for a workflow (simplified)
  function findTranscriptIdForWorkflow(workflow: Workflow): string {
    // This would need to look up through analysis -> transcript relationship
    // For now, return a placeholder
    return workflow.plan_id ? workflow.plan_id.split('_').pop() || 'UNKNOWN' : 'UNKNOWN';
  }

  // Format stage for display
  const formatStage = (stage: string): string => {
    switch (stage) {
      case 'ANALYSIS_COMPLETED':
        return '✅ Analysis Completed';
      case 'PLAN_COMPLETED':
        return '✅ Plan Completed';
      case 'WORKFLOWS_COMPLETED':
        return '✅ Workflows Generated';
      case 'EXECUTION_COMPLETED':
        return '✅ Execution Completed';
      case 'COMPLETE':
        return '🎉 Pipeline Complete';
      default:
        return stage;
    }
  };

  // UI Components
  const Badge = ({ children }: { children: React.ReactNode }) => (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 border border-gray-200 text-[11px]">
      {children}
    </span>
  );

  const StatusIcon = ({ s }: { s: string }) => {
    if (s === "done") return <span className="text-green-600 font-bold">✓</span>;
    if (s === "pending") return <span className="text-yellow-600">⏳</span>;
    if (s === "queued") return <span className="text-blue-600">➜</span>;
    if (s === "pending_approval") return <span className="text-orange-600">📝</span>;
    return <span className="text-gray-500">⏸</span>;
  };

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen font-mono text-sm">
      {/* Header */}
      <header className="flex items-center justify-between">
        <h1 className="font-bold text-lg">Pipeline Manager</h1>
        <div className="flex gap-2">
          {wfTypes.map((t) => (
            <button
              key={t}
              onClick={() => setVisible(v => ({ ...v, [t]: !v[t as keyof typeof v] }))}
              className={
                "px-2 py-1 rounded-full text-xs border transition " +
                (visible[t as keyof typeof visible]
                  ? "bg-blue-50 border-blue-300 text-blue-700"
                  : "bg-white border-gray-300 text-gray-600 line-through opacity-70")
              }
              aria-pressed={visible[t as keyof typeof visible]}
              title={`Toggle ${t}`}
            >
              {t} <span className="ml-1">({countsByType[t.toUpperCase()] || 0})</span>
            </button>
          ))}
          <label className="ml-2 inline-flex items-center gap-1 text-xs">
            <input
              type="checkbox"
              checked={onlyPending}
              onChange={e => setOnlyPending(e.target.checked)}
            />
            Only Pending
          </label>
        </div>
      </header>

      {/* Transcript Selector Section */}
      <section className="bg-white border rounded-xl shadow-sm">
        <div className="px-4 py-3 border-b font-semibold">Select Transcripts to Process</div>
        <div className="p-4">
          <div className="space-y-2 mb-4">
            {transcripts.map((t) => (
              <label key={t.id} className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={selectedTranscripts.includes(t.id)}
                  onChange={() => toggleTranscript(t.id)}
                />
                <span className="font-medium">{t.id}</span>
                <span className="text-sm text-gray-600">{t.topic}</span>
              </label>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => runPipeline.mutate({
                transcript_ids: selectedTranscripts,
                auto_approve: false
              })}
              disabled={selectedTranscripts.length === 0 || activeRun !== null}
              className="px-4 py-2 bg-blue-500 text-white rounded disabled:opacity-50"
            >
              Run Pipeline
            </button>
            <button
              onClick={() => runPipeline.mutate({
                transcript_ids: selectedTranscripts,
                auto_approve: true
              })}
              disabled={selectedTranscripts.length === 0 || activeRun !== null}
              className="px-4 py-2 bg-green-500 text-white rounded disabled:opacity-50"
            >
              Run with Auto-Approve
            </button>
          </div>
        </div>
      </section>

      {/* Active Run Status */}
      {activeRun && (
        <section className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
          <h3 className="font-semibold mb-2">Pipeline Running: {activeRun}</h3>
          {runStatus && (
            <div className="space-y-1 text-sm">
              <div>Status: {runStatus.status}</div>
              <div>Stage: {formatStage(runStatus.stage)}</div>
              {runStatus.analysis_id && <div>✓ Analysis: {runStatus.analysis_id}</div>}
              {runStatus.plan_id && <div>✓ Plan: {runStatus.plan_id}</div>}
              {runStatus.workflow_count && <div>✓ Workflows: {runStatus.workflow_count}</div>}
              {runStatus.executed_count !== undefined && (
                <div>✓ Executed: {runStatus.executed_count}/{runStatus.workflow_count}</div>
              )}
            </div>
          )}
        </section>
      )}

      {/* Recent Runs Table */}
      <section className="bg-white border rounded-xl shadow-sm">
        <div className="px-4 py-3 border-b font-semibold">Recent Runs</div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-3 py-2">Run ID</th>
                <th className="px-3 py-2">Status</th>
                <th className="px-3 py-2">Stage</th>
                <th className="px-3 py-2">Transcripts</th>
                <th className="px-3 py-2">Started</th>
              </tr>
            </thead>
            <tbody>
              {runsData?.runs?.map((run) => (
                <tr key={run.id} className="border-t">
                  <td className="px-3 py-2 font-medium">{run.id}</td>
                  <td className="px-3 py-2">
                    <Badge>
                      <StatusIcon s={run.status.toLowerCase()} />
                      <span className="ml-1">{run.status}</span>
                    </Badge>
                  </td>
                  <td className="px-3 py-2">{formatStage(run.stage)}</td>
                  <td className="px-3 py-2">{run.transcript_ids.join(', ')}</td>
                  <td className="px-3 py-2 text-sm text-gray-600">
                    {new Date(run.started_at).toLocaleString()}
                  </td>
                </tr>
              )) || (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-gray-500">No runs yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Workflows grouped by type */}
      <section className="bg-white border rounded-xl shadow-sm">
        <div className="px-4 py-3 border-b font-semibold">Workflows (Grouped)</div>
        <div className="p-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {grouped.map(group => (
            <div key={group.type} className="border rounded-lg">
              <div className="px-3 py-2 border-b font-semibold flex items-center justify-between">
                <span>{group.type}</span>
                <Badge>{group.items.length}</Badge>
              </div>
              <ul className="p-3 space-y-2">
                {group.items.map(item => (
                  <li key={item.id} className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{item.action_item}</div>
                      <div className="text-[11px] text-gray-500">From: {item.txId}</div>
                    </div>
                    <Badge>
                      <StatusIcon s={item.status.toLowerCase()} />
                      <span className="ml-1 capitalize">{item.status}</span>
                    </Badge>
                  </li>
                ))}
                {group.items.length === 0 && (
                  <li className="text-xs text-gray-500">No items</li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Right-side Explainability Panel */}
      {panel && (
        <div className="fixed inset-0 z-50 flex">
          <div className="flex-1 bg-black/30" onClick={closePanel} />
          <div className="w-[420px] max-w-[90vw] bg-white h-full shadow-xl border-l p-4 overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="font-bold">
                {panel.mode === "analyze" ? "Analyze Details" : "Plan Details"}
              </h3>
              <button onClick={closePanel} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            <div className="text-xs text-gray-500 mt-1">Transcript: {panel.id}</div>

            <div className="mt-4 space-y-3">
              <div className="text-sm font-semibold">
                {panel.mode === "analyze" ? "Analysis Summary" : "Plan Details"}
              </div>
              <p className="text-xs text-gray-700">
                {panel.mode === "analyze"
                  ? "Analysis data would be loaded here..."
                  : "Plan data would be loaded here..."
                }
              </p>
            </div>

            <div className="mt-6 pt-3 border-t">
              <div className="text-xs uppercase text-gray-500 mb-1">Audit Links</div>
              <div className="flex flex-wrap gap-2 text-xs">
                <button className="border rounded px-2 py-1">Open Transcript</button>
                <button className="border rounded px-2 py-1">View Audit Log</button>
                <button className="border rounded px-2 py-1">Export Evidence</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}