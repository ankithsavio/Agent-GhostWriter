from dotenv import load_dotenv

load_dotenv(".env")
import re
from typing import List, Dict
from backend.models.user import UserReport
from backend.models.company import CompanyReport
from backend.models.search import SearchQueries, RAGQueries, Entity
from ghost_writer.utils.prompt import Prompt
from ghost_writer.utils.workers import Worker, Message
from ghost_writer.utils.logger import logger
from ghost_writer.modules.vectordb import Qdrant
from ghost_writer.modules.storm import Storm
from ghost_writer.modules.knowledgebase import KnowledgeBaseBuilder
from backend.utils.prompts import PDF_PROMPT, JD_PROMPT, QUERY_PROMPT
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
from threading import Lock


class WriterEngine:
    """
    Engine for the orchestration of the ghost wrtier framework.
    """

    def __init__(self):
        self.user_collection_name = "user"
        self.company_collection_name = "company"
        self.workflow = Storm()
        self.vectordb = Qdrant()

    def get_job_kb(self, text: str):
        """
        Generates company knowledge base using the job description.
        Args:
            text (str): Job Description of the company.
        """
        self.company_knowledge_base = KnowledgeBaseBuilder(
            source=text,
            source_name=self.company_collection_name,
            model=CompanyReport,
            research=True,
        )
        logger.info("Company Knowledge Base Created")

    def get_user_kb(self, files: List[str]):
        """
        Generates user knowledge base using the uploaded files.
        Args:
            files (List[os.pathlike]): Paths for the uploaded user files.
        """
        self.user_knowledge_base = KnowledgeBaseBuilder(
            source=files,
            source_name=self.user_collection_name,
            model=UserReport,
            research=False,
        )
        logger.info("User Knowledge Base Created")

    def load_reports(self):
        """
        Generates structured reports of the user and the company.

        """
        docs = self.user_knowledge_base.source
        self.user_report = []
        for doc in docs:
            result = self.user_knowledge_base.structured_document(
                prompt=Prompt(prompt=PDF_PROMPT, doc=doc())
            )
            self.user_report.append(result)
        logger.info("User Report Loaded")

        docs = self.company_knowledge_base.source
        self.company_report = []
        for doc in docs:
            result = self.company_knowledge_base.structured_document(
                prompt=Prompt(prompt=JD_PROMPT, doc=doc())
            )
            self.company_report.append(result)

        logger.info("Company Report Loaded")

    def create_portfolios(self):
        """
        Generates knowledge documents for the user and the company using the knowledge builder module

        """
        portfolio_prompt = Prompt(
            prompt="Generate a single comperehensive portfolio article using the provided outline and two structured user reports",
            user_report_1=self.user_report[0].model_dump(),
            user_report_2=self.user_report[1].model_dump(),
        )
        self.user_portfolio = self.user_knowledge_base.create_knowledge_document(
            gen_prompt=portfolio_prompt
        )
        logger.info("User Portfolio Created")

        research_prompt = Prompt(
            prompt=QUERY_PROMPT,
            company_report=self.company_report[0].model_dump(),
        )
        portfolio_prompt = Prompt(
            prompt=f"You are a **technical writer** specializing in company reports. Your task is to write specific sections of the report for **{self.company_report[0].company.name}** using the web search results.",
            instructions=f"""
            1. Content Relevance: Ensure all added content is directly relevant to **{self.company_report[0].company.name}**. Do not include information about other companies or irrelevant topics. Focus on information that directly supports the outline sections.
            2. Subsection and Content: For the provided query and section, create a single appropriate subsection using the format - ### Subsection Title followed by its content. Generate this content directly.
            3. Outline Adherence: Strictly adhere to the provided section and outline. Do not add new sections, focus only on the given section and appropriately extend the provided outline.
            4. No Irrelevant Information: If the search results do not contain relevant information for the chosen specific section of the outline, leave that section blank. Do not invent or assume information.
            5. Concise Integration: Integrate the information from the search results concisely and effectively into the outline.
            """,
        )
        self.company_portfolio = (
            self.company_knowledge_base.create_knowledge_document_with_research(
                search_model=SearchQueries,
                search_prompt=research_prompt,
                gen_prompt=portfolio_prompt,
            )
        )
        logger.info("Company Portfolio Created")

    def cross_knowledge_base_query(self, entity: Entity, queries: List[str]):
        """
        Query across multiple collections in Qdrant
        """
        collection = entity.value.lower()
        if not collection in self.vectordb.get_collections():
            raise ValueError("Invalid collections name")

        result_list = []
        for query in queries:
            results = self.vectordb.query_documents(collection, query, limit=2)
            result_list.append(
                {
                    "query": query,
                    "result": [result.payload["doc"]["text"] for result in results],
                }
            )

        return result_list

    def set_prompts(self):
        """
        Prompts for Knowledge Storm
        """
        self.topic = f"Personalized Resume for the role {self.company_report[0].jobPosting.jobTitle} at {self.company_report[0].company.name}"

        self.persona_prompt = Prompt(
            prompt=f"You need to select a group of Resume editors who will work together to create a {self.topic}. \
            Each of them represents a different perspective , role , or affiliation for editing the resume for the user."
        )

        self.question_prompt = Prompt(
            prompt=f"You are an experienced Resume writer and want to create a {self.topic}. Besides your identity as a Resume writer , you have a specific focus when researching.\
            Now , you are chatting with an expert to get information.",
            instructions="""
                1. Ask good questions directly to get more useful information.
                2. When you have no more question to ask , say "Thank you so much for your help" to end the conversation.
                3. Only ask one question at a time and don't ask what you have asked before.
                4. Your questions should be related to the topic you want to write.
            """,
        )

        self.search_prompt = Prompt(
            prompt="\n",
            instructions="""
            1. Generate a set of queries that can completely and effectively answer the question.
            3. Generate no more than 3-5 queries. The queries must be independent of each other.
            2. Choose appropriate entity based on the question.
            """,
            example="""
            # Input
            role: xyz editor
            content: The role requires proficiency with a specific CRM, 'Salesforce,' along with 'lead generation' and 'sales pipeline management.' \
            Does the candidate have documented Salesforce experience, and can you find examples related to those specific sales processes?
            # Output
            {
                entity : user,
                queries : ["Salesforce experience", "Lead generation experience", "Sales pipeline management experience"]
            }
            # Input
            role: xyz editor
            content: The job description mentions a preference for candidates with a Master's degree and research experience. Does john doe hold a \
            Master's degree, and if so, in what field? Can you provide details of any research projects they've been involved in, including publications or presentations?
            # Output
            {
                entity : user,
                queries : ["John Doe Master's degree field of study", "Research projects", "Research publications", "Research presentations", "Academic research experience"]
            }
            """,
        )

        self.answer_prompt = Prompt(
            prompt=f"You are an expert who can use information effectively. You are chatting with a Resume writer who wants to createa a {self.topic}\
            for which you have the necessary information. You have gathered the related information and will now use the information to \
            form a response.",
            gathered_information="{search_results}",
            instructions="""
            1. Make your response as informative as possible.
            2. Make sure every sentence is supported by the gathered information.
            3. Provide your answers directly and do not create new information that is not available in gathered information.
            4. Keep your answer concise.
            """,
        )
        logger.info("Prompts are set for orchestration")

    def generate_personas(self):
        """
        Generate personas for multi-agent communication.

        """
        self.personas = self.workflow.get_personas(prompt=self.persona_prompt)
        logger.info("Personas successfully created")
        return self.personas

    def conversation_simulation(self, worker: Worker):
        """
        Simulates a single conversation for a worker with the expert.
        Args:
            worker (Worker): persona with conversation history.

        """
        logger.info("Initiating conversation simulation")
        iterations = 3  # 10
        for _ in range(iterations):
            message = self.workflow.get_questions(worker, self.question_prompt)
            if "thank you so much for your help" in message.content.lower():
                break
            queries = self.workflow.get_search_queries(
                worker, RAGQueries, self.search_prompt
            )
            results = self.cross_knowledge_base_query(**queries.model_dump())

            self.workflow.get_answers(
                worker, self.answer_prompt.format(search_results=results)
            )
        logger.info("Conversation simulation completed")
        return worker.conversation.get_messages()

    def parallel_conversation(self, personas: List[Worker]):
        """
        Starts conversation_simulation in parallel among many workers.
        Args:
            personas (List[Worker]): list of personas with conversation history.

        """
        logger.info("Initiating Parallel Conversation")
        conversations = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_results = {
                executor.submit(self.conversation_simulation, worker): worker
                for worker in personas
            }

            for future in as_completed(future_results):
                worker = future_results[future]
                conversation_history = future.result()
                conversations.append({worker: conversation_history})
        logger.info("Parallel Conversation Completed")
        return conversations

    def post_workflow(self):
        """
        Create reports for editing the users documents.
        """

        from llms.basellm import LLM

        reasoning_model = LLM(
            provider="google", model="gemini-2.0-flash-thinking-exp-01-21"
        )

        self.reports = {"resume": {}, "cover_letter": {}}
        lock = Lock()

        def create_reports(worker: Worker):
            """
            Create reports using a static template
            """
            format = """
            # Targeted Keywords & Skills:

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
            formatted_conv = "\n".join(
                f"role: {item['role']}\nmessage: {item['content']}"
                for item in worker.conversation.get_messages()
            )

            def create_resume_report():
                doc = "resume"
                prompt = Prompt(
                    prompt="You are an expert resume editor and you are provided with an information_seeking_conversation and user_resume. You have to provide a report to update user_resume using the provided format",
                    user_resume=self.user_knowledge_base.source[0](),
                    information_seeking_conversation=formatted_conv,
                    format=format.format(doc=doc),
                    instructions="""1. Strictly follow the format provided. Including sections and their instructions.
                    2. Report must be derived from the information_seeking_conversation. If information_seeking_conversation does target a particular section put "LGTM" in that section.
                    3. Only output the resume report in the provided format. Do not output any additional details.""",
                )
                response = reasoning_model(str(prompt))
                return response

            def create_cover_letter_report():
                doc = "cover letter"
                prompt = Prompt(
                    prompt="You are an expert cover letter editor and you are provided with an information_seeking_conversation and user_cover_letter. You have to provide a report to update user_cover_letter using the provided format",
                    user_cover_letter=self.user_knowledge_base.source[1](),
                    information_seeking_conversation=formatted_conv,
                    format=format.format(doc=doc),
                    instructions="""1. Strictly follow the format provided. Including sections and their instructions.
                    2. Report must be derived from the information_seeking_conversation. If information_seeking_conversation does target a particular section put "LGTM" in that section and nothing else.
                    3. Only output the cover letter report in the provided format. Do not output any additional details.""",
                )
                response = reasoning_model(str(prompt))
                return response

            with ThreadPoolExecutor(max_workers=2) as executor:
                futures_to_doc = {
                    executor.submit(create_resume_report): "resume",
                    executor.submit(create_cover_letter_report): "cover_letter",
                }

                for future in futures_to_doc:
                    doc = futures_to_doc[future]
                    with lock:
                        report = future.result()
                        self.reports[doc] |= {worker.role: report}
            return

        def combine_report(workers: List[Worker], doc_report: Dict[str, str]):
            """
            Combine reports from different personas into a single report.
            """
            report_template = """
            ###
            Source: {worker}
            Report: \n{content}
            ###
            """
            section = ""
            for worker in workers:
                worker_content = report_template.format(
                    worker=worker.role, content=doc_report[worker.role]
                )
                section += worker_content

            prompt = Prompt(
                prompt="Combine provided reports into a single comprehensive report by adapting the format to accommodate for sources",
                sources=section,
                example_format="""
                            # Report 
                            ## Title
                            Content as bullet points 
                            ## Title 2
                            Content as bullet points 2
                            """,
                instructions="""
                            1. Retain all informations from the sources.
                            2. Remove or merge dubplicates gracefully. If a section content is "LGTM" do not consider that source for that section.
                            3. Merge multiple sources into a single report using the example_format extensively covering all important details in the sources.
                            4. Only output the single report and no other additional details.
                            """,
            )
            response = reasoning_model(str(prompt))
            return response

        def process_content(content):
            """
            Remove markdown code block delimiters (triple backticks) from text. (for gemini)
            """
            if "```" in content:
                content = re.sub(r"```(?:\w*\n?|\n?)", "", content)
            return content

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for worker in self.personas:
                futures.append(executor.submit(create_reports, worker))

            wait(futures)
            futures.clear()
            for doc in self.reports:
                futures.append(
                    {
                        executor.submit(
                            combine_report, self.personas, self.reports[doc]
                        ): doc
                    }
                )

            for future_doc in futures:
                future, doc = future_doc.popitem()
                report = future.result()
                self.reports[doc] = process_content(report)
