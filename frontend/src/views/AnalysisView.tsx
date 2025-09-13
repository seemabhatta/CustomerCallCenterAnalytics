import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Trash2, AlertTriangle } from "lucide-react";
import { analysisApi, planApi } from "@/api/client";
import { Analysis } from "@/types";

interface AnalysisViewProps {
  goToPlan: () => void;
}

export function AnalysisView({ goToPlan }: AnalysisViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [showDeleteAllConfirm, setShowDeleteAllConfirm] = useState(false);
  const [analysisToDelete, setAnalysisToDelete] = useState<string | null>(null);
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

  // Filter analyses based on search query
  const filteredAnalyses = analyses.filter((analysis: Analysis) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      analysis.id?.toLowerCase().includes(query) ||
      analysis.transcript_id?.toLowerCase().includes(query) ||
      analysis.summary?.toLowerCase().includes(query)
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
    <div className="space-y-2">
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

      <div className="overflow-hidden rounded-lg border">
        <table className="w-full text-xs">
          <thead className="bg-slate-50 border-b">
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
            {filteredAnalyses.map((analysis: Analysis) => (
              <tr key={analysis.id} className="border-b hover:bg-slate-50">
                <td className="py-1 px-2 text-xs font-medium text-slate-900">
                  {analysis.id}
                </td>
                <td className="py-1 px-2 text-xs">{analysis.transcript_id}</td>
                <td className="py-1 px-2 text-xs max-w-xs truncate" title={analysis.summary}>
                  {analysis.summary}
                </td>
                <td className="py-1 px-2">
                  <Badge variant="destructive" className="text-xs px-1 py-0">
                    {analysis.high || 0}
                  </Badge>
                </td>
                <td className="py-1 px-2">
                  <Badge variant="default" className="text-xs px-1 py-0">
                    {analysis.medium || 0}
                  </Badge>
                </td>
                <td className="py-1 px-2">
                  <Badge variant="secondary" className="text-xs px-1 py-0">
                    {analysis.low || 0}
                  </Badge>
                </td>
                <td className="py-1 px-2">
                  <Badge variant={analysis.status === 'Done' ? 'default' : 'secondary'} className="text-xs px-1 py-0">
                    {analysis.status}
                  </Badge>
                </td>
                <td className="py-1 px-2 text-xs">
                  {new Date(analysis.created_at).toLocaleDateString()}
                </td>
                <td className="py-1 px-2 text-right">
                  <div className="flex gap-1 justify-end">
                    <Button 
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0 text-gray-500 hover:text-red-600"
                      onClick={() => handleDeleteClick(analysis.id)}
                      disabled={deleteAnalysisMutation.isPending}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      className="h-6 text-xs px-2 text-gray-600"
                      disabled={hasPlan(analysis.id) || createPlanMutation.isPending}
                      onClick={() => handleTriggerPlan(analysis.id)}
                    >
                      {createPlanMutation.isPending ? 
                        "..." : 
                        hasPlan(analysis.id) ? 
                          "✓" : 
                          "Plan"
                      }
                    </Button>
                  </div>
                </td>
              </tr>
            ))}
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