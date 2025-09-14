import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Trash2, AlertTriangle } from "lucide-react";
import { planApi, workflowApi } from "@/api/client";

interface PlanViewProps {
  goToWorkflow: () => void;
}

export function PlanView({ goToWorkflow }: PlanViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false);
  const [planToDelete, setPlanToDelete] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch plans
  const { data: plans = [], isLoading, error } = useQuery({
    queryKey: ['plans'],
    queryFn: () => planApi.list(),
  });

  // Fetch workflows to check which plans have workflows
  const { data: workflows = [] } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowApi.list(),
  });

  // Selected plan details
  const { data: selectedPlan } = useQuery({
    queryKey: ['plan', selectedPlanId],
    queryFn: () => planApi.getById(selectedPlanId!),
    enabled: !!selectedPlanId,
  });

  // Create workflow mutation
  const createWorkflowMutation = useMutation({
    mutationFn: (planId: string) =>
      workflowApi.extractFromPlan(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      goToWorkflow();
    },
    onError: (error: any) => {
      console.error('Failed to create workflow:', error);
      // You could add a toast notification here if you have a toast system
    },
  });

  // Delete plan mutation
  const deletePlanMutation = useMutation({
    mutationFn: (id: string) => planApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      setShowDeleteConfirm(false);
      setPlanToDelete(null);
    },
    onError: (error) => {
      console.error('Failed to delete plan:', error);
    },
  });

  // Delete all plans mutation
  const deleteAllPlansMutation = useMutation({
    mutationFn: () => planApi.deleteAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      setShowDeleteAllConfirm(false);
    },
    onError: (error) => {
      console.error('Failed to delete all plans:', error);
    },
  });

  // Filter plans based on search query with backend field mapping
  const filteredPlans = plans.filter((plan: any) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      plan.plan_id?.toLowerCase().includes(query) ||
      plan.analysis_id?.toLowerCase().includes(query) ||
      plan.routing_reason?.toLowerCase().includes(query)
    );
  });

  // Check if plan has workflow
  const hasWorkflow = (planId: string) => 
    workflows.some((workflow: any) => workflow.plan_id === planId);

  const handleTriggerWorkflow = (planId: string) => {
    createWorkflowMutation.mutate(planId);
  };

  const handleDeleteClick = (planId: string) => {
    setPlanToDelete(planId);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = () => {
    if (planToDelete) {
      deletePlanMutation.mutate(planToDelete);
    }
  };

  const handleDeleteAllConfirm = () => {
    deleteAllPlansMutation.mutate();
  };

  const handlePlanClick = (planId: string) => {
    setSelectedPlanId(planId);
  };

  const handleClosePlanView = () => {
    setSelectedPlanId(null);
  };

  const getStatusBadgeVariant = (queueStatus: string) => {
    switch (queueStatus?.toLowerCase()) {
      case 'approved': return 'default';
      case 'pending_supervisor': return 'destructive';
      case 'pending_advisor': return 'secondary';
      case 'rejected': return 'outline';
      default: return 'secondary';
    }
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
          Error loading plans: {(error as any)?.detail || 'Unknown error'}
        </div>
      </div>
    );
  }

  // Render plan details view for any selected plan
  if (selectedPlanId && selectedPlan) {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold">Plan Details • {selectedPlanId}</h2>
            <p className="text-xs text-slate-600">Action plan structure and implementation details</p>
          </div>
          <div className="flex items-center gap-1">
            <Button 
              onClick={handleClosePlanView} 
              variant="outline"
              size="sm"
              className="h-7 text-xs px-2"
            >
              Back to List
            </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
          {/* Plan Overview */}
          <Card>
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Plan Overview</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <div className="text-slate-600">Plan ID</div>
                  <div className="font-medium">{selectedPlan.plan_id}</div>
                </div>
                <div>
                  <div className="text-slate-600">Analysis ID</div>
                  <div className="font-medium">{selectedPlan.analysis_id}</div>
                </div>
                <div>
                  <div className="text-slate-600">Transcript ID</div>
                  <div className="font-medium">{selectedPlan.transcript_id}</div>
                </div>
                <div>
                  <div className="text-slate-600">Risk Level</div>
                  <Badge 
                    variant={selectedPlan.risk_level === 'high' ? 'destructive' : selectedPlan.risk_level === 'medium' ? 'default' : 'secondary'}
                    className="text-xs px-1 py-0"
                  >
                    {selectedPlan.risk_level || 'Not set'}
                  </Badge>
                </div>
                <div>
                  <div className="text-slate-600">Approval Route</div>
                  <div className="font-medium">{selectedPlan.approval_route?.replace('_', ' ') || 'N/A'}</div>
                </div>
                <div>
                  <div className="text-slate-600">Queue Status</div>
                  <Badge variant={getStatusBadgeVariant(selectedPlan.queue_status || '')} className="text-xs px-1 py-0">
                    {selectedPlan.queue_status?.replace('_', ' ') || 'Unknown'}
                  </Badge>
                </div>
                <div>
                  <div className="text-slate-600">Auto Executable</div>
                  <div className="font-medium">{selectedPlan.auto_executable ? 'Yes' : 'No'}</div>
                </div>
                <div>
                  <div className="text-slate-600">Created At</div>
                  <div className="font-medium">{selectedPlan.created_at ? new Date(selectedPlan.created_at).toLocaleString() : 'N/A'}</div>
                </div>
              </div>
              {selectedPlan.routing_reason && (
                <div className="mt-2 pt-2 border-t">
                  <div className="text-slate-600 text-xs">Routing Reason</div>
                  <div className="text-xs">{selectedPlan.routing_reason}</div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Approval Status */}
          <Card>
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Approval Status</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-600">Generator Version</span>
                  <span className="font-medium">{selectedPlan.generator_version || 'N/A'}</span>
                </div>
                {selectedPlan.approved_at && (
                  <div className="flex justify-between">
                    <span className="text-slate-600">Approved At</span>
                    <span className="font-medium">{new Date(selectedPlan.approved_at).toLocaleString()}</span>
                  </div>
                )}
                {selectedPlan.approved_by && (
                  <div className="flex justify-between">
                    <span className="text-slate-600">Approved By</span>
                    <span className="font-medium">{selectedPlan.approved_by}</span>
                  </div>
                )}
                {!selectedPlan.approved_at && (
                  <div className="text-slate-500 text-xs">Plan not yet approved</div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Four-Layer Plan Structure */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
          {/* Borrower Plan */}
          {selectedPlan.borrower_plan && (
            <Card>
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-xs font-medium">Borrower Plan</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="space-y-2">
                  {selectedPlan.borrower_plan.immediate_actions && selectedPlan.borrower_plan.immediate_actions.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Immediate Actions:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.borrower_plan.immediate_actions.map((action: any, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-red-50 p-2 rounded">
                            <span className="text-red-500">⚡</span>
                            <div>
                              <div className="font-medium">{action.action}</div>
                              <div className="text-xs text-slate-600">{action.timeline} • {action.priority} priority</div>
                              {action.description && <div className="text-xs text-slate-500 mt-1">{action.description}</div>}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.borrower_plan.follow_ups && selectedPlan.borrower_plan.follow_ups.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Follow-ups:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.borrower_plan.follow_ups.map((followUp: any, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-orange-50 p-2 rounded">
                            <span className="text-orange-500">📅</span>
                            <div>
                              <div className="font-medium">{followUp.action}</div>
                              <div className="text-xs text-slate-600">{followUp.due_date} • {followUp.owner}</div>
                              {followUp.trigger_condition && <div className="text-xs text-slate-500 mt-1">Trigger: {followUp.trigger_condition}</div>}
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.borrower_plan.personalized_offers && selectedPlan.borrower_plan.personalized_offers.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Personalized Offers:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.borrower_plan.personalized_offers.map((offer: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-green-50 p-2 rounded">
                            <span className="text-green-500">💡</span>
                            <span>{offer}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.borrower_plan.risk_mitigation && selectedPlan.borrower_plan.risk_mitigation.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Risk Mitigation:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.borrower_plan.risk_mitigation.map((risk: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-yellow-50 p-2 rounded">
                            <span className="text-yellow-600">🛡️</span>
                            <span>{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Advisor Plan */}
          {selectedPlan.advisor_plan && (
            <Card>
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-xs font-medium">Advisor Plan</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="space-y-2">
                  {selectedPlan.advisor_plan.coaching_items && selectedPlan.advisor_plan.coaching_items.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Coaching Items:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.advisor_plan.coaching_items.map((item: any, index: number) => (
                          <li key={index} className="bg-blue-50 p-2 rounded">
                            <div className="flex items-start gap-1">
                              <span className="text-blue-500">🎯</span>
                              <div>
                                <div className="font-medium">{item.action}</div>
                                <div className="text-xs text-slate-600">{item.coaching_point}</div>
                                <div className="text-xs text-blue-600 mt-1">Expected: {item.expected_improvement}</div>
                                <div className="text-xs text-slate-500">Priority: {item.priority}</div>
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.advisor_plan.performance_feedback && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Performance Feedback:</div>
                      <div className="bg-green-50 p-2 rounded text-xs space-y-1">
                        {selectedPlan.advisor_plan.performance_feedback.strengths && selectedPlan.advisor_plan.performance_feedback.strengths.length > 0 && (
                          <div>
                            <div className="font-medium text-green-700">Strengths:</div>
                            <ul className="ml-2">
                              {selectedPlan.advisor_plan.performance_feedback.strengths.map((strength: string, index: number) => (
                                <li key={index} className="flex items-start gap-1">
                                  <span className="text-green-500">✓</span>
                                  <span>{strength}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {selectedPlan.advisor_plan.performance_feedback.improvements && selectedPlan.advisor_plan.performance_feedback.improvements.length > 0 && (
                          <div>
                            <div className="font-medium text-orange-700">Areas for Improvement:</div>
                            <ul className="ml-2">
                              {selectedPlan.advisor_plan.performance_feedback.improvements.map((improvement: string, index: number) => (
                                <li key={index} className="flex items-start gap-1">
                                  <span className="text-orange-500">→</span>
                                  <span>{improvement}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                  {selectedPlan.advisor_plan.training_recommendations && selectedPlan.advisor_plan.training_recommendations.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Training Recommendations:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.advisor_plan.training_recommendations.map((training: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-purple-50 p-2 rounded">
                            <span className="text-purple-500">📚</span>
                            <span>{training}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.advisor_plan.next_actions && selectedPlan.advisor_plan.next_actions.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Next Actions:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.advisor_plan.next_actions.map((action: string, index: number) => (
                          <li key={index} className="flex items-start gap-1">
                            <span className="text-slate-400">▶</span>
                            <span>{action}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Supervisor Plan */}
          {selectedPlan.supervisor_plan && (
            <Card>
              <CardHeader className="py-2 px-3">
                <CardTitle className="flex items-center justify-between text-xs font-medium">
                  <span>Supervisor Plan</span>
                  {selectedPlan.supervisor_plan.approval_required && (
                    <Badge variant="destructive" className="text-xs px-1 py-0">
                      Approval Required
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="space-y-2">
                  {selectedPlan.supervisor_plan.escalation_items && selectedPlan.supervisor_plan.escalation_items.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Escalation Items:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.supervisor_plan.escalation_items.map((item: any, index: number) => (
                          <li key={index} className="bg-red-50 p-2 rounded">
                            <div className="flex items-start gap-1">
                              <span className="text-red-500">🚨</span>
                              <div>
                                <div className="font-medium">{item.item}</div>
                                <div className="text-xs text-slate-600">Reason: {item.reason}</div>
                                <div className="text-xs text-red-600 mt-1">{item.action_required}</div>
                                <div className="text-xs text-slate-500">Priority: {item.priority}</div>
                              </div>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.supervisor_plan.team_patterns && selectedPlan.supervisor_plan.team_patterns.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Team Patterns:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.supervisor_plan.team_patterns.map((pattern: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-orange-50 p-2 rounded">
                            <span className="text-orange-500">📊</span>
                            <span>{pattern}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.supervisor_plan.compliance_review && selectedPlan.supervisor_plan.compliance_review.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Compliance Review:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.supervisor_plan.compliance_review.map((review: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-yellow-50 p-2 rounded">
                            <span className="text-yellow-600">📋</span>
                            <span>{review}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.supervisor_plan.process_improvements && selectedPlan.supervisor_plan.process_improvements.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Process Improvements:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.supervisor_plan.process_improvements.map((improvement: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-blue-50 p-2 rounded">
                            <span className="text-blue-500">🔧</span>
                            <span>{improvement}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Leadership Plan */}
          {selectedPlan.leadership_plan && (
            <Card>
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-xs font-medium">Leadership Plan</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="space-y-2">
                  {selectedPlan.leadership_plan.portfolio_insights && selectedPlan.leadership_plan.portfolio_insights.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Portfolio Insights:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.leadership_plan.portfolio_insights.map((insight: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-blue-50 p-2 rounded">
                            <span className="text-blue-500">📈</span>
                            <span>{insight}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.leadership_plan.strategic_opportunities && selectedPlan.leadership_plan.strategic_opportunities.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Strategic Opportunities:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.leadership_plan.strategic_opportunities.map((opportunity: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-green-50 p-2 rounded">
                            <span className="text-green-500">🚀</span>
                            <span>{opportunity}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.leadership_plan.risk_indicators && selectedPlan.leadership_plan.risk_indicators.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Risk Indicators:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.leadership_plan.risk_indicators.map((risk: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-red-50 p-2 rounded">
                            <span className="text-red-500">⚠</span>
                            <span>{risk}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.leadership_plan.trend_analysis && selectedPlan.leadership_plan.trend_analysis.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Trend Analysis:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.leadership_plan.trend_analysis.map((trend: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-purple-50 p-2 rounded">
                            <span className="text-purple-500">📊</span>
                            <span>{trend}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {selectedPlan.leadership_plan.resource_allocation && selectedPlan.leadership_plan.resource_allocation.length > 0 && (
                    <div>
                      <div className="text-xs font-medium text-slate-700 mb-1">Resource Allocation:</div>
                      <ul className="space-y-1 text-xs">
                        {selectedPlan.leadership_plan.resource_allocation.map((allocation: string, index: number) => (
                          <li key={index} className="flex items-start gap-1 bg-orange-50 p-2 rounded">
                            <span className="text-orange-500">💼</span>
                            <span>{allocation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <Input 
          className="w-64 h-7 text-xs" 
          placeholder="Search by plan or analysis ID" 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
        />
        <Badge variant="secondary" className="text-xs px-1 py-0">{filteredPlans.length} item(s)</Badge>
        {filteredPlans.length > 0 && (
          <Button 
            variant="outline" 
            size="sm"
            className="h-7 text-xs px-2 text-gray-600 hover:text-red-600"
            onClick={() => setShowDeleteAllConfirm(true)}
            disabled={deleteAllPlansMutation.isPending}
          >
            {deleteAllPlansMutation.isPending ? 'Deleting...' : 'Delete All'}
          </Button>
        )}
      </div>

      <div className="overflow-hidden rounded-lg border">
        <table className="w-full text-xs">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left py-1 px-2 text-xs font-medium">Plan</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Analysis</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Routing Reason</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Risk Level</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Route</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Auto Exec</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Status</th>
              <th className="text-left py-1 px-2 text-xs font-medium">Created</th>
              <th className="text-right py-1 px-2 text-xs font-medium">Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredPlans.map((plan: any) => (
              <tr key={plan.plan_id} className="border-b hover:bg-slate-50">
                <td className="py-1 px-2 text-xs font-medium text-slate-900">
                  <button 
                    className="underline hover:text-blue-600 text-xs" 
                    onClick={() => handlePlanClick(plan.plan_id)}
                  >
                    {plan.plan_id}
                  </button>
                </td>
                <td className="py-1 px-2 text-xs">{plan.analysis_id}</td>
                <td className="py-1 px-2 text-xs max-w-xs truncate" title={plan.routing_reason}>
                  {plan.routing_reason || 'No reason provided'}
                </td>
                <td className="py-1 px-2">
                  <Badge 
                    variant={plan.risk_level === 'high' ? 'destructive' : plan.risk_level === 'medium' ? 'default' : 'secondary'} 
                    className="text-xs px-1 py-0"
                  >
                    {plan.risk_level || 'Unknown'}
                  </Badge>
                </td>
                <td className="py-1 px-2">
                  <Badge variant="outline" className="text-xs px-1 py-0">
                    {plan.approval_route?.replace('_', ' ') || 'N/A'}
                  </Badge>
                </td>
                <td className="py-1 px-2">
                  <Badge variant={plan.auto_executable ? 'default' : 'secondary'} className="text-xs px-1 py-0">
                    {plan.auto_executable ? 'Yes' : 'No'}
                  </Badge>
                </td>
                <td className="py-1 px-2">
                  <Badge variant={getStatusBadgeVariant(plan.queue_status)} className="text-xs px-1 py-0">
                    {plan.queue_status?.replace('_', ' ') || 'Unknown'}
                  </Badge>
                </td>
                <td className="py-1 px-2 text-xs">
                  {plan.created_at ? new Date(plan.created_at).toLocaleDateString() : 'N/A'}
                </td>
                <td className="py-1 px-2 text-right">
                  <div className="flex gap-1 justify-end">
                    <Button 
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 text-gray-500 hover:text-red-600"
                      onClick={() => handleDeleteClick(plan.plan_id)}
                      disabled={deletePlanMutation.isPending}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-6 text-xs px-2 text-gray-600"
                      disabled={hasWorkflow(plan.plan_id) || createWorkflowMutation.isPending}
                      onClick={() => handleTriggerWorkflow(plan.plan_id)}
                    >
                      {createWorkflowMutation.isPending ? 
                        "..." : 
                        hasWorkflow(plan.plan_id) ? 
                          "✓" : 
                          "Workflow"
                      }
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredPlans.length === 0 && (
          <div className="p-4 text-center text-slate-500 text-xs">
            {searchQuery ? 'No plans match your search.' : 'No plans found.'}
          </div>
        )}
      </div>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg max-w-md mx-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <h3 className="text-sm font-medium">Delete Plan</h3>
            </div>
            <p className="text-xs text-gray-600 mb-4">
              Are you sure you want to delete plan <code className="font-mono">{planToDelete}</code>? This action cannot be undone.
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
                disabled={deletePlanMutation.isPending}
              >
                {deletePlanMutation.isPending ? 'Deleting...' : 'Delete'}
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
              <h3 className="text-sm font-medium">Delete All Plans</h3>
            </div>
            <p className="text-xs text-gray-600 mb-4">
              Are you sure you want to delete all <strong>{filteredPlans.length}</strong> plans? This will permanently remove all plan data and cannot be undone.
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
                disabled={deleteAllPlansMutation.isPending}
              >
                {deleteAllPlansMutation.isPending ? 'Deleting...' : 'Delete All'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}