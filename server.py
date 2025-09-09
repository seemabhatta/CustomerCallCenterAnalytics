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
        print("✅ Business logic initialized")
        
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
            transcripts = store.get_all()
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
            
            transcript = store.get_by_id(transcript_id)
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
            customer = params.get('customer')
            topic = params.get('topic')
            text = params.get('text')
            
            if customer:
                results = store.search_by_customer(customer)
            elif topic:
                results = store.search_by_topic(topic)
            elif text:
                results = store.search_by_text(text)
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
            transcript_id = params.get('transcript_id')
            if not transcript_id:
                return {'success': False, 'error': 'transcript_id required'}
            
            result = store.delete(transcript_id)
            if result:
                return {'success': True, 'message': f'Deleted transcript {transcript_id}'}
            else:
                return {'success': False, 'error': f'Transcript {transcript_id} not found'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_delete_all(self, params):
        """Handle delete all command."""
        try:
            # Get count before deletion for confirmation
            count = store.delete_all()
            
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
            
            analyzed_count = 0
            
            if all_transcripts:
                # Analyze all transcripts
                all_transcripts_list = store.get_all()
                for transcript in all_transcripts_list:
                    analysis = analyzer.analyze(transcript)
                    analysis_store.store(analysis)
                    analyzed_count += 1
            elif transcript_id:
                # Analyze specific transcript
                transcript = store.get_by_id(transcript_id)
                if not transcript:
                    return {'success': False, 'error': f'Transcript {transcript_id} not found'}
                
                analysis = analyzer.analyze(transcript)
                analysis_store.store(analysis)
                analyzed_count = 1
            else:
                return {'success': False, 'error': 'Must specify either --transcript-id or --all'}
            
            return {
                'success': True,
                'message': f'Analyzed {analyzed_count} transcript(s)',
                'count': analyzed_count
            }
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
            transcript = store.get_by_id(transcript_id)
            if not transcript:
                return {'success': False, 'error': f'Transcript {transcript_id} not found'}
            
            # Get analysis
            analysis_store = AnalysisStore('data/call_center.db')
            analysis = analysis_store.get_by_transcript_id(transcript_id)
            if not analysis:
                return {'success': False, 'error': f'Analysis for transcript {transcript_id} not found. Run analyze first.'}
            
            # Generate action plan
            generator = ActionPlanGenerator()
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
    
    return app


def start_fastapi_server():
    """Start FastAPI server on port 8000 (with fallback ports)."""
    global fastapi_app
    
    # Try multiple ports for FastAPI
    ports_to_try = [8000, 8001, 8002, 8003]
    
    for port in ports_to_try:
        try:
            fastapi_app = create_fastapi_app()
            print(f"🌐 FastAPI ready on http://localhost:{port}")
            print(f"📚 API Documentation: http://localhost:{port}/docs")
            if port != 8000:
                print(f"⚠️  Note: Using alternate port {port} (8000 was busy)")
            
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
    print("   • Web API: http://localhost:8000 (browser/curl)")
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