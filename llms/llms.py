from .basellm import HfBaseLLM, GeminiBaseLLM
from .prompts import GEN_PROMPT, EVAL_PROMPT, AI_CRITIC_PROMPT, GEMINI_GEN_PROMPT


class GenLLM(HfBaseLLM):
    def __init__(self, user_prompt_template):
        super().__init__(system_prompt=GEN_PROMPT)
        self.prompt_template = user_prompt_template


class OptimLLM(HfBaseLLM):
    def __init__(self, user_prompt_template):
        super().__init__(system_prompt=EVAL_PROMPT)
        self.prompt_template = user_prompt_template


class GeminiLLM(GeminiBaseLLM):
    def __init__(self, user_prompt_template):
        super().__init__(system_prompt=GEMINI_GEN_PROMPT)
        self.prompt_template = user_prompt_template
