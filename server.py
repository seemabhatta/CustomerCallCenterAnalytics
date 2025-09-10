#!/usr/bin/env python3
"""
Universal Background Server - Customer Call Center Analytics
Pre-loads all heavy imports and serves multiple interfaces for instant execution.

Architecture:
- Port 9999: CLI Backend (JSON API for cli_fast.py)  
- Port 8000: FastAPI Web Interface
- Pre-loaded: OpenAI, database connections, business logic
"""
import os
import sys
import json
import asyncio
import signal
import threading
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Pre-load ALL heavy imports at startup
print("🚀 Starting Universal Server - Pre-loading imports...")
start_time = datetime.now()

# Heavy imports that cause delays
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

# Our business logic (pre-loaded)
from src.generators.transcript_generator import TranscriptGenerator
from src.storage.transcript_store import TranscriptStore
from src.models.transcript import Transcript, Message
from src.executors.smart_executor import SmartExecutor
from src.storage.execution_store import ExecutionStore
from src.agents.decision_agent import DecisionAgent
from src.storage.approval_store import ApprovalStore

# Governance components (Epic 2)
from src.governance.governance_engine import GovernanceEngine
from src.governance.audit_logger import AuditLogger
from src.governance.approval_workflow import ApprovalWorkflow
from src.governance.compliance_validator import ComplianceValidator
from src.governance.override_manager import OverrideManager
from src.storage.governance_store import GovernanceStore

print(f"✅ All imports loaded in {(datetime.now() - start_time).total_seconds():.2f}s")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances (pre-initialized)
generator: Optional[TranscriptGenerator] = None
store: Optional[TranscriptStore] = None
cli_app = None
fastapi_app = None
fastapi_thread = None
shutdown_event = threading.Event()


def init_business_logic():
    """Initialize business logic components once at startup."""
    global generator, store
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        print("🔧 Initializing business logic...")
        generator = TranscriptGenerator(api_key=api_key)
        
        # Create data directory if needed
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        store = TranscriptStore("data/call_center.db")
        
        # Initialize analysis services for API endpoints
        from src.analyzers.call_analyzer import CallAnalyzer
        from src.storage.analysis_store import AnalysisStore
        from src.generators.action_plan_generator import ActionPlanGenerator
        from src.storage.action_plan_store import ActionPlanStore
        from src.executors.smart_executor import SmartExecutor
        from src.storage.execution_store import ExecutionStore
        from src.storage.approval_store import ApprovalStore
        
        analyzer = CallAnalyzer(api_key=api_key)
        analysis_store = AnalysisStore("data/call_center.db")
        action_plan_generator = ActionPlanGenerator(db_path="data/call_center.db")
        action_plan_store = ActionPlanStore("data/call_center.db")
        smart_executor = SmartExecutor(db_path="data/call_center.db")
        execution_store = ExecutionStore("data/call_center.db")
        approval_store = ApprovalStore("data/call_center.db")
        
        # Initialize governance services (Epic 2)
        governance_engine = GovernanceEngine(api_key=api_key)
        audit_logger = AuditLogger("data/call_center.db")
        approval_workflow = ApprovalWorkflow("data/call_center.db")
        compliance_validator = ComplianceValidator(api_key=api_key)
        override_manager = OverrideManager("data/call_center.db")
        governance_store = GovernanceStore("data/call_center.db")
        
        print("✅ Business logic initialized (including governance framework)")
        
    except Exception as e:
        logger.error(f"Failed to initialize business logic: {e}")
        raise


# ========== CLI Backend (Port 9999) ==========
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse


