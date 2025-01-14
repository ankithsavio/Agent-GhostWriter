from llms.basellm import HfBaseLLM, GeminiBaseLLM
from .utils.prompts import (
    JOB_EXTRACTOR_PROMPT,
    JOB_EXTRACTOR_USER_PROMPT,
    CONVO_SUMMARIZER_SYSTEM_PROMPT,
    CONVO_SUMMARIZER_PROMPT,
    COVER_LETTER_DRAFT_GEN_SYSTEM_PROMPT,
    COVER_LETTER_DRAFT_GEN_PROMPT,
)


class JobExtractorWorker(HfBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=JOB_EXTRACTOR_PROMPT)
        self.prompt_template = JOB_EXTRACTOR_USER_PROMPT


class ConvoSummarizerWorker(GeminiBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=CONVO_SUMMARIZER_SYSTEM_PROMPT)
        self.prompt_template = CONVO_SUMMARIZER_PROMPT


class DraftWriterWorker(GeminiBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=COVER_LETTER_DRAFT_GEN_SYSTEM_PROMPT)
        self.prompt_template = COVER_LETTER_DRAFT_GEN_PROMPT