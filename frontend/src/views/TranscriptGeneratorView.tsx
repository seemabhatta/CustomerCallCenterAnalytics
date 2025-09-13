import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
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

  const queryClient = useQueryClient();

  const createTranscriptMutation = useMutation({
    mutationFn: (data: TranscriptCreateRequest) => transcriptApi.create(data),
    onSuccess: (newTranscript) => {
      queryClient.invalidateQueries({ queryKey: ['transcripts'] });
      setShowSuccess(true);
      setCreatedTranscriptId(newTranscript.id);
    },
    onError: (error) => {
      console.error('Failed to create transcript:', error);
    },
  });

  const [showSuccess, setShowSuccess] = useState(false);
  const [createdTranscriptId, setCreatedTranscriptId] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuccess(false);
    createTranscriptMutation.mutate(formData);
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

  if (showSuccess && createdTranscriptId) {
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
            <Alert className="border-green-200 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                <strong>Transcript created successfully!</strong>
                <br />
                New transcript ID: <code className="font-mono">{createdTranscriptId}</code>
              </AlertDescription>
            </Alert>

            <div className="flex gap-3 mt-6">
              <Button onClick={handleViewTranscript} className="flex-1">
                View in Transcripts Tab
              </Button>
              <Button 
                variant="outline" 
                onClick={() => {
                  setShowSuccess(false);
                  setCreatedTranscriptId(null);
                }}
                className="flex-1"
              >
                Create Another
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

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="h-5 w-5" />
            Create New Transcript
          </CardTitle>
          <CardDescription>
            Configure the parameters for generating a new customer service transcript
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {createTranscriptMutation.error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  Failed to create transcript. Please try again.
                </AlertDescription>
              </Alert>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-2">
                <Label htmlFor="topic">Topic</Label>
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
                <Label htmlFor="urgency">Urgency Level</Label>
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
                <Label htmlFor="customer_sentiment">Customer Sentiment</Label>
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
                <Label htmlFor="customer_id">Customer ID</Label>
                <Input
                  id="customer_id"
                  value={formData.customer_id}
                  onChange={(e) => handleInputChange('customer_id', e.target.value)}
                  placeholder="e.g., CUST_001"
                />
              </div>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="financial_impact"
                checked={formData.financial_impact}
                onCheckedChange={(checked) => handleInputChange('financial_impact', checked)}
              />
              <Label htmlFor="financial_impact">Financial Impact</Label>
              <span className="text-sm text-muted-foreground">
                Indicates if this transcript involves financial matters
              </span>
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id="store"
                checked={formData.store}
                onCheckedChange={(checked) => handleInputChange('store', checked)}
              />
              <Label htmlFor="store">Store Transcript</Label>
              <span className="text-sm text-muted-foreground">
                Save the generated transcript to the database
              </span>
            </div>

            <Button 
              type="submit" 
              className="w-full" 
              disabled={createTranscriptMutation.isPending}
            >
              {createTranscriptMutation.isPending ? 'Generating...' : 'Generate Transcript'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}