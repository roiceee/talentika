# Business Logic Flows

## 1. User Registration & Organization Setup

```mermaid
flowchart TD
    A[User Registers] --> B[Email & Password Saved]
    B --> C[User Creates Organization]
    C --> D[Org Status: PENDING]
    D --> E{Admin Approves?}
    E -->|Yes| F[Org Status: ACTIVE]
    E -->|No| G[Org Status: REJECTED]
    F --> H[Org Admin Invites Members]
    H --> I[Invitation Email Sent - 7 day token]
    I --> J{Invite Accepted?}
    J -->|Yes| K[Membership Created]
    J -->|No/Expired| L[Invitation Cancelled]
```

---

## 2. Job Profile Creation

```mermaid
flowchart TD
    A[Admin Creates Job Profile] --> B[Set Title, Category, Type, Level]
    B --> C[Write Job Description]
    C --> D[Add Qualifications - Required / Preferred]
    D --> E[Add Screening Questions]
    E --> F[Configure AI Strictness]
    F --> G[Job Profile Published]
    G --> H[Public Application Link Generated]
    H --> I[Share Link with Candidates]
```

---

## 3. Candidate Application Submission

```mermaid
flowchart TD
    A[Candidate Opens Public Link] --> B[Fill Contact Info]
    B --> C[Upload Resume - returns file_id]
    C --> D[Answer Screening Questions]
    D --> E[Submit Application]
    E --> F{Duplicate Check}
    F -->|Score >= 0.75| G[Flag as Duplicate]
    F -->|Score < 0.75| H[Save Application]
    H --> I[Confirmation Email Sent]
    H --> J[Queue for OCR Processing]
```

---

## 4. Duplicate Detection

```mermaid
flowchart TD
    A[New Application Arrives] --> B[Pre-filter: Same Job + Any Matching Signal]
    B --> C[Score Name Similarity - 40%]
    C --> D[Score Phone Match - 35%]
    D --> E[Score Email Match - 20%]
    E --> F[Score File Hash Match - 25%]
    F --> G[Compute Composite Score]
    G --> H{Score >= 0.75?}
    H -->|Yes| I[Flag as Probable Duplicate]
    H -->|No| J[Proceed as New Application]
```

---

## 5. AI Analysis Pipeline

```mermaid
flowchart TD
    A[Application Submitted] --> B[Status: OCR_PENDING]
    B --> C[OCR Worker: Extract Text from Resume]
    C --> D{OCR Success?}
    D -->|Yes| E[Status: OCR_DONE]
    D -->|No| F[Status: FAILED]
    E --> G[Status: AI_PENDING]
    G --> H[AI Worker: Build Prompt - Job + Requirements + Resume Text]
    H --> I[Send to LLM - OpenAI or Gemini]
    I --> J{AI Success?}
    J -->|Yes| K[Validate Response with Pydantic]
    J -->|No| L[Status: FAILED]
    K --> M[Status: DONE]
    M --> N[Analysis Available to HR Team]
    F --> O[HR can Retry Manually]
    L --> O
```

---

## 6. HR Review & Application Management

```mermaid
flowchart TD
    A[HR Opens Job Profile Dashboard] --> B[View Applications by Status]
    B --> C[Select Application]
    C --> D[View Applicant Info + AI Analysis]
    D --> E[Review Score, Summary, Strengths, Skills]
    E --> F{Decision}
    F -->|Advance| G[Status: SHORTLISTED]
    F -->|Pass| H[Status: REJECTED]
    F -->|Review Later| I[Status: UNDER_REVIEW]
    G --> J[Export Data for Reporting]
    H --> J
    J --> K[Export Job Queued]
    K --> L[CSV / XLSX File Generated]
    L --> M[Download Export File]
```
