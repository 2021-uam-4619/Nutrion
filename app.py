import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime, date
import time
import base64
from io import BytesIO

# Configuration
API_BASE_URL = "http://127.0.0.1:5000"

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

# API Helper Functions
def api_call(endpoint, method='GET', data=None):
    """Make API calls to backend"""
    try:
        url = f"{API_BASE_URL}{endpoint}"
        
        if method == 'GET':
            response = requests.get(url)
        elif method == 'POST':
            response = requests.post(url, json=data)
        elif method == 'PUT':
            response = requests.put(url, json=data)
        elif method == 'DELETE':
            response = requests.delete(url)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {str(e)}")
        return None

def initialize_app():
    """Initialize application data"""
    if not st.session_state.initialized:
        # Get next invoice number
        result = api_call('/api/next-invoice-number')
        if result:
            st.session_state.current_invoice_number = result.get('nextInvoiceNumber', '1')
        
        # Get parties list
        result = api_call('/api/parties')
        if result:
            st.session_state.parties = [party['name'] for party in result]
        
        st.session_state.initialized = True

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
            
            result = api_call('/api/payments', 'POST', payment_data)
            if result:
                st.success("Payment recorded successfully!")
                st.rerun()

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
                st.info("PDF download functionality would be implemented here")
                # Note: Actual PDF generation would require backend integration
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
                payments = api_call(f'/api/payments?partyName={party_name}')
                if payments:
                    display_payments_for_deletion(payments, party_name)
            else:
                st.error("Please select a party name")

def display_payments_for_deletion(payments, party_name):
    """Display payments for deletion"""
    if payments:
        df = pd.DataFrame(payments)
        st.dataframe(df, use_container_width=True)
        
        # Delete functionality
        payment_ids = df.get('paymentId', [])
        if len(payment_ids) > 0:
            selected_id = st.selectbox("Select Payment ID to Delete", payment_ids)
            if st.button("Delete Selected Payment", type="primary"):
                result = api_call(f'/api/payments/{selected_id}', 'DELETE')
                if result:
                    st.success("Payment deleted successfully!")
                    st.rerun()
    else:
        st.info("No payments found for this party")

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
            if start_date <= end_date:
                st.info("PDF download functionality would be implemented here")
            else:
                st.error("Start date must be before end date")
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
            st.info("Bilty Expense PDF generation would be implemented here")

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
            st.info("Party Exclude PDF generation would be implemented here")

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
            st.info("No Bilty Payments PDF generation would be implemented here")

def render_ledger_section():
    """Feed Mills Ledger Details"""
    st.header("Feed Mills Ledger Details")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="ledger_party")
    with col2:
        if st.button("View Ledger"):
            if party_name:
                ledger_data = api_call(f'/api/ledger/{party_name}')
                if ledger_data:
                    display_ledger(ledger_data)

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
    
    col1, col2 = st.columns([3, 1])
    with col1:
        party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="history_party")
    with col2:
        if st.button("View History"):
            if party_name:
                history = api_call(f'/api/parties/{party_name}/opening-balance-history')
                if history:
                    display_opening_balance_history(history, party_name)

def display_opening_balance_history(history, party_name):
    """Display opening balance history"""
    if history:
        df = pd.DataFrame(history)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No history found for this party")

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
            st.info("Product Sales PDF generation would be implemented here")

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
            st.info("Party Invoices PDF generation would be implemented here")

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
            result = api_call('/api/stock/batch-add', 'POST', {"items": st.session_state.stock_items})
            if result:
                st.success(result.get('message', 'Stock items saved successfully!'))
                st.session_state.stock_items = []
                st.rerun()
    
    # Available stock
    st.subheader("Available Stock")
    if st.button("Refresh Stock"):
        stock_data = api_call('/api/stock')
        if stock_data:
            display_stock_data(stock_data)

