# Talentika — System Capabilities Overview

> **Purpose**: This document describes the core technical capabilities of Talentika for patent documentation purposes. It covers what the system does, how it works, and the key technologies and concepts involved.

---

## What Is Talentika?

Talentika is a multi-tenant **HR decision-support tool**. It is not a job posting platform — organizations continue to advertise openings on their existing platforms (job boards, company websites, etc.) and simply share a Talentika application link with interested candidates. What Talentika does is collect those applications and run them through an AI-powered analysis pipeline, giving HR professionals structured, objective insights to help them make better hiring decisions. The final call always remains with the HR team; the system is designed to assist, not to automate.

---

## Core Capabilities

### 1. Multi-Tenant Organization Management

Talentika is built as a **multi-tenant system**, meaning multiple organizations can operate independently on the same platform. Each organization is isolated — its job profiles, applicants, and analysis results are visible only to its own members.

- Organizations go through an administrative status workflow: **Pending → Approved → Active** (or Rejected/Suspended).
- Users can belong to **multiple organizations simultaneously**.
- Within each organization, users hold one of two roles: **Organization Admin** or **Member**, controlling what actions they can perform.
- Admins can invite new members via **email-based invitation tokens** that expire after 7 days and are valid for single use only.

---

### 2. Job Profile Creation and Management

Before collecting applications, an organization creates a **Job Profile** inside Talentika — a structured template for the role being hired for. This is not the job advertisement itself (which lives on whatever external platform the organization uses), but rather the internal configuration that tells Talentika what to look for in candidates.

A Job Profile includes:

- **Job title, category, and employment type** (full-time, part-time, contract, internship, freelance)
- **Experience level requirements** (e.g., entry-level, senior)
- **Job description and requirements** — a free-text description plus a structured list of specific requirements
- **Skill definitions** — each skill is tagged as either required or nice-to-have
- **Custom screening questions** — admins can define questions that every applicant must answer, supporting three formats:
  - Open-ended text responses
  - Multiple-choice (multi-select)
  - Multiple-choice (single-select)
- **AI Screening Configuration** — a configurable profile that guides how strictly the AI evaluates candidates (e.g., strict/exact match, balanced, or flexible/potential-based)

This structured job profile is later fed directly into the AI as contextual grounding for evaluation — making the AI scoring specific to each role, not generic.

---

### 3. Public Application Submission via Shareable Links

Applicants do not need an account to apply. Each job profile generates a **publicly shareable application link** that HR teams can distribute however they choose — posted alongside a job advertisement, sent directly to candidates, embedded on a website, or shared through any other channel. Talentika itself is not a job board; it simply provides the intake form that candidates fill out.

The submission process uses a **two-step file upload flow** to handle large files reliably:

1. **Step 1 — Resume Pre-Upload**: The applicant uploads their resume file first. The system stores it temporarily and returns a `file_id` token.
2. **Step 2 — Full Submission**: The applicant submits the complete application (contact info, address, question answers) along with the `file_id`. The system links the pre-uploaded file to the application record.

Each application captures:

- Applicant contact information (name, email, phone)
- Full address (with ISO country code)
- Answers to all custom screening questions defined in the Job Profile
- File attachments: resume (required for AI analysis), cover letter, portfolio, certificates, or other documents

On successful submission, the applicant receives an **automatic confirmation email** with their application reference ID and position details.

Applications move through a status lifecycle: **Submitted → Under Review → Shortlisted / Rejected**.

---

### 4. Intelligent Duplicate Detection

When a new application arrives, the system automatically runs a **multi-signal duplicate detection check** against all previous applications for the same job profile before saving.

Rather than a simple exact-match check, the system computes a **weighted similarity score** using four signals:

| Signal         | Method                                                 | Weight |
| -------------- | ------------------------------------------------------ | ------ |
| Applicant name | Fuzzy string matching (token-sort ratio via RapidFuzz) | 40%    |
| Phone number   | Exact match                                            | 35%    |
| Resume file    | SHA-256 cryptographic hash comparison                  | 25%    |

Any application whose composite score meets or exceeds a **0.75 threshold** is flagged as a probable duplicate. The database query is pre-filtered at the SQL level (same job profile + at least one matching signal) before Python-level scoring, keeping performance efficient even for high-volume job postings.

SHA-256 hashes are computed at upload time and stored alongside each file, enabling instant zero-computation file identity checks for future comparisons.

---

### 5. AI-Powered Resume Analysis Pipeline

This is the core intelligence of Talentika. Once an application with a resume is submitted, the system automatically kicks off a **multi-stage asynchronous analysis pipeline** that prepares structured insights for the HR team to review.

#### Pipeline Architecture

The pipeline is **fully asynchronous**, running in the background via **Redis Queue (RQ)**. This ensures the applicant gets an instant submission response while heavy processing happens separately. Two specialized worker queues handle the pipeline:

```
Application Submitted
        │
        ▼
  [ocr_queue]  ─── Stage 1: OCR Processing
        │
        ▼
  [ai_queue]   ─── Stage 2: AI Analysis
        │
        ▼
  Result Stored (available for HR review)
```

Each stage has its own status, and the pipeline tracks progress through a well-defined state machine:

```
UPLOADED → OCR_PENDING → OCR_DONE → AI_PENDING → DONE
                                                 ↘ FAILED (any stage)
```

Failed analyses can be re-triggered manually by an admin without re-submitting the application.

---

#### Stage 1 — Optical Character Recognition (OCR)

