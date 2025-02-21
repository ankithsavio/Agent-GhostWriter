from dotenv import load_dotenv

load_dotenv(".env")
from typing import List, Dict
from pydantic import BaseModel
from resume_writer.utils.formats.prompt import Prompt
from resume_writer.utils.formats.user import UserReport
from resume_writer.utils.formats.company import CompanyReport
from resume_writer.utils.formats.search import SearchQueries, RAGQueries
from resume_writer.utils.formats.persona import Personas
from resume_writer.utils.workers import Worker, Message
from resume_writer.utils.diff import Updates, DiffDocument
from llms.extractor import PDFExtractor
from llms.basellm import TogetherBaseLLM, GeminiBaseStructuredLLM
from resume_writer.utils.prompts import PDF_PROMPT, JD_PROMPT, JOB_DESC, QUERY_PROMPT
from researcher.search import SearXNG
from researcher.vectordb import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer
from concurrent.futures import ThreadPoolExecutor, as_completed
import pymupdf4llm as pymupdf
import json
import time


class ResumeWriterEngine:

    def __init__(self):
        self.pdf_llm = PDFExtractor()
        self.structured_llm = GeminiBaseStructuredLLM()
        self.llm = TogetherBaseLLM()
        # self.large_llm = GeminiBaseLLM()
        # self.large_llm.model = self.large_llm.large_model
        self.search = SearXNG()
        self.vectordb = Qdrant()
        self.user_collection = "User_Report"
        self.company_collection = "Company_Report"
        self.setup_vectordb([self.user_collection, self.company_collection])
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=0,
            length_function=len,
            is_separator_regex=False,
            separators=[
                "\n\n",
                "\n",
                ".",
                "\uff0e",
                "\u3002",
                ",",
                "\uff0c",
                "\u3001",
                " ",
                "\u200B",
                "",
            ],
        )
        self.job_description = JOB_DESC
        self.resume_path = "pdf/Resume.pdf"
        self.cover_letter_path = "pdf/Cover Letter.pdf"
        self.pdf_paths = [self.resume_path, self.cover_letter_path]
        self.anonymizer = PresidioReversibleAnonymizer(
            analyzed_fields=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS", "URL"]
        )
        self.user_reports = self.load_files()
        self.company_reports = self.load_job()
        self.create_user_portfolio()
        self.create_company_portfolio()

    def load_files(self):
        def anonymize(path):
            md = pymupdf.to_markdown(path)
            doc = DiffDocument(self.anonymizer.anonymize(md))
            return doc

        docs = (anonymize(item) for item in [self.resume_path, self.cover_letter_path])
        self.resume_doc, self.cover_letter_doc = docs
        for doc in docs:
            result = self.structured_llm(
                prompt=str(Prompt(prompt=PDF_PROMPT, doc=doc)),
                format=UserReport,
            )
            results.append(result)

        return results

    def load_job(self):
        result = self.structured_llm(
            prompt=str(Prompt(prompt=JD_PROMPT, job_description=self.job_description)),
            format=CompanyReport,
        )
        return [result]

    def summarize_search_results(self, results: List[Dict[str, str]]):
        summarized_results = []
        for result in results:
            combined_results = "\n\n".join(str(item) for item in result["result"])
            response = self.llm(
                str(
                    Prompt(
                        prompt="You are a helpful researcher. You are provided with the user query and a list of web search results.",
                        instructions="""
                        1. Summarize the search results into clear and concise overview that directly address the search query.
                        2. Synthesize information from multiple results where appropriate.
                        3. Include citations for key facts and claims. For each piece of information you present, indicate which search result(s) it came from.
                        4. Prioritize information relevance, omit irrelevant or tangential details.
                        5. Maintain a neutral and objective tone.
                        6. If a source is repeated, reuse the same source number.
                        7. The summary should be no more than 500 words followed by Sources.
                        """,
                        user_query=result["query"],
                        result_list=combined_results,
                    )
                )
            )
            summarized_results.append({"summary": response} | result)
        return summarized_results

    def split_and_upload_document(self, collection_name, doc):
        list_chunks = self.text_splitter.split_text(doc)
        list_of_payloads = [{"text": chunk} for chunk in list_chunks]
        self.vectordb.upsert_documents(collection_name, list_of_payloads)

    def create_user_portfolio(self):
        portfolio_outline = self.llm(
            str(
                Prompt(
                    prompt=f"Generate an user portfolio outline by strictly following the pydantic config : {str(UserReport.model_fields)}",
                    example="""
                    # Title
                    ## Subsection Title
                    ### Subsubsection Title
                    """,
                )
            )
        )
        self.user_portfolio = self.llm(
            str(
                Prompt(
                    prompt="Generate a single comperehensive portfolio article using the provided outline and two structured user reports",
                    outline=portfolio_outline,
                    user_report_1=self.user_reports[0].model_dump(),
                    user_report_2=self.user_reports[1].model_dump(),
                )
            )
        )
        self.split_and_upload_document(self.user_collection, self.user_portfolio)

    def create_company_portfolio(self):
        portfolio_outline = self.llm(
            str(
                Prompt(
                    prompt=f"Generate an company portfolio outline with only the topic headers and sources by strictly following the pydantic config : {str(SearchQueries.model_fields)}",
                    example="""
                    # Title\n
                    ## Subsection Title\n
                    ### Subsubsection Title\n
                    # Sources
                    """,
                )
            )
        )

        result = self.structured_llm(
            prompt=str(
                Prompt(
                    prompt=QUERY_PROMPT,
                    company_report=self.company_reports[0].model_dump(),
                )
            ),
            format=SearchQueries,
        )
        search_queires = [query for item in result for query in item[1].queries[:2]]
        search_results = self.summarize_search_results(
            self.search.run_many(queries=search_queires)
        )

        self.company_portfolio = portfolio_outline

        for item in search_results:
            search_results_formatted = f"""<Query>\n{item['query']}\n</Query>\n<Result>\n{item['summary']}\n</Result>"""
            self.company_portfolio = self.llm(
                str(
                    Prompt(
                        prompt=f"You are a **technical writer** specializing in company reports. Your task is to expand the report for **{self.company_reports[0].company.name}** by filling in sections of the provided outline using the following search results.",
                        instructions=f"""
                            1. Content Relevance: Ensure all added content is directly relevant to **{self.company_reports[0].company.name}**. Do not include information about other companies or irrelevant topics. Focus on information that directly supports the outline sections.
                            2. Outline Adherence: Strictly adhere to the provided outline structure. Only fill in content under the appropriate headings. Do not add new sections or deviate from the existing outline.
                            3. Source Citations: Cite sources using square brackets and numbers, e.g., `[1]`, `[2]`. If a source is already cited in the existing report, reuse the same source number.
                            4. No Irrelevant Information: If the search results do not contain relevant information for a specific section of the outline, leave that section blank. Do not invent or assume information. Maintain the original outline structure even if some sections remain unfilled.
                            5. Concise Integration: Integrate the information from the search results concisely and effectively into the report. 
                        """,
                        outline=self.company_portfolio,
                        search_results=search_results_formatted,
                    )
                )
            )

        self.split_and_upload_document(self.company_collection, self.company_portfolio)

    def setup_vectordb(self, collection_names):
        for name in collection_names:
            self.vectordb.create_collection(name)

    def query_vectordb(self, entity, queries: List[str]):
        if entity.value == "user":
            collection_name = self.user_collection
        elif entity.value == "company":
            collection_name = self.company_collection
        else:
            raise ValueError("Invalid entity")

        result_list = []
        for query in queries:
            results = self.vectordb.query_documents(collection_name, query, limit=2)
            result_list.append(
                {
                    "query": query,
                    "result": [result.payload["text"] for result in results],
                }
            )

        return result_list

    def workflow(self):
        topic = f"Personalized Resume for the role {self.company_reports[0].jobPosting.jobTitle} at {self.company_reports[0].company.name} for {self.user_reports[0].personal_information.name}"

        def get_personas():
            personas_result = self.structured_llm(
                prompt=str(
                    Prompt(
                        prompt=f"You need to select a group of Resume editors who will work together to create a {topic}. \
                        Each of them represents a different perspective , role , or affiliation for editing the resume for the user."
                    )
                ),
                format=Personas,
            )
            return [
                Worker(**persona.model_dump()) for persona in personas_result.editors
            ]

        def get_questions(worker: Worker):
            response = self.llm(
                str(
                    Prompt(
                        prompt=f"You are an experienced Resume writer and want to create a {topic}. Besides your identity as a Resume writer , you have a specific focus when researching i.e {worker.short_summary}.\
                        Now , you are chatting with an expert to get information.",
                        persona=f"""
                        role: {worker.persona} 
                        description: {worker.description} 
                        """,
                        conversation_history="\n".join(
                            [
                                f"\nrole : {message.role}\ncontent: {message.content}"
                                for message in worker.conversation.get_messages()
                            ]
                        ),
                        instructions="""
                            1. Ask good questions directly to get more useful information.
                            2. When you have no more question to ask , say "Thank you so much for your help" to end the conversation.
                            3. Only ask one question at a time and don't ask what you have asked before.
                            4. Your questions should be related to the topic you want to write.
                        """,
                    )
                )
            )
            message = Message(role=worker.persona, content=response)
            worker.conversation.add_message(message)
            return message

        def get_search_result(worker: Worker):
            last_message = worker.conversation.get_messages()[-1]
            response = self.structured_llm(
                str(
                    Prompt(
                        prompt=f"You want to answer the {worker.persona}'s question by querying vector database. What queries would answer the question effectively?",
                        question=f"role: {last_message.role}\ncontent: {last_message.content}",
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
                ),
                format=RAGQueries,
            )
            return self.query_vectordb(**response.model_dump())

        def get_answers(worker: Worker, search_results):
            response = self.llm(
                str(
                    Prompt(
                        prompt=f"You are an expert who can use information effectively. You are chatting with a Resume writer who wants to createa a {topic}\
                        for which you have the necessary information. You have gathered the related information and will now use the information to \
                        form a response.",
                        conversation_history="\n".join(
                            [
                                f"\nrole : {message.role}\ncontent: {message.content}"
                                for message in worker.conversation.get_messages()
                            ]
                        ),
                        gathered_information=search_results,
                        instructions="""
                        1. Make your response as informative as possible.
                        2. Make sure every sentence is supported by the gathered information.
                        3. Provide your answers directly and do not create new information that is not available in gathered information.
                        4. Keep your answer concise.
                        """,
                    )
                )
            )
            message = Message(role="Expert", content=response)
            worker.conversation.add_message(message)

        def conversation_simulation(worker: Worker):
            iterations = 10
            for _ in range(iterations):
                message = get_questions(worker)
                if "thank you so much for your help" in message.content.lower():
                    break
                search_results = get_search_result(worker)
                get_answers(worker, search_results)

            return worker.conversation.get_messages()

        personas = get_personas()
        conversations = []
        time.sleep(60)
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

    def post_workflow(self, conversation: List[Message]):
        formatted_conv = "\n".join(
            f"role: {item.role}\ncontent: {item.content}" for item in conversation
        )
        updated_content = ""
        while True:
            resume_updates = self.structured_llm(
                prompt=str(
                    Prompt(
                        prompt=f"You are a professional resume writer. Your task is to update the given resume for the role **{self.company_reports[0].jobPosting.jobTitle}** by using the information learned from the information-seeking conversation",
                        resume=self.resume_doc(),
                        information_seeking_conversation=formatted_conv,
                        update_history=updated_content,
                        instructions="""
                            1. Content Relevance: Ensure added content is high priority and relevant. Focus on information that directly supports the resume with the informative conversation.
                            2. New Content: Add the new information at the end of the pre-existing content as the obvious choice.
                            3. Concise Integration: Integrate the information from the conversation concisely and effectively into the resume. 
                            4. Updates History: Content that have already been updated and do not further processing. Only the content here has to be excluded from processing.
                            5. No Further Updates: When there are no more relevant information available to update the resume, return `None` for content i.e. {content : "None"}
                            6. Important: Strictly adhere to the format provided. Aim for high priority short phrases that needs updates.
                        """,
                        format="""
                            1. short_summary: short yet brief description on the changes made.
                            2. content: exact phrases from the resume that needs to be replaced.
                            3. reason: brief reasoning for replacement based on the information seeking conversation.
                            4. replacement: phrases from the `content` with updates to be replaced.
                        """,
                    )
                ),
                format=Updates,
            )
            if not exec(resume_updates.content):
                break
            updated_content += resume_updates.content
            self.resume_doc.apply(resume_updates)


if __name__ == "__main__":
    start_time = time.time()
    model = ResumeWriterEngine()
    results = model.workflow()
    end_time = time.time()

    print(results)
    print(f"Execution time: {end_time - start_time} seconds")
