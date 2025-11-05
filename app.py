# app.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import io
from backend import backend
import base64
from fpdf import FPDF
import tempfile
import os

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = []
if 'stock_items' not in st.session_state:
    st.session_state.stock_items = []
if 'current_invoice_number' not in st.session_state:
    st.session_state.current_invoice_number = "1"
if 'parties' not in st.session_state:
    st.session_state.parties = []

# Product configuration
PRODUCTS = [
    "Strophase G", "Strophase P", "Strozyme NSP", "SP200", "SP300", 
    "SP300 Advance", "Monica", "Linco Magic", "Enra Magic", "InduceAcid Plus",
    "InduceAcid Buty", "Huntox", "Strozyme XYL", "Super Ener Emusifier", 
    "Antioxdant", "Toxin Binder Weilituo", "Toxin Clean", "GutPro 60 (Tributyrin)", 
    "InduceAcid Liquid"
]

PACKING_OPTIONS = ["Ltr", "Kg", "25 Ltr", "25 kg"]

class PDFGenerator(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'NUTRION', 0, 1, 'C')
        self.set_font('Arial', '', 12)
        self.cell(0, 10, 'Address: Pearl City Sargodha Road Faisalabad', 0, 1, 'C')
        self.cell(0, 10, 'Contact: +923007993003', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_invoice_pdf(invoice_data):
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Invoice header
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'TAX INVOICE', 0, 1, 'C')
    pdf.ln(10)
    
    # Party and invoice details
    pdf.set_font('Arial', '', 12)
    pdf.cell(40, 10, 'Bill To:', 0, 0)
    pdf.cell(0, 10, invoice_data['partyName'], 0, 1)
    
    pdf.cell(40, 10, 'Invoice #:', 0, 0)
    pdf.cell(0, 10, invoice_data['invoiceNumber'], 0, 1)
    
    pdf.cell(40, 10, 'Date:', 0, 0)
    pdf.cell(0, 10, invoice_data['date'], 0, 1)
    pdf.ln(10)
    
    # Items table header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(10, 10, 'Sr', 1, 0, 'C', True)
    pdf.cell(80, 10, 'Product Name', 1, 0, 'C', True)
    pdf.cell(20, 10, 'Qty', 1, 0, 'C', True)
    pdf.cell(20, 10, 'Packing', 1, 0, 'C', True)
    pdf.cell(25, 10, 'Unit Price', 1, 0, 'C', True)
    pdf.cell(25, 10, 'Amount', 1, 1, 'C', True)
    
    # Items
    pdf.set_fill_color(255, 255, 255)
    for i, item in enumerate(invoice_data['items'], 1):
        pdf.cell(10, 10, str(i), 1, 0, 'C')
        pdf.cell(80, 10, item['productName'], 1, 0)
        pdf.cell(20, 10, str(item['qty']), 1, 0, 'C')
        pdf.cell(20, 10, item['packing'], 1, 0, 'C')
        pdf.cell(25, 10, f"₹{item['unitPrice']:.2f}", 1, 0, 'R')
        pdf.cell(25, 10, f"₹{item['amount']:.2f}", 1, 1, 'R')
    
    pdf.ln(10)
    
    # Totals
    pdf.cell(150, 10, 'Subtotal:', 0, 0, 'R')
    pdf.cell(30, 10, f"₹{invoice_data['totalAmount']:.2f}", 0, 1, 'R')
    
    pdf.cell(150, 10, 'Previous Balance:', 0, 0, 'R')
    pdf.cell(30, 10, f"₹{invoice_data['previousBalance']:.2f}", 0, 1, 'R')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 10, 'Grand Total:', 0, 0, 'R')
    pdf.cell(30, 10, f"₹{invoice_data['grandTotal']:.2f}", 0, 1, 'R')
    
    return pdf

