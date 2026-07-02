from tqdm import tqdm
from pathlib import Path
from src.indexing.chunking import (
    ChunkerStrategy,
    PythonChunker,
    MarkdownChunker,
    TextChunker)
from src.model.model_indexing import ChunkSource
from src.retrieval.retriever import Retriever
from src.exceptions import IndexationError


class Indexation:
    """Discover supported files, chunk them, and build the retrieval index."""

    def __init__(self, data_dir: Path, max_chunk_size: int):
        """Initialize an indexation run.

        Args:
            data_dir: The root directory containing input files.
            max_chunk_size: The maximum size allowed for each chunk.
        """
        self.data_dir = data_dir
        self.max_chunk_size = max_chunk_size
        self.chunkers: dict[str, ChunkerStrategy] = {
            ".py": PythonChunker(),
            ".md": MarkdownChunker(),
            ".txt": TextChunker()
        }
        self.target_files: list[Path] = []
        self._discover_files()

    def _discover_files(self) -> None:
        if not self.data_dir.exists():
            raise FileNotFoundError(f"{self.data_dir}")

        self.target_files = [
            path for path in self.data_dir.rglob("*")
            if path.suffix in self.chunkers]

    def processed_chunks(self) -> None:
        """Chunk the discovered files and persist the resulting index.

        Returns:
            None.

        Raises:
            IndexationError: If one or more files fail during processing.
        """

        all_processed_chunks: list[ChunkSource] = []
        failed_logs: list[dict[str, str]] = []

        for file_path in tqdm(
                self.target_files, desc="Ingesting and chunking repository"):
            try:
                text_content = file_path.read_text(encoding="utf-8")
                extension = file_path.suffix
                strategy = self.chunkers[extension]
                file_chunks = strategy.chunk(
                    text_content, str(file_path), self.max_chunk_size)
                all_processed_chunks.extend(file_chunks)
            except Exception as e:
                failed_logs.append({"file": file_path.name, "error": str(e)})
                continue

        retriever = Retriever()
        retriever.build_index(all_processed_chunks)
        retriever.save_index()
        if failed_logs:
            raise IndexationError(failed_logs)
