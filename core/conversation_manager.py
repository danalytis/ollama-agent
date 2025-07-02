"""
Conversation history management with prompt reinforcement
"""

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class ConversationStats:
    """Track conversation statistics for adaptive reinforcement"""
    total_messages: int = 0
    function_calls: int = 0
    last_reinforcement: int = 0
    drift_score: float = 0.0  # How much the conversation has drifted


class ConversationManager:
    """Manages conversation history with intelligent prompt reinforcement"""

    def __init__(self, config, prompt_manager):
        self.config = config
        self.prompt_manager = prompt_manager
        self.stats = ConversationStats()
        self.messages: List[Dict] = []
        self.summary_buffer: List[str] = []  # Store summaries of trimmed content

    def initialize_conversation(self, system_prompt: str) -> None:
        """Start a new conversation with the system prompt"""
        self.messages = [{"role": "system", "content": system_prompt}]
        self.stats = ConversationStats()
        self.summary_buffer = []

    def add_message(self, role: str, content: str, is_function_result: bool = False) -> None:
        """Add a message with intelligent handling"""
        # Truncate function results if needed
        if is_function_result and len(content) > self.config.function_result_max_length:
            content = self._truncate_function_result(content)

        self.messages.append({"role": role, "content": content})
        self.stats.total_messages += 1

        if is_function_result:
            self.stats.function_calls += 1

        # Check if we need to reinforce or trim
        self._manage_conversation_health()

    def _manage_conversation_health(self) -> None:
        """Maintain conversation health through reinforcement and trimming"""
        # Check if we should reinforce
        if self._should_reinforce():
            self._reinforce_prompt()

        # Check if we should trim
        if len(self.messages) > self.config.max_conversation_length:
            self._trim_conversation()

    def _should_reinforce(self) -> bool:
        """Determine if prompt reinforcement is needed"""
        if not self.config.reinforce_enabled:
            return False

        messages_since_reinforcement = self.stats.total_messages - self.stats.last_reinforcement

        if self.config.prompt_strength_mode == "adaptive":
            # Adaptive mode: reinforce more frequently if we detect drift
            drift_threshold = self.config.reinforce_interval / (1 + self.stats.drift_score)
            return messages_since_reinforcement >= drift_threshold
        else:
            # Fixed mode: reinforce at regular intervals
            return messages_since_reinforcement >= self.config.reinforce_interval

    def _reinforce_prompt(self) -> None:
        """Add prompt reinforcement to the conversation"""
        base_prompt, _ = self.prompt_manager.load_prompt(self.config.current_prompt)

        # Create a contextual reinforcement based on conversation state
        reinforcement = self._create_reinforcement_message(base_prompt)

        # Add as a system message
        self.messages.append({
            "role": "system",
            "content": reinforcement
        })

        self.stats.last_reinforcement = self.stats.total_messages

    def _create_reinforcement_message(self, base_prompt: str) -> str:
        """Create an intelligent reinforcement message"""
        # Analyze recent conversation to create targeted reinforcement
        recent_context = self._analyze_recent_messages()

        if self.stats.function_calls > 5:
            # Heavy function use - remind about conversational aspects
            reminder = "Remember to maintain your defined personality and communication style while using functions. "
        elif "debug" in recent_context or "error" in recent_context:
            # Debugging context - reinforce problem-solving approach
            reminder = "Continue applying your systematic approach while maintaining your role. "
        else:
            reminder = ""

        # Extract key traits from the prompt
        key_traits = self._extract_key_traits(base_prompt)

        reinforcement = f"{reminder}Core directive: {key_traits}"

        return reinforcement

    def _extract_key_traits(self, prompt: str) -> str:
        """Extract the most important traits from the prompt"""
        # Take first paragraph or first 150 characters as key traits
        lines = prompt.split('\n')
        first_para = ""

        for line in lines:
            if line.strip():
                first_para = line.strip()
                break

        if len(first_para) > 150:
            first_para = first_para[:147] + "..."

        return first_para

    def _analyze_recent_messages(self) -> str:
        """Analyze recent messages for context"""
        # Look at last 5 non-system messages
        recent = []
        for msg in reversed(self.messages):
            if msg["role"] != "system":
                recent.append(msg["content"][:100].lower())
            if len(recent) >= 5:
                break

        return " ".join(recent)

    def _trim_conversation(self) -> None:
        """Intelligently trim conversation history"""
        # Always keep the original system prompt
        system_prompt = self.messages[0]

        if self.config.summarize_old_messages:
            # Create a summary of messages to be removed
            to_remove = self.messages[1:-(self.config.keep_recent_messages)]
            if to_remove:
                summary = self._create_conversation_summary(to_remove)
                self.summary_buffer.append(summary)

                # Add summary as a system message
                summary_msg = {
                    "role": "system",
                    "content": f"Previous conversation summary: {summary}"
                }

                # Reconstruct messages: system prompt + summary + recent messages
                recent_messages = self.messages[-(self.config.keep_recent_messages):]
                self.messages = [system_prompt, summary_msg] + recent_messages
        else:
            # Simple trim without summary
            recent_messages = self.messages[-(self.config.keep_recent_messages):]
            self.messages = [system_prompt] + recent_messages

    def _create_conversation_summary(self, messages: List[Dict]) -> str:
        """Create a concise summary of messages"""
        # Group by topic/function calls
        topics = []
        function_summary = {}

        for msg in messages:
            if "function_call" in msg.get("content", ""):
                # Track function usage
                func_match = json.loads(msg["content"]) if "{" in msg["content"] else {}
                if "function_call" in func_match:
                    func_name = func_match["function_call"].get("name", "unknown")
                    function_summary[func_name] = function_summary.get(func_name, 0) + 1
            else:
                # Extract key topics (simple approach)
                content = msg["content"][:200]
                if len(content.strip()) > 20:
                    topics.append(content.strip())

        summary_parts = []

        if function_summary:
            func_list = [f"{name}({count}x)" for name, count in function_summary.items()]
            summary_parts.append(f"Functions used: {', '.join(func_list)}")

        if topics:
            summary_parts.append(f"Topics discussed: {len(topics)} items")

        return "; ".join(summary_parts) if summary_parts else "General conversation"

    def _truncate_function_result(self, content: str) -> str:
        """Intelligently truncate function results"""
        max_len = self.config.function_result_max_length

        if len(content) <= max_len:
            return content

        # Try to truncate at a sensible point
        truncated = content[:max_len]

        # Look for good truncation points
        for delimiter in ['\n', '. ', ', ', ' ']:
            last_delimiter = truncated.rfind(delimiter)
            if last_delimiter > max_len * 0.8:  # Within 80% of max length
                truncated = truncated[:last_delimiter]
                break

        return f"{truncated}... [truncated from {len(content)} chars]"

    def get_messages(self) -> List[Dict]:
        """Get the current message list"""
        return self.messages

    def get_stats(self) -> Dict:
        """Get conversation statistics"""
        return {
            "total_messages": self.stats.total_messages,
            "function_calls": self.stats.function_calls,
            "last_reinforcement": self.stats.last_reinforcement,
            "drift_score": self.stats.drift_score,
            "current_length": len(self.messages),
            "summaries_created": len(self.summary_buffer)
        }

    def update_drift_score(self, response: str) -> None:
        """Update drift score based on response analysis"""
        # Simple heuristic: check if response seems off-topic or generic
        base_prompt, _ = self.prompt_manager.load_prompt(self.config.current_prompt)

        # Check for key terms from the prompt
        prompt_keywords = set(word.lower() for word in base_prompt.split()
                            if len(word) > 4)
        response_keywords = set(word.lower() for word in response.split()
                              if len(word) > 4)

        overlap = len(prompt_keywords & response_keywords)
        expected_overlap = min(5, len(prompt_keywords) // 10)

        if overlap < expected_overlap:
            self.stats.drift_score = min(1.0, self.stats.drift_score + 0.1)
        else:
            self.stats.drift_score = max(0.0, self.stats.drift_score - 0.05)
