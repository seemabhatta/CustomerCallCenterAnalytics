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

    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch executions: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Error fetching executions:', error);
      // Return mock data for development
      return this.getMockExecutions(filters);
    }
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
      return null;
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

  /**
   * Mock data for development when backend is unavailable
   */
  private getMockExecutions(filters: ExecutionFilters): WorkflowExecution[] {
    const mockData: WorkflowExecution[] = [
      {
        id: "exec_bb4ac73-527d-45e0-8a8f-39bb6bc10058",
        workflow_id: "wf_bb4ac73-527d-45e0-8a8f-39bb6bc10058",
        status: "IN_PROGRESS",
        risk_level: "MEDIUM",
        priority: "high",
        workflow_type: "BORROWER",
        action_item: "Remove PMI from loan account",
        created_at: "2025-09-15T10:30:00Z",
        execution_steps: [
          {
            step_number: 1,
            action: "Check current loan-to-value ratio",
            tool_needed: "servicing_api",
            details: "GET /api/v1/loans/{loan_id}/ltv - Retrieve current LTV from mortgage servicing system",
            status: "EXECUTED",
            result: "Current LTV: 78% - Eligible for PMI removal",
            executed_at: "2025-09-15T10:31:00Z"
          },
          {
            step_number: 2,
            action: "Get current property valuation",
            tool_needed: "pricing_api",
            details: "GET /api/v1/properties/{property_id}/value - Get automated valuation model estimate",
            status: "IN_PROGRESS"
          },
          {
            step_number: 3,
            action: "Verify PMI removal requirements",
            tool_needed: "compliance_api",
            details: "POST /api/v1/compliance/pmi-removal-check - Check regulatory requirements for PMI removal",
            status: "PENDING"
          },
          {
            step_number: 4,
            action: "Generate PMI removal letter",
            tool_needed: "document_api",
            details: "POST /api/v1/documents/generate - Create official PMI removal notification letter",
            status: "PENDING"
          },
          {
            step_number: 5,
            action: "Send confirmation email to borrower",
            tool_needed: "email",
            details: "Send email to borrower confirming PMI removal and updated payment schedule",
            status: "PENDING"
          }
        ]
      },
      {
        id: "exec_100e7f4d-551c-41a6-9567-86d79db261d1",
        workflow_id: "wf_100e7f4d-551c-41a6-9567-86d79db261d1",
        status: "EXECUTED",
        risk_level: "LOW",
        priority: "normal",
        workflow_type: "ADVISOR",
        action_item: "Process satisfaction survey follow-up",
        created_at: "2025-09-15T09:00:00Z",
        execution_steps: [
          {
            step_number: 1,
            action: "Send satisfaction survey to customer",
            tool_needed: "email",
            details: "Send post-service satisfaction survey with 5-minute completion time",
            status: "EXECUTED",
            result: "Survey sent successfully - Response rate tracking initiated",
            executed_at: "2025-09-15T09:01:00Z"
          }
        ]
      }
    ];

    // Apply basic filtering to mock data
    let filtered = mockData;

    if (filters.status && filters.status !== 'All Statuses') {
      const statusFilter = filters.status.toUpperCase().replace(' ', '_');
      filtered = filtered.filter(exec => exec.status === statusFilter);
    }

    if (filters.risk_level && filters.risk_level !== 'All Risk Levels') {
      const riskFilter = filters.risk_level.toUpperCase();
      filtered = filtered.filter(exec => exec.risk_level === riskFilter);
    }

    if (filters.workflow_type) {
      filtered = filtered.filter(exec => exec.workflow_type === filters.workflow_type);
    }

    if (filters.limit) {
      filtered = filtered.slice(0, filters.limit);
    }

    return filtered;
  }
}

export const executionService = new ExecutionService();