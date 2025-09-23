import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';
import {
  MessageCircle,
  Send,
  Trash2,
  User,
  Bot,
  Zap,
  FileText,
  CheckCircle,
  DollarSign,
  Crown,
  Settings,
  Users,
  Shield
} from 'lucide-react';
import {
  ChatRole,
  AgentMode,
  UnifiedChatResponse
} from '@/types';
import { sendUnifiedChatMessage } from '@/services/chatService';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  actions?: any[];
  metadata?: any;
  type?: 'message' | 'thinking' | 'tool_call' | 'streaming';
  isComplete?: boolean;
  isThinking?: boolean;
}

interface SimpleChatViewProps {
  role: ChatRole;
  userId: string;
  agentMode?: AgentMode;
  context?: {
    transcriptId?: string | null;
    planId?: string | null;
    analysisId?: string | null;
    workflowId?: string | null;
  };
  onChatResponse?: (response: UnifiedChatResponse) => void;
}

export function SimpleChatView({
  role,
  userId,
  agentMode = 'borrower',
  context = {},
  onChatResponse
}: SimpleChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: getWelcomeMessage(role),
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentAgentMode, setCurrentAgentMode] = useState<AgentMode>(agentMode);
  const [streamingEnabled, setStreamingEnabled] = useState(true);
  const messageContainerRef = useRef<HTMLDivElement>(null);
  const lastAutoScrolledMessageIdRef = useRef<string | null>(null);
  const [isAtBottom, setIsAtBottom] = useState(true);
  const abortControllerRef = useRef<AbortController | null>(null);

  const scrollToBottom = (behavior: ScrollBehavior = 'smooth') => {
    if (!messageContainerRef.current) return;
    messageContainerRef.current.scrollTo({
      top: messageContainerRef.current.scrollHeight,
      behavior
    });
    setIsAtBottom(true);
  };

  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (!lastMessage) return;

    const isStreaming = lastMessage.type === 'streaming' && !lastMessage.isComplete;
    const isSameAsLastScrolled = lastAutoScrolledMessageIdRef.current === lastMessage.id;

    if (!isAtBottom) {
      lastAutoScrolledMessageIdRef.current = lastMessage.id;
      return;
    }

    if (isStreaming && isSameAsLastScrolled) {
      return;
    }

    scrollToBottom(isStreaming ? 'auto' : 'smooth');
    lastAutoScrolledMessageIdRef.current = lastMessage.id;
  }, [messages, isAtBottom]);

  const handleMessagesScroll = (event: React.UIEvent<HTMLDivElement>) => {
    const target = event.currentTarget;
    const distanceFromBottom = target.scrollHeight - target.scrollTop - target.clientHeight;
    const atBottom = distanceFromBottom <= 32;
    if (atBottom !== isAtBottom) {
      setIsAtBottom(atBottom);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleSendMessage = async (messageContent?: string) => {
    const messageToSend = messageContent || inputMessage.trim();
    if (!messageToSend) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageToSend,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    if (!messageContent) setInputMessage('');
    setIsLoading(true);

    // Use streaming for all roles when enabled
    if (streamingEnabled) {
      await handleStreamingMessage(messageToSend);
    } else {
      await handleRegularMessage(messageToSend);
    }
  };

  const handleStreamingMessage = async (messageToSend: string) => {
    try {
      // Abort any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();

      // Create placeholder assistant message for streaming
      const streamingMessageId = (Date.now() + 1).toString();
      let assistantMessage: ChatMessage = {
        id: streamingMessageId,
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        type: 'streaming',
        isComplete: false,
        isThinking: false
      };

      setMessages(prev => [...prev, assistantMessage]);

      const response = await fetch('/api/v1/advisor/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          advisor_id: userId,
          message: messageToSend,
          role: role, // Add role parameter for unified endpoint
          session_id: sessionId || undefined,
          transcript_id: context.transcriptId || undefined,
          plan_id: context.planId || undefined
        }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body reader available');
      }

      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const eventData = JSON.parse(line.slice(6));
                await handleStreamEvent(eventData, streamingMessageId);

                // Update session ID if received
                if (eventData.session_id && !sessionId) {
                  setSessionId(eventData.session_id);
                }

                // Break if completed or error
                if (eventData.type === 'completed' || eventData.type === 'error') {
                  break;
                }
              } catch (e) {
                console.warn('Failed to parse SSE event:', line, e);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }

    } catch (error: any) {
      if (error.name !== 'AbortError') {
        console.error('Streaming chat error:', error);
        const errorMessage: ChatMessage = {
          id: (Date.now() + 2).toString(),
          role: 'assistant',
          content: 'Sorry, I encountered an error with the streaming response. Please try again.',
          timestamp: new Date(),
          type: 'message'
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleRegularMessage = async (messageToSend: string) => {
    try {
      const response = await sendUnifiedChatMessage({
        role,
        user_id: userId,
        message: messageToSend,
        session_id: sessionId || undefined,
        agent_mode: currentAgentMode,
        context: {
          transcript_id: context.transcriptId || undefined,
          plan_id: context.planId || undefined,
          analysis_id: context.analysisId || undefined,
          workflow_id: context.workflowId || undefined
        }
      });

      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        actions: response.actions,
        metadata: response.metadata,
        type: 'message'
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (onChatResponse) {
        onChatResponse(response);
      }

    } catch (error) {
      console.error('Unified chat API error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date(),
        type: 'message'
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleStreamEvent = async (eventData: any, messageId: string) => {
    setMessages(prev => {
      const newMessages = [...prev];
      const messageIndex = newMessages.findIndex(m => m.id === messageId);

      if (messageIndex === -1) return prev;

      const currentMessage = { ...newMessages[messageIndex] };

      switch (eventData.type) {
        case 'thinking':
          // Add thinking indicator flag
          currentMessage.isThinking = true;
          break;

        case 'tool_call':
          // Add tool call indicator
          const toolContent = eventData.content + '\n\n';
          if (!currentMessage.content.includes(toolContent)) {
            currentMessage.isThinking = false;
            currentMessage.content = currentMessage.content + toolContent;
          }
          break;

        case 'response_delta':
          // Append text delta and stop thinking
          currentMessage.isThinking = false;
          const deltaContent = eventData.content;
          // Remove tool indicators when real content starts
          let baseContent = currentMessage.content.replace(/🔧 Calling.*?\.\.\.\n\n/g, '');
          currentMessage.content = baseContent + deltaContent;
          break;

        case 'completed':
          // Just mark as complete - we already have the content from streaming deltas
          currentMessage.isComplete = true;
          currentMessage.type = 'message';
          break;

        case 'error':
          // Show error
          currentMessage.content = eventData.content;
          currentMessage.isComplete = true;
          currentMessage.type = 'message';
          break;
      }

      newMessages[messageIndex] = currentMessage;
      return newMessages;
    });
  };

  const handleClearChat = () => {
    setSessionId(null);
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content: getWelcomeMessage(role),
        timestamp: new Date()
      }
    ]);
    lastAutoScrolledMessageIdRef.current = null;
  };

  const handleAgentModeChange = (mode: AgentMode) => {
    setCurrentAgentMode(mode);
    const systemMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content: `Switched to ${mode} mode. How can I assist you in this context?`,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, systemMessage]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickActions = getQuickActionsForRole(role);

  return (
    <>
      <style>{`
        .thinking-dots {
          display: inline-block;
          animation: thinking 1.5s infinite;
          color: #64748b;
          font-weight: bold;
        }

        @keyframes thinking {
          0%, 20% { opacity: 0.2; }
          40% { opacity: 1; }
          60%, 100% { opacity: 0.2; }
        }

        .chat-markdown-root {
          line-height: 1.5;
        }

        .chat-markdown-root :where(p,
          ul,
          ol,
          pre,
          blockquote,
          table) {
          margin-top: 0.2rem;
          margin-bottom: 0.2rem;
        }

        .chat-markdown-root :where(p,
          ul,
          ol,
          blockquote):first-child {
          margin-top: 0;
        }

        .chat-markdown-root :where(h1,
          h2,
          h3,
          h4,
          h5,
          h6) {
          margin-top: 0.5rem;
          margin-bottom: 0.3rem;
          line-height: 1.3;
        }

        .chat-markdown-root :where(ul,
          ol) {
          padding-left: 1.25rem;
        }

        .chat-markdown-root :where(li) {
          margin-top: 0.25rem;
        }

        .chat-markdown-root :where(li > p) {
          margin-top: 0;
          margin-bottom: 0;
        }

        .chat-markdown-root :where(li > p:first-child) {
          display: inline;
        }

        .chat-markdown-root :where(li > p:not(:first-child)) {
          display: block;
          margin-top: 0.2rem;
        }
      `}</style>
      <div className="page-shell">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-blue-600" />
          <h1 className="text-xl font-bold">
            {role === 'leadership' ? 'Executive Assistant' : 'AI Assistant'}
          </h1>
          {(context.transcriptId || context.planId) && (
            <div className="flex gap-2 ml-4">
              {context.transcriptId && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                  Transcript: {context.transcriptId.slice(0, 8)}...
                </span>
              )}
              {context.planId && (
                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                  Plan: {context.planId.slice(0, 8)}...
                </span>
              )}
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {role === 'advisor' && (
            <Select value={currentAgentMode} onValueChange={(value: AgentMode) => handleAgentModeChange(value)}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="borrower">
                  <div className="flex items-center gap-1">
                    <User className="h-3 w-3" />
                    Borrower
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          )}
          <Button
            variant="outline"
            size="sm"
            onClick={handleClearChat}
            className="flex items-center gap-1"
          >
            <Trash2 className="h-3 w-3" />
            Clear Chat
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3">
          <Card className="h-[600px] flex flex-col overflow-hidden">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">
                Conversation {role === 'advisor' && `(${currentAgentMode} mode)`}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col min-h-0">
              {/* Messages Container */}
              <div
                ref={messageContainerRef}
                onScroll={handleMessagesScroll}
                className="flex-1 overflow-y-auto min-h-0"
              >
                <div className="space-y-4 p-2">
                  {messages.map((message) => (
                    <div key={message.id} className="mb-4">
                      {/* Message Container with Flex and Width Constraint */}
                      <div className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} w-full`}>
                        {/* Avatar for assistant messages */}
                        {message.role === 'assistant' && (
                          <div className="flex-shrink-0 mr-3">
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                              message.type === 'streaming' && !message.isComplete
                                ? 'bg-blue-100 animate-pulse'
                                : 'bg-blue-100'
                            }`}>
                              {role === 'leadership' ? (
                                <Crown className="h-4 w-4 text-blue-600" />
                              ) : (
                                <Bot className="h-4 w-4 text-blue-600" />
                              )}
                            </div>
                          </div>
                        )}

                        {/* Message Bubble with Proper Text Wrapping */}
                        <div
                          className={`
                            ${message.role === 'user' ? 'max-w-[70%]' : 'max-w-[85%]'} min-w-0 px-4 py-2 rounded-lg
                            ${message.role === 'user'
                              ? 'bg-blue-600 text-white'
                              : 'bg-slate-100 text-slate-900'
                            }
                          `}
                          style={{
                            wordWrap: 'break-word',
                            overflowWrap: 'break-word',
                            wordBreak: 'break-word',
                            whiteSpace: 'normal'
                          }}
                        >
                          <div className="text-sm w-full overflow-x-auto break-words chat-markdown-root">
                            {message.isThinking && (
                              <span className="thinking-dots">...</span>
                            )}
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              rehypePlugins={[rehypeHighlight]}
                              components={{
                                // Custom styling for markdown elements - compact version
                                h1: ({node, ...props}) => <h1 className="text-base font-bold" {...props} />,
                                h2: ({node, ...props}) => <h2 className="text-sm font-bold" {...props} />,
                                h3: ({node, ...props}) => <h3 className="text-xs font-bold" {...props} />,
                                p: ({node, ...props}) => <p className="leading-relaxed" {...props} />,
                                ul: ({node, ...props}) => <ul className="list-disc list-inside" {...props} />,
                                ol: ({node, ...props}) => <ol className="list-decimal list-inside" {...props} />,
                                li: ({node, ...props}) => <li {...props} />,
                                code: ({node, ...props}) => {
                                  // Check if this is inline code (no className or short content)
                                  const isInline = !props.className || (typeof props.children === 'string' && props.children.length < 100);
                                  return isInline
                                    ? <code className="bg-gray-200/50 px-0.5 py-0 rounded text-xs font-mono" {...props} />
                                    : <code className="block bg-gray-100 p-1 rounded text-xs font-mono overflow-x-auto" {...props} />;
                                },
                                pre: ({node, ...props}) => <pre className="bg-gray-100 p-1 rounded overflow-x-auto mb-1" {...props} />,
                                blockquote: ({node, ...props}) => <blockquote className="border-l-4 border-gray-300 pl-4 italic mb-1" {...props} />,
                                a: ({node, ...props}) => <a className="text-blue-600 underline" {...props} />,
                                table: ({node, ...props}) => <table className="border-collapse border border-gray-300 mb-1 overflow-x-auto" {...props} />,
                                th: ({node, ...props}) => <th className="border border-gray-300 px-1 py-0.5 bg-gray-100 font-bold text-xs" {...props} />,
                                td: ({node, ...props}) => <td className="border border-gray-300 px-1 py-0.5 text-xs" {...props} />,
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          </div>

                          {message.actions && message.actions.length > 0 && (
                            <div className="mt-2">
                              <p className="text-xs font-medium opacity-70">
                                Actions taken:
                              </p>
                              {message.actions.map((action, idx) => (
                                <div
                                  key={idx}
                                  className="text-xs bg-white p-2 rounded border mt-1 break-words"
                                >
                                  <span className="font-medium">{action.type}:</span> {action.description}
                                </div>
                              ))}
                            </div>
                          )}

                          <p className="text-xs mt-1 opacity-70">
                            {message.timestamp.toLocaleTimeString()}
                          </p>
                        </div>

                        {/* Avatar for user messages */}
                        {message.role === 'user' && (
                          <div className="flex-shrink-0 ml-3">
                            <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
                              <User className="h-4 w-4 text-slate-600" />
                            </div>
                          </div>
                        )}
                      </div>
                  </div>
                ))}
                </div>
              </div>

              {/* Input Area */}
              <div className="border-t pt-4 flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={getPlaceholderText(role, currentAgentMode)}
                  disabled={isLoading}
                  className="flex-1"
                />
                <Button
                  onClick={() => handleSendMessage()}
                  disabled={isLoading || !inputMessage.trim()}
                  size="sm"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">
                Quick Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {quickActions.map((action, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  className="w-full justify-start text-left h-auto p-3"
                  onClick={() => handleSendMessage(action.message)}
                  disabled={isLoading}
                >
                  <div className="flex items-start gap-2">
                    <action.icon className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span className="text-xs">{action.label}</span>
                  </div>
                </Button>
              ))}
            </CardContent>
          </Card>

          {sessionId && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-slate-600">
                  Session Info
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-xs text-slate-500 break-all">
                  ID: {sessionId}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Messages: {messages.length}
                </p>
                <p className="text-xs text-slate-500 mt-1">
                  Role: {role}
                </p>
                {role === 'advisor' && (
                  <p className="text-xs text-slate-500 mt-1">
                    Mode: {currentAgentMode}
                  </p>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
      </div>
    </>
  );
}

// Helper functions
function getWelcomeMessage(role: ChatRole): string {
  if (role === 'leadership') {
    return "Hello! I'm your executive assistant for strategic insights and portfolio analytics. I can help you with portfolio performance, risk analysis, and strategic decision support. What would you like to explore?";
  }
  return "Hello! I'm your AI assistant for mortgage servicing workflows. I can help you with customer requests, compliance checks, document generation, and system actions. How can I assist you today?";
}

function getPlaceholderText(role: ChatRole, agentMode: AgentMode): string {
  if (role === 'leadership') {
    return "Ask about portfolio insights, metrics, or strategic opportunities...";
  }

  switch (agentMode) {
    case 'borrower':
      return "Ask about borrower-specific actions and workflows...";
    case 'supervisor':
      return "Ask about supervision and escalation workflows...";
    case 'compliance':
      return "Ask about compliance requirements and regulations...";
    default:
      return "Ask me anything about customer workflows...";
  }
}

function getQuickActionsForRole(role: ChatRole) {
  if (role === 'leadership') {
    return [
      {
        icon: CheckCircle,
        label: "Portfolio Health",
        message: "Show me the current portfolio health and key metrics"
      },
      {
        icon: FileText,
        label: "Risk Analysis",
        message: "Analyze current risk patterns and provide recommendations"
      },
      {
        icon: DollarSign,
        label: "Revenue Impact",
        message: "Show revenue opportunities and cost optimization insights"
      },
      {
        icon: Zap,
        label: "Strategic Actions",
        message: "What strategic actions should we prioritize this quarter?"
      }
    ];
  }

  return [
    {
      icon: FileText,
      label: "Last Call ID",
      message: "What was the last call ID?"
    },
    {
      icon: CheckCircle,
      label: "Show Analysis",
      message: "Tell me the analysis result for the call"
    },
    {
      icon: Zap,
      label: "Show Plan",
      message: "Show me the strategic plan for this call"
    },
    {
      icon: DollarSign,
      label: "Show Workflows",
      message: "What workflows are available for this plan?"
    }
  ];
}
