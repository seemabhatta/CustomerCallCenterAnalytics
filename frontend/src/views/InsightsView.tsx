import React from "react";
import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Legend, Tooltip as RTooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { insightsApi } from "@/api/client";
import { Lightbulb, TrendingUp, AlertTriangle, Target } from "lucide-react";

// Mock data for insights
const mockInsights = {
  borrower_pain: [
    "Fee confusion on refinance",
    "APR vs monthly payment mismatch",
    "Unclear closing timeline",
    "Document requirements complexity"
  ],
  advisor_coaching: [
    "Proactive fee explanation",
    "Use disclosure template",
    "Schedule follow-up calls",
    "Improve document preparation guidance"
  ],
  compliance_alerts: [
    "Late disclosure mention",
    "Missing APR explanation",
    "Incomplete risk assessment documentation",
    "Required cooling-off period not mentioned"
  ],
};

const mockRiskByPersona = [
  { persona: "BORROWER", HIGH: 1, MEDIUM: 3, LOW: 2 },
  { persona: "ADVISOR", HIGH: 2, MEDIUM: 1, LOW: 1 },
  { persona: "SUPERVISOR", HIGH: 3, MEDIUM: 0, LOW: 0 },
  { persona: "LEADERSHIP", HIGH: 3, MEDIUM: 2, LOW: 1 },
];

const mockActionableSteps = [
  "Enable MEDIUM auto-approval for Borrower confirmations",
  "Add advisor checklist on fee explanation",
  "Launch supervisor audit batch for 20 calls",
  "Update disclosure templates with clearer language",
  "Implement automated compliance checking",
];

const mockTrendData = [
  { month: "Jan", riskScore: 65, resolution: 78 },
  { month: "Feb", riskScore: 58, resolution: 82 },
  { month: "Mar", riskScore: 52, resolution: 85 },
  { month: "Apr", riskScore: 48, resolution: 88 },
  { month: "May", riskScore: 45, resolution: 91 },
  { month: "Jun", riskScore: 42, resolution: 94 },
];

function RiskByPersonaChart({ data }: { data: Array<{ persona: string; HIGH: number; MEDIUM: number; LOW: number }> }) {
  return (
    <Card className="rounded-2xl">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Risk Distribution by Persona</CardTitle>
      </CardHeader>
      <CardContent className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="persona" />
            <YAxis allowDecimals={false} />
            <Legend />
            <RTooltip />
            <Bar dataKey="HIGH" stackId="a" fill="#ef4444" name="High Risk" />
            <Bar dataKey="MEDIUM" stackId="a" fill="#f59e0b" name="Medium Risk" />
            <Bar dataKey="LOW" stackId="a" fill="#10b981" name="Low Risk" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function TrendChart({ data }: { data: Array<{ month: string; riskScore: number; resolution: number }> }) {
  return (
    <Card className="rounded-2xl">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">Risk & Resolution Trends</CardTitle>
      </CardHeader>
      <CardContent className="h-56">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="month" />
            <YAxis />
            <Legend />
            <RTooltip />
            <Bar dataKey="riskScore" fill="#ef4444" name="Risk Score" />
            <Bar dataKey="resolution" fill="#10b981" name="Resolution %" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function InsightCard({ 
  title, 
  items, 
  icon: Icon, 
  variant = "default" 
}: { 
  title: string; 
  items: string[]; 
  icon: React.ComponentType<any>;
  variant?: "default" | "warning" | "success";
}) {
  const cardColors = {
    default: "border-blue-200 bg-blue-50",
    warning: "border-amber-200 bg-amber-50",
    success: "border-green-200 bg-green-50",
  };

  const iconColors = {
    default: "text-blue-600",
    warning: "text-amber-600", 
    success: "text-green-600",
  };

  return (
    <Card className={`rounded-2xl ${cardColors[variant]}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm flex items-center gap-2">
          <Icon className={`h-4 w-4 ${iconColors[variant]}`} />
          {title}
          <Badge variant="secondary" className="ml-auto">
            {items.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="text-sm space-y-2">
        {items.map((item, idx) => (
          <div key={idx} className="flex items-start gap-2">
            <span className="text-slate-400 mt-1">•</span>
            <span>{item}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

export function InsightsView() {
  // In a real implementation, these would fetch from the API
  // const { data: insights, isLoading, error } = useQuery({
  //   queryKey: ['insights-dashboard'],
  //   queryFn: () => insightsApi.getDashboard(),
  // });

  // const { data: riskPatterns } = useQuery({
  //   queryKey: ['risk-patterns'],
  //   queryFn: () => insightsApi.discoverPatterns(),
  // });

  // Using mock data for now
  const isLoading = false;
  const error = null;
  const insights = mockInsights;

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => (
            <Card key={i} className="rounded-2xl animate-pulse">
              <CardContent className="h-48"></CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-4">
        <div className="text-red-600">
          Error loading insights: {(error as any)?.detail || 'Unknown error'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Key Insights Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <InsightCard
          title="Borrower Pain Points"
          items={insights.borrower_pain}
          icon={AlertTriangle}
          variant="warning"
        />
        <InsightCard
          title="Advisor Coaching Opportunities"
          items={insights.advisor_coaching}
          icon={Target}
          variant="default"
        />
        <InsightCard
          title="Compliance Alerts"
          items={insights.compliance_alerts}
          icon={Lightbulb}
          variant="warning"
        />
      </div>

      {/* Charts and Analysis */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <RiskByPersonaChart data={mockRiskByPersona} />
        <TrendChart data={mockTrendData} />
      </div>

      {/* Actionable Recommendations */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <InsightCard
          title="Actionable Next Steps"
          items={mockActionableSteps}
          icon={TrendingUp}
          variant="success"
        />
        
        <Card className="rounded-2xl">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Risk Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-red-600">
                  {mockRiskByPersona.reduce((sum, p) => sum + p.HIGH, 0)}
                </div>
                <div className="text-xs text-slate-500">High Risk</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-amber-600">
                  {mockRiskByPersona.reduce((sum, p) => sum + p.MEDIUM, 0)}
                </div>
                <div className="text-xs text-slate-500">Medium Risk</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {mockRiskByPersona.reduce((sum, p) => sum + p.LOW, 0)}
                </div>
                <div className="text-xs text-slate-500">Low Risk</div>
              </div>
            </div>
            
            <div className="border-t pt-4">
              <div className="text-sm font-medium mb-2">Top Risk Categories</div>
              <div className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <span>Disclosure Issues</span>
                  <Badge variant="destructive" className="text-xs">High</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Fee Transparency</span>
                  <Badge variant="default" className="text-xs">Medium</Badge>
                </div>
                <div className="flex justify-between">
                  <span>Documentation</span>
                  <Badge variant="secondary" className="text-xs">Low</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}