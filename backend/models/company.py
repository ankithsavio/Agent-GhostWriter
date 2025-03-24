from typing import List

from pydantic import BaseModel


class company(BaseModel):
    name: str
    website: str
    industry: str
    companySize: str
    foundedYear: str
    missionStatement: str
    values: List[str]
    productsServices: List[str]
    locations: List[str]


class jobPosting(BaseModel):
    jobTitle: str
    jobDescriptionSummary: str
    jobResponsibilities: List[str]
    jobRequirements: List[str]
    jobLocation: str
    postingDate: str


class CompanyReport(BaseModel):
    company: company
    jobPosting: jobPosting
