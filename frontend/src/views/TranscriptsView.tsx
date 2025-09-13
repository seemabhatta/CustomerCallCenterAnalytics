import React, { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { transcriptApi, analysisApi } from "@/api/client";
import { Transcript } from "@/types";

interface TranscriptsViewProps {
  onOpenTranscript: (id: string) => void;
  goToAnalysis: () => void;
}

export function TranscriptsView({ onOpenTranscript, goToAnalysis }: TranscriptsViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const queryClient = useQueryClient();

  // Fetch transcripts
  const { data: transcripts = [], isLoading, error } = useQuery({
    queryKey: ['transcripts'],
    queryFn: () => transcriptApi.list(),
  });

  // Fetch analyses to check which transcripts have analyses
  const { data: analyses = [] } = useQuery({
    queryKey: ['analyses'],
    queryFn: () => analysisApi.list(),
  });

  // Create analysis mutation
  const createAnalysisMutation = useMutation({
    mutationFn: (transcriptId: string) => 
      analysisApi.create({ transcript_id: transcriptId }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      goToAnalysis();
    },
  });

  // Filter transcripts based on search query
  const filteredTranscripts = transcripts.filter((transcript: Transcript) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      transcript.id.toLowerCase().includes(query) ||
      transcript.customer?.toLowerCase().includes(query) ||
      transcript.advisor?.toLowerCase().includes(query)
    );
  });

  // Check if transcript has analysis
  const hasAnalysis = (transcriptId: string) => 
    analyses.some((analysis: any) => analysis.transcript_id === transcriptId);

  const handleStartAnalysis = (transcriptId: string) => {
    createAnalysisMutation.mutate(transcriptId);
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
          Error loading transcripts: {(error as any)?.detail || 'Unknown error'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Input 
          className="w-96" 
          placeholder="Search by ID, customer, or advisor" 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
        />
        <Badge variant="secondary">{filteredTranscripts.length} item(s)</Badge>
      </div>

      <div className="overflow-hidden rounded-2xl border">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left py-2 px-3">Transcript</th>
              <th className="text-left py-2 px-3">Customer</th>
              <th className="text-left py-2 px-3">Advisor</th>
              <th className="text-left py-2 px-3">Topic</th>
              <th className="text-left py-2 px-3">Created</th>
              <th className="text-left py-2 px-3">Duration</th>
              <th className="text-left py-2 px-3">Messages</th>
              <th className="text-left py-2 px-3">Status</th>
              <th className="text-right py-2 px-3">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredTranscripts.map((transcript: Transcript) => (
              <tr key={transcript.id} className="border-b hover:bg-slate-50">
                <td className="py-2 px-3 font-medium text-slate-900">
                  <button 
                    className="underline hover:text-blue-600" 
                    onClick={() => onOpenTranscript(transcript.id)}
                  >
                    {transcript.id}
                  </button>
                </td>
                <td className="py-2 px-3">{transcript.customer || transcript.customer_id}</td>
                <td className="py-2 px-3">{transcript.advisor || '-'}</td>
                <td className="py-2 px-3">{transcript.topic}</td>
                <td className="py-2 px-3">
                  {new Date(transcript.created_at).toLocaleString()}
                </td>
                <td className="py-2 px-3">{transcript.duration_sec || '-'}s</td>
                <td className="py-2 px-3">{transcript.message_count || '-'}</td>
                <td className="py-2 px-3">
                  <Badge variant={transcript.status === 'Complete' ? 'default' : 'secondary'}>
                    {transcript.status}
                  </Badge>
                </td>
                <td className="py-2 px-3 text-right">
                  <Button 
                    size="sm" 
                    disabled={hasAnalysis(transcript.id) || createAnalysisMutation.isPending}
                    onClick={() => handleStartAnalysis(transcript.id)}
                  >
                    {createAnalysisMutation.isPending ? 
                      "Creating..." : 
                      hasAnalysis(transcript.id) ? 
                        "Analysis Exists" : 
                        "Start Analysis"
                    }
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {filteredTranscripts.length === 0 && (
          <div className="p-8 text-center text-slate-500">
            {searchQuery ? 'No transcripts match your search.' : 'No transcripts found.'}
          </div>
        )}
      </div>
    </div>
  );
}