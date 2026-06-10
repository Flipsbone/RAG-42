import fire
import sys
from pathlib import Path
from indexing.indexation import Indexation

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

def main()-> int:
    try:
        fire.Fire(RagCLI)
    except PermissionError as e:
        print(f"Permission Error: {e}", file=sys.stderr)
        return 1
    except FileNotFoundError as e:
        print(f"Error: File '{e}' not found.", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    main()
