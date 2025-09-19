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
  | 'actions';

export type Environment = 'dev' | 'staging' | 'prod';

// User Role Types
export type UserRole = 'leadership' | 'supervisor' | 'advisor' | 'admin';

// Leadership Chat Types
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

// Error Types
export interface ApiError {
  detail: string;
  status_code?: number;
}
