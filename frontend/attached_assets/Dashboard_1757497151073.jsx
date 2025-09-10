import React from "react";

// ---- Dashboard Landing Page – Pipeline Overview (with trends, labels, icons, actions) ----

const metrics = {
  transcripts: 1228,
  transcriptsPrev: 1160,
  complete: 0.17, // 17%
  completePrev: 0.13,
  avgProcessing: 12.3, // minutes
  avgProcessingPrev: 13.8,
  stages: {
    transcript: { ready: 28, processing: 3 },
    analysis: { queue: 127, processing: 15 },
    plan: { queue: 89, generating: 8 },
    approval: { pending: 234, approved: 568 },
    execution: { running: 187, complete: 208 },
  },
  lastUpdated: "5:09:30 AM",
};

function delta(curr, prev) {
  const d = curr - prev;
  const pct = prev === 0 ? 0 : (d / prev) * 100;
  return { d, pct };
}

function Trend({ pct, positiveIsGood = true }) {
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
  const tDelta = delta(metrics.transcripts, metrics.transcriptsPrev);
  const cDelta = delta(metrics.complete, metrics.completePrev);
  const pDelta = delta(metrics.avgProcessing, metrics.avgProcessingPrev);

  return (
    <div className="p-6 max-w-screen-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Pipeline Overview – 9/10/2025</h1>
          <p className="text-sm text-gray-500">AI‑Powered Monitoring Dashboard</p>
        </div>
        <div className="text-xs text-gray-400">Last updated: {metrics.lastUpdated}</div>
      </div>

      {/* Top metrics with trends */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="rounded-2xl border p-4 text-center shadow-sm" title="Total transcripts ingested vs. yesterday">
          <div className="text-3xl font-bold text-indigo-600 tabular-nums">{metrics.transcripts.toLocaleString()}</div>
          <div className="text-sm text-gray-600">Total Transcripts
            <Trend pct={tDelta.pct} positiveIsGood={true} />
          </div>
        </div>
        <div className="rounded-2xl border p-4 text-center shadow-sm" title="Percent of items fully completed vs. yesterday">
          <div className="text-3xl font-bold text-indigo-600 tabular-nums">{Math.round(metrics.complete*100)}%</div>
          <div className="text-sm text-gray-600">Complete
            <Trend pct={cDelta.pct} positiveIsGood={true} />
          </div>
        </div>
        <div className="rounded-2xl border p-4 text-center shadow-sm" title="Average end‑to‑end processing time vs. yesterday">
          <div className="text-3xl font-bold text-indigo-600 tabular-nums">{metrics.avgProcessing}m</div>
          <div className="text-sm text-gray-600">Avg Processing Time
            <Trend pct={pDelta.pct} positiveIsGood={false} />
          </div>
        </div>
      </div>

      {/* Progress bar with label */}
      <div>
        <div className="flex items-center justify-between mb-1">
          <div className="text-sm text-gray-600">Overall completion</div>
          <div className="text-sm font-medium tabular-nums">{Math.round(metrics.complete*100)}%</div>
        </div>
        <div className="w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-indigo-500 via-blue-400 to-cyan-400" style={{ width: `${metrics.complete*100}%` }} />
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
          <button className="text-xs rounded-full border px-3 py-1 hover:bg-amber-100">View Approval Queue</button>
          <button className="text-xs rounded-full bg-amber-600 text-white px-3 py-1 hover:bg-amber-700">Scale Resources</button>
        </div>
      </div>

      {/* Stage breakdown with icons + tooltips */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Stage Breakdown</h2>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
          <div className="rounded-2xl border p-4 text-center" title="Stage 1 – Transcript ingestion">
            <div className="text-sm text-gray-500 mb-1">📄 Transcript</div>
            <div className="text-2xl font-bold text-emerald-600">{metrics.stages.transcript.ready}</div>
            <div className="text-sm text-gray-600">Ready</div>
            <div className="text-xs text-gray-500">{metrics.stages.transcript.processing} Processing</div>
          </div>
          <div className="rounded-2xl border p-4 text-center" title="Stage 2 – AI analysis">
            <div className="text-sm text-gray-500 mb-1">🔍 Analysis</div>
            <div className="text-2xl font-bold text-orange-600">{metrics.stages.analysis.queue}</div>
            <div className="text-sm text-gray-600">In Queue</div>
            <div className="text-xs text-gray-500">{metrics.stages.analysis.processing} Processing</div>
          </div>
          <div className="rounded-2xl border p-4 text-center" title="Stage 3 – Plan generation">
            <div className="text-sm text-gray-500 mb-1">📋 Plan</div>
            <div className="text-2xl font-bold text-orange-600">{metrics.stages.plan.queue}</div>
            <div className="text-sm text-gray-600">Queue</div>
            <div className="text-xs text-gray-500">{metrics.stages.plan.generating} Generating</div>
          </div>
          <div className="rounded-2xl border p-4 text-center" title="Stage 4 – Human approval">
            <div className="text-sm text-gray-500 mb-1">✅ Approval</div>
            <div className="text-2xl font-bold text-red-600">{metrics.stages.approval.pending}</div>
            <div className="text-sm text-gray-600">Pending</div>
            <div className="text-xs text-gray-500">{metrics.stages.approval.approved} Approved</div>
          </div>
          <div className="rounded-2xl border p-4 text-center" title="Stage 5 – Automated execution">
            <div className="text-sm text-gray-500 mb-1">⚡ Execution</div>
            <div className="text-2xl font-bold text-indigo-600">{metrics.stages.execution.running}</div>
            <div className="text-sm text-gray-600">Running</div>
            <div className="text-xs text-gray-500">{metrics.stages.execution.complete} Complete</div>
          </div>
        </div>
      </div>
    </div>
  );
}
