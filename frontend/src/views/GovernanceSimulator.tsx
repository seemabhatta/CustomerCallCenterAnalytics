import React, { useState, useMemo } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

// Mock checkbox component since we didn't implement it yet
function Checkbox({ checked, onCheckedChange, children, ...props }: any) {
  return (
    <label className="flex items-center gap-2 cursor-pointer">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onCheckedChange?.(e.target.checked)}
        className="rounded border-gray-300"
        {...props}
      />
      {children}
    </label>
  );
}

// Mock data for risk patterns
const mockRiskByPersona = [
  { persona: "BORROWER", HIGH: 1, MEDIUM: 2, LOW: 3 },
  { persona: "ADVISOR", HIGH: 2, MEDIUM: 1, LOW: 2 },
  { persona: "SUPERVISOR", HIGH: 3, MEDIUM: 0, LOW: 1 },
  { persona: "LEADERSHIP", HIGH: 3, MEDIUM: 1, LOW: 0 },
];

const mockRun = {
  funnel: { generated: 10, approved: 2, executed: 1, failed: 0 },
};

export function GovernanceSimulator() {
  const [autoLow, setAutoLow] = useState(true);
  const [autoMediumBorrower, setAutoMediumBorrower] = useState(false);
  const [autoMediumAdvisor, setAutoMediumAdvisor] = useState(false);
  const [requireTwoPersonHigh, setRequireTwoPersonHigh] = useState(true);
  const [customThreshold, setCustomThreshold] = useState("0.8");

  const projected = useMemo(() => {
    let exec = mockRun.funnel.executed;
    
    if (autoLow) {
      exec += mockRiskByPersona.reduce((acc, p) => acc + (p.LOW || 0), 0);
    }
    
    if (autoMediumBorrower) {
      exec += (mockRiskByPersona.find(p => p.persona === "BORROWER")?.MEDIUM || 0);
    }
    
    if (autoMediumAdvisor) {
      exec += (mockRiskByPersona.find(p => p.persona === "ADVISOR")?.MEDIUM || 0);
    }
    
    return exec;
  }, [autoLow, autoMediumBorrower, autoMediumAdvisor]);

  const policyJson = useMemo(() => ({
    rules: {
      autoApprove: {
        LOW: autoLow,
        MEDIUM: { 
          BORROWER: autoMediumBorrower, 
          ADVISOR: autoMediumAdvisor, 
          SUPERVISOR: false, 
          LEADERSHIP: false 
        },
      },
      approvals: { 
        HIGH: requireTwoPersonHigh ? 2 : 1 
      },
      thresholds: {
        riskScore: parseFloat(customThreshold) || 0.8
      }
    },
  }), [autoLow, autoMediumBorrower, autoMediumAdvisor, requireTwoPersonHigh, customThreshold]);

  const handlePreviewPolicy = () => {
    alert(JSON.stringify(policyJson, null, 2));
  };

  const handleSavePolicy = () => {
    alert("POST /api/v1/governance/policy → saved (this would save to the backend)");
  };

  const handleResetToDefaults = () => {
    setAutoLow(true);
    setAutoMediumBorrower(false);
    setAutoMediumAdvisor(false);
    setRequireTwoPersonHigh(true);
    setCustomThreshold("0.8");
  };

  return (
    <div className="space-y-6">
      <Card className="rounded-2xl">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg">Approval Policy — What‑if Simulator</CardTitle>
          <p className="text-sm text-slate-600">
            Configure approval rules and see projected execution rates in real-time.
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Auto-approval Settings */}
          <div>
            <h3 className="text-sm font-medium mb-3">Auto-Approval Rules</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Checkbox 
                checked={autoLow} 
                onCheckedChange={setAutoLow}
              >
                Auto-approve <strong>LOW</strong> risk for all personas
              </Checkbox>
              
              <Checkbox 
                checked={requireTwoPersonHigh} 
                onCheckedChange={setRequireTwoPersonHigh}
              >
                Require <strong>two-person</strong> approval for HIGH risk
              </Checkbox>
              
              <Checkbox 
                checked={autoMediumBorrower} 
                onCheckedChange={setAutoMediumBorrower}
              >
                Auto-approve <strong>MEDIUM</strong> risk for BORROWER
              </Checkbox>
              
              <Checkbox 
                checked={autoMediumAdvisor} 
                onCheckedChange={setAutoMediumAdvisor}
              >
                Auto-approve <strong>MEDIUM</strong> risk for ADVISOR
              </Checkbox>
            </div>
          </div>

          {/* Risk Thresholds */}
          <div>
            <h3 className="text-sm font-medium mb-3">Risk Thresholds</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="text-xs text-slate-500">Risk Score Threshold</label>
                <Input
                  type="number"
                  step="0.1"
                  min="0"
                  max="1"
                  value={customThreshold}
                  onChange={(e) => setCustomThreshold(e.target.value)}
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-xs text-slate-500">Current Setting</label>
                <div className="mt-1 p-2 bg-slate-50 rounded border text-sm">
                  {parseFloat(customThreshold) >= 0.8 ? "Strict" : "Moderate"}
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-500">Impact</label>
                <div className="mt-1 p-2 bg-slate-50 rounded border text-sm">
                  {parseFloat(customThreshold) >= 0.8 ? "Fewer auto-approvals" : "More auto-approvals"}
                </div>
              </div>
            </div>
          </div>

          {/* Simulation Results */}
          <div className="border-t pt-4">
            <h3 className="text-sm font-medium mb-3">Simulation Results</h3>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{projected}</div>
                <div className="text-xs text-slate-500">Projected Executed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-slate-600">
                  {mockRun.funnel.executed}
                </div>
                <div className="text-xs text-slate-500">Baseline Executed</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  +{projected - mockRun.funnel.executed}
                </div>
                <div className="text-xs text-slate-500">Improvement</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {((projected / mockRun.funnel.generated) * 100).toFixed(0)}%
                </div>
                <div className="text-xs text-slate-500">Execution Rate</div>
              </div>
            </div>
          </div>

          {/* Current Policy Summary */}
          <div className="border-t pt-4">
            <h3 className="text-sm font-medium mb-3">Current Policy Summary</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-xs text-slate-500 mb-1">Auto-Approved</div>
                <div className="space-y-1">
                  {autoLow && <Badge variant="secondary" className="mr-1">LOW (All)</Badge>}
                  {autoMediumBorrower && <Badge variant="default" className="mr-1">MEDIUM (Borrower)</Badge>}
                  {autoMediumAdvisor && <Badge variant="default" className="mr-1">MEDIUM (Advisor)</Badge>}
                  {!autoLow && !autoMediumBorrower && !autoMediumAdvisor && (
                    <span className="text-slate-400">None</span>
                  )}
                </div>
              </div>
              <div>
                <div className="text-xs text-slate-500 mb-1">Manual Approval Required</div>
                <div className="space-y-1">
                  <Badge variant="destructive" className="mr-1">
                    HIGH ({requireTwoPersonHigh ? "2-person" : "1-person"})
                  </Badge>
                  {!autoMediumBorrower && (
                    <Badge variant="outline" className="mr-1">MEDIUM (Others)</Badge>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4 border-t">
            <Button variant="outline" onClick={handlePreviewPolicy}>
              Preview Policy JSON
            </Button>
            <Button onClick={handleSavePolicy}>
              Save Policy
            </Button>
            <Button variant="outline" onClick={handleResetToDefaults}>
              Reset to Defaults
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Policy Impact Analysis */}
      <Card className="rounded-2xl">
        <CardHeader className="pb-4">
          <CardTitle className="text-sm">Policy Impact Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-lg font-semibold text-green-700">
                {Math.round(((projected - mockRun.funnel.executed) / mockRun.funnel.generated) * 100)}%
              </div>
              <div className="text-sm text-green-600">Efficiency Gain</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-lg font-semibold text-blue-700">
                {mockRun.funnel.generated - projected}
              </div>
              <div className="text-sm text-blue-600">Manual Reviews</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-lg font-semibold text-purple-700">
                {Math.round((projected / mockRun.funnel.generated) * 1440)}
              </div>
              <div className="text-sm text-purple-600">Minutes Saved/Day</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}