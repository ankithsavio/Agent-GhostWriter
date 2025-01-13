from .utils.prompts import CONVO_SUMMARIZER_SYSTEM_PROMPT, CONVO_SUMMARIZER_PROMPT
from llms.basellm import GeminiBaseLLM


class ConvoSummarizer(GeminiBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=CONVO_SUMMARIZER_SYSTEM_PROMPT)

    def generate(self, model, messages, **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            "temperature": kwargs.pop("temperature", None),
            "top_p": kwargs.pop("top_p", None),
            "max_completion_tokens": kwargs.pop("max_token", None),
            "tools": kwargs.pop("tools", None),
            "tool_choice": kwargs.pop("tool_choice", None),
            **kwargs,
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, conversation):
        content = CONVO_SUMMARIZER_PROMPT.format(Conversation=conversation)
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": content},
        ]
        return self.generate(self.model, message)