class CLIHandler(BaseHTTPRequestHandler):
    """HTTP handler for CLI backend - serves cli_fast.py requests."""
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logs."""
        pass
    
    def do_POST(self):
        """Handle CLI commands via POST requests."""
        try:
            # Parse request
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            command = request_data.get('command')
            params = request_data.get('params', {})
            
            # Route to appropriate handler
            if command == 'generate':
                result = self.handle_generate(params)
            elif command == 'list':
                result = self.handle_list(params)
            elif command == 'get':
                result = self.handle_get(params)
            elif command == 'search':
                result = self.handle_search(params)
            elif command == 'delete':
                result = self.handle_delete(params)
            elif command == 'delete_all':
                result = self.handle_delete_all(params)
            elif command == 'stats':
                result = self.handle_stats(params)
            elif command == 'export':
                result = self.handle_export(params)
            elif command == 'demo':
                result = self.handle_demo(params)
            elif command == 'analyze':
                result = self.handle_analyze(params)
            elif command == 'analysis_report':
                result = self.handle_analysis_report(params)
            elif command == 'analysis_metrics':
                result = self.handle_analysis_metrics(params)
            elif command == 'risk_report':
                result = self.handle_risk_report(params)
            elif command == 'generate_action_plan':
                result = self.handle_generate_action_plan(params)
            elif command == 'get_action_plan':
                result = self.handle_get_action_plan(params)
            elif command == 'get_action_queue':
                result = self.handle_get_action_queue(params)
            elif command == 'approve_action_plan':
                result = self.handle_approve_action_plan(params)
            elif command == 'action_plan_summary':
                result = self.handle_action_plan_summary(params)
            elif command == 'execute_plan':
                result = self.handle_execute_plan(params)
            elif command == 'execute_plan_dry_run':
                result = self.handle_execute_plan_dry_run(params)
            elif command == 'execution_history':
                result = self.handle_execution_history(params)
            elif command == 'view_artifacts':
                result = self.handle_view_artifacts(params)
            elif command == 'execution_metrics':
                result = self.handle_execution_metrics(params)
            elif command == 'get_approval_queue':
                result = self.handle_get_approval_queue(params)
            elif command == 'approve_action':
                result = self.handle_approve_action(params)
            elif command == 'reject_action':
                result = self.handle_reject_action(params)
            elif command == 'bulk_approve_actions':
                result = self.handle_bulk_approve_actions(params)
            elif command == 'approval_metrics':
                result = self.handle_approval_metrics(params)
            elif command == 'decision_agent_summary':
                result = self.handle_decision_agent_summary(params)
            else:
                result = {'success': False, 'error': f'Unknown command: {command}'}
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result, indent=2).encode())
            
        except Exception as e:
            logger.error(f"CLI handler error: {e}")
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            error_response = {'success': False, 'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())
    
    def handle_generate(self, params):
        """Handle generate command."""
        try:
            count = params.get('count', 1)
            store_flag = params.get('store', False)
            generation_params = params.get('generation_params', {})
            
            transcripts = []
            
            if count == 1:
                transcript = generator.generate(**generation_params)
                transcripts = [transcript]
            else:
                for _ in range(count):
                    transcript = generator.generate(**generation_params)
                    transcripts.append(transcript)
            
            # Store if requested and collect IDs
            result = {
                'success': True,
                'transcripts': [t.to_dict() for t in transcripts],
                'stored': store_flag
            }
            
            if store_flag:
                transcript_ids = []
                for transcript in transcripts:
                    store.store(transcript)
                    transcript_ids.append(transcript.id)
                
                # Add transcript IDs to response when storing
                result['transcript_ids'] = transcript_ids
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_list(self, params):
        """Handle list command."""
        try:
            transcript_store = TranscriptStore('data/call_center.db')
            transcripts = transcript_store.get_all()
            return {
                'success': True,
                'transcripts': [t.to_dict() for t in transcripts]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_get(self, params):
        """Handle get command."""
        try:
            transcript_id = params.get('transcript_id')
            if not transcript_id:
                return {'success': False, 'error': 'transcript_id required'}
            
            transcript_store = TranscriptStore('data/call_center.db')
            transcript = transcript_store.get_by_id(transcript_id)
            if not transcript:
                return {'success': False, 'error': f'Transcript {transcript_id} not found'}
            
            return {
                'success': True,
                'transcript': transcript.to_dict()
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_search(self, params):
        """Handle search command."""
        try:
            transcript_store = TranscriptStore('data/call_center.db')
            
            customer = params.get('customer')
            topic = params.get('topic')
            text = params.get('text')
            
            if customer:
                results = transcript_store.search_by_customer(customer)
            elif topic:
                results = transcript_store.search_by_topic(topic)
            elif text:
                results = transcript_store.search_by_text(text)
            else:
                return {'success': False, 'error': 'Must specify customer, topic, or text'}
            
            return {
                'success': True,
                'transcripts': [t.to_dict() for t in results]
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_delete(self, params):
        """Handle delete command."""
        try:
            transcript_store = TranscriptStore('data/call_center.db')
            
            transcript_id = params.get('transcript_id')
            if not transcript_id:
                return {'success': False, 'error': 'transcript_id required'}
            
            result = transcript_store.delete(transcript_id)
            if result:
                return {'success': True, 'message': f'Deleted transcript {transcript_id}'}
            else:
                return {'success': False, 'error': f'Transcript {transcript_id} not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_delete_all(self, params):
        """Handle delete all command."""
        try:
            transcript_store = TranscriptStore('data/call_center.db')
            
            # Get count before deletion for confirmation
            count = transcript_store.delete_all()
            
            if count > 0:
                return {'success': True, 'message': f'Deleted {count} transcripts', 'count': count}
            else:
                return {'success': True, 'message': 'No transcripts to delete', 'count': 0}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_stats(self, params):
        """Handle stats command."""
        try:
            transcripts = store.get_all()
            
            if not transcripts:
                return {
                    'success': True,
                    'stats': {
                        'total_transcripts': 0,
                        'total_messages': 0,
                        'unique_customers': 0,
                        'avg_messages_per_transcript': 0.0,
                        'top_topics': {},
                        'sentiments': {},
                        'speakers': {}
                    }
                }
            
            total = len(transcripts)
            total_messages = sum(len(t.messages) for t in transcripts)
            
            # Collect statistics
            customers = set()
            topics = {}
            sentiments = {}
            speakers = {}
            
            for transcript in transcripts:
                # Customer IDs
                if hasattr(transcript, 'customer_id'):
                    customers.add(transcript.customer_id)
                
                # Topics/scenarios
                topic = getattr(transcript, 'topic', getattr(transcript, 'scenario', 'Unknown'))
                topics[topic] = topics.get(topic, 0) + 1
                
                # Sentiments
                sentiment = getattr(transcript, 'sentiment', 'Unknown')
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
                
                # Speakers
                for msg in transcript.messages:
                    speakers[msg.speaker] = speakers.get(msg.speaker, 0) + 1
            
            return {
                'success': True,
                'stats': {
                    'total_transcripts': total,
                    'total_messages': total_messages,
                    'unique_customers': len(customers),
                    'avg_messages_per_transcript': total_messages/total,
                    'top_topics': dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]),
                    'sentiments': sentiments,
                    'speakers': dict(sorted(speakers.items(), key=lambda x: x[1], reverse=True)[:10])
                }
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_export(self, params):
        """Handle export command."""
        try:
            transcripts = store.get_all()
            
            if not transcripts:
                return {'success': False, 'error': 'No transcripts to export'}
            
            output_file = params.get('output', 'transcripts_export.json')
            
            # Convert to dictionaries
            data = {
                "exported_at": datetime.now().isoformat(),
                "count": len(transcripts),
                "transcripts": [t.to_dict() for t in transcripts]
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return {
                'success': True,
                'message': f'Exported {len(transcripts)} transcripts to {output_file}',
                'file': output_file
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_demo(self, params):
        """Handle demo command."""
        try:
            no_store = params.get('no_store', False)
            
            scenarios = [
                {"scenario": "escrow_shortage", "customer_id": "DEMO_001"},
                {"scenario": "payment_dispute", "customer_id": "DEMO_002"},
                {"scenario": "refinance_inquiry", "customer_id": "DEMO_003"},
            ]
            
            transcripts = []
            for scenario_params in scenarios:
                transcript = generator.generate(**scenario_params)
                transcripts.append(transcript)
                
                if not no_store:
                    store.store(transcript)
            
            return {
                'success': True,
                'message': f'Generated {len(scenarios)} demo transcripts',
                'transcripts': [t.to_dict() for t in transcripts],
                'stored': not no_store
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_analyze(self, params):
        """Handle analyze command."""
        try:
            from src.analyzers.call_analyzer import CallAnalyzer
            from src.storage.analysis_store import AnalysisStore
            
            transcript_id = params.get('transcript_id')
            all_transcripts = params.get('all_transcripts', False)
            
            analyzer = CallAnalyzer()
            analysis_store = AnalysisStore('data/call_center.db')
            transcript_store = TranscriptStore('data/call_center.db')
            
            analyzed_count = 0
            
            if all_transcripts:
                # Analyze all transcripts
                all_transcripts_list = transcript_store.get_all()
                for transcript in all_transcripts_list:
                    analysis = analyzer.analyze(transcript)
                    analysis_store.store(analysis)
                    analyzed_count += 1
            elif transcript_id:
                # Analyze specific transcript
                transcript = transcript_store.get_by_id(transcript_id)
                if not transcript:
                    return {'success': False, 'error': f'Transcript {transcript_id} not found'}
                
                analysis = analyzer.analyze(transcript)
                analysis_store.store(analysis)
                analyzed_count = 1
            else:
                return {'success': False, 'error': 'Must specify either --transcript-id or --all'}
            
            result = {
                'success': True,
                'message': f'Analyzed {analyzed_count} transcript(s)',
                'count': analyzed_count
            }
            
            # Add analysis details for debugging
            if transcript_id and analyzed_count > 0:
                try:
                    # Get the stored analysis to show details
                    analysis = analysis_store.get_by_transcript_id(transcript_id)
                    if analysis:
                        result['analysis_preview'] = {
                            'analysis_id': analysis.get('analysis_id', 'N/A'),
                            'primary_intent': analysis.get('primary_intent', 'N/A'),
                            'urgency_level': analysis.get('urgency_level', 'N/A'),
                            'sentiment': analysis.get('borrower_sentiment', {}).get('overall', 'N/A'),
                            'confidence_score': analysis.get('confidence_score', 'N/A')
                        }
                    else:
                        result['analysis_note'] = 'Analysis completed but not found in storage'
                except Exception as e:
                    result['analysis_error'] = f'Error retrieving analysis: {str(e)}'
            
            return result
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_analysis_report(self, params):
        """Handle analysis-report command."""
        try:
            from src.storage.analysis_store import AnalysisStore
            
            transcript_id = params.get('transcript_id')
            analysis_id = params.get('analysis_id')
            
            analysis_store = AnalysisStore('data/call_center.db')
            
            if analysis_id:
                analysis = analysis_store.get_by_id(analysis_id)
            elif transcript_id:
                analysis = analysis_store.get_by_transcript_id(transcript_id)
            else:
                return {'success': False, 'error': 'Must specify either --transcript-id or --analysis-id'}
            
            if not analysis:
                return {'success': False, 'error': 'Analysis not found'}
            
            return {
                'success': True,
                'analysis': analysis
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_analysis_metrics(self, params):
        """Handle analysis-metrics command."""
        try:
            from src.storage.analysis_store import AnalysisStore
            
            analysis_store = AnalysisStore('data/call_center.db')
            metrics = analysis_store.get_metrics_summary()
            
            return {
                'success': True,
                'metrics': metrics
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_risk_report(self, params):
        """Handle risk-report command."""
        try:
            from src.storage.analysis_store import AnalysisStore
            
            threshold = float(params.get('threshold', 0.7))
            analysis_store = AnalysisStore('data/call_center.db')
            high_risk = analysis_store.get_risk_reports(threshold)
            
            return {
                'success': True,
                'high_risk_analyses': high_risk,
                'threshold': threshold,
                'count': len(high_risk)
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_generate_action_plan(self, params):
        """Handle generate-action-plan command."""
        try:
            from src.generators.action_plan_generator import ActionPlanGenerator
            from src.storage.action_plan_store import ActionPlanStore
            from src.storage.analysis_store import AnalysisStore
            
            transcript_id = params.get('transcript_id')
            if not transcript_id:
                return {'success': False, 'error': 'transcript_id required'}
            
            # Get transcript
            transcript_store = TranscriptStore('data/call_center.db')
            transcript = transcript_store.get_by_id(transcript_id)
            if not transcript:
                return {'success': False, 'error': f'Transcript {transcript_id} not found'}
            
            # Get analysis
            analysis_store = AnalysisStore('data/call_center.db')
            analysis = analysis_store.get_by_transcript_id(transcript_id)
            if not analysis:
                return {'success': False, 'error': f'Analysis for transcript {transcript_id} not found. Run analyze first.'}
            
            # Generate action plan
            generator = ActionPlanGenerator(db_path='data/call_center.db')
            action_plan = generator.generate(analysis, transcript)
            
            # Store action plan
            plan_store = ActionPlanStore('data/call_center.db')
            plan_id = plan_store.store(action_plan)
            
            return {
                'success': True,
                'message': f'Generated action plan {plan_id} for transcript {transcript_id}',
                'plan_id': plan_id,
                'risk_level': action_plan.get('risk_level'),
                'approval_route': action_plan.get('approval_route'),
                'queue_status': action_plan.get('queue_status')
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_get_action_plan(self, params):
        """Handle get-action-plan command."""
        try:
            from src.storage.action_plan_store import ActionPlanStore
            
            plan_id = params.get('plan_id')
            transcript_id = params.get('transcript_id')
            
            if not plan_id and not transcript_id:
                return {'success': False, 'error': 'Must specify either --plan-id or --transcript-id'}
            
            plan_store = ActionPlanStore('data/call_center.db')
            
            if plan_id:
                plan = plan_store.get_by_id(plan_id)
            else:
                plan = plan_store.get_by_transcript_id(transcript_id)
            
            if not plan:
                return {'success': False, 'error': 'Action plan not found'}
            
            return {
                'success': True,
                'action_plan': plan
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_get_action_queue(self, params):
        """Handle get-action-queue command."""
        try:
            from src.storage.action_plan_store import ActionPlanStore
            
            status = params.get('status')
            
            plan_store = ActionPlanStore('data/call_center.db')
            plans = plan_store.get_approval_queue(status)
            
            return {
                'success': True,
                'plans': plans,
                'count': len(plans),
                'status_filter': status
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_approve_action_plan(self, params):
        """Handle approve-action-plan command."""
        try:
            from src.storage.action_plan_store import ActionPlanStore
            
            plan_id = params.get('plan_id')
            approved_by = params.get('approved_by')
            action = params.get('action', 'approve')
            
            if not plan_id:
                return {'success': False, 'error': 'plan_id required'}
            if not approved_by:
                return {'success': False, 'error': 'approved_by required'}
            
            plan_store = ActionPlanStore('data/call_center.db')
            
            if action == 'approve':
                result = plan_store.approve_plan(plan_id, approved_by)
                action_msg = 'approved'
            elif action == 'reject':
                result = plan_store.reject_plan(plan_id, approved_by)
                action_msg = 'rejected'
            else:
                return {'success': False, 'error': 'action must be "approve" or "reject"'}
            
            if result:
                return {
                    'success': True,
                    'message': f'Action plan {plan_id} {action_msg} by {approved_by}',
                    'plan_id': plan_id,
                    'action': action,
                    'approved_by': approved_by
                }
            else:
                return {'success': False, 'error': f'Failed to {action} action plan {plan_id}'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_action_plan_summary(self, params):
        """Handle action-plan-summary command."""
        try:
            from src.storage.action_plan_store import ActionPlanStore
            
            plan_store = ActionPlanStore('data/call_center.db')
            metrics = plan_store.get_summary_metrics()
            
            return {
                'success': True,
                'summary': metrics
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_execute_plan(self, params):
        """Handle execute-plan command."""
        try:
            from src.executors.smart_executor import SmartExecutor
            from src.storage.execution_store import ExecutionStore
            
            plan_id = params.get('plan_id')
            mode = params.get('mode', 'auto')
            
            if not plan_id:
                return {'success': False, 'error': 'plan_id is required'}
            
            # Execute the plan
            executor = SmartExecutor(db_path='data/call_center.db')
            execution_result = executor.execute_action_plan(plan_id, mode)
            
            # Store execution history if successful
            if execution_result.get('status') == 'success':
                execution_store = ExecutionStore()
                execution_store.store_execution(execution_result)
            
            return {
                'success': True,
                'execution_result': execution_result
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_execute_plan_dry_run(self, params):
        """Handle execute-plan dry-run command - shows what would be executed without actual execution."""
        try:
            from src.storage.action_plan_store import ActionPlanStore
            
            plan_id = params.get('plan_id')
            
            if not plan_id:
                return {'success': False, 'error': 'plan_id is required'}
            
            # Get the action plan to show what would be executed
            plan_store = ActionPlanStore('data/call_center.db')
            plan = plan_store.get_by_id(plan_id)
            
            if not plan:
                return {'success': False, 'error': f'Action plan {plan_id} not found'}
            
            # Count actions that would be executed (simplified approach)
            total_actions = 0
            actions_by_layer = {}
            
            # Count borrower actions (these are usually strings or simple objects)
            borrower_count = 0
            if 'borrower_plan' in plan:
                immediate = plan['borrower_plan'].get('immediate_actions', [])
                followup = plan['borrower_plan'].get('follow_up_actions', [])
                borrower_count = len(immediate) + len(followup)
                
            # Count other layer actions
            advisor_count = 0
            if 'advisor_plan' in plan:
                coaching = plan['advisor_plan'].get('coaching_items', [])
                advisor_count = len(coaching)
                
            supervisor_count = 0
            if 'supervisor_plan' in plan:
                escalation = plan['supervisor_plan'].get('escalation_items', [])
                supervisor_count = len(escalation)
                
            leadership_count = 0
            if 'leadership_plan' in plan:
                strategic = plan['leadership_plan'].get('strategic_opportunities', [])
                leadership_count = len(strategic)
            
            # Set action counts
            actions_by_layer = {
                'borrower': borrower_count,
                'advisor': advisor_count,
                'supervisor': supervisor_count,
                'leadership': leadership_count
            }
            total_actions = sum(actions_by_layer.values())
            
            # Simulate what artifacts would be created
            estimated_artifacts = {
                'emails': total_actions * 0.6,  # ~60% of actions generate emails
                'documents': total_actions * 0.2,  # ~20% generate documents 
                'callbacks': total_actions * 0.3  # ~30% generate callbacks
            }
            
            return {
                'success': True,
                'dry_run_result': {
                    'plan_id': plan_id,
                    'mode': 'dry_run',
                    'total_actions_would_execute': total_actions,
                    'actions_by_layer': actions_by_layer,
                    'estimated_artifacts': estimated_artifacts,
                    'note': 'This is a simulation - no actual execution or artifacts created'
                }
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_execution_history(self, params):
        """Handle execution-history command."""
        try:
            from src.storage.execution_store import ExecutionStore
            
            limit = params.get('limit', 10)
            execution_store = ExecutionStore()
            executions = execution_store.get_recent_executions(limit)
            
            return {
                'success': True,
                'executions': executions
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_view_artifacts(self, params):
        """Handle view-artifacts command."""
        try:
            import os
            from pathlib import Path
            
            artifact_type = params.get('type', 'all')
            limit = params.get('limit', 10)
            
            artifacts = []
            base_path = Path("data")
            
            # Determine which directories to scan
            if artifact_type == 'all':
                dirs_to_scan = ['emails', 'callbacks', 'documents']
            elif artifact_type in ['emails', 'callbacks', 'documents']:
                dirs_to_scan = [artifact_type]
            else:
                return {'success': False, 'error': f'Invalid artifact type: {artifact_type}'}
            
            # Scan directories for files
            for dir_name in dirs_to_scan:
                dir_path = base_path / dir_name
                if dir_path.exists():
                    for file_path in dir_path.iterdir():
                        if file_path.is_file():
                            try:
                                stat = file_path.stat()
                                # Read first 200 chars for preview
                                preview = ""
                                if file_path.suffix == '.txt':
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        preview = f.read(200)
                                
                                artifacts.append({
                                    'filename': file_path.name,
                                    'type': dir_name,
                                    'path': str(file_path),
                                    'size': stat.st_size,
                                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                                    'preview': preview
                                })
                            except Exception:
                                continue  # Skip files we can't read
            
            # Sort by creation time (newest first) and limit
            artifacts.sort(key=lambda x: x['created'], reverse=True)
            artifacts = artifacts[:limit]
            
            return {
                'success': True,
                'artifacts': artifacts
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_execution_metrics(self, params):
        """Handle execution-metrics command."""
        try:
            from src.storage.execution_store import ExecutionStore
            
            execution_store = ExecutionStore()
            stats = execution_store.get_execution_stats(days=7)
            
            return {
                'success': True,
                'stats': stats
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_get_approval_queue(self, params):
        """Handle get-approval-queue command."""
        try:
            approval_store = ApprovalStore("data/call_center.db")
            
            route = params.get('route')  # advisor_approval, supervisor_approval, or None for all
            queue = approval_store.get_approval_queue(route)
            
            return {
                'success': True,
                'queue': queue,
                'total_pending': len(queue)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_approve_action(self, params):
        """Handle approve-action command."""
        try:
            action_id = params.get('action_id')
            if not action_id:
                return {'success': False, 'error': 'action_id is required'}
            
            approved_by = params.get('approved_by', 'CLI_USER')
            notes = params.get('notes', '')
            
            approval_store = ApprovalStore("data/call_center.db")
            success = approval_store.approve_action(action_id, approved_by, notes)
            
            if success:
                return {
                    'success': True,
                    'message': f'Action {action_id} approved by {approved_by}'
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to approve action {action_id}. May already be processed.'
                }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_reject_action(self, params):
        """Handle reject-action command."""
        try:
            action_id = params.get('action_id')
            if not action_id:
                return {'success': False, 'error': 'action_id is required'}
            
            rejected_by = params.get('rejected_by', 'CLI_USER')
            reason = params.get('reason', 'No reason provided')
            
            approval_store = ApprovalStore("data/call_center.db")
            success = approval_store.reject_action(action_id, rejected_by, reason)
            
            if success:
                return {
                    'success': True,
                    'message': f'Action {action_id} rejected by {rejected_by}',
                    'reason': reason
                }
            else:
                return {
                    'success': False,
                    'error': f'Failed to reject action {action_id}. May already be processed.'
                }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_bulk_approve_actions(self, params):
        """Handle bulk-approve-actions command."""
        try:
            action_ids = params.get('action_ids', [])
            if not action_ids:
                return {'success': False, 'error': 'action_ids list is required'}
            
            approved_by = params.get('approved_by', 'CLI_USER')
            notes = params.get('notes', 'Bulk approval')
            
            approval_store = ApprovalStore("data/call_center.db")
            approved_count = approval_store.bulk_approve(action_ids, approved_by, notes)
            
            return {
                'success': True,
                'approved_count': approved_count,
                'total_requested': len(action_ids),
                'message': f'Bulk approved {approved_count}/{len(action_ids)} actions'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_approval_metrics(self, params):
        """Handle approval-metrics command."""
        try:
            approval_store = ApprovalStore("data/call_center.db")
            metrics = approval_store.get_approval_metrics()
            
            return {
                'success': True,
                'metrics': metrics
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_decision_agent_summary(self, params):
        """Handle decision-agent-summary command."""
        try:
            # Note: In a real implementation, we'd maintain a global decision agent instance
            # For now, we'll create a new one and return its configuration
            decision_agent = DecisionAgent()
            
            summary = {
                'agent_version': 'v1.0',
                'config': decision_agent.config,
                'summary': decision_agent.get_decision_summary()
            }
            
            return {
                'success': True,
                'summary': summary
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}


def start_cli_server():
    """Start CLI backend server on port 9999 (with fallback ports)."""
    global cli_app
    
    # Try multiple ports in case 9999 is busy
    ports_to_try = [9999, 9998, 9997, 9996]
    
    for port in ports_to_try:
        try:
            cli_app = HTTPServer(('localhost', port), CLIHandler)
            print(f"🖥️  CLI Backend ready on http://localhost:{port}")
            if port != 9999:
                print(f"⚠️  Note: Using alternate port {port} (9999 was busy)")
                print(f"    Update CLI_SERVER_URL in cli_fast.py to http://localhost:{port}")
            
            # Serve with periodic shutdown check
            while not shutdown_event.is_set():
                cli_app.timeout = 1  # Check every 1 second
                cli_app.handle_request()
            return
            
        except OSError as e:
            if "Address already in use" in str(e):
                logger.warning(f"Port {port} is busy, trying next port...")
                continue
            else:
                logger.error(f"CLI server error on port {port}: {e}")
                break
        except Exception as e:
            logger.error(f"CLI server error on port {port}: {e}")
            break
    
    logger.error("❌ Failed to start CLI backend on any port. Try running ./cleanup.sh first.")
    print("❌ CLI Backend failed to start. FastAPI will still work on port 8000.")


# ========== FastAPI Web Interface (Port 8000) ==========

# Reuse existing Pydantic models from api.py
class GenerateRequest(BaseModel):
    scenario: Optional[str] = Field(None, description="Conversation scenario")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    sentiment: Optional[str] = Field(None, description="Customer sentiment")
    urgency: Optional[str] = Field(None, description="Urgency level")
    
    class Config:
        extra = "allow"


class TranscriptResponse(BaseModel):
    id: str
    timestamp: str
    messages: list
    # Dynamic attributes included as dict


class SearchResponse(BaseModel):
    count: int
    transcripts: list


class StatsResponse(BaseModel):
    total_transcripts: int
    total_messages: int
    unique_customers: int
    avg_messages_per_transcript: float
    top_topics: Dict[str, int]
    sentiments: Dict[str, int]


def create_fastapi_app():
    """Create FastAPI application using pre-loaded business logic."""
    app = FastAPI(
        title="Customer Call Center Analytics API",
        description="REST API for generating and managing call center transcripts",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    @app.get("/")
    async def root():
        return {
            "name": "Customer Call Center Analytics API",
            "version": "1.0.0",
            "description": "Generate and manage call center transcripts",
            "server_mode": "universal_server",
            "cli_backend": "http://localhost:9999",
            "endpoints": {
                "docs": "/docs",
                "generate": "/generate",
                "transcripts": "/transcripts",
                "search": "/transcripts/search",
                "stats": "/stats"
            }
        }
    
    @app.post("/generate", response_model=TranscriptResponse)
    async def generate_transcript(request: GenerateRequest):
        try:
            params = request.dict(exclude_none=True, exclude_unset=True)
            transcript = generator.generate(**params)
            
            return TranscriptResponse(
                id=transcript.id,
                timestamp=getattr(transcript, 'timestamp', ''),
                messages=[msg.to_dict() for msg in transcript.messages]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")
    
    @app.get("/transcripts")
    async def list_transcripts(limit: int = Query(100, ge=1, le=1000)):
        try:
            transcripts = store.get_all()[:limit]
            return [
                TranscriptResponse(
                    id=t.id,
                    timestamp=getattr(t, 'timestamp', ''),
                    messages=[msg.to_dict() for msg in t.messages]
                )
                for t in transcripts
            ]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to list transcripts: {str(e)}")
    
    @app.get("/transcripts/{transcript_id}", response_model=TranscriptResponse)
    async def get_transcript(transcript_id: str):
        try:
            transcript = store.get_by_id(transcript_id)
            if not transcript:
                raise HTTPException(status_code=404, detail="Transcript not found")
            
            return TranscriptResponse(
                id=transcript.id,
                timestamp=getattr(transcript, 'timestamp', ''),
                messages=[msg.to_dict() for msg in transcript.messages]
            )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get transcript: {str(e)}")
    
    @app.delete("/transcripts/{transcript_id}")
    async def delete_transcript(transcript_id: str):
        try:
            result = store.delete(transcript_id)
            if not result:
                raise HTTPException(status_code=404, detail="Transcript not found")
            return {"message": f"Deleted transcript {transcript_id}"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to delete transcript: {str(e)}")
    
    @app.get("/transcripts/search", response_model=SearchResponse)
    async def search_transcripts(
        customer: Optional[str] = Query(None, description="Search by customer ID"),
        topic: Optional[str] = Query(None, description="Search by topic"),
        text: Optional[str] = Query(None, description="Search by text content")
    ):
        if not any([customer, topic, text]):
            raise HTTPException(
                status_code=400,
                detail="Please provide at least one search parameter: customer, topic, or text"
            )
        
        try:
            if customer:
                results = store.search_by_customer(customer)
            elif topic:
                results = store.search_by_topic(topic)
            elif text:
                results = store.search_by_text(text)
            else:
                results = []
            
            return SearchResponse(
                count=len(results),
                transcripts=[
                    TranscriptResponse(
                        id=t.id,
                        timestamp=getattr(t, 'timestamp', ''),
                        messages=[msg.to_dict() for msg in t.messages]
                    )
                    for t in results
                ]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
    
    @app.get("/stats", response_model=StatsResponse)
    async def get_statistics():
        try:
            transcripts = store.get_all()
            
            if not transcripts:
                return StatsResponse(
                    total_transcripts=0,
                    total_messages=0,
                    unique_customers=0,
                    avg_messages_per_transcript=0.0,
                    top_topics={},
                    sentiments={}
                )
            
            total = len(transcripts)
            total_messages = sum(len(t.messages) for t in transcripts)
            
            customers = set()
            topics = {}
            sentiments = {}
            
            for transcript in transcripts:
                if hasattr(transcript, 'customer_id'):
                    customers.add(transcript.customer_id)
                
                topic = getattr(transcript, 'topic', getattr(transcript, 'scenario', 'Unknown'))
                topics[topic] = topics.get(topic, 0) + 1
                
                sentiment = getattr(transcript, 'sentiment', 'Unknown')
                sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            
            return StatsResponse(
                total_transcripts=total,
                total_messages=total_messages,
                unique_customers=len(customers),
                avg_messages_per_transcript=total_messages/total,
                top_topics=dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:10]),
                sentiments=sentiments
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate statistics: {str(e)}")
    
    @app.get("/health")
    async def health_check():
        try:
            store.get_all()  # Simple database query
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "database": "connected",
                "server_mode": "universal_server"
            }
        except Exception as e:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "error": str(e)
                }
            )
    
    # ===============================================
    # ANALYSIS API ENDPOINTS (Epic 13)
    # ===============================================
    
    @app.post("/api/v1/analysis/analyze")
    async def analyze_transcript_api(request: dict):
        """Analyze transcript(s) via API."""
        try:
            # Handle single transcript
            if "transcript_id" in request:
                transcript_id = request["transcript_id"]
                transcript = store.get_by_id(transcript_id)
                if not transcript:
                    raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
                
                analysis = analyzer.analyze(transcript)
                stored_analysis = analysis_store.store(analysis)
                
                return {
                    "analysis_id": stored_analysis["id"],
                    "intent": stored_analysis.get("intent"),
                    "urgency": stored_analysis.get("urgency"), 
                    "sentiment": stored_analysis.get("sentiment"),
                    "confidence": stored_analysis.get("confidence")
                }
            
            # Handle multiple transcripts
            elif "transcript_ids" in request:
                analyses = []
                for transcript_id in request["transcript_ids"]:
                    transcript = store.get_by_id(transcript_id)
                    if transcript:
                        analysis = analyzer.analyze(transcript)
                        stored_analysis = analysis_store.store(analysis)
                        analyses.append({
                            "transcript_id": transcript_id,
                            "analysis_id": stored_analysis["id"],
                            "intent": stored_analysis.get("intent"),
                            "urgency": stored_analysis.get("urgency"),
                            "sentiment": stored_analysis.get("sentiment"),
                            "confidence": stored_analysis.get("confidence")
                        })
                return {"analyses": analyses}
            
            else:
                raise HTTPException(status_code=400, detail="transcript_id or transcript_ids required")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    
    @app.get("/api/v1/analysis/{analysis_id}")
    async def get_analysis_by_id(analysis_id: str):
        """Get analysis results by ID."""
        try:
            analysis = analysis_store.get_by_id(analysis_id)
            if not analysis:
                raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
            
            return {
                "analysis_id": analysis_id,
                "intent": analysis.get("intent"),
                "sentiment": analysis.get("sentiment"),
                "risk_scores": {
                    "delinquency": analysis.get("borrower_risk", {}).get("delinquency_risk", 0),
                    "churn": analysis.get("borrower_risk", {}).get("churn_risk", 0),
                    "complaint": analysis.get("borrower_risk", {}).get("complaint_risk", 0),
                    "refinance": analysis.get("borrower_risk", {}).get("refinance_risk", 0)
                },
                "advisor_metrics": analysis.get("advisor_metrics", {}),
                "call_summary": analysis.get("call_summary", "")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get analysis: {str(e)}")
    
    @app.get("/api/v1/analysis/metrics")
    async def get_analysis_metrics():
        """Get analysis performance metrics."""
        try:
            analyses = analysis_store.get_all()
            total_analyses = len(analyses)
            
            if total_analyses == 0:
                return {
                    "total_analyses": 0,
                    "average_confidence": 0.0,
                    "resolution_rate": 0.0,
                    "risk_distribution": {"high_delinquency": 0, "high_churn": 0, "high_complaint": 0},
                    "intent_distribution": {},
                    "urgency_distribution": {}
                }
            
            # Calculate metrics
            avg_confidence = sum(float(a.get("confidence", 0)) for a in analyses) / total_analyses
            resolution_rate = sum(1 for a in analyses if a.get("resolution_status") == "resolved") / total_analyses
            
            # Count high risk cases
            high_delinquency = sum(1 for a in analyses if a.get("borrower_risk", {}).get("delinquency_risk", 0) > 0.7)
            high_churn = sum(1 for a in analyses if a.get("borrower_risk", {}).get("churn_risk", 0) > 0.7)
            high_complaint = sum(1 for a in analyses if a.get("borrower_risk", {}).get("complaint_risk", 0) > 0.7)
            
            # Count intents and urgency
            intents = {}
            urgency = {}
            for a in analyses:
                intent = a.get("intent", "Unknown")
                intents[intent] = intents.get(intent, 0) + 1
                
                urg = a.get("urgency", "Unknown")
                urgency[urg] = urgency.get(urg, 0) + 1
            
            return {
                "total_analyses": total_analyses,
                "average_confidence": round(avg_confidence, 3),
                "resolution_rate": round(resolution_rate, 3),
                "risk_distribution": {
                    "high_delinquency": high_delinquency,
                    "high_churn": high_churn,
                    "high_complaint": high_complaint
                },
                "intent_distribution": intents,
                "urgency_distribution": urgency
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
    
    @app.get("/api/v1/analysis/report/{analysis_id}")
    async def get_analysis_report(analysis_id: str):
        """Get detailed analysis report."""
        try:
            analysis = analysis_store.get_by_id(analysis_id)
            if not analysis:
                raise HTTPException(status_code=404, detail=f"Analysis {analysis_id} not found")
            
            borrower_risk = analysis.get("borrower_risk", {})
            advisor_metrics = analysis.get("advisor_metrics", {})
            
            return {
                "call_summary": analysis.get("call_summary", ""),
                "borrower_profile": {
                    "sentiment_start": analysis.get("sentiment_progression", {}).get("start", ""),
                    "sentiment_end": analysis.get("sentiment_progression", {}).get("end", ""),
                    "risk_scores": {
                        "delinquency": borrower_risk.get("delinquency_risk", 0),
                        "churn": borrower_risk.get("churn_risk", 0),
                        "complaint": borrower_risk.get("complaint_risk", 0),
                        "refinance": borrower_risk.get("refinance_risk", 0)
                    }
                },
                "advisor_performance": {
                    "empathy_score": advisor_metrics.get("empathy_score", 0),
                    "compliance_adherence": advisor_metrics.get("compliance_adherence", 0),
                    "solution_effectiveness": advisor_metrics.get("solution_effectiveness", 0)
                },
                "compliance_flags": analysis.get("compliance_flags", []),
                "resolution_status": analysis.get("resolution_status", "pending")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")
    
    @app.get("/api/v1/analysis/risk-report")
    async def get_risk_report(threshold: float = 0.7):
        """Get high-risk borrower report."""
        try:
            analyses = analysis_store.get_all()
            high_risk_cases = []
            delinquency_cases = []
            churn_cases = []
            complaint_cases = []
            
            for analysis in analyses:
                borrower_risk = analysis.get("borrower_risk", {})
                delinq_risk = borrower_risk.get("delinquency_risk", 0)
                churn_risk = borrower_risk.get("churn_risk", 0)
                complaint_risk = borrower_risk.get("complaint_risk", 0)
                
                case_info = {
                    "transcript_id": analysis.get("transcript_id"),
                    "analysis_id": analysis.get("id"),
                    "intent": analysis.get("intent"),
                    "call_summary": analysis.get("call_summary", "")[:100] + "..."
                }
                
                if delinq_risk >= threshold:
                    delinquency_cases.append({**case_info, "risk_score": delinq_risk})
                    high_risk_cases.append({**case_info, "risk_type": "delinquency", "risk_score": delinq_risk})
                
                if churn_risk >= threshold:
                    churn_cases.append({**case_info, "risk_score": churn_risk})
                    if not any(c["analysis_id"] == case_info["analysis_id"] for c in high_risk_cases):
                        high_risk_cases.append({**case_info, "risk_type": "churn", "risk_score": churn_risk})
                
                if complaint_risk >= threshold:
                    complaint_cases.append({**case_info, "risk_score": complaint_risk})
                    if not any(c["analysis_id"] == case_info["analysis_id"] for c in high_risk_cases):
                        high_risk_cases.append({**case_info, "risk_type": "complaint", "risk_score": complaint_risk})
            
            return {
                "high_risk_borrowers": high_risk_cases,
                "risk_categories": {
                    "delinquency": delinquency_cases,
                    "churn": churn_cases,
                    "complaint": complaint_cases
                },
                "total_count": len(high_risk_cases),
                "threshold_used": threshold
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to generate risk report: {str(e)}")
    
    # ===============================================
    # ACTION PLAN API ENDPOINTS (Epic 13)
    # ===============================================
    
    @app.post("/api/v1/plans/generate")
    async def generate_action_plan_api(request: dict):
        """Generate action plan via API."""
        try:
            if "transcript_id" in request:
                transcript_id = request["transcript_id"]
                transcript = store.get_by_id(transcript_id)
                if not transcript:
                    raise HTTPException(status_code=404, detail=f"Transcript {transcript_id} not found")
                
                # Generate the action plan
                plan = action_plan_generator.generate_comprehensive_plan(transcript)
                stored_plan = action_plan_store.store(plan)
                
                return {
                    "plan_id": stored_plan["plan_id"],
                    "risk_level": stored_plan.get("risk_level"),
                    "approval_route": stored_plan.get("approval_route"),
                    "total_actions": len(stored_plan.get("borrower_plan", {}).get("immediate_actions", [])) + 
                                   len(stored_plan.get("borrower_plan", {}).get("follow_ups", [])),
                    "queue_status": stored_plan.get("queue_status")
                }
            else:
                raise HTTPException(status_code=400, detail="transcript_id required")
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Plan generation failed: {str(e)}")
    
    @app.get("/api/v1/plans/{plan_id}")
    async def get_action_plan_details(plan_id: str, layer: str = None):
        """Get action plan details."""
        try:
            plan = action_plan_store.get_by_id(plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
            
            if layer:
                layer_key = f"{layer}_plan"
                if layer_key in plan:
                    return plan[layer_key]
                else:
                    raise HTTPException(status_code=400, detail=f"Invalid layer: {layer}")
            
            return {
                "plan_id": plan_id,
                "borrower_plan": plan.get("borrower_plan", {}),
                "advisor_plan": plan.get("advisor_plan", {}),
                "supervisor_plan": plan.get("supervisor_plan", {}),
                "leadership_plan": plan.get("leadership_plan", {}),
                "risk_level": plan.get("risk_level"),
                "approval_route": plan.get("approval_route"),
                "queue_status": plan.get("queue_status")
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get plan: {str(e)}")
    
    @app.get("/api/v1/plans/queue")
    async def get_plan_approval_queue(status: str = None):
        """Get plan approval queue."""
        try:
            plans = action_plan_store.get_all()
            
            if status:
                plans = [p for p in plans if p.get("queue_status") == status]
            
            queue_items = []
            status_distribution = {}
            
            for plan in plans:
                plan_status = plan.get("queue_status", "unknown")
                status_distribution[plan_status] = status_distribution.get(plan_status, 0) + 1
                
                queue_items.append({
                    "plan_id": plan.get("plan_id"),
                    "transcript_id": plan.get("transcript_id"),
                    "risk_level": plan.get("risk_level"),
                    "status": plan_status,
                    "approval_route": plan.get("approval_route"),
                    "created_at": plan.get("created_at"),
                    "routing_reason": plan.get("routing_reason", "")
                })
            
            return {
                "queue_items": queue_items,
                "total_count": len(queue_items),
                "status_distribution": status_distribution
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get queue: {str(e)}")
    
    @app.put("/api/v1/plans/{plan_id}/approve")
    async def approve_action_plan_api(plan_id: str, request: dict):
        """Approve action plan."""
        try:
            plan = action_plan_store.get_by_id(plan_id)
            if not plan:
                raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
            
            approved_by = request.get("approved_by", "api_user")
            notes = request.get("notes", "")
            decision = request.get("decision", "approve")
            
            if decision == "approve":
                # Update plan status
                plan["queue_status"] = "approved"
                plan["approved_by"] = approved_by
                plan["approval_notes"] = notes
                plan["approval_timestamp"] = datetime.now().isoformat()
                
                # Store updated plan
                action_plan_store.update(plan_id, plan)
                
                return {
                    "plan_id": plan_id,
                    "status": "approved",
                    "approved_by": approved_by,
                    "approval_timestamp": plan["approval_timestamp"]
                }
            else:
                raise HTTPException(status_code=400, detail="Only 'approve' decision supported")
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to approve plan: {str(e)}")
    
    @app.get("/api/v1/plans/summary")
    async def get_planning_summary():
        """Get planning metrics summary."""
        try:
            plans = action_plan_store.get_all()
            total_plans = len(plans)
            
            if total_plans == 0:
                return {
                    "total_plans": 0,
                    "pending_approvals": 0,
                    "auto_executable_percentage": 0.0,
                    "risk_distribution": {},
                    "approval_route_distribution": {}
                }
            
            pending_approvals = sum(1 for p in plans if p.get("queue_status", "").startswith("pending"))
            auto_executable = sum(1 for p in plans if p.get("auto_executable", False))
            
            risk_distribution = {}
            route_distribution = {}
            
            for plan in plans:
                risk = plan.get("risk_level", "unknown")
                risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
                
                route = plan.get("approval_route", "unknown")
                route_distribution[route] = route_distribution.get(route, 0) + 1
            
            return {
                "total_plans": total_plans,
                "pending_approvals": pending_approvals,
                "auto_executable_percentage": round((auto_executable / total_plans) * 100, 2),
                "risk_distribution": risk_distribution,
                "approval_route_distribution": route_distribution
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")
    
    # ===============================================
    # EXECUTION API ENDPOINTS (Epic 13)
    # ===============================================
    
    @app.post("/api/v1/execution/{plan_id}")
    async def execute_action_plan_api(plan_id: str, request: dict):
        """Execute action plan via API."""
        try:
            mode = request.get("mode", "auto")
            dry_run = request.get("dry_run", False)
            
            if dry_run:
                # Return preview without executing
                plan = action_plan_store.get_by_id(plan_id)
                if not plan:
                    raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
                
                borrower_actions = plan.get("borrower_plan", {}).get("immediate_actions", [])
                return {
                    "preview": True,
                    "plan_id": plan_id,
                    "would_execute": len(borrower_actions),
                    "estimated_artifacts": len(borrower_actions)
                }
            
            # Execute the plan
            result = smart_executor.execute_action_plan(plan_id)
            
            return {
                "execution_id": result.get("execution_id"),
                "status": "success" if result.get("status") == "success" else "failed",
                "total_actions_executed": result.get("total_actions_executed", 0),
                "artifacts_created": result.get("artifacts_created", []),
                "plan_id": plan_id
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Execution failed: {str(e)}")
    
    @app.get("/api/v1/execution/{execution_id}")
    async def get_execution_status(execution_id: str):
        """Get execution status by ID."""
        try:
            execution = execution_store.get_by_id(execution_id)
            if not execution:
                raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
            
            return {
                "execution_id": execution_id,
                "status": execution.get("status"),
                "plan_id": execution.get("plan_id"),
                "executed_at": execution.get("executed_at"),
                "action_results": execution.get("action_results", []),
                "artifacts_created": execution.get("artifacts_created", []),
                "errors": execution.get("errors", [])
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get execution: {str(e)}")
    
    @app.get("/api/v1/execution/history")
    async def get_execution_history(limit: int = 10):
        """Get execution history."""
        try:
            executions = execution_store.get_all()[-limit:]  # Get last N executions
            
            return {
                "executions": [
                    {
                        "execution_id": exec.get("execution_id"),
                        "plan_id": exec.get("plan_id"),
                        "status": exec.get("status"),
                        "executed_at": exec.get("executed_at"),
                        "artifacts_count": len(exec.get("artifacts_created", [])),
                        "errors_count": len(exec.get("errors", []))
                    }
                    for exec in reversed(executions)
                ],
                "total_count": len(executions)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")
    
    @app.get("/api/v1/execution/artifacts")
    async def get_execution_artifacts(type: str = "all", limit: int = 10):
        """Get execution artifacts."""
        try:
            # This is a simplified version - in reality you'd scan artifact directories
            return {
                "artifacts": [],  # Would be populated from filesystem scan
                "total_count": 0,
                "artifact_type": type
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get artifacts: {str(e)}")
    
    @app.get("/api/v1/execution/metrics")
    async def get_execution_metrics():
        """Get execution performance metrics."""
        try:
            executions = execution_store.get_all()
            total_executions = len(executions)
            
            if total_executions == 0:
                return {
                    "total_executions": 0,
                    "success_rate": 0.0,
                    "artifacts_created": 0,
                    "actions_by_source": {},
                    "status_breakdown": {}
                }
            
            successful = sum(1 for e in executions if e.get("status") == "success")
            success_rate = (successful / total_executions) * 100
            
            total_artifacts = sum(len(e.get("artifacts_created", [])) for e in executions)
            
            status_breakdown = {}
            for exec in executions:
                status = exec.get("status", "unknown")
                status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            return {
                "total_executions": total_executions,
                "success_rate": round(success_rate, 2),
                "artifacts_created": total_artifacts,
                "actions_by_source": {"borrower": 50, "advisor": 30, "supervisor": 15, "leadership": 5},  # Simplified
                "status_breakdown": status_breakdown
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
    
    # ===============================================
    # APPROVAL API ENDPOINTS (Epic 13)
    # ===============================================
    
    @app.get("/api/v1/approvals/queue")
    async def get_approval_queue_api(route: str = None):
        """Get approval queue."""
        try:
            approvals = approval_store.get_pending_actions()
            
            if route:
                approvals = [a for a in approvals if a.get("approval_route") == route]
            
            route_distribution = {}
            for approval in approvals:
                approval_route = approval.get("approval_route", "unknown")
                route_distribution[approval_route] = route_distribution.get(approval_route, 0) + 1
            
            return {
                "pending_actions": [
                    {
                        "action_id": a.get("id"),
                        "plan_id": a.get("plan_id"),
                        "action_type": a.get("action_type"),
                        "risk_score": a.get("risk_score", 0),
                        "approval_route": a.get("approval_route"),
                        "created_at": a.get("created_at")
                    }
                    for a in approvals
                ],
                "total_count": len(approvals),
                "route_distribution": route_distribution
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get approval queue: {str(e)}")
    
    @app.post("/api/v1/approvals/{action_id}/approve")
    async def approve_action_api(action_id: str, request: dict):
        """Approve specific action."""
        try:
            approved_by = request.get("approved_by", "api_user")
            notes = request.get("notes", "")
            
            # Update approval status
            approval_store.approve_action(action_id, approved_by, notes)
            
            return {
                "action_id": action_id,
                "status": "approved",
                "approved_by": approved_by,
                "approval_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to approve action: {str(e)}")
    
    @app.post("/api/v1/approvals/{action_id}/reject")
    async def reject_action_api(action_id: str, request: dict):
        """Reject specific action."""
        try:
            rejected_by = request.get("rejected_by", "api_user")
            reason = request.get("reason", "No reason provided")
            
            # Update rejection status
            approval_store.reject_action(action_id, rejected_by, reason)
            
            return {
                "action_id": action_id,
                "status": "rejected",
                "rejected_by": rejected_by,
                "reason": reason,
                "rejection_timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to reject action: {str(e)}")
    
    @app.post("/api/v1/approvals/bulk")
    async def bulk_approve_actions_api(request: dict):
        """Bulk approve actions."""
        try:
            action_ids = request.get("action_ids", [])
            approved_by = request.get("approved_by", "api_user")
            notes = request.get("notes", "Bulk approval")
            
            approved_count = 0
            failed_count = 0
            
            for action_id in action_ids:
                try:
                    approval_store.approve_action(action_id, approved_by, notes)
                    approved_count += 1
                except:
                    failed_count += 1
            
            return {
                "approved_count": approved_count,
                "failed_count": failed_count,
                "total_requested": len(action_ids)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to bulk approve: {str(e)}")
    
    @app.get("/api/v1/approvals/metrics")
    async def get_approval_metrics_api():
        """Get approval system metrics."""
        try:
            all_actions = approval_store.get_all_actions()
            pending_actions = approval_store.get_pending_actions()
            
            total_actions = len(all_actions)
            pending_approvals = len(pending_actions)
            
            if total_actions == 0:
                return {
                    "total_actions": 0,
                    "pending_approvals": 0,
                    "approval_rate": 0.0,
                    "avg_approval_time": 0.0,
                    "queue_status": {},
                    "risk_distribution": {}
                }
            
            approved_actions = sum(1 for a in all_actions if a.get("status") == "approved")
            approval_rate = (approved_actions / total_actions) * 100
            
            # Simplified metrics
            queue_status = {}
            risk_distribution = {}
            
            for action in all_actions:
                status = action.get("status", "pending")
                queue_status[status] = queue_status.get(status, 0) + 1
                
                risk = action.get("risk_level", "unknown")
                risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
            
            return {
                "total_actions": total_actions,
                "pending_approvals": pending_approvals,
                "approval_rate": round(approval_rate, 2),
                "avg_approval_time": 2.3,  # Simplified - would calculate from timestamps
                "queue_status": queue_status,
                "risk_distribution": risk_distribution
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get approval metrics: {str(e)}")

    # ========== Governance API Endpoints (Epic 2) ==========
    
    @app.post("/api/v1/governance/submit")
    async def submit_for_governance_api(request: dict):
        """Submit action for governance review with LLM-based routing."""
        try:
            # Use GovernanceEngine for intelligent routing
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise HTTPException(status_code=500, detail="OpenAI API key not configured")
            
            governance_engine = GovernanceEngine(api_key=api_key)
            audit_logger = AuditLogger("data/call_center.db")
            approval_workflow = ApprovalWorkflow("data/call_center.db")
            
            # Evaluate action for governance routing
            action_data = {
                "action_id": request.get("action_id"),
                "description": request.get("description"),
                "financial_impact": request.get("financial_impact", False),
                "risk_score": request.get("risk_score", 0.5),
                "compliance_flags": request.get("compliance_flags", []),
                "amount": request.get("amount", 0)
            }
            
            # LLM-based governance evaluation
            governance_result = governance_engine.evaluate_action(action_data)
            
            # Log governance decision in audit trail
            audit_id = audit_logger.log_event({
                "event_type": "governance_submission",
                "action_id": action_data["action_id"],
                "user_id": request.get("submitted_by"),
                "timestamp": datetime.now(),
                "details": {
                    "governance_decision": governance_result,
                    "original_request": request
                }
            })
            
            # Submit to approval workflow if needed
            if governance_result["routing_decision"] != "auto_approved":
                approval_request = {
                    "action_id": action_data["action_id"],
                    "submitted_by": request.get("submitted_by"),
                    "urgency": request.get("urgency", "medium"),
                    "governance_routing": governance_result["routing_decision"]
                }
                approval_id = approval_workflow.submit_for_approval(approval_request)
                
                return {
                    "governance_id": audit_id,
                    "approval_id": approval_id,
                    "routing_decision": governance_result["routing_decision"],
                    "risk_assessment": governance_result["risk_assessment"],
                    "reasoning": governance_result["routing_reason"],
                    "status": "pending_approval",
                    "confidence": governance_result["confidence_score"]
                }
            else:
                return {
                    "governance_id": audit_id,
                    "routing_decision": "auto_approved",
                    "risk_assessment": governance_result["risk_assessment"], 
                    "reasoning": governance_result["routing_reason"],
                    "status": "approved",
                    "confidence": governance_result["confidence_score"]
                }
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Governance submission failed: {str(e)}")
    
    @app.get("/api/v1/governance/status/{governance_id}")
    async def get_governance_status_api(governance_id: str):
        """Get status of governance submission."""
        try:
            audit_logger = AuditLogger("data/call_center.db")
            approval_workflow = ApprovalWorkflow("data/call_center.db")
            
            # Get governance audit event
            governance_event = audit_logger.get_event(governance_id)
            if not governance_event:
                raise HTTPException(status_code=404, detail="Governance submission not found")
            
            # Check if there's an associated approval
            action_id = governance_event.get("action_id")
            approval_status = None
            
            # This is simplified - in production would need better tracking
            return {
                "governance_id": governance_id,
                "action_id": action_id,
                "status": "submitted",
                "submitted_at": governance_event.get("timestamp"),
                "routing_decision": governance_event["details"]["governance_decision"]["routing_decision"],
                "risk_assessment": governance_event["details"]["governance_decision"]["risk_assessment"]
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get governance status: {str(e)}")
    
    @app.post("/api/v1/governance/approve")
    async def approve_governance_api(request: dict):
        """Approve governance submission with conditions."""
        try:
            approval_workflow = ApprovalWorkflow("data/call_center.db")
            audit_logger = AuditLogger("data/call_center.db")
            
            approval_id = request.get("approval_id")
            approved_by = request.get("approved_by")
            conditions = request.get("conditions", [])
            notes = request.get("notes", "")
            
            # Approve via workflow
            approval_result = approval_workflow.approve(
                approval_id=approval_id,
                approved_by=approved_by,
                conditions=conditions,
                notes=notes
            )
            
            # Log approval in audit trail
            audit_logger.log_event({
                "event_type": "governance_approved",
                "action_id": request.get("action_id"),
                "user_id": approved_by,
                "timestamp": datetime.now(),
                "details": {
                    "approval_id": approval_id,
                    "conditions": conditions,
                    "notes": notes
                }
            })
            
            return approval_result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to approve: {str(e)}")
    
    @app.post("/api/v1/governance/reject")
    async def reject_governance_api(request: dict):
        """Reject governance submission with reason."""
        try:
            approval_workflow = ApprovalWorkflow("data/call_center.db")
            audit_logger = AuditLogger("data/call_center.db")
            
            approval_id = request.get("approval_id")
            rejected_by = request.get("rejected_by")
            reason = request.get("reason", "")
            
            # Reject via workflow
            rejection_result = approval_workflow.reject(
                approval_id=approval_id,
                rejected_by=rejected_by,
                reason=reason
            )
            
            # Log rejection in audit trail
            audit_logger.log_event({
                "event_type": "governance_rejected",
                "action_id": request.get("action_id"),
                "user_id": rejected_by,
                "timestamp": datetime.now(),
                "details": {
                    "approval_id": approval_id,
                    "reason": reason
                }
            })
            
            return rejection_result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to reject: {str(e)}")
    
    @app.post("/api/v1/governance/bulk-approve")
    async def bulk_approve_governance_api(request: dict):
        """Bulk approve multiple governance submissions."""
        try:
            approval_workflow = ApprovalWorkflow("data/call_center.db")
            audit_logger = AuditLogger("data/call_center.db")
            
            approval_ids = request.get("approval_ids", [])
            approved_by = request.get("approved_by")
            
            # Bulk approve via workflow
            bulk_result = approval_workflow.bulk_approve(
                approval_ids=approval_ids,
                approved_by=approved_by
            )
            
            # Log bulk approval
            audit_logger.log_event({
                "event_type": "governance_bulk_approved",
                "user_id": approved_by,
                "timestamp": datetime.now(),
                "details": {
                    "approval_ids": approval_ids,
                    "bulk_result": bulk_result
                }
            })
            
            return bulk_result
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to bulk approve: {str(e)}")
    
    @app.get("/api/v1/governance/queue")
    async def get_governance_queue_api(status: str = "pending"):
        """Get governance approval queue."""
        try:
            approval_workflow = ApprovalWorkflow("data/call_center.db")
            
            # Get approvals by status
            if status == "pending":
                approvals = approval_workflow.get_pending_approvals()
            else:
                # Would implement other status filters
                approvals = approval_workflow.get_pending_approvals()
            
            return {
                "status": status,
                "count": len(approvals),
                "approvals": approvals
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get queue: {str(e)}")
    
    @app.get("/api/v1/governance/audit")
    async def get_governance_audit_api(
        user_id: str = None,
        event_type: str = None,
        start_date: str = None,
        end_date: str = None,
        limit: int = 100
    ):
        """Query governance audit trail."""
        try:
            audit_logger = AuditLogger("data/call_center.db")
            
            # Convert date strings if provided
            start_date_obj = None
            end_date_obj = None
            if start_date:
                start_date_obj = datetime.fromisoformat(start_date).date()
            if end_date:
                end_date_obj = datetime.fromisoformat(end_date).date()
            
            # Query audit trail
            events = audit_logger.query_events(
                user_id=user_id,
                event_type=event_type,
                start_date=start_date_obj,
                end_date=end_date_obj,
                limit=limit
            )
            
            return {
                "count": len(events),
                "events": events,
                "integrity_verified": audit_logger.verify_chain_integrity()
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to query audit trail: {str(e)}")
    
    @app.get("/api/v1/governance/metrics")
    async def get_governance_metrics_api():
        """Get governance system metrics."""
        try:
            audit_logger = AuditLogger("data/call_center.db")
            approval_workflow = ApprovalWorkflow("data/call_center.db")
            governance_store = GovernanceStore("data/call_center.db")
            
            # Get basic metrics
            performance_stats = governance_store.get_performance_stats()
            
            # Get recent events for analysis
            recent_events = audit_logger.query_events(limit=100)
            
            # Calculate governance metrics
            governance_events = [e for e in recent_events if e["event_type"].startswith("governance")]
            approval_events = [e for e in recent_events if "approved" in e["event_type"]]
            
            return {
                "audit_events_count": performance_stats["audit_events_count"],
                "governance_rules_count": performance_stats["governance_rules_count"],
                "recent_governance_events": len(governance_events),
                "recent_approvals": len(approval_events),
                "chain_integrity_verified": audit_logger.verify_chain_integrity(),
                "database_performance": {
                    "query_time": performance_stats["recent_query_time_seconds"],
                    "performance_target_met": performance_stats["performance_target_met"]
                }
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
    
    @app.post("/api/v1/governance/override")
    async def emergency_override_api(request: dict):
        """Execute emergency override with enhanced logging."""
        try:
            override_manager = OverrideManager("data/call_center.db")
            
            override_request = {
                "action_id": request.get("action_id"),
                "override_by": request.get("override_by"),
                "emergency_type": request.get("emergency_type"),
                "justification": request.get("justification"),
                "approval_level_bypassed": request.get("approval_level_bypassed")
            }
            
            # Execute override with permission validation
            override_id = override_manager.execute_override(override_request)
            
            # Get the override log for response
            override_log = override_manager.get_override_log(override_id)
            
            return {
                "override_id": override_id,
                "status": "executed",
                "emergency_type": override_request["emergency_type"],
                "justification": override_request["justification"],
                "executed_by": override_request["override_by"],
                "impact_assessment": override_log.get("impact_assessment"),
                "followup_required": True
            }
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Emergency override failed: {str(e)}")
    
    @app.get("/api/v1/workflow/status")
    async def get_workflow_status():
        """Get aggregated workflow status for all transcripts - used by UI pipeline visualizer."""
        # Import all required modules and backend logic
        from src.workflow.status_backend import WorkflowStatusBackend
        from src.storage.transcript_store import TranscriptStore
        from src.storage.analysis_store import AnalysisStore
        from src.storage.action_plan_store import ActionPlanStore
        from src.storage.approval_store import ApprovalStore
        from src.storage.execution_store import ExecutionStore
        
        # Initialize all stores - NO FALLBACK LOGIC
        transcript_store = store if store else TranscriptStore("data/call_center.db")
        analysis_store = AnalysisStore("data/call_center.db")
        action_plan_store = ActionPlanStore("data/call_center.db")
        approval_store = ApprovalStore("data/call_center.db")
        execution_store = ExecutionStore("data/call_center.db")
        
        # Initialize backend with all required stores - NO FALLBACK LOGIC
        backend = WorkflowStatusBackend(
            transcript_store,         # transcript_store
            analysis_store,           # analysis_store
            action_plan_store,        # plan_store
            approval_store,           # approval_store
            execution_store           # execution_store
        )
        
        # Get workflow status using pure business logic - NO FALLBACK
        workflow_statuses = backend.get_all_workflows_status()
        
        # Return the results directly - NO FALLBACK LOGIC
        return workflow_statuses
    
    return app


def start_fastapi_server():
    """Start FastAPI server on port 5000 (with fallback ports)."""
    global fastapi_app
    
    # Try multiple ports for FastAPI (Replit needs 5000 for frontend)
    ports_to_try = [5000, 5001, 5002, 5003]
    
    for port in ports_to_try:
        try:
            fastapi_app = create_fastapi_app()
            print(f"🌐 FastAPI ready on http://localhost:{port}")
            print(f"📚 API Documentation: http://localhost:{port}/docs")
            if port != 5000:
                print(f"⚠️  Note: Using alternate port {port} (5000 was busy)")
            
            # Run with explicit signal handling
            config = uvicorn.Config(
                fastapi_app, 
                host="0.0.0.0", 
                port=port, 
                log_level="error",
                loop="asyncio"
            )
            server = uvicorn.Server(config)
            
            # Check for shutdown signal periodically
            import asyncio
            async def serve_with_shutdown():
                while not shutdown_event.is_set():
                    try:
                        await asyncio.wait_for(server.serve(), timeout=1.0)
                        break  # Server exited normally
                    except asyncio.TimeoutError:
                        continue  # Check shutdown signal again
                    except Exception:
                        break
            
            asyncio.run(serve_with_shutdown())
            return
            
        except OSError as e:
            if "Address already in use" in str(e):
                logger.warning(f"FastAPI port {port} is busy, trying next port...")
                continue
            else:
                logger.error(f"FastAPI server error on port {port}: {e}")
                break
        except Exception as e:
            logger.error(f"FastAPI server error on port {port}: {e}")
            break
    
    logger.error("❌ Failed to start FastAPI on any port. Try running ./cleanup.sh first.")


# ========== Server Management ==========

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    
    # Set shutdown event to stop both servers
    shutdown_event.set()
    
    # Give servers a moment to shut down gracefully
    import time
    time.sleep(1)
    
    print("✅ Universal server shutdown complete")
    sys.exit(0)


def main():
    """Main server entry point."""
    print("🚀 Universal Customer Call Center Analytics Server")
    print("=" * 50)
    
    # Initialize business logic once
    try:
        init_business_logic()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start FastAPI in background thread
    global fastapi_thread
    fastapi_thread = threading.Thread(target=start_fastapi_server, daemon=False)
    fastapi_thread.start()
    
    # Start CLI server in main thread
    print("🎯 Both servers ready!")
    print("   • CLI Backend: http://localhost:9999 (for cli_fast.py)")
    print("   • Web API: http://localhost:5000 (browser/curl)")
    print("   • Press Ctrl+C to stop")
    print()
    
    try:
        start_cli_server()
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)
    except Exception as e:
        logger.error(f"CLI server error: {e}")
        shutdown_event.set()
    
    # Wait for FastAPI thread to finish
    if fastapi_thread and fastapi_thread.is_alive():
        fastapi_thread.join(timeout=2)
    
    print("✅ Both servers stopped")


if __name__ == "__main__":
    main()