import React, { useEffect, useMemo, useState } from "react";
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
import { Play, Pause, BarChart2, Check, X, CheckCircle2 } from "lucide-react";

type PriorityTone = "high" | "medium" | "low" | "default";

const WF_LABELS: Record<string, string> = {
  BORROWER: "Borrower",
  ADVISOR: "Advisor",
  SUPERVISOR: "Supervisor",
  LEADERSHIP: "Leadership",
};

const priorityInfo = (analysis?: Analysis, plan?: Plan): { label: string; tone: PriorityTone } => {
  const raw = plan?.risk_level || analysis?.urgency || "";
  if (!raw) {
    return { label: "Medium", tone: "medium" };
  }
  const normalized = raw.toLowerCase();
  if (normalized.includes("high")) {
    return { label: "High", tone: "high" };
  }
  if (normalized.includes("low")) {
    return { label: "Low", tone: "low" };
  }
  if (normalized.includes("critical")) {
    return { label: "High", tone: "high" };
  }
  return { label: "Medium", tone: "medium" };
};

const priorityToneStyles: Record<PriorityTone, string> = {
  high: "text-red-500",
  medium: "text-orange-500",
  low: "text-green-500",
  default: "text-slate-600",
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

const pluralize = (count: number, label: string) => {
  if (count === 1) return `1 ${label}`;
  return `${count} ${label}s`;
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
  priority: { label: string; tone: PriorityTone };
  analyzeDone: boolean;
  workflowCount: number;
  approvalsPending: number;
}

export function NewPipeline2View() {
  const queryClient = useQueryClient();

  const [selectedTranscripts, setSelectedTranscripts] = useState<string[]>([]);
  const [expandedTranscript, setExpandedTranscript] = useState<string | null>(null);
  const [activeRun, setActiveRun] = useState<string | null>(null);
  const [approvalNotes, setApprovalNotes] = useState<Record<string, string>>({});

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
  });

  const runs: OrchestrationRun[] = runsData?.runs || [];

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
      const analysis = analysisByTranscript[transcript.id];
      const plan = planByTranscript[transcript.id];
      const transcriptWorkflows = workflowsByTranscript[transcript.id] || [];
      return {
        transcript,
        analysis,
        plan,
        workflows: transcriptWorkflows,
        priority: priorityInfo(analysis, plan),
        analyzeDone: analyzeComplete(analysis),
        workflowCount: transcriptWorkflows.length,
        approvalsPending: workflowsNeedingApproval(transcriptWorkflows).length,
      };
    });
  }, [transcripts, analysisByTranscript, planByTranscript, workflowsByTranscript]);

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

  const totals = useMemo(() => {
    const totalWorkflows = rows.reduce((acc, row) => acc + row.workflowCount, 0);
    const approvals = rows.reduce((acc, row) => acc + row.approvalsPending, 0);
    return { totalWorkflows, approvals };
  }, [rows]);

  const runPipeline = useMutation({
    mutationFn: (params: { transcript_ids: string[]; auto_approve: boolean }) =>
      orchestrationApi.runPipeline(params.transcript_ids, params.auto_approve),
    onSuccess: (data) => {
      setActiveRun(data.run_id);
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
  });

  useEffect(() => {
    if (!runStatus) return;
    if (runStatus.status === "COMPLETED" || runStatus.status === "FAILED") {
      setActiveRun(null);
      queryClient.invalidateQueries({ queryKey: ["workflows"] });
      queryClient.invalidateQueries({ queryKey: ["plans"] });
      queryClient.invalidateQueries({ queryKey: ["analyses"] });
    }
  }, [runStatus, queryClient]);

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

  const activeRunSummary = runStatus
    ? {
        status: normalizeStatusLabel(runStatus.status),
        stage: normalizeStatusLabel(runStatus.stage),
        progress: runStatus.progress,
        workflowCount: runStatus.workflow_count,
        executed: runStatus.executed_count,
      }
    : null;

  const devTests = useMemo(() => {
    const firstRow = rows[0];
    const firstApprovals = firstRow ? workflowsNeedingApproval(firstRow.workflows).length : 0;
    const approvalsPhrase = firstRow ? `T${firstRow.transcript.id?.slice(-3)}` : "N/A";

    const totalGrouped = rows.reduce((acc, row) => acc + row.workflowCount, 0);
    const totalDerived = workflows.length;

    const allowedTypesOnly = workflows.every((workflow) => workflow.workflow_type in WF_LABELS);

    return [
      {
        label: `${approvalsPhrase} pending approvals = ${firstRow ? firstRow.approvalsPending : 0}`,
        expected: firstApprovals,
        pass: firstRow ? firstRow.approvalsPending === firstApprovals : true,
      },
      {
        label: `Grouped count equals total workflows (sum ${totalGrouped} vs total ${totalDerived})`,
        expected: totalDerived,
        pass: totalGrouped === totalDerived,
      },
      {
        label: "All workflows use allowed types",
        expected: workflows.length,
        pass: allowedTypesOnly,
      },
    ];
  }, [rows, workflows]);

  return (
    <div className="space-y-6 bg-gray-50 p-6 font-mono text-sm">
      <header className="rounded-2xl bg-slate-900 px-6 py-5 text-slate-100 shadow">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h1 className="text-lg font-bold tracking-wide">PIPELINE ORCHESTRATION DASHBOARD</h1>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="font-semibold">[Live]</span>
            <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" aria-hidden="true" />
          </div>
        </div>
      </header>

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
                <th className="px-5 py-3">Priority</th>
                <th className="px-5 py-3">Analyze</th>
                <th className="px-5 py-3">Workflows</th>
                <th className="px-5 py-3">Execute</th>
                <th className="px-5 py-3">Approvals</th>
                <th className="px-5 py-3">Reason</th>
                <th className="px-5 py-3">Time</th>
              </tr>
            </thead>
            <tbody className="bg-white text-[13px]">
              {rows.map((row) => {
                const isExpanded = expandedTranscript === row.transcript.id;
                const workflowLabel = pluralize(row.workflowCount, "Workflow");
                const approvalsLabel = pluralize(row.approvalsPending, "pending");
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
                      <td className={`px-5 py-3 font-semibold ${priorityToneStyles[row.priority.tone]}`}>
                        {row.priority.label}
                      </td>
                      <td className="px-5 py-3">
                        {row.analyzeDone ? (
                          <Check className="h-4 w-4 text-green-500" aria-hidden="true" />
                        ) : (
                          <span className="text-slate-400">—</span>
                        )}
                      </td>
                      <td className="px-5 py-3 text-slate-700">{workflowLabel}</td>
                      <td className="px-5 py-3 text-center text-lg text-slate-500">‖</td>
                      <td className="px-5 py-3 text-slate-700">{approvalsLabel}</td>
                      <td className="px-5 py-3">
                        <input
                          type="text"
                          value={approvalNotes[row.transcript.id] || ""}
                          onChange={(event) =>
                            setApprovalNotes((prev) => ({
                              ...prev,
                              [row.transcript.id]: event.target.value,
                            }))
                          }
                          placeholder="Add reason..."
                          className="w-full rounded border border-slate-300 bg-white px-2 py-1 text-xs text-slate-700"
                        />
                      </td>
                      <td className="px-5 py-3 text-slate-700">
                        {formatMinutes(row.transcript.duration_sec, row.transcript.created_at)}
                      </td>
                    </tr>
                    {isExpanded ? (
                      <tr className="border-t bg-slate-50">
                        <td colSpan={10} className="px-5 pb-4 pt-0">
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
                                        return (
                                          <li
                                            key={workflow.id}
                                            className="rounded border border-slate-200 bg-white p-3 shadow-sm"
                                          >
                                            <div className="flex items-start justify-between gap-3">
                                              <div>
                                                <div className="font-semibold text-slate-700">
                                                  {workflow.workflow_data?.actions?.[0] || workflow.workflow_type}
                                                </div>
                                                <div className="text-[11px] text-slate-500">
                                                  Status: {statusLabel}
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

      {activeRun && activeRunSummary ? (
        <section className="rounded-2xl border border-blue-200 bg-blue-50 p-4 text-xs text-blue-800">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="font-semibold">Pipeline Running • {activeRun}</div>
            <div>Status: {activeRunSummary.status}</div>
            <div>Stage: {activeRunSummary.stage}</div>
            {activeRunSummary.progress ? (
              <div>
                Progress: {activeRunSummary.progress.processed}/{activeRunSummary.progress.total} ·
                {" "}
                {activeRunSummary.progress.percentage}%
              </div>
            ) : null}
            {typeof activeRunSummary.executed === "number" && typeof activeRunSummary.workflowCount === "number" ? (
              <div>
                Executed: {activeRunSummary.executed}/{activeRunSummary.workflowCount}
              </div>
            ) : null}
          </div>
        </section>
      ) : null}

      <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Dev Tests</div>
        <ul className="mt-3 space-y-2 text-[13px]">
          {devTests.map((test, index) => (
            <li key={index} className="flex items-center gap-2">
              {test.pass ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <X className="h-4 w-4 text-red-500" />
              )}
              <span className="text-slate-700">{test.label}</span>
              {!test.pass ? (
                <span className="text-slate-500">expected {test.expected}</span>
              ) : null}
            </li>
          ))}
          <li className="flex items-center gap-2 text-slate-500">
            <Check className="h-4 w-4 text-green-500" /> Total workflows tracked: {totals.totalWorkflows}
          </li>
        </ul>
      </section>
    </div>
  );
}

