import React, { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Download, ArrowRight, Info } from "lucide-react";

// Mock run data
const mockRuns = [
  {
    id: "RUN_CALL_27FF315B",
    started_at: "2025-09-12T16:41:34Z",
    durations: [
      { stage: "analysis", seconds: 9.7 },
      { stage: "plan", seconds: 24.4 },
      { stage: "workflows", seconds: 110.4 },
      { stage: "approval", seconds: 0.0 },
      { stage: "execution", seconds: 0.0 },
    ],
    funnel: { generated: 10, approved: 0, executed: 0, failed: 0 },
  },
  {
    id: "RUN_CALL_ABCD1234",
    started_at: "2025-09-12T15:30:00Z",
    durations: [
      { stage: "analysis", seconds: 12.3 },
      { stage: "plan", seconds: 18.7 },
      { stage: "workflows", seconds: 95.2 },
      { stage: "approval", seconds: 45.1 },
      { stage: "execution", seconds: 23.8 },
    ],
    funnel: { generated: 8, approved: 6, executed: 5, failed: 1 },
  },
];

export function RunsExplorer() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedRun, setSelectedRun] = useState<any>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const filteredRuns = mockRuns.filter(run => 
    !searchQuery || run.id.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const openRunDialog = (run: any) => {
    setSelectedRun(run);
    setDialogOpen(true);
  };

  const getTotalDuration = (durations: any[]) => {
    return durations.reduce((sum, d) => sum + d.seconds, 0).toFixed(1);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2">
        <Input 
          placeholder="Search run ID" 
          className="w-80" 
          value={searchQuery} 
          onChange={(e) => setSearchQuery(e.target.value)} 
        />
        <Badge variant="secondary">{filteredRuns.length} run(s)</Badge>
        <Button variant="outline" className="ml-auto gap-2">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </div>

      <div className="overflow-hidden rounded-2xl border">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left py-2 px-3">Run</th>
              <th className="text-left py-2 px-3">Started</th>
              <th className="text-left py-2 px-3">Total Duration</th>
              <th className="text-left py-2 px-3">Funnel</th>
              <th className="text-right py-2 px-3">Details</th>
            </tr>
          </thead>
          <tbody>
            {filteredRuns.map(run => (
              <tr key={run.id} className="border-b hover:bg-slate-50">
                <td className="py-2 px-3 font-medium text-slate-900">
                  {run.id}
                </td>
                <td className="py-2 px-3">
                  {new Date(run.started_at).toLocaleString()}
                </td>
                <td className="py-2 px-3">
                  {getTotalDuration(run.durations)}s
                </td>
                <td className="py-2 px-3 text-xs">
                  <div className="space-y-1">
                    <div>Generated: <span className="font-medium">{run.funnel.generated}</span></div>
                    <div>Approved: <span className="font-medium">{run.funnel.approved}</span></div>
                    <div>Executed: <span className="font-medium">{run.funnel.executed}</span></div>
                  </div>
                </td>
                <td className="py-2 px-3 text-right">
                  <Button 
                    size="sm" 
                    variant="outline" 
                    onClick={() => openRunDialog(run)} 
                    className="gap-1"
                  >
                    Open <ArrowRight className="h-4 w-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Run Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-4xl">
          {selectedRun && (
            <div className="space-y-4">
              <DialogHeader>
                <DialogTitle>Run Details • {selectedRun.id}</DialogTitle>
              </DialogHeader>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="rounded-2xl">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Stage Durations</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {selectedRun.durations.map((duration: any, index: number) => (
                      <div key={index} className="flex justify-between items-center">
                        <span className="capitalize">{duration.stage}</span>
                        <Badge variant="outline">
                          {duration.seconds}s
                        </Badge>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card className="rounded-2xl">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm">Pipeline Funnel</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <div className="flex justify-between">
                      <span>Generated</span>
                      <Badge>{selectedRun.funnel.generated}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Approved</span>
                      <Badge>{selectedRun.funnel.approved}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Executed</span>
                      <Badge>{selectedRun.funnel.executed}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span>Failed</span>
                      <Badge variant="destructive">{selectedRun.funnel.failed}</Badge>
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card className="rounded-2xl">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm">Run Artifacts</CardTitle>
                </CardHeader>
                <CardContent className="text-sm space-y-2">
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-slate-500" />
                    Plan ID: <span className="font-medium">PLAN_ANALYSIS_CALL_2</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-slate-500" />
                    Transcript ID: <span className="font-medium">CALL_27FF315B</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Info className="h-4 w-4 text-slate-500" />
                    Analysis Risk: <span className="font-medium">High-heavy</span>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}