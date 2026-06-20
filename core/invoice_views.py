"""
Invoice and Certificate Generation Views
"""

from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from io import BytesIO

from .models import Order, OrderItem, Certificate, CourseAccess


@login_required
def invoice_page(request, order_id):
    """Display invoice page with download option."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()
    
    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'core/invoice.html', context)


@login_required
def download_invoice_pdf(request, order_id):
    """Generate and download invoice as PDF."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.items.all()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=colors.HexColor('#ffc107'),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'HeaderStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1e1e1e'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    label_style = ParagraphStyle(
        'LabelStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666'),
        spaceAfter=4
    )
    
    value_style = ParagraphStyle(
        'ValueStyle',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1e1e1e'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    # Title
    title = Paragraph("TRADERSFY", title_style)
    elements.append(title)
    
    subtitle = Paragraph("Premium Learning Platform", header_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.2*inch))
    
    # Invoice Header
    invoice_header = Paragraph(f"<b>INVOICE #{order.order_id}</b>", ParagraphStyle('InvoiceHeader', parent=styles['Normal'], fontSize=14, textColor=colors.HexColor('#1e1e1e'), spaceAfter=10))
    elements.append(invoice_header)
    
    # Invoice Details Grid
    invoice_data = [
        ['Invoice Date:', order.created_at.strftime('%d %B %Y')],
        ['Order Status:', order.status.upper()],
        ['Payment Method:', order.payment_method],
    ]
    
    invoice_table = Table(invoice_data, colWidths=[2*inch, 3*inch])
    invoice_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#666')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#1e1e1e')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(invoice_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Bill To
    bill_to_title = Paragraph("<b>BILL TO:</b>", ParagraphStyle('BillToTitle', parent=styles['Normal'], fontSize=11, textColor=colors.HexColor('#1e1e1e')))
    elements.append(bill_to_title)
    
    bill_to_data = [
        f"<b>{order.user.username}</b>",
        order.user.email,
        f"State: {order.state_union_territory}",
        f"Country: {order.country}",
    ]
    
    for line in bill_to_data:
        elements.append(Paragraph(line, label_style))
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Items Table
    items_data = [['Course', 'Price', 'Quantity', 'Total']]
    
    for item in items:
        items_data.append([
            item.course.title if item.course else 'Deleted Course',
            f"₹{item.price}",
            '1',
            f"₹{item.price}"
        ])
    
    items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('FONTNAME', (1, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))
    
    elements.append(items_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # Summary
    summary_data = [
        ['Subtotal:', f"₹{order.original_price}"],
        ['GST (18%):', f"₹{order.tax}"],
        ['Total Amount:', f"₹{order.total}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[4*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica'),
        ('FONTNAME', (1, 0), (1, -2), 'Helvetica'),
        ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -2), 10),
        ('FONTSIZE', (1, -1), (1, -1), 12),
        ('TEXTCOLOR', (1, -1), (1, -1), colors.HexColor('#ffc107')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('GRID', (0, -1), (-1, -1), 1, colors.HexColor('#ddd')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.4*inch))
    
    # Footer
    footer_text = "Thank you for your purchase! Your courses are now unlocked and ready to access."
    footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#999'), alignment=TA_CENTER, spaceAfter=10))
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.order_id}_{datetime.now().strftime("%Y%m%d")}.pdf"'
    return response


@login_required
def certificate_page(request, course_id):
    """Display certificate for completed course."""
    course_access = get_object_or_404(CourseAccess, user=request.user, course_id=course_id)
    
    # Try to get or create certificate
    certificate, created = Certificate.objects.get_or_create(
        user=request.user,
        course_id=course_id
    )
    
    context = {
        'certificate': certificate,
        'course': course_access.course,
    }
    return render(request, 'core/certificate.html', context)


@login_required
def download_certificate_pdf(request, certificate_id):
    """Generate and download certificate as PDF."""
    certificate = get_object_or_404(Certificate, id=certificate_id, user=request.user)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=1*inch, leftMargin=1*inch, topMargin=1*inch, bottomMargin=1*inch)
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Certificate Title
    title_style = ParagraphStyle(
        'CertTitle',
        parent=styles['Heading1'],
        fontSize=36,
        textColor=colors.HexColor('#ffc107'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    subtitle_style = ParagraphStyle(
        'CertSubtitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=colors.HexColor('#666'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    body_style = ParagraphStyle(
        'CertBody',
        parent=styles['Normal'],
        fontSize=12,
        textColor=colors.HexColor('#1e1e1e'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Title
    title = Paragraph("Certificate of Completion", title_style)
    elements.append(title)
    
    # Subtitle
    subtitle = Paragraph("This is to certify that", subtitle_style)
    elements.append(subtitle)
    
    # Student Name
    name_style = ParagraphStyle(
        'StudentName',
        parent=styles['Normal'],
        fontSize=24,
        textColor=colors.HexColor('#ffc107'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    name = Paragraph(f"{request.user.username}", name_style)
    elements.append(name)
    
    # Certificate Text
    cert_text = f"has successfully completed the course"
    cert_para = Paragraph(cert_text, body_style)
    elements.append(cert_para)
    
    # Course Name
    course_style = ParagraphStyle(
        'CourseName',
        parent=styles['Normal'],
        fontSize=18,
        textColor=colors.HexColor('#ffc107'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    course_name = Paragraph(f"{certificate.course.title}", course_style)
    elements.append(course_name)
    
    elements.append(Spacer(1, 0.4*inch))
    
    # Certificate Details
    details_text = f"""
    <b>Certificate Number:</b> {certificate.certificate_number}<br/>
    <b>Issue Date:</b> {certificate.issue_date.strftime('%d %B %Y')}<br/>
    <b>Course Level:</b> {certificate.course.level}
    """
    details = Paragraph(details_text, body_style)
    elements.append(details)
    
    elements.append(Spacer(1, 0.3*inch))
    
    # Footer
    footer_text = "Tradersfy - Premium Learning Platform"
    footer = Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor('#999'), alignment=TA_CENTER))
    elements.append(footer)
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{certificate.certificate_number}.pdf"'
    return response
