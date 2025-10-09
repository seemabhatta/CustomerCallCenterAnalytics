// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
}

// Transcript Types
export interface Transcript {
  id: string;
  customer_id: string;
  customer: string;
  advisor: string;
  topic: string;
  urgency: string;
  financial_impact: boolean;
  customer_sentiment: string;
  created_at: string;
  started_at?: string;
  duration_sec?: number;
  message_count?: number;
  status: string;
  messages?: TranscriptMessage[];
}

export interface TranscriptMessage {
  t: number;
  speaker: string;
  text: string;
}

export interface TranscriptCreateRequest {
  topic?: string;
  urgency?: string;
  financial_impact?: boolean;
  customer_sentiment?: string;
  customer_id?: string;
  store?: boolean;
}

export interface TranscriptListResponse {
  transcripts: Transcript[];
  metadata: {
    requested: number;
    returned: number;
    total_available: number;
    completeness: 'complete' | 'partial';
  };
}

// Analysis Types
export interface Analysis {
  id: string;
  transcript_id: string;
  summary: string;
  high: number;
  medium: number;
  low: number;
  status: string;
  analysis_type: string;
  urgency: string;
  customer_tier: string;
  created_at: string;
  risk_items?: RiskItem[];
}

export interface RiskItem {
  id: string;
  risk_level: string;
  category: string;
  description: string;
  impact_score: number;
  persona: string;
}

export interface AnalysisCreateRequest {
  transcript_id: string;
  analysis_type?: string;
  urgency?: string;
  customer_tier?: string;
  store?: boolean;
}

// Plan Types - Updated to match actual API response
export interface Plan {
  // Core identifiers
  plan_id: string;
  analysis_id: string;
  transcript_id: string;
  generator_version: string;
  
  // Status and routing
  risk_level: string | null;
  approval_route: string | null;
  queue_status: string | null;
  auto_executable: number;
  routing_reason: string | null;
  
  // Timestamps
  created_at: string;
  approved_at: string | null;
  approved_by: string | null;
  
  // Four-layer plan structure
  borrower_plan: BorrowerPlan;
  advisor_plan: AdvisorPlan;
  supervisor_plan: SupervisorPlan;
  leadership_plan: LeadershipPlan;
}

export interface BorrowerPlan {
  immediate_actions: PlanAction[];
  follow_ups: FollowUpAction[];
  personalized_offers: string[];
  risk_mitigation: string[];
}

export interface AdvisorPlan {
  coaching_items: CoachingItem[];
  performance_feedback: PerformanceFeedback;
  training_recommendations: string[];
  next_actions: string[];
}

export interface SupervisorPlan {
  escalation_items: EscalationItem[];
  team_patterns: string[];
  compliance_review: string[];
  approval_required: boolean;
  process_improvements: string[];
}

export interface LeadershipPlan {
  portfolio_insights: string[];
  strategic_opportunities: string[];
  risk_indicators: string[];
  trend_analysis: string[];
  resource_allocation: string[];
}

export interface PlanAction {
  action: string;
  timeline: string;
  priority: string;
  auto_executable: boolean;
  description: string;
}

export interface FollowUpAction {
  action: string;
  due_date: string;
  owner: string;
  trigger_condition: string;
}

export interface CoachingItem {
  action: string;
  coaching_point: string;
  expected_improvement: string;
  priority: string;
}

export interface PerformanceFeedback {
  strengths: string[];
  improvements: string[];
  score_explanations: string[];
}

export interface EscalationItem {
  item: string;
  reason: string;
  priority: string;
  action_required: string;
}

export interface PlanCreateRequest {
  analysis_id: string;
  plan_type?: string;
  urgency?: string;
  customer_tier?: string;
  constraints?: string[];
  store?: boolean;
}

// Workflow Types (Updated to match comprehensive API contract)
export interface Workflow {
  // Core Identifiers
  id: string;                      // Unique workflow ID (e.g., "WF_123_456")
  plan_id: string;                 // Associated action plan ID
  analysis_id: string;             // Associated analysis ID
  transcript_id: string;           // Associated transcript ID

