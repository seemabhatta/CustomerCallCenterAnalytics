import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { MessageCircle, Send, Users, TrendingUp, AlertTriangle, Crown } from 'lucide-react';

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

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: getSimulatedResponse(inputMessage),
        timestamp: new Date()
      };
      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const getSimulatedResponse = (input: string): string => {
    const lowerInput = input.toLowerCase();

    if (lowerInput.includes('risk') || lowerInput.includes('high risk')) {
      return 'Based on recent analysis, I see a 15% increase in high-risk calls this month. PMI removal and hardship requests show the highest escalation rates. Would you like me to drill down into specific risk patterns?';
    }

    if (lowerInput.includes('team') || lowerInput.includes('performance')) {
      return 'Team performance metrics show advisors are resolving 78% of calls on first contact. Top performers are excelling in payment arrangement scenarios. I recommend coaching focus on escrow analysis techniques.';
    }

    if (lowerInput.includes('trend') || lowerInput.includes('pattern')) {
      return 'Key trends this quarter: 23% increase in refinancing inquiries, 8% rise in property tax disputes, and seasonal uptick in PMI removal requests. These align with current market interest rate changes.';
    }

    if (lowerInput.includes('customer') || lowerInput.includes('satisfaction')) {
      return 'Customer sentiment analysis shows 82% positive resolution rate. Main pain points: wait times for escrow analysis (avg 3.2 days) and complex PMI removal documentation. Opportunity for process streamlining exists.';
    }

    return 'I understand you\'re looking for insights. I can help analyze risk patterns, team performance, customer trends, or operational metrics. Try asking about specific areas like "What are our current risk trends?" or "How is team performance this month?"';
  };

  const quickQuestions = [
    "What are our highest risk areas?",
    "Show me team performance trends",
    "What customer issues are trending?",
    "How are resolution times looking?"
  ];

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
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 mb-4">
        <Card className="panel">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              <div>
                <div className="text-xs text-slate-600">Resolution Rate</div>
                <div className="text-lg font-bold">82%</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-orange-600" />
              <div>
                <div className="text-xs text-slate-600">High Risk Calls</div>
                <div className="text-lg font-bold">15%</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-600" />
              <div>
                <div className="text-xs text-slate-600">Team Efficiency</div>
                <div className="text-lg font-bold">78%</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="panel">
          <CardContent className="pt-4">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-4 w-4 text-purple-600" />
              <div>
                <div className="text-xs text-slate-600">Avg Response Time</div>
                <div className="text-lg font-bold">3.2d</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card className="panel">
        <CardHeader className="py-3">
          <CardTitle className="text-sm font-bold flex items-center gap-2">
            <MessageCircle className="h-4 w-4" />
            AI Insights Assistant
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-slate-50 rounded-lg p-3 h-64 overflow-y-auto space-y-3">
            {messages.map((message) => (
              <div key={message.id} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-xs px-3 py-2 rounded-lg text-xs ${
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

          <div className="space-y-3">
            <div className="flex gap-2 flex-wrap">
              {quickQuestions.map((question, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  className="text-xs h-7"
                  onClick={() => setInputMessage(question)}
                  disabled={isLoading}
                >
                  {question}
                </Button>
              ))}
            </div>

            <div className="flex gap-2">
              <Input
                placeholder="Ask about trends, risks, team performance..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                disabled={isLoading}
                className="text-xs h-8"
              />
              <Button
                onClick={handleSendMessage}
                disabled={isLoading || !inputMessage.trim()}
                size="sm"
                className="h-8 px-3"
              >
                <Send className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}