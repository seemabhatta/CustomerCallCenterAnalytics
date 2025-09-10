import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import type { Metrics } from "@shared/schema";

function delta(curr: number, prev: number) {
  const d = curr - prev;
  const pct = prev === 0 ? 0 : (d / prev) * 100;
  return { d, pct };
}

function Trend({ pct, positiveIsGood = true }: { pct: number; positiveIsGood?: boolean }) {
  const up = pct >= 0;
  const good = positiveIsGood ? up : !up;
  return (
    <span className={`ml-1 inline-flex items-center gap-0.5 text-xs font-medium ${good ? "text-emerald-600" : "text-red-600"}`}>
      <span>{up ? "▲" : "▼"}</span>
      <span className="tabular-nums">{Math.abs(pct).toFixed(1)}%</span>
    </span>
  );
}

export default function DashboardPage() {
  const { data: metrics, isLoading } = useQuery<Metrics>({
    queryKey: ["/api/metrics"],
  });

  if (isLoading) {
    return (
      <div className="p-6 max-w-screen-2xl mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!metrics) {
    return (
      <div className="p-6 max-w-screen-2xl mx-auto">
        <div className="text-center text-red-600">Failed to load metrics</div>
      </div>
    );
  }

  const tDelta = delta(metrics.totalTranscripts || 0, metrics.transcriptsPrev || 0);
  const cDelta = delta(Number(metrics.completeRate || 0), Number(metrics.completeRatePrev || 0));
  const pDelta = delta(Number(metrics.avgProcessingTime || 0), Number(metrics.avgProcessingTimePrev || 0));

  return (
    <div className="p-6 max-w-screen-2xl mx-auto space-y-6" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="page-title">AI Decision Support Platform</h1>
          <p className="text-sm text-muted-foreground">Mortgage Servicing Intelligence • 11-Step Workflow</p>
        </div>
        <div className="text-xs text-muted-foreground" data-testid="last-updated">
          Last updated: {new Date(metrics.lastUpdated!).toLocaleTimeString()}
        </div>
      </div>

      {/* Top metrics with trends */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card" title="Total transcripts ingested vs. yesterday">
          <div className="text-3xl font-bold text-primary tabular-nums" data-testid="metric-transcripts">
            {(metrics.totalTranscripts || 0).toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">
            Total Transcripts
            <Trend pct={tDelta.pct} positiveIsGood={true} />
          </div>
        </div>
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card" title="Percent of items fully completed vs. yesterday">
          <div className="text-3xl font-bold text-primary tabular-nums" data-testid="metric-complete">
            {Math.round(Number(metrics.completeRate) * 100)}%
          </div>
          <div className="text-sm text-muted-foreground">
            Complete
            <Trend pct={cDelta.pct} positiveIsGood={true} />
          </div>
        </div>
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card" title="Average end‑to‑end processing time vs. yesterday">
          <div className="text-3xl font-bold text-primary tabular-nums" data-testid="metric-processing">
            {Number(metrics.avgProcessingTime)}m
          </div>
          <div className="text-sm text-muted-foreground">
            Avg Processing Time
            <Trend pct={pDelta.pct} positiveIsGood={false} />
          </div>
        </div>
      </div>

      {/* Progress bar with label */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className="text-sm text-muted-foreground">Overall completion</div>
          <div className="text-sm font-medium tabular-nums" data-testid="completion-percentage">
            {Math.round(Number(metrics.completeRate) * 100)}%
          </div>
        </div>
        <div className="w-full h-2.5 bg-muted rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-primary via-blue-400 to-cyan-400" 
            style={{ width: `${Number(metrics.completeRate) * 100}%` }}
          />
        </div>
      </div>

      {/* Bottleneck alert with actions */}
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
        <div className="text-amber-600 text-xl">⚠</div>
        <div className="flex-1">
          <div className="font-semibold text-amber-800">Bottleneck Detected</div>
          <div className="text-sm text-amber-700">High volume in approval stage – consider scaling resources</div>
        </div>
        <div className="flex gap-2">
          <Link href="/approval-queue">
            <button className="text-xs rounded-full border border-amber-300 px-3 py-1 hover:bg-amber-100 transition-colors" data-testid="button-view-queue">
              View Approval Queue
            </button>
          </Link>
          <button className="text-xs rounded-full bg-amber-600 text-white px-3 py-1 hover:bg-amber-700 transition-colors" data-testid="button-scale">
            Scale Resources
          </button>
        </div>
      </div>

      {/* Key Pipeline Stages */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Pipeline Stages</h2>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
          <div className="rounded-2xl border border-border p-4 text-center bg-card" title="Step 1 – Transcript ingestion">
            <div className="text-sm text-muted-foreground mb-1">Transcripts</div>
            <div className="text-2xl font-bold text-emerald-600" data-testid="stage-transcript-ready">
              {metrics.stageData!.transcript.ready}
            </div>
            <div className="text-sm text-foreground">Ready</div>
            <div className="text-xs text-muted-foreground" data-testid="stage-transcript-processing">
              {metrics.stageData!.transcript.processing} Processing
            </div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center bg-card" title="Step 2 – AI analysis">
            <div className="text-sm text-muted-foreground mb-1">Analysis</div>
            <div className="text-2xl font-bold text-orange-600" data-testid="stage-analysis-queue">
              {metrics.stageData!.analysis.queue}
            </div>
            <div className="text-sm text-foreground">In Queue</div>
            <div className="text-xs text-muted-foreground" data-testid="stage-analysis-processing">
              {metrics.stageData!.analysis.processing} Processing
            </div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center bg-card" title="Step 3 – Plan generation">
            <div className="text-sm text-muted-foreground mb-1">Plans</div>
            <div className="text-2xl font-bold text-orange-600" data-testid="stage-plan-queue">
              {metrics.stageData!.plan.queue}
            </div>
            <div className="text-sm text-foreground">Queue</div>
            <div className="text-xs text-muted-foreground" data-testid="stage-plan-generating">
              {metrics.stageData!.plan.generating} Generating
            </div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center bg-card" title="Step 4 – Human approval">
            <div className="text-sm text-muted-foreground mb-1">Approval</div>
            <div className="text-2xl font-bold text-destructive" data-testid="stage-approval-pending">
              {metrics.stageData!.approval.pending}
            </div>
            <div className="text-sm text-foreground">Pending</div>
            <div className="text-xs text-muted-foreground" data-testid="stage-approval-approved">
              {metrics.stageData!.approval.approved} Approved
            </div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center bg-card" title="Step 5 – Action execution">
            <div className="text-sm text-muted-foreground mb-1">Execution</div>
            <div className="text-2xl font-bold text-primary" data-testid="stage-execution-running">
              {metrics.stageData!.execution.running}
            </div>
            <div className="text-sm text-foreground">Running</div>
            <div className="text-xs text-muted-foreground" data-testid="stage-execution-complete">
              {metrics.stageData!.execution.complete} Complete
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
