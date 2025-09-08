"""
Function tools for the Customer Call Center Analytics system.
Provides essential tools for the router agent to interact with the system.
"""

from agents import function_tool, Runner
from typing import Optional
import json
import re
from datetime import datetime, timedelta

from .storage_sqlite import get_storage
from .config import settings
from .agent_definitions import get_transcript_generator, get_transcript_analyzer


storage = get_storage()


def _extract_and_save_action_items(analysis_id: str, analysis_content: str) -> int:
    """Extract action items from analysis and save to database"""
    try:
        if not hasattr(storage, '_get_connection'):
            return 0  # Skip if not SQLite storage
            
        # Parse action queues from analysis using IntegrationOrchestrator
        from .llm.integrations import IntegrationOrchestrator
        orchestrator = IntegrationOrchestrator()
        parsed = orchestrator.parse_analysis_output(analysis_content)
        
        items_saved = 0
        
        with storage._get_connection() as conn:
            # Process each action queue type
            action_queues = parsed.get('actions', {})
            
            for queue_type, actions in action_queues.items():
                if not isinstance(actions, list):
                    continue
                    
                for action in actions:
                    try:
                        # Extract common fields
                        description = ""
                        action_type = queue_type.replace('_', ' ').title()
                        priority = "MEDIUM"
                        due_date = None
                        
                        # Parse based on queue type
                        if queue_type == 'borrower_actions':
                            description = action.get('action', action.get('content', ''))
                            action_type = action.get('type', 'BORROWER_ACTION')
                            priority = action.get('priority', 'MEDIUM')
                            if action.get('due_date'):
                                try:
                                    due_date = action['due_date']
                                except:
                                    pass
                                    
                        elif queue_type == 'advisor_tasks':
                            description = action.get('task', action.get('content', ''))
                            action_type = action.get('system', 'ADVISOR_TASK')
                            priority = "HIGH" if action.get('blocking') else "MEDIUM"
                            if action.get('deadline'):
                                try:
                                    due_date = action['deadline']
                                except:
                                    pass
                                    
                        elif queue_type == 'supervisor_items':
                            description = action.get('item', action.get('content', ''))
                            action_type = action.get('approval_type', 'SUPERVISOR_ITEM')
                            risk_level = action.get('risk_level', 'MEDIUM')
                            priority = "HIGH" if risk_level == 'HIGH' else "MEDIUM"
                            
                        elif queue_type == 'leadership_insights':
                            description = action.get('pattern', action.get('content', ''))
                            action_type = action.get('impact', 'LEADERSHIP_INSIGHT')
                            priority = "LOW"
                        
                        if description:  # Only save if we have a description
                            conn.execute("""
                                INSERT INTO action_items 
                                (analysis_id, action_type, description, priority, due_date, status, metadata)
                                VALUES (?, ?, ?, ?, ?, 'pending', ?)
                            """, (analysis_id, action_type, description, priority, due_date, json.dumps(action)))
                            
                            items_saved += 1
                            
                    except Exception as e:
                        print(f"Warning: Failed to save action item: {e}")
                        continue
        
        return items_saved
        
    except Exception as e:
        print(f"Warning: Failed to extract action items: {e}")
        return 0


@function_tool
def generate_transcript(request: str) -> str:
    """Generate call transcript based on request"""
    try:
        # Use Agent SDK with Responses API instead of chat completions
        generator_agent = get_transcript_generator()
        result = Runner.run_sync(generator_agent, request)
        content = result.final_output
        
        # Save the transcript
        transcript_id = storage.save_transcript(
            content,
            metadata={"generated_from": request}
        )
        
        # Return preview with ID
        preview = content[:500]
        if len(content) > 500:
            preview += "\n... [truncated]"
            
        return f"Generated and saved as {transcript_id}.\n\nPreview:\n{preview}"
        
    except Exception as e:
        return f"Error generating transcript: {str(e)}"


