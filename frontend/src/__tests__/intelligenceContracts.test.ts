/**
 * Type-level smoke tests for intelligence contracts.
 *
 * These guards run during tsc (type-check) and sanity-check
 * the key factories without requiring a full test harness.
 */
import {
  LeadershipBriefing,
  LeadershipDecisionQueue,
  QueueStatusResponse,
  MarketingSegmentsResponse,
} from '@/types';
import { intelligenceKeys } from '@/api/intelligenceHooks';

// Sample objects to validate type compatibility (compile-time check)
const leadershipBriefingSample: LeadershipBriefing = {
  portfolio_health: 'STABLE',
  health_summary: 'Portfolio stable with monitoring required.',
  urgent_items: [],
  financial_summary: {
    total_at_risk: 0,
    delinquency_risk: 0,
    churn_risk: 0,
    compliance_risk: 0,
    recoverable_with_action: 0,
    net_impact: 0,
  },
  recommendations: [],
  generated_at: new Date().toISOString(),
  _generated_at: new Date().toISOString(),
  _cached: false,
};

const decisionQueueSample: LeadershipDecisionQueue = {
  count: 0,
  urgent_count: 0,
  decisions: [],
  generated_at: new Date().toISOString(),
};

const queueStatusSample: QueueStatusResponse = {
  current_queue: {
    high_priority: 0,
    standard: 0,
    callback_scheduled: 0,
  },
  predicted_volume: [],
  current_capacity: 0,
  staffing_status: 'unknown',
  generated_at: new Date().toISOString(),
};

const marketingSegmentsSample: MarketingSegmentsResponse = {
  segments: [],
  summary: {
    total_segments: 0,
    high_priority_segments: 0,
    total_opportunity_value: 0,
  },
  generated_at: new Date().toISOString(),
};

void leadershipBriefingSample;
void decisionQueueSample;
void queueStatusSample;
void marketingSegmentsSample;

// Runtime assertions on query key factories (executed via node --test or direct import)
const briefingKey = intelligenceKeys.leadership.briefing(true, 1);
const expectedBriefingKey = ['intelligence', 'leadership', 'briefing', { useCache: true, ttlHours: 1 }] as const;

// Lightweight runtime checks executed when file is imported
if (briefingKey[0] !== expectedBriefingKey[0] || briefingKey[1] !== expectedBriefingKey[1]) {
  throw new Error('Leadership briefing key prefix mismatch');
}

const marketingKey = intelligenceKeys.marketing.campaignPerformance('cmp-1', 'last_30_days');
if (marketingKey[2] !== 'campaign-performance') {
  throw new Error('Marketing campaign performance key mismatch');
}

const insightKey = intelligenceKeys.crossPersona.insights('leadership', 'briefing', 5);
if (insightKey[3]?.persona !== 'leadership') {
  throw new Error('Cross-persona insight key persona mismatch');
}

export default true;
