from pydantic import BaseModel
from dataclasses import dataclass
import ast


class MinimalSource(BaseModel):
    """Minimal source metadata shared across retrieval outputs."""

    file_path: str
    first_character_index: int
    last_character_index: int


class ChunkSource(MinimalSource):
    """A chunk of source text with context and content."""

    context_name: str
    text: str


@dataclass
class NodeContext:
    """Pair an AST node with the owning class name when applicable."""

    node: ast.stmt
    class_name: str | None = None
