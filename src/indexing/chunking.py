import ast
from typing import Protocol
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


class MarkdownChunker:
    def chunk(
            self,
            text: str,
            file_path: str,
            max_chunk_size: int) -> list[ChunkSource]:
        # Langchain logic goes here...
        result: list[ChunkSource] = []
        return result


class PythonChunker:
    def chunk(self,
              text: str,
              file_path: str,
              max_chunk_size: int) -> list[ChunkSource]:

        chunks: list[ChunkSource] = []
        tree: ast.Module = ast.parse(text)

        lines: str = text.splitlines(keepends=True)
        current_chunk_text: str = ""
        current_start_char_idx: int = 0
        last_processed_line: int = 0

        def seal_chunk():
            nonlocal current_chunk_text, current_start_char_idx
            if current_chunk_text:
                chunks.append(
                    ChunkSource(
                        file_path=file_path,
                        first_character_index=current_start_char_idx,
                        last_character_index=(
                            current_start_char_idx + len(current_chunk_text)),
                        text=current_chunk_text
                    )
                )
                current_start_char_idx += len(current_chunk_text)
                current_chunk_text = ""

        def process_segment(segment_text: str):
            nonlocal current_chunk_text
            if len(current_chunk_text) + len(segment_text) <= max_chunk_size:
                current_chunk_text += segment_text
                return
            seal_chunk()
            if len(segment_text) <= max_chunk_size:
                current_chunk_text = segment_text
            else:
                for line in segment_text.splitlines(keepends=True):
                    if len(current_chunk_text) + len(line) <= max_chunk_size:
                        current_chunk_text += line
                    else:
                        seal_chunk()
                        if len(line) > max_chunk_size:
                            for i in range(0, len(line), max_chunk_size):
                                current_chunk_text = line[i:i+max_chunk_size]
                                seal_chunk()
                        else:
                            current_chunk_text = line

        for node in tree.body:
            start_line_idx: int = last_processed_line
            end_line_idx: int | None = node.end_lineno
            if end_line_idx is None:
                end_line_idx = start_line_idx
            block_lines: str = lines[start_line_idx:end_line_idx]
            block_text: str = "".join(block_lines)
            process_segment(block_text)
            last_processed_line = end_line_idx

        remaining_text = "".join(lines[last_processed_line:])
        if remaining_text:
            process_segment(remaining_text)
        seal_chunk()
        return chunks
