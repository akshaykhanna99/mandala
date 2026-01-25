"""API routes for report generation."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from typing import Dict, Any
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from io import BytesIO
import os

router = APIRouter(prefix="/reports", tags=["reports"])


def generate_pdf_report(pipeline_result: Dict[str, Any]) -> BytesIO:
    """
    Generate a 1-page A4 PDF report for a GP health scan.
    
    Layout:
    - Top left: Mandala logo + "MANDALA" title
    - Top right: Report date
    - Title: "Geopolitical Health Scan"
    - Asset Summary
    - Impact Summary
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, 
                           leftMargin=20*mm, rightMargin=20*mm,
                           topMargin=20*mm, bottomMargin=20*mm)
    
    # Container for the story (content)
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#334155'),
        spaceAfter=4,
        spaceBefore=4,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=9,
        textColor=colors.HexColor('#475569'),
        spaceAfter=3,
        leading=12,
        fontName='Helvetica'
    )
    
    # Header: Logo + Title (left) and Date (right)
    # Try to load logo
    logo_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'public', 'mandala_logo.png')
    logo_elements = []
    
    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=20*mm, height=20*mm)
            logo_elements.append(logo)
        except Exception:
            pass
    
    mandala_text = Paragraph('<b>MANDALA</b>', ParagraphStyle(
        'MandalaTitle',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica-Bold',
        alignment=TA_LEFT
    ))
    logo_elements.append(mandala_text)
    
    # Create left column with logo and text
    left_col = Table([[elem] for elem in logo_elements], colWidths=[doc.width * 0.7])
    left_col.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    
    # Right side: Date
    report_date = datetime.now().strftime("%B %d, %Y")
    date_text = Paragraph(report_date, ParagraphStyle(
        'ReportDate',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748b'),
        fontName='Helvetica',
        alignment=TA_RIGHT
    ))
    
    # Create header table
    header_table = Table([[left_col, date_text]], colWidths=[doc.width * 0.7, doc.width * 0.3])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 4*mm))
    
    # Main Title
    story.append(Paragraph("Geopolitical Health Scan", title_style))
    story.append(Spacer(1, 4*mm))
    
    # Asset Summary Section
    story.append(Paragraph("Asset Summary", heading_style))
    
    asset_name = pipeline_result.get("name") or "Unknown Asset"
    asset_ticker = pipeline_result.get("ticker", "")
    asset_country = pipeline_result.get("asset_country") or "Unknown"
    asset_region = pipeline_result.get("asset_region", "Unknown")
    asset_sector = pipeline_result.get("asset_sector", "Unknown")
    asset_class = pipeline_result.get("asset_class", "Unknown")
    
    asset_info = [
        f"<b>Asset:</b> {asset_name}" + (f" ({asset_ticker})" if asset_ticker else ""),
        f"<b>Country:</b> {asset_country}",
        f"<b>Region:</b> {asset_region}",
        f"<b>Sector:</b> {asset_sector}",
        f"<b>Asset Class:</b> {asset_class}",
    ]
    
    # Add exposures if available
    exposures = pipeline_result.get("exposures", [])
    if exposures:
        asset_info.append(f"<b>Exposures:</b> {', '.join(exposures)}")
    
    # Add characterization summary
    char_summary = pipeline_result.get("characterization_summary", "")
    if char_summary:
        asset_info.append("")
        asset_info.append(f"<i>{char_summary[:300]}{'...' if len(char_summary) > 300 else ''}</i>")
    
    for info in asset_info:
        if info:
            story.append(Paragraph(info, body_style))
        else:
            story.append(Spacer(1, 2*mm))
    
    story.append(Spacer(1, 3*mm))
    
    # Impact Summary Section
    story.append(Paragraph("Impact Summary", heading_style))
    
    impact = pipeline_result.get("impact", {})
    probabilities = pipeline_result.get("probabilities", {})
    confidence = impact.get("confidence", 0.0)
    
    # Probability scores
    negative_prob = probabilities.get("negative") or probabilities.get("sell", 0.0)
    neutral_prob = probabilities.get("neutral") or probabilities.get("hold", 0.0)
    positive_prob = probabilities.get("positive") or probabilities.get("buy", 0.0)
    
    # Geopolitical Health Score first
    story.append(Paragraph("<b>Geopolitical Health Score</b>", body_style))
    story.append(Paragraph(f"Negative: {negative_prob:.1%} | Neutral: {neutral_prob:.1%} | Positive: {positive_prob:.1%}", body_style))
    story.append(Spacer(1, 2*mm))
    
    # Confidence level below
    story.append(Paragraph(f"<b>Confidence Level:</b> {confidence:.1%}", body_style))
    story.append(Spacer(1, 3*mm))
    
    # Key Theme Impacts with full AI summaries
    theme_impacts = impact.get("theme_impacts", [])
    if theme_impacts:
        story.append(Paragraph("<b>Key Theme Impacts</b>", heading_style))
        
        for theme_impact in theme_impacts[:5]:  # Top 5 themes
            theme = theme_impact.get("theme", "Unknown")
            direction = theme_impact.get("impact_direction", "neutral")
            magnitude = theme_impact.get("impact_magnitude", 0.0)
            summary = theme_impact.get("summary", "")
            
            # Theme header
            theme_header_style = ParagraphStyle(
                'ThemeHeader',
                parent=body_style,
                fontSize=10,
                textColor=colors.HexColor('#1e293b'),
                fontName='Helvetica-Bold',
                spaceAfter=2,
                spaceBefore=3
            )
            story.append(Paragraph(f"<b>{theme}</b> - {direction.capitalize()} Impact ({magnitude:.2f})", theme_header_style))
            
            # Full AI summary
            if summary:
                summary_style = ParagraphStyle(
                    'ThemeSummary',
                    parent=body_style,
                    fontSize=8,
                    textColor=colors.HexColor('#475569'),
                    leading=11,
                    leftIndent=4*mm,
                    spaceAfter=3
                )
                story.append(Paragraph(summary, summary_style))
            else:
                # Fallback to reasoning if summary not available
                reasoning = theme_impact.get("reasoning", "")
                if reasoning:
                    summary_style = ParagraphStyle(
                        'ThemeSummary',
                        parent=body_style,
                        fontSize=8,
                        textColor=colors.HexColor('#475569'),
                        leading=11,
                        leftIndent=4*mm,
                        spaceAfter=3
                    )
                    story.append(Paragraph(reasoning, summary_style))
            
            story.append(Spacer(1, 2*mm))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


@router.post("/generate-gp-scan")
def generate_gp_scan_report(pipeline_result: Dict[str, Any]):
    """
    Generate a PDF report for a GP health scan.
    
    Accepts a DetailedPipelineResult as JSON and returns a PDF file.
    """
    try:
        pdf_buffer = generate_pdf_report(pipeline_result)
        
        # Generate filename
        asset_name = pipeline_result.get("name", "asset")
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"mandala_gp_scan_{asset_name.replace(' ', '_')}_{date_str}.pdf"
        
        return Response(
            content=pdf_buffer.read(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")