  // Workflow Classification
  workflow_type: "BORROWER" | "ADVISOR" | "SUPERVISOR" | "LEADERSHIP";

  // Workflow Content
  workflow_data: {
    actions: string[];              // List of actions to take
    priority: string;               // Priority level
    estimated_time?: string;        // Time estimate
    dependencies?: string[];        // Other workflow dependencies
  };

  // Risk Assessment (LLM Agent Decisions)
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  status: "PENDING_ASSESSMENT" | "AWAITING_APPROVAL" | "AUTO_APPROVED" | "REJECTED" | "EXECUTED";

  // Context & Reasoning
  context_data: {
    customer_risk_score?: number;
    delinquency_days?: number;
    full_transcript?: string;
    analysis_results?: object;
    [key: string]: any;             // Additional context
  };
  risk_reasoning: string | null;
  approval_reasoning: string | null;

  // Approval Workflow
  requires_human_approval: boolean;
  assigned_approver: string | null;
  approved_by: string | null;
  approved_at: string | null;       // ISO 8601 timestamp
  rejected_by: string | null;
  rejected_at: string | null;       // ISO 8601 timestamp
  rejection_reason: string | null;

  // Execution Tracking
  executed_at: string | null;       // ISO 8601 timestamp
  execution_results: object | null;

  // Timestamps
  created_at: string;               // ISO 8601 timestamp
  updated_at: string;               // ISO 8601 timestamp
}

// Granular Workflow Types (New extract-all endpoint format)
export interface GranularWorkflow {
  // Core Identifiers
  id: string;                      // Unique workflow ID
  plan_id: string;                 // Associated action plan ID
  analysis_id: string;             // Associated analysis ID
  transcript_id: string;           // Associated transcript ID

  // Granular Action Details (Key differentiator from meta-workflow)
  action_item: string;             // Specific action to be taken (e.g., "Escalate PMI removal request")
  description: string;             // Detailed description of what to do
  priority: "high" | "medium" | "low"; // Priority level
  timeline: string;                // When to complete (e.g., "Within 24 hours")
  
  // Workflow Classification
  workflow_type: "BORROWER" | "ADVISOR" | "SUPERVISOR" | "LEADERSHIP";

  // Optional Execution Details
  steps?: string[];                // Specific execution steps
  dependencies?: string[];         // Prerequisites or dependencies
  assigned_to?: string;           // Who should execute this
  estimated_duration?: string;    // How long it should take

  // Risk Assessment
  risk_level: "LOW" | "MEDIUM" | "HIGH";
  risk_reasoning?: string;         // Risk assessment for this specific action
  
  // Status & Approval
  status: "PENDING_ASSESSMENT" | "AWAITING_APPROVAL" | "AUTO_APPROVED" | "REJECTED" | "EXECUTED";
  requires_human_approval: boolean;
  approved_by?: string | null;
  approved_at?: string | null;
  
  // Timestamps
  created_at: string;
  updated_at: string;
}

// Workflow Response from API
export interface WorkflowResponse {
  workflows: Workflow[];
}

// Workflow Filter Parameters
export interface WorkflowFilterParams {
  status?: "PENDING_ASSESSMENT" | "AWAITING_APPROVAL" | "AUTO_APPROVED" | "REJECTED" | "EXECUTED";
  risk_level?: "LOW" | "MEDIUM" | "HIGH";
  limit?: number;
}

export interface WorkflowApprovalRequest {
  approved_by: string;
  reasoning?: string;
}

export interface WorkflowRejectionRequest {
  rejected_by: string;
  reason: string;
}

export interface WorkflowExecutionRequest {
  executed_by: string;
}

// Execution Types (Updated to match API contract)
export interface Execution {
  id: string;
  workflow_id: string;
  executor_type: string;
  execution_status: string;
  execution_payload: Record<string, any>;
  executed_at: string;
  executed_by: string;
  execution_duration_ms: number;
  mock_execution: boolean;
  error_message: string | null;
  metadata: Record<string, any>;
  created_at: string;
}

