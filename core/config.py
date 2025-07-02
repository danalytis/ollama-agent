"""
Configuration management for the Ollama AI Agent
"""

from dataclasses import dataclass
from typing import List, Dict


@dataclass
class AgentConfig:
    """Configuration for the AI agent"""

    model: str = "qwen2.5-coder:7b"
    verbose: bool = False
    typing_speed: float = 0.03
    typing_enabled: bool = True
    syntax_highlighting: bool = True
    rich_enabled: bool = True
    max_turns: int = 20
    api_base: str = "http://localhost:11434"
    
    # Model parameters
    temperature: float = 0.1
    top_p: float = 0.9
    top_k: int = 40
    num_predict: int = 4096
    repeat_penalty: float = 1.1
    
    # System prompt management
    current_prompt: str = "default"
    
    # Directory safety settings
    safe_mode: bool = True
    allowed_base_dirs: List[str] = None
    
    # Shell command safety
    shell_commands_enabled: bool = True  # Can be disabled as kill switch
    
    def __post_init__(self):
        """Initialize default allowed directories"""
        if self.allowed_base_dirs is None:
            import os
            self.allowed_base_dirs = [
                os.path.expanduser("~"),  # User home directory
                os.getcwd(),              # Current working directory
                "/tmp",                   # Temporary directory
                "/var/tmp",               # Alternative temp directory
            ]

    def toggle_verbose(self) -> None:
        """Toggle verbose mode"""
        self.verbose = not self.verbose

    def toggle_syntax_highlighting(self) -> None:
        """Toggle syntax highlighting"""
        self.syntax_highlighting = not self.syntax_highlighting

    def toggle_typing(self) -> None:
        """Toggle typing animation"""
        self.typing_enabled = not self.typing_enabled

    def set_typing_speed(self, speed: float) -> bool:
        """Set typing speed, returns True if valid"""
        if 0.005 <= speed <= 0.2:
            self.typing_speed = speed
            return True
        return False
    
    def set_temperature(self, temp: float) -> bool:
        """Set temperature, returns True if valid"""
        if 0.0 <= temp <= 2.0:
            self.temperature = temp
            return True
        return False
    
    def set_top_p(self, p: float) -> bool:
        """Set top_p, returns True if valid"""
        if 0.0 <= p <= 1.0:
            self.top_p = p
            return True
        return False
    
    def set_top_k(self, k: int) -> bool:
        """Set top_k, returns True if valid"""
        if 1 <= k <= 100:
            self.top_k = k
            return True
        return False
    
    def set_num_predict(self, num: int) -> bool:
        """Set num_predict, returns True if valid"""
        if 1 <= num <= 8192:
            self.num_predict = num
            return True
        return False
    
    def set_repeat_penalty(self, penalty: float) -> bool:
        """Set repeat_penalty, returns True if valid"""
        if 0.5 <= penalty <= 2.0:
            self.repeat_penalty = penalty
            return True
        return False
    
    def set_api_base(self, url: str) -> bool:
        """Set API base URL, returns True if valid"""
        if url.startswith(('http://', 'https://')):
            self.api_base = url.rstrip('/')
            return True
        return False
    
    def get_model_options(self) -> Dict:
        """Get current model options for API calls"""
        return {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "num_predict": self.num_predict,
            "repeat_penalty": self.repeat_penalty
        }


# Legacy function for backwards compatibility
def get_system_prompt(prompt_name: str) -> str:
    """Get system prompt by name - now redirects to PromptManager"""
    from core.prompt_manager import PromptManager
    manager = PromptManager()
    content, _ = manager.load_prompt(prompt_name)
    return content if content else "You are a helpful AI assistant."


def list_system_prompts() -> Dict[str, str]:
    """Get all available system prompts with descriptions"""
    from core.prompt_manager import PromptManager
    manager = PromptManager()
    prompts = manager.list_available_prompts()
    
    # Convert to old format for compatibility
    descriptions = {}
    for name, info in prompts.items():
        descriptions[name] = info['description']
    
    return descriptions