#!/usr/bin/env python3
"""
CLI Agent - BORROWER-focused Claude Code for Advisors
A thin REST client that calls the advisor API for all operations.
Follows microservices principle: CLI → API → Service → Agent
NO FALLBACK LOGIC - fails fast with clear errors and guidance.
"""
import os
import sys
import requests
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

# Initialize CLI and console
app = typer.Typer(
    name="agent",
    help="BORROWER-focused Claude Code for mortgage customer advisors",
    add_completion=False
)
console = Console()

# API configuration
DEFAULT_API_URL = os.getenv("CCANALYTICS_API_URL", "http://localhost:8000")


def display_banner(advisor_id: str, session_id: str, context: str):
    """Display startup banner with session information."""
    table = Table(show_header=False, box=None)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("🧑‍💼 Advisor", advisor_id)
    table.add_row("📋 Session", session_id)
    table.add_row("📄 Context", context)
    table.add_row("🎯 Focus", "BORROWER workflows only")

    console.print(Panel(
        table,
        title="[bold blue]Advisor Agent - BORROWER Workflow Assistant[/bold blue]",
        border_style="blue"
    ))
    console.print("[dim]Type your requests naturally. I'll help you work through borrower workflows step-by-step.[/dim]")
    console.print("[dim]Commands: 'list workflows', 'start <workflow>', 'status', 'help', 'end session'[/dim]\n")


class AdvisorCLI:
    """REST client for advisor chat interactions."""

    def __init__(self, api_url: str = DEFAULT_API_URL):
        """Initialize REST client.

        Args:
            api_url: Base URL for the API server
        """
        self.api_url = api_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def chat(self, advisor_id: str, message: str, session_id: Optional[str] = None,
             transcript_id: Optional[str] = None, plan_id: Optional[str] = None) -> dict:
        """Send a chat message to the advisor API.

        Args:
            advisor_id: Advisor identifier
            message: Chat message
            session_id: Optional session to resume
            transcript_id: Optional transcript context
            plan_id: Optional plan context

        Returns:
            API response with agent response and session info

        Raises:
            Exception: If API call fails (NO FALLBACK)
        """
        try:
            response = self.session.post(
                f"{self.api_url}/api/v1/advisor/chat",
                json={
                    "advisor_id": advisor_id,
                    "message": message,
                    "session_id": session_id,
                    "transcript_id": transcript_id,
                    "plan_id": plan_id
                },
                timeout=30
            )

            if response.status_code != 200:
                error_msg = response.text
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', error_msg)
                except:
                    pass
                raise Exception(f"API error ({response.status_code}): {error_msg}")

            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to API at {self.api_url}: {str(e)}")


@app.command()
def main(
    advisor_id: str = typer.Option(..., "--advisor-id", help="Advisor identifier (required)"),
    session_id: Optional[str] = typer.Option(None, "--session-id", help="Resume existing session"),
    transcript_id: Optional[str] = typer.Option(None, "--transcript-id", help="Pre-load transcript context"),
    plan_id: Optional[str] = typer.Option(None, "--plan-id", help="Pre-load plan context"),
    workflow_type: str = typer.Option("BORROWER", "--workflow-type", help="Workflow type (must be BORROWER)"),
    api_url: str = typer.Option(DEFAULT_API_URL, "--api-url", help="API server URL")
):
    """
    Start an interactive advisor session for BORROWER workflows.

    This is a Claude Code-like assistant that helps advisors work through
    borrower action items step-by-step via REST API calls.

    Examples:
      agent --advisor-id ADV001 --transcript-id CALL_46F4C703 --workflow-type BORROWER
      agent --advisor-id ADV001 --session-id SID-abc123ef --workflow-type BORROWER
    """

    # Validate workflow type (must be BORROWER for advisor access)
    if workflow_type != "BORROWER":
        console.print("[red]Error: Only BORROWER workflow type is supported for advisors[/red]")
        console.print("[dim]Advisors can only access borrower-related workflows for security and role separation[/dim]")
        raise typer.Exit(1)

    # Validate context options
    if transcript_id and plan_id:
        console.print("[red]Error: Provide either --transcript-id or --plan-id, not both[/red]")
        console.print("[dim]Choose one context source to avoid conflicts[/dim]")
        raise typer.Exit(1)

    try:
        # Initialize REST client
        client = AdvisorCLI(api_url)

        # Test API connection and get initial session
        context = "none yet"
        if transcript_id:
            context = f"Transcript {transcript_id}"
        elif plan_id:
            context = f"Plan {plan_id}"

        # Start with a simple hello to establish session
        try:
            result = client.chat(
                advisor_id=advisor_id,
                message="Hello, I'm ready to work on borrower workflows.",
                session_id=session_id,
                transcript_id=transcript_id,
                plan_id=plan_id
            )
            current_session_id = result["session_id"]

        except Exception as e:
            console.print(f"[red]Failed to connect to API: {str(e)}[/red]")
            console.print(f"[dim]Make sure the API server is running at {api_url}[/dim]")
            raise typer.Exit(1)

        # Display banner
        display_banner(advisor_id, current_session_id, context)

        # Display initial response
        console.print(f"[bold]Agent:[/bold] {result['response']}")

        # Run chat loop
        chat_loop(client, advisor_id, current_session_id, transcript_id, plan_id)

    except KeyboardInterrupt:
        console.print(f"\n[yellow]Session interrupted by user[/yellow]")
        console.print(f"[dim]Session saved. Resume with: agent --advisor-id {advisor_id} --session-id {current_session_id if 'current_session_id' in locals() else 'unknown'} --workflow-type BORROWER[/dim]")
    except Exception as e:
        console.print(f"[red]Fatal error: {str(e)}[/red]")
        console.print("[dim]NO FALLBACK - System failed as designed. Check configuration and try again.[/dim]")
        raise typer.Exit(1)