export interface ExecutionDetails {
  execution_record: Execution;
  audit_trail: Array<{
    id: number;
    execution_id: string;
    event_type: string;
    event_description: string;
    event_timestamp: string;
    event_data: Record<string, any> | null;
  }>;
  retrieved_at: string;
}

// Forecast Types
export interface ForecastPrediction {
  date: string;
  predicted: number;
  lower_bound: number;
  upper_bound: number;
  confidence_interval: number;
}

export interface ForecastSummary {
  average_predicted: number;
  min_predicted: number;
  max_predicted: number;
  total_periods: number;
  prediction_start: string;
  prediction_end: string;
}

export interface ForecastMetadata {
  model_type?: string;
  seasonality_mode?: string;
  growth?: string;
  forecast_type?: string;
  granularity?: string;
  data_points_used?: number;
  training_start?: string;
  training_end?: string;
  [key: string]: any;
}

export type ForecastComponents = Record<string, any>;

export interface ForecastResult {
  forecast_id?: string;
  forecast_type: string;
  cached?: boolean;
  generated_at?: string;
  expires_at?: string | null;
  summary: ForecastSummary;
  predictions: ForecastPrediction[];
  metadata: ForecastMetadata;
  components?: ForecastComponents;
}

export interface ForecastTypeSummary {
  type: string;
  description: string;
  granularity: string;
  min_data_days: number;
  default_horizon_days: number;
}

export interface ForecastTypeInfo extends ForecastTypeSummary {
  model_type: string;
  prophet_config: Record<string, any>;
}

export interface ForecastGenerateRequest {
  forecast_type: string;
  horizon_days?: number;
  start_date?: string;
  end_date?: string;
  use_cache?: boolean;
  ttl_hours?: number;
}

export interface ForecastReadiness {
  forecast_type: string;
  ready: boolean;
  days_of_data: number;
  min_required: number;
  recommendation: string;
  earliest_date?: string | null;
  latest_date?: string | null;
}

export interface ForecastReadinessOverview {
  total_types: number;
  ready_types: number;
  not_ready_types: number;
  overall_status: 'ready' | 'not_ready';
  by_type: Record<string, ForecastReadiness>;
}

export type ForecastReadinessResponse = ForecastReadiness | ForecastReadinessOverview;

export interface ForecastDataSummary {
  transcripts: {
    total: number;
    earliest_date: string | null;
    latest_date: string | null;
    unique_days: number;
  };
  analyses: {
    total: number;
    unique_intents: number;
    avg_delinquency_risk: number;
    avg_churn_risk: number;
  };
  top_intents: Record<string, number>;
}

export interface ForecastStatistics {
  total_forecasts: number;
  active_by_type: Record<string, number>;
  average_mae?: number | null;
  average_mape?: number | null;
  most_accessed: Array<{
    id: string;
    forecast_type: string;
    access_count: number;
  }>;
}

export interface ForecastHistoryItem {
  forecast_id: string;
  forecast_type: string;
  generated_at: string;
  expires_at?: string | null;
  summary?: ForecastSummary;
}

// Dashboard & Metrics Types
export interface DashboardMetrics {
  transcripts: {
    total: number;
    today: number;
    pending: number;
  };
  analyses: {
    total: number;
    high_risk: number;
    completed: number;
  };
  plans: {
    total: number;
    approved: number;
    executed: number;
  };
  workflows: {
    total: number;
    pending_approval: number;
    approved: number;
    executed: number;
    failed: number;
  };
}

export interface StageDuration {
  stage: string;
  seconds: number;
}

export interface RiskByPersona {
  persona: string;
  HIGH: number;
  MEDIUM: number;
  LOW: number;
}

export interface RunData {
  id: string;
  started_at: string;
  durations: StageDuration[];
  funnel: {
    generated: number;
    approved: number;
    executed: number;
    failed: number;
  };
}

export interface LiveEvent {
  t: string;
  msg: string;
  type: 'info' | 'success' | 'warn' | 'error';
}

