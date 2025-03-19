PDF_PROMPT = """ 
You are an expert in natural language processing and information extraction. Given the following PDF text, extract all the relevant information into a structured JSON format. Please follow these instructions:

1. **Output Format:**  
- The JSON must include the following keys: `personal_information`, `education`, `work_experience`, `certifications`, `projects`, `publications`, `skills`, `additional_details`, and `professional_summary`.
- For any fields that are not present in the file, assign the value empty string '' rather than placeholder strings.

2. **Detailed Extraction Requirements:**  
- **Personal Information:**  
- Extract `name`, `email`, `phone`, and `address` from the contact details.
- **Education:**  
- For each education entry, extract the `institution`, `degree`, `major`, `start_date`, `end_date`, and any `additional_info` (e.g., thesis details, distinctions).  
- Use consistent date formatting (e.g., `YYYY-MM` if dates are provided).
- **Work Experience:**  
- If available, extract details such as the company name, role, start and end dates, and a list of responsibilities or achievements.
- **Certifications and Publications:**  
- Extract these as lists if mentioned; otherwise, set them as null.
- **Projects:**  
- For each project, extract the `project_title`, `description`, and `technology_used`.  
- Ensure that the description provides enough detail to understand the project context.
- **Skills:**  
- List all technical and soft skills mentioned.
- **Additional Details:**  
- Capture any extra details that do not fall into the above categories.
- **Professional Summary:**  
- Extract a cohesive summary that reflects the candidate's motivation, objectives, and unique value proposition.

3. **Consistency and Validation:**  
- Ensure that the final JSON output is valid, well-formatted, and free of placeholder values such as "NA".  
- If certain sections or details are not found in the file, use an empty list (e.g., `[]`) appropriately.

4. **Decouple from the recipient:**  
- Do not include any details or phrases aimed towards the recipient of the file. In such cases, paraphrase to extract more general information.

5. **Output Only JSON:**  
- Do not include any additional commentary or explanation. Provide only the JSON output.

Please generate the JSON from the file given accordingly.
"""
JD_PROMPT = """
You are an expert in natural language processing and information extraction. Given the following text input, extract all the relevant information into a structured JSON format. Please follow these instructions:

1. **Output Format:**
   - The JSON must include the following keys: `company` and `jobPosting`.
   - Under the `company` key, extract and output the following fields:
     - `name`
     - `website`
     - `industry`
     - `companySize`
     - `foundedYear`
     - `missionStatement`
     - `values` (as a list)
     - `productsServices` (as a list)
     - `locations` (as a list)
   - Under the `jobPosting` key, extract and output the following fields:
     - `jobTitle`
     - `jobDescriptionSummary`
     - `jobResponsibilities` (as a list)
     - `jobRequirements` (as a list)
     - `jobLocation`
     - `postingDate`
   - For any fields that are not present in the input text, assign an empty string `''` for string values or an empty list `[]` for list values.

2. **Detailed Extraction Requirements:**
   - **Company:**
     - Extract the company's official `name`.
     - Extract the company's `website` URL.
     - Extract the `industry` in which the company operates.
     - Extract the `companySize` (e.g., number of employees or size range).
     - Extract the year the company was founded as `foundedYear`.
     - Extract the company's `missionStatement` if available.
     - Extract the company's core `values` as a list.
     - Extract the company's `productsServices` as a list.
     - Extract the `locations` where the company operates as a list.
   - **Job Posting:**
     - Extract the `jobTitle` of the position.
     - Extract a concise `jobDescriptionSummary` that outlines the role.
     - Extract the list of `jobResponsibilities`.
     - Extract the list of `jobRequirements`.
     - Extract the `jobLocation` where the job is based.
     - Extract the `postingDate` (ensure the date is formatted consistently, e.g., YYYY-MM-DD).

3. **Consistency and Validation:**
   - Ensure that the final JSON output is valid and well-formatted.
   - Do not include any placeholder values like "NA". If specific details are missing in the text, use an empty string (`''`) for string fields or an empty list (`[]`) for list fields.

4. **Decouple from the Recipient:**
   - Do not include any extraneous commentary, greetings, or salutations. Provide only the JSON output without additional explanation.

5. **Output Only JSON:**
   - Your response should contain only the JSON output and no extra text.

Please generate the JSON from the provided job description accordingly.
"""

