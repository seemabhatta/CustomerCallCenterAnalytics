import { useState } from 'react';
import type { ApprovalItem, Transcript, Analysis, ActionPlan } from '../types/workflow';

interface ApprovalQueueProps {
  onBack: () => void;
  totalPendingCount: number;
}

interface ApprovalItemExtended extends ApprovalItem {
  transcript: Transcript;
  analysis: Analysis;
  actionPlan: ActionPlan;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  business_impact: 'financial' | 'compliance' | 'retention' | 'standard';
  priority_score: number;
}

export function ApprovalQueue({ onBack, totalPendingCount }: ApprovalQueueProps) {
  const [selectedItem, setSelectedItem] = useState<ApprovalItemExtended | null>(null);
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');

  // Simulated approval items with realistic business context
  const approvalItems: ApprovalItemExtended[] = [
    {
      approval_id: "APR_001",
      action_id: "ACT_PMI_001",
      plan_id: "PLAN_001",
      submitted_by: "advisor_sarah",
      status: "pending_approval",
      routed_to: "supervisor",
      urgency: "high",
      submitted_at: "2025-09-10T14:15:00Z",
      estimated_approval_time: "2025-09-10T16:00:00Z",
      risk_level: "high",
      business_impact: "retention",
      priority_score: 95,
      transcript: {
        transcript_id: "T_20250910_001",
        customer_id: "CUST_5421",
        scenario: "PMI Removal Dispute",
        message_count: 23,
        urgency: "high",
        financial_impact: true,
        stored: true,
        created_at: "2025-09-10T14:00:00Z"
      },
      analysis: {
        analysis_id: "ANA_001",
        transcript_id: "T_20250910_001", 
        intent: "PMI Removal Request",
        sentiment: "frustrated → concerned",
        urgency: "high",
        confidence: 0.95,
        risk_scores: {
          delinquency: 0.34,
          churn: 0.72,
          complaint: 0.81,
          refinance: 0.45
        }
      },
      actionPlan: {
        plan_id: "PLAN_001",
        transcript_id: "T_20250910_001",
        analysis_id: "ANA_001",
        total_actions: 7,
        routing_summary: {
          auto_approved: 2,
          advisor_approval: 2,
          supervisor_approval: 3
        },
        layers: {
          borrower_plan: { actions: [] },
          advisor_plan: { actions: [] },
          supervisor_plan: { actions: [] },
          leadership_plan: { actions: [] }
        },
        risk_level: "high",
        approval_route: "supervisor_approval"
      }
    },
    {
      approval_id: "APR_002",
      action_id: "ACT_REFI_002",
      plan_id: "PLAN_002", 
      submitted_by: "advisor_michael",
      status: "pending_approval",
      routed_to: "supervisor",
      urgency: "medium",
      submitted_at: "2025-09-10T13:30:00Z",
      estimated_approval_time: "2025-09-10T17:00:00Z",
      risk_level: "medium",
      business_impact: "financial",
      priority_score: 78,
      transcript: {
        transcript_id: "T_20250910_002",
        customer_id: "CUST_7892",
        scenario: "Refinancing Inquiry",
        message_count: 15,
        urgency: "medium",
        financial_impact: true,
        stored: true,
        created_at: "2025-09-10T13:15:00Z"
      },
      analysis: {
        analysis_id: "ANA_002",
        transcript_id: "T_20250910_002",
        intent: "Refinance Interest Check",
        sentiment: "neutral → interested",
        urgency: "medium", 
        confidence: 0.87,
        risk_scores: {
          delinquency: 0.12,
          churn: 0.23,
          complaint: 0.08,
          refinance: 0.89
        }
      },
      actionPlan: {
        plan_id: "PLAN_002",
        transcript_id: "T_20250910_002",
        analysis_id: "ANA_002",
        total_actions: 5,
        routing_summary: {
          auto_approved: 3,
          advisor_approval: 1,
          supervisor_approval: 1
        },
        layers: {
          borrower_plan: { actions: [] },
          advisor_plan: { actions: [] },
          supervisor_plan: { actions: [] },
          leadership_plan: { actions: [] }
        },
        risk_level: "medium",
        approval_route: "supervisor_approval"
      }
    }
  ];

  const filteredItems = approvalItems.filter(item => {
    if (filter === 'all') return true;
    return item.risk_level === filter;
  });

  const getUrgencyColor = (urgency: string) => {
    switch (urgency) {
      case 'high': return 'text-red-600 bg-red-50 border-red-200';
      case 'medium': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'low': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  const getBusinessImpactIcon = (impact: string) => {
    switch (impact) {
      case 'financial': return '💰';
      case 'compliance': return '⚖️';
      case 'retention': return '🔒';
      default: return '📋';
    }
  };

  const handleApprove = (item: ApprovalItemExtended) => {
    console.log('Approving item:', item.approval_id);
    // TODO: Call API to approve action
  };

  const handleReject = (item: ApprovalItemExtended) => {
    console.log('Rejecting item:', item.approval_id);
    // TODO: Call API to reject action
  };

  if (selectedItem) {
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => setSelectedItem(null)}
              className="text-blue-600 hover:text-blue-800 flex items-center"
            >
              ← Back to Queue
            </button>
            <h2 className="text-xl font-semibold">Approval Details</h2>
          </div>
          <div className="flex space-x-3">
            <button 
              onClick={() => handleReject(selectedItem)}
              className="px-4 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50"
            >
              ❌ Reject
            </button>
            <button 
              onClick={() => handleApprove(selectedItem)}
              className="modern-button"
            >
              ✅ Approve Plan
            </button>
          </div>
        </div>

        {/* Detailed View */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Transcript Summary */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              📄 Transcript Summary
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Customer:</span>
                <span className="font-medium">{selectedItem.transcript.customer_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Scenario:</span>
                <span className="font-medium">{selectedItem.transcript.scenario}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Duration:</span>
                <span className="font-medium">{selectedItem.transcript.message_count} exchanges</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Financial Impact:</span>
                <span className={selectedItem.transcript.financial_impact ? 'text-red-600 font-medium' : 'text-gray-500'}>
                  {selectedItem.transcript.financial_impact ? 'Yes' : 'No'}
                </span>
              </div>
            </div>
          </div>

          {/* AI Analysis */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              🔍 AI Analysis
            </h3>
            <div className="space-y-4">
              <div>
                <span className="text-gray-600 text-sm">Intent Detection</span>
                <div className="font-medium">{selectedItem.analysis.intent}</div>
                <div className="text-sm text-gray-500">
                  {Math.round(selectedItem.analysis.confidence * 100)}% confidence
                </div>
              </div>
              
              <div>
                <span className="text-gray-600 text-sm">Sentiment Journey</span>
                <div className="font-medium">{selectedItem.analysis.sentiment}</div>
              </div>

              <div>
                <span className="text-gray-600 text-sm">Risk Scores</span>
                <div className="space-y-2 mt-2">
                  <div className="flex justify-between">
                    <span>Churn Risk</span>
                    <span className="font-medium text-red-600">
                      {Math.round(selectedItem.analysis.risk_scores.churn * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Complaint Risk</span>
                    <span className="font-medium text-orange-600">
                      {Math.round(selectedItem.analysis.risk_scores.complaint * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Plan */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              📋 Proposed Actions
            </h3>
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                {selectedItem.actionPlan.total_actions} total actions planned
              </div>

              <div className="space-y-3">
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="font-medium text-green-800">Auto-Approved (2)</div>
                  <div className="text-sm text-green-600">Send PMI review checklist, Update CRM</div>
                </div>

                <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <div className="font-medium text-orange-800">Needs Approval (3)</div>
                  <div className="text-sm text-orange-600 space-y-1">
                    <div>• Schedule expedited appraisal</div>
                    <div>• Proactive retention call within 24hrs</div>
                    <div>• Escalate to PMI review team</div>
                  </div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="font-medium text-red-800">⚠️ Requires Approval</div>
                <div className="text-sm text-red-600 mt-1">
                  High churn risk (72%) + complaint escalation detected
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button 
            onClick={onBack}
            className="text-blue-600 hover:text-blue-800 flex items-center"
          >
            ← Back to Dashboard
          </button>
          <div>
            <h2 className="text-xl font-semibold">Approval Queue</h2>
            <p className="text-sm text-gray-600">{totalPendingCount} items pending review</p>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded-lg text-sm ${filter === 'all' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}
          >
            All ({totalPendingCount})
          </button>
          <button
            onClick={() => setFilter('high')}
            className={`px-3 py-1 rounded-lg text-sm ${filter === 'high' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}
          >
            High Priority (23)
          </button>
          <button
            onClick={() => setFilter('medium')}
            className={`px-3 py-1 rounded-lg text-sm ${filter === 'medium' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-600'}`}
          >
            Medium (156)
          </button>
        </div>
      </div>

      {/* Approval Items List */}
      <div className="space-y-4">
        {filteredItems.map((item) => (
          <div 
            key={item.approval_id}
            className="card hover:shadow-lg cursor-pointer transition-all"
            onClick={() => setSelectedItem(item)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <span className="text-xl">{getBusinessImpactIcon(item.business_impact)}</span>
                  <div>
                    <h3 className="font-semibold">{item.transcript.scenario}</h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>Customer: {item.transcript.customer_id}</span>
                      <span>•</span>
                      <span>Called: {new Date(item.submitted_at).toLocaleTimeString()}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">AI Analysis:</span>
                    <div className="font-medium">{item.analysis.intent}</div>
                    <div className="text-gray-500">Confidence: {Math.round(item.analysis.confidence * 100)}%</div>
                  </div>
                  
                  <div>
                    <span className="text-gray-500">Risk Profile:</span>
                    <div className="font-medium">Churn: {Math.round(item.analysis.risk_scores.churn * 100)}%</div>
                    <div className="font-medium">Complaint: {Math.round(item.analysis.risk_scores.complaint * 100)}%</div>
                  </div>

                  <div>
                    <span className="text-gray-500">Proposed Actions:</span>
                    <div className="font-medium">{item.actionPlan.total_actions} total actions</div>
                    <div className="text-orange-600">{item.actionPlan.routing_summary.supervisor_approval} need approval</div>
                  </div>
                </div>

                <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded text-sm">
                  <span className="font-medium text-orange-800">⚠️ Requires Approval: </span>
                  <span className="text-orange-700">
                    {item.risk_level === 'high' ? 'High churn risk + complaint escalation detected' : 
                     item.business_impact === 'financial' ? 'Financial impact requires supervisor review' :
                     'Standard approval workflow'}
                  </span>
                </div>
              </div>

              <div className="flex flex-col items-end space-y-2 ml-6">
                <div className={`px-2 py-1 rounded-full text-xs font-medium border ${getUrgencyColor(item.urgency)}`}>
                  {item.urgency.toUpperCase()}
                </div>
                <div className="text-xs text-gray-500">
                  Score: {item.priority_score}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredItems.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500">No approval items match the current filter</div>
        </div>
      )}
    </div>
  );
}