// Insights Types
export interface RiskPattern {
  pattern: string;
  frequency: number;
  risk_score: number;
  affected_customers: string[];
  common_themes: string[];
}

export interface CustomerRecommendation {
  customer_id: string;
  recommendations: string[];
  risk_factors: string[];
  priority: string;
}

export interface InsightsData {
  borrower_pain: string[];
  advisor_coaching: string[];
  compliance_alerts: string[];
}

// Approval Types
export interface ApprovalChip {
  role: string;
  status: 'APPROVED' | 'PENDING' | 'REJECTED';
}

export interface ApprovalRequest {
  approved_by: string;
  approved_at?: string;
  notes?: string;
}

// Generic Types
export interface SearchParams {
  customer?: string;
  topic?: string;
  text?: string;
}

export interface ListParams {
  limit?: number;
  offset?: number;
}

export interface FilterParams {
  status?: string;
  risk_level?: string;
  workflow_type?: string;
}

// Legacy workflow types for backward compatibility
export interface LegacyWorkflow {
  id: string;
  plan_id: string;
  persona: string;
  risk: string;
  status: string;
  action: string;
  workflow_type: string;
  risk_level: string;
  created_at: string;
  approved_by?: string;
  approved_at?: string;
  rejected_by?: string;
  rejection_reason?: string;
  executed_by?: string;
  executed_at?: string;
}

// Orchestration Types
export interface OrchestrationRun {
  id: string;                          // RUN_XXXXX
  transcript_ids: string[];            // Array of transcripts being processed
  auto_approve: boolean;               // Whether workflows auto-approve
  status: 'STARTED' | 'RUNNING' | 'COMPLETED' | 'FAILED';
  stage: string;                       // Current stage or "COMPLETE"
  started_at: string;                  // ISO timestamp
  completed_at?: string;               // ISO timestamp when done
  results: OrchestrationResult[];      // Results per transcript
  errors: OrchestrationError[];        // Any errors encountered
  summary?: {
    total_transcripts: number;
    successful: number;
    failed: number;
    success_rate: number;
  };
  // Real-time status fields from our granular updates
  analysis_id?: string;                // When analysis completes
  plan_id?: string;                    // When plan completes
  workflow_count?: number;             // When workflows generated
  executed_count?: number;             // Successful executions
  failed_count?: number;               // Failed executions
}

export interface OrchestrationResult {
  transcript_id: string;
  analysis_id: string;
  plan_id: string;
  workflow_count: number;
  approved_count: number;
  executed_count: number;
  failed_count: number;
  execution_results: any[];
  stage: string;
  success: boolean;
  partial_success?: boolean;
}

export interface OrchestrationError {
  transcript_id: string;
  error: string;
  timestamp: string;
}

export interface OrchestrationRunRequest {
  transcript_ids: string[];
  auto_approve?: boolean;
}

export interface OrchestrationRunResponse {
  run_id: string;
  status: string;
  message: string;
}

export type PipelineStage =
  | 'PROCESSING'
  | 'ANALYSIS_COMPLETED'
  | 'PLAN_COMPLETED'
  | 'WORKFLOWS_COMPLETED'
  | 'EXECUTION_COMPLETED'
  | 'COMPLETE';

// UI State Types
export type TabValue =
  | 'analytics'
  | 'control-tower'
  | 'servicing-intel'
  | 'marketing-intel'
  | 'transcripts'
  | 'analysis'
  | 'plan'
  | 'workflow'
  | 'execution'
  | 'governance'
  | 'generator'
  | 'pipeline'
  | 'insights'
  | 'dashboard'
  | 'approvals'
  | 'reviews'
  | 'monitoring'
  | 'calls'
  | 'actions'
  | 'advisor-chat';

export type Environment = 'dev' | 'staging' | 'prod';

// User Role Types
export type UserRole = 'leadership' | 'supervisor' | 'advisor' | 'admin';

// Unified Chat Types
export type ChatRole = 'leadership' | 'advisor';
export type AgentMode = 'borrower' | 'selfreflection';

