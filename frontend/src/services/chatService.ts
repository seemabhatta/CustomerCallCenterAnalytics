import {
  UnifiedChatRequest,
  UnifiedChatResponse,
  LeadershipChatRequest,
  AdvisorChatRequest
} from '@/types';
import { leadershipApi, advisorApi } from '@/api/client';

/**
 * Unified chat service that routes requests to appropriate APIs based on role
 * and transforms responses to a consistent format.
 */
export class ChatService {
  /**
   * Send a unified chat request that automatically routes to the correct API
   * based on the role and transforms the response.
   */
  static async sendMessage(request: UnifiedChatRequest): Promise<UnifiedChatResponse> {
    if (request.role === 'leadership') {
      return await this.sendLeadershipMessage(request);
    } else if (request.role === 'advisor') {
      return await this.sendAdvisorMessage(request);
    } else {
      throw new Error(`Unsupported chat role: ${request.role}`);
    }
  }

  /**
   * Handle leadership chat requests
   */
  private static async sendLeadershipMessage(request: UnifiedChatRequest): Promise<UnifiedChatResponse> {
    // Transform unified request to leadership API format
    const leadershipRequest: LeadershipChatRequest = {
      query: request.message,
      executive_id: request.user_id,
      executive_role: this.mapRoleToExecutiveRole(request.agent_mode),
      session_id: request.session_id
    };

    try {
      const response = await leadershipApi.chat(leadershipRequest);

      // Transform leadership response to unified format
      return {
        content: response.content,
        session_id: response.session_id,
        role: 'leadership',
        agent_mode: request.agent_mode,
        executive_summary: response.executive_summary,
        key_metrics: response.key_metrics,
        recommendations: response.recommendations,
        supporting_data: response.supporting_data,
        metadata: {
          processing_time_ms: response.metadata.total_processing_time_ms,
          confidence: response.metadata.overall_confidence,
          data_sources_used: response.metadata.data_sources_used,
          query_understanding: response.metadata.query_understanding
        }
      };
    } catch (error) {
      console.error('Leadership chat API error:', error);
      throw error;
    }
  }

  /**
   * Handle advisor chat requests
   */
  private static async sendAdvisorMessage(request: UnifiedChatRequest): Promise<UnifiedChatResponse> {
    // Transform unified request to advisor API format
    const advisorRequest: AdvisorChatRequest = {
      advisor_id: request.user_id,
      message: this.enhanceMessageWithMode(request.message, request.agent_mode),
      session_id: request.session_id,
      transcript_id: request.context?.transcript_id,
      plan_id: request.context?.plan_id
    };

    try {
      const response = await advisorApi.chat(advisorRequest);

      // Transform advisor response to unified format
      return {
        content: response.response,
        session_id: response.session_id,
        role: 'advisor',
        agent_mode: request.agent_mode,
        actions: response.actions,
        context: response.context,
        metadata: {
          processing_time_ms: 1000, // Default value as advisor API doesn't provide this
          confidence: 0.9 // Default value as advisor API doesn't provide this
        }
      };
    } catch (error) {
      console.error('Advisor chat API error:', error);
      throw error;
    }
  }

  /**
   * Map agent mode to leadership executive role
   */
  private static mapRoleToExecutiveRole(agentMode?: string): string {
    switch (agentMode) {
      case 'supervisor':
        return 'Supervisor';
      case 'compliance':
        return 'Compliance Officer';
      case 'borrower':
        return 'Customer Relations Manager';
      default:
        return 'Manager';
    }
  }

  /**
   * Enhance the message with agent mode context for advisor requests
   */
  private static enhanceMessageWithMode(message: string, agentMode?: string): string {
    if (!agentMode || agentMode === 'general') {
      return message;
    }

    const modeContexts = {
      borrower: 'Acting as a borrower-focused advisor, ',
      supervisor: 'Acting in supervisor mode for escalation and team management, ',
      compliance: 'Acting in compliance mode with focus on regulatory requirements, '
    };

    const context = modeContexts[agentMode as keyof typeof modeContexts];
    return context ? `${context}${message}` : message;
  }

  /**
   * Get user sessions (currently only supported for advisor role)
   */
  static async getUserSessions(userId: string, role: string, limit: number = 5): Promise<any[]> {
    if (role === 'advisor') {
      try {
        const response = await advisorApi.getSessions(userId, limit);
        return response.sessions;
      } catch (error) {
        console.error('Error fetching advisor sessions:', error);
        return [];
      }
    }

    // Leadership sessions not currently supported by API
    return [];
  }
}

/**
 * Convenience function for sending unified chat messages
 */
export async function sendUnifiedChatMessage(request: UnifiedChatRequest): Promise<UnifiedChatResponse> {
  return ChatService.sendMessage(request);
}