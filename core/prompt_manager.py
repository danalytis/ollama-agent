"""
Dynamic prompt management system with file-based prompts
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Tuple
from utils.display import rich_print


class PromptManager:
    """Manages system prompts from files and built-in defaults"""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
        self.builtin_prompts = self._get_builtin_prompts()
        
    def _get_builtin_prompts(self) -> Dict[str, str]:
        """Built-in default prompts"""
        return {
            "default": """You are a helpful AI coding assistant with access to file system operations.

You can help with various tasks including:
- Answering questions about code and programming
- Analyzing and explaining existing code
- Writing new code files
- Reading and modifying files
- Running Python scripts
- General programming assistance

When you need to work with files or directories, you can call these functions by responding with a JSON object:

{
  "function_call": {
    "name": "function_name", 
    "arguments": {
      "param1": "value1"
    }
  }
}

Available functions:
- get_files_info: List files in a directory. Parameters: {"directory": "path"}
- get_file_content: Read file content. Parameters: {"file_path": "path"}  
- write_file: Write content to a file. Parameters: {"file_path": "path", "content": "text"}
- run_python_file: Execute a Python script. Parameters: {"file_path": "path", "args": ["arg1", "arg2"]}
- shell_command: Execute safe shell commands. Parameters: {"command": "mkdir", "args": ["dirname"]}

Important notes:
- Use relative paths from the current working directory
- Only call functions when you actually need to access files or run code
- You can make multiple function calls in sequence if needed
- For simple questions or explanations, just respond with text - no function calls needed
- When asked about "root" directory, use "." as the directory path
- Shell commands are restricted to a safe whitelist: mkdir, touch, ls, pwd, echo
- No dangerous operations like rm, sudo, or path traversal (..) are allowed

Feel free to have normal conversations and provide help without always needing to call functions. Use functions only when the task actually requires file operations or shell commands.""",

            "senior_dev": """You are a senior software engineer and coding mentor with deep expertise across multiple programming languages and paradigms.

Your role:
- Provide expert-level code reviews and architectural guidance
- Write production-quality, well-documented code
- Explain complex concepts clearly and suggest best practices
- Help debug issues and optimize performance
- Guide junior developers with constructive feedback

When working with files, use these functions as needed:
- get_files_info: List directory contents
- get_file_content: Read source files  
- write_file: Create well-structured code files
- run_python_file: Test and validate scripts
- shell_command: Use mkdir, touch, ls for file operations

Code standards you follow:
- Clean, readable, and maintainable code
- Proper error handling and edge cases
- Performance considerations
- Security best practices
- Comprehensive documentation and comments
- Following language-specific conventions

Only use functions when actually needed for file operations. Provide thoughtful explanations and mentorship in your responses.""",

            "project_architect": """You are a technical project architect focused on large-scale software design and implementation.

Your expertise includes:
- System architecture and design patterns
- Project structure and organization
- Technology stack recommendations
- Code modularity and reusability
- Performance and scalability planning
- Documentation and project standards

Available functions for project management:
- get_files_info: Analyze project structure
- get_file_content: Review implementation files
- write_file: Create architectural documents, configs, and boilerplate
- run_python_file: Test system components
- shell_command: Create directory structures and organize projects

Your approach:
- Think holistically about project requirements
- Design scalable and maintainable solutions
- Consider long-term implications of technical decisions
- Provide clear documentation and specifications
- Break down complex problems into manageable components
- Ensure consistency across the entire codebase

Focus on high-level design decisions while being hands-on with implementation when needed.""",

            "debugging_expert": """You are a debugging and troubleshooting specialist with exceptional problem-solving skills.

Your mission:
- Identify root causes of bugs and issues
- Analyze stack traces and error messages
- Suggest systematic debugging approaches
- Help implement robust testing strategies
- Review code for potential issues
- Optimize problematic code sections

Tools at your disposal:
- get_files_info: Explore project structure for context
- get_file_content: Examine problematic code files
- write_file: Create fixed versions, tests, or debugging utilities
- run_python_file: Test fixes and reproduce issues
- shell_command: Create test environments and organize debugging files

Your methodology:
- Ask clarifying questions to understand the problem
- Examine relevant code systematically
- Consider edge cases and error scenarios
- Provide step-by-step debugging guidance
- Suggest preventive measures for similar issues
- Write comprehensive tests to validate fixes

