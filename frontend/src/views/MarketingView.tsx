import { FormEvent, useMemo, useState } from 'react';
import {
  AlignLeft,
  BarChart4,
  Megaphone,
  MessageCircle,
  PieChart,
  RefreshCw,
  Target,
  Users,
} from 'lucide-react';
import {
  useMarketingIntelligence,
  useMessageOptimizer,
} from '@/api/intelligenceHooks';
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
} from '@/utils/formatters';
import {
  ChurnRootCause,
  ChurnTargetSegment,
  MarketingCampaign,
  MarketingSegment,
  RetentionStrategy,
} from '@/types';

const MarketingView = () => {
  const intelligence = useMarketingIntelligence();
  const messageOptimizer = useMessageOptimizer();

  const [messageDraft, setMessageDraft] = useState('We appreciate your loyalty. Here is an exclusive rate just for you.');
  const [targetSegment, setTargetSegment] = useState('general');

  const segments = (intelligence.segments.data?.segments ?? []) as MarketingSegment[];
  const churn = intelligence.churnAnalysis.data;

  const isLoading = combineLoadingStates(
    intelligence.segments.isLoading,
    intelligence.campaignRecommendations.isLoading,
    intelligence.campaignPerformance.isLoading,
    intelligence.churnAnalysis.isLoading,
    intelligence.customerJourney.isLoading,
    intelligence.roiAttribution.isLoading,
  );

  const error = combineErrors(
    intelligence.segments.error as Error | undefined,
    intelligence.campaignRecommendations.error as Error | undefined,
    intelligence.churnAnalysis.error as Error | undefined,
    intelligence.roiAttribution.error as Error | undefined
  );

  const handleOptimize = (event: FormEvent) => {
    event.preventDefault();
    if (!messageDraft.trim()) return;
    messageOptimizer.mutate({ message: messageDraft, segment: targetSegment });
  };

  const optimizedMessage = messageOptimizer.data?.optimized_message ?? messageOptimizer.data?.message;

  const campaignRecommendations = (intelligence.campaignRecommendations.data?.campaigns ?? []) as MarketingCampaign[];

  const churnSummary = useMemo(() => (
    churn?.insights?.churn_summary ?? {}
  ), [churn?.insights?.churn_summary]);

  const retentionStrategies = (churn?.insights?.retention_strategies ?? []) as RetentionStrategy[];
  const rootCauses = (churn?.insights?.root_causes ?? []) as ChurnRootCause[];
  const targetSegments = (churn?.insights?.target_segments ?? []) as ChurnTargetSegment[];

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 flex items-center gap-2">
            <Megaphone className="h-6 w-6 text-pink-600" />
            Marketing Intelligence
          </h1>
          <p className="mt-1 text-sm text-slate-600 max-w-2xl">
            Campaign-ready insight for marketing teams. Combines predictive churn models with GenAI
            to surface high-value segments, ready-to-run campaigns, and optimized messaging.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          className="gap-2"
          onClick={() => {
            intelligence.segments.refetch();
            intelligence.campaignRecommendations.refetch();
            intelligence.campaignPerformance.refetch();
            intelligence.churnAnalysis.refetch();
            intelligence.customerJourney.refetch();
            intelligence.roiAttribution.refetch();
          }}
          disabled={isLoading}
        >
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh insights
        </Button>
      </div>

      {error && (
        <Card className="border border-rose-200 bg-rose-50">
          <CardContent className="py-4 text-sm text-rose-700">
            Marketing intelligence temporarily unavailable: {error.message}
          </CardContent>
        </Card>
      )}

      <IntelligenceStatusBar persona="marketing" />

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-lg">
                <PieChart className="h-5 w-5 text-indigo-500" />
                High-value segments
              </CardTitle>
              <p className="text-sm text-slate-500">
                {formatNumber(intelligence.segments.data?.summary?.total_segments)} segments identified •
                {' '}Total opportunity {formatCurrency(intelligence.segments.data?.summary?.total_opportunity_value)}
              </p>
            </div>
          </CardHeader>
          <CardContent className="grid gap-3 md:grid-cols-2">
            {segments.length === 0 ? (
              <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
                No segmentation data yet. Run the pipeline to populate persona intelligence.
              </div>
            ) : (
              segments.map((segment) => (
                <div key={segment.segment_id} className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <p className="text-sm font-semibold text-slate-900">{segment.segment_name}</p>
                      <p className="text-xs text-slate-500">{segment.profile}</p>
                    </div>
                    <Badge variant="outline" className="text-[10px] uppercase">
                      {segment.priority}
                    </Badge>
                  </div>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600">
                    <div className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                      <p className="uppercase tracking-wide text-[10px] text-slate-400">Count</p>
                      <p className="font-semibold text-slate-800">{formatNumber(segment.count)}</p>
                    </div>
                    <div className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                      <p className="uppercase tracking-wide text-[10px] text-slate-400">Opportunity</p>
                      <p className="font-semibold text-slate-800">{formatCurrency(segment.opportunity_value)}</p>
                    </div>
                  </div>
                  <p className="mt-3 text-xs text-slate-500">
                    Engagement: {segment.engagement_strategy ?? '—'}
                  </p>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <BarChart4 className="h-5 w-5 text-emerald-500" />
              ROI attribution
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            {intelligence.roiAttribution.data ? (
              <>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-400">Total opportunity</p>
                  <p className="text-xl font-semibold text-slate-900">
                    {formatCurrency(intelligence.roiAttribution.data.total_opportunity_value)}
                  </p>
                </div>
                <div className="space-y-2">
                  {Object.entries(intelligence.roiAttribution.data.by_category || {}).map(([category, value]) => (
                    <div key={category} className="flex items-center justify-between">
                      <span className="capitalize text-slate-600">{category.replace('_', ' ')}</span>
                      <span className="font-medium text-slate-900">{formatCurrency(value)}</span>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="h-40 animate-pulse rounded-lg border border-dashed border-slate-200 bg-slate-50" />
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Users className="h-5 w-5 text-emerald-500" />
              Campaign playbook
            </CardTitle>
            <p className="text-sm text-slate-500">
              {formatNumber(intelligence.campaignRecommendations.data?.summary?.total_campaigns)} ready-to-launch campaigns •
              {' '}Projected lift {formatCurrency(intelligence.campaignRecommendations.data?.summary?.total_potential_revenue)}
            </p>
          </div>
          <Badge variant="outline" className="text-xs">
            Avg ROI {formatPercent(intelligence.campaignRecommendations.data?.summary?.avg_roi)}
          </Badge>
        </CardHeader>
        <CardContent className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {campaignRecommendations.length === 0 ? (
            <div className="rounded-lg border border-slate-200 bg-white p-4 text-sm text-slate-500">
              No campaign recommendations yet. Re-run marketing intelligence after refreshing forecasts.
            </div>
          ) : (
            campaignRecommendations.map((campaign) => (
              <div key={campaign.id} className="rounded-lg border border-slate-200 bg-white p-4 text-sm">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-slate-900">{campaign.title}</p>
                  <Badge variant="outline" className="text-[10px] uppercase">
                    {campaign.urgency}
                  </Badge>
                </div>
                <p className="mt-2 text-xs text-slate-500">Segment: {campaign.target_segment}</p>
                <p className="mt-1 text-xs text-slate-500">Size: {formatNumber(campaign.target_count)}</p>
                <div className="mt-3 grid grid-cols-2 gap-2 text-xs text-slate-600">
                  <div className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                    <p className="uppercase tracking-wide text-[10px] text-slate-400">Revenue</p>
                    <p className="font-semibold text-slate-800">{formatCurrency(campaign.expected_revenue)}</p>
                  </div>
                  <div className="rounded border border-slate-200 bg-slate-50 px-2 py-1">
                    <p className="uppercase tracking-wide text-[10px] text-slate-400">Cost</p>
                    <p className="font-semibold text-slate-800">{formatCurrency(campaign.campaign_cost)}</p>
                  </div>
                </div>
                <p className="mt-3 text-xs text-slate-500">{campaign.recommendation}</p>
              </div>
            ))
          )}
        </CardContent>
      </Card>

      <div className="grid gap-6 xl:grid-cols-3">
        <Card className="xl:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-lg">
                <Target className="h-5 w-5 text-rose-500" />
                Churn watchlist
              </CardTitle>
              <p className="text-sm text-slate-500">
                Revenue at risk {formatCurrency(churnSummary?.revenue_at_risk)} • Trend {churnSummary?.trend ?? '—'} • Current rate {formatPercent((churnSummary?.current_rate ?? 0) * 100)}
              </p>
            </div>
            <Badge variant="outline" className="text-xs">
              {formatNumber(churnSummary?.high_risk_count)} high-risk customers
            </Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            {rootCauses.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Root causes</h3>
                <div className="mt-2 grid gap-3 md:grid-cols-2">
                  {rootCauses.map((cause: ChurnRootCause, index: number) => (
                    <div key={`${cause.cause}-${index}`} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-slate-900">{cause.cause}</p>
                        <Badge variant="outline" className="text-[10px] uppercase">
                          {cause.impact}
                        </Badge>
                      </div>
                      <p className="mt-2 text-xs text-slate-500">{cause.evidence}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {targetSegments.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Priority segments</h3>
                <div className="mt-2 grid gap-3 md:grid-cols-2">
                  {targetSegments.map((segment: ChurnTargetSegment, index: number) => (
                    <div key={`${segment.segment_name}-${index}`} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                      <p className="font-medium text-slate-900">{segment.segment_name}</p>
                      <p className="text-xs text-slate-500">
                        {formatNumber(segment.count)} customers • Drivers: {segment.risk_drivers.join(', ')}
                      </p>
                      <p className="mt-2 text-xs text-slate-500">
                        Traits: {segment.characteristics.join(', ')}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {retentionStrategies.length > 0 && (
              <div>
                <h3 className="text-sm font-semibold text-slate-900">Retention strategies</h3>
                <div className="mt-2 space-y-3">
                  {retentionStrategies.map((strategy: RetentionStrategy, index: number) => (
                    <div key={`${strategy.strategy}-${index}`} className="rounded-lg border border-slate-200 bg-white p-3 text-sm">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-slate-900">{strategy.strategy}</p>
                        <Badge variant="outline" className="text-[10px] uppercase">
                          ROI {formatPercent(strategy.roi_estimate)}
                        </Badge>
                      </div>
                      <p className="mt-2 text-xs text-slate-500">Target: {strategy.target_segment}</p>
                      <p className="mt-1 text-xs text-slate-500">Approach: {strategy.approach}</p>
                      <p className="mt-1 text-xs text-slate-500">Messaging: {strategy.messaging.join(', ')}</p>
                      <p className="mt-1 text-xs text-slate-500">Channels: {strategy.channels.join(', ')}</p>
                      <p className="mt-2 text-xs text-slate-500">
                        Expected retention {formatPercent(strategy.expected_retention_rate * 100)} • Cost per contact {formatCurrency(strategy.cost_per_contact)}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <Users className="h-5 w-5 text-indigo-500" />
              Journey insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm text-slate-600">
            <p>{intelligence.customerJourney.data?.message ?? 'Journey analytics not yet available.'}</p>
            {intelligence.customerJourney.data?.stages?.length ? (
              <div className="space-y-2 text-xs text-slate-500">
                {intelligence.customerJourney.data.stages.map((stage) => (
                  <div key={stage.stage} className="rounded border border-slate-200 bg-white p-3">
                    <div className="flex items-center justify-between text-slate-700">
                      <span className="font-medium text-slate-900">{stage.stage}</span>
                      <span>{formatNumber(stage.count)} records</span>
                    </div>
                    <div className="mt-1 flex items-center justify-between">
                      <span>{stage.description}</span>
                      <span className="text-slate-400">Conversion {formatPercent(stage.conversion_rate * 100)}</span>
                    </div>
                  </div>
                ))}
                <p className="text-slate-500">Top intents: {intelligence.customerJourney.data.top_intents}</p>
              </div>
            ) : null}
            <div className="text-xs text-slate-500">
              Generated {diffFromNow(intelligence.customerJourney.data?.generated_at)}
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-lg">
              <MessageCircle className="h-5 w-5 text-purple-500" />
              Message optimizer
            </CardTitle>
            <p className="text-sm text-slate-500">
              Feed a draft invite or retention script and let GenAI tailor it to the selected segment.
            </p>
          </div>
          {messageOptimizer.data && (
            <Badge variant="secondary" className="text-xs text-slate-600">
              Updated {diffFromNow(messageOptimizer.data.generated_at)}
            </Badge>
          )}
        </CardHeader>
        <CardContent>
          <form onSubmit={handleOptimize} className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Draft message</label>
              <textarea
                className="min-h-[160px] w-full rounded border border-slate-300 bg-white px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                value={messageDraft}
                onChange={(event) => setMessageDraft(event.target.value)}
              />
              <div>
                <span className="text-xs uppercase tracking-wide text-slate-500">Target segment</span>
                <select
                  className="mt-1 w-full rounded border border-slate-300 bg-white px-2 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
                  value={targetSegment}
                  onChange={(event) => setTargetSegment(event.target.value)}
                >
                  <option value="general">General audience</option>
                  {segments.map((segment) => (
                    <option key={segment.segment_id} value={segment.segment_id}>
                      {segment.segment_name}
                    </option>
                  ))}
                </select>
              </div>
              <Button
                type="submit"
                className="mt-2 flex items-center gap-2"
                disabled={messageOptimizer.status === 'pending'}
              >
                {messageOptimizer.status === 'pending' && <RefreshCw className="h-4 w-4 animate-spin" />}
                Optimize message
              </Button>
            </div>

            <div className="flex min-h-[200px] flex-col rounded border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
              <div className="mb-2 flex items-center gap-2 text-slate-500">
                <AlignLeft className="h-4 w-4" />
                Optimized output
              </div>
              <div className="flex-1 whitespace-pre-line">
                {optimizedMessage || 'Run the optimizer to generate tailored copy for this segment.'}
              </div>
              {messageOptimizer.data?.suggestions?.length ? (
                <div className="mt-3 space-y-1 text-xs text-slate-500">
                  {messageOptimizer.data.suggestions.map((tip, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <span className="mt-[2px] text-slate-400">•</span>
                      <span>{tip}</span>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default MarketingView;
