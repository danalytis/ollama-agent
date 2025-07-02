# AI Agent System Prompts

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
