import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
import tempfile
from io import BytesIO
import base64
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch, mm
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import math

# Page configuration
st.set_page_config(
    page_title="Invoice Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #4f46e5;
        text-align: center;
        margin-bottom: 2rem;
    }
    .invoice-section {
        background-color: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .total-section {
        background-color: #f8fafc;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #4f46e5;
    }
    .action-button {
        width: 100%;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
def init_db():
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT NOT NULL,
            fbr_invoice_number TEXT,
            date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            party_name TEXT NOT NULL,
            party_ntn TEXT,
            items TEXT NOT NULL,
            subtotal REAL NOT NULL,
            gst_total REAL,
            grand_total REAL NOT NULL,
            invoice_type TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Number to words function
def number_to_words(num):
    if num == 0:
        return "Zero Only"
    
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 
            'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 
            'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def convert_less_than_thousand(n):
        if n == 0:
            return ''
        elif n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 != 0 else '')
        else:
            return ones[n // 100] + ' Hundred' + (' ' + convert_less_than_thousand(n % 100) if n % 100 != 0 else '')
    
    if num < 0:
        return 'Minus ' + number_to_words(abs(num))
    
    result = ''
    
    # Crores
    if num >= 10000000:
        crore = num // 10000000
        result += convert_less_than_thousand(crore) + ' Crore '
        num %= 10000000
    
    # Lakhs
    if num >= 100000:
        lakh = num // 100000
        result += convert_less_than_thousand(lakh) + ' Lakh '
        num %= 100000
    
    # Thousands
    if num >= 1000:
        thousand = num // 1000
        result += convert_less_than_thousand(thousand) + ' Thousand '
        num %= 1000
    
    # Hundreds and below
    if num > 0:
        result += convert_less_than_thousand(num)
    
    return result.strip() + ' Only.'

# PDF Generation functions
def generate_invoice_pdf(invoice_data):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1,  # Center
        textColor=colors.HexColor('#4f46e5')
    )
    
    title_text = "SALE TAX INVOICE" if invoice_data['invoice_type'] == 'tax' else "SALE INVOICE"
    elements.append(Paragraph(title_text, title_style))
    
    # Company Info
    company_style = ParagraphStyle(
        'CompanyStyle',
        parent=styles['Normal'],
        fontSize=10,
        alignment=2  # Right
    )
    
    company_info = """
    <b>NUTRION</b><br/>
    Office # 34, Lower Ground, Pearl City Towers<br/>
    Sargodha Road, Faisalabad<br/>
    Email: info@nutrion.pk
    """
    elements.append(Paragraph(company_info, company_style))
    elements.append(Spacer(1, 20))
    
    # Invoice Details
    details_style = ParagraphStyle(
        'DetailsStyle',
        parent=styles['Normal'],
        fontSize=9
    )
    
    details_data = [
        [f"<b>Invoice #:</b> {invoice_data['invoice_number']}", 
         f"<b>Date:</b> {invoice_data['date']}"],
        [f"<b>FBR Invoice #:</b> {invoice_data.get('fbr_invoice_number', 'N/A')}", 
         f"<b>Due Date:</b> {invoice_data['due_date']}"]
    ]
    
    details_table = Table(details_data, colWidths=[3*inch, 3*inch])
    details_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(details_table)
    elements.append(Spacer(1, 20))
    
    # Party Information
    party_info = f"""
    <b>Bill To:</b> {invoice_data['party_name']}<br/>
    <b>NTN:</b> {invoice_data.get('party_ntn', 'N/A')}
    """
    elements.append(Paragraph(party_info, details_style))
    elements.append(Spacer(1, 20))
    
    # Items Table
    items_data = [['Sr.', 'Product Name', 'Description', 'Qty', 'Packing', 'Unit Price', 'Amount']]
    
    for idx, item in enumerate(invoice_data['items'], 1):
        items_data.append([
            str(idx),
            item.get('productName', ''),
            item.get('description', '')[:50] + '...' if len(item.get('description', '')) > 50 else item.get('description', ''),
            str(item.get('qty', 0)),
            item.get('packing', ''),
            f"{item.get('unitPrice', 0):.2f}",
            f"{item.get('amount', 0):.2f}"
        ])
    
    items_table = Table(items_data, colWidths=[0.4*inch, 1.2*inch, 2*inch, 0.6*inch, 0.8*inch, 0.8*inch, 1*inch])
    items_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#374151')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 20))
    
    # Totals
    totals_data = [
        ['Subtotal:', f"Rs {invoice_data['subtotal']:.2f}"],
    ]
    
    if invoice_data['invoice_type'] == 'tax':
        totals_data.append(['GST (18%):', f"Rs {invoice_data.get('gst_total', 0):.2f}"])
    
    totals_data.append(['<b>Grand Total:</b>', f"<b>Rs {invoice_data['grand_total']:.2f}</b>"])
    
    totals_table = Table(totals_data, colWidths=[3*inch, 2*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('FONTNAME', (-1, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (-1, -1), (-1, -1), colors.HexColor('#dc2626')),
    ]))
    elements.append(totals_table)
    elements.append(Spacer(1, 15))
    
    # Amount in words
    amount_words = number_to_words(int(invoice_data['grand_total']))
    words_style = ParagraphStyle(
        'WordsStyle',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#374151')
    )
    elements.append(Paragraph(f"<b>Amount in words:</b> {amount_words}", words_style))
    elements.append(Spacer(1, 20))
    
    # Notes
    notes_style = ParagraphStyle(
        'NotesStyle',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b7280')
    )
    
    notes = """
    <b>Note:</b><br/>
    • All products are supplied as per agreed quality standards and specifications.<br/>
    • For any inquiries or issues related to this invoice, please contact info@nutrion.pk.<br/>
    • Thank you for choosing NUTRION.
    """
    elements.append(Paragraph(notes, notes_style))
    
    # Build PDF
    doc.build(elements)
    
    buffer.seek(0)
    return buffer

# Database operations
def save_invoice_to_db(invoice_data):
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        if 'id' in invoice_data and invoice_data['id']:
            # Update existing invoice
            c.execute('''
                UPDATE invoices 
                SET invoice_number=?, fbr_invoice_number=?, date=?, due_date=?, party_name=?, 
                    party_ntn=?, items=?, subtotal=?, gst_total=?, grand_total=?, invoice_type=?
                WHERE id=?
            ''', (
                invoice_data['invoice_number'],
                invoice_data.get('fbr_invoice_number', ''),
                invoice_data['date'],
                invoice_data['due_date'],
                invoice_data['party_name'],
                invoice_data.get('party_ntn', ''),
                json.dumps(invoice_data['items']),
                invoice_data['subtotal'],
                invoice_data.get('gst_total', 0),
                invoice_data['grand_total'],
                invoice_data['invoice_type'],
                invoice_data['id']
            ))
            invoice_id = invoice_data['id']
        else:
            # Insert new invoice
            c.execute('''
                INSERT INTO invoices 
                (invoice_number, fbr_invoice_number, date, due_date, party_name, party_ntn, 
                 items, subtotal, gst_total, grand_total, invoice_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_data['invoice_number'],
                invoice_data.get('fbr_invoice_number', ''),
                invoice_data['date'],
                invoice_data['due_date'],
                invoice_data['party_name'],
                invoice_data.get('party_ntn', ''),
                json.dumps(invoice_data['items']),
                invoice_data['subtotal'],
                invoice_data.get('gst_total', 0),
                invoice_data['grand_total'],
                invoice_data['invoice_type'],
                datetime.now().isoformat()
            ))
            invoice_id = c.lastrowid
        
        conn.commit()
        return {'success': True, 'invoice_id': invoice_id}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def search_invoices(search_term):
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        search_pattern = f'%{search_term}%'
        c.execute('''
            SELECT * FROM invoices 
            WHERE invoice_number LIKE ? OR party_name LIKE ? OR fbr_invoice_number LIKE ?
            ORDER BY date DESC
        ''', (search_pattern, search_pattern, search_pattern))
        
        invoices = c.fetchall()
        result = []
        
        for invoice in invoices:
            result.append({
                'id': invoice[0],
                'invoice_number': invoice[1],
                'fbr_invoice_number': invoice[2],
                'date': invoice[3],
                'due_date': invoice[4],
                'party_name': invoice[5],
                'party_ntn': invoice[6],
                'items': json.loads(invoice[7]),
                'subtotal': invoice[8],
                'gst_total': invoice[9],
                'grand_total': invoice[10],
                'invoice_type': invoice[11],
                'created_at': invoice[12]
            })
        
        return {'success': True, 'invoices': result}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def get_invoices_by_date_range(start_date, end_date, invoice_type=None):
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        query = 'SELECT * FROM invoices WHERE date BETWEEN ? AND ?'
        params = [start_date, end_date]
        
        if invoice_type:
            query += ' AND invoice_type = ?'
            params.append(invoice_type)
        
        query += ' ORDER BY date'
        c.execute(query, params)
        
        invoices = c.fetchall()
        result = []
        
        for invoice in invoices:
            result.append({
                'id': invoice[0],
                'invoice_number': invoice[1],
                'fbr_invoice_number': invoice[2],
                'date': invoice[3],
                'due_date': invoice[4],
                'party_name': invoice[5],
                'party_ntn': invoice[6],
                'items': json.loads(invoice[7]),
                'subtotal': invoice[8],
                'gst_total': invoice[9],
                'grand_total': invoice[10],
                'invoice_type': invoice[11],
                'created_at': invoice[12]
            })
        
        return {'success': True, 'invoices': result}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

def delete_invoice(invoice_id):
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        c.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
        conn.commit()
        return {'success': True}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()

# Initialize session state
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = [{'productName': '', 'description': '', 'qty': 1, 'packing': '', 'unitPrice': 0}]

if 'current_invoice_id' not in st.session_state:
    st.session_state.current_invoice_id = None

if 'invoice_type' not in st.session_state:
    st.session_state.invoice_type = 'non-tax'

# Product options
product_options = [
    "Antioxdant", "InduceAcid Buty", "InduceAcid Plus", "InduceAcid Liquid", 
    "Linco Magic", "Monica", "SP300", "SP300 Advance", "Strophase G", 
    "Strophase P", "Strozyme NSP", "Strozyme XYL", "Super Ener Emusifier", 
    "Toxin Binder Weilituo", "Toxin Clean"
]

packing_options = ['kg', 'Ltr', 'Can', '25 Ltr', '25 kg']

# Main App
def main():
    st.markdown('<div class="main-header">Invoice Generator</div>', unsafe_allow_html=True)
    
    # Invoice Type Selection
    col1, col2 = st.columns(2)
    with col1:
        invoice_type = st.radio(
            "Invoice Type",
            ["Without GST (Sale Invoice)", "With GST (Sale Tax Invoice)"],
            horizontal=True
        )
        st.session_state.invoice_type = 'tax' if "With GST" in invoice_type else 'non-tax'
    
    with col2:
        invoice_number = st.number_input("Invoice Number", value=1001, min_value=1)
        fbr_invoice_number = st.text_input("FBR Invoice Number (Optional)", placeholder="Optional")
    
    # Dates
    col1, col2 = st.columns(2)
    with col1:
        date = st.date_input("Date", datetime.now())
    with col2:
        due_date = st.date_input("Due Date", datetime.now())
    
    # Party Information
    col1, col2 = st.columns(2)
    with col1:
        party_name = st.text_input("Bill To", placeholder="Enter Party Name")
    with col2:
        party_ntn = st.text_input("NTN", placeholder="Enter NTN Number")
    
    # Invoice Items
    st.markdown("### Items")
    
    # Add item button
    if st.button("+ Add Item"):
        st.session_state.invoice_items.append({'productName': '', 'description': '', 'qty': 1, 'packing': '', 'unitPrice': 0})
    
    # Display items
    items_to_remove = []
    for i, item in enumerate(st.session_state.invoice_items):
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 3, 1, 1, 1, 1])
            
            with col1:
                product_name = st.selectbox(
                    f"Product {i+1}",
                    product_options,
                    key=f"product_{i}",
                    index=product_options.index(item['productName']) if item['productName'] in product_options else 0
                )
                st.session_state.invoice_items[i]['productName'] = product_name
            
            with col2:
                description = st.text_area(
                    "Description",
                    value=item['description'],
                    key=f"desc_{i}",
                    height=30,
                    placeholder="Product description"
                )
                st.session_state.invoice_items[i]['description'] = description
            
            with col3:
                qty = st.number_input(
                    "Qty",
                    value=item['qty'],
                    min_value=0,
                    key=f"qty_{i}",
                    step=1
                )
                st.session_state.invoice_items[i]['qty'] = qty
            
            with col4:
                packing = st.selectbox(
                    "Packing",
                    packing_options,
                    key=f"pack_{i}",
                    index=packing_options.index(item['packing']) if item['packing'] in packing_options else 0
                )
                st.session_state.invoice_items[i]['packing'] = packing
            
            with col5:
                unit_price = st.number_input(
                    "Unit Price",
                    value=item['unitPrice'],
                    min_value=0.0,
                    key=f"price_{i}",
                    step=0.01
                )
                st.session_state.invoice_items[i]['unitPrice'] = unit_price
            
            with col6:
                amount = qty * unit_price
                st.session_state.invoice_items[i]['amount'] = amount
                st.text(f"Rs {amount:.2f}")
                
                if len(st.session_state.invoice_items) > 1:
                    if st.button("❌", key=f"remove_{i}"):
                        items_to_remove.append(i)
    
    # Remove marked items
    for i in sorted(items_to_remove, reverse=True):
        st.session_state.invoice_items.pop(i)
        st.rerun()
    
    # Calculate totals
    subtotal = sum(item.get('amount', 0) for item in st.session_state.invoice_items)
    
    if st.session_state.invoice_type == 'tax':
        gst_total = subtotal * 0.18
        grand_total = subtotal + gst_total
    else:
        gst_total = 0
        grand_total = subtotal
    
    # Display totals
    st.markdown('<div class="total-section">', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Subtotal", f"Rs {subtotal:.2f}")
    
    with col2:
        if st.session_state.invoice_type == 'tax':
            st.metric("GST (18%)", f"Rs {gst_total:.2f}")
    
    with col3:
        st.metric("Grand Total", f"Rs {grand_total:.2f}", delta=None)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action Buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Invoice", use_container_width=True):
            if not party_name:
                st.error("Please enter Party Name")
            elif not any(item['productName'] for item in st.session_state.invoice_items):
                st.error("Please add at least one valid item")
            else:
                invoice_data = {
                    'id': st.session_state.current_invoice_id,
                    'invoice_number': str(invoice_number),
                    'fbr_invoice_number': fbr_invoice_number,
                    'date': date.isoformat(),
                    'due_date': due_date.isoformat(),
                    'party_name': party_name,
                    'party_ntn': party_ntn,
                    'items': st.session_state.invoice_items,
                    'subtotal': subtotal,
                    'gst_total': gst_total,
                    'grand_total': grand_total,
                    'invoice_type': st.session_state.invoice_type
                }
                
                result = save_invoice_to_db(invoice_data)
                if result['success']:
                    st.session_state.current_invoice_id = result['invoice_id']
                    st.success(f"Invoice {'updated' if invoice_data['id'] else 'saved'} successfully!")
                else:
                    st.error(f"Error saving invoice: {result['error']}")
    
    with col2:
        # Generate PDF
        pdf_buffer = generate_invoice_pdf({
            'invoice_number': str(invoice_number),
            'fbr_invoice_number': fbr_invoice_number,
            'date': date.strftime('%Y-%m-%d'),
            'due_date': due_date.strftime('%Y-%m-%d'),
            'party_name': party_name,
            'party_ntn': party_ntn,
            'items': st.session_state.invoice_items,
            'subtotal': subtotal,
            'gst_total': gst_total,
            'grand_total': grand_total,
            'invoice_type': st.session_state.invoice_type
        })
        
        st.download_button(
            label="📄 Download PDF",
            data=pdf_buffer,
            file_name=f"Invoice_{invoice_number}_{party_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    
    with col3:
        if st.button("🆕 New Invoice", use_container_width=True):
            st.session_state.invoice_items = [{'productName': '', 'description': '', 'qty': 1, 'packing': '', 'unitPrice': 0}]
            st.session_state.current_invoice_id = None
            st.rerun()
    
    # Search and Manage Invoices
    st.markdown("---")
    st.markdown("## Search & Manage Invoices")
    
    search_term = st.text_input("Search by invoice number, party name, or FBR number")
    
    if st.button("🔍 Search Invoices"):
        if search_term:
            result = search_invoices(search_term)
            if result['success']:
                st.session_state.search_results = result['invoices']
            else:
                st.error(f"Search error: {result['error']}")
        else:
            st.warning("Please enter a search term")
    
    if 'search_results' in st.session_state and st.session_state.search_results:
        st.markdown("### Search Results")
        
        for invoice in st.session_state.search_results:
            with st.expander(f"Invoice #{invoice['invoice_number']} - {invoice['party_name']} - Rs {invoice['grand_total']:.2f}"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.write(f"**Date:** {invoice['date']}")
                    st.write(f"**Type:** {'Tax Invoice' if invoice['invoice_type'] == 'tax' else 'Non-Tax Invoice'}")
                
                with col2:
                    st.write(f"**Party:** {invoice['party_name']}")
                    st.write(f"**NTN:** {invoice.get('party_ntn', 'N/A')}")
                
                with col3:
                    if st.button("📝 Load", key=f"load_{invoice['id']}"):
                        st.session_state.current_invoice_id = invoice['id']
                        st.session_state.invoice_items = invoice['items']
                        st.session_state.invoice_type = invoice['invoice_type']
                        st.rerun()
                    
                    if st.button("🗑️ Delete", key=f"delete_{invoice['id']}"):
                        if delete_invoice(invoice['id'])['success']:
                            st.success("Invoice deleted successfully!")
                            st.rerun()
                        else:
                            st.error("Error deleting invoice")
    
    # Bulk Download Section
    st.markdown("---")
    st.markdown("## Download Invoices by Date Range")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", datetime.now())
    with col2:
        end_date = st.date_input("To Date", datetime.now())
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download Tax Invoices", use_container_width=True):
            result = get_invoices_by_date_range(start_date.isoformat(), end_date.isoformat(), 'tax')
            if result['success']:
                if result['invoices']:
                    # Create a combined PDF (simplified - in practice you might want to create separate PDFs)
                    st.success(f"Found {len(result['invoices'])} tax invoices")
                    # Here you would implement combined PDF generation
                else:
                    st.warning("No tax invoices found in the selected date range")
            else:
                st.error(f"Error: {result['error']}")
    
    with col2:
        if st.button("📥 Download Non-Tax Invoices", use_container_width=True):
            result = get_invoices_by_date_range(start_date.isoformat(), end_date.isoformat(), 'non-tax')
            if result['success']:
                if result['invoices']:
                    st.success(f"Found {len(result['invoices'])} non-tax invoices")
                    # Here you would implement combined PDF generation
                else:
                    st.warning("No non-tax invoices found in the selected date range")
            else:
                st.error(f"Error: {result['error']}")

if __name__ == "__main__":
    main()
