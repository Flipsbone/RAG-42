import ast
from typing import Protocol
from indexing.model_indexation import MinimalSource

class ChunkerStrategy(Protocol):
    def chunk(self, text: str, file_path: str, max_chunk_size: int) -> list[MinimalSource]:
        """All chunkers must implement this method and return a list of MinimalSource objects."""
        ...

class MarkdownChunker:
    def chunk(self, text: str, file_path: str, max_chunk_size: int) -> list[MinimalSource]:
        # Langchain logic goes here...
        result: list[MinimalSource] = []
        return result

class PythonChunker:
    def chunk(self, text: str, file_path: str, max_chunk_size: int) -> list[MinimalSource]:
        tree = ast.parse(text)
        previous_line = 0
        bloc_code: list[str] = []
        for node in tree.body:
            end_line = node.end_lineno
            code_node = ast.get_source_segment(text, node)
            size_node = len(code_node)
            print(code_node)
            print(size_node)
        source = MinimalSource(
            file_path=file_path,
            first_character_index=0,
            last_character_index=len(text)
        )
        return [source]
        