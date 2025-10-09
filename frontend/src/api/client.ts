import axios, { AxiosResponse } from 'axios';
import {
  Transcript,
  Analysis,
  Plan,
  Workflow,
  Execution,
  ExecutionDetails,
  TranscriptCreateRequest,
  AnalysisCreateRequest,
  PlanCreateRequest,
  WorkflowApprovalRequest,
  WorkflowRejectionRequest,
  WorkflowExecutionRequest,
  DashboardMetrics,
  RiskPattern,
  CustomerRecommendation,
  InsightsData,
  SearchParams,
  ListParams,
  FilterParams,
  ApiError,
  OrchestrationRun,
  OrchestrationRunRequest,
  OrchestrationRunResponse,
  LeadershipChatRequest,
  LeadershipChatResponse,
  AdvisorChatRequest,
  AdvisorChatResponse,
  ForecastGenerateRequest,
  ForecastResult,
  ForecastTypeSummary,
  ForecastTypeInfo,
  ForecastReadinessResponse,
  ForecastDataSummary,
  ForecastStatistics,
  ForecastHistoryItem
} from '@/types';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Generic API helper
const apiCall = async <T>(request: () => Promise<AxiosResponse<T>>): Promise<T> => {
  try {
    const response = await request();
    return response.data;
  } catch (error: any) {
    if (error.response?.data) {
      throw error.response.data as ApiError;
    }
    throw { detail: error.message } as ApiError;
  }
};

// Transcript API
export const transcriptApi = {
  list: (params?: ListParams) =>
    apiCall<Transcript[]>(async () => {
      const response = await api.get('/api/v1/transcripts', { params });
      // Handle new API response format with metadata
      if (response.data && typeof response.data === 'object' && 'transcripts' in response.data) {
        // Create a mock AxiosResponse for the transcripts array
        return {
          ...response,
          data: response.data.transcripts
        };
      }
      // Fallback for old format (plain array)
      return response;
    }),

  create: (data: TranscriptCreateRequest) => 
    apiCall<Transcript>(() => 
      api.post('/api/v1/transcripts', data)
    ),

  getById: (id: string) => 
    apiCall<Transcript>(() => 
      api.get(`/api/v1/transcripts/${id}`)
    ),

  delete: (id: string) => 
    apiCall<{ message: string }>(() => 
      api.delete(`/api/v1/transcripts/${id}`)
    ),

  search: (params: SearchParams) => 
    apiCall<Transcript[]>(() => 
      api.get('/api/v1/transcripts/search', { params })
    ),

  getMetrics: () => 
    apiCall<any>(() => 
      api.get('/api/v1/transcripts/metrics')
    ),

  createBulk: (requests: TranscriptCreateRequest[]) => 
    apiCall<{ transcripts: Transcript[]; count: number }>(() => 
      api.post('/api/v1/transcripts/bulk', requests)
    ),

  getMessages: (id: string) => 
    apiCall<any[]>(() => 
      api.get(`/api/v1/transcripts/${id}/messages`)
    ),

  getLiveSegments: (id: string) => 
    apiCall<any>(() => 
      api.get(`/api/v1/transcripts/${id}`)
    ),
};

// Analysis API
export const analysisApi = {
  list: (params?: ListParams) => 
    apiCall<Analysis[]>(() => 
      api.get('/api/v1/analyses', { params })
    ),

  create: (data: AnalysisCreateRequest) => 
    apiCall<Analysis>(() => 
      api.post('/api/v1/analyses', data)
    ),

  getById: (id: string) => 
    apiCall<Analysis>(() => 
      api.get(`/api/v1/analyses/${id}`)
    ),

  delete: (id: string) => 
    apiCall<{ message: string }>(() => 
      api.delete(`/api/v1/analyses/${id}`)
    ),

  deleteAll: () => 
    apiCall<{ message: string; count: number }>(() => 
      api.delete('/api/v1/analyses')
    ),

  searchByTranscript: (transcriptId: string) => 
    apiCall<Analysis[]>(() => 
      api.get(`/api/v1/analyses/search/transcript/${transcriptId}`)
    ),
};

