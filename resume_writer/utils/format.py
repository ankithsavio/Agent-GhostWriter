from pydantic import BaseModel
from typing import List


class contact(BaseModel):
    email: str
    phone: str
    address: str


class personal_information(BaseModel):
    name: str
    contact: contact
    professional_summary: str


class work_experience(BaseModel):
    company: str
    role: str
    start_date: str
    end_data: str
    additional_information: str


class education(BaseModel):
    institution: str
    degree: str
    major: str
    start_data: str
    end_data: str
    additional_information: str


class projects(BaseModel):
    title: str
    description: str
    technology_used: str


class additional_details(BaseModel):
    detail_name: str
    detail_value: str


class UserReport(BaseModel):
    personal_information: personal_information
    education: education
    work_experience: List[work_experience]
    projects: List[projects]
    additional_details: List[additional_details]
    skills: List[str]
    certifications: List[str]
    publications: List[str]

