import { useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  AlertTriangle,
  BarChart3,
  Briefcase,
  DollarSign,
  Download,
  CheckCircle2,
  LineChart,
  RefreshCw,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  Target,
  Users,
} from 'lucide-react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
} from '@dnd-kit/sortable';
import { forecastApi, planApi } from '@/api/client';
import { useLeadershipIntelligence } from '@/api/intelligenceHooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import IntelligenceStatusBar from '@/components/IntelligenceStatusBar';
import DraggableCard from '@/components/DraggableCard';
import { useRowLayout } from '@/hooks/useGridLayout';
import {
  combineErrors,
  combineLoadingStates,
  diffFromNow,
  formatCurrency,
  formatDateTime,
  formatNumber,
  formatPercent,
} from '@/utils/formatters';
import {
  LeadershipDecisionQueueItem,
  LeadershipFinancialSummary,
  LeadershipRecommendation,
  LeadershipRiskWaterfall,
  LeadershipUrgentItem,
  ForecastResult,
  ForecastStatistics,
  ForecastTypeSummary,
  ForecastDataSummary,
  Plan,
} from '@/types';

const HEALTH_TONE: Record<string, string> = {
  STABLE: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
  ATTENTION: 'bg-amber-100 text-amber-700 border border-amber-200',
  CRITICAL: 'bg-rose-100 text-rose-700 border border-rose-200',
};

const dateLabel = (iso?: string | null) => {
  if (!iso) return '—';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '—';
  return date.toLocaleDateString();
};

type ForecastExecutiveBriefing = {
  forecastHeadline: string;
  riskCallouts: string[];
  automationWins: string[];
  coachingNotes: string[];
};

