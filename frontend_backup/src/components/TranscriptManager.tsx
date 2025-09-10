import { useState } from 'react';
import { useApi, useApiCall } from '../hooks/useApi';
import type { Transcript } from '../types/workflow';

interface TranscriptManagerProps {
  onTranscriptSelected: (transcript: Transcript) => void;
  selectedTranscriptId?: string;
}

export function TranscriptManager({ onTranscriptSelected, selectedTranscriptId }: TranscriptManagerProps) {
  const { data: transcripts, loading: loadingTranscripts, refetch } = useApi<Transcript[]>('/transcripts');
  const { makeApiCall, loading: generatingTranscript, error } = useApiCall();
  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [generateForm, setGenerateForm] = useState({
    scenario: 'Mortgage Servicing - PMI Removal Dispute',
    urgency: 'high' as 'low' | 'medium' | 'high',
    financial_impact: true,
    customer_sentiment: 'frustrated'
  });

  const handleGenerateTranscript = async () => {
    try {
      const result = await makeApiCall<Transcript>('/generate', {
        method: 'POST',
        body: JSON.stringify({
          ...generateForm,
          store: true
        })
      });

      // Refetch transcripts to update the list
      refetch();
      
      // Auto-select the new transcript
      onTranscriptSelected(result);
      
      // Reset form
      setShowGenerateForm(false);
      setGenerateForm({
        scenario: 'Mortgage Servicing - PMI Removal Dispute',
        urgency: 'high',
        financial_impact: true,
        customer_sentiment: 'frustrated'
      });
    } catch (err) {
      console.error('Failed to generate transcript:', err);
    }
  };

  const handleTranscriptSelect = (transcriptId: string) => {
    const transcript = transcripts?.find(t => t.transcript_id === transcriptId);
    if (transcript) {
      onTranscriptSelected(transcript);
    }
  };

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-4">Transcript Management</h2>
      
      <div className="flex gap-4 items-start">
        {/* Transcript Selector */}
        <div className="flex-1">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Transcript
          </label>
          <select
            value={selectedTranscriptId || ''}
            onChange={(e) => handleTranscriptSelect(e.target.value)}
            className="form-select"
            disabled={loadingTranscripts}
          >
            <option value="">Choose a transcript...</option>
            {transcripts?.map((transcript) => (
              <option key={transcript.transcript_id} value={transcript.transcript_id}>
                {transcript.transcript_id} - {transcript.scenario.substring(0, 50)}...
              </option>
            ))}
          </select>
          {loadingTranscripts && (
            <p className="text-sm text-gray-500 mt-1">Loading transcripts...</p>
          )}
        </div>

        {/* Generate Button */}
        <div className="flex gap-2">
          <button
            onClick={() => setShowGenerateForm(!showGenerateForm)}
            className="btn-primary"
            disabled={generatingTranscript}
          >
            Generate New
          </button>
          
          {selectedTranscriptId && (
            <button
              onClick={() => {
                const transcript = transcripts?.find(t => t.transcript_id === selectedTranscriptId);
                if (transcript) onTranscriptSelected(transcript);
              }}
              className="btn-success"
            >
              Process
            </button>
          )}
        </div>
      </div>

      {/* Generate Form */}
      {showGenerateForm && (
        <div className="mt-6 p-4 bg-gray-50 rounded-md">
          <h3 className="text-lg font-medium mb-4">Generate New Transcript</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Scenario
              </label>
              <select
                value={generateForm.scenario}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, scenario: e.target.value }))}
                className="form-select"
              >
                <option value="Mortgage Servicing - PMI Removal Dispute">PMI Removal Dispute</option>
                <option value="Mortgage Servicing - Payment Dispute">Payment Dispute</option>
                <option value="Mortgage Servicing - Refinancing Inquiry">Refinancing Inquiry</option>
                <option value="Mortgage Servicing - Hardship Assistance">Hardship Assistance</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Urgency
              </label>
              <select
                value={generateForm.urgency}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, urgency: e.target.value as 'low' | 'medium' | 'high' }))}
                className="form-select"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Customer Sentiment
              </label>
              <select
                value={generateForm.customer_sentiment}
                onChange={(e) => setGenerateForm(prev => ({ ...prev, customer_sentiment: e.target.value }))}
                className="form-select"
              >
                <option value="frustrated">Frustrated</option>
                <option value="concerned">Concerned</option>
                <option value="neutral">Neutral</option>
                <option value="satisfied">Satisfied</option>
              </select>
            </div>
            
            <div className="flex items-center">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={generateForm.financial_impact}
                  onChange={(e) => setGenerateForm(prev => ({ ...prev, financial_impact: e.target.checked }))}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">Financial Impact</span>
              </label>
            </div>
          </div>
          
          <div className="flex gap-2 mt-4">
            <button
              onClick={handleGenerateTranscript}
              className="btn-primary"
              disabled={generatingTranscript}
            >
              {generatingTranscript ? 'Generating...' : 'Generate Transcript'}
            </button>
            <button
              onClick={() => setShowGenerateForm(false)}
              className="btn-secondary"
            >
              Cancel
            </button>
          </div>
          
          {error && (
            <div className="mt-4 p-3 bg-error-50 border border-error-200 rounded-md">
              <p className="text-error-700 text-sm">{error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}