"""
Display utilities and formatting functions
"""

import time
from typing import List, Tuple, Optional, Dict
from utils.terminal import is_terminal_compatible, get_terminal_width

# Rich imports with fallback
try:
    from rich.console import Console
    from rich.syntax import Syntax
    from rich.panel import Panel
    from rich.text import Text
    from rich.table import Table

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# Initialize console
RICH_ENABLED = RICH_AVAILABLE and is_terminal_compatible()
console = Console(width=get_terminal_width()) if RICH_ENABLED else None


def rich_print(
    text: str,
    style: Optional[str] = None,
    panel: bool = False,
    title: Optional[str] = None,
) -> None:
    """Print with rich formatting if available, fallback to regular print"""
    if RICH_ENABLED and console:
        if panel:
            console.print(Panel(text, title=title, style=style))
        else:
            console.print(text, style=style)
    else:
        print(text)


def print_syntax_highlighted(
    code: str, language: str = "python", enabled: bool = True
) -> None:
    """Print code with syntax highlighting"""
    if enabled and RICH_ENABLED and console:
        try:
            # Limit width to prevent terminal corruption
            width = min(get_terminal_width() - 4, 120)
            syntax = Syntax(
                code,
                language,
                theme="monokai",
                line_numbers=True,
                word_wrap=True,
                code_width=width,
            )
            console.print(syntax)
        except Exception:
            # Fallback if syntax highlighting fails
            print_code_plain(code, language)
    else:
        print_code_plain(code, language)


def print_code_plain(code: str, language: str) -> None:
    """Print code without syntax highlighting but with line numbers"""
    print(f"Content ({language}):")
    print("-" * 40)
    lines = code.split("\n")
    for i, line in enumerate(lines, 1):
        print(f"{i:3d} | {line}")
    print("-" * 40)


def print_file_table(
    files_data: List[Tuple[str, str, str]], enabled: bool = True
) -> None:
    """Print file listing as a table"""
    if enabled and RICH_ENABLED and console:
        try:
            table = Table(title="📁 Directory Contents", width=get_terminal_width() - 4)
            table.add_column("Name", style="cyan", no_wrap=False, max_width=40)
            table.add_column("Type", style="magenta", width=10)
            table.add_column("Size", justify="right", style="green", width=12)

            for name, file_type, size in files_data:
                icon = "📁" if file_type == "directory" else "📄"
                # Truncate long filenames
                display_name = name if len(name) <= 35 else name[:32] + "..."
                table.add_row(f"{icon} {display_name}", file_type, size)

            console.print(table)
        except Exception:
            print_file_list_plain(files_data)
    else:
        print_file_list_plain(files_data)


def print_file_list_plain(files_data: List[Tuple[str, str, str]]) -> None:
    """Print file listing without rich formatting"""
    print("📁 Directory Contents:")
    print("-" * 60)
    for name, file_type, size in files_data:
        icon = "📁" if file_type == "directory" else "📄"
        print(f"{icon} {name:<30} {file_type:<10} {size:>10}")
    print("-" * 60)


def print_prompts_table(prompts: Dict[str, str], current_prompt: str, enabled: bool = True) -> None:
    """Print available system prompts as a table"""
    if enabled and RICH_ENABLED and console:
        try:
            table = Table(
                title="📋 Available System Prompts", width=get_terminal_width() - 4
            )
            table.add_column("Name", style="cyan", width=18)
            table.add_column("Description", style="white", no_wrap=False)
            table.add_column("Status", style="green", width=12)

            for name, description in prompts.items():
                status = "← current" if name == current_prompt else "available"
                icon = "🎯" if name == current_prompt else "📋"
                table.add_row(f"{icon} {name}", description, status)

            console.print(table)
        except Exception:
            print_prompts_plain(prompts, current_prompt)
    else:
        print_prompts_plain(prompts, current_prompt)


def print_prompts_plain(prompts: Dict[str, str], current_prompt: str) -> None:
    """Print system prompts without rich formatting"""
    print("📋 Available System Prompts:")
    print("-" * 80)
    for name, description in prompts.items():
        indicator = " ← current" if name == current_prompt else ""
        icon = "🎯" if name == current_prompt else "📋"
        print(f"{icon} {name:<18} {description}{indicator}")
    print("-" * 80)


def print_model_params_table(params_data: Dict[str, str], enabled: bool = True) -> None:
    """Print model parameters as a table"""
    if enabled and RICH_ENABLED and console:
        try:
            table = Table(
                title="🎛️ Model Parameters", width=get_terminal_width() - 4
            )
            table.add_column("Parameter", style="bold blue", width=20)
            table.add_column("Value & Description", style="white", no_wrap=False)

            for param, value_desc in params_data.items():
                table.add_row(param, value_desc)

            console.print(table)
        except Exception:
            print_model_params_plain(params_data)
    else:
        print_model_params_plain(params_data)


def print_model_params_plain(params_data: Dict[str, str]) -> None:
    """Print model parameters without rich formatting"""
    print("🎛️ Model Parameters:")
    print("-" * 80)
    for param, value_desc in params_data.items():
        print(f"{param}: {value_desc}")
    print("-" * 80)


def typewriter_print(
    text: str, speed: float = 0.03, enabled: bool = True, style: Optional[str] = None
) -> None:
    """Print text with typewriter effect"""
    if not enabled or speed <= 0:
        rich_print(text, style=style)
        return

    for char in text:
        if RICH_ENABLED and console and style:
            console.print(char, end="", style=style)
        else:
            print(char, end="", flush=True)

        if char != "\n":
            time.sleep(speed)

    print()  # Final newline


