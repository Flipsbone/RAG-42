import uuid
from typing import Sequence
from pydantic import BaseModel, Field
from src.model.model_indexing import ChunkSource


class UnansweredQuestion(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str


class AnsweredQuestion(UnansweredQuestion):
    sources: list[ChunkSource]
    answer: str


class RagDataset(BaseModel):
    rag_questions: list[AnsweredQuestion | UnansweredQuestion]


class MinimalSearchResults(BaseModel):
    question_id: str
    question_str: str
    retrieved_sources: list[ChunkSource]


class StudentSearchResults(BaseModel):
    search_results: Sequence[MinimalSearchResults]
    k: int