@function_tool
def analyze_transcript(request: str) -> str:
    """Analyze transcript - handles 'recent', specific ID, or general request"""
    try:
        
        # Handle different types of analysis requests
        if "recent" in request.lower() or not request.strip():
            # Analyze most recent transcript
            recent = storage.list_recent(1)
            if not recent:
                return "No transcripts found. Generate some transcripts first!"
                
            transcript_data = storage.get_transcript_with_analysis(recent[0]['id'])
            if 'error' in transcript_data:
                return f"Error loading transcript: {transcript_data['error']}"
                
            transcript_content = transcript_data['content']
            transcript_id = recent[0]['id']
            
        elif "CALL_" in request.upper():
            # Extract transcript ID from request
            words = request.split()
            transcript_id = None
            for word in words:
                if "CALL_" in word.upper():
                    transcript_id = word.upper()
                    break
                    
            if transcript_id:
                transcript_data = storage.get_transcript_with_analysis(transcript_id)
                if 'error' in transcript_data:
                    return f"Transcript {transcript_id} not found."
                    
                transcript_content = transcript_data['content']
            else:
                return "Could not find valid transcript ID in request."
        else:
            return "Please specify 'recent' or a transcript ID (e.g., CALL_123)."
            
        # Use Agent SDK with Responses API instead of chat completions
        analyzer_agent = get_transcript_analyzer()
        analysis_prompt = f"Analyze this mortgage servicing call transcript:\n\n{transcript_content}"
        result = Runner.run_sync(analyzer_agent, analysis_prompt)
        analysis_result = result.final_output
        
        # Save analysis
        analysis_id = storage.save_analysis(transcript_id, analysis_result)
        
        # Extract and save action items to database
        action_items_saved = _extract_and_save_action_items(analysis_id, analysis_result)
        
        summary = f"Analysis of {transcript_id} (saved as {analysis_id}):\n\n{analysis_result}"
        if action_items_saved > 0:
            summary += f"\n\n📋 {action_items_saved} action items added to queue"
        
        return summary
        
    except Exception as e:
        return f"Error analyzing transcript: {str(e)}"


@function_tool
def search_data(query: str) -> str:
    """Search transcripts database"""
    try:
        results = storage.search_transcripts(query, limit=10)
        
        if not results:
            return f"No results found for '{query}'"
            
        output = f"Found {len(results)} matches for '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            output += f"{i}. {result['id']} ({result['created']})\n"
            output += f"   Context: {result['match_context']}\n\n"
            
        return output
        
    except Exception as e:
        return f"Error searching data: {str(e)}"


@function_tool
def list_recent_items(limit: int = 10) -> str:
    """List recent transcripts and analyses"""
    try:
        recent = storage.list_recent(limit)
        
        if not recent:
            return "No items found. Generate some transcripts first!"
            
        output = f"Recent {len(recent)} items:\n\n"
        
        for i, item in enumerate(recent, 1):
            icon = "📊" if item['type'] == 'analysis' else "📄"
            output += f"{i}. {icon} {item['id']}\n"
            output += f"   {item['summary']}\n"
            output += f"   Created: {item['created'][:10]}\n\n"
            
        return output
        
    except Exception as e:
        return f"Error listing items: {str(e)}"


@function_tool
def get_system_status() -> str:
    """Get system status and statistics"""
    try:
        from .config import settings
        
        stats = storage.get_stats()
        
        output = "System Status:\n\n"
        output += f"Model: {settings.OPENAI_MODEL}\n"
        output += f"Handoffs: Enabled\n"
        
        if 'error' not in stats:
            output += f"\nStorage Statistics:\n"
            output += f"Path: {stats['storage_path']}\n"
            output += f"Total Files: {stats['total_files']}\n"
            output += f"Transcripts: {stats['transcripts']}\n"
            output += f"Analyses: {stats['analyses']}\n"
            output += f"Storage Used: {stats['total_size_mb']} MB\n"
        else:
            output += f"\nStorage Error: {stats['error']}\n"
            
        return output
        
    except Exception as e:
        return f"Error getting system status: {str(e)}"


