import React, { useState } from "react";

// ---- Case Detail Page – aligned with Approval Queue styling ----

const caseMeta = {
  id: 1,
  customer: "CUST_123",
  scenario: "PMI Removal Dispute",
  exchanges: 22,
  impact: "$2,500 potential loss",
  created: "Sep 9, 2025, 08:25 AM",
  risk: "High",
  status: "Needs Supervisor Approval",
};

const transcript = [
  { speaker: "Emily (Servicing Specialist)", text: "Hi James, thanks for reaching out. I understand you’re looking to remove the PMI. Can you tell me about the valuation?" },
  { speaker: "James (Homeowner)", text: "Yes, I had an independent appraisal done, higher than lender’s last assessment. PMI is $200/mo and a burden." },
  { speaker: "Emily", text: "That PMI can add up. We need to confirm compliance before proceeding. Did you submit the appraisal report?" },
  { speaker: "James", text: "Yes, last week. Appraiser valued home at $350,000 vs lender’s $325,000." },
  { speaker: "Lisa (Compliance Officer)", text: "We need to ensure regulatory compliance before removal. Additional review required." },
];

const analysis = {
  intent: { label: "General Inquiry", confidence: 0.9 },
  sentiment: "neutral",
  risks: [
    { label: "Churn", value: 0.23 },
    { label: "Complaint", value: 0.61 },
    { label: "Delinquency", value: 0.0 },
  ],
};

const actions = [
  { action: "Send automated payment reminder email", category: "Routine Communication", risk: "Low", impact: "Minimal", submitted: "Sep 9, 05:48 AM", decision: "Auto‑Approved" },
  { action: "Update customer contact preferences", category: "Routine Communication", risk: "Low", impact: "Minimal", submitted: "Sep 9, 05:48 AM", decision: "Auto‑Approved" },
  { action: "Apply late fee waiver to account", category: "Account Adjustment", risk: "Medium", impact: "$500–1000", submitted: "Sep 9, 05:48 AM", decision: "Approved" },
  { action: "Initiate loan modification process", category: "Loan Restructuring", risk: "High", impact: "$2,500 potential loss", submitted: "Sep 9, 05:48 AM", decision: "Pending" },
  { action: "Approve 90‑day payment deferral", category: "Payment Plan", risk: "Medium", impact: "$450 interest impact", submitted: "Sep 9, 05:48 AM", decision: "Pending" },
];

export default function CaseDetailPage() {
  const [showFull, setShowFull] = useState(false);

  return (
    <div className="p-6 max-w-screen-xl mx-auto space-y-6">
      {/* Header bar */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Customer Service Case #{caseMeta.id}</h1>
          <p className="text-sm text-gray-500">{caseMeta.customer} • {caseMeta.scenario}</p>
        </div>
        <div className="flex gap-2">
          <button className="text-sm rounded-full border px-3 py-1 hover:bg-gray-50">Reject</button>
          <button className="text-sm rounded-full bg-indigo-600 text-white px-3 py-1 hover:bg-indigo-700">Approve Plan</button>
        </div>
      </div>

      {/* Summary */}
      <div className="rounded-2xl border p-4 grid grid-cols-2 gap-4 text-sm">
        <div><span className="text-gray-500">Customer</span><div className="font-medium">{caseMeta.customer}</div></div>
        <div><span className="text-gray-500">Scenario</span><div className="font-medium">{caseMeta.scenario}</div></div>
        <div><span className="text-gray-500">Messages</span><div className="font-medium">{caseMeta.exchanges} exchanges</div></div>
        <div><span className="text-gray-500">Financial Impact</span><div className="font-medium">{caseMeta.impact}</div></div>
        <div><span className="text-gray-500">Risk</span><div className="font-medium text-red-700">{caseMeta.risk}</div></div>
        <div><span className="text-gray-500">Created</span><div className="font-medium">{caseMeta.created}</div></div>
      </div>

      {/* Transcript */}
      <div className="rounded-2xl border p-4">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold">Transcript</h2>
          <button
            onClick={() => setShowFull(!showFull)}
            className="text-xs rounded-full bg-gray-900 text-white px-3 py-1"
          >
            {showFull ? "Hide" : `Show full (${transcript.length})`}
          </button>
        </div>
        <div className="space-y-2 text-sm text-gray-700 max-h-64 overflow-auto">
          {(showFull ? transcript : transcript.slice(0,3)).map((t,i) => (
            <div key={i}><span className="font-semibold text-gray-800">{t.speaker}:</span> {t.text}</div>
          ))}
        </div>
      </div>

      {/* AI Analysis */}
      <div className="rounded-2xl border p-4 space-y-3">
        <h2 className="font-semibold">AI Analysis</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div className="rounded-xl border p-3"><div className="text-xs text-gray-500">Intent</div><div className="font-medium">{analysis.intent.label}</div><div className="text-xs">Confidence {Math.round(analysis.intent.confidence*100)}%</div></div>
          <div className="rounded-xl border p-3"><div className="text-xs text-gray-500">Sentiment</div><div className="font-medium capitalize">{analysis.sentiment}</div></div>
          <div className="rounded-xl border p-3"><div className="text-xs text-gray-500">Risks</div>{analysis.risks.map(r=>(<div key={r.label} className="flex justify-between"><span>{r.label}</span><span className={`font-semibold ${r.value>0.5?"text-red-700":r.value>0.2?"text-amber-600":"text-green-600"}`}>{Math.round(r.value*100)}%</span></div>))}</div>
        </div>
      </div>

      {/* Action Plan */}
      <div className="rounded-2xl border overflow-hidden">
        <div className="px-4 py-2 bg-gray-50 text-sm font-medium">Action Plan Details ({actions.length})</div>
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-left">
            <tr className="text-gray-600">
              <th className="px-4 py-2">Action</th>
              <th className="px-4 py-2">Category</th>
              <th className="px-4 py-2">Risk</th>
              <th className="px-4 py-2">Impact</th>
              <th className="px-4 py-2">Submitted</th>
              <th className="px-4 py-2">Decision</th>
            </tr>
          </thead>
          <tbody>
            {actions.map((a,i)=>(
              <tr key={i} className="border-t hover:bg-gray-50">
                <td className="px-4 py-2 font-medium text-gray-900">{a.action}</td>
                <td className="px-4 py-2">{a.category}</td>
                <td className="px-4 py-2">{a.risk}</td>
                <td className="px-4 py-2">{a.impact}</td>
                <td className="px-4 py-2 whitespace-nowrap">{a.submitted}</td>
                <td className="px-4 py-2">
                  {a.decision.includes("Approved") ? (
                    <span className="text-xs font-medium rounded-full bg-emerald-100 text-emerald-700 px-2.5 py-1">{a.decision}</span>
                  ) : a.decision === "Pending" ? (
                    <div className="flex gap-2">
                      <button className="text-xs rounded-full border px-3 py-1 hover:bg-gray-50">Reject</button>
                      <button className="text-xs rounded-full bg-indigo-600 text-white px-3 py-1 hover:bg-indigo-700">Approve</button>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-500">{a.decision}</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Supervisor Callout */}
      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
        <div className="text-amber-600 text-xl">⚠</div>
        <div><div className="font-semibold text-amber-800">Supervisor Approval Required</div><div className="text-sm text-amber-700">High urgency requires expedited approval</div></div>
      </div>
    </div>
  );
}
