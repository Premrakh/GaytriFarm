from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from django.core.files.base import ContentFile

from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch

def generate_bill_pdf(bill_data):
    """
    Generate a formatted PDF bill with company header, separator, and footer.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=30, leftMargin=30,
        topMargin=30, bottomMargin=18
    )

    elements = []
    styles = getSampleStyleSheet()

    # ---------- Styles ----------
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#222222'),
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    sub_style = ParagraphStyle(
        'SubHeading',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        alignment=TA_CENTER,
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    normal_style = ParagraphStyle(
        'NormalText',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.black
    )

    # ---------- Company Header ----------
    company_name = Paragraph("Gayatri Dairy Farm", title_style)
    tagline = Paragraph("Pure. Fresh. Delivered Daily.", sub_style)
    company_details = Paragraph(
        "Virani Chowk, 1st Floor,Riddhi Siddhi Complex, Rajkot, Gujarat 360002, India<br/>"
        "GSTIN: 27AAECG1234R1Z5 ",
        ParagraphStyle('CompanyInfo', parent=styles['Normal'],
                       alignment=TA_CENTER, fontSize=9,
                       textColor=colors.HexColor('#666666'), spaceAfter=10)
    )

    elements += [company_name, tagline, company_details]

    # ---------- Separator Line ----------
    separator = HRFlowable(
        width="100%",
        thickness=1,
        color=colors.HexColor("#171A17"),  # soft green line
        spaceBefore=10,
        spaceAfter=20
    )
    elements.append(separator)

    # ---------- Bill Title ----------
    title = Paragraph("<b>MONTHLY BILL</b>", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # ---------- Customer Info ----------
    customer_info = [
        ["Customer Name:", bill_data.get('customer_name', 'N/A')],
        ["Customer ID:", bill_data.get('customer_id', 'N/A')],
        ["Billing Period:", f"{bill_data['billing_period']['month_name']} {bill_data['billing_period']['year']}"],
        ["Generated On:", bill_data.get('generated_at', '')[:10]],
    ]
    customer_table = Table(customer_info, colWidths=[2*inch, 4*inch])
    customer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    elements.append(customer_table)
    elements.append(Spacer(1, 20))

    # ---------- Product Breakdown ----------
    elements.append(Paragraph("Product Breakdown", heading_style))
    elements.append(Spacer(1, 12))

    product_data = [['Product Name', 'Unit Price (Rs.)', 'Quantity', 'Total Amount (Rs.)']]
    for p in bill_data.get('product_breakdown', []):
        product_data.append([
            p['product_name'],
            f"Rs. {p['unit_price']}",
            str(p['quantity']),
            f"Rs. {p['total_amount']}"
        ])
    product_table = Table(product_data, colWidths=[2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    elements.append(product_table)
    elements.append(Spacer(1, 20))

    # ---------- Summary ----------
    summary_data = [
        ['Total Items:', str(bill_data.get('total_items', 0))],
        ['Total Amount:', f"Rs. {bill_data.get('total_amount', 0)}"],
    ]
    summary_table = Table(summary_data, colWidths=[4.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
        ('LINEBELOW', (0, -1), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, -1), (-1, -1), colors.whitesmoke),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 30))

    # ---------- Footer ----------
    footer = Paragraph(
        "Thank you for choosing <b>Gayatri Dairy Farm</b>!<br/>"
        "For support or billing queries, email us at "
        "<a href='mailto:support@gayatridairy.com'>support@gayatridairy.com</a>",
        ParagraphStyle('Footer', parent=normal_style, alignment=TA_CENTER,
                       fontSize=9, textColor=colors.HexColor('#666666'))
    )
    elements.append(footer)

    # ---------- Build & Return ----------
    doc.build(elements)
    pdf_content = buffer.getvalue()
    buffer.close()
    return ContentFile(pdf_content)