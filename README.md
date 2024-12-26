# Cover Letter AI Agent

## Overview
The Cover Letter AI Agent is a sophisticated system designed to generate tailored cover letters based on a user's resume and a specific job description. By leveraging advanced language models and agentic orchestration, this tool streamlines the application process for job seekers by automating the creation of compelling and personalized cover letters.

## Features
- **Resume Understanding**: Analyzes the user's resume to extract relevant skills, experiences, and achievements.
- **Job Description Parsing**: Understands the job requirements and responsibilities to align with the candidate's profile.
- **Cover Letter Generation**: Creates a well-structured, customized cover letter that highlights the user's suitability for the job.
- **Agentic Orchestration**: Utilizes multiple specialized agents for different aspects of the cover letter generation process:
  - **Writer Agent**: Drafts the cover letter content.
  - **Router Agent**: Decides the best API (Gemini or OpenRouter) to use based on rate limits and other parameters.
  - **Tester Agent**: Evaluates the AI-generated content for quality and adherence to professional standards.
  - **Researcher Agent**: Gathers additional information about the company and the role to enhance the personalization of the cover letter.

## Setup and Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/cover-letter-ai-agent.git
   cd cover-letter-ai-agent
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Configure API keys in a `.env` file:
   ```env
   GEMINI_API_KEY=your_gemini_api_key
   OPENROUTER_API_KEY=your_openrouter_api_key
   ```

## Usage
1. Prepare your resume and job description as input files (e.g., `resume.pdf` and `job_description.txt`).
2. Run the script:
   ```bash
   python main.py --resume resume.pdf --job job_description.txt
   ```
3. The generated cover letter will be saved to a file (e.g., `cover_letter.txt`) and optionally displayed in the console.

## Architecture
### Agentic Workflow
The system uses multiple agents to handle specific tasks:
- **Writer Agent**: Responsible for generating the initial draft of the cover letter.
- **Router Agent**: Dynamically selects the API (Gemini or OpenRouter) to optimize response times and minimize rate-limit issues.
- **Tester Agent**: Ensures the generated cover letter meets quality standards, checking for grammar, tone, and relevance.
- **Researcher Agent**: Augments the cover letter by retrieving details about the company and job role for additional personalization.

### API Integration
The tool supports Gemini and OpenRouter APIs, switching between them based on availability and rate limits. This ensures seamless operation and high-quality outputs.

## Roadmap
### 1st Iteration
- Develop a functional script to:
  - Parse resumes and job descriptions.
  - Generate basic cover letters using a single API.

### Future Enhancements
- Add advanced resume parsing to identify soft skills and personality traits.
- Integrate feedback loops for iterative improvements to the cover letter.
- Expand API support for redundancy and improved performance.

## Contributing
We welcome contributions from the community! Please submit a pull request or open an issue for bug reports and feature requests.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgments
- OpenAI for the foundational language models.
- Gemini and OpenRouter for robust API support.

---

**Disclaimer**: This project is intended for educational and personal use. Always review AI-generated content for accuracy and appropriateness before submission.
