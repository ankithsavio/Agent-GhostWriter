from dotenv import load_dotenv

load_dotenv(".env")
from typing import List, Dict
from app.models.user import UserReport
from app.models.company import CompanyReport
from app.models.search import SearchQueries, RAGQueries
from ghost_writer.utils.persona import Personas
from ghost_writer.utils.prompt import Prompt
from ghost_writer.utils.workers import Worker, Message
from ghost_writer.utils.diff import Updates, DiffDocument
from ghost_writer.modules.search import SearXNG
from ghost_writer.modules.vectordb import Qdrant
from ghost_writer.modules.storm import Storm
from ghost_writer.modules.knowledgebase import KnowledgeBaseBuilder

from llms.basellm import TogetherBaseLLM, GeminiBaseStructuredLLM
from resume_writer.utils.prompts import PDF_PROMPT, JD_PROMPT, JOB_DESC, QUERY_PROMPT
from concurrent.futures import ThreadPoolExecutor, as_completed
import pymupdf4llm as pymupdf
import time


class WriterEngine:

    def __init__(self):
        self.resume_path = "pdf/Resume.pdf"
        self.cover_letter_path = "pdf/Cover Letter.pdf"
        self.job_description = JOB_DESC
        self.user_collection_name = "user"
        self.user_knowledge_base = KnowledgeBaseBuilder(
            source=[self.resume_path, self.cover_letter_path],
            source_name=self.user_collection_name,
            model=UserReport,
            anonymize=True,
        )
        self.company_collection_name = "company"
        self.company_knowledge_base = KnowledgeBaseBuilder(
            source=self.job_description,
            source_name=self.company_collection_name,
            model=CompanyReport,
            anonymize=False,  # for web search
        )
        self.workflow = Storm()
        self.vectordb = Qdrant()

    def load_reports(self):
        docs = self.user_knowledge_base.source
        self.user_report = []
        for doc in docs:
            result = self.user_knowledge_base.structured_document(
                prompt=Prompt(prompt=PDF_PROMPT, doc=doc())
            )
            self.user_report.append(result)

        docs = self.company_knowledge_base.source
        self.company_report = []
        for doc in docs:
            result = self.company_knowledge_base.structured_document(
                prompt=Prompt(prompt=JD_PROMPT, doc=doc())
            )
            self.company_report.append(result)

    def create_portfolios(self):
        portfolio_prompt = Prompt(
            prompt="Generate a single comperehensive portfolio article using the provided outline and two structured user reports",
            user_report_1=self.user_report[0].model_dump(),
            user_report_2=self.user_report[1].model_dump(),
        )
        self.user_portfolio = self.user_knowledge_base.create_knowledge_document(
            gen_prompt=portfolio_prompt
        )

        research_prompt = Prompt(
            prompt=QUERY_PROMPT,
            company_report=self.company_report[0].model_dump(),
        )
        portfolio_prompt = Prompt(
            prompt=f"You are a **technical writer** specializing in company reports. Your task is to expand the report for **{self.company_report[0].company.name}** by filling in sections of the provided outline using the following search results.",
            instructions=f"""
            1. Content Relevance: Ensure all added content is directly relevant to **{self.company_report[0].company.name}**. Do not include information about other companies or irrelevant topics. Focus on information that directly supports the outline sections.
            2. Outline Adherence: Strictly adhere to the provided outline structure. Only fill in content under the appropriate headings. Do not add new sections or deviate from the existing outline.
            3. Source Citations: Cite sources using square brackets and numbers, e.g., `[1]`, `[2]`. If a source is already cited in the existing report, reuse the same source number.
            4. No Irrelevant Information: If the search results do not contain relevant information for a specific section of the outline, leave that section blank. Do not invent or assume information. Maintain the original outline structure even if some sections remain unfilled.
            5. Concise Integration: Integrate the information from the search results concisely and effectively into the report. 
            """,
        )
        self.company_portfolio = (
            self.company_knowledge_base.create_knowledge_document_with_research(
                search_model=SearchQueries,
                search_prompt=research_prompt,
                gen_prompt=portfolio_prompt,
            )
        )

    def cross_knowledge_base_query(self, entity, queries: List[str]):
        """
        Query across multiple collections in Qdrant
        """
        collection = entity.value.lower()
        if not collection in self.vectordb.client.get_collections():
            raise ValueError("Invalid collections name")

        result_list = []
        for query in queries:
            results = self.vectordb.query_documents(collection, query, limit=2)
            result_list.append(
                {
                    "query": query,
                    "result": [result.payload["text"] for result in results],
                }
            )

        return result_list

    def orchestrate(self):
        """
        Knowledge Storm Orchestration
        """
        topic = f"Personalized Resume for the role {self.company_report[0].jobPosting.jobTitle} at {self.company_report[0].company.name} for {self.user_report[0].personal_information.name}"

        persona_prompt = Prompt(
            prompt=f"You need to select a group of Resume editors who will work together to create a {topic}. \
            Each of them represents a different perspective , role , or affiliation for editing the resume for the user."
        )

        question_prompt = Prompt(
            prompt=f"You are an experienced Resume writer and want to create a {topic}. Besides your identity as a Resume writer , you have a specific focus when researching.\
            Now , you are chatting with an expert to get information.",
            instructions="""
                1. Ask good questions directly to get more useful information.
                2. When you have no more question to ask , say "Thank you so much for your help" to end the conversation.
                3. Only ask one question at a time and don't ask what you have asked before.
                4. Your questions should be related to the topic you want to write.
            """,
        )

        search_prompt = Prompt(
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

        answer_prompt = Prompt(
            prompt=f"You are an expert who can use information effectively. You are chatting with a Resume writer who wants to createa a {topic}\
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

        def conversation_simulation(worker: Worker):
            iterations = 10
            for _ in range(iterations):
                message = self.workflow.get_questions(worker, question_prompt)
                if "thank you so much for your help" in message.content.lower():
                    break
                queries = self.workflow.get_search_queries(
                    worker, RAGQueries, search_prompt
                )
                results = self.cross_knowledge_base_query(**queries.model_dump())

                self.workflow.get_answers(
                    worker, answer_prompt.format(search_results=results)
                )

            return worker.conversation.get_messages()

        personas = self.workflow.get_personas(prompt=persona_prompt)
        conversations = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_results = {
                executor.submit(conversation_simulation, worker): worker
                for worker in personas
            }

            for future in as_completed(future_results):
                worker = future_results[future]
                conversation_history = future.result()
                conversations.append({worker: conversation_history})

        return conversations
