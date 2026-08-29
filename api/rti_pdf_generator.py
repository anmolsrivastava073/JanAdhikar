import io
import re
from typing import Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
    from reportlab.lib import colors
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

def sanitize_for_pdf(text: str) -> str:
    if not text:
        return ""
    
    replacements = {
        '“': '"', '”': '"', 
        '‘': "'", '’': "'",
        '–': '-', '—': '-', 
        '•': '-', '…': '...',
        '₹': 'Rs. ',
        '\u200b': '', '\xa0': ' ', '\r': ''
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'#{1,6}\s?', '', text)
    return text.encode('latin-1', 'ignore').decode('latin-1')

def escape_xml(text: str) -> str:
    """Escapes characters that break ReportLab's XML Paragraph parser."""
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _simple_pdf(title: str, body: str) -> bytes:
    content = f"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    content += f"3 0 obj<</Type/Page/MediaBox[0 0 595 842]/Parent 2 0 R/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>endobj\n"
    content += f"4 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    
    lines = [sanitize_for_pdf(title)] + [sanitize_for_pdf(l) for l in body.split('\n') if l.strip()]
    stream_content = "BT /F1 10 Tf 50 780 Td 14 TL "
    for line in lines[:55]:
        safe_line = line.replace('(', '\\(').replace(')', '\\)')
        stream_content += f"({safe_line}) ' "
    stream_content += "ET"
    
    stream_len = len(stream_content.encode('latin-1', 'ignore'))
    content += f"5 0 obj<</Length {stream_len}>>stream\n{stream_content}\nendstream\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000224 00000 n \n0000000293 00000 n \ntrailer<</Size 6/Root 1 0 R>>\nstartxref\n{len(content.encode('latin-1', 'ignore'))}\n%%EOF"
    return content.encode('latin-1', 'ignore')

