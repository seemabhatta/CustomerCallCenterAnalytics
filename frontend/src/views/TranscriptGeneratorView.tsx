import React, { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CheckCircle, AlertCircle, Plus } from 'lucide-react';
import { transcriptApi } from '@/api/client';
import { TranscriptCreateRequest, TranscriptSeedData } from '@/types';

interface TranscriptGeneratorViewProps {
  goToTranscripts: () => void;
}

const TOPIC_OPTIONS: { value: string; label: string }[] = [
  { value: 'payment_inquiry', label: 'Payment Inquiry' },
  { value: 'mortgage_payment_issue', label: 'Mortgage Payment Issue' },
  { value: 'escrow_inquiry', label: 'Escrow Inquiry' },
  { value: 'pmi_removal_request', label: 'PMI Removal Request' },
  { value: 'refinance_inquiry', label: 'Refinance Inquiry' },
  { value: 'hardship_assistance', label: 'Hardship Assistance' },
  { value: 'payoff_request', label: 'Payoff Request' },
  { value: 'complaint_resolution', label: 'Complaint Resolution' },
];

const formatLabel = (value?: string) =>
  value ? value.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ') : 'N/A';

export function TranscriptGeneratorView({ goToTranscripts }: TranscriptGeneratorViewProps) {
  const queryClient = useQueryClient();

  const seedQuery = useQuery<TranscriptSeedData>({
    queryKey: ['transcript-seeds'],
    queryFn: () => transcriptApi.getSeeds(),
    staleTime: 5 * 60 * 1000,
  });

  const seeds = seedQuery.data;

  const [formData, setFormData] = useState<TranscriptCreateRequest>({
    topic: 'payment_inquiry',
    urgency: 'medium',
    financial_impact: false,
    customer_sentiment: 'neutral',
    store: true,
    context: '',
  });
  const [initializedSeeds, setInitializedSeeds] = useState(false);
  const [bulkCount, setBulkCount] = useState<number>(5);
  const [showSuccess, setShowSuccess] = useState(false);
  const [createdTranscriptId, setCreatedTranscriptId] = useState<string | null>(null);
  const [createdTranscripts, setCreatedTranscripts] = useState<any[] | null>(null);
  const [bulkCreatedCount, setBulkCreatedCount] = useState<number>(0);

  useEffect(() => {
    if (seeds && !initializedSeeds && seeds.customers.length > 0) {
      const defaultCustomer = seeds.customers[0];
      const defaultLoan = defaultCustomer.loans[0];
      const defaultAdvisor = seeds.advisors[0];
      setFormData(prev => ({
        ...prev,
        customer_id: defaultCustomer.customer_id,
        loan_id: defaultLoan?.loan_id,
        property_id: defaultCustomer.property.property_id,
        advisor_id: defaultAdvisor?.advisor_id,
      }));
      setInitializedSeeds(true);
    }
  }, [seeds, initializedSeeds]);

  const selectedCustomer = useMemo(
    () => seeds?.customers.find(customer => customer.customer_id === formData.customer_id),
    [seeds, formData.customer_id]
  );

  const selectedLoan = useMemo(
    () => selectedCustomer?.loans.find(loan => loan.loan_id === formData.loan_id) ?? selectedCustomer?.loans[0],
    [selectedCustomer, formData.loan_id]
  );

  const selectedAdvisor = useMemo(
    () => seeds?.advisors.find(advisor => advisor.advisor_id === formData.advisor_id),
    [seeds, formData.advisor_id]
  );

  const handleInputChange = (field: keyof TranscriptCreateRequest, value: string | boolean | undefined) => {
    setFormData(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleCustomerChange = (customerId: string) => {
    const customer = seeds?.customers.find(c => c.customer_id === customerId);
    const defaultLoan = customer?.loans[0];
    setFormData(prev => ({
      ...prev,
      customer_id: customerId,
      loan_id: defaultLoan?.loan_id,
      property_id: customer?.property.property_id,
    }));
  };

  const handleLoanChange = (loanId: string) => {
    setFormData(prev => ({
      ...prev,
      loan_id: loanId,
    }));
  };

  const handleAdvisorChange = (advisorId: string) => {
    setFormData(prev => ({
      ...prev,
      advisor_id: advisorId,
    }));
  };

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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuccess(false);
    createTranscriptMutation.mutate(formData);
  };

  const handleBulkSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowSuccess(false);

    if (!seeds || seeds.customers.length === 0) {
      console.error('Seed data unavailable for bulk generation');
      return;
    }

    const customerPool = seeds.customers;
    const advisorPool = seeds.advisors.length > 0 ? seeds.advisors : undefined;

    const requests = Array.from({ length: bulkCount }, (_, index) => {
      const chosenCustomer = formData.customer_id
        ? customerPool.find(c => c.customer_id === formData.customer_id) ?? customerPool[index % customerPool.length]
        : customerPool[index % customerPool.length];

      const chosenLoan = chosenCustomer.loans.find(l => l.loan_id === formData.loan_id) ?? chosenCustomer.loans[0];
      const chosenAdvisor = formData.advisor_id && advisorPool
        ? advisorPool.find(a => a.advisor_id === formData.advisor_id) ?? advisorPool[index % advisorPool.length]
        : advisorPool?.[index % advisorPool.length];

      return {
        ...formData,
        customer_id: chosenCustomer.customer_id,
        loan_id: chosenLoan?.loan_id,
        property_id: chosenCustomer.property.property_id,
        advisor_id: chosenAdvisor?.advisor_id ?? formData.advisor_id,
      } as TranscriptCreateRequest;
    });

    createBulkTranscriptsMutation.mutate(requests);
  };

  const handleViewTranscript = () => {
    goToTranscripts();
  };

  if (seedQuery.isLoading) {
    return (
      <div className="page-shell">
        <h2 className="text-lg font-semibold text-slate-900">Transcript Generator</h2>
        <p className="text-xs text-slate-500">Loading portfolio seed profiles...</p>
      </div>
    );
  }

  if (seedQuery.isError || !seeds || seeds.customers.length === 0) {
    return (
      <div className="page-shell">
        <h2 className="text-lg font-semibold text-slate-900">Transcript Generator</h2>
        <Card className="mt-4 border border-rose-200 bg-rose-50">
          <CardContent className="py-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-rose-600 mt-0.5" />
              <div>
                <h3 className="text-sm font-semibold text-rose-700">Seed data unavailable</h3>
                <p className="text-sm text-rose-600">
                  Unable to load the portfolio seed profiles required for transcript generation. Please refresh or seed the portfolio dataset.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (showSuccess && (createdTranscriptId || createdTranscripts)) {
    return (
      <div className="page-shell">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="view-header">Transcript Generator</h2>
            <p className="text-xs text-slate-500">
              Generate new customer service transcripts for analysis
            </p>
          </div>
        </div>

        <Card className="panel">
          <CardContent className="pt-6">
            <div className="border border-slate-200 bg-slate-50 p-3 rounded-lg flex items-start gap-2">
              <CheckCircle className="h-4 w-4 text-green-600 mt-0.5" />
              <div className="text-slate-700">
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
                    Created {bulkCreatedCount} new transcripts.
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
    <div className="page-shell">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-900">Transcript Generator</h2>
          <p className="text-xs text-slate-500">
            Generate new customer service transcripts for analysis
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card className="panel">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-bold">
              <Plus className="h-4 w-4" />
              Create Single Transcript
            </CardTitle>
            <CardDescription>
              Generate one customer service transcript with seeded customer and advisor context.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {createTranscriptMutation.error && (
                <div className="border border-slate-200 bg-slate-50 p-3 rounded-lg flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                  <div className="text-slate-700">
                    Failed to create transcript. Please try again.
                  </div>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="topic" className="text-xs font-medium">Topic</label>
                  <Select
                    value={formData.topic}
                    onValueChange={(value) => handleInputChange('topic', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select topic" />
                    </SelectTrigger>
                    <SelectContent>
                      {TOPIC_OPTIONS.map(option => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="urgency" className="text-xs font-medium">Urgency Level</label>
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
                  <label htmlFor="customer_sentiment" className="text-xs font-medium">Customer Sentiment</label>
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
                  <label htmlFor="customer_id" className="text-xs font-medium">Customer</label>
                  <Select
                    value={formData.customer_id ?? ''}
                    onValueChange={handleCustomerChange}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select customer" />
                    </SelectTrigger>
                    <SelectContent>
                      {seeds.customers.map(customer => (
                        <SelectItem key={customer.customer_id} value={customer.customer_id}>
                          {customer.display_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="loan_id" className="text-xs font-medium">Loan</label>
                  <Select
                    value={formData.loan_id ?? selectedLoan?.loan_id ?? ''}
                    onValueChange={handleLoanChange}
                    disabled={!selectedCustomer}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select loan" />
                    </SelectTrigger>
                    <SelectContent>
                      {selectedCustomer?.loans.map(loan => (
                        <SelectItem key={loan.loan_id} value={loan.loan_id}>
                          {loan.loan_id} · {loan.product}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <label htmlFor="advisor_id" className="text-xs font-medium">Advisor</label>
                  <Select
                    value={formData.advisor_id ?? ''}
                    onValueChange={handleAdvisorChange}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select advisor" />
                    </SelectTrigger>
                    <SelectContent>
                      {seeds.advisors.map(advisor => (
                        <SelectItem key={advisor.advisor_id} value={advisor.advisor_id}>
                          {advisor.display_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 text-xs space-y-2">
                <div className="font-semibold text-slate-700">Profile Summary</div>
                {selectedCustomer && (
                  <div className="space-y-1">
                    <div><span className="font-medium">Customer:</span> {selectedCustomer.name} · {selectedCustomer.segment}</div>
                    <div><span className="font-medium">Preferred Channel:</span> {selectedCustomer.preferred_channel}</div>
                    <div><span className="font-medium">Risk Flags:</span> {selectedCustomer.risk_flags.join(', ') || 'None'}</div>
                    <div><span className="font-medium">Property:</span> {selectedCustomer.property.address}</div>
                  </div>
                )}
                {selectedLoan && (
                  <div className="space-y-1">
                    <div><span className="font-medium">Loan Product:</span> {selectedLoan.product}</div>
                    <div><span className="font-medium">Balance:</span> ${selectedLoan.principal_balance.toLocaleString()}</div>
                    <div><span className="font-medium">Monthly Payment:</span> ${selectedLoan.monthly_payment.toLocaleString()}</div>
                    <div><span className="font-medium">Tags:</span> {selectedLoan.tags.join(', ') || 'None'}</div>
                  </div>
                )}
                {selectedAdvisor && (
                  <div className="space-y-1">
                    <div><span className="font-medium">Advisor:</span> {selectedAdvisor.name}</div>
                    <div><span className="font-medium">Team:</span> {selectedAdvisor.team}</div>
                    <div><span className="font-medium">Specialization:</span> {formatLabel(selectedAdvisor.specialization)}</div>
                  </div>
                )}
              </div>

              <div className="space-y-2">
                <label htmlFor="context" className="text-xs font-medium">Conversation Context (optional)</label>
                <textarea
                  id="context"
                  value={formData.context ?? ''}
                  onChange={(e) => handleInputChange('context', e.target.value)}
                  placeholder="E.g., Customer is calling for the second time about escrow overages and expects a supervisor follow-up."
                  className="w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-slate-400 focus:outline-none focus:ring-1 focus:ring-slate-400"
                  rows={3}
                />
                <p className="text-xs text-gray-500">
                  This narrative is passed to the generator so transcripts stay consistent with prior calls or promised actions.
                </p>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="financial_impact"
                  checked={Boolean(formData.financial_impact)}
                  onChange={(e) => handleInputChange('financial_impact', e.target.checked)}
                  className="rounded border-gray-300"
                />
                <label htmlFor="financial_impact" className="text-xs font-medium">Financial Impact</label>
                <span className="text-sm text-gray-500">
                  Indicates if this transcript involves financial matters
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="store"
                  checked={Boolean(formData.store)}
                  onChange={(e) => handleInputChange('store', e.target.checked)}
                  className="rounded border-gray-300"
                />
                <label htmlFor="store" className="text-xs font-medium">Store Transcript</label>
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

        <Card className="panel">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm font-bold">
              <Plus className="h-4 w-4" />
              Bulk Generate Transcripts
            </CardTitle>
            <CardDescription>
              Generate multiple transcripts rotating through seeded customers and advisors.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleBulkSubmit} className="space-y-4">
              {createBulkTranscriptsMutation.error && (
                <div className="border border-slate-200 bg-slate-50 p-3 rounded-lg flex items-start gap-2">
                  <AlertCircle className="h-4 w-4 text-red-600 mt-0.5" />
                  <div className="text-slate-700">
                    Failed to create bulk transcripts. Please try again.
                  </div>
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="bulk_count" className="text-xs font-medium">Number of Transcripts</label>
                <Input
                  id="bulk_count"
                  type="number"
                  min="1"
                  max="50"
                  value={bulkCount}
                  onChange={(e) => setBulkCount(Math.min(50, Math.max(1, parseInt(e.target.value, 10) || 1)))}
                  placeholder="Enter number of transcripts to generate"
                />
                <p className="text-xs text-gray-500">
                  Customers and advisors will automatically rotate if more transcripts are requested than selected profiles.
                </p>
              </div>

              <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                <h4 className="text-xs font-medium">Template Configuration</h4>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="font-medium">Topic:</span> {formatLabel(formData.topic)}
                  </div>
                  <div>
                    <span className="font-medium">Urgency:</span> {formatLabel(formData.urgency)}
                  </div>
                  <div>
                    <span className="font-medium">Sentiment:</span> {formatLabel(formData.customer_sentiment)}
                  </div>
                  <div>
                    <span className="font-medium">Customer:</span> {selectedCustomer?.display_name ?? 'Rotating'}
                  </div>
                  <div>
                    <span className="font-medium">Loan:</span> {selectedLoan ? `${selectedLoan.loan_id} · ${selectedLoan.product}` : 'Derived'}
                  </div>
                  <div>
                    <span className="font-medium">Advisor:</span> {selectedAdvisor?.display_name ?? 'Rotating'}
                  </div>
                  <div>
                    <span className="font-medium">Financial Impact:</span> {formData.financial_impact ? 'Yes' : 'No'}
                  </div>
                  <div>
                    <span className="font-medium">Store:</span> {formData.store ? 'Yes' : 'No'}
                  </div>
                  <div className="col-span-2">
                    <span className="font-medium">Context:</span> {formData.context && formData.context.trim().length > 0 ? formData.context : 'None'}
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
