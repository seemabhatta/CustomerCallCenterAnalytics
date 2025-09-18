import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trash2, AlertTriangle } from "lucide-react";
import { analysisApi, planApi } from "@/api/client";

interface AnalysisViewProps {
  goToPlan: () => void;
}

export function AnalysisView({ goToPlan }: AnalysisViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedAnalysisId, setSelectedAnalysisId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false);
  const [analysisToDelete, setAnalysisToDelete] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch analyses
  const { data: analyses = [], isLoading, error } = useQuery({
    queryKey: ['analyses'],
    queryFn: () => analysisApi.list(),
  });

  // Selected analysis details
  const { data: selectedAnalysis } = useQuery({
    queryKey: ['analysis', selectedAnalysisId],
    queryFn: () => analysisApi.getById(selectedAnalysisId!),
    enabled: !!selectedAnalysisId,
  });

  // Fetch plans to check which analyses have plans
  const { data: plans = [] } = useQuery({
    queryKey: ['plans'],
    queryFn: () => planApi.list(),
  });

  // Create plan mutation
  const createPlanMutation = useMutation({
    mutationFn: (analysisId: string) => 
      planApi.create({ analysis_id: analysisId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      goToPlan();
    },
  });

  // Delete analysis mutation
  const deleteAnalysisMutation = useMutation({
    mutationFn: (id: string) => analysisApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      setShowDeleteConfirm(false);
      setAnalysisToDelete(null);
    },
    onError: (error) => {
      console.error('Failed to delete analysis:', error);
    },
  });

  // Delete all analyses mutation
  const deleteAllAnalysesMutation = useMutation({
    mutationFn: () => analysisApi.deleteAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      setShowDeleteAllConfirm(false);
    },
    onError: (error) => {
      console.error('Failed to delete all analyses:', error);
    },
  });

  // Filter analyses based on search query with backend field mapping
  const filteredAnalyses = analyses.filter((analysis: any) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      analysis.analysis_id?.toLowerCase().includes(query) ||
      analysis.transcript_id?.toLowerCase().includes(query) ||
      analysis.call_summary?.toLowerCase().includes(query) ||
      analysis.primary_intent?.toLowerCase().includes(query)
    );
  });

  // Check if analysis has plan
  const hasPlan = (analysisId: string) => 
    plans.some((plan: any) => plan.analysis_id === analysisId);

  const handleTriggerPlan = (analysisId: string) => {
    createPlanMutation.mutate(analysisId);
  };

  const handleDeleteClick = (analysisId: string) => {
    setAnalysisToDelete(analysisId);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = () => {
    if (analysisToDelete) {
      deleteAnalysisMutation.mutate(analysisToDelete);
    }
  };

  const handleDeleteAllConfirm = () => {
    deleteAllAnalysesMutation.mutate();
  };

  const getSentimentColor = (sentiment: string) => {
    if (sentiment?.includes('distressed') || sentiment?.includes('frustrated') || sentiment?.includes('angry')) return 'text-red-600';
    if (sentiment?.includes('anxious') || sentiment?.includes('concerned')) return 'text-orange-600';
    if (sentiment?.includes('satisfied') || sentiment?.includes('hopeful')) return 'text-green-600';
    return 'text-slate-600';
  };

  const getUrgencyBadgeVariant = (urgency: string) => {
    if (urgency === 'high') return 'danger';
    if (urgency === 'medium') return 'warning';
    return 'success';
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        <div className="animate-pulse">
          <div className="h-10 bg-gray-200 rounded mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-3">
        <div className="text-red-600">
          Error loading analyses: {(error as any)?.detail || 'Unknown error'}
        </div>
      </div>
    );
  }

  // Render analysis details view for any selected analysis
  if (selectedAnalysisId && selectedAnalysis) {
    const analysis = selectedAnalysis as any; // Cast to any for comprehensive API fields
    return (
      <div className="page-shell">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="view-header">Analysis Details • {selectedAnalysisId}</h2>
            <p className="text-xs text-slate-500">Comprehensive call intelligence and analysis insights</p>
          </div>
          <div className="flex items-center gap-1">
            <Button 
              onClick={() => setSelectedAnalysisId(null)} 
              variant="outline"
              size="sm"
              className="h-7 text-xs px-2"
            >
              Back to List
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
          {/* Call Intelligence Overview */}
          <Card className="panel">
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Call Intelligence</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                <div>
                  <div className="text-slate-600">Analysis ID</div>
                  <div className="font-medium">{analysis.analysis_id}</div>
                </div>
                <div>
                  <div className="text-slate-600">Transcript ID</div>
                  <div className="font-medium">{analysis.transcript_id}</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-600">Primary Intent</div>
                    <Badge variant="outline" className="text-xs px-1 py-0">
                      {analysis.primary_intent || 'N/A'}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-slate-600">Urgency Level</div>
                    <Badge variant={getUrgencyBadgeVariant(analysis.urgency_level)} className="text-xs px-1 py-0">
                      {analysis.urgency_level || 'N/A'}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-slate-600">Confidence Score</div>
                  <div className="font-medium">{analysis.confidence_score ? `${(analysis.confidence_score * 100).toFixed(1)}%` : 'N/A'}</div>
                </div>
                {analysis.call_summary && (
                  <div className="mt-2 pt-2 border-t">
                    <div className="text-slate-600 mb-1">Call Summary</div>
                    <div className="text-xs bg-slate-50 p-2 rounded">{analysis.call_summary}</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Resolution Status */}
          <Card className="panel">
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Resolution Status</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-600">Issue Resolved</span>
                  <Badge variant={analysis.issue_resolved ? 'success' : 'warning'} className="text-xs px-1 py-0">
                    {analysis.issue_resolved ? 'Yes' : 'No'}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">First Call Resolution</span>
                  <Badge variant={analysis.first_call_resolution ? 'success' : 'info'} className="text-xs px-1 py-0">
                    {analysis.first_call_resolution ? 'Yes' : 'No'}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-600">Escalation Needed</span>
                  <Badge variant={analysis.escalation_needed ? 'danger' : 'success'} className="text-xs px-1 py-0">
                    {analysis.escalation_needed ? 'Yes' : 'No'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Borrower Sentiment & Risk Assessment */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
          {/* Borrower Sentiment */}
          {analysis.borrower_sentiment && (
            <Card className="panel">
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-xs font-medium">Borrower Sentiment</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Overall</span>
                    <span className={`font-medium ${getSentimentColor(analysis.borrower_sentiment.overall)}`}>
                      {analysis.borrower_sentiment.overall || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Start of Call</span>
                    <span className={`font-medium ${getSentimentColor(analysis.borrower_sentiment.start)}`}>
                      {analysis.borrower_sentiment.start || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">End of Call</span>
                    <span className={`font-medium ${getSentimentColor(analysis.borrower_sentiment.end)}`}>
                      {analysis.borrower_sentiment.end || 'N/A'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Trend</span>
                    <Badge variant={analysis.borrower_sentiment.trend === 'improving' ? 'success' : analysis.borrower_sentiment.trend === 'declining' ? 'danger' : 'info'} className="text-xs px-1 py-0">
                      {analysis.borrower_sentiment.trend || 'N/A'}
                    </Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Risk Assessment */}
          {analysis.borrower_risks && (
            <Card className="panel">
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-xs font-medium">Risk Assessment</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <div className="text-slate-600">Delinquency Risk</div>
                    <div className="font-medium text-red-600">{(analysis.borrower_risks.delinquency_risk * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-slate-600">Churn Risk</div>
                    <div className="font-medium text-orange-600">{(analysis.borrower_risks.churn_risk * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-slate-600">Complaint Risk</div>
                    <div className="font-medium text-yellow-600">{(analysis.borrower_risks.complaint_risk * 100).toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-slate-600">Refinance Likelihood</div>
                    <div className="font-medium text-blue-600">{(analysis.borrower_risks.refinance_likelihood * 100).toFixed(1)}%</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Advisor Performance & Compliance */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
          {/* Advisor Performance */}
          {analysis.advisor_metrics && (
            <Card className="panel">
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-xs font-medium">Advisor Performance</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-600">Empathy Score</span>
                    <span className="font-medium">{analysis.advisor_metrics.empathy_score?.toFixed(1) || 'N/A'}/10</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Compliance Adherence</span>
                    <span className="font-medium text-green-600">{analysis.advisor_metrics.compliance_adherence?.toFixed(1) || 'N/A'}/10</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600">Solution Effectiveness</span>
                    <span className="font-medium">{analysis.advisor_metrics.solution_effectiveness?.toFixed(1) || 'N/A'}/10</span>
                  </div>
                  {analysis.advisor_metrics.coaching_opportunities && analysis.advisor_metrics.coaching_opportunities.length > 0 && (
                    <div className="mt-2 pt-2 border-t">
                      <div className="text-slate-600 mb-1">Coaching Opportunities</div>
                      <ul className="space-y-1">
                        {analysis.advisor_metrics.coaching_opportunities.map((opportunity: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 text-orange-700">
                            <span>📊</span>
                            <span>{opportunity}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Compliance & Flags */}
          <Card className="panel">
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Compliance & Flags</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                {analysis.compliance_flags && analysis.compliance_flags.length > 0 && (
                  <div>
                    <div className="text-slate-600 font-medium mb-1">Compliance Flags</div>
                    <ul className="space-y-1">
                      {analysis.compliance_flags.map((flag: string, index: number) => (
                        <li key={index} className="flex items-start gap-1 text-red-700">
                          <span>⚠</span>
                          <span>{flag}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {analysis.required_disclosures && analysis.required_disclosures.length > 0 && (
                  <div className={analysis.compliance_flags?.length > 0 ? 'pt-2 border-t' : ''}>
                    <div className="text-slate-600 font-medium mb-1">Required Disclosures</div>
                    <ul className="space-y-1">
                      {analysis.required_disclosures.map((disclosure: string, index: number) => (
                        <li key={index} className="flex items-start gap-1 text-blue-700">
                          <span>📝</span>
                          <span>{disclosure}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {(!analysis.compliance_flags || analysis.compliance_flags.length === 0) &&
                 (!analysis.required_disclosures || analysis.required_disclosures.length === 0) && (
                  <div className="text-slate-500 text-xs">No compliance issues detected</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Topics & Opportunities */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
          {/* Topics Discussed */}
          <Card className="panel">
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Topics & Issues</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                {analysis.topics_discussed && analysis.topics_discussed.length > 0 && (
                  <div>
                    <div className="text-slate-600 font-medium mb-1">Topics Discussed</div>
                    <ul className="space-y-1">
                      {analysis.topics_discussed.map((topic: string, index: number) => (
                        <li key={index} className="flex items-start gap-1">
                          <span className="text-slate-400">•</span>
                          <span>{topic}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {analysis.payment_concerns && analysis.payment_concerns.length > 0 && (
                  <div className={analysis.topics_discussed?.length > 0 ? 'pt-2 border-t' : ''}>
                    <div className="text-slate-600 font-medium mb-1">Payment Concerns</div>
                    <ul className="space-y-1">
                      {analysis.payment_concerns.map((concern: string, index: number) => (
                        <li key={index} className="flex items-start gap-1 text-orange-700">
                          <span>💵</span>
                          <span>{concern}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {analysis.property_related_issues && analysis.property_related_issues.length > 0 && (
                  <div className={(analysis.topics_discussed?.length > 0 || analysis.payment_concerns?.length > 0) ? 'pt-2 border-t' : ''}>
                    <div className="text-slate-600 font-medium mb-1">Property Issues</div>
                    <ul className="space-y-1">
                      {analysis.property_related_issues.map((issue: string, index: number) => (
                        <li key={index} className="flex items-start gap-1 text-green-700">
                          <span>🏠</span>
                          <span>{issue}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Product Opportunities */}
          <Card className="panel">
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Opportunities</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                {analysis.product_opportunities && analysis.product_opportunities.length > 0 && (
                  <div>
                    <div className="text-slate-600 font-medium mb-1">Product Opportunities</div>
                    <ul className="space-y-1">
                      {analysis.product_opportunities.map((opportunity: string, index: number) => (
                        <li key={index} className="flex items-start gap-1 text-blue-700">
                          <span>✨</span>
                          <span>{opportunity}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {(!analysis.product_opportunities || analysis.product_opportunities.length === 0) && (
                  <div className="text-slate-500 text-xs">No product opportunities identified</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="page-shell">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="view-header">Analysis</h2>
          <p className="text-xs text-slate-500">AI-powered analysis of customer interactions and sentiment</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        <Input 
          className="w-64 h-7 text-xs" 
          placeholder="Search by analysis or transcript ID" 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
        />
        <Badge variant="secondary" className="text-xs px-1 py-0">{filteredAnalyses.length} item(s)</Badge>
        {filteredAnalyses.length > 0 && (
          <Button 
            variant="outline" 
            size="sm"
            className="h-7 text-xs px-2 text-gray-600 hover:text-red-600"
            onClick={() => setShowDeleteAllConfirm(true)}
            disabled={deleteAllAnalysesMutation.isPending}
          >
            {deleteAllAnalysesMutation.isPending ? 'Deleting...' : 'Delete All'}
          </Button>
        )}
      </div>

      <div className="panel overflow-hidden">
        <table className="w-full text-xs">
          <thead className="table-header border-b">
            <tr>
              <th className="text-left py-1 px-2 text-xs font-medium">Analysis</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Transcript</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Summary</th>
              <th className="text-left py-1 px-2 text-xs font-medium">High</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Med</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Low</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Status</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Created</th>
              <th className="text-right py-1 px-2 text-xs font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredAnalyses.map((analysis: any) => {
              // Map backend data to frontend display format
              const borrowerRisks = analysis.borrower_risks || {};
              
              return (
                <tr key={analysis.analysis_id} className="table-row-hover">
                  <td className="py-1 px-2 text-xs font-medium text-slate-900">
                    <button 
                      className="underline hover:text-blue-600 text-xs" 
                      onClick={() => setSelectedAnalysisId(analysis.analysis_id)}
                    >
                      {analysis.analysis_id}
                    </button>
                  </td>
                  <td className="py-1 px-2 text-xs">{analysis.transcript_id}</td>
                  <td className="py-1 px-2 text-xs max-w-xs truncate" title={analysis.call_summary}>
                    {analysis.call_summary || analysis.primary_intent || 'No summary'}
                  </td>
                  <td className="py-1 px-2">
                    <Badge variant="destructive" className="text-xs px-1 py-0">
                      {Math.round((borrowerRisks.delinquency_risk || 0) * 10)}
                    </Badge>
                  </td>
                  <td className="py-1 px-2">
                    <Badge variant="default" className="text-xs px-1 py-0">
                      {Math.round((borrowerRisks.churn_risk || 0) * 10)}
                    </Badge>
                  </td>
                  <td className="py-1 px-2">
                    <Badge variant="secondary" className="text-xs px-1 py-0">
                      {Math.round((borrowerRisks.complaint_risk || 0) * 10)}
                    </Badge>
                  </td>
                  <td className="py-1 px-2">
                    <Badge variant={analysis.issue_resolved ? 'success' : 'warning'} className="text-xs px-1 py-0">
                      {analysis.issue_resolved ? 'Done' : 'Pending'}
                    </Badge>
                  </td>
                  <td className="py-1 px-2 text-xs">
                    {analysis.created_at ? new Date(analysis.created_at).toLocaleDateString() : 'N/A'}
                  </td>
                  <td className="py-1 px-2 text-right">
                    <div className="flex gap-1 justify-end">
                      <Button 
                        variant="ghost"
                        size="sm"
                        className="h-6 w-6 p-0 text-gray-500 hover:text-red-600"
                        onClick={() => handleDeleteClick(analysis.analysis_id)}
                        disabled={deleteAnalysisMutation.isPending}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="outline"
                        className="h-6 text-xs px-2 text-gray-600"
                        disabled={hasPlan(analysis.analysis_id) || createPlanMutation.isPending}
                        onClick={() => handleTriggerPlan(analysis.analysis_id)}
                      >
                        {createPlanMutation.isPending ? 
                          "..." : 
                          hasPlan(analysis.analysis_id) ? 
                            "✓" : 
                            "Plan"
                        }
                      </Button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        
        {filteredAnalyses.length === 0 && (
          <div className="p-4 text-center text-slate-500 text-xs">
            {searchQuery ? 'No analyses match your search.' : 'No analyses found.'}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg max-w-md mx-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <h3 className="text-sm font-medium">Delete Analysis</h3>
            </div>
            <p className="text-xs text-gray-600 mb-4">
              Are you sure you want to delete analysis <code className="font-mono">{analysisToDelete}</code>? This action cannot be undone.
            </p>
            <div className="flex gap-2 justify-end">
              <Button 
                variant="outline" 
                size="sm"
                className="text-xs"
                onClick={() => setShowDeleteConfirm(false)}
              >
                Cancel
              </Button>
              <Button 
                variant="destructive" 
                size="sm"
                className="text-xs"
                onClick={handleDeleteConfirm}
                disabled={deleteAnalysisMutation.isPending}
              >
                {deleteAnalysisMutation.isPending ? 'Deleting...' : 'Delete'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Delete All Confirmation Dialog */}
      {showDeleteAllConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg max-w-md mx-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <h3 className="text-sm font-medium">Delete All Analyses</h3>
            </div>
            <p className="text-xs text-gray-600 mb-4">
              Are you sure you want to delete all <strong>{filteredAnalyses.length}</strong> analyses? This will permanently remove all analysis data and cannot be undone.
            </p>
            <div className="flex gap-2 justify-end">
              <Button 
                variant="outline" 
                size="sm"
                className="text-xs"
                onClick={() => setShowDeleteAllConfirm(false)}
              >
                Cancel
              </Button>
              <Button 
                variant="destructive" 
                size="sm"
                className="text-xs"
                onClick={handleDeleteAllConfirm}
                disabled={deleteAllAnalysesMutation.isPending}
              >
                {deleteAllAnalysesMutation.isPending ? 'Deleting...' : 'Delete All'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}