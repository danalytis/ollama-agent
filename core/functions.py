"""
Function execution handlers for the AI agent
"""

import os
import sys
import subprocess
import platform
from typing import Dict, Tuple, List
from utils.display import rich_print


def get_file_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    ext = os.path.splitext(file_path)[1].lower()
    language_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".cs": "csharp",
        ".php": "php",
        ".rb": "ruby",
        ".go": "go",
        ".rs": "rust",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".fish": "fish",
        ".ps1": "powershell",
        ".html": "html",
        ".htm": "html",
        ".xml": "xml",
        ".css": "css",
        ".scss": "scss",
        ".sass": "sass",
        ".less": "less",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".toml": "toml",
        ".ini": "ini",
        ".cfg": "ini",
        ".conf": "ini",
        ".sql": "sql",
        ".md": "markdown",
        ".markdown": "markdown",
        ".rst": "rst",
        ".txt": "text",
        ".log": "text",
        ".dockerfile": "dockerfile",
        ".makefile": "makefile",
        ".r": "r",
        ".R": "r",
        ".m": "matlab",
        ".pl": "perl",
        ".vim": "vim",
    }
    return language_map.get(ext, "text")


def execute_get_files_info(
    arguments: Dict, verbose: bool = False
) -> Tuple[str, str, List[Tuple[str, str, str]]]:
    """List files in directory"""
    directory = arguments.get("directory", ".")

    if verbose:
        rich_print(f"  📂 Listing files in: {directory}", style="dim")

    try:
        files = os.listdir(directory)
        file_info = []
        files_data = []

        for file in sorted(files):
            full_path = os.path.join(directory, file)
            try:
                size = os.path.getsize(full_path)
                is_dir = os.path.isdir(full_path)
                file_type = "directory" if is_dir else "file"

                # For AI context
                file_info.append(f"{file} ({file_type}, {size} bytes)")

                # For display
                if size > 1024 * 1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                files_data.append((file, file_type, size_str))

            except:
                file_info.append(f"{file} (unknown)")
                files_data.append((file, "unknown", "unknown"))

        ai_result = f"Files in '{directory}':\n" + "\n".join(file_info)
        user_result = f"📁 Files in '{directory}'"

        return ai_result, user_result, files_data

    except FileNotFoundError:
        error_msg = f"❌ Error: Directory '{directory}' not found"
        return error_msg, error_msg, []
    except PermissionError:
        error_msg = f"❌ Error: Permission denied accessing '{directory}'"
        return error_msg, error_msg, []


