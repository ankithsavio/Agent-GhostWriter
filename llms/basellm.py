from openai import OpenAI
import google.generativeai as genai
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
        genai.configure(api_key=os.getenv("GEMINI_API_KEY", None))
        self.config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        self.model = genai.GenerativeModel("gemini-1.5-flash-002", generation_config= self.config)
        self.large_model = genai.GenerativeModel("gemini-exp-1206", generation_config= self.config) # needs testing

    def generate(self):
        raise NotImplementedError
