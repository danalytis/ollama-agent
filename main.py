#!/usr/bin/env python3
"""
Ollama AI Agent - Main Script
A beautiful, interactive AI coding assistant with function calling capabilities.
"""

import sys
import argparse
from pathlib import Path

# Add current directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import OllamaAgent
from core.config import AgentConfig
from utils.terminal import check_ollama_connection
from utils.display import rich_print


def main():
    parser = argparse.ArgumentParser(
        description="Ollama AI Agent with function calling"
    )
    parser.add_argument("--prompt", type=str, help="Single user input prompt")
    parser.add_argument(
        "--interactive", action="store_true", help="Run in interactive mode"
    )
    parser.add_argument(
        "--verbose", action="store_true", help="Show detailed debug output"
    )
    parser.add_argument(
        "--model", type=str, default="qwen2.5-coder:7b", help="Ollama model to use"
    )
    parser.add_argument(
        "--list-models", action="store_true", help="List available Ollama models"
    )
    parser.add_argument(
        "--typing-speed",
        type=float,
        default=0.03,
        help="Typing animation speed (0.005-0.2)",
    )
    parser.add_argument(
        "--no-typing", action="store_true", help="Disable typing animation"
    )
    parser.add_argument(
        "--no-syntax", action="store_true", help="Disable syntax highlighting"
    )
    parser.add_argument(
        "--no-rich", action="store_true", help="Disable Rich formatting entirely"
    )
    parser.add_argument(
        "--api-base", 
        type=str, 
        default="http://localhost:11434",
        help="Ollama API base URL (for remote connections)"
    )
    parser.add_argument(
        "--prompt-type",
        type=str,
        default="default",
        help="System prompt type (default, senior_dev, project_architect, debugging_expert, code_reviewer, rapid_prototyper)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.1,
        help="Model temperature (0.0-2.0, creativity level)"
    )
    parser.add_argument(
        "--working-dir",
        type=str,
        help="Set initial working directory"
    )
    parser.add_argument(
        "--unsafe-mode",
        action="store_true",
        help="Disable directory safety restrictions (USE WITH CAUTION)"
    )

    args = parser.parse_args()

    # Create configuration
    config = AgentConfig(
        model=args.model,
        verbose=args.verbose,
        typing_speed=args.typing_speed,
        typing_enabled=not args.no_typing,
        syntax_highlighting=not args.no_syntax,
        rich_enabled=not args.no_rich,
        api_base=args.api_base,
        current_prompt=args.prompt_type,
        temperature=args.temperature,
        safe_mode=not args.unsafe_mode,
    )

    # Handle initial working directory change
    if args.working_dir:
        from utils.filesystem import safe_change_directory
        success, message = safe_change_directory(
            args.working_dir, 
            config.safe_mode,
            config.allowed_base_dirs,
            force=args.unsafe_mode
        )
        if success:
            rich_print(message, style="green")
        else:
            rich_print(message, style="red")
            if not args.unsafe_mode:
                rich_print("💡 Use --unsafe-mode to override safety restrictions", style="dim")
            sys.exit(1)

    # Validate typing speed
    if not (0.005 <= config.typing_speed <= 0.2):
        rich_print("Error: typing speed must be between 0.005 and 0.2", style="red")
        sys.exit(1)

    # Validate temperature
    if not (0.0 <= config.temperature <= 2.0):
        rich_print("Error: temperature must be between 0.0 and 2.0", style="red")
        sys.exit(1)

    # Validate API base URL
    if not config.api_base.startswith(('http://', 'https://')):
        rich_print("Error: API base must start with http:// or https://", style="red")
        sys.exit(1)

    # Handle list models command
    if args.list_models:
        agent = OllamaAgent(config)
        agent.list_models()
        return

    # Check if Ollama is running
    if not check_ollama_connection(config.api_base):
        rich_print(
            f"Error: Cannot connect to Ollama at {config.api_base}",
            style="red",
        )
        if config.api_base == "http://localhost:11434":
            rich_print("Make sure Ollama is running with: ollama serve", style="red")
        else:
            rich_print("Make sure the remote Ollama instance is accessible", style="red")
        sys.exit(1)

    # Create and run agent
    agent = OllamaAgent(config)

    if args.interactive:
        agent.run_interactive()
    else:
        if not args.prompt:
            rich_print(
                "error: must provide --prompt or use --interactive mode", style="red"
            )
            sys.exit(1)

        agent.run_single_prompt(args.prompt)


if __name__ == "__main__":
    main()