from typing import Sequence
from src.model.model_retrivial import (
    MinimalSearchResults,
    StudentSearchResults)


class MinimalAnswer(MinimalSearchResults):
    answer: str


class StudentSearchResultsAndAnswer(StudentSearchResults):
    search_results: Sequence[MinimalAnswer]
