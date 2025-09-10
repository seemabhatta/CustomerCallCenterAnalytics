import { useState, useEffect } from 'react';
import { useApprovalData, getTranscriptDetail, type ApprovalItem, type TranscriptDetail } from '../hooks/useApprovalData';

interface ApprovalQueueProps {
  onBack: () => void;
  totalPendingCount: number;
}

interface SimulatedAnalysis {
  intent: string;
  sentiment: string;
  confidence: number;
  risk_scores: {
    delinquency: number;
    churn: number;
    complaint: number;
    refinance: number;
  };
}

interface SimulatedActionPlan {
  total_actions: number;
  auto_approved: number;
  manually_approved: number;
  pending_approval: number;
  approval_reason: string;
}

export function ApprovalQueue({ onBack, totalPendingCount }: ApprovalQueueProps) {
  const [selectedItem, setSelectedItem] = useState<ApprovalItem | null>(null);
  const [selectedTranscript, setSelectedTranscript] = useState<TranscriptDetail | null>(null);
  const [simulatedAnalysis, setSimulatedAnalysis] = useState<SimulatedAnalysis | null>(null);
  const [simulatedActionPlan, setSimulatedActionPlan] = useState<SimulatedActionPlan | null>(null);
  const [filter, setFilter] = useState<'all' | 'high' | 'medium' | 'low'>('all');
  const [loadingDetail, setLoadingDetail] = useState(false);
  
  const { approvalItems, loading, error } = useApprovalData();

  // Generate simulated analysis and action plan data
  const generateSimulatedData = (item: ApprovalItem): { analysis: SimulatedAnalysis; actionPlan: SimulatedActionPlan } => {
    // Simulate analysis based on transcript characteristics
    let intent = "General Inquiry";
    let sentiment = "neutral";
    
    if (item.scenario.toLowerCase().includes('pmi')) {
      intent = "PMI Removal Request";
      sentiment = item.urgency === 'high' ? "frustrated → concerned" : "neutral → interested";
    } else if (item.scenario.toLowerCase().includes('payment')) {
      intent = "Payment Assistance";
      sentiment = item.financial_impact ? "stressed → hopeful" : "neutral";
    } else if (item.scenario.toLowerCase().includes('refinanc')) {
      intent = "Refinance Interest Check";
      sentiment = "neutral → interested";
    }
    
    const analysis: SimulatedAnalysis = {
      intent,
      sentiment,
      confidence: 0.85 + Math.random() * 0.1,
      risk_scores: {
        delinquency: item.financial_impact ? 0.3 + Math.random() * 0.4 : Math.random() * 0.3,
        churn: item.risk_level === 'critical' ? 0.6 + Math.random() * 0.3 : Math.random() * 0.5,
        complaint: item.urgency === 'high' ? 0.5 + Math.random() * 0.4 : Math.random() * 0.4,
        refinance: Math.random() * 0.6
      }
    };
    
    let approval_reason = "Standard workflow approval required";
    if (item.risk_level === 'critical') {
      approval_reason = "Critical risk level requires supervisor approval";
    } else if (item.financial_impact) {
      approval_reason = "Financial impact requires supervisor review";
    } else if (item.urgency === 'high') {
      approval_reason = "High urgency requires expedited approval";
    }
    
    const actionPlan: SimulatedActionPlan = {
      total_actions: item.auto_approved + item.manually_approved + item.pending_actions,
      auto_approved: item.auto_approved,
      manually_approved: item.manually_approved,
      pending_approval: item.pending_actions,
      approval_reason
    };
    
    return { analysis, actionPlan };
  };

  const handleItemClick = async (item: ApprovalItem) => {
    setLoadingDetail(true);
    try {
      // Get full transcript details
      const transcript = await getTranscriptDetail(item.transcript_id);
      
      // Generate simulated analysis and action plan
      const { analysis, actionPlan } = generateSimulatedData(item);
      
      setSelectedItem(item);
      setSelectedTranscript(transcript);
      setSimulatedAnalysis(analysis);
      setSimulatedActionPlan(actionPlan);
    } catch (error) {
      console.error('Error loading transcript details:', error);
      alert('Failed to load transcript details');
    } finally {
      setLoadingDetail(false);
    }
  };

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

  const handleApprove = (item: ApprovalItem) => {
    console.log('Approving item:', item.transcript_id);
    // TODO: Call API to approve action
  };

  const handleReject = (item: ApprovalItem) => {
    console.log('Rejecting item:', item.transcript_id);
    // TODO: Call API to reject action
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-gray-500">Loading approval queue...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-red-500">Error loading approvals: {error}</div>
      </div>
    );
  }

  if (selectedItem && selectedTranscript && simulatedAnalysis && simulatedActionPlan) {
    const scenarioName = selectedItem.scenario === 'Unknown scenario' 
      ? `Customer Service Case #${approvalItems.findIndex(item => item.transcript_id === selectedItem.transcript_id) + 1}`
      : selectedItem.scenario;
      
    return (
      <div className="space-y-6">
        {/* Breadcrumbs */}
        <div className="flex items-center space-x-2 text-sm text-gray-500">
          <button
            onClick={onBack}
            className="hover:text-blue-600 transition-colors"
          >
            Dashboard
          </button>
          <span>›</span>
          <button
            onClick={() => {
              setSelectedItem(null);
              setSelectedTranscript(null);
              setSimulatedAnalysis(null);
              setSimulatedActionPlan(null);
            }}
            className="hover:text-blue-600 transition-colors"
          >
            Approval Queue
          </button>
          <span>›</span>
          <span className="text-gray-900 font-medium">{scenarioName}</span>
        </div>

        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
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
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              📄 Transcript Details
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Customer:</span>
                <span className="font-medium">{selectedTranscript.customer_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Scenario:</span>
                <span className="font-medium">{selectedTranscript.scenario === 'Unknown scenario' ? scenarioName : selectedTranscript.scenario}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Messages:</span>
                <span className="font-medium">{selectedTranscript.message_count} exchanges</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Financial Impact:</span>
                <span className={selectedTranscript.financial_impact ? 'text-red-600 font-medium' : 'text-gray-500'}>
                  {selectedTranscript.financial_impact ? 'Yes' : 'No'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Created:</span>
                <span className="text-sm text-gray-500">
                  {new Date(selectedTranscript.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
            
            {/* Show conversation preview */}
            <div className="mt-4 p-3 bg-gray-50 rounded-lg max-h-64 overflow-y-auto">
              <div className="text-sm font-medium text-gray-700 mb-3">Full Conversation:</div>
              {selectedTranscript.messages.map((msg, idx) => {
                // Clean up role names by removing asterisks
                const cleanRole = msg.role.replace(/\*\*/g, '').trim();
                return (
                  <div key={idx} className="mb-3 text-sm">
                    <div className="font-medium text-blue-600">{cleanRole}:</div>
                    <div className="text-gray-700 ml-2 mt-1">{msg.content}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* AI Analysis */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              🔍 AI Analysis
            </h3>
            <div className="space-y-4">
              <div className="p-3 bg-blue-50 rounded-lg">
                <span className="text-blue-600 text-sm font-medium">Intent Detection</span>
                <div className="font-semibold text-gray-900 mt-1">{simulatedAnalysis.intent}</div>
                <div className="text-sm text-blue-600 mt-1">
                  {Math.round(simulatedAnalysis.confidence * 100)}% confidence
                </div>
              </div>
              
              <div className="p-3 bg-green-50 rounded-lg">
                <span className="text-green-600 text-sm font-medium">Sentiment Journey</span>
                <div className="font-semibold text-gray-900 mt-1">{simulatedAnalysis.sentiment}</div>
              </div>

              <div className="p-3 bg-orange-50 rounded-lg">
                <span className="text-orange-600 text-sm font-medium">Risk Assessment</span>
                <div className="space-y-2 mt-2">
                  <div className="flex justify-between">
                    <span className="text-sm">Churn Risk</span>
                    <span className="font-semibold text-red-600">
                      {Math.round(simulatedAnalysis.risk_scores.churn * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Complaint Risk</span>
                    <span className="font-semibold text-orange-600">
                      {Math.round(simulatedAnalysis.risk_scores.complaint * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm">Delinquency Risk</span>
                    <span className="font-semibold text-yellow-600">
                      {Math.round(simulatedAnalysis.risk_scores.delinquency * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Plan */}
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              📋 Action Plan
            </h3>
            <div className="space-y-4">
              <div className="text-sm text-gray-600 text-center p-2 bg-gray-50 rounded">
                <span className="font-semibold text-gray-900">{simulatedActionPlan.total_actions}</span> total actions planned
              </div>

              <div className="space-y-3">
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div className="font-medium text-green-800">✅ Auto-Approved</div>
                    <div className="font-bold text-green-800">{simulatedActionPlan.auto_approved}</div>
                  </div>
                  <div className="text-sm text-green-600 mt-1">System executed automatically</div>
                </div>

                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div className="font-medium text-blue-800">👤 Manually Approved</div>
                    <div className="font-bold text-blue-800">{simulatedActionPlan.manually_approved}</div>
                  </div>
                  <div className="text-sm text-blue-600 mt-1">Previously approved by supervisors</div>
                </div>

                <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <div className="flex justify-between items-center">
                    <div className="font-medium text-orange-800">⏳ Pending Approval</div>
                    <div className="font-bold text-orange-800">{simulatedActionPlan.pending_approval}</div>
                  </div>
                  <div className="text-sm text-orange-600 mt-1">Requires your approval to proceed</div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="font-medium text-red-800 flex items-center">
                  ⚠️ Approval Required
                </div>
                <div className="text-sm text-red-600 mt-2">
                  {simulatedActionPlan.approval_reason}
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
      {/* Breadcrumbs */}
      <div className="flex items-center space-x-2 text-sm text-gray-500">
        <button
          onClick={onBack}
          className="hover:text-blue-600 transition-colors"
        >
          Dashboard
        </button>
        <span>›</span>
        <span className="text-gray-900 font-medium">Approval Queue</span>
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div>
            <h2 className="text-xl font-semibold">Approval Queue</h2>
            <p className="text-sm text-gray-600">{approvalItems.length} items pending review</p>
          </div>
        </div>

        {/* Filter Controls */}
        <div className="flex space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1 rounded-lg text-sm ${filter === 'all' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'}`}
          >
            All ({approvalItems.length})
          </button>
          <button
            onClick={() => setFilter('high')}
            className={`px-3 py-1 rounded-lg text-sm ${filter === 'high' ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-600'}`}
          >
            High Priority ({approvalItems.filter(i => i.risk_level === 'high' || i.risk_level === 'critical').length})
          </button>
          <button
            onClick={() => setFilter('medium')}
            className={`px-3 py-1 rounded-lg text-sm ${filter === 'medium' ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-600'}`}
          >
            Medium ({approvalItems.filter(i => i.risk_level === 'medium').length})
          </button>
        </div>
      </div>

      {/* Clean Approval List */}
      <div className="space-y-2">
        {filteredItems.map((item, index) => {
          const scenarioName = item.scenario === 'Unknown scenario' 
            ? `Customer Service Case #${index + 1}`
            : item.scenario;
            
          return (
            <div 
              key={item.transcript_id}
              className={`bg-white border border-gray-200 rounded-lg p-4 hover:shadow-md hover:border-blue-300 cursor-pointer transition-all duration-200 ${loadingDetail ? 'opacity-50' : ''}`}
              onClick={() => !loadingDetail && handleItemClick(item)}
            >
              <div className="flex items-center justify-between">
                {/* Left: Case Info */}
                <div className="flex items-center space-x-4 flex-1">
                  <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-white text-sm">{getBusinessImpactIcon(item.business_impact)}</span>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-semibold text-gray-900 truncate">{scenarioName}</div>
                    <div className="text-xs text-gray-500">{item.customer_id} • {item.transcript_id}</div>
                  </div>
                </div>

                {/* Center: Priority */}
                <div className="flex items-center space-x-3 px-4">
                  <div className={`px-2 py-1 rounded text-xs font-medium ${
                    item.risk_level === 'high' ? 'bg-red-100 text-red-700' : 
                    item.risk_level === 'medium' ? 'bg-yellow-100 text-yellow-700' : 
                    'bg-green-100 text-green-700'
                  }`}>
                    {item.risk_level.toUpperCase()}
                  </div>
                  <div className="text-sm font-medium text-gray-900">{item.priority_score}</div>
                </div>

                {/* Center: Actions */}
                <div className="flex items-center space-x-4 px-4">
                  <div className="text-xs">
                    <span className="text-green-600 font-medium">{item.auto_approved}</span>
                    <span className="text-gray-500"> auto</span>
                  </div>
                  <div className="text-xs">
                    <span className="text-blue-600 font-medium">{item.manually_approved}</span>
                    <span className="text-gray-500"> done</span>
                  </div>
                  <div className="text-xs">
                    <span className="text-orange-600 font-bold">{item.pending_actions}</span>
                    <span className="text-orange-600"> pending</span>
                  </div>
                </div>

                {/* Right: Status */}
                <div className="text-right">
                  <div className="px-2 py-1 bg-orange-100 text-orange-700 rounded text-xs font-medium">
                    Needs Review
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {new Date(item.created_at).toLocaleDateString('en-US', { 
                      month: 'short', 
                      day: 'numeric' 
                    })}
                  </div>
                </div>
              </div>

              {/* Bottom: Approval Reason */}
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="flex items-center justify-between">
                  <div className="text-sm text-gray-700">
                    <span className="font-medium">Reason:</span> {
                      item.risk_level === 'high' ? 'High Risk Review Required' :
                      item.financial_impact ? 'Financial Impact Review' :
                      'Standard Workflow Approval'
                    }
                  </div>
                  <div className="flex items-center space-x-2">
                    {item.financial_impact && (
                      <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded">Financial Impact</span>
                    )}
                    {item.urgency === 'high' && (
                      <span className="text-xs bg-orange-100 text-orange-700 px-2 py-1 rounded">High Urgency</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {filteredItems.length === 0 && (
        <div className="text-center py-12">
          <div className="text-gray-500">No approval items match the current filter</div>
        </div>
      )}

      {loadingDetail && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white p-6 rounded-lg">
            <div className="text-gray-600">Loading transcript details...</div>
          </div>
        </div>
      )}
    </div>
  );
}