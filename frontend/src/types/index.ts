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

// Plan Types
export interface Plan {
  id: string;
  analysis_id: string;
  title: string;
  owner: string;
  status: string;
  plan_type: string;
  urgency: string;
  customer_tier: string;
  constraints: string[];
  created_at: string;
  approved_by?: string;
  approved_at?: string;
  executed_by?: string;
  executed_at?: string;
  actions?: PlanAction[];
}

export interface PlanAction {
  id: string;
  description: string;
  persona: string;
  priority: string;
  estimated_duration: number;
}

export interface PlanCreateRequest {
  analysis_id: string;
  plan_type?: string;
  urgency?: string;
  customer_tier?: string;
  constraints?: string[];
  store?: boolean;
}

// Workflow Types
export interface Workflow {
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

// Execution Types
export interface Execution {
  id: string;
  type: string;
  status: string;
  started_at: string;
  completed_at?: string;
  duration_sec?: number;
  logs: string[];
  workflow_id?: string;
  error?: string;
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

// UI State Types
export type TabValue = 
  | 'transcripts' 
  | 'analysis' 
  | 'plan' 
  | 'workflow' 
  | 'execution' 
  | 'dashboard' 
  | 'insights' 
  | 'runs' 
  | 'governance'
  | 'generator';

export type Environment = 'dev' | 'staging' | 'prod';

// Error Types
export interface ApiError {
  detail: string;
  status_code?: number;
}