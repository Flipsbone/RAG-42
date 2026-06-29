from typing import Sequence
from src.model.model_retrivial import (
    MinimalSearchResults,
    StudentSearchResults)
from dataclasses import dataclass


class MinimalAnswer(MinimalSearchResults):
    answer: str


class StudentSearchResultsAndAnswer(StudentSearchResults):
    search_results: Sequence[MinimalAnswer]


@dataclass
class EvalSource:
    file_path: str
    first_index: int
    last_index: int
