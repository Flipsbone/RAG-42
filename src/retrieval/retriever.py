import bm25s
import re
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

    def save_index(self) -> None:
        try:
            self.retriever.save("./data/processed/bm25_index")
            chunks_dir = Path("./data/processed/chunks")
            chunks_dir.mkdir(parents=True, exist_ok=True)
            adapter = TypeAdapter(list[ChunkSource])
            json_data = adapter.dump_json(self.chunks)
            with open(chunks_dir / "chunk_mapping.json", "wb") as f:
                f.write(json_data)
        except OSError as e:
            error_msg = f"the file could not be save {str(e)}"
            raise RetrieverError(error_msg) from e

    def load_index(self) -> None:
        try:
            self.retriever = bm25s.BM25.load("./data/processed/bm25_index")
        except OSError as e:
            raise RetrieverError(
                "The BM25 index could not be loaded. "
                "Did you run: uv run python3 -m src index "
                "--max_chunk_size=2000"
            ) from e

        chunks_path = Path("./data/processed/chunks/chunk_mapping.json")
        try:
            with open(chunks_path, "r") as file:
                raw_data = file.read()
            self.chunks = (
                TypeAdapter(list[ChunkSource]).validate_json(raw_data))
        except OSError as e:
            raise RetrieverError(
                f"The chunk mapping file could not be read at {chunks_path}. "
                "Please run the indexing process again."
            ) from e
        except ValueError as e:
            raise RetrieverError(
                f"Failed to parse chunk mapping JSON: {e}") from e

    def _format_text(self, text: str) -> str:
        # # just remaind maybe here adjust important word to keep the corresspondance like vllm
        # # and not v + llm you will loose your sementic
        # text = text.replace("vLLM", "VLLMPROTECTED")
        # # text_with_spaces = text.replace('_', ' ')
        # # text = text + " " + text_with_spaces
        # # Handle Acronyms (e.g., "HTTPResponse" -> "HTTP Response")
        # text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)
        # # Handle lowercase/Uppercase (e.g., "getHTTP" -> "get HTTP")
        # text = re.sub(r'([a-z\d])([A-Z])', r'\1 \2', text)
        # text = text.replace("VLLMPROTECTED", "vllm")
        return text

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
            chunks: list[ChunkSource],
            max_chunk_size: int) -> None:

        self.chunks = chunks
        expanded_corpus: list[str] = []
        for chunk in chunks:
            expanded_corpus.append(chunk.text)
        tokens_corpus = self._tokenizing(expanded_corpus)
        self.retriever.index(tokens_corpus)

    def bulk_search(self,
                    queries: list[UnansweredQuestion],
                    k: int) -> StudentSearchResults:
        if k < 1:
            raise RetrieverError("k must be > 0")

        format_queries: list[str] = (
            [self._format_text(query.question) for query in queries])
        queries_tokens = self._tokenizing(format_queries)
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
