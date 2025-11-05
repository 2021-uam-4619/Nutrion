import streamlit as st
import sqlite3
import json
import os
from datetime import datetime
import tempfile
import base64
from fpdf import FPDF
import pandas as pd
import requests

# Initialize session state
def init_session_state():
    if 'invoice_items_without_gst' not in st.session_state:
        st.session_state.invoice_items_without_gst = [{
            'product_name': '', 'description': '', 'qty': 1, 'packing': '', 'unit_price': 0, 'amount': 0
        }]
    if 'invoice_items_with_gst' not in st.session_state:
        st.session_state.invoice_items_with_gst = [{
            'product_name': '', 'description': '', 'qty': 1, 'packing': '', 'unit_price_incl_gst': 0, 
            'base_amount': 0, 'gst_amount': 0, 'total_amount': 0
        }]
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = 'without_gst'
    if 'current_invoice_id' not in st.session_state:
        st.session_state.current_invoice_id = None
    if 'db_initialized' not in st.session_state:
        st.session_state.db_initialized = False

# Download and integrate existing database
def download_and_integrate_db():
    """Download existing database from GitHub and integrate with current database"""
    try:
        # GitHub raw content URL (aap apni actual URL yahan dalen)
        github_db_url = "https://github.com/yourusername/yourrepo/raw/main/invoices.db"
        
        # Temporary file for downloaded database
        temp_db_path = "temp_invoices.db"
        
        # Download the database file
        response = requests.get(github_db_url)
        if response.status_code == 200:
            with open(temp_db_path, 'wb') as f:
                f.write(response.content)
            
            # Connect to both databases
            conn_main = sqlite3.connect('invoices.db')
            conn_temp = sqlite3.connect(temp_db_path)
            
            # Copy data from temp database to main database
            temp_cursor = conn_temp.cursor()
            main_cursor = conn_main.cursor()
            
            # Check if tables exist in temp database
            temp_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")
            if temp_cursor.fetchone():
                # Get all invoices from temp database
                temp_cursor.execute("SELECT * FROM invoices")
                temp_invoices = temp_cursor.fetchall()
                
                # Insert into main database if they don't exist
                for invoice in temp_invoices:
                    # Check if invoice already exists
                    main_cursor.execute("SELECT id FROM invoices WHERE invoice_number = ?", (invoice[1],))
                    if not main_cursor.fetchone():
                        main_cursor.execute('''
                            INSERT INTO invoices 
                            (invoice_number, fbr_invoice_number, date, due_date, party_name, party_ntn, items, 
                             subtotal, gst_total, grand_total, invoice_type, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', invoice[1:])
                
                conn_main.commit()
                st.success(f"Successfully integrated {len(temp_invoices)} invoices from existing database!")
            
            # Close connections
            conn_temp.close()
            conn_main.close()
            
            # Clean up temporary file
            os.remove(temp_db_path)
            
        else:
            st.warning("Could not download existing database file. Starting with fresh database.")
            
    except Exception as e:
        st.warning(f"Could not integrate existing database: {str(e)}")

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
    
    # Download and integrate existing database only once
    if not st.session_state.db_initialized:
        download_and_integrate_db()
        st.session_state.db_initialized = True

# Product and packing options
product_options = [
    "Antioxdant", "InduceAcid Buty", "InduceAcid Plus", "InduceAcid Liquid", 
    "Linco Magic", "Monica", "SP300", "SP300 Advance", "Strophase G", 
    "Strophase P", "Strozyme NSP", "Strozyme XYL", "Super Ener Emusifier", 
    "Toxin Binder Weilituo", "Toxin Clean"
]

packing_options = ['kg', 'Ltr', 'Can', '25 Ltr', '25 kg']

# PDF Generation with HTML template style
class InvoicePDF(FPDF):
    def header(self):
        pass
    
    def footer(self):
        pass

def generate_invoice_pdf(invoice_data):
    pdf = InvoicePDF()
    pdf.add_page()
    
    # Set up basic styling similar to HTML template
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "INVOICE", 0, 1, "C")
    
    # Add invoice details
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"Invoice #: {invoice_data['invoice_number']}", 0, 1)
    pdf.cell(0, 10, f"Date: {invoice_data['date']}", 0, 1)
    pdf.cell(0, 10, f"Party: {invoice_data['party_name']}", 0, 1)
    
    # Add items table
    pdf.cell(60, 10, "Product", 1)
    pdf.cell(40, 10, "Qty", 1)
    pdf.cell(40, 10, "Price", 1)
    pdf.cell(40, 10, "Amount", 1)
    pdf.ln()
    
    for item in invoice_data['items']:
        pdf.cell(60, 10, item['product_name'][:20], 1)
        pdf.cell(40, 10, str(item['qty']), 1)
        pdf.cell(40, 10, f"{item.get('unit_price', 0):.2f}", 1)
        pdf.cell(40, 10, f"{item.get('amount', 0):.2f}", 1)
        pdf.ln()
    
    # Add totals
    pdf.cell(140, 10, "Subtotal:", 1)
    pdf.cell(40, 10, f"{invoice_data['subtotal']:.2f}", 1)
    pdf.ln()
    
    if invoice_data['invoice_type'] == 'tax':
        pdf.cell(140, 10, "GST (18%):", 1)
        pdf.cell(40, 10, f"{invoice_data['gst_total']:.2f}", 1)
        pdf.ln()
    
    pdf.cell(140, 10, "Grand Total:", 1)
    pdf.cell(40, 10, f"{invoice_data['grand_total']:.2f}", 1)
    
    return pdf

# Database operations with error handling
def save_invoice(invoice_data):
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        if invoice_data.get('id'):
            c.execute('''
                UPDATE invoices SET 
                invoice_number=?, fbr_invoice_number=?, date=?, due_date=?, party_name=?, party_ntn=?,
                items=?, subtotal=?, gst_total=?, grand_total=?, invoice_type=?
                WHERE id=?
            ''', (
                invoice_data['invoice_number'], invoice_data.get('fbr_invoice_number', ''),
                invoice_data['date'], invoice_data['due_date'], invoice_data['party_name'],
                invoice_data.get('party_ntn', ''), json.dumps(invoice_data['items']),
                invoice_data['subtotal'], invoice_data.get('gst_total', 0),
                invoice_data['grand_total'], invoice_data['invoice_type'], invoice_data['id']
            ))
        else:
            c.execute('''
                INSERT INTO invoices 
                (invoice_number, fbr_invoice_number, date, due_date, party_name, party_ntn, items, 
                 subtotal, gst_total, grand_total, invoice_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_data['invoice_number'], invoice_data.get('fbr_invoice_number', ''),
                invoice_data['date'], invoice_data['due_date'], invoice_data['party_name'],
                invoice_data.get('party_ntn', ''), json.dumps(invoice_data['items']),
                invoice_data['subtotal'], invoice_data.get('gst_total', 0),
                invoice_data['grand_total'], invoice_data['invoice_type'], datetime.now().isoformat()
            ))
            invoice_data['id'] = c.lastrowid
        
        conn.commit()
        return invoice_data['id']
    except Exception as e:
        conn.rollback()
        raise e
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
        
        invoices = []
        for row in c.fetchall():
            # Handle JSON parsing with error handling
            items_data = row[7]
            if items_data and isinstance(items_data, str):
                try:
                    items = json.loads(items_data)
                except json.JSONDecodeError:
                    items = []
            else:
                items = []
                
            invoices.append({
                'id': row[0], 'invoice_number': row[1], 'fbr_invoice_number': row[2],
                'date': row[3], 'due_date': row[4], 'party_name': row[5], 'party_ntn': row[6],
                'items': items, 'subtotal': row[8], 'gst_total': row[9],
                'grand_total': row[10], 'invoice_type': row[11], 'created_at': row[12]
            })
        
        return invoices
    finally:
        conn.close()

