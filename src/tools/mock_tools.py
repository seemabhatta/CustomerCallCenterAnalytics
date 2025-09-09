"""
Mock Tools for Execution Layer
Creates visible artifacts to demonstrate execution without real integrations.
"""
import os
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional


class MockTools:
    """Simple mock tools that create visible artifacts for demonstration"""
    
    def __init__(self, artifacts_base_path: str = "data"):
        self.base_path = artifacts_base_path
        self.ensure_directories()
        
    def ensure_directories(self):
        """Create artifact directories if they don't exist"""
        dirs = ['emails', 'callbacks', 'documents', 'crm_updates']
        for directory in dirs:
            path = os.path.join(self.base_path, directory)
            os.makedirs(path, exist_ok=True)
    
    def send_email(self, recipient: str, subject: str, body: str, 
                   template_id: Optional[str] = None, attachments: Optional[list] = None) -> Dict[str, Any]:
        """Simulate sending email by creating a file"""
        
        email_id = f"EMAIL_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now()
        
        # Create email file
        email_file = os.path.join(self.base_path, "emails", f"{email_id}.txt")
        
        email_content = f"""From: Customer Service <service@demo.com>
To: {recipient}
Subject: {subject}
Date: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Message-ID: {email_id}@demo.local
{f'Template: {template_id}' if template_id else ''}

{'-' * 50}

{body}

{'-' * 50}
This is a simulated email for demo purposes.
Attachments: {attachments if attachments else 'None'}
"""
        
        with open(email_file, 'w', encoding='utf-8') as f:
            f.write(email_content)
        
        # Log the email
        self._log_action('email_sent', {
            'email_id': email_id,
            'recipient': recipient,
            'subject': subject,
            'timestamp': timestamp.isoformat()
        })
        
        return {
            'email_id': email_id,
            'status': 'sent',
            'timestamp': timestamp.isoformat(),
            'file_path': email_file
        }
    
    def schedule_callback(self, customer_id: str, scheduled_time: str, 
                         notes: str, priority: str = 'normal') -> Dict[str, Any]:
        """Simulate callback scheduling by creating appointment file"""
        
        appointment_id = f"APT_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now()
        
        # Create appointment file
        appointment_file = os.path.join(self.base_path, "callbacks", f"{appointment_id}.txt")
        
        appointment_content = f"""CALLBACK APPOINTMENT
====================
Appointment ID: {appointment_id}
Customer ID: {customer_id}
Scheduled Time: {scheduled_time}
Priority: {priority.upper()}
Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}

Notes:
{notes}

Status: Scheduled
Reminder Set: Yes
Agent Assignment: TBD

====================
This is a simulated appointment for demo purposes.
"""
        
        with open(appointment_file, 'w', encoding='utf-8') as f:
            f.write(appointment_content)
        
        # Create simple ICS file for calendar integration demo
        ics_file = os.path.join(self.base_path, "callbacks", f"{appointment_id}.ics")
        ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Demo Call Center//EN