def display_stock_data(stock_data):
    """Display available stock"""
    if stock_data:
        df = pd.DataFrame(stock_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No stock data available")

def render_edit_invoice_section():
    """Invoice Update & Delete"""
    st.header("Invoice Update & Delete")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        invoice_number = st.text_input("Invoice Number", placeholder="Enter Invoice # to Edit/Delete")
    with col2:
        if st.button("Search Invoice"):
            if invoice_number:
                invoice_data = api_call(f'/api/invoices/{invoice_number}')
                if invoice_data:
                    load_invoice_for_editing(invoice_data)
    
    # Edit form will appear here when an invoice is loaded
    if 'editing_invoice' in st.session_state:
        render_invoice_edit_form()

def load_invoice_for_editing(invoice_data):
    """Load invoice data for editing"""
    st.session_state.editing_invoice = invoice_data
    st.session_state.invoice_items = invoice_data.get('items', [])
    st.success(f"Invoice #{invoice_data.get('invoiceNumber')} loaded for editing")

def render_invoice_edit_form():
    """Render form for editing invoice"""
    invoice_data = st.session_state.editing_invoice
    
    with st.form("edit_invoice_form"):
        st.subheader(f"Editing Invoice #{invoice_data.get('invoiceNumber')}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            party_name = st.text_input("Party Name", value=invoice_data.get('partyName', ''))
        with col2:
            invoice_date = st.date_input("Date", 
                                       value=datetime.strptime(invoice_data.get('date', '2024-01-01'), '%Y-%m-%d').date())
        with col3:
            st.text_input("Invoice #", value=invoice_data.get('invoiceNumber', ''), disabled=True)
        
        # Invoice items editing would go here
        
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("Update Invoice"):
                st.info("Invoice update functionality would be implemented here")
        with col2:
            if st.form_submit_button("Delete Invoice", type="secondary"):
                result = api_call(f'/api/invoices/{invoice_data.get("invoiceNumber")}', 'DELETE')
                if result:
                    st.success("Invoice deleted successfully!")
                    del st.session_state.editing_invoice
                    st.rerun()

def render_invoice_creation_section():
    """Main Invoice Creation Section"""
    st.header("Create New Invoice")
    
    with st.form("invoice_form"):
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
            previous_balance = st.number_input("Previous Balance", value=0.0, step=0.01)
        with col3:
            subtotal = calculate_subtotal()
            st.metric("Subtotal", f"₹{subtotal:.2f}")
        with col4:
            grand_total = calculate_grand_total(subtotal, gst_percentage, previous_balance)
            st.metric("Grand Total", f"₹{grand_total:.2f}")
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.form_submit_button("Save Invoice"):
                save_invoice(party_name, invoice_date, gst_percentage, previous_balance)
        with col2:
            if st.form_submit_button("Download PDF"):
                st.info("PDF download would be implemented here")
        with col3:
            if st.form_submit_button("Clear Form"):
                st.session_state.invoice_items = []
                st.rerun()
        with col4:
            if st.form_submit_button("Refresh"):
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
        st.text_input("Amount", value=f"{new_amount:.2f}", disabled=True)
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
        "gstPercentage": gst_percentage,
        "previousBalance": previous_balance,
        "grandTotal": calculate_grand_total(calculate_subtotal(), gst_percentage, previous_balance)
    }
    
    result = api_call('/api/invoices', 'POST', invoice_data)
    if result:
        st.success("Invoice saved successfully!")
        # Update invoice number and clear items
        st.session_state.current_invoice_number = result.get('nextInvoiceNumber', str(int(st.session_state.current_invoice_number) + 1))
        st.session_state.invoice_items = []
        st.rerun()

def render_additional_actions():
    """Additional actions section"""
    st.header("Additional Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("All Party Balances PDF"):
            st.info("All Party Balances PDF generation would be implemented here")
    with col2:
        if st.button("Product Sales with Party"):
            st.info("Product Sales PDF generation would be implemented here")
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
        st.markdown("---")
        render_edit_invoice_section()
    
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
            result = api_call('/api/parties')
            if result:
                st.session_state.parties = [party['name'] for party in result]
                st.success("Party list refreshed!")
        
        st.markdown("---")
        
        # Danger zone
        st.header("Danger Zone")
        if st.button("Delete All Data", type="primary"):
            if st.checkbox("I understand this will delete ALL data permanently"):
                if st.button("CONFIRM DELETE ALL DATA", type="secondary"):
                    result = api_call('/api/admin/delete-all-data', 'POST')
                    if result:
                        st.success("All data deleted successfully!")
                        st.session_state.initialized = False
                        st.rerun()

if __name__ == "__main__":
    main()
