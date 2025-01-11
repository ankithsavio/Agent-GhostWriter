from openai import OpenAI
from .basellm import HfBaseLLM, GeminiBaseLLM
from .prompts import *
import os


class GenLLM(HfBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=GEN_PROMPT)

    def generate(self, model, messages, **kwargs):

        self.config = {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", None),
            "top_p": kwargs.get("top_p", None),
            "max_completion_tokens": kwargs.get("max_token", None),
            "tools": kwargs.get("tools", None),
            "tool_choice": kwargs.get("tool_choice", None),
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, user_message):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self.generate(self.model, message)


class OptimLLM(HfBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=EVAL_PROMPT)

    def generate(self, model, messages, **kwargs):

        self.config |= {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", None),
            "top_p": kwargs.get("top_p", None),
            "max_completion_tokens": kwargs.get("max_token", None),
            "tools": kwargs.get("tools", None),
            "tool_choice": kwargs.get("tool_choice", None),
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, user_message):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self.generate(self.model, message)


class AICriticLLM(HfBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=AI_CRITIC_PROMPT)

    def generate(self, model, messages, **kwargs):

        self.config |= {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", None),
            "top_p": kwargs.get("top_p", None),
            "max_completion_tokens": kwargs.get("max_token", None),
            "tools": kwargs.get("tools", None),
            "tool_choice": kwargs.get("tool_choice", None),
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, user_message):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self.generate(self.model, message)


class GeminiLLM(GeminiBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=GEMINI_GEN_PROMPT)

    def generate(self, model, messages, **kwargs):

        self.config |= {
            "model": model,
            "messages": messages,
            "temperature": kwargs.get("temperature", None),
            "top_p": kwargs.get("top_p", None),
            "max_completion_tokens": kwargs.get("max_token", None),
            "tools": kwargs.get("tools", None),
            "tool_choice": kwargs.get("tool_choice", None),
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, user_message):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self.generate(self.model, message)


if __name__ == "__main__":
    GenLLM()
    OptimLLM()
    AICriticLLM()
    GeminiLLM()
