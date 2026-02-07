# Job Profile App

## Overview

The `job_profile` app manages job postings with AI-powered screening capabilities. It supports job categorization, experience level tracking, and customizable AI screening configurations.

## Models

### AIScreeningConfiguration

Configuration for AI-powered candidate screening.

**Fields:**

- `id` (UUID) - Primary key
- `title` (CharField) - Configuration name
- `description` (TextField) - Detailed description
- `created_at`, `updated_at` - Timestamps

### JobCategory

Categories for organizing job profiles (e.g., Software Engineering, Marketing).

**Fields:**

- `id` (UUID) - Primary key
- `title` (CharField, unique) - Category name
- `created_at`, `updated_at` - Timestamps

### ExperienceLevel

Experience level requirements for jobs (e.g., Entry Level, Senior).

**Fields:**

- `id` (UUID) - Primary key
- `title` (CharField, unique) - Level name
- `created_at`, `updated_at` - Timestamps

### JobProfile

Main model representing a job posting. Each job profile belongs to an organization and is created by a user.

**Fields:**

- `id` (UUID) - Primary key
- `organization` (ForeignKey, required) - Organization that owns this job profile
- `created_by` (ForeignKey, required) - User who created this job profile
- `title` (CharField) - Job title
- `category` (ForeignKey) - JobCategory reference
- `employment_type` (CharField) - Enum: full_time, part_time, contract, internship, freelance, not_applicable
- `experience_level` (ForeignKey) - ExperienceLevel reference
- `description` (TextField) - Job description
- `requirements` (ArrayField) - Array of requirement strings
- `skills` (JSONField) - Array of {skill: string, is_required: boolean} objects
- `ai_screening_configuration` (ForeignKey, nullable) - AI screening config
- `created_at`, `updated_at` - Timestamps

**Relationships:**

- Many-to-one with Organization (required): Each job profile belongs to one organization, an organization can have many job profiles
- Many-to-one with User (required): Each job profile is created by one user, a user can create many job profiles

## Seeding Data

The app includes a management command to seed initial data:

```bash
uv run python manage.py seed_job_data
```

This creates:

- **15 Job Categories**: Software Engineering, Data Science, Marketing, etc.
- **6 Experience Levels**: Internship through Executive/C-Level
- **3 AI Screening Configurations**:
  - Strict, Exact Matches Only
  - Balanced, Allow Similar Skills
  - Flexible, Consider Potential

## Skills Field Format

The `skills` field uses JSON format:

```json
[
  { "skill": "Python", "is_required": true },
  { "skill": "Django", "is_required": true },
  { "skill": "PostgreSQL", "is_required": false }
]
```

## Requirements Field Format

The `requirements` field uses PostgreSQL ArrayField:

```python
requirements = [
    "Bachelor's degree in Computer Science or related field",
    "3+ years of experience with Django",
    "Strong problem-solving skills"
]
```

## Admin Interface

All models are registered in Django admin with:

- Search functionality
- Filtering options
- Autocomplete fields for foreign keys

## Database Tables

- `ai_screening_configurations`
- `job_categories`
- `experience_levels`
- `job_profiles`

## API Endpoints

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Reference Data Endpoints

These endpoints provide data needed for creating job profiles:

#### Get Job Categories

```
GET /api/job-profiles/job-categories/
```

Returns all job categories for dropdown selection.

#### Get Experience Levels

```
GET /api/job-profiles/experience-levels/
```

Returns all experience levels for dropdown selection.

#### Get AI Screening Configurations

```
GET /api/job-profiles/ai-screening-configs/
```

Returns all AI screening configurations for dropdown selection.

### Job Profile Endpoints

#### Create Job Profile

```
POST /api/job-profiles/create/
```

**Permission**: User must be an admin of the specified organization.

**Request Body**:

```json
{
  "title": "Senior Backend Developer",
  "organization": "org-uuid-here",
  "category": "category-uuid-here",
  "employment_type": "full_time",
  "experience_level": "experience-level-uuid-here",
  "description": "We are looking for an experienced backend developer...",
  "requirements": [
    "5+ years of Python experience",
    "Strong understanding of Django",
    "Experience with PostgreSQL"
  ],
  "skills": [
    { "skill": "Python", "is_required": true },
    { "skill": "Django", "is_required": true },
    { "skill": "Docker", "is_required": false }
  ],
  "ai_screening_configuration": "config-uuid-here"
}
```

**Response**: Full job profile details with status 201.

#### List Organization Job Profiles

```
GET /api/organizations/<org_id>/job-profiles/
```

**Permission**: User must be a member of the organization.

Returns a list of job profiles for the specified organization with preview information (id, title, category, employment type, etc.).

#### Get Job Profile Details

```
GET /api/job-profiles/<job_id>/
```

**Permission**: User must be a member of the organization that owns the job profile.

Returns complete job profile information including description, requirements, skills, and AI screening configuration.

#### Update Job Profile

```
PATCH /api/job-profiles/<job_id>/update/
```

**Permission**: User must be an admin of the organization that owns the job profile.

Supports partial updates - only include fields you want to change.

**Request Body** (all fields optional):

```json
{
  "title": "Updated Job Title",
  "description": "Updated description...",
  "requirements": ["Updated requirement 1", "Updated requirement 2"],
  "skills": [
    { "skill": "Python", "is_required": true },
    { "skill": "Kubernetes", "is_required": false }
  ],
  "employment_type": "contract",
  "category": "new-category-uuid",
  "experience_level": "new-experience-level-uuid",
  "ai_screening_configuration": "new-config-uuid"
}
```

**Response**: Full updated job profile details with status 200.

**Note**: If changing the organization field, you must be an admin of both the current and new organization.

## Example Usage

### 1. Get Reference Data

```bash
# Get categories
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/job-profiles/job-categories/

# Get experience levels
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/job-profiles/experience-levels/

# Get AI configs
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/job-profiles/ai-screening-configs/
```

### 2. Create a Job Profile

```bash
curl -X POST http://localhost:8000/api/job-profiles/create/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Backend Developer",
    "organization": "<org-uuid>",
    "category": "<category-uuid>",
    "employment_type": "full_time",
    "experience_level": "<experience-uuid>",
    "description": "Looking for senior developer...",
    "requirements": ["5+ years Python", "Django expert"],
    "skills": [
      {"skill": "Python", "is_required": true},
      {"skill": "Django", "is_required": true}
    ]
  }'
```

### 3. List Organization Jobs

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/organizations/<org-uuid>/job-profiles/
```

### 4. Get Job Details

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/job-profiles/<job-uuid>/
```

### 5. Update Job Profile

```bash
curl -X PATCH http://localhost:8000/api/job-profiles/<job-uuid>/update/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Job Title",
    "description": "Updated description",
    "requirements": ["New requirement 1", "New requirement 2"],
    "skills": [
      {"skill": "Python", "is_required": true},
      {"skill": "Kubernetes", "is_required": false}
    ]
  }'
```

curl -H "Authorization: Bearer <token>" \
 http://localhost:8000/api/job-profiles/<job-uuid>/

```

```