// Plan API
export const planApi = {
  list: (params?: ListParams) => 
    apiCall<Plan[]>(() => 
      api.get('/api/v1/plans', { params })
    ),

  create: (data: PlanCreateRequest) => 
    apiCall<Plan>(() => 
      api.post('/api/v1/plans', data)
    ),

  getById: (id: string) => 
    apiCall<Plan>(() => 
      api.get(`/api/v1/plans/${id}`)
    ),

  update: (id: string, updates: Record<string, any>) => 
    apiCall<Plan>(() => 
      api.put(`/api/v1/plans/${id}`, { updates })
    ),

  delete: (id: string) => 
    apiCall<{ message: string }>(() => 
      api.delete(`/api/v1/plans/${id}`)
    ),

  deleteAll: () => 
    apiCall<{ message: string; count: number }>(() => 
      api.delete('/api/v1/plans')
    ),

  searchByAnalysis: (analysisId: string) => 
    apiCall<Plan[]>(() => 
      api.get(`/api/v1/plans/search/analysis/${analysisId}`)
    ),

  approve: (id: string, data: { approved_by: string; approved_at?: string; notes?: string }) => 
    apiCall<Plan>(() => 
      api.post(`/api/v1/plans/${id}/approve`, data)
    ),

  execute: (id: string, data: { executed_by: string }) => 
    apiCall<Plan>(() => 
      api.post(`/api/v1/plans/${id}/execute`, data)
    ),
};

// Workflow API
export const workflowApi = {
  extractFromPlan: (planId: string) => 
    apiCall<any>(() => 
      api.post('/api/v1/workflows/extract', { plan_id: planId })
    ),

  list: (params?: FilterParams & ListParams) => 
    apiCall<Workflow[]>(() => 
      api.get('/api/v1/workflows', { params })
    ),

  getPending: () => 
    apiCall<Workflow[]>(() => 
      api.get('/api/v1/workflows/pending')
    ),

  extractAllFromPlan: (planId: string) => 
    apiCall<any>(() => 
      api.post('/api/v1/workflows/extract-all', { plan_id: planId })
    ),

  getByPlan: (planId: string) => 
    apiCall<Workflow[]>(() => 
      api.get(`/api/v1/workflows/plan/${planId}`)
    ),

  getByType: (workflowType: string) => 
    apiCall<Workflow[]>(() => 
      api.get(`/api/v1/workflows/type/${workflowType}`)
    ),

  getByPlanAndType: (planId: string, workflowType: string) => 
    apiCall<Workflow[]>(() => 
      api.get(`/api/v1/workflows/plan/${planId}/type/${workflowType}`)
    ),

  getById: (id: string) => 
    apiCall<Workflow>(() => 
      api.get(`/api/v1/workflows/${id}`)
    ),

  approve: (id: string, data: WorkflowApprovalRequest) => 
    apiCall<Workflow>(() => 
      api.post(`/api/v1/workflows/${id}/approve`, data)
    ),

  reject: (id: string, data: WorkflowRejectionRequest) => 
    apiCall<Workflow>(() => 
      api.post(`/api/v1/workflows/${id}/reject`, data)
    ),

  execute: (id: string, data: WorkflowExecutionRequest) => 
    apiCall<any>(() => 
      api.post(`/api/v1/workflows/${id}/execute`, data)
    ),

  getHistory: (id: string) => 
    apiCall<any>(() => 
      api.get(`/api/v1/workflows/${id}/history`)
    ),

  executeAll: (data?: { workflow_type?: string; executed_by?: string }) => 
    apiCall<any>(() => 
      api.post('/api/v1/workflows/execute-all', data)
    ),

  previewExecution: (id: string) => 
    apiCall<any>(() => 
      api.post(`/api/v1/workflows/${id}/preview-execution`)
    ),

  delete: (id: string) => 
    apiCall<{ message: string }>(() => 
      api.delete(`/api/v1/workflows/${id}`)
    ),

  deleteAll: () => 
    apiCall<{ message: string; deleted_count: number }>(() => 
      api.delete('/api/v1/workflows')
    ),
};

