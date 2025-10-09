import { useMutation, useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import { intelligenceApi } from './client';
import {
  LeadershipBriefing,
  LeadershipDollarImpact,
  LeadershipDecisionQueue,
  LeadershipRiskWaterfall,
  QueueStatusResponse,
  SlaMonitorResponse,
  AdvisorHeatmapResponse,
  CoachingAlertsResponse,
  WorkloadBalanceResponse,
  CaseResolutionResponse,
  MarketingSegmentsResponse,
  CampaignRecommendationsResponse,
  CampaignPerformanceRequest,
  CampaignPerformanceResponse,
  ChurnAnalysisResponse,
  MessageOptimizerRequest,
  MessageOptimizerResponse,
  CustomerJourneyResponse,
  RoiAttributionResponse,
  IntelligenceAskRequest,
  IntelligenceAskResponse,
  CachedInsightSummary,
  ClearCacheParams,
  ClearCacheResponse,
  IntelligenceHealth,
} from '@/types';

const hoursToMs = (hours: number) => Math.max(1, Math.round(hours * 60 * 60 * 1000));

export const intelligenceKeys = {
  leadership: {
    base: ['intelligence', 'leadership'] as const,
    briefing: (useCache: boolean, ttlHours: number) => [
      'intelligence',
      'leadership',
      'briefing',
      { useCache, ttlHours },
    ] as const,
    dollarImpact: () => ['intelligence', 'leadership', 'dollar-impact'] as const,
    decisionQueue: () => ['intelligence', 'leadership', 'decision-queue'] as const,
    riskWaterfall: () => ['intelligence', 'leadership', 'risk-waterfall'] as const,
  },
  servicing: {
    base: ['intelligence', 'servicing'] as const,
    queueStatus: () => ['intelligence', 'servicing', 'queue-status'] as const,
    slaMonitor: () => ['intelligence', 'servicing', 'sla-monitor'] as const,
    advisorHeatmap: () => ['intelligence', 'servicing', 'advisor-heatmap'] as const,
    coachingAlerts: () => ['intelligence', 'servicing', 'coaching-alerts'] as const,
    workloadBalance: () => ['intelligence', 'servicing', 'workload-balance'] as const,
    caseResolution: () => ['intelligence', 'servicing', 'case-resolution'] as const,
  },
  marketing: {
    base: ['intelligence', 'marketing'] as const,
    segments: () => ['intelligence', 'marketing', 'segments'] as const,
    campaignRecommendations: () => ['intelligence', 'marketing', 'campaign-recommendations'] as const,
    campaignPerformance: (campaignId?: string, dateRange?: string) => [
      'intelligence',
      'marketing',
      'campaign-performance',
      { campaignId: campaignId ?? null, dateRange: dateRange ?? null },
    ] as const,
    churnAnalysis: (useCache: boolean, ttlHours: number) => [
      'intelligence',
      'marketing',
      'churn-analysis',
      { useCache, ttlHours },
    ] as const,
    messageOptimizer: (segment?: string) => [
      'intelligence',
      'marketing',
      'message-optimizer',
      { segment: segment ?? 'general' },
    ] as const,
    customerJourney: () => ['intelligence', 'marketing', 'customer-journey'] as const,
    roiAttribution: () => ['intelligence', 'marketing', 'roi-attribution'] as const,
  },
  crossPersona: {
    ask: () => ['intelligence', 'cross-persona', 'ask'] as const,
    insights: (persona?: string, insightType?: string, limit?: number) => [
      'intelligence',
      'cross-persona',
      'insights',
      { persona: persona ?? null, insightType: insightType ?? null, limit: limit ?? 10 },
    ] as const,
    cache: () => ['intelligence', 'cross-persona', 'cache'] as const,
    health: () => ['intelligence', 'cross-persona', 'health'] as const,
  },
};

type LeadershipIntelligenceOptions = {
  enabled?: boolean;
  briefing?: {
    useCache?: boolean;
    ttlHours?: number;
  };
};

export const useLeadershipIntelligence = (
  options: LeadershipIntelligenceOptions = {}
) => {
  const enabled = options.enabled ?? true;
  const useCache = options.briefing?.useCache ?? true;
  const ttlHours = options.briefing?.ttlHours ?? 1;
  const staleMs = hoursToMs(ttlHours);

  const briefing = useQuery<LeadershipBriefing>({
    queryKey: intelligenceKeys.leadership.briefing(useCache, ttlHours),
    queryFn: () => intelligenceApi.leadership.briefing({ useCache, ttlHours }),
    enabled,
    staleTime: staleMs,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<LeadershipBriefing, Error>;

  const dollarImpact = useQuery<LeadershipDollarImpact>({
    queryKey: intelligenceKeys.leadership.dollarImpact(),
    queryFn: () => intelligenceApi.leadership.dollarImpact(),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<LeadershipDollarImpact, Error>;

  const decisionQueue = useQuery<LeadershipDecisionQueue>({
    queryKey: intelligenceKeys.leadership.decisionQueue(),
    queryFn: () => intelligenceApi.leadership.decisionQueue(),
    enabled,
    staleTime: 60 * 1000,
    refetchInterval: enabled ? 60 * 1000 : false,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<LeadershipDecisionQueue, Error>;

  const riskWaterfall = useQuery<LeadershipRiskWaterfall>({
    queryKey: intelligenceKeys.leadership.riskWaterfall(),
    queryFn: () => intelligenceApi.leadership.riskWaterfall(),
    enabled,
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<LeadershipRiskWaterfall, Error>;

  return {
    briefing,
    dollarImpact,
    decisionQueue,
    riskWaterfall,
  };
};

type ServicingIntelligenceOptions = {
  enabled?: boolean;
  pollIntervalMs?: number;
};

export const useServicingIntelligence = (
  options: ServicingIntelligenceOptions = {}
) => {
  const enabled = options.enabled ?? true;
  const pollMs = options.pollIntervalMs ?? 60_000;

  const queueStatus = useQuery<QueueStatusResponse>({
    queryKey: intelligenceKeys.servicing.queueStatus(),
    queryFn: () => intelligenceApi.servicing.queueStatus(),
    enabled,
    staleTime: pollMs,
    refetchInterval: enabled ? pollMs : false,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<QueueStatusResponse, Error>;

  const slaMonitor = useQuery<SlaMonitorResponse>({
    queryKey: intelligenceKeys.servicing.slaMonitor(),
    queryFn: () => intelligenceApi.servicing.slaMonitor(),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchInterval: enabled ? 2 * pollMs : false,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<SlaMonitorResponse, Error>;

  const advisorHeatmap = useQuery<AdvisorHeatmapResponse>({
    queryKey: intelligenceKeys.servicing.advisorHeatmap(),
    queryFn: () => intelligenceApi.servicing.advisorHeatmap(),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<AdvisorHeatmapResponse, Error>;

  const coachingAlerts = useQuery<CoachingAlertsResponse>({
    queryKey: intelligenceKeys.servicing.coachingAlerts(),
    queryFn: () => intelligenceApi.servicing.coachingAlerts(),
    enabled,
    staleTime: 2 * 60 * 1000,
    refetchInterval: enabled ? 2 * 60 * 1000 : false,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<CoachingAlertsResponse, Error>;

  const workloadBalance = useQuery<WorkloadBalanceResponse>({
    queryKey: intelligenceKeys.servicing.workloadBalance(),
    queryFn: () => intelligenceApi.servicing.workloadBalance(),
    enabled,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<WorkloadBalanceResponse, Error>;

  const caseResolution = useQuery<CaseResolutionResponse>({
    queryKey: intelligenceKeys.servicing.caseResolution(),
    queryFn: () => intelligenceApi.servicing.caseResolution(),
    enabled,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<CaseResolutionResponse, Error>;

  return {
    queueStatus,
    slaMonitor,
    advisorHeatmap,
    coachingAlerts,
    workloadBalance,
    caseResolution,
  };
};

type MarketingIntelligenceOptions = {
  enabled?: boolean;
  churn?: {
    useCache?: boolean;
    ttlHours?: number;
  };
  campaignPerformance?: CampaignPerformanceRequest;
};

export const useMarketingIntelligence = (
  options: MarketingIntelligenceOptions = {}
) => {
  const enabled = options.enabled ?? true;
  const churnUseCache = options.churn?.useCache ?? true;
  const churnTtl = options.churn?.ttlHours ?? 2;
  const churnStaleMs = hoursToMs(churnTtl);
  const campaignFilters = options.campaignPerformance ?? {};

  const segments = useQuery<MarketingSegmentsResponse>({
    queryKey: intelligenceKeys.marketing.segments(),
    queryFn: () => intelligenceApi.marketing.segments(),
    enabled,
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<MarketingSegmentsResponse, Error>;

  const campaignRecommendations = useQuery<CampaignRecommendationsResponse>({
    queryKey: intelligenceKeys.marketing.campaignRecommendations(),
    queryFn: () => intelligenceApi.marketing.campaignRecommendations(),
    enabled,
    staleTime: 10 * 60 * 1000,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<CampaignRecommendationsResponse, Error>;

  const campaignPerformance = useQuery<CampaignPerformanceResponse>({
    queryKey: intelligenceKeys.marketing.campaignPerformance(
      campaignFilters.campaign_id,
      campaignFilters.date_range
    ),
    queryFn: () => intelligenceApi.marketing.campaignPerformance(campaignFilters),
    enabled,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<CampaignPerformanceResponse, Error>;

  const churnAnalysis = useQuery<ChurnAnalysisResponse>({
    queryKey: intelligenceKeys.marketing.churnAnalysis(churnUseCache, churnTtl),
    queryFn: () =>
      intelligenceApi.marketing.churnAnalysis({
        useCache: churnUseCache,
        ttlHours: churnTtl,
      }),
    enabled,
    staleTime: churnStaleMs,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<ChurnAnalysisResponse, Error>;

  const customerJourney = useQuery<CustomerJourneyResponse>({
    queryKey: intelligenceKeys.marketing.customerJourney(),
    queryFn: () => intelligenceApi.marketing.customerJourney(),
    enabled,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<CustomerJourneyResponse, Error>;

  const roiAttribution = useQuery<RoiAttributionResponse>({
    queryKey: intelligenceKeys.marketing.roiAttribution(),
    queryFn: () => intelligenceApi.marketing.roiAttribution(),
    enabled,
    refetchOnWindowFocus: false,
  }) as UseQueryResult<RoiAttributionResponse, Error>;

  return {
    segments,
    campaignRecommendations,
    campaignPerformance,
    churnAnalysis,
    customerJourney,
    roiAttribution,
  };
};

export const useMessageOptimizer = () =>
  useMutation<MessageOptimizerResponse, unknown, MessageOptimizerRequest>({
    mutationKey: intelligenceKeys.marketing.messageOptimizer(),
    mutationFn: (payload) => intelligenceApi.marketing.messageOptimizer(payload),
  });

export const useIntelligenceAsk = () =>
  useMutation<IntelligenceAskResponse, unknown, IntelligenceAskRequest>({
    mutationKey: intelligenceKeys.crossPersona.ask(),
    mutationFn: (payload) => intelligenceApi.crossPersona.ask(payload),
  });

type CachedInsightsOptions = {
  persona?: string;
  insightType?: string;
  limit?: number;
  enabled?: boolean;
};

export const useCachedInsights = (options: CachedInsightsOptions = {}) => {
  const enabled = options.enabled ?? true;

  return useQuery<CachedInsightSummary[]>({
    queryKey: intelligenceKeys.crossPersona.insights(
      options.persona,
      options.insightType,
      options.limit
    ),
    queryFn: () =>
      intelligenceApi.crossPersona.listInsights({
        persona: options.persona,
        insightType: options.insightType,
        limit: options.limit,
      }),
    enabled,
    refetchOnWindowFocus: false,
  });
};

export const useClearIntelligenceCache = () => {
  const queryClient = useQueryClient();

  return useMutation<ClearCacheResponse, unknown, ClearCacheParams>({
    mutationKey: intelligenceKeys.crossPersona.cache(),
    mutationFn: (params) => intelligenceApi.crossPersona.clearCache(params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: intelligenceKeys.crossPersona.insights(undefined, undefined, undefined) });
      queryClient.invalidateQueries({ queryKey: intelligenceKeys.leadership.base });
      queryClient.invalidateQueries({ queryKey: intelligenceKeys.marketing.base });
      queryClient.invalidateQueries({ queryKey: intelligenceKeys.servicing.base });
    },
  });
};

export const useIntelligenceHealth = (options: { enabled?: boolean } = {}) =>
  useQuery<IntelligenceHealth>({
    queryKey: intelligenceKeys.crossPersona.health(),
    queryFn: () => intelligenceApi.crossPersona.health(),
    enabled: options.enabled ?? true,
    refetchInterval: options.enabled === false ? false : 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  });
