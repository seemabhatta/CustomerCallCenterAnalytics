import { useState } from 'react';
import { PipelineDashboard } from './components/PipelineDashboard';
import { ApprovalQueue } from './components/ApprovalQueue';
import { TranscriptManager } from './components/TranscriptManager';
import { usePipelineStats } from './hooks/usePipelineStats';
import type { Transcript } from './types/workflow';

function App() {
  const [showTestingPanel, setShowTestingPanel] = useState(false);
  const [currentView, setCurrentView] = useState<'dashboard' | 'approvals'>('dashboard');
  const { stats, loading, error } = usePipelineStats();

  const handleStageClick = (stage: string, count: number) => {
    console.log('Drilling down into stage:', stage, 'with count:', count);
    if (stage === 'approval') {
      setCurrentView('approvals');
    }
    // TODO: Handle other stage drill-downs
  };

  const handleTranscriptSelected = (transcript: Transcript) => {
    console.log('Test transcript selected:', transcript.transcript_id);
    // For testing purposes only
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-xl font-semibold text-red-600">Error Loading Pipeline</h1>
          <p className="text-gray-600 mt-2">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl modern-heading">
                Customer Call Center Analytics
              </h1>
              <p className="modern-subheading mt-2">
                AI-Powered Pipeline Monitoring Dashboard
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setShowTestingPanel(!showTestingPanel)}
                className="modern-button text-sm"
              >
                {showTestingPanel ? 'Hide' : 'Show'} Testing Tools
              </button>
              {loading && (
                <div className="text-sm text-gray-500">
                  ⟳ Updating...
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Conditional View Rendering */}
          {currentView === 'dashboard' && stats && (
            <>
              {/* Pipeline Dashboard */}
              <PipelineDashboard
                stats={stats}
                onStageClick={handleStageClick}
              />

              {/* Testing Panel (Collapsible) */}
              {showTestingPanel && (
                <div className="card">
                  <h3 className="text-lg font-semibold mb-4">🧪 Testing & Validation Tools</h3>
                  <p className="text-sm text-gray-600 mb-4">
                    Generate individual transcripts for testing purposes
                  </p>
                  <TranscriptManager
                    onTranscriptSelected={handleTranscriptSelected}
                    selectedTranscriptId={undefined}
                  />
                </div>
              )}
            </>
          )}

          {/* Approval Queue View */}
          {currentView === 'approvals' && (
            <ApprovalQueue
              onBack={() => setCurrentView('dashboard')}
              totalPendingCount={stats?.stage_counts.approval.pending || 0}
            />
          )}
        </div>
      </main>
    </div>
  );
}

export default App;