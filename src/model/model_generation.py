from typing import Sequence
from src.model.model_retrivial import (
    MinimalSearchResults,
    StudentSearchResults)


class MinimalAnswer(MinimalSearchResults):
    """Search results augmented with a generated answer."""

    answer: str


class StudentSearchResultsAndAnswer(StudentSearchResults):
    """Search results collection containing generated answers."""

    search_results: Sequence[MinimalAnswer]
