export interface Transcript {
  transcript_id: string;
  customer_id: string;
  scenario: string;
  message_count: number;
  urgency: 'low' | 'medium' | 'high';
  financial_impact: boolean;
  stored: boolean;
  created_at: string;
}

export interface Analysis {
  analysis_id: string;
  transcript_id: string;
  intent: string;
  sentiment: string;
  urgency: 'low' | 'medium' | 'high';
  confidence: number;
  risk_scores: {
    delinquency: number;
    churn: number;
    complaint: number;
    refinance: number;
  };
}

export interface Action {
  action_id: string;
  description: string;
  risk_score: number;
  approval_route: 'auto' | 'advisor_approval' | 'supervisor_approval' | 'leadership_approval';
  actor: string;
  timeline?: string;
  financial_impact?: boolean;
  compliance_required?: string[];
}

export interface ActionPlan {
  plan_id: string;
  transcript_id: string;
  analysis_id: string;
  total_actions: number;
  routing_summary: {
    auto_approved: number;
    advisor_approval: number;
    supervisor_approval: number;
    leadership_approval?: number;
  };
  layers: {
    borrower_plan: { actions: Action[] };
    advisor_plan: { actions: Action[] };
    supervisor_plan: { actions: Action[] };
    leadership_plan: { actions: Action[] };
  };
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  approval_route: string;
}

export interface GovernanceStatus {
  governance_id: string;
  plan_id: string;
  compliance_status: 'pending' | 'compliant' | 'flagged';
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  routing_decision: string;
  evaluated_actions: number;
  compliant_actions: number;
  flagged_actions: number;
  required_disclosures: string[];
  compliance_concerns: string[];
  confidence_score: number;
}

export interface ApprovalItem {
  approval_id: string;
  action_id: string;
  plan_id: string;
  submitted_by: string;
  status: 'pending_approval' | 'approved' | 'rejected';
  routed_to: 'advisor' | 'supervisor' | 'leadership';
  urgency: 'low' | 'medium' | 'high';
  submitted_at: string;
  estimated_approval_time: string;
}

export interface ExecutionStatus {
  execution_id: string;
  plan_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  actions_executed: number;
  actions_skipped: number;
  artifacts_created: number;
  compliance_events: number;
  started_at?: string;
  completed_at?: string;
}

export interface WorkflowState {
  transcript?: Transcript;
  analysis?: Analysis;
  plan?: ActionPlan;
  governance?: GovernanceStatus;
  approvals?: ApprovalItem[];
  execution?: ExecutionStatus;
  currentStage: 'transcript' | 'analysis' | 'planning' | 'governance' | 'approval' | 'execution' | 'complete';
}

export type StageStatus = 'pending' | 'running' | 'complete' | 'failed';