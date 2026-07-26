"""External service adapters."""

from .deepseek import (
    DeepSeekDialogueClient,
    DialogueContext,
    DialogueSuggestion,
)

__all__ = [
    "DeepSeekDialogueClient",
    "DialogueContext",
    "DialogueSuggestion",
]
