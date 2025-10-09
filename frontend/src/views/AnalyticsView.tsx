import { useMemo, useState } from "react";
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  ClipboardList,
  Gauge,
  Layers,
  Network,
  ShieldCheck,
  Sparkles,
  Target,
  Zap,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Mode = "predictive" | "prescriptive";

type Metric = {
  title: string;
  value: string;
  delta: string;
  direction: "up" | "down";
  detail: string;
};

type RolePanel = {
  role: string;
  items: Array<{ label: string; status: string }>;
};

type Campaign = {
  name: string;
  summary: string;
  upliftLabel: string;
  upliftValue: string;
  audience: string;
  bullets: string[];
};

type LiveEvent = {
  time: string;
  tone: "warn" | "success" | "info";
  message: string;
};

type ModelHealthSignal = {
  label: string;
  status: string;
  detail: string;
};

const METRICS: Record<Mode, Metric[]> = {
  predictive: [
    { title: "Delinquency Risk", value: "12%", delta: "+3%", direction: "up", detail: "High-risk borrower share" },
    { title: "Churn Probability", value: "8.7%", delta: "+0.6%", direction: "up", detail: "Predicted attrition likelihood" },
    { title: "Refi Opportunity", value: "$45M", delta: "+$4.3M", direction: "up", detail: "Conversion potential" },
    { title: "Compliance Deviation", value: "2.1%", delta: "+0.3%", direction: "up", detail: "Flagged calls" },
  ],
  prescriptive: [
    { title: "Automation Savings", value: "$128K", delta: "+$18K", direction: "up", detail: "Monthly run-rate" },
    { title: "Manual Reviews Avoided", value: "312", delta: "-26", direction: "down", detail: "Advisor hours reclaimed" },
    { title: "Playbooks Running", value: "9", delta: "+2", direction: "up", detail: "Active campaigns" },
    { title: "Compliance Lift", value: "0.9pp", delta: "+0.2pp", direction: "up", detail: "Deviation reduction" },
  ],
};

const ROLE_PANELS: RolePanel[] = [
  {
    role: "Borrower",
    items: [
      { label: "Submit income docs", status: "Pending" },
      { label: "Complete hardship affidavit", status: "In Progress" },
    ],
  },
  {
    role: "Advisor",
    items: [
      { label: "Analyze refinance qualification", status: "Pending" },
      { label: "Evaluate forbearance vs modification", status: "Pending" },
    ],
  },
  {
    role: "Supervisor",
    items: [
      { label: "Approve DTI exception", status: "Pending" },
      { label: "Review pricing authorization", status: "Completed" },
    ],
  },
  {
    role: "Leadership",
    items: [
      { label: "Monitor churn trends", status: "Active" },
      { label: "Deploy hardship outreach playbook", status: "Planned" },
    ],
  },
];

const PIPELINE_FORECAST = [
  { label: "Week 1", value: 2200 },
  { label: "Week 2", value: 1840 },
  { label: "Week 3", value: 2050 },
  { label: "Week 4", value: 2310 },
  { label: "Week 5", value: 2470 },
];

const CAMPAIGNS: Campaign[] = [
  {
    name: "Hardship Outreach Campaign",
    summary: "Target borrowers with elevated delinquency risk to preempt roll rates.",
    upliftLabel: "retention",
    upliftValue: "+12%",
    audience: "320 borrowers (High risk)",
    bullets: ["Send hardship affidavit", "Schedule advisor callback", "Offer payment plan"],
  },
  {
    name: "Refinance Promotion",
    summary: "Engage refi-eligible borrowers with personalized offers and compliant scripts.",
    upliftLabel: "revenue",
    upliftValue: "+$4.2M",
    audience: "150 borrowers (>70% likelihood)",
    bullets: ["Generate offer package", "One-click disclosures", "Follow-up cadence"],
  },
  {
    name: "Compliance Coaching",
    summary: "Reduce deviation probability with targeted live nudges and post-call QA.",
    upliftLabel: "deviation",
    upliftValue: "-0.9pp",
    audience: "Advisors with >3 flagged calls/week",
    bullets: ["Automated disclosure reminders", "Real-time scripting hints", "QA shadow sessions"],
  },
];

