import type { PipelineStats } from '../types/workflow';

interface PipelineDashboardProps {
  stats: PipelineStats;
  onStageClick: (stage: string, count: number) => void;
}

export function PipelineDashboard({ stats, onStageClick }: PipelineDashboardProps) {
  const calculateProgress = () => {
    const total = stats.total_transcripts;
    const completed = stats.stage_counts.execution.completed || 0;
    return total > 0 ? Math.round((completed / total) * 100) : 0;
  };

  const findBottleneck = () => {
    const stages = stats.stage_counts;
    const pending = {
      analysis: stages.analysis.pending || 0,
      planning: stages.planning.pending || 0,
      approval: stages.approval.pending || 0,
      execution: stages.execution.running || 0, // Use 'running' instead of 'pending'
    };
    
    const maxPending = Math.max(...Object.values(pending));
    if (maxPending > 50) { // Threshold for bottleneck alert
      return Object.entries(pending).find(([_, count]) => count === maxPending)?.[0];
    }
    return null;
  };

  const progress = calculateProgress();
  const bottleneck = findBottleneck();

  return (
    <div className="space-y-6">
      {/* Batch Overview */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold">
            Pipeline Overview - {new Date().toLocaleDateString()}
          </h2>
          <div className="text-sm text-gray-500">
            Last updated: {new Date(stats.last_updated).toLocaleTimeString()}
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-100">
            <div className="metric-number text-blue-600">
              {stats.total_transcripts.toLocaleString()}
            </div>
            <div className="text-sm font-medium text-blue-700 mt-2">Total Transcripts</div>
          </div>
          
          <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 border border-green-100">
            <div className="metric-number text-green-600">{progress}%</div>
            <div className="text-sm font-medium text-green-700 mt-2">Complete</div>
          </div>
          
          <div className="text-center p-6 rounded-2xl bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-100">
            <div className="metric-number text-orange-600">
              {stats.processing_time_avg}m
            </div>
            <div className="text-sm font-medium text-orange-700 mt-2">Avg Processing Time</div>
          </div>
        </div>

        {/* Modern Progress Bar */}
        <div className="modern-progress h-3 mb-6">
          <div 
            className="modern-progress-fill"
            style={{ width: `${progress}%` }}
          ></div>
        </div>

        {/* Bottleneck Alert */}
        {bottleneck && (
          <div className="modern-alert">
            <div className="flex items-center">
              <span className="text-2xl mr-3">⚠️</span>
              <div>
                <span className="font-semibold text-orange-800 block">
                  Bottleneck Detected
                </span>
                <span className="text-orange-700 text-sm">
                  High volume in {bottleneck} stage - consider scaling resources
                </span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stage Breakdown */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Stage Breakdown</h3>
        
        <div className="modern-grid">
          {/* Transcript Stage */}
          <div className="stage-card">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">📄 Transcript</span>
              <span className="text-xs text-gray-500">Stage 1</span>
            </div>
            <div className="space-y-2">
              <div 
                className="stage-count cursor-pointer hover:bg-green-50 p-3 rounded-xl transition-all"
                onClick={() => onStageClick('transcript', stats.stage_counts.transcript.ready)}
              >
                <div className="stage-number text-green-600">
                  {stats.stage_counts.transcript.ready}
                </div>
                <div className="text-xs font-medium text-green-700 mt-1">Ready</div>
              </div>
              {stats.stage_counts.transcript.processing > 0 && (
                <div className="stage-count">
                  <div className="text-lg font-semibold text-blue-600">
                    {stats.stage_counts.transcript.processing}
                  </div>
                  <div className="text-xs text-gray-600">Processing</div>
                </div>
              )}
            </div>
          </div>

          {/* Analysis Stage */}
          <div className="stage-card">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">🔍 Analysis</span>
              <span className="text-xs text-gray-500">Stage 2</span>
            </div>
            <div className="space-y-2">
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('analysis', stats.stage_counts.analysis.pending)}
              >
                <div className="text-2xl font-bold text-orange-600">
                  {stats.stage_counts.analysis.pending}
                </div>
                <div className="text-xs text-gray-600">In Queue</div>
              </div>
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('analysis', stats.stage_counts.analysis.processing)}
              >
                <div className="text-lg font-semibold text-blue-600">
                  {stats.stage_counts.analysis.processing}
                </div>
                <div className="text-xs text-gray-600">Processing</div>
              </div>
            </div>
          </div>

          {/* Planning Stage */}
          <div className="stage-card">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">📋 Plan</span>
              <span className="text-xs text-gray-500">Stage 3</span>
            </div>
            <div className="space-y-2">
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('planning', stats.stage_counts.planning.pending)}
              >
                <div className="text-2xl font-bold text-orange-600">
                  {stats.stage_counts.planning.pending}
                </div>
                <div className="text-xs text-gray-600">Queue</div>
              </div>
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('planning', stats.stage_counts.planning.processing)}
              >
                <div className="text-lg font-semibold text-blue-600">
                  {stats.stage_counts.planning.processing}
                </div>
                <div className="text-xs text-gray-600">Generating</div>
              </div>
            </div>
          </div>

          {/* Approval Stage */}
          <div className="stage-card">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">✅ Approval</span>
              <span className="text-xs text-gray-500">Stage 4</span>
            </div>
            <div className="space-y-2">
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('approval', stats.stage_counts.approval.pending)}
              >
                <div className="text-2xl font-bold text-red-600">
                  {stats.stage_counts.approval.pending}
                </div>
                <div className="text-xs text-gray-600">Pending</div>
              </div>
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('approval', stats.stage_counts.approval.approved)}
              >
                <div className="text-lg font-semibold text-green-600">
                  {stats.stage_counts.approval.approved}
                </div>
                <div className="text-xs text-gray-600">Approved</div>
              </div>
            </div>
          </div>

          {/* Execution Stage */}
          <div className="stage-card">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">⚡ Execution</span>
              <span className="text-xs text-gray-500">Stage 5</span>
            </div>
            <div className="space-y-2">
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('execution', stats.stage_counts.execution.running)}
              >
                <div className="text-2xl font-bold text-blue-600">
                  {stats.stage_counts.execution.running}
                </div>
                <div className="text-xs text-gray-600">Running</div>
              </div>
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('execution', stats.stage_counts.execution.completed)}
              >
                <div className="text-lg font-semibold text-green-600">
                  {stats.stage_counts.execution.completed}
                </div>
                <div className="text-xs text-gray-600">Complete</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}