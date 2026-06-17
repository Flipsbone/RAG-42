from tqdm import tqdm
from pathlib import Path
from src.indexing.chunking import (
    ChunkerStrategy,
    PythonChunker,
    MarkdownChunker)
from src.model.model_indexing import ChunkSource


class Indexation:
    def __init__(self, data_dir: Path, max_chunk_size: int = 2000):
        self.data_dir = data_dir
        self.max_chunk_size = max_chunk_size
        self.chunkers: dict[str, ChunkerStrategy] = {
            ".py": PythonChunker(),
            ".md": MarkdownChunker()
        }
        self.target_files: list[Path] = []
        self._discover_files()

    def _discover_files(self) -> None:
        if not self.data_dir.exists():
            raise FileNotFoundError(f"{self.data_dir}")

        self.target_files: list[str] = [
            path for path in self.data_dir.rglob("*") if path.suffix in self.chunkers]

    def processed_chunks(self) -> list[ChunkSource]:

        all_processed_chunks: list[ChunkSource] = []

        for file_path in tqdm(
                self.target_files, desc="Ingesting and chunking repository"):

            text_content = file_path.read_text(encoding="utf-8")
            extension = file_path.suffix
            strategy = self.chunkers[extension]
            file_chunks = strategy.chunk(
                text_content, str(file_path), self.max_chunk_size)
            all_processed_chunks.extend(file_chunks)

        return(all_processed_chunks)
