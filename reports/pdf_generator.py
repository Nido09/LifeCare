import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
from django.conf import settings

LOGO_PATH = os.path.join(settings.BASE_DIR, 'static', 'images', 'logo.png')
STAMP_PATH = os.path.join(settings.BASE_DIR, 'static', 'images', 'stamp.png')
TEAL = colors.HexColor('#078895')
NAVY = colors.HexColor('#122d48')


def build_report_pdf(report):
    """
    Only used for GENERATED reports — UPLOADED reports carry their own
    pdf_file directly, this function is never called for them.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm
    )
    styles = getSampleStyleSheet()
    elements = []

    # ---- HEADER: branding block, matching the sample's letterhead ----
    header_data = [[
        Image(LOGO_PATH, width=18 * mm, height=18 * mm) if os.path.exists(LOGO_PATH) else '',
        Paragraph(
            "<b><font size=16 color='#122d48'>LIFE CARE DIAGNOSTIC CENTER</font></b><br/>"
            "<font size=9>Sena Nagar, Shiv Krupa Medical Store, Near Sai Baba Temple,<br/>"
            "Kajupada, Kurla West, Mumbai – 400072 | Mobile: 9082098149</font>",
            styles['Normal']
        )
    ]]
    header_table = Table(header_data, colWidths=[22 * mm, 160 * mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LINEBELOW', (0, 0), (-1, -1), 1.2, TEAL),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 6 * mm))
    elements.append(Paragraph("<b><font size=13 color='#122d48'>LABORATORY TEST REPORT</font></b>", styles['Normal']))
    elements.append(Spacer(1, 4 * mm))

    # ---- PATIENT / REPORT INFO — two-column block, like the sample ----
    patient = report.patient
    appointment = report.appointment
    info_data = [
        ['Patient Name', patient.user.get_full_name() or patient.user.username, 'Lab ID', appointment.appointment_id],
        ['Age / Gender', f"{patient.age or '—'} Yrs / {patient.gender or '—'}", 'Collection Date', str(appointment.preferred_date)],
        ['Patient ID', patient.patient_id, 'Reporting Date', report.created_at.strftime('%d-%b-%Y %H:%M')],
        ['Referred By', report.referred_by or 'Self', 'Report ID', str(report.report_uid)[:8]],
    ]
    info_table = Table(info_data, colWidths=[32 * mm, 58 * mm, 32 * mm, 58 * mm])
    info_table.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E1E8E8')),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8 * mm))

    if report.is_demo_data:
        elements.append(Paragraph(
            "<b><font color='#D6473D'>⚠ THIS IS DEMO / SAMPLE DATA — NOT A REAL DIAGNOSTIC RESULT.</font></b>",
            styles['Normal']
        ))
        elements.append(Spacer(1, 6 * mm))

    # ---- RESULTS, grouped by department (matching sample's "HEMATOLOGY"
    # section header, then test name, then its result lines) ----
    results_by_dept = {}
    for r in report.results.all():
        dept_name = r.test.category.name if r.test.category else 'OTHER'
        results_by_dept.setdefault(dept_name, []).append(r)

    for dept_name, dept_results in results_by_dept.items():
        elements.append(Paragraph(f"<b><font size=10 color='#ffffff' backColor='#122d48'>&nbsp;{dept_name}&nbsp;</font></b>", styles['Normal']))
        elements.append(Spacer(1, 2 * mm))

        result_data = [['Test Name', 'Result', 'Units', 'Reference Range']]
        for r in dept_results:
            flag_symbol = '▲' if r.abnormal_flag == 'HIGH' else ('▼' if r.abnormal_flag == 'LOW' else '')
            result_data.append([
                r.test.name,
                f"{flag_symbol} {r.result_value or '—'}".strip(),
                r.units or '—',
                r.reference_range or '—',
            ])

        result_table = Table(result_data, colWidths=[65 * mm, 45 * mm, 25 * mm, 45 * mm])
        result_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), NAVY),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#E1E8E8')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fbfb')]),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(result_table)
        elements.append(Spacer(1, 6 * mm))

    elements.append(Paragraph("<i><font size=8 color='#5C6E6E'>---------- End of report ----------</font></i>", styles['Normal']))
    elements.append(Spacer(1, 10 * mm))

    if os.path.exists(STAMP_PATH):
        elements.append(Image(STAMP_PATH, width=28 * mm, height=28 * mm))
    elements.append(Spacer(1, 4 * mm))

    elements.append(Paragraph(
        "<font size=7 color='#5C6E6E'>This report was generated digitally by LIFE CARE DIAGNOSTIC CENTER. "
        "Registration/Accreditation No.: [To be added]. For queries, contact 9082098149.</font>",
        styles['Normal']
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer