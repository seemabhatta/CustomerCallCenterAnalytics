"""
Interactive Command Selector for Vision-Aligned Co-Pilot Interface
Provides typeahead and arrow key navigation for command selection.
"""

import sys
from typing import Dict, List, Tuple, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from prompt_toolkit import prompt
from prompt_toolkit.keys import Keys
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import Frame
from prompt_toolkit.formatted_text import FormattedText


class InteractiveCommandSelector:
    """Interactive command selector with typeahead and navigation."""
    
    def __init__(self, commands_handler):
        """Initialize with command handler."""
        self.commands_handler = commands_handler
        self.console = Console()
        self.selected_index = 0
        self.filter_text = ""
        
    def show_prefix_commands(self, prefix: str) -> Optional[str]:
        """
        Show interactive command selector for a prefix.
        Returns selected command or None if cancelled.
        """
        # Get commands for this prefix
        commands_data = self._get_commands_for_prefix(prefix)
        
        if not commands_data:
            return None
            
        # Try rich interactive mode first
        if self._supports_rich_interaction():
            return self._show_rich_selector(prefix, commands_data)
        else:
            return self._show_simple_selector(prefix, commands_data)
    
    def _get_commands_for_prefix(self, prefix: str) -> List[Dict]:
        """Get structured command data for a prefix."""
        commands_data = []
        
        if prefix == '/':
            command_dict = self.commands_handler.action_commands
            header = "Actions (/) - Execute & Change State"
        elif prefix == '@':
            command_dict = self.commands_handler.reference_commands  
            header = "References (@) - Focus Context"
        elif prefix == '?':
            command_dict = self.commands_handler.query_commands
            header = "Queries (?) - Intelligence & Predictions"
        else:
            return []
            
        for cmd, info in command_dict.items():
            commands_data.append({
                'command': cmd,
                'description': info['description'],
                'usage': info['usage'],
                'category': info['category']
            })
            
        return sorted(commands_data, key=lambda x: x['command'])
    
    def _supports_rich_interaction(self) -> bool:
        """Check if terminal supports rich interactive features."""
        try:
            # Check if we're in a proper terminal
            return sys.stdin.isatty() and sys.stdout.isatty()
        except:
            return False
    
    def _show_rich_selector(self, prefix: str, commands_data: List[Dict]) -> Optional[str]:
        """Show rich interactive selector."""
        try:
            # Create rich table for display
            table = self._create_command_table(prefix, commands_data)
            
            with self.console.capture() as capture:
                self.console.print(table)
            
            # Show the table
            self.console.print(table)
            
            # Show instructions
            instructions = Text("⬆⬇ Navigate  ⏎ Select  ESC Cancel  Type to filter", style="dim")
            self.console.print(Align.center(instructions))
            
            # Get user input with simple prompt for now
            # (Full interactive navigation would require more complex prompt_toolkit setup)
            try:
                selection = prompt("\nSelect command (type name or number, or press Enter to cancel): ", 
                                 completer=self._create_completer(commands_data))
                
                # Handle empty input (cancel)
                if not selection.strip():
                    return None
                
                selection = selection.strip()
                
                # Handle numeric selection
                if selection.isdigit():
                    idx = int(selection) - 1
                    if 0 <= idx < len(commands_data):
                        return commands_data[idx]['command']
                
                # Handle command name selection
                for cmd_data in commands_data:
                    if cmd_data['command'] == selection or cmd_data['command'] == prefix + selection:
                        return cmd_data['command']
                        
                # Handle partial matches
                matches = [cmd for cmd in commands_data if selection.lower() in cmd['command'].lower()]
                if len(matches) == 1:
                    return matches[0]['command']
                    
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[dim]Cancelled[/dim]")
                return None
                
        except Exception as e:
            # Fallback to simple selector
            return self._show_simple_selector(prefix, commands_data)
            
        return None
    
    def _show_simple_selector(self, prefix: str, commands_data: List[Dict]) -> Optional[str]:
        """Show simple text-based selector for basic terminals."""
        header_map = {
            '/': "Actions (Execute & Change State)",
            '@': "References (Focus Context)",
            '?': "Queries (Intelligence & Predictions)"
        }
        
        print(f"\n{header_map.get(prefix, 'Commands')}:")
        print("-" * 50)
        
        for i, cmd_data in enumerate(commands_data, 1):
            print(f"  {i:2}. {cmd_data['command']:<12} - {cmd_data['description']}")
        
        print(f"\nEnter command number (1-{len(commands_data)}) or command name (or press Enter to cancel):")
        
        try:
            selection = input("> ").strip()
            
            # Handle empty input (cancel)
            if not selection:
                return None
            
            # Handle numeric selection
            if selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(commands_data):
                    return commands_data[idx]['command']
            
            # Handle command name
            if not selection.startswith(prefix):
                selection = prefix + selection
                
            for cmd_data in commands_data:
                if cmd_data['command'] == selection:
                    return cmd_data['command']
                    
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled")
            
        return None
    
    def _create_command_table(self, prefix: str, commands_data: List[Dict]) -> Panel:
        """Create rich table for command display."""
        
        header_map = {
            '/': "Actions (/) - Execute & Change State",
            '@': "References (@) - Focus Context", 
            '?': "Queries (?) - Intelligence & Predictions"
        }
        
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Command", style="cyan", width=12)
        table.add_column("Description", style="white")
        
        for i, cmd_data in enumerate(commands_data, 1):
            command_text = f"{i:2}. {cmd_data['command']}"
            table.add_row(command_text, cmd_data['description'])
        
        return Panel(
            table,
            title=header_map.get(prefix, "Commands"),
            title_align="left",
            border_style="blue"
        )
    
    def _create_completer(self, commands_data: List[Dict]):
        """Create command completer for prompt_toolkit."""
        from prompt_toolkit.completion import WordCompleter
        
        # Extract command names without prefix for completion
        command_names = []
        for cmd_data in commands_data:
            # Add both full command and without prefix
            command_names.append(cmd_data['command'])
            command_names.append(cmd_data['command'][1:])  # Remove prefix
            
        return WordCompleter(command_names, ignore_case=True)
    
    def show_command_usage(self, command: str) -> None:
        """Show usage information for a command."""
        if command in self.commands_handler.all_commands:
            cmd_info = self.commands_handler.all_commands[command]
            
            if self._supports_rich_interaction():
                usage_panel = Panel(
                    f"[bold]{cmd_info['usage']}[/bold]\n\n"
                    f"Description: {cmd_info['description']}\n"
                    f"Category: {cmd_info['category']}",
                    title="Usage",
                    border_style="green"
                )
                self.console.print(usage_panel)
            else:
                print(f"\nUsage: {cmd_info['usage']}")
                print(f"Description: {cmd_info['description']}")
                print(f"Category: {cmd_info['category']}\n")


def create_command_selector(commands_handler) -> InteractiveCommandSelector:
    """Factory function to create command selector."""
    return InteractiveCommandSelector(commands_handler)