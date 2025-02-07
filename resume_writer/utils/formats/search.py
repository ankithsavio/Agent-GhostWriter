from pydantic import BaseModel, Field
from typing import List


class company_overview(BaseModel):
    queries: List[str]


class products_and_services(BaseModel):
    queries: List[str]


class job_specific_context(BaseModel):
    queries: List[str]


class recent_news_and_projects(BaseModel):
    queries: List[str]


class SearchQueries(BaseModel):
    company_overview: company_overview
    products_and_services: products_and_services
    job_specific_context: job_specific_context
    recent_news_and_projects: recent_news_and_projects