def get_invoice_by_id(invoice_id):
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        c.execute('SELECT * FROM invoices WHERE id = ?', (invoice_id,))
        row = c.fetchone()
        
        if row:
            # Handle JSON parsing with error handling
            items_data = row[7]
            if items_data and isinstance(items_data, str):
                try:
                    items = json.loads(items_data)
                except json.JSONDecodeError:
                    items = []
            else:
                items = []
                
            invoice = {
                'id': row[0], 'invoice_number': row[1], 'fbr_invoice_number': row[2],
                'date': row[3], 'due_date': row[4], 'party_name': row[5], 'party_ntn': row[6],
                'items': items, 'subtotal': row[8], 'gst_total': row[9],
                'grand_total': row[10], 'invoice_type': row[11], 'created_at': row[12]
            }
            return invoice
        
        return None
    finally:
        conn.close()

def delete_invoice(invoice_id):
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        c.execute('DELETE FROM invoices WHERE id = ?', (invoice_id,))
        success = c.rowcount > 0
        conn.commit()
        return success
    finally:
        conn.close()

def get_invoices_by_date_range(start_date, end_date, invoice_type=None):
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        if invoice_type:
            c.execute('SELECT * FROM invoices WHERE date BETWEEN ? AND ? AND invoice_type = ?', 
                     (start_date, end_date, invoice_type))
        else:
            c.execute('SELECT * FROM invoices WHERE date BETWEEN ? AND ?', (start_date, end_date))
        
        invoices = []
        for row in c.fetchall():
            # Handle JSON parsing with error handling
            items_data = row[7]
            if items_data and isinstance(items_data, str):
                try:
                    items = json.loads(items_data)
                except json.JSONDecodeError:
                    items = []
            else:
                items = []
                
            invoices.append({
                'id': row[0], 'invoice_number': row[1], 'fbr_invoice_number': row[2],
                'date': row[3], 'due_date': row[4], 'party_name': row[5], 'party_ntn': row[6],
                'items': items, 'subtotal': row[8], 'gst_total': row[9],
                'grand_total': row[10], 'invoice_type': row[11], 'created_at': row[12]
            })
        
        return invoices
    finally:
        conn.close()

