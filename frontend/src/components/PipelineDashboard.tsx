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
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">
              {stats.total_transcripts.toLocaleString()}
            </div>
            <div className="text-sm text-gray-600">Total Transcripts</div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">{progress}%</div>
            <div className="text-sm text-gray-600">Complete</div>
          </div>
          
          <div className="text-center">
            <div className="text-3xl font-bold text-orange-600">
              {stats.processing_time_avg}m
            </div>
            <div className="text-sm text-gray-600">Avg Processing Time</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
          <div 
            className="bg-blue-600 h-3 rounded-full transition-all duration-500"
            style={{ width: `${progress}%` }}
          ></div>
        </div>

        {/* Bottleneck Alert */}
        {bottleneck && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-center">
              <span className="text-orange-600 mr-2">⚠️</span>
              <span className="font-medium text-orange-800">
                Bottleneck Alert: High volume in {bottleneck} stage
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Stage Breakdown */}
      <div className="card">
        <h3 className="text-lg font-semibold mb-4">Stage Breakdown</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          {/* Transcript Stage */}
          <div className="stage-card">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium">📄 Transcript</span>
              <span className="text-xs text-gray-500">Stage 1</span>
            </div>
            <div className="space-y-2">
              <div 
                className="stage-count cursor-pointer hover:bg-gray-50 p-2 rounded"
                onClick={() => onStageClick('transcript', stats.stage_counts.transcript.ready)}
              >
                <div className="text-2xl font-bold text-green-600">
                  {stats.stage_counts.transcript.ready}
                </div>
                <div className="text-xs text-gray-600">Ready</div>
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