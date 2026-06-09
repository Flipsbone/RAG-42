from typing import Protocol
from model_indexation import MinimalSource

class ChunkerStrategy(Protocol):
    def chunk(self, text: str, file_path: str, max_chunk_size: int) -> list[MinimalSource]:
        """All chunkers must implement this method and return a list of MinimalSource objects."""
        ...

class MarkdownChunker:
    def chunk(self, text: str, file_path: str, max_chunk_size: int) -> list[MinimalSource]:
        # Langchain logic goes here...
        pass

class PythonChunker:
    def chunk(self, text: str, file_path: str, max_chunk_size: int) -> list[MinimalSource]:
        # AST logic goes here...
        pass