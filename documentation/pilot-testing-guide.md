# TALENTIKA — Pilot Testing: Interviewer Guide

**Format:** One-on-one assisted demo | **Estimated Duration:** 45–60 minutes per respondent

---

## Pre-Session Checklist

_(Complete before the HR person arrives)_

- [ ] System is running and accessible at the demo URL
- [ ] All 5 job profiles have 30 applicants each with AI analysis status **DONE**
- [ ] Assign one job profile + one login to this respondent (see table below)
- [ ] Browser is open at the login page, credentials given to HR
- [ ] Questionnaire ready for the respondent to fill out at the end

**Respondent Assignment Table**

| Respondent # | Login                             | Role      | Assigned Job Profile            |
| ------------ | --------------------------------- | --------- | ------------------------------- |
| 1            | tester1@example.com / password123 | Org Admin | Accountant III                  |
| 2            | tester2@example.com / password123 | Member    | Staff Nurse – ICU               |
| 3            | tester3@example.com / password123 | Member    | Barista                         |
| 4            | tester4@example.com / password123 | Member    | Clinical Coder                  |
| 5            | tester5@example.com / password123 | Member    | Customer Service Representative |

---

## Part 0 — Welcome & Section I

Make the HR read the data privacy statement and make sure they agree.

---

## Part 1 — Guided Demo: Functional Capabilities _(~25 min)_

_Cover each item in Section II. Walk the respondent through each area in order. Where indicated, hand over control so they perform the action themselves._

---

### 1.1 · Multi-tenant Organization Management

**You demonstrate:**

- Log in with the assigned credentials
- Point out the organization name **"test"** in the dashboard header/sidebar
- Say: _"Each organization on the platform operates independently — their job profiles, applicants, and data are completely separate from other organizations."_
- Navigate to **Organization Settings → Members** and show the list of members with their roles (Admin, Member)
- Make them create a new organization and then navigate to job profiles, and members. It should have no data yet.

**Prompt the respondent:**

> "Each organization has their own data, and can be viewed only when you are a member of that organization"

_Section II items covered: Multi-tenant management, Member management_

---

### 1.2 · Job Profile Management

**Hand over control to the respondent:**

- Navigate to **Job Profiles**
- Open the assigned job profile (see their assignment from the table above)
- Ask them to read through the profile: title, description, qualifications, screening questions
- Make them create a new sample profile if possible

**Say:**

> "This is a fully configured job profile with required and preferred qualifications already set. In real use, HR would create this profile before opening applications."

_Section II item covered: Create and manage job profiles_

---

### 1.3 · Application Submission — Generating the Link

**You demonstrate** _(still on the job profile page)_:

- Find and click the **"Application Link"** or **"Share"** button/section
- Show the unique application URL that applicants would receive.
- Open the url in the browser

**Say:**

> "After creating a job profile, HR generates this link and shares it — via email, job boards, or social media. Applicants fill out a form and attach their resume through this link."

_Section II items covered: Generate and share application link_

---

### 1.4 · Receiving and Viewing Applications

**Hand over control to the respondent:**

- Submit an application from the form (can be any pdf for the resume)
- Show the full list of 30 applicants on this job profile
- Ask them to scroll through and notice the applicant cards (name, status, AI score/badge)

**Prompt:**

> "These are all the applications received for this role. Notice the status and score information visible right from the list — you don't need to open each resume to get an initial picture."

_Section II item covered: Receive and view submitted applications_

### 1.5 · Bulk Resume Upload

**You demonstrate:**

- Navigate to the **Applications** list for this job profile
- Show the **"Bulk Upload"** or **"Upload Resumes"** feature
- Upload a couple of resume data on your device.

**Say:**

> "HR can also upload multiple resumes at once — useful when receiving applications from email or walk-ins. The system processes them all automatically."

_Section II item covered: Upload multiple resume PDFs_

---

### 1.6 · AI Resume Analysis

**Hand over control to the respondent:**

- Ask them to click on any applicant from the list to open their profile
- Walk them through the AI analysis panel:
  - Overall match score
  - Qualification breakdown (met vs. not met)
  - Strengths and concerns
  - AI-generated summary / recommendation