// Execution API
export const executionApi = {
  list: (params?: { limit?: number; status?: string; executor_type?: string }) => 
    apiCall<Execution[]>(() => 
      api.get('/api/v1/executions', { params })
    ),

  getById: (id: string) => 
    apiCall<ExecutionDetails>(() => 
      api.get(`/api/v1/executions/${id}`)
    ),

  delete: (id: string) => 
    apiCall<{ message: string; deleted: boolean }>(() => 
      api.delete(`/api/v1/executions/${id}`)
    ),

  deleteAll: (params?: { status?: string; executor_type?: string }) => 
    apiCall<{ message: string; deleted_count: number }>(() => 
      api.delete('/api/v1/executions', { params })
    ),

  getWorkflowExecutions: (workflowId: string) => 
    apiCall<Execution[]>(() => 
      api.get(`/api/v1/workflows/${workflowId}/executions`)
    ),

  getStatistics: () => 
    apiCall<any>(() => 
      api.get('/api/v1/executions/statistics')
    ),
};

// Forecast API
export const forecastApi = {
  generate: (payload: ForecastGenerateRequest) =>
    apiCall<ForecastResult>(() =>
      api.post('/api/v1/forecasts/generate', payload)
    ),

  getById: (forecastId: string) =>
    apiCall<ForecastResult>(() =>
      api.get(`/api/v1/forecasts/${forecastId}`)
    ),

  getAvailableTypes: () =>
    apiCall<ForecastTypeSummary[]>(() =>
      api.get('/api/v1/forecasts/types/available')
    ),

  getTypeInfo: (forecastType: string) =>
    apiCall<ForecastTypeInfo>(() =>
      api.get(`/api/v1/forecasts/types/${forecastType}`)
    ),

  getReadiness: (forecastType?: string) =>
    apiCall<ForecastReadinessResponse>(() =>
      api.get('/api/v1/forecasts/data/readiness', {
        params: forecastType ? { forecast_type: forecastType } : undefined,
      })
    ),

  getDataSummary: () =>
    apiCall<ForecastDataSummary>(() =>
      api.get('/api/v1/forecasts/data/summary')
    ),

  getStatistics: () =>
    apiCall<ForecastStatistics>(() =>
      api.get('/api/v1/forecasts/statistics')
    ),

  delete: (forecastId: string) =>
    apiCall<{ message: string }>(() =>
      api.delete(`/api/v1/forecasts/${forecastId}`)
    ),

  cleanupExpired: () =>
    apiCall<{ message: string }>(() =>
      api.post('/api/v1/forecasts/cleanup')
    ),

  getHistory: (forecastType: string, limit: number = 10) =>
    apiCall<ForecastHistoryItem[]>(() =>
      api.get(`/api/v1/forecasts/type/${forecastType}/history`, { params: { limit } })
    ),
};

// System API
export const systemApi = {
  health: () => 
    apiCall<any>(() => 
      api.get('/api/v1/health')
    ),

  getMetrics: () => 
    apiCall<DashboardMetrics>(() => 
      api.get('/api/v1/metrics')
    ),

  getWorkflowStatus: () => 
    apiCall<any>(() => 
      api.get('/api/v1/workflow/status')
    ),
};

