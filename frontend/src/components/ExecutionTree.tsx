import React, { useState, useEffect } from "react";
import { ChevronDown, ChevronRight, CheckCircle2, XCircle, Play, Info, RefreshCw } from "lucide-react";
import api, { executionApi } from "../api/client";
import { Execution } from "../types";

// ---- Local Type Definitions ----
interface ExecutionStep {
  step_number: number;
  action: string;
  tool_needed: string;
  details: string;
  status: "PENDING" | "IN_PROGRESS" | "EXECUTED" | "ERROR";
  result?: string;
  executed_at?: string;
}

interface WorkflowExecution {
  id: string;
  workflow_id: string;
  status: "PENDING" | "IN_PROGRESS" | "EXECUTED" | "ERROR";
  risk_level?: "LOW" | "MEDIUM" | "HIGH";
  priority?: "normal" | "medium" | "high";
  workflow_type?: "BORROWER" | "ADVISOR" | "SUPERVISOR" | "LEADERSHIP";
  created_at: string;
  execution_steps: ExecutionStep[];
  action_item?: string;
}


// ---- Badge helpers ----
const pill = (
  label: string,
  color:
    | "slate"
    | "green"
    | "emerald"
    | "amber"
    | "red"
    | "blue"
    | "violet"
    | "indigo"
) => (
  <span
    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium bg-${color}-100 text-${color}-800 border border-${color}-200`}
  >
    {label}
  </span>
);

// Tailwind's arbitrary class detection may not pick dynamic template strings well in some setups.
// To make sure colors are included, we mention the classes here (tree-shake friendly hint):
// bg-slate-100 text-slate-800 border-slate-200 bg-green-100 text-green-800 border-green-200
// bg-emerald-100 text-emerald-800 border-emerald-200 bg-amber-100 text-amber-800 border-amber-200
// bg-red-100 text-red-800 border-red-200 bg-blue-100 text-blue-800 border-blue-200
// bg-violet-100 text-violet-800 border-violet-200 bg-indigo-100 text-indigo-800 border-indigo-200

// Types are imported from executionService

// ---- Utilities ----
const StatusPill: React.FC<{ status: ExecutionStep["status"] | WorkflowExecution["status"] }> = ({ status }) => {
  switch (status) {
    case "PENDING":
      return pill("PENDING", "slate");
    case "IN_PROGRESS":
      return pill("IN PROGRESS", "blue");
    case "EXECUTED":
      return pill("EXECUTED", "emerald");
    case "ERROR":
      return pill("ERROR", "red");
  }
};

const RiskPill: React.FC<{ risk?: WorkflowExecution["risk_level"] }> = ({ risk }) => {
  if (!risk) return null;
  if (risk === "LOW") return pill("LOW", "green");
  if (risk === "MEDIUM") return pill("MEDIUM", "amber");
  return pill("HIGH", "red");
};

const PriorityPill: React.FC<{ priority?: WorkflowExecution["priority"] }> = ({ priority }) => {
  if (!priority) return null;
  if (priority === "normal") return pill("normal", "slate");
  if (priority === "medium") return pill("medium", "indigo");
  return pill("high", "violet");
};

const WorkflowTypePill: React.FC<{ type?: WorkflowExecution["workflow_type"] }> = ({ type }) => {
  if (!type) return null;
  const colorMap: Record<NonNullable<WorkflowExecution["workflow_type"]>, any> = {
    BORROWER: pill("BORROWER", "slate"),
    ADVISOR: pill("ADVISOR", "blue"),
    SUPERVISOR: pill("SUPERVISOR", "violet"),
    LEADERSHIP: pill("LEADERSHIP", "indigo"),
  };
  return <>{colorMap[type]}</>;
};

const ToolPill: React.FC<{ tool: string }> = ({ tool }) => {
  const isAPI = tool.endsWith('_api');
  return pill(tool.toUpperCase(), isAPI ? "emerald" : "blue");
};

// ---- Row components ----
const Cell: React.FC<{ className?: string; children: React.ReactNode }> = ({ className, children }) => (
  <div className={`px-3 py-2 text-sm ${className ?? ""}`}>{children}</div>
);

const HeaderCell: React.FC<{ children: React.ReactNode; className?: string }> = ({ children, className }) => (
  <div className={`px-3 py-2 text-xs uppercase tracking-wide font-semibold text-slate-500 ${className ?? ""}`}>{children}</div>
);

const Row: React.FC<{ children: React.ReactNode; depth?: number }> = ({ children, depth = 0 }) => (
  <div
    className={`grid grid-cols-[minmax(300px,1fr)_120px_110px_110px_140px_150px_200px] items-center border-b border-slate-200 hover:bg-slate-50 transition`}
    style={{ paddingLeft: depth * 16 }}
  >
    {children}
  </div>
);

// ---- Tree Row ----
const TreeCaret: React.FC<{ open: boolean; onClick: () => void }> = ({ open, onClick }) => (
  <button
    onClick={onClick}
    className="mr-2 inline-flex h-6 w-6 items-center justify-center rounded-md border border-slate-200 bg-white hover:bg-slate-100"
    aria-label={open ? "Collapse" : "Expand"}
  >
    {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
  </button>
);

const ActionButtons: React.FC<{
  level: "workflow" | "step";
  status: ExecutionStep["status"] | WorkflowExecution["status"];
  onExecute?: () => void;
  onApprove?: () => void;
  onReject?: () => void;
  onDetails?: () => void;
  isLoading?: boolean;
}> = ({ level, status, onExecute, onApprove, onReject, onDetails, isLoading }) => {
  const base = "inline-flex items-center gap-1 rounded-md border px-2 py-1 text-xs font-medium hover:shadow-sm transition";
  const ghost = "border-slate-200 text-slate-700 bg-white hover:bg-slate-50";
  const primary = "border-emerald-600 text-emerald-700 bg-emerald-50 hover:bg-emerald-100";
  const danger = "border-red-600 text-red-700 bg-red-50 hover:bg-red-100";

  return (
    <div className="flex gap-2">
      {status !== "EXECUTED" && (
        <button
          className={`${base} ${primary} ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          onClick={onExecute}
          disabled={isLoading}
        >
          {isLoading ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />} Execute
        </button>
      )}
      {level === "workflow" && status !== "EXECUTED" && (
        <button
          className={`${base} ${ghost} ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          onClick={onApprove}
          disabled={isLoading}
        >
          <CheckCircle2 size={14} /> Approve
        </button>
      )}
      {status !== "EXECUTED" && (
        <button
          className={`${base} ${danger} ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
          onClick={onReject}
          disabled={isLoading}
        >
          <XCircle size={14} /> Reject
        </button>
      )}
      <button className={`${base} ${ghost}`} onClick={onDetails}>
        <Info size={14} /> Details
      </button>
    </div>
  );
};