const LIVE_EVENTS: LiveEvent[] = [
  { time: "10:42", tone: "warn", message: "High churn probability detected for CALL_7420" },
  { time: "10:18", tone: "success", message: "AI approved auto workflow > PMI checklist" },
  { time: "09:58", tone: "info", message: "Sentiment recovery trending upward in hardship calls" },
  { time: "09:21", tone: "warn", message: "Compliance anomaly flagged: Reg Z timing" },
];

const MODEL_HEALTH: ModelHealthSignal[] = [
  { label: "Sentiment classifier", status: "Stable", detail: "Confidence 0.86, drift 0.06" },
  { label: "Risk predictor", status: "Watching", detail: "Confidence 0.79, drift 0.11" },
  { label: "Compliance detector", status: "Action", detail: "Refresh training data (aging 120 days)" },
];

const DELTA_COLOR: Record<Metric["direction"], string> = {
  up: "text-emerald-500",
  down: "text-rose-500",
};

function MetricCard({ metric }: { metric: Metric }) {
  return (
    <Card className="rounded-2xl border border-slate-200 bg-white/95">
      <CardHeader className="pb-1">
        <CardTitle className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          {metric.title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex items-baseline gap-2">
          <div className="text-2xl metric-value text-slate-900">{metric.value}</div>
          <div className={`text-xs font-semibold ${DELTA_COLOR[metric.direction]}`}>
            {metric.direction === "up" ? "^" : "v"} {metric.delta}
          </div>
        </div>
        <p className="mt-2 text-[11px] text-slate-500">{metric.detail}</p>
      </CardContent>
    </Card>
  );
}

function RolePanel({ panel }: { panel: RolePanel }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-sm font-semibold text-slate-700">{panel.role}</div>
      <div className="mt-3 space-y-2 text-xs text-slate-600">
        {panel.items.map((item) => (
          <div key={item.label} className="flex items-center justify-between">
            <span>{item.label}</span>
            <Badge variant="outline" className="text-[10px]">
              {item.status}
            </Badge>
          </div>
        ))}
      </div>
    </div>
  );
}

function CampaignCard({ campaign }: { campaign: Campaign }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2 text-base font-semibold text-slate-800">
            <Sparkles className="h-4 w-4 text-indigo-500" /> {campaign.name}
          </div>
          <p className="mt-1 text-xs text-slate-500">{campaign.summary}</p>
          <p className="mt-2 text-[11px] text-slate-400">Who: {campaign.audience}</p>
        </div>
        <Badge variant="secondary" className="text-[11px] capitalize">
          {campaign.upliftValue} {campaign.upliftLabel}
        </Badge>
      </div>
      <ul className="mt-3 list-disc space-y-1 pl-4 text-xs text-slate-600">
        {campaign.bullets.map((bullet) => (
          <li key={bullet}>{bullet}</li>
        ))}
      </ul>
      <div className="mt-4 flex flex-wrap gap-2 text-xs">
        <button className="inline-flex items-center gap-2 rounded-full bg-slate-900 px-3 py-1 font-semibold text-white shadow">
          <CheckCircle2 className="h-3.5 w-3.5" /> Approve & Deploy
        </button>
        <button className="inline-flex items-center gap-2 rounded-full border border-slate-200 px-3 py-1 font-semibold text-slate-600">
          <Zap className="h-3.5 w-3.5" /> Simulate Impact
        </button>
      </div>
    </div>
  );
}

function LiveEventCard({ event }: { event: LiveEvent }) {
  const toneIcon = event.tone === "warn" ? (
    <AlertTriangle className="mt-0.5 h-3.5 w-3.5 text-amber-600" />
  ) : event.tone === "success" ? (
    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-500" />
  ) : (
    <ClipboardList className="mt-0.5 h-3.5 w-3.5 text-slate-400" />
  );

  return (
    <div className="flex items-start gap-2 text-xs text-slate-600">
      <span className="w-12 text-slate-400">{event.time}</span>
      {toneIcon}
      <span>{event.message}</span>
    </div>
  );
}

