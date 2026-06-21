import ast
from typing import Protocol
from markdown_it import MarkdownIt
from src.model.model_indexing import ChunkSource


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

    def process_lines(self, block_text: str, context_name: str) -> None:
        """Processes a block line by line when
        it natively exceeds the max size.
        """
        # header = f"# [Continued: {context_name}]\n" if context_name else ""

        for line in block_text.splitlines(keepends=True):
            if (len(line) + len(self._current_chunk_text) >
                    self.max_chunk_size and self._current_chunk_text):
                self.seal_chunk()
                # self._current_chunk_text = header
                # header = ""

            while len(line) > 0:
                space_left = self.max_chunk_size - len(
                    self._current_chunk_text)
                self._current_chunk_text += line[:space_left]
                line = line[space_left:]

                if len(self._current_chunk_text) == self.max_chunk_size:
                    self.seal_chunk()
                    # self._current_chunk_text = header
                    # header = ""

    def process_segment(self, block_text: str, context_name: str) -> None:
        """Evaluates and routes a text segment
        to the accumulator or line processing.
        """
        if len(self._current_chunk_text) + len(block_text) < (
                self.max_chunk_size):
            self._current_chunk_text += block_text
            return

        self.seal_chunk()

        if len(block_text) < self.max_chunk_size:
            self._current_chunk_text += block_text
            return

        self.process_lines(block_text, context_name)

    def try_process_full_document(self, text: str) -> bool:
        """Handles the fast-path for small documents.
        Returns True if processed.
        """
        if len(text) < self.max_chunk_size:
            self._context_name = "Full Document"
            self._current_chunk_text = text
            self.seal_chunk()
            return True
        return False

    def process_tail_and_seal(
            self, lines: list[str],
            last_line_idx: int,
            context_name: str) -> None:
        """Processes any remaining lines and seals the final chunk."""
        if last_line_idx < len(lines):
            remaining_text = "".join(lines[last_line_idx:])
            self.process_segment(remaining_text, context_name)
        self.seal_chunk()


class PythonChunker:
    """Parses Python files via AST and delegates assembly to the ChunkBuilder
    """

    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:

        builder = ChunkBuilder(file_path, max_chunk_size)

        if builder.try_process_full_document(text):
            return builder.chunks

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
                    builder._context_name = context_name
                case ast.ClassDef(name=class_name):
                    context_name = f"Class: {class_name}"
                    builder._context_name = context_name
                case _:
                    context_name = "Module level"
                    builder._context_name = context_name
            builder.process_segment(block_text, context_name)
            last_line_idx = end_line_idx

        builder.process_tail_and_seal(lines, last_line_idx, "Trailing code")
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
        if builder.try_process_full_document(text):
            return builder.chunks

        md = MarkdownIt()
        tokens = md.parse(text)
        lines = text.splitlines(keepends=True)
        last_line_idx: int = 0
        current_header = "Introduction"
        header_stack = {}

        for i, token in enumerate(tokens):
            if token.type == "heading_open":
                level = int(token.tag[1]) 
                if i + 1 < len(tokens) and tokens[i+1].type == "inline":
                    header_text = tokens[i+1].content.strip()
                    keys_to_remove = [k for k in header_stack.keys() if k >= level]
                    for k in keys_to_remove:
                        del header_stack[k]
                    header_stack[level] = header_text
                    current_header = " > ".join([header_stack[k] for k in sorted(header_stack.keys())])
            if token.map is not None:
                start_line, end_line = token.map
                is_valid_block = (
                    (token.nesting == 1) or (token.type == "fence"))
                if is_valid_block and start_line >= last_line_idx:
                    block_text = "".join(lines[last_line_idx:end_line])
                    context_name = f"Section: {current_header}"
                    builder._context_name = context_name
                    builder.process_segment(block_text, context_name)
                    last_line_idx = end_line

        builder.process_tail_and_seal(
            lines, last_line_idx, f"Section: {current_header}")

        return builder.chunks
