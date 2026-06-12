from pathlib import Path
from src.indexing.indexation import Indexation

class RagCLI:
    """A Command Line Interface for managing the RAG document index."""
    def index(self, target_dir: str = "vllm-0.10.1", max_chunk_size: int = 2000)-> None:
        """
        Indexes documents found in the target directory.

        Args:
            target_dir: The folder path containing the raw documents.
            max_chunk_size: The maximum character limit for each text chunk.
        """
        path = Path(target_dir)
        Indexation.load_file(path, max_chunk_size)
