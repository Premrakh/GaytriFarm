from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.core.files.base import ContentFile


def generate_bill_pdf(bill_data):
    """
    Generate a formatted PDF bill from bill data
    
    Args:
        bill_data: Dictionary containing bill information
        
    Returns:
        ContentFile: PDF file content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30,
                           topMargin=30, bottomMargin=18)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    
    # Title
    title = Paragraph("MONTHLY BILL", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Customer Information
    customer_info = [
        ["Customer Name:", bill_data.get('customer_name', 'N/A')],
        ["Customer ID:", bill_data.get('customer_id', 'N/A')],
        ["Billing Period:", f"{bill_data['billing_period']['month_name']} {bill_data['billing_period']['year']}"],
        ["Generated On:", bill_data.get('generated_at', '')[:10]],
    ]
    
    customer_table = Table(customer_info, colWidths=[2*inch, 4*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(customer_table)
    elements.append(Spacer(1, 20))
    
    # Product Breakdown Section
    elements.append(Paragraph("Product Breakdown", heading_style))
    elements.append(Spacer(1, 12))
    
    # Product table header
    product_data = [['Product Name', 'Unit Price (Rs.)', 'Quantity', 'Total Amount (Rs.)']]
    
    # Add product rows
    for product in bill_data.get('product_breakdown', []):
        product_data.append([
            product['product_name'],
            f"Rs.{product['unit_price']}",
            str(product['quantity']),
            f"Rs.{product['total_amount']}"
        ])
    
    # Product table
    product_table = Table(product_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    product_table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Body styling
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Grid
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
    ]))
    
    elements.append(product_table)
    elements.append(Spacer(1, 20))
    
    # Summary Section
    summary_data = [
        ['Total Items:', str(bill_data.get('total_items', 0))],
        ['Total Amount:', f"Rs.{bill_data.get('total_amount', 0)}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[4.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LINEABOVE', (0, 0), (-1, 0), 2, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 2, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 30))
    
    # Footer
    footer_text = Paragraph(
        "<i>Thank you for your business!</i><br/><br/>"
        "For any queries, please contact us.",
        ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER, 
                      fontSize=9, textColor=colors.grey)
    )
    elements.append(footer_text)
    
    # Build PDF
    doc.build(elements)
    
    # Get PDF content
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return ContentFile(pdf_content)
