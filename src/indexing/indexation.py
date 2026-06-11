from tqdm import tqdm
from pathlib import Path
from src.indexing.chunking import ChunkerStrategy, PythonChunker, MarkdownChunker
from src.indexing.model_indexation import MinimalSource

class Indexation:
    @staticmethod
    def load_file(data_dir: Path, max_chunk_size: int = 2000) -> None:
        """
            Traverse the directory, extract all file paths and then 
        """
        if not data_dir.exists():
            raise FileNotFoundError(f"{data_dir}")

        chunkers: dict[str, ChunkerStrategy] = {
            ".py": PythonChunker(),
            ".md": MarkdownChunker()
        }

        all_processed_chunks: list[MinimalSource] = []
        target_files = [path for path in data_dir.rglob("*") if path.suffix in chunkers]
        for file_path in tqdm(target_files, desc="Ingesting and chunking repository"):
            text_content = file_path.read_text(encoding="utf-8")
            extension = file_path.suffix
            strategy = chunkers[extension]
            file_chunks = strategy.chunk(text_content, str(file_path), max_chunk_size)
            all_processed_chunks.extend(file_chunks)
        print(all_processed_chunks)