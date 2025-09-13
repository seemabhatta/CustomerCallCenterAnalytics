import React, { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { transcriptApi, analysisApi } from "@/api/client";
import { Transcript } from "@/types";

interface TranscriptsViewProps {
  onOpenTranscript: (id: string) => void;
  goToAnalysis: () => void;
}

export function TranscriptsView({ onOpenTranscript, goToAnalysis }: TranscriptsViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedTranscriptId, setSelectedTranscriptId] = useState<string | null>(null);
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

  // Live transcript data for any selected transcript
  const { data: liveTranscriptData, isLoading: isLoadingLive } = useQuery({
    queryKey: ['liveTranscript', selectedTranscriptId],
    queryFn: () => transcriptApi.getLiveSegments(selectedTranscriptId!),
    refetchInterval: 3000, // Poll every 3 seconds for live updates
    enabled: !!selectedTranscriptId,
  });

  // Selected transcript details
  const { data: selectedTranscript, isLoading: isLoadingSelected } = useQuery({
    queryKey: ['transcript', selectedTranscriptId],
    queryFn: () => transcriptApi.getById(selectedTranscriptId!),
    enabled: !!selectedTranscriptId,
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

  const handleOpenTranscriptInternal = (transcriptId: string) => {
    setSelectedTranscriptId(transcriptId);
    // onOpenTranscript(transcriptId); // Removed to prevent popup dialog
  };

  const handleCloseLiveView = () => {
    setSelectedTranscriptId(null);
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

  // Render live transcript view for any selected transcript
  if (selectedTranscriptId && selectedTranscript) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Live Transcript • {selectedTranscriptId}</h2>
            <p className="text-slate-600">Customer transcript details and conversation flow</p>
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={handleCloseLiveView} variant="outline">
              Back to List
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Transcript Details</span>
              <Badge variant="secondary">
                Connected to GET /api/v1/transcripts/{selectedTranscriptId}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <div className="text-sm text-slate-600">Customer</div>
                <div className="font-medium">{selectedTranscript.customer || selectedTranscript.customer_id || 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm text-slate-600">Advisor</div>
                <div className="font-medium">{selectedTranscript.advisor || 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm text-slate-600">Topic</div>
                <div className="font-medium">{selectedTranscript.topic || 'N/A'}</div>
              </div>
              <div>
                <div className="text-sm text-slate-600">Status</div>
                <Badge variant={selectedTranscript.status === 'Complete' ? 'default' : 'secondary'}>
                  {selectedTranscript.status}
                </Badge>
              </div>
            </div>
            
            {isLoadingLive && (
              <div className="text-center py-4">
                <div className="animate-pulse text-slate-500">Loading live segments...</div>
              </div>
            )}
            
            {liveTranscriptData && (
              <div className="space-y-2">
                <div className="text-sm font-medium text-slate-700">Live Conversation Segments:</div>
                <div className="bg-slate-50 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <div className="space-y-3">
                    <div className="text-sm text-slate-600">
                      Duration: {liveTranscriptData.duration_sec || 0}s | 
                      Messages: {liveTranscriptData.message_count || 0} | 
                      Last Updated: {new Date().toLocaleTimeString()}
                    </div>
                    {liveTranscriptData.messages && liveTranscriptData.messages.length > 0 ? (
                      liveTranscriptData.messages.map((message: any, index: number) => (
                        <div key={index} className="border-l-2 border-blue-200 pl-3">
                          <div className="text-xs text-slate-500">
                            {message.speaker || 'Unknown'} • {message.timestamp || 'No timestamp'}
                          </div>
                          <div className="text-sm">{message.content || message.text || 'No content'}</div>
                        </div>
                      ))
                    ) : (
                      <div className="text-slate-500 text-sm">No conversation segments available yet.</div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
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
                    onClick={() => handleOpenTranscriptInternal(transcript.id)}
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