BEGIN:VEVENT
UID:{appointment_id}@demo.local
DTSTAMP:{datetime.now().strftime('%Y%m%dT%H%M%SZ')}
DTSTART:{scheduled_time}
SUMMARY:Customer Callback - {customer_id}
DESCRIPTION:{notes}
STATUS:CONFIRMED
END:VEVENT
END:VCALENDAR"""
        
        with open(ics_file, 'w', encoding='utf-8') as f:
            f.write(ics_content)
        
        self._log_action('callback_scheduled', {
            'appointment_id': appointment_id,
            'customer_id': customer_id,
            'scheduled_time': scheduled_time,
            'timestamp': timestamp.isoformat()
        })
        
        return {
            'appointment_id': appointment_id,
            'status': 'scheduled',
            'scheduled_time': scheduled_time,
            'timestamp': timestamp.isoformat(),
            'file_path': appointment_file,
            'ics_path': ics_file
        }
    
    def generate_document(self, doc_type: str, customer_id: str, 
                         data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate document generation by creating document files"""
        
        doc_id = f"DOC_{uuid.uuid4().hex[:10].upper()}"
        timestamp = datetime.now()
        
        # Create document file
        doc_file = os.path.join(self.base_path, "documents", f"{doc_id}.txt")
        
        # Generate document content based on type
        content = self._generate_document_content(doc_type, customer_id, data)
        
        doc_content = f"""GENERATED DOCUMENT
==================
Document ID: {doc_id}
Type: {doc_type.upper()}
Customer ID: {customer_id}
Generated: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Status: Generated

{'-' * 50}

{content}

{'-' * 50}
This document was generated automatically from call analysis.
Document is compliance-approved and ready for delivery.
"""
        
        with open(doc_file, 'w', encoding='utf-8') as f:
            f.write(doc_content)
        
        self._log_action('document_generated', {
            'doc_id': doc_id,
            'doc_type': doc_type,
            'customer_id': customer_id,
            'timestamp': timestamp.isoformat()
        })
        
        return {
            'doc_id': doc_id,
            'doc_type': doc_type,
            'status': 'generated',
            'timestamp': timestamp.isoformat(),
            'file_path': doc_file,
            'download_url': f"http://demo.docs/{doc_id}.pdf"
        }
    
    def update_crm(self, customer_id: str, updates: Dict[str, Any], 
                   interaction_type: str = 'call_followup') -> Dict[str, Any]:
        """Simulate CRM update by logging to CRM updates file"""
        
        update_id = f"CRM_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now()
        
        # Log CRM update
        crm_log_file = os.path.join(self.base_path, "crm_updates.log")
        
        crm_entry = f"[{timestamp.isoformat()}] UPDATE_ID:{update_id} CUSTOMER:{customer_id} TYPE:{interaction_type}\n"
        crm_entry += f"  Updates: {json.dumps(updates)}\n"
        crm_entry += f"  Status: SUCCESS\n\n"
        
        with open(crm_log_file, 'a', encoding='utf-8') as f:
            f.write(crm_entry)
        
        self._log_action('crm_updated', {
            'update_id': update_id,
            'customer_id': customer_id,
            'interaction_type': interaction_type,
            'fields_updated': list(updates.keys()),
            'timestamp': timestamp.isoformat()
        })
        
        return {
            'update_id': update_id,
            'status': 'success',
            'fields_updated': list(updates.keys()),
            'timestamp': timestamp.isoformat()
        }
    
    def send_notification(self, recipient: str, message: str, 
                         channel: str = 'app', urgency: str = 'normal') -> Dict[str, Any]:
        """Simulate sending notification"""
        
        notification_id = f"NOTIF_{uuid.uuid4().hex[:8].upper()}"
        timestamp = datetime.now()
        
        # Create notification file
        notification_file = os.path.join(self.base_path, "notifications.log")
        
        notification_entry = f"[{timestamp.isoformat()}] {notification_id} | {channel.upper()} | {urgency.upper()}\n"
        notification_entry += f"  To: {recipient}\n"
        notification_entry += f"  Message: {message}\n"
        notification_entry += f"  Status: DELIVERED\n\n"
        
        with open(notification_file, 'a', encoding='utf-8') as f:
            f.write(notification_entry)
        
        self._log_action('notification_sent', {
            'notification_id': notification_id,
            'recipient': recipient,
            'channel': channel,
            'urgency': urgency,
            'timestamp': timestamp.isoformat()
        })
        
        return {
            'notification_id': notification_id,
            'status': 'delivered',
            'channel': channel,
            'timestamp': timestamp.isoformat()
        }
    
    def _generate_document_content(self, doc_type: str, customer_id: str, 
                                  data: Dict[str, Any]) -> str:
        """Generate document content based on type"""
        
        templates = {
            'payment_confirmation': f"""
PAYMENT CONFIRMATION

Dear Valued Customer,

This confirms we have received your payment details and processed your request.

Payment Information:
- Amount: {data.get('amount', 'N/A')}
- Date: {data.get('payment_date', datetime.now().strftime('%Y-%m-%d'))}
- Reference: {data.get('reference', customer_id)}

Your account has been updated accordingly. Thank you for your prompt payment.

If you have any questions, please contact us at 1-800-DEMO-123.
""",
            'escrow_analysis': f"""
ESCROW ANALYSIS REPORT

Account Holder: {customer_id}
Analysis Date: {datetime.now().strftime('%Y-%m-%d')}

Current Escrow Balance: ${data.get('current_balance', '2,450.00')}
Projected Annual Payments:
- Property Taxes: ${data.get('property_tax', '3,200.00')}
- Insurance: ${data.get('insurance', '1,800.00')}
- PMI: ${data.get('pmi', '0.00')}

Analysis Result:
{data.get('analysis_result', 'Your escrow account is on track. No shortage detected.')}

Next Review Date: {(datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')}
""",
            'callback_confirmation': f"""
CALLBACK CONFIRMATION

Dear {customer_id},

This confirms we have scheduled a callback for you as requested.

Callback Details:
- Date: {data.get('callback_date', 'TBD')}
- Time: {data.get('callback_time', 'TBD')}
- Purpose: {data.get('purpose', 'Follow-up on recent inquiry')}

A customer service representative will call you at the number on file.
If you need to reschedule, please contact us at 1-800-DEMO-123.
"""
        }
        
        return templates.get(doc_type, f"Document of type '{doc_type}' generated with data: {json.dumps(data, indent=2)}")
    
    def _log_action(self, action_type: str, details: Dict[str, Any]):
        """Log all actions to a central execution log"""
        
        log_file = os.path.join(self.base_path, "execution_history.log")
        
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'details': details
        }
        
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_recent_actions(self, limit: int = 10) -> list:
        """Get recent execution actions for monitoring"""
        
        log_file = os.path.join(self.base_path, "execution_history.log")
        
        if not os.path.exists(log_file):
            return []
        
        actions = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    action = json.loads(line.strip())
                    actions.append(action)
                except json.JSONDecodeError:
                    continue
        
        # Return most recent actions
        return actions[-limit:] if actions else []
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of execution statistics"""
        
        recent_actions = self.get_recent_actions(1000)  # Get more for stats
        
        stats = {
            'total_actions': len(recent_actions),
            'emails_sent': sum(1 for a in recent_actions if a['action_type'] == 'email_sent'),
            'callbacks_scheduled': sum(1 for a in recent_actions if a['action_type'] == 'callback_scheduled'),
            'documents_generated': sum(1 for a in recent_actions if a['action_type'] == 'document_generated'),
            'crm_updates': sum(1 for a in recent_actions if a['action_type'] == 'crm_updated'),
            'notifications_sent': sum(1 for a in recent_actions if a['action_type'] == 'notification_sent'),
            'last_action': recent_actions[-1]['timestamp'] if recent_actions else None
        }
        
        return stats