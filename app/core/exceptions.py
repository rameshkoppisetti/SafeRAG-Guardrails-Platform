class SafeRAGError(Exception):
    pass


class GuardrailBlockedError(SafeRAGError):
    pass


class UnauthorizedRetrievalError(SafeRAGError):
    pass
