# Business Logic Flows

## User Registration Flow

```mermaid
flowchart TD
    Start([Applicant / Invited User]) --> Register["POST /api/users/register/"]

    Register --> Validate{Validate Input}
    Validate -->|Invalid| Error400["400 Bad Request"]

    Validate -->|Valid| HasToken{invitation_token<br/>provided?}

    HasToken -->|No| CreateUser["Create User Account"]
    CreateUser --> Return201A["201 Created<br/>Standalone user"]

    HasToken -->|Yes| LookupToken["Lookup Invitation by Token"]
    LookupToken --> TokenValid{Token valid?<br/>Not expired?<br/>Email matches?}
    TokenValid -->|No| Error400

    TokenValid -->|Yes| CreateUserInv["Create User Account"]
    CreateUserInv --> CreateMembership["Create OrganizationMembership<br/>with invited role"]
    CreateMembership --> MarkAccepted["Mark Invitation as Accepted"]
    MarkAccepted --> SetDefault["Set org as default<br/>(if user has none)"]
    SetDefault --> Return201B["201 Created<br/>User joined org"]
```

## Invitation Flow (Existing Users)

```mermaid
flowchart TD
    Start([Org Admin]) --> SendInvite["POST /api/organizations/{org_id}/invitations/"]
    SendInvite --> ValidateOrg{Org approved?<br/>User is admin?}
    ValidateOrg -->|No| Error403["403 Forbidden"]
    ValidateOrg -->|Yes| CreateInvitation["Create OrganizationInvitation<br/>(7-day token)"]
    CreateInvitation --> SendEmail["Send Invitation Email<br/>via Gmail SMTP"]
    SendEmail --> Return201["201 Created"]

    Recipient([Invited User]) --> Accept["POST /api/invitations/accept/<br/>{token}"]
    Accept --> CheckToken{Token valid?<br/>Not expired?<br/>Not already accepted?}
    CheckToken -->|No| Error400["400 Bad Request"]
    CheckToken -->|Yes| EmailMatch{Authenticated user's<br/>email matches<br/>invitation email?}
    EmailMatch -->|No| Error400
    EmailMatch -->|Yes| AlreadyMember{Already a member?}
    AlreadyMember -->|Yes| Error400
    AlreadyMember -->|No| JoinOrg["Create OrganizationMembership"]
    JoinOrg --> SetDefault["Set org as default<br/>(if user has none)"]
    SetDefault --> MarkAccepted["Mark Invitation Accepted"]
    MarkAccepted --> Return200["200 OK<br/>Joined organization"]
```

## Organization Creation Flow

```mermaid
flowchart TD
    Start([Authenticated User]) --> Create["POST /api/organizations/"]

    Create --> Validate{Validate Input<br/>name, address}
    Validate -->|Invalid| Error400["400 Bad Request"]

    Validate -->|Valid| CreateOrg["Create Organization<br/>(status: APPROVED)"]
    CreateOrg --> CreateMembership["Create OrganizationMembership<br/>role: ORG_ADMIN"]
    CreateMembership --> HasDefault{User has a<br/>default org?}
    HasDefault -->|No| SetDefault["Set as default organization"]
    HasDefault -->|Yes| Skip["Skip"]
    SetDefault --> Return201["201 Created"]
    Skip --> Return201
```

## Job Profile Creation → Application Submission → Analysis Flow

