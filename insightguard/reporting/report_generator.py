from __future__ import annotations

from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def generate_report_bytes(title: str, summary: str, insights: list[str]) -> bytes:
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph(escape(title), styles['Title']),
        Spacer(1, 18),
        Paragraph(escape('Synthetic data / simulated AI note'), ParagraphStyle(name='note', parent=styles['BodyText'], fontName='Helvetica-Oblique')),
        Spacer(1, 12),
        Paragraph(escape(summary).replace('\n', '<br/>'), styles['BodyText']),
        Spacer(1, 12),
    ]
    for item in insights:
        story.append(Paragraph(f'- {escape(item)}', styles['BodyText']))
    doc.build(story)
    return output.getvalue()


def generate_report(output_path: str | Path, title: str, summary: str, insights: list[str]) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(generate_report_bytes(title, summary, insights))
    return str(output)
