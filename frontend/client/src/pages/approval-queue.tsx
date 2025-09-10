import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import type { Case } from "@shared/schema";

const badgeByPriority = (p: number) =>
  p >= 88 ? "bg-red-100 text-red-700" : p >= 83 ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-700";

const fmtTime = (d: Date) =>
  new Date(d).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });

function Segmented({ value, onChange, items }: { 
  value: string; 
  onChange: (value: string) => void; 
  items: Array<{ label: string; value: string; count?: number }> 
}) {
  return (
    <div className="inline-flex rounded-full border border-border bg-card p-1 shadow-sm">
      {items.map((it) => (
        <button
          key={it.value}
          onClick={() => onChange(it.value)}
          className={`px-3 py-1 text-sm rounded-full transition-colors ${
            value === it.value 
              ? "bg-primary text-primary-foreground" 
              : "text-muted-foreground hover:bg-accent"
          }`}
          data-testid={`filter-${it.value}`}
        >
          {it.label}
          {typeof it.count === "number" && (
            <span className={`ml-2 text-xs font-medium ${
              value === it.value ? "text-primary-foreground/80" : "text-muted-foreground"
            }`}>
              {it.count}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

function MiniProgress({ auto, done, pending }: { auto: number; done: number; pending: number }) {
  const total = auto + done + pending;
  const w = (n: number) => `${(n / total) * 100}%`;
  return (
    <div className="w-48 h-2.5 bg-muted rounded-full overflow-hidden flex" aria-label="progress">
      <div className="bg-emerald-400" style={{ width: w(auto) }} />
      <div className="bg-sky-400" style={{ width: w(done) }} />
      <div className="bg-orange-400" style={{ width: w(pending) }} />
    </div>
  );
}

export default function ApprovalQueuePage() {
  const [query, setQuery] = useState("");
  const [seg, setSeg] = useState("all");
  const [sort, setSort] = useState({ key: "priority", dir: "desc" });
  const [dense, setDense] = useState(true);

  const { data: cases = [], isLoading } = useQuery<Case[]>({
    queryKey: ["/api/cases"],
  });

  const counts = useMemo(() => ({
    all: cases.length,
    high: cases.filter((r) => r.priority >= 88).length,
    medium: cases.filter((r) => r.priority >= 83 && r.priority < 88).length,
  }), [cases]);

  const filtered = useMemo(() => {
    return cases.filter((r) => {
      if (seg === "high" && r.priority < 88) return false;
      if (seg === "medium" && (r.priority < 83 || r.priority >= 88)) return false;
      if (!query) return true;
      const s = `${r.id} ${r.customerId} ${r.callId}`.toLowerCase();
      return s.includes(query.toLowerCase());
    }).sort((a, b) => {
      const dir = sort.dir === "asc" ? 1 : -1;
      if (sort.key === "priority") return dir * (a.priority - b.priority);
      if (sort.key === "time") return dir * (new Date(a.createdAt!).getTime() - new Date(b.createdAt!).getTime());
      return 0;
    });
  }, [cases, seg, query, sort]);

  const Row = ({ r }: { r: Case }) => (
    <tr className={`border-t border-border hover:bg-accent transition-colors ${dense ? "text-sm" : "text-base"}`}>
      <td className="px-4 py-2.5">
        <Link href={`/case/${r.id}`}>
          <a className="text-primary font-medium hover:underline" data-testid={`case-link-${r.id}`}>
            #{r.id.slice(-4)} ({r.customerId})
          </a>
        </Link>
        <div className="text-muted-foreground text-xs">{r.callId}</div>
      </td>
      <td className="px-4 py-2.5 align-middle">
        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${badgeByPriority(r.priority)}`}>
          HIGH{r.priority}
        </span>
      </td>
      <td className="px-4 py-2.5 text-foreground">{r.scenario}</td>
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-3">
          <MiniProgress auto={2} done={1} pending={2} />
          <div className="text-xs text-muted-foreground whitespace-nowrap">
            <span className="text-emerald-700 font-medium">2</span> auto •
            <span className="text-sky-700 font-medium"> 1</span> done •
            <span className="text-orange-700 font-medium"> 2</span> pending
          </div>
        </div>
      </td>
      <td className="px-4 py-2.5 text-muted-foreground whitespace-nowrap">
        {fmtTime(r.createdAt!)}
      </td>
      <td className="px-4 py-2.5 font-medium text-foreground">{r.status}</td>
      <td className="px-4 py-2.5 text-right">
        <Link href={`/case/${r.id}`}>
          <button className="text-xs rounded-full border border-border px-3 py-1 hover:bg-accent mr-2 transition-colors" data-testid={`button-details-${r.id}`}>
            Details
          </button>
        </Link>
        <button className="text-xs rounded-full bg-primary text-primary-foreground px-3 py-1 hover:bg-primary/90 transition-colors" data-testid={`button-approve-${r.id}`}>
          Approve
        </button>
      </td>
    </tr>
  );

  const Th = ({ children, k }: { children: React.ReactNode; k: string }) => (
    <th 
      className="font-semibold px-4 py-2.5 cursor-pointer select-none text-left text-muted-foreground hover:text-foreground" 
      onClick={() => setSort(({ key, dir }) => ({ key: k, dir: key === k && dir === "desc" ? "asc" : "desc" }))}
    >
      <span className="inline-flex items-center gap-1">
        {children}
        {sort.key === k && <span className="text-muted-foreground">{sort.dir === "asc" ? "▲" : "▼"}</span>}
      </span>
    </th>
  );

  if (isLoading) {
    return (
      <div className="p-4 sm:p-6 max-w-screen-2xl mx-auto">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 sm:p-6 max-w-screen-2xl mx-auto space-y-4" data-testid="approval-queue-page">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold" data-testid="page-title">Pipeline & Approvals</h1>
          <p className="text-sm text-muted-foreground" data-testid="queue-count">
            Complete workflow management • {counts.all} items pending review
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Segmented
            value={seg}
            onChange={setSeg}
            items={[
              { label: "All", value: "all", count: counts.all }, 
              { label: "High", value: "high", count: counts.high }, 
              { label: "Medium", value: "medium", count: counts.medium }
            ]}
          />
        </div>
      </div>

      {/* Pipeline Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-3 mb-4">
        <div className="rounded-xl border border-border p-3 text-center bg-card">
          <div className="text-xs text-muted-foreground mb-1">Transcripts</div>
          <div className="text-lg font-bold text-blue-600">{Math.floor(counts.all * 0.8)}</div>
          <div className="text-xs text-foreground">Ready</div>
        </div>
        <div className="rounded-xl border border-border p-3 text-center bg-card">
          <div className="text-xs text-muted-foreground mb-1">Analysis</div>
          <div className="text-lg font-bold text-orange-600">{Math.floor(counts.all * 0.6)}</div>
          <div className="text-xs text-foreground">Processing</div>
        </div>
        <div className="rounded-xl border border-border p-3 text-center bg-card">
          <div className="text-xs text-muted-foreground mb-1">Plans</div>
          <div className="text-lg font-bold text-amber-600">{Math.floor(counts.all * 0.4)}</div>
          <div className="text-xs text-foreground">Generated</div>
        </div>
        <div className="rounded-xl border border-border p-3 text-center bg-card">
          <div className="text-xs text-muted-foreground mb-1">Approval</div>
          <div className="text-lg font-bold text-red-600">{counts.all}</div>
          <div className="text-xs text-foreground">Pending</div>
        </div>
        <div className="rounded-xl border border-border p-3 text-center bg-card">
          <div className="text-xs text-muted-foreground mb-1">Execution</div>
          <div className="text-lg font-bold text-emerald-600">{Math.floor(counts.all * 0.15)}</div>
          <div className="text-xs text-foreground">Running</div>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative">
          <input
            className="h-9 rounded-xl border border-border px-3 pr-10 text-sm focus:outline-none focus:ring-2 focus:ring-ring bg-background"
            placeholder="Search case, customer, or call…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            data-testid="input-search"
          />
          <span className="absolute right-3 top-2.5 text-muted-foreground text-xs">⌘K</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="text-muted-foreground">Sort</span>
          <select
            className="h-9 rounded-xl border border-border px-2 text-sm bg-background"
            value={`${sort.key}:${sort.dir}`}
            onChange={(e) => {
              const [key, dir] = e.target.value.split(":");
              setSort({ key, dir });
            }}
            data-testid="select-sort"
          >
            <option value="priority:desc">Priority (high→low)</option>
            <option value="priority:asc">Priority (low→high)</option>
            <option value="time:desc">Newest first</option>
            <option value="time:asc">Oldest first</option>
          </select>
        </div>
        <label className="inline-flex items-center gap-2 text-sm cursor-pointer">
          <input 
            type="checkbox" 
            checked={dense} 
            onChange={(e) => setDense(e.target.checked)}
            data-testid="checkbox-compact"
          />
          Compact rows
        </label>
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-border overflow-hidden shadow-sm">
        <div className="bg-muted sticky top-0 z-10">
          <table className="w-full text-sm">
            <thead>
              <tr>
                <Th k="id">Case ID</Th>
                <Th k="priority">Priority</Th>
                <th className="font-semibold px-4 py-2.5 text-left text-muted-foreground">Reason</th>
                <th className="font-semibold px-4 py-2.5 text-left text-muted-foreground">Progress</th>
                <Th k="time">Time</Th>
                <th className="font-semibold px-4 py-2.5 text-left text-muted-foreground">Status</th>
                <th className="px-4 py-2.5 text-right text-muted-foreground">Actions</th>
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
