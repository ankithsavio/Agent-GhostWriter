from typing import List, Optional

import yaml

from llms.basellm import LLM

provider_config = yaml.safe_load(open("config/llms.yaml", "r"))


class Prompt:
    """
    A simple prompt template with in-built summarization and xml tag formatting.
    """

    def __init__(
        self,
        prompt: str,
        watch: Optional[List[str]] = None,
        token_limit: int = 4096,
        **kwargs,
    ):
        self.prompt = prompt
        self.llm = LLM(
            provider=provider_config["llm"]["provider"],
            model=provider_config["llm"]["model"],
        )
        self.dynamic_attr = {}
        self.summarize = watch or []
        self.token_limit = token_limit

        if kwargs:
            self.set_new_values(kwargs)

    def set_new_values(self, kwargs):
        if not isinstance(kwargs, dict):
            raise ValueError("Expected dict for kwargs")

        def format_value(value):
            if isinstance(value, str):
                return value
            elif isinstance(value, list):
                return "\n".join(str(item) for item in value)
            else:
                return str(value)

        for key, value in kwargs.items():
            formatted_value = f"<{key}>\n{format_value(value)}\n</{key}>"
            self.dynamic_attr[key] = formatted_value

    def _summarize(self, content):
        summary_prompt = f"Please summarize the following content concisely while preserving key information:\n{content}"
        return self.llm(summary_prompt)

    def __str__(self):
        prompt = self.prompt + "\n" + "\n".join(self.dynamic_attr.values())

        if not self.summarize or self._count_tokens(prompt) <= self.token_limit:
            return prompt

        attrs = self.dynamic_attr.copy()

        for key in self.summarize:
            original_content = attrs[key]
            content_start = original_content.find(f"<{key}>\n") + len(f"<{key}>\n")
            content_end = original_content.rfind(f"\n</{key}>")
            if content_start >= 0 and content_end >= 0:
                content = original_content[content_start:content_end]
                summary = self._summarize(content)
                attrs[key] = f"<{key}>\n{summary}\n</{key}>"

        return self.prompt + "\n" + "\n".join(attrs.values())

    def _count_tokens(self, text):
        return self.llm.count_tokens(text)

    def format(self, **kwargs):
        return Prompt(
            prompt=str(self).format(**kwargs),
            summarize=self.summarize,
            token_limit=self.token_limit,
        )
