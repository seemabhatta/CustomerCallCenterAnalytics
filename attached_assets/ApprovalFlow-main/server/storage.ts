import { type User, type InsertUser, type Case, type InsertCase, type Transcript, type InsertTranscript, type Analysis, type InsertAnalysis, type Action, type InsertAction, type Metrics } from "@shared/schema";
import { randomUUID } from "crypto";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // Cases
  getCases(filters?: { priority?: string; status?: string; search?: string }): Promise<Case[]>;
  getCase(id: string): Promise<Case | undefined>;
  createCase(caseData: InsertCase): Promise<Case>;
  updateCase(id: string, updates: Partial<Case>): Promise<Case | undefined>;
  
  // Transcripts
  getTranscriptsByCase(caseId: string): Promise<Transcript[]>;
  createTranscript(transcript: InsertTranscript): Promise<Transcript>;
  
  // Analysis
  getAnalysisByCase(caseId: string): Promise<Analysis | undefined>;
  createAnalysis(analysis: InsertAnalysis): Promise<Analysis>;
  
  // Actions
  getActionsByCase(caseId: string): Promise<Action[]>;
  createAction(action: InsertAction): Promise<Action>;
  updateAction(id: string, updates: Partial<Action>): Promise<Action | undefined>;
  
  // Metrics
  getMetrics(): Promise<Metrics | undefined>;
  updateMetrics(metrics: Partial<Metrics>): Promise<Metrics>;
}

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private cases: Map<string, Case>;
  private transcripts: Map<string, Transcript>;
  private analyses: Map<string, Analysis>;
  private actions: Map<string, Action>;
  private metrics: Metrics | undefined;

  constructor() {
    this.users = new Map();
    this.cases = new Map();
    this.transcripts = new Map();
    this.analyses = new Map();
    this.actions = new Map();
    this.initializeData();
  }

  private initializeData() {
    // Initialize with sample data
    const now = new Date();
    
    // Sample metrics
    this.metrics = {
      id: randomUUID(),
      totalTranscripts: 1228,
      transcriptsPrev: 1160,
      completeRate: 0.17,
      completeRatePrev: 0.13,
      avgProcessingTime: 12.3,
      avgProcessingTimePrev: 13.8,
      stageData: {
        transcript: { ready: 28, processing: 3 },
        analysis: { queue: 127, processing: 15 },
        plan: { queue: 89, generating: 8 },
        approval: { pending: 234, approved: 568 },
        execution: { running: 187, complete: 208 },
      },
      lastUpdated: now,
    };

    // Sample cases
    for (let i = 1; i <= 28; i++) {
      const caseId = randomUUID();
      const priority = 79 + (i % 11);
      const case_: Case = {
        id: caseId,
        customerId: `CUST_${1000 + i}`,
        callId: `CALL_${Math.random().toString(36).slice(2, 10).toUpperCase()}`,
        scenario: "PMI Removal Dispute",
        priority,
        status: "Needs Review",
        risk: priority >= 88 ? "High" : priority >= 83 ? "Medium" : "Low",
        financialImpact: "$2,500 potential loss",
        exchanges: 22,
        createdAt: new Date(2025, 8, 9, 8 + (i * 2) % 16, (i * 7) % 60),
        updatedAt: new Date(2025, 8, 9, 8 + (i * 2) % 16, (i * 7) % 60),
      };
      this.cases.set(caseId, case_);

      // Sample transcripts for first case
      if (i === 1) {
        const transcriptData = [
          { speaker: "Emily (Servicing Specialist)", content: "Hi James, thanks for reaching out. I understand you're looking to remove the PMI. Can you tell me about the valuation?" },
          { speaker: "James (Homeowner)", content: "Yes, I had an independent appraisal done, higher than lender's last assessment. PMI is $200/mo and a burden." },
          { speaker: "Emily", content: "That PMI can add up. We need to confirm compliance before proceeding. Did you submit the appraisal report?" },
          { speaker: "James", content: "Yes, last week. Appraiser valued home at $350,000 vs lender's $325,000." },
          { speaker: "Lisa (Compliance Officer)", content: "We need to ensure regulatory compliance before removal. Additional review required." },
        ];

        transcriptData.forEach((t, idx) => {
          const transcript: Transcript = {
            id: randomUUID(),
            caseId,
            speaker: t.speaker,
            content: t.content,
            timestamp: new Date(now.getTime() + idx * 60000),
          };
          this.transcripts.set(transcript.id, transcript);
        });

        // Sample analysis
        const analysis: Analysis = {
          id: randomUUID(),
          caseId,
          intent: "General Inquiry",
          confidence: 0.9,
          sentiment: "neutral",
          risks: [
            { label: "Churn", value: 0.23 },
            { label: "Complaint", value: 0.61 },
            { label: "Delinquency", value: 0.0 },
          ],
        };
        this.analyses.set(analysis.id, analysis);

        // Sample actions
        const actionsData = [
          { action: "Send automated payment reminder email", category: "Routine Communication", risk: "Low", impact: "Minimal", decision: "Auto‑Approved", autoCount: 2, doneCount: 1, pendingCount: 2 },
          { action: "Update customer contact preferences", category: "Routine Communication", risk: "Low", impact: "Minimal", decision: "Auto‑Approved", autoCount: 3, doneCount: 2, pendingCount: 3 },
          { action: "Apply late fee waiver to account", category: "Account Adjustment", risk: "Medium", impact: "$500–1000", decision: "Approved", autoCount: 2, doneCount: 1, pendingCount: 2 },
          { action: "Initiate loan modification process", category: "Loan Restructuring", risk: "High", impact: "$2,500 potential loss", decision: "Pending", autoCount: 3, doneCount: 2, pendingCount: 3 },
          { action: "Approve 90‑day payment deferral", category: "Payment Plan", risk: "Medium", impact: "$450 interest impact", decision: "Pending", autoCount: 2, doneCount: 1, pendingCount: 2 },
        ];

        actionsData.forEach(a => {
          const action: Action = {
            id: randomUUID(),
            caseId,
            action: a.action,
            category: a.category,
            risk: a.risk,
            impact: a.impact,
            submittedAt: new Date(2025, 8, 9, 5, 48),
            decision: a.decision,
            autoCount: a.autoCount,
            doneCount: a.doneCount,
            pendingCount: a.pendingCount,
          };
          this.actions.set(action.id, action);
        });
      }
    }
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  async getCases(filters?: { priority?: string; status?: string; search?: string }): Promise<Case[]> {
    let cases = Array.from(this.cases.values());
    
    if (filters?.priority) {
      if (filters.priority === 'high') {
        cases = cases.filter(c => c.priority >= 88);
      } else if (filters.priority === 'medium') {
        cases = cases.filter(c => c.priority >= 83 && c.priority < 88);
      }
    }
    
    if (filters?.status) {
      cases = cases.filter(c => c.status === filters.status);
    }
    
    if (filters?.search) {
      const query = filters.search.toLowerCase();
      cases = cases.filter(c => 
        c.id.toLowerCase().includes(query) ||
        c.customerId.toLowerCase().includes(query) ||
        c.callId.toLowerCase().includes(query)
      );
    }
    
    return cases;
  }

  async getCase(id: string): Promise<Case | undefined> {
    return this.cases.get(id);
  }

  async createCase(caseData: InsertCase): Promise<Case> {
    const id = randomUUID();
    const now = new Date();
    const case_: Case = { 
      ...caseData, 
      id, 
      createdAt: now, 
      updatedAt: now 
    };
    this.cases.set(id, case_);
    return case_;
  }

  async updateCase(id: string, updates: Partial<Case>): Promise<Case | undefined> {
    const case_ = this.cases.get(id);
    if (!case_) return undefined;
    
    const updated = { ...case_, ...updates, updatedAt: new Date() };
    this.cases.set(id, updated);
    return updated;
  }

  async getTranscriptsByCase(caseId: string): Promise<Transcript[]> {
    return Array.from(this.transcripts.values()).filter(t => t.caseId === caseId);
  }

  async createTranscript(transcript: InsertTranscript): Promise<Transcript> {
    const id = randomUUID();
    const newTranscript: Transcript = { 
      ...transcript, 
      id, 
      timestamp: new Date() 
    };
    this.transcripts.set(id, newTranscript);
    return newTranscript;
  }

  async getAnalysisByCase(caseId: string): Promise<Analysis | undefined> {
    return Array.from(this.analyses.values()).find(a => a.caseId === caseId);
  }

  async createAnalysis(analysis: InsertAnalysis): Promise<Analysis> {
    const id = randomUUID();
    const newAnalysis: Analysis = { ...analysis, id };
    this.analyses.set(id, newAnalysis);
    return newAnalysis;
  }

  async getActionsByCase(caseId: string): Promise<Action[]> {
    return Array.from(this.actions.values()).filter(a => a.caseId === caseId);
  }

  async createAction(action: InsertAction): Promise<Action> {
    const id = randomUUID();
    const newAction: Action = { 
      ...action, 
      id, 
      submittedAt: new Date() 
    };
    this.actions.set(id, newAction);
    return newAction;
  }

  async updateAction(id: string, updates: Partial<Action>): Promise<Action | undefined> {
    const action = this.actions.get(id);
    if (!action) return undefined;
    
    const updated = { ...action, ...updates };
    this.actions.set(id, updated);
    return updated;
  }

  async getMetrics(): Promise<Metrics | undefined> {
    return this.metrics;
  }

  async updateMetrics(updates: Partial<Metrics>): Promise<Metrics> {
    this.metrics = { ...this.metrics!, ...updates, lastUpdated: new Date() };
    return this.metrics;
  }
}

export const storage = new MemStorage();
