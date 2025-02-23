from typing import List
from pydantic import BaseModel


class Editor(BaseModel):
    persona: str
    short_summary: str
    description: str


class Personas(BaseModel):
    editors: List[Editor]
