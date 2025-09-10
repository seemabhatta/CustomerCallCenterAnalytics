import React, { useMemo, useState } from "react";

// ----- Approval Queue – Pro Table (React + Tailwind) -----
// Features: segmented filters, search, sort, compact rows, sticky header, badges, mini progress bar

const MOCK = Array.from({ length: 28 }).map((_, i) => {
  const id = i + 1;
  const pr = 79 + (i % 11); // 79..89
  const pending = (i % 6) + 1;
  const auto = 2 + (i % 3);
  const done = 1 + (i % 2);
  const hour = (8 + (i * 2)) % 24;
  return {
    id,
    cust: `CUST_${1000 + id}`,
    call: `CALL_${Math.random().toString(36).slice(2, 10).toUpperCase()}`,
    priority: pr, // numeric
    reason: "High Risk Review",
    progress: { auto, done, pending },
    time: new Date(2025, 8, 9, hour, (i * 7) % 60), // Sep 9
    status: "Needs Review",
  };
});

const badgeByPriority = (p) =>
  p >= 88 ? "bg-red-100 text-red-700" : p >= 83 ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-700";

const fmtTime = (d) =>
  d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

function Segmented({ value, onChange, items }) {
  return (
    <div className="inline-flex rounded-full border bg-white p-1 shadow-sm">
      {items.map((it) => (
        <button
          key={it.value}
          onClick={() => onChange(it.value)}
          className={`px-3 py-1 text-sm rounded-full ${
            value === it.value ? "bg-gray-900 text-white" : "text-gray-700 hover:bg-gray-50"
          }`}
        >
          {it.label}
          {typeof it.count === "number" && (
            <span className={`ml-2 text-xs font-medium ${value === it.value ? "text-white/80" : "text-gray-500"}`}>{it.count}</span>
          )}
        </button>
      ))}
    </div>
  );
}

function MiniProgress({ auto, done, pending }) {
  const total = auto + done + pending;
  const w = (n) => `${(n / total) * 100}%`;
  return (
    <div className="w-48 h-2.5 bg-gray-100 rounded-full overflow-hidden" aria-label="progress">
      <div className="h-full bg-emerald-400" style={{ width: w(auto) }} />
      <div className="h-full bg-sky-400" style={{ width: w(done) }} />
      <div className="h-full bg-orange-400" style={{ width: w(pending) }} />
    </div>
  );
}

export default function ApprovalQueuePage() {
  const [query, setQuery] = useState("");
  const [seg, setSeg] = useState("all");
  const [sort, setSort] = useState({ key: "priority", dir: "desc" });
  const [dense, setDense] = useState(true);

  const counts = useMemo(() => ({
    all: MOCK.length,
    high: MOCK.filter((r) => r.priority >= 88).length,
    medium: MOCK.filter((r) => r.priority >= 83 && r.priority < 88).length,
  }), []);

  const filtered = useMemo(() => {
    return MOCK.filter((r) => {
      if (seg === "high" && r.priority < 88) return false;
      if (seg === "medium" && (r.priority < 83 || r.priority >= 88)) return false;
      if (!query) return true;
      const s = `${r.id} ${r.cust} ${r.call}`.toLowerCase();
      return s.includes(query.toLowerCase());
    }).sort((a, b) => {
      const dir = sort.dir === "asc" ? 1 : -1;
      if (sort.key === "priority") return dir * (a.priority - b.priority);
      if (sort.key === "pending") return dir * (a.progress.pending - b.progress.pending);
      if (sort.key === "time") return dir * (a.time - b.time);
      return 0;
    });
  }, [seg, query, sort]);

  const Row = ({ r }) => (
    <tr className={`border-t border-gray-100 hover:bg-gray-50 ${dense ? "text-sm" : "text-base"}`}>
      <td className="px-4 py-2.5">
        <a className="text-indigo-700 font-medium hover:underline" href="#">#{r.id} ({r.cust})</a>
        <div className="text-gray-500 text-xs">{r.call}</div>
      </td>
      <td className="px-4 py-2.5 align-middle">
        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badgeByPriority(r.priority)}`}>HIGH{r.priority}</span>
      </td>
      <td className="px-4 py-2.5 text-gray-800">{r.reason}</td>
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-3">
          <MiniProgress {...r.progress} />
          <div className="text-xs text-gray-600 whitespace-nowrap">
            <span className="text-emerald-700 font-medium">{r.progress.auto}</span> auto •
            <span className="text-sky-700 font-medium"> {r.progress.done}</span> done •
            <span className="text-orange-700 font-medium"> {r.progress.pending}</span> pending
          </div>
        </div>
      </td>
      <td className="px-4 py-2.5 text-gray-700 whitespace-nowrap">{fmtTime(r.time)}</td>
      <td className="px-4 py-2.5 font-medium text-gray-900">{r.status}</td>
      <td className="px-4 py-2.5 text-right">
        <button className="text-xs rounded-full border px-3 py-1 hover:bg-gray-50 mr-2">Details</button>
        <button className="text-xs rounded-full bg-indigo-600 text-white px-3 py-1 hover:bg-indigo-700">Approve</button>
      </td>
    </tr>
  );

  const Th = ({ children, k }) => (
    <th className="font-semibold px-4 py-2.5 cursor-pointer select-none text-left text-gray-600" onClick={() => setSort(({ key, dir }) => ({ key: k, dir: key === k && dir === "desc" ? "asc" : "desc" }))}>
      <span className="inline-flex items-center gap-1">
        {children}
        {sort.key === k && <span className="text-gray-400">{sort.dir === "asc" ? "▲" : "▼"}</span>}
      </span>
    </th>
  );

  return (
    <div className="p-4 sm:p-6 max-w-screen-2xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Approval Queue</h1>
          <p className="text-sm text-gray-500">{counts.all} items pending review</p>
        </div>
        <div className="flex items-center gap-2">
          <Segmented
            value={seg}
            onChange={setSeg}
            items={[{ label: "All", value: "all", count: counts.all }, { label: "High", value: "high", count: counts.high }, { label: "Medium", value: "medium", count: counts.medium }]}
          />
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <input
            className="h-9 rounded-xl border px-3 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            placeholder="Search case, customer, or call…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <span className="absolute right-3 top-2.5 text-gray-400">⌘K</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-600">Sort</span>
          <select
            className="h-9 rounded-xl border px-2 text-sm"
            value={`${sort.key}:${sort.dir}`}
            onChange={(e) => {
              const [key, dir] = e.target.value.split(":");
              setSort({ key, dir });
            }}
          >
            <option value="priority:desc">Priority (high→low)</option>
            <option value="priority:asc">Priority (low→high)</option>
            <option value="pending:desc">Pending (more→less)</option>
            <option value="time:desc">Newest first</option>
            <option value="time:asc">Oldest first</option>
          </select>
        </div>
        <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
          <input type="checkbox" checked={dense} onChange={(e) => setDense(e.target.checked)} />
          Compact rows
        </label>
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-gray-200 overflow-hidden shadow-sm">
        <div className="bg-gray-50 sticky top-0 z-10">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <Th k="id">Case ID</Th>
                <Th k="priority">Priority</Th>
                <Th k="reason">Reason</Th>
                <Th k="pending">Progress</Th>
                <Th k="time">Time</Th>
                <Th k="status">Status</Th>
                <th className="px-4 py-2.5 text-right text-gray-600">Actions</th>
              </tr>
            </thead>
          </table>
        </div>
        <div className="max-h-[560px] overflow-auto">
          <table className="w-full text-sm">
            <tbody>
              {filtered.map((r) => (
                <Row key={r.id} r={r} />
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
