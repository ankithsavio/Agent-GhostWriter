import base64
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv("Agent-GhostWriter/.env")
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel("gemini-1.5-flash")
doc_path = "/mnt/c/Users/ankit/Desktop/Portfolio/automation/Agent-GhostWriter/pdf/Resume.pdf"  # Replace with the actual path to your local PDF

# Read and encode the local file
with open(doc_path, "rb") as doc_file:
    doc_data = base64.standard_b64encode(doc_file.read()).decode("utf-8")

prompt = """
You are an AI assistant tasked with converting the contents of PDF files into clean, structured, and well-organized text. Your goal is to extract all relevant information while maintaining clarity, accuracy, and coherence. Follow these guidelines:

## Instructions:
1. **Extract Information Clearly**:
   - Ensure the extracted text is easy to read and logically organized.
   - Maintain original formatting elements like headings, subheadings, and lists for better structure.

2. **Preserve Hierarchies**:
   - Use headings and subheadings to clearly separate different sections.
   - Number lists and retain bullet points as they appear in the PDF.

3. **Simplify Complex Elements**:
   - For tables or figures, describe their content in plain text if recreating them exactly is impractical.
   - Maintain the flow and avoid omitting critical information.

4. **Maintain Context and Meaning**:
   - Ensure the written text reflects the intent and context of the original content.
   - Avoid misinterpretations or rephrasing that alters meaning.

5. **Exclude Non-Essential Elements**:
   - Skip watermarks, unnecessary blank spaces, or visual-only elements irrelevant to the main content.

Execute these tasks efficiently, keeping the user's objectives in focus, and always prioritize clarity and usability in the output.
"""

response = model.generate_content(
    [{"mime_type": "application/pdf", "data": doc_data}, prompt]
)

print(response.text)
