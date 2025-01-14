from llms import GeminiLLM, GenLLM, OptimLLM, PDFExtractor
from llms.logger import logger
from .workers import JobExtractorWorker, ConvoSummarizerWorker, DraftWriterWorker
from .utils.prompts import RESUME_GEN_PROMPT, RESUME_EVAL_PROMPT
import os


class CoverLetterWriterEngine:
    def __init__(
        self, path_to_resume: str, job_description: str, cover_letter: str = None
    ):
        self.generator = GenLLM
        self.evaluator = OptimLLM
        self.pdf_extractor = PDFExtractor()  # genai client
        self.job_extractor_worker = JobExtractorWorker()
        self.summarizer_worker = ConvoSummarizerWorker()
        self.draft_worker = DraftWriterWorker()
        if os.path.exists(path_to_resume):
            try:
                self.text_resume = self.pdf_extractor(path_to_resume)
            except:
                logger.info("Error fetching resume")
                raise FileNotFoundError
            logger.info(f"Resume Loaded")
            logger.debug(f"Resume :\n{self.text_resume}")

        try:
            self.job_insights = self.job_extractor_worker(job_description)
        except:
            logger.info("Error fetching job details")
            raise TypeError
        logger.info(f"Job details loaded")
        logger.debug(f"Job details:\n{self.job_insights}")

    def get_resume_insights(self, iter: int = 2):
        insight_generator = self.generator(RESUME_GEN_PROMPT)
        insight_evaluator = self.evaluator(RESUME_EVAL_PROMPT)
        conversation = ""
        response = ""
        for _ in range(iter):
            response = insight_generator(Resume=self.text_resume, Feedback=response)
            conversation += f"\nInsights :\n{response}"
            response = insight_evaluator(
                Job_Description=self.job_insights, Insights=response
            )
            conversation += f"\nFeedback :\n{response}"

        self.resume_insights = self.summarizer_worker(conversation)
        logger.debug(f"Insight optimization conversation: \n{conversation}")
        logger.debug(f"Resume insights generated: \n{self.resume_insights}")
        logger.info(f"Resume insights derived")

    def generate_init_draft(self):
        draft_cover_letter = self.draft_worker(
            Job_Insights=self.job_insights, User_Insights=self.resume_insights
        )
        logger.debug(f"Draft cover letter generated: \n{draft_cover_letter}")
        logger.info(f"Draft cover ltter derived")
        return draft_cover_letter

    def get_cover_letter_insights(self, iter: int = 2):
        # TODO : cover letter draft gen with optimization
        pass

    def run(self):
        # TODO : run end-to-end all modules
        pass
