import ast
from typing import Protocol
from markdown_it import MarkdownIt
from src.indexing.model_indexation import ChunkSource


class ChunkerStrategy(Protocol):
    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:
        """All chunkers must implement this method and
        return a list of ChunkSource objects."""
        ...


class ChunkBuilder:
    """Manages the global state and assembly of text chunks
    while strictly respecting the maximum allowed size."""

    def __init__(self, file_path: str, max_chunk_size: int):
        self.file_path = file_path
        self.max_chunk_size = max_chunk_size
        self.chunks: list[ChunkSource] = []
        self._current_chunk_text: str = ""
        self._current_start_char_idx: int = 0

    def seal_chunk(self) -> None:
        """Seals the current chunk, saves its precise metadata,
        and resets the accumulator."""
        if not self._current_chunk_text:
            return
        self.chunks.append(
            ChunkSource(
                file_path=self.file_path,
                first_character_index=self._current_start_char_idx,
                last_character_index=(
                    self._current_start_char_idx + len(
                        self._current_chunk_text)),
                text=self._current_chunk_text
            )
        )
        self._current_start_char_idx += len(self._current_chunk_text)
        self._current_chunk_text = ""

    def process_lines(self, block_text: str, context_name: str) -> None:
        """Processes a block line by line when
        it natively exceeds the max size.
        """
        header = f"# [Continued: {context_name}]\n" if context_name else ""

        for line in block_text.splitlines(keepends=True):
            if len(line) + len(self._current_chunk_text) > (
                    self.max_chunk_size and self._current_chunk_text):
                self.seal_chunk()
                self._current_chunk_text = header
                header = ""

            while len(line) > 0:
                space_left = self.max_chunk_size - len(
                    self._current_chunk_text)
                self._current_chunk_text += line[:space_left]
                line = line[space_left:]

                if len(self._current_chunk_text) == self.max_chunk_size:
                    self.seal_chunk()
                    self._current_chunk_text = header
                    header = ""

    def process_segment(self, block_text: str, context_name: str) -> None:
        """Evaluates and routes a text segment
        to the accumulator or line processing.
        """
        if len(self._current_chunk_text) + len(block_text) < (
                self.max_chunk_size):
            self._current_chunk_text += block_text
            return

        self.seal_chunk()

        if len(block_text) <= self.max_chunk_size:
            self._current_chunk_text += block_text
            return

        self.process_lines(block_text, context_name)


class PythonChunker:
    """Parses Python files via AST and delegates assembly to the ChunkBuilder
    """

    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:

        builder = ChunkBuilder(file_path, max_chunk_size)
        tree = ast.parse(text)
        lines = text.splitlines(keepends=True)
        last_line_idx = 0

        for node in tree.body:
            start_line_idx = last_line_idx
            end_line_idx: int | None = node.end_lineno or start_line_idx
            block_text = "".join(lines[start_line_idx:end_line_idx])

            match node:
                case ast.FunctionDef(name=func_name) | (
                        ast.AsyncFunctionDef(name=func_name)):
                    context_name = f"Function: {func_name}"
                case ast.ClassDef(name=class_name):
                    context_name = f"Class: {class_name}"
                case _:
                    context_name = "Module level"

            builder.process_segment(block_text, context_name)
            last_line_idx = end_line_idx

        remaining_text = "".join(lines[last_line_idx:])
        if remaining_text:
            builder.process_segment(remaining_text, "Trailing code")

        builder.seal_chunk()
        return builder.chunks


class MarkdownChunker:
    """Parses Markdown files via markdown-it-py
        and delegates assembly to the ChunkBuilder.
    """

    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:

        builder = ChunkBuilder(file_path, max_chunk_size)
        md = MarkdownIt()
        tokens = md.parse(text)

        lines = text.splitlines(keepends=True)
        last_line_idx = 0
        current_heading = "Document start"
