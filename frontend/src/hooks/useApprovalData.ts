import { useState, useEffect } from 'react';

export interface TranscriptDetail {
  transcript_id: string;
  customer_id: string;
  scenario: string;
  messages: Array<{
    role: string;
    content: string;
    timestamp?: string;
  }>;
  message_count: number;
  urgency: 'low' | 'medium' | 'high';
  financial_impact: boolean;
  stored: boolean;
  created_at: string;
  metadata?: any;
}

export interface ApprovalItem {
  transcript_id: string;
  scenario: string;
  customer_id: string;
  urgency: 'low' | 'medium' | 'high';
  financial_impact: boolean;
  created_at: string;
  // Simulated approval workflow data
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  business_impact: 'financial' | 'compliance' | 'retention' | 'standard';
  priority_score: number;
  pending_actions: number;
  auto_approved: number;
  manually_approved: number;
}

export function useApprovalData() {
  const [approvalItems, setApprovalItems] = useState<ApprovalItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchApprovalData = async () => {
      try {
        setLoading(true);
        
        // Get all transcripts from the backend
        const response = await fetch('/transcripts');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const transcripts = await response.json();
        
        // Transform transcript data into approval items with simulated workflow data
        const approvalItems = transcripts.map((transcript: any, index: number): ApprovalItem => {
          // Simulate approval workflow data based on transcript characteristics
          const hasFinancialImpact = transcript.financial_impact;
          const isHighUrgency = transcript.urgency === 'high';
          const messageCount = transcript.message_count || 0;
          
          // Calculate risk level based on transcript characteristics
          let risk_level: 'low' | 'medium' | 'high' | 'critical' = 'medium';
          if (hasFinancialImpact && isHighUrgency) {
            risk_level = 'critical';
          } else if (hasFinancialImpact || isHighUrgency) {
            risk_level = 'high';
          } else if (messageCount > 20) {
            risk_level = 'medium';
          } else {
            risk_level = 'low';
          }
          
          // Determine business impact
          let business_impact: 'financial' | 'compliance' | 'retention' | 'standard' = 'standard';
          if (hasFinancialImpact) business_impact = 'financial';
          else if (transcript.scenario?.toLowerCase().includes('compliance')) business_impact = 'compliance';
          else if (isHighUrgency) business_impact = 'retention';
          
          // Calculate priority score (0-100)
          let priority_score = 50;
          if (risk_level === 'critical') priority_score = 90 + Math.floor(Math.random() * 10);
          else if (risk_level === 'high') priority_score = 70 + Math.floor(Math.random() * 20);
          else if (risk_level === 'medium') priority_score = 40 + Math.floor(Math.random() * 30);
          else priority_score = 10 + Math.floor(Math.random() * 40);
          
          // Simulate action counts
          const total_actions = Math.floor(Math.random() * 8) + 5; // 5-12 actions
          const auto_approved = Math.floor(total_actions * 0.4); // ~40% auto approved
          const manually_approved = Math.floor(total_actions * 0.2); // ~20% manually approved
          const pending_actions = total_actions - auto_approved - manually_approved; // Rest pending
          
          return {
            transcript_id: transcript.transcript_id,
            scenario: transcript.scenario || 'Customer Service Inquiry',
            customer_id: transcript.customer_id || `CUST_${index + 1000}`,
            urgency: transcript.urgency,
            financial_impact: transcript.financial_impact,
            created_at: transcript.created_at,
            risk_level,
            business_impact,
            priority_score,
            pending_actions: Math.max(1, pending_actions), // Always at least 1 pending
            auto_approved,
            manually_approved
          };
        });
        
        // Sort by priority score (highest first)
        approvalItems.sort((a, b) => b.priority_score - a.priority_score);
        
        setApprovalItems(approvalItems);
        setError(null);
      } catch (err) {
        console.error('Error fetching approval data:', err);
        setError(err instanceof Error ? err.message : 'Failed to fetch approval data');
      } finally {
        setLoading(false);
      }
    };

    fetchApprovalData();
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchApprovalData, 30000);
    return () => clearInterval(interval);
  }, []);

  return { approvalItems, loading, error };
}

export async function getTranscriptDetail(transcriptId: string): Promise<TranscriptDetail> {
  try {
    const response = await fetch(`/transcript/${transcriptId}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch transcript details: ${response.status}`);
    }
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching transcript:', error);
    throw new Error('Failed to load transcript details');
  }
}