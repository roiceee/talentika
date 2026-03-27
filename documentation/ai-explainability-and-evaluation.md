# AI Explainability and Evaluation

This document addresses the panel's feedback on model transparency, scoring rationale, evaluation methodology, and research ethics.

---

## 1. How the Model Arrives at Its Decisions

Talentika does not use a trained machine-learning classifier. Instead it uses a **Large Language Model (LLM) — specifically OpenAI GPT-4o-mini or Google Gemini 2.0 Flash** — guided by a structured system prompt and a rich user prompt assembled from four sources of ground truth:

1. **Job profile title and description** — defines what the role requires
2. **Qualifications list** — structured requirements (name, category, requirement level, years, proficiency) tagged as `required` or `preferred`
3. **Applicant's answers to screening questions** — direct responses from the candidate
4. **OCR-extracted resume text** — the candidate's full resume content

The LLM is given explicit classification criteria and must return a validated JSON object (`ResumeAnalysisResult`) — it cannot deviate from the schema. The structured output includes:

- `score_category` — one of `suitable`, `potentially_suitable`, or `unsuitable` (returned directly by the AI; no numeric score is used)
- `ai_analysis_summary` — narrative fit assessment
- `notable_traits` — inferred personal/professional traits
- `key_skills` — technical and soft skills detected
- `detailed_analysis` — strengths, areas for development, parsed work experience, education, certifications

Every output field has a defined purpose and is constrained by the Pydantic schema — the model cannot produce vague or unstructured answers.

---

## 2. Why the System Is Not a Black Box

The system provides full transparency at every layer:

| Layer | What is exposed |
|-------|----------------|
| Input | The exact resume text, qualifications, and Q&A answers sent to the LLM are traceable in the worker logs |
| Prompt | The system prompt and user prompt are human-readable templates in `ai_service.py` |
| Output | Every field returned by the LLM is stored in the database and shown in the UI |
| Classification | The AI returns the category directly — there is no hidden numeric intermediary |
| Narrative | `ai_analysis_summary` explains in plain language why the candidate received that classification |
| Detail | `detailed_analysis.strengths` and `areas_for_development` cite specific evidence from the resume |

HR reviewers can read the summary, inspect the strengths/weaknesses, and then decide whether to shortlist, hold, or reject — the system makes a recommendation, not a final decision.

---

## 3. Classification System

### Categories

The AI classifies each candidate directly into one of three categories. There is no numeric score — the LLM evaluates the full context and returns a category key.

| Category | Key | Meaning |
|----------|-----|---------|
| **Suitable** | `suitable` | Strong fit — meets key requirements well |
| **Potentially Suitable** | `potentially_suitable` | Partial fit — meets some requirements but has notable gaps |
| **Unsuitable** | `unsuitable` | Poor fit — does not meet core requirements |

### What Makes Someone "Suitable"

A candidate is classified here when the LLM finds that:
- Required qualifications are satisfied (the right skills, years of experience, and proficiency levels are present in the resume)
- Screening question answers demonstrate relevant knowledge and readiness
- Work experience and education align with the role's expectations
- No hard disqualifiers are present

### What Makes Someone "Potentially Suitable"

A candidate is classified here when:
- Some required qualifications are met but key ones are missing or only partially demonstrated
- Screening answers show limited depth or experience
- Experience is relevant but below the required level (e.g., 2 years vs. 5 years required)
- The resume suggests transferable skills but not direct experience

### What Makes Someone "Unsuitable"

A candidate is classified here when:
- Core required qualifications are absent from the resume
- Screening answers indicate a mismatch with the role
- Experience is unrelated to the position
- Fundamental requirements (e.g., specific degree, licensure, technology) are not met

### Basis for Classification

The AI is explicitly instructed:
- `required` qualifications that are unmet push the classification toward `unsuitable`
- `preferred` qualifications are nice-to-have and do not penalise a candidate if absent
- Strong screening answers can reinforce `suitable`; weak, evasive, or disqualifying answers push toward `potentially_suitable` or `unsuitable`

---

## 4. The Matching Process: Job Profile → Resume

The matching follows these steps:

### Step 1 — Text Extraction (OCR)

The uploaded resume (PDF or DOCX) is processed by the following pipeline:

1. **DOCX → PDF conversion** (if applicable): LibreOffice is called via the command line (`soffice`) to convert DOCX files to PDF before OCR begins.
2. **PDF → Images**: `pdf2image` rasterises each page of the PDF at **200 DPI** using Poppler.
3. **Downscaling**: Each page image is checked against a maximum of **4 megapixels** (4,000,000 pixels). Images exceeding this limit are downsampled using the Lanczos filter to prevent out-of-memory errors.
4. **OCR**: `pytesseract` (a Python wrapper for **Tesseract OCR**) runs `image_to_string()` on each page image. Pages are concatenated and separated by `--- Page N ---` markers.

**Tokenisation** occurs implicitly within Tesseract — the engine segments each page into text blocks, lines, and words before recognition. The output is a single plain-text string passed to the LLM.

### Step 2 — Prompt Assembly

The system builds a structured user prompt:

```
## Job Position
Title: [job title]
Description: [job description]

## Qualifications
### Technical
- Python (required) — 3+ years — intermediate level
- ...

## Applicant's Answers to Screening Questions
Q: Do you have experience with cloud platforms?
A: Yes, I have 2 years of AWS experience.

## Candidate Resume (OCR-extracted text)
--- Page 1 ---
[page text]
--- Page 2 ---
[page text]
```

