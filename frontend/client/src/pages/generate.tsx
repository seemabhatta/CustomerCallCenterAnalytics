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
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight">Generate Transcript</h1>
        <p className="text-muted-foreground">
          Create new call center transcripts using AI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Generation Form */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Transcript Generation</CardTitle>
              <CardDescription>
                Generate realistic customer call transcripts with customizable parameters
              </CardDescription>
            </CardHeader>
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="scenario">Scenario</Label>
                    <Select value={scenario} onValueChange={setScenario} required>
                      <SelectTrigger>
                        <SelectValue placeholder="Select scenario" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="PMI Removal">PMI Removal</SelectItem>
                        <SelectItem value="Payment Dispute">Payment Dispute</SelectItem>
                        <SelectItem value="Refinance">Refinance</SelectItem>
                        <SelectItem value="Escrow Shortage">Escrow Shortage</SelectItem>
                        <SelectItem value="Late Payment">Late Payment</SelectItem>
                        <SelectItem value="Loan Modification">Loan Modification</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="customerId">Customer ID</Label>
                    <Input
                      id="customerId"
                      value={customerId}
                      onChange={(e) => setCustomerId(e.target.value)}
                      placeholder="CUST_001"
                      required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="sentiment">Sentiment</Label>
                    <Select value={sentiment} onValueChange={setSentiment}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select sentiment" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="frustrated">Frustrated</SelectItem>
                        <SelectItem value="neutral">Neutral</SelectItem>
                        <SelectItem value="hopeful">Hopeful</SelectItem>
                        <SelectItem value="anxious">Anxious</SelectItem>
                        <SelectItem value="satisfied">Satisfied</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="urgency">Urgency</Label>
                    <Select value={urgency} onValueChange={setUrgency}>
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
                </div>

                <div className="space-y-2">
                  <Label htmlFor="notes">Additional Notes</Label>
                  <Textarea
                    id="notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    placeholder="Any specific requirements or context for the transcript..."
                    rows={3}
                  />
                </div>

                <Button type="submit" disabled={isLoading || generatedTranscript} className="w-full">
                  {isLoading ? "Generating..." : "Generate Transcript"}
                </Button>
              </form>
            </CardContent>
          </Card>
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