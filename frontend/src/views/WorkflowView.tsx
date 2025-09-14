import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { workflowApi } from '@/api/client';
import { WorkflowFilterParams } from '@/types';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { RefreshCw, Filter, Clock, Users, Trash2, AlertTriangle } from 'lucide-react';
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
                      {workflow.status.replace('_', ' ')}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-slate-600">Risk Level</div>
                    <Badge className={`text-xs h-5 ${getRiskLevelColor(workflow.risk_level)}`}>
                      {workflow.risk_level}
                    </Badge>
                  </div>
                </div>
                <div>
                  <div className="text-slate-600">Requires Human Approval</div>
                  <div className="font-medium">{workflow.requires_human_approval ? 'Yes' : 'No'}</div>
                </div>
                {workflow.risk_reasoning && (
                  <div>
                    <div className="text-slate-600">Risk Reasoning</div>
                    <div className="text-slate-700 bg-slate-50 rounded p-2 border text-xs">
                      {workflow.risk_reasoning}
                    </div>
                  </div>
                )}
                {workflow.approval_reasoning && (
                  <div>
                    <div className="text-slate-600">Approval Reasoning</div>
                    <div className="text-slate-700 bg-slate-50 rounded p-2 border text-xs">
                      {workflow.approval_reasoning}
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
                          {workflow.status.replace('_', ' ')}
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
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-gray-500 hover:text-red-600"
                          onClick={() => handleDeleteClick(workflow.id)}
                          disabled={deleteWorkflowMutation.isPending}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
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