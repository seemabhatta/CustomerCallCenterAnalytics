import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { analysisApi, planApi } from "@/api/client";
import { Analysis } from "@/types";

interface AnalysisViewProps {
  goToPlan: () => void;
}

export function AnalysisView({ goToPlan }: AnalysisViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const queryClient = useQueryClient();

  // Fetch analyses
  const { data: analyses = [], isLoading, error } = useQuery({
    queryKey: ['analyses'],
    queryFn: () => analysisApi.list(),
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

  // Filter analyses based on search query
  const filteredAnalyses = analyses.filter((analysis: Analysis) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      analysis.id.toLowerCase().includes(query) ||
      analysis.transcript_id.toLowerCase().includes(query) ||
      analysis.summary?.toLowerCase().includes(query)
    );
  });

  // Check if analysis has plan
  const hasPlan = (analysisId: string) => 
    plans.some((plan: any) => plan.analysis_id === analysisId);

  const handleTriggerPlan = (analysisId: string) => {
    createPlanMutation.mutate(analysisId);
  };

  const getRiskBadgeVariant = (level: string) => {
    switch (level?.toLowerCase()) {
      case 'high': return 'destructive';
      case 'medium': return 'default';
      case 'low': return 'secondary';
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
          Error loading analyses: {(error as any)?.detail || 'Unknown error'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Input 
          className="w-96" 
          placeholder="Search by analysis or transcript ID" 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
        />
        <Badge variant="secondary">{filteredAnalyses.length} item(s)</Badge>
      </div>

      <div className="overflow-hidden rounded-2xl border">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left py-2 px-3">Analysis</th>
              <th className="text-left py-2 px-3">Transcript</th>
              <th className="text-left py-2 px-3">Summary</th>
              <th className="text-left py-2 px-3">High</th>
              <th className="text-left py-2 px-3">Medium</th>
              <th className="text-left py-2 px-3">Low</th>
              <th className="text-left py-2 px-3">Status</th>
              <th className="text-left py-2 px-3">Created</th>
              <th className="text-right py-2 px-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredAnalyses.map((analysis: Analysis) => (
              <tr key={analysis.id} className="border-b hover:bg-slate-50">
                <td className="py-2 px-3 font-medium text-slate-900">
                  {analysis.id}
                </td>
                <td className="py-2 px-3">{analysis.transcript_id}</td>
                <td className="py-2 px-3 max-w-xs truncate" title={analysis.summary}>
                  {analysis.summary}
                </td>
                <td className="py-2 px-3">
                  <Badge variant="destructive" className="text-xs">
                    {analysis.high || 0}
                  </Badge>
                </td>
                <td className="py-2 px-3">
                  <Badge variant="default" className="text-xs">
                    {analysis.medium || 0}
                  </Badge>
                </td>
                <td className="py-2 px-3">
                  <Badge variant="secondary" className="text-xs">
                    {analysis.low || 0}
                  </Badge>
                </td>
                <td className="py-2 px-3">
                  <Badge variant={analysis.status === 'Done' ? 'default' : 'secondary'}>
                    {analysis.status}
                  </Badge>
                </td>
                <td className="py-2 px-3">
                  {new Date(analysis.created_at).toLocaleString()}
                </td>
                <td className="py-2 px-3 text-right">
                  <Button 
                    size="sm" 
                    disabled={hasPlan(analysis.id) || createPlanMutation.isPending}
                    onClick={() => handleTriggerPlan(analysis.id)}
                  >
                    {createPlanMutation.isPending ? 
                      "Creating..." : 
                      hasPlan(analysis.id) ? 
                        "Plan Created" : 
                        "Trigger Plan"
                    }
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredAnalyses.length === 0 && (
          <div className="p-8 text-center text-slate-500">
            {searchQuery ? 'No analyses match your search.' : 'No analyses found.'}
          </div>
        )}
      </div>
    </div>
  );
}