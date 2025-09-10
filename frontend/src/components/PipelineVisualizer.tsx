import React, { useState } from 'react';
import type { WorkflowState, StageStatus } from '../types/workflow';

interface PipelineVisualizerProps {
  workflowState: WorkflowState;
  onStageClick?: (stage: string) => void;
}

interface Stage {
  id: string;
  name: string;
  icon: string;
  description: string;
}

const STAGES: Stage[] = [
  { id: 'transcript', name: 'Transcript', icon: '📄', description: 'Call transcript generated' },
  { id: 'analysis', name: 'Analysis', icon: '🔍', description: 'AI sentiment & risk analysis' },
  { id: 'planning', name: 'Plan', icon: '📋', description: '4-layer action plan creation' },
  { id: 'approval', name: 'Approval', icon: '✅', description: 'Governance & approval workflow' },
  { id: 'execution', name: 'Execution', icon: '⚡', description: 'Action execution & artifacts' }
];

export function PipelineVisualizer({ workflowState, onStageClick }: PipelineVisualizerProps) {
  const [selectedStage, setSelectedStage] = useState<string | null>(null);

  const getStageStatus = (stageId: string): StageStatus => {
    switch (stageId) {
      case 'transcript':
        return workflowState.transcript ? 'complete' : 'pending';
      case 'analysis':
        return workflowState.analysis ? 'complete' : 
               workflowState.transcript ? 'pending' : 'pending';
      case 'planning':
        return workflowState.plan ? 'complete' :
               workflowState.analysis ? 'pending' : 'pending';
      case 'approval':
        return workflowState.governance?.compliance_status === 'compliant' ? 'complete' :
               workflowState.governance ? 'running' :
               workflowState.plan ? 'pending' : 'pending';
      case 'execution':
        return workflowState.execution?.status === 'completed' ? 'complete' :
               workflowState.execution?.status === 'running' ? 'running' :
               workflowState.approvals && workflowState.approvals.some(a => a.status === 'approved') ? 'pending' : 'pending';
      default:
        return 'pending';
    }
  };

  const getStageMetadata = (stageId: string) => {
    switch (stageId) {
      case 'transcript':
        return workflowState.transcript ? {
          details: [
            `ID: ${workflowState.transcript.transcript_id}`,
            `Scenario: ${workflowState.transcript.scenario}`,
            `Messages: ${workflowState.transcript.message_count}`,
            `Urgency: ${workflowState.transcript.urgency}`,
            `Financial Impact: ${workflowState.transcript.financial_impact ? 'Yes' : 'No'}`
          ]
        } : null;
      
      case 'analysis':
        return workflowState.analysis ? {
          details: [
            `Intent: ${workflowState.analysis.intent}`,
            `Sentiment: ${workflowState.analysis.sentiment}`,
            `Confidence: ${(workflowState.analysis.confidence * 100).toFixed(1)}%`,
            `Churn Risk: ${(workflowState.analysis.risk_scores.churn * 100).toFixed(1)}%`,
            `Complaint Risk: ${(workflowState.analysis.risk_scores.complaint * 100).toFixed(1)}%`
          ]
        } : null;
        
      case 'planning':
        return workflowState.plan ? {
          details: [
            `Total Actions: ${workflowState.plan.total_actions}`,
            `Risk Level: ${workflowState.plan.risk_level}`,
            `Auto Approved: ${workflowState.plan.routing_summary.auto_approved}`,
            `Advisor Approval: ${workflowState.plan.routing_summary.advisor_approval}`,
            `Supervisor Approval: ${workflowState.plan.routing_summary.supervisor_approval}`
          ]
        } : null;
        
      case 'approval':
        return workflowState.governance ? {
          details: [
            `Compliance: ${workflowState.governance.compliance_status}`,
            `Risk Level: ${workflowState.governance.risk_level}`,
            `Compliant Actions: ${workflowState.governance.compliant_actions}/${workflowState.governance.evaluated_actions}`,
            `Confidence: ${(workflowState.governance.confidence_score * 100).toFixed(1)}%`,
            `Disclosures: ${workflowState.governance.required_disclosures.length}`
          ]
        } : null;
        
      case 'execution':
        return workflowState.execution ? {
          details: [
            `Status: ${workflowState.execution.status}`,
            `Executed: ${workflowState.execution.actions_executed}`,
            `Skipped: ${workflowState.execution.actions_skipped}`,
            `Artifacts: ${workflowState.execution.artifacts_created}`,
            `Compliance Events: ${workflowState.execution.compliance_events}`
          ]
        } : null;
        
      default:
        return null;
    }
  };

  const handleStageClick = (stage: Stage) => {
    setSelectedStage(stage.id);
    onStageClick?.(stage.id);
  };

  const getStatusColorClass = (status: StageStatus): string => {
    switch (status) {
      case 'complete':
        return 'border-success-500 bg-success-50 text-success-700';
      case 'running':
        return 'border-primary-500 bg-primary-50 text-primary-700 animate-pulse';
      case 'failed':
        return 'border-error-500 bg-error-50 text-error-700';
      case 'pending':
      default:
        return 'border-gray-300 bg-gray-50 text-gray-600';
    }
  };

  const getStatusIcon = (status: StageStatus): string => {
    switch (status) {
      case 'complete':
        return '✓';
      case 'running':
        return '⏳';
      case 'failed':
        return '❌';
      case 'pending':
      default:
        return '⭕';
    }
  };

  return (
    <div className="card">
      <h2 className="text-xl font-semibold mb-6">Workflow Pipeline</h2>
      
      {/* Pipeline Stages */}
      <div className="flex items-center justify-between space-x-4 mb-6">
        {STAGES.map((stage, index) => {
          const status = getStageStatus(stage.id);
          const isActive = workflowState.currentStage === stage.id;
          
          return (
            <React.Fragment key={stage.id}>
              <div 
                className={`flex-1 cursor-pointer transition-all ${
                  isActive ? 'transform scale-105' : ''
                }`}
                onClick={() => handleStageClick(stage)}
              >
                <div className={`
                  border-2 rounded-lg p-4 text-center
                  ${getStatusColorClass(status)}
                  ${selectedStage === stage.id ? 'ring-2 ring-primary-200' : ''}
                  hover:shadow-md transition-shadow
                `}>
                  <div className="text-2xl mb-2">{stage.icon}</div>
                  <div className="font-semibold text-sm mb-1">{stage.name}</div>
                  <div className="text-xs opacity-75 mb-2">{stage.description}</div>
                  <div className="flex items-center justify-center space-x-1">
                    <span className="text-lg">{getStatusIcon(status)}</span>
                    <span className="text-xs capitalize">{status}</span>
                  </div>
                </div>
              </div>
              
              {/* Arrow */}
              {index < STAGES.length - 1 && (
                <div className="flex-shrink-0 text-gray-400">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8.59 16.59L13.17 12L8.59 7.41L10 6l6 6-6 6l-1.41-1.41z"/>
                  </svg>
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>
      
      {/* Stage Details */}
      {selectedStage && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h3 className="font-semibold mb-3">
            {STAGES.find(s => s.id === selectedStage)?.name} Details
          </h3>
          
          {(() => {
            const metadata = getStageMetadata(selectedStage);
            if (!metadata) {
              return (
                <p className="text-gray-500 text-sm">
                  No data available for this stage yet.
                </p>
              );
            }
            
            return (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {metadata.details.map((detail, index) => (
                  <div key={index} className="text-sm">
                    <span className="font-medium">{detail}</span>
                  </div>
                ))}
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
}