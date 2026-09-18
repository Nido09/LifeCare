from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from packages.models import HealthPackage
from tests_app.models import DiagnosticTest


class Command(BaseCommand):
    help = "Keep only the 6 packages present in the PDF and link their tests"


    def get_test(self, test_name):
        """
        Find a diagnostic test using its exact name.
        """
        return DiagnosticTest.objects.filter(
            name__iexact=test_name
        ).first()


    def link_tests(self, package, test_names, label):
        """
        Link tests to a package without deleting existing links.
        """

        linked = 0
        already_linked = 0
        not_found = []

        for test_name in test_names:

            test = self.get_test(test_name)

            if not test:
                not_found.append(test_name)
                self.stdout.write(
                    self.style.WARNING(
                        f"NOT FOUND: {test_name}"
                    )
                )
                continue

            if package.tests_included.filter(pk=test.pk).exists():

                already_linked += 1

                self.stdout.write(
                    f"ALREADY LINKED: {test.name}"
                )

            else:

                package.tests_included.add(test)

                linked += 1

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ LINKED: {test.name}"
                    )
                )

        self.stdout.write("\nSUMMARY")

        self.stdout.write(
            f"New tests linked: {linked}"
        )

        self.stdout.write(
            f"Already linked: {already_linked}"
        )

        self.stdout.write(
            f"Total tests currently in package: "
            f"{package.tests_included.count()}"
        )

        if not_found:

            self.stdout.write(
                self.style.WARNING(
                    "\nStill not found:"
                )
            )

            for test_name in not_found:
                self.stdout.write(
                    f"  - {test_name}"
                )


    def handle(self, *args, **options):

        with transaction.atomic():

            self.stdout.write("\n")
            self.stdout.write("=" * 60)
            self.stdout.write(
                self.style.SUCCESS(
                    "STARTING PDF PACKAGE CLEANUP"
                )
            )
            self.stdout.write("=" * 60)

            # =================================================
            # 1. FIND / FIX RPL ANC PROFILE
            # =================================================

            self.stdout.write("\n")
            self.stdout.write("=" * 60)
            self.stdout.write("SETTING UP RPL ANC PROFILE - 1")
            self.stdout.write("=" * 60)

            rpl_package = HealthPackage.objects.filter(
                package_code="PKG-6151"
            ).first()

            if rpl_package:

                self.stdout.write(
                    f"FOUND EXISTING PACKAGE: "
                    f"{rpl_package.name} "
                    f"({rpl_package.package_code})"
                )

                rpl_package.name = "RPL ANC Profile - 1"
                rpl_package.package_code = "PKG-RPL-001"
                rpl_package.save()

                self.stdout.write(
                    self.style.SUCCESS(
                        "✓ Renamed to RPL ANC Profile - 1"
                    )
                )

            else:

                rpl_package = HealthPackage.objects.filter(
                    package_code="PKG-RPL-001"
                ).first()

                if not rpl_package:

                    self.stdout.write(
                        self.style.WARNING(
                            "RPL package not found. "
                            "Creating new package."
                        )
                    )

                    rpl_package = HealthPackage.objects.create(
                        name="RPL ANC Profile - 1",
                        package_code="PKG-RPL-001",
                        description=(
                            "Comprehensive antenatal screening package."
                        ),
                        price=Decimal("0.00"),
                        is_available=True,
                    )


            # =================================================
            # 2. CREATE / FIND MASTER WELLNESS PACKAGE
            # =================================================

            self.stdout.write("\n")
            self.stdout.write("=" * 60)
            self.stdout.write("SETTING UP MASTER WELLNESS PACKAGE")
            self.stdout.write("=" * 60)

            master_package = HealthPackage.objects.filter(
                name__iexact="Master Wellness Package"
            ).first()

            if not master_package:

                master_package = HealthPackage.objects.create(
                    name="Master Wellness Package",
                    package_code="PKG-MASTER-001",
                    description=(
                        "Comprehensive wellness screening package."
                    ),
                    price=Decimal("0.00"),
                    is_available=True,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        "✓ Created Master Wellness Package"
                    )
                )

            else:

                self.stdout.write(
                    f"EXISTING PACKAGE FOUND: "
                    f"{master_package.name}"
                )


            # =================================================
            # 3. LINK RPL ANC TESTS
            # =================================================

            self.stdout.write("\n")
            self.stdout.write("=" * 60)
            self.stdout.write("LINKING RPL ANC PROFILE - 1")
            self.stdout.write("=" * 60)

            RPL_TESTS = [

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
            ]

            self.link_tests(
                rpl_package,
                RPL_TESTS,
                "RPL"
            )


            # =================================================
            # 4. LINK MASTER WELLNESS TESTS
            # =================================================

            self.stdout.write("\n")
            self.stdout.write("=" * 60)
            self.stdout.write("LINKING MASTER WELLNESS PACKAGE")
            self.stdout.write("=" * 60)

            MASTER_TESTS = [

                "ESR Automated",

                "Blood Glucose Fasting",

                "HsCRP High Sensitivity CRP",

                "Vitamin B12 Cyanocobalamin",

                "Vitamin D Total-25 Hydroxy",

                "Liver F. Test",

                "Thyroid Profile-I [T3T4TSH]",

                "Iron Panel with Ferritin",

                "HbA1c (Glycated hemoglobin)",

                "Complete Blood Count (CBC)",

                "Lipid Profile",

                "Urine R/M (Urine Analysis)",
            ]

            self.link_tests(
                master_package,
                MASTER_TESTS,
                "MASTER"
            )


            # =================================================
            # 5. KEEP ONLY THESE SIX PACKAGES
            # =================================================

            self.stdout.write("\n")
            self.stdout.write("=" * 60)
            self.stdout.write("REMOVING PACKAGES NOT IN PDF")
            self.stdout.write("=" * 60)

            KEEP_CODES = [

                "PKG-MASTER-001",   # Master Wellness Package

                "PKG-2955",         # Swasthya Mitra ADVANCE

                "PKG-2954",         # Swasthya Mitra PREMIUM

                "PKG-2956",         # Swasthya Mitra BASIC

                "PKG-RPL-001",      # RPL ANC Profile - 1

                "PKG-3029",         # Swasthya Mitra Super
            ]


            packages_to_delete = HealthPackage.objects.exclude(
                package_code__in=KEEP_CODES
            )

            for package in packages_to_delete:

                self.stdout.write(
                    self.style.WARNING(
                        f"REMOVING: "
                        f"{package.name} "
                        f"({package.package_code})"
                    )
                )


            packages_to_delete.delete()


            # =================================================
            # 6. FINAL VERIFICATION
            # =================================================

            self.stdout.write("\n")
            self.stdout.write("=" * 60)
            self.stdout.write(
                self.style.SUCCESS(
                    "FINAL PACKAGES"
                )
            )
            self.stdout.write("=" * 60)

            packages = HealthPackage.objects.filter(
                package_code__in=KEEP_CODES
            ).order_by("name")


            for package in packages:

                self.stdout.write(
                    f"\nPACKAGE: {package.name}"
                )

                self.stdout.write(
                    f"CODE: {package.package_code}"
                )

                self.stdout.write(
                    f"TESTS INCLUDED: "
                    f"{package.tests_included.count()}"
                )

                self.stdout.write(
                    f"PRICE: ₹{package.price}"
                )


            self.stdout.write("\n")

            self.stdout.write(
                self.style.SUCCESS(
                    "✓ PACKAGE CLEANUP COMPLETED SUCCESSFULLY"
                )
            )

            self.stdout.write(
                self.style.SUCCESS(
                    "✓ ONLY 6 PDF PACKAGES REMAIN"
                )
            )