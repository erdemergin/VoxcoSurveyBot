"""
Main entry point for the Gemini Chatbot application.
"""
import os
import sys
import json
import requests
from typing import Optional, List, Dict, Any

import typer
from rich.console import Console
from rich.markdown import Markdown

from . import config
from .utils.gemini_client import GeminiClient

# Initialize rich console for formatted output
console = Console()
app = typer.Typer(help="Gemini-powered chatbot")

def display_response(text: str) -> None:
    """
    Display the AI response with formatting if enabled.
    
    Args:
        text: The text to display
    """
    if config.ENABLE_RICH_FORMATTING:
        console.print(Markdown(text))
    else:
        print(f"{config.AI_RESPONSE_PREFIX}{text}")

def display_welcome() -> None:
    """Display welcome message and instructions."""
    console.print("[bold blue]Welcome to Voxco Chatbot![/bold blue]")
    console.print(f"Using model: [green]{config.GEMINI_MODEL}[/green]")
    console.print("---")

@app.command()
def chat(
    api_key: Optional[str] = typer.Option(
        None, "--api-key", "-k", help="Gemini API key (overrides .env file)"
    ),
    model: str = typer.Option(
        config.GEMINI_MODEL, "--model", "-m", help="Gemini model to use"
    ),
    system_prompt: Optional[str] = typer.Option(
        None, "--system-prompt", "-s", help="System prompt to set AI behavior (overrides .env file)"
    ),
) -> None:
    """
    Start an interactive chat session with the Gemini AI.
    Type 'file <filename>' to attach a file to your message.
    """
    # Set API key from parameter if provided
    if api_key:
        os.environ["GEMINI_API_KEY"] = api_key
    
    # Set model from parameter if provided
    if model != config.GEMINI_MODEL:
        os.environ["GEMINI_MODEL"] = model
    
    # Set system prompt from parameter if provided
    if system_prompt:
        os.environ["SYSTEM_PROMPT"] = system_prompt
    
    try:
        # Initialize the Gemini client
        client = GeminiClient()
        
        # Display welcome message
        display_welcome()
        console.print("[dim]Type 'file <filename>' to attach a file to your message.[/dim]")
        console.print("[dim]Type 'help' for more information.[/dim]")
        console.print("---")
                
        # Main chat loop
        while True:
            # Get user input
            user_input = input(f"{config.USER_PROMPT_PREFIX}")
            
            # Check for exit command
            if user_input.lower().strip() in config.EXIT_COMMANDS:
                console.print("[bold blue]Goodbye![/bold blue]")
                break
                        
            # Check for file attachment command
            if user_input.lower().startswith("file "):
                file_path = user_input[5:].strip()
                if not file_path:
                    console.print("[bold red]Error: Please specify a file name[/bold red]")
                    continue
                
                if not os.path.exists(file_path):
                    console.print(f"[bold red]Error: File not found: {file_path}[/bold red]")
                    continue
                
                # Process file
                try:
                    response = client.process_file(file_path)
                    display_response(response)
                except Exception as e:
                    console.print(f"[bold red]Error: {str(e)}[/bold red]")
                continue
            
            # Regular message handling
            try:
                response = client.send_message(user_input)
                display_response(response)
            except Exception as e:
                console.print(f"[bold red]Error: {str(e)}[/bold red]")
    
    except ValueError as e:
        # This will catch the API key validation error
        console.print(f"[bold red]Error: {str(e)}[/bold red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error: {str(e)}[/bold red]")
        sys.exit(1)

@app.command()
def version() -> None:
    """Display the version of the chatbot."""
    from . import __version__
    console.print(f"Gemini Chatbot v{__version__}")

if __name__ == "__main__":
    app() 