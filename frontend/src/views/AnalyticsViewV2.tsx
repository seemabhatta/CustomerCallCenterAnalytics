import { useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  ChevronsRight,
  CircleDot,
  Download,
  LineChart,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Target,
  Users,
} from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { forecastApi, planApi, workflowApi } from "@/api/client";
import {
  ForecastReadiness,
  ForecastReadinessOverview,
  ForecastReadinessResponse,
  ForecastResult,
  ForecastStatistics,
  ForecastTypeSummary,
  Plan,
  Workflow,
} from "@/types";

const ROLE_LABELS: Record<string, string> = {
  BORROWER: "Borrower",
  ADVISOR: "Advisor",
  SUPERVISOR: "Supervisor",
  LEADERSHIP: "Leadership",
};

const ROLE_ACCENT: Record<string, string> = {
  BORROWER: "text-indigo-500",
  ADVISOR: "text-emerald-500",
  SUPERVISOR: "text-amber-600",
  LEADERSHIP: "text-rose-500",
};

const STATUS_TONE: Record<string, "info" | "warn" | "success"> = {
  AUTO_APPROVED: "success",
  EXECUTED: "success",
  AWAITING_APPROVAL: "warn",
  PENDING_ASSESSMENT: "info",
  REJECTED: "warn",
};

const formatNumber = (value: number | null | undefined, opts: Intl.NumberFormatOptions = {}) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "–";
  }
  return new Intl.NumberFormat("en-US", opts).format(value);
};

const formatPercent = (value: number | null | undefined) => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return "–";
  }
  return `${value.toFixed(1)}%`;
};

const timeLabel = (iso?: string | null) => {
  if (!iso) return "--:--";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "--:--";
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
};

const dateLabel = (iso?: string | null) => {
  if (!iso) return "—";
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString();
};

const readinessToProgress = (record: ForecastReadiness) => {
  const ratio = record.days_of_data / Math.max(record.min_required, 1);
  return Math.max(0, Math.min(1, ratio));
};

type RoleInsight = {
  key: string;
  headline: string;
  pending: number;
  completed: number;
  highlights: string[];
};

type PlaybookCard = {
  id: string;
  title: string;
  persona: string;
  summary: string;
  actions: string[];
  autoExecutable: number;
};

type LiveSignal = {
  id: string;
  timestamp: string;
  persona: string;
  summary: string;
  tone: "info" | "warn" | "success";
};

type ExecutiveBriefing = {
  forecastHeadline: string;
  riskCallouts: string[];
  automationWins: string[];
  coachingNotes: string[];
};

const deriveReadinessMap = (payload?: ForecastReadinessResponse) => {
  if (!payload) return {} as Record<string, ForecastReadiness>;
  if ((payload as ForecastReadinessOverview).by_type) {
    return (payload as ForecastReadinessOverview).by_type;
  }
  const single = payload as ForecastReadiness;
  return { [single.forecast_type]: single };
};

const deriveRoleInsights = (plans?: Plan[], workflows?: Workflow[]): RoleInsight[] => {
  const latestPlan = plans?.[0];
  const map = new Map<string, RoleInsight>();

  Object.keys(ROLE_LABELS).forEach((roleKey) => {
    const roleWorkflows = (workflows || []).filter((wf) => wf.workflow_type === roleKey);
    const pending = roleWorkflows.filter((wf) => wf.status !== "EXECUTED").length;
    const completed = roleWorkflows.filter((wf) => wf.status === "EXECUTED").length;

    const highlights: string[] = [];
    if (latestPlan) {
      if (roleKey === "BORROWER") {
        highlights.push(
          latestPlan.borrower_plan?.immediate_actions?.[0]?.action ?? "Review borrower plan"
        );
        if (latestPlan.borrower_plan?.risk_mitigation?.length) {
          highlights.push(latestPlan.borrower_plan.risk_mitigation[0]);
        }
      }
      if (roleKey === "ADVISOR") {
        highlights.push(
          latestPlan.advisor_plan?.coaching_items?.[0]?.action ?? "Review advisor coaching"
        );
        if (latestPlan.advisor_plan?.next_actions?.length) {
          highlights.push(latestPlan.advisor_plan.next_actions[0]);
        }
      }
      if (roleKey === "SUPERVISOR") {
        highlights.push(
          latestPlan.supervisor_plan?.escalation_items?.[0]?.item ?? "Review escalations"
        );
        if (latestPlan.supervisor_plan?.compliance_review?.length) {
          highlights.push(latestPlan.supervisor_plan.compliance_review[0]);
        }
      }
      if (roleKey === "LEADERSHIP") {
        highlights.push(
          latestPlan.leadership_plan?.strategic_opportunities?.[0] ?? "Review leadership outlook"
        );
        if (latestPlan.leadership_plan?.risk_indicators?.length) {
          highlights.push(latestPlan.leadership_plan.risk_indicators[0]);
        }
      }
    }

    map.set(roleKey, {
      key: roleKey,
      headline: `${ROLE_LABELS[roleKey]} spotlight`,
      pending,
      completed,
      highlights: highlights.filter(Boolean).slice(0, 2),
    });
  });

  return Array.from(map.values());
};

