import { useState } from 'react';
import { AlertTriangle, Database, Loader2, Sparkles, Trash2 } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  useCachedInsights,
  useClearIntelligenceCache,
  useIntelligenceHealth,
} from '@/api/intelligenceHooks';
import { formatDateTime } from '@/utils/formatters';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface IntelligenceStatusBarProps {
  persona?: 'leadership' | 'servicing' | 'marketing';
  className?: string;
}

const personaLabel: Record<string, string> = {
  leadership: 'Leadership intelligence',
  servicing: 'Servicing intelligence',
  marketing: 'Marketing intelligence',
};

export const IntelligenceStatusBar = ({ persona, className }: IntelligenceStatusBarProps) => {
  const [isDialogOpen, setDialogOpen] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);

  const health = useIntelligenceHealth();
  const cachedInsights = useCachedInsights({ persona, limit: 20, enabled: isDialogOpen });
  const clearCache = useClearIntelligenceCache();

  const status = health.data?.status ?? 'loading';
  const statusBadgeClass =
    status === 'healthy'
      ? 'bg-emerald-100 text-emerald-700 border border-emerald-200'
      : 'bg-amber-100 text-amber-700 border border-amber-200';

  const handleClearCache = () => {
    clearCache.mutate(
      { persona },
      {
        onSuccess: (response) => {
          setNotice(`${response.message}`);
        },
        onError: (error) => {
          setNotice(error instanceof Error ? error.message : 'Failed to clear cache');
        },
      }
    );
  };

  const busy = clearCache.status === 'pending' || health.isLoading;

  return (
    <>
      <Card className={className ?? ''}>
        <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-3">
            <Sparkles className="h-5 w-5 text-indigo-500" />
            <div>
              <p className="text-sm font-semibold text-slate-900">
                {persona ? personaLabel[persona] : 'Intelligence fabric'}
              </p>
              <p className="text-xs text-slate-500">
                Cache hit rate and GenAI health across Prophet + LLM hybrid.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Badge className={`${statusBadgeClass} px-3 py-1 text-xs uppercase`}>
              {status === 'loading' ? 'Checking…' : status}
            </Badge>
            {health.data?.cache_statistics && (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <Database className="h-4 w-4" />
                <span>
                  {health.data.cache_statistics.active_insights ?? 0} cached /
                  {' '}
                  hit rate {Math.round((health.data.cache_statistics.hit_rate ?? 0) * 100)}%
                </span>
              </div>
            )}
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => setDialogOpen(true)}
            >
              View cached insights
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="gap-2 text-rose-600 hover:text-rose-600"
              onClick={handleClearCache}
              disabled={busy}
            >
              {clearCache.status === 'pending' ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
              Clear cache
            </Button>
          </div>
        </CardContent>
        {notice && (
          <div className="border-t border-slate-200 bg-slate-50 px-6 py-2 text-xs text-slate-500">
            {notice}
          </div>
        )}
      </Card>

      <Dialog open={isDialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Cached insights</DialogTitle>
            <DialogDescription>
              {persona
                ? `Active cache entries for the ${persona} persona`
                : 'All active cache entries'}
            </DialogDescription>
          </DialogHeader>
          <div className="max-h-[60vh] overflow-auto">
            {cachedInsights.isLoading && (
              <div className="flex items-center gap-2 p-4 text-sm text-slate-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading cached intelligence…
              </div>
            )}

            {cachedInsights.error && (
              <div className="flex items-center gap-2 rounded border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">
                <AlertTriangle className="h-4 w-4" />
                {(cachedInsights.error as Error).message}
              </div>
            )}

            {(cachedInsights.data ?? []).length === 0 && !cachedInsights.isLoading && (
              <div className="rounded border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                No active cache entries for this persona.
              </div>
            )}

            <div className="space-y-3 p-1">
              {(cachedInsights.data ?? []).map((insight) => (
                <div
                  key={insight.id}
                  className="rounded border border-slate-200 bg-white p-3 text-sm text-slate-700"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[10px] uppercase">
                        {insight.persona}
                      </Badge>
                      <span className="font-semibold text-slate-900">{insight.insight_type}</span>
                    </div>
                    <span className="text-xs text-slate-500">
                      Cached {formatDateTime(insight.generated_at)}
                    </span>
                  </div>
                  <div className="mt-2 text-xs text-slate-500">
                    Expires {formatDateTime(insight.expires_at)} • Accessed {insight.access_count}×
                  </div>
                </div>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default IntelligenceStatusBar;
