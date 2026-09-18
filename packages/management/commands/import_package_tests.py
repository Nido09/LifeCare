from django.core.management.base import BaseCommand
from django.db import transaction

from packages.models import HealthPackage
from tests_app.models import DiagnosticTest


# ==========================================================
# PACKAGE NAME -> DATABASE TEST NAME MAPPING
# ==========================================================

PACKAGE_TESTS = {

    # ------------------------------------------------------
    # SWASTHYA MITRA ADVANCE
    # ------------------------------------------------------
    "Swasthya Mitra ADVANCE": [
        "ESR Automated",
        "Blood Glucose Fasting",
        "Liver F. Test",
        "Thyroid Profile-I [T3T4TSH]",
        "HbA1c (Glycated hemoglobin)",
        "Complete Blood Count (CBC)",
        "Lipid Profile",
        "Urine R/M (Urine Analysis)",
    ],


    # ------------------------------------------------------
    # SWASTHYA MITRA PREMIUM
    # ------------------------------------------------------
    "Swasthya Mitra PREMIUM": [
        "ESR Automated",
        "Blood Glucose Fasting",
        "Vitamin B12 (Cynocobalamin)",
        "Vitamin D Total-25 Hydroxy",
        "Liver F. Test",
        "Thyroid Profile-I [T3T4TSH]",
        "Iron Panel with Ferritin",
        "HbA1c (Glycated hemoglobin)",
        "Complete Blood Count (CBC)",
        "Lipid Profile",
        "Urine R/M (Urine Analysis)",
    ],


    # ------------------------------------------------------
    # SWASTHYA MITRA BASIC
    # ------------------------------------------------------
    "Swasthya Mitra BASIC": [
        "Blood Glucose Fasting",
        "Liver F. Test",
        "Thyroid Profile-I [T3T4TSH]",
        "Lipid Profile",
        "Urine R/M (Urine Analysis)",
    ],


    # ------------------------------------------------------
    # SWASTHYA MITRA SUPER
    # ------------------------------------------------------
    "Swasthya Mitra Super": [
        "RA Test Rheumatoid Arthritis Factor, Quantitative",
        "CRP (C Reactive Protein) Quantitative, Serum",
        "Blood Glucose Fasting",
        "Vitamin B12 (Cynocobalamin)",
        "Vitamin D Total-25 Hydroxy",
        "ESR Automated",
        "Liver F. Test",
        "Complete Blood Count (CBC)",
        "Thyroid Profile-I [T3T4TSH]",
        "HbA1c (Glycated hemoglobin)",
        "Urine R/M (Urine Analysis)",
    ],


    # ------------------------------------------------------
    # PDF NAME:
    # RPL ANC Profile - 1
    #
    # DATABASE PACKAGE NAME:
    # Swasthya Mitra Antenatal Profile (Random Sugar)
    # ------------------------------------------------------
    "Swasthya Mitra Antenatal Profile (Random Sugar)": [
        "Anti HCV Antibody (qualitative)",
        "ABO Group & Rh Type (Blood Group)",
        "Complete Blood Count (CBC)",
        "ESR Automated",
        "Hepatitis B Virus (HBV) HbsAg-Quantitative Surface Antigen",
        "HIV 1&2 Antibodies",
        "Random Blood Sugar",
        "RPR",
        "TSH Ultra - Sensitive",
        "Urine R/M (Urine Analysis)",
    ],
}


# ==========================================================
# FIND TEST SAFELY
# ==========================================================

def get_test(test_name):

    matches = DiagnosticTest.objects.filter(
        name__iexact=test_name
    ).order_by("id")

    if matches.exists():

        # Use first record if duplicate test names exist
        return matches.first(), matches.count()

    return None, 0


# ==========================================================
# MANAGEMENT COMMAND
# ==========================================================