**Say:**

> "The system reads the resume using OCR and sends it to an AI model. The AI evaluates the candidate against the job's qualifications and screening questions, then produces this structured report."

**Repeat:** Ask them to open 2–3 more applicants so they get a feel for the variation in analysis.

_Section II items covered: View AI-generated insights, HR review and decision support_

---

### 1.7 · Application Status Management

**Hand over control to the respondent:**

- On any open applicant profile, find the **Status** dropdown or update control
- Ask them to change the status (e.g., from `PENDING` to `SHORTLISTED` or `REJECTED`)

**Say:**

> "You remain in control of all hiring decisions. The system supports your process but never automatically accepts or rejects anyone."

_Section II item covered: Update and manage application statuses_

---

### 1.8 · Candidate Shortlisting

**Hand over control to the respondent:**

- Ask them to go back to the applicant list and use any available filters, sort options, or score ranking to identify who they would consider for shortlisting
- Ask them to shortlist at least one candidate

**Prompt:**

> "Using the AI scores and insights you've seen, who would you bring forward? Try using the filter or sort features to help narrow down."

_Section II item covered: Shortlist candidates with AI-generated insights_

---

## Part 2 — Non-Functional Walkthrough _(~5 min)_

_Point these out conversationally while still in the system. Do not make this feel like a lecture._

| Non-Functional Area | What to show / say                                                                                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Security**        | "You had to log in with your account to access anything — applicant data is protected and only accessible to authenticated org members."                                                               |
| **Privacy**         | "The system is designed so that applicant data can be managed and deleted by the organization. Nothing is shared outside the organization's workspace."                                                |
| **Performance**     | Point to the AI analysis results already loaded: "These analyses were generated automatically after each resume was uploaded. The system processes them in the background so HR doesn't have to wait." |
| **Scalability**     | "This organization has 5 job profiles each with 30 applicants — in production, it's designed to handle many organizations, jobs, and applicants without slowing down."                                 |
| **Reliability**     | "Even if the AI service had a delay or outage, the application submission itself is always stored first. AI analysis catches up once the service recovers — no application is ever lost."              |

---

## Part 3 — Independent Exploration for Section IV _(~15 min)_

_This is the key part for the System User Evaluation section. Step back and let the respondent explore on their own._

**Say to the respondent:**

> "Now I'd like you to use the system on your own for a few minutes. You're evaluating for the **[assigned job title]** position. You have 30 applicants. Using the AI insights and whatever tools the system provides, try to identify your top candidates. There's no right or wrong answer — just use it the way you naturally would."

**Interviewer checklist while observing (do not intervene unless they are stuck):**

- [ ] Do they sort or filter by score?
- [ ] Do they read the full AI analysis or just the score?
- [ ] Do they update statuses as they go?
- [ ] Do they seem to trust or question the AI insights?
- [ ] Do they compare candidates side by side or evaluate one at a time?

---

## Part 4 — Questionnaire Completion _(~10 min)_

**Interviewer note:** Be available for clarification but do not influence their ratings. If they ask what a question means, rephrase it neutrally. Do not suggest a rating.

**After they finish:**

- Collect the questionnaire
- Thank the respondent
- Remind them that responses are confidential and used for academic purposes only

---

## Quick Reference: Section ↔ Demo Coverage

| Questionnaire Section               | Covered In                                       |
| ----------------------------------- | ------------------------------------------------ |
| Section I — Respondent Info         | Part 0                                           |
| Section II — Functional Capability  | Parts 1.1 – 1.8                                  |
| Section III — Non-Functional        | Part 2                                           |
| Section IV — System User Evaluation | Part 3 (independent exploration) + questionnaire |

---

## If Something Goes Wrong

| Situation                                      | What to do                                                                    |
| ---------------------------------------------- | ----------------------------------------------------------------------------- |
| AI analysis not yet `DONE` for some applicants | Skip that applicant, pick one with `DONE` status                              |
| Respondent can't log in                        | Double-check the assigned credentials; use the table above                    |
| Page loads slowly                              | Note it honestly — don't hide it; it's valid feedback                         |
| Respondent is confused by a UI element         | You may assist with navigation, but let them interpret the content themselves |
