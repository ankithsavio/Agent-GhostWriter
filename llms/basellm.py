from openai import OpenAI
from google import genai
from google.genai import types
from dotenv import load_dotenv

import os

load_dotenv("./.env")


class HfBaseLLM:
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

    def generate(self):
        raise NotImplementedError


class GeminiBaseLLM:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.client = OpenAI(
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
            api_key=os.getenv("GEMINI_API_KEY", None),
        )
        self.model = "gemini-1.5-flash-002"
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

    def generate(self):
        raise NotImplementedError


class GeminiMultiModalBaseLLM:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", None))
        self.model = "gemini-1.5-flash-002"
        self.large_model = "gemini-exp-1206"
        self.config = {
            "temperature": None,
            "top_p": None,
            "top_k": None,
            "max_output_tokens": None,
            "response_mime_type": "text/plain",
        }

    def generate(self):
        raise NotImplementedError
