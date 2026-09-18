import re
import pdfplumber
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from tests_app.models import TestCategory, DiagnosticTest


class Command(BaseCommand):
    help = "Imports ALL test rows from the Panel Wise Rate List PDF, including tests whose names wrap across multiple PDF text lines. Never deletes or duplicates existing tests."

    DEPARTMENTS = [
        'IMMUNOHISTOCHEMISTRY', 'COAGULATION_HAEMATOLOGY', 'MICROBIOLOGY SPE',
        'IMMUNOASSAY_SPE', 'MOLECULAR BIOLOGY', 'CLINICAL PATHOLOGY',
        '.IMMUNO BIOCHEMISTRY-1', 'MOL. BIOLOGY', 'HISTOPATHOLOGY',
        'MICROBIOLOGY', 'BIOCHEMISTRY-3', 'OPD-PACKAGE', 'HAEMATOLOGY',
        'OUT SOURCE', 'IMMUNOASSAY', 'IMMUNOLOGY', 'SEROLOGY', 'CYTOLOGY',
    ]
    HEADER_MARKERS = ('Department', 'Date Time', 'Panel wise', 'AP052206')
    CODE = r'[A-Za-z0-9#_]{1,10}'
    RATE = r'[\d,]+\.\d{2}'

    def _not_noise(self, line):
        line = line.strip()

        if not line:
            return False

        if any(marker.lower() in line.lower() for marker in self.HEADER_MARKERS):
            return False

        if re.fullmatch(r'Page\s+\d+(\s+of\s+\d+)?', line, re.IGNORECASE):
            return False

        return True

    def _not_noise(self, line):
        line = line.strip()
        if not line or line == 'HOME':
            return False
        return not line.startswith(self.HEADER_MARKERS)

    def add_arguments(self, parser):
        parser.add_argument('pdf_path', type=str, help='Path to the rate list PDF')

    def handle(self, *args, **options):
        pdf_path = options['pdf_path']
        dept_alt = '|'.join(re.escape(d) for d in self.DEPARTMENTS)

        row_pattern = re.compile(rf'^(?P<dept>{dept_alt})\s+(?P<name>.+?)\s+(?P<code>{self.CODE})\s+(?P<rate>{self.RATE})$')
        orphan_pattern = re.compile(rf'^(?P<dept>{dept_alt})\s+(?P<code>{self.CODE})\s+(?P<rate>{self.RATE})$')
        tail_pattern = re.compile(rf'^(?P<name>.+?)\s+(?P<code>{self.CODE})\s+(?P<rate>{self.RATE})$')
        dept_start_pattern = re.compile(rf'^(?P<dept>{dept_alt})\s+(?P<name>.+)$')

        extracted_rows = []
        unresolved_lines = []

        with pdfplumber.open(pdf_path) as pdf:
            total_pages = len(pdf.pages)
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if not text:
                    continue
                raw_lines = [l.strip() for l in text.split('\n') if self._not_noise(l)]
                consumed = [False] * len(raw_lines)

                # PASS 1 — orphan DEPT+CODE+RATE rows (no name text on this
                # line at all — the name wrapped onto neighboring lines).
                # This MUST run before the full-row pattern below: for
                # two-word departments, the full-row pattern's lazy name
                # group can otherwise backtrack into the department text
                # itself and produce a wrong split (verified against this
                # exact PDF — see command docstring / chat explanation).
                for i, line in enumerate(raw_lines):
                    m = orphan_pattern.match(line)
                    if not m:
                        continue
                    name_parts = []
                    j = i - 1
                    while j >= 0 and not consumed[j] and not row_pattern.match(raw_lines[j]) and not orphan_pattern.match(raw_lines[j]):
                        name_parts.insert(0, raw_lines[j]); consumed[j] = True; j -= 1
                        if i - j > 2:
                            break
                    k = i + 1
                    while k < len(raw_lines) and not consumed[k] and not row_pattern.match(raw_lines[k]) and not orphan_pattern.match(raw_lines[k]):
                        name_parts.append(raw_lines[k]); consumed[k] = True; k += 1
                        if k - i > 2:
                            break
                    consumed[i] = True
                    full_name = ' '.join(name_parts).strip()
                    if full_name:
                        extracted_rows.append({
                            'dept': m.group('dept').strip(), 'name': full_name,
                            'code': m.group('code').strip(), 'rate': m.group('rate').replace(',', ''),
                        })
                    else:
                        unresolved_lines.append((page_num, line))

                # PASS 2 — standard single-line DEPT NAME CODE RATE
                for i, line in enumerate(raw_lines):
                    if consumed[i]:
                        continue
                    m = row_pattern.match(line)
                    if m:
                        extracted_rows.append({
                            'dept': m.group('dept').strip(), 'name': m.group('name').strip(),
                            'code': m.group('code').strip(), 'rate': m.group('rate').replace(',', ''),
                        })
                        consumed[i] = True

                # PASS 3 — "DEPT + name-start" line directly followed by
                # "name-end + CODE + RATE" line (2-line split with no
                # clean orphan line in between).
                for i, line in enumerate(raw_lines):
                    if consumed[i]:
                        continue
                    m1 = dept_start_pattern.match(line)
                    if not m1 or row_pattern.match(line) or orphan_pattern.match(line):
                        continue
                    if i + 1 >= len(raw_lines) or consumed[i + 1]:
                        continue
                    next_line = raw_lines[i + 1]
                    if row_pattern.match(next_line) or orphan_pattern.match(next_line) or dept_start_pattern.match(next_line):
                        continue
                    m2 = tail_pattern.match(next_line)
                    if not m2:
                        continue
                    full_name = f"{m1.group('name')} {m2.group('name')}".strip()
                    extracted_rows.append({
                        'dept': m1.group('dept').strip(), 'name': full_name,
                        'code': m2.group('code').strip(), 'rate': m2.group('rate').replace(',', ''),
                    })
                    consumed[i] = True
                    consumed[i + 1] = True

                for i, line in enumerate(raw_lines):
                    if not consumed[i]:
                        unresolved_lines.append((page_num, line))

        # ---- De-duplicate by test_code within the PDF itself, safely ----
        seen_codes = {}
        duplicates_in_pdf = 0
        for row in extracted_rows:
            code = row['code']
            if code in seen_codes:
                duplicates_in_pdf += 1
                continue
            seen_codes[code] = row
        unique_rows = list(seen_codes.values())

        # ---- Compare against current database state ----
        already_existing_codes = set(
            DiagnosticTest.objects.filter(test_code__in=seen_codes.keys()).values_list('test_code', flat=True)
        )
        missing_rows = [r for r in unique_rows if r['code'] not in already_existing_codes]

        created_categories = 0
        created_tests = 0

        for row in missing_rows:
            category, was_created = TestCategory.objects.get_or_create(
                name=row['dept'], defaults={'slug': slugify(row['dept'])}
            )
            if was_created:
                created_categories += 1

            _, test_created = DiagnosticTest.objects.get_or_create(
                test_code=row['code'],
                defaults={'name': row['name'], 'category': category, 'price': row['rate']},
            )
            if test_created:
                created_tests += 1

        final_count = DiagnosticTest.objects.count()

        # ---- Verification report, in the exact format requested ----
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=== IMPORT VERIFICATION REPORT ==='))
        self.stdout.write(f'Total pages scanned: {total_pages}')
        self.stdout.write(f'Total test rows found in PDF: {len(extracted_rows)}')
        self.stdout.write(f'Unique test codes in PDF: {len(unique_rows)}')
        self.stdout.write(f'Duplicate rows within PDF (skipped safely): {duplicates_in_pdf}')
        self.stdout.write(f'Already existing in database: {len(already_existing_codes)}')
        self.stdout.write(f'Missing tests found: {len(missing_rows)}')
        self.stdout.write(f'Newly imported: {created_tests}')
        self.stdout.write(f'New categories created: {created_categories}')
        self.stdout.write(f'Final DiagnosticTest count in database: {final_count}')

        if unresolved_lines:
            self.stdout.write('')
            self.stdout.write(self.style.WARNING(
                f'{len(unresolved_lines)} line(s) could not be parsed and require manual review (not imported, nothing lost silently):'
            ))
            for page_num, line in unresolved_lines:
                self.stdout.write(f'  [page {page_num}] {line!r}')