// ---- Main Component ----
export default function ExecutionTree() {
  const [open, setOpen] = useState<Record<string, boolean>>({});
  const [executions, setExecutions] = useState<WorkflowExecution[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState<Record<string, boolean>>({});
  const [filters, setFilters] = useState({
    status: 'All Statuses',
    risk_level: 'All Risk Levels',
    limit: 50
  });

  const toggle = (id: string) => setOpen((s) => ({ ...s, [id]: !s[id] }));

  // Load executions on component mount and when filters change
  useEffect(() => {
    loadExecutions();
  }, [filters]);

  const loadExecutions = async () => {
    try {
      setLoading(true);
      setError(null);

      // Call hierarchical API endpoint - NO FALLBACK
      const response = await api.get('/api/v1/executions/hierarchical', {
        params: {
          status: filters.status !== 'All Statuses' ? filters.status.toLowerCase() : undefined,
          limit: filters.limit
        }
      });
      const hierarchicalExecutions = response.data;

      // Validate structure - FAIL FAST if wrong format
      if (!Array.isArray(hierarchicalExecutions)) {
        throw new Error('Invalid response format: expected array');
      }

      for (const execution of hierarchicalExecutions) {
        if (!execution.execution_steps || !Array.isArray(execution.execution_steps)) {
          throw new Error(`Invalid execution format: missing execution_steps array for workflow ${execution.workflow_id}`);
        }
      }

      setExecutions(hierarchicalExecutions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load executions');
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteWorkflow = async (executionId: string) => {
    try {
      setActionLoading(prev => ({ ...prev, [executionId]: true }));

      // Find the execution and trigger a reload

      // Reload executions to get updated data
      await loadExecutions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute workflow');
    } finally {
      setActionLoading(prev => ({ ...prev, [executionId]: false }));
    }
  };

  const handleExecuteStep = async (executionId: string, stepNumber: number) => {
    try {
      const stepKey = `${executionId}-step-${stepNumber}`;
      setActionLoading(prev => ({ ...prev, [stepKey]: true }));

      // Execute step action

      // Reload executions to get updated data
      await loadExecutions();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute step');
    } finally {
      const stepKey = `${executionId}-step-${stepNumber}`;
      setActionLoading(prev => ({ ...prev, [stepKey]: false }));
    }
  };

  const handleApproveWorkflow = async (executionId: string) => {
    try {
      setActionLoading(prev => ({ ...prev, [executionId]: true }));
      // Workflow approval not implemented yet - fail fast
      throw new Error('Workflow approval not yet implemented');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to approve workflow');
    } finally {
      setActionLoading(prev => ({ ...prev, [executionId]: false }));
    }
  };

  const handleRejectWorkflow = async (executionId: string) => {
    try {
      setActionLoading(prev => ({ ...prev, [executionId]: true }));
      // Workflow rejection not implemented yet - fail fast
      throw new Error('Workflow rejection not yet implemented');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reject workflow');
    } finally {
      setActionLoading(prev => ({ ...prev, [executionId]: false }));
    }
  };

  const Header = (
    <div className="grid grid-cols-[minmax(300px,1fr)_120px_110px_110px_140px_150px_200px] border-b border-slate-300 bg-slate-50">
      <HeaderCell className="">Execution Tree</HeaderCell>
      <HeaderCell>Status</HeaderCell>
      <HeaderCell>Risk</HeaderCell>
      <HeaderCell>Priority</HeaderCell>
      <HeaderCell>Type/Tool</HeaderCell>
      <HeaderCell>Created</HeaderCell>
      <HeaderCell>Actions</HeaderCell>
    </div>
  );

  const renderExecutionStep = (step: ExecutionStep, depth: number, executionId: string) => (
    <Row key={step.step_number} depth={depth}>
      <Cell>
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Step {step.step_number}</span>
            <span className="text-slate-700 font-medium">{step.action}</span>
          </div>
          <div className="text-xs text-slate-500 truncate max-w-sm">{step.details}</div>
          {step.result && (
            <div className="text-xs text-emerald-600 bg-emerald-50 px-2 py-1 rounded mt-1">
              {step.result}
            </div>
          )}
        </div>
      </Cell>
      <Cell>
        <StatusPill status={step.status} />
      </Cell>
      <Cell>
        {/* Risk inherited from parent workflow */}
      </Cell>
      <Cell>
        {/* Priority inherited from parent workflow */}
      </Cell>
      <Cell>
        <ToolPill tool={step.tool_needed} />
      </Cell>
      <Cell className="text-slate-500">
        {step.executed_at ? new Date(step.executed_at).toLocaleString() : '-'}
      </Cell>
      <Cell>
        <ActionButtons
          level="step"
          status={step.status}
          onExecute={() => handleExecuteStep(executionId, step.step_number)}
          isLoading={actionLoading[`${executionId}-step-${step.step_number}`]}
        />
      </Cell>
    </Row>
  );

  const renderWorkflowExecution = (execution: WorkflowExecution, depth: number) => (
    <React.Fragment key={execution.id}>
      <Row depth={depth}>
        <Cell>
          <div className="flex items-center">
            <TreeCaret open={!!open[execution.id]} onClick={() => toggle(execution.id)} />
            <div className="flex flex-col gap-1">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900">{execution.workflow_id.slice(3, 11)}…</span>
                <WorkflowTypePill type={execution.workflow_type} />
              </div>
              <div className="text-xs text-slate-600">{execution.action_item}</div>
              <span className="text-xs text-slate-500">({execution.execution_steps?.length || 0} steps)</span>
            </div>
          </div>
        </Cell>
        <Cell>
          <StatusPill status={execution.status} />
        </Cell>
        <Cell>
          <RiskPill risk={execution.risk_level} />
        </Cell>
        <Cell>
          <PriorityPill priority={execution.priority} />
        </Cell>
        <Cell>
          <span className="text-xs text-slate-500">Workflow</span>
        </Cell>
        <Cell className="text-slate-500">
          {new Date(execution.created_at).toLocaleString()}
        </Cell>
        <Cell>
          <ActionButtons
            level="workflow"
            status={execution.status}
            onExecute={() => handleExecuteWorkflow(execution.id)}
            onApprove={() => handleApproveWorkflow(execution.id)}
            onReject={() => handleRejectWorkflow(execution.id)}
            isLoading={actionLoading[execution.id]}
          />
        </Cell>
      </Row>
      {open[execution.id] && execution.execution_steps?.map((step) => renderExecutionStep(step, depth + 1, execution.id))}
    </React.Fragment>
  );

  return (
    <div className="w-full min-h-screen bg-white p-6">
      <div className="mb-4 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Execution</h1>
          <p className="text-sm text-slate-500">Hierarchical view of Workflows → Execution Steps</p>
        </div>
        <div className="flex items-center gap-2">
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={filters.status}
            onChange={(e) => setFilters(prev => ({ ...prev, status: e.target.value }))}
          >
            <option>All Statuses</option>
            <option>Pending</option>
            <option>In Progress</option>
            <option>Executed</option>
            <option>Error</option>
          </select>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={filters.risk_level}
            onChange={(e) => setFilters(prev => ({ ...prev, risk_level: e.target.value }))}
          >
            <option>All Risk Levels</option>
            <option>Low</option>
            <option>Medium</option>
            <option>High</option>
          </select>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={filters.limit}
            onChange={(e) => setFilters(prev => ({ ...prev, limit: parseInt(e.target.value) }))}
          >
            <option value={25}>25</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
          <button
            onClick={loadExecutions}
            className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm hover:bg-slate-50"
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="mb-4 rounded-md bg-red-50 border border-red-200 p-4">
          <div className="text-sm text-red-800">
            <strong>Error:</strong> {error}
          </div>
        </div>
      )}

      <div className="rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {Header}
        <div className="divide-y divide-slate-200">
          {loading ? (
            <div className="p-8 text-center">
              <RefreshCw className="mx-auto h-8 w-8 animate-spin text-slate-400" />
              <p className="mt-2 text-sm text-slate-600">Loading executions...</p>
            </div>
          ) : executions.length === 0 ? (
            <div className="p-8 text-center">
              <p className="text-sm text-slate-600">No executions found</p>
            </div>
          ) : (
            executions.map((execution) => renderWorkflowExecution(execution, 0))
          )}
        </div>
      </div>

      <div className="mt-6 text-xs text-slate-500">
        <p>
          Showing {executions.length} workflow executions.
          {executions.length === 0 && !loading && ' Try adjusting your filters or check if the backend service is running.'}
        </p>
      </div>
    </div>
  );
}