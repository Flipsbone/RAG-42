import bm25s
import re
import Stemmer
from pathlib import Path
from pydantic import TypeAdapter
from src.exeptions import RetrieverError
from src.model.model_indexing import ChunkSource


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
        except Exception as e:
            error_msg = f"the file can't be save {str(e)}"
            raise RetrieverError(error_msg)

    def load_index(self) -> None:
        try:
            self.retriever = bm25s.BM25.load("./data/processed/bm25_index")
        except Exception:
            error_msg = ("The BM25 index could not be loaded. "
                         "Do you have run indexing command before searching: "
                         "uv run python3 -m src index --max_chunk_size=2000")
            raise RetrieverError(error_msg)

        chunks_path = Path("./data/processed/chunks/chunk_mapping.json")
        try:
            adapter = TypeAdapter(list[ChunkSource])
            with open(chunks_path, "rb") as f:
                self.chunks = adapter.validate_json(f.read())
        except FileNotFoundError:
            error_msg = (f"The chunk mapping file not found at {chunks_path}. "
                         "Please run the indexing process again.")
            raise RetrieverError(error_msg)
        except Exception as e:
            error_msg = (f"Failed chunk mapping JSON: {str(e)}")
            raise RetrieverError(error_msg) from e

    def _format_text(self, text: str) -> str:
        # just remaind maybe here adjust important word to keep the corresspondance like vllm
        # and not v + llm you will loose your sementic
        text = text.replace("vLLM", "VLLMPROTECTED")
        # Handle Acronyms (e.g., "HTTPResponse" -> "HTTP Response")
        text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)
        # Handle lowercase/Uppercase (e.g., "getHTTP" -> "get HTTP")
        text = re.sub(r'([a-z\d])([A-Z])', r'\1 \2', text)
        text = text.replace('_', ' ')
        text = text.replace("VLLMPROTECTED", "vllm")
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

    def build_index(self, chunks: list[ChunkSource]) -> None:
        self.chunks = chunks
        expanded_corpus: list[str] = (
            [self._format_text(
                chunk.context_name + chunk.text) for chunk in chunks])
        tokens_corpus = self._tokenizing(expanded_corpus)
        self.retriever.index(tokens_corpus)

    def bulk_search(self,
                    queries: list[str],
                    k: int) -> list[list[ChunkSource]]:

        format_queries: list[str] = (
            [self._format_text(query) for query in queries])
        queries_tokens = self._tokenizing(format_queries)
        docs_idx, scores = self.retriever.retrieve(queries_tokens, k=k)

        all_results: list[list[ChunkSource]] = []
        for query_indices in docs_idx:
            query_chunks: list[ChunkSource] = []
            for doc_idx in query_indices:
                clean_id = int(doc_idx)
                actual_chunk = self.chunks[clean_id]
                query_chunks.append(actual_chunk)
            all_results.append(query_chunks)

        return all_results

    def search(self, query: str, k: int) -> list[ChunkSource]:
        return (self.bulk_search([query], k))[0]