```mermaid
flowchart TD
    subgraph Job Profile Creation
        Admin([Org Admin]) --> CreateProfile["POST /api/organizations/{org_id}/job-profiles/"]
        CreateProfile --> SaveProfile["Create JobProfile<br/>(title, category, employment type,<br/>experience level, description)"]
        SaveProfile --> AddQuals["Add Qualifications<br/>(skills, experience, education, etc.)"]
        AddQuals --> AddQuestions["Add Questions<br/>(text, MCQ, MCQ single)"]
        AddQuestions --> ProfileReady["Job Profile Active ✓"]
    end

    subgraph Resume Pre-Upload
        Applicant([Applicant]) --> Upload["POST /api/applications/submit/upload/resume/"]
        Upload --> StoreTemp["Store in TemporaryFileUpload<br/>Compute SHA-256 hash<br/>Dedup check"]
        StoreTemp --> ReturnUUID["Return file UUID"]
    end

    subgraph Application Submission
        ReturnUUID --> Submit["POST /api/applications/submit/<br/>(public endpoint, no auth)"]
        ProfileReady -.-> Submit
        Submit --> ValidateApp{Validate:<br/>Profile active?<br/>Required questions answered?}
        ValidateApp -->|Invalid| Error400["400 Bad Request"]
        ValidateApp -->|Valid| CreateApp["Create JobApplication<br/>(status: TO_BE_REVIEWED)"]
        CreateApp --> SaveAnswers["Create QuestionAnswer records"]
        SaveAnswers --> LinkFiles["Link ApplicationAttachments<br/>(from temp uploads)"]
        LinkFiles --> SendConfirm["Send Confirmation Email<br/>to applicant"]
        SendConfirm --> TriggerPipeline["Trigger Analysis Pipeline<br/>(silent fail)"]
    end

    subgraph Analysis Pipeline
        TriggerPipeline --> HasResume{Resume<br/>attached?}
        HasResume -->|No| SkipAnalysis["Skip analysis"]
        HasResume -->|Yes| CreateAnalysis["Create ApplicationAnalysis<br/>(status: UPLOADED)"]
        CreateAnalysis --> EnqueueOCR["Enqueue on ocr_queue<br/>(RQ retry: max 3, 30/60/120s)"]

        subgraph OCR Worker [ocr_queue worker]
            EnqueueOCR --> OCRStart["OCR Worker picks up job"]
            OCRStart --> SetOCRPending["Status → OCR_PENDING"]
            SetOCRPending --> DownloadPDF["Download resume from storage<br/>(S3 or local)"]
            DownloadPDF --> ConvertDocx{DOCX?}
            ConvertDocx -->|Yes| ConvertPDF["Convert to PDF via LibreOffice"]
            ConvertDocx -->|No| ExtractText
            ConvertPDF --> ExtractText["Extract text via Tesseract OCR"]
            ExtractText --> SaveText["Save extracted text<br/>Status → OCR_DONE"]
            SaveText --> EnqueueAI["Enqueue on ai_queue<br/>(no auto-retry)"]
        end

        subgraph AI Worker [ai_queue worker]
            EnqueueAI --> AIStart["AI Worker picks up job"]
            AIStart --> SetAIPending["Status → AI_PENDING"]
            SetAIPending --> CollectContext["Collect job profile data +<br/>qualifications + Q&A pairs"]
            CollectContext --> CallAI["Call OpenAI API<br/>(structured output)"]
            CallAI --> PersistResults["Save: summary, skills,<br/>traits, score_category,<br/>detailed analysis"]
            PersistResults --> Done["Status → DONE"]
        end

        SetOCRPending -->|Any error| OCRAutoRetry{"RQ retries<br/>exhausted?"}
        DownloadPDF -->|Any error| OCRAutoRetry
        ConvertPDF -->|Any error| OCRAutoRetry
        ExtractText -->|Any error| OCRAutoRetry
        OCRAutoRetry -->|No — re-enqueue<br/>w/ backoff| OCRStart
        OCRAutoRetry -->|Yes| FailedOCR["Status → FAILED<br/>error_message saved"]

        SetAIPending -->|Any error| FailedAI["Status → FAILED<br/>error_message saved"]
        CollectContext -->|Any error| FailedAI
        CallAI -->|Any error| FailedAI

        FailedOCR --> ManualRetry["POST /api/applications/{id}/analysis/retry/<br/>Reset → UPLOADED, clear error"]
        FailedAI --> ManualRetry
        ManualRetry --> EnqueueOCR
    end
```

## Shortlisting Flow

```mermaid
flowchart TD
    subgraph Application Review
        Admin([Org Member]) --> ViewApps["GET /api/organizations/{org_id}/<br/>job-profiles/{id}/applications/"]
        ViewApps --> ListApps["List applications with<br/>AI scores & categories"]
    end

    subgraph Score Categories
        Score["AI Score (0-100)"]
        Score --> Excellent["90-100: Excellent"]
        Score --> Good["75-89: Good"]
        Score --> Moderate["40-74: Moderate"]
        Score --> Bad["0-39: Bad"]
    end

    subgraph Status Update
        ListApps --> SelectApp["Select application to review"]
        SelectApp --> ViewDetail["View full analysis:<br/>summary, skills, traits,<br/>strengths, experience,<br/>education, certifications"]
        ViewDetail --> Decision{Admin Decision}

        Decision -->|Shortlist| Shortlist["PATCH status → shortlisted"]
        Decision -->|Reject| Reject["PATCH status → rejected"]
        Decision -->|Mark Reviewed| Review["PATCH status → reviewed"]
    end

    subgraph Status Flow
        direction LR
        TBR["to_be_reviewed"] --> R["reviewed"]
        TBR --> S["shortlisted"]
        TBR --> RJ["rejected"]
        R --> S
        R --> RJ
    end

    subgraph Data Export
        Admin2([Org Member]) --> Export["POST export job<br/>(CSV or XLSX)"]
        Export --> EnqueueExport["Enqueue on export_queue"]
        EnqueueExport --> GenerateFile["Generate file with<br/>application + analysis data"]
        GenerateFile --> StoreFile["Store in S3 / local"]
        StoreFile --> Download["Download export file"]
    end
```
