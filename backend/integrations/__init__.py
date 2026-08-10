"""External service adapters."""

from .deepseek import (
    DeepSeekDialogueClient,
    DialogueContext,
    DialogueSuggestion,
)
from .tts import TtsRequest, TtsResult, TtsService
from .edge_voice import EdgeVoiceProvider
from .voice_contracts import (
    VoiceProvider,
    VoiceProviderName,
    VoiceSynthesisRequest,
    VoiceSynthesisResult,
)

__all__ = [
    "DeepSeekDialogueClient",
    "DialogueContext",
    "DialogueSuggestion",
    "EdgeVoiceProvider",
    "TtsRequest",
    "TtsResult",
    "TtsService",
    "VoiceProvider",
    "VoiceProviderName",
    "VoiceSynthesisRequest",
    "VoiceSynthesisResult",
]
