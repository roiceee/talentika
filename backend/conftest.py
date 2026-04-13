import logging

# Silence Django request logs so test output stays clean
logging.getLogger("django.request").setLevel(logging.CRITICAL)
logging.getLogger("job_applications.views").setLevel(logging.CRITICAL)
logging.getLogger("job_application_analysis.workers").setLevel(logging.CRITICAL)
