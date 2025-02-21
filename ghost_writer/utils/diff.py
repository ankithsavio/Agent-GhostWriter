from pydantic import BaseModel


class Updates(BaseModel):
    short_summary: str
    content: str
    reason: str
    replacement: str


class DiffDocument:

    def __init__(self, doc: str):
        self.document = doc

    def apply(self, update: Updates):
        self.document = self.document.replace(update.content, update.replacement)
        return update.short_summary, update.reason

    def __call__(self):
        return self.document