def get_all_invoices_count():
    """Get total count of invoices in database"""
    conn = sqlite3.connect('invoices.db')
    c = conn.cursor()
    
    try:
        c.execute('SELECT COUNT(*) FROM invoices')
        count = c.fetchone()[0]
        return count
    finally:
        conn.close()

# Streamlit UI Components with HTML template styling
def render_invoice_form():
    # Custom CSS for HTML template look
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f2937;
            text-align: center;
            margin-bottom: 2rem;
        }
        .invoice-card {
            background-color: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }
        .section-header {
            font-size: 1.5rem;
            font-weight: 600;
            color: #374151;
            margin-bottom: 1rem;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 0.5rem;
        }
        .tab-container {
            background-color: #f8fafc;
            border-radius: 0.5rem;
            padding: 1rem;
        }
        .total-box {
            background-color: #f0f9ff;
            border: 2px solid #e0f2fe;
            border-radius: 0.5rem;
            padding: 1rem;
            margin-top: 1rem;
        }
        .action-button {
            width: 100%;
            margin: 0.5rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">Invoice Generator</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="invoice-card">', unsafe_allow_html=True)
        
        # Header section with columns
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown('<div class="section-header">Invoice Details</div>', unsafe_allow_html=True)
        
        with col2:
            invoice_number = st.number_input("**Invoice #**", value=1001, min_value=1, step=1, key="invoice_number")
            fbr_invoice_number = st.text_input("**FBR Invoice #**", placeholder="Optional", key="fbr_invoice")
            date = st.date_input("**Date**", value=datetime.now(), key="date")
            due_date = st.date_input("**Due Date**", value=datetime.now(), key="due_date")
        
        # Party information
        party_name = st.text_input("**Bill To**", placeholder="Enter Party Name", key="party_name")
        party_ntn = st.text_input("**NTN**", placeholder="Enter NTN Number", key="party_ntn")
        
        # Tab selection
        st.markdown('<div class="section-header">Items</div>', unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["**Without GST (Sale Invoice)**", "**With GST (Sale Tax Invoice)**"])
        
        # Calculate totals
        subtotal = 0
        gst_total = 0
        grand_total = 0
        
        # Without GST Tab
        with tab1:
            st.session_state.active_tab = 'without_gst'
            st.subheader("Items (Without GST)")
            
            # Items table
            for i, item in enumerate(st.session_state.invoice_items_without_gst):
                with st.container():
                    cols = st.columns([2, 3, 1, 1, 1, 1])
                    
                    with cols[0]:
                        product_name = st.selectbox(
                            "Product", 
                            options=[""] + product_options,
                            index=product_options.index(item['product_name']) + 1 if item['product_name'] in product_options else 0,
                            key=f"product_without_{i}"
                        )
                        st.session_state.invoice_items_without_gst[i]['product_name'] = product_name
                    
                    with cols[1]:
                        description = st.text_area(
                            "Description", 
                            value=item['description'],
                            placeholder="Description",
                            key=f"desc_without_{i}",
                            height=30
                        )
                        st.session_state.invoice_items_without_gst[i]['description'] = description
                    
                    with cols[2]:
                        qty = st.number_input("Qty", value=item['qty'], min_value=0, step=1, key=f"qty_without_{i}")
                        st.session_state.invoice_items_without_gst[i]['qty'] = qty
                    
                    with cols[3]:
                        packing = st.selectbox(
                            "Packing", 
                            options=[""] + packing_options,
                            index=packing_options.index(item['packing']) + 1 if item['packing'] in packing_options else 0,
                            key=f"packing_without_{i}"
                        )
                        st.session_state.invoice_items_without_gst[i]['packing'] = packing
                    
                    with cols[4]:
                        unit_price = st.number_input("Unit Price", value=float(item['unit_price']), min_value=0.0, step=0.01, key=f"price_without_{i}")
                        st.session_state.invoice_items_without_gst[i]['unit_price'] = unit_price
                    
                    with cols[5]:
                        amount = qty * unit_price
                        st.session_state.invoice_items_without_gst[i]['amount'] = amount
                        st.text(f"**Amount:** {amount:.2f}")
                    
                    # Remove button
                    remove_col1, remove_col2 = st.columns([5, 1])
                    with remove_col2:
                        if st.button("🗑️ Remove", key=f"remove_without_{i}") and len(st.session_state.invoice_items_without_gst) > 1:
                            st.session_state.invoice_items_without_gst.pop(i)
                            st.rerun()
                
                st.divider()
            
            # Add row button
            if st.button("➕ Add Item", key="add_without_gst"):
                st.session_state.invoice_items_without_gst.append({
                    'product_name': '', 'description': '', 'qty': 1, 'packing': '', 'unit_price': 0, 'amount': 0
                })
                st.rerun()
            
            # Calculate totals for without GST
            subtotal = sum(item['amount'] for item in st.session_state.invoice_items_without_gst)
            grand_total = subtotal
        
        # With GST Tab
        with tab2:
            st.session_state.active_tab = 'with_gst'
            st.subheader("Items (With GST)")
            
            for i, item in enumerate(st.session_state.invoice_items_with_gst):
                with st.container():
                    cols = st.columns([2, 2, 1, 1, 1, 1, 1, 1])
                    
                    with cols[0]:
                        product_name = st.selectbox(
                            "Product", 
                            options=[""] + product_options,
                            index=product_options.index(item['product_name']) + 1 if item['product_name'] in product_options else 0,
                            key=f"product_with_{i}"
                        )
                        st.session_state.invoice_items_with_gst[i]['product_name'] = product_name
                    
                    with cols[1]:
                        description = st.text_area(
                            "Description", 
                            value=item['description'],
                            placeholder="Description",
                            key=f"desc_with_{i}",
                            height=30
                        )
                        st.session_state.invoice_items_with_gst[i]['description'] = description
                    
                    with cols[2]:
                        qty = st.number_input("Qty", value=item['qty'], min_value=0, step=1, key=f"qty_with_{i}")
                        st.session_state.invoice_items_with_gst[i]['qty'] = qty
                    
                    with cols[3]:
                        packing = st.selectbox(
                            "Packing", 
                            options=[""] + packing_options,
                            index=packing_options.index(item['packing']) + 1 if item['packing'] in packing_options else 0,
                            key=f"packing_with_{i}"
                        )
                        st.session_state.invoice_items_with_gst[i]['packing'] = packing
                    
                    with cols[4]:
                        unit_price_incl_gst = st.number_input("Unit Price (Incl. GST)", value=float(item['unit_price_incl_gst']), 
                                                             min_value=0.0, step=0.01, key=f"price_with_{i}")
                        st.session_state.invoice_items_with_gst[i]['unit_price_incl_gst'] = unit_price_incl_gst
                    
                    # Calculate GST amounts
                    total_amount = qty * unit_price_incl_gst
                    base_amount = total_amount / 1.18
                    gst_amount = total_amount - base_amount
                    
                    st.session_state.invoice_items_with_gst[i]['total_amount'] = total_amount
                    st.session_state.invoice_items_with_gst[i]['base_amount'] = base_amount
                    st.session_state.invoice_items_with_gst[i]['gst_amount'] = gst_amount
                    
                    with cols[5]:
                        st.text(f"**Base:** {base_amount:.2f}")
                    with cols[6]:
                        st.text(f"**GST:** {gst_amount:.2f}")
                    with cols[7]:
                        st.text(f"**Total:** {total_amount:.2f}")
                    
                    # Remove button
                    remove_col1, remove_col2 = st.columns([7, 1])
                    with remove_col2:
                        if st.button("🗑️ Remove", key=f"remove_with_{i}") and len(st.session_state.invoice_items_with_gst) > 1:
                            st.session_state.invoice_items_with_gst.pop(i)
                            st.rerun()
                
                st.divider()
            
            # Add row button
            if st.button("➕ Add Item", key="add_with_gst"):
                st.session_state.invoice_items_with_gst.append({
                    'product_name': '', 'description': '', 'qty': 1, 'packing': '', 
                    'unit_price_incl_gst': 0, 'base_amount': 0, 'gst_amount': 0, 'total_amount': 0
                })
                st.rerun()
            
            # Calculate totals for with GST
            subtotal = sum(item['base_amount'] for item in st.session_state.invoice_items_with_gst)
            gst_total = sum(item['gst_amount'] for item in st.session_state.invoice_items_with_gst)
            grand_total = subtotal + gst_total
        
        # Display totals in styled box
        st.markdown('<div class="total-box">', unsafe_allow_html=True)
        st.subheader("Totals")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Subtotal", f"₹{subtotal:.2f}")
        with col2:
            if st.session_state.active_tab == 'with_gst':
                st.metric("GST (18%)", f"₹{gst_total:.2f}")
        with col3:
            st.metric("Grand Total", f"₹{grand_total:.2f}", delta=None)
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return {
        'invoice_number': invoice_number,
        'fbr_invoice_number': fbr_invoice_number,
        'date': date.isoformat(),
        'due_date': due_date.isoformat(),
        'party_name': party_name,
        'party_ntn': party_ntn,
        'subtotal': subtotal,
        'gst_total': gst_total,
        'grand_total': grand_total,
        'invoice_type': 'tax' if st.session_state.active_tab == 'with_gst' else 'non-tax'
    }

def render_search_section():
    st.markdown("""
        <style>
        .search-section {
            background-color: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    st.header("🔍 Search & Manage Invoices")
    
    # Show total invoices count
    total_invoices = get_all_invoices_count()
    st.info(f"**Total Invoices in Database:** {total_invoices}")
    
    search_term = st.text_input("Search by invoice number, party name, or FBR number", placeholder="Enter search term...")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔍 Search", use_container_width=True):
            if search_term:
                invoices = search_invoices(search_term)
                if invoices:
                    st.subheader("Search Results")
                    
                    # Display results in a table
                    data = []
                    for invoice in invoices:
                        data.append({
                            'Invoice #': invoice['invoice_number'],
                            'Party Name': invoice['party_name'],
                            'Date': invoice['date'],
                            'Type': 'Tax Invoice' if invoice['invoice_type'] == 'tax' else 'Non-Tax Invoice',
                            'Total': f"₹{invoice['grand_total']:.2f}",
                            'ID': invoice['id']
                        })
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                    
                    # Action buttons for each invoice
                    for invoice in invoices:
                        with st.expander(f"📄 Invoice {invoice['invoice_number']} - {invoice['party_name']}"):
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                if st.button("📝 Load", key=f"load_{invoice['id']}", use_container_width=True):
                                    load_invoice(invoice)
                            
                            with col2:
                                if st.button("📥 PDF", key=f"pdf_{invoice['id']}", use_container_width=True):
                                    pdf = generate_invoice_pdf(invoice)
                                    pdf_output = pdf.output(dest='S').encode('latin1')
                                    st.download_button(
                                        label="Download PDF",
                                        data=pdf_output,
                                        file_name=f"Invoice_{invoice['invoice_number']}.pdf",
                                        mime="application/pdf",
                                        key=f"download_{invoice['id']}",
                                        use_container_width=True
                                    )
                            
                            with col3:
                                if st.button("🔄 Update", key=f"update_{invoice['id']}", use_container_width=True):
                                    st.info("Update functionality would be implemented here")
                            
                            with col4:
                                if st.button("🗑️ Delete", key=f"delete_{invoice['id']}", use_container_width=True):
                                    if delete_invoice(invoice['id']):
                                        st.success("✅ Invoice deleted successfully!")
                                        st.rerun()
                                    else:
                                        st.error("❌ Error deleting invoice")
                else:
                    st.warning("No invoices found matching your search.")
            else:
                st.warning("Please enter a search term.")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_bulk_download():
    st.markdown("""
        <style>
        .bulk-section {
            background-color: white;
            padding: 2rem;
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="bulk-section">', unsafe_allow_html=True)
    st.header("📥 Download Invoices by Date Range")
    
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input("From Date", value=datetime.now())
    with col2:
        end_date = st.date_input("To Date", value=datetime.now())
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download Tax Invoices", use_container_width=True):
            try:
                invoices = get_invoices_by_date_range(start_date.isoformat(), end_date.isoformat(), 'tax')
                if invoices:
                    st.success(f"✅ Found {len(invoices)} tax invoices")
                    # Create zip file or combined PDF logic would go here
                    for invoice in invoices:
                        pdf = generate_invoice_pdf(invoice)
                        pdf_output = pdf.output(dest='S').encode('latin1')
                        st.download_button(
                            label=f"Download Invoice {invoice['invoice_number']}",
                            data=pdf_output,
                            file_name=f"Invoice_{invoice['invoice_number']}.pdf",
                            mime="application/pdf",
                            key=f"bulk_tax_{invoice['id']}"
                        )
                else:
                    st.warning("No tax invoices found in the selected date range.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        if st.button("📥 Download Non-Tax Invoices", use_container_width=True):
            try:
                invoices = get_invoices_by_date_range(start_date.isoformat(), end_date.isoformat(), 'non-tax')
                if invoices:
                    st.success(f"✅ Found {len(invoices)} non-tax invoices")
                    for invoice in invoices:
                        pdf = generate_invoice_pdf(invoice)
                        pdf_output = pdf.output(dest='S').encode('latin1')
                        st.download_button(
                            label=f"Download Invoice {invoice['invoice_number']}",
                            data=pdf_output,
                            file_name=f"Invoice_{invoice['invoice_number']}.pdf",
                            mime="application/pdf",
                            key=f"bulk_non_tax_{invoice['id']}"
                        )
                else:
                    st.warning("No non-tax invoices found in the selected date range.")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def load_invoice(invoice):
    st.session_state.current_invoice_id = invoice['id']
    
    # Set basic fields
    st.session_state.invoice_number = int(invoice['invoice_number'])
    st.session_state.fbr_invoice = invoice.get('fbr_invoice_number', '')
    st.session_state.date = datetime.fromisoformat(invoice['date'])
    st.session_state.due_date = datetime.fromisoformat(invoice['due_date'])
    st.session_state.party_name = invoice['party_name']
    st.session_state.party_ntn = invoice.get('party_ntn', '')
    
    # Load items based on invoice type
    if invoice['invoice_type'] == 'tax':
        st.session_state.active_tab = 'with_gst'
        st.session_state.invoice_items_with_gst = invoice['items']
    else:
        st.session_state.active_tab = 'without_gst'
        st.session_state.invoice_items_without_gst = invoice['items']
    
    st.success("✅ Invoice loaded successfully!")

def main():
    st.set_page_config(
        page_title="Invoice Generator", 
        page_icon="📄", 
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .stApp {
            background-color: #f8fafc;
        }
        .css-1d391kg {
            padding: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state and database
    init_session_state()
    init_db()
    
    # Main invoice form
    invoice_data = render_invoice_form()
    
    # Action buttons
    st.markdown("""
        <style>
        .action-buttons {
            display: flex;
            gap: 1rem;
            margin: 2rem 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Save Invoice", type="primary", use_container_width=True):
            if not invoice_data['party_name']:
                st.error("❌ Please enter Party Name")
            else:
                # Get items based on active tab
                if st.session_state.active_tab == 'without_gst':
                    items = st.session_state.invoice_items_without_gst
                else:
                    items = st.session_state.invoice_items_with_gst
                
                # Filter out empty items
                valid_items = [item for item in items if item.get('product_name') and item.get('qty', 0) > 0]
                
                if not valid_items:
                    st.error("❌ Please add at least one valid item")
                else:
                    invoice_data['items'] = valid_items
                    invoice_data['id'] = st.session_state.current_invoice_id
                    
                    try:
                        invoice_id = save_invoice(invoice_data)
                        st.session_state.current_invoice_id = invoice_id
                        st.success(f"✅ Invoice saved successfully! ID: {invoice_id}")
                    except Exception as e:
                        st.error(f"❌ Error saving invoice: {str(e)}")
    
    with col2:
        if st.button("📄 Download PDF", use_container_width=True):
            if not invoice_data['party_name']:
                st.error("❌ Please enter Party Name")
            else:
                # Get items based on active tab
                if st.session_state.active_tab == 'without_gst':
                    items = st.session_state.invoice_items_without_gst
                else:
                    items = st.session_state.invoice_items_with_gst
                
                valid_items = [item for item in items if item.get('product_name') and item.get('qty', 0) > 0]
                
                if not valid_items:
                    st.error("❌ Please add at least one valid item")
                else:
                    invoice_data['items'] = valid_items
                    try:
                        pdf = generate_invoice_pdf(invoice_data)
                        pdf_output = pdf.output(dest='S').encode('latin1')
                        
                        st.download_button(
                            label="📥 Click to Download PDF",
                            data=pdf_output,
                            file_name=f"Invoice_{invoice_data['invoice_number']}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"❌ Error generating PDF: {str(e)}")
    
    with col3:
        if st.button("🆕 New Invoice", use_container_width=True):
            # Reset session state
            st.session_state.invoice_items_without_gst = [{
                'product_name': '', 'description': '', 'qty': 1, 'packing': '', 'unit_price': 0, 'amount': 0
            }]
            st.session_state.invoice_items_with_gst = [{
                'product_name': '', 'description': '', 'qty': 1, 'packing': '', 
                'unit_price_incl_gst': 0, 'base_amount': 0, 'gst_amount': 0, 'total_amount': 0
            }]
            st.session_state.current_invoice_id = None
            st.session_state.invoice_number = 1001
            st.rerun()
    
    # Search section
    render_search_section()
    
    # Bulk download section
    render_bulk_download()

if __name__ == "__main__":
    main()
