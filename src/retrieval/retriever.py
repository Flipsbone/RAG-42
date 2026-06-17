import bm25s
import re
import Stemmer
from src.model.model_indexing import ChunkSource


class Retriever:
    def __init__(self, chunks: list[ChunkSource]):
        self.chunks: list[ChunkSource] = chunks
        self._stemmer = Stemmer.Stemmer("english")
        self.retriever = bm25s.BM25()

    def save_index(self) -> None:
        self.retriever.save("./data/processed/bm25_index")

    def _format_text(self, text: str) -> str:
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        text = text.replace('_', ' ')
        return text

    def build_index(self) -> None:
        expanded_corpus: list[str] = (
            [self._format_text(
                chunk.context_name + chunk.text) for chunk in self.chunks])

        corpus_tokens = bm25s.tokenize(
            texts=expanded_corpus,
            lower=True,
            stopwords="en",
            stemmer=self._stemmer,
            return_ids=True,
            show_progress=True
        )
        self.retriever.index(corpus_tokens)
