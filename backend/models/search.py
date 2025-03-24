from enum import Enum
from typing import List

from pydantic import BaseModel


class company_overview(BaseModel):
    queries: str


class products_and_services(BaseModel):
    queries: str


class job_specific_context(BaseModel):
    queries: str


class recent_news_and_projects(BaseModel):
    queries: str


class SearchQueries(BaseModel):
    company_overview: company_overview
    products_and_services: products_and_services
    job_specific_context: job_specific_context
    recent_news_and_projects: recent_news_and_projects


class Entity(Enum):
    USER = "user"
    COMPANY = "company"


class RAGQueries(BaseModel):
    entity: Entity
    queries: List[str]
