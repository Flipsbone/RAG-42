import bm25s
import hashlib
import Stemmer
from pathlib import Path
from pydantic import TypeAdapter
from src.exeptions import RetrieverError
from src.model.model_indexing import ChunkSource
from src.model.model_retrivial import (
    UnansweredQuestion,
    MinimalSearchResults,
    StudentSearchResults
)


class Retriever:
    def __init__(self) -> None:
        self._stemmer = Stemmer.Stemmer("english")
        self.retriever = bm25s.BM25()
        self.chunks: list[ChunkSource] = []

    def _verify_file_hash(self, target_file: Path) -> None:
        """Verifies if the current file hash matches the stored hash."""
        hash_path = target_file.with_suffix(target_file.suffix + ".hash")
        if not hash_path.exists():
            raise RetrieverError(
                f"Signature file missing for {target_file.name}")

        with open(hash_path, "r") as f:
            stored_hash = f.read().strip()

        if self._calculate_file_hash(target_file) != stored_hash:
            raise RetrieverError(
                f"Alert: {target_file.name} has been changed!")

    @staticmethod
    def _calculate_file_hash(file_path: Path) -> str:
        """Calculates SHA-256 hash."""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except OSError as e:
            raise RetrieverError(
                f"Could not read file for hashing: {file_path}") from e

    def _save_hash_file(self, target_file: Path) -> None:
        """Generates a .hash file next to the target file."""
        hash_path = target_file.with_suffix(target_file.suffix + ".hash")
        file_hash = self._calculate_file_hash(target_file)
        try:
            with open(hash_path, "w") as f:
                f.write(file_hash)
        except OSError as e:
            raise RetrieverError(
                f"Could not save hash for {target_file.name}") from e

    def save_index(self) -> None:
        try:
            index_dir = Path("./data/processed/bm25_index")
            index_dir.mkdir(parents=True, exist_ok=True)
            self.retriever.save(str(index_dir))
            for file in index_dir.iterdir():
                if file.is_file():
                    self._save_hash_file(file)

            chunks_dir = Path("./data/processed/chunks")
            chunks_dir.mkdir(parents=True, exist_ok=True)
            adapter = TypeAdapter(list[ChunkSource])
            json_data = adapter.dump_json(self.chunks, indent=4)
            chunk_mapping_path = chunks_dir / "chunk_mapping.json"

            with open(chunks_dir / "chunk_mapping.json", "wb") as f:
                f.write(json_data)
            self._save_hash_file(chunk_mapping_path)

        except OSError as e:
            error_msg = f"the file could not be save {str(e)}"
            raise RetrieverError(error_msg) from e

    def load_index(self) -> None:
        index_dir: Path = Path("./data/processed/bm25_index")
        chunks_dir: Path = Path("./data/processed/chunks")
        chunk_mapping_path: Path = chunks_dir / "chunk_mapping.json"

        if not index_dir.exists():
            raise RetrieverError(
                "Index directory does not exist. Please run indexing first.")
        for file in index_dir.iterdir():
            if file.is_file() and not file.name.endswith(".hash"):
                self._verify_file_hash(file)
        if not chunk_mapping_path.exists():
            raise RetrieverError(
                f"Chunk mapping file not found at {chunk_mapping_path}")

        self._verify_file_hash(chunk_mapping_path)

        try:
            self.retriever = bm25s.BM25.load(str(index_dir))
            with open(chunk_mapping_path, "r", encoding="utf-8") as f:
                raw_data = f.read()
            self.chunks = (
                TypeAdapter(list[ChunkSource]).validate_json(raw_data))

        except Exception as e:
            raise RetrieverError(
                f"Failed to load index or chunks: {str(e)}") from e

    def _tokenizing(self, text_data: list[str]) -> list[str] | list[int]:
        text_data = bm25s.tokenize(
            texts=text_data,
            lower=True,
            stopwords="en",
            stemmer=self._stemmer,
            return_ids=True,
            show_progress=True
        )
        return text_data

    def build_index(
            self,
            chunks: list[ChunkSource]) -> None:

        self.chunks = chunks
        expanded_corpus: list[str] = []
        for chunk in chunks:
            expanded_corpus.append(
                (chunk.context_name) + (chunk.file_path) + (chunk.text))
        tokens_corpus = self._tokenizing(expanded_corpus)
        self.retriever.index(tokens_corpus)

    def save_dataset(
            self,
            nb_queries: int,
            dataset_file: Path,
            save_file: Path,
            search_results: StudentSearchResults) -> None:

        print(f"Executing bulk search for {nb_queries} queries...")
        file_name: str = dataset_file.name
        output_path = save_file / file_name
        try:
            with open(output_path, "w") as out_file:
                out_file.write(search_results.model_dump_json(indent=4))
            self._save_hash_file(output_path)
            print(f"Dataset search complete. Results saved to {output_path}")
        except OSError as e:
            raise RetrieverError(
                f"Dataset at {out_file} could not save.") from e

    def bulk_search(
            self,
            queries: list[UnansweredQuestion],
            k: int) -> StudentSearchResults:

        if k < 1:
            raise RetrieverError("k must be > 0")
        questions: list[str] = []
        for query in queries:
            questions.append(query.question)

        queries_tokens = self._tokenizing(questions)
        docs_idx, scores = self.retriever.retrieve(queries_tokens, k=k)

        all_results: list[MinimalSearchResults] = []
        for query, query_indices in zip(queries, docs_idx):
            query_chunks: list[ChunkSource] = []
            for doc_idx in query_indices:
                clean_id = int(doc_idx)
                actual_chunk = self.chunks[clean_id]
                query_chunks.append(actual_chunk)
            search_result = MinimalSearchResults(
                question_id=query.question_id,
                question_str=query.question,
                retrieved_sources=query_chunks
            )
            all_results.append(search_result)
        search_results: StudentSearchResults = StudentSearchResults(
            search_results=all_results,
            k=k
        )

        return search_results
