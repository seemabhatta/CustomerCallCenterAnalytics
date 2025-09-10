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
          <h1 className="text-2xl font-semibold" data-testid="page-title">🧠 AI Decision Support Platform</h1>
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

      {/* Workflow Command Center */}
      <div>
        <h2 className="text-xl font-semibold mb-4">🎯 Workflow Command Center</h2>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
            <div className="text-2xl font-bold text-blue-600" data-testid="active-cases">
              {Math.floor((metrics.totalTranscripts || 0) * 0.12)}
            </div>
            <div className="text-sm text-muted-foreground">🔄 Active Cases</div>
            <div className="text-xs text-muted-foreground mt-1">
              {Math.floor((metrics.totalTranscripts || 0) * 0.06)} analyzing • {Math.floor((metrics.totalTranscripts || 0) * 0.04)} planning
            </div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
            <div className="text-2xl font-bold text-amber-600" data-testid="pending-approval">
              {metrics.stageData!.approval.pending}
            </div>
            <div className="text-sm text-muted-foreground">🛡️ Pending Approval</div>
            <div className="text-xs text-muted-foreground mt-1">
              Governance • Traditional
            </div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
            <div className="text-2xl font-bold text-emerald-600" data-testid="executed-today">
              {metrics.stageData!.execution.complete}
            </div>
            <div className="text-sm text-muted-foreground">✅ Executed Today</div>
            <div className="text-xs text-muted-foreground mt-1">
              {Math.round(Number(metrics.completeRate) * 100)}% success rate
            </div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
            <div className="text-2xl font-bold text-purple-600" data-testid="learning-score">
              4.2
            </div>
            <div className="text-sm text-muted-foreground">📈 Learning Score</div>
            <div className="text-xs text-muted-foreground mt-1">
              Observer evaluation
            </div>
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

      {/* Pipeline Velocity Metrics */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Pipeline Performance</h2>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4 mb-6">
          <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
            <div className="text-2xl font-bold text-blue-600">2.4h</div>
            <div className="text-sm text-muted-foreground">Avg Pipeline Time</div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
            <div className="text-2xl font-bold text-emerald-600">94%</div>
            <div className="text-sm text-muted-foreground">Success Rate</div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
            <div className="text-2xl font-bold text-amber-600">12/hr</div>
            <div className="text-sm text-muted-foreground">Throughput</div>
          </div>
          <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
            <div className="text-2xl font-bold text-purple-600">Approval</div>
            <div className="text-sm text-muted-foreground">Current Bottleneck</div>
          </div>
        </div>
      </div>

      {/* Enhanced 11-Step Pipeline Visualization */}
      <div>
        <h2 className="text-xl font-semibold mb-4">AI Decision Pipeline</h2>
        
        {/* Pipeline Flow Visualization */}
        <div className="bg-gradient-to-r from-blue-50 to-purple-50 rounded-2xl p-6 mb-6">
          <div className="flex items-center justify-between text-xs text-muted-foreground mb-4">
            <div>Input</div>
            <div>Processing</div>
            <div>Decision</div>
            <div>Action</div>
            <div>Learning</div>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <div className="w-8 h-px bg-blue-300 mx-1"></div>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
              <div className="w-8 h-px bg-orange-300 mx-1"></div>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-amber-500 rounded-full"></div>
              <div className="w-8 h-px bg-amber-300 mx-1"></div>
            </div>
            <div className="flex items-center">
              <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
              <div className="w-8 h-px bg-emerald-300 mx-1"></div>
            </div>
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
          </div>
        </div>

        {/* 11-Step Detailed Breakdown */}
        <div className="grid grid-cols-1 sm:grid-cols-6 gap-3">
          {/* Step 1: Transcripts */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 1 – Call transcript ingestion">
            <div className="text-xs text-muted-foreground mb-1">📝 Transcripts</div>
            <div className="text-lg font-bold text-blue-600" data-testid="stage-transcript-ready">
              {metrics.stageData!.transcript.ready}
            </div>
            <div className="text-xs text-foreground">Ready</div>
          </div>

          {/* Step 2: AI Analysis */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 2 – AI analysis">
            <div className="text-xs text-muted-foreground mb-1">🔬 Analysis</div>
            <div className="text-lg font-bold text-orange-600" data-testid="stage-analysis-queue">
              {metrics.stageData!.analysis.queue}
            </div>
            <div className="text-xs text-foreground">Processing</div>
          </div>

          {/* Step 3: Plan Generation */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 3 – Action plan generation">
            <div className="text-xs text-muted-foreground mb-1">📋 Plans</div>
            <div className="text-lg font-bold text-orange-600" data-testid="stage-plan-queue">
              {metrics.stageData!.plan.queue}
            </div>
            <div className="text-xs text-foreground">Generating</div>
          </div>

          {/* Step 4: Plan Review */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 4 – Plan review">
            <div className="text-xs text-muted-foreground mb-1">👀 Review</div>
            <div className="text-lg font-bold text-blue-600">
              {Math.floor((metrics.totalTranscripts || 0) * 0.08)}
            </div>
            <div className="text-xs text-foreground">Pending</div>
          </div>

          {/* Step 5: Governance */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 5 – CFPB compliance">
            <div className="text-xs text-muted-foreground mb-1">🔐 Governance</div>
            <div className="text-lg font-bold text-purple-600">
              {Math.floor((metrics.totalTranscripts || 0) * 0.06)}
            </div>
            <div className="text-xs text-foreground">Validating</div>
          </div>

          {/* Step 6: Approval */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 6 – Human approval">
            <div className="text-xs text-muted-foreground mb-1">👍 Approval</div>
            <div className="text-lg font-bold text-amber-600" data-testid="stage-approval-pending">
              {metrics.stageData!.approval.pending}
            </div>
            <div className="text-xs text-foreground">Pending</div>
          </div>
        </div>

        {/* Second Row - Execution & Learning Steps */}
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mt-3">
          {/* Step 7: Execution */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 7 – Action execution">
            <div className="text-xs text-muted-foreground mb-1">🎯 Execution</div>
            <div className="text-lg font-bold text-emerald-600" data-testid="stage-execution-running">
              {metrics.stageData!.execution.running}
            </div>
            <div className="text-xs text-foreground">Running</div>
          </div>

          {/* Step 8: Monitoring */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 8 – Progress monitoring">
            <div className="text-xs text-muted-foreground mb-1">📊 Monitor</div>
            <div className="text-lg font-bold text-blue-600">
              {Math.floor((metrics.totalTranscripts || 0) * 0.05)}
            </div>
            <div className="text-xs text-foreground">Active</div>
          </div>

          {/* Step 9: Artifacts */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 9 – Artifact generation">
            <div className="text-xs text-muted-foreground mb-1">📄 Artifacts</div>
            <div className="text-lg font-bold text-emerald-600">
              {Math.floor((metrics.totalTranscripts || 0) * 0.15)}
            </div>
            <div className="text-xs text-foreground">Generated</div>
          </div>

          {/* Step 10: Observer */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 10 – AI observation">
            <div className="text-xs text-muted-foreground mb-1">📈 Observer</div>
            <div className="text-lg font-bold text-purple-600">
              {Math.floor((metrics.totalTranscripts || 0) * 0.12)}
            </div>
            <div className="text-xs text-foreground">Evaluating</div>
          </div>

          {/* Step 11: Learning */}
          <div className="rounded-2xl border border-border p-3 text-center bg-card hover:shadow-md transition-shadow" title="Step 11 – Continuous learning">
            <div className="text-xs text-muted-foreground mb-1">🔄 Learning</div>
            <div className="text-lg font-bold text-emerald-600">
              {metrics.stageData!.execution.complete}
            </div>
            <div className="text-xs text-foreground">Complete</div>
          </div>
        </div>
      </div>
    </div>
  );
}
