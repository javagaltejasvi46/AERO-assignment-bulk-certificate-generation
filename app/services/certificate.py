"""
Certificate PDF generation service using ReportLab canvas drawing.
"""

import os
from datetime import datetime

from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

CERTS_DIR = os.getenv(
    "CERTS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "generated_certs"),
)
os.makedirs(CERTS_DIR, exist_ok=True)


def _draw_border(c, width, height):
    """Draws outer and inner decorative border."""
    c.setStrokeColor(HexColor("#1a3c5e"))
    c.setLineWidth(3)
    margin = 0.4 * inch
    c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    c.setStrokeColor(HexColor("#2980b9"))
    c.setLineWidth(1.5)
    inner_margin = 0.6 * inch
    c.rect(inner_margin, inner_margin, width - 2 * inner_margin, height - 2 * inner_margin)


def _draw_decorative_corners(c, width, height):
    """Draws corner accents."""
    c.setFillColor(HexColor("#2980b9"))
    corner_offset = 0.5 * inch
    diamond_size = 6

    corners = [
        (corner_offset, corner_offset),
        (width - corner_offset, corner_offset),
        (corner_offset, height - corner_offset),
        (width - corner_offset, height - corner_offset),
    ]

    for cx, cy in corners:
        c.saveState()
        c.translate(cx, cy)
        c.rotate(45)
        c.rect(-diamond_size, -diamond_size, diamond_size * 2, diamond_size * 2, fill=True, stroke=False)
        c.restoreState()


def generate_certificate_pdf(
    recipient_name: str,
    course_name: str = "Certificate of Completion",
    issuer_name: str = "Organization",
    cert_id: str = "000",
) -> str:
    """Generates a certificate PDF and returns the file path."""
    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "" for c in recipient_name)
    safe_name = safe_name.strip().replace(" ", "_")
    filename = f"cert_{cert_id}_{safe_name}.pdf"
    filepath = os.path.join(CERTS_DIR, filename)

    page_width, page_height = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=landscape(A4))

    # Background canvas
    c.setFillColor(HexColor("#fdfaf3"))
    c.rect(0, 0, page_width, page_height, fill=True, stroke=False)

    _draw_border(c, page_width, page_height)
    _draw_decorative_corners(c, page_width, page_height)

    center_x = page_width / 2

    # Header section
    line_y = page_height - 1.5 * inch
    c.setStrokeColor(HexColor("#c0a44d"))
    c.setLineWidth(1)
    c.line(center_x - 2.5 * inch, line_y, center_x + 2.5 * inch, line_y)

    c.setFillColor(HexColor("#1a3c5e"))
    c.setFont("Helvetica", 38)
    c.drawCentredString(center_x, page_height - 2.0 * inch, "CERTIFICATE")

    c.setFont("Helvetica", 14)
    c.setFillColor(HexColor("#555555"))
    c.drawCentredString(center_x, page_height - 2.4 * inch, "OF COMPLETION")

    sub_line_y = page_height - 2.6 * inch
    c.setStrokeColor(HexColor("#c0a44d"))
    c.line(center_x - 1.5 * inch, sub_line_y, center_x + 1.5 * inch, sub_line_y)

    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#777777"))
    c.drawCentredString(center_x, page_height - 3.1 * inch, "This is proudly presented to")

    # Recipient Name with dynamic font sizing for long names
    c.setFillColor(HexColor("#1a3c5e"))
    name_font_size = 30
    if len(recipient_name) > 25:
        name_font_size = 24
    if len(recipient_name) > 35:
        name_font_size = 20
    c.setFont("Helvetica-Bold", name_font_size)
    c.drawCentredString(center_x, page_height - 3.7 * inch, recipient_name)

    name_line_y = page_height - 3.85 * inch
    c.setStrokeColor(HexColor("#c0a44d"))
    c.setLineWidth(0.5)
    c.line(center_x - 2 * inch, name_line_y, center_x + 2 * inch, name_line_y)

    # -- "for successfully completing" --
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#777777"))
    c.drawCentredString(center_x, page_height - 4.2 * inch, "for successfully completing")

    # -- course name --
    c.setFont("Helvetica-Bold", 16)
    c.setFillColor(HexColor("#2980b9"))
    c.drawCentredString(center_x, page_height - 4.6 * inch, course_name)

    # -- date and issuer at the bottom --
    today = datetime.now().strftime("%B %d, %Y")

    bottom_y = 1.2 * inch

    # date on the left
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#999999"))
    c.drawCentredString(center_x - 2.5 * inch, bottom_y + 0.3 * inch, "Date")
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(center_x - 2.5 * inch, bottom_y, today)

    # issuer on the right
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor("#999999"))
    c.drawCentredString(center_x + 2.5 * inch, bottom_y + 0.3 * inch, "Issued by")
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor("#333333"))
    c.drawCentredString(center_x + 2.5 * inch, bottom_y, issuer_name)

    # -- certificate ID at the very bottom (for reference) --
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#bbbbbb"))
    c.drawCentredString(center_x, 0.5 * inch, f"Certificate ID: {cert_id}")

    c.save()
    return filepath
