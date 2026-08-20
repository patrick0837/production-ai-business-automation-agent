class AIProviderError(RuntimeError):
    """Base exception for AI provider failures."""


class TransientAIProviderError(AIProviderError):
    """Temporary provider failure that may succeed on retry."""


class InvalidAIResponseError(AIProviderError):
    """The provider returned data that does not match our contract."""