def format_help_text(rich_enabled: bool = True) -> None:
    """Display help text"""
    help_content = """
📚 Available slash commands:

Basic Commands:
  /quit, /exit, /q     - Exit the interactive session
  /help               - Show this help message
  /status             - Show current session status
  /clear              - Clear conversation history
  /verbose            - Toggle verbose mode on/off

Model & Connection:
  /listmodels         - List all available Ollama models
  /model <name>       - Switch to a different model
  /connect <url>      - Connect to remote Ollama instance
                        Example: /connect http://192.168.1.100:11434

System Prompts:
  /prompts            - List available system prompts
  /prompt <name>      - Switch to different system prompt
  /showprompt         - Display current system prompt

Model Parameters:
  /params             - Show current model parameters
  /temperature <0-2>  - Set creativity (0=focused, 2=chaotic)
  /topp <0-1>         - Set nucleus sampling (0.1=narrow, 1.0=full)
  /topk <1-100>       - Set top-k sampling (1=strict, 100=diverse)
  /maxtokens <1-8192> - Set response length limit
  /penalty <0.5-2>    - Set repeat penalty (0.5=repetitive, 2.0=no repeats)

Display & Interface:
  /syntax             - Toggle syntax highlighting on/off
  /typing <speed>     - Enable typing animation (speed: 0.01-0.1)
  /typing off         - Disable typing animation

File Operations (Quick):
  /pwd                - Show current working directory with safety info
  /cd <directory>     - Change working directory (with safety checks)
  /cd --force <dir>   - Force change to sensitive directory
  /ls [directory]     - Quick file listing (doesn't use AI)
  /cat <file>         - Quick file content view (doesn't use AI)

Directory Safety:
  /safemode <on|off>  - Toggle directory safety restrictions
  /allowdir <path>    - Add directory to allowed list
  /allowdir --remove  - Remove directory from allowed list
  /safedirs           - Show suggested safe directories
  /dirinfo [path]     - Show directory safety information
  /shellcmds <on|off> - Enable/disable shell commands (KILL SWITCH)

💡 Regular prompts (not starting with /) will be sent to the AI model.
💡 System prompts define the AI's personality and capabilities.
💡 Model parameters control response style and creativity.
    """

    if rich_enabled and RICH_ENABLED and console:
        try:
            help_panel = Panel(
                help_content.strip(),
                title="🤖 AI Agent Help",
                style="bold blue",
                width=get_terminal_width() - 4,
            )
            console.print(help_panel)
        except Exception:
            print(help_content)
    else:
        print(help_content)


def print_startup_banner(model: str, config: dict, rich_enabled: bool = True) -> None:
    """Print startup banner"""
    if rich_enabled and RICH_ENABLED and console:
        try:
            title = Text("🤖 Interactive AI Agent", style="bold cyan")
            info_table = Table.grid(padding=1)
            info_table.add_column(style="bold blue")
            info_table.add_column(style="green")

            for key, value in config.items():
                info_table.add_row(f"{key}:", str(value))

            startup_panel = Panel(
                info_table,
                title=title,
                style="bold blue",
                width=get_terminal_width() - 4,
            )
            console.print(startup_panel)
            console.print("─" * min(50, get_terminal_width()), style="dim")
        except Exception:
            print_startup_plain(model, config)
    else:
        print_startup_plain(model, config)


def print_startup_plain(model: str, config: dict) -> None:
    """Print startup banner without rich formatting"""
    print("🤖 Interactive AI Agent")
    for key, value in config.items():
        print(f"{key}: {value}")
    print("-" * 50)


def print_status_table(status_data: dict, rich_enabled: bool = True) -> None:
    """Print status information as a table"""
    if rich_enabled and RICH_ENABLED and console:
        try:
            table = Table(
                title="📊 Session Status",
                show_header=False,
                width=get_terminal_width() - 4,
            )
            table.add_column("Property", style="bold blue", width=22)
            table.add_column("Value", style="green")

            for key, value in status_data.items():
                table.add_row(key, str(value))

            console.print(table)
        except Exception:
            print_status_plain(status_data)
    else:
        print_status_plain(status_data)


def print_status_plain(status_data: dict) -> None:
    """Print status without rich formatting"""
    print("📊 Session Status:")
    for key, value in status_data.items():
        print(f"  {key}: {value}")


def print_models_table(
    models: List[str], current_model: str, rich_enabled: bool = True
) -> None:
    """Print available models as a table"""
    if rich_enabled and RICH_ENABLED and console:
        try:
            table = Table(
                title="📦 Available Ollama Models", width=get_terminal_width() - 4
            )
            table.add_column("Model", style="cyan", no_wrap=False)
            table.add_column("Status", style="green", width=15)

            for model in models:
                if model == current_model:
                    table.add_row(f"🎯 {model}", "← current")
                else:
                    table.add_row(f"🤖 {model}", "available")

            console.print(table)
        except Exception:
            print_models_plain(models, current_model)
    else:
        print_models_plain(models, current_model)


def print_models_plain(models: List[str], current_model: str) -> None:
    """Print models without rich formatting"""
    print("📦 Available Ollama models:")
    for model in models:
        indicator = " ← current" if model == current_model else ""
        print(f"  - {model}{indicator}")