import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useRoute } from "wouter";
import type { Case, Transcript, Analysis, Action } from "@shared/schema";

export default function CaseDetailPage() {
  const [, params] = useRoute("/case/:caseId");
  const caseId = params?.caseId;
  const [showFull, setShowFull] = useState(false);

  const { data: case_, isLoading: caseLoading } = useQuery<Case>({
    queryKey: ["/api/cases", caseId],
    enabled: !!caseId,
  });

  const { data: transcripts = [], isLoading: transcriptsLoading } = useQuery<Transcript[]>({
    queryKey: ["/api/cases", caseId, "/transcripts"],
    enabled: !!caseId,
  });

  const { data: analysis, isLoading: analysisLoading } = useQuery<Analysis>({
    queryKey: ["/api/cases", caseId, "/analysis"],
    enabled: !!caseId,
  });

  const { data: actions = [], isLoading: actionsLoading } = useQuery<Action[]>({
    queryKey: ["/api/cases", caseId, "/actions"],
    enabled: !!caseId,
  });

  if (caseLoading || transcriptsLoading || analysisLoading || actionsLoading) {
    return (
      <div className="p-6 max-w-screen-xl mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          <div className="h-32 bg-gray-200 rounded"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (!case_) {
    return (
      <div className="p-6 max-w-screen-xl mx-auto">
        <div className="text-center text-red-600">Case not found</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-screen-xl mx-auto space-y-6" data-testid="case-detail-page">
      {/* Header bar */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="page-title">
            Customer Service Case #{case_.id.slice(-4)}
          </h1>
          <p className="text-sm text-muted-foreground" data-testid="case-subtitle">
            {case_.customerId} • {case_.scenario}
          </p>
        </div>
        <div className="flex gap-2">
          <button className="text-sm rounded-full border border-border px-3 py-1 hover:bg-accent transition-colors" data-testid="button-reject">
            Reject
          </button>
          <button className="text-sm rounded-full bg-primary text-primary-foreground px-3 py-1 hover:bg-primary/90 transition-colors" data-testid="button-approve">
            Approve Plan
          </button>
        </div>
      </div>

      {/* Summary */}
      <div className="rounded-2xl border border-border p-4 grid grid-cols-2 gap-4 text-sm bg-card">
        <div>
          <span className="text-muted-foreground">Customer</span>
          <div className="font-medium" data-testid="case-customer">{case_.customerId}</div>
        </div>
        <div>
          <span className="text-muted-foreground">Scenario</span>
          <div className="font-medium" data-testid="case-scenario">{case_.scenario}</div>
        </div>
        <div>
          <span className="text-muted-foreground">Messages</span>
          <div className="font-medium" data-testid="case-exchanges">{case_.exchanges} exchanges</div>
        </div>
        <div>
          <span className="text-muted-foreground">Financial Impact</span>
          <div className="font-medium" data-testid="case-impact">{case_.financialImpact}</div>
        </div>
        <div>
          <span className="text-muted-foreground">Risk</span>
          <div className="font-medium text-destructive" data-testid="case-risk">{case_.risk}</div>
        </div>
        <div>
          <span className="text-muted-foreground">Created</span>
          <div className="font-medium" data-testid="case-created">
            {new Date(case_.createdAt!).toLocaleString()}
          </div>
        </div>
      </div>

      {/* Transcript */}
      <div className="rounded-2xl border border-border p-4 bg-card">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Transcript</h2>
          <button
            onClick={() => setShowFull(!showFull)}
            className="text-xs rounded-full bg-primary text-primary-foreground px-3 py-1 hover:bg-primary/90 transition-colors"
            data-testid="button-toggle-transcript"
          >
            {showFull ? "Hide" : `Show full (${transcripts.length})`}
          </button>
        </div>
        <div className="space-y-2 text-sm text-muted-foreground max-h-64 overflow-auto" data-testid="transcript-content">
          {(showFull ? transcripts : transcripts.slice(0, 3)).map((t, i) => (
            <div key={i}>
              <span className="font-semibold text-foreground">{t.speaker}:</span> {t.content}
            </div>
          ))}
        </div>
      </div>

      {/* AI Analysis */}
      {analysis && (
        <div className="rounded-2xl border border-border p-4 space-y-3 bg-card">
          <h2 className="font-semibold">AI Analysis</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
            <div className="rounded-xl border border-border p-3 bg-background">
              <div className="text-xs text-muted-foreground">Intent</div>
              <div className="font-medium" data-testid="analysis-intent">{analysis.intent}</div>
              <div className="text-xs" data-testid="analysis-confidence">
                Confidence {Math.round(Number(analysis.confidence) * 100)}%
              </div>
            </div>
            <div className="rounded-xl border border-border p-3 bg-background">
              <div className="text-xs text-muted-foreground">Sentiment</div>
              <div className="font-medium capitalize" data-testid="analysis-sentiment">{analysis.sentiment}</div>
            </div>
            <div className="rounded-xl border border-border p-3 bg-background">
              <div className="text-xs text-muted-foreground">Risks</div>
              {analysis.risks?.map((r, i) => (
                <div key={i} className="flex justify-between">
                  <span>{r.label}</span>
                  <span className={`font-semibold ${
                    r.value > 0.5 ? "text-destructive" : 
                    r.value > 0.2 ? "text-amber-600" : 
                    "text-emerald-600"
                  }`} data-testid={`risk-${r.label.toLowerCase()}`}>
                    {Math.round(r.value * 100)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Action Plan */}
      <div className="rounded-2xl border border-border overflow-hidden bg-card">
        <div className="px-4 py-2 bg-muted text-sm font-medium">
          Action Plan Details ({actions.length})
        </div>
        <table className="w-full text-sm">
          <thead className="bg-muted text-left">
            <tr className="text-muted-foreground">
              <th className="px-4 py-2">Action</th>
              <th className="px-4 py-2">Category</th>
              <th className="px-4 py-2">Risk</th>
              <th className="px-4 py-2">Impact</th>
              <th className="px-4 py-2">Submitted</th>
              <th className="px-4 py-2">Decision</th>
            </tr>
          </thead>
          <tbody>
            {actions.map((a, i) => (
              <tr key={i} className="border-t border-border hover:bg-accent transition-colors">
                <td className="px-4 py-2 font-medium text-foreground" data-testid={`action-name-${i}`}>
                  {a.action}
                </td>
                <td className="px-4 py-2" data-testid={`action-category-${i}`}>{a.category}</td>
                <td className="px-4 py-2" data-testid={`action-risk-${i}`}>{a.risk}</td>
                <td className="px-4 py-2" data-testid={`action-impact-${i}`}>{a.impact}</td>
                <td className="px-4 py-2 whitespace-nowrap" data-testid={`action-submitted-${i}`}>
                  {new Date(a.submittedAt!).toLocaleString()}
                </td>
                <td className="px-4 py-2" data-testid={`action-decision-${i}`}>
                  {a.decision.includes("Approved") ? (
                    <span className="text-xs font-medium rounded-full bg-emerald-100 text-emerald-700 px-2.5 py-1">
                      {a.decision}
                    </span>
                  ) : a.decision === "Pending" ? (
                    <div className="flex gap-2">
                      <button className="text-xs rounded-full border border-border px-3 py-1 hover:bg-accent transition-colors" data-testid={`button-reject-action-${i}`}>
                        Reject
                      </button>
                      <button className="text-xs rounded-full bg-primary text-primary-foreground px-3 py-1 hover:bg-primary/90 transition-colors" data-testid={`button-approve-action-${i}`}>
                        Approve
                      </button>
                    </div>
                  ) : (
                    <span className="text-xs text-muted-foreground">{a.decision}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Supervisor Callout */}
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
        <div className="text-amber-600 text-xl">⚠</div>
        <div>
          <div className="font-semibold text-amber-800">Supervisor Approval Required</div>
          <div class="text-sm text-amber-700">High urgency requires expedited approval</div>
        </div>
      </div>
    </div>
  );
}
