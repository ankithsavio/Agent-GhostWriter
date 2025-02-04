from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class BasePrompt(BaseModel):
    prompt: str
    model_config = ConfigDict(extra="forbid")


class Prompt(BasePrompt):
    example: Optional[List[str]] = None

    def __str__(self):
        if self.example:
            examples = "\n".join(f"{i+1}:{item}" for i, item in enumerate(self.example))
            return f"{self.prompt}\n<Examples>\n{examples}\n</Examples>"
        else:
            return self.prompt

    def __radd__(self, left):
        if isinstance(left, str):
            return left + str(self)
        return NotImplemented