export interface UnifiedChatRequest {
  role: ChatRole;
  user_id: string;
  message: string;
  session_id?: string;
  agent_mode?: AgentMode;
  context?: {
    transcript_id?: string;
    plan_id?: string;
    analysis_id?: string;
    workflow_id?: string;
  };
}

export interface UnifiedChatResponse {
  content: string;
  session_id: string;
  role: ChatRole;
  agent_mode?: AgentMode;
  actions?: any[];
  metadata?: {
    processing_time_ms?: number;
    confidence?: number;
    data_sources_used?: string[];
    query_understanding?: any;
  };
  // Leadership-specific fields
  executive_summary?: string;
  key_metrics?: any[];
  recommendations?: string[];
  supporting_data?: Record<string, any>;
  // Additional context
  context?: Record<string, any>;
}

// Legacy types for backward compatibility
export interface LeadershipChatRequest {
  query: string;
  executive_id: string;
  executive_role?: string;
  session_id?: string;
}

export interface LeadershipChatResponse {
  content: string;
  executive_summary: string;
  key_metrics: any[];
  recommendations: string[];
  supporting_data: Record<string, any>;
  session_id: string;
  cache_hit: boolean;
  metadata: {
    query_understanding: any;
    total_processing_time_ms: number;
    overall_confidence: number;
    data_sources_used: string[];
    records_analyzed: number;
    response_timestamp: string;
  };
}

export interface AdvisorChatRequest {
  advisor_id: string;
  message: string;
  role?: string; // Role parameter for unified endpoint ("advisor", "leadership", etc.)
  session_id?: string;
  transcript_id?: string;
  plan_id?: string;
}

export interface AdvisorChatResponse {
  response: string;
  session_id: string;
  actions?: any[];
  context?: Record<string, any>;
}

// Configuration Types
export interface QuickAction {
  icon: string;
  label: string;
  message: string;
}

export interface ConfigMode {
  prompt_file: string;
  description: string;
  icon: string;
  quick_actions?: QuickAction[];
}

export interface ConfigRole {
  display_name: string;
  description: string;
  modes: Record<string, ConfigMode>;
}

export interface ConfigSettings {
  default_mode: string;
  default_model: string;
  models?: {
    default: string;
    fallback: string;
  };
  validation?: {
    require_prompt_files: boolean;
    fail_on_missing_prompt: boolean;
  };
  ui?: {
    show_future_roles: boolean;
    show_mode_descriptions: boolean;
  };
}

export interface SystemConfiguration {
  roles: Record<string, ConfigRole>;
  settings: ConfigSettings;
  ui: ConfigSettings['ui'];
  metadata: {
    version: string;
    last_updated: string;
    description: string;
  };
}

// Intelligence Types
export type PortfolioHealthStatus = 'STABLE' | 'ATTENTION' | 'CRITICAL' | (string & {});

export interface LeadershipUrgentItem {
  title: string;
  urgency: 'high' | 'medium' | 'low' | (string & {});
  financial_impact: number;
  description: string;
  recommendation: string;
}

export interface LeadershipRecommendation {
  action: string;
  expected_roi: number;
  timeline: 'immediate' | 'this_week' | 'this_month' | (string & {});
  confidence: 'high' | 'medium' | 'low' | (string & {});
  reasoning: string;
}

export interface LeadershipFinancialSummary {
  total_at_risk: number;
  delinquency_risk: number;
  churn_risk: number;
  compliance_risk: number;
  recoverable_with_action: number;
  net_impact: number;
}

export interface LeadershipBriefing {
  portfolio_health: PortfolioHealthStatus;
  health_summary: string;
  urgent_items: LeadershipUrgentItem[];
  financial_summary: LeadershipFinancialSummary;
  recommendations: LeadershipRecommendation[];
  generated_at: string;
  _generated_at?: string;
  _cached?: boolean;
}

export interface LeadershipDollarImpact {
  total_at_risk: number;
  by_category: Record<string, number>;
  portfolio_value: number;
  high_risk_customers: number;
  trend: string;
  trend_delta_pct?: number | null;
  recent_delinquency_avg?: number | null;
  previous_delinquency_avg?: number | null;
  generated_at: string;
}

