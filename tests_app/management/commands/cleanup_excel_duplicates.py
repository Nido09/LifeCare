import re

from django.core.management.base import BaseCommand
from django.db import transaction

from tests_app.models import DiagnosticTest
from appointments.models import Appointment
from packages.models import HealthPackage
from reports.models import Report


class Command(BaseCommand):
    help = (
        "Safely removes only unused XL-imported tests that have the same "
        "normalized name as an older non-XL test."
    )

    def normalize_name(self, name):
        return re.sub(r"\s+", " ", name.strip().lower())

    @transaction.atomic
    def handle(self, *args, **options):

        # Build names of all older/original tests
        old_names = set()

        for test in DiagnosticTest.objects.exclude(
            test_code__startswith="XL-"
        ).only("name"):

            old_names.add(
                self.normalize_name(test.name)
            )

        deleted_count = 0
        skipped_in_use = 0

        xl_tests = DiagnosticTest.objects.filter(
            test_code__startswith="XL-"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "===== CLEANING EXCEL DUPLICATES ====="
            )
        )

        for test in xl_tests:

            normalized_name = self.normalize_name(test.name)

            # Only consider XL tests that duplicate an older test
            if normalized_name not in old_names:
                continue

            # Safety check again before deleting
            appointment_count = Appointment.objects.filter(
                tests=test
            ).count()

            package_count = HealthPackage.objects.filter(
                tests_included=test
            ).count()

            report_count = Report.objects.filter(
                test=test
            ).count()

            if (
                appointment_count > 0
                or package_count > 0
                or report_count > 0
            ):

                skipped_in_use += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"SKIPPED (IN USE): "
                        f"{test.test_code} | {test.name}"
                    )
                )

                continue

            # Safe deletion
            self.stdout.write(
                f"DELETING: "
                f"{test.id} | "
                f"{test.test_code} | "
                f"{test.name}"
            )

            test.delete()

            deleted_count += 1

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "===== CLEANUP COMPLETED ====="
            )
        )

        self.stdout.write(
            f"XL duplicate tests deleted: {deleted_count}"
        )

        self.stdout.write(
            f"Tests skipped because they are in use: "
            f"{skipped_in_use}"
        )

        self.stdout.write(
            f"Final DiagnosticTest count: "
            f"{DiagnosticTest.objects.count()}"
        )