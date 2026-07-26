"""External service adapters."""

from .deepseek import (
    DeepSeekDialogueClient,
    DialogueContext,
    DialogueSuggestion,
)
from .tts import TtsRequest, TtsResult, TtsService

__all__ = [
    "DeepSeekDialogueClient",
    "DialogueContext",
    "DialogueSuggestion",
    "TtsRequest",
    "TtsResult",
    "TtsService",
]