class Command(BaseCommand):

    help = (
        "Safely link existing diagnostic tests "
        "to existing health packages"
    )


    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write("\n")

        self.stdout.write(
            self.style.WARNING(
                "Starting package-test linking..."
            )
        )

        self.stdout.write(
            f"Total diagnostic tests: "
            f"{DiagnosticTest.objects.count()}"
        )

        self.stdout.write(
            f"Total packages: "
            f"{HealthPackage.objects.count()}\n"
        )


        # ==================================================
        # LOOP THROUGH PACKAGES
        # ==================================================

        for package_name, test_names in PACKAGE_TESTS.items():

            package = HealthPackage.objects.filter(
                name__iexact=package_name
            ).first()


            # ----------------------------------------------
            # PACKAGE NOT FOUND
            # ----------------------------------------------

            if not package:

                self.stdout.write(

                    self.style.ERROR(
                        f"\n✗ PACKAGE NOT FOUND: "
                        f"{package_name}"
                    )
                )

                continue


            # ----------------------------------------------
            # PACKAGE HEADER
            # ----------------------------------------------

            self.stdout.write(

                self.style.SUCCESS(

                    f"\n{'=' * 60}\n"
                    f"PACKAGE: {package.name}\n"
                    f"{'=' * 60}"
                )
            )


            linked_count = 0
            already_linked_count = 0
            duplicate_count = 0
            missing_tests = []


            # ==============================================
            # LOOP THROUGH TESTS
            # ==============================================

            for test_name in test_names:


                test, duplicate_matches = get_test(
                    test_name
                )


                # ------------------------------------------
                # TEST NOT FOUND
                # ------------------------------------------

                if not test:

                    missing_tests.append(
                        test_name
                    )

                    self.stdout.write(

                        self.style.WARNING(
                            f"NOT FOUND: "
                            f"{test_name}"
                        )
                    )

                    continue


                # ------------------------------------------
                # DUPLICATE TEST NAMES
                # ------------------------------------------

                if duplicate_matches > 1:

                    duplicate_count += 1

                    self.stdout.write(

                        self.style.WARNING(

                            f"DUPLICATE NAME FOUND "
                            f"({duplicate_matches} records): "
                            f"{test_name}"
                        )
                    )


                # ------------------------------------------
                # CHECK IF ALREADY LINKED
                # ------------------------------------------

                if package.tests_included.filter(
                    id=test.id
                ).exists():

                    already_linked_count += 1

                    self.stdout.write(
                        f"ALREADY LINKED: "
                        f"{test.name}"
                    )


                # ------------------------------------------
                # ADD TEST TO PACKAGE
                # ------------------------------------------

                else:

                    package.tests_included.add(
                        test
                    )

                    linked_count += 1

                    self.stdout.write(

                        self.style.SUCCESS(
                            f"✓ LINKED: "
                            f"{test.name}"
                        )
                    )


            # ==============================================
            # PACKAGE SUMMARY
            # ==============================================

            self.stdout.write(
                "\nSUMMARY"
            )

            self.stdout.write(
                f"New tests linked: "
                f"{linked_count}"
            )

            self.stdout.write(
                f"Already linked: "
                f"{already_linked_count}"
            )

            self.stdout.write(
                f"Total tests currently "
                f"in package: "
                f"{package.tests_included.count()}"
            )


            # ----------------------------------------------
            # DUPLICATE SUMMARY
            # ----------------------------------------------

            if duplicate_count:

                self.stdout.write(

                    self.style.WARNING(

                        f"Duplicate-name matches handled: "
                        f"{duplicate_count}"
                    )
                )


            # ----------------------------------------------
            # MISSING TEST SUMMARY
            # ----------------------------------------------

            if missing_tests:

                self.stdout.write(

                    self.style.WARNING(
                        "\nStill not found:"
                    )
                )

                for missing in missing_tests:

                    self.stdout.write(
                        f"  - {missing}"
                    )


        # ==================================================
        # FINAL SUCCESS MESSAGE
        # ==================================================

        self.stdout.write("\n")

        self.stdout.write(

            self.style.SUCCESS(
                "✓ PACKAGE TEST LINKING COMPLETED"
            )
        )

        self.stdout.write("\n")