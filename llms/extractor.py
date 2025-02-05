from .basellm import GeminiMultiModalBaseLLM
from .prompts import GEMINI_MULTIMODAL_EXTRACTOR_PROMPT
from google import genai
from google.genai import types
import base64


class PDFExtractor(GeminiMultiModalBaseLLM):

    def __init__(self):
        super().__init__(system_prompt=GEMINI_MULTIMODAL_EXTRACTOR_PROMPT)

    def generate(self, model, prompt, file_part, format, **kwargs):
        self.config |= {
            "response_mime_type": "application/json",
            "response_schema": format,
            **kwargs,
        }

        return self.client.models.generate_content(
            model=model or self.model,
            contents=[
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                        file_part,
                    ],
                )
            ],
            config=self.config,
        )

    def __call__(self, prompt, pdf_path, format):
        file = self.client.files.upload(path=pdf_path)
        file_part = types.Part.from_uri(
            file_uri=file.uri,
            mime_type="application/pdf",
        )

        return (
            self.generate(self.model, prompt, file_part, format)
            .candidates[0]
            .content.parts[0]
            .text
        )
