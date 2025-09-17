import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  analysisApi,
  orchestrationApi,
  planApi,
  transcriptApi,
  workflowApi,
} from "@/api/client";
import {
  Analysis,
  OrchestrationRun,
  Plan,
  Transcript,
  Workflow,
} from "@/types";
import { Play, Pause, BarChart2, Check, CheckCircle2 } from "lucide-react";

const WF_LABELS: Record<string, string> = {
  BORROWER: "Borrower",
  ADVISOR: "Advisor",
  SUPERVISOR: "Supervisor",
  LEADERSHIP: "Leadership",
};

const stageTargetForStatus = (
  stage?: string,
  run?: OrchestrationRun
): number | null => {
  if (!stage) return null;
  switch (stage) {
    case "ANALYSIS_COMPLETED":
      return 25;
    case "PLAN_COMPLETED":
      return 50;
    case "WORKFLOWS_COMPLETED":
      return 75;
    case "EXECUTION_COMPLETED":
      return 100;
    case "COMPLETE":
      return 100;
    default:
      return null;
  }
};

const formatMinutes = (durationSec?: number, createdAt?: string) => {
  if (typeof durationSec === "number") {
    return `${Math.max(durationSec / 60, 0).toFixed(1)}min`;
  }
  if (!createdAt) return "—";
  const started = new Date(createdAt).getTime();
  if (Number.isNaN(started)) return "—";
  const diffMs = Date.now() - started;
  return `${Math.max(diffMs / 60000, 0).toFixed(1)}min`;
};

const analyzeComplete = (analysis?: Analysis) => {
  if (!analysis?.status) return false;
  const status = analysis.status.toLowerCase();
  return status.includes("done") || status.includes("complete");
};

const workflowsNeedingApproval = (workflows: Workflow[]) =>
  workflows.filter((workflow) => {
    const status = workflow.status.toLowerCase();
    return status.includes("await") || status.includes("pending");
  });

const normalizeStatusLabel = (status: string) => {
  return status
    .toLowerCase()
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
};

interface TranscriptRow {
  transcript: Transcript;
  analysis?: Analysis;
  plan?: Plan;
  workflows: Workflow[];
  analyzeDone: boolean;
  planReady: boolean;
  workflowCount: number;
  executedCount: number;
  workflowReady: boolean;
  executeComplete: boolean;
  approvalsPending: number;
  progress: number;
}

