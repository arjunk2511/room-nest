import sys

from django.core.management.base import BaseCommand
from django.core.exceptions import ImproperlyConfigured

from roomnest.production_safety import run_production_verification


class Command(BaseCommand):
    help = 'Verify production readiness without destructive database operations.'

    def handle(self, *args, **options):
        try:
            result = run_production_verification()
        except Exception as exc:
            self.stderr.write(f'PRODUCTION READINESS FAILED: {exc}\n')
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS('Production readiness checks passed.'))
        self.stdout.write(f"Last migration: {result['last_migration']}")
        self.stdout.write(f"Counts: {result['counts']}")
        self.stdout.write(f"Cloud status: {result['cloud_message']}")
        self.stdout.write(f"Logs written to: {result['log_path']}")
