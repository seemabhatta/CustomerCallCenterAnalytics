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

      {/* Transcripts Table */}
      <div className="border rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-muted/50">
            <tr className="border-b">
              <th className="text-left p-4 font-medium">Call ID</th>
              <th className="text-left p-4 font-medium">Priority</th>
              <th className="text-left p-4 font-medium">Status</th>
              <th className="text-left p-4 font-medium">Customer</th>
              <th className="text-left p-4 font-medium">Type</th>
              <th className="text-left p-4 font-medium">Created</th>
              <th className="text-left p-4 font-medium">Updated</th>
              <th className="text-left p-4 font-medium">Action</th>
            </tr>
          </thead>
          <tbody>
            {cases?.map((caseItem) => (
              <tr key={caseItem.id} className="border-b hover:bg-muted/30">
                <td className="p-4 font-mono text-sm">{caseItem.id}</td>
                <td className="p-4">
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    caseItem.priority >= 80 ? "bg-red-100 text-red-800" :
                    caseItem.priority >= 50 ? "bg-yellow-100 text-yellow-800" :
                    "bg-green-100 text-green-800"
                  }`}>
                    {caseItem.priority >= 80 ? "High Priority" :
                     caseItem.priority >= 50 ? "Medium Priority" : "Low Priority"}
                  </span>
                </td>
                <td className="p-4">
                  <span className="text-sm">{caseItem.status}</span>
                </td>
                <td className="p-4 text-sm">{caseItem.customerId}</td>
                <td className="p-4 text-sm">{caseItem.scenario}</td>
                <td className="p-4 text-sm">
                  {caseItem.createdAt ? new Date(caseItem.createdAt).toLocaleDateString() : "N/A"}
                </td>
                <td className="p-4 text-sm">
                  {caseItem.updatedAt ? new Date(caseItem.updatedAt).toLocaleDateString() : "N/A"}
                </td>
                <td className="p-4">
                  <Link href={`/case/${caseItem.id}`}>
                    <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                      View Details →
                    </button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Show message if no transcripts */}
      {!isLoading && (!cases || cases.length === 0) && (
        <div className="text-center py-12 text-muted-foreground">
          No transcripts found
        </div>
      )}
    </div>
  );
}