def generate_rti_pdf(applicant_details: Dict[str, Any], department_info: Dict[str, Any], rti_body_text: str) -> bytes:
    """
    Generates a statutory Form A Right to Information application PDF under Section 6(1)
    of the Right to Information Act, 2005.
    """
    if not HAS_REPORTLAB:
        full_text = f"Applicant: {applicant_details.get('name', 'Applicant')}\n"
        full_text += f"Public Authority: {department_info.get('public_authority_name', 'CPIO')}\n\n"
        full_text += rti_body_text
        return _simple_pdf("FORM A — RTI APPLICATION (SECTION 6(1))", full_text)

    buffer = io.BytesIO()
    try:
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, 
            topMargin=18*mm, bottomMargin=18*mm, 
            leftMargin=18*mm, rightMargin=18*mm
        )
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'FormTitle', parent=styles['Heading2'], 
            alignment=TA_CENTER, fontSize=12, leading=15, 
            fontName='Helvetica-Bold', spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            'FormSubtitle', parent=styles['Normal'], 
            alignment=TA_CENTER, fontSize=9.5, leading=12, 
            fontName='Helvetica-Bold', spaceAfter=10
        )
        section_heading = ParagraphStyle(
            'SecHead', parent=styles['Normal'], 
            fontSize=9.5, leading=13, fontName='Helvetica-Bold', spaceAfter=4
        )
        normal = ParagraphStyle(
            'Body', parent=styles['Normal'], 
            alignment=TA_JUSTIFY, leading=13.5, fontSize=9, fontName='Helvetica', spaceAfter=4
        )
        right_align = ParagraphStyle(
            'RightAlign', parent=styles['Normal'], 
            alignment=TA_RIGHT, leading=13, fontSize=9, fontName='Helvetica-Bold'
        )

        story = []

        # 1. Header Block
        story.append(Paragraph("FORM A", title_style))
        story.append(Paragraph("APPLICATION FOR SEEKING INFORMATION UNDER SECTION 6(1) OF THE RIGHT TO INFORMATION ACT, 2005", subtitle_style))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=8))

        # 2. Addressee Block
        pio_desig = escape_xml(sanitize_for_pdf(department_info.get('pio_designation') or 'The Central Public Information Officer (CPIO)'))
        pa_name = escape_xml(sanitize_for_pdf(department_info.get('public_authority_name') or 'Concerned Public Authority'))
        addr_template = escape_xml(sanitize_for_pdf(department_info.get('suggested_address_template') or ''))
        
        story.append(Paragraph("<b>To,</b>", normal))
        story.append(Paragraph(f"{pio_desig}<br/>{pa_name}<br/>{addr_template}", normal))
        story.append(Spacer(1, 4*mm))

        # 3. Applicant Particulars
        app_name = escape_xml(sanitize_for_pdf(applicant_details.get('name') or 'Applicant'))
        app_addr = escape_xml(sanitize_for_pdf(applicant_details.get('address') or applicant_details.get('place') or ''))
        app_contact = escape_xml(sanitize_for_pdf(applicant_details.get('contact') or ''))
        
        story.append(Paragraph("<b>1. PARTICULARS OF THE APPLICANT:</b>", section_heading))
        story.append(Paragraph(f"• <b>Full Name:</b> {app_name}", normal))
        story.append(Paragraph(f"• <b>Correspondence Address:</b> {app_addr}", normal))
        story.append(Paragraph(f"• <b>Contact Details / Email:</b> {app_contact}", normal))
        story.append(Paragraph("• <b>Citizenship:</b> Citizen of India (Eligible under Section 3 of RTI Act, 2005)", normal))
        story.append(Spacer(1, 4*mm))

        # 4. Particulars of Information Sought (Section 2(f))
        story.append(Paragraph("<b>2. PARTICULAR OF INFORMATION SOUGHT UNDER SECTION 2(f) &amp; SECTION 2(j):</b>", section_heading))
        
        clean_body = escape_xml(sanitize_for_pdf(rti_body_text)).replace("\n", "<br/>")
        story.append(Paragraph(clean_body, normal))
        story.append(Spacer(1, 4*mm))

        # 5. Statutory Mandates (Section 6(3), Section 10, Section 7(6))
        story.append(Paragraph("<b>3. STATUTORY PROVISIONS &amp; LEGAL MANDATES:</b>", section_heading))
        story.append(Paragraph("• <b>Section 6(3) Transfer Mandate:</b> If the requested information or any part thereof is held by another public authority, the CPIO/SPIO is statutorily mandated to transfer this application within 5 days of receipt with intimation to the applicant.", normal))
        story.append(Paragraph("• <b>Section 10(1) Severability Clause:</b> In case any part of the requested records is considered exempt under Section 8 or 9, access shall be provided to the non-exempt portion after severing the exempt record.", normal))
        story.append(Paragraph("• <b>Section 7(6) Fee Waiver:</b> If the public authority fails to provide the requested information within 30 calendar days, the information shall be provided free of any charge.", normal))
        story.append(Spacer(1, 4*mm))

        # 6. Fee Details
        story.append(Paragraph("<b>4. APPLICATION FEE PARTICULARS:</b>", section_heading))
        story.append(Paragraph("Statutory application fee of Rs. 10/- (Rupees Ten Only) remitted via Indian Postal Order (IPO) / Court Fee Stamp / Online RTI Payment Receipt.", normal))
        story.append(Spacer(1, 4*mm))

        # 7. Verification & Declaration
        story.append(Paragraph("<b>5. VERIFICATION &amp; DECLARATION:</b>", section_heading))
        story.append(Paragraph("I hereby declare that I am a citizen of India and the requested information does not fall within the exemptions contained in Section 8 or 9 of the RTI Act, 2005.", normal))
        story.append(Spacer(1, 6*mm))

        place_clean = escape_xml(sanitize_for_pdf(applicant_details.get('place') or ''))
        story.append(Paragraph(f"<b>Place:</b> {place_clean}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b>Date:</b> ______________", normal))
        story.append(Spacer(1, 4*mm))
        story.append(Paragraph("<b>Signature of Applicant:</b> ___________________________", right_align))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception as e:
        print(f"PDF generation exception: {e}")
        return _simple_pdf("FORM A — RTI APPLICATION (SECTION 6(1))", rti_body_text)

def generate_generic_pdf(title: str, body_text: str) -> bytes:
    if not HAS_REPORTLAB:
        return _simple_pdf(title, body_text)

    buffer = io.BytesIO()
    try:
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, 
            topMargin=18*mm, bottomMargin=18*mm, 
            leftMargin=18*mm, rightMargin=18*mm
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading3'], alignment=TA_CENTER, spaceAfter=12, fontName='Helvetica-Bold')
        normal = ParagraphStyle('Normal', parent=styles['Normal'], alignment=TA_JUSTIFY, leading=14, fontSize=9.5)

        story = []
        clean_title = escape_xml(sanitize_for_pdf(title))
        story.append(Paragraph(f"<b>{clean_title}</b>", title_style))
        story.append(Spacer(1, 6*mm))

        clean_body = escape_xml(sanitize_for_pdf(body_text)).replace("\n", "<br/>")
        story.append(Paragraph(clean_body, normal))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return _simple_pdf(title, body_text)
