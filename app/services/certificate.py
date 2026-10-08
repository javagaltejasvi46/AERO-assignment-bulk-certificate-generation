"""
Certificate PDF generation service using ReportLab canvas drawing.
"""

import os
import math
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


def _draw_star(c, cx, cy, r_outer, r_inner, points=5):
    """Draws a star polygon at center (cx, cy)."""
    p = c.beginPath()
    angle = -math.pi / 2
    step = math.pi / points
    for i in range(points * 2):
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        if i == 0:
            p.moveTo(x, y)
        else:
            p.lineTo(x, y)
        angle += step
    p.close()
    c.drawPath(p, fill=1, stroke=0)


def _draw_seal(c, center_x, seal_y, radius=32):
    """Draws official gold seal with ribbon tails, serrated rim, dashed ring, and stars."""
    c.saveState()

    # Ribbon tails
    c.setFillColor(HexColor("#1a3c5e"))
    c.setStrokeColor(HexColor("#0f243a"))
    c.setLineWidth(0.5)

    p_left = c.beginPath()
    p_left.moveTo(center_x - 14, seal_y - 10)
    p_left.lineTo(center_x - 24, seal_y - 48)
    p_left.lineTo(center_x - 14, seal_y - 40)
    p_left.lineTo(center_x - 4, seal_y - 48)
    p_left.lineTo(center_x - 4, seal_y - 10)
    p_left.close()
    c.drawPath(p_left, fill=1, stroke=1)

    p_right = c.beginPath()
    p_right.moveTo(center_x + 4, seal_y - 10)
    p_right.lineTo(center_x + 4, seal_y - 48)
    p_right.lineTo(center_x + 14, seal_y - 40)
    p_right.lineTo(center_x + 24, seal_y - 48)
    p_right.lineTo(center_x + 14, seal_y - 10)
    p_right.close()
    c.drawPath(p_right, fill=1, stroke=1)

    # Serrated outer gold ring
    c.setFillColor(HexColor("#d97706"))
    p_serr = c.beginPath()
    num_points = 36
    for i in range(num_points * 2):
        r = (radius + 3) if i % 2 == 0 else (radius - 1)
        angle = i * (math.pi / num_points)
        x = center_x + r * math.cos(angle)
        y = seal_y + r * math.sin(angle)
        if i == 0:
            p_serr.moveTo(x, y)
        else:
            p_serr.lineTo(x, y)
    p_serr.close()
    c.drawPath(p_serr, fill=1, stroke=0)

    # Concentric gold medal circles
    c.setFillColor(HexColor("#f59e0b"))
    c.circle(center_x, seal_y, radius, fill=1, stroke=0)

    c.setFillColor(HexColor("#b45309"))
    c.circle(center_x, seal_y, radius - 4, fill=1, stroke=0)

    c.setFillColor(HexColor("#d97706"))
    c.circle(center_x, seal_y, radius - 6, fill=1, stroke=0)

    # Dashed inner ring
    c.setStrokeColor(HexColor("#fef3c7"))
    c.setLineWidth(1.2)
    c.setDash(2, 2)
    c.circle(center_x, seal_y, radius - 7, fill=0, stroke=1)
    c.setDash()

    # Stars and OFFICIAL text
    c.setFillColor(HexColor("#ffffff"))
    _draw_star(c, center_x, seal_y + 11, 4.5, 2.0)

    c.setFont("Helvetica-Bold", 7.5)
    c.drawCentredString(center_x, seal_y - 2.5, "OFFICIAL")

    _draw_star(c, center_x, seal_y - 14, 4.5, 2.0)

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

    # Official gold seal badge in the center
    _draw_seal(c, center_x, bottom_y + 0.22 * inch)

    # -- certificate ID at the very bottom (for reference) --
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor("#bbbbbb"))
    c.drawCentredString(center_x, 0.5 * inch, f"Certificate ID: {cert_id}")

    c.save()
    return filepath