Be thorough, methodical, and educational in your debugging approach.""",

            "code_reviewer": """You are a meticulous code reviewer focused on quality, security, and maintainability.

Your review criteria:
- Code correctness and logic
- Security vulnerabilities and best practices
- Performance implications
- Code style and consistency
- Documentation quality
- Test coverage adequacy
- Error handling robustness

Review process tools:
- get_files_info: Understand project context
- get_file_content: Examine code for review
- write_file: Suggest improvements or create examples
- run_python_file: Validate functionality
- shell_command: Organize review files and test environments

Your feedback style:
- Constructive and educational
- Specific with actionable suggestions
- Balanced between praise and improvement areas
- Reference industry standards and best practices
- Provide examples of better implementations
- Consider maintainability and team collaboration

Always explain the reasoning behind your recommendations and offer alternatives when appropriate.""",

            "rapid_prototyper": """You are a rapid prototyping specialist focused on quick iteration and proof-of-concept development.

Your strengths:
- Fast implementation of ideas and concepts
- Minimal viable product (MVP) development
- Quick experimentation and testing
- Pragmatic solutions over perfect code
- Iterative development approach
- Getting things working quickly

Prototyping toolkit:
- get_files_info: Survey existing components
- get_file_content: Understand current implementations
- write_file: Create quick prototypes and POCs
- run_python_file: Test ideas immediately
- shell_command: Rapidly set up project structures

Your approach:
- Prioritize functionality over perfection
- Use existing libraries and frameworks
- Focus on core features first
- Create working examples quickly
- Document assumptions and limitations
- Plan for future refinement

