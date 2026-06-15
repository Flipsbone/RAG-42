import ast
from langchain_text_splitters import Language, RecursiveCharacterTextSplitter
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
        
        markdown_splitter = RecursiveCharacterTextSplitter.from_language(
            language=Language.MARKDOWN,
            chunk_size=max_chunk_size,
            chunk_overlap=0,
        )

        langchain_chunks = markdown_splitter.create_documents([text])
        
        chunks: list[ChunkSource] = []
        current_start_idx = 0
        
        for doc in langchain_chunks:
            chunk_text = doc.page_content
            chunks.append(
                ChunkSource(
                    file_path=file_path,
                    first_character_index=current_start_idx,
                    last_character_index=current_start_idx + len(chunk_text),
                    text=chunk_text
                )
            )
            current_start_idx += len(chunk_text)

        return chunks


class PythonChunker:
    def chunk(self,
              text: str,
              file_path: str,
              max_chunk_size: int) -> list[ChunkSource]:

        chunks: list[ChunkSource] = []
        tree: ast.Module = ast.parse(text)

        lines: list[str] = text.splitlines(keepends=True)

        current_chunk_text: str = ""
        current_start_char_idx: int = 0
        last_line_idx: int = 0

        def seal_chunk() -> None:
            nonlocal current_chunk_text, current_start_char_idx
            if not current_chunk_text:
                return
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

        def process_trailing_code(final_line_idx: int) -> None:
            remaining_text = "".join(lines[final_line_idx:])
            if remaining_text:
                process_segment(remaining_text, context_name="trailing code")
            seal_chunk()

        def process_lines(block_text: str, context_name: str) -> None:
            nonlocal current_chunk_text
            
            header = f"# [Continued: {context_name}]\n" if context_name else ""

            for line in block_text.splitlines(keepends=True):
                if len(line) + len(current_chunk_text) > max_chunk_size and current_chunk_text:
                    seal_chunk()
                    current_chunk_text = header
                    header = ""

                while len(line) > 0:
                    space_left = max_chunk_size - len(current_chunk_text)
                    current_chunk_text += line[:space_left]
                    line = line[space_left:]

                    if len(current_chunk_text) == max_chunk_size:
                        seal_chunk()
                        current_chunk_text = header
                        header = ""

        def process_segment(block_text: str, context_name: str) -> None:
            nonlocal current_chunk_text

            if len(current_chunk_text) + len(block_text) < max_chunk_size:
                current_chunk_text += block_text
                return

            seal_chunk()

            if len(block_text) < max_chunk_size:
                current_chunk_text += block_text
                return

            process_lines(block_text, context_name)

        for node in tree.body:
            start_line_idx: int = last_line_idx
            end_line_idx: int | None = node.end_lineno 
            if end_line_idx is None:
                end_line_idx = start_line_idx
            block_lines: list[str] = lines[start_line_idx:end_line_idx]
            block_text: str = "".join(block_lines)
            node_name = getattr(node, "name", "module level")
            process_segment(block_text, node_name)
            last_line_idx = end_line_idx

        process_trailing_code(last_line_idx)

        return chunks
