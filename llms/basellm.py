from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import List, Dict
import os

load_dotenv("./.env")


class HfBaseLLM:
    """
    Base Huggingface Wrapper for Llama-3.3-70B-Instruct. Uses OpenAI Client using Huggingface inference base url.
    """

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.client = OpenAI(
            base_url="https://api-inference.huggingface.co/v1/",
            api_key=os.getenv("HF_TOKEN", None),
        )
        self.model = "meta-llama/Llama-3.3-70B-Instruct"
        self.config = {
            "model": self.model,
            "messages": None,
            "temperature": None,
            "top_p": None,
            "max_completion_tokens": None,
            "tools": None,
            "tool_choice": None,
        }

    def generate(self, model: str, messages: List[Dict[str, str]], **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            **kwargs,
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, **kwargs):
        prompt = self.prompt_template(**kwargs)
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self.generate(self.model, message).choices[0].message.content


class GeminiBaseLLM:
    """
    Base Gemini Wrapper for gemini-1.5 flash and pro models. Uses OpenAI Client using gemini inference base url.
    """

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.getenv("GEMINI_API_KEY", None),
        )
        self.model = "gemini-2.0-flash-exp"
        self.large_model = "gemini-1.5-pro"
        self.config = {
            "model": self.model,
            "messages": None,
            "temperature": None,
            "top_p": None,
            "max_completion_tokens": None,
            "tools": None,
            "tool_choice": None,
        }

    def generate(self, model: str, messages: List[Dict[str, str]], **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            **kwargs,
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, **kwargs):
        prompt = self.prompt_template(**kwargs)
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self.generate(self.model, message).choices[0].message.content


class GeminiMultiModalBaseLLM:
    """
    Base MultiModal Gemini Wrapper for Genai Pyton SDK. WIP.
    """

    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", None))
        self.model = "gemini-1.5-flash-002"
        self.large_model = "gemini-exp-1206"
        self.config = {
            "system_instruction": self.system_prompt,
            "temperature": None,
            "top_p": None,
            "top_k": None,
            "max_output_tokens": None,
            "response_mime_type": "text/plain",
        }

    def generate(self):
        raise NotImplementedError