export function NewPipeline2View() {
  const queryClient = useQueryClient();

  const [selectedTranscripts, setSelectedTranscripts] = useState<string[]>([]);
  const [expandedTranscript, setExpandedTranscript] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<string | null>(null);
  const [approvalNotes, setApprovalNotes] = useState<Record<string, string>>({});
  const [activeTranscripts, setActiveTranscripts] = useState<string[]>([]);
  const [transcriptProgress, setTranscriptProgress] = useState<Record<string, number>>({});
  const lastStageRef = useRef<string | null>(null);
  const processingTranscriptRef = useRef<string | null>(null);

  const ensureTranscriptsTracked = useCallback((ids: string[] = []) => {
    if (!ids.length) return;
    setActiveTranscripts((prev) => {
      const merged = new Set(prev);
      ids.forEach((id) => merged.add(id));
      const next = Array.from(merged);
      if (next.length === prev.length && next.every((id) => prev.includes(id))) {
        return prev;
      }
      return next;
    });
  }, []);

  const updateProgressFor = useCallback((ids: string[], milestone: number) => {
    if (!ids.length) return;
    setTranscriptProgress((prev) => {
      const next = { ...prev };
      let changed = false;
      ids.forEach((id) => {
        const current = next[id] ?? 0;
        if (current < milestone) {
          next[id] = milestone;
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, []);

  const { data: transcripts = [] } = useQuery({
    queryKey: ["transcripts"],
    queryFn: transcriptApi.list,
  });

  const { data: analyses = [] } = useQuery({
    queryKey: ["analyses"],
    queryFn: analysisApi.list,
  });

  const { data: plans = [] } = useQuery({
    queryKey: ["plans"],
    queryFn: planApi.list,
  });

  const { data: workflows = [] } = useQuery({
    queryKey: ["workflows"],
    queryFn: workflowApi.list,
  });

  const { data: runsData } = useQuery({
    queryKey: ["orchestration-runs"],
    queryFn: orchestrationApi.listRuns,
    refetchInterval: activeRun ? 2000 : 10000,
    refetchIntervalInBackground: true,
  });

  const runs: OrchestrationRun[] = runsData?.runs || [];

  useEffect(() => {
    if (activeRun) {
      const currentRun = runs.find((run) => run.id === activeRun);
      const isActive =
        currentRun &&
        (currentRun.status === "RUNNING" || currentRun.status === "STARTED");
      if (isActive && currentRun) {
        const ids = currentRun.transcript_ids || [];
        ensureTranscriptsTracked(ids);
        updateProgressFor(ids, 5);
      }
      if (!isActive) {
        setActiveRun(null);
        setActiveTranscripts([]);
        processingTranscriptRef.current = null;
        lastStageRef.current = null;
      }
    } else {
      const runningRun = runs.find(
        (run) => run.status === "RUNNING" || run.status === "STARTED"
      );
      if (runningRun) {
        const ids = runningRun.transcript_ids || [];
        setActiveRun(runningRun.id);
        ensureTranscriptsTracked(ids);
        updateProgressFor(ids, 5);
        lastStageRef.current = null;
      }
    }
  }, [
    runs,
    activeRun,
    ensureTranscriptsTracked,
    updateProgressFor,
  ]);

  const analysisByTranscript = useMemo(() => {
    const map: Record<string, Analysis> = {};
    analyses.forEach((analysis) => {
      const current = map[analysis.transcript_id];
      if (!current || new Date(current.created_at) < new Date(analysis.created_at)) {
        map[analysis.transcript_id] = analysis;
      }
    });
    return map;
  }, [analyses]);

  const planByTranscript = useMemo(() => {
    const map: Record<string, Plan> = {};
    plans.forEach((plan) => {
      const current = map[plan.transcript_id];
      if (!current || new Date(current.created_at) < new Date(plan.created_at)) {
        map[plan.transcript_id] = plan;
      }
    });
    return map;
  }, [plans]);

  const workflowsByTranscript = useMemo(() => {
    const map: Record<string, Workflow[]> = {};
    workflows.forEach((workflow) => {
      const key = workflow.transcript_id;
      if (!map[key]) map[key] = [];
      map[key].push(workflow);
    });
    return map;
  }, [workflows]);

  const rows: TranscriptRow[] = useMemo(() => {
    return transcripts.map((transcript) => {
      const transcriptWorkflows = workflowsByTranscript[transcript.id] || [];
      const executedCount = transcriptWorkflows.filter(
        (workflow) => workflow.status === "EXECUTED"
      ).length;
      const progress = transcriptProgress[transcript.id] ?? 0;
      const analyzeReady = progress >= 25;
      const planReady = progress >= 50;
      const workflowReady = progress >= 75;
      const executeComplete = progress >= 100;
      return {
        transcript,
        analysis: analysisByTranscript[transcript.id],
        plan: planByTranscript[transcript.id],
        workflows: transcriptWorkflows,
        analyzeDone: analyzeReady,
        planReady,
        workflowCount: transcriptWorkflows.length,
        executedCount,
        workflowReady,
        executeComplete,
        approvalsPending: workflowsNeedingApproval(transcriptWorkflows).length,
        progress,
      };
    });
  }, [
    transcripts,
    analysisByTranscript,
    planByTranscript,
    workflowsByTranscript,
    transcriptProgress,
  ]);

  useEffect(() => {
    setTranscriptProgress((prev) => {
      const next = { ...prev };
      let changed = false;
      transcripts.forEach((transcript) => {
        const analysis = analysisByTranscript[transcript.id];
        const plan = planByTranscript[transcript.id];
        const transcriptWorkflows = workflowsByTranscript[transcript.id] || [];
        const executedCount = transcriptWorkflows.filter(
          (workflow) => workflow.status === "EXECUTED"
        ).length;
        let baseline = 0;
        if (analysis) baseline = 25;
        if (plan) baseline = Math.max(baseline, 50);
        if (transcriptWorkflows.length > 0) baseline = Math.max(baseline, 75);
        if (
          transcriptWorkflows.length > 0 &&
          executedCount === transcriptWorkflows.length &&
          transcriptWorkflows.length > 0
        ) {
          baseline = 100;
        }
        const current = next[transcript.id] ?? 0;
        if (baseline > current) {
          next[transcript.id] = baseline;
          changed = true;
        }
      });
      return changed ? next : prev;
    });
  }, [
    transcripts,
    analysisByTranscript,
    planByTranscript,
    workflowsByTranscript,
  ]);

  const metrics = useMemo(() => {
    const processed = runs.reduce((acc, run) => acc + run.transcript_ids.length, 0);
    const autoApproved = workflows.filter((workflow) => workflow.status === "AUTO_APPROVED").length;
    const manualReview = workflows.filter((workflow) => workflow.status === "AWAITING_APPROVAL").length;

    const durations: number[] = runs
      .map((run) => {
        if (!run.started_at || !run.completed_at) return undefined;
        const start = new Date(run.started_at).getTime();
        const end = new Date(run.completed_at).getTime();
        if (Number.isNaN(start) || Number.isNaN(end)) return undefined;
        return Math.max(end - start, 0);
      })
      .filter((value): value is number => typeof value === "number");

    const avgDuration = durations.length
      ? `${(durations.reduce((a, b) => a + b, 0) / durations.length / 60000).toFixed(1)}min`
      : "3.2min";

    const successRate = runs.length
      ? `${(
          (runs.filter((run) => run.status === "COMPLETED").length / runs.length) * 100
        ).toFixed(1)}%`
      : "96.8%";

    const errorsRate = runs.length
      ? `${(
          (runs.filter((run) => run.status === "FAILED").length / runs.length) * 100
        ).toFixed(1)}%`
      : "1.2%";

    const pending = workflowsNeedingApproval(workflows).length;
    const critical = workflows.filter((workflow) => workflow.risk_level === "HIGH").length;
    const overdue = workflows.filter((workflow) => workflow.status.toLowerCase().includes("overdue")).length;

    return {
      processed,
      autoApproved,
      manualReview,
      avgDuration,
      successRate,
      errorsRate,
      pending,
      critical,
      overdue,
    };
  }, [runs, workflows]);

  const runPipeline = useMutation({
    mutationFn: (params: { transcript_ids: string[]; auto_approve: boolean }) =>
      orchestrationApi.runPipeline(params.transcript_ids, params.auto_approve),
    onSuccess: (data, variables) => {
      setActiveRun(data.run_id);
      const transcriptIds = variables.transcript_ids || [];
      ensureTranscriptsTracked(transcriptIds);
      updateProgressFor(transcriptIds, 5);
      lastStageRef.current = null;
      setSelectedTranscripts([]);
      queryClient.invalidateQueries({ queryKey: ["orchestration-runs"] });
    },
  });

  const approveWorkflow = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason?: string }) =>
      workflowApi.approve(id, {
        approved_by: "UI_AUTO",
        reasoning: reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    },
  });

  const rejectWorkflow = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) =>
      workflowApi.reject(id, {
        rejected_by: "UI_AUTO",
        reason,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
    },
  });

  const { data: runStatus } = useQuery({
    queryKey: ["new-pipeline2-run-status", activeRun],
    queryFn: () => orchestrationApi.getStatus(activeRun!),
    enabled: Boolean(activeRun),
    refetchInterval: 2000,
    refetchIntervalInBackground: true,
  });

  useEffect(() => {
    if (!runStatus) return;

    if (Array.isArray(runStatus.transcript_ids)) {
      ensureTranscriptsTracked(runStatus.transcript_ids);
    }

    const stageRaw = runStatus.stage || "";
    if (stageRaw.startsWith("PROCESSING_")) {
      const id = stageRaw.slice("PROCESSING_".length);
      if (id) {
        processingTranscriptRef.current = id;
        ensureTranscriptsTracked([id]);
        updateProgressFor([id], 5);
      }
    }

    const stageTarget = stageTargetForStatus(stageRaw, runStatus);
    if (stageTarget !== null) {
      let targetIds: string[] = [];
      if (stageRaw === "COMPLETE") {
        targetIds = runStatus.transcript_ids || activeTranscripts;
      } else if (processingTranscriptRef.current) {
        targetIds = [processingTranscriptRef.current];
      } else if (Array.isArray(runStatus.transcript_ids)) {
        targetIds = runStatus.transcript_ids;
      } else {
        targetIds = activeTranscripts;
      }
      updateProgressFor(targetIds, stageTarget);
    }

    if (Array.isArray(runStatus.results)) {
      const completedIds = runStatus.results
        .map((result) => result?.transcript_id)
        .filter((id): id is string => Boolean(id));
      if (completedIds.length) {
        ensureTranscriptsTracked(completedIds);
        updateProgressFor(completedIds, 100);
      }
    }

    if (runStatus.status === "COMPLETED") {
      updateProgressFor(runStatus.transcript_ids || activeTranscripts, 100);
      processingTranscriptRef.current = null;
    }

    if (runStatus.stage && runStatus.stage !== lastStageRef.current) {
      lastStageRef.current = runStatus.stage;
      if (runStatus.stage.includes("ANALYSIS")) {
        queryClient.invalidateQueries({ queryKey: ["analyses"] });
      }
      if (runStatus.stage.includes("PLAN")) {
        queryClient.invalidateQueries({ queryKey: ["plans"] });
      }
      if (runStatus.stage.includes("WORKFLOW") || runStatus.stage.includes("EXECUTION")) {
        queryClient.invalidateQueries({ queryKey: ["workflows"] });
      }
      queryClient.invalidateQueries({ queryKey: ["orchestration-runs"] });
    }

    if (runStatus.status === "COMPLETED" || runStatus.status === "FAILED") {
      lastStageRef.current = null;
      setActiveRun(null);
      setActiveTranscripts([]);
      processingTranscriptRef.current = null;
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      queryClient.invalidateQueries({ queryKey: ["analyses"] });
      queryClient.invalidateQueries({ queryKey: ["transcripts"] });
      queryClient.invalidateQueries({ queryKey: ["orchestration-runs"] });
    }
  }, [
    runStatus,
    queryClient,
    ensureTranscriptsTracked,
    updateProgressFor,
    activeTranscripts,
  ]);

  const toggleTranscript = (id: string) => {
    setSelectedTranscripts((prev) =>
      prev.includes(id) ? prev.filter((value) => value !== id) : [...prev, id]
    );
  };

  const toggleExpanded = (id: string) => {
    setExpandedTranscript((current) => (current === id ? null : id));
  };

  const handleApprove = (workflowId: string) => {
    approveWorkflow.mutate({ id: workflowId, reason: approvalNotes[workflowId] });
  };

  const handleReject = (workflowId: string) => {
    const reason = approvalNotes[workflowId] || "Rejected from dashboard";
    rejectWorkflow.mutate({ id: workflowId, reason });
  };

  const openWorkflowDetails = (workflowId: string) => {
    window.dispatchEvent(
      new CustomEvent("ccan:open-workflow-details", {
        detail: { workflowId },
      })
    );
  };

  return (
    <div className="space-y-6 bg-gray-50 p-6 font-mono text-sm">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Today's Metrics</h2>
          <div className="mt-3 space-y-1 text-[13px] text-slate-700">
            <div>Processed: <span className="font-semibold">{metrics.processed}</span></div>
            <div>Auto-Approved: <span className="font-semibold">{metrics.autoApproved}</span></div>
            <div>Manual Review: <span className="font-semibold">{metrics.manualReview}</span></div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Performance</h2>
          <div className="mt-3 space-y-1 text-[13px] text-slate-700">
            <div>Avg Time: <span className="font-semibold">{metrics.avgDuration}</span></div>
            <div>Success: <span className="font-semibold">{metrics.successRate}</span></div>
            <div>Errors: <span className="font-semibold">{metrics.errorsRate}</span></div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Compliance</h2>
          <div className="mt-3 space-y-1 text-[13px] text-slate-700">
            <div>SLA Met: <span className="font-semibold">98.7%</span></div>
            <div>Audit: <span className="font-semibold">100%</span></div>
            <div>Policy: <span className="font-semibold">✓</span></div>
          </div>
        </div>
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-slate-500">Queue Status</h2>
          <div className="mt-3 space-y-1 text-[13px] text-slate-700">
            <div>Pending: <span className="font-semibold">{metrics.pending}</span></div>
            <div>Critical: <span className="font-semibold">{metrics.critical}</span></div>
            <div>Overdue: <span className="font-semibold">{metrics.overdue}</span></div>
          </div>
        </div>
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="px-5 py-4">
          <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">
            Transcript Pipeline Manager
          </div>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="bg-slate-100 text-[12px] uppercase tracking-wide text-slate-600">
              <tr>
                <th className="px-5 py-3">ID</th>
                <th className="px-5 py-3">Customer</th>
                <th className="px-5 py-3">Topic</th>
                <th className="px-5 py-3">Progress</th>
                <th className="px-5 py-3">Analyze</th>
                <th className="px-5 py-3">Plan</th>
                <th className="px-5 py-3">Workflow</th>
                <th className="px-5 py-3">Execute</th>
                <th className="px-5 py-3">Time</th>
              </tr>
            </thead>
            <tbody className="bg-white text-[13px]">
              {rows.map((row) => {
                const isExpanded = expandedTranscript === row.transcript.id;
                const workflowLabel = row.workflowCount
                  ? `${row.workflowCount} ${row.workflowCount === 1 ? "Workflow" : "Workflows"}${
                      row.approvalsPending ? ` (${row.approvalsPending} pending)` : ""
                    }`
                  : "—";
                const executionLabel = row.workflowCount
                  ? `${row.executedCount}/${row.workflowCount}`
                  : "—";
                const clampedProgress = Math.min(
                  Math.max(row.progress, 0),
                  100
                );
                const progressLabel = Math.round(clampedProgress);
                return (
                  <React.Fragment key={row.transcript.id}>
                    <tr
                      className={`border-t hover:bg-slate-50 ${isExpanded ? "bg-slate-50" : ""}`}
                    >
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={selectedTranscripts.includes(row.transcript.id)}
                            onChange={() => toggleTranscript(row.transcript.id)}
                            aria-label={`Select ${row.transcript.id}`}
                          />
                          <button
                            className="font-semibold text-blue-600 underline"
                            onClick={() => toggleExpanded(row.transcript.id)}
                          >
                            {row.transcript.id}
                          </button>
                        </div>
                      </td>
                      <td className="px-5 py-3">{row.transcript.customer || "—"}</td>
                      <td className="px-5 py-3 text-slate-700">{row.transcript.topic || "—"}</td>
                      <td className="px-5 py-3">
                        <div className="w-28">
                          <div className="h-2 w-full rounded-full bg-slate-200">
                            <div
                              className="h-2 rounded-full bg-blue-500"
                              style={{
                                width: `${clampedProgress}%`,
                                transition: "width 0.8s ease-in-out",
                              }}
                            />
                          </div>
                          <div className="mt-1 text-[11px] text-slate-500">{progressLabel}%</div>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        {row.analyzeDone ? (
                          <Check className="h-4 w-4 text-green-500" aria-hidden="true" />
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        {row.planReady ? (
                          <Check className="h-4 w-4 text-green-500" aria-hidden="true" />
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        {row.workflowReady ? (
                          <div className="flex items-center gap-2 text-slate-700">
                            <Check className="h-4 w-4 text-green-500" aria-hidden="true" />
                            <span>{workflowLabel}</span>
                          </div>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3">
                        {row.executeComplete ? (
                          <div className="flex items-center gap-2 text-slate-700">
                            <Check className="h-4 w-4 text-green-500" aria-hidden="true" />
                            <span>{executionLabel}</span>
                          </div>
                        ) : row.workflowCount ? (
                          <span className="text-slate-500">{executionLabel}</span>
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-slate-700">
                        {formatMinutes(row.transcript.duration_sec, row.transcript.created_at)}
                      </td>
                    </tr>
                    {isExpanded ? (
                      <tr className="border-t bg-slate-50">
                        <td colSpan={9} className="px-5 pb-4 pt-0">
                          <div className="space-y-3 py-3">
                            <div className="grid gap-4 text-xs text-slate-600 md:grid-cols-3">
                              {Object.entries(WF_LABELS).map(([type, label]) => {
                                const typed = row.workflows.filter(
                                  (workflow) => workflow.workflow_type === type
                                );
                                if (typed.length === 0) return null;
                                return (
                                  <div key={type} className="space-y-2">
                                    <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">
                                      {label}
                                    </div>
                                    <ul className="space-y-1">
                                      {typed.map((workflow) => {
                                        const noteKey = workflow.id;
                                        const note = approvalNotes[noteKey] || "";
                                        const statusLabel = normalizeStatusLabel(workflow.status);
                                        const description =
                                          workflow.workflow_data?.description ||
                                          workflow.workflow_data?.actions?.[0] ||
                                          workflow.workflow_type;
                                        const priority = workflow.workflow_data?.priority || "";
                                        const risk = workflow.risk_level || "";
                                        const priorityStyle =
                                          priority.toLowerCase() === "high"
                                            ? "bg-red-100 text-red-700 border-red-200"
                                            : priority.toLowerCase() === "medium"
                                            ? "bg-orange-100 text-orange-700 border-orange-200"
                                            : priority.toLowerCase() === "low"
                                            ? "bg-green-100 text-green-700 border-green-200"
                                            : "bg-slate-100 text-slate-600 border-slate-200";
                                        const riskStyle =
                                          risk === "HIGH"
                                            ? "bg-red-100 text-red-700 border-red-200"
                                            : risk === "MEDIUM"
                                            ? "bg-orange-100 text-orange-700 border-orange-200"
                                            : risk === "LOW"
                                            ? "bg-green-100 text-green-700 border-green-200"
                                            : "bg-slate-100 text-slate-600 border-slate-200";
                                        return (
                                          <li
                                            key={workflow.id}
                                            className="rounded border border-slate-200 bg-white p-3 shadow-sm"
                                          >
                                            <div className="flex items-start justify-between gap-3">
                                              <div>
                                                <div className="font-semibold text-slate-700">
                                                  {description}
                                                </div>
                                                <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-slate-500">
                                                  <span className="uppercase tracking-wide text-slate-400">
                                                    {statusLabel}
                                                  </span>
                                                  {priority ? (
                                                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${priorityStyle}`}>
                                                      Priority: {priority}
                                                    </span>
                                                  ) : null}
                                                  {risk ? (
                                                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${riskStyle}`}>
                                                      Risk: {risk}
                                                    </span>
                                                  ) : null}
                                                  <button
                                                    type="button"
                                                    className="text-blue-600 underline"
                                                    onClick={() => openWorkflowDetails(workflow.id)}
                                                  >
                                                    Details
                                                  </button>
                                                </div>
                                              </div>
                                              <CheckCircle2
                                                className={`h-4 w-4 flex-shrink-0 ${
                                                  workflow.status === "EXECUTED"
                                                    ? "text-green-500"
                                                    : "text-slate-300"
                                                }`}
                                              />
                                            </div>

                                            <div className="mt-2 flex flex-col gap-2 sm:flex-row sm:items-center">
                                              <input
                                                type="text"
                                                value={note}
                                                onChange={(event) =>
                                                  setApprovalNotes((prev) => ({
                                                    ...prev,
                                                    [noteKey]: event.target.value,
                                                  }))
                                                }
                                                placeholder="Approval reason..."
                                                className="flex-1 rounded border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700"
                                              />
                                              <div className="flex gap-2 text-xs">
                                                <button
                                                  onClick={() => handleApprove(workflow.id)}
                                                  className="rounded bg-blue-600 px-3 py-1 font-semibold text-white"
                                                  disabled={approveWorkflow.isPending}
                                                >
                                                  Approve
                                                </button>
                                                <button
                                                  onClick={() => handleReject(workflow.id)}
                                                  className="rounded bg-red-500 px-3 py-1 font-semibold text-white"
                                                  disabled={rejectWorkflow.isPending}
                                                >
                                                  Reject
                                                </button>
                                              </div>
                                            </div>
                                          </li>
                                        );
                                      })}
                                    </ul>
                                  </div>
                                );
                              })}
                            </div>
                            <div className="flex items-center gap-4 text-[12px] text-blue-600">
                              <button className="underline" onClick={() => toggleExpanded(row.transcript.id)}>
                                View Analyze
                              </button>
                              <button className="underline" onClick={() => toggleExpanded(row.transcript.id)}>
                                View Plan
                              </button>
                            </div>
                          </div>
                        </td>
                      </tr>
                    ) : null}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        <div className="flex flex-wrap items-center gap-3 px-5 py-4">
          <button
            onClick={() =>
              runPipeline.mutate({ transcript_ids: selectedTranscripts, auto_approve: false })
            }
            disabled={selectedTranscripts.length === 0 || runPipeline.isPending}
            className="flex items-center gap-2 rounded-full bg-blue-600 px-5 py-2 font-semibold text-white shadow disabled:opacity-50"
          >
            <Play className="h-4 w-4" /> Start
          </button>
          <button
            disabled
            className="flex items-center gap-2 rounded-full bg-yellow-400 px-5 py-2 font-semibold text-slate-900 shadow disabled:cursor-not-allowed disabled:opacity-80"
          >
            <Pause className="h-4 w-4" /> Pause
          </button>
          <button
            onClick={() => setExpandedTranscript(selectedTranscripts[0] || null)}
            className="flex items-center gap-2 rounded-full bg-slate-900 px-5 py-2 font-semibold text-white shadow"
          >
            <BarChart2 className="h-4 w-4" /> Progress
          </button>
        </div>
      </section>

    </div>
  );
}