@function_tool
def view_action_queue(status: str = "pending") -> str:
    """View action items in the queue by status (pending/approved/rejected/completed)"""
    try:
        # Get action items from database
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                rows = conn.execute("""
                    SELECT ai.id, ai.action_type, ai.description, ai.priority, ai.status, 
                           ai.due_date, ai.created_at, a.id as analysis_id
                    FROM action_items ai
                    JOIN analyses a ON ai.analysis_id = a.id  
                    WHERE ai.status = ?
                    ORDER BY ai.priority DESC, ai.created_at DESC
                    LIMIT 20
                """, (status,)).fetchall()
                
                if not rows:
                    return f"No {status} action items found"
                
                output = f"{status.title()} Action Items ({len(rows)}):\n\n"
                
                for i, row in enumerate(rows, 1):
                    priority_icon = "🔥" if row['priority'] == 'HIGH' else "⚠️" if row['priority'] == 'MEDIUM' else "📝"
                    output += f"{i}. {priority_icon} [{row['action_type']}] {row['description']}\n"
                    output += f"   ID: {row['id']} | Priority: {row['priority']}\n"
                    if row['due_date']:
                        output += f"   Due: {row['due_date']}\n"
                    output += f"   Analysis: {row['analysis_id']}\n\n"
                
                return output
        else:
            return "SQLite storage not available - action queue requires database"
            
    except Exception as e:
        return f"Error viewing action queue: {str(e)}"


@function_tool
def approve_action(action_id: int, notes: str = "") -> str:
    """Approve an action item for execution"""
    try:
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                # Check if action exists and is pending
                row = conn.execute("""
                    SELECT id, description, status FROM action_items WHERE id = ?
                """, (action_id,)).fetchone()
                
                if not row:
                    return f"Action item {action_id} not found"
                
                if row['status'] != 'pending':
                    return f"Action item {action_id} is already {row['status']}"
                
                # Update to approved status
                conn.execute("""
                    UPDATE action_items 
                    SET status = 'approved', 
                        metadata = json_set(COALESCE(metadata, '{}'), '$.approval_notes', ?, 
                                          '$.approved_at', datetime('now'))
                    WHERE id = ?
                """, (notes, action_id))
                
                return f"✅ Action item {action_id} approved: {row['description']}"
        else:
            return "SQLite storage not available - approvals require database"
            
    except Exception as e:
        return f"Error approving action: {str(e)}"


@function_tool
def reject_action(action_id: int, reason: str) -> str:
    """Reject an action item with reason"""
    try:
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                # Check if action exists and is pending
                row = conn.execute("""
                    SELECT id, description, status FROM action_items WHERE id = ?
                """, (action_id,)).fetchone()
                
                if not row:
                    return f"Action item {action_id} not found"
                
                if row['status'] != 'pending':
                    return f"Action item {action_id} is already {row['status']}"
                
                # Update to rejected status
                conn.execute("""
                    UPDATE action_items 
                    SET status = 'rejected',
                        metadata = json_set(COALESCE(metadata, '{}'), '$.rejection_reason', ?, 
                                          '$.rejected_at', datetime('now'))
                    WHERE id = ?
                """, (reason, action_id))
                
                return f"❌ Action item {action_id} rejected: {row['description']}\nReason: {reason}"
        else:
            return "SQLite storage not available - rejections require database"
            
    except Exception as e:
        return f"Error rejecting action: {str(e)}"


@function_tool
def complete_action(action_id: int, result: str = "") -> str:
    """Mark an action item as completed"""
    try:
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                # Check if action exists and is approved
                row = conn.execute("""
                    SELECT id, description, status FROM action_items WHERE id = ?
                """, (action_id,)).fetchone()
                
                if not row:
                    return f"Action item {action_id} not found"
                
                if row['status'] not in ['approved', 'in_progress']:
                    return f"Action item {action_id} is {row['status']} - cannot complete"
                
                # Update to completed status
                conn.execute("""
                    UPDATE action_items 
                    SET status = 'completed',
                        metadata = json_set(COALESCE(metadata, '{}'), '$.completion_result', ?, 
                                          '$.completed_at', datetime('now'))
                    WHERE id = ?
                """, (result, action_id))
                
                return f"✅ Action item {action_id} completed: {row['description']}"
        else:
            return "SQLite storage not available - completion tracking requires database"
            
    except Exception as e:
        return f"Error completing action: {str(e)}"


