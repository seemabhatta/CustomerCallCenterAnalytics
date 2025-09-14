import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2, AlertTriangle } from "lucide-react";
import { planApi, workflowApi } from "@/api/client";
import { Plan } from "@/types";

interface PlanViewProps {
  goToWorkflow: () => void;
}

export function PlanView({ goToWorkflow }: PlanViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
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

  // Create workflow mutation
  const createWorkflowMutation = useMutation({
    mutationFn: (planId: string) => 
      workflowApi.extractFromPlan(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
      goToWorkflow();
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
                  {plan.plan_id}
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