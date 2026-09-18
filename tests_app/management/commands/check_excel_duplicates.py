import re

from django.core.management.base import BaseCommand

from tests_app.models import DiagnosticTest


class Command(BaseCommand):
    help = (
        "READ-ONLY check: finds newly imported XL- tests "
        "that have the same normalized name as an older non-XL test."
    )

    def normalize_name(self, name):
        return re.sub(
            r"\s+",
            " ",
            name.strip().lower()
        )

    def handle(self, *args, **options):

        old_tests = {}
        xl_tests = []

        for test in DiagnosticTest.objects.all().only(
            "id", "name", "test_code"
        ):

            normalized_name = self.normalize_name(test.name)

            if test.test_code.startswith("XL-"):
                xl_tests.append((test, normalized_name))
            else:
                old_tests.setdefault(
                    normalized_name, []
                ).append(test)

        duplicates = []

        for xl_test, normalized_name in xl_tests:

            if normalized_name in old_tests:

                duplicates.append(
                    (xl_test, old_tests[normalized_name])
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "===== EXCEL IMPORT DUPLICATE REPORT ====="
            )
        )

        self.stdout.write(
            f"XL imported tests checked: {len(xl_tests)}"
        )

        self.stdout.write(
            f"XL tests matching an older test by exact name: "
            f"{len(duplicates)}"
        )

        if not duplicates:

            self.stdout.write(
                self.style.SUCCESS(
                    "\nNo Excel-imported duplicates found."
                )
            )
            return

        for xl_test, existing_tests in duplicates:

            self.stdout.write(
                self.style.WARNING(
                    f"\nNEW XL TEST: "
                    f"ID={xl_test.id} | "
                    f"Code={xl_test.test_code} | "
                    f"Name={xl_test.name}"
                )
            )

            for old_test in existing_tests:

                self.stdout.write(
                    f"   OLD TEST: "
                    f"ID={old_test.id} | "
                    f"Code={old_test.test_code} | "
                    f"Name={old_test.name}"
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "READ-ONLY REPORT: Nothing was deleted or modified."
            )
        )