@function_tool
def process_approved_items() -> str:
    """Execute approved action items via IntegrationOrchestrator"""
    try:
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                # Get approved items
                rows = conn.execute("""
                    SELECT ai.id, ai.analysis_id, ai.action_type, ai.description, ai.metadata,
                           a.content as analysis_content
                    FROM action_items ai
                    JOIN analyses a ON ai.analysis_id = a.id
                    WHERE ai.status = 'approved'
                    ORDER BY ai.priority DESC, ai.created_at ASC
                    LIMIT 10
                """).fetchall()
                
                if not rows:
                    return "No approved action items to process"
                
                from .llm.integrations import IntegrationOrchestrator
                orchestrator = IntegrationOrchestrator()
                
                processed = 0
                results = []
                
                for row in rows:
                    try:
                        # Parse the full analysis to get integration context
                        parsed_analysis = orchestrator.parse_analysis_output(row['analysis_content'])
                        
                        # Execute integrations for this analysis
                        integration_results = orchestrator.execute_integrations(parsed_analysis)
                        
                        # Update action item to in_progress
                        conn.execute("""
                            UPDATE action_items 
                            SET status = 'in_progress',
                                metadata = json_set(COALESCE(metadata, '{}'), '$.integration_results', ?, 
                                                  '$.processed_at', datetime('now'))
                            WHERE id = ?
                        """, (json.dumps(integration_results), row['id']))
                        
                        processed += 1
                        results.append(f"✅ Processed action {row['id']}: {row['description']}")
                        
                        # If no errors, mark as completed
                        if not integration_results.get('errors'):
                            conn.execute("""
                                UPDATE action_items 
                                SET status = 'completed'
                                WHERE id = ?
                            """, (row['id'],))
                            results[-1] = results[-1].replace("Processed", "Completed")
                        
                    except Exception as e:
                        results.append(f"❌ Failed action {row['id']}: {str(e)}")
                        # Mark as failed
                        conn.execute("""
                            UPDATE action_items 
                            SET status = 'failed',
                                metadata = json_set(COALESCE(metadata, '{}'), '$.error', ?, 
                                                  '$.failed_at', datetime('now'))
                            WHERE id = ?
                        """, (str(e), row['id']))
                
                summary = f"Processed {processed}/{len(rows)} approved items:\n\n" + "\n".join(results)
                return summary
        else:
            return "SQLite storage not available - integration processing requires database"
            
    except Exception as e:
        return f"Error processing approved items: {str(e)}"


