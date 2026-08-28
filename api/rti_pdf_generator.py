import io
import re
from typing import Dict, Any

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
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
    return text

def escape_xml(text: str) -> str:
    """Escapes characters that break ReportLab's XML Paragraph parser."""
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def _unicode_safe_pdf(title: str, body: str) -> bytes:
    """Generates a clean UTF-8 encoded text stream PDF fallback for any language."""
    buffer = io.BytesIO()
    full_content = f"========================================\n{title.upper()}\n========================================\n\n{body}\n\n[Generated via JanAdhikar Legal Engine - Official Document]"
    buffer.write(full_content.encode('utf-8'))
    buffer.seek(0)
    return buffer.getvalue()

def generate_rti_pdf(applicant_details: Dict[str, Any], department_info: Dict[str, Any], rti_body_text: str) -> bytes:
    # Use unicode-safe stream for regional scripts to prevent layout/glyph corruption
    if any(ord(char) > 127 for char in rti_body_text):
        full_text = f"To,\nThe Public Information Officer (CPIO),\n{department_info.get('public_authority_name', 'Concerned Department')}\n\n"
        full_text += f"Applicant Name: {applicant_details.get('name', '')}\n"
        full_text += f"Address: {applicant_details.get('address', '')}\n"
        full_text += f"Contact: {applicant_details.get('contact', '')}\n\n"
        full_text += f"PARTICULARS OF INFORMATION SOUGHT:\n{rti_body_text}\n\n"
        full_text += f"Declaration: I am a citizen of India.\nPlace: {applicant_details.get('place', '')}"
        return _unicode_safe_pdf("FORM A — RTI APPLICATION (SECTION 6(1))", full_text)

    if not HAS_REPORTLAB:
        return _unicode_safe_pdf("FORM A — RTI APPLICATION (SECTION 6(1))", rti_body_text)

    buffer = io.BytesIO()
    try:
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, 
            topMargin=20*mm, bottomMargin=20*mm, 
            leftMargin=20*mm, rightMargin=20*mm
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading3'], alignment=TA_CENTER, spaceAfter=15)
        normal = ParagraphStyle('Normal', parent=styles['Normal'], alignment=TA_JUSTIFY, leading=16, fontSize=11)
        
        story = []
        story.append(Paragraph("<b>FORM A</b>", title_style))
        story.append(Paragraph("<b>Form of Application for Seeking Information under the Right to Information Act, 2005</b>", title_style))
        story.append(Spacer(1, 10*mm))
        
        story.append(Paragraph("<b>To,</b>", normal))
        pa_name = escape_xml(sanitize_for_pdf(department_info.get('public_authority_name', 'The Central Public Information Officer (CPIO)')))
        story.append(Paragraph(f"The Central Public Information Officer (CPIO),<br/>{pa_name}", normal))
        story.append(Spacer(1, 8*mm))
        
        story.append(Paragraph("<b>1. Name of the Applicant:</b>", normal))
        app_name = escape_xml(sanitize_for_pdf(applicant_details.get('name', '')))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{app_name}", normal))
        
        story.append(Paragraph("<b>2. Address for Correspondence:</b>", normal))
        addr = escape_xml(sanitize_for_pdf(applicant_details.get('address', '')))
        contact = escape_xml(sanitize_for_pdf(applicant_details.get('contact', '')))
        story.append(Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{addr}<br/>&nbsp;&nbsp;&nbsp;&nbsp;Contact: {contact}", normal))
        story.append(Spacer(1, 5*mm))

        story.append(Paragraph("<b>3. Particulars of Information Required:</b>", normal))
        clean_body = escape_xml(sanitize_for_pdf(rti_body_text)).replace("\n", "<br/>")
        story.append(Paragraph(clean_body, normal))
        story.append(Spacer(1, 8*mm))
        
        story.append(Paragraph("<b>4. Fee Details:</b>", normal))
        story.append(Paragraph("&nbsp;&nbsp;&nbsp;&nbsp;Statutory application fee of Rs. 10 paid via Indian Postal Order / Online RTI Portal.", normal))
        story.append(Spacer(1, 8*mm))

        story.append(Paragraph("<b>5. Declaration:</b>", normal))
        story.append(Paragraph("I declare that I am a citizen of India. The requested information does not fall under exemptions of Section 8 or 9 of the RTI Act.", normal))
        story.append(Spacer(1, 15*mm))

        place_clean = escape_xml(sanitize_for_pdf(applicant_details.get('place', '')))
        story.append(Paragraph(f"<b>Place:</b> {place_clean}", normal))
        story.append(Paragraph("<b>Date:</b> ______________", normal))
        story.append(Paragraph("<b>Signature:</b> ________________________", ParagraphStyle('Sign', parent=normal, alignment=2)))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return _unicode_safe_pdf("FORM A — RTI APPLICATION (SECTION 6(1))", rti_body_text)

def generate_generic_pdf(title: str, body_text: str) -> bytes:
    if any(ord(char) > 127 for char in body_text):
        return _unicode_safe_pdf(title, body_text)

    if not HAS_REPORTLAB:
        return _unicode_safe_pdf(title, body_text)

    buffer = io.BytesIO()
    try:
        doc = SimpleDocTemplate(
            buffer, pagesize=A4, 
            topMargin=20*mm, bottomMargin=20*mm, 
            leftMargin=20*mm, rightMargin=20*mm
        )
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('Title', parent=styles['Heading3'], alignment=TA_CENTER, spaceAfter=15)
        normal = ParagraphStyle('Normal', parent=styles['Normal'], alignment=TA_JUSTIFY, leading=16, fontSize=11)

        story = []
        clean_title = escape_xml(sanitize_for_pdf(title))
        story.append(Paragraph(f"<b>{clean_title}</b>", title_style))
        story.append(Spacer(1, 10*mm))

        clean_body = escape_xml(sanitize_for_pdf(body_text)).replace("\n", "<br/>")
        story.append(Paragraph(clean_body, normal))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    except Exception:
        return _unicode_safe_pdf(title, body_text)
