# AI Explainability and Evaluation

This document provides a scientifically grounded explanation of the AI-based resume screening system implemented in Talentika, addressing how decisions are made, how candidate-job matching works, what the classification categories mean, and how the system will be evaluated.

---

## 1. Underlying Technology: Large Language Models

Talentika uses a **Large Language Model (LLM)** — specifically OpenAI GPT-4o-mini or Google Gemini 2.0 Flash — as its AI reasoning engine. Understanding how an LLM works is necessary to understand how and why the system produces the outputs it does.

### What Is a Large Language Model?

LLMs are a class of artificial neural networks trained on vast corpora of human-produced text. Their architecture is based on the **Transformer** (Vaswani et al., 2017), which introduced a mechanism called **self-attention**: the ability for any part of an input text to selectively focus on and relate to any other part of the same input. This allows the model to understand language not as a sequence of isolated words, but as a web of contextual relationships.

During training, these models learn to predict the next word (token) in a sequence given all preceding words. Through this process — performed billions of times across diverse text sources — the model internalises grammar, factual knowledge, reasoning patterns, and importantly for this system, the semantic relationships between professional concepts, skills, job roles, and qualifications.

The result is a model capable of **in-context reasoning**: when given a task description and relevant data as input, it performs the task through inference rather than through pre-programmed rules or retraining.

### Why an LLM Is Appropriate for Resume Screening

Traditional automated resume screening approaches — such as keyword matching, Boolean filters, or TF-IDF document similarity — are fundamentally limited in that they operate on surface-level text patterns. They cannot determine that a candidate who describes themselves as a "software engineer specialising in backend systems" satisfies a requirement for a "server-side developer," nor can they interpret that "five years of professional Python experience" fulfils a "minimum three years required" condition.

LLMs overcome these limitations through:

- **Semantic understanding**: The model comprehends meaning rather than matching characters. Two phrases that describe the same concept will be recognised as equivalent even if they share no words.
- **Contextual reasoning**: The model evaluates evidence in context. A skill mentioned once in passing carries less weight than one demonstrated repeatedly across multiple roles.
- **Multi-criteria judgment**: The model simultaneously considers the job description, required qualifications, the candidate's resume, and their screening answers — synthesising all of these into a single reasoned classification.

---

## 2. How the System Makes Decisions

The AI's classification of each candidate is entirely determined by two structured text inputs it receives: a **system instruction** and a **candidate data package**.

### System Instruction

The system instruction is a fixed, human-authored description of the analyst's role and the classification rules. It establishes:

- The model's purpose (talent-acquisition analysis)
- The three classification categories and their definitions (described in Section 4)
- Which types of evidence carry greater weight (required qualifications vs. preferred ones)
- How screening question answers should influence the classification

This instruction does not change between candidates — it defines the consistent standard against which all candidates are measured.

### Candidate Data Package

For each candidate, a structured document is assembled from four sources:

| Source | Content | Role in Classification |
|--------|---------|----------------------|
| Job title and description | Free-text description of the position | Establishes what the role demands |
| Qualifications list | Structured criteria: skill name, whether required or preferred, years of experience, proficiency level | Provides the measurable standards |
| Screening question answers | The candidate's verbatim responses to structured questions | Provides direct, self-reported evidence |
| Resume text (extracted via OCR) | The full readable content of the uploaded resume | Provides the primary evidence base |

The model reads all four sources together and produces a classification along with a narrative explanation and structured breakdown.

### Output Constraints

The AI is technically constrained to return a fixed set of outputs in a defined format. The classification field must be exactly one of three values (`suitable`, `potentially_suitable`, `unsuitable`) — the system enforces this through schema validation, meaning the model cannot produce an ambiguous, hybrid, or invented category. If the model's response cannot be validated, the analysis is rejected and marked as failed. This constraint ensures the system behaves predictably and consistently across all candidates.

---

## 3. Why the System Is Not a Black Box

A system is considered a "black box" when it produces outputs that cannot be traced back to specific, inspectable reasons. Talentika is designed to avoid this:

