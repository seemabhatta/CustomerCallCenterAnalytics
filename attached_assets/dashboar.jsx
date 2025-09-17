// orchestration_dashboard_preview.jsx (fixed, plain JSX)
import React from "react";

export default function DashboardPreview() {
  const [panel, setPanel] = React.useState(null);

  // Demo data so the panel and grouping work
  const rows = [
    {
      id: "TX-1001",
      transcript: "Borrower called about payment relief options…",
      analyze: { status: "done" }, // done|pending|queued
      plan: { status: "pending_approval" }, // pending_approval|done|queued
      workflows: [
        { id: "WF-1", name: "Send Hardship Packet", type: "Borrower", status: "queued" },
        { id: "WF-2", name: "DTI Exception Review", type: "Supervisor", status: "pending" },
      ],
      planDetails: [
        { id: "PLAN-1", name: "Hardship Assistance", risks: ["CFPB loss mit"], approvals: ["Supervisor"] },
      ],
    },
    {
      id: "TX-1002",
      transcript: "Advisor discussed refinance scenarios…",
      analyze: { status: "done" },
      plan: { status: "done" },
      workflows: [
        { id: "WF-3", name: "Rate Options Email", type: "Advisor", status: "done" },
        { id: "WF-4", name: "Leadership Pricing Review", type: "Leadership", status: "pending" },
      ],
      planDetails: [
        { id: "PLAN-2", name: "Refi Evaluation", risks: ["pricing-volatility"], approvals: ["Leadership"] },
      ],
    },
    {
      id: "TX-1003",
      transcript: "Escrow analysis requested…",
      analyze: { status: "pending" },
      plan: { status: "queued" },
      workflows: [
        { id: "WF-5", name: "Escrow Projection", type: "Advisor", status: "queued" },
      ],
      planDetails: [
        { id: "PLAN-3", name: "Escrow Adjustment", risks: [], approvals: [] },
      ],
    },
  ];

  const wfTypes = ["Borrower", "Advisor", "Supervisor", "Leadership"];

  const [visible, setVisible] = React.useState({
    Borrower: true,
    Advisor: true,
    Supervisor: true,
    Leadership: true,
  });
  const [onlyPending, setOnlyPending] = React.useState(false);

  const countsByType = rows
    .flatMap(r => r.workflows || [])
    .reduce((acc, w) => {
      acc[w.type] = (acc[w.type] || 0) + 1;
      return acc;
    }, {});

  const Badge = ({ children }) => (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-gray-100 text-gray-700 border border-gray-200 text-[11px]">
      {children}
    </span>
  );

  const StatusIcon = ({ s }) => {
    if (s === "done") return <span className="text-green-600 font-bold">✓</span>;
    if (s === "pending") return <span className="text-yellow-600">⏳</span>;
    if (s === "queued") return <span className="text-blue-600">➜</span>;
    if (s === "pending_approval") return <span className="text-orange-600">📝</span>;
    return <span className="text-gray-500">⏸</span>;
  };

  const openPanel = (id, mode) => setPanel({ id, mode });
  const closePanel = () => setPanel(null);

  // Group workflows by type
  const grouped = wfTypes.map((t) => ({
    type: t,
    items: rows
      .flatMap(r =>
        (r.workflows || []).map(w => ({
          ...w,
          txId: r.id,
          analyzeStatus: r.analyze?.status,
          planStatus: r.plan?.status,
        }))
      )
      .filter(w => w.type === t)
      .filter(w => (visible[t] ? true : false))
      .filter(w => (onlyPending ? (w.status === "pending" || w.status === "pending_approval") : true)),
  }));

  return (
    <div className="p-6 space-y-6 bg-gray-50 min-h-screen font-mono text-sm">
      <header className="flex items-center justify-between">
        <h1 className="font-bold text-lg">Transcript Pipeline Manager</h1>
        <div className="flex gap-2">
          {wfTypes.map((t) => (
            <button
              key={t}
              onClick={() => setVisible(v => ({ ...v, [t]: !v[t] }))}
              className={
                "px-2 py-1 rounded-full text-xs border transition " +
                (visible[t]
                  ? "bg-blue-50 border-blue-300 text-blue-700"
                  : "bg-white border-gray-300 text-gray-600 line-through opacity-70")
              }
              aria-pressed={visible[t]}
              title={`Toggle ${t}`}
            >
              {t} <span className="ml-1">({countsByType[t] || 0})</span>
            </button>
          ))}
          <label className="ml-2 inline-flex items-center gap-1 text-xs">
            <input
              type="checkbox"
              checked={onlyPending}
              onChange={e => setOnlyPending(e.target.checked)}
            />
            Only Pending
          </label>
        </div>
      </header>

      {/* Simple transcript table with quick actions */}
      <section className="bg-white border rounded-xl shadow-sm">
        <div className="px-4 py-3 border-b font-semibold">Transcripts</div>
        <div className="overflow-x-auto">
          <table className="min-w-full text-left">
            <thead className="bg-gray-100">
              <tr>
                <th className="px-3 py-2">Transcript ID</th>
                <th className="px-3 py-2">Analyze</th>
                <th className="px-3 py-2">Plan</th>
                <th className="px-3 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} className="border-t">
                  <td className="px-3 py-2">
                    <div className="font-medium">{r.id}</div>
                    <div className="text-[11px] text-gray-500 truncate max-w-[420px]">{r.transcript}</div>
                  </td>
                  <td className="px-3 py-2">
                    <Badge><StatusIcon s={r.analyze?.status} /> <span className="ml-1 capitalize">{r.analyze?.status || "n/a"}</span></Badge>
                  </td>
                  <td className="px-3 py-2">
                    <Badge><StatusIcon s={r.plan?.status} /> <span className="ml-1 capitalize">{r.plan?.status || "n/a"}</span></Badge>
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex gap-2">
                      <button className="border rounded px-2 py-1" onClick={() => openPanel(r.id, "analyze")}>View Analyze</button>
                      <button className="border rounded px-2 py-1" onClick={() => openPanel(r.id, "plan")}>View Plan</button>
                    </div>
                  </td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-3 py-6 text-center text-gray-500">No transcripts.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      {/* Workflows grouped by type */}
      <section className="bg-white border rounded-xl shadow-sm">
        <div className="px-4 py-3 border-b font-semibold">Workflows (Grouped)</div>
        <div className="p-4 grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          {grouped.map(group => (
            <div key={group.type} className="border rounded-lg">
              <div className="px-3 py-2 border-b font-semibold flex items-center justify-between">
                <span>{group.type}</span>
                <Badge>{group.items.length}</Badge>
              </div>
              <ul className="p-3 space-y-2">
                {group.items.map(item => (
                  <li key={item.id} className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-sm font-medium truncate">{item.name}</div>
                      <div className="text-[11px] text-gray-500">From: {item.txId}</div>
                    </div>
                    <Badge><StatusIcon s={item.status} /> <span className="ml-1 capitalize">{item.status}</span></Badge>
                  </li>
                ))}
                {group.items.length === 0 && (
                  <li className="text-xs text-gray-500">No items</li>
                )}
              </ul>
            </div>
          ))}
        </div>
      </section>

      {/* Right-side Explainability Panel */}
      {panel && (
        <div className="fixed inset-0 z-50 flex">
          <div className="flex-1 bg-black/30" onClick={closePanel} />
          <div className="w-[420px] max-w-[90vw] bg-white h-full shadow-xl border-l p-4 overflow-y-auto">
            <div className="flex items-center justify-between">
              <h3 className="font-bold">{panel.mode === "analyze" ? "Analyze Details" : "Plan Details"}</h3>
              <button onClick={closePanel} className="text-gray-500 hover:text-gray-700">✕</button>
            </div>
            <div className="text-xs text-gray-500 mt-1">Transcript: {panel.id}</div>

            {(() => {
              const row = rows.find(x => x.id === panel.id);
              if (!row) {
                return <div className="mt-4 text-xs text-red-600">Unable to load details.</div>;
              }
              if (panel.mode === "analyze") {
                return (
                  <div className="mt-4 space-y-3">
                    <div className="text-sm font-semibold">Analysis Summary</div>
                    <p className="text-xs text-gray-700">
                      Status: <span className="capitalize">{row.analyze?.status || "n/a"}</span>
                    </p>
                    <div className="pt-2 border-t">
                      <div className="text-xs uppercase text-gray-500 mb-1">Traceability</div>
                      <p className="text-xs text-gray-600">
                        This analysis produced the following plan and workflows:
                      </p>
                      <ul className="list-disc list-inside text-sm">
                        {(row.workflows || []).map(w => <li key={w.id}>{w.name} — {w.type || "System"}</li>)}
                      </ul>
                      <div className="mt-2 flex gap-2">
                        <a className="underline text-blue-600 cursor-pointer" onClick={() => setPanel({ id: panel.id, mode: "plan" })}>View Plan</a>
                      </div>
                    </div>
                  </div>
                );
              }
              return (
                <div className="mt-4 space-y-3">
                  <ul className="space-y-2">
                    {(row.planDetails || []).map((p) => (
                      <li key={p.id} className="flex items-start justify-between">
                        <div>
                          <div className="text-sm font-medium">{p.name}</div>
                          {p.risks?.length ? <div className="text-xs text-gray-500">Risks: {p.risks.join(", ")}</div> : null}
                          {p.approvals?.length ? <div className="text-xs text-gray-500">Approvals: {p.approvals.join(", ")}</div> : null}
                        </div>
                        <Badge>{p.id}</Badge>
                      </li>
                    ))}
                  </ul>
                  <div className="pt-2 border-t">
                    <div className="text-xs uppercase text-gray-500 mb-1">Traceability</div>
                    <p className="text-xs text-gray-600">
                      These plan items generated the following workflows (grouped by type in the table):
                    </p>
                    <ul className="list-disc list-inside text-sm">
                      {(row.workflows || []).map((w) => <li key={w.id}>{w.name} — {w.type || "System"}</li>)}
                    </ul>
                    <div className="mt-2 flex gap-2">
                      <a className="underline text-blue-600 cursor-pointer" onClick={() => setPanel({ id: panel.id, mode: "analyze" })}>Back to Analyze</a>
                    </div>
                  </div>
                </div>
              );
            })()}

            <div className="mt-6 pt-3 border-t">
              <div className="text-xs uppercase text-gray-500 mb-1">Audit Links</div>
              <div className="flex flex-wrap gap-2 text-xs">
                <button className="border rounded px-2 py-1">Open Transcript</button>
                <button className="border rounded px-2 py-1">View Audit Log</button>
                <button className="border rounded px-2 py-1">Export Evidence</button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
