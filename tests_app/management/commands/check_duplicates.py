import re

from django.core.management.base import BaseCommand
from django.db.models import Count

from tests_app.models import DiagnosticTest


class Command(BaseCommand):
    help = "READ-ONLY check for exact duplicate test names."

    def normalize_name(self, name):
        return re.sub(
            r"\s+",
            " ",
            name.strip().lower()
        )

    def handle(self, *args, **options):

        all_tests = DiagnosticTest.objects.all().only(
            "id",
            "name",
            "test_code"
        )

        names = {}

        for test in all_tests:
            normalized = self.normalize_name(test.name)

            if normalized not in names:
                names[normalized] = []

            names[normalized].append(test)

        duplicates = {
            name: tests
            for name, tests in names.items()
            if len(tests) > 1
        }

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "========== DUPLICATE CHECK =========="
            )
        )

        self.stdout.write(
            f"Total tests checked: {all_tests.count()}"
        )

        self.stdout.write(
            f"Duplicate name groups found: {len(duplicates)}"
        )

        self.stdout.write("")

        if not duplicates:
            self.stdout.write(
                self.style.SUCCESS(
                    "No exact duplicate test names found."
                )
            )
            return

        for normalized_name, tests in duplicates.items():

            self.stdout.write(
                self.style.WARNING(
                    f"\nDUPLICATE: {normalized_name}"
                )
            )

            for test in tests:
                self.stdout.write(
                    f"  ID={test.id} | "
                    f"Code={test.test_code} | "
                    f"Name={test.name}"
                )