This format enables **keyword and pattern recognition**: the LLM reads the qualification names and scans the resume text for matching terminology, phrasing, and context.

### Step 3 — Semantic Similarity via LLM

Unlike traditional keyword-matching systems, the LLM performs **semantic similarity** — it understands that "React.js developer" and "frontend engineer with React experience" refer to the same concept, and that "5 years in software engineering" may satisfy a "3 years required" condition even if the exact phrasing differs.

The LLM also evaluates **contextual relevance** — a listed skill that was used minimally carries less weight than one demonstrated across multiple roles and highlighted as a core responsibility.

### Step 4 — Structured Output Validation

The LLM's response is parsed and validated by **Pydantic**. The `score_category` field is constrained to a `Literal["suitable", "potentially_suitable", "unsuitable"]` type — any other value causes the response to be rejected and the analysis to be marked `FAILED`. This enforces output integrity.

- **OpenAI**: uses `client.beta.chat.completions.parse()` with `response_format=ResumeAnalysisResult` (Structured Outputs API)
- **Gemini**: uses `response_mime_type: "application/json"` with `response_schema: ResumeAnalysisResult`

### Step 5 — Storage and Display

The validated result is persisted to the database and surfaced in the HR dashboard, where reviewers see the classification, the narrative summary, strengths, areas for development, key skills, and notable traits.

---

## 5. Basis for Specific Outputs

| Output | Basis |
|--------|-------|
| `score_category` | Direct LLM classification from the full context (job + qualifications + answers + resume) |
| `ai_analysis_summary` | LLM narrative assessment of the candidate's overall fit for the role |
| `notable_traits` | Traits inferred from tone, language, and described experiences in the resume |
| `key_skills` | Skills explicitly mentioned or clearly demonstrated in the resume text |
| `detailed_analysis.strengths` | Specific resume evidence that supports the candidate's fit |
| `detailed_analysis.areas_for_development` | Specific gaps relative to the job requirements |
| `detailed_analysis.experience` | Parsed directly from the resume text (title, company, duration, highlights) |

---

## 6. System as Integration of Multiple Components

Talentika's innovation is in the **pipeline integration**, not in a single component:

```
Resume Upload (PDF or DOCX)
         ↓
DOCX → PDF conversion (LibreOffice, if needed)
         ↓
PDF → Page Images (pdf2image, 200 DPI, max 4MP per page)
         ↓
OCR (Tesseract via pytesseract) — extracts plain text from each page
         ↓
Prompt Assembly — job profile + qualifications + screening answers + resume text
         ↓
LLM (OpenAI GPT-4o-mini / Google Gemini 2.0 Flash) — structured classification
         ↓
Pydantic validation — enforces schema and category constraints
         ↓
HR Dashboard — classification badge, narrative, strengths/gaps, skills, traits
```

Each component is individually well-established; the value is in the automated, end-to-end pipeline that replaces manual CV screening. The system also handles multi-tenant access control, asynchronous job queues with retry logic (up to 3 retries: 30s, 60s, 120s intervals), duplicate detection, and CSV/XLSX export — without HR needing to interact with any individual component.

---

## 7. Evaluation Methodology

### HR-Based Evaluation

The system will be tested using **structured HR evaluation sessions**:

1. A set of real or anonymized resumes is submitted through the system
2. HR practitioners review both the AI's recommendation and the underlying analysis
3. Practitioners rate agreement/disagreement with the category classification and narrative
4. Discrepancies are recorded and analyzed

### Evaluation Instrument

The evaluation will use a **standardized questionnaire**. The target standard is **ISO 9241-11 (Usability)** covering:
- Effectiveness — does the system produce accurate recommendations?
- Efficiency — does it reduce HR screening time?
- Satisfaction — is the output clear and trustworthy?

For AI-specific evaluation, items from the **System Usability Scale (SUS)** will be adapted, supplemented by custom items targeting:
- Perceived accuracy of the classification
- Clarity of the justification
- Confidence in using the recommendation as a decision aid

If a non-standard instrument is used, internal validation (Cronbach's alpha ≥ 0.7) will be computed before results are reported.

### Scoring and Reporting

- Mean scores per dimension will be computed and reported with standard deviation
- Results will be compared against established benchmarks (e.g., SUS score ≥ 68 = above average usability)
- Individual item analysis will identify which aspects of the system need improvement

### Ethical Practices

- No participant data will be manipulated
- All evaluation results — positive or negative — will be reported as-is
- If the system scores weakly on a dimension, the root cause will be identified and the system will be improved before re-testing
- Participants will be informed that their evaluations inform a research study
- Resume data used during testing will be anonymized or use synthetic data where possible

---

## 8. Timeline

| Phase | Target |
|-------|--------|
| System completion and internal testing | April 2026 |
| HR evaluation sessions | April 2026 |
| Results analysis and system improvements | Late April 2026 |
| Final documentation and presentation preparation | Late April – Early May 2026 |
| Defense | Early May 2026 |

### Methodology Note

This project follows a **Waterfall methodology**:
- Requirements → Design → Implementation → Testing → Evaluation → Defense
- Phases do not overlap; each is completed before the next begins
- Changes identified during testing are addressed within the testing phase, not by restarting earlier phases
