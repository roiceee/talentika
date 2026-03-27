"""
AI analysis service — sends extracted resume text + job profile data to
OpenAI and returns a structured analysis.
"""

import logging

from typing import Literal

from pydantic import BaseModel, Field
from django.conf import settings

logger = logging.getLogger(__name__)


class ExperienceEntry(BaseModel):
    title: str = Field(description="Job title / role")
    company: str = Field(description="Company or employer name")
    duration: str = Field(description="Duration or date range, e.g. '2020-2023'")
    highlights: list[str] = Field(
        default_factory=list,
        description="Key achievements or responsibilities",
    )


class EducationEntry(BaseModel):
    degree: str = Field(description="Degree or qualification obtained")
    institution: str = Field(description="School / university name")
    year: str = Field(description="Graduation year or date range")


class DetailedAnalysis(BaseModel):
    strengths: list[str] = Field(default_factory=list, description="Candidate strengths relevant to the position")
    areas_for_development: list[str] = Field(default_factory=list, description="Areas where the candidate could improve")
    experience: list[ExperienceEntry] = Field(default_factory=list, description="Parsed work experience entries")
    education: list[EducationEntry] = Field(default_factory=list, description="Parsed education entries")
    certifications: list[str] = Field(default_factory=list, description="Professional certifications or licences")


class ResumeAnalysisResult(BaseModel):
    ai_analysis_summary: str = Field(description="A concise paragraph summarising the candidate's fit for the role")
    notable_traits: list[str] = Field(default_factory=list, description="Noteworthy personal / professional traits")
    key_skills: list[str] = Field(default_factory=list, description="Technical and soft skills identified")
    score_category: Literal["suitable", "potentially_suitable", "unsuitable"] = Field(
        description=(
            "Overall candidate-job-fit classification. "
            "Choose exactly one: "
            "'suitable' — strong fit, meets key requirements well; "
            "'potentially_suitable' — partial fit, meets some requirements but has notable gaps; "
            "'unsuitable' — poor fit, does not meet core requirements."
        ),
    )
    detailed_analysis: DetailedAnalysis = Field(description="In-depth structured analysis")


def _build_system_prompt() -> str:
    return (
        "You are an expert talent-acquisition analyst. "
        "Given a candidate's resume text, a job description with structured qualifications, "
        "and the candidate's answers to screening questions (if provided), "
        "produce a structured analysis of the candidate's fit for the role. "
        "Be objective, thorough, and concise.\n\n"
        "When classifying the candidate, choose exactly one category:\n"
        "- suitable: Strong fit — meets key requirements well\n"
        "- potentially_suitable: Partial fit — meets some requirements but has notable gaps\n"
        "- unsuitable: Poor fit — does not meet core requirements\n\n"
        "Pay special attention to 'required' qualifications — failing to meet them "
        "should push the classification toward 'unsuitable'. 'Preferred' qualifications are nice-to-have.\n\n"
        "If screening question answers are provided, factor them into the classification: "
        "strong answers support 'suitable'; weak, evasive, or disqualifying answers "
        "should push toward 'potentially_suitable' or 'unsuitable'."
    )


def _build_user_prompt(
    resume_text: str,
    job_title: str,
    job_description: str,
    qualifications: list[dict],
    questions_and_answers: list[dict],
) -> str:
    parts: list[str] = []
    parts.append("## Job Position\n")
    parts.append(f"**Title:** {job_title}\n")
    parts.append(f"**Description:** {job_description}\n")

    if qualifications:
        # Group qualifications by category for clarity
        by_category: dict[str, list[dict]] = {}
        for q in qualifications:
            cat = q.get("category", "other")
            by_category.setdefault(cat, []).append(q)

        parts.append("\n## Qualifications\n")
        for category, items in by_category.items():
            parts.append(f"\n### {category.title()}\n")
            for item in items:
                level = item.get("requirement_level", "required")
                name = item.get("name", "")
                line = f"- {name} ({level})"
                years = item.get("years_required")
                if years:
                    line += f" — {years}+ years"
                proficiency = item.get("proficiency_level")
                if proficiency:
                    line += f" — {proficiency} level"
                parts.append(line + "\n")

    if questions_and_answers:
        parts.append("\n## Applicant's Answers to Screening Questions\n")
        for qa in questions_and_answers:
            parts.append(f"**Q:** {qa['question']}\n")
            parts.append(f"**A:** {qa['answer']}\n\n")

    parts.append("\n## Candidate Resume (OCR-extracted text)\n")
    parts.append(resume_text)
    return "".join(parts)


def analyse_resume(
    resume_text: str,
    job_title: str,
    job_description: str,
    qualifications: list[dict] | None = None,
    questions_and_answers: list[dict] | None = None,
) -> ResumeAnalysisResult:
    if not getattr(settings, "OPENAI_API_KEY", ""):
        raise ValueError("OPENAI_API_KEY is not set.")

    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(
        resume_text=resume_text,
        job_title=job_title,
        job_description=job_description,
        qualifications=qualifications or [],
        questions_and_answers=questions_and_answers or [],
    )

    logger.info("Sending resume analysis request to OpenAI (model=%s)", settings.OPENAI_MODEL)
    completion = client.beta.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format=ResumeAnalysisResult,
    )
    result = completion.choices[0].message.parsed
    if result is None:
        raise ValueError("OpenAI returned a null parsed response (possible refusal).")
    return result