const derivePlaybooks = (plans?: Plan[]): PlaybookCard[] => {
  if (!plans) return [];
  return plans.slice(0, 6).map((plan) => {
    const firstBorrowerAction = plan.borrower_plan?.immediate_actions?.[0]?.action;
    const firstAdvisorAction = plan.advisor_plan?.coaching_items?.[0]?.action;
    const firstSupervisorItem = plan.supervisor_plan?.escalation_items?.[0]?.item;
    const firstLeadershipItem = plan.leadership_plan?.strategic_opportunities?.[0];

    const persona = plan.risk_level ? plan.risk_level.toLowerCase() : "balanced";
    const summary = firstBorrowerAction
      || firstAdvisorAction
      || firstSupervisorItem
      || firstLeadershipItem
      || "Review multi-layer playbook";

    const actions: string[] = [];
    if (plan.borrower_plan?.immediate_actions?.length) {
      actions.push(plan.borrower_plan.immediate_actions[0].action);
    }
    if (plan.advisor_plan?.next_actions?.length) {
      actions.push(plan.advisor_plan.next_actions[0]);
    }
    if (plan.supervisor_plan?.process_improvements?.length) {
      actions.push(plan.supervisor_plan.process_improvements[0]);
    }
    if (plan.leadership_plan?.strategic_opportunities?.length) {
      actions.push(plan.leadership_plan.strategic_opportunities[0]);
    }

    return {
      id: plan.plan_id,
      title: `Plan ${plan.plan_id.slice(-6)}`,
      persona,
      summary,
      actions: actions.filter(Boolean).slice(0, 3),
      autoExecutable: plan.auto_executable,
    };
  });
};

const deriveSignals = (workflows?: Workflow[]): LiveSignal[] => {
  if (!workflows) return [];
  return workflows
    .slice()
    .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 8)
    .map((wf) => {
      const tone = STATUS_TONE[wf.status] ?? "info";
      const summary = wf.workflow_data?.actions?.[0] || "Workflow update";
      return {
        id: wf.id,
        timestamp: timeLabel(wf.updated_at || wf.created_at),
        persona: ROLE_LABELS[wf.workflow_type] ?? wf.workflow_type,
        summary,
        tone,
      };
    });
};

const deriveBriefing = (
  forecast?: ForecastResult,
  statistics?: ForecastStatistics,
  plans?: Plan[]
): ExecutiveBriefing => {
  const riskCallouts: string[] = [];
  const automationWins: string[] = [];
  const coachingNotes: string[] = [];

  if (forecast?.summary) {
    riskCallouts.push(
      `Forecast horizon spans ${forecast.summary.total_periods} periods (${dateLabel(
        forecast.summary.prediction_start
      )} – ${dateLabel(forecast.summary.prediction_end)}).`
    );
    riskCallouts.push(
      `Average predicted volume ${formatNumber(forecast.summary.average_predicted, {
        maximumFractionDigits: 0,
      })}.`
    );
  }

  if (statistics?.most_accessed?.length) {
    const top = statistics.most_accessed[0];
    automationWins.push(`Top referenced forecast: ${top.forecast_type} (${top.access_count} views).`);
  }

  if (plans?.length) {
    const plan = plans[0];
    const advisorCoaching = plan.advisor_plan?.coaching_items?.[0]?.coaching_point;
    if (advisorCoaching) {
      coachingNotes.push(`Advisor focus: ${advisorCoaching}`);
    }
    const leadershipItem = plan.leadership_plan?.risk_indicators?.[0];
    if (leadershipItem) {
      riskCallouts.push(`Leadership indicator: ${leadershipItem}`);
    }
  }

  return {
    forecastHeadline: forecast
      ? `${forecast.forecast_type.replace(/_/g, " ")} outlook`
      : "Forecast summary",
    riskCallouts: riskCallouts.slice(0, 3),
    automationWins: automationWins.slice(0, 3),
    coachingNotes: coachingNotes.slice(0, 3),
  };
};

