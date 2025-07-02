"""
Main AI Agent implementation
"""

import json
import requests
import os
from typing import List, Dict, Optional
from core.config import AgentConfig, get_system_prompt, list_system_prompts
from core.prompt_manager import PromptManager
from core.functions import execute_function, get_file_language
from utils.display import (
    rich_print,
    typewriter_print,
    print_syntax_highlighted,
    print_file_table,
    format_help_text,
    print_startup_banner,
    print_status_table,
    print_models_table,
    print_prompts_table,
    print_model_params_table,
)
from utils.terminal import setup_readline_history, save_readline_history, test_ollama_connection
from utils.filesystem import safe_change_directory, get_directory_info, suggest_safe_directories, format_directory_safety_info


class OllamaAgent:
    """Main AI Agent class"""

    def __init__(self, config: AgentConfig):
        self.config = config
        self.prompt_manager = PromptManager()
        # Ensure prompts directory exists and export built-ins
        self.prompt_manager.ensure_prompts_directory()
        self.reset_conversation()

    def reset_conversation(self) -> None:
        """Reset conversation with current system prompt"""
        base_prompt, is_from_file = self.prompt_manager.load_prompt(self.config.current_prompt)

        if not base_prompt:
            rich_print(f"⚠️  Prompt '{self.config.current_prompt}' not found, using default", style="yellow")
            base_prompt, _ = self.prompt_manager.load_prompt("default")

        # Dynamically append shell command instructions if enabled
        if self.config.shell_commands_enabled:
            shell_instructions = """

SHELL COMMANDS ENABLED:
You now have access to safe shell commands via the shell_command function. Use these for common file operations:

- Create directories: shell_command with {"command": "mkdir", "args": ["dirname"]}
- Create empty files: shell_command with {"command": "touch", "args": ["filename"]}
- List directory contents: shell_command with {"command": "ls", "args": []} or {"command": "ls", "args": ["-la"]}
- Show current directory: shell_command with {"command": "pwd", "args": []}
- Print text: shell_command with {"command": "echo", "args": ["text"]}

Examples of natural usage:
- "create a directory called test-folder" → use shell_command: mkdir test-folder
- "make an empty file called app.py" → use shell_command: touch app.py
- "show me what's in this directory" → use shell_command: ls -la
- "create a new project structure" → use multiple shell_command calls for mkdir

These shell commands are safer and more intuitive than writing Python scripts for basic file operations.
Use shell commands as your first choice for file/directory operations, then use write_file for adding content.
"""
            system_content = base_prompt + shell_instructions
        else:
            system_content = base_prompt

        self.messages = [{"role": "system", "content": system_content}]

    def call_ollama_api(self, messages: List[Dict]) -> Dict:
        """Call Ollama's REST API"""
        url = f"{self.config.api_base}/api/chat"

        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False,
            "options": self.config.get_model_options(),
        }

        response = requests.post(url, json=payload)
        if response.status_code != 200:
            raise Exception(
                f"Ollama API error: {response.status_code} - {response.text}"
            )

        return response.json()

    def parse_function_call(self, text: str) -> Optional[Dict]:
        """Parse function call from model response"""
        text = text.strip()

        # Look for JSON function call pattern
        start_idx = text.find("{")
        end_idx = text.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            return None

        try:
            json_str = text[start_idx:end_idx]
            parsed = json.loads(json_str)

            if "function_call" in parsed:
                return parsed["function_call"]
        except json.JSONDecodeError:
            pass

        return None

    def should_show_function_result(self, func_name: str, user_prompt: str) -> bool:
        """Determine if function result should be shown to user"""
        if self.config.verbose:
            return True

        # Keywords that indicate user wants to see content
        show_keywords = [
            "show",
            "display",
            "view",
            "see",
            "content",
            "contents",
            "read",
            "what is",
            "what's",
            "tell me about",
            "examine",
            "look at",
            "open",
            "check",
            "inspect",
        ]

        user_lower = user_prompt.lower()

        # Show file content when explicitly requested
        if func_name == "get_file_content":
            for keyword in show_keywords:
                if keyword in user_lower:
                    return True

        # Always show file listings and operations
        if func_name in ["get_files_info", "write_file", "run_python_file"]:
            return True

        return False

    def process_conversation_turn(self, user_prompt: str) -> None:
        """Process a single conversation turn"""
        max_function_calls = 5  # Prevent infinite loops
        function_call_count = 0

        while function_call_count < max_function_calls:
            try:
                response = self.call_ollama_api(self.messages)
                assistant_response = response["message"]["content"]

                if self.config.verbose:
                    rich_print(f"\n--- Function Call {function_call_count + 1} ---", style="dim")
                    rich_print(f"Model response: {assistant_response}", style="dim")

                function_call = self.parse_function_call(assistant_response)

                if function_call:
                    function_call_count += 1
                    func_name = function_call.get("name")
                    func_args = function_call.get("arguments", {})

                    rich_print(f"🔧 Calling function: {func_name}", style="bold yellow")

                    # Execute function
                    ai_result, user_result, extra_data = execute_function(
                        func_name, func_args, self.config.verbose, self.config
                    )

                    # Show result if appropriate
                    show_result = self.should_show_function_result(
                        func_name, user_prompt
                    )

                    if show_result:
                        rich_print("\n📋 Function Result:", style="bold green")

                        # Handle different display types
                        if func_name == "get_files_info" and extra_data:
                            print_file_table(extra_data, self.config.rich_enabled)
                        elif func_name == "get_file_content" and ":" in user_result:
                            # Extract file info and content
                            parts = user_result.split(":", 1)
                            if len(parts) == 2:
                                header, content = parts
                                rich_print(header, style="bold cyan")
                                # Extract language from header
                                if "(" in header and ")" in header:
                                    lang_part = (
                                        header.split("(")[1].split(")")[0].split(",")[0]
                                    )
                                    print_syntax_highlighted(
                                        content,
                                        lang_part,
                                        self.config.syntax_highlighting,
                                    )
                                else:
                                    print(content)
                            else:
                                print(user_result)
                        else:
                            print(user_result)
                        print()

                    # Add function call and result to conversation
                    self.messages.append(
                        {"role": "assistant", "content": assistant_response}
                    )
                    self.messages.append(
                        {"role": "user", "content": f"Function result: {ai_result}"}
                    )

                    if self.config.verbose:
                        rich_print(
                            "[DEBUG] Added function result to conversation", style="dim"
                        )

                    # Continue the loop to get the next response (might be another function call or final answer)

                else:
                    # No function call detected - this is the final response
                    typewriter_print(
                        assistant_response,
                        self.config.typing_speed,
                        self.config.typing_enabled,
                        style="white",
                    )
                    self.messages.append(
                        {"role": "assistant", "content": assistant_response}
                    )
                    break

            except Exception as e:
                rich_print(f"❌ Error: {e}", style="red")
                break

        if function_call_count >= max_function_calls:
            rich_print(
                f"⚠️  Reached maximum function calls ({max_function_calls}). Stopping to prevent loops.",
                style="yellow"
            )

    def list_models(self) -> None:
        """List available Ollama models"""
        try:
            response = requests.get(f"{self.config.api_base}/api/tags")
            if response.status_code == 200:
                models_data = response.json()
                models = [model["name"] for model in models_data["models"]]
                print_models_table(models, self.config.model, self.config.rich_enabled)
            else:
                rich_print("No models found or Ollama not running", style="red")
        except Exception as e:
            rich_print(f"Error listing models: {e}", style="red")

    def handle_slash_command(self, command: str) -> bool:
        """Handle slash commands. Returns True to continue, False to exit"""
        cmd_parts = command[1:].split()
        cmd = cmd_parts[0].lower()

        if cmd in ["quit", "exit", "q"]:
            rich_print("👋 Goodbye!", style="green")
            return False

        elif cmd == "help":
            format_help_text(self.config.rich_enabled)

        elif cmd == "listmodels":
            self.list_models()

        elif cmd == "model":
            if len(cmd_parts) < 2:
                rich_print("❌ Usage: /model <model_name>", style="red")
                rich_print("💡 Use /listmodels to see available models", style="dim")
            else:
                new_model = cmd_parts[1]
                # TODO: Validate model exists
                self.config.model = new_model
                rich_print(f"✅ Switched to model: {new_model}", style="green")

        elif cmd == "clear":
            self.reset_conversation()
            rich_print("🧹 Conversation history cleared", style="green")

        elif cmd == "verbose":
            self.config.toggle_verbose()
            status = "enabled" if self.config.verbose else "disabled"
            rich_print(f"🔧 Verbose mode {status}", style="blue")

        elif cmd == "syntax":
            self.config.toggle_syntax_highlighting()
            status = "enabled" if self.config.syntax_highlighting else "disabled"
            rich_print(f"🎨 Syntax highlighting {status}", style="blue")

        elif cmd == "typing":
            if len(cmd_parts) < 2:
                current_status = (
                    f"enabled (speed: {self.config.typing_speed})"
                    if self.config.typing_enabled
                    else "disabled"
                )
                rich_print(f"🎭 Typing animation: {current_status}", style="blue")
                rich_print("💡 Usage: /typing <speed> or /typing off", style="dim")
            else:
                param = cmd_parts[1].lower()
                if param == "off":
                    self.config.typing_enabled = False
                    rich_print("🎭 Typing animation disabled", style="blue")
                else:
                    try:
                        speed = float(param)
                        if self.config.set_typing_speed(speed):
                            self.config.typing_enabled = True
                            rich_print(
                                f"🎭 Typing animation enabled (speed: {speed})",
                                style="blue",
                            )
                        else:
                            rich_print(
                                "❌ Speed must be between 0.005 and 0.2", style="red"
                            )
                    except ValueError:
                        rich_print(
                            "❌ Invalid speed. Use a number (e.g., 0.03) or 'off'",
                            style="red",
                        )

        elif cmd == "prompts":
            prompts = self.prompt_manager.list_available_prompts()
            from utils.display import print_prompts_table
            # Convert to old format for display compatibility
            prompt_descriptions = {name: info['description'] for name, info in prompts.items()}
            print_prompts_table(prompt_descriptions, self.config.current_prompt, self.config.rich_enabled)

            # Show additional info about file-based prompts
            file_prompts = [name for name, info in prompts.items() if 'file' in info['source']]
            if file_prompts:
                rich_print(f"\n💡 File-based prompts: {', '.join(file_prompts)}", style="dim")
                rich_print("💡 Edit .md files in prompts/ directory to customize", style="dim")

        elif cmd == "prompt":
            if len(cmd_parts) < 2:
                rich_print("❌ Usage: /prompt <prompt_name>", style="red")
                rich_print("💡 Use /prompts to see available prompts", style="dim")
            else:
                prompt_name = cmd_parts[1]
                content, is_from_file = self.prompt_manager.load_prompt(prompt_name)
                if content:
                    self.config.current_prompt = prompt_name
                    self.reset_conversation()
                    source = "file" if is_from_file else "built-in"
                    rich_print(f"✅ Switched to prompt: {prompt_name} ({source})", style="green")
                    rich_print("🔄 Conversation history cleared for new prompt", style="dim")
                else:
                    rich_print(f"❌ Unknown prompt: {prompt_name}", style="red")
                    rich_print("💡 Use /prompts to see available prompts", style="dim")

        elif cmd == "showprompt":
            preview = self.prompt_manager.get_prompt_preview(self.config.current_prompt, max_lines=20)
            rich_print(preview, style="cyan")
            rich_print("\n💡 Use /editprompt to modify, /previewprompt <name> for others", style="dim")

        elif cmd == "previewprompt":
            if len(cmd_parts) < 2:
                rich_print("❌ Usage: /previewprompt <prompt_name>", style="red")
                rich_print("💡 Use /prompts to see available prompts", style="dim")
            else:
                prompt_name = cmd_parts[1]
                max_lines = int(cmd_parts[2]) if len(cmd_parts) > 2 else 15
                preview = self.prompt_manager.get_prompt_preview(prompt_name, max_lines)
                rich_print(preview, style="cyan")

        elif cmd == "editprompt":
            if len(cmd_parts) < 2:
                rich_print("❌ Usage: /editprompt <prompt_name>", style="red")
                rich_print("💡 Creates/edits a prompt file in prompts/ directory", style="dim")
            else:
                prompt_name = cmd_parts[1]
                prompt_file = self.prompt_manager.prompts_dir / f"{prompt_name}.md"
                rich_print(f"📝 Edit prompt file: {prompt_file}", style="blue")
                rich_print(f"💡 After saving, use /prompt {prompt_name} to switch to it", style="dim")

                # Show current content if exists
                if prompt_file.exists():
                    rich_print("📄 Current content preview:", style="dim")
                    preview = self.prompt_manager.get_prompt_preview(prompt_name, max_lines=5)
                    rich_print(preview, style="dim")

        elif cmd == "exportprompts":
            self.prompt_manager.export_builtin_prompts()
            rich_print("✅ Built-in prompts exported to prompts/ directory", style="green")
            rich_print("💡 You can now edit the .md files to customize prompts", style="dim")

        elif cmd == "params":
            params_data = {
                "🌡️ Temperature": f"{self.config.temperature} (creativity: 0.0=focused, 2.0=chaotic)",
                "🎯 Top P": f"{self.config.top_p} (nucleus sampling: 0.1=narrow, 1.0=full)",
                "🔢 Top K": f"{self.config.top_k} (top-k sampling: 1=strict, 100=diverse)",
                "📏 Max Tokens": f"{self.config.num_predict} (response length limit)",
                "🔄 Repeat Penalty": f"{self.config.repeat_penalty} (0.5=repetitive, 2.0=no repeats)",
            }
            print_model_params_table(params_data, self.config.rich_enabled)

        elif cmd == "temperature":
            if len(cmd_parts) < 2:
                rich_print(f"🌡️ Current temperature: {self.config.temperature}", style="blue")
                rich_print("💡 Usage: /temperature <0.0-2.0>", style="dim")
                rich_print("   0.0 = Very focused, 0.1 = Balanced, 1.0 = Creative, 2.0 = Chaotic", style="dim")
            else:
                try:
                    temp = float(cmd_parts[1])
                    if self.config.set_temperature(temp):
                        rich_print(f"🌡️ Temperature set to: {temp}", style="blue")
                    else:
                        rich_print("❌ Temperature must be between 0.0 and 2.0", style="red")
                except ValueError:
                    rich_print("❌ Invalid temperature. Use a number (e.g., 0.7)", style="red")

        elif cmd == "topp":
            if len(cmd_parts) < 2:
                rich_print(f"🎯 Current top_p: {self.config.top_p}", style="blue")
                rich_print("💡 Usage: /topp <0.0-1.0>", style="dim")
            else:
                try:
                    p = float(cmd_parts[1])
                    if self.config.set_top_p(p):
                        rich_print(f"🎯 Top P set to: {p}", style="blue")
                    else:
                        rich_print("❌ Top P must be between 0.0 and 1.0", style="red")
                except ValueError:
                    rich_print("❌ Invalid top_p. Use a number (e.g., 0.9)", style="red")

        elif cmd == "topk":
            if len(cmd_parts) < 2:
                rich_print(f"🔢 Current top_k: {self.config.top_k}", style="blue")
                rich_print("💡 Usage: /topk <1-100>", style="dim")
            else:
                try:
                    k = int(cmd_parts[1])
                    if self.config.set_top_k(k):
                        rich_print(f"🔢 Top K set to: {k}", style="blue")
                    else:
                        rich_print("❌ Top K must be between 1 and 100", style="red")
                except ValueError:
                    rich_print("❌ Invalid top_k. Use an integer (e.g., 40)", style="red")

        elif cmd == "maxtokens":
            if len(cmd_parts) < 2:
                rich_print(f"📏 Current max tokens: {self.config.num_predict}", style="blue")
                rich_print("💡 Usage: /maxtokens <1-8192>", style="dim")
            else:
                try:
                    tokens = int(cmd_parts[1])
                    if self.config.set_num_predict(tokens):
                        rich_print(f"📏 Max tokens set to: {tokens}", style="blue")
                    else:
                        rich_print("❌ Max tokens must be between 1 and 8192", style="red")
                except ValueError:
                    rich_print("❌ Invalid max tokens. Use an integer (e.g., 4096)", style="red")

        elif cmd == "penalty":
            if len(cmd_parts) < 2:
                rich_print(f"🔄 Current repeat penalty: {self.config.repeat_penalty}", style="blue")
                rich_print("💡 Usage: /penalty <0.5-2.0>", style="dim")
            else:
                try:
                    penalty = float(cmd_parts[1])
                    if self.config.set_repeat_penalty(penalty):
                        rich_print(f"🔄 Repeat penalty set to: {penalty}", style="blue")
                    else:
                        rich_print("❌ Repeat penalty must be between 0.5 and 2.0", style="red")
                except ValueError:
                    rich_print("❌ Invalid repeat penalty. Use a number (e.g., 1.1)", style="red")

        elif cmd == "connect":
            if len(cmd_parts) < 2:
                rich_print(f"🌐 Current API base: {self.config.api_base}", style="blue")
                rich_print("💡 Usage: /connect <url>", style="dim")
                rich_print("   Example: /connect http://192.168.1.100:11434", style="dim")
            else:
                url = cmd_parts[1]
                if self.config.set_api_base(url):
                    rich_print(f"🌐 Testing connection to: {url}", style="blue")
                    if test_ollama_connection(url):
                        rich_print(f"✅ Connected to remote Ollama: {url}", style="green")
                    else:
                        rich_print(f"❌ Failed to connect to: {url}", style="red")
                        rich_print("💡 Make sure Ollama is running and accessible", style="dim")
                else:
                    rich_print("❌ Invalid URL. Must start with http:// or https://", style="red")

        elif cmd == "status":
            status_data = {
                "🤖 Model": self.config.model,
                "🌐 API Base": self.config.api_base,
                "📋 System Prompt": self.config.current_prompt,
                "💬 Conversation turns": len(
                    [m for m in self.messages if m["role"] != "system"]
                ),
                "🔧 Verbose mode": "enabled" if self.config.verbose else "disabled",
                "🎨 Syntax highlighting": (
                    "enabled" if self.config.syntax_highlighting else "disabled"
                ),
                "🎭 Typing animation": (
                    f"enabled (speed: {self.config.typing_speed})"
                    if self.config.typing_enabled
                    else "disabled"
                ),
                "🌡️ Temperature": str(self.config.temperature),
                "🎯 Top P": str(self.config.top_p),
                "🔢 Top K": str(self.config.top_k),
                "📏 Max Tokens": str(self.config.num_predict),
                "🔄 Repeat Penalty": str(self.config.repeat_penalty),
                "🖥️  Shell Commands": "enabled" if self.config.shell_commands_enabled else "disabled",
                "📂 Working directory": os.getcwd(),
            }
            print_status_table(status_data, self.config.rich_enabled)

        elif cmd == "cd":
            if len(cmd_parts) < 2:
                # Show current directory and safety info
                rich_print(format_directory_safety_info(), style="blue")
                rich_print("\n💡 Usage: /cd <directory>", style="dim")
                rich_print("💡 Use /cd --force <directory> for sensitive directories", style="dim")
                rich_print("💡 Use /safedirs to see suggested safe directories", style="dim")
            else:
                force = False
                target_dir = cmd_parts[1]

                # Check for --force flag
                if target_dir == "--force" and len(cmd_parts) > 2:
                    force = True
                    target_dir = cmd_parts[2]
                elif target_dir.startswith("--force="):
                    force = True
                    target_dir = target_dir[8:]  # Remove --force= prefix

                success, message = safe_change_directory(
                    target_dir,
                    self.config.safe_mode,
                    self.config.allowed_base_dirs,
                    force
                )

                if success:
                    rich_print(message, style="green")
                    # Update prompt to show new directory if it fits
                    new_dir = os.path.basename(os.getcwd())
                    if len(new_dir) < 20:
                        rich_print(f"💡 Prompt will show: [{self.config.model}:{new_dir}]>", style="dim")
                else:
                    rich_print(message, style="red")

        elif cmd == "safemode":
            if len(cmd_parts) < 2:
                status = "enabled" if self.config.safe_mode else "disabled"
                rich_print(f"🛡️  Safe mode: {status}", style="blue")
                rich_print("💡 Usage: /safemode <on|off>", style="dim")
                rich_print("💡 Safe mode prevents access to system directories", style="dim")
            else:
                param = cmd_parts[1].lower()
                if param in ["on", "true", "1", "enable"]:
                    self.config.safe_mode = True
                    rich_print("🛡️  Safe mode enabled", style="green")
                elif param in ["off", "false", "0", "disable"]:
                    rich_print("⚠️  WARNING: Disabling safe mode allows access to system directories!", style="yellow")
                    rich_print("💡 This could be dangerous. Use /safemode on to re-enable.", style="yellow")
                    self.config.safe_mode = False
                    rich_print("🛡️  Safe mode disabled", style="red")
                else:
                    rich_print("❌ Invalid option. Use 'on' or 'off'", style="red")

        elif cmd == "allowdir":
            if len(cmd_parts) < 2:
                rich_print("📁 Currently allowed base directories:", style="blue")
                for i, dir_path in enumerate(self.config.allowed_base_dirs, 1):
                    rich_print(f"  {i}. {dir_path}", style="cyan")
                rich_print("\n💡 Usage: /allowdir <directory>", style="dim")
                rich_print("💡 Use /allowdir --remove <directory> to remove", style="dim")
            else:
                if cmd_parts[1] == "--remove" and len(cmd_parts) > 2:
                    dir_to_remove = os.path.abspath(cmd_parts[2])
                    if dir_to_remove in self.config.allowed_base_dirs:
                        self.config.allowed_base_dirs.remove(dir_to_remove)
                        rich_print(f"✅ Removed from allowed directories: {dir_to_remove}", style="green")
                    else:
                        rich_print(f"❌ Directory not in allowed list: {dir_to_remove}", style="red")
                else:
                    new_dir = os.path.abspath(cmd_parts[1])
                    if os.path.exists(new_dir) and os.path.isdir(new_dir):
                        if new_dir not in self.config.allowed_base_dirs:
                            self.config.allowed_base_dirs.append(new_dir)
                            rich_print(f"✅ Added to allowed directories: {new_dir}", style="green")
                        else:
                            rich_print(f"💡 Directory already allowed: {new_dir}", style="blue")
                    else:
                        rich_print(f"❌ Directory does not exist: {new_dir}", style="red")

        elif cmd == "safedirs":
            safe_dirs = suggest_safe_directories()
            rich_print("💡 Suggested safe directories for development:", style="blue")
            for i, dir_path in enumerate(safe_dirs, 1):
                exists = "✅" if os.path.exists(dir_path) else "❌"
                rich_print(f"  {i}. {exists} {dir_path}", style="cyan")
            rich_print("\n💡 Use /cd <directory> to change to any of these", style="dim")
            rich_print("💡 Use /allowdir <directory> to add custom allowed directories", style="dim")

        elif cmd == "shellcmds":
            if len(cmd_parts) < 2:
                status = "enabled" if self.config.shell_commands_enabled else "disabled"
                rich_print(f"🖥️  Shell commands: {status}", style="blue")
                rich_print("💡 Usage: /shellcmds <on|off>", style="dim")
                rich_print("💡 Controls whether AI can execute shell commands", style="dim")
            else:
                param = cmd_parts[1].lower()
                if param in ["on", "true", "1", "enable"]:
                    self.config.shell_commands_enabled = True
                    # Reset conversation to include shell command instructions
                    self.reset_conversation()
                    rich_print("🖥️  Shell commands enabled", style="green")
                    rich_print("💡 AI can now use mkdir, touch, ls, etc.", style="dim")
                    rich_print("🔄 Conversation reset with shell command instructions", style="dim")
                elif param in ["off", "false", "0", "disable"]:
                    self.config.shell_commands_enabled = False
                    # Reset conversation to remove shell command instructions
                    self.reset_conversation()
                    rich_print("🖥️  Shell commands disabled (KILL SWITCH ACTIVATED)", style="red")
                    rich_print("💡 AI cannot execute any shell commands", style="dim")
                    rich_print("🔄 Conversation reset without shell command instructions", style="dim")
                else:
                    rich_print("❌ Invalid option. Use 'on' or 'off'", style="red")

        elif cmd == "dirinfo" or cmd == "pwd":
            target_dir = cmd_parts[1] if len(cmd_parts) > 1 else "."
            try:
                rich_print(format_directory_safety_info(target_dir), style="blue")
            except Exception as e:
                rich_print(f"❌ Error getting directory info: {e}", style="red")

        elif cmd == "ls":
            directory = cmd_parts[1] if len(cmd_parts) > 1 else "."
            try:
                files = os.listdir(directory)
                rich_print(f"📁 Files in '{directory}':", style="bold blue")
                for file in sorted(files):
                    full_path = os.path.join(directory, file)
                    if os.path.isdir(full_path):
                        rich_print(f"  📁 {file}/", style="cyan")
                    else:
                        size = os.path.getsize(full_path)
                        rich_print(f"  📄 {file} ({size} bytes)", style="white")
            except Exception as e:
                rich_print(f"❌ Error listing directory: {e}", style="red")

        elif cmd == "cat":
            if len(cmd_parts) < 2:
                rich_print("❌ Usage: /cat <filename>", style="red")
            else:
                filename = cmd_parts[1]
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        content = f.read()
                        if len(content) > 1500:
                            content = (
                                content[:1500]
                                + f"\n... [truncated - showing first 1500 of {len(content)} characters]"
                            )
                            content += f"\n💡 Use AI prompt 'show me the full content of {filename}' for complete file"

                        rich_print(f"📄 Content of '{filename}':", style="bold cyan")
                        language = get_file_language(filename)
                        print_syntax_highlighted(
                            content, language, self.config.syntax_highlighting
                        )
                except Exception as e:
                    rich_print(f"❌ Error reading file: {e}", style="red")

        else:
            rich_print(f"❌ Unknown command: /{cmd}", style="red")
            rich_print("💡 Use /help to see available commands", style="dim")

        return True

    def run_interactive(self) -> None:
        """Run in interactive mode"""
        config_info = {
            "Model": self.config.model,
            "API Base": self.config.api_base,
            "System Prompt": self.config.current_prompt,
            "Temperature": str(self.config.temperature),
            "Safe Mode": "enabled" if self.config.safe_mode else "disabled",
            "Working Dir": os.path.basename(os.getcwd()) or os.getcwd(),
            "Syntax highlighting": (
                "enabled" if self.config.syntax_highlighting else "disabled"
            ),
            "Typing animation": (
                f"enabled (speed: {self.config.typing_speed})"
                if self.config.typing_enabled
                else "disabled"
            ),
            "Commands": "Type /help for commands",
            "History": "Use ↑/↓ arrow keys",
        }

        print_startup_banner(self.config.model, config_info, self.config.rich_enabled)

        # Setup command history
        history_file = setup_readline_history()

        try:
            while True:
                try:
                    # Dynamic prompt showing current directory
                    current_dir = os.path.basename(os.getcwd())
                    if current_dir and len(current_dir) < 20:
                        prompt = f"\n[{self.config.model}:{current_dir}]> "
                    else:
                        prompt = f"\n[{self.config.model}]> "

                    user_input = input(prompt).strip()

                    if not user_input:
                        continue

                    # Handle slash commands
                    if user_input.startswith("/"):
                        if not self.handle_slash_command(user_input):
                            break
                        continue

                    # Regular AI prompt
                    self.messages.append({"role": "user", "content": user_input})
                    self.process_conversation_turn(user_input)

                except KeyboardInterrupt:
                    rich_print(
                        "\n\n👋 Interrupted. Use /quit to exit gracefully.",
                        style="yellow",
                    )
                    continue
                except EOFError:
                    rich_print("\n👋 Goodbye!", style="green")
                    break
        finally:
            save_readline_history(history_file)

    def run_single_prompt(self, prompt: str) -> None:
        """Run a single prompt"""
        self.messages.append({"role": "user", "content": prompt})
        self.process_conversation_turn(prompt)