| What might seem opaque | How the system makes it transparent |
|------------------------|-------------------------------------|
| Why was a candidate classified as Unsuitable? | The `ai_analysis_summary` provides a plain-language explanation citing the specific gaps found |
| What evidence was considered? | `strengths` and `areas_for_development` list the specific resume signals the model identified |
| What data was the AI given? | The resume text, qualifications, and answers are stored and visible to reviewers |
| What rules did the AI follow? | The classification criteria are fixed, written definitions (see Section 4) |
| What did the AI decide? | The classification, summary, skills, and traits are all stored and displayed — nothing is hidden |

Additionally, the system is positioned as a **decision-support tool**, not an autonomous decision-maker. Every classification is a recommendation. The human HR reviewer reads the AI's reasoning, examines the evidence, and independently decides whether to shortlist, hold, or reject the candidate. The AI reduces the volume of manual reading required; it does not replace human judgment.

---

## 4. Classification System: Measurable Criteria

### Why Direct Classification Instead of a Numeric Score

An earlier version of the system assigned a numeric score (0–100) that was then converted to a category. This approach was replaced for the following reasons:

- **False precision**: A score of 72 vs. 74 implies a meaningful difference that the model cannot reliably produce and that HR practitioners cannot meaningfully act on.
- **Conceptual mismatch**: HR practitioners reason in categories — a candidate is either a strong fit or a borderline one — not in percentage terms.
- **Transparency**: A direct category is self-explanatory; a derived numeric score adds an opaque conversion step.

The system now instructs the model to classify directly into one of three ordinal categories.

### The Three Categories

| Category | Meaning |
|----------|---------|
| **Suitable** | The candidate demonstrates strong alignment with the role. Required qualifications are substantially met, experience is relevant and at the appropriate level, and no disqualifying factors are present. |
| **Potentially Suitable** | The candidate meets some but not all key requirements. There are notable gaps in required qualifications or demonstrated competency, but the candidate may warrant further evaluation. |
| **Unsuitable** | The candidate does not meet the core requirements of the role. Critical qualifications are absent, experience is insufficient or unrelated, or disqualifying factors are identified. |

### Measurable Basis for Each Category

The classification is grounded in concrete criteria derived directly from the job profile:

**Suitable** — substantially all of the following are true:
- Required qualifications (skills, years of experience, proficiency levels) are present in the resume
- Work experience aligns with the role's domain and responsibilities
- Screening answers support the candidate's stated competencies without revealing disqualifying factors

**Potentially Suitable** — one or more of the following apply:
- One or more required qualifications are only partially met (e.g., fewer years of experience than specified, or a lower proficiency level)
- Experience is in a related but not directly matching field
- Screening answers are non-committal or reveal partial fit

**Unsuitable** — one or more of the following apply:
- Multiple required qualifications are entirely absent
- Experience is in an unrelated field
- Screening answers reveal a disqualifying factor (e.g., unavailability, absence of mandatory licensure, explicit incompatibility with role terms)

### Evidence Weighting

The system applies differential weighting to the types of evidence it considers:
- **Required qualifications** — unmet required qualifications are a strong signal toward `unsuitable` and are weighted accordingly
- **Preferred qualifications** — additive signals; their absence does not penalise a candidate
- **Screening answers** — used as corroborating or contradicting evidence; a strong answer supports a higher classification, while a disqualifying answer can override an otherwise favourable resume

---

## 5. The Matching Process: How the System Compares Resumes to Job Profiles

### Stage 1 — Text Extraction (Optical Character Recognition)

Resume files submitted as PDF or DOCX must first be converted into machine-readable text before any analysis can occur. This is accomplished through Optical Character Recognition (OCR).

**How OCR works in this system:**