@function_tool
def view_integration_results(limit: int = 10) -> str:
    """View integration execution results and status"""
    try:
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                rows = conn.execute("""
                    SELECT ai.id, ai.action_type, ai.description, ai.status, ai.metadata,
                           ai.created_at, ai.analysis_id
                    FROM action_items ai
                    WHERE ai.status IN ('in_progress', 'completed', 'failed')
                       AND json_extract(ai.metadata, '$.integration_results') IS NOT NULL
                    ORDER BY ai.created_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()
                
                if not rows:
                    return "No integration results found"
                
                output = f"Integration Results ({len(rows)}):\n\n"
                
                for i, row in enumerate(rows, 1):
                    status_icon = "✅" if row['status'] == 'completed' else "⏳" if row['status'] == 'in_progress' else "❌"
                    output += f"{i}. {status_icon} [{row['action_type']}] {row['description']}\n"
                    output += f"   ID: {row['id']} | Status: {row['status']}\n"
                    
                    try:
                        metadata = json.loads(row['metadata'] or '{}')
                        integration_results = metadata.get('integration_results', {})
                        
                        if integration_results.get('executed_actions'):
                            actions = integration_results['executed_actions']
                            output += f"   Executed: {len(actions)} actions\n"
                            
                        if integration_results.get('errors'):
                            errors = integration_results['errors']
                            output += f"   Errors: {len(errors)} issues\n"
                            
                        if integration_results.get('pending_approvals'):
                            approvals = integration_results['pending_approvals']
                            output += f"   Pending: {len(approvals)} approvals\n"
                            
                    except (json.JSONDecodeError, KeyError):
                        output += f"   Integration data unavailable\n"
                    
                    output += f"   Analysis: {row['analysis_id']}\n\n"
                
                return output
        else:
            return "SQLite storage not available - integration results require database"
            
    except Exception as e:
        return f"Error viewing integration results: {str(e)}"


@function_tool  
def record_satisfaction(transcript_id: str, satisfied: bool, feedback: str = "") -> str:
    """Record satisfaction with resolution and feedback"""
    try:
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                # Check if transcript exists
                row = conn.execute("""
                    SELECT id FROM transcripts WHERE id LIKE ?
                """, (f"%{transcript_id}%",)).fetchone()
                
                if not row:
                    return f"Transcript {transcript_id} not found"
                
                transcript_id = row['id']
                
                # Record satisfaction in transcript metadata
                conn.execute("""
                    UPDATE transcripts 
                    SET metadata = json_set(COALESCE(metadata, '{}'), 
                                          '$.satisfaction.satisfied', ?,
                                          '$.satisfaction.feedback', ?,
                                          '$.satisfaction.recorded_at', datetime('now'))
                    WHERE id = ?
                """, (satisfied, feedback, transcript_id))
                
                # If unsatisfied, flag for potential reanalysis
                if not satisfied:
                    conn.execute("""
                        UPDATE transcripts 
                        SET metadata = json_set(metadata, '$.satisfaction.needs_reanalysis', true)
                        WHERE id = ?
                    """, (transcript_id,))
                    
                    return f"😞 Recorded unsatisfied resolution for {transcript_id}\nFeedback: {feedback}\n🔄 Flagged for potential reanalysis"
                else:
                    return f"😊 Recorded satisfied resolution for {transcript_id}\nFeedback: {feedback}"
        else:
            return "SQLite storage not available - satisfaction tracking requires database"
            
    except Exception as e:
        return f"Error recording satisfaction: {str(e)}"


@function_tool
def trigger_reanalysis(transcript_id: str, focus_areas: str = "") -> str:
    """Trigger reanalysis of a transcript with optional focus areas"""
    try:
        # Load transcript
        transcript_data = storage.get_transcript_with_analysis(transcript_id)
        if not transcript_data or 'error' in transcript_data:
            return f"Transcript {transcript_id} not found"
        
        # Build reanalysis prompt
        prompt = f"Re-analyze this customer service call transcript"
        if focus_areas:
            prompt += f" with special focus on: {focus_areas}"
        prompt += f"\n\nPrevious analysis may have missed important details. Please provide fresh analysis.\n\n{transcript_data['content']}"
        
        # Use Agent SDK with Responses API instead of chat completions
        analyzer_agent = get_transcript_analyzer()
        result = Runner.run_sync(analyzer_agent, prompt)
        result_content = result.final_output
        
        # Save new analysis
        analysis_id = storage.save_analysis(transcript_id, result_content, 
                                          metadata={"type": "reanalysis", "focus_areas": focus_areas})
        
        # Extract and save new action items
        action_items_saved = _extract_and_save_action_items(analysis_id, result_content)
        
        # Update transcript to indicate reanalysis completed
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                conn.execute("""
                    UPDATE transcripts 
                    SET metadata = json_set(COALESCE(metadata, '{}'), 
                                          '$.satisfaction.needs_reanalysis', false,
                                          '$.reanalysis.completed_at', datetime('now'),
                                          '$.reanalysis.latest_analysis_id', ?)
                    WHERE id = ?
                """, (analysis_id, transcript_id))
        
        summary = f"🔄 Reanalysis completed for {transcript_id}\n"
        summary += f"New analysis saved as {analysis_id}\n"
        if action_items_saved > 0:
            summary += f"📋 {action_items_saved} new action items added to queue\n"
        summary += f"\nReanalysis Results:\n{result_content}"
        
        return summary
        
    except Exception as e:
        return f"Error triggering reanalysis: {str(e)}"


@function_tool
def view_outcomes(limit: int = 10) -> str:
    """View analytics on resolution outcomes and satisfaction rates"""
    try:
        if hasattr(storage, '_get_connection'):
            with storage._get_connection() as conn:
                # Satisfaction statistics
                satisfaction_stats = conn.execute("""
                    SELECT 
                        COUNT(*) as total,
                        SUM(CASE WHEN json_extract(metadata, '$.satisfaction.satisfied') = true THEN 1 ELSE 0 END) as satisfied,
                        SUM(CASE WHEN json_extract(metadata, '$.satisfaction.satisfied') = false THEN 1 ELSE 0 END) as unsatisfied,
                        SUM(CASE WHEN json_extract(metadata, '$.satisfaction.needs_reanalysis') = true THEN 1 ELSE 0 END) as needs_reanalysis
                    FROM transcripts 
                    WHERE json_extract(metadata, '$.satisfaction.satisfied') IS NOT NULL
                """).fetchone()
                
                # Action item completion rates  
                action_stats = conn.execute("""
                    SELECT 
                        status,
                        COUNT(*) as count,
                        ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM action_items), 1) as percentage
                    FROM action_items
                    GROUP BY status
                    ORDER BY count DESC
                """).fetchall()
                
                # Recent satisfaction feedback
                recent_feedback = conn.execute("""
                    SELECT 
                        id,
                        json_extract(metadata, '$.satisfaction.satisfied') as satisfied,
                        json_extract(metadata, '$.satisfaction.feedback') as feedback,
                        json_extract(metadata, '$.satisfaction.recorded_at') as recorded_at
                    FROM transcripts 
                    WHERE json_extract(metadata, '$.satisfaction.satisfied') IS NOT NULL
                    ORDER BY json_extract(metadata, '$.satisfaction.recorded_at') DESC
                    LIMIT ?
                """, (limit,)).fetchall()
                
                output = "📊 Resolution Outcomes & Analytics\n\n"
                
                # Satisfaction rates
                if satisfaction_stats and satisfaction_stats['total'] > 0:
                    total = satisfaction_stats['total']
                    satisfied = satisfaction_stats['satisfied'] or 0
                    unsatisfied = satisfaction_stats['unsatisfied'] or 0
                    satisfaction_rate = round(satisfied / total * 100, 1) if total > 0 else 0
                    
                    output += f"**Satisfaction Rates:**\n"
                    output += f"• Total resolutions tracked: {total}\n"
                    output += f"• Satisfied: {satisfied} ({satisfaction_rate}%)\n" 
                    output += f"• Unsatisfied: {unsatisfied} ({round(unsatisfied/total*100,1)}%)\n"
                    output += f"• Flagged for reanalysis: {satisfaction_stats['needs_reanalysis'] or 0}\n\n"
                else:
                    output += "**Satisfaction Rates:** No data yet\n\n"
                
                # Action item completion
                if action_stats:
                    output += f"**Action Item Status:**\n"
                    for stat in action_stats:
                        status_icon = "✅" if stat['status'] == 'completed' else "⏳" if stat['status'] in ['pending', 'approved'] else "❌"
                        output += f"• {status_icon} {stat['status'].title()}: {stat['count']} ({stat['percentage']}%)\n"
                    output += "\n"
                
                # Recent feedback
                if recent_feedback:
                    output += f"**Recent Feedback:**\n"
                    for feedback in recent_feedback:
                        status_icon = "😊" if feedback['satisfied'] else "😞"
                        output += f"{status_icon} {feedback['id']}: "
                        if feedback['feedback']:
                            output += f'"{feedback['feedback'][:60]}..."\n'
                        else:
                            output += "No feedback provided\n"
                
                return output
        else:
            return "SQLite storage not available - outcomes analytics require database"
            
    except Exception as e:
        return f"Error viewing outcomes: {str(e)}"