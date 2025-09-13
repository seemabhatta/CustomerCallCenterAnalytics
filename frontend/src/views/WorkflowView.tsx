import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { workflowApi } from "@/api/client";
import { Workflow } from "@/types";
import { 
  Workflow as WorkflowIcon, 
  CheckCircle2, 
  Clock, 
  X, 
  Play,
  AlertTriangle 
} from "lucide-react";

export function WorkflowView() {
  const [approvalDialog, setApprovalDialog] = useState<{ open: boolean; workflow: Workflow | null }>({
    open: false,
    workflow: null,
  });
  const [rejectionDialog, setRejectionDialog] = useState<{ open: boolean; workflow: Workflow | null }>({
    open: false,
    workflow: null,
  });
  const [rejectionReason, setRejectionReason] = useState("");

  const queryClient = useQueryClient();

  // Fetch workflows
  const { data: workflows = [], isLoading, error } = useQuery({
    queryKey: ['workflows'],
    queryFn: () => workflowApi.list(),
  });

  // Approve workflow mutation
  const approveMutation = useMutation({
    mutationFn: ({ workflowId, approvedBy }: { workflowId: string; approvedBy: string }) =>
      workflowApi.approve(workflowId, { approved_by: approvedBy }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      setApprovalDialog({ open: false, workflow: null });
    },
  });

  // Reject workflow mutation
  const rejectMutation = useMutation({
    mutationFn: ({ workflowId, rejectedBy, reason }: { workflowId: string; rejectedBy: string; reason: string }) =>
      workflowApi.reject(workflowId, { rejected_by: rejectedBy, reason }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      setRejectionDialog({ open: false, workflow: null });
      setRejectionReason("");
    },
  });

  // Execute workflow mutation
  const executeMutation = useMutation({
    mutationFn: ({ workflowId, executedBy }: { workflowId: string; executedBy: string }) =>
      workflowApi.execute(workflowId, { executed_by: executedBy }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const handleApprove = (workflow: Workflow) => {
    setApprovalDialog({ open: true, workflow });
  };

  const handleReject = (workflow: Workflow) => {
    setRejectionDialog({ open: true, workflow });
  };

  const handleExecute = (workflow: Workflow) => {
    executeMutation.mutate({
      workflowId: workflow.id,
      executedBy: "current_user", // In real app, get from auth context
    });
  };

  const confirmApproval = () => {
    if (approvalDialog.workflow) {
      approveMutation.mutate({
        workflowId: approvalDialog.workflow.id,
        approvedBy: "current_user", // In real app, get from auth context
      });
    }
  };

  const confirmRejection = () => {
    if (rejectionDialog.workflow && rejectionReason.trim()) {
      rejectMutation.mutate({
        workflowId: rejectionDialog.workflow.id,
        rejectedBy: "current_user", // In real app, get from auth context
        reason: rejectionReason.trim(),
      });
    }
  };

  const getRiskBadgeVariant = (risk: string) => {
    switch (risk?.toLowerCase()) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
      default: return 'secondary';
    }
  };

  const columns = [
    { key: "PENDING_APPROVAL", title: "Pending Approval", icon: Clock },
    { key: "AUTO_APPROVED", title: "Auto-Approved", icon: CheckCircle2 },
    { key: "APPROVED", title: "Approved", icon: CheckCircle2 },
    { key: "EXECUTED", title: "Executed", icon: Play },
    { key: "REJECTED", title: "Rejected", icon: X },
  ];

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {columns.map(col => (
          <Card key={col.key} className="rounded-2xl animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-4 bg-gray-200 rounded"></div>
            </CardHeader>
            <CardContent>
              <div className="h-32 bg-gray-200 rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-red-600">
        Error loading workflows: {(error as any)?.detail || 'Unknown error'}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        {columns.map(col => {
          const Icon = col.icon;
          const columnWorkflows = workflows.filter((w: Workflow) => 
            w.status === col.key || 
            (col.key === "APPROVED" && w.status === "APPROVED")
          );

          return (
            <Card key={col.key} className="rounded-2xl">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Icon className="h-4 w-4" />
                  {col.title}
                  <Badge variant="secondary" className="ml-auto">
                    {columnWorkflows.length}
                  </Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {columnWorkflows.map((workflow: Workflow) => (
                  <div key={workflow.id} className="border rounded-xl p-3 text-sm bg-card">
                    <div className="font-medium">{workflow.id}</div>
                    <div className="text-slate-600 mt-1">{workflow.action}</div>
                    <div className="flex items-center gap-2 mt-2 text-xs">
                      <Badge variant="outline">{workflow.persona}</Badge>
                      <Badge variant={getRiskBadgeVariant(workflow.risk)}>
                        {workflow.risk}
                      </Badge>
                    </div>
                    
                    {/* Action buttons based on status */}
                    <div className="mt-3 flex gap-2">
                      {workflow.status === "PENDING_APPROVAL" && (
                        <>
                          <Button 
                            size="sm" 
                            onClick={() => handleApprove(workflow)}
                            disabled={approveMutation.isPending}
                          >
                            Approve
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => handleReject(workflow)}
                            disabled={rejectMutation.isPending}
                          >
                            Reject
                          </Button>
                        </>
                      )}
                      
                      {(workflow.status === "APPROVED" || workflow.status === "AUTO_APPROVED") && (
                        <Button 
                          size="sm" 
                          onClick={() => handleExecute(workflow)}
                          disabled={executeMutation.isPending}
                        >
                          <Play className="h-3 w-3 mr-1" />
                          Execute
                        </Button>
                      )}
                      
                      {workflow.status === "EXECUTED" && (
                        <Badge variant="default" className="text-xs">
                          <CheckCircle2 className="h-3 w-3 mr-1" />
                          Complete
                        </Badge>
                      )}
                      
                      {workflow.status === "REJECTED" && (
                        <Badge variant="destructive" className="text-xs">
                          <X className="h-3 w-3 mr-1" />
                          Rejected
                        </Badge>
                      )}
                    </div>

                    {/* Show approved/rejected details */}
                    {workflow.approved_by && (
                      <div className="mt-2 text-xs text-slate-500">
                        Approved by: {workflow.approved_by}
                      </div>
                    )}
                    {workflow.rejected_by && (
                      <div className="mt-2 text-xs text-slate-500">
                        Rejected by: {workflow.rejected_by}
                        {workflow.rejection_reason && (
                          <div className="text-red-600 mt-1">
                            Reason: {workflow.rejection_reason}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                
                {columnWorkflows.length === 0 && (
                  <div className="text-sm text-slate-400 text-center py-4">
                    No items
                  </div>
                )}
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Approval Confirmation Dialog */}
      <Dialog open={approvalDialog.open} onOpenChange={(open) => setApprovalDialog({ open, workflow: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Workflow</DialogTitle>
            <DialogDescription>
              Are you sure you want to approve workflow {approvalDialog.workflow?.id}?
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2 mt-4">
            <Button 
              variant="outline" 
              onClick={() => setApprovalDialog({ open: false, workflow: null })}
            >
              Cancel
            </Button>
            <Button 
              onClick={confirmApproval}
              disabled={approveMutation.isPending}
            >
              {approveMutation.isPending ? "Approving..." : "Approve"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Rejection Dialog */}
      <Dialog open={rejectionDialog.open} onOpenChange={(open) => setRejectionDialog({ open, workflow: null })}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Workflow</DialogTitle>
            <DialogDescription>
              Please provide a reason for rejecting workflow {rejectionDialog.workflow?.id}:
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <Input
              placeholder="Enter rejection reason..."
              value={rejectionReason}
              onChange={(e) => setRejectionReason(e.target.value)}
            />
            <div className="flex justify-end gap-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  setRejectionDialog({ open: false, workflow: null });
                  setRejectionReason("");
                }}
              >
                Cancel
              </Button>
              <Button 
                variant="destructive"
                onClick={confirmRejection}
                disabled={!rejectionReason.trim() || rejectMutation.isPending}
              >
                {rejectMutation.isPending ? "Rejecting..." : "Reject"}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}