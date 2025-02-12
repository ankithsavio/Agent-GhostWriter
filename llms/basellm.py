import openai
from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv
from typing import List, Dict
import os
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

load_dotenv("./.env")


class HfBaseLLM:
    """
    Base Huggingface Wrapper for Llama-3.3-70B-Instruct. Uses OpenAI Client using Huggingface inference base url.
    """

    def __init__(self, system_prompt=None):
        self.system_prompt = (
            system_prompt if system_prompt else "You are an helpful assistant"
        )
        self.prompt_template = ""
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
        }

    def generate(self, model: str, messages: List[Dict[str, str]], **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            **kwargs,
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, prompt, **kwargs):
        # prompt = self.prompt_template.format(**kwargs)
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self.generate(self.model, message).choices[0].message.content


class TogetherBaseLLM:
    """
    Base Huggingface Wrapper for Llama-3.3-70B-Instruct. Uses OpenAI Client using Huggingface inference base url.
    """

    def __init__(self, system_prompt=None):
        self.system_prompt = (
            system_prompt if system_prompt else "You are an helpful assistant"
        )
        self.prompt_template = ""
        self.client = OpenAI(
            base_url="https://api.together.xyz/v1",
            api_key=os.getenv("TOGETHER_API_KEY", None),
        )
        self.model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        self.config = {
            "model": self.model,
            "messages": None,
            "temperature": None,
            "top_p": None,
            "max_completion_tokens": None,
        }

    @retry(
        retry=retry_if_exception_type(openai.RateLimitError),
        wait=wait_random_exponential(min=5, max=60),
        stop=stop_after_attempt(10),
    )
    def generate(self, model: str, messages: List[Dict[str, str]], **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            **kwargs,
        }

        time.sleep(0.5)

        try:
            response = self.client.chat.completions.create(**self.config)
            return response
        except openai.RateLimitError as e:
            raise

    def __call__(self, prompt, **kwargs):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self.generate(self.model, message).choices[0].message.content


class GeminiBaseLLM:
    """
    Base Gemini Wrapper for gemini-1.5 flash and pro models. Uses OpenAI Client using gemini inference base url.
    """

    def __init__(self, system_prompt=None):
        self.system_prompt = (
            system_prompt if system_prompt else "You are an helpful assistant"
        )
        self.prompt_template = ""
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.getenv("GEMINI_API_KEY", None),
        )
        self.model = "gemini-2.0-flash-exp"
        self.large_model = "gemini-2.0-pro-exp-02-05"
        self.config = {
            "model": self.model,
            "messages": None,
            "temperature": None,
            "top_p": None,
            "max_completion_tokens": None,
        }

    def generate(self, model: str, messages: List[Dict[str, str]], **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            **kwargs,
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, prompt, **kwargs):
        # prompt = self.prompt_template.format(**kwargs)
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self.generate(self.model, message).choices[0].message.content


class GeminiMultiModalBaseLLM:
    """
    Base MultiModal Gemini Wrapper for Genai Pyton SDK. WIP.
    """

    def __init__(self, system_prompt=None):
        self.system_prompt = (
            system_prompt if system_prompt else "You are an helpful assistant"
        )
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


class EmbeddingModel:
    """
    Base Gemini Wrapper for text-embedding-004 model. Uses OpenAI Client using gemini inference base url.
    """

    def __init__(self):
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.getenv("GEMINI_API_KEY", None),
        )
        self.model = "text-embedding-004"
        self.config = {"model": self.model, "input": None}

    def generate(self, model: str, texts: List[Dict[str, str]], **kwargs):

        self.config |= {
            "model": model or self.model,
            "input": texts,
            **kwargs,
        }

        return self.client.embeddings.create(**self.config)

    def __call__(self, texts: List[str]):

        return [data.embedding for data in self.generate(self.model, texts).data]


class GeminiBaseStructuredLLM:
    """
    Base Gemini Wrapper for gemini-1.5 flash and pro models. Uses OpenAI Client using gemini inference base url.
    """

    def __init__(self, system_prompt=None):
        self.system_prompt = (
            system_prompt if system_prompt else "You are an helpful assistant"
        )
        self.prompt_template = ""
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
        }

    def generate(self, model: str, messages: List[Dict[str, str]], format, **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            "response_format": format,
            **kwargs,
        }

        return self.client.beta.chat.completions.parse(**self.config)

    def __call__(self, prompt, format, **kwargs):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self.generate(self.model, message, format).choices[0].message.parsed
