from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from datetime import datetime
from num2words import num2words

def _safe_fetch_image(qr_field):
    """Fetch image bytes from URL, return BytesIO or None."""
    if not qr_field:
        return None
    
    try:
        # If it's a Django FileField/ImageField object
        if hasattr(qr_field, 'read'):
            # Read file content directly
            qr_field.open('rb')  # Open in binary read mode
            content = qr_field.read()
            qr_field.close()
            return BytesIO(content)
        return None
    except Exception as e:
        print(f"Error fetching QR image: {e}")
        return None


def _amount_to_words(amount):
    try:
        amt = float(amount)
    except:
        return str(amount)

    if num2words:
        try:
            words = num2words(int(round(amt)), lang="en_IN")
            return f"{words.title()} Rupees Only"
        except:
            pass

    return f"{int(round(amt))} Rupees Only"



def generate_bill_pdf(bill_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=60, bottomMargin=18
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0B4F8A'),
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        spaceAfter=8
    )
    normal = ParagraphStyle('normal', parent=styles['Normal'], fontSize=10, fontName="Helvetica")
    bold = ParagraphStyle('bold', parent=styles['Normal'], fontSize=10, fontName="Helvetica-Bold")
    right_normal = ParagraphStyle('right_normal', parent=styles['Normal'], alignment=TA_RIGHT, fontSize=10)

    # Calculate available width (A4 width - left margin - right margin)
    # A4 width = 8.27 inches, with 30pt margins on each side
    page_width = A4[0] - 60  # 60 = leftMargin + rightMargin
    
    elements = []

    # ---------------- HEADER (Distributor Left) ----------------
    dist = bill_data.get('supplier', {})
    dist_name = dist.get('name') or dist.get('user_name')

    header_lines = [f"<b>{dist_name.upper()}</b>"]
    if dist.get('address'): header_lines.append("Address: " + dist.get('address'))
    if dist.get('mobile'): header_lines.append("Mobile: " + dist.get('mobile'))
    if dist.get('email'): header_lines.append("Email: " + dist.get('email'))
    if dist.get('gst_no'): header_lines.append("GSTIN: " + dist.get('gst_no'))
    if dist.get('state'): header_lines.append("State: " + dist.get('state'))

    distributor_para = Paragraph("<br/>".join(header_lines), normal)

    header = Table([[distributor_para, ""]], colWidths=[page_width * 0.62, page_width * 0.38])
    header.setStyle(TableStyle([
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.lightgrey),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 8))

    # ---------------- TAX INVOICE TITLE ----------------
    elements.append(Paragraph("<b>Tax Invoice</b>", title_style))
    elements.append(Spacer(1, 10))

    # ---------------- Invoice Details (Right) + Bill To ----------------
    generated = bill_data.get('generated_at', '')[:10]
    try:
        inv_date = datetime.fromisoformat(generated).strftime("%d-%m-%Y")
    except:
        inv_date = generated

    inv_block = Paragraph(
        f"<b>Invoice Details</b><br/>"
        f"Invoice No: {bill_data.get('bill_id')}<br/>"
        f"Date: {inv_date}",
        right_normal
    )

    customer = bill_data.get('user', {})
    customer_lines = [
        f"<b>Bill To:</b>"
    ]
    customer_name = customer.get('name') or customer.get('user_name')
    if customer_name: customer_lines.append(customer_name)
    if customer.get('address'): customer_lines.append(customer.get('address'))
    if customer.get('mobile'): customer_lines.append("Contact No.: " + customer.get('mobile'))
    if customer.get('email'): customer_lines.append("Email: " + customer.get('email'))

    c_para = Paragraph("<br/>".join(customer_lines), normal)

    section = Table([[c_para, inv_block]], colWidths=[page_width * 0.62, page_width * 0.38])
    section.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(section)
    elements.append(Spacer(1, 12))

    # ---------------- PRODUCT BREAKDOWN TABLE ----------------
    prods = bill_data.get('product_breakdown', [])
    total_items = bill_data.get('total_items')
    grand_total = float(bill_data.get('total_amount'))

    rows = [['#', 'Item Name', 'Quantity', 'Unit', 'Price/Unit', 'Amount']]
    for i, p in enumerate(prods, start=1):
        name = p.get('product_name')
        qty = int(p.get('total_quantity', 0))
        unit = 'ltr'
        price = float(p.get('unit_price', 0))
        amt = float(p.get('total_amount', price * qty))

        rows.append([
            str(i),
            Paragraph(name, normal),
            str(qty),
            str(unit),
            f"Rs. {price:,.2f}",
            f"Rs. {amt:,.2f}"
        ])
    rows.append([
        '',
        Paragraph("<b>Total</b>", bold),
        Paragraph(f"<b>{total_items}</b>", bold),
        '',
        '',
        Paragraph(f"<b>Rs. {grand_total:,.2f}</b>", bold)
    ])

    # Use proportional widths based on page_width
    table = Table(
        rows,
        colWidths=[
            page_width * 0.07,   # # column
            page_width * 0.38,   # Item Name
            page_width * 0.12,   # Quantity
            page_width * 0.10,   # Unit
            page_width * 0.16,   # Price/Unit
            page_width * 0.17    # Amount
        ],
        repeatRows=1
    )

    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F7F9FC')]),
        # Align money columns right
        ('ALIGN', (4, 1), (5, -1), 'RIGHT'),
        # Bold total row
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F5FF')),
        ('ALIGN', (2, -1), (2, -1), 'CENTER'),
        # Remove extra padding to align with page margins
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # ---------------- AMOUNT IN WORDS ----------------
    amount_para = Paragraph(f"<b>Invoice Amount In Words:</b> <br/> {_amount_to_words(grand_total)}", normal)
    amount_table = Table([[amount_para]], colWidths=[page_width])
    amount_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(amount_table)
    elements.append(Spacer(1, 10))

    # ---------------- TERMS & CONDITIONS ----------------
    terms = "According to our farm’s policy, no claims will be accepted after delivery. Payment should be made on time."
    terms_title = Paragraph("<b>Terms And Conditions</b>", bold)
    terms_content = Paragraph(terms, normal)
    
    terms_table = Table([[terms_title]], colWidths=[page_width])
    terms_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(terms_table)
    
    terms_content_table = Table([[terms_content]], colWidths=[page_width])
    terms_content_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(terms_content_table)
    elements.append(Spacer(1, 14))

    # ---------------- QR + BANK ----------------
    bank = bill_data.get('bank_account', {})

    qr_img = None
    
    bank_lines = []
    if bank:
        qr_io = _safe_fetch_image(bank.get('qr')) ### error
        if qr_io:
            qr_img = Image(qr_io, width=1.2*inch, height=1.2*inch)
        bank_lines.append('<b>Pay To:</b>')
        if bank.get('bank_name'): bank_lines.append(f"Bank Name: {bank.get('bank_name')}")
        if bank.get('account_no'): bank_lines.append(f"Account No: {bank.get('account_no')}")
        if bank.get('ifsc_code'): bank_lines.append(f"IFSC Code: {bank.get('ifsc_code')}")
        if bank.get('holder_name'): bank_lines.append(f"Account Holder: {bank.get('holder_name')}")

    bank_para = Paragraph("<br/>".join(bank_lines), normal)

    # Table layout: QR on left, Bank details on right
    row = [qr_img if qr_img else '', bank_para]
    t = Table([row], colWidths=[page_width * 0.23, page_width * 0.77])
    t.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, 0), 0.5, colors.grey),
    ]))

    elements.append(t)
    elements.append(Spacer(1, 12))

    # Build PDF
    doc.build(elements)
    pdf_data = buffer.getvalue()
    buffer.close()
    return ContentFile(pdf_data)