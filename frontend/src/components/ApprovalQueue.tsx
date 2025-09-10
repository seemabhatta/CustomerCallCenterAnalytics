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
    return (
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button 
              onClick={() => {
                setSelectedItem(null);
                setSelectedTranscript(null);
                setSimulatedAnalysis(null);
                setSimulatedActionPlan(null);
              }}
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
              📄 Transcript Details
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-gray-600">Customer:</span>
                <span className="font-medium">{selectedTranscript.customer_id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Scenario:</span>
                <span className="font-medium">{selectedTranscript.scenario}</span>
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
            <div className="mt-4 p-3 bg-gray-50 rounded-lg max-h-48 overflow-y-auto">
              <div className="text-sm font-medium text-gray-700 mb-2">Conversation Preview:</div>
              {selectedTranscript.messages.slice(0, 3).map((msg, idx) => (
                <div key={idx} className="mb-2 text-sm">
                  <span className="font-medium text-blue-600">{msg.role}:</span>
                  <span className="text-gray-700 ml-2">{msg.content.substring(0, 100)}...</span>
                </div>
              ))}
              {selectedTranscript.messages.length > 3 && (
                <div className="text-xs text-gray-500">...and {selectedTranscript.messages.length - 3} more messages</div>
              )}
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
                <div className="font-medium">{simulatedAnalysis.intent}</div>
                <div className="text-sm text-gray-500">
                  {Math.round(simulatedAnalysis.confidence * 100)}% confidence
                </div>
              </div>
              
              <div>
                <span className="text-gray-600 text-sm">Sentiment Journey</span>
                <div className="font-medium">{simulatedAnalysis.sentiment}</div>
              </div>

              <div>
                <span className="text-gray-600 text-sm">Risk Scores</span>
                <div className="space-y-2 mt-2">
                  <div className="flex justify-between">
                    <span>Churn Risk</span>
                    <span className="font-medium text-red-600">
                      {Math.round(simulatedAnalysis.risk_scores.churn * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Complaint Risk</span>
                    <span className="font-medium text-orange-600">
                      {Math.round(simulatedAnalysis.risk_scores.complaint * 100)}%
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Delinquency Risk</span>
                    <span className="font-medium text-yellow-600">
                      {Math.round(simulatedAnalysis.risk_scores.delinquency * 100)}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Action Plan */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center">
              📋 Action Plan
            </h3>
            <div className="space-y-4">
              <div className="text-sm text-gray-600">
                {simulatedActionPlan.total_actions} total actions planned
              </div>

              <div className="space-y-3">
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                  <div className="font-medium text-green-800">Auto-Approved ({simulatedActionPlan.auto_approved})</div>
                  <div className="text-sm text-green-600">System executed automatically</div>
                </div>

                <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="font-medium text-blue-800">Manually Approved ({simulatedActionPlan.manually_approved})</div>
                  <div className="text-sm text-blue-600">Previously approved by supervisors</div>
                </div>

                <div className="p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <div className="font-medium text-orange-800">Pending Approval ({simulatedActionPlan.pending_approval})</div>
                  <div className="text-sm text-orange-600">Requires your approval to proceed</div>
                </div>
              </div>

              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="font-medium text-red-800">⚠️ Approval Required</div>
                <div className="text-sm text-red-600 mt-1">
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

      {/* Approval Items List */}
      <div className="space-y-4">
        {filteredItems.map((item) => (
          <div 
            key={item.transcript_id}
            className={`card hover:shadow-lg cursor-pointer transition-all ${loadingDetail ? 'opacity-50' : ''}`}
            onClick={() => !loadingDetail && handleItemClick(item)}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-3">
                  <span className="text-xl">{getBusinessImpactIcon(item.business_impact)}</span>
                  <div>
                    <h3 className="font-semibold">{item.scenario}</h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-600">
                      <span>Customer: {item.customer_id}</span>
                      <span>•</span>
                      <span>ID: {item.transcript_id}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Business Impact:</span>
                    <div className="font-medium capitalize">{item.business_impact}</div>
                    <div className="text-gray-500">Priority Score: {item.priority_score}</div>
                  </div>
                  
                  <div>
                    <span className="text-gray-500">Action Status:</span>
                    <div className="font-medium">
                      <span className="text-green-600">{item.auto_approved} auto</span>, 
                      <span className="text-blue-600 ml-1">{item.manually_approved} approved</span>
                    </div>
                    <div className="text-orange-600 font-medium">{item.pending_actions} pending approval</div>
                  </div>

                  <div>
                    <span className="text-gray-500">Risk Level:</span>
                    <div className="font-medium capitalize">{item.risk_level}</div>
                    <div className="text-gray-500">Financial: {item.financial_impact ? 'Yes' : 'No'}</div>
                  </div>
                </div>

                <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded text-sm">
                  <span className="font-medium text-orange-800">⚠️ Requires Approval: </span>
                  <span className="text-orange-700">
                    {item.risk_level === 'critical' ? 'Critical risk level detected' : 
                     item.risk_level === 'high' ? 'High risk requires supervisor review' :
                     item.financial_impact ? 'Financial impact needs approval' :
                     'Standard approval workflow'}
                  </span>
                </div>
              </div>

              <div className="flex flex-col items-end space-y-2 ml-6">
                <div className={`px-2 py-1 rounded-full text-xs font-medium border ${getUrgencyColor(item.urgency)}`}>
                  {item.urgency.toUpperCase()}
                </div>
                <div className="text-xs text-gray-500">
                  {new Date(item.created_at).toLocaleDateString()}
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