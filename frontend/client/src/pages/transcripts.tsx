import { useQuery } from "@tanstack/react-query";
import { Link } from "wouter";
import { useState, useMemo } from "react";
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

  // Sorting and filtering state
  const [sortColumn, setSortColumn] = useState<keyof Case | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filters, setFilters] = useState({
    search: '',
    priority: '',
    status: '',
  });

  // Handle column sorting
  const handleSort = (column: keyof Case) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // Filter and sort cases
  const filteredAndSortedCases = useMemo(() => {
    if (!cases) return [];

    // Apply filters
    let filtered = cases.filter(caseItem => {
      const matchesSearch = !filters.search || 
        caseItem.id.toLowerCase().includes(filters.search.toLowerCase()) ||
        caseItem.customerId.toLowerCase().includes(filters.search.toLowerCase()) ||
        caseItem.scenario.toLowerCase().includes(filters.search.toLowerCase());
      
      const matchesPriority = !filters.priority || 
        (filters.priority === 'high' && caseItem.priority >= 80) ||
        (filters.priority === 'medium' && caseItem.priority >= 50 && caseItem.priority < 80) ||
        (filters.priority === 'low' && caseItem.priority < 50);
      
      const matchesStatus = !filters.status || caseItem.status === filters.status;

      return matchesSearch && matchesPriority && matchesStatus;
    });

    // Apply sorting
    if (sortColumn) {
      filtered.sort((a, b) => {
        let aValue = a[sortColumn];
        let bValue = b[sortColumn];

        // Handle date fields
        if (sortColumn === 'createdAt' || sortColumn === 'updatedAt') {
          aValue = new Date(aValue as string);
          bValue = new Date(bValue as string);
        }

        // Handle string comparison
        if (typeof aValue === 'string' && typeof bValue === 'string') {
          aValue = aValue.toLowerCase();
          bValue = bValue.toLowerCase();
        }

        if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
        if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
        return 0;
      });
    }

    return filtered;
  }, [cases, filters, sortColumn, sortDirection]);

  // Get sort indicator
  const getSortIndicator = (column: keyof Case) => {
    if (sortColumn !== column) return ' ↕️';
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  };

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
          <div className="text-2xl font-bold text-primary">{filteredAndSortedCases?.length || 0}</div>
          <div className="text-sm text-muted-foreground">Total Transcripts</div>
        </div>
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
          <div className="text-2xl font-bold text-emerald-600">
            {filteredAndSortedCases?.filter(c => c.status === "completed").length || 0}
          </div>
          <div className="text-sm text-muted-foreground">Analyzed</div>
        </div>
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
          <div className="text-2xl font-bold text-amber-600">
            {filteredAndSortedCases?.filter(c => c.status === "in_progress").length || 0}
          </div>
          <div className="text-sm text-muted-foreground">Processing</div>
        </div>
        <div className="rounded-2xl border border-border p-4 text-center shadow-sm bg-card">
          <div className="text-2xl font-bold text-blue-600">
            {filteredAndSortedCases?.filter(c => c.priority >= 80).length || 0}
          </div>
          <div className="text-sm text-muted-foreground">High Priority</div>
        </div>
      </div>

      {/* Filters */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div>
          <input
            type="text"
            placeholder="Search Call ID, Customer, or Type..."
            value={filters.search}
            onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
            className="w-full px-3 py-2 rounded-lg border border-border bg-card text-sm"
          />
        </div>
        <div>
          <select
            value={filters.priority}
            onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
            className="w-full px-3 py-2 rounded-lg border border-border bg-card text-sm"
          >
            <option value="">All Priorities</option>
            <option value="high">High Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="low">Low Priority</option>
          </select>
        </div>
        <div>
          <select
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="w-full px-3 py-2 rounded-lg border border-border bg-card text-sm"
          >
            <option value="">All Statuses</option>
            <option value="Needs Review">Needs Review</option>
            <option value="completed">Completed</option>
            <option value="in_progress">In Progress</option>
          </select>
        </div>
        <div>
          <button
            onClick={() => setFilters({ search: '', priority: '', status: '' })}
            className="px-4 py-2 rounded-lg border border-border bg-card text-sm hover:bg-muted/30 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      </div>

      {/* Transcript List */}
      <div className="rounded-2xl border border-border shadow-sm bg-card overflow-hidden">
        <table className="w-full">
          <thead className="bg-card">
            <tr className="border-b border-border">
              <th 
                className="text-left p-6 font-semibold text-lg cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => handleSort('id')}
              >
                Call ID{getSortIndicator('id')}
              </th>
              <th 
                className="text-left p-6 font-semibold text-lg cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => handleSort('priority')}
              >
                Priority{getSortIndicator('priority')}
              </th>
              <th 
                className="text-left p-6 font-semibold text-lg cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => handleSort('status')}
              >
                Status{getSortIndicator('status')}
              </th>
              <th 
                className="text-left p-6 font-semibold text-lg cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => handleSort('customerId')}
              >
                Customer{getSortIndicator('customerId')}
              </th>
              <th 
                className="text-left p-6 font-semibold text-lg cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => handleSort('scenario')}
              >
                Type{getSortIndicator('scenario')}
              </th>
              <th 
                className="text-left p-6 font-semibold text-lg cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => handleSort('createdAt')}
              >
                Created{getSortIndicator('createdAt')}
              </th>
              <th 
                className="text-left p-6 font-semibold text-lg cursor-pointer hover:bg-muted/30 transition-colors"
                onClick={() => handleSort('updatedAt')}
              >
                Updated{getSortIndicator('updatedAt')}
              </th>
              <th className="text-left p-6 font-semibold text-lg">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedCases?.map((caseItem) => (
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