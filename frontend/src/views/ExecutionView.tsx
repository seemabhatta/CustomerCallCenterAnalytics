import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { executionApi } from "@/api/client";
import { Execution } from "@/types";
import { 
  Play, 
  CheckCircle2, 
  XCircle, 
  Clock, 
  AlertTriangle,
  FileText 
} from "lucide-react";

// Mock execution data until real API is connected
const mockExecutions: Execution[] = [
  { 
    id: "JOB-1", 
    type: "email", 
    status: "COMPLETED", 
    started_at: "2025-09-12T16:45:00Z", 
    completed_at: "2025-09-12T16:45:02Z",
    duration_sec: 2, 
    logs: ["Queued SMTP", "Sent 200 OK"],
    workflow_id: "WF-1001"
  },
  { 
    id: "JOB-2", 
    type: "crm-note", 
    status: "FAILED", 
    started_at: "2025-09-12T16:46:10Z", 
    completed_at: "2025-09-12T16:46:11Z",
    duration_sec: 1, 
    logs: ["CRM timeout", "Retry failed"],
    workflow_id: "WF-1002",
    error: "Connection timeout after 30s"
  },
  { 
    id: "JOB-3", 
    type: "notification", 
    status: "RUNNING", 
    started_at: "2025-09-12T16:47:00Z", 
    duration_sec: 0, 
    logs: ["Started notification job", "Processing recipients..."],
    workflow_id: "WF-1003"
  },
  { 
    id: "JOB-4", 
    type: "audit", 
    status: "PENDING", 
    started_at: "2025-09-12T16:48:00Z", 
    duration_sec: 0, 
    logs: ["Queued for execution"],
    workflow_id: "WF-1004"
  },
];

export function ExecutionView() {
  const [logDialog, setLogDialog] = useState<{ open: boolean; execution: Execution | null }>({
    open: false,
    execution: null,
  });

  // In a real implementation, this would fetch from the API
  // const { data: executions = [], isLoading, error } = useQuery({
  //   queryKey: ['executions'],
  //   queryFn: () => executionApi.getStatistics(),
  // });

  // Using mock data for now
  const executions = mockExecutions;
  const isLoading = false;
  const error = null;

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed':
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-600" />;
      case 'running':
        return <Play className="h-4 w-4 text-blue-600" />;
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-600" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-600" />;
    }
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'completed': return 'default';
      case 'failed': return 'destructive';
      case 'running': return 'default';
      case 'pending': return 'secondary';
      default: return 'secondary';
    }
  };

  const handleViewLogs = (execution: Execution) => {
    setLogDialog({ open: true, execution });
  };

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="animate-pulse">
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-600">
          Error loading executions: {(error as any)?.detail || 'Unknown error'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Execution History</h2>
        <Badge variant="secondary">{executions.length} execution(s)</Badge>
      </div>

      <div className="overflow-hidden rounded-2xl border">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left py-2 px-3">Job</th>
              <th className="text-left py-2 px-3">Type</th>
              <th className="text-left py-2 px-3">Status</th>
              <th className="text-left py-2 px-3">Workflow</th>
              <th className="text-left py-2 px-3">Started</th>
              <th className="text-left py-2 px-3">Duration</th>
              <th className="text-left py-2 px-3">Error</th>
              <th className="text-right py-2 px-3">Logs</th>
            </tr>
          </thead>
          <tbody>
            {executions.map((execution: Execution) => (
              <tr key={execution.id} className="border-b hover:bg-slate-50">
                <td className="py-2 px-3 font-medium text-slate-900">
                  {execution.id}
                </td>
                <td className="py-2 px-3">
                  <Badge variant="outline" className="text-xs">
                    {execution.type}
                  </Badge>
                </td>
                <td className="py-2 px-3">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(execution.status)}
                    <Badge variant={getStatusBadgeVariant(execution.status)}>
                      {execution.status}
                    </Badge>
                  </div>
                </td>
                <td className="py-2 px-3">
                  {execution.workflow_id || '-'}
                </td>
                <td className="py-2 px-3">
                  {new Date(execution.started_at).toLocaleString()}
                </td>
                <td className="py-2 px-3">
                  {execution.duration_sec ? `${execution.duration_sec}s` : '-'}
                </td>
                <td className="py-2 px-3">
                  {execution.error ? (
                    <div className="text-red-600 text-xs max-w-xs truncate" title={execution.error}>
                      {execution.error}
                    </div>
                  ) : '-'}
                </td>
                <td className="py-2 px-3 text-right">
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => handleViewLogs(execution)}
                    className="gap-1"
                  >
                    <FileText className="h-3 w-3" />
                    View
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {executions.length === 0 && (
          <div className="p-8 text-center text-slate-500">
            No executions found.
          </div>
        )}
      </div>

      {/* Logs Dialog */}
      <Dialog open={logDialog.open} onOpenChange={(open) => setLogDialog({ open, execution: null })}>
        <DialogContent className="max-w-2xl">
          {logDialog.execution && (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Logs • {logDialog.execution.id}
                </DialogTitle>
                <DialogDescription className="flex items-center gap-4">
                  <span>{logDialog.execution.type}</span>
                  <div className="flex items-center gap-1">
                    {getStatusIcon(logDialog.execution.status)}
                    <span>{logDialog.execution.status}</span>
                  </div>
                </DialogDescription>
              </DialogHeader>
              
              <div className="space-y-4">
                {/* Execution Details */}
                <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
                  <div>
                    <div className="text-xs text-slate-500">Started</div>
                    <div className="text-sm">
                      {new Date(logDialog.execution.started_at).toLocaleString()}
                    </div>
                  </div>
                  {logDialog.execution.completed_at && (
                    <div>
                      <div className="text-xs text-slate-500">Completed</div>
                      <div className="text-sm">
                        {new Date(logDialog.execution.completed_at).toLocaleString()}
                      </div>
                    </div>
                  )}
                  <div>
                    <div className="text-xs text-slate-500">Duration</div>
                    <div className="text-sm">
                      {logDialog.execution.duration_sec ? 
                        `${logDialog.execution.duration_sec}s` : 
                        'In progress...'
                      }
                    </div>
                  </div>
                  {logDialog.execution.workflow_id && (
                    <div>
                      <div className="text-xs text-slate-500">Workflow</div>
                      <div className="text-sm">{logDialog.execution.workflow_id}</div>
                    </div>
                  )}
                </div>

                {/* Error Details */}
                {logDialog.execution.error && (
                  <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                    <div className="text-xs text-red-600 font-medium mb-1">Error</div>
                    <div className="text-sm text-red-800">{logDialog.execution.error}</div>
                  </div>
                )}

                {/* Logs */}
                <div className="rounded-xl bg-slate-50 border p-3 text-xs overflow-auto max-h-[60vh]">
                  <div className="text-xs text-slate-500 font-medium mb-2">Execution Logs</div>
                  {logDialog.execution.logs.map((log, i) => (
                    <div key={i} className="py-1 border-l-2 border-slate-300 pl-2 mb-1">
                      <span className="text-slate-400">[{i + 1}]</span> {log}
                    </div>
                  ))}
                  {logDialog.execution.logs.length === 0 && (
                    <div className="text-slate-400">No logs available</div>
                  )}
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}