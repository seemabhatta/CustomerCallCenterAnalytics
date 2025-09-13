import axios, { AxiosResponse } from 'axios';
import { 
  Transcript, 
  Analysis, 
  Plan, 
  Workflow, 
  Execution,
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
  ApiError
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
    apiCall<Transcript[]>(() => 
      api.get('/api/v1/transcripts', { params })
    ),

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
};

// Execution API
export const executionApi = {
  getStatus: (id: string) => 
    apiCall<any>(() => 
      api.get(`/api/v1/executions/${id}`)
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

export default api;