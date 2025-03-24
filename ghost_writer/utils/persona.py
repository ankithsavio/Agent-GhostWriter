from typing import List

from pydantic import BaseModel


class Editor(BaseModel):
    persona: str
    role_name: str
    description: str


class Personas(BaseModel):
    editors: List[Editor]