// Insights API
export const insightsApi = {
  discoverPatterns: (riskThreshold: number = 0.7) => 
    apiCall<RiskPattern[]>(() => 
      api.get('/api/v1/insights/patterns', { params: { risk_threshold: riskThreshold } })
    ),

  getHighRisks: (riskThreshold: number = 0.8) => 
    apiCall<RiskPattern[]>(() => 
      api.get('/api/v1/insights/risks', { params: { risk_threshold: riskThreshold } })
    ),

  getCustomerRecommendations: (customerId: string) => 
    apiCall<CustomerRecommendation>(() => 
      api.get(`/api/v1/insights/recommendations/${customerId}`)
    ),

  findSimilarCases: (analysisId: string, limit: number = 5) => 
    apiCall<Analysis[]>(() => 
      api.get(`/api/v1/insights/similar/${analysisId}`, { params: { limit } })
    ),

  getDashboard: () => 
    apiCall<InsightsData>(() => 
      api.get('/api/v1/insights/dashboard')
    ),

  populate: (data: { 
    analysis_id?: string; 
    analysis_ids?: string[]; 
    from_date?: string; 
    all?: boolean;
  }) => 
    apiCall<any>(() => 
      api.post('/api/v1/insights/populate', data)
    ),

  query: (data: { cypher: string; parameters?: Record<string, any> }) => 
    apiCall<any>(() => 
      api.post('/api/v1/insights/query', data)
    ),

  getStatus: () => 
    apiCall<any>(() => 
      api.get('/api/v1/insights/status')
    ),

  deleteAnalysis: (analysisId: string) => 
    apiCall<any>(() => 
      api.delete(`/api/v1/insights/analyses/${analysisId}`)
    ),

  deleteCustomer: (customerId: string, cascade: boolean = false) => 
    apiCall<any>(() => 
      api.delete(`/api/v1/insights/customers/${customerId}`, { params: { cascade } })
    ),

  pruneData: (olderThanDays: number) => 
    apiCall<any>(() => 
      api.post('/api/v1/insights/prune', { older_than_days: olderThanDays })
    ),

  clearGraph: () => 
    apiCall<any>(() => 
      api.delete('/api/v1/insights/clear')
    ),

  getVisualizationData: () => 
    apiCall<any>(() => 
      api.get('/api/v1/insights/visualization/data')
    ),

  getVisualizationStats: () => 
    apiCall<any>(() => 
      api.get('/api/v1/insights/visualization/stats')
    ),
};

// Orchestration API
export const orchestrationApi = {
  // Start a new pipeline run
  runPipeline: (transcript_ids: string[], auto_approve: boolean = false) =>
    apiCall<OrchestrationRunResponse>(() =>
      api.post('/api/v1/orchestrate/run', {
        transcript_ids,
        auto_approve
      })
    ),

  // Get status of a specific run
  getStatus: (run_id: string) =>
    apiCall<OrchestrationRun>(() =>
      api.get(`/api/v1/orchestrate/status/${run_id}`)
    ),

  // List all orchestration runs
  listRuns: () =>
    apiCall<{ runs: OrchestrationRun[] }>(() =>
      api.get('/api/v1/orchestrate/runs')
    ),
};

// Unified Chat API - Single endpoint for all roles
export const chatApi = {
  send: (data: { advisor_id: string; message: string; role: string; session_id?: string; transcript_id?: string; plan_id?: string }) =>
    apiCall<AdvisorChatResponse>(() =>
      api.post('/api/v1/advisor/chat', data)
    ),

  sendStream: (data: { advisor_id: string; message: string; role: string; session_id?: string; transcript_id?: string; plan_id?: string }) =>
    api.post('/api/v1/advisor/chat/stream', data),
};

// Legacy APIs - kept for backward compatibility but use unified chatApi instead
export const leadershipApi = {
  chat: (data: LeadershipChatRequest) =>
    // Route to unified endpoint with leadership role
    chatApi.send({
      advisor_id: data.executive_id,
      message: data.query,
      role: 'leadership',
      session_id: data.session_id
    }),
};

export const advisorApi = {
  chat: (data: AdvisorChatRequest) =>
    // Route to unified endpoint with advisor role
    chatApi.send({
      advisor_id: data.advisor_id,
      message: data.message,
      role: data.role || 'advisor',
      session_id: data.session_id,
      transcript_id: data.transcript_id,
      plan_id: data.plan_id
    }),

  getSessions: (advisorId: string, limit: number = 5) =>
    apiCall<{ sessions: any[] }>(() =>
      api.get(`/api/v1/advisor/sessions/${advisorId}`, { params: { limit } })
    ),
};

export default api;
