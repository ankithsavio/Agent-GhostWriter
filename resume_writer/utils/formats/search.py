from pydantic import BaseModel
from typing import List


class projects_initiatives(BaseModel):
    queries: List[str]


class recent_news(BaseModel):
    queries: List[str]


class company_culture(BaseModel):
    queries: List[str]


class products_services(BaseModel):
    queries: List[str]


class job_posting_department(BaseModel):
    queries: List[str]


class SearchQueries(BaseModel):
    projects_initiatives: projects_initiatives
    recent_news: recent_news
    company_culture: company_culture
    products_services: products_services
    job_posting_department: job_posting_department
