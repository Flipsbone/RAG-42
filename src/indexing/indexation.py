from pathlib import Path

class Indexation:
    @staticmethod
    def load_file(data_dir: Path, max_chunk_size: int = 2000) -> None:
        """
            Traverse the directory, extract all file paths and then 
        """
        if not data_dir.exists():
            raise FileNotFoundError(f"{data_dir}")
        count_py: int = 0
        count_md: int = 0
        file_py: dict[Path, str] = {}
        file_md: dict[Path, str] = {}
        for file_path in data_dir.rglob("*"):
                extension = file_path.suffix
                match extension:
                    case ".py":
                        print(file_path)
                        file_py[file_path] = file_path.read_text()
                        count_py += 1
                    case ".md":
                        print(file_path)
                        file_md[file_path] = file_path.read_text()
                        count_md += 1
                    case _:
                        continue