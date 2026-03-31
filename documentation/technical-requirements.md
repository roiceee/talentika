# Technical Requirements

## Software Requirements

- **Python 3.13** - The backend is implemented in Python 3.13, a high-level, general-purpose programming language known for its readability and broad ecosystem. Python serves as the runtime for the Django REST API, RQ background workers, OCR processing, and AI integration logic.

- **Django 6** - A high-level Python web framework that encourages rapid development and clean, pragmatic design. Django provides the ORM, authentication system, admin interface, and application structure for the Talentika backend. Django REST Framework (DRF) is used on top of it to expose RESTful API endpoints consumed by the frontend.

- **Next.js 16** - A React-based full-stack web framework used for the Talentika frontend. It functions as a Backend-for-Frontend (BFF), handling server-side rendering, routing, and proxying all API requests to the Django backend. All browser-to-server communication passes through Next.js BFF routes, which enforce CSRF validation and JWT injection before forwarding requests.

- **React 19** - A JavaScript library for building user interfaces. React powers the component-based UI of the Talentika frontend, enabling dynamic and responsive views for job profile management, application review, and AI analysis results.

- **TypeScript** - A statically typed superset of JavaScript used throughout the frontend codebase. TypeScript provides compile-time type safety, improving code maintainability and reducing runtime errors in the Next.js application.

- **Tailwind CSS** - A utility-first CSS framework used to style the Talentika frontend. Tailwind enables rapid UI development by applying low-level utility classes directly in markup, without writing custom CSS.

- **PostgreSQL 16** - An open-source object-relational database management system used as the primary data store for Talentika. PostgreSQL stores all application data including users, organizations, job profiles, applications, and AI analysis results. It is accessed via Django's ORM using the psycopg2 adapter.

- **Redis** - An open-source, in-memory data structure store used as the message broker for Talentika's asynchronous task queues. Redis backs the RQ (Redis Queue) workers that process OCR extraction and AI analysis jobs outside of the HTTP request cycle.

- **RQ (Redis Queue)** - A simple Python library for queueing background jobs backed by Redis. Talentika uses three separate RQ queues: `ocr_queue` for resume text extraction, `ai_queue` for OpenAI analysis, and `export_queue` for generating application exports.

- **Tesseract OCR (pytesseract / pdf2image)** - An open-source optical character recognition engine used to extract text from uploaded resume files. PDF pages are converted to images via pdf2image and then processed by pytesseract, producing the machine-readable resume text that is forwarded to the AI analysis step.

- **OpenAI API (gpt-4o-mini)** - The AI provider used for resume screening and candidate classification. The backend sends structured prompts containing the job description, qualifications, and extracted resume text to the OpenAI API, which returns a validated structured output including a candidate summary, key skills, notable traits, and a fit classification (Suitable / Potentially Suitable / Unsuitable).

- **Docker** - A platform for building, shipping, and running applications in containers. The backend and all worker services are containerized as Docker images published to Docker Hub, enabling consistent deployments across environments. Docker Compose is used locally to run PostgreSQL and Redis during development.

- **Terraform** - An infrastructure-as-code tool used to provision and manage Talentika's cloud resources. Terraform configurations define the AWS S3 bucket, IAM policies, DigitalOcean managed databases, and DigitalOcean App Platform services in a reproducible and version-controlled manner.

- **uv** - A fast Python package and project manager used to manage the backend's dependencies and virtual environment. It replaces pip and virtualenv, providing significantly faster dependency resolution and installation.

- **pnpm** - A fast, disk-efficient Node.js package manager used to manage the frontend's dependencies. pnpm is also used to run the openapi-ts code generation script that regenerates the type-safe API client from the backend's Swagger schema.

## Hardware Requirements

Talentika is deployed on cloud infrastructure and does not require dedicated on-premise hardware. The following describes the infrastructure used to run the system in production.

- **AWS S3** - Amazon Simple Storage Service is used as the file storage backend for all uploaded resume files and application attachments in production. S3 buckets are provisioned per environment (development and production) with corresponding IAM users and access policies managed via Terraform.

- **DigitalOcean App Platform** - A platform-as-a-service (PaaS) used to host the Django backend web server and all background worker processes. The backend is deployed as a containerized web service, alongside three separate worker dyno instances for the OCR queue, AI analysis queue, and export queue. Each component runs on a `apps-s-1vcpu-1gb` instance (1 vCPU, 1 GB RAM) in the Singapore (`sgp`) region.

- **DigitalOcean Managed PostgreSQL** - A fully managed PostgreSQL 16 database cluster hosted on DigitalOcean. It handles all persistent application data for the production environment and is provisioned in the same region as the App Platform services to minimize latency.

- **DigitalOcean Managed Redis (Valkey)** - A fully managed Redis-compatible key-value store (Valkey engine) used as the RQ message broker in production. It is provisioned on a `db-s-1vcpu-1gb` instance alongside the PostgreSQL cluster.

- **Vercel** - A cloud platform used to host the Next.js frontend. Vercel provides automatic deployments, edge network distribution, and serverless function execution for the BFF API routes, ensuring low-latency responses for end users.