const deriveForecastExecutiveBriefing = (
  forecast?: ForecastResult,
  statistics?: ForecastStatistics,
  plans?: Plan[],
): ForecastExecutiveBriefing => {
  const riskCallouts: string[] = [];
  const automationWins: string[] = [];
  const coachingNotes: string[] = [];

  if (forecast?.summary) {
    riskCallouts.push(
      `Forecast horizon spans ${forecast.summary.total_periods} periods (${dateLabel(
        forecast.summary.prediction_start,
      )} – ${dateLabel(forecast.summary.prediction_end)}).`,
    );
    riskCallouts.push(
      `Average predicted volume ${formatNumber(forecast.summary.average_predicted, {
        maximumFractionDigits: 0,
      })}.`,
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
      ? `${forecast.forecast_type.replace(/_/g, ' ')} outlook`
      : 'Forecast summary',
    riskCallouts: riskCallouts.slice(0, 3),
    automationWins: automationWins.slice(0, 3),
    coachingNotes: coachingNotes.slice(0, 3),
  };
};

const urgencyBadge = (urgency?: string) => {
  switch (urgency) {
    case 'high':
      return 'bg-rose-100 text-rose-700 border border-rose-200';
    case 'medium':
      return 'bg-amber-100 text-amber-700 border border-amber-200';
    case 'low':
      return 'bg-slate-100 text-slate-700 border border-slate-200';
    default:
      return 'bg-slate-100 text-slate-600 border border-slate-200';
  }
};

const DEFAULT_LAYOUT = [
  'briefing',
  'forecastOutlook',
  'pipelineInsights',
  'dollarImpact',
  'topIntents',
  'recommendations',
  'riskWaterfall',
  'decisionQueue',
];

const DEFAULT_ROW_MAP: Record<string, number> = {
  forecastOutlook: 0,
  dollarImpact: 0,
  riskWaterfall: 0,
  pipelineInsights: 1,
  topIntents: 1,
  briefing: 2,
  decisionQueue: 2,
  recommendations: 2,
};

const ControlTowerView = () => {
  const queryClient = useQueryClient();
  const intelligence = useLeadershipIntelligence();
  const { items, moveItem, resetLayout, getRows } = useRowLayout(
    'control-tower-rows',
    DEFAULT_LAYOUT,
    DEFAULT_ROW_MAP,
  );

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const { data: forecastTypes } = useQuery({
    queryKey: ['control-tower', 'forecast-types'],
    queryFn: forecastApi.getAvailableTypes,
    staleTime: 5 * 60 * 1000,
  });

  const selectedForecastType: ForecastTypeSummary | undefined = forecastTypes?.[0];

  const {
    data: forecast,
    isLoading: forecastLoading,
  } = useQuery({
    queryKey: ['control-tower', 'forecast', selectedForecastType?.type],
    queryFn: () =>
      forecastApi.generate({
        forecast_type: selectedForecastType!.type,
        use_cache: true,
      }),
    enabled: Boolean(selectedForecastType?.type),
    staleTime: 60 * 1000,
  });

  const { data: statistics, isLoading: statisticsLoading } = useQuery({
    queryKey: ['control-tower', 'forecast-statistics'],
    queryFn: forecastApi.getStatistics,
    staleTime: 5 * 60 * 1000,
  });

  const { data: plans, isLoading: plansLoading } = useQuery({
    queryKey: ['control-tower', 'plans', 'latest'],
    queryFn: () => planApi.list({ limit: 6 }),
    staleTime: 60 * 1000,
  });

  const { data: dataSummary, isLoading: summaryLoading } = useQuery<ForecastDataSummary>({
    queryKey: ['control-tower', 'forecast-data-summary'],
    queryFn: forecastApi.getDataSummary,
    staleTime: 5 * 60 * 1000,
  });

  const executiveBriefing = useMemo(
    () => deriveForecastExecutiveBriefing(forecast, statistics, plans),
    [forecast, statistics, plans],
  );

  const topIntents = useMemo(
    () =>
      Object.entries(dataSummary?.top_intents ?? {})
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6),
    [dataSummary],
  );

  const pipelineBriefingLoading = forecastLoading || statisticsLoading || plansLoading;
  const pipelineInsightsLoading = pipelineBriefingLoading;

  const isLoading = combineLoadingStates(
    intelligence.briefing.isLoading,
    intelligence.dollarImpact.isLoading,
    intelligence.decisionQueue.isLoading,
    intelligence.riskWaterfall.isLoading
  );

  const topIntentsLoading = summaryLoading;

  const dollarImpact = intelligence.dollarImpact.data;

  const summaryStats = useMemo(() => {
    const stats: SummaryStat[] = [];

    const forecastStamp = forecast?.generated_at;
    stats.push({
      label: 'Forecast refresh',
      value: forecastStamp ? diffFromNow(forecastStamp) || 'Just now' : 'Awaiting run',
      helper: selectedForecastType?.description ?? 'Select a forecast type',
    });

    if (dollarImpact) {
      const delta = dollarImpact.trend_delta_pct ?? null;
      const tone: SummaryStat['tone'] = delta === null ? 'neutral' : delta > 0 ? 'negative' : delta < 0 ? 'positive' : 'neutral';
      const deltaLabel =
        delta === null
          ? dollarImpact.trend ?? 'vs. prior run'
          : `${delta > 0 ? '+' : ''}${formatPercent(delta)} ${delta > 0 ? 'increase' : delta < 0 ? 'decrease' : 'flat'}`;
      stats.push({
        label: 'Portfolio at risk',
        value: formatCurrency(dollarImpact.total_at_risk),
        helper: deltaLabel,
        tone,
      });
    } else {
      stats.push({
        label: 'Portfolio at risk',
        value: '—',
        helper: 'Risk telemetry unavailable',
      });
    }

    const approvalsTotal = intelligence.decisionQueue.data?.count ?? null;
    const approvalsUrgent = intelligence.decisionQueue.data?.urgent_count ?? 0;
    stats.push({
      label: 'Approvals waiting',
      value: formatNumber(approvalsTotal),
      helper: approvalsUrgent ? `${formatNumber(approvalsUrgent)} urgent` : 'All standard priority',
      tone: approvalsUrgent ? 'negative' : 'neutral',
    });

    return stats;
  }, [forecast?.generated_at, selectedForecastType?.description, dollarImpact, intelligence.decisionQueue.data]);

  const handleRefreshForecast = () => {
    if (!selectedForecastType?.type) return;
    queryClient.invalidateQueries({
      queryKey: ['control-tower', 'forecast', selectedForecastType.type],
    });
  };

  const error = combineErrors(
    intelligence.briefing.error as Error | undefined,
    intelligence.dollarImpact.error as Error | undefined,
    intelligence.decisionQueue.error as Error | undefined,
    intelligence.riskWaterfall.error as Error | undefined
  );

  const portfolioHealthClass = useMemo(() => {
    const status = intelligence.briefing.data?.portfolio_health;
    if (!status) return 'bg-slate-100 text-slate-700 border border-slate-200';
    return HEALTH_TONE[status] ?? 'bg-slate-100 text-slate-700 border border-slate-200';
  }, [intelligence.briefing.data?.portfolio_health]);

  const urgentItems = (intelligence.briefing.data?.urgent_items ?? []) as LeadershipUrgentItem[];
  const recommendations = (intelligence.briefing.data?.recommendations ?? []) as LeadershipRecommendation[];
  const decisionQueue = (intelligence.decisionQueue.data?.decisions ?? []) as LeadershipDecisionQueueItem[];
  const financialSummary = intelligence.briefing.data?.financial_summary as LeadershipFinancialSummary | undefined;
  const riskWaterfall = intelligence.riskWaterfall.data as LeadershipRiskWaterfall | undefined;

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;

    if (over && active.id !== over.id) {
      moveItem(active.id as string, over.id as string);
    }
  };

  const cardComponents: Record<string, JSX.Element> = {
    briefing: (
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Users className="h-5 w-5 text-rose-500" />
            Executive Briefing
          </CardTitle>
          <p className="text-sm text-slate-500">
            Generated {diffFromNow(intelligence.briefing.data?._generated_at ?? intelligence.briefing.data?.generated_at)}
          </p>
        </div>
        <Badge className={`${portfolioHealthClass} px-3 py-1 text-xs uppercase font-medium`}>
          {intelligence.briefing.data?.portfolio_health ?? 'Loading'}
        </Badge>
      </CardHeader>
    ),
    forecastOutlook: (
      <>
        <CardHeader className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <LineChart className="h-4 w-4 text-indigo-500" /> Daily call volume forecast
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-tight text-slate-600">
              /api/v1/forecasts/generate
            </Badge>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={handleRefreshForecast}
              disabled={forecastLoading}
            >
              <RefreshCw className={`h-4 w-4 ${forecastLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4 text-xs text-slate-600">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <div className="text-sm font-semibold text-slate-800">
              {selectedForecastType?.description ?? 'Select a forecast'}
            </div>
            {forecast?.generated_at && (
              <span className="text-[11px] text-slate-500">
                Generated {dateLabel(forecast.generated_at)} · Horizon {forecast?.summary?.total_periods ?? '—'} periods
              </span>
            )}
          </div>

          <div className="grid gap-3 sm:grid-cols-3">
            <ForecastMetricCard
              label="Average"
              value={formatNumber(forecast?.summary?.average_predicted ?? null, { maximumFractionDigits: 0 })}
              helper="Across prediction window"
            />
            <ForecastMetricCard
              label="Peak"
              value={formatNumber(forecast?.summary?.max_predicted ?? null, { maximumFractionDigits: 0 })}
              helper="Highest interval"
            />
            <ForecastMetricCard
              label="Latest"
              value={formatNumber(forecast?.predictions?.at(-1)?.predicted ?? null, { maximumFractionDigits: 0 })}
              helper="Most recent day"
            />
          </div>

          <div className="space-y-2">
            {(forecast?.predictions ?? []).slice(0, 5).map((point) => (
              <div
                key={`${point.date}-${point.period}`}
                className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2"
              >
                <div>
                  <div className="text-sm font-semibold text-slate-800">
                    {point.period_label ?? dateLabel(point.date)}
                  </div>
                  {point.commentary && (
                    <p className="text-[11px] text-slate-500">{point.commentary}</p>
                  )}
                </div>
                <div className="text-right text-sm font-semibold text-slate-800">
                  {formatNumber(point.predicted, { maximumFractionDigits: 0 })}
                  <div className="text-[11px] text-slate-500">
                    ({formatNumber(point.lower_bound, { maximumFractionDigits: 0 })} – {formatNumber(point.upper_bound, { maximumFractionDigits: 0 })})
                  </div>
                </div>
              </div>
            ))}
            {!forecast?.predictions?.length && (
              <p className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-3 text-center text-[11px] text-slate-500">
                Forecast predictions will populate once telemetry is available.
              </p>
            )}
          </div>
        </CardContent>
      </>
    ),
    pipelineInsights: (
      <>
        <CardHeader className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <LineChart className="h-4 w-4 text-emerald-500" />
            Pipeline outlook & enablement
          </div>
          <Button variant="secondary" size="sm" className="inline-flex items-center gap-2 text-xs">
            <Download className="h-3.5 w-3.5" /> Download PDF
          </Button>
        </CardHeader>
        <CardContent className="space-y-4 text-xs text-slate-600">
          {pipelineInsightsLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, idx) => (
                <div
                  key={`pipeline-outlook-loading-${idx}`}
                  className="h-20 animate-pulse rounded-md border border-dashed border-slate-200 bg-slate-50"
                />
              ))}
            </div>
          ) : (
            <>
              <div>
                <div className="text-sm font-semibold text-slate-800">Call volume daily outlook</div>
                <ul className="mt-2 space-y-1">
                  {executiveBriefing.riskCallouts.length ? (
                    executiveBriefing.riskCallouts.map((item, idx) => (
                      <li key={`risk-${idx}`} className="flex items-start gap-2">
                        <AlertTriangle className="mt-0.5 h-3.5 w-3.5 text-amber-600" /> {item}
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500">Run a forecast to populate call volume trends.</li>
                  )}
                </ul>
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-800">Automation & enablement</div>
                <ul className="mt-2 space-y-1">
                  {executiveBriefing.automationWins.length ? (
                    executiveBriefing.automationWins.map((item, idx) => (
                      <li key={`auto-${idx}`} className="flex items-start gap-2">
                        <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 text-emerald-500" /> {item}
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500">Run auto workflows to capture automation metrics.</li>
                  )}
                </ul>
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-800">Coaching priorities</div>
                <ul className="mt-2 space-y-1">
                  {executiveBriefing.coachingNotes.length ? (
                    executiveBriefing.coachingNotes.map((item, idx) => (
                      <li key={`coach-${idx}`} className="flex items-start gap-2">
                        <Target className="mt-0.5 h-3.5 w-3.5 text-indigo-500" /> {item}
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-500">Advisor coaching insights will flow once plans are generated.</li>
                  )}
                </ul>
              </div>
            </>
          )}
        </CardContent>
      </>
    ),
    dollarImpact: (
      <>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <DollarSign className="h-5 w-5 text-emerald-500" />
            Dollar impact snapshot
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {dollarImpact ? (
            <>
              <div>
                <p className="text-sm text-slate-500">Total at risk</p>
                <p className="text-2xl font-semibold text-slate-900">
                  {formatCurrency(dollarImpact.total_at_risk)}
                </p>
              </div>
              <div className="space-y-3 text-sm">
                {Object.entries(dollarImpact.by_category || {}).map(([category, value]) => (
                  <div key={category} className="flex items-center justify-between">
                    <span className="capitalize text-slate-600">{category.replace('_', ' ')}</span>
                    <span className="font-medium">{formatCurrency(value)}</span>
                  </div>
                ))}
              </div>
              <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
                {formatNumber(dollarImpact.high_risk_customers)} high-risk customers across a
                {" "}
                {formatCurrency(dollarImpact.portfolio_value, { maximumFractionDigits: 0 })} portfolio.
              </div>
            </>
          ) : (
            <div className="h-40 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
          )}
        </CardContent>
      </>
    ),
    topIntents: (
      <>
        <CardHeader className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-700">
            <BarChart3 className="h-4 w-4 text-indigo-500" />
            Top intents
          </div>
          <Badge variant="outline" className="font-mono text-[10px] uppercase tracking-tight text-slate-600">
            /api/v1/forecasts/data/summary
          </Badge>
        </CardHeader>
        <CardContent className="space-y-2 text-xs text-slate-600">
          {topIntentsLoading ? (
            Array.from({ length: 5 }).map((_, idx) => (
              <div
                key={`intent-loading-${idx}`}
                className="h-8 animate-pulse rounded-md border border-dashed border-slate-200 bg-slate-50"
              />
            ))
          ) : topIntents.length ? (
            topIntents.map(([intent, count]) => (
              <div
                key={intent}
                className="flex items-center justify-between rounded-lg border border-slate-200 bg-white px-3 py-2"
              >
                <span className="font-medium text-slate-800">{intent}</span>
                <span className="text-slate-500">{count}</span>
              </div>
            ))
          ) : (
            <p className="text-slate-500">No intent distribution available. Generate analyses to populate this view.</p>
          )}
        </CardContent>
      </>
    ),
    decisionQueue: (
      <>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Briefcase className="h-5 w-5 text-slate-500" />
              Decision queue
            </CardTitle>
            <p className="text-sm text-slate-500">
              {formatNumber(intelligence.decisionQueue.data?.urgent_count)} urgent approvals pending.
            </p>
          </div>
          <Badge variant="outline" className="text-xs">
            {formatNumber(intelligence.decisionQueue.data?.count)} items
          </Badge>
        </CardHeader>
        <CardContent className="space-y-3">
          {decisionQueue.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
              No pending leadership actions right now.
            </div>
          ) : (
            <div className="space-y-3">
              {decisionQueue.map((decision: LeadershipDecisionQueueItem, index: number) => (
                <div
                  key={`${decision.id}-${index}`}
                  className="rounded-lg border border-slate-200 bg-white p-4"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-2 text-sm text-slate-500">
                      <Badge className={`${urgencyBadge(decision.urgency)} text-[10px] uppercase`}>
                        {decision.urgency}
                      </Badge>
                      <span className="font-medium text-slate-900">{decision.title || decision.type}</span>
                    </div>
                    <span className="text-xs text-slate-500">
                      Awaiting {diffFromNow(decision.waiting_since)}
                    </span>
                  </div>
                  {decision.recommendation && (
                    <p className="mt-2 text-sm text-slate-600">{decision.recommendation}</p>
                  )}
                  <div className="mt-3 grid gap-3 text-sm text-slate-600 sm:grid-cols-3">
                    <div className="rounded border border-slate-200 bg-slate-50 px-3 py-2">
                      <p className="text-xs uppercase tracking-wide text-slate-400">Type</p>
                      <p className="font-medium text-slate-700">{decision.workflow_type || decision.type}</p>
                    </div>
                    <div className="rounded border border-slate-200 bg-slate-50 px-3 py-2">
                      <p className="text-xs uppercase tracking-wide text-slate-400">Impact</p>
                      <p className="font-medium text-slate-700">
                        {formatCurrency(decision.expected_impact ?? 0)}
                      </p>
                    </div>
                    <div className="rounded border border-slate-200 bg-slate-50 px-3 py-2">
                      <p className="text-xs uppercase tracking-wide text-slate-400">ROI</p>
                      <p className="font-medium text-slate-700">
                        {decision.roi !== undefined ? formatPercent(decision.roi) : '—'}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </>
    ),
    riskWaterfall: (
      <>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <BarChart3 className="h-5 w-5 text-indigo-500" />
            Risk waterfall
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {riskWaterfall ? (
            <>
              <div className="space-y-2 text-sm text-slate-600">
                <div className="flex justify-between">
                  <span>Total portfolio</span>
                  <span className="font-medium">{formatCurrency(riskWaterfall.starting_portfolio)}</span>
                </div>
                <div className="flex justify-between text-rose-600">
                  <span>At risk</span>
                  <span className="font-semibold">{formatCurrency(riskWaterfall.at_risk)}</span>
                </div>
                <div className="flex justify-between text-emerald-600">
                  <span>Recoverable</span>
                  <span className="font-semibold">{formatCurrency(riskWaterfall.recoverable_with_action)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Net risk</span>
                  <span className="font-medium text-slate-900">{formatCurrency(riskWaterfall.net_risk)}</span>
                </div>
              </div>
              <div className="space-y-2">
                {riskWaterfall.stages?.map((stage, index) => (
                  <div key={`${stage.label}-${index}`} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between text-xs uppercase tracking-wide text-slate-500">
                      <span>{stage.label}</span>
                      <span>{formatCurrency(stage.value)}</span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-200">
                      <div
                        className="h-2 rounded-full bg-indigo-500"
                        style={{
                          width: `${Math.min(100, Math.abs(stage.value) / Math.max(riskWaterfall.starting_portfolio || 1, 1) * 100)}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              {financialSummary && (
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
                  Generated {formatDateTime(intelligence.briefing.data?.generated_at)} • Net impact {formatCurrency(financialSummary.net_impact)}
                </div>
              )}
            </>
          ) : (
            <div className="h-48 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
          )}
        </CardContent>
      </>
    ),
    recommendations: (
      <>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Sparkles className="h-5 w-5 text-purple-500" />
            Strategic recommendations
          </CardTitle>
          <Badge variant="secondary" className="text-xs text-slate-600">
            {recommendations.length} playbook items
          </Badge>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {recommendations.length === 0 && (
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
              Awaiting new recommendations. Check back after the next forecast cycle.
            </div>
          )}
          {recommendations.map((item: LeadershipRecommendation, index: number) => (
            <div key={`${item.action}-${index}`} className="rounded-lg border border-slate-200 bg-white p-4">
              <p className="font-semibold text-slate-900">{item.action}</p>
              <p className="mt-2 text-sm text-slate-600">{item.reasoning}</p>
              <div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">
                <Badge variant="outline" className="text-xs uppercase">
                  ROI {formatPercent(item.expected_roi)}
                </Badge>
                <Badge variant="outline" className="text-xs uppercase">
                  Timeline: {item.timeline}
                </Badge>
                <Badge variant="outline" className="text-xs uppercase">
                  Confidence: {item.confidence}
                </Badge>
              </div>
            </div>
          ))}
        </CardContent>
      </>
    ),
  };

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 flex items-center gap-2">
            <ShieldAlert className="h-6 w-6 text-emerald-600" />
            Executive Control Tower
          </h1>
          <p className="mt-1 text-sm text-slate-600 max-w-2xl">
            Daily command center for leadership. Combines Prophet forecasts and GenAI analysis to
            quantify dollars at risk, urgent decisions, and the ROI of proactive actions.
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={resetLayout}
            title="Reset card layout to default"
          >
            <RotateCcw className="h-4 w-4" />
            Reset layout
          </Button>
          <Button
            variant="outline"
            size="sm"
            className="gap-2"
            onClick={() => {
              intelligence.briefing.refetch();
              intelligence.dollarImpact.refetch();
              intelligence.decisionQueue.refetch();
              intelligence.riskWaterfall.refetch();
            }}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh intelligence
          </Button>
        </div>
      </div>

      <SummaryRibbon stats={summaryStats} />

      {error && (
        <Card className="border border-rose-200 bg-rose-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 text-rose-700">
              <AlertTriangle className="h-5 w-5" />
              <div>
                <p className="font-semibold">Unable to load leadership intelligence.</p>
                <p className="text-sm">{error.message}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <IntelligenceStatusBar persona="leadership" />

      <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={items.map(item => item.id)} strategy={rectSortingStrategy}>
          <div className="space-y-6">
            {getRows().map((rowItems, rowIndex) => (
              <div
                key={`row-${rowIndex}`}
                className="grid gap-6"
                style={{
                  gridTemplateColumns: `repeat(${rowItems.length}, 1fr)`,
                }}
              >
                {rowItems.map((item) => {
                  const cardId = item.id;
                  if (cardId === 'briefing') {
                    return (
                      <DraggableCard key={cardId} id={cardId}>
                        {cardComponents[cardId]}
                        <CardContent className="space-y-5">
                          {isLoading ? (
                            <div className="h-40 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
                          ) : (
                            <>
                              <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-700">
                                {intelligence.briefing.data?.health_summary || 'All systems nominal.'}
                              </div>

                              <div>
                                <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-900">
                                  <Sparkles className="h-4 w-4 text-indigo-500" />
                                  Urgent priorities
                                </h3>
                                <div className="grid gap-3 md:grid-cols-2">
                                  {urgentItems.length === 0 && (
                                    <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
                                      No urgent items detected in the last run.
                                    </div>
                                  )}
                                  {urgentItems.map((item: LeadershipUrgentItem, index: number) => (
                                    <div key={`${item.title}-${index}`} className="rounded-lg border border-slate-200 bg-white p-4">
                                      <div className="flex items-start justify-between gap-2">
                                        <div>
                                          <p className="font-semibold text-slate-900">{item.title}</p>
                                          <p className="mt-1 text-sm text-slate-600">{item.description}</p>
                                        </div>
                                        <Badge className={`${urgencyBadge(item.urgency)} text-[10px] uppercase`}>{item.urgency}</Badge>
                                      </div>
                                      <div className="mt-4 flex justify-between text-sm">
                                        <span className="text-slate-500">Financial impact</span>
                                        <span className="font-medium">{formatCurrency(item.financial_impact)}</span>
                                      </div>
                                      <div className="mt-2 rounded border border-indigo-100 bg-indigo-50 px-3 py-2 text-sm text-indigo-700">
                                        {item.recommendation}
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            </>
                          )}
                        </CardContent>
                      </DraggableCard>
                    );
                  }
                  return (
                    <DraggableCard key={cardId} id={cardId}>
                      {cardComponents[cardId]}
                    </DraggableCard>
                  );
                })}
              </div>
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  );
};

const ForecastMetricCard = ({
  label,
  value,
  helper,
}: {
  label: string;
  value: string;
  helper: string;
}) => (
  <div className="rounded-lg border border-slate-200 bg-white/80 p-3">
    <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
    <div className="mt-2 text-lg font-semibold text-slate-900">{value}</div>
    <p className="mt-1 text-[11px] text-slate-500">{helper}</p>
  </div>
);

type SummaryStat = {
  label: string;
  value: string;
  helper?: string;
  tone?: 'neutral' | 'positive' | 'negative';
};

const SummaryRibbon = ({ stats }: { stats: SummaryStat[] }) => {
  if (!stats.length) return null;

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {stats.map((stat) => {
        const toneClass =
          stat.tone === 'positive'
            ? 'text-emerald-600'
            : stat.tone === 'negative'
            ? 'text-rose-600'
            : 'text-slate-900';
        return (
          <div
            key={stat.label}
            className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
          >
            <div className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
              {stat.label}
            </div>
            <div className={`mt-2 text-base font-semibold ${toneClass}`}>{stat.value}</div>
            {stat.helper && (
              <p className="mt-1 text-[11px] text-slate-500">{stat.helper}</p>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ControlTowerView;