The resume PDF is retrieved from storage (local disk or Amazon S3) and processed by **doctr**, a deep learning-based document understanding library.

Doctr uses two neural network models in sequence:

- **Text Detection**: `db_resnet50` — a ResNet-50-based differentiable binarization model that locates text regions in each page of the PDF
- **Text Recognition**: `crnn_vgg16_bn` — a convolutional recurrent neural network (CRNN) built on VGG-16 that reads and transcribes detected text regions

The output is the **full plain text of the resume**, with each page separated by a marker. This extracted text becomes the input for Stage 2.

The OCR model is loaded once at worker startup using thread-safe singleton initialization, avoiding repeated model loading overhead between jobs.

> **Note**: This is not a simple PDF text-copy operation — the OCR approach handles scanned documents, image-based PDFs, and non-selectable text. The system processes the visual layout of the document rather than relying on embedded text metadata.

---

#### Stage 2 — AI Analysis with Structured Outputs

The extracted resume text is combined with the full job profile context and sent to a **Large Language Model (LLM)** for structured analysis.

**Provider flexibility**: The system supports two LLM providers, switchable via configuration:

- **OpenAI** (GPT models) — using the Structured Outputs API
- **Google Gemini** — using the JSON Schema response mode

Both providers are instructed to return a **Pydantic-validated structured output** rather than free-form text. This means the AI response is type-checked and guaranteed to match a strict schema before being saved to the database.

**What the AI receives as input (the prompt):**

The AI receives a carefully constructed prompt containing all relevant context:

1. **Job title** — so the AI knows exactly what role is being evaluated
2. **Job description** — the full narrative of what the job entails
3. **Requirements list** — the explicit requirements from the job profile
4. **Skills list** — each skill tagged as required or nice-to-have
5. **Applicant's answers to screening questions** — the Q&A pairs from the application
6. **Full OCR-extracted resume text** — the candidate's experience as extracted from their document

This approach — providing the AI with rich, structured job-specific context alongside the candidate's document — ensures the evaluation is deeply relevant to the actual role, not a generic resume review.

> **On RAG (Retrieval-Augmented Generation)**: The current system does **not use RAG**. Rather than retrieving documents from a vector store, the system uses **context injection** — the full relevant context (job profile data + extracted resume text) is compiled directly into the prompt. The AI acts as a reasoning engine over this contained, well-structured context window. This is more suitable for the use case since each evaluation is fully self-contained.

**What the AI returns (structured output schema):**

| Field                                     | Type             | Description                                                      |
| ----------------------------------------- | ---------------- | ---------------------------------------------------------------- |
| `ai_analysis_summary`                     | Text             | A concise paragraph summarizing the candidate's fit for the role |
| `notable_traits`                          | Array of strings | Noteworthy personal and professional traits observed             |
| `key_skills`                              | Array of strings | Technical and soft skills identified from the resume             |
| `score`                                   | Integer (0–100)  | Overall candidate-to-job-fit score                               |
| `detailed_analysis.strengths`             | Array of strings | Candidate strengths relevant to the position                     |
| `detailed_analysis.areas_for_development` | Array of strings | Areas the candidate could improve                                |
| `detailed_analysis.experience`            | Structured array | Parsed work history: title, company, duration, highlights        |
| `detailed_analysis.education`             | Structured array | Parsed education: degree, institution, graduation year           |
| `detailed_analysis.certifications`        | Array of strings | Professional certifications and credentials                      |

All of this is stored in the database and surfaced to HR professionals through the API, giving them a clear, structured summary alongside the raw application to support — not replace — their judgment.

---

### 6. Cloud-Native File Storage

The system supports two file storage backends, switchable via configuration:

- **Local filesystem** — for development and single-server deployments
- **Amazon S3** — for scalable cloud deployments

Both backends implement a consistent interface through an abstract storage class, so the rest of the system works identically regardless of where files are stored. Files are organized with unique generated paths to prevent name collisions.

---

### 7. HR Review Interface and Application Status Management

Authenticated organization members can review all incoming applications and their AI-generated analysis results through the API. The system provides the data layer; the decisions remain entirely with the HR team.

- List all applications for a job profile, with filtering by status
- View detailed application data including all Q&A answers and attached files
- View the full AI analysis result alongside the application to inform decisions
- Manually update an application's status (shortlist, reject, move to under review, etc.)
- Re-trigger the analysis pipeline for a failed analysis without asking the applicant to resubmit

---

## Technical Concepts Summary

| Concept                     | Implementation                                                   |
| --------------------------- | ---------------------------------------------------------------- |
| Multi-tenancy               | Organization-scoped data with role-based permissions             |
| Async processing            | Redis Queue (RQ) with separate OCR and AI worker queues          |
| Deep learning OCR           | doctr with db_resnet50 (detection) + crnn_vgg16_bn (recognition) |
| LLM Structured Outputs      | OpenAI / Google Gemini with Pydantic-enforced JSON schema        |
| Context injection           | Job profile + resume text + Q&A compiled into a single prompt    |
| Fuzzy deduplication         | RapidFuzz token-sort ratio for name similarity                   |
| Cryptographic deduplication | SHA-256 file hashing for resume identity matching                |
| Dual storage backend        | Local filesystem or Amazon S3, swappable via config              |
| Email notifications         | SMTP (Gmail TLS) for submission confirmation and invitations     |
| API documentation           | Auto-generated Swagger/OpenAPI via drf-yasg                      |

---

_Document generated: February 24, 2026_
