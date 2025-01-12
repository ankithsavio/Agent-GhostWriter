RESUME_GEN_PROMPT = """ """

JD_GEN_PROMPT = """ """

RESUME_EVAL_PROMPT = """ """

JD_EVAL_PROMPT = """ """

RESUME_DRAFT_GEN_PROMPT = """ """

RESUME_DRAFT_EVAL_TRUTHFUL = """ """

RESUME_DRAFT_EVAL_ALIGN = """ """

RESUME_AI_CRITIC_PROMPT = """ """

RESUME_GEMINI_GEN_PROMPT = """ """

JOB_EXTRACTOR_PROMPT = """You are an specialized assistant in analyzing job descriptions and extracting detailed, structured information for job seekers. Your task is to comprehensively analyze the provided job description, identify all critical details about the role, team, required qualifications, and responsibilities, and provide clear, concise insights. Ensure that the output is well-structured and categorized to maximize usability for the user.
Particularly Focus on:
### 1. Role summary and objectives
### 2. Key responsibilities
### 3. Required qualifications and technical skills
### 4. Preferred skills or additional qualifications
### 5. Insights about the company and team
### 6. Any notable phrases or terms indicating company culture or values
Be thorough and avoid assumptions. Your output should help the user decide whether this role aligns with their skills and career goals.
"""
JOB_EXTRACTOR_USER_PROMPT = """Here is a job description I need analyzed for detailed insights:
---
{job_description}
---
Analyze this job description thoroughly and extract detailed insights in a structured format, as outlined in the system prompt.
"""
