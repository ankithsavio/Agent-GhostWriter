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

1.  **Hierarchical JSON Structure:** Organize queries into a nested JSON. Top levels are broad information categories; each category contains a list of specific search queries. Use descriptive category names as JSON keys.

2.  **Progressive Depth (Broad to Specific):** Begin with general "about" queries, then narrow to details vital for a cover letter. Think: *What information empowers a candidate to write a compelling, informed cover letter?*

3.  **Prioritize Job Application Relevance:** Actively consider the company report when formulating queries. Prioritize understanding the company and the mentioned Research projects, technologies, or industry trends.

4.  **Diverse Query Types for Comprehensive Research:** Employ diverse query types to capture varied information:
    -   **Foundational "About" Queries:** e.g., "about [Company Name]"
    -   **Informational Core:** e.g., "[Company Name] mission statement", "[Company Name] company values"
    -   **Job-Specific Insights (Company Report):** e.g., "[Company Name] projects in [domain/tech from job description]", "[Company Name] team structure [job title from job description]", "[Company Name] using [technology from job description]"
    -   **Recent & Dynamic:** e.g., "[Company Name] recent news", "[Company Name] press releases", "[Company Name] latest projects"

5.  **Strategic Keywords for Precision:** Use effective keywords and phrases to target relevant articles. 

6.  **Ensure Specificity & Relevance:** Queries *must* be specific enough for meaningful results. Avoid overly generic searches.

7.  **Balanced Query Volume:** Aim for no more than 2 strong queries per category for comprehensiveness without redundancy.

Given the Company Report, generate a JSON output following the structure. Focus on queries that yield valuable information for understanding the company and writing a highly targeted and impactful cover letter.
"""


JOB_DESC = """
About the job
About Builder.ai
We're on a mission to make app building so easy everyone can do it - regardless of their background, tech knowledge or budget. We've already helped thousands of entrepreneurs, small businesses and even global brands, like the BBC, Makro and Pepsi achieve their software goals and we've only just started.
Builder.ai was voted as one of 2023's ‘Most Innovative Companies in AI' by Fast Company, and won Europas 2022 ‘Scaleup of the Year'. Our team has grown to over 800 people across the world and our recent announcement of $250m Series D funding (and partnership with Microsoft) means there's never been a more exciting time to become a Builder.
Life at Builder.ai
At Builder.ai we encourage you to experiment! Each role at Builder has unlimited opportunities to learn, progress and challenge the status quo. We want you to help us become even better at supporting our customers and take AI app building to new heights.
Our global team is diverse, collaborative and exceptionally talented. We hire people for their differences but all unite with our shared belief in Builder's HEARTT values: (Heart, Entrepreneurship, Accountability, Respect, Trust and Transparency) and a let's-get-stuff-done attitude.
In return for your skills and commitment, we offer a range of great perks, from hybrid working and a discretionary variable pay or commision scheme, to employee stock options, generous paid leave, and trips abroad #WhatWillYouBuild
About The Role
We're looking for a curious, ambitious and a razor-sharp engineer to be based in Gurugram, India or London, UK. You are someone who is passionate about technology and is keen to build machine learning data pipelines that will ingest data and productionize machine learning models in the cloud. You are someone who has an understanding of machine learning and artificial intelligence technologies. You are motivated to drive significant business impact by applying your knowledge and skills. You are able to inspire your colleagues and champion your skills through influence and effective communication. We embrace those who see things differently, aren't afraid to experiment, and who have a healthy disregard for constraints.
You will be a part of the AI organization and will work closely and collaborate with global product and engineering teams across many locations including London, New Delhi, Los Angeles, France and Dubai. The Intelligent Systems team will drive all of the innovation powered by data science, machine learning and AI (decision making). It is likely to witness significant growth over the course of the next year and beyond.
Why you should join
This is a challenging and diverse role that will require you to be a part of the growth of the AI organization from the ground up. The problems we face are unique, requiring us to innovate across a range of stages through invention and research of new techniques, to intelligent implementation and system integration. Furthermore, this is an opportunity to help grow our suite of products that in conjunction are aiming to automate the entire software development life cycle.
You'll be responsible for
Build, maintain and manage data pipelines that support the modeling initiatives of data scientists
Work closely with data scientists and engineering teams to productionize machine learning models
Contribute to the development of the Builder Knowledge Graph
Build unique solutions which ensure that GenAI LLM models in our pipeline have the data they need (through efficient RAG, prompting, agent architectures) and are able to integrate with automated and human workflows efficiently to deliver to our customers and capture feedback for continuous learning.
Engineer to scale in the cloud using methodologies such as service-oriented architectures, containerized applications and lambdas
Requirements
Higher university degree (MSc or PhD) in Computer Science, Engineering, Mathematics, Physics etc
Solid programming experience in one or more general purpose programming languages: Python (required), Ruby (desirable).
Software engineering experience applied to productionising machine learning or building data pipelines
Solid fundamental knowledge of data querying and manipulation using SQL (required), Neo4j (desirable)
Practical ML experience in R&D, commercial or academic projects
Ability to communicate with diverse stakeholders
Added Bonus
Understanding of or experience of building knowledge graphs and graph databases
Experience working with events type data
Experience with technologies such as Docker or Kubernetes
Engineering at scale using production level architectures
Benefits
Discretionary variable pay or commission scheme dependant on your role
Stock options in a $450 million funded Series D scale-up company
Hybrid working 
24 days annual leave + bank holidays
2 x Builder family days each year
Time off between Christmas and New Year
Generous Referral Bonus scheme
Pension contributions
Private Medical Insurance provided by AXA 
Private Dental Insurance provided by Bupa 
Access to our Perkbox
"""
