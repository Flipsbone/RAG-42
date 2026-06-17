import uuid
from pydantic import BaseModel, Field
from src.model.model_indexing import MinimalSource


class MinimalSearchResults(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    question: str
    retrieved_sources: list[MinimalSource]


class StudentSearchResults(BaseModel):
    search_results: list[MinimalSearchResults]
    k: int
