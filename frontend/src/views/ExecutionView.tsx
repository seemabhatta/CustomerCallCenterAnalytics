import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Trash2, AlertTriangle, RefreshCw, ArrowLeft } from "lucide-react";
import { executionApi } from "@/api/client";
import { Execution, ExecutionDetails } from "@/types";

export function ExecutionView() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false);
  const [executionToDelete, setExecutionToDelete] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState("");
  const [executorTypeFilter, setExecutorTypeFilter] = useState("");
  const queryClient = useQueryClient();

  // Fetch executions
  const { data: executions = [], isLoading, error, refetch } = useQuery({
    queryKey: ['executions', statusFilter, executorTypeFilter],
    queryFn: () => executionApi.list({
      status: statusFilter || undefined,
      executor_type: executorTypeFilter || undefined,
    }),
  });

  // Selected execution details
  const { data: selectedExecution } = useQuery({
    queryKey: ['execution', selectedExecutionId],
    queryFn: () => executionApi.getById(selectedExecutionId!),
    enabled: !!selectedExecutionId,
  });

  // Delete execution mutation
  const deleteExecutionMutation = useMutation({
    mutationFn: (id: string) => executionApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      setShowDeleteConfirm(false);
      setExecutionToDelete(null);
      // Clear selected execution if it was deleted
      if (executionToDelete === selectedExecutionId) {
        setSelectedExecutionId(null);
      }
    },
    onError: (error) => {
      console.error('Failed to delete execution:', error);
    },
  });

  // Delete all executions mutation
  const deleteAllExecutionsMutation = useMutation({
    mutationFn: () => executionApi.deleteAll({
      status: statusFilter || undefined,
      executor_type: executorTypeFilter || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['executions'] });
      setShowDeleteAllConfirm(false);
    },
    onError: (error) => {
      console.error('Failed to delete all executions:', error);
    },
  });

  // Filter executions based on search query
  const filteredExecutions = executions.filter((execution: Execution) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      execution.id?.toLowerCase().includes(query) ||
      execution.workflow_id?.toLowerCase().includes(query) ||
      execution.executor_type?.toLowerCase().includes(query) ||
      execution.executed_by?.toLowerCase().includes(query)
    );
  });

  const handleDeleteClick = (executionId: string) => {
    setExecutionToDelete(executionId);
    setShowDeleteConfirm(true);
  };

  const handleDeleteAll = () => {
    setShowDeleteAllConfirm(true);
  };

  const handleDeleteConfirm = () => {
    if (executionToDelete) {
      deleteExecutionMutation.mutate(executionToDelete);
    }
  };

  const handleDeleteAllConfirm = () => {
    deleteAllExecutionsMutation.mutate();
  };

  const handleExecutionClick = (executionId: string) => {
    setSelectedExecutionId(executionId);
  };

  const handleCloseExecutionView = () => {
    setSelectedExecutionId(null);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'success': return 'default';
      case 'failed': return 'destructive';
      case 'pending': return 'secondary';
      case 'running': return 'secondary';
      default: return 'outline';
    }
  };

  const getExecutorTypeBadge = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'email': return 'default';
      case 'crm': return 'secondary';
      case 'task': return 'outline';
      case 'notification': return 'secondary';
      default: return 'outline';
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
      <div className="text-center py-8">
        <p className="text-red-500 text-sm mb-4">Failed to load executions</p>
        <Button onClick={() => refetch()} variant="outline" size="sm">
          Try Again
        </Button>
      </div>
    );
  }

  // Show execution details if selected
  if (selectedExecutionId && selectedExecution) {
    const details = selectedExecution;
    const execution = details.execution_record;

    return (
      <div className="space-y-4">
        <div className="flex items-center gap-2">
          <Button
            onClick={handleCloseExecutionView}
            variant="ghost"
            size="sm"
            className="h-7 w-7 p-0"
          >
            <ArrowLeft className="h-3 w-3" />
          </Button>
          <h3 className="text-sm font-medium">Execution Details: {execution.id}</h3>
        </div>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Execution Record</CardTitle>
          </CardHeader>
          <CardContent className="text-xs space-y-3">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <div className="font-medium text-slate-600 mb-1">Workflow ID</div>
                <div className="font-mono">{execution.workflow_id}</div>
              </div>
              <div>
                <div className="font-medium text-slate-600 mb-1">Executor Type</div>
                <Badge variant={getExecutorTypeBadge(execution.executor_type)} className="text-xs">
                  {execution.executor_type}
                </Badge>
              </div>
              <div>
                <div className="font-medium text-slate-600 mb-1">Status</div>
                <Badge variant={getStatusBadgeVariant(execution.execution_status)} className="text-xs">
                  {execution.execution_status}
                </Badge>
              </div>
              <div>
                <div className="font-medium text-slate-600 mb-1">Executed By</div>
                <div>{execution.executed_by}</div>
              </div>
              <div>
                <div className="font-medium text-slate-600 mb-1">Duration</div>
                <div>{execution.execution_duration_ms}ms</div>
              </div>
              <div>
                <div className="font-medium text-slate-600 mb-1">Mock Execution</div>
                <div>{execution.mock_execution ? 'Yes' : 'No'}</div>
              </div>
            </div>

            {execution.error_message && (
              <div>
                <div className="font-medium text-slate-600 mb-1">Error Message</div>
                <div className="text-red-600 bg-red-50 p-2 rounded text-xs">
                  {execution.error_message}
                </div>
              </div>
            )}

            <div>
              <div className="font-medium text-slate-600 mb-1">Execution Payload</div>
              <pre className="bg-slate-50 p-2 rounded text-xs overflow-x-auto">
                {JSON.stringify(execution.execution_payload, null, 2)}
              </pre>
            </div>

            {Object.keys(execution.metadata).length > 0 && (
              <div>
                <div className="font-medium text-slate-600 mb-1">Metadata</div>
                <pre className="bg-slate-50 p-2 rounded text-xs overflow-x-auto">
                  {JSON.stringify(execution.metadata, null, 2)}
                </pre>
              </div>
            )}
          </CardContent>
        </Card>

        {details.audit_trail && details.audit_trail.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Audit Trail</CardTitle>
            </CardHeader>
            <CardContent className="text-xs">
              <div className="space-y-2">
                {details.audit_trail.map((event) => (
                  <div key={event.id} className="border-l-2 border-slate-200 pl-3 py-1">
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-medium">{event.event_type}</span>
                      <span className="text-slate-500">
                        {new Date(event.event_timestamp).toLocaleString()}
                      </span>
                    </div>
                    <div className="text-slate-600 mb-1">{event.event_description}</div>
                    {event.event_data && (
                      <pre className="bg-slate-50 p-1 rounded text-xs">
                        {JSON.stringify(event.event_data, null, 2)}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with search and actions */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 flex-1">
          <Input
            placeholder="Search executions..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="h-8 text-xs max-w-xs"
          />
          
          {/* Status Filter */}
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="h-8 text-xs min-w-[120px]">
              <SelectValue placeholder="All Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Status</SelectItem>
              <SelectItem value="success">Success</SelectItem>
              <SelectItem value="failed">Failed</SelectItem>
              <SelectItem value="pending">Pending</SelectItem>
              <SelectItem value="running">Running</SelectItem>
            </SelectContent>
          </Select>

          {/* Executor Type Filter */}
          <Select value={executorTypeFilter} onValueChange={setExecutorTypeFilter}>
            <SelectTrigger className="h-8 text-xs min-w-[120px]">
              <SelectValue placeholder="All Types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All Types</SelectItem>
              <SelectItem value="email">Email</SelectItem>
              <SelectItem value="crm">CRM</SelectItem>
              <SelectItem value="task">Task</SelectItem>
              <SelectItem value="notification">Notification</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="flex items-center gap-1">
          <Button onClick={() => refetch()} variant="outline" size="sm" className="h-7 text-xs px-2">
            <RefreshCw className="h-3 w-3" />
            Refresh
          </Button>
          {executions.length > 0 && (
            <Button
              onClick={handleDeleteAll}
              variant="outline"
              size="sm"
              className="h-7 text-xs px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
              disabled={deleteAllExecutionsMutation.isPending}
            >
              {deleteAllExecutionsMutation.isPending ? 'Deleting...' : 'Delete All'}
            </Button>
          )}
        </div>
      </div>

      {/* Executions Table */}
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead className="border-b bg-slate-50">
                <tr>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">ID</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Workflow</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Type</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Status</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Executed By</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Duration</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Created</th>
                  <th className="text-left py-2 px-3 font-medium text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredExecutions.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-slate-500">
                      {searchQuery ? 'No executions match your search.' : 'No executions found.'}
                    </td>
                  </tr>
                ) : (
                  filteredExecutions.map((execution: Execution) => (
                    <tr key={execution.id} className="border-b hover:bg-slate-50">
                      <td className="py-2 px-3">
                        <button
                          onClick={() => handleExecutionClick(execution.id)}
                          className="font-mono text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {execution.id}
                        </button>
                      </td>
                      <td className="py-2 px-3">
                        <span className="font-mono text-xs">{execution.workflow_id}</span>
                      </td>
                      <td className="py-2 px-3">
                        <Badge variant={getExecutorTypeBadge(execution.executor_type)} className="text-xs">
                          {execution.executor_type}
                        </Badge>
                      </td>
                      <td className="py-2 px-3">
                        <Badge variant={getStatusBadgeVariant(execution.execution_status)} className="text-xs">
                          {execution.execution_status}
                        </Badge>
                      </td>
                      <td className="py-2 px-3">{execution.executed_by}</td>
                      <td className="py-2 px-3">{execution.execution_duration_ms}ms</td>
                      <td className="py-2 px-3">
                        {new Date(execution.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-2 px-3">
                        <Button
                          variant="ghost"
                          size="sm"
                          className="h-6 w-6 p-0 text-gray-500 hover:text-red-600"
                          onClick={() => handleDeleteClick(execution.id)}
                          disabled={deleteExecutionMutation.isPending}
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
      <Dialog open={showDeleteConfirm} onOpenChange={setShowDeleteConfirm}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              Delete Execution
            </DialogTitle>
            <DialogDescription className="text-xs">
              Are you sure you want to delete execution {executionToDelete}? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
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
              disabled={deleteExecutionMutation.isPending}
            >
              {deleteExecutionMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete All Confirmation Dialog */}
      <Dialog open={showDeleteAllConfirm} onOpenChange={setShowDeleteAllConfirm}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-sm">
              <AlertTriangle className="h-4 w-4 text-red-600" />
              Delete All Executions
            </DialogTitle>
            <DialogDescription className="text-xs">
              Are you sure you want to delete all {filteredExecutions.length} executions? 
              {(statusFilter || executorTypeFilter) && " (with current filters applied)"} 
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
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
              disabled={deleteAllExecutionsMutation.isPending}
            >
              {deleteAllExecutionsMutation.isPending ? 'Deleting...' : 'Delete All'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}