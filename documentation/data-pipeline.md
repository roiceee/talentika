# Data Pipeline

Talentika employs a structured data pipeline to process job applications from the point of submission to the delivery of AI-generated insights to HR personnel. The pipeline is divided into three sequential phases: Data Preprocessing, AI Analysis, and Data Postprocessing and Insights. Each phase is designed to transform raw applicant data into structured, actionable information that supports hiring decisions, while ensuring that HR professionals retain full control over the final outcome.

---

## Data Preprocessing

The pipeline begins when an applicant submits their resume through a job posting link. Upon receipt, the system immediately performs duplicate detection to prevent redundant entries from entering the system and ensure the integrity of the applicant pool.

Duplicate detection operates in two layers. The first is a hard constraint: if an application with the same email address already exists for the same job profile, the submission is rejected outright, as email is treated as a unique identifier per position. The second layer is a weighted similarity score computed across three signals:

- **Name similarity** (weight: 0.55) — the applicant's full name is compared against existing entries using fuzzy string matching, which accounts for minor spelling variations and differences in name order.
- **Phone number match** (weight: 0.20) — an exact match check against the phone number of existing applicants.
- **Resume file hash** (weight: 0.25) — a SHA-256 cryptographic hash of the uploaded file is compared against stored hashes, allowing the system to detect identical file submissions regardless of filename.

These three signals are combined into a composite score between 0 and 1. Any submission scoring 0.75 or above is flagged as a duplicate and rejected. The weights are calibrated such that a matching name combined with either a matching phone number (0.55 + 0.20 = 0.75) or an identical resume file (0.55 + 0.25 = 0.80) is sufficient to trigger the threshold.

Following duplicate detection, the system performs file normalization. Since applicants may submit resumes in different file formats, any file submitted in DOCX format is automatically converted to PDF to ensure a consistent format for downstream processing. PDF submissions bypass this step.

Once the file is in a standardized format, text extraction is carried out through Optical Character Recognition (OCR). The system scans the resume and converts its visual content into machine-readable text, which serves as the primary input for the AI analysis phase.

---

## AI Analysis

With the extracted resume text available, the system proceeds to assemble the full context required for analysis. This includes the resume text, the job profile details such as the job title, description, and required qualifications, as well as any answers the applicant provided to screening questions defined by the organization. Together, these elements give the AI a complete picture of both the applicant and the position being applied for.

Using this assembled context, the system constructs a structured prompt that instructs the AI model on how to evaluate the applicant. The prompt is designed to guide the model toward producing consistent, job-relevant assessments rather than general observations.

The constructed prompt is then submitted to the AI model, which produces an analysis covering the applicant's qualifications, key skills, notable traits, and an overall fit assessment relative to the job profile.

---

## Data Postprocessing and Insights

Before the AI output is stored, it undergoes output validation to ensure the response conforms to a predefined structure. This step checks that all required fields are present and correctly formatted, preventing incomplete or malformed results from reaching the HR team.

Once validated, the results are saved to the database and made available to HR personnel for review. HR staff can examine each application alongside its AI-generated analysis, update the application status, and shortlist candidates as part of their evaluation process. At any point, HR can export the application data, including AI insights, as a CSV or spreadsheet file for reporting or further review.

The system also aggregates application and analysis data into an analytics view, giving HR teams a high-level overview of applicant trends, score distributions, and status breakdowns across a job profile.