function ModelHealthPanel({ signal }: { signal: ModelHealthSignal }) {
  const toneClass = signal.status === "Action" ? "text-rose-500" : signal.status === "Watching" ? "text-amber-600" : "text-emerald-600";
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3 shadow-sm">
      <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
        <ShieldCheck className="h-4 w-4 text-emerald-500" /> {signal.label}
      </div>
      <div className={`mt-2 text-xs font-semibold ${toneClass}`}>{signal.status}</div>
      <p className="mt-1 text-[11px] text-slate-500">{signal.detail}</p>
    </div>
  );
}

export function AnalyticsView() {
  const [mode, setMode] = useState<Mode>("predictive");
  const metrics = useMemo(() => METRICS[mode], [mode]);

  return (
    <div className="space-y-6 bg-gray-50 p-6 font-mono text-sm">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="view-header">Analytics</h1>
          <p className="text-xs text-slate-500">
            Predictive insights and prescriptive playbooks aligned with Borrower, Advisor, Supervisor, Leadership flows.
          </p>
        </div>
        <div className="inline-flex items-center rounded-full border border-slate-200 bg-white p-1 text-xs font-semibold text-slate-500 shadow-sm">
          <button
            type="button"
            onClick={() => setMode("predictive")}
            className={`rounded-full px-3 py-1 ${mode === "predictive" ? "bg-slate-900 text-white shadow" : ""}`}
          >
            Predictive
          </button>
          <button
            type="button"
            onClick={() => setMode("prescriptive")}
            className={`rounded-full px-3 py-1 ${mode === "prescriptive" ? "bg-slate-900 text-white shadow" : ""}`}
          >
            Prescriptive
          </button>
        </div>
      </header>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <MetricCard key={metric.title} metric={metric} />
        ))}
      </section>

      <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
        <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
          <Target className="h-4 w-4 text-indigo-500" /> Workflow Items by Role
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {ROLE_PANELS.map((panel) => (
            <RolePanel key={panel.role} panel={panel} />
          ))}
        </div>
      </section>

      <section className="grid gap-4 xl:grid-cols-3">
        <div className="xl:col-span-2 space-y-4">
          <Card className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Network className="h-4 w-4 text-blue-500" /> Pipeline Forecast
            </div>
            <div className="mt-4 space-y-2">
              {PIPELINE_FORECAST.map((bar) => (
                <div key={bar.label} className="space-y-1 text-xs text-slate-500">
                  <div className="flex items-center justify-between">
                    <span>{bar.label}</span>
                    <span>{bar.value}</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100">
                    <div
                      className="h-2 rounded-full bg-blue-500"
                      style={{ width: `${Math.min(100, (bar.value / 2470) * 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </Card>
          <Card className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <Activity className="h-4 w-4 text-emerald-500" /> Model Health Monitor
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              {MODEL_HEALTH.map((signal) => (
                <ModelHealthPanel key={signal.label} signal={signal} />
              ))}
            </div>
          </Card>
        </div>
        <div className="space-y-4">
          {CAMPAIGNS.map((campaign) => (
            <CampaignCard key={campaign.name} campaign={campaign} />
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <Card className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Layers className="h-4 w-4 text-slate-500" /> Live Analytics Feed
          </div>
          <div className="mt-4 space-y-3">
            {LIVE_EVENTS.map((event) => (
              <LiveEventCard key={`${event.time}-${event.message}`} event={event} />
            ))}
          </div>
        </Card>
        <Card className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <Gauge className="h-4 w-4 text-blue-500" /> AI Briefing Snapshot
          </div>
          <div className="mt-3 space-y-3 text-xs text-slate-600">
            <p>
              Daily digest generated from orchestration signals. Summarizes risk spikes, automation wins, compliance
              attention areas, and advisor coaching priorities for servicing leadership.
            </p>
            <div className="flex flex-wrap gap-2">
              <button className="rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white shadow">
                Download PDF Briefing
              </button>
              <button className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">
                Schedule Email
              </button>
              <button className="rounded-full border border-slate-200 px-3 py-1 text-xs font-semibold text-slate-600">
                Bookmark View
              </button>
            </div>
          </div>
        </Card>
      </section>
    </div>
  );
}

export default AnalyticsView;
