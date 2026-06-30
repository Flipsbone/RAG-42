class IndexationError(Exception):
    """Raised when one or more files fail during indexation."""

    def __init__(self, failed_logs: list[dict[str, str]]):
        """Store the failed file logs and build the exception message.

        Args:
            failed_logs: A list of file/error mappings collected during
                indexation.
        """
        self.failed_logs = failed_logs
        super().__init__(f"{len(failed_logs)} files failed during indexation.")


class RetrieverError(Exception):
    """Raised when retrieval or index loading fails."""


class FileSecurityError(Exception):
    """Raised when an integrity check or hash is invalid."""
    pass


class FileAccessError(Exception):
    """Raised when a disk access problem occurs."""
    pass


class GeneratorError(Exception):
    """Raised when answer or question generation fails."""
    pass


class EvaluatError(Exception):
    """Raised when evaluation of retrieved results fails."""
    pass
