from typing import Sequence
from src.model.model_retrivial import (
    MinimalSearchResults,
    StudentSearchResults)
from dataclasses import dataclass


class MinimalAnswer(MinimalSearchResults):
    """Search results augmented with a generated answer."""

    answer: str


class StudentSearchResultsAndAnswer(StudentSearchResults):
    """Search results collection containing generated answers."""

    search_results: Sequence[MinimalAnswer]


@dataclass
class EvalSource:
    """Source interval used by evaluation scoring."""

    file_path: str
    first_index: int
    last_index: int
