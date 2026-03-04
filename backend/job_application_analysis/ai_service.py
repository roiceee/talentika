"""
AI analysis service — sends extracted resume text + job profile data to an
LLM (OpenAI or Google Gemini) and returns a structured analysis.

Provider via settings.AI_PROVIDER (env AI_PROVIDER):
  - "openai"  → OpenAI Structured Outputs (default)
  - "gemini"  → Google Gemini Structured Output
"""

import logging

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
    score: int = Field(
        ge=0, le=100,
        description=(
            "Overall candidate-job-fit score from 0 to 100. "
            "Use these ranges: "
            "Excellent = 90-100, Good = 75-89, Moderate = 40-74, Bad = 0-39."
        ),
    )
    detailed_analysis: DetailedAnalysis = Field(description="In-depth structured analysis")


def _build_system_prompt() -> str:
    return (
        "You are an expert talent-acquisition analyst. "
        "Given a candidate's resume text and a job description with structured qualifications, "
        "produce a structured analysis of the candidate's fit for the role. "
        "Be objective, thorough, and concise.\n\n"
        "When assigning the score, use these category thresholds:\n"
        "- Excellent (90-100): Outstanding fit — exceeds most requirements\n"
        "- Good (75-89): Strong fit — meets key requirements well\n"
        "- Moderate (40-74): Partial fit — meets some requirements but has gaps\n"
        "- Bad (0-39): Poor fit — does not meet core requirements\n"
        "Pick a score that clearly places the candidate in the right category.\n\n"
        "Pay special attention to 'required' qualifications — failing to meet them "
        "should weigh heavily against the score. 'Preferred' qualifications are nice-to-have."
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


def _analyse_openai(system_prompt: str, user_prompt: str) -> ResumeAnalysisResult:
    from openai import OpenAI
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
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


def _analyse_gemini(system_prompt: str, user_prompt: str) -> ResumeAnalysisResult:
    from google import genai
    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=f"{system_prompt}\n\n{user_prompt}",
        config={
            "response_mime_type": "application/json",
            "response_schema": ResumeAnalysisResult,
        },
    )
    parsed = response.parsed
    if parsed is None:
        raise ValueError("Gemini returned a null parsed response.")
    return parsed


_PROVIDERS = {
    "openai": _analyse_openai,
    "gemini": _analyse_gemini,
}


def _get_provider():
    provider_name = getattr(settings, "AI_PROVIDER", "openai").lower()
    provider_fn = _PROVIDERS.get(provider_name)
    if provider_fn is None:
        raise ValueError(f"Unknown AI_PROVIDER: '{provider_name}'. Choose from: {', '.join(_PROVIDERS.keys())}")
    if provider_name == "openai" and not getattr(settings, "OPENAI_API_KEY", ""):
        raise ValueError("AI_PROVIDER is 'openai' but OPENAI_API_KEY is not set.")
    if provider_name == "gemini" and not getattr(settings, "GEMINI_API_KEY", ""):
        raise ValueError("AI_PROVIDER is 'gemini' but GEMINI_API_KEY is not set.")
    return provider_name, provider_fn


def analyse_resume(
    resume_text: str,
    job_title: str,
    job_description: str,
    qualifications: list[dict] | None = None,
    questions_and_answers: list[dict] | None = None,
) -> ResumeAnalysisResult:
    provider_name, provider_fn = _get_provider()
    logger.info("Using AI provider: %s", provider_name)
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(
        resume_text=resume_text,
        job_title=job_title,
        job_description=job_description,
        qualifications=qualifications or [],
        questions_and_answers=questions_and_answers or [],
    )
    return provider_fn(system_prompt, user_prompt)
