import openai as oai
from dotenv import load_dotenv
from typing import List, Dict
import os
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
    retry_if_exception_type,
)

# from langfuse.openai import openai
# from langfuse.decorators import observe
from transformers import AutoTokenizer

load_dotenv(".env")


class BaseLLM:
    def __init__(self, provider: str, system_prompt=None):
        self.system_prompt = (
            system_prompt if system_prompt else "You are an helpful assistant"
        )

        if provider == "huggingface":
            base_url = "https://api-inference.huggingface.co/v1/"
            api_key = os.getenv("HF_TOKEN", None)
            self.default_model = "meta-llama/Llama-3.3-70B-Instruct"
        elif provider == "togetherai":
            base_url = "https://api.together.xyz/v1"
            api_key = os.getenv("TOGETHER_API_KEY", None)
            self.default_model = "meta-llama/Llama-3.3-70B-Instruct-Turbo-Free"
        elif provider == "ollama":
            base_url = "http://localhost:11434/v1"
            api_key = "ollama"
            self.default_model = None
        elif provider == "openai":
            base_url = None
            api_key = os.getenv("OPENAI_API_KEY", None)
            self.default_model = "gpt-4o-mini-2024-07-18"
        elif provider == "google":
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            api_key = os.getenv("GEMINI_API_KEY", None)
            self.default_model = "gemini-2.0-flash"

        self.client = oai.OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Llama-3.3-70B-Instruct"
        )

    def count_tokens(self, content):
        token_count = len(self.tokenizer.encode(content))
        return token_count


class LLM(BaseLLM):
    """
    Base Huggingface Wrapper for Llama-3.3-70B-Instruct. Uses OpenAI Client using Huggingface inference base url.
    """

    def __init__(self, provider: str, system_prompt=None, model=None):
        super().__init__(provider, system_prompt)

        self.model = model if model else self.default_model
        self.config = {
            "model": self.model,
            "messages": None,
            "temperature": None,
            "top_p": None,
            "max_completion_tokens": None,
        }

    # @observe(name="LLM_Generate")
    @retry(
        retry=retry_if_exception_type((oai.RateLimitError, oai.InternalServerError)),
        wait=wait_random_exponential(min=5, max=60),
        stop=stop_after_attempt(10),
    )
    def generate(self, model: str, messages: List[Dict[str, str]], **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            **kwargs,
        }

        try:
            response = self.client.chat.completions.create(**self.config)
            return response
        except oai.RateLimitError as e:
            raise
        except oai.InternalServerError as e:
            raise

    def __call__(self, prompt, **kwargs):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return self.generate(self.model, message).choices[0].message.content


class StructLLM(BaseLLM):
    """
    Base Gemini Wrapper for gemini-2.0 flash and pro models. Uses OpenAI Client using gemini inference base url.
    """

    def __init__(self, provider: str, system_prompt=None, model=None):
        super().__init__(provider, system_prompt)

        self.model = model if model else self.default_model
        self.config = {
            "model": self.model,
            "messages": None,
            "temperature": 0,
            "top_p": None,
            "max_completion_tokens": None,
        }

    # @observe(name="Struct_Generate")
    @retry(
        retry=retry_if_exception_type((oai.RateLimitError, oai.InternalServerError)),
        wait=wait_random_exponential(min=5, max=60),
        stop=stop_after_attempt(10),
    )
    def generate(self, model: str, messages: List[Dict[str, str]], format, **kwargs):

        self.config |= {
            "model": model or self.model,
            "messages": messages,
            "response_format": format,
            **kwargs,
        }

        try:
            response = self.client.beta.chat.completions.parse(**self.config)
            return response
        except oai.RateLimitError as e:
            raise
        except oai.InternalServerError as e:
            raise

    def __call__(self, prompt, format, **kwargs):
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        return (
            self.generate(self.model, message, format, **kwargs)
            .choices[0]
            .message.parsed
        )


class EmbeddingModel:
    """
    Base Gemini Wrapper for text-embedding-004 model. Uses OpenAI Client using gemini inference base url.
    """

    def __init__(self):
        self.client = oai.OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.getenv("GEMINI_API_KEY", None),
        )
        self.model = "text-embedding-004"
        self.config = {"model": self.model, "input": None}

    # @observe(name="Embedding_Generate")
    @retry(
        retry=retry_if_exception_type((oai.RateLimitError, oai.InternalServerError)),
        wait=wait_random_exponential(min=5, max=60),
        stop=stop_after_attempt(10),
    )
    def generate(self, model: str, texts: List[Dict[str, str]], **kwargs):

        self.config |= {
            "model": model or self.model,
            "input": texts,
            **kwargs,
        }

        try:
            response = self.client.embeddings.create(**self.config)
            return response
        except oai.RateLimitError as e:
            raise
        except oai.InternalServerError as e:
            raise

    def __call__(self, texts: List[str]):

        return [data.embedding for data in self.generate(self.model, texts).data]
