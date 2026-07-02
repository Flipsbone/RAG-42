import uuid
from typing import Sequence
from pydantic import BaseModel, Field
from src.model.model_indexing import ChunkSource, MinimalSource


class UnansweredQuestion(BaseModel):
    """A question without reference sources or answers."""

    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    """A labeled question with source references and an answer."""

    sources: list[MinimalSource]
    answer: str


class RagDataset(BaseModel):
    """Dataset containing answered and unanswered RAG questions."""

    rag_questions: list[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    """Search results for a single question."""

    question_id: str
    question_str: str
    retrieved_sources: list[ChunkSource]


class StudentSearchResults(BaseModel):
    """Collection of search results paired with the retrieval depth."""

    search_results: Sequence[MinimalSearchResults]
    k: int