export interface LeadershipDecisionQueueItem {
  id: string;
  type: string;
  workflow_type?: string;
  waiting_since?: string;
  risk_level?: string;
  urgency: 'high' | 'medium' | 'low' | (string & {});
  title?: string;
  recommendation?: string;
  expected_impact?: number;
  cost_estimate?: number;
  roi?: number;
}

export interface LeadershipDecisionQueue {
  count: number;
  urgent_count: number;
  decisions: LeadershipDecisionQueueItem[];
  generated_at: string;
}

export interface LeadershipWaterfallStage {
  label: string;
  value: number;
  color?: string;
}

export interface LeadershipRiskWaterfall {
  starting_portfolio: number;
  at_risk: number;
  recoverable_with_action: number;
  net_risk: number;
  stages: LeadershipWaterfallStage[];
  generated_at: string;
}

export interface QueueBreakdown {
  high_priority: number;
  standard: number;
  callback_scheduled: number;
  [key: string]: number;
}

export interface PredictedVolumePoint {
  hour: string;
  predicted_calls: number;
  confidence?: [number, number] | { lower: number; upper: number } | null;
}

export interface QueueStatusResponse {
  current_queue: QueueBreakdown;
  predicted_volume: PredictedVolumePoint[];
  current_capacity: number;
  staffing_status: string;
  staffing_gap?: number;
  generated_at: string;
}

export interface SlaPerformanceMetrics {
  fcr_rate: number;
  fcr_target: number;
  fcr_status: string;
  escalation_rate: number;
  escalation_target: number;
  escalation_status: string;
  compliance_score: number;
}

export interface SlaMonitorResponse {
  current_performance: SlaPerformanceMetrics;
  predictions: Record<string, any>;
  generated_at: string;
}

export interface AdvisorHeatmapEntry {
  advisor_id?: string;
  advisor_name?: string;
  empathy_score: number;
  compliance_score: number;
  fcr_rate: number;
  status: 'green' | 'yellow' | 'red' | (string & {});
  segment?: string;
}

export interface AdvisorHeatmapResponse {
  advisors: AdvisorHeatmapEntry[];
  summary: {
    total_advisors: number;
    green_status: number;
    yellow_status: number;
    red_status: number;
  };
  generated_at: string;
}

export interface CoachingAlert {
  id?: string;
  title?: string;
  type: string;
  urgency: 'high' | 'medium' | 'low' | (string & {});
  advisor_id?: string;
  recommendation?: string;
  expected_impact?: number;
}

export interface CoachingAlertsResponse {
  critical_alerts: CoachingAlert[];
  team_summary: {
    total_advisors: number;
    advisors_needing_coaching: number;
    avg_empathy_score: number;
    avg_compliance_score: number;
    team_health: string;
  };
  generated_at: string;
}

export interface WorkloadBalanceResponse {
  current_staff: number;
  needed_for_peak: number;
  gap: number;
  recommendation: string;
  peak_hour: number;
  generated_at: string;
}

export interface CaseResolutionSummary {
  total_active_cases: number;
  resolved_last_7_days: number;
  avg_case_age_days: number;
  total_resolved_cases: number;
}

export interface CaseResolutionCase {
  analysis_id: string;
  transcript_id: string;
  topic: string;
  delinquency_risk: number;
  churn_risk: number;
  opened_at: string | null;
  age_days: number | null;
}

export interface CaseResolutionResponse {
  message: string;
  summary: CaseResolutionSummary;
  urgent_cases: CaseResolutionCase[];
  generated_at: string;
}

export interface MarketingSegment {
  segment_name: string;
  segment_id: string;
  count: number;
  profile: string;
  avg_score?: number;
  satisfaction_rate?: number;
  opportunity: string;
  opportunity_value: number;
  engagement_strategy?: string;
  expected_response_rate?: number;
  priority: 'high' | 'medium' | 'low' | (string & {});
}

