class IndexationError(Exception):
    """
    All errors specific append inside the indexer.
    """
    def __init__(self, failed_logs: list[dict]):
        self.failed_logs = failed_logs
        super().__init__(f"{len(failed_logs)} files failed during indexation.")


class RetrieverError(Exception):
    """
    All errors specific append inside the retriever.
    """
    pass


class FileSecurityError(Exception):
    """Raised when an integrity check or hash is invalid."""
    pass


class FileAccessError(Exception):
    """Raised when a disk access problem occurs."""
    pass


class GeneratorError(Exception):
    """
    All errors specific append inside Generate
    """
    pass


class EvaluatError(Exception):
    """
    All errors specific append inside Generate
    """
    pass
