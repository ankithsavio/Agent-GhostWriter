from dotenv import load_dotenv

load_dotenv(".env")
from typing import List, Dict
from pydantic import BaseModel
from resume_writer.utils.formats.prompt import Prompt
from resume_writer.utils.formats.user import UserReport
from resume_writer.utils.formats.company import CompanyReport
from resume_writer.utils.formats.search import SearchQueries
from llms.extractor import PDFExtractor
from llms.basellm import TogetherBaseLLM, GeminiBaseStructuredLLM, HfBaseLLM
from resume_writer.utils.prompts import PDF_PROMPT, JD_PROMPT, JOB_DESC, QUERY_PROMPT
from researcher.search import SearXNG
import json
import time


class ResumeWriterEngine:

    def __init__(self):
        self.pdf_llm = PDFExtractor()
        self.structured_llm = GeminiBaseStructuredLLM()
        self.llm = TogetherBaseLLM()
        self.search = SearXNG()
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
                        6. The summary should be no more than 500 words followed by Sources.
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
        self.user_portfolio = self.llm(
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

    def create_company_portfolio(self):
        portfolio_outline = self.llm(
            str(
                Prompt(
                    prompt=f"Generate an company portfolio outline by strictly following the pydantic config : {str(SearchQueries.model_fields)}",
                    example=[
                        """
                        # Title
                        ## Subsection Title
                        ### Subsubsection Title
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

        search_results_formatted = "\n".join(
            f"""<Query {idx}>\n{item['query']}\n</Query {idx}>\n<Result {idx}>\n{item['summary']}\n</Result {idx}>"""
            for idx, item in enumerate(search_results)
        )

        self.company_portfolio = self.llm(
            str(
                Prompt(
                    prompt=f"""Generate a single company report article on {self.company_reports[0].company.name} using the provided outline and a list of search queries and their results.
                        <Outline>
                        {portfolio_outline}
                        </Outline>
                        <Search Results>
                        {search_results_formatted}
                        </Search Results>
                        """
                )
            )
        )

        return self.company_portfolio


if __name__ == "__main__":
    start_time = time.time()
    model = ResumeWriterEngine()
    results = model.create_company_portfolio()
    end_time = time.time()

    print(results)
    print(f"Execution time: {end_time - start_time} seconds")