QUERY_PROMPT = """
You are an expert in crafting highly effective information retrieval queries for in-depth company research. Your goal is to generate a structured JSON output containing a **hierarchical and targeted** set of web search queries. These queries will research a company (based on its name and a job description) to build a **"ground truth" document** for cover letter generation.

The queries should progressively explore the company, starting broadly and becoming increasingly specific and relevant to a job applicant's needs.

**Input:**

*   **Company Report:** (json) A report on the company.

**Query Generation Instructions:**

1.  **Hierarchical JSON Structure:** Organize queries into a nested JSON. Top levels are broad information categories; each category contains a list of specific search queries. 
2.  **Progressive Depth (Broad to Specific):** Begin with general "about" queries, then narrow to details vital for a cover letter. Think: *What information empowers a candidate to write a compelling, informed cover letter?*
3.  **Prioritize Job Application Relevance:** Consider the company report when formulating queries. Prioritize understanding the company and the mentioned Research projects, technologies, or industry trends.
4.  **Diverse Query Types for Comprehensive Research:** Employ diverse query types to capture varied information:
    -   **Foundational "About" Queries:** e.g., "about [Company Name]"
    -   **Informational Core:** e.g., "[Company Name] mission statement", "[Company Name] company values"
    -   **Job-Specific Insights (Company Report):** e.g., "[Company Name] projects in [domain/tech from job description]", "[Company Name] team structure [job title from job description]", "[Company Name] using [technology from job description]"
    -   **Recent & Dynamic:** e.g., "[Company Name] recent news", "[Company Name] press releases", "[Company Name] latest projects"
5.  **Strategic Keywords for Precision:** Use effective keywords and phrases to target relevant articles. 
6.  **Ensure Specificity & Relevance:** Queries *must* be specific enough for meaningful results. Avoid overly generic searches.
7.  **Balanced Query Volume:** Aim for single comprehensive query per category for without redundancy.

Given the Company Report, generate a JSON output following the structure. Focus on queries that yield valuable information for understanding the company and writing a highly targeted and impactful cover letter.
"""

REPORT_TEMPLATE = """# Targeted Keywords & Skills:

List 2-3 most impactful keywords to add or emphasize in the {doc}, based on conversation about company/role. E.g., "Cloud Computing", "Agile Methodologies", "Customer Success Metrics"

Mention 1-2 specific skills to highlight more prominently based on company needs. E.g., "Emphasize your Python skills in the Skills and Projects sections", "Showcase experience with Salesforce CRM in your Experience bullets."

Note any skills to de-emphasize if they are less relevant to the target company, but only if clearly discussed. E.g., "Reduce focus on legacy system experience, shift to modern tech."

# Company & Role Alignment:

Identify 1-2 specific aspects of the company/role mentioned in the conversation that should be directly addressed in the {doc}. E.g., "Highlight your experience in the FinTech industry to align with their sector focus.", "Showcase projects demonstrating innovation as it's a company value."

Suggest 1-2 sections or bullet points where this alignment can be explicitly shown. E.g., "In your Summary, mention your interest in contributing to a 'mission-driven company' (as discussed).", "In your 'Project X' description, link it to solving a problem similar to those in the [Company's Industry]."

# Experience Section - Impact & Quantify:

Point out 1-2 experience bullet points that could be strengthened by quantification. E.g., "Quantify the 'improved efficiency' in your role at Company Y - use numbers or percentages.", "For 'managed projects', specify the team size and budget if possible."

Suggest 1-2 action verbs to use to make experience descriptions more impactful and results-oriented. E.g., "Replace 'Responsible for' with stronger verbs like 'Spearheaded', 'Led', or 'Achieved'.", "Use verbs that imply impact, like 'Reduced', 'Increased', 'Optimized'."

# Summary/Profile Enhancement:

Suggest 1-2 adjustments to the summary to make it more targeted and compelling for the company. E.g., "Tailor your summary to directly mention your interest in [Company's Mission/Industry].", "Add a sentence highlighting your key value proposition in the first line."

Recommend if the summary should be more specific or more general based on the conversation context and target company type. E.g., "Make the summary more specific to the 'Data Science' role.", "Keep the summary slightly broader to accommodate various roles at a large corporation."

# Formatting & Clarity:

If formatting issues were discussed or are apparent, give 1-2 brief formatting tips. E.g., "Ensure consistent date formatting throughout.", "Break up large paragraphs into bullet points for readability."

If clarity issues were discussed, suggest 1-2 clarity improvements. E.g., "Simplify technical jargon in the 'Skills' section for broader readability.", "Ensure each bullet point clearly starts with your action and then the result."
"""
