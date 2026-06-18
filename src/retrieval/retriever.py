import bm25s
from bm25s import BM25
import re
import Stemmer
from src.exeptions import RetrieverError
from src.model.model_indexing import ChunkSource


class Retriever:
    def __init__(self) -> None:
        self._stemmer = Stemmer.Stemmer("english")
        self.retriever = bm25s.BM25()
        self.chunk: list[ChunkSource] = []

    def save_index(self) -> None:
        self.retriever.save("./data/processed/bm25_index")

    def load_index(self) -> None:
        try:
            self.retriever = bm25s.BM25.load("./data/processed/bm25_index")
        except Exception as e:
            error_msg = ("the file index not found. Have you made before :"
            "uv run python3 -m src index --max_chunk_size=2000 --target_dir=<your_file> ?")
            raise RetrieverError(error_msg)

    def _format_text(self, text: str) -> str:
        #just remaind maybe here adjust important word to keep the corresspondance like vllm
        #and not v + llm you will loose your sementic 
        text = text.replace("vLLM", "VLLMPROTECTED")
        #Handle Acronyms (e.g., "HTTPResponse" -> "HTTP Response")
        text = re.sub(r'([a-z])([A-Z][a-z])', r'\1 \2', text)
        #Handle lowercase/Uppercase (e.g., "getHTTP" -> "get HTTP")
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

    def bulk_search(self, queries: list[str], k:int) -> list[ChunkSource]:
        format_queries: list[str] = (
        [self._format_text(query) for query in queries])
        queries_tokens = self._tokenizing(format_queries)
        docs_idx, scores = self.retriever.retrieve(queries_tokens, k=k)
        result = []
        for doc_idx in docs_idx:
            clean_id = int(doc_idx)
            actual_chunk = self.chunks[clean_id]
            result.append(actual_chunk)
            print(result)
        return result

    def search(self, query: str, k: int) -> list[ChunkSource]:
        return(self.bulk_search([query], k))
