import ast
from typing import Protocol
from markdown_it import MarkdownIt
from src.model.model_indexing import ChunkSource, NodeContext


class ChunkerStrategy(Protocol):
    """Protocol for text chunking strategies."""

    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:
        """Split text into chunk sources.

        Args:
            text: The source text to chunk.
            file_path: The file path associated with the text.
            max_chunk_size: The maximum size of each chunk.

        Returns:
            A list of chunk metadata and content objects.
        """
        ...


class ChunkBuilder:
    """Assemble text chunks while preserving chunk boundaries and metadata."""

    def __init__(self, file_path: str, max_chunk_size: int):
        """Initialize the chunk assembly state.

        Args:
            file_path: The file path associated with generated chunks.
            max_chunk_size: The maximum size allowed for each chunk.
        """
        self.file_path = file_path
        self.max_chunk_size = max_chunk_size
        self.chunks: list[ChunkSource] = []
        self._current_chunk_text: str = ""
        self._current_start_char_idx: int = 0
        self._context_name = ""

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
                context_name=self._context_name,
                text=self._current_chunk_text
            )
        )
        self._current_start_char_idx += len(self._current_chunk_text)
        self._current_chunk_text = ""

    def process_lines(self, block_text: str) -> None:
        """Process oversized text line by line.

        Args:
            block_text: The text block to split across chunks.

        Returns:
            None.
        """

        for line in block_text.splitlines(keepends=True):
            if (len(line) + len(self._current_chunk_text) >
                    self.max_chunk_size and self._current_chunk_text):
                self.seal_chunk()

            while len(line) > 0:
                space_left = self.max_chunk_size - len(
                    self._current_chunk_text)
                self._current_chunk_text += line[:space_left]
                line = line[space_left:]

                if len(self._current_chunk_text) == self.max_chunk_size:
                    self.seal_chunk()

    def process_segment(self, block_text: str) -> None:
        """Route a text segment to the accumulator or the line splitter.

        Args:
            block_text: The text segment to process.

        Returns:
            None.
        """
        if len(self._current_chunk_text) + len(block_text) < (
                self.max_chunk_size):
            self._current_chunk_text += block_text
            return

        self.seal_chunk()

        if len(block_text) < self.max_chunk_size:
            self._current_chunk_text += block_text
            return

        self.process_lines(block_text)

    def try_process_full_document(self, text: str) -> bool:
        """Handle small documents as a single chunk.

        Args:
            text: The document text to evaluate.

        Returns:
            True if the document was stored as a single chunk; otherwise
            False.
        """
        if len(text) < self.max_chunk_size:
            self._context_name = "Full Document"
            self._current_chunk_text = text
            self.seal_chunk()
            return True
        return False

    def process_tail_and_seal(
            self, lines: list[str],
            last_line_idx: int) -> None:
        """Process any remaining lines and flush the final chunk.

        Args:
            lines: The document lines being chunked.
            last_line_idx: The index of the last processed line.

        Returns:
            None.
        """
        if last_line_idx < len(lines):
            remaining_text = "".join(lines[last_line_idx:])
            self.process_segment(remaining_text)
        self.seal_chunk()


class PythonChunker:
    """Chunk Python files by traversing their abstract syntax tree."""

    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:
        """Split Python source code into chunks.

        Args:
            text: The Python source code to chunk.
            file_path: The file path associated with the source code.
            max_chunk_size: The maximum size of each chunk.

        Returns:
            A list of chunk sources extracted from the Python file.
        """

        builder = ChunkBuilder(file_path, max_chunk_size)

        if builder.try_process_full_document(text):
            return builder.chunks

        tree = ast.parse(text)
        lines = text.splitlines(keepends=True)
        last_line_idx = 0
        node_ast: list[NodeContext] = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    node_ast.append(NodeContext(child, node.name))
            else:
                node_ast.append(NodeContext(node, None))

        for item in node_ast:
            node = item.node
            parent_class_name = item.class_name
            start_line_idx = last_line_idx
            end_line_idx: int = (
                node.end_lineno
                if node.end_lineno is not None
                else start_line_idx
            )
            block_text = "".join(lines[start_line_idx:end_line_idx])
            match node:
                case ast.FunctionDef(name=func_name) | (
                        ast.AsyncFunctionDef(name=func_name)):
                    if parent_class_name:
                        context_name = (
                            f"Class: {parent_class_name} - Method: {func_name}"
                            )
                    else:
                        context_name = f"Function: {func_name}"
                    builder._context_name = context_name
                case ast.ClassDef(name=class_name):
                    context_name = f"Class: {class_name}"
                    builder._context_name = context_name
                case _:
                    if parent_class_name:
                        context_name = (
                            f"Class: {parent_class_name} - Attribute/Setup")
                    else:
                        context_name = "Module level"
                    builder._context_name = context_name
            builder.process_segment(block_text)
            last_line_idx = end_line_idx

        builder.process_tail_and_seal(lines, last_line_idx)
        return builder.chunks


class MarkdownChunker:
    """Chunk Markdown files using Markdown-It token boundaries."""

    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:
        """Split Markdown content into chunks.

        Args:
            text: The Markdown text to chunk.
            file_path: The file path associated with the text.
            max_chunk_size: The maximum size of each chunk.

        Returns:
            A list of chunk sources extracted from the Markdown file.
        """

        builder = ChunkBuilder(file_path, max_chunk_size)

        if builder.try_process_full_document(text):
            return builder.chunks

        md = MarkdownIt()
        tokens = md.parse(text)
        lines = text.splitlines(keepends=True)

        last_line_idx = 0
        current_header = "Introduction"
        builder._context_name = f"Section: {current_header}"

        for i, token in enumerate(tokens):
            if token.type == "heading_open" and token.map is not None:
                start_line = token.map[0]

                if start_line > last_line_idx:
                    block_text = "".join(lines[last_line_idx:start_line])
                    builder.process_segment(block_text)
                    last_line_idx = start_line

                if i + 1 < len(tokens) and tokens[i+1].type == "inline":
                    current_header = tokens[i+1].content.strip()

                builder.seal_chunk()
                builder._context_name = f"Section: {current_header}"

        builder.process_tail_and_seal(lines, last_line_idx)

        return builder.chunks


class TextChunker:
    """Fallback chunker for plain text and structured text files."""

    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:
        """Split plain text into chunks.

        Args:
            text: The text to chunk.
            file_path: The file path associated with the text.
            max_chunk_size: The maximum size of each chunk.

        Returns:
            A list of chunk sources extracted from the text file.
        """

        builder = ChunkBuilder(file_path, max_chunk_size)
        builder._context_name = "Fallback Text"

        if builder.try_process_full_document(text):
            return builder.chunks

        builder.process_segment(text)
        builder.seal_chunk()

        return builder.chunks
