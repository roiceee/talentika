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
- **5 AI Screening Configurations**: Various screening templates

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