def get_pdf_download_link(pdf, filename):
    """Generate a download link for PDF"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
        pdf.output(tmp_file.name)
        with open(tmp_file.name, "rb") as f:
            pdf_bytes = f.read()
        os.unlink(tmp_file.name)
    
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">Download PDF</a>'
    return href

def initialize_app():
    """Initialize application data"""
    if not st.session_state.initialized:
        try:
            # Get next invoice number
            result = backend.get_next_invoice_number()
            if result:
                st.session_state.current_invoice_number = result.get('nextInvoiceNumber', '1')
            
            # Get parties list
            result = backend.get_parties()
            if result:
                st.session_state.parties = [party['name'] for party in result]
            
            st.session_state.initialized = True
        except Exception as e:
            st.error(f"Initialization error: {str(e)}")

# UI Components
def render_payment_section():
    """Payment Received Section"""
    st.header("Payment Received")
    
    with st.form("payment_form"):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="payment_party")
        with col2:
            amount = st.number_input("Amount Received", min_value=0.0, step=0.01, key="payment_amount")
        with col3:
            remarks = st.text_input("Remarks", placeholder="e.g., Advance, Bill Clearance", key="payment_remarks")
        with col4:
            payment_date = st.date_input("Payment Date", value=date.today(), key="payment_date")
        
        submitted = st.form_submit_button("Save Payment")
        if submitted:
            if not party_name:
                st.error("Party name is required")
                return
                
            payment_data = {
                "partyName": party_name,
                "amount": amount,
                "date": payment_date.isoformat(),
                "remarks": remarks
            }
            
            try:
                result = backend.record_payment(payment_data)
                if result:
                    st.success("Payment recorded successfully!")
                    # Refresh parties list
                    parties = backend.get_parties()
                    st.session_state.parties = [party['name'] for party in parties]
            except Exception as e:
                st.error(f"Error recording payment: {str(e)}")

def render_payment_range_section():
    """Payments Range Download"""
    st.header("Payments Range Download")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="payment_range_start")
    with col2:
        end_date = st.date_input("End Date", key="payment_range_end")
    
    if st.button("Download Payments PDF"):
        if start_date and end_date:
            if start_date <= end_date:
                try:
                    payments = backend.get_payments(start_date=start_date.isoformat(), end_date=end_date.isoformat())
                    if payments:
                        # Generate PDF for payments
                        pdf = PDFGenerator()
                        pdf.add_page()
                        pdf.set_font('Arial', 'B', 16)
                        pdf.cell(0, 10, 'Payments Report', 0, 1, 'C')
                        pdf.ln(10)
                        
                        # Add payments table
                        pdf.cell(20, 10, 'ID', 1, 0, 'C', True)
                        pdf.cell(60, 10, 'Party Name', 1, 0, 'C', True)
                        pdf.cell(40, 10, 'Date', 1, 0, 'C', True)
                        pdf.cell(40, 10, 'Amount', 1, 1, 'C', True)
                        
                        for payment in payments:
                            pdf.cell(20, 10, str(payment['paymentId']), 1, 0)
                            pdf.cell(60, 10, payment['partyName'], 1, 0)
                            pdf.cell(40, 10, payment['date'], 1, 0)
                            pdf.cell(40, 10, f"₹{payment['amount']:.2f}", 1, 1, 'R')
                        
                        st.markdown(get_pdf_download_link(pdf, f"payments_{start_date}_{end_date}.pdf"), unsafe_allow_html=True)
                    else:
                        st.info("No payments found in the selected date range")
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
            else:
                st.error("Start date must be before end date")
        else:
            st.error("Please select both start and end dates")

def render_delete_payment_section():
    """Payment Delete Section"""
    st.header("Payment Delete")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="delete_payment_party")
    with col2:
        if st.button("View Payments"):
            if party_name:
                try:
                    payments = backend.get_payments(party_name=party_name)
                    if payments:
                        display_payments_for_deletion(payments, party_name)
                    else:
                        st.info("No payments found for this party")
                except Exception as e:
                    st.error(f"Error fetching payments: {str(e)}")
            else:
                st.error("Please select a party name")

def display_payments_for_deletion(payments, party_name):
    """Display payments for deletion"""
    if payments:
        df = pd.DataFrame(payments)
        st.dataframe(df, use_container_width=True)
        
        # Simple delete functionality
        if st.button("Delete All Payments for This Party", type="secondary"):
            st.warning("This will delete all payments for this party. This action cannot be undone.")
            if st.button("Confirm Delete"):
                st.info("Delete functionality would be implemented here")
                # Note: In a real implementation, you'd add delete methods to the backend

def render_invoice_range_section():
    """Invoices Range Download"""
    st.header("Invoices Range Download")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="invoice_range_start")
    with col2:
        end_date = st.date_input("End Date", key="invoice_range_end")
    
    if st.button("Download Invoices PDF"):
        if start_date and end_date:
            st.info("Invoice range PDF download functionality")
        else:
            st.error("Please select both start and end dates")

def render_bilty_expense_section():
    """Bilty Expense Report"""
    st.header("Bilty Expense Report")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="bilty_start")
    with col2:
        end_date = st.date_input("End Date", key="bilty_end")
    
    if st.button("Download Bilty Expense Report PDF"):
        if start_date and end_date:
            st.info("Bilty Expense PDF generation")

def render_party_exclude_section():
    """Party Exclude Report"""
    st.header("Party Exclude Report")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        parties_to_exclude = st.multiselect("Parties to Exclude", st.session_state.parties)
    with col2:
        start_date = st.date_input("Start Date", key="exclude_start")
    with col3:
        end_date = st.date_input("End Date", key="exclude_end")
    
    if st.button("Download Party Exclude Report PDF"):
        if parties_to_exclude and start_date and end_date:
            st.info("Party Exclude PDF generation")

def render_no_bilty_section():
    """Payments Without Bilty Expense"""
    st.header("Payments Without Bilty Expense")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="no_bilty_start")
    with col2:
        end_date = st.date_input("End Date", key="no_bilty_end")
    
    if st.button("Download Payments Without Bilty PDF"):
        if start_date and end_date:
            st.info("No Bilty Payments PDF generation")

def render_ledger_section():
    """Feed Mills Ledger Details"""
    st.header("Feed Mills Ledger Details")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="ledger_party")
    with col2:
        if st.button("View Ledger"):
            if party_name:
                try:
                    ledger_data = backend.get_ledger(party_name)
                    if ledger_data:
                        display_ledger(ledger_data)
                except Exception as e:
                    st.error(f"Error fetching ledger: {str(e)}")

def display_ledger(ledger_data):
    """Display party ledger"""
    st.subheader(f"Ledger for: {ledger_data.get('partyName', '')}")
    
    transactions = ledger_data.get('transactions', [])
    if transactions:
        df = pd.DataFrame(transactions)
        st.dataframe(df, use_container_width=True)
        
        # Show opening and current balance
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Opening Balance", f"₹{ledger_data.get('openingBalance', 0):.2f}")
        with col2:
            st.metric("Current Balance", f"₹{ledger_data.get('currentBalance', 0):.2f}")
    else:
        st.info("No transactions found for this party")

def render_opening_balance_history():
    """Opening Balance History"""
    st.header("Opening Balance History")
    st.info("Opening balance history functionality would be implemented here")

def render_product_sales_section():
    """Product Sales Summary"""
    st.header("Product Sales Summary with Date Range")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="product_sales_start")
    with col2:
        end_date = st.date_input("End Date", key="product_sales_end")
    
    if st.button("Product Sales Summary PDF"):
        if start_date and end_date:
            st.info("Product Sales PDF generation")

def render_party_invoices_section():
    """Individual Invoices"""
    st.header("Individual Invoices")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="party_invoices")
    with col2:
        start_date = st.date_input("Start Date", key="party_invoices_start")
    with col3:
        end_date = st.date_input("End Date", key="party_invoices_end")
    
    if st.button("Download Party Invoices"):
        if party_name and start_date and end_date:
            st.info("Party Invoices PDF generation")

def render_stock_section():
    """Stock Management"""
    st.header("Stock Management")
    
    # Add stock form
    with st.form("stock_form"):
        st.subheader("Add Stock Item")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            product_name = st.selectbox("Product Name", PRODUCTS, key="stock_product")
        with col2:
            batch_no = st.text_input("Batch No.", placeholder="e.g., B-12345")
        with col3:
            stock_date = st.date_input("Date", value=date.today(), key="stock_date")
        with col4:
            quantity = st.number_input("Quantity", min_value=0, step=1, key="stock_quantity")
        
        if st.form_submit_button("Add Stock Item"):
            if product_name and quantity > 0:
                new_item = {
                    "productName": product_name,
                    "batchNo": batch_no,
                    "date": stock_date.isoformat(),
                    "quantity": quantity
                }
                st.session_state.stock_items.append(new_item)
                st.success("Stock item added to list!")
            else:
                st.error("Please fill all required fields")
    
    # Display current stock items
    if st.session_state.stock_items:
        st.subheader("Current Stock Items")
        stock_df = pd.DataFrame(st.session_state.stock_items)
        st.dataframe(stock_df, use_container_width=True)
        
        if st.button("Save All Stock Items"):
            try:
                result = backend.add_stock({"items": st.session_state.stock_items})
                if result:
                    st.success(result.get('message', 'Stock items saved successfully!'))
                    st.session_state.stock_items = []
            except Exception as e:
                st.error(f"Error saving stock: {str(e)}")
    
    # Available stock
    st.subheader("Available Stock")
    if st.button("Refresh Stock"):
        try:
            stock_data = backend.get_stock()
            if stock_data:
                display_stock_data(stock_data)
        except Exception as e:
            st.error(f"Error fetching stock: {str(e)}")

def display_stock_data(stock_data):
    """Display available stock"""
    if stock_data:
        df = pd.DataFrame(stock_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No stock data available")

def render_invoice_creation_section():
    """Main Invoice Creation Section"""
    st.header("Create New Invoice")
    
    # Party and basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="invoice_party")
    with col2:
        invoice_date = st.date_input("Date", value=date.today(), key="invoice_date")
    with col3:
        st.text_input("Invoice #", value=st.session_state.current_invoice_number, disabled=True)
    
    # Invoice items
    st.subheader("Invoice Items")
    render_invoice_items()
    
    # Totals
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        gst_percentage = st.number_input("GST %", min_value=0.0, max_value=100.0, value=0.0, step=0.1)
    with col2:
        # Get previous balance for the party
        previous_balance = 0.0
        if party_name:
            try:
                balance_info = backend.get_party_balance(party_name)
                previous_balance = balance_info['balance']
            except:
                pass
        st.number_input("Previous Balance", value=previous_balance, step=0.01, disabled=True)
    with col3:
        subtotal = calculate_subtotal()
        st.metric("Subtotal", f"₹{subtotal:.2f}")
    with col4:
        grand_total = calculate_grand_total(subtotal, gst_percentage, previous_balance)
        st.metric("Grand Total", f"₹{grand_total:.2f}")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Save Invoice", type="primary"):
            save_invoice(party_name, invoice_date, gst_percentage, previous_balance)
    with col2:
        if st.button("Download PDF"):
            if st.session_state.invoice_items and party_name:
                invoice_data = {
                    "partyName": party_name,
                    "invoiceNumber": st.session_state.current_invoice_number,
                    "date": invoice_date.isoformat(),
                    "items": st.session_state.invoice_items,
                    "totalAmount": subtotal,
                    "previousBalance": previous_balance,
                    "grandTotal": grand_total
                }
                pdf = generate_invoice_pdf(invoice_data)
                st.markdown(get_pdf_download_link(pdf, f"invoice_{st.session_state.current_invoice_number}.pdf"), unsafe_allow_html=True)
            else:
                st.error("Please add items and select a party first")
    with col3:
        if st.button("Clear Form"):
            st.session_state.invoice_items = []
            st.rerun()
    with col4:
        if st.button("Refresh"):
            st.rerun()

def render_invoice_items():
    """Render invoice items with add/remove functionality"""
    # Add new item row
    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 1])
    
    with col1:
        new_product = st.selectbox("Product", [""] + PRODUCTS, key="new_product")
    with col2:
        new_qty = st.number_input("Qty", min_value=0.0, step=0.1, key="new_qty")
    with col3:
        new_packing = st.selectbox("Packing", PACKING_OPTIONS, key="new_packing")
    with col4:
        new_unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01, key="new_unit_price")
    with col5:
        new_amount = new_qty * new_unit_price
        st.text_input("Amount", value=f"{new_amount:.2f}", disabled=True, key="new_amount")
    
    # Add button outside any form
    with col6:
        if st.button("Add", key="add_item"):
            if new_product and new_qty > 0:
                new_item = {
                    "productName": new_product,
                    "qty": new_qty,
                    "packing": new_packing,
                    "unitPrice": new_unit_price,
                    "amount": new_amount
                }
                st.session_state.invoice_items.append(new_item)
                st.rerun()
    
    # Display current items
    if st.session_state.invoice_items:
        st.subheader("Current Items")
        for i, item in enumerate(st.session_state.invoice_items):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 1])
            with col1:
                st.text(item['productName'])
            with col2:
                st.text(str(item['qty']))
            with col3:
                st.text(item['packing'])
            with col4:
                st.text(f"₹{item['unitPrice']:.2f}")
            with col5:
                st.text(f"₹{item['amount']:.2f}")
            with col6:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.invoice_items.pop(i)
                    st.rerun()

def calculate_subtotal():
    """Calculate invoice subtotal"""
    return sum(item['amount'] for item in st.session_state.invoice_items)

def calculate_grand_total(subtotal, gst_percentage, previous_balance):
    """Calculate grand total"""
    gst_amount = subtotal * (gst_percentage / 100)
    return subtotal + gst_amount + previous_balance

def save_invoice(party_name, invoice_date, gst_percentage, previous_balance):
    """Save invoice to backend"""
    if not party_name:
        st.error("Party name is required")
        return
        
    if not st.session_state.invoice_items:
        st.error("Please add at least one invoice item")
        return
    
    invoice_data = {
        "partyName": party_name,
        "date": invoice_date.isoformat(),
        "invoiceNumber": st.session_state.current_invoice_number,
        "items": st.session_state.invoice_items,
        "totalAmount": calculate_subtotal(),
        "previousBalance": previous_balance,
        "grandTotal": calculate_grand_total(calculate_subtotal(), gst_percentage, previous_balance)
    }
    
    try:
        result = backend.create_invoice(invoice_data)
        if result:
            st.success("Invoice saved successfully!")
            # Update invoice number and clear items
            st.session_state.current_invoice_number = result.get('nextInvoiceNumber', str(int(st.session_state.current_invoice_number) + 1))
            st.session_state.invoice_items = []
            # Refresh parties list
            parties = backend.get_parties()
            st.session_state.parties = [party['name'] for party in parties]
    except Exception as e:
        st.error(f"Error saving invoice: {str(e)}")

def render_additional_actions():
    """Additional actions section"""
    st.header("Additional Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("All Party Balances PDF"):
            st.info("All Party Balances PDF generation")
    with col2:
        if st.button("Product Sales with Party"):
            st.info("Product Sales PDF generation")
    with col3:
        if st.button("Refresh Application"):
            st.session_state.initialized = False
            st.rerun()

# Main App
def main():
    st.set_page_config(
        page_title="NUTRION - Invoice, Ledger & Stock",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #FFA500;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        background-color: #FFA500;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-top: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">NUTRION - Invoice, Ledger & Stock</h1>', unsafe_allow_html=True)
    
    # Initialize app
    initialize_app()
    
    # Status indicator
    if st.session_state.initialized:
        st.success("✅ Application initialized successfully")
    else:
        st.warning("🔄 Initializing application...")
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Invoices", 
        "💰 Payments", 
        "📊 Ledger", 
        "📦 Stock", 
        "📈 Reports",
        "🛠️ Tools"
    ])
    
    with tab1:
        render_invoice_creation_section()
    
    with tab2:
        render_payment_section()
        st.markdown("---")
        render_payment_range_section()
        st.markdown("---")
        render_delete_payment_section()
    
    with tab3:
        render_ledger_section()
        st.markdown("---")
        render_opening_balance_history()
    
    with tab4:
        render_stock_section()
    
    with tab5:
        render_invoice_range_section()
        st.markdown("---")
        render_bilty_expense_section()
        st.markdown("---")
        render_party_exclude_section()
        st.markdown("---")
        render_no_bilty_section()
        st.markdown("---")
        render_product_sales_section()
        st.markdown("---")
        render_party_invoices_section()
    
    with tab6:
        render_additional_actions()
        st.markdown("---")
        
        # Data management section
        st.header("Data Management")
        if st.button("Refresh Party List", type="secondary"):
            try:
                parties = backend.get_parties()
                st.session_state.parties = [party['name'] for party in parties]
                st.success("Party list refreshed!")
            except Exception as e:
                st.error(f"Error refreshing party list: {str(e)}")

if __name__ == "__main__":
    main()
