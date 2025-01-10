# from openai import OpenAI

# client = OpenAI(
# 	base_url="https://api-inference.huggingface.co/v1/",
# 	api_key="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# )

# messages = [
# 	{
# 		"role": "user",
# 		"content": "What is the capital of France?"
# 	}
# ]

# completion = client.chat.completions.create(
#     model="meta-llama/Llama-3.3-70B-Instruct",
# 	messages=messages,
# 	max_tokens=500
# )

# print(completion.choices[0].message)

from openai import OpenAI
import google.generativeai as genai
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
            "temperature": kwargs['temperature'],
            "top_p": kwargs['top_p'],
            "max_completion_tokens": kwargs['max_token'], 
            "tools": kwargs['tools'] or None,
            "tool_choice": kwargs['tool_choice'] or None,
        }

        return self.client.chat.completions.create(**self.config)

class OptimLLM(HfBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=EVAL_PROMPT)

    def generate(self, model, messages, **kwargs):

        self.config = {
            "model": model,
            "messages": messages,
            "temperature": kwargs['temperature'],
            "top_p": kwargs['top_p'],
            "max_completion_tokens": kwargs['max_token'], 
            "tools": kwargs['tools'] or None,
            "tool_choice": kwargs['tool_choice'] or None,
        }

        return self.client.chat.completions.create(**self.config)


class AICriticLLM(HfBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=AI_CRITIC_PROMPT)

    def generate(self, model, messages, **kwargs):

        self.config = {
            "model": model,
            "messages": messages,
            "temperature": kwargs['temperature'],
            "top_p": kwargs['top_p'],
            "max_completion_tokens": kwargs['max_token'], 
            "tools": kwargs['tools'] or None,
            "tool_choice": kwargs['tool_choice'] or None,
        }

        return self.client.chat.completions.create(**self.config)


class GeminiLLM(GeminiBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=GEMINI_GEN_PROMPT)

    def generate(self, model, messages, **kwargs):

        self.config = {
            "model": model,
            "messages": messages,
            "temperature": kwargs['temperature'],
            "top_p": kwargs['top_p'],
            "max_completion_tokens": kwargs['max_token'], 
            "tools": kwargs['tools'] or None,
            "tool_choice": kwargs['tool_choice'] or None,
        }
        model = genai.GenerativeModel("gemini-1.5-flash")

        genai.GenerationConfig()

        return model.generate_content("Explain how AI works")


if __name__ == "__main__":
    GenLLM()
    OptimLLM()
    AICriticLLM()
    GeminiLLM()