export function AnalyticsViewV2() {
  const queryClient = useQueryClient();
  const [selectedType, setSelectedType] = useState<string | null>(null);

  const {
    data: forecastTypes,
    isLoading: typesLoading,
    isError: typesError,
  } = useQuery({
    queryKey: ["forecast-types"],
    queryFn: forecastApi.getAvailableTypes,
  });

  useEffect(() => {
    if (forecastTypes && forecastTypes.length && !selectedType) {
      setSelectedType(forecastTypes[0].type);
    }
  }, [forecastTypes, selectedType]);

  const {
    data: forecast,
    isLoading: forecastLoading,
    isFetching: forecastRefreshing,
  } = useQuery({
    queryKey: ["forecast", selectedType],
    queryFn: () =>
      forecastApi.generate({
        forecast_type: selectedType!,
        use_cache: true,
      }),
    enabled: Boolean(selectedType),
    staleTime: 1000 * 60,
  });

  const { data: readiness } = useQuery({
    queryKey: ["forecast-readiness"],
    queryFn: () => forecastApi.getReadiness(),
    staleTime: 1000 * 60 * 5,
  });

  const { data: statistics } = useQuery({
    queryKey: ["forecast-statistics"],
    queryFn: forecastApi.getStatistics,
    staleTime: 1000 * 60 * 5,
  });

  const { data: dataSummary } = useQuery({
    queryKey: ["forecast-data-summary"],
    queryFn: forecastApi.getDataSummary,
    staleTime: 1000 * 60 * 5,
  });

  const { data: plans } = useQuery({
    queryKey: ["plans", "latest"],
    queryFn: () => planApi.list({ limit: 6 }),
    staleTime: 1000 * 60,
  });

  const { data: workflows } = useQuery({
    queryKey: ["workflows", "latest"],
    queryFn: () => workflowApi.list({ limit: 20 }),
    staleTime: 1000 * 30,
  });

  const readinessMap = useMemo(() => deriveReadinessMap(readiness), [readiness]);
  const roleInsights = useMemo(
    () => deriveRoleInsights(plans, workflows),
    [plans, workflows]
  );
  const playbooks = useMemo(() => derivePlaybooks(plans), [plans]);
  const signals = useMemo(() => deriveSignals(workflows), [workflows]);
  const briefing = useMemo(
    () => deriveBriefing(forecast, statistics, plans),
    [forecast, statistics, plans]
  );

  const handleRefreshForecast = () => {
    if (!selectedType) return;
    queryClient.invalidateQueries({ queryKey: ["forecast", selectedType] });
  };

  if (typesLoading && !forecastTypes) {
    return (
      <div className="space-y-4 bg-slate-50 p-6 text-sm">
        <p className="text-slate-500">Loading analytics intelligence…</p>
      </div>
    );
  }

  if (typesError) {
    return (
      <div className="space-y-4 bg-slate-50 p-6 text-sm">
        <p className="text-rose-600">Unable to load forecast configuration.</p>
      </div>
    );
  }

  const selectedForecastType: ForecastTypeSummary | undefined = forecastTypes?.find(
    (item) => item.type === selectedType
  );

  return (
    <div className="space-y-6 bg-slate-50 p-6 text-sm">
      <header className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Analytics Command Center</h1>
          <p className="text-xs text-slate-500">
            Unified predictive outlooks and prescriptive playbooks aligned with borrower, advisor, supervisor, and leadership flows.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Select value={selectedType ?? undefined} onValueChange={setSelectedType}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Select forecast" />
            </SelectTrigger>
            <SelectContent>
              {forecastTypes?.map((type) => (
                <SelectItem key={type.type} value={type.type}>
                  {type.type.replace(/_/g, " ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button
            variant="secondary"
            size="sm"
            className="inline-flex items-center gap-2"
            onClick={handleRefreshForecast}
            disabled={!selectedType || forecastLoading}
          >
            <RefreshCw className={`h-4 w-4 ${forecastRefreshing ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        </div>
      </header>

      <section className="space-y-4">
        <SectionHeader
          title="Forecast Intelligence"
          description="Live output from the forecasting engine"
          paths={["/api/v1/forecasts/types/available", "/api/v1/forecasts/generate", "/api/v1/forecasts/*"]}
        />

        <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
          <Card className="border border-slate-200/80 shadow-sm">
            <CardHeader className="flex flex-col gap-2 border-b border-slate-100 pb-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <LineChart className="h-4 w-4 text-indigo-500" /> Forecast Outlook
                </div>
                <ApiBadgeGroup paths={["/api/v1/forecasts/generate", "/api/v1/forecasts/types/available"]} />
              </div>
              <CardTitle className="text-xl font-semibold text-slate-900">
                {selectedForecastType
                  ? selectedForecastType.description
                  : "Select a forecast"}
              </CardTitle>
              {forecast?.generated_at && (
                <p className="text-xs text-slate-500">
                  Generated {dateLabel(forecast.generated_at)} · Horizon {forecast?.summary?.total_periods ?? "—"} periods
                </p>
              )}
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              <div className="grid gap-3 sm:grid-cols-3">
                <ForecastMetric
                  label="Average"
                  value={formatNumber(forecast?.summary?.average_predicted, { maximumFractionDigits: 0 })}
                  helper="Across prediction window"
                />
                <ForecastMetric
                  label="Peak"
                  value={formatNumber(forecast?.summary?.max_predicted, { maximumFractionDigits: 0 })}
                  helper="Highest predicted value"
                />
                <ForecastMetric
                  label="Confidence band"
                  value={formatNumber(
                    forecast?.predictions?.[0]?.confidence_interval ?? null,
                    { maximumFractionDigits: 0 }
                  )}
                  helper="First-period interval width"
                />
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <span>Prediction horizon</span>
                  <span>
                    {dateLabel(forecast?.summary?.prediction_start)} – {dateLabel(forecast?.summary?.prediction_end)}
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-slate-100">
                  <div
                    className="h-2 rounded-full bg-indigo-500 transition-all"
                    style={{
                      width: `${Math.min(100, ((forecast?.summary?.average_predicted ?? 0) /
                        Math.max(forecast?.summary?.max_predicted ?? 1, 1)) * 100)}%`,
                    }}
                  />
                </div>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {forecast?.predictions?.slice(0, 4).map((item) => (
                  <div key={item.date} className="rounded-xl border border-slate-100 p-3 text-xs">
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>{dateLabel(item.date)}</span>
                      <Badge variant="outline" className="uppercase">
                        {ROLE_LABELS[selectedForecastType?.type?.includes("advisor") ? "ADVISOR" : "BORROWER"] ?? "Focus"}
                      </Badge>
                    </div>
                    <div className="mt-2 flex items-baseline gap-2 text-slate-800">
                      <span className="text-lg font-semibold">
                        {formatNumber(item.predicted, { maximumFractionDigits: 0 })}
                      </span>
                      <span className="text-[11px] text-slate-500">
                        ({formatNumber(item.lower_bound, { maximumFractionDigits: 0 })} – {formatNumber(item.upper_bound, { maximumFractionDigits: 0 })})
                      </span>
                    </div>
                  </div>
                ))}
                {!forecast?.predictions?.length && (
                  <div className="rounded-xl border border-dashed border-slate-200 p-4 text-xs text-slate-500">
                    Forecast predictions will appear after data is available.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          <Card className="border border-slate-200/80 shadow-sm">
            <CardHeader className="border-b border-slate-100 pb-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <ShieldCheck className="h-4 w-4 text-emerald-500" /> Data Readiness
                </div>
                <ApiBadgeGroup paths={["/api/v1/forecasts/data/readiness"]} />
              </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-4 text-xs text-slate-600">
              {Object.entries(readinessMap).map(([type, record]) => (
                <div key={type} className="space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-semibold text-slate-700">{type.replace(/_/g, " ")}</span>
                    <Badge variant={record.ready ? "secondary" : "outline"} className="text-[10px] uppercase">
                      {record.ready ? "Ready" : "Collecting"}
                    </Badge>
                  </div>
                  <div className="h-2 w-full rounded-full bg-slate-100">
                    <div
                      className={`h-2 rounded-full ${record.ready ? "bg-emerald-500" : "bg-amber-500"}`}
                      style={{ width: `${Math.round(readinessToProgress(record) * 100)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <span>{record.days_of_data} / {record.min_required} days</span>
                    <span>{record.recommendation}</span>
                  </div>
                </div>
              ))}
              {!Object.keys(readinessMap).length && (
                <p className="text-slate-500">Forecast readiness information will appear once telemetry is available.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <Card className="border border-slate-200/80 shadow-sm">
          <CardHeader className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-4">
            <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
              <BarChart3 className="h-4 w-4 text-indigo-500" /> Forecast Operations Summary
            </div>
            <ApiBadgeGroup paths={["/api/v1/forecasts/data/summary", "/api/v1/forecasts/statistics"]} />
          </CardHeader>
          <CardContent className="space-y-3 pt-4 text-xs text-slate-600">
            <div className="grid gap-3 sm:grid-cols-2">
              <SummaryTile label="Transcripts" value={formatNumber(dataSummary?.transcripts?.total ?? null)} helper={`${dataSummary?.transcripts?.unique_days ?? "–"} days of history`} />
              <SummaryTile label="Analyses" value={formatNumber(dataSummary?.analyses?.total ?? null)} helper={`${formatPercent(dataSummary?.analyses?.avg_delinquency_risk ?? null)} delinquency risk`} />
              <SummaryTile label="Unique intents" value={formatNumber(dataSummary?.analyses?.unique_intents ?? null)} helper="Coverage for forecasting" />
              <SummaryTile label="Active forecasts" value={formatNumber(statistics?.total_forecasts ?? null)} helper={`${Object.keys(statistics?.active_by_type ?? {}).length} types cached`} />
            </div>
            <div>
              <div className="mb-2 text-[11px] font-semibold uppercase text-slate-500">Top intents</div>
              <div className="space-y-1">
                {Object.entries(dataSummary?.top_intents ?? {}).slice(0, 5).map(([intent, count]) => (
                  <div key={intent} className="flex items-center justify-between text-slate-600">
                    <span>{intent}</span>
                    <span>{count}</span>
                  </div>
                ))}
                {!Object.keys(dataSummary?.top_intents ?? {}).length && (
                  <p className="text-slate-500">Intent distribution will appear as analyses are generated.</p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="space-y-4">
        <SectionHeader
          title="Workflow & Playbooks"
          description="Execution context from action plans and workflow orchestration"
          paths={["/api/v1/plans", "/api/v1/workflows"]}
        />

        <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
          <Card className="border border-slate-200/80 shadow-sm">
            <CardHeader className="border-b border-slate-100 pb-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <Target className="h-4 w-4 text-emerald-500" /> Role Execution Snapshot
                </div>
                <ApiBadgeGroup paths={["/api/v1/plans", "/api/v1/workflows"]} />
              </div>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              {roleInsights.map((insight) => (
                <div key={insight.key} className="rounded-xl border border-slate-100 p-3 text-xs">
                  <div className="flex items-center justify-between">
                    <span className={`text-sm font-semibold ${ROLE_ACCENT[insight.key] ?? "text-slate-600"}`}>
                      {ROLE_LABELS[insight.key]}
                    </span>
                    <div className="flex items-center gap-2 text-[11px] text-slate-500">
                      <span>Pending {insight.pending}</span>
                      <span>•</span>
                      <span>Done {insight.completed}</span>
                    </div>
                  </div>
                  <ul className="mt-2 space-y-1 text-slate-600">
                    {insight.highlights.map((note, index) => (
                      <li key={`${insight.key}-${index}`} className="flex items-center gap-2">
                        <CircleDot className="h-3 w-3 text-slate-300" /> {note}
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border border-slate-200/80 shadow-sm">
            <CardHeader className="border-b border-slate-100 pb-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                  <Activity className="h-4 w-4 text-amber-500" /> Live Signals
                </div>
                <ApiBadgeGroup paths={["/api/v1/workflows"]} />
              </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-4 text-xs text-slate-600">
              {signals.map((signal) => (
                <div key={signal.id} className="flex items-start gap-3">
                  <span className="w-12 text-slate-400">{signal.timestamp}</span>
                  {signal.tone === "warn" ? (
                    <AlertTriangle className="mt-0.5 h-3.5 w-3.5 text-amber-600" />
                  ) : signal.tone === "success" ? (
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-500" />
                  ) : (
                    <CircleDot className="mt-0.5 h-3.5 w-3.5 text-slate-300" />
                  )}
                  <div>
                    <div className="font-semibold text-slate-700">{signal.persona}</div>
                    <p className="text-slate-600">{signal.summary}</p>
                  </div>
                </div>
              ))}
              {!signals.length && (
                <p className="text-slate-500">Workflow activity will stream in once orchestrations run.</p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.4fr_1fr]">
          <Card className="border border-slate-200/80 shadow-sm">
            <CardHeader className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <PlayCircle className="h-4 w-4 text-blue-500" /> Prescriptive Playbooks
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <ApiBadgeGroup paths={["/api/v1/plans"]} />
                <Badge variant="secondary" className="text-[11px]">
                  {playbooks.length} active
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="grid gap-4 pt-4 md:grid-cols-2">
              {playbooks.map((card) => (
                <div key={card.id} className="rounded-2xl border border-slate-100 p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                        <Sparkles className="h-4 w-4 text-indigo-500" /> {card.title}
                      </div>
                      <p className="mt-1 text-xs text-slate-500">{card.summary}</p>
                    </div>
                    <Badge variant="outline" className="capitalize text-[11px]">
                      {card.persona}
                    </Badge>
                  </div>
                  <ul className="mt-3 space-y-1 text-xs text-slate-600">
                    {card.actions.map((action) => (
                      <li key={action} className="flex items-center gap-2">
                        <ArrowRight className="h-3 w-3 text-slate-300" /> {action}
                      </li>
                    ))}
                  </ul>
                  <div className="mt-4 flex items-center justify-between text-[11px] text-slate-500">
                    <span>Auto-ready: {card.autoExecutable}</span>
                    <Button variant="link" size="sm" className="px-0 text-xs">
                      Launch <ChevronsRight className="ml-1 h-3 w-3" />
                    </Button>
                  </div>
                </div>
              ))}
              {!playbooks.length && (
                <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-xs text-slate-500">
                  Playbook recommendations will populate once plans are generated.
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border border-slate-200/80 shadow-sm">
            <CardHeader className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
                <Users className="h-4 w-4 text-rose-500" /> Executive Briefing
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <ApiBadgeGroup paths={["/api/v1/forecasts/generate", "/api/v1/forecasts/statistics", "/api/v1/plans"]} />
                <Button variant="secondary" size="sm" className="inline-flex items-center gap-2 text-xs">
                  <Download className="h-3.5 w-3.5" /> Download PDF
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3 pt-4 text-xs text-slate-600">
              <div>
                <div className="text-sm font-semibold text-slate-800">{briefing.forecastHeadline}</div>
                <ul className="mt-2 space-y-1">
                  {briefing.riskCallouts.map((item, idx) => (
                    <li key={`risk-${idx}`} className="flex items-start gap-2">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 text-amber-600" /> {item}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-800">Automation & enablement</div>
                <ul className="mt-2 space-y-1">
                  {briefing.automationWins.map((item, idx) => (
                    <li key={`auto-${idx}`} className="flex items-start gap-2">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-500" /> {item}
                    </li>
                  ))}
                  {!briefing.automationWins.length && (
                    <li className="text-slate-500">Run auto workflows to capture automation metrics.</li>
                  )}
                </ul>
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-800">Coaching priorities</div>
                <ul className="mt-2 space-y-1">
                  {briefing.coachingNotes.map((item, idx) => (
                    <li key={`coach-${idx}`} className="flex items-start gap-2">
                      <Target className="mt-0.5 h-3.5 w-3.5 text-indigo-500" /> {item}
                    </li>
                  ))}
                  {!briefing.coachingNotes.length && (
                    <li className="text-slate-500">Advisor coaching insights will flow once plans are generated.</li>
                  )}
                </ul>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
}

function ForecastMetric({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white/60 p-4 text-xs">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-xl font-semibold text-slate-900">{value}</div>
      <p className="mt-1 text-[11px] text-slate-500">{helper}</p>
    </div>
  );
}

function SummaryTile({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper: string;
}) {
  return (
    <div className="rounded-xl border border-slate-100 bg-white/80 p-4 text-xs">
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-2 text-lg font-semibold text-slate-900">{value}</div>
      <p className="mt-1 text-[11px] text-slate-500">{helper}</p>
    </div>
  );
}

function ApiBadge({ path }: { path: string }) {
  return (
    <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-tight text-slate-600">
      {path}
    </Badge>
  );
}

function ApiBadgeGroup({ paths }: { paths?: string[] }) {
  if (!paths || !paths.length) {
    return null;
  }
  return (
    <div className="flex flex-wrap items-center gap-1">
      {paths.map((path) => (
        <ApiBadge key={path} path={path} />
      ))}
    </div>
  );
}

function SectionHeader({
  title,
  description,
  paths,
}: {
  title: string;
  description: string;
  paths: string[];
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 className="text-sm font-semibold text-slate-900">{title}</h2>
        <p className="text-xs text-slate-500">{description}</p>
      </div>
      <ApiBadgeGroup paths={paths} />
    </div>
  );
}

export default AnalyticsViewV2;
