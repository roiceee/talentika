from django.urls import path
from .views import submit_job_application

urlpatterns = [
    path("applications/submit/", submit_job_application, name="submit_job_application"),
]
