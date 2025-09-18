/**
 * Execution Service - API calls for workflow execution data
 */

const API_BASE = 'http://localhost:8000/api/v1';

export interface ExecutionStep {
  step_number: number;
  action: string;
  tool_needed: string;
  details: string;
  status: "PENDING" | "IN_PROGRESS" | "EXECUTED" | "ERROR";
  result?: string;
  executed_at?: string;
}

export interface WorkflowExecution {
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

export interface ExecutionFilters {
  status?: string;
  risk_level?: string;
  workflow_type?: string;
  limit?: number;
}

class ExecutionService {
  /**
   * Get all workflow executions with optional filtering
   */
  async getExecutions(filters: ExecutionFilters = {}): Promise<WorkflowExecution[]> {
    const params = new URLSearchParams();

    if (filters.status && filters.status !== 'All Statuses') {
      params.append('status', filters.status.toUpperCase().replace(' ', '_'));
    }
    if (filters.risk_level && filters.risk_level !== 'All Risk Levels') {
      params.append('risk_level', filters.risk_level.toUpperCase());
    }
    if (filters.workflow_type) {
      params.append('workflow_type', filters.workflow_type);
    }
    if (filters.limit) {
      params.append('limit', filters.limit.toString());
    }

    const url = `${API_BASE}/executions${params.toString() ? '?' + params.toString() : ''}`;

    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch executions: ${response.statusText}`);
    }
    return await response.json();
  }

  /**
   * Get specific workflow execution by ID
   */
  async getExecution(executionId: string): Promise<WorkflowExecution | null> {
    try {
      const response = await fetch(`${API_BASE}/executions/${executionId}`);
      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error(`Failed to fetch execution: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching execution:', error);
      throw error;
    }
  }

  /**
   * Execute a specific step in a workflow
   */
  async executeStep(executionId: string, stepNumber: number): Promise<ExecutionStep> {
    try {
      const response = await fetch(`${API_BASE}/executions/${executionId}/steps/${stepNumber}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to execute step: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing step:', error);
      throw error;
    }
  }

  /**
   * Execute entire workflow
   */
  async executeWorkflow(executionId: string): Promise<WorkflowExecution> {
    try {
      const response = await fetch(`${API_BASE}/executions/${executionId}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to execute workflow: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error executing workflow:', error);
      throw error;
    }
  }

  /**
   * Approve a workflow for execution
   */
  async approveWorkflow(executionId: string): Promise<WorkflowExecution> {
    try {
      const response = await fetch(`${API_BASE}/executions/${executionId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to approve workflow: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error approving workflow:', error);
      throw error;
    }
  }

  /**
   * Reject a workflow
   */
  async rejectWorkflow(executionId: string, reason?: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE}/executions/${executionId}/reject`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ reason }),
      });

      if (!response.ok) {
        throw new Error(`Failed to reject workflow: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Error rejecting workflow:', error);
      throw error;
    }
  }

}

export const executionService = new ExecutionService();