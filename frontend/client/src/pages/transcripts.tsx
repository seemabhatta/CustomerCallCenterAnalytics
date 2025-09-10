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
      <div className="space-y-4">
        {cases?.map((caseItem) => (
          <Link key={caseItem.id} href={`/case/${caseItem.id}`}>
            <div className="rounded-2xl border border-border p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer bg-card">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-semibold text-lg">{caseItem.id}</span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      caseItem.priority === 3 ? "bg-red-100 text-red-800" :
                      caseItem.priority === 2 ? "bg-yellow-100 text-yellow-800" :
                      "bg-green-100 text-green-800"
                    }`}>
                      {caseItem.priority === 3 ? "high" : caseItem.priority === 2 ? "medium" : "low"} priority
                    </span>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      caseItem.status === "completed" ? "bg-emerald-100 text-emerald-800" :
                      caseItem.status === "in_progress" ? "bg-blue-100 text-blue-800" :
                      "bg-gray-100 text-gray-800"
                    }`}>
                      {caseItem.status}
                    </span>
                  </div>
                  
                  <p className="text-sm text-muted-foreground mb-2">
                    Customer: {caseItem.customerId} • {caseItem.scenario}
                  </p>
                  
                  <div className="text-xs text-muted-foreground">
                    Created: {caseItem.createdAt ? new Date(caseItem.createdAt).toLocaleDateString() : "N/A"} • 
                    Updated: {caseItem.updatedAt ? new Date(caseItem.updatedAt).toLocaleDateString() : "N/A"}
                  </div>
                </div>
                
                <div className="text-right">
                  <div className="text-sm font-medium text-primary">
                    View Details →
                  </div>
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </div>
  );
}