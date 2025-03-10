from pydantic import BaseModel
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer


class Updates(BaseModel):
    content: str
    reason: str
    replacement: str


class DiffDocument:

    def __init__(self, doc: str, anonymizer: PresidioReversibleAnonymizer = None):
        self.document = doc
        self.anonymizer = anonymizer
        self.update_history = []

    def apply(self, update: Updates):
        self.document = self.document.replace(update.content, update.replacement)
        self.update_history.append(update.replacement)

    def __call__(self, deanonymize: bool = False):
        if deanonymize and self.anonymizer:
            return self.anonymizer.deanonymize(self.document)
        else:
            return self.document