export interface MarketingSegmentsResponse {
  segments: MarketingSegment[];
  summary: {
    total_segments: number;
    high_priority_segments: number;
    total_opportunity_value: number;
  };
  generated_at: string;
}

export interface MarketingCampaign {
  id: string;
  title: string;
  type: string;
  urgency: 'high' | 'medium' | 'low' | (string & {});
  target_segment: string;
  target_count: number;
  campaign_cost: number;
  expected_revenue: number;
  roi: number;
  recommendation: string;
  expected_retention_rate?: number;
  expected_save?: number;
}

export interface CampaignRecommendationsResponse {
  campaigns: MarketingCampaign[];
  summary: {
    total_campaigns: number;
    high_priority: number;
    total_potential_revenue: number;
    total_cost: number;
    avg_roi: number;
  };
  generated_at: string;
}

export interface CampaignPerformanceResponse {
  campaign_id?: string | null;
  segment: string | null;
  date_range: string;
  touchpoints: number;
  resolved_cases: number;
  open_cases: number;
  conversion_rate: number;
  avg_churn_risk: number;
  avg_delinquency_risk: number;
  avg_compliance_score: number;
  sentiment_index: number;
  opportunity_value?: number | null;
  message: string;
  generated_at: string;
}

export interface ChurnRootCause {
  cause: string;
  impact: 'high' | 'medium' | 'low' | (string & {});
  evidence: string;
}

export interface ChurnTargetSegment {
  segment_name: string;
  count: number;
  characteristics: string[];
  risk_drivers: string[];
}

export interface RetentionStrategy {
  strategy: string;
  target_segment: string;
  approach: string;
  messaging: string[];
  channels: string[];
  timing: 'immediate' | 'this_week' | 'this_month' | (string & {});
  expected_retention_rate: number;
  cost_per_contact: number;
  roi_estimate: number;
}

export interface ChurnAnalysisResponse {
  forecast: Record<string, any>;
  insights: {
    churn_summary?: {
      current_rate?: number;
      trend?: string;
      high_risk_count?: number;
      revenue_at_risk?: number;
    };
    root_causes?: ChurnRootCause[];
    target_segments?: ChurnTargetSegment[];
    retention_strategies?: RetentionStrategy[];
    financial_impact?: Record<string, number>;
    confidence?: string;
  };
  at_risk_segment?: MarketingSegment | null;
  generated_at: string;
}

export interface MessageOptimizerResponse {
  segment: string;
  message: string;
  optimized_message: string;
  suggestions: string[];
  generated_at: string;
}

export interface JourneyStage {
  stage: string;
  count: number;
  conversion_rate: number;
  description: string;
}

export interface CustomerJourneyResponse {
  message: string;
  stages: JourneyStage[];
  top_intents: string;
  generated_at: string;
}

export interface RoiAttributionResponse {
  total_opportunity_value: number;
  by_category: Record<string, number>;
  generated_at: string;
}

export interface IntelligenceAskRequest {
  question: string;
  persona?: string;
  context?: Record<string, any>;
}

export interface IntelligenceAskResponse {
  question: string;
  persona?: string;
  answer: string;
  generated_at: string;
  [key: string]: any;
}

export interface CachedInsightSummary {
  id: string;
  insight_type: string;
  persona: string;
  generated_at: string;
  expires_at: string;
  access_count: number;
  confidence_score: number | null;
}

export interface ClearCacheParams {
  persona?: string;
  insightType?: string;
}

export interface ClearCacheResponse {
  message: string;
  cleared_count: number;
}

export interface IntelligenceHealth {
  status: 'healthy' | 'unhealthy' | (string & {});
  cache_statistics?: Record<string, any>;
  services?: Record<string, string>;
  checked_at: string;
  error?: string;
}

export interface CampaignPerformanceRequest {
  campaign_id?: string;
  date_range?: string;
}

export interface MessageOptimizerRequest {
  message: string;
  segment?: string;
}

// Error Types
export interface ApiError {
  detail: string;
  status_code?: number;
}
