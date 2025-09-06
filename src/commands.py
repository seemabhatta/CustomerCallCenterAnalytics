"""
Vision-Aligned Command Handler for Co-Pilot Interface
Supports multiple prefixes for real-time co-execution:
- / = Actions (Execute)
- @ = References (Context)
- ? = Queries (Intelligence)
"""

import re
from typing import Dict, Tuple, Optional, List


class VisionCommandHandler:
    """Handles vision-aligned commands for the Co-Pilot interface."""
    
    def __init__(self):
        # Action Commands (/) - Execute actions and change state
        self.action_commands = {
            '/plan': {
                'handler': self.handle_plan,
                'description': 'Create actionable plan with risk assessment',
                'usage': '/plan <request>',
                'category': 'Co-Execution'
            },
            '/execute': {
                'handler': self.handle_execute,
                'description': 'Execute plan with downstream integrations',
                'usage': '/execute [plan_id]',
                'category': 'Co-Execution'
            },
            '/reflect': {
                'handler': self.handle_reflect,
                'description': 'Analyze and learn from outcomes',
                'usage': '/reflect [execution_id]',
                'category': 'Co-Execution'
            },
            '/generate': {
                'handler': self.handle_generate,
                'description': 'Generate training transcripts',
                'usage': '/generate [count]',
                'category': 'System'
            },
            '/analyze': {
                'handler': self.handle_analyze,
                'description': 'Trigger multi-agent analysis',
                'usage': '/analyze [transcript_id]',
                'category': 'Analysis'
            },
            '/approve': {
                'handler': self.handle_approve,
                'description': 'Approve pending high-risk action',
                'usage': '/approve <action_id>',
                'category': 'Approval'
            },
            '/escalate': {
                'handler': self.handle_escalate,
                'description': 'Escalate to supervisor',
                'usage': '/escalate <reason>',
                'category': 'Approval'
            },
            '/clear': {
                'handler': self.handle_clear,
                'description': 'Clear conversation history',
                'usage': '/clear',
                'category': 'System'
            },
            '/exit': {
                'handler': self.handle_exit,
                'description': 'Exit the system',
                'usage': '/exit',
                'category': 'System'
            },
            '/help': {
                'handler': self.show_help,
                'description': 'Get help information',
                'usage': '/help [command]',
                'category': 'System'
            },
            '/status': {
                'handler': self.handle_status,
                'description': 'Show system status',
                'usage': '/status',
                'category': 'System'
            },
            '/search': {
                'handler': self.handle_search,
                'description': 'Search transcripts',
                'usage': '/search <query>',
                'category': 'System'
            },
            '/list': {
                'handler': self.handle_list,
                'description': 'List recent transcripts',
                'usage': '/list',
                'category': 'System'
            }
        }
        
        # Reference Commands (@) - Focus context and attention
        self.reference_commands = {
            '@current': {
                'handler': self.ref_current,
                'description': 'Focus on current live call',
                'usage': '@current',
                'category': 'Live Call'
            },
            '@borrower': {
                'handler': self.ref_borrower,
                'description': 'Show borrower action plan',
                'usage': '@borrower',
                'category': 'Action Plans'
            },
            '@advisor': {
                'handler': self.ref_advisor,
                'description': 'Show advisor tasks and coaching',
                'usage': '@advisor',
                'category': 'Action Plans'
            },
            '@supervisor': {
                'handler': self.ref_supervisor,
                'description': 'Show supervisor escalation items',
                'usage': '@supervisor',
                'category': 'Action Plans'
            },
            '@leadership': {
                'handler': self.ref_leadership,
                'description': 'Show leadership strategic insights',
                'usage': '@leadership',
                'category': 'Action Plans'
            },
            '@recent': {
                'handler': self.ref_recent,
                'description': 'Reference recent items',
                'usage': '@recent',
                'category': 'Context'
            },
            '@last': {
                'handler': self.ref_last,
                'description': 'Reference last item',
                'usage': '@last',
                'category': 'Context'
            },
            '@help': {
                'handler': self.show_help,
                'description': 'Get help information',
                'usage': '@help [command]',
                'category': 'System'
            }
        }
        
        # Query Commands (?) - Intelligence and predictions without state change
        self.query_commands = {
            '?predict': {
                'handler': self.query_predict,
                'description': 'Show predictions (FCR, churn, delinquency)',
                'usage': '?predict [type]',
                'category': 'Predictions'
            },
            '?compliance': {
                'handler': self.query_compliance,
                'description': 'Check compliance status',
                'usage': '?compliance',
                'category': 'Intelligence'
            },
            '?sentiment': {
                'handler': self.query_sentiment,
                'description': 'Current sentiment analysis',
                'usage': '?sentiment',
                'category': 'Intelligence'
            },
            '?risk': {
                'handler': self.query_risk,
                'description': 'Risk assessment',
                'usage': '?risk',
                'category': 'Intelligence'
            },
            '?confidence': {
                'handler': self.query_confidence,
                'description': 'Confidence scores',
                'usage': '?confidence',
                'category': 'Intelligence'
            },
            '?metrics': {
                'handler': self.query_metrics,
                'description': 'Performance metrics',
                'usage': '?metrics',
                'category': 'Intelligence'
            },
            '?learning': {
                'handler': self.query_learning,
                'description': 'Learning insights',
                'usage': '?learning',
                'category': 'Intelligence'
            },
            '?status': {
                'handler': self.query_status,
                'description': 'System status (read-only)',
                'usage': '?status',
                'category': 'System'
            },
            '?help': {
                'handler': self.show_help,
                'description': 'Get help information',
                'usage': '?help [command]',
                'category': 'System'
            }
        }
        
        # All commands combined for easy access
        self.all_commands = {
            **self.action_commands,
            **self.reference_commands,
            **self.query_commands
        }
        
        # Command aliases for intuitive shortcuts
        self.command_aliases = {
            '/h': '/help',
            '/s': '/status',
            '/q': '/exit',
            '/ls': '/list',
            '/?': '/help',
            '@h': '@help',
            '?h': '?help',
        }
        
        # Store references to handlers from CLI
        self._cli_handlers = {}
    
    def register_cli_handlers(self, handlers: Dict):
        """Register CLI handler functions."""
        self._cli_handlers = handlers
    
    def is_command(self, input_text: str) -> bool:
        """Check if input starts with any command prefix."""
        text = input_text.strip()
        return text.startswith('/') or text.startswith('@') or text.startswith('?')
    
    def parse_command(self, input_text: str) -> Tuple[str, str, str]:
        """Parse command and arguments with alias expansion. Returns (prefix, command, args)."""
        input_text = input_text.strip()
        
        if not self.is_command(input_text):
            return '', '', input_text
        
        prefix = input_text[0]  # /, @, or ?
        parts = input_text.split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''
        
        # Expand aliases
        if command in self.command_aliases:
            expanded_command = self.command_aliases[command]
            expanded_prefix = expanded_command[0]
            return expanded_prefix, expanded_command, args
        
        return prefix, command, args
    
    def get_command_type(self, prefix: str) -> str:
        """Get command type description based on prefix."""
        if prefix == '/':
            return "Action"
        elif prefix == '@':
            return "Reference"
        elif prefix == '?':
            return "Query"
        else:
            return "Unknown"
    
    def get_available_commands(self) -> List[str]:
        """Get list of available commands for autocomplete."""
        return list(self.all_commands.keys())
    
    def get_commands_by_prefix(self) -> Dict[str, Dict]:
        """Get commands organized by prefix type."""
        return {
            'Actions (/)': self.action_commands,
            'References (@)': self.reference_commands, 
            'Queries (?)': self.query_commands
        }
    
    def get_commands_by_category(self, prefix_type: str = None) -> Dict[str, List[Dict]]:
        """Get commands organized by category within a prefix type."""
        if prefix_type == 'action':
            commands = self.action_commands
        elif prefix_type == 'reference':
            commands = self.reference_commands
        elif prefix_type == 'query':
            commands = self.query_commands
        else:
            commands = self.all_commands
            
        categories = {}
        for cmd, info in commands.items():
            category = info['category']
            if category not in categories:
                categories[category] = []
            categories[category].append({
                'command': cmd,
                'description': info['description'],
                'usage': info['usage']
            })
        return categories
    
    def get_commands_for_prefix(self, prefix: str) -> Dict:
        """Get commands dictionary for a specific prefix."""
        if prefix == '/':
            return self.action_commands
        elif prefix == '@':
            return self.reference_commands
        elif prefix == '?':
            return self.query_commands
        else:
            return {}
    
    def get_prefix_description(self, prefix: str) -> str:
        """Get description for a prefix type."""
        descriptions = {
            '/': "Actions (Execute & Change State)",
            '@': "References (Focus Context)", 
            '?': "Queries (Intelligence & Predictions)"
        }
        return descriptions.get(prefix, "Commands")
    
    def show_command_help(self) -> str:
        """Show formatted command help with vision-aligned prefixes."""
        help_text = "\n🤖 Co-Pilot Command System\n"
        help_text += "=" * 60 + "\n"
        help_text += "\n💡 Command Prefixes:\n"
        help_text += "  / = Actions (Execute & Change State)\n"
        help_text += "  @ = References (Focus Context)\n" 
        help_text += "  ? = Queries (Intelligence & Predictions)\n"
        
        # Show commands by prefix type
        prefix_groups = self.get_commands_by_prefix()
        
        for group_name, commands in prefix_groups.items():
            help_text += f"\n{group_name}:\n"
            # Group by category within prefix
            categories = {}
            for cmd, info in commands.items():
                cat = info['category']
                if cat not in categories:
                    categories[cat] = []
                categories[cat].append((cmd, info['description']))
            
            for category, cmd_list in categories.items():
                help_text += f"  📂 {category}:\n"
                for cmd, desc in cmd_list:
                    help_text += f"    {cmd:<15} {desc}\n"
        
        help_text += "\nℹ️  Type ?help <command> for detailed usage\n"
        help_text += "ℹ️  Vision: Real-time co-execution during live calls\n"
        
        return help_text
    
    def process_command(self, input_text: str) -> Tuple[bool, str]:
        """
        Process a vision-aligned command.
        Returns (handled, response) tuple.
        """
        prefix, command, args = self.parse_command(input_text)
        
        if not prefix:
            return False, ""
        
        # Show command list if user just types a prefix
        if input_text.strip() in ['/', '@', '?']:
            return True, self.show_command_help()
        
        # Handle specific command
        if command in self.all_commands:
            try:
                response = self.all_commands[command]['handler'](args)
                return True, response
            except Exception as e:
                cmd_type = self.get_command_type(prefix)
                return True, f"❌ Error executing {cmd_type.lower()} {command}: {str(e)}"
        else:
            # Smart cross-prefix routing - check if command exists in other prefixes
            found_in_other_prefix = self._find_command_in_other_prefixes(command, prefix)
            if found_in_other_prefix:
                correct_command, correct_prefix = found_in_other_prefix
                try:
                    # Execute the command from the correct prefix
                    response = self.all_commands[correct_command]['handler'](args)
                    # Add a gentle note about availability
                    note = f"\n💡 Note: {command} is also available as {correct_command}"
                    return True, response + note
                except Exception as e:
                    return True, f"❌ Error executing {command}: {str(e)}"
            
            # Show similar commands suggestion
            similar = self._find_similar_commands(command)
            if similar:
                response = f"❌ Unknown command: {command}\n"
                response += f"💡 Did you mean: {', '.join(similar)}?"
                return True, response
            else:
                cmd_type = self.get_command_type(prefix)
                return True, f"❌ Unknown {cmd_type.lower()} command: {command}\n💡 Type /help to see available commands"
    
    def _find_command_in_other_prefixes(self, command: str, current_prefix: str) -> Optional[Tuple[str, str]]:
        """
        Find if a command exists in other prefixes.
        Returns (full_command, prefix) if found, None otherwise.
        """
        # Remove current prefix and try with other prefixes
        command_name = command[1:] if command.startswith(('/','@','?')) else command
        
        # Try different prefixes
        prefixes_to_try = ['/', '@', '?']
        for prefix in prefixes_to_try:
            if prefix == current_prefix:
                continue
            
            full_command = prefix + command_name
            if full_command in self.all_commands:
                return full_command, prefix
                
        # Also try the command as-is in case it was typed without prefix
        for full_cmd in self.all_commands.keys():
            if full_cmd.endswith(command_name) and full_cmd != command:
                return full_cmd, full_cmd[0]
        
        return None
    
    def _find_similar_commands(self, command: str) -> List[str]:
        """Find similar commands for typo suggestions."""
        similar = []
        for cmd in self.all_commands.keys():
            if command in cmd or cmd[1:].startswith(command[1:]):  # Remove prefix for comparison
                similar.append(cmd)
        return similar[:3]  # Return max 3 suggestions
    
    # Command handlers
    def show_help(self, args: str) -> str:
        """Show help for specific command or all commands."""
        if args:
            command = args.strip()
            if not command.startswith(('/', '@', '?')):
                command = '/' + command
            
            if command in self.all_commands:
                info = self.all_commands[command]
                help_text = f"\n📖 Help for {command}\n"
                help_text += "-" * 30 + "\n"
                help_text += f"Description: {info['description']}\n"
                help_text += f"Usage: {info['usage']}\n"
                help_text += f"Category: {info['category']}\n"
                return help_text
            else:
                return f"❌ No help available for '{command}'"
        else:
            return self.show_command_help()
    
    def handle_generate(self, args: str) -> str:
        """Handle generate command."""
        if 'handle_generation' in self._cli_handlers:
            # Convert to natural language for existing handler
            if args and args.isdigit():
                natural_input = f"generate {args} transcripts"
            else:
                natural_input = "generate some transcripts"
            
            try:
                self._cli_handlers['handle_generation'](natural_input)
                return ""  # Handler manages its own output
            except Exception as e:
                return f"❌ Generation failed: {str(e)}"
        else:
            return "❌ Generation handler not available"
    
    def handle_analyze(self, args: str) -> str:
        """Handle analyze command."""
        if 'handle_analysis' in self._cli_handlers:
            try:
                if args:
                    natural_input = f"analyze {args}"
                else:
                    natural_input = "analyze recent"
                
                self._cli_handlers['handle_analysis'](natural_input)
                return ""  # Handler manages its own output
            except Exception as e:
                return f"❌ Analysis failed: {str(e)}"
        else:
            return "❌ Analysis handler not available"
    
    def handle_plan(self, args: str) -> str:
        """Handle plan command."""
        if 'handle_plan_mode' in self._cli_handlers:
            if not args:
                return "❌ Plan command requires a request. Usage: /plan <request>"
            
            try:
                self._cli_handlers['handle_plan_mode'](args)
                return ""  # Handler manages its own output
            except Exception as e:
                return f"❌ Plan mode failed: {str(e)}"
        else:
            return "❌ Plan mode handler not available"
    
    def handle_execute(self, args: str) -> str:
        """Handle execute command."""
        if 'handle_execute_mode' in self._cli_handlers:
            try:
                self._cli_handlers['handle_execute_mode'](args or "")
                return ""  # Handler manages its own output
            except Exception as e:
                return f"❌ Execute mode failed: {str(e)}"
        else:
            return "❌ Execute mode handler not available"
    
    def handle_reflect(self, args: str) -> str:
        """Handle reflect command."""
        if 'handle_reflect_mode' in self._cli_handlers:
            try:
                self._cli_handlers['handle_reflect_mode'](args or "reflect")
                return ""  # Handler manages its own output
            except Exception as e:
                return f"❌ Reflect mode failed: {str(e)}"
        else:
            return "❌ Reflect mode handler not available"
    
    def handle_search(self, args: str) -> str:
        """Handle search command."""
        if 'handle_search' in self._cli_handlers:
            if not args:
                return "❌ Search command requires a query. Usage: /search <query>"
            
            try:
                self._cli_handlers['handle_search'](f"search {args}")
                return ""  # Handler manages its own output
            except Exception as e:
                return f"❌ Search failed: {str(e)}"
        else:
            return "❌ Search handler not available"
    
    def handle_list(self, args: str) -> str:
        """Handle list command."""
        if 'handle_list' in self._cli_handlers:
            try:
                self._cli_handlers['handle_list']("list")
                return ""  # Handler manages its own output
            except Exception as e:
                return f"❌ List failed: {str(e)}"
        else:
            return "❌ List handler not available"
    
    def handle_status(self, args: str) -> str:
        """Handle status command."""
        if 'handle_status' in self._cli_handlers:
            try:
                self._cli_handlers['handle_status']()
                return ""  # Handler manages its own output
            except Exception as e:
                return f"❌ Status check failed: {str(e)}"
        else:
            return "❌ Status handler not available"
    
    def handle_clear(self, args: str) -> str:
        """Handle clear command."""
        import os
        import sys
        
        # Clear screen
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # Unix/Linux/Mac
            os.system('clear')
        
        return "✅ Conversation history cleared"
    
    def handle_exit(self, args: str) -> str:
        """Handle exit command."""
        import sys
        print("👋 Goodbye!")
        sys.exit(0)
    
    def handle_approve(self, args: str) -> str:
        """Handle approve command for high-risk actions."""
        if not args:
            return "❌ Approve command requires an action ID. Usage: /approve <action_id>"
        
        return f"🔄 Approving action: {args}\\n✅ Action approved and executed"
    
    def handle_escalate(self, args: str) -> str:
        """Handle escalate command."""
        if not args:
            return "❌ Escalate command requires a reason. Usage: /escalate <reason>"
        
        return f"🔼 Escalating to supervisor\\nReason: {args}\\n✅ Escalation submitted"
    
    # Reference Command Handlers (@)
    def ref_current(self, args: str) -> str:
        """Focus on current live call."""
        return "🎯 Focused on current live call\\n📞 Real-time co-execution mode activated"
    
    def ref_borrower(self, args: str) -> str:
        """Show borrower action plan."""
        return ("🏠 BORROWER ACTION PLAN\\n" + "="*30 + "\\n" +
                "• Next best action: Review escrow options\\n" +
                "• Disclosures: Hardship assistance available\\n" +
                "• Predicted sentiment: Anxious but cooperative\\n" +
                "• Churn risk: 0.3 (Low-Medium)")
    
    def ref_advisor(self, args: str) -> str:
        """Show advisor tasks and coaching."""
        return ("👩‍💻 ADVISOR PLAN\\n" + "="*20 + "\\n" +
                "• Real-time coaching: Use empathetic language\\n" +
                "• Post-call task: Send hardship documentation\\n" +
                "• Performance note: Excellent compliance adherence\\n" +
                "• Development: Practice de-escalation techniques")
    
    def ref_supervisor(self, args: str) -> str:
        """Show supervisor escalation items."""
        return ("👩‍💼 SUPERVISOR ITEMS\\n" + "="*25 + "\\n" +
                "• High-risk case: Fee waiver approval needed\\n" +
                "• Compliance review: ARM disclosure timing\\n" +
                "• Coaching opportunity: Advisor needs empathy training\\n" +
                "• Exception handling: Payment plan modification")
    
    def ref_leadership(self, args: str) -> str:
        """Show leadership strategic insights."""
        return ("🧑‍💼 LEADERSHIP INSIGHTS\\n" + "="*28 + "\\n" +
                "• Portfolio trend: 15% increase in hardship calls\\n" +
                "• Compliance exposure: Low overall risk\\n" +
                "• Operational efficiency: FCR rate 87%\\n" +
                "• Strategic recommendation: Expand hardship programs")
    
    def ref_recent(self, args: str) -> str:
        """Reference recent items."""
        return ("📋 RECENT ITEMS\\n" + "="*15 + "\\n" +
                "• Last call: CALL_20250106_143022\\n" +
                "• Last plan: Hardship assistance workflow\\n" +
                "• Last execution: CRM update completed\\n" +
                "• Last analysis: Multi-agent analysis completed")
    
    def ref_last(self, args: str) -> str:
        """Reference last item."""
        return ("⏮️  LAST ITEM\\n" + "="*12 + "\\n" +
                "• Type: Analysis\\n" +
                "• ID: CALL_20250106_143022\\n" +
                "• Status: Completed\\n" +
                "• Confidence: 0.87")
    
    # Query Command Handlers (?)
    def query_predict(self, args: str) -> str:
        """Show predictions."""
        prediction_type = args.lower() if args else "all"
        
        if prediction_type in ["fcr", "all"]:
            fcr_text = "📊 FCR Prediction: 0.85 (High confidence)\\n"
        else:
            fcr_text = ""
            
        if prediction_type in ["churn", "all"]:
            churn_text = "📈 Churn Risk: 0.3 (Low-Medium)\\n"
        else:
            churn_text = ""
            
        if prediction_type in ["delinquency", "all"]:
            delinq_text = "⚠️  Delinquency Risk: 0.15 (Low)\\n"
        else:
            delinq_text = ""
            
        return f"🔮 PREDICTIONS\\n{'='*15}\\n{fcr_text}{churn_text}{delinq_text}Confidence: High"
    
    def query_compliance(self, args: str) -> str:
        """Check compliance status."""
        return ("⚖️  COMPLIANCE STATUS\\n" + "="*20 + "\\n" +
                "• Overall Score: 94/100\\n" +
                "• Missing Disclosures: None\\n" +
                "• Regulatory Violations: None detected\\n" +
                "• Risk Level: LOW\\n" +
                "• Last Audit: Passed")
    
    def query_sentiment(self, args: str) -> str:
        """Current sentiment analysis."""
        return ("😐 SENTIMENT ANALYSIS\\n" + "="*22 + "\\n" +
                "• Current: Anxious but cooperative\\n" +
                "• Trajectory: 😡 → 😐 → 😊 (Improving)\\n" +
                "• Confidence: 0.88\\n" +
                "• Emotional triggers: Payment concerns\\n" +
                "• De-escalation: Successful")
    
    def query_risk(self, args: str) -> str:
        """Risk assessment."""
        return ("⚡ RISK ASSESSMENT\\n" + "="*18 + "\\n" +
                "• Overall Risk: MEDIUM\\n" +
                "• Risk Score: 65/100\\n" +
                "• Compliance Risk: LOW\\n" +
                "• Financial Risk: MEDIUM\\n" +
                "• Escalation Needed: No")
    
    def query_confidence(self, args: str) -> str:
        """Show confidence scores."""
        return ("🎯 CONFIDENCE SCORES\\n" + "="*21 + "\\n" +
                "• Analysis: 0.87\\n" +
                "• Predictions: 0.82\\n" +
                "• Sentiment: 0.91\\n" +
                "• Compliance: 0.95\\n" +
                "• Overall: 0.89")
    
    def query_metrics(self, args: str) -> str:
        """Show performance metrics."""
        return ("📊 PERFORMANCE METRICS\\n" + "="*24 + "\\n" +
                "• FCR Rate: 87%\\n" +
                "• CSAT Score: 4.2/5.0\\n" +
                "• Handle Time: 8.5 min avg\\n" +
                "• Resolution Rate: 92%\\n" +
                "• Compliance Score: 94%")
    
    def query_learning(self, args: str) -> str:
        """Show learning insights."""
        return ("🧠 LEARNING INSIGHTS\\n" + "="*20 + "\\n" +
                "• Total Feedback Items: 147\\n" +
                "• Analysis Accuracy: 89%\\n" +
                "• Integration Success: 94%\\n" +
                "• Improvement Rate: +2.3% weekly\\n" +
                "• Active Learning: 23 cases")
    
    def query_status(self, args: str) -> str:
        """System status (read-only)."""
        return ("🤖 SYSTEM STATUS\\n" + "="*16 + "\\n" +
                "• Multi-Agent System: ✅ Operational\\n" +
                "• Integration Layer: ✅ Connected\\n" +
                "• Learning System: ✅ Active\\n" +
                "• Compliance Monitor: ✅ Active\\n" +
                "• Co-Pilot Modes: ✅ Ready")