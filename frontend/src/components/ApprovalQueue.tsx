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
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Compact Header with Stats */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        {/* Breadcrumbs */}
        <div className="flex items-center space-x-2 text-sm text-gray-500 mb-3">
          <button onClick={onBack} className="hover:text-blue-600 transition-colors">Dashboard</button>
          <span>›</span>
          <span className="text-gray-900 font-medium">Approval Queue</span>
        </div>

        {/* Header with Quick Stats */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-8">
            <div>
              <h1 className="text-xl font-semibold text-gray-900">Approval Queue</h1>
              <p className="text-sm text-gray-600">{approvalItems.length} items pending review</p>
            </div>
            
            {/* Quick Stats */}
            <div className="flex items-center space-x-6">
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{approvalItems.filter(item => item.risk_level === 'high').length}</div>
                <div className="text-xs text-gray-500">High Risk</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{approvalItems.filter(item => item.financial_impact).length}</div>
                <div className="text-xs text-gray-500">Financial</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{approvalItems.reduce((sum, item) => sum + item.pending_actions, 0)}</div>
                <div className="text-xs text-gray-500">Total Pending</div>
              </div>
            </div>
          </div>

          {/* Compact Filters */}
          <div className="flex items-center space-x-2">
            <button
              onClick={() => setFilter('all')}
              className={`px-3 py-1.5 rounded text-xs font-medium ${
                filter === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              All ({approvalItems.length})
            </button>
            <button
              onClick={() => setFilter('high')}
              className={`px-3 py-1.5 rounded text-xs font-medium ${
                filter === 'high' ? 'bg-red-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              High ({approvalItems.filter(item => item.risk_level === 'high').length})
            </button>
            <button
              onClick={() => setFilter('medium')}
              className={`px-3 py-1.5 rounded text-xs font-medium ${
                filter === 'medium' ? 'bg-orange-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              Medium ({approvalItems.filter(item => item.risk_level === 'medium').length})
            </button>
          </div>
        </div>
      </div>

      {/* High-Density Table */}
      <div className="flex-1 overflow-hidden">
        <div className="h-full overflow-y-auto">
          <table className="w-full">
            <thead className="bg-gray-50 sticky top-0 z-10">
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase">Case</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase">Priority</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 uppercase">Actions</th>
                <th className="text-left py-3 px-4 text-xs font-semibold text-gray-700 uppercase">Approval Reason</th>
                <th className="text-center py-3 px-4 text-xs font-semibold text-gray-700 uppercase">Risk Flags</th>
                <th className="text-right py-3 px-4 text-xs font-semibold text-gray-700 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-100">
              {filteredItems.map((item, index) => {
                const scenarioName = item.scenario === 'Unknown scenario' 
                  ? `Customer Service Case #${index + 1}`
                  : item.scenario;
                
                const riskColor = item.risk_level === 'high' ? 'bg-red-50 border-l-4 border-red-400' : 
                                 item.risk_level === 'medium' ? 'bg-orange-50 border-l-4 border-orange-400' : 
                                 'bg-white border-l-4 border-gray-200';

                return (
                  <tr 
                    key={item.transcript_id}
                    className={`${riskColor} hover:bg-blue-50 cursor-pointer transition-colors ${loadingDetail ? 'opacity-50' : ''}`}
                    onClick={() => !loadingDetail && handleItemClick(item)}
                  >
                    {/* Case Info */}
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-blue-500 rounded flex items-center justify-center">
                          <span className="text-white text-xs">{getBusinessImpactIcon(item.business_impact)}</span>
                        </div>
                        <div>
                          <div className="text-sm font-medium text-gray-900">{scenarioName}</div>
                          <div className="text-xs text-gray-500">{item.customer_id} • {item.transcript_id}</div>
                        </div>
                      </div>
                    </td>

                    {/* Priority */}
                    <td className="py-3 px-4">
                      <div className="flex items-center space-x-2">
                        <span className={`inline-flex px-2 py-1 text-xs font-medium rounded ${
                          item.risk_level === 'high' ? 'bg-red-100 text-red-800' : 
                          item.risk_level === 'medium' ? 'bg-orange-100 text-orange-800' : 
                          'bg-green-100 text-green-800'
                        }`}>
                          {item.risk_level.toUpperCase()}
                        </span>
                        <span className="text-sm font-semibold text-gray-900">{item.priority_score}</span>
                      </div>
                    </td>

                    {/* Actions */}
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center space-x-4">
                        <div className="text-xs">
                          <div className="font-medium text-green-600">{item.auto_approved}</div>
                          <div className="text-gray-500">auto</div>
                        </div>
                        <div className="text-xs">
                          <div className="font-medium text-blue-600">{item.manually_approved}</div>
                          <div className="text-gray-500">done</div>
                        </div>
                        <div className="text-xs">
                          <div className="font-bold text-orange-600">{item.pending_actions}</div>
                          <div className="text-orange-600">pending</div>
                        </div>
                      </div>
                    </td>

                    {/* Approval Reason */}
                    <td className="py-3 px-4">
                      <div className="text-sm text-gray-900">
                        {item.risk_level === 'high' ? 'High Risk Review Required' :
                         item.financial_impact ? 'Financial Impact Review' :
                         'Standard Workflow Approval'}
                      </div>
                    </td>

                    {/* Risk Flags */}
                    <td className="py-3 px-4 text-center">
                      <div className="flex items-center justify-center space-x-1">
                        {item.financial_impact && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-red-100 text-red-700">
                            💰 Financial
                          </span>
                        )}
                        {item.urgency === 'high' && (
                          <span className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-orange-100 text-orange-700">
                            ⚡ Urgent
                          </span>
                        )}
                      </div>
                    </td>

                    {/* Status */}
                    <td className="py-3 px-4 text-right">
                      <div>
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                          Needs Review
                        </span>
                        <div className="text-xs text-gray-500 mt-1">
                          {new Date(item.created_at).toLocaleDateString('en-US', { 
                            month: 'short', 
                            day: 'numeric' 
                          })}
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
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