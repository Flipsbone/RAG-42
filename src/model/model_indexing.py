from pydantic import BaseModel
from dataclasses import dataclass
import ast

class MinimalSource(BaseModel):
    file_path: str
    first_character_index: int
    last_character_index: int


class ChunkSource(MinimalSource):
    context_name: str
    text: str


@dataclass
class NodeContext:
    node: ast.stmt
    class_name: str | None = None