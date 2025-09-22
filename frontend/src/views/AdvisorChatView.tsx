import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { MessageCircle, Send, Trash2, User, Bot, Zap, FileText, CheckCircle, DollarSign } from 'lucide-react';
import { advisorApi } from '@/api/client';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  actions?: any[];
}

interface AdvisorChatViewProps {
  advisorId?: string;
  transcriptId?: string | null;
  planId?: string | null;
}

export function AdvisorChatView({
  advisorId = 'current-advisor',
  transcriptId = null,
  planId = null
}: AdvisorChatViewProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI assistant for mortgage servicing workflows. I can help you with customer requests, compliance checks, document generation, and system actions. How can I assist you today?',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

    try {
      const response = await advisorApi.chat({
        advisor_id: advisorId,
        message: messageToSend,
        session_id: sessionId || undefined,
        transcript_id: transcriptId || undefined,
        plan_id: planId || undefined
      });

      // Store session ID for conversation continuity
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        actions: response.actions
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Advisor chat API error:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const quickActions = [
    {
      icon: DollarSign,
      label: "Remove PMI",
      message: "Help me process a PMI removal request for the customer"
    },
    {
      icon: FileText,
      label: "Check Eligibility",
      message: "Check customer eligibility for loan modification or refinancing"
    },
    {
      icon: CheckCircle,
      label: "Compliance Review",
      message: "Review compliance requirements for this customer interaction"
    },
    {
      icon: Zap,
      label: "Quick Actions",
      message: "Show me quick actions I can take for this customer"
    }
  ];

  const handleClearChat = () => {
    setSessionId(null);
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content: 'Hello! I\'m your AI assistant for mortgage servicing workflows. I can help you with customer requests, compliance checks, document generation, and system actions. How can I assist you today?',
        timestamp: new Date()
      }
    ]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="page-shell">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5 text-blue-600" />
          <h1 className="text-xl font-bold">AI Assistant</h1>
          {(transcriptId || planId) && (
            <div className="flex gap-2 ml-4">
              {transcriptId && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                  Transcript: {transcriptId.slice(0, 8)}...
                </span>
              )}
              {planId && (
                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded">
                  Plan: {planId.slice(0, 8)}...
                </span>
              )}
            </div>
          )}
        </div>
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

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <div className="lg:col-span-3">
          <Card className="h-[600px] flex flex-col">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">
                Conversation
              </CardTitle>
            </CardHeader>
            <CardContent className="flex-1 flex flex-col">
              <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex gap-3 ${
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    }`}
                  >
                    {message.role === 'assistant' && (
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                          <Bot className="h-4 w-4 text-blue-600" />
                        </div>
                      </div>
                    )}
                    <div
                      className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                        message.role === 'user'
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-100 text-slate-900'
                      }`}
                    >
                      <p className="text-sm">{message.content}</p>
                      {message.actions && message.actions.length > 0 && (
                        <div className="mt-2 space-y-1">
                          <p className="text-xs text-slate-600 font-medium">Actions taken:</p>
                          {message.actions.map((action, idx) => (
                            <div key={idx} className="text-xs bg-white p-2 rounded border">
                              <span className="font-medium">{action.type}:</span> {action.description}
                            </div>
                          ))}
                        </div>
                      )}
                      <p className="text-xs mt-1 opacity-70">
                        {message.timestamp.toLocaleTimeString()}
                      </p>
                    </div>
                    {message.role === 'user' && (
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-slate-200 rounded-full flex items-center justify-center">
                          <User className="h-4 w-4 text-slate-600" />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
                {isLoading && (
                  <div className="flex gap-3 justify-start">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <Bot className="h-4 w-4 text-blue-600" />
                      </div>
                    </div>
                    <div className="bg-slate-100 px-4 py-2 rounded-lg">
                      <p className="text-sm text-slate-600">Assistant is typing...</p>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="flex gap-2">
                <Input
                  value={inputMessage}
                  onChange={(e) => setInputMessage(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me anything about customer workflows..."
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
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}