import { useMemo } from 'react';
import {
  AlertTriangle,
  BarChart3,
  Briefcase,
  DollarSign,
  RefreshCw,
  ShieldAlert,
  Sparkles,
} from 'lucide-react';
import { useLeadershipIntelligence } from '@/api/intelligenceHooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import IntelligenceStatusBar from '@/components/IntelligenceStatusBar';
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
} from '@/types';

const HEALTH_TONE: Record<string, string> = {
  STABLE: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
  ATTENTION: 'bg-amber-100 text-amber-700 border border-amber-200',
  CRITICAL: 'bg-rose-100 text-rose-700 border border-rose-200',
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

const ControlTowerView = () => {
  const intelligence = useLeadershipIntelligence();

  const isLoading = combineLoadingStates(
    intelligence.briefing.isLoading,
    intelligence.dollarImpact.isLoading,
    intelligence.decisionQueue.isLoading,
    intelligence.riskWaterfall.isLoading
  );

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
  const dollarImpact = intelligence.dollarImpact.data;
  const riskWaterfall = intelligence.riskWaterfall.data as LeadershipRiskWaterfall | undefined;

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

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="text-lg">Executive Briefing</CardTitle>
              <p className="text-sm text-slate-500">
                Generated {diffFromNow(intelligence.briefing.data?._generated_at ?? intelligence.briefing.data?.generated_at)}
              </p>
            </div>
            <Badge className={`${portfolioHealthClass} px-3 py-1 text-xs uppercase font-medium`}>
              {intelligence.briefing.data?.portfolio_health ?? 'Loading'}
            </Badge>
          </CardHeader>
          <CardContent className="space-y-5">
            {isLoading ? (
              <div className="h-40 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
            ) : (
              <>
                <div className="text-slate-700">
                  {intelligence.briefing.data?.health_summary || 'All systems nominal.'}
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-900 mb-3 flex items-center gap-2">
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
        </Card>

        <Card>
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
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-2">
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
        </Card>

        <Card>
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
        </Card>
      </div>

      <Card>
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
      </Card>
    </div>
  );
};

export default ControlTowerView;
