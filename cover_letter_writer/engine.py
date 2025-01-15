from llms import GeminiLLM, GenLLM, OptimLLM, PDFExtractor
from llms.logger import logger
from .workers import (
    JobExtractorWorker,
    ConvoSummarizerWorker,
    DraftWriterWorker,
    CriticWorker,
    FinalWriterWorker,
)
from .utils.prompts import (
    RESUME_GEN_PROMPT,
    RESUME_EVAL_PROMPT,
    COVER_LETTER_GEN_PROMPT,
    COVER_LETTER_EVAL_PROMPT,
)
from .utils.test import JOB_DESC, RESUME_PATH, COVER_LETTER_PATH
from pprint import pprint
import os


class CoverLetterWriterEngine:
    def __init__(
        self, job_description: str, path_to_resume: str, path_to_cover_letter: str
    ):
        self.generator = GenLLM
        self.evaluator = OptimLLM
        self.pdf_extractor = PDFExtractor()  # genai client
        self.job_extractor_worker = JobExtractorWorker()
        self.summarizer_worker = ConvoSummarizerWorker()
        self.draft_worker = DraftWriterWorker()
        self.critic_worker = CriticWorker()
        self.final_writer_worker = FinalWriterWorker()
        self.text_resume = self.load_pdf(path_to_resume)
        self.prev_cover_letter = self.load_pdf(path_to_cover_letter)
        try:
            self.job_insights = self.job_extractor_worker(
                job_description=job_description
            )
        except:
            logger.info("Error fetching job details")
            raise TypeError
        logger.info(f"Job details loaded")
        logger.debug(f"Job details:\n{self.job_insights}")

    def load_pdf(self, path):
        try:
            text = self.pdf_extractor(path)
        except:
            logger.info("Error fetching pdf")
            raise FileNotFoundError
        logger.info(f"Resume Loaded")
        logger.debug(f"Resume :\n{text}")
        return text

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

        self.resume_insights = self.summarizer_worker(Conversation=conversation)
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

    def get_cover_letter_draft(self, iter: int = 2):
        draft_generator = self.generator(COVER_LETTER_GEN_PROMPT)
        draft_evaluator = self.evaluator(COVER_LETTER_EVAL_PROMPT)
        conversation = ""
        response = self.generate_init_draft()
        for _ in range(iter):
            feedback = draft_evaluator(
                previous_cover_letter=self.prev_cover_letter,
                draft_cover_letter=response,
            )
            conversation += f"\nFeedback :\n{feedback}"
            response = draft_generator(draft_cover_letter=response, feedback=feedback)
            conversation += f"\nNew Draft :\n{response}"
        logger.debug(f"Draft optimization conversation: \n{conversation}")
        logger.info(f"Final draft derived")
        return response

    def run(self):
        self.get_resume_insights(2)
        draft_letter = self.get_cover_letter_draft(2)
        critic_response = self.critic_worker(cover_letter=draft_letter)
        self.final_letter = self.final_writer_worker(
            cover_letter=draft_letter, critic=critic_response
        )
        logger.debug(f"Draft Critic: \n{critic_response}")
        logger.debug(f"Final Cover Letter : \n{self.final_letter}")
        logger.info(f"Final Cover Letter Generated")

        return self.final_letter


if __name__ == "__main__":

    engine = CoverLetterWriterEngine(
        job_description=JOB_DESC,
        path_to_resume=RESUME_PATH,
        path_to_cover_letter=COVER_LETTER_PATH,
    )
    letter = engine.run()
    pprint(f"\n\n{letter}\n\n")
