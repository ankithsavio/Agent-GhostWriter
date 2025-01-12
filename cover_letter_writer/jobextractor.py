from linkedin_api import Linkedin
from llms.basellm import HfBaseLLM
from .prompts import JOB_EXTRACTOR_PROMPT, JOB_EXTRACTOR_USER_PROMPT
import os


class JobExtractor(HfBaseLLM):
    def __init__(self):
        super().__init__(system_prompt=JOB_EXTRACTOR_PROMPT)
        self.job_client = Linkedin(
            os.getenv("LINKEDIN_USER"), os.getenv("LINKEDIN_PASS")
        )

    def extract_job_id(self, url):
        import re

        match = re.search(r"[?&]currentJobId=(\d+)", url)
        if match:
            id = match.group(1)
        else:
            print(f"No `currentJobId` found in URL: {url}")

        return id

    def get_job_description(self, job_id):

        job_details = self.job_client.get_job(job_id)

        return job_details["description"]["text"]

    def generate(self, model, messages, **kwargs):

        self.config |= {
            "model": model,
            "messages": messages,
        }

        return self.client.chat.completions.create(**self.config)

    def __call__(self, job_url):
        job_id = self.extract_job_id(job_url)
        job_description = self.get_job_description(job_id)

        message = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": JOB_EXTRACTOR_USER_PROMPT.format(
                    job_description=job_description
                ),
            },
        ]
        return self.generate(self.model, message)
