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
    if (sortColumn !== column) return ' ↕';
    return sortDirection === 'asc' ? ' ↗' : ' ↘';
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

  // Helper functions for chips
  const getPriorityChip = (priority: number) => {
    if (priority >= 80) return "px-2 py-0.5 text-xs font-medium rounded-full bg-red-100 text-red-700 border border-red-200";
    if (priority >= 50) return "px-2 py-0.5 text-xs font-medium rounded-full bg-orange-100 text-orange-700 border border-orange-200";
    return "px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700 border border-green-200";
  };

  const getStatusChip = (status: string) => {
    if (status === "completed") return "px-2 py-0.5 text-xs font-medium rounded-full bg-emerald-100 text-emerald-700 border border-emerald-200";
    if (status === "in_progress") return "px-2 py-0.5 text-xs font-medium rounded-full bg-blue-100 text-blue-700 border border-blue-200";
    return "px-2 py-0.5 text-xs font-medium rounded-full bg-gray-100 text-gray-700 border border-gray-200";
  };

  const getPriorityText = (priority: number) => {
    if (priority >= 80) return "High";
    if (priority >= 50) return "Medium";
    return "Low";
  };

  return (
    <div className="p-4 max-w-screen-2xl mx-auto space-y-4">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-medium text-gray-900">Call Transcripts</h1>
          <p className="text-sm text-gray-500">
            All customer service call recordings and transcripts
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 shadow-sm hover:shadow-md transition-shadow">
          <div className="text-lg font-semibold text-gray-900">{filteredAndSortedCases?.length || 0}</div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Total Transcripts</div>
        </div>
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 shadow-sm hover:shadow-md transition-shadow">
          <div className="text-lg font-semibold text-emerald-600">
            {filteredAndSortedCases?.filter(c => c.status === "completed").length || 0}
          </div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Analyzed</div>
        </div>
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 shadow-sm hover:shadow-md transition-shadow">
          <div className="text-lg font-semibold text-amber-600">
            {filteredAndSortedCases?.filter(c => c.status === "in_progress").length || 0}
          </div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">Processing</div>
        </div>
        <div className="rounded-lg bg-gray-50 border border-gray-200 p-3 shadow-sm hover:shadow-md transition-shadow">
          <div className="text-lg font-semibold text-red-600">
            {filteredAndSortedCases?.filter(c => c.priority >= 80).length || 0}
          </div>
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">High Priority</div>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
        <input
          type="text"
          placeholder="Search Call ID, Customer, or Type..."
          value={filters.search}
          onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
          className="flex-1 px-2 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <select
          value={filters.priority}
          onChange={(e) => setFilters(prev => ({ ...prev, priority: e.target.value }))}
          className="px-2 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Priorities</option>
          <option value="high">High Priority</option>
          <option value="medium">Medium Priority</option>
          <option value="low">Low Priority</option>
        </select>
        <select
          value={filters.status}
          onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
          className="px-2 py-1.5 text-sm border border-gray-300 rounded-md bg-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        >
          <option value="">All Statuses</option>
          <option value="Needs Review">Needs Review</option>
          <option value="completed">Completed</option>
          <option value="in_progress">In Progress</option>
        </select>
        <button
          onClick={() => setFilters({ search: '', priority: '', status: '' })}
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md bg-white hover:bg-gray-50 transition-colors"
        >
          Clear
        </button>
      </div>

      {/* Transcript List */}
      <div className="rounded-lg border border-gray-300 overflow-hidden bg-white shadow-sm">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-200">
              <th 
                className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('id')}
              >
                Call ID{getSortIndicator('id')}
              </th>
              <th 
                className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('priority')}
              >
                Priority{getSortIndicator('priority')}
              </th>
              <th 
                className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('status')}
              >
                Status{getSortIndicator('status')}
              </th>
              <th 
                className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('customerId')}
              >
                Customer{getSortIndicator('customerId')}
              </th>
              <th 
                className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('scenario')}
              >
                Type{getSortIndicator('scenario')}
              </th>
              <th 
                className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('createdAt')}
              >
                Created{getSortIndicator('createdAt')}
              </th>
              <th 
                className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('updatedAt')}
              >
                Updated{getSortIndicator('updatedAt')}
              </th>
              <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider bg-gray-50">Action</th>
            </tr>
          </thead>
          <tbody>
            {filteredAndSortedCases?.map((caseItem, index) => (
              <tr key={caseItem.id} className={`border-b border-gray-200 hover:bg-gray-50 transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-gray-50/50'}`}>
                <td className="px-4 py-2 text-sm">
                  <span className="font-medium text-gray-900">{caseItem.id}</span>
                </td>
                <td className="px-4 py-2 text-sm">
                  <span className={getPriorityChip(caseItem.priority)}>
                    {getPriorityText(caseItem.priority)}
                  </span>
                </td>
                <td className="px-4 py-2 text-sm">
                  <span className={getStatusChip(caseItem.status)}>
                    {caseItem.status}
                  </span>
                </td>
                <td className="px-4 py-2 text-sm text-gray-600">{caseItem.customerId}</td>
                <td className="px-4 py-2 text-sm text-gray-600">{caseItem.scenario}</td>
                <td className="px-4 py-2 text-xs text-gray-500">
                  {caseItem.createdAt ? new Date(caseItem.createdAt).toLocaleDateString() : "N/A"}
                </td>
                <td className="px-4 py-2 text-xs text-gray-500">
                  {caseItem.updatedAt ? new Date(caseItem.updatedAt).toLocaleDateString() : "N/A"}
                </td>
                <td className="px-4 py-2 text-sm">
                  <Link href={`/case/${caseItem.id}`}>
                    <span className="text-blue-600 hover:text-blue-800 font-medium">
                      View Details →
                    </span>
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