"""
Management command: check_services

Verifies connectivity to all external services required at startup:
  - PostgreSQL (database)
  - Redis (RQ queue broker)

Exits with code 1 if any service is unreachable, causing the entrypoint
to abort and the container to stop before attempting to serve traffic.
"""

import sys

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check connectivity to all external services (PostgreSQL, Redis). Exit 1 if any fail."

    def handle(self, *args, **options):
        failed = False

        # ------------------------------------------------------------------
        # 1. PostgreSQL
        # ------------------------------------------------------------------
        self.stdout.write("Checking PostgreSQL...")
        try:
            from django.db import connection

            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS("  PostgreSQL: OK"))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  PostgreSQL: FAILED — {exc}"))
            failed = True

        # ------------------------------------------------------------------
        # 2. Redis
        # ------------------------------------------------------------------
        self.stdout.write("Checking Redis...")
        try:
            import redis
            from django.conf import settings
            import ssl as ssl_module

            ssl_enabled = getattr(settings, "REDIS_SSL", False)
            if ssl_enabled:
                r = redis.Redis.from_url(
                    settings.REDIS_URL,
                    ssl_cert_reqs=ssl_module.CERT_NONE,
                )
            else:
                r = redis.Redis.from_url(settings.REDIS_URL)

            r.ping()
            self.stdout.write(self.style.SUCCESS("  Redis: OK"))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"  Redis: FAILED — {exc}"))
            failed = True

        # ------------------------------------------------------------------
        # Result
        # ------------------------------------------------------------------
        if failed:
            self.stderr.write(
                self.style.ERROR(
                    "\nOne or more required services are unavailable. Aborting startup."
                )
            )
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS("\nAll services are healthy."))
