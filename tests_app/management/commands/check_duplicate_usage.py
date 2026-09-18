import re

from django.core.management.base import BaseCommand

from tests_app.models import DiagnosticTest
from appointments.models import Appointment
from packages.models import HealthPackage
from reports.models import Report


class Command(BaseCommand):
    help = (
        "READ-ONLY: checks whether XL-imported duplicate tests "
        "are referenced by appointments, packages, or reports."
    )

    def normalize_name(self, name):
        return re.sub(r"\s+", " ", name.strip().lower())

    def handle(self, *args, **options):

        # Build a set of names belonging to older, non-XL tests
        old_names = set()

        for test in DiagnosticTest.objects.exclude(
            test_code__startswith="XL-"
        ).only("name"):

            old_names.add(self.normalize_name(test.name))

        # Find XL tests whose names already exist in old tests
        duplicate_xl_tests = []

        for test in DiagnosticTest.objects.filter(
            test_code__startswith="XL-"
        ).only("id", "name", "test_code"):

            if self.normalize_name(test.name) in old_names:
                duplicate_xl_tests.append(test)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "===== DUPLICATE USAGE CHECK ====="
            )
        )

        self.stdout.write(
            f"XL duplicate tests found: {len(duplicate_xl_tests)}"
        )

        used_count = 0
        unused_count = 0

        for test in duplicate_xl_tests:

            # Check Appointment.tests ManyToMany relationship
            appointment_count = Appointment.objects.filter(
                tests=test
            ).count()

            # Check Package.tests_included ManyToMany relationship
            package_count = HealthPackage.objects.filter(
                tests_included=test
            ).count()

            # Check Report.test ForeignKey relationship
            report_count = Report.objects.filter(
                test=test
            ).count()

            total_usage = (
                appointment_count
                + package_count
                + report_count
            )

            if total_usage > 0:

                used_count += 1

                self.stdout.write(
                    self.style.WARNING(
                        f"\nIN USE - DO NOT DELETE:"
                        f"\n  ID={test.id}"
                        f"\n  Code={test.test_code}"
                        f"\n  Name={test.name}"
                        f"\n  Appointments: {appointment_count}"
                        f"\n  Packages: {package_count}"
                        f"\n  Reports: {report_count}"
                    )
                )

            else:

                unused_count += 1

                self.stdout.write(
                    f"\nUNUSED:"
                    f"\n  ID={test.id}"
                    f"\n  Code={test.test_code}"
                    f"\n  Name={test.name}"
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "===== SUMMARY ====="
            )
        )

        self.stdout.write(
            f"Duplicate XL tests currently IN USE: {used_count}"
        )

        self.stdout.write(
            f"Duplicate XL tests currently UNUSED: {unused_count}"
        )

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "READ-ONLY CHECK COMPLETE. "
                "Nothing was deleted or modified."
            )
        )