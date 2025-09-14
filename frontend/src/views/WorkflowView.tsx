import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowApi } from '@/api/client';
import { WorkflowFilterParams, GranularWorkflow } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Filter, Clock, Users, Trash2, AlertTriangle, Shield, AlertCircle, CheckCircle, Info, Play, Check, X, RotateCcw } from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface WorkflowViewProps {
  goToPlan?: (planId: string) => void;
}

export function WorkflowView({ goToPlan }: WorkflowViewProps) {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [riskLevelFilter, setRiskLevelFilter] = useState<string>("");
  const [limitFilter, setLimitFilter] = useState<string>("50");
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false);
  const [workflowToDelete, setWorkflowToDelete] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Helper function to safely parse risk reasoning
  const parseRiskFactor = (reasoning: any, factor: string): string => {
    if (!reasoning) return '';
    
    // If reasoning is an object, try to access the property directly
    if (typeof reasoning === 'object') {
      return reasoning[factor] || '';
    }
    
    // If reasoning is a string, try JSON parsing first
    if (typeof reasoning === 'string') {
      try {
        const parsed = JSON.parse(reasoning);
        if (parsed && typeof parsed === 'object' && parsed[factor]) {
          return parsed[factor];
        }
      } catch (e) {
        // Not valid JSON, continue with string parsing
      }
      
      // Fallback to regex and string extraction
      const regexMatch = reasoning.match(new RegExp(`"${factor}":\\s*"([^"]*)"`));
      if (regexMatch) return regexMatch[1];
      
      // Final fallback: basic string splitting
      if (reasoning.includes(factor)) {
        return reasoning.split(factor).slice(1, 2).join('').replace(/[":\,]/g, '').trim().substring(0, 200);
      }
    }
    
    return '';
  };
  
  // Helper function to get risk level icon with fallback
  const getRiskLevelIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'HIGH': return <AlertCircle className="h-4 w-4 text-red-600" />;
      case 'MEDIUM': return <AlertTriangle className="h-4 w-4 text-orange-600" />;
      case 'LOW': return <CheckCircle className="h-4 w-4 text-green-600" />;
      default: return <Info className="h-4 w-4 text-gray-600" />;
    }
  };

  // Helper function to detect workflow type
  const getWorkflowDisplayType = (workflow: any) => {
    if (workflow.workflow_data?.action_item) return 'GRANULAR'; // New granular format
    if (workflow.risk_reasoning) return 'META';   // Old meta format  
    return 'UNKNOWN';
  };

  const isGranularWorkflow = (workflow: any): workflow is GranularWorkflow => 
    getWorkflowDisplayType(workflow) === 'GRANULAR';

  // Helper function for priority colors
  const getPriorityColor = (priority: string) => {
    switch (priority?.toLowerCase()) {
      case 'high': return 'bg-red-100 text-red-700 border-red-200';
      case 'medium': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'low': return 'bg-green-100 text-green-700 border-green-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  // Build filter parameters
  const filterParams: WorkflowFilterParams = {};
  if (statusFilter && statusFilter !== "all") {
    filterParams.status = statusFilter as any;
  }
  if (riskLevelFilter && riskLevelFilter !== "all") {
    filterParams.risk_level = riskLevelFilter as any;
  }
  if (limitFilter) {
    filterParams.limit = parseInt(limitFilter);
  }

  // Fetch workflows with current filters
  const { data: workflows = [], isLoading, error, refetch } = useQuery({
    queryKey: ['workflows', filterParams],
    queryFn: () => workflowApi.list(filterParams),
  });

  // Selected workflow details
  const { data: selectedWorkflow } = useQuery({
    queryKey: ['workflow', selectedWorkflowId],
    queryFn: () => workflowApi.getById(selectedWorkflowId!),
    enabled: !!selectedWorkflowId,
  });

  // Delete workflow mutation
  const deleteWorkflowMutation = useMutation({
    mutationFn: (id: string) => workflowApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      setShowDeleteConfirm(false);
      setWorkflowToDelete(null);
    },
    onError: (error) => {
      console.error('Failed to delete workflow:', error);
    },
  });

  // Delete all workflows mutation
  const deleteAllWorkflowsMutation = useMutation({
    mutationFn: () => workflowApi.deleteAll(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      setShowDeleteAllConfirm(false);
    },
    onError: (error) => {
      console.error('Failed to delete all workflows:', error);
    },
  });

  // Helper function to generate approval data based on workflow risk and context
  const generateApprovalData = (workflow: GranularWorkflow) => {
    const baseData = {
      approval_timestamp: new Date().toISOString(),
      workflow_type: workflow.workflow_type,
      risk_level: workflow.risk_level
    };

    switch (workflow.risk_level) {
      case 'LOW':
        return {
          ...baseData,
          approved_by: "user",
          reasoning: "Standard approval for low-risk action item per operational guidelines. Minimal compliance requirements met."
        };
      
      case 'MEDIUM':
        return {
          ...baseData,
          approved_by: "supervisor_user",
          reasoning: `Reviewed ${workflow.workflow_type.toLowerCase()} action item. Customer situation qualifies for assistance based on documented case details. Approval granted per policy guidelines and compliance requirements. Risk assessment completed.`
        };
      
      case 'HIGH':
        return {
          ...baseData,
          approved_by: "manager_user",
          reasoning: `Executive approval for high-risk ${workflow.workflow_type.toLowerCase()} action. Compliance review completed. Customer situation warrants exceptional handling per escalation protocol and risk management guidelines. Senior authority authorization provided.`
        };
      
      default:
        return {
          ...baseData,
          approved_by: "user",
          reasoning: "Standard approval for action item per operational guidelines."
        };
    }
  };

  // Approve workflow mutation
  const approveWorkflowMutation = useMutation({
    mutationFn: ({ id, workflow }: { id: string; workflow: GranularWorkflow }) => {
      const approvalData = generateApprovalData(workflow);
      return workflowApi.approve(id, approvalData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      console.error('Error approving workflow:', error);
      alert('Failed to approve workflow: ' + (error?.detail || 'Unknown error'));
    },
  });

  // Reject workflow mutation
  const rejectWorkflowMutation = useMutation({
    mutationFn: (id: string) => workflowApi.reject(id, { rejected_by: "user", reason: "Manual rejection" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      console.error('Error rejecting workflow:', error);
      alert('Failed to reject workflow: ' + (error?.detail || 'Unknown error'));
    },
  });

  // Execute workflow mutation
  const executeWorkflowMutation = useMutation({
    mutationFn: (id: string) => workflowApi.execute(id, { executed_by: "user" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      console.error('Error executing workflow:', error);
      alert('Failed to execute workflow: ' + (error?.detail || 'Unknown error'));
    },
  });

  // Execute all workflows mutation
  const executeAllWorkflowsMutation = useMutation({
    mutationFn: (data?: { workflow_type?: string }) => workflowApi.executeAll({ executed_by: "user", ...data }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: (error: any) => {
      console.error('Error executing all workflows:', error);
      alert('Failed to execute all workflows: ' + (error?.detail || 'Unknown error'));
    },
  });

  // Badge variant utility (future use)
  // const getStatusBadgeVariant = (status: string) => {
  //   switch (status) {
  //     case 'EXECUTED': return 'default';
  //     case 'AUTO_APPROVED': return 'secondary';
  //     case 'AWAITING_APPROVAL': return 'secondary';
  //     case 'REJECTED': return 'destructive';
  //     case 'PENDING_ASSESSMENT': return 'outline';
  //     default: return 'secondary';
  //   }
  // };

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'EXECUTED': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'AUTO_APPROVED': return 'text-green-600 bg-green-50 border-green-200';
      case 'AWAITING_APPROVAL': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'REJECTED': return 'text-red-600 bg-red-50 border-red-200';
      case 'PENDING_ASSESSMENT': return 'text-gray-600 bg-gray-50 border-gray-200';
      default: return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  const getRiskLevelColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'HIGH': return 'text-red-600 bg-red-50 border-red-200';
      case 'MEDIUM': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'LOW': return 'text-green-600 bg-green-50 border-green-200';
      default: return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  const getWorkflowTypeColor = (type: string) => {
    switch (type) {
      case 'BORROWER': return 'text-purple-600 bg-purple-50 border-purple-200';
      case 'ADVISOR': return 'text-blue-600 bg-blue-50 border-blue-200';
      case 'SUPERVISOR': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'LEADERSHIP': return 'text-red-600 bg-red-50 border-red-200';
      default: return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  const handleFilterChange = (type: string, value: string) => {
    if (type === 'status') {
      setStatusFilter(value);
      // Clear risk level filter when status is selected (API constraint)
      if (value && value !== "all") {
        setRiskLevelFilter("");
      }
    } else if (type === 'risk_level') {
      setRiskLevelFilter(value);
      // Clear status filter when risk level is selected (API constraint)
      if (value && value !== "all") {
        setStatusFilter("");
      }
    }
  };

  const handleDeleteClick = (workflowId: string) => {
    setWorkflowToDelete(workflowId);
    setShowDeleteConfirm(true);
  };

  const handleDeleteAll = () => {
    setShowDeleteAllConfirm(true);
  };

  const handleDeleteConfirm = () => {
    if (workflowToDelete) {
      deleteWorkflowMutation.mutate(workflowToDelete);
    }
  };

  const handleDeleteAllConfirm = () => {
    deleteAllWorkflowsMutation.mutate();
  };

  // Granular Workflow Components
  const GranularWorkflowHeader = ({ workflow }: { workflow: GranularWorkflow }) => (
    <Card>
      <CardHeader className="py-2 px-3">
        <CardTitle className="text-xs font-medium flex items-center gap-2">
          <Badge className={`text-xs h-5 ${getPriorityColor(workflow.workflow_data?.priority || 'normal')}`}>
            {(workflow.workflow_data?.priority || 'normal').toUpperCase()}
          </Badge>
          Action Details
        </CardTitle>
      </CardHeader>
      <CardContent className="py-2 px-3">
        <div className="space-y-2">
          <div>
            <div className="text-slate-600 text-xs">Action Item</div>
            <div className="font-medium text-sm">{workflow.workflow_data?.action_item || 'No action item specified'}</div>
          </div>
          <div className="grid grid-cols-3 gap-2 text-xs">
            <div>
              <div className="text-slate-600">Timeline</div>
              <div className="font-medium">{workflow.workflow_data?.timeline || 'TBD'}</div>
            </div>
            <div>
              <div className="text-slate-600">Type</div>
              <Badge className="text-xs h-5">{workflow.workflow_type}</Badge>
            </div>
            <div>
              <div className="text-slate-600">Duration</div>
              <div className="font-medium">{workflow.workflow_data?.estimated_duration || 'TBD'}</div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const ActionDescription = ({ workflow }: { workflow: GranularWorkflow }) => (
    <Card>
      <CardHeader className="py-2 px-3">
        <CardTitle className="text-xs font-medium flex items-center gap-1">
          <Info className="h-3 w-3" />
          Description & Context
        </CardTitle>
      </CardHeader>
      <CardContent className="py-2 px-3">
        <p className="text-xs text-slate-700 leading-relaxed">
          {workflow.workflow_data?.description || 'No description provided'}
        </p>
      </CardContent>
    </Card>
  );

  const ExecutionSteps = ({ workflow }: { workflow: GranularWorkflow }) => (
    <Card>
      <CardHeader className="py-2 px-3">
        <CardTitle className="text-xs font-medium flex items-center gap-1">
          <CheckCircle className="h-3 w-3" />
          Execution Steps
        </CardTitle>
      </CardHeader>
      <CardContent className="py-2 px-3">
        {workflow.workflow_data?.steps && workflow.workflow_data.steps.length > 0 ? (
          <div className="space-y-1">
            {workflow.workflow_data.steps.map((step, index) => (
              <div key={index} className="flex items-center gap-2 text-xs">
                <div className="w-4 h-4 border border-slate-300 rounded flex items-center justify-center text-xs">
                  {index + 1}
                </div>
                <span className="text-slate-700">{step}</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-xs text-slate-500 italic">
            No specific steps defined. Follow standard procedures for: {workflow.workflow_data?.action_item || 'this task'}
          </div>
        )}
      </CardContent>
    </Card>
  );

  const AssignmentDetails = ({ workflow }: { workflow: GranularWorkflow }) => (
    <Card>
      <CardHeader className="py-2 px-3">
        <CardTitle className="text-xs font-medium flex items-center gap-1">
          <Users className="h-3 w-3" />
          Assignment & Dependencies
        </CardTitle>
      </CardHeader>
      <CardContent className="py-2 px-3">
        <div className="space-y-2 text-xs">
          <div>
            <div className="text-slate-600">Assigned To</div>
            <div className="font-medium">{workflow.workflow_data?.assigned_to || 'Unassigned'}</div>
          </div>
          {workflow.workflow_data?.dependencies && workflow.workflow_data.dependencies.length > 0 && (
            <div>
              <div className="text-slate-600 mb-1">Dependencies</div>
              <div className="space-y-1">
                {workflow.workflow_data.dependencies.map((dep, index) => (
                  <div key={index} className="flex items-center gap-1">
                    <AlertTriangle className="h-3 w-3 text-orange-500" />
                    <span className="text-slate-700">{dep}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );

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
          Error loading workflows: {(error as any)?.detail || 'Unknown error'}
        </div>
      </div>
    );
  }

  // Render workflow details view for any selected workflow
  if (selectedWorkflowId && selectedWorkflow) {
    const workflow = selectedWorkflow as any; // Cast to any for comprehensive API fields
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold">Workflow Details • {selectedWorkflowId}</h2>
            <p className="text-xs text-slate-600">Comprehensive workflow intelligence and execution details</p>
          </div>
          <div className="flex items-center gap-1">
            <Button 
              onClick={() => setSelectedWorkflowId(null)} 
              variant="outline"
              size="sm"
              className="h-7 text-xs px-2"
            >
              Back to List
            </Button>
          </div>
        </div>

        {/* Conditional rendering based on workflow type */}
        {isGranularWorkflow(workflow) ? (
          /* Granular Workflow Layout */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
            <GranularWorkflowHeader workflow={workflow} />
            <ActionDescription workflow={workflow} />
            <ExecutionSteps workflow={workflow} />
            <AssignmentDetails workflow={workflow} />
          </div>
        ) : (
          /* Meta Workflow Layout (Existing) */
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-2">
            {/* Core Information */}
            <Card>
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Core Information</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-600">Workflow ID</div>
                    <div className="font-medium">{workflow.id}</div>
                  </div>
                  <div>
                    <div className="text-slate-600">Type</div>
                    <Badge className={`text-xs h-5 ${getWorkflowTypeColor(workflow.workflow_type)}`}>
                      {workflow.workflow_type}
                    </Badge>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-600">Plan ID</div>
                    <button
                      onClick={() => goToPlan?.(workflow.plan_id)}
                      className="text-blue-600 hover:text-blue-800 font-medium underline text-xs"
                    >
                      {workflow.plan_id}
                    </button>
                  </div>
                  <div>
                    <div className="text-slate-600">Analysis ID</div>
                    <div className="font-medium">{workflow.analysis_id}</div>
                  </div>
                </div>
                <div>
                  <div className="text-slate-600">Transcript ID</div>
                  <div className="font-medium">{workflow.transcript_id}</div>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-600">Created</div>
                    <div className="font-medium">{new Date(workflow.created_at).toLocaleDateString()}</div>
                  </div>
                  <div>
                    <div className="text-slate-600">Updated</div>
                    <div className="font-medium">{new Date(workflow.updated_at).toLocaleDateString()}</div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Status & Risk */}
          <Card>
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Status & Risk Assessment</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="text-slate-600">Status</div>
                    <Badge className={`text-xs h-5 ${getStatusBadgeColor(workflow.status)}`}>
                      {workflow.status.replace(/_/g, ' ')}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-slate-600">Risk Level</div>
                    <Badge className={`text-xs h-5 ${getRiskLevelColor(workflow.risk_level)}`}>
                      {workflow.risk_level}
                    </Badge>
                  </div>
                </div>
                {workflow.risk_reasoning && (
                  <div className="border-t pt-2">
                    <div className="flex items-center gap-1 text-slate-600 mb-2">
                      <Shield className="h-3 w-3" />
                      <span className="font-medium">Risk Assessment</span>
                    </div>
                    <div className="bg-gradient-to-r from-red-50 to-orange-50 border border-red-200 rounded-lg p-3 space-y-2">
                      {/* Risk Level Indicator */}
                      <div className="flex items-center gap-2 mb-2">
                        {getRiskLevelIcon(workflow.risk_level)}
                        <Badge className={`text-xs h-5 ${getRiskLevelColor(workflow.risk_level)}`}>
                          {workflow.risk_level || 'UNKNOWN'} RISK
                        </Badge>
                      </div>
                      
                      {/* Parse and display risk factors with robust parsing */}
                      {(() => {
                        const operationalComplexity = parseRiskFactor(workflow.risk_reasoning, 'operational_complexity');
                        const customerImpact = parseRiskFactor(workflow.risk_reasoning, 'customer_impact');
                        const regulatoryCompliance = parseRiskFactor(workflow.risk_reasoning, 'regulatory_compliance');
                        const executionDifficulty = parseRiskFactor(workflow.risk_reasoning, 'execution_difficulty');
                        
                        const hasStructuredData = operationalComplexity || customerImpact || regulatoryCompliance || executionDifficulty;
                        
                        return (
                          <>
                            {operationalComplexity && (
                              <div className="bg-white rounded p-2 border-l-2 border-red-300">
                                <div className="flex items-center gap-1 text-red-700 font-medium text-xs mb-1">
                                  <Info className="h-3 w-3" />
                                  Operational Complexity
                                </div>
                                <p className="text-xs text-slate-700 leading-relaxed">
                                  {operationalComplexity}
                                </p>
                              </div>
                            )}
                            
                            {customerImpact && (
                              <div className="bg-white rounded p-2 border-l-2 border-orange-300">
                                <div className="flex items-center gap-1 text-orange-700 font-medium text-xs mb-1">
                                  <Users className="h-3 w-3" />
                                  Customer Impact
                                </div>
                                <p className="text-xs text-slate-700 leading-relaxed">
                                  {customerImpact}
                                </p>
                              </div>
                            )}
                            
                            {regulatoryCompliance && (
                              <div className="bg-white rounded p-2 border-l-2 border-blue-300">
                                <div className="flex items-center gap-1 text-blue-700 font-medium text-xs mb-1">
                                  <Shield className="h-3 w-3" />
                                  Regulatory Compliance
                                </div>
                                <p className="text-xs text-slate-700 leading-relaxed">
                                  {regulatoryCompliance}
                                </p>
                              </div>
                            )}
                            
                            {executionDifficulty && (
                              <div className="bg-white rounded p-2 border-l-2 border-purple-300">
                                <div className="flex items-center gap-1 text-purple-700 font-medium text-xs mb-1">
                                  <Clock className="h-3 w-3" />
                                  Execution Difficulty
                                </div>
                                <p className="text-xs text-slate-700 leading-relaxed">
                                  {executionDifficulty}
                                </p>
                              </div>
                            )}
                            
                            {/* Fallback for unstructured content */}
                            {!hasStructuredData && (
                              <div className="bg-white rounded p-2 border-l-2 border-gray-300">
                                <p className="text-xs text-slate-700 leading-relaxed">
                                  {typeof workflow.risk_reasoning === 'string' ? workflow.risk_reasoning : JSON.stringify(workflow.risk_reasoning, null, 2)}
                                </p>
                              </div>
                            )}
                          </>
                        );
                      })()}
                    </div>
                  </div>
                )}
                
                {workflow.approval_reasoning && (
                  <div className="border-t pt-2">
                    <div className="flex items-center gap-1 text-slate-600 mb-2">
                      <CheckCircle className="h-3 w-3" />
                      <span className="font-medium">Approval Assessment</span>
                    </div>
                    <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-3">
                      <div className="bg-white rounded p-2 border-l-2 border-green-300">
                        <div className="flex items-center gap-1 text-green-700 font-medium text-xs mb-1">
                          <Info className="h-3 w-3" />
                          Decision Rationale
                        </div>
                        <p className="text-xs text-slate-700 leading-relaxed">
                          {workflow.approval_reasoning}
                        </p>
                      </div>
                      
                      {/* Approval indicators */}
                      <div className="mt-2 flex items-center gap-2">
                        {workflow.requires_human_approval ? (
                          <div className="flex items-center gap-1 text-orange-600">
                            <AlertTriangle className="h-3 w-3" />
                            <span className="text-xs font-medium">Human Review Required</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1 text-green-600">
                            <CheckCircle className="h-3 w-3" />
                            <span className="text-xs font-medium">Auto-approval Eligible</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Actions & Execution */}
          <Card>
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium flex items-center gap-1">
                <Users className="h-3 w-3" />
                Actions & Execution
              </CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                <div>
                  <div className="text-slate-600">Priority</div>
                  <Badge variant={workflow.workflow_data?.priority === 'high' ? 'destructive' : 'secondary'} className="text-xs h-5">
                    {workflow.workflow_data?.priority || 'normal'}
                  </Badge>
                </div>
                {workflow.workflow_data?.estimated_time && (
                  <div>
                    <div className="text-slate-600 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Estimated Time
                    </div>
                    <div className="font-medium">{workflow.workflow_data.estimated_time}</div>
                  </div>
                )}
                <div>
                  <div className="text-slate-600">Actions ({workflow.workflow_data?.actions?.length || 0})</div>
                  <div className="space-y-1">
                    {workflow.workflow_data?.actions?.map((action: string, index: number) => (
                      <div key={index} className="text-slate-700 bg-slate-50 rounded p-2 border text-xs flex items-start gap-2">
                        <span className="text-slate-500 font-mono text-xs mt-0.5">{index + 1}.</span>
                        <span>{action}</span>
                      </div>
                    )) || <div className="text-slate-500">No actions defined</div>}
                  </div>
                </div>
                {workflow.workflow_data?.dependencies && workflow.workflow_data.dependencies.length > 0 && (
                  <div>
                    <div className="text-slate-600">Dependencies</div>
                    <div className="space-y-1">
                      {workflow.workflow_data.dependencies.map((dep: string, index: number) => (
                        <Badge key={index} variant="outline" className="text-xs mr-1 mb-1">
                          {dep}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Approval Workflow */}
          <Card>
            <CardHeader className="py-2 px-3">
              <CardTitle className="text-xs font-medium">Approval Workflow</CardTitle>
            </CardHeader>
            <CardContent className="py-2 px-3">
              <div className="space-y-2 text-xs">
                {workflow.assigned_approver && (
                  <div>
                    <div className="text-slate-600">Assigned Approver</div>
                    <div className="font-medium">{workflow.assigned_approver}</div>
                  </div>
                )}
                {workflow.approved_by && (
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <div className="text-slate-600">Approved By</div>
                      <div className="font-medium">{workflow.approved_by}</div>
                    </div>
                    <div>
                      <div className="text-slate-600">Approved At</div>
                      <div className="font-medium">{workflow.approved_at ? new Date(workflow.approved_at).toLocaleDateString() : '-'}</div>
                    </div>
                  </div>
                )}
                {workflow.rejected_by && (
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <div className="text-slate-600">Rejected By</div>
                      <div className="font-medium">{workflow.rejected_by}</div>
                    </div>
                    <div>
                      <div className="text-slate-600">Rejected At</div>
                      <div className="font-medium">{workflow.rejected_at ? new Date(workflow.rejected_at).toLocaleDateString() : '-'}</div>
                    </div>
                  </div>
                )}
                {workflow.rejection_reason && (
                  <div>
                    <div className="text-slate-600">Rejection Reason</div>
                    <div className="text-slate-700 bg-red-50 rounded p-2 border border-red-200 text-xs">
                      {workflow.rejection_reason}
                    </div>
                  </div>
                )}
                {workflow.executed_at && (
                  <div>
                    <div className="text-slate-600">Executed At</div>
                    <div className="font-medium">{new Date(workflow.executed_at).toLocaleDateString()}</div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Context Data */}
          {workflow.context_data && Object.keys(workflow.context_data).length > 0 && (
            <Card className="lg:col-span-2">
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-xs font-medium">Context Data</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="space-y-2 text-xs">
                  <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
                    {workflow.context_data.customer_risk_score && (
                      <div>
                        <div className="text-slate-600">Customer Risk Score</div>
                        <div className="font-medium">{(workflow.context_data.customer_risk_score * 100).toFixed(1)}%</div>
                      </div>
                    )}
                    {workflow.context_data.delinquency_days && (
                      <div>
                        <div className="text-slate-600">Delinquency Days</div>
                        <div className="font-medium">{workflow.context_data.delinquency_days}</div>
                      </div>
                    )}
                  </div>
                  {workflow.context_data.analysis_results && (
                    <div>
                      <div className="text-slate-600">Analysis Results</div>
                      <div className="text-slate-700 bg-slate-50 rounded p-2 border text-xs font-mono">
                        {JSON.stringify(workflow.context_data.analysis_results, null, 2)}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Execution Results */}
          {workflow.execution_results && (
            <Card className="lg:col-span-2">
              <CardHeader className="py-2 px-3">
                <CardTitle className="text-xs font-medium">Execution Results</CardTitle>
              </CardHeader>
              <CardContent className="py-2 px-3">
                <div className="text-slate-700 bg-slate-50 rounded p-2 border text-xs font-mono">
                  {JSON.stringify(workflow.execution_results, null, 2)}
                </div>
              </CardContent>
            </Card>
          )}
        </div>
        )}
      </div>
    );
  }


  return (
    <div className="space-y-3">
      {/* Header with filters */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-sm font-bold">Workflow Management</h2>
          <p className="text-xs text-slate-600">Orchestration and approval processes for action plans</p>
        </div>
        <div className="flex items-center gap-1">
          <Button onClick={() => refetch()} variant="outline" size="sm" className="h-7 text-xs px-2">
            <RefreshCw className="h-3 w-3" />
            Refresh
          </Button>
          {workflows.filter(w => w.status === 'AUTO_APPROVED' || w.status === 'APPROVED').length > 0 && (
            <Button
              onClick={() => executeAllWorkflowsMutation.mutate()}
              variant="outline"
              size="sm"
              className="h-7 text-xs px-2 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
              disabled={executeAllWorkflowsMutation.isPending}
            >
              <Play className="h-3 w-3 mr-1" />
              {executeAllWorkflowsMutation.isPending ? 'Executing...' : 'Execute All Approved'}
            </Button>
          )}
          {workflows.length > 0 && (
            <Button
              onClick={handleDeleteAll}
              variant="outline"
              size="sm"
              className="h-7 text-xs px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
              disabled={deleteAllWorkflowsMutation.isPending}
            >
              {deleteAllWorkflowsMutation.isPending ? 'Deleting...' : 'Delete All'}
            </Button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 items-end">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs text-slate-600">Filters:</span>
        </div>
        
        <Select value={statusFilter} onValueChange={(value) => handleFilterChange('status', value)}>
          <SelectTrigger className="w-40 h-7 text-xs">
            <SelectValue placeholder="All Statuses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Statuses</SelectItem>
            <SelectItem value="PENDING_ASSESSMENT">Pending Assessment</SelectItem>
            <SelectItem value="AWAITING_APPROVAL">Awaiting Approval</SelectItem>
            <SelectItem value="AUTO_APPROVED">Auto Approved</SelectItem>
            <SelectItem value="REJECTED">Rejected</SelectItem>
            <SelectItem value="EXECUTED">Executed</SelectItem>
          </SelectContent>
        </Select>

        <Select value={riskLevelFilter} onValueChange={(value) => handleFilterChange('risk_level', value)}>
          <SelectTrigger className="w-32 h-7 text-xs">
            <SelectValue placeholder="All Risk Levels" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Risk Levels</SelectItem>
            <SelectItem value="HIGH">High</SelectItem>
            <SelectItem value="MEDIUM">Medium</SelectItem>
            <SelectItem value="LOW">Low</SelectItem>
          </SelectContent>
        </Select>

        <Input
          type="number"
          placeholder="Limit"
          value={limitFilter}
          onChange={(e) => setLimitFilter(e.target.value)}
          className="w-20 h-7 text-xs"
          min="1"
          max="1000"
        />

        {(statusFilter || riskLevelFilter) && (
          <Button
            onClick={() => {
              setStatusFilter("");
              setRiskLevelFilter("");
            }}
            variant="outline"
            size="sm"
            className="h-7 text-xs px-2"
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Constraint notice */}
      {statusFilter && riskLevelFilter && (
        <div className="text-xs text-orange-600 bg-orange-50 border border-orange-200 rounded p-2">
          ⚠️ API constraint: Cannot filter by both status and risk level simultaneously. Please choose one filter type.
        </div>
      )}

      {/* Workflows table */}
      <Card>
        <CardHeader className="py-2 px-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-xs font-medium">
              Workflows ({workflows.length})
            </CardTitle>
            <CardDescription className="text-xs">
              Click workflow ID for details
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent className="py-2 px-3">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Workflow ID</th>
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Type</th>
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Status</th>
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Risk</th>
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Priority</th>
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Actions</th>
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Time Est</th>
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Created</th>
                  <th className="text-left py-1 px-2 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {workflows.length === 0 ? (
                  <tr>
                    <td colSpan={9} className="text-center py-8 text-slate-500">
                      No workflows found matching current filters
                    </td>
                  </tr>
                ) : (
                  workflows.map((workflow) => (
                    <tr key={workflow.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-1 px-2">
                        <button
                          onClick={() => setSelectedWorkflowId(workflow.id)}
                          className="text-blue-600 hover:text-blue-800 font-medium underline"
                        >
                          {workflow.id}
                        </button>
                      </td>
                      <td className="py-1 px-2">
                        <Badge className={`text-xs h-5 ${getWorkflowTypeColor(workflow.workflow_type)}`}>
                          {workflow.workflow_type}
                        </Badge>
                      </td>
                      <td className="py-1 px-2">
                        <Badge className={`text-xs h-5 ${getStatusBadgeColor(workflow.status)}`}>
                          {workflow.status.replace(/_/g, ' ')}
                        </Badge>
                      </td>
                      <td className="py-1 px-2">
                        <Badge className={`text-xs h-5 ${getRiskLevelColor(workflow.risk_level)}`}>
                          {workflow.risk_level}
                        </Badge>
                      </td>
                      <td className="py-1 px-2">
                        <Badge 
                          variant={workflow.workflow_data?.priority === 'high' ? 'destructive' : 'secondary'} 
                          className="text-xs h-5"
                        >
                          {workflow.workflow_data?.priority || 'normal'}
                        </Badge>
                      </td>
                      <td className="py-1 px-2">
                        <span className="font-medium">{workflow.workflow_data?.actions?.length || 0}</span>
                      </td>
                      <td className="py-1 px-2">
                        {workflow.workflow_data?.estimated_time || '-'}
                      </td>
                      <td className="py-1 px-2">
                        {new Date(workflow.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-1 px-2">
                        <div className="flex items-center gap-1">
                          {/* Status-based execution buttons */}
                          {workflow.status === 'AWAITING_APPROVAL' && (
                            <>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 text-green-600 hover:text-green-700 hover:bg-green-50"
                                onClick={() => approveWorkflowMutation.mutate({ id: workflow.id, workflow })}
                                disabled={approveWorkflowMutation.isPending}
                                title="Approve"
                              >
                                <Check className="h-3 w-3" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 w-6 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                                onClick={() => rejectWorkflowMutation.mutate(workflow.id)}
                                disabled={rejectWorkflowMutation.isPending}
                                title="Reject"
                              >
                                <X className="h-3 w-3" />
                              </Button>
                            </>
                          )}
                          
                          {workflow.status === 'AUTO_APPROVED' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                              onClick={() => executeWorkflowMutation.mutate(workflow.id)}
                              disabled={executeWorkflowMutation.isPending}
                              title="Execute"
                            >
                              <Play className="h-3 w-3" />
                            </Button>
                          )}
                          
                          {workflow.status === 'APPROVED' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                              onClick={() => executeWorkflowMutation.mutate(workflow.id)}
                              disabled={executeWorkflowMutation.isPending}
                              title="Execute"
                            >
                              <Play className="h-3 w-3" />
                            </Button>
                          )}
                          
                          {workflow.status === 'EXECUTED' && (
                            <Badge className="text-xs h-5 bg-green-100 text-green-700 border-green-200">
                              ✓ Done
                            </Badge>
                          )}
                          
                          {workflow.status === 'REJECTED' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 text-gray-600 hover:text-blue-700 hover:bg-blue-50"
                              onClick={() => approveWorkflowMutation.mutate({ id: workflow.id, workflow })}
                              disabled={approveWorkflowMutation.isPending}
                              title="Retry (Approve)"
                            >
                              <RotateCcw className="h-3 w-3" />
                            </Button>
                          )}
                          
                          {/* Always show delete button (unless executing) */}
                          {workflow.status !== 'EXECUTED' && (
                            <Button
                              variant="ghost"
                              size="sm"
                              className="h-6 w-6 p-0 text-gray-400 hover:text-red-600 ml-1"
                              onClick={() => handleDeleteClick(workflow.id)}
                              disabled={deleteWorkflowMutation.isPending}
                              title="Delete"
                            >
                              <Trash2 className="h-3 w-3" />
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Delete Confirmation Dialog */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white p-4 rounded-lg max-w-md mx-4">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              <h3 className="text-sm font-medium">Delete Workflow</h3>
            </div>
            <p className="text-xs text-gray-600 mb-4">
              Are you sure you want to delete workflow {workflowToDelete}? This action cannot be undone.
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
                disabled={deleteWorkflowMutation.isPending}
              >
                {deleteWorkflowMutation.isPending ? 'Deleting...' : 'Delete'}
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
              <h3 className="text-sm font-medium">Delete All Workflows</h3>
            </div>
            <p className="text-xs text-gray-600 mb-4">
              Are you sure you want to delete all workflows? This will permanently remove all {workflows.length} workflows and cannot be undone.
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
                disabled={deleteAllWorkflowsMutation.isPending}
              >
                {deleteAllWorkflowsMutation.isPending ? 'Deleting...' : 'Delete All'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}