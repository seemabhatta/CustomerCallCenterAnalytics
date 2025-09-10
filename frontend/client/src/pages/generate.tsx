import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";

export default function GeneratePage() {
  const [isLoading, setIsLoading] = useState(false);
  const [scenario, setScenario] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [sentiment, setSentiment] = useState("");
  const [urgency, setUrgency] = useState("");
  const [notes, setNotes] = useState("");
  const [generatedTranscript, setGeneratedTranscript] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      const response = await fetch('/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          scenario,
          customer_id: customerId,
          sentiment,
          urgency,
          notes,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate transcript');
      }

      const result = await response.json();
      
      // Store the generated transcript for preview
      setGeneratedTranscript(result);
      
      toast({
        title: "Success", 
        description: `Transcript generated successfully! ID: ${result.transcript_id}`,
      });

    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate transcript. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!generatedTranscript) return;
    
    setIsSaving(true);
    try {
      // The transcript is already stored when store=true in generation
      // This is just for user confirmation
      toast({
        title: "Saved!",
        description: `Transcript ${generatedTranscript.transcript_id} has been saved to the database.`,
      });
      
      // Clear form and transcript preview
      setScenario("");
      setCustomerId("");
      setSentiment("");
      setUrgency("");
      setNotes("");
      setGeneratedTranscript(null);
      
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save transcript.",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const handleClearPreview = () => {
    setGeneratedTranscript(null);
    setScenario("");
    setCustomerId("");
    setSentiment("");
    setUrgency("");
    setNotes("");
  };

  return (
    <div className="p-4 max-w-screen-2xl mx-auto space-y-4">
      <div className="mb-4">
        <h1 className="text-xl font-medium text-gray-900">Generate Transcript</h1>
        <p className="text-sm text-gray-500">
          Create new call center transcripts using AI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Generation Form */}
        <div>
          <div className="rounded-lg bg-gray-50 border border-gray-200 p-4 shadow-sm">
            <div className="mb-4">
              <h3 className="text-lg font-medium text-gray-900">Transcript Generation</h3>
              <p className="text-sm text-gray-500">
                Generate realistic customer call transcripts with customizable parameters
              </p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-gray-700">Scenario</label>
                    <select 
                      value={scenario} 
                      onChange={(e) => setScenario(e.target.value)}
                      required
                      className="px-2 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">Select scenario</option>
                      <option value="PMI Removal">PMI Removal</option>
                      <option value="Payment Dispute">Payment Dispute</option>
                      <option value="Refinance">Refinance</option>
                      <option value="Escrow Shortage">Escrow Shortage</option>
                      <option value="Late Payment">Late Payment</option>
                      <option value="Loan Modification">Loan Modification</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium text-gray-700">Customer ID</label>
                    <input
                      type="text"
                      value={customerId}
                      onChange={(e) => setCustomerId(e.target.value)}
                      placeholder="CUST_001"
                      required
                      className="px-2 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="text-sm font-medium text-gray-700">Sentiment</label>
                    <select 
                      value={sentiment} 
                      onChange={(e) => setSentiment(e.target.value)}
                      className="px-2 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">Select sentiment</option>
                      <option value="frustrated">Frustrated</option>
                      <option value="neutral">Neutral</option>
                      <option value="hopeful">Hopeful</option>
                      <option value="anxious">Anxious</option>
                      <option value="satisfied">Satisfied</option>
                    </select>
                  </div>

                  <div className="space-y-1">
                    <label className="text-sm font-medium text-gray-700">Urgency</label>
                    <select 
                      value={urgency} 
                      onChange={(e) => setUrgency(e.target.value)}
                      className="px-2 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    >
                      <option value="">Select urgency</option>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="critical">Critical</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">Additional Notes</label>
                  <textarea
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Any specific requirements or context for the transcript..."
                    rows={3}
                    className="px-2 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full"
                  />
                </div>

                <button type="submit" disabled={isLoading || generatedTranscript} className="w-full px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed">
                  {isLoading ? "Generating..." : "Generate Transcript"}
                </button>
              </form>
            </div>
          </div>

        {/* Preview Section */}
        {generatedTranscript && (
          <div>
            <Card>
              <CardHeader>
                <CardTitle>Generated Transcript Preview</CardTitle>
                <CardDescription>
                  Review the generated transcript before saving
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Transcript Info */}
                <div className="bg-muted/30 p-4 rounded-lg">
                  <h3 className="font-semibold mb-2">Transcript Details</h3>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div><strong>ID:</strong> {generatedTranscript.transcript_id}</div>
                    <div><strong>Customer:</strong> {generatedTranscript.customer_id}</div>
                    <div><strong>Scenario:</strong> {generatedTranscript.scenario}</div>
                    <div><strong>Messages:</strong> {generatedTranscript.message_count}</div>
                  </div>
                </div>

                {/* Conversation */}
                <div>
                  <h3 className="font-semibold mb-2">Conversation</h3>
                  <div className="border rounded-lg p-4 max-h-96 overflow-y-auto space-y-3">
                    {generatedTranscript.messages?.map((message: any, index: number) => (
                      <div 
                        key={index} 
                        className={`p-3 rounded-lg ${
                          message.speaker === 'Customer' 
                            ? 'bg-blue-50 border-l-4 border-blue-400' 
                            : 'bg-green-50 border-l-4 border-green-400'
                        }`}
                      >
                        <div className="font-medium text-sm text-muted-foreground mb-1">
                          {message.speaker}
                        </div>
                        <div className="text-sm">{message.text}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button onClick={handleSave} disabled={isSaving} className="flex-1">
                    {isSaving ? "Saving..." : "Save to Database"}
                  </Button>
                  <Button onClick={handleClearPreview} variant="outline" className="flex-1">
                    Generate Another
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
}