import React from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Legend, Tooltip as RTooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { 
  Rocket, 
  Settings2, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldCheck, 
  Activity, 
  LineChart 
} from "lucide-react";
import { systemApi } from "@/api/client";

interface KPIProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  sub?: string;
}

function KPI({ title, value, icon, sub }: KPIProps) {
  return (
    <Card className="rounded-2xl shadow-sm">
      <CardHeader className="pb-1 flex flex-row items-center justify-between">
        <CardTitle className="text-sm text-slate-500 flex items-center gap-2">
          {title} 
          {sub && <span className="text-[11px] text-slate-400">{sub}</span>}
        </CardTitle>
        {icon}
      </CardHeader>
      <CardContent className="text-2xl font-semibold">{value}</CardContent>
    </Card>
  );
}

function StageDurationChart({ data }: { data: Array<{ stage: string; seconds: number }> }) {
  return (
    <Card className="rounded-2xl">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Pipeline Stage Durations (s)</CardTitle>
      </CardHeader>
      <CardContent className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="stage" />
            <YAxis />
            <RTooltip />
            <Bar dataKey="seconds" fill="#3b82f6" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function RiskByPersonaChart({ data }: { data: Array<{ persona: string; HIGH: number; MEDIUM: number; LOW: number }> }) {
  return (
    <Card className="rounded-2xl">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Risk by Persona</CardTitle>
      </CardHeader>
      <CardContent className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="persona" />
            <YAxis allowDecimals={false} />
            <Legend />
            <RTooltip />
            <Bar dataKey="HIGH" stackId="a" fill="#ef4444" />
            <Bar dataKey="MEDIUM" stackId="a" fill="#f59e0b" />
            <Bar dataKey="LOW" stackId="a" fill="#10b981" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function LiveEvents({ items }: { items: Array<{ t: string; msg: string; type: string }> }) {
  return (
    <Card className="rounded-2xl">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Live Events</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {items.map((e, i) => (
          <div key={i} className="flex items-center gap-3 text-sm">
            <span className="w-14 text-slate-400">{e.t}</span>
            {e.type === "warn" ? (
              <AlertTriangle className="h-4 w-4 text-amber-600" />
            ) : e.type === "success" ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600" />
            ) : (
              <LineChart className="h-4 w-4 text-slate-400" />
            )}
            <span>{e.msg}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

// Mock data - this should be replaced with real API calls
const mockRun = {
  durations: [
    { stage: "analysis", seconds: 9.7 },
    { stage: "plan", seconds: 24.4 },
    { stage: "workflows", seconds: 110.4 },
    { stage: "approval", seconds: 0.0 },
    { stage: "execution", seconds: 0.0 },
  ],
  funnel: { generated: 10, approved: 0, executed: 0, failed: 0 },
};

const mockRiskByPersona = [
  { persona: "BORROWER", HIGH: 1, MEDIUM: 1, LOW: 0 },
  { persona: "ADVISOR", HIGH: 2, MEDIUM: 0, LOW: 0 },
  { persona: "SUPERVISOR", HIGH: 3, MEDIUM: 0, LOW: 0 },
  { persona: "LEADERSHIP", HIGH: 3, MEDIUM: 0, LOW: 0 },
];

const mockEvents = [
  { t: "16:41:34", msg: "analysis started", type: "info" },
  { t: "16:41:44", msg: "plan completed (id=PLAN_ANALYSIS_CALL_2)", type: "success" },
  { t: "16:42:26", msg: "risk assessed HIGH for BORROWER action", type: "warn" },
  { t: "16:43:58", msg: "workflows extracted (10) — queued for approval", type: "info" },
  { t: "16:43:58", msg: "pipeline complete — executed 0 (autoApprove=false)", type: "warn" },
];

export function Dashboard() {
  const { data: metrics, isLoading, error } = useQuery({
    queryKey: ['dashboard-metrics'],
    queryFn: systemApi.getMetrics,
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Card key={i} className="rounded-2xl shadow-sm animate-pulse">
              <CardContent className="h-20"></CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Card className="rounded-2xl">
        <CardContent className="p-6">
          <div className="text-red-600">
            Error loading dashboard metrics: {(error as any)?.detail || 'Unknown error'}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-6 gap-4">
        <KPI 
          title="Workflows Generated" 
          value={mockRun.funnel.generated} 
          icon={<Rocket className="h-4 w-4 text-indigo-500" />} 
        />
        <KPI 
          title="Approved" 
          value={mockRun.funnel.approved} 
          icon={<Settings2 className="h-4 w-4 text-slate-500" />} 
        />
        <KPI 
          title="Executed" 
          value={mockRun.funnel.executed} 
          icon={<CheckCircle2 className="h-4 w-4 text-emerald-600" />} 
        />
        <KPI 
          title="Failed" 
          value={mockRun.funnel.failed} 
          icon={<AlertTriangle className="h-4 w-4 text-amber-600" />} 
        />
        <KPI 
          title="Risk ≥ High" 
          value={mockRiskByPersona.reduce((a, b) => a + (b.HIGH || 0), 0)} 
          icon={<ShieldCheck className="h-4 w-4 text-rose-600" />} 
        />
        <KPI 
          title="SLA Hot" 
          value={2} 
          sub="(near due)" 
          icon={<Activity className="h-4 w-4 text-sky-600" />} 
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        <div className="xl:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          <StageDurationChart data={mockRun.durations} />
          <RiskByPersonaChart data={mockRiskByPersona} />
        </div>
        <div className="space-y-4">
          <LiveEvents items={mockEvents} />
        </div>
      </div>
    </div>
  );
}