def execute_get_file_content(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Read file content"""
    file_path = arguments.get("file_path")
    if not file_path:
        error_msg = "❌ Error: file_path parameter required"
        return error_msg, error_msg

    if verbose:
        rich_print(f"  📖 Reading file: {file_path}", style="dim")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

            # AI gets limited but sufficient content
            if len(content) > 2000:
                ai_content = (
                    content[:2000]
                    + f"\n[Note: This file has {len(content)} total characters. The above excerpt should be sufficient to answer most questions about this file.]"
                )
            else:
                ai_content = content

            ai_result = f"Content of '{file_path}':\n{ai_content}"

            # User display format
            language = get_file_language(file_path)
            user_result = f"📄 {file_path} ({language}, {len(content)} chars):{content}"

            return ai_result, user_result

    except FileNotFoundError:
        error_msg = f"❌ Error: File '{file_path}' not found"
        return error_msg, error_msg
    except PermissionError:
        error_msg = f"❌ Error: Permission denied reading '{file_path}'"
        return error_msg, error_msg
    except UnicodeDecodeError:
        error_msg = (
            f"❌ Error: Cannot read '{file_path}' - binary file or encoding issue"
        )
        return error_msg, error_msg


def execute_write_file(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Write content to file"""
    file_path = arguments.get("file_path")
    content = arguments.get("content", "")

    if not file_path:
        error_msg = "❌ Error: file_path parameter required"
        return error_msg, error_msg

    if verbose:
        rich_print(f"  ✍️  Writing to file: {file_path}", style="dim")

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        result = f"✅ Successfully wrote {len(content)} characters to '{file_path}'"
        return result, result
    except PermissionError:
        error_msg = f"❌ Error: Permission denied writing to '{file_path}'"
        return error_msg, error_msg
    except Exception as e:
        error_msg = f"❌ Error writing to '{file_path}': {str(e)}"
        return error_msg, error_msg


def execute_run_python_file(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Run Python script"""
    file_path = arguments.get("file_path")
    args = arguments.get("args", [])

    if not file_path:
        error_msg = "❌ Error: file_path parameter required"
        return error_msg, error_msg

    if verbose:
        rich_print(
            f"  🐍 Running Python file: {file_path} with args: {args}", style="dim"
        )

    try:
        cmd = [sys.executable, file_path] + args

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30, cwd=os.getcwd()
        )

        output = ""
        if result.stdout:
            output += f"📤 STDOUT:\n{result.stdout}\n"
        if result.stderr:
            output += f"🚨 STDERR:\n{result.stderr}\n"
        output += f"🔢 Return code: {result.returncode}"

        return output, output

    except subprocess.TimeoutExpired:
        error_msg = f"⏰ Error: Script '{file_path}' timed out after 30 seconds"
        return error_msg, error_msg
    except FileNotFoundError:
        error_msg = f"❌ Error: Python file '{file_path}' not found"
        return error_msg, error_msg
    except Exception as e:
        error_msg = f"❌ Error running '{file_path}': {str(e)}"
        return error_msg, error_msg


def execute_shell_command(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Execute safe shell commands with strict security controls"""
    command = arguments.get("command")
    args = arguments.get("args", [])
    
    if not command:
        error_msg = "❌ Error: command parameter required"
        return error_msg, error_msg

    # Ultra-conservative whitelist - start very small
    SAFE_COMMANDS = {
        'mkdir': {
            'command': 'mkdir',
            'description': 'Create directory',
            'max_args': 2,  # mkdir -p dirname
        },
        'touch': {
            'command': 'touch', 
            'description': 'Create empty file',
            'max_args': 1,
        },
        'ls': {
            'command': 'ls',
            'description': 'List directory contents', 
            'max_args': 2,  # ls -la dirname
        },
        'pwd': {
            'command': 'pwd',
            'description': 'Show current directory',
            'max_args': 0,
        },
        'echo': {
            'command': 'echo',
            'description': 'Print text',
            'max_args': 10,
        }
    }
    
    # Windows equivalents
    if platform.system().lower() == "windows":
        SAFE_COMMANDS.update({
            'dir': {
                'command': 'dir',
                'description': 'List directory contents (Windows)',
                'max_args': 1,
            },
            'md': {
                'command': 'md', 
                'description': 'Create directory (Windows)',
                'max_args': 1,
            }
        })

    if verbose:
        rich_print(f"  🖥️  Requested shell command: {command} {args}", style="dim")

    # Check if command is in whitelist
    if command not in SAFE_COMMANDS:
        error_msg = f"❌ Error: Command '{command}' not in safe whitelist"
        available = ", ".join(SAFE_COMMANDS.keys())
        error_msg += f"\n💡 Available commands: {available}"
        return error_msg, error_msg

    cmd_info = SAFE_COMMANDS[command]
    
    # Check argument count
    if len(args) > cmd_info['max_args']:
        error_msg = f"❌ Error: Too many arguments for '{command}' (max: {cmd_info['max_args']})"
        return error_msg, error_msg

    # Security validation for arguments
    for arg in args:
        if not isinstance(arg, str):
            error_msg = f"❌ Error: Invalid argument type: {type(arg)}"
            return error_msg, error_msg
            
        # Block dangerous patterns
        dangerous_patterns = [
            '..',      # Path traversal
            ';',       # Command chaining
            '&&',      # Command chaining
            '||',      # Command chaining  
            '|',       # Piping
            '>',       # Redirection
            '<',       # Redirection
            '`',       # Command substitution
            '$(',      # Command substitution
            '${',      # Variable expansion
            '~/',      # Home directory (force explicit paths)
            '\\',      # Windows path separators (use forward slash)
        ]
        
        for pattern in dangerous_patterns:
            if pattern in arg:
                error_msg = f"❌ Error: Dangerous pattern '{pattern}' detected in argument: {arg}"
                return error_msg, error_msg
        
        # Additional path safety for file/directory operations
        if command in ['mkdir', 'touch', 'md'] and arg not in ['-p', '-v']:
            # Must be relative path in current directory or subdirectory
            if arg.startswith('/') or arg.startswith('C:') or arg.startswith('D:'):
                error_msg = f"❌ Error: Absolute paths not allowed: {arg}"
                error_msg += f"\n💡 Use relative paths like 'dirname' or 'subdir/filename'"
                return error_msg, error_msg
                
            # Check if path would escape current directory
            try:
                resolved_path = os.path.abspath(arg)
                current_dir = os.getcwd()
                if not resolved_path.startswith(current_dir):
                    error_msg = f"❌ Error: Path escapes current directory: {arg}"
                    return error_msg, error_msg
            except Exception:
                error_msg = f"❌ Error: Invalid path: {arg}"
                return error_msg, error_msg

    try:
        # Build command
        cmd_list = [cmd_info['command']] + args
        
        if verbose:
            rich_print(f"  ✅ Executing safe command: {' '.join(cmd_list)}", style="dim")
        
        # Execute with strict timeout and security
        result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            timeout=10,  # 10 second timeout
            cwd=os.getcwd(),  # Explicitly set working directory
            shell=False,  # NEVER use shell=True for security
        )
        
        output = ""
        if result.stdout:
            output += f"📤 Output:\n{result.stdout.strip()}\n"
        if result.stderr:
            output += f"🚨 Error:\n{result.stderr.strip()}\n"
        output += f"🔢 Exit code: {result.returncode}"
        
        if result.returncode == 0:
            success_msg = f"✅ Command executed successfully: {command}"
            if result.stdout.strip():
                success_msg += f"\n{result.stdout.strip()}"
        else:
            success_msg = f"⚠️  Command completed with exit code {result.returncode}"
        
        return output, success_msg

    except subprocess.TimeoutExpired:
        error_msg = f"⏰ Error: Command '{command}' timed out after 10 seconds"
        return error_msg, error_msg
    except FileNotFoundError:
        error_msg = f"❌ Error: Command '{command}' not found on system"
        return error_msg, error_msg
    except Exception as e:
        error_msg = f"❌ Error executing command '{command}': {str(e)}"
        return error_msg, error_msg
def execute_get_file_content_smart(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Read file content with smart limiting for large files"""
    file_path = arguments.get("file_path")
    max_chars = arguments.get("max_chars", 3000)  # Adjustable limit
    context_lines = arguments.get("context_lines", 5)  # Lines around target
    target_line = arguments.get("target_line", None)  # Focus on specific line

    if not file_path:
        error_msg = "❌ Error: file_path parameter required"
        return error_msg, error_msg

    if verbose:
        rich_print(f"  📖 Smart reading file: {file_path}", style="dim")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        total_chars = len(content)
        lines = content.split('\n')
        total_lines = len(lines)

        # If file is small enough, return everything
        if total_chars <= max_chars:
            ai_result = f"Content of '{file_path}' ({total_chars} chars, {total_lines} lines):\n{content}"
            language = get_file_language(file_path)
            user_result = f"📄 {file_path} ({language}, {total_chars} chars):{content}"
            return ai_result, user_result

        # File is large - use smart strategies
        if target_line:
            # Focus on specific line with context
            start_line = max(1, target_line - context_lines)
            end_line = min(total_lines, target_line + context_lines)

            selected_lines = lines[start_line-1:end_line]
            smart_content = '\n'.join(selected_lines)

            ai_result = f"Content around line {target_line} in '{file_path}' (lines {start_line}-{end_line} of {total_lines}):\n{smart_content}\n\n[Note: This is a focused excerpt. Use read_file_lines for other sections.]"

        else:
            # Show beginning and end with summary
            head_lines = 20
            tail_lines = 10

            head_content = '\n'.join(lines[:head_lines])
            tail_content = '\n'.join(lines[-tail_lines:])

            ai_result = f"""Content of '{file_path}' (LARGE FILE - {total_chars} chars, {total_lines} lines):

[BEGINNING - Lines 1-{head_lines}]
{head_content}

[... {total_lines - head_lines - tail_lines} lines omitted ...]

[END - Lines {total_lines - tail_lines + 1}-{total_lines}]
{tail_content}

[Note: Use read_file_lines or target_line parameter to see specific sections.]"""

        language = get_file_language(file_path)
        user_result = f"📄 {file_path} ({language}, {total_chars} chars - EXCERPT SHOWN)"

        return ai_result, user_result

    except FileNotFoundError:
        error_msg = f"❌ Error: File '{file_path}' not found"
        return error_msg, error_msg
    except Exception as e:
        error_msg = f"❌ Error reading '{file_path}': {str(e)}"
        return error_msg, error_msg


def execute_find_in_file(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Find text patterns in a file and show context"""
    file_path = arguments.get("file_path")
    search_text = arguments.get("search_text", "")
    context_lines = arguments.get("context_lines", 3)
    max_matches = arguments.get("max_matches", 10)

    if not file_path or not search_text:
        error_msg = "❌ Error: file_path and search_text parameters required"
        return error_msg, error_msg

    if verbose:
        rich_print(f"  🔍 Searching for '{search_text}' in: {file_path}", style="dim")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        matches = []
        for line_num, line in enumerate(lines, 1):
            if search_text.lower() in line.lower():
                # Get context around the match
                start_context = max(0, line_num - context_lines - 1)
                end_context = min(len(lines), line_num + context_lines)

                context_block = []
                for i in range(start_context, end_context):
                    prefix = ">>> " if i == line_num - 1 else "    "
                    context_block.append(f"{prefix}{i+1:3d}: {lines[i].rstrip()}")

                matches.append({
                    'line_num': line_num,
                    'context': '\n'.join(context_block)
                })

                if len(matches) >= max_matches:
                    break

        if matches:
            result_parts = [f"Found {len(matches)} matches for '{search_text}' in '{file_path}':\n"]
            for i, match in enumerate(matches, 1):
                result_parts.append(f"Match {i} (line {match['line_num']}):")
                result_parts.append(match['context'])
                result_parts.append("")  # Empty line separator

            ai_result = '\n'.join(result_parts)
            user_result = f"🔍 Found {len(matches)} matches in {file_path}"
        else:
            ai_result = f"No matches found for '{search_text}' in '{file_path}'"
            user_result = f"🔍 No matches found for '{search_text}'"

        return ai_result, user_result

    except Exception as e:
        error_msg = f"❌ Error searching '{file_path}': {str(e)}"
        return error_msg, error_msg
def execute_read_file_lines(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Read specific lines from a file"""
    file_path = arguments.get("file_path")
    start_line = arguments.get("start_line", 1)
    end_line = arguments.get("end_line", None)

    if not file_path:
        error_msg = "❌ Error: file_path parameter required"
        return error_msg, error_msg

    if verbose:
        rich_print(f"  📖 Reading lines {start_line}-{end_line or 'end'} from: {file_path}", style="dim")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        total_lines = len(lines)

        # Adjust line numbers (1-based to 0-based)
        start_idx = max(0, start_line - 1)
        end_idx = min(total_lines, end_line) if end_line else total_lines

        selected_lines = lines[start_idx:end_idx]
        content = ''.join(selected_lines)

        ai_result = f"Lines {start_line}-{end_idx} of '{file_path}' (total: {total_lines} lines):\n{content}"
        user_result = f"📄 {file_path} [lines {start_line}-{end_idx}]:{content}"

        return ai_result, user_result

    except FileNotFoundError:
        error_msg = f"❌ Error: File '{file_path}' not found"
        return error_msg, error_msg
    except Exception as e:
        error_msg = f"❌ Error reading '{file_path}': {str(e)}"
        return error_msg, error_msg


def execute_write_file_lines(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Replace specific lines in a file"""
    file_path = arguments.get("file_path")
    content = arguments.get("content", "")
    start_line = arguments.get("start_line", 1)
    end_line = arguments.get("end_line", None)

    if not file_path:
        error_msg = "❌ Error: file_path parameter required"
        return error_msg, error_msg

    if verbose:
        rich_print(f"  ✍️  Replacing lines {start_line}-{end_line or 'end'} in: {file_path}", style="dim")

    try:
        # Read existing file
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        # Convert to 0-based indexing
        start_idx = max(0, start_line - 1)
        end_idx = min(len(lines), end_line) if end_line else len(lines)

        # Split new content into lines
        new_lines = content.split('\n')
        if new_lines and not new_lines[-1].endswith('\n'):
            new_lines = [line + '\n' for line in new_lines[:-1]] + [new_lines[-1]]
        else:
            new_lines = [line + '\n' for line in new_lines if line]

        # Replace the specified lines
        updated_lines = lines[:start_idx] + new_lines + lines[end_idx:]

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(updated_lines)

        result = f"✅ Successfully replaced lines {start_line}-{end_idx} in '{file_path}'"
        return result, result

    except Exception as e:
        error_msg = f"❌ Error updating '{file_path}': {str(e)}"
        return error_msg, error_msg


def execute_append_to_file(arguments: Dict, verbose: bool = False) -> Tuple[str, str]:
    """Append content to end of file"""
    file_path = arguments.get("file_path")
    content = arguments.get("content", "")

    if not file_path:
        error_msg = "❌ Error: file_path parameter required"
        return error_msg, error_msg

    if verbose:
        rich_print(f"  ➕ Appending to file: {file_path}", style="dim")

    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(content)

        result = f"✅ Successfully appended {len(content)} characters to '{file_path}'"
        return result, result

    except Exception as e:
        error_msg = f"❌ Error appending to '{file_path}': {str(e)}"
        return error_msg, error_msg

# Function registry
FUNCTION_HANDLERS = {
    "get_files_info": execute_get_files_info,
    "get_file_content": execute_get_file_content,
    "write_file": execute_write_file,
    "run_python_file": execute_run_python_file,
    "shell_command": execute_shell_command,

    "get_file_content_smart": execute_get_file_content_smart,
    "read_file_lines": execute_read_file_lines,
    "write_file_lines": execute_write_file_lines,
    "append_to_file": execute_append_to_file,
    "find_in_file": execute_find_in_file,
}


def execute_function(
    function_name: str, arguments: Dict, verbose: bool = False, config=None
) -> Tuple[str, str, any]:
    """Execute a function and return results"""
    if function_name not in FUNCTION_HANDLERS:
        error_msg = f"❌ Error: Unknown function '{function_name}'"
        return error_msg, error_msg, None

    try:
        handler = FUNCTION_HANDLERS[function_name]
        
        # Special handling for shell commands to check if enabled
        if function_name == "shell_command":
            if config and hasattr(config, 'shell_commands_enabled') and not config.shell_commands_enabled:
                error_msg = "❌ Error: Shell commands are disabled. Use /shellcmds on to enable."
                return error_msg, error_msg, None
        
        result = handler(arguments, verbose)

        # Handle different return formats
        if function_name == "get_files_info":
            ai_result, user_result, files_data = result
            return ai_result, user_result, files_data
        else:
            ai_result, user_result = result
            return ai_result, user_result, None

    except Exception as e:
        error_msg = f"❌ Error executing {function_name}: {str(e)}"
        return error_msg, error_msg, None