def chat_loop(client: AdvisorCLI, advisor_id: str, session_id: str, transcript_id: Optional[str], plan_id: Optional[str]):
    """
    Main conversation loop - like Claude Code's interaction model.
    Uses REST API calls to communicate with the advisor agent.
    """

    # Initial proactive message based on context
    if plan_id or transcript_id:
        console.print("[bold]Agent:[/bold] Let me check what borrower workflows are available...")

        # Agent proactively fetches and displays workflows
        if plan_id:
            initial_message = f"Show me the borrower workflows from plan {plan_id}"
        else:
            initial_message = "Show me available borrower workflows from the loaded context"

        try:
            initial_result = client.chat(
                advisor_id=advisor_id,
                message=initial_message,
                session_id=session_id,
                transcript_id=transcript_id,
                plan_id=plan_id
            )
            if initial_result.get('response'):
                console.print(f"[bold]Agent:[/bold] {initial_result['response']}")
        except Exception as e:
            console.print(f"[yellow]Could not load initial workflows: {str(e)}[/yellow]")
            console.print("[dim]You can manually request workflows with 'list workflows' or provide a plan/transcript ID[/dim]")
    else:
        console.print("[bold]Agent:[/bold] Hello! I'm here to help you work through borrower workflows step-by-step.")
        console.print("Please provide a plan ID or transcript ID to get started, or say 'help' to see what I can do.")

    # Main conversation loop
    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")

            # Check for exit commands
            if user_input.lower() in ["exit", "quit", "end session", "bye", "goodbye"]:
                console.print("\n[bold]Agent:[/bold] Session ended. Your progress has been saved.")
                console.print(f"[dim]Resume anytime with: agent --advisor-id {advisor_id} --session-id {session_id} --workflow-type BORROWER[/dim]")
                break

            # Check for help commands
            if user_input.lower() in ["help", "?", "commands"]:
                console.print("\n[bold]Available Commands:[/bold]")
                console.print("• [cyan]list workflows[/cyan] - Show available borrower workflows")
                console.print("• [cyan]start <workflow name>[/cyan] - Begin working on a specific workflow")
                console.print("• [cyan]execute step <number>[/cyan] - Execute a specific step")
                console.print("• [cyan]skip step <number> <reason>[/cyan] - Skip a step with reason")
                console.print("• [cyan]status[/cyan] or [cyan]where are we[/cyan] - Show current progress")
                console.print("• [cyan]go back[/cyan] - Navigate to previous step")
                console.print("• [cyan]approve now[/cyan] - Approve high-risk operations")
                console.print("• [cyan]switch to plan <id>[/cyan] - Change context to different plan")
                console.print("• [cyan]end session[/cyan] - Save and exit")
                console.print("\n[dim]Or just describe what you want to do in natural language![/dim]")
                continue

            # Process message through API (fully agentic - agent decides what to do)
            console.print("[dim]Processing request...[/dim]")
            result = client.chat(
                advisor_id=advisor_id,
                message=user_input,
                session_id=session_id,
                transcript_id=transcript_id,
                plan_id=plan_id
            )

            # Display agent's response
            response = result.get('response', '')
            if response:
                console.print(f"\n[bold]Agent:[/bold] {response}")
            else:
                console.print(f"\n[bold]Agent:[/bold] I processed your request but don't have a specific response. Is there anything else you'd like to do?")

        except KeyboardInterrupt:
            raise  # Re-raise to be caught by main
        except Exception as e:
            console.print(f"\n[red]Error processing request: {str(e)}[/red]")

            # Provide helpful guidance based on error type
            if "not found" in str(e).lower():
                console.print("[dim]Try 'list workflows' to see available options or check your IDs[/dim]")
            elif "access denied" in str(e).lower():
                console.print("[dim]You can only access borrower workflows. Use 'list workflows' to see what's available[/dim]")
            elif "required" in str(e).lower():
                console.print("[dim]Please provide the required information or say 'help' for guidance[/dim]")
            else:
                console.print("[dim]NO FALLBACK - Please try rephrasing your request or say 'help' for available commands[/dim]")


if __name__ == "__main__":
    app()