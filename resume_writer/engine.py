from dotenv import load_dotenv

load_dotenv(".env")
from typing import List, Dict
from pydantic import BaseModel
from resume_writer.utils.formats.prompt import Prompt
from resume_writer.utils.formats.user import UserReport
from resume_writer.utils.formats.company import CompanyReport
from resume_writer.utils.formats.search import SearchQueries
from llms.extractor import PDFExtractor
from llms.basellm import (
    TogetherBaseLLM,
    GeminiBaseStructuredLLM,
    HfBaseLLM,
    GeminiBaseLLM,
)
from resume_writer.utils.prompts import PDF_PROMPT, JD_PROMPT, JOB_DESC, QUERY_PROMPT
from researcher.search import SearXNG
from researcher.rag import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
import json
import time


class ResumeWriterEngine:

    def __init__(self):
        self.pdf_llm = PDFExtractor()
        self.structured_llm = GeminiBaseStructuredLLM()
        self.llm = TogetherBaseLLM()
        self.large_llm = GeminiBaseLLM()
        self.large_llm.model = self.large_llm.large_model
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
        self.pdf_paths = ["pdf/Resume.pdf", "pdf/Cover Letter.pdf"]
        # self.user_reports = self.load_files()
        self.company_reports = self.load_job()

    def load_files(self):
        results = []
        for file_path in self.pdf_paths:
            result = self.pdf_llm(
                prompt=str(Prompt(prompt=PDF_PROMPT)),
                pdf_path=file_path,
                format=UserReport,
            )
            dict_result = json.loads(result)
            results.append(UserReport(**dict_result))
        return results

    def load_job(self):
        result = self.structured_llm(
            prompt=str(
                Prompt(
                    prompt=JD_PROMPT
                    + f"<Job Description>\n{self.job_description}\n</Job Description>"
                )
            ),
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
                        prompt=f"""You are a helpful researcher. You are provided with the user query and a list of web search results.
                        <Instructions> 
                        1. Summarize the search results into clear and concise overview that directly address the search query.
                        2. Synthesize information from multiple results where appropriate.
                        3. Include citations for key facts and claims. For each piece of information you present, indicate which search result(s) it came from.
                        4. Prioritize information relevance, omit irrelevant or tangential details.
                        5. Maintain a neutral and objective tone.
                        6. If a source is repeated, reuse the same source number.
                        7. The summary should be no more than 500 words followed by Sources.
                        </Instructions> 
                        <User_Query>
                        {result['query']}
                        </User_Query>
                        <Result_List>
                        {combined_results}
                        </Result_List>"""
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
                    example=[
                        """
                        # Title
                        ## Subsection Title
                        ### Subsubsection Title
                        """
                    ],
                )
            )
        )
        self.user_portfolio = self.large_llm(
            str(
                Prompt(
                    prompt=f"""Generate a single comperehensive portfolio article using the provided outline and two structured user reports.
                        <Outline>
                        {portfolio_outline}
                        </Outline>
                        <User Report 1>
                        {self.user_reports[0].model_dump()}
                        </User Report 1>
                        <User Report 2>
                        {self.user_reports[1].model_dump()}
                        </User Report 2>
                        """
                )
            )
        )
        self.split_and_upload_document(self.user_collection, self.user_portfolio)

    def create_company_portfolio(self):
        portfolio_outline = self.llm(
            str(
                Prompt(
                    prompt=f"Generate an company portfolio outline with only the topic headers and sources by strictly following the pydantic config : {str(SearchQueries.model_fields)}",
                    example=[
                        """
                        # Title\n
                        ## Subsection Title\n
                        ### Subsubsection Title\n
                        # Sources
                        """
                    ],
                )
            )
        )

        result = self.structured_llm(
            prompt=str(
                Prompt(
                    prompt=QUERY_PROMPT
                    + f"""<Company Report>{self.company_reports[0].model_dump()}</Company Report>"""
                )
            ),
            format=SearchQueries,
        )
        search_queires = [query for item in result for query in item[1].queries[:2]]
        search_results = self.summarize_search_results(
            self.search.run_many(queries=search_queires)
        )

        # Dump search_results to a file for testing
        with open("tests/search_results_dump.json", "w") as f:
            json.dump(search_results, f, indent=4)

        # Load the search_results from the dumped file for testing purposes
        with open("tests/search_results_dump.json", "r") as f:
            loaded_search_results = json.load(f)

        self.company_portfolio = portfolio_outline

        for item in loaded_search_results:
            search_results_formatted = f"""<Query>\n{item['query']}\n</Query>\n<Result>\n{item['summary']}\n</Result>"""
            self.company_portfolio = self.llm(
                str(
                    Prompt(
                        prompt=f"""You are a **technical writer** specializing in company reports. Your task is to expand the report for **{self.company_reports[0].company.name}** by filling in sections of the provided outline using the following search results. \
                            <Instructions>
                            1. Content Relevance: Ensure all added content is directly relevant to **{self.company_reports[0].company.name}**. Do not include information about other companies or irrelevant topics. Focus on information that directly supports the outline sections.
                            2. Outline Adherence: Strictly adhere to the provided outline structure. Only fill in content under the appropriate headings. Do not add new sections or deviate from the existing outline.
                            3. Source Citations: Cite sources using square brackets and numbers, e.g., `[1]`, `[2]`. If a source is already cited in the existing report, reuse the same source number.
                            4. No Irrelevant Information: If the search results do not contain relevant information for a specific section of the outline, leave that section blank. Do not invent or assume information. Maintain the original outline structure even if some sections remain unfilled.
                            5. Concise Integration: Integrate the information from the search results concisely and effectively into the report. 
                            </Instructions>
                            <Outline>
                            {self.company_portfolio}
                            </Outline>
                            <Search Results>
                            {search_results_formatted}
                            </Search Results>
                            """
                    )
                )
            )

        self.split_and_upload_document(self.company_collection, self.company_portfolio)

    def setup_vectordb(self, collection_names):
        for name in collection_names:
            self.vectordb.create_collection(name)

    def query_user(self, queries):
        pass

    def query_company(self, queries):
        pass


if __name__ == "__main__":
    start_time = time.time()
    model = ResumeWriterEngine()
    results = model.create_company_portfolio()
    end_time = time.time()

    print(results)
    print(f"Execution time: {end_time - start_time} seconds")
