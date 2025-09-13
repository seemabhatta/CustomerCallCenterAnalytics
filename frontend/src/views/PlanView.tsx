import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { planApi, workflowApi } from "@/api/client";
import { Plan } from "@/types";

interface PlanViewProps {
  goToWorkflow: () => void;
}

export function PlanView({ goToWorkflow }: PlanViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
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

  // Filter plans based on search query
  const filteredPlans = plans.filter((plan: Plan) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      plan.id.toLowerCase().includes(query) ||
      plan.analysis_id.toLowerCase().includes(query) ||
      plan.title?.toLowerCase().includes(query)
    );
  });

  // Check if plan has workflow
  const hasWorkflow = (planId: string) => 
    workflows.some((workflow: any) => workflow.plan_id === planId);

  const handleTriggerWorkflow = (planId: string) => {
    createWorkflowMutation.mutate(planId);
  };

  const getStatusBadgeVariant = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'approved': return 'default';
      case 'executed': return 'default';
      case 'draft': return 'secondary';
      case 'ready': return 'outline';
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
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Input 
          className="w-96" 
          placeholder="Search by plan or analysis ID" 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
        />
        <Badge variant="secondary">{filteredPlans.length} item(s)</Badge>
      </div>

      <div className="overflow-hidden rounded-2xl border">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left py-2 px-3">Plan</th>
              <th className="text-left py-2 px-3">Analysis</th>
              <th className="text-left py-2 px-3">Title</th>
              <th className="text-left py-2 px-3">Owner</th>
              <th className="text-left py-2 px-3">Type</th>
              <th className="text-left py-2 px-3">Urgency</th>
              <th className="text-left py-2 px-3">Status</th>
              <th className="text-left py-2 px-3">Created</th>
              <th className="text-right py-2 px-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredPlans.map((plan: Plan) => (
              <tr key={plan.id} className="border-b hover:bg-slate-50">
                <td className="py-2 px-3 font-medium text-slate-900">
                  {plan.id}
                </td>
                <td className="py-2 px-3">{plan.analysis_id}</td>
                <td className="py-2 px-3 max-w-xs truncate" title={plan.title}>
                  {plan.title}
                </td>
                <td className="py-2 px-3">{plan.owner}</td>
                <td className="py-2 px-3">
                  <Badge variant="outline" className="text-xs">
                    {plan.plan_type}
                  </Badge>
                </td>
                <td className="py-2 px-3">
                  <Badge 
                    variant={plan.urgency === 'high' ? 'destructive' : 'secondary'} 
                    className="text-xs"
                  >
                    {plan.urgency}
                  </Badge>
                </td>
                <td className="py-2 px-3">
                  <Badge variant={getStatusBadgeVariant(plan.status)}>
                    {plan.status}
                  </Badge>
                </td>
                <td className="py-2 px-3">
                  {new Date(plan.created_at).toLocaleString()}
                </td>
                <td className="py-2 px-3 text-right">
                  <Button 
                    size="sm" 
                    disabled={hasWorkflow(plan.id) || createWorkflowMutation.isPending}
                    onClick={() => handleTriggerWorkflow(plan.id)}
                  >
                    {createWorkflowMutation.isPending ? 
                      "Creating..." : 
                      hasWorkflow(plan.id) ? 
                        "Workflow Created" : 
                        "Trigger Workflow"
                    }
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredPlans.length === 0 && (
          <div className="p-8 text-center text-slate-500">
            {searchQuery ? 'No plans match your search.' : 'No plans found.'}
          </div>
        )}
      </div>
    </div>
  );
}