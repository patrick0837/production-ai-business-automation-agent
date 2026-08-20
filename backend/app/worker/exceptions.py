class TransientProcessingError(RuntimeError):
    """A temporary processing failure that may succeed on retry."""