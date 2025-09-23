import {
  UnifiedChatRequest,
  UnifiedChatResponse,
  LeadershipChatRequest,
  AdvisorChatRequest
} from '@/types';
import { chatApi } from '@/api/client';

/**
 * Unified chat service using single endpoint for all roles.
 * Much simpler now - no routing needed!
 */
export class ChatService {
  /**
   * Send a unified chat request using the single endpoint with role parameter.
   */
  static async sendMessage(request: UnifiedChatRequest): Promise<UnifiedChatResponse> {
    try {
      const response = await chatApi.send({
        advisor_id: request.user_id,
        message: request.message,
        role: request.role,
        session_id: request.session_id,
        transcript_id: request.context?.transcript_id,
        plan_id: request.context?.plan_id
      });

      // Transform response to unified format
      return {
        content: response.response,
        session_id: response.session_id,
        role: request.role,
        agent_mode: request.agent_mode,
        actions: response.actions,
        context: response.context,
        metadata: {
          processing_time_ms: 1000, // Default value
          confidence: 0.9 // Default value
        }
      };
    } catch (error) {
      console.error('Unified chat API error:', error);
      throw error;
    }
  }


  /**
   * Get user sessions - now managed automatically by OpenAI Agents
   */
  static async getUserSessions(userId: string, role: string, limit: number = 5): Promise<any[]> {
    // Sessions are now managed automatically by OpenAI Agents SQLiteSession
    // No need for explicit session management
    return [];
  }
}

/**
 * Convenience function for sending unified chat messages
 */
export async function sendUnifiedChatMessage(request: UnifiedChatRequest): Promise<UnifiedChatResponse> {
  return ChatService.sendMessage(request);
}