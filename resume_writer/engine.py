from dotenv import load_dotenv

load_dotenv(".env")

from pydantic import BaseModel
from resume_writer.utils.formats.prompt import Prompt
from resume_writer.utils.formats.user import UserReport
from resume_writer.utils.formats.company import CompanyReport
from resume_writer.utils.formats.search import SearchQueries
from llms.extractor import PDFExtractor
from llms.basellm import TogetherBaseLLM, GeminiBaseStructuredLLM
from resume_writer.utils.prompts import PDF_PROMPT, JD_PROMPT, JOB_DESC, QUERY_PROMPT
from researcher.search import SearXNG
import json


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
        search_queires = result

        def search_web(queries):
            results = []
            for query in queries:
                result = self.search.run(query)
                results.append({"query": query, "results": result})
                break  # TODO : fix multi query error
            return results

        results = search_web(search_queires.products_services.queries)
        return results


if __name__ == "__main__":
    model = ResumeWriterEngine()
    results = model.create_company_portfolio()
    print(results)
