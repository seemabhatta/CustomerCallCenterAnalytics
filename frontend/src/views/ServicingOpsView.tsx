import {
  AlertTriangle,
  Clock3,
  FlameKindling,
  Headphones,
  Layers,
  LineChart,
  Users,
} from 'lucide-react';
import { useServicingIntelligence } from '@/api/intelligenceHooks';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import IntelligenceStatusBar from '@/components/IntelligenceStatusBar';
import {
  combineErrors,
  combineLoadingStates,
  diffFromNow,
  formatCurrency,
  formatNumber,
  formatPercent,
  formatTime,
} from '@/utils/formatters';
import { RefreshCw } from 'lucide-react';

const STATUS_COLOR: Record<string, string> = {
  green: 'bg-emerald-100 text-emerald-700 border border-emerald-200',
  yellow: 'bg-amber-100 text-amber-700 border border-amber-200',
  red: 'bg-rose-100 text-rose-700 border border-rose-200',
};

const ServicingOpsView = () => {
  const intelligence = useServicingIntelligence({ pollIntervalMs: 45_000 });

  const isLoading = combineLoadingStates(
    intelligence.queueStatus.isLoading,
    intelligence.slaMonitor.isLoading,
    intelligence.advisorHeatmap.isLoading,
    intelligence.coachingAlerts.isLoading,
    intelligence.workloadBalance.isLoading,
    intelligence.caseResolution.isLoading
  );

  const error = combineErrors(
    intelligence.queueStatus.error as Error | undefined,
    intelligence.slaMonitor.error as Error | undefined,
    intelligence.advisorHeatmap.error as Error | undefined,
    intelligence.coachingAlerts.error as Error | undefined,
    intelligence.workloadBalance.error as Error | undefined
  );

  const queue = intelligence.queueStatus.data;
  const sla = intelligence.slaMonitor.data;
  const heatmap = intelligence.advisorHeatmap.data?.advisors ?? [];
  const heatmapSummary = intelligence.advisorHeatmap.data?.summary;
  const coaching = intelligence.coachingAlerts.data;
  const staffing = intelligence.workloadBalance.data;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 flex items-center gap-2">
            <Headphones className="h-6 w-6 text-indigo-600" />
            Servicing Command Center
          </h1>
          <p className="mt-1 text-sm text-slate-600 max-w-2xl">
            Real-time view of servicing operations. Forecast-backed queue outlook, SLA health, and
            advisor coaching intelligence to keep customer promises on track.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={() => {
            intelligence.queueStatus.refetch();
            intelligence.slaMonitor.refetch();
            intelligence.advisorHeatmap.refetch();
            intelligence.coachingAlerts.refetch();
            intelligence.workloadBalance.refetch();
            intelligence.caseResolution.refetch();
          }}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Sync now
        </Button>
      </div>

      {error && (
        <Card className="border border-rose-200 bg-rose-50">
          <CardContent className="py-4">
            <div className="flex items-center gap-3 text-rose-700">
              <AlertTriangle className="h-5 w-5" />
              <div>
                <p className="font-semibold">Operational telemetry unavailable</p>
                <p className="text-sm">{error.message}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <IntelligenceStatusBar persona="servicing" />

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-lg">
                <LineChart className="h-5 w-5 text-indigo-500" />
                Queue outlook (next 4 hours)
              </CardTitle>
              <p className="text-sm text-slate-500">
                Updated {diffFromNow(queue?.generated_at)} • Staffing {queue?.staffing_status ?? 'unknown'}
              </p>
            </div>
          </CardHeader>
          <CardContent>
            {queue ? (
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-lg border border-slate-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-slate-900">Live queue</h3>
                  <div className="mt-3 space-y-2 text-sm text-slate-600">
                    {Object.entries(queue.current_queue || {}).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="capitalize">{key.replace('_', ' ')}</span>
                        <span className="font-medium">{formatNumber(value)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="rounded-lg border border-slate-200 bg-white p-4">
                  <h3 className="text-sm font-semibold text-slate-900">Forecast window</h3>
                  <div className="mt-3 space-y-3">
                    {queue.predicted_volume?.map((slot, index) => (
                      <div key={`${slot.hour}-${index}`} className="flex items-center justify-between text-sm">
                        <div>
                          <p className="font-medium text-slate-800">{formatTime(slot.hour)}</p>
                          <p className="text-xs text-slate-500">Predicted calls</p>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-slate-900">{formatNumber(slot.predicted_calls)}</p>
                          {slot.confidence && Array.isArray(slot.confidence) && (
                            <p className="text-xs text-slate-500">
                              CI {formatNumber(slot.confidence[0])} - {formatNumber(slot.confidence[1])}
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="h-40 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Clock3 className="h-5 w-5 text-emerald-500" />
              SLA health
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm">
            {sla ? (
              <>
                {Object.entries(sla.current_performance || {}).map(([metric, value]) => (
                  <div key={metric} className="flex justify-between">
                    <span className="capitalize text-slate-600">{metric.replace(/_/g, ' ')}</span>
                    <span className="font-medium text-slate-900">
                      {typeof value === 'number' ? formatPercent(value * (metric.includes('rate') ? 100 : 1)) : String(value)}
                    </span>
                  </div>
                ))}
                {sla.predictions && (
                  <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
                    Forecast outlook: {JSON.stringify(sla.predictions)}
                  </div>
                )}
              </>
            ) : (
              <div className="h-40 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Users className="h-5 w-5 text-sky-500" />
                Advisor performance heatmap
              </CardTitle>
              <p className="text-sm text-slate-500">
                {formatNumber(heatmapSummary?.total_advisors)} advisors monitored •
                {' '}
                {formatNumber(heatmapSummary?.red_status)} in red status
              </p>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {heatmap.length === 0 ? (
              <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
                Heatmap data unavailable. Ensure advisor analytics pipeline has run in the last 24 hours.
              </div>
            ) : (
              <div className="grid gap-3 md:grid-cols-2">
                {heatmap.slice(0, 8).map((advisor, index) => (
                  <div key={`${advisor.advisor_id ?? index}`} className="rounded-lg border border-slate-200 bg-white p-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-sm font-semibold text-slate-900">{advisor.advisor_name ?? `Advisor ${advisor.advisor_id ?? index + 1}`}</p>
                        <p className="text-xs text-slate-500">Segment: {advisor.segment ?? '—'}</p>
                      </div>
                      <Badge className={`${STATUS_COLOR[advisor.status] ?? STATUS_COLOR.yellow} text-[10px] uppercase`}>{advisor.status}</Badge>
                    </div>
                    <div className="mt-3 grid grid-cols-3 gap-2 text-xs text-slate-600">
                      <div className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                        <p className="uppercase tracking-wide text-[10px] text-slate-400">Empathy</p>
                        <p className="font-semibold text-slate-800">{formatNumber(advisor.empathy_score, { maximumFractionDigits: 1 })}</p>
                      </div>
                      <div className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                        <p className="uppercase tracking-wide text-[10px] text-slate-400">Compliance</p>
                        <p className="font-semibold text-slate-800">{formatPercent(advisor.compliance_score * 100)}</p>
                      </div>
                      <div className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                        <p className="uppercase tracking-wide text-[10px] text-slate-400">FCR</p>
                        <p className="font-semibold text-slate-800">{formatPercent(advisor.fcr_rate * 100)}</p>
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
              <FlameKindling className="h-5 w-5 text-rose-500" />
              Coaching alerts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {coaching ? (
              <>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
                  {formatNumber(coaching.team_summary?.advisors_needing_coaching)} of{' '}
                  {formatNumber(coaching.team_summary?.total_advisors)} advisors flagged. Team health:
                  {' '}
                  {coaching.team_summary?.team_health ?? '—'}.
                </div>
                <div className="space-y-3">
                  {(coaching.critical_alerts ?? []).map((alert, index) => (
                    <div key={`${alert.id ?? index}`} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                      <div className="flex items-center justify-between">
                        <p className="font-semibold text-slate-900">{alert.title ?? alert.type}</p>
                        <Badge className="bg-rose-100 text-rose-700 border border-rose-200 text-[10px] uppercase">
                          {alert.urgency}
                        </Badge>
                      </div>
                      <p className="mt-2 text-slate-600">{alert.recommendation ?? 'Coaching required'}</p>
                      {alert.expected_impact && (
                        <p className="mt-2 text-xs text-slate-500">
                          Impact: {formatCurrency(alert.expected_impact)}
                        </p>
                      )}
                    </div>
                  ))}
                  {(coaching.critical_alerts ?? []).length === 0 && (
                    <p className="text-sm text-slate-500">No critical coaching alerts right now.</p>
                  )}
                </div>
              </>
            ) : (
              <div className="h-48 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Layers className="h-5 w-5 text-indigo-500" />
              Staffing balance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {staffing ? (
              <>
                <div className="flex justify-between">
                  <span className="text-slate-600">Current staff</span>
                  <span className="font-semibold text-slate-900">{formatNumber(staffing.current_staff)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Needed for peak</span>
                  <span className="font-semibold text-slate-900">{formatNumber(staffing.needed_for_peak)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Gap</span>
                  <span className="font-semibold text-slate-900">{formatNumber(staffing.gap)}</span>
                </div>
                <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
                  {staffing.recommendation}
                </div>
              </>
            ) : (
              <div className="h-32 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Case resolution
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-600">
            {intelligence.caseResolution.data ? (
              <>
                <p>{intelligence.caseResolution.data.message}</p>
                <div className="grid grid-cols-2 gap-3 rounded border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 sm:grid-cols-4">
                  <div>
                    <p className="uppercase tracking-wide text-[10px] text-slate-400">Active cases</p>
                    <p className="text-sm font-semibold text-slate-900">
                      {formatNumber(intelligence.caseResolution.data.summary.total_active_cases)}
                    </p>
                  </div>
                  <div>
                    <p className="uppercase tracking-wide text-[10px] text-slate-400">Resolved (7d)</p>
                    <p className="text-sm font-semibold text-slate-900">
                      {formatNumber(intelligence.caseResolution.data.summary.resolved_last_7_days)}
                    </p>
                  </div>
                  <div>
                    <p className="uppercase tracking-wide text-[10px] text-slate-400">Avg age (days)</p>
                    <p className="text-sm font-semibold text-slate-900">
                      {formatNumber(intelligence.caseResolution.data.summary.avg_case_age_days, { maximumFractionDigits: 1 })}
                    </p>
                  </div>
                  <div>
                    <p className="uppercase tracking-wide text-[10px] text-slate-400">Resolved total</p>
                    <p className="text-sm font-semibold text-slate-900">
                      {formatNumber(intelligence.caseResolution.data.summary.total_resolved_cases)}
                    </p>
                  </div>
                </div>
                {intelligence.caseResolution.data.urgent_cases.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Top open cases</p>
                    <div className="space-y-2">
                      {intelligence.caseResolution.data.urgent_cases.map((item) => (
                        <div key={item.analysis_id} className="rounded border border-slate-200 bg-white p-3 text-xs text-slate-600">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="font-medium text-slate-900">{item.topic || 'Unspecified issue'}</span>
                            <span className="text-slate-500">{item.age_days ?? 0}d open</span>
                          </div>
                          <div className="mt-2 flex gap-4 text-[11px] text-slate-500">
                            <span>Delinquency {formatPercent(item.delinquency_risk * 100)}</span>
                            <span>Churn {formatPercent(item.churn_risk * 100)}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-slate-500">No unresolved cases detected right now.</p>
                )}
                <div className="text-xs text-slate-500">
                  Generated {diffFromNow(intelligence.caseResolution.data.generated_at)}
                </div>
              </>
            ) : (
              <div className="h-32 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default ServicingOpsView;
