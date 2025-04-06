import os
from typing import Any, Dict, List, Type, TypeVar, Union

import openai as oai
import yaml
from dotenv import load_dotenv
from openai.types import CreateEmbeddingResponse
from openai.types.chat import ChatCompletion, ParsedChatCompletion
from pydantic import BaseModel
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random_exponential,
)
from transformers import AutoTokenizer

load_dotenv(".env")

provider_config = yaml.safe_load(open("config/llms.yaml", "r"))

T = TypeVar("T", bound=BaseModel)


class BaseLLM:
    def __init__(self, provider: str, system_prompt: Union[str, None] = None):
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
            self.default_model = provider_config["ollama"]["model"]
        elif provider == "openai":
            base_url = None
            api_key = os.getenv("OPENAI_API_KEY", None)
            self.default_model = "gpt-4o-mini-2024-07-18"
        elif provider == "google":
            base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            api_key = os.getenv("GEMINI_API_KEY", None)
            self.default_model = "gemini-2.0-flash"
        elif provider == "openrouter":
            base_url = "https://openrouter.ai/api/v1"
            api_key = os.getenv("OPENROUTER_API_KEY", None)
            self.default_model = "meta-llama/llama-3.3-70b-instruct:free"
        elif provider == "cloudfare":
            account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", None)
            api_key = os.getenv("CLOUDFLARE_AUTH_TOKEN", None)
            base_url = (
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1"
            )
            self.default_model = "@cf/meta/llama-4-scout-17b-16e-instruct"
        else:
            raise ValueError(f"Unsupported provider: {provider}")

        self.client = oai.OpenAI(
            base_url=base_url,
            api_key=api_key,
        )

        self.tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-32B-Instruct")

    def count_tokens(self, content: str) -> int:
        token_count = len(self.tokenizer.encode(content))
        return token_count


class LLM(BaseLLM):
    """
    Base Huggingface Wrapper for Llama-3.3-70B-Instruct. Uses OpenAI Client using Huggingface inference base url.
    """

    def __init__(
        self,
        provider: str,
        system_prompt: Union[str, None] = None,
        model: Union[str, None] = None,
    ):
        super().__init__(provider, system_prompt)

        self.model: str = model if model else self.default_model
        self.config: Dict[str, Any] = {
            "model": self.model,
            "messages": None,
        }

    @retry(
        retry=retry_if_exception_type((oai.RateLimitError, oai.InternalServerError)),
        wait=wait_random_exponential(min=5, max=60),
        stop=stop_after_attempt(10),
    )
    def generate(
        self, model: str, messages: List[Dict[str, str]], **kwargs: Dict[str, Any]
    ) -> ChatCompletion:
        self.config |= {
            "model": model or self.model,
            "messages": messages,
            **kwargs,
        }
        print("iteration")
        try:
            response = self.client.chat.completions.create(stream=False, **self.config)
            return response
        except oai.RateLimitError:
            print("Rate limit trying again")
            raise
        except oai.InternalServerError:
            print("Internal server error trying again")
            raise

    def __call__(self, prompt: str, **kwargs: Dict[str, Any]) -> str:
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]

        response = (
            self.generate(self.model, message, **kwargs).choices[0].message.content
        )

        if not isinstance(response, str):
            raise TypeError()
        else:
            return response


class StructLLM(BaseLLM):
    """
    Base Gemini Wrapper for gemini-2.0 flash and pro models. Uses OpenAI Client using gemini inference base url.
    """

    def __init__(
        self,
        provider: str,
        system_prompt: Union[str, None] = None,
        model: Union[str, None] = None,
    ):
        super().__init__(provider, system_prompt)

        self.model = model if model else self.default_model
        self.config: Dict[str, Any] = {
            "model": self.model,
            "messages": None,
            "temperature": 0,
        }

    @retry(
        retry=retry_if_exception_type((oai.RateLimitError, oai.InternalServerError)),
        wait=wait_random_exponential(min=5, max=60),
        stop=stop_after_attempt(10),
    )
    def generate(
        self,
        model: str,
        messages: List[Dict[str, str]],
        format: Type[T],
        **kwargs: Dict[str, Any],
    ) -> ParsedChatCompletion[T]:
        self.config |= {
            "model": model or self.model,
            "messages": messages,
            "response_format": format,
            **kwargs,
        }

        try:
            response = self.client.beta.chat.completions.parse(**self.config)
            return response
        except oai.RateLimitError:
            raise
        except oai.InternalServerError:
            raise

    def __call__(self, prompt: str, format: Type[T], **kwargs: Dict[str, Any]) -> T:
        message = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": prompt},
        ]
        response = (
            self.generate(self.model, message, format, **kwargs)
            .choices[0]
            .message.parsed
        )

        if not isinstance(response, format):
            raise TypeError()

        return response


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
        self.config: Dict[str, Any] = {
            "model": self.model,
            "input": None,
        }

    @retry(
        retry=retry_if_exception_type((oai.RateLimitError, oai.InternalServerError)),
        wait=wait_random_exponential(min=5, max=60),
        stop=stop_after_attempt(10),
    )
    def generate(
        self, model: str, texts: Union[str, List[str]], **kwargs: Dict[str, Any]
    ) -> CreateEmbeddingResponse:
        self.config |= {
            "model": model or self.model,
            "input": texts,
            **kwargs,
        }

        try:
            response = self.client.embeddings.create(**self.config)
            return response
        except oai.RateLimitError:
            raise
        except oai.InternalServerError:
            raise

    def __call__(self, texts: Union[str, List[str]]):
        return [data.embedding for data in self.generate(self.model, texts).data]
