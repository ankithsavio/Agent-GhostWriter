from .basellm import GeminiMultiModalBaseLLM
from .prompts import GEMINI_MULTIMODAL_EXTRACTOR_PROMPT
from google import genai
from google.genai import types
import base64


class PDFExtractor(GeminiMultiModalBaseLLM):

    def __init__(self):
        super().__init__(system_prompt=GEMINI_MULTIMODAL_EXTRACTOR_PROMPT)

    def generate(self, model, file_part, **kwargs):
        self.config |= {
            "system_instruction": self.system_prompt,
            "temperature": kwargs.get("temperature", None),
            "top_p": kwargs.get("top_p", None),
            "top_k": kwargs.get("top_k", None),
            "max_output_tokens": kwargs.get("max_token", None),
        }

        return self.client.models.generate_content(
            model=model or self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[types.Part.from_text("Extract the pdf:"), file_part],
                )
            ],
            config=self.config,
        )

    def __call__(self, pdf_path):
        file = self.client.files.upload(path=pdf_path)
        file_part = types.Part.from_uri(
            file_uri=file.uri,
            mime_type="application/pdf",
        )

        return self.generate(self.model, file_part)
