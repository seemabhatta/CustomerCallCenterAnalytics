import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import type { Case } from "@shared/schema";

export default function TranscriptsPage() {
  const { data: cases, isLoading } = useQuery<Case[]>({
    queryKey: ["/api/cases"],
    queryFn: async () => {
      const response = await fetch("/api/cases");
      if (!response.ok) {
        throw new Error("Failed to fetch transcripts");
      }
      return response.json();
    },
  });

  if (isLoading) {
    return (
      <div className="p-6 max-w-screen-2xl mx-auto">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-gray-200 rounded w-1/3"></div>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-screen-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Call Transcripts</h1>
          <p className="text-sm text-muted-foreground">
            All customer service call recordings and transcripts
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
          <div className="text-2xl font-bold text-primary">{cases?.length || 0}</div>
          <div className="text-sm text-muted-foreground">Total Transcripts</div>
        </div>
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
          <div className="text-2xl font-bold text-emerald-600">
            {cases?.filter(c => c.status === "completed").length || 0}
          </div>
          <div className="text-sm text-muted-foreground">Analyzed</div>
        </div>
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
          <div className="text-2xl font-bold text-amber-600">
            {cases?.filter(c => c.status === "in_progress").length || 0}
          </div>
          <div className="text-sm text-muted-foreground">Processing</div>
        </div>
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
          <div className="text-2xl font-bold text-blue-600">
            {cases?.filter(c => c.priority === 3).length || 0}
          </div>
          <div className="text-sm text-muted-foreground">High Priority</div>
        </div>
      </div>

      {/* Transcript List */}
      <div className="rounded-2xl border border-border shadow-sm bg-card overflow-hidden">
        <table className="w-full">
          <thead className="bg-card">
            <tr className="border-b border-border">
              <th className="text-left p-6 font-semibold text-lg">Call ID</th>
              <th className="text-left p-6 font-semibold text-lg">Priority</th>
              <th className="text-left p-6 font-semibold text-lg">Status</th>
              <th className="text-left p-6 font-semibold text-lg">Customer</th>
              <th className="text-left p-6 font-semibold text-lg">Type</th>
              <th className="text-left p-6 font-semibold text-lg">Created</th>
              <th className="text-left p-6 font-semibold text-lg">Updated</th>
              <th className="text-left p-6 font-semibold text-lg">Action</th>
            </tr>
          </thead>
          <tbody>
            {cases?.map((caseItem) => (
              <tr key={caseItem.id} className="border-b border-border hover:shadow-md transition-shadow cursor-pointer">
                <td className="p-6">
                  <span className="font-semibold text-lg">{caseItem.id}</span>
                </td>
                <td className="p-6">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    caseItem.priority === 3 ? "bg-red-100 text-red-800" :
                    caseItem.priority === 2 ? "bg-yellow-100 text-yellow-800" :
                    "bg-green-100 text-green-800"
                  }`}>
                    {caseItem.priority === 3 ? "high" : caseItem.priority === 2 ? "medium" : "low"} priority
                  </span>
                </td>
                <td className="p-6">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    caseItem.status === "completed" ? "bg-emerald-100 text-emerald-800" :
                    caseItem.status === "in_progress" ? "bg-blue-100 text-blue-800" :
                    "bg-gray-100 text-gray-800"
                  }`}>
                    {caseItem.status}
                  </span>
                </td>
                <td className="p-6 text-sm text-muted-foreground">{caseItem.customerId}</td>
                <td className="p-6 text-sm text-muted-foreground">{caseItem.scenario}</td>
                <td className="p-6 text-xs text-muted-foreground">
                  {caseItem.createdAt ? new Date(caseItem.createdAt).toLocaleDateString() : "N/A"}
                </td>
                <td className="p-6 text-xs text-muted-foreground">
                  {caseItem.updatedAt ? new Date(caseItem.updatedAt).toLocaleDateString() : "N/A"}
                </td>
                <td className="p-6">
                  <Link href={`/case/${caseItem.id}`}>
                    <div className="text-sm font-medium text-primary">
                      View Details →
                    </div>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}