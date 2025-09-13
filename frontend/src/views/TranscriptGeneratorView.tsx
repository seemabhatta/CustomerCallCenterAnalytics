import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CheckCircle, AlertCircle, Plus } from 'lucide-react';
import { transcriptApi } from '@/api/client';
import { TranscriptCreateRequest } from '@/types';

interface TranscriptGeneratorViewProps {
  goToTranscripts: () => void;
}

export function TranscriptGeneratorView({ goToTranscripts }: TranscriptGeneratorViewProps) {
  const [formData, setFormData] = useState<TranscriptCreateRequest>({
    topic: 'payment_inquiry',
    urgency: 'medium',
    financial_impact: false,
    customer_sentiment: 'neutral',
    customer_id: 'CUST_001',
    store: true,
  });

  const [bulkCount, setBulkCount] = useState<number>(5);

  const queryClient = useQueryClient();

  const createTranscriptMutation = useMutation({
    mutationFn: (data: TranscriptCreateRequest) => transcriptApi.create(data),
    onSuccess: (newTranscript) => {
      queryClient.invalidateQueries({ queryKey: ['transcripts'] });
      setShowSuccess(true);
      setCreatedTranscriptId(newTranscript.id);
      setCreatedTranscripts(null);
      setBulkCreatedCount(0);
    },
    onError: (error) => {
      console.error('Failed to create transcript:', error);
    },
  });

  const createBulkTranscriptsMutation = useMutation({
    mutationFn: (requests: TranscriptCreateRequest[]) => transcriptApi.createBulk(requests),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['transcripts'] });
      setShowSuccess(true);
      setCreatedTranscripts(result.transcripts);
      setBulkCreatedCount(result.count);
      setCreatedTranscriptId(null);
    },
    onError: (error) => {
      console.error('Failed to create bulk transcripts:', error);
    },
  });

  const [showSuccess, setShowSuccess] = useState(false);
  const [createdTranscriptId, setCreatedTranscriptId] = useState<string | null>(null);
  const [createdTranscripts, setCreatedTranscripts] = useState<any[] | null>(null);
  const [bulkCreatedCount, setBulkCreatedCount] = useState<number>(0);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuccess(false);
    createTranscriptMutation.mutate(formData);
  };

  const handleBulkSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuccess(false);
    
    // Create multiple requests with unique customer IDs
    const requests = Array.from({ length: bulkCount }, (_, index) => ({
      ...formData,
      customer_id: `${formData.customer_id}_${index + 1}`,
    }));
    
    createBulkTranscriptsMutation.mutate(requests);
  };

  const handleInputChange = (field: keyof TranscriptCreateRequest, value: string | boolean) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleViewTranscript = () => {
    goToTranscripts();
  };

  if (showSuccess && (createdTranscriptId || createdTranscripts)) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Transcript Generator</h2>
            <p className="text-muted-foreground">
              Generate new customer service transcripts for analysis
            </p>
          </div>
        </div>

        <Card>
          <CardContent className="pt-6">
            <div className="border border-green-200 bg-green-50 p-4 rounded-lg flex items-start gap-3">
              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
              <div className="text-green-800">
                {createdTranscriptId ? (
                  <>
                    <strong>Transcript created successfully!</strong>
                    <br />
                    New transcript ID: <code className="font-mono">{createdTranscriptId}</code>
                  </>
                ) : (
                  <>
                    <strong>Bulk transcripts created successfully!</strong>
                    <br />
                    Created {bulkCreatedCount} new transcripts
                    {createdTranscripts && createdTranscripts.length > 0 && (
                      <div className="mt-2 max-h-32 overflow-y-auto">
                        <div className="text-sm">
                          {createdTranscripts.map((transcript, index) => (
                            <div key={index} className="font-mono text-xs">
                              {transcript.id}
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <Button onClick={handleViewTranscript} className="flex-1">
                View in Transcripts Tab
              </Button>
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowSuccess(false);
                  setCreatedTranscriptId(null);
                  setCreatedTranscripts(null);
                  setBulkCreatedCount(0);
                }}
                className="flex-1"
              >
                Create More
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Transcript Generator</h2>
          <p className="text-muted-foreground">
            Generate new customer service transcripts for analysis
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Create Single Transcript
            </CardTitle>
            <CardDescription>
              Generate one customer service transcript with specific parameters
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              {createTranscriptMutation.error && (
                <div className="border border-red-200 bg-red-50 p-4 rounded-lg flex items-start gap-3">
                  <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                  <div className="text-red-800">
                    Failed to create transcript. Please try again.
                  </div>
                </div>
              )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <label htmlFor="topic" className="text-sm font-medium">Topic</label>
                <Select
                  value={formData.topic}
                  onValueChange={(value) => handleInputChange('topic', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select topic" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="payment_inquiry">Payment Inquiry</SelectItem>
                    <SelectItem value="billing_dispute">Billing Dispute</SelectItem>
                    <SelectItem value="account_access">Account Access</SelectItem>
                    <SelectItem value="product_support">Product Support</SelectItem>
                    <SelectItem value="refund_request">Refund Request</SelectItem>
                    <SelectItem value="general_inquiry">General Inquiry</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label htmlFor="urgency" className="text-sm font-medium">Urgency Level</label>
                <Select
                  value={formData.urgency}
                  onValueChange={(value) => handleInputChange('urgency', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select urgency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label htmlFor="customer_sentiment" className="text-sm font-medium">Customer Sentiment</label>
                <Select
                  value={formData.customer_sentiment}
                  onValueChange={(value) => handleInputChange('customer_sentiment', value)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select sentiment" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="positive">Positive</SelectItem>
                    <SelectItem value="neutral">Neutral</SelectItem>
                    <SelectItem value="negative">Negative</SelectItem>
                    <SelectItem value="frustrated">Frustrated</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <label htmlFor="customer_id" className="text-sm font-medium">Customer ID</label>
                <Input
                  id="customer_id"
                  value={formData.customer_id}
                  onChange={(e) => handleInputChange('customer_id', e.target.value)}
                  placeholder="e.g., CUST_001"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="financial_impact"
                checked={formData.financial_impact}
                onChange={(e) => handleInputChange('financial_impact', e.target.checked)}
                className="rounded border-gray-300"
              />
              <label htmlFor="financial_impact" className="text-sm font-medium">Financial Impact</label>
              <span className="text-sm text-gray-500">
                Indicates if this transcript involves financial matters
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                id="store"
                checked={formData.store}
                onChange={(e) => handleInputChange('store', e.target.checked)}
                className="rounded border-gray-300"
              />
              <label htmlFor="store" className="text-sm font-medium">Store Transcript</label>
              <span className="text-sm text-gray-500">
                Save the generated transcript to the database
              </span>
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={createTranscriptMutation.isPending}
            >
              {createTranscriptMutation.isPending ? 'Generating...' : 'Generate Single Transcript'}
            </Button>
          </form>
        </CardContent>
      </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Bulk Generate Transcripts
            </CardTitle>
            <CardDescription>
              Generate multiple transcripts with the same parameters but unique customer IDs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleBulkSubmit} className="space-y-6">
              {createBulkTranscriptsMutation.error && (
                <div className="border border-red-200 bg-red-50 p-4 rounded-lg flex items-start gap-3">
                  <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                  <div className="text-red-800">
                    Failed to create bulk transcripts. Please try again.
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="bulk_count" className="text-sm font-medium">Number of Transcripts</label>
                <Input
                  id="bulk_count"
                  type="number"
                  min="1"
                  max="50"
                  value={bulkCount}
                  onChange={(e) => setBulkCount(parseInt(e.target.value) || 1)}
                  placeholder="Enter number of transcripts to generate"
                />
                <p className="text-xs text-gray-500">
                  Will generate {bulkCount} transcripts with customer IDs: {formData.customer_id}_1, {formData.customer_id}_2, etc.
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                <h4 className="text-sm font-medium">Template Configuration</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="font-medium">Topic:</span> {formData.topic?.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'N/A'}
                  </div>
                  <div>
                    <span className="font-medium">Urgency:</span> {formData.urgency ? formData.urgency.charAt(0).toUpperCase() + formData.urgency.slice(1) : 'N/A'}
                  </div>
                  <div>
                    <span className="font-medium">Sentiment:</span> {formData.customer_sentiment ? formData.customer_sentiment.charAt(0).toUpperCase() + formData.customer_sentiment.slice(1) : 'N/A'}
                  </div>
                  <div>
                    <span className="font-medium">Base Customer ID:</span> {formData.customer_id}
                  </div>
                  <div>
                    <span className="font-medium">Financial Impact:</span> {formData.financial_impact ? 'Yes' : 'No'}
                  </div>
                  <div>
                    <span className="font-medium">Store:</span> {formData.store ? 'Yes' : 'No'}
                  </div>
                </div>
                <p className="text-xs text-gray-600">
                  Modify these settings using the form on the left, then generate bulk transcripts here.
                </p>
              </div>

              <Button 
                type="submit" 
                className="w-full" 
                disabled={createBulkTranscriptsMutation.isPending}
              >
                {createBulkTranscriptsMutation.isPending 
                  ? `Generating ${bulkCount} Transcripts...` 
                  : `Generate ${bulkCount} Transcripts`}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}