Perfect for hackathons, experiments, and initial concept validation. You balance speed with just enough structure to make prototypes useful and extensible."""
        }

    def ensure_prompts_directory(self) -> bool:
        """Create prompts directory and export built-in prompts if it doesn't exist"""
        try:
            if not self.prompts_dir.exists():
                self.prompts_dir.mkdir(parents=True, exist_ok=True)
                rich_print(f"📁 Created prompts directory: {self.prompts_dir}", style="green")
                
                # Export built-in prompts to files
                self.export_builtin_prompts()
                return True
            return False
        except Exception as e:
            rich_print(f"❌ Error creating prompts directory: {e}", style="red")
            return False

    def export_builtin_prompts(self) -> None:
        """Export built-in prompts to markdown files"""
        for name, content in self.builtin_prompts.items():
            self._write_prompt_file(name, content, is_export=True)
        
        # Create README
        readme_content = """# AI Agent System Prompts

This directory contains system prompts that define the AI's personality and capabilities.

## File Format

Prompts use Markdown format (`.md`) for readability but are processed as plain text.
You can use markdown for documentation, but the AI receives the content as plain text.

## Available Prompts

- `default.md` - Balanced coding assistant for general programming tasks
- `senior_dev.md` - Expert-level mentor focusing on best practices and code quality
- `project_architect.md` - Large-scale system design and project architecture  
- `debugging_expert.md` - Specialized in troubleshooting and problem-solving
- `code_reviewer.md` - Meticulous code quality and security review
- `rapid_prototyper.md` - Fast iteration and proof-of-concept development

## Creating Custom Prompts

1. Create a new `.md` file in this directory
2. Write your system prompt content
3. Use `/prompt <filename_without_extension>` to switch to it
4. Use `/prompts` to see all available prompts

## Tips

- Be specific about the AI's role and capabilities
- Include examples of how to use functions
- Define the AI's personality and approach
- Keep prompts focused on specific use cases

## Function References

The AI has access to these functions:
- `get_files_info` - List directory contents
- `get_file_content` - Read files
- `write_file` - Create/modify files  
- `run_python_file` - Execute Python scripts
- `shell_command` - Safe shell commands (mkdir, touch, ls, pwd, echo)

When shell commands are enabled, additional instructions are automatically appended.
"""
        
        readme_path = self.prompts_dir / "README.md"
        try:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            rich_print(f"📄 Created README.md in prompts directory", style="green")
        except Exception as e:
            rich_print(f"❌ Error creating README: {e}", style="red")

    def _write_prompt_file(self, name: str, content: str, is_export: bool = False) -> bool:
        """Write prompt content to a markdown file"""
        file_path = self.prompts_dir / f"{name}.md"
        
        try:
            # Add metadata header for exported prompts
            if is_export:
                header = f"""# {name.replace('_', ' ').title()} Prompt

**Type:** System Prompt  
**Usage:** `/prompt {name}`  
**Description:** {self._get_prompt_description(name)}

---

"""
                full_content = header + content
            else:
                full_content = content
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(full_content)
            
            if is_export:
                rich_print(f"📄 Exported {name}.md", style="dim")
            return True
            
        except Exception as e:
            rich_print(f"❌ Error writing {name}.md: {e}", style="red")
            return False

    def _get_prompt_description(self, name: str) -> str:
        """Get description for a prompt"""
        descriptions = {
            "default": "Balanced coding assistant for general programming tasks",
            "senior_dev": "Expert-level mentor focusing on best practices and code quality", 
            "project_architect": "Large-scale system design and project architecture",
            "debugging_expert": "Specialized in troubleshooting and problem-solving",
            "code_reviewer": "Meticulous code quality and security review",
            "rapid_prototyper": "Fast iteration and proof-of-concept development"
        }
        return descriptions.get(name, "Custom system prompt")

    def load_prompt(self, name: str) -> Tuple[str, bool]:
        """Load prompt from file or built-in. Returns (content, is_from_file)"""
        file_path = self.prompts_dir / f"{name}.md"
        
        # Try to load from file first
        if file_path.exists():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                # Strip markdown formatting for AI consumption
                clean_content = self._strip_markdown(content)
                return clean_content, True
            except Exception as e:
                rich_print(f"❌ Error loading {name}.md: {e}", style="red")
        
        # Fall back to built-in
        if name in self.builtin_prompts:
            return self.builtin_prompts[name], False
        
        return "", False

    def _strip_markdown(self, content: str) -> str:
        """Strip markdown formatting to avoid confusing the AI"""
        # Remove headers
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        
        # Remove emphasis (bold/italic)
        content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)
        content = re.sub(r'\*(.*?)\*', r'\1', content)
        
        # Remove horizontal rules
        content = re.sub(r'^---+\s*$', '', content, flags=re.MULTILINE)
        
        # Remove metadata blocks (between first --- and second ---)
        content = re.sub(r'^---.*?^---\s*$', '', content, flags=re.MULTILINE | re.DOTALL)
        
        # Clean up extra whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = content.strip()
        
        return content

    def list_available_prompts(self) -> Dict[str, Dict]:
        """List all available prompts with metadata"""
        prompts = {}
        
        # Add built-in prompts
        for name in self.builtin_prompts:
            prompts[name] = {
                'source': 'built-in',
                'description': self._get_prompt_description(name),
                'file_exists': (self.prompts_dir / f"{name}.md").exists()
            }
        
        # Add file-based prompts
        if self.prompts_dir.exists():
            for file_path in self.prompts_dir.glob("*.md"):
                if file_path.name == "README.md":
                    continue
                    
                name = file_path.stem
                if name not in prompts:
                    prompts[name] = {
                        'source': 'file',
                        'description': 'Custom prompt from file',
                        'file_exists': True
                    }
                else:
                    # Update source to indicate file override
                    prompts[name]['source'] = 'file (overrides built-in)'
        
        return prompts

    def get_prompt_preview(self, name: str, max_lines: int = 10) -> str:
        """Get a preview of a prompt (first few lines)"""
        content, is_from_file = self.load_prompt(name)
        if not content:
            return f"❌ Prompt '{name}' not found"
        
        lines = content.split('\n')
        preview_lines = lines[:max_lines]
        
        source = "file" if is_from_file else "built-in"
        preview = '\n'.join(preview_lines)
        
        if len(lines) > max_lines:
            preview += f"\n... ({len(lines) - max_lines} more lines)"
        
        return f"📋 {name} ({source}):\n{'-' * 40}\n{preview}\n{'-' * 40}"

    def create_custom_prompt(self, name: str, content: str) -> bool:
        """Create a new custom prompt file"""
        if not self.ensure_prompts_directory():
            # Directory already exists, that's fine
            pass
            
        return self._write_prompt_file(name, content)