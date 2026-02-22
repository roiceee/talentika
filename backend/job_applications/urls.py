from django.urls import path
from .views import submit_job_application, upload_resume, list_job_applications

urlpatterns = [
    path("applications/submit/", submit_job_application, name="submit_job_application"),
    path("applications/submit/upload/resume/", upload_resume, name="upload_resume"),
    path(
        "organizations/<uuid:org_id>/job-profiles/<uuid:job_profile_id>/applications",
        list_job_applications,
        name="list_job_applications",
    ),
]