1. If the file is a DOCX document, it is first converted to PDF format using LibreOffice to produce a consistent input format.
2. Each page of the PDF is converted into a digital image (rasterised) at 200 dots per inch (DPI). Higher DPI means more pixels per character, which improves recognition accuracy.
3. Each page image is passed through **Tesseract OCR** (Google's open-source OCR engine, version 4+), which uses a **Long Short-Term Memory (LSTM) neural network** to recognise text. LSTM-based recognition outperforms classical pattern-matching OCR because it interprets characters in sequence — understanding that `rn` in a cursive font likely represents the letter `m`, for example.
4. Tesseract internally performs **layout analysis** — segmenting the page into columns, paragraphs, lines, and words — before running character recognition. This is the OCR-side tokenisation: breaking the visual document into discrete units of meaning.
5. The recognised text from all pages is combined into a single document, with page boundaries marked.

### Stage 2 — Tokenisation (Language Model Side)

Before the extracted text is processed by the LLM, it is **tokenised** — broken into subword units called tokens. Tokenisation for LLMs is a linguistic operation: common words become a single token, while rare or compound words may be split across multiple tokens. Each token is then converted into a high-dimensional numerical vector (an **embedding**) that encodes its semantic meaning as learned during pre-training.

This embedding representation is what allows the model to understand that `"developer"` and `"engineer"` occupy similar positions in semantic space — they have similar embeddings — and are therefore related concepts.

### Stage 3 — Keyword and Pattern Recognition

The structured prompt format guides the model to identify specific types of content. When the model reads a qualification requirement such as `Python (required) — 3+ years`, it attends across the entire resume text looking for evidence of this qualification. This process is analogous to keyword and pattern recognition, but is implemented through the **self-attention mechanism** of the Transformer: every token in the qualification requirement is mathematically related to every token in the resume, weighted by semantic relevance.

This means the model can recognise the presence of a skill even when the exact phrasing differs from the requirement — for example, identifying that a resume describing "building REST APIs in Python for production systems" satisfies a "Python (required)" qualification.

### Stage 4 — Semantic Similarity Assessment

Semantic similarity refers to the degree to which two pieces of text convey the same meaning, independent of the specific words used. LLMs are particularly effective at semantic similarity because their embeddings capture conceptual meaning rather than surface form.

In the context of resume screening, this manifests as:

- **Equivalent terminology recognition**: "frontend developer" ↔ "UI engineer", "data analyst" ↔ "business intelligence specialist"
- **Requirement satisfaction inference**: "7 years of Java experience" satisfies "minimum 3 years required"
- **Contextual competency assessment**: "led a team of 5 engineers" implies leadership skills relevant to a managerial role, even if the word "leadership" does not appear

This capability is what distinguishes LLM-based screening from traditional document similarity methods (TF-IDF, BM25), which are sensitive to vocabulary mismatch and cannot perform this type of inference.

### Stage 5 — Classification and Explanation Generation

After processing all input tokens through its attention layers, the model generates the classification category along with the supporting narrative. The classification is produced in a single inference pass — the model considers the full context (job description, qualifications, answers, resume) simultaneously before generating any output.

The narrative outputs (`ai_analysis_summary`, `strengths`, `areas_for_development`) are generated by the same model in the same pass — they are the model's articulation of its reasoning, grounded in the evidence it identified in the resume text.

---

## 6. System Architecture: Integration of Components

The system's scientific contribution lies not in any single component but in the **integration of established technologies** into an automated, end-to-end screening pipeline. Each component addresses a specific technical challenge:

| Component | Technology | Challenge Addressed |
|-----------|-----------|---------------------|
| Document ingestion | LibreOffice, pdf2image | Normalises diverse file formats into a consistent text-extractable form |
| Text extraction | Tesseract OCR (LSTM) | Converts visual document content into machine-readable text |
| Semantic matching | LLM (GPT-4o-mini / Gemini 2.0 Flash) | Performs context-aware, semantically-aware candidate-job fit analysis |
| Output integrity | Schema validation (Pydantic) | Ensures the AI returns a valid, predictable, machine-parseable result |
| HR workflow | Web application, async queue | Delivers results to reviewers and supports their decision-making process |

The pipeline is fully automated — a candidate submits their resume and the system produces a classification, narrative, and structured breakdown without human intervention between submission and review.

---

## References

- Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. *Advances in Neural Information Processing Systems, 30*.
