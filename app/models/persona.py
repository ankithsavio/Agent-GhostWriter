from pydantic import BaseModel
from typing import List


class Editor(BaseModel):
    persona: str
    short_summary: str
    description: str


class Personas(BaseModel):
    editors: List[Editor]
