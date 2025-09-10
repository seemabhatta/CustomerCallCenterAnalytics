import { useState } from 'react';
import { TranscriptManager } from './components/TranscriptManager';
import { PipelineVisualizer } from './components/PipelineVisualizer';
import type { Transcript, WorkflowState } from './types/workflow';

function App() {
  const [workflowState, setWorkflowState] = useState<WorkflowState>({
    currentStage: 'transcript'
  });

  const handleTranscriptSelected = (transcript: Transcript) => {
    setWorkflowState(prev => ({
      ...prev,
      transcript,
      currentStage: 'analysis'
    }));
  };

  const handleStageClick = (stageId: string) => {
    console.log('Stage clicked:', stageId);
    // TODO: Handle stage-specific drill-down
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                Customer Call Center Analytics
              </h1>
              <p className="text-sm text-gray-600">
                AI-Powered Workflow Visualizer
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-500">
                Current Stage: <span className="font-semibold capitalize">{workflowState.currentStage}</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Transcript Management */}
          <TranscriptManager
            onTranscriptSelected={handleTranscriptSelected}
            selectedTranscriptId={workflowState.transcript?.transcript_id}
          />

          {/* Pipeline Visualization */}
          <PipelineVisualizer
            workflowState={workflowState}
            onStageClick={handleStageClick}
          />

          {/* Current Workflow Summary */}
          {workflowState.transcript && (
            <div className="card">
              <h2 className="text-xl font-semibold mb-4">Current Workflow</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">Transcript</h3>
                  <p className="text-sm text-gray-600">
                    {workflowState.transcript.transcript_id}
                  </p>
                  <p className="text-xs text-gray-500">
                    {workflowState.transcript.scenario}
                  </p>
                </div>
                
                {workflowState.analysis && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">Analysis</h3>
                    <p className="text-sm text-gray-600">
                      Intent: {workflowState.analysis.intent}
                    </p>
                    <p className="text-xs text-gray-500">
                      Sentiment: {workflowState.analysis.sentiment}
                    </p>
                  </div>
                )}
                
                {workflowState.plan && (
                  <div>
                    <h3 className="font-medium text-gray-700 mb-2">Action Plan</h3>
                    <p className="text-sm text-gray-600">
                      {workflowState.plan.total_actions} actions
                    </p>
                    <p className="text-xs text-gray-500">
                      Risk: {workflowState.plan.risk_level}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;