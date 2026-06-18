import bm25s
import re
import Stemmer
from src.exeptions import RetrieverError
from src.model.model_indexing import ChunkSource



class Retriever:
    def __init__(self, chunks: list[ChunkSource]):
        self.chunks: list[ChunkSource] = chunks
        self._stemmer = Stemmer.Stemmer("english")
        self.retriever = bm25s.BM25()

    def save_index(self) -> None:
        self.retriever.save("./data/processed/bm25_index")

    def load_index(self) -> None:
        try:
            self.retriever = bm25s.BM25.load("./data/processed/bm25_index")
        except RetrieverError as e:
            error = ("the file index not found. Have you made before :"
            "uv run python3 -m src index --max_chunk_size=2000 --target_dir=<your_file>")
            raise e

    def _format_text(self, text: str) -> str:
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = text.replace('_', ' ')
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

    def build_index(self) -> None:
        expanded_corpus: list[str] = (
            [self._format_text(
                chunk.context_name + chunk.text) for chunk in self.chunks])
        tokens_corpus = self._tokenizing(expanded_corpus)
        self.retriever.index(tokens_corpus)
