# Ollama AI Agent - Enhanced Edition

A powerful, interactive AI coding assistant with function calling capabilities, system prompt management, model parameter controls, and remote connectivity.

## 🚀 New Features

### System Prompt Management
- **6 specialized prompts**: Default, Senior Developer, Project Architect, Debugging Expert, Code Reviewer, Rapid Prototyper
- **Runtime switching**: Change AI personality without restarting
- **Preview prompts**: View current system prompt anytime

### Model Parameter Controls
- **Temperature control**: Adjust creativity (0.0=focused, 2.0=chaotic)
- **Nucleus sampling**: Fine-tune response diversity
- **Repeat penalties**: Control output repetition
- **Token limits**: Set response length
- **Real-time adjustment**: Change parameters during conversation

### Remote Connectivity
- **Remote Ollama**: Connect to Ollama on other machines
- **Connection testing**: Verify remote connections
- **Runtime switching**: Change connections on-the-fly

## Prerequisites

1. **Ollama**: Install and run Ollama locally or remotely
   ```bash
   # Install Ollama (see https://ollama.ai for your platform)
   
   # Start Ollama server
   ollama serve
   
   # Pull a coding model (recommended)
   ollama pull qwen2.5-coder:7b
   ```

2. **Python**: Python 3.8+ with pip

## Installation

1. **Clone/Download** the project files
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Directory Structure

```
ollama-agent/
├── main.py                 # Entry point
├── core/
│   ├── __init__.py        # Empty file
│   ├── agent.py           # Main AI agent logic
│   ├── config.py          # Configuration and system prompts
│   └── functions.py       # Function handlers
├── utils/
│   ├── __init__.py        # Empty file
│   ├── display.py         # Rich formatting and display
│   └── terminal.py        # Terminal utilities
├── requirements.txt       # Dependencies
└── README.md             # This file
```

**Important**: Create empty `__init__.py` files:
```bash
mkdir -p core utils
touch core/__init__.py utils/__init__.py
```

## Usage

### Enhanced Command Line Options
```bash
python main.py --help

Options:
  --interactive          Run in interactive mode
  --prompt TEXT          Single user input prompt
  --verbose             Show detailed debug output
  --model TEXT          Ollama model to use (default: qwen2.5-coder:7b)
  --list-models         List available Ollama models
  --api-base URL        Ollama API base URL (for remote connections)
  --prompt-type TYPE    System prompt type (see Available System Prompts)
  --temperature FLOAT   Model temperature (0.0-2.0, creativity level)
  --typing-speed FLOAT  Typing animation speed (0.005-0.2)
  --no-typing          Disable typing animation
  --no-syntax          Disable syntax highlighting
  --no-rich            Disable Rich formatting entirely
```

### Examples

**Local usage with custom prompt:**
```bash
python main.py --interactive --prompt-type senior_dev --temperature 0.7
```

**Remote Ollama connection:**
```bash
python main.py --interactive --api-base http://192.168.1.100:11434
```

**Debugging specialist with high creativity:**
```bash
python main.py --interactive --prompt-type debugging_expert --temperature 1.2
```

## Available System Prompts

| Prompt | Description | Best For |
|--------|-------------|----------|
| **default** | Balanced coding assistant | General programming tasks |
| **senior_dev** | Expert mentor focusing on best practices | Code reviews, mentoring, production code |
| **project_architect** | Large-scale system design specialist | Architecture planning, project structure |
| **debugging_expert** | Problem-solving and troubleshooting | Bug hunting, error analysis, optimization |
| **code_reviewer** | Quality and security focused reviewer | Code audits, security analysis, standards |
| **rapid_prototyper** | Fast iteration and MVP development | Hackathons, POCs, quick experiments |

## Enhanced Interactive Commands

### System Prompt Management
| Command | Description |
|---------|-------------|
| `/prompts` | List all available system prompts |
| `/prompt <n>` | Switch to different system prompt |
| `/showprompt` | Display current system prompt |

### Model Parameter Controls
| Command | Description |
|---------|-------------|
| `/params` | Show current model parameters |
| `/temperature <0-2>` | Set creativity level |
| `/topp <0-1>` | Set nucleus sampling |
| `/topk <1-100>` | Set top-k sampling |
| `/maxtokens <1-8192>` | Set response length limit |
| `/penalty <0.5-2>` | Set repeat penalty |

### Connectivity
| Command | Description |
|---------|-------------|
| `/connect <url>` | Connect to remote Ollama instance |

### Enhanced Status
| Command | Description |
|---------|-------------|
| `/status` | Show comprehensive session status |

## Example Workflows

### 1. Code Review Session
```bash
python main.py --interactive --prompt-type code_reviewer

[code_reviewer]> /temperature 0.3
[code_reviewer]> Please review the security of my authentication code
```

### 2. Debugging Session
```bash
python main.py --interactive --prompt-type debugging_expert

[debugging_expert]> /verbose
[debugging_expert]> I'm getting a memory leak in my Python application
```

### 3. Architecture Planning
```bash
python main.py --interactive --prompt-type project_architect

[project_architect]> /temperature 
