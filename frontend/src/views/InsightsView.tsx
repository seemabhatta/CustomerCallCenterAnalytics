import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { MessageCircle, Send, Trash2, Crown } from 'lucide-react';
import { leadershipApi } from '@/api/client';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function InsightsView() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I\'m your AI insights assistant. I can help you analyze customer call patterns, risk trends, and team performance. What would you like to know?',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentQuery = inputMessage;
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await leadershipApi.chat({
        query: currentQuery,
        executive_id: 'EXEC_001',
        executive_role: 'Manager',
        session_id: sessionId || undefined
      });

      // Store session ID for conversation continuity
      if (response.session_id && !sessionId) {
        setSessionId(response.session_id);
      }

      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat API error:', error);
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


  const quickQuestions = [
    "What are our highest risk areas?",
    "Show me team performance trends",
    "What customer issues are trending?",
    "How are resolution times looking?"
  ];

  const handleClearChat = () => {
    setSessionId(null);
    setMessages([
      {
        id: '1',
        role: 'assistant',
        content: 'Hello! I\'m your AI insights assistant. I can help you analyze customer call patterns, risk trends, and team performance. What would you like to know?',
        timestamp: new Date()
      }
    ]);
  };

  return (
    <div className="page-shell">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="view-header flex items-center gap-2">
            <Crown className="h-5 w-5 text-yellow-600" />
            Leadership Insights
          </h2>
          <p className="text-xs text-slate-500">AI-powered analysis and strategic insights</p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={handleClearChat}
          className="h-8 px-3"
        >
          <Trash2 className="h-3 w-3 mr-1" />
          Clear Chat
        </Button>
      </div>

      <Card className="panel">
        <CardHeader className="py-3 border-b">
          <CardTitle className="text-sm font-bold flex items-center gap-2">
            <MessageCircle className="h-4 w-4" />
            AI Insights Assistant
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="bg-slate-50 p-4 h-[500px] overflow-y-auto space-y-3">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-2xl px-4 py-3 rounded-lg text-sm ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-slate-200'
                }`}>
                  <div>{message.content}</div>
                  <div className={`text-xs mt-1 ${
                    message.role === 'user' ? 'text-blue-200' : 'text-slate-400'
                  }`}>
                    {message.timestamp.toLocaleTimeString()}
                  </div>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-white border border-slate-200 px-3 py-2 rounded-lg text-xs">
                  <div className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="border-t p-4 space-y-3">
            <div className="flex gap-2 flex-wrap">
              {quickQuestions.map((question, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  className="text-xs h-8"
                  onClick={() => setInputMessage(question)}
                  disabled={isLoading}
                >
                  {question}
                </Button>
              ))}
            </div>

            <div className="flex gap-2">
              <Input
                placeholder="Ask about trends, risks, team performance, customer issues..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                disabled={isLoading}
                className="text-sm h-10"
              />
              <Button
                onClick={handleSendMessage}
                disabled={isLoading || !inputMessage.trim()}
                size="sm"
                className="h-10 px-4"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}