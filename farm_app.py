import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, time, timedelta
import plotly.express as px
import plotly.graph_objects as go
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import json

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Farm Management System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        background: linear-gradient(90deg, #2E7D32, #4CAF50);
        color: white;
        border-radius: 10px;
    }
    .stButton>button {
        background-color: #2E7D32;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
    }
    .delete-btn {
        background-color: #dc3545 !important;
    }
    .edit-btn {
        background-color: #ffc107 !important;
        color: black !important;
    }
    .card {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8f9fa;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATABASE SETUP
# ============================================
def init_database():
    conn = sqlite3.connect('farm_management_live.db')
    cursor = conn.cursor()
    
    # Create Livestock Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livestock_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            animal_type TEXT NOT NULL,
            expense_type TEXT NOT NULL,
            quantity REAL,
            unit TEXT,
            rate REAL,
            amount REAL NOT NULL,
            paid_by TEXT,
            payment_method TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Livestock Income table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livestock_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            animal_type TEXT NOT NULL,
            income_type TEXT NOT NULL,
            quantity REAL,
            unit TEXT,
            rate REAL,
            amount REAL NOT NULL,
            buyer_name TEXT,
            payment_method TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Crop Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crop_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            crop_name TEXT NOT NULL,
            expense_type TEXT NOT NULL,
            quantity REAL,
            unit TEXT,
            rate REAL,
            amount REAL NOT NULL,
            paid_by TEXT,
            payment_method TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Crop Income table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crop_income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            crop_name TEXT NOT NULL,
            income_type TEXT NOT NULL,
            quantity REAL,
            unit TEXT,
            rate REAL,
            amount REAL NOT NULL,
            buyer_name TEXT,
            payment_method TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Water Bills table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT NOT NULL,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            hours_used REAL NOT NULL,
            rate_per_hour REAL NOT NULL,
            total_bill REAL NOT NULL,
            amount_paid REAL DEFAULT 0,
            balance_due REAL DEFAULT 0,
            payment_status TEXT DEFAULT 'Pending',
            payment_method TEXT,
            payment_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Operational Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS operational_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            expense_type TEXT NOT NULL,
            managed_by TEXT,
            amount REAL NOT NULL,
            paid_to TEXT,
            paid_amount REAL DEFAULT 0,
            balance_due REAL DEFAULT 0,
            description TEXT,
            payment_method TEXT,
            is_paid BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Employees table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            designation TEXT,
            salary REAL,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Farmers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Ledger table for double-entry accounting
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_date DATE NOT NULL,
            account_name TEXT NOT NULL,
            account_type TEXT NOT NULL,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            reference_type TEXT,
            reference_id INTEGER,
            description TEXT,
            balance REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_date DATE NOT NULL,
            payee_name TEXT,
            payer_name TEXT,
            amount REAL NOT NULL,
            payment_method TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

# Initialize database
conn = init_database()

# ============================================
# HELPER FUNCTIONS
# ============================================
def calculate_hours(start_time, end_time):
    """Calculate hours between two times"""
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    
    if end_dt < start_dt:
        end_dt = end_dt + timedelta(days=1)
    
    hours = (end_dt - start_dt).total_seconds() / 3600
    return round(hours, 2)

def add_ledger_entry(transaction_date, account_name, account_type, debit, credit, reference_type, reference_id, description):
    """Add double-entry ledger entry"""
    cursor = conn.cursor()
    
    # Calculate running balance for the account
    cursor.execute('''
        SELECT balance FROM ledger 
        WHERE account_name = ? 
        ORDER BY id DESC LIMIT 1
    ''', (account_name,))
    
    result = cursor.fetchone()
    prev_balance = result[0] if result else 0
    
    # Update balance based on account type
    if account_type in ['Asset', 'Expense']:
        new_balance = prev_balance + debit - credit
    else:  # Liability, Income, Equity
        new_balance = prev_balance + credit - debit
    
    cursor.execute('''
        INSERT INTO ledger (transaction_date, account_name, account_type, debit, credit, 
                          reference_type, reference_id, description, balance)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (transaction_date, account_name, account_type, debit, credit, 
          reference_type, reference_id, description, new_balance))
    
    conn.commit()
    return cursor.lastrowid

def record_payment(payment_date, payee_name, payer_name, amount, payment_method, reference_type, reference_id, description):
    """Record payment in payments table"""
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payments (payment_date, payee_name, payer_name, amount, 
                            payment_method, reference_type, reference_id, description)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (payment_date, payee_name, payer_name, amount, payment_method, 
          reference_type, reference_id, description))
    conn.commit()
    return cursor.lastrowid

def generate_pdf_report(data, title, columns, filename="report.pdf"):
    """Generate PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = styles['Title']
    title_style.alignment = 1  # Center alignment
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 20))
    
    # Date
    date_style = styles['Normal']
    date_style.alignment = 1
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style))
    elements.append(Spacer(1, 30))
    
    # Convert data to table format
    table_data = [columns] + data
    
    # Create table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.green),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    elements.append(table)
    
    # Total if applicable
    if data and len(data[0]) > 3 and any(isinstance(x, (int, float)) for x in data[0][3:]):
        total = sum(float(row[3]) for row in data if len(row) > 3 and row[3])
        elements.append(Spacer(1, 20))
        elements.append(Paragraph(f"<b>Total Amount: PKR {total:,.2f}</b>", styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# ============================================
# SIDEBAR NAVIGATION
# ============================================
st.sidebar.image("", width=100)
st.sidebar.title("🌾 Farm Management")

menu = st.sidebar.radio(
    "Select Section",
    ["🏠 Dashboard", 
     "🐄 Livestock Management", 
     "🌱 Crop Management",
     "💧 Water Income",
     "💰 Operational Expenses",
     "📊 Reports & Analytics",
     "👥 Employees & Farmers"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Quick Actions")
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

# ============================================
# DASHBOARD
# ============================================
if menu == "🏠 Dashboard":
    st.markdown("<h1 class='main-header'>Farm Management Dashboard</h1>", unsafe_allow_html=True)
    
    # Get summary statistics
    cursor = conn.cursor()
    
    # Today's date
    today = date.today()
    
    # Calculate totals
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM livestock_expenses WHERE date = ?", (today,))
    today_livestock_exp = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM crop_expenses WHERE date = ?", (today,))
    today_crop_exp = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(total_bill), 0) FROM water_bills WHERE date = ?", (today,))
    today_water_inc = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM operational_expenses WHERE date = ?", (today,))
    today_op_exp = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(balance_due), 0) FROM water_bills WHERE balance_due > 0")
    total_outstanding = cursor.fetchone()[0]
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Today's Income", f"PKR {today_water_inc:,.0f}")
    
    with col2:
        st.metric("Today's Expenses", f"PKR {(today_livestock_exp + today_crop_exp + today_op_exp):,.0f}")
    
    with col3:
        st.metric("Outstanding Balance", f"PKR {total_outstanding:,.0f}")
    
    with col4:
        cursor.execute("SELECT COUNT(DISTINCT farmer_name) FROM water_bills WHERE balance_due > 0")
        farmers_count = cursor.fetchone()[0]
        st.metric("Farmers with Dues", f"{farmers_count}")
    
    # Recent Transactions
    st.subheader("📋 Recent Transactions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Recent Livestock Expenses")
        cursor.execute('''
            SELECT date, animal_type, expense_type, amount 
            FROM livestock_expenses 
            ORDER BY date DESC LIMIT 5
        ''')
        livestock_data = cursor.fetchall()
        
        if livestock_data:
            df_livestock = pd.DataFrame(livestock_data, columns=['Date', 'Animal', 'Expense Type', 'Amount'])
            st.dataframe(df_livestock, use_container_width=True)
        else:
            st.info("No livestock expenses recorded")
    
    with col2:
        st.markdown("#### Recent Water Bills")
        cursor.execute('''
            SELECT date, farmer_name, total_bill, payment_status 
            FROM water_bills 
            ORDER BY date DESC LIMIT 5
        ''')
        water_data = cursor.fetchall()
        
        if water_data:
            df_water = pd.DataFrame(water_data, columns=['Date', 'Farmer', 'Total Bill', 'Status'])
            st.dataframe(df_water, use_container_width=True)
        else:
            st.info("No water bills recorded")

# ============================================
# LIVESTOCK MANAGEMENT
# ============================================
elif menu == "🐄 Livestock Management":
    st.markdown("<h1 class='main-header'>Livestock Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Expense", "💰 Add Income", "📋 View/Edit Records", "📄 Generate Report"])
    
    # ============ ADD EXPENSE ============
    with tab1:
        st.subheader("Add Livestock Expense")
        
        with st.form("livestock_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Date*", value=date.today())
                animal_type = st.selectbox("Animal Type*", 
                    ["Cow", "Goat", "Sheep", "Buffalo", "Other"])
                expense_type = st.selectbox("Expense Type*",
                    ["Wanda (Feed)", "Chokar", "Khal", "Tori", "Khas", "Medicine", "Other"])
                
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5)
                unit = st.selectbox("Unit", ["KG", "Liters", "Bags", "Other"])
                rate = st.number_input("Rate per Unit (PKR)", min_value=0.0, value=0.0, step=10.0)
                amount = st.number_input("Total Amount (PKR)*", min_value=0.0, step=100.0)
            
            paid_by = st.text_input("Paid By (Person Name)")
            payment_method = st.selectbox("Payment Method", 
                ["Cash", "Bank Transfer", "Credit", "Mobile Payment"])
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("💾 Save Expense", type="primary")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    cursor = conn.cursor()
                    try:
                        # Insert expense
                        cursor.execute('''
                            INSERT INTO livestock_expenses 
                            (date, animal_type, expense_type, quantity, unit, rate, amount, paid_by, payment_method, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (expense_date, animal_type, expense_type, quantity, unit, rate, amount, 
                              paid_by, payment_method, notes))
                        
                        expense_id = cursor.lastrowid
                        
                        # Add to ledger (Double-entry)
                        # Debit: Livestock Expense Account
                        add_ledger_entry(
                            transaction_date=expense_date,
                            account_name=f"Livestock Expense - {animal_type}",
                            account_type="Expense",
                            debit=amount,
                            credit=0,
                            reference_type="livestock_expense",
                            reference_id=expense_id,
                            description=f"{animal_type} - {expense_type}"
                        )
                        
                        # Credit: Cash/Bank or Accounts Payable
                        if payment_method == "Credit":
                            credit_account = "Accounts Payable"
                            account_type = "Liability"
                        elif payment_method == "Bank Transfer":
                            credit_account = "Bank Account"
                            account_type = "Asset"
                        else:
                            credit_account = "Cash Account"
                            account_type = "Asset"
                        
                        add_ledger_entry(
                            transaction_date=expense_date,
                            account_name=credit_account,
                            account_type=account_type,
                            debit=0,
                            credit=amount,
                            reference_type="livestock_expense",
                            reference_id=expense_id,
                            description=f"Payment for {animal_type} expense"
                        )
                        
                        conn.commit()
                        st.success("✅ Livestock expense recorded successfully!")
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error saving expense: {str(e)}")
    
    # ============ ADD INCOME ============
    with tab2:
        st.subheader("Add Livestock Income")
        
        with st.form("livestock_income_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                income_date = st.date_input("Date*", value=date.today(), key="income_date")
                animal_type = st.selectbox("Animal Type*", 
                    ["Cow", "Goat", "Sheep", "Buffalo", "Other"], key="income_animal")
                income_type = st.selectbox("Income Type*",
                    ["Milk Sale", "Animal Sale", "Manure Sale", "Other"], key="income_type")
                
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5, key="income_qty")
                unit = st.selectbox("Unit", ["KG", "Liters", "Animals", "Other"], key="income_unit")
                rate = st.number_input("Rate per Unit (PKR)", min_value=0.0, value=0.0, step=10.0, key="income_rate")
                amount = st.number_input("Total Amount (PKR)*", min_value=0.0, step=100.0, key="income_amount")
            
            buyer_name = st.text_input("Buyer Name")
            payment_method = st.selectbox("Payment Method", 
                ["Cash", "Bank Transfer", "Mobile Payment"], key="income_payment")
            notes = st.text_area("Notes", key="income_notes")
            
            submitted = st.form_submit_button("💰 Record Income", type="primary")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    cursor = conn.cursor()
                    try:
                        # Insert income
                        cursor.execute('''
                            INSERT INTO livestock_income 
                            (date, animal_type, income_type, quantity, unit, rate, amount, buyer_name, payment_method, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (income_date, animal_type, income_type, quantity, unit, rate, amount, 
                              buyer_name, payment_method, notes))
                        
                        income_id = cursor.lastrowid
                        
                        # Add to ledger (Double-entry)
                        # Debit: Cash/Bank Account
                        if payment_method == "Bank Transfer":
                            debit_account = "Bank Account"
                        else:
                            debit_account = "Cash Account"
                        
                        add_ledger_entry(
                            transaction_date=income_date,
                            account_name=debit_account,
                            account_type="Asset",
                            debit=amount,
                            credit=0,
                            reference_type="livestock_income",
                            reference_id=income_id,
                            description=f"Income from {animal_type} - {income_type}"
                        )
                        
                        # Credit: Livestock Income Account
                        add_ledger_entry(
                            transaction_date=income_date,
                            account_name=f"Livestock Income - {animal_type}",
                            account_type="Income",
                            debit=0,
                            credit=amount,
                            reference_type="livestock_income",
                            reference_id=income_id,
                            description=f"{animal_type} - {income_type}"
                        )
                        
                        conn.commit()
                        st.success("✅ Livestock income recorded successfully!")
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error saving income: {str(e)}")
    
    # ============ VIEW/EDIT RECORDS ============
    with tab3:
        st.subheader("View & Edit Records")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("From Date", value=date.today().replace(day=1))
        with col2:
            end_date = st.date_input("To Date", value=date.today())
        with col3:
            record_type = st.selectbox("Record Type", ["Expenses", "Income"])
        
        # Fetch data
        cursor = conn.cursor()
        
        if record_type == "Expenses":
            cursor.execute('''
                SELECT id, date, animal_type, expense_type, quantity, unit, rate, amount, 
                       paid_by, payment_method, notes 
                FROM livestock_expenses 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (start_date, end_date))
            
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=[
                    'ID', 'Date', 'Animal Type', 'Expense Type', 'Quantity', 'Unit', 
                    'Rate', 'Amount', 'Paid By', 'Payment Method', 'Notes'
                ])
                
                # Display with edit/delete options
                st.dataframe(df, use_container_width=True)
                
                # Edit/Delete Section
                st.subheader("Edit/Delete Record")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    edit_id = st.number_input("Enter Record ID to edit/delete", min_value=1, step=1)
                
                with col2:
                    if st.button("📝 Edit Record", key="edit_livestock"):
                        # Fetch record for editing
                        cursor.execute('SELECT * FROM livestock_expenses WHERE id = ?', (edit_id,))
                        record = cursor.fetchone()
                        
                        if record:
                            # Pre-fill form for editing
                            with st.form("edit_livestock_form"):
                                st.write(f"Editing Record ID: {edit_id}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    edit_date = st.date_input("Date", value=datetime.strptime(record[1], '%Y-%m-%d').date())
                                    edit_animal = st.selectbox("Animal Type", 
                                        ["Cow", "Goat", "Sheep", "Buffalo", "Other"],
                                        index=["Cow", "Goat", "Sheep", "Buffalo", "Other"].index(record[2]))
                                    edit_expense = st.text_input("Expense Type", value=record[3])
                                
                                with col2:
                                    edit_quantity = st.number_input("Quantity", value=record[4] or 0.0)
                                    edit_unit = st.text_input("Unit", value=record[5] or "")
                                    edit_rate = st.number_input("Rate", value=record[6] or 0.0)
                                    edit_amount = st.number_input("Amount", value=record[7])
                                
                                edit_paid_by = st.text_input("Paid By", value=record[8] or "")
                                edit_payment = st.text_input("Payment Method", value=record[9] or "")
                                edit_notes = st.text_area("Notes", value=record[10] or "")
                                
                                if st.form_submit_button("💾 Update Record", type="primary"):
                                    try:
                                        cursor.execute('''
                                            UPDATE livestock_expenses 
                                            SET date = ?, animal_type = ?, expense_type = ?, 
                                                quantity = ?, unit = ?, rate = ?, amount = ?,
                                                paid_by = ?, payment_method = ?, notes = ?,
                                                updated_at = CURRENT_TIMESTAMP
                                            WHERE id = ?
                                        ''', (edit_date, edit_animal, edit_expense, edit_quantity,
                                              edit_unit, edit_rate, edit_amount, edit_paid_by,
                                              edit_payment, edit_notes, edit_id))
                                        
                                        # Update ledger entries
                                        cursor.execute('''
                                            DELETE FROM ledger 
                                            WHERE reference_type = 'livestock_expense' 
                                            AND reference_id = ?
                                        ''', (edit_id,))
                                        
                                        # Re-add ledger entries
                                        add_ledger_entry(
                                            transaction_date=edit_date,
                                            account_name=f"Livestock Expense - {edit_animal}",
                                            account_type="Expense",
                                            debit=edit_amount,
                                            credit=0,
                                            reference_type="livestock_expense",
                                            reference_id=edit_id,
                                            description=f"{edit_animal} - {edit_expense}"
                                        )
                                        
                                        if edit_payment == "Credit":
                                            credit_account = "Accounts Payable"
                                            acc_type = "Liability"
                                        elif edit_payment == "Bank Transfer":
                                            credit_account = "Bank Account"
                                            acc_type = "Asset"
                                        else:
                                            credit_account = "Cash Account"
                                            acc_type = "Asset"
                                        
                                        add_ledger_entry(
                                            transaction_date=edit_date,
                                            account_name=credit_account,
                                            account_type=acc_type,
                                            debit=0,
                                            credit=edit_amount,
                                            reference_type="livestock_expense",
                                            reference_id=edit_id,
                                            description=f"Payment for {edit_animal} expense"
                                        )
                                        
                                        conn.commit()
                                        st.success("✅ Record updated successfully!")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        conn.rollback()
                                        st.error(f"Error updating record: {str(e)}")
                        else:
                            st.error("Record not found!")
                
                with col3:
                    if st.button("🗑️ Delete Record", type="secondary"):
                        try:
                            # Delete from livestock_expenses
                            cursor.execute('DELETE FROM livestock_expenses WHERE id = ?', (edit_id,))
                            
                            # Delete related ledger entries
                            cursor.execute('''
                                DELETE FROM ledger 
                                WHERE reference_type = 'livestock_expense' 
                                AND reference_id = ?
                            ''', (edit_id,))
                            
                            conn.commit()
                            st.success("✅ Record deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error deleting record: {str(e)}")
                
                # Summary
                total_amount = df['Amount'].sum()
                st.metric("Total Expenses in Period", f"PKR {total_amount:,.2f}")
                
            else:
                st.info("No livestock expenses found for the selected period")
        
        else:  # Income records
            cursor.execute('''
                SELECT id, date, animal_type, income_type, quantity, unit, rate, amount, 
                       buyer_name, payment_method, notes 
                FROM livestock_income 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (start_date, end_date))
            
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=[
                    'ID', 'Date', 'Animal Type', 'Income Type', 'Quantity', 'Unit', 
                    'Rate', 'Amount', 'Buyer', 'Payment Method', 'Notes'
                ])
                
                st.dataframe(df, use_container_width=True)
                
                # Edit/Delete for Income
                st.subheader("Edit/Delete Income Record")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    income_id = st.number_input("Enter Income ID to edit/delete", min_value=1, step=1, key="income_edit_id")
                
                with col2:
                    if st.button("📝 Edit Income", key="edit_income_btn"):
                        cursor.execute('SELECT * FROM livestock_income WHERE id = ?', (income_id,))
                        record = cursor.fetchone()
                        
                        if record:
                            with st.form("edit_income_form"):
                                st.write(f"Editing Income ID: {income_id}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    edit_date = st.date_input("Date", 
                                        value=datetime.strptime(record[1], '%Y-%m-%d').date(), 
                                        key="edit_inc_date")
                                    edit_animal = st.selectbox("Animal Type", 
                                        ["Cow", "Goat", "Sheep", "Buffalo", "Other"],
                                        index=["Cow", "Goat", "Sheep", "Buffalo", "Other"].index(record[2]),
                                        key="edit_inc_animal")
                                    edit_income_type = st.text_input("Income Type", value=record[3], key="edit_inc_type")
                                
                                with col2:
                                    edit_qty = st.number_input("Quantity", value=record[4] or 0.0, key="edit_inc_qty")
                                    edit_unit = st.text_input("Unit", value=record[5] or "", key="edit_inc_unit")
                                    edit_rate = st.number_input("Rate", value=record[6] or 0.0, key="edit_inc_rate")
                                    edit_amount = st.number_input("Amount", value=record[7], key="edit_inc_amount")
                                
                                edit_buyer = st.text_input("Buyer", value=record[8] or "", key="edit_inc_buyer")
                                edit_payment = st.text_input("Payment Method", value=record[9] or "", key="edit_inc_payment")
                                edit_notes = st.text_area("Notes", value=record[10] or "", key="edit_inc_notes")
                                
                                if st.form_submit_button("Update Income", type="primary"):
                                    try:
                                        cursor.execute('''
                                            UPDATE livestock_income 
                                            SET date = ?, animal_type = ?, income_type = ?, 
                                                quantity = ?, unit = ?, rate = ?, amount = ?,
                                                buyer_name = ?, payment_method = ?, notes = ?
                                            WHERE id = ?
                                        ''', (edit_date, edit_animal, edit_income_type, edit_qty,
                                              edit_unit, edit_rate, edit_amount, edit_buyer,
                                              edit_payment, edit_notes, income_id))
                                        
                                        # Update ledger
                                        cursor.execute('''
                                            DELETE FROM ledger 
                                            WHERE reference_type = 'livestock_income' 
                                            AND reference_id = ?
                                        ''', (income_id,))
                                        
                                        # Re-add ledger entries
                                        if edit_payment == "Bank Transfer":
                                            debit_account = "Bank Account"
                                        else:
                                            debit_account = "Cash Account"
                                        
                                        add_ledger_entry(
                                            transaction_date=edit_date,
                                            account_name=debit_account,
                                            account_type="Asset",
                                            debit=edit_amount,
                                            credit=0,
                                            reference_type="livestock_income",
                                            reference_id=income_id,
                                            description=f"Income from {edit_animal} - {edit_income_type}"
                                        )
                                        
                                        add_ledger_entry(
                                            transaction_date=edit_date,
                                            account_name=f"Livestock Income - {edit_animal}",
                                            account_type="Income",
                                            debit=0,
                                            credit=edit_amount,
                                            reference_type="livestock_income",
                                            reference_id=income_id,
                                            description=f"{edit_animal} - {edit_income_type}"
                                        )
                                        
                                        conn.commit()
                                        st.success("✅ Income record updated!")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        conn.rollback()
                                        st.error(f"Error updating income: {str(e)}")
                
                with col3:
                    if st.button("🗑️ Delete Income", type="secondary", key="delete_income_btn"):
                        try:
                            cursor.execute('DELETE FROM livestock_income WHERE id = ?', (income_id,))
                            cursor.execute('''
                                DELETE FROM ledger 
                                WHERE reference_type = 'livestock_income' 
                                AND reference_id = ?
                            ''', (income_id,))
                            conn.commit()
                            st.success("✅ Income record deleted!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error deleting income: {str(e)}")
                
                total_income = df['Amount'].sum()
                st.metric("Total Income in Period", f"PKR {total_income:,.2f}")
                
            else:
                st.info("No livestock income found for the selected period")
    
    # ============ GENERATE REPORT ============
    with tab4:
        st.subheader("Generate Livestock Report")
        
        report_type = st.selectbox("Select Report Type", 
            ["Expenses Report", "Income Report", "Profit/Loss Summary"])
        
        col1, col2 = st.columns(2)
        with col1:
            report_start = st.date_input("Start Date", value=date.today().replace(day=1), key="report_start")
        with col2:
            report_end = st.date_input("End Date", value=date.today(), key="report_end")
        
        if st.button("📄 Generate PDF Report", type="primary"):
            cursor = conn.cursor()
            
            if report_type == "Expenses Report":
                cursor.execute('''
                    SELECT date, animal_type, expense_type, quantity, unit, rate, amount, paid_by, payment_method
                    FROM livestock_expenses 
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date
                ''', (report_start, report_end))
                
                data = cursor.fetchall()
                
                if data:
                    pdf_data = []
                    for row in data:
                        pdf_data.append([
                            str(row[0]), row[1], row[2], 
                            f"{row[3]} {row[4]}" if row[3] else "",
                            f"PKR {row[5]:,.2f}" if row[5] else "",
                            f"PKR {row[6]:,.2f}", 
                            row[7] or "", row[8] or ""
                        ])
                    
                    columns = ['Date', 'Animal', 'Expense Type', 'Quantity', 'Rate', 'Amount', 'Paid By', 'Payment Method']
                    pdf_buffer = generate_pdf_report(pdf_data, "Livestock Expenses Report", columns)
                    
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer,
                        file_name=f"livestock_expenses_{report_start}_{report_end}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("No data found for the selected period")
            
            elif report_type == "Income Report":
                cursor.execute('''
                    SELECT date, animal_type, income_type, quantity, unit, rate, amount, buyer_name, payment_method
                    FROM livestock_income 
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date
                ''', (report_start, report_end))
                
                data = cursor.fetchall()
                
                if data:
                    pdf_data = []
                    for row in data:
                        pdf_data.append([
                            str(row[0]), row[1], row[2], 
                            f"{row[3]} {row[4]}" if row[3] else "",
                            f"PKR {row[5]:,.2f}" if row[5] else "",
                            f"PKR {row[6]:,.2f}", 
                            row[7] or "", row[8] or ""
                        ])
                    
                    columns = ['Date', 'Animal', 'Income Type', 'Quantity', 'Rate', 'Amount', 'Buyer', 'Payment Method']
                    pdf_buffer = generate_pdf_report(pdf_data, "Livestock Income Report", columns)
                    
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer,
                        file_name=f"livestock_income_{report_start}_{report_end}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("No data found for the selected period")
            
            else:  # Profit/Loss Summary
                cursor.execute('''
                    SELECT 'Expenses' as type, COALESCE(SUM(amount), 0) as total
                    FROM livestock_expenses 
                    WHERE date BETWEEN ? AND ?
                    UNION ALL
                    SELECT 'Income' as type, COALESCE(SUM(amount), 0) as total
                    FROM livestock_income 
                    WHERE date BETWEEN ? AND ?
                ''', (report_start, report_end, report_start, report_end))
                
                data = cursor.fetchall()
                
                if data:
                    expenses = data[0][1]
                    income = data[1][1]
                    profit_loss = income - expenses
                    
                    summary_data = [
                        ["Total Expenses", f"PKR {expenses:,.2f}"],
                        ["Total Income", f"PKR {income:,.2f}"],
                        ["Net Profit/Loss", f"PKR {profit_loss:,.2f}"],
                        ["Profit Margin", f"{(profit_loss/income*100 if income > 0 else 0):.1f}%"]
                    ]
                    
                    pdf_buffer = generate_pdf_report(summary_data, "Livestock Profit/Loss Summary", ['Category', 'Amount'])
                    
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer,
                        file_name=f"livestock_summary_{report_start}_{report_end}.pdf",
                        mime="application/pdf"
                    )

# ============================================
# CROP MANAGEMENT
# ============================================
elif menu == "🌱 Crop Management":
    st.markdown("<h1 class='main-header'>Crop Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Expense", "💰 Add Income", "📋 View/Edit Records", "📄 Generate Report"])
    
    # ============ ADD EXPENSE ============
    with tab1:
        st.subheader("Add Crop Expense")
        
        with st.form("crop_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Date*", value=date.today(), key="crop_date")
                crop_name = st.selectbox("Crop Name*",
                    ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Vegetables", "Fruits", "Other"])
                expense_type = st.selectbox("Expense Type*",
                    ["Khad (Fertilizer)", "Sapry (Spray)", "Seed", "Irrigation", "Labor", "Other"])
                
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5, key="crop_qty")
                unit = st.selectbox("Unit", ["KG", "Liters", "Bags", "Acres", "Other"], key="crop_unit")
                rate = st.number_input("Rate per Unit (PKR)", min_value=0.0, value=0.0, step=10.0, key="crop_rate")
                amount = st.number_input("Total Amount (PKR)*", min_value=0.0, step=100.0, key="crop_amount")
            
            paid_by = st.text_input("Paid By (Person Name)", key="crop_paid_by")
            payment_method = st.selectbox("Payment Method", 
                ["Cash", "Bank Transfer", "Credit", "Mobile Payment"], key="crop_payment")
            notes = st.text_area("Notes", key="crop_notes")
            
            submitted = st.form_submit_button("💾 Save Expense", type="primary")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO crop_expenses 
                            (date, crop_name, expense_type, quantity, unit, rate, amount, paid_by, payment_method, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (expense_date, crop_name, expense_type, quantity, unit, rate, amount, 
                              paid_by, payment_method, notes))
                        
                        expense_id = cursor.lastrowid
                        
                        # Add to ledger
                        add_ledger_entry(
                            transaction_date=expense_date,
                            account_name=f"Crop Expense - {crop_name}",
                            account_type="Expense",
                            debit=amount,
                            credit=0,
                            reference_type="crop_expense",
                            reference_id=expense_id,
                            description=f"{crop_name} - {expense_type}"
                        )
                        
                        if payment_method == "Credit":
                            credit_account = "Accounts Payable"
                            account_type = "Liability"
                        elif payment_method == "Bank Transfer":
                            credit_account = "Bank Account"
                            account_type = "Asset"
                        else:
                            credit_account = "Cash Account"
                            account_type = "Asset"
                        
                        add_ledger_entry(
                            transaction_date=expense_date,
                            account_name=credit_account,
                            account_type=account_type,
                            debit=0,
                            credit=amount,
                            reference_type="crop_expense",
                            reference_id=expense_id,
                            description=f"Payment for {crop_name} expense"
                        )
                        
                        conn.commit()
                        st.success("✅ Crop expense recorded successfully!")
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error saving expense: {str(e)}")
    
    # ============ ADD INCOME ============
    with tab2:
        st.subheader("Add Crop Income")
        
        with st.form("crop_income_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                income_date = st.date_input("Date*", value=date.today(), key="crop_inc_date")
                crop_name = st.selectbox("Crop Name*",
                    ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Vegetables", "Fruits", "Other"],
                    key="crop_inc_name")
                income_type = st.selectbox("Income Type*",
                    ["Sale", "Subsidy", "Other"], key="crop_inc_type")
                
            with col2:
                quantity = st.number_input("Quantity", min_value=0.0, value=1.0, step=0.5, key="crop_inc_qty")
                unit = st.selectbox("Unit", ["KG", "Maund", "Bags", "Other"], key="crop_inc_unit")
                rate = st.number_input("Rate per Unit (PKR)", min_value=0.0, value=0.0, step=10.0, key="crop_inc_rate")
                amount = st.number_input("Total Amount (PKR)*", min_value=0.0, step=100.0, key="crop_inc_amount")
            
            buyer_name = st.text_input("Buyer Name", key="crop_inc_buyer")
            payment_method = st.selectbox("Payment Method", 
                ["Cash", "Bank Transfer", "Mobile Payment"], key="crop_inc_payment")
            notes = st.text_area("Notes", key="crop_inc_notes")
            
            submitted = st.form_submit_button("💰 Record Income", type="primary")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO crop_income 
                            (date, crop_name, income_type, quantity, unit, rate, amount, buyer_name, payment_method, notes)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (income_date, crop_name, income_type, quantity, unit, rate, amount, 
                              buyer_name, payment_method, notes))
                        
                        income_id = cursor.lastrowid
                        
                        # Add to ledger
                        if payment_method == "Bank Transfer":
                            debit_account = "Bank Account"
                        else:
                            debit_account = "Cash Account"
                        
                        add_ledger_entry(
                            transaction_date=income_date,
                            account_name=debit_account,
                            account_type="Asset",
                            debit=amount,
                            credit=0,
                            reference_type="crop_income",
                            reference_id=income_id,
                            description=f"Income from {crop_name} - {income_type}"
                        )
                        
                        add_ledger_entry(
                            transaction_date=income_date,
                            account_name=f"Crop Income - {crop_name}",
                            account_type="Income",
                            debit=0,
                            credit=amount,
                            reference_type="crop_income",
                            reference_id=income_id,
                            description=f"{crop_name} - {income_type}"
                        )
                        
                        conn.commit()
                        st.success("✅ Crop income recorded successfully!")
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error saving income: {str(e)}")
    
    # ============ VIEW/EDIT RECORDS ============
    with tab3:
        st.subheader("View & Edit Crop Records")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("From Date", value=date.today().replace(day=1), key="crop_view_start")
        with col2:
            end_date = st.date_input("To Date", value=date.today(), key="crop_view_end")
        with col3:
            record_type = st.selectbox("Record Type", ["Expenses", "Income"], key="crop_record_type")
        
        cursor = conn.cursor()
        
        if record_type == "Expenses":
            cursor.execute('''
                SELECT id, date, crop_name, expense_type, quantity, unit, rate, amount, 
                       paid_by, payment_method, notes 
                FROM crop_expenses 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (start_date, end_date))
            
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=[
                    'ID', 'Date', 'Crop Name', 'Expense Type', 'Quantity', 'Unit', 
                    'Rate', 'Amount', 'Paid By', 'Payment Method', 'Notes'
                ])
                
                st.dataframe(df, use_container_width=True)
                
                # Edit/Delete Section
                st.subheader("Edit/Delete Crop Expense")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    edit_id = st.number_input("Enter Record ID to edit/delete", min_value=1, step=1, key="crop_edit_id")
                
                with col2:
                    if st.button("📝 Edit Record", key="edit_crop_btn"):
                        cursor.execute('SELECT * FROM crop_expenses WHERE id = ?', (edit_id,))
                        record = cursor.fetchone()
                        
                        if record:
                            with st.form("edit_crop_form"):
                                st.write(f"Editing Record ID: {edit_id}")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    edit_date = st.date_input("Date", 
                                        value=datetime.strptime(record[1], '%Y-%m-%d').date(), 
                                        key="edit_crop_date")
                                    edit_crop = st.text_input("Crop Name", value=record[2], key="edit_crop_name")
                                    edit_expense = st.text_input("Expense Type", value=record[3], key="edit_crop_exp")
                                
                                with col2:
                                    edit_qty = st.number_input("Quantity", value=record[4] or 0.0, key="edit_crop_qty")
                                    edit_unit = st.text_input("Unit", value=record[5] or "", key="edit_crop_unit")
                                    edit_rate = st.number_input("Rate", value=record[6] or 0.0, key="edit_crop_rate")
                                    edit_amount = st.number_input("Amount", value=record[7], key="edit_crop_amount")
                                
                                edit_paid_by = st.text_input("Paid By", value=record[8] or "", key="edit_crop_paid")
                                edit_payment = st.text_input("Payment Method", value=record[9] or "", key="edit_crop_payment")
                                edit_notes = st.text_area("Notes", value=record[10] or "", key="edit_crop_notes")
                                
                                if st.form_submit_button("Update Crop Expense", type="primary"):
                                    try:
                                        cursor.execute('''
                                            UPDATE crop_expenses 
                                            SET date = ?, crop_name = ?, expense_type = ?, 
                                                quantity = ?, unit = ?, rate = ?, amount = ?,
                                                paid_by = ?, payment_method = ?, notes = ?,
                                                updated_at = CURRENT_TIMESTAMP
                                            WHERE id = ?
                                        ''', (edit_date, edit_crop, edit_expense, edit_qty,
                                              edit_unit, edit_rate, edit_amount, edit_paid_by,
                                              edit_payment, edit_notes, edit_id))
                                        
                                        # Update ledger
                                        cursor.execute('''
                                            DELETE FROM ledger 
                                            WHERE reference_type = 'crop_expense' 
                                            AND reference_id = ?
                                        ''', (edit_id,))
                                        
                                        add_ledger_entry(
                                            transaction_date=edit_date,
                                            account_name=f"Crop Expense - {edit_crop}",
                                            account_type="Expense",
                                            debit=edit_amount,
                                            credit=0,
                                            reference_type="crop_expense",
                                            reference_id=edit_id,
                                            description=f"{edit_crop} - {edit_expense}"
                                        )
                                        
                                        if edit_payment == "Credit":
                                            credit_account = "Accounts Payable"
                                            acc_type = "Liability"
                                        elif edit_payment == "Bank Transfer":
                                            credit_account = "Bank Account"
                                            acc_type = "Asset"
                                        else:
                                            credit_account = "Cash Account"
                                            acc_type = "Asset"
                                        
                                        add_ledger_entry(
                                            transaction_date=edit_date,
                                            account_name=credit_account,
                                            account_type=acc_type,
                                            debit=0,
                                            credit=edit_amount,
                                            reference_type="crop_expense",
                                            reference_id=edit_id,
                                            description=f"Payment for {edit_crop} expense"
                                        )
                                        
                                        conn.commit()
                                        st.success("✅ Crop expense updated!")
                                        st.rerun()
                                        
                                    except Exception as e:
                                        conn.rollback()
                                        st.error(f"Error updating: {str(e)}")
                
                with col3:
                    if st.button("🗑️ Delete Record", type="secondary", key="delete_crop_btn"):
                        try:
                            cursor.execute('DELETE FROM crop_expenses WHERE id = ?', (edit_id,))
                            cursor.execute('''
                                DELETE FROM ledger 
                                WHERE reference_type = 'crop_expense' 
                                AND reference_id = ?
                            ''', (edit_id,))
                            conn.commit()
                            st.success("✅ Crop expense deleted!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error deleting: {str(e)}")
                
                total_amount = df['Amount'].sum()
                st.metric("Total Crop Expenses", f"PKR {total_amount:,.2f}")
                
            else:
                st.info("No crop expenses found")
        
        else:  # Crop Income
            cursor.execute('''
                SELECT id, date, crop_name, income_type, quantity, unit, rate, amount, 
                       buyer_name, payment_method, notes 
                FROM crop_income 
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC
            ''', (start_date, end_date))
            
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=[
                    'ID', 'Date', 'Crop Name', 'Income Type', 'Quantity', 'Unit', 
                    'Rate', 'Amount', 'Buyer', 'Payment Method', 'Notes'
                ])
                
                st.dataframe(df, use_container_width=True)
                
                total_income = df['Amount'].sum()
                st.metric("Total Crop Income", f"PKR {total_income:,.2f}")
                
            else:
                st.info("No crop income found")
    
    # ============ GENERATE REPORT ============
    with tab4:
        st.subheader("Generate Crop Report")
        
        report_type = st.selectbox("Select Report Type", 
            ["Expenses Report", "Income Report", "Crop-wise Summary"], key="crop_report_type")
        
        col1, col2 = st.columns(2)
        with col1:
            report_start = st.date_input("Start Date", value=date.today().replace(day=1), key="crop_rep_start")
        with col2:
            report_end = st.date_input("End Date", value=date.today(), key="crop_rep_end")
        
        if st.button("📄 Generate PDF Report", type="primary", key="crop_gen_report"):
            cursor = conn.cursor()
            
            if report_type == "Expenses Report":
                cursor.execute('''
                    SELECT date, crop_name, expense_type, quantity, unit, rate, amount, paid_by, payment_method
                    FROM crop_expenses 
                    WHERE date BETWEEN ? AND ?
                    ORDER BY date
                ''', (report_start, report_end))
                
                data = cursor.fetchall()
                
                if data:
                    pdf_data = []
                    for row in data:
                        pdf_data.append([
                            str(row[0]), row[1], row[2], 
                            f"{row[3]} {row[4]}" if row[3] else "",
                            f"PKR {row[5]:,.2f}" if row[5] else "",
                            f"PKR {row[6]:,.2f}", 
                            row[7] or "", row[8] or ""
                        ])
                    
                    columns = ['Date', 'Crop', 'Expense Type', 'Quantity', 'Rate', 'Amount', 'Paid By', 'Payment Method']
                    pdf_buffer = generate_pdf_report(pdf_data, "Crop Expenses Report", columns)
                    
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_buffer,
                        file_name=f"crop_expenses_{report_start}_{report_end}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("No data found")

# ============================================
# WATER INCOME
# ============================================
elif menu == "💧 Water Income":
    st.markdown("<h1 class='main-header'>Water Income Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Water Bill", "💰 Record Payment", "📋 View/Edit Bills", "📄 Generate Report"])
    
    # ============ ADD WATER BILL ============
    with tab1:
        st.subheader("Create Water Bill")
        
        with st.form("water_bill_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                farmer_name = st.text_input("Farmer Name*")
                bill_date = st.date_input("Date*", value=date.today())
                
                col1a, col1b = st.columns(2)
                with col1a:
                    start_time = st.time_input("Start Time*", value=datetime.now().time())
                with col1b:
                    end_time = st.time_input("End Time*", 
                        value=(datetime.now() + timedelta(hours=2)).time())
            
            with col2:
                rate_per_hour = st.number_input("Rate per Hour (PKR)*", 
                    min_value=0.0, value=500.0, step=50.0)
                
                # Calculate hours and bill
                hours_used = calculate_hours(start_time, end_time)
                total_bill = hours_used * rate_per_hour
                
                st.metric("Hours Used", f"{hours_used:.2f}")
                st.metric("Total Bill", f"PKR {total_bill:,.2f}")
                
                amount_paid = st.number_input("Amount Paid Now", 
                    min_value=0.0, max_value=total_bill, value=0.0, step=100.0)
                balance_due = total_bill - amount_paid
                
                if balance_due > 0:
                    st.warning(f"Balance Due: PKR {balance_due:,.2f}")
                else:
                    st.success("Fully Paid!")
            
            payment_method = st.selectbox("Payment Method", 
                ["Cash", "Bank Transfer", "Mobile Payment", "Credit"])
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("💧 Generate Bill", type="primary")
            
            if submitted:
                cursor = conn.cursor()
                try:
                    # Insert water bill
                    cursor.execute('''
                        INSERT INTO water_bills 
                        (farmer_name, date, start_time, end_time, hours_used, rate_per_hour, 
                         total_bill, amount_paid, balance_due, payment_status, payment_method, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (farmer_name, bill_date, start_time, end_time, hours_used, rate_per_hour,
                          total_bill, amount_paid, balance_due,
                          "Paid" if balance_due == 0 else "Partial" if amount_paid > 0 else "Pending",
                          payment_method if amount_paid > 0 else None, notes))
                    
                    bill_id = cursor.lastrowid
                    
                    # Add to ledger
                    # Debit: Accounts Receivable (Farmer)
                    add_ledger_entry(
                        transaction_date=bill_date,
                        account_name=f"Receivable - {farmer_name}",
                        account_type="Asset",
                        debit=total_bill,
                        credit=0,
                        reference_type="water_bill",
                        reference_id=bill_id,
                        description=f"Water bill for {hours_used} hours"
                    )
                    
                    # Credit: Water Income
                    add_ledger_entry(
                        transaction_date=bill_date,
                        account_name="Water Income",
                        account_type="Income",
                        debit=0,
                        credit=total_bill,
                        reference_type="water_bill",
                        reference_id=bill_id,
                        description=f"Income from {farmer_name}"
                    )
                    
                    # If partial payment received
                    if amount_paid > 0:
                        # Record payment
                        record_payment(
                            payment_date=bill_date,
                            payee_name=farmer_name,
                            payer_name="Farm",
                            amount=amount_paid,
                            payment_method=payment_method,
                            reference_type="water_bill",
                            reference_id=bill_id,
                            description=f"Payment for water bill"
                        )
                        
                        # Update ledger for payment
                        if payment_method == "Bank Transfer":
                            debit_account = "Bank Account"
                        else:
                            debit_account = "Cash Account"
                        
                        add_ledger_entry(
                            transaction_date=bill_date,
                            account_name=debit_account,
                            account_type="Asset",
                            debit=amount_paid,
                            credit=0,
                            reference_type="payment",
                            reference_id=bill_id,
                            description=f"Payment from {farmer_name}"
                        )
                        
                        add_ledger_entry(
                            transaction_date=bill_date,
                            account_name=f"Receivable - {farmer_name}",
                            account_type="Asset",
                            debit=0,
                            credit=amount_paid,
                            reference_type="payment",
                            reference_id=bill_id,
                            description=f"Payment received"
                        )
                    
                    conn.commit()
                    st.success(f"✅ Water bill created successfully!")
                    
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error creating bill: {str(e)}")
    
    # ============ RECORD PAYMENT ============
    with tab2:
        st.subheader("Record Payment for Outstanding Bill")
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, farmer_name, total_bill, amount_paid, balance_due 
            FROM water_bills 
            WHERE balance_due > 0
            ORDER BY date DESC
        ''')
        
        unpaid_bills = cursor.fetchall()
        
        if not unpaid_bills:
            st.info("No outstanding bills found")
        else:
            bill_options = {f"{b[1]} - PKR {b[4]:,.2f} due (Bill #{b[0]})": b[0] for b in unpaid_bills}
            
            selected_bill = st.selectbox("Select Bill", list(bill_options.keys()))
            bill_id = bill_options[selected_bill]
            
            # Get bill details
            cursor.execute('SELECT * FROM water_bills WHERE id = ?', (bill_id,))
            bill = cursor.fetchone()
            
            if bill:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Farmer:** {bill[1]}")
                    st.write(f"**Total Bill:** PKR {bill[6]:,.2f}")
                    st.write(f"**Already Paid:** PKR {bill[7]:,.2f}")
                    st.write(f"**Balance Due:** PKR {bill[8]:,.2f}")
                
                with col2:
                    with st.form("payment_form"):
                        payment_date = st.date_input("Payment Date", value=date.today())
                        payment_amount = st.number_input("Payment Amount", 
                            min_value=0.0, max_value=bill[8], value=bill[8], step=100.0)
                        payment_method = st.selectbox("Payment Method",
                            ["Cash", "Bank Transfer", "Mobile Payment"])
                        
                        if st.form_submit_button("💳 Record Payment", type="primary"):
                            try:
                                # Update water bill
                                new_paid = bill[7] + payment_amount
                                new_balance = bill[8] - payment_amount
                                
                                cursor.execute('''
                                    UPDATE water_bills 
                                    SET amount_paid = ?, balance_due = ?, 
                                        payment_status = ?, payment_method = ?, payment_date = ?,
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                ''', (new_paid, new_balance,
                                      "Paid" if new_balance == 0 else "Partial",
                                      payment_method, payment_date, bill_id))
                                
                                # Record payment
                                payment_id = record_payment(
                                    payment_date=payment_date,
                                    payee_name=bill[1],
                                    payer_name="Farm",
                                    amount=payment_amount,
                                    payment_method=payment_method,
                                    reference_type="water_bill",
                                    reference_id=bill_id,
                                    description=f"Payment for water bill #{bill_id}"
                                )
                                
                                # Update ledger
                                if payment_method == "Bank Transfer":
                                    debit_account = "Bank Account"
                                else:
                                    debit_account = "Cash Account"
                                
                                add_ledger_entry(
                                    transaction_date=payment_date,
                                    account_name=debit_account,
                                    account_type="Asset",
                                    debit=payment_amount,
                                    credit=0,
                                    reference_type="payment",
                                    reference_id=payment_id,
                                    description=f"Payment from {bill[1]}"
                                )
                                
                                add_ledger_entry(
                                    transaction_date=payment_date,
                                    account_name=f"Receivable - {bill[1]}",
                                    account_type="Asset",
                                    debit=0,
                                    credit=payment_amount,
                                    reference_type="payment",
                                    reference_id=payment_id,
                                    description=f"Payment received"
                                )
                                
                                conn.commit()
                                st.success(f"✅ Payment of PKR {payment_amount:,.2f} recorded successfully!")
                                st.rerun()
                                
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Error recording payment: {str(e)}")
    
    # ============ VIEW/EDIT BILLS ============
    with tab3:
        st.subheader("View & Edit Water Bills")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("From Date", value=date.today().replace(day=1), key="water_start")
        with col2:
            end_date = st.date_input("To Date", value=date.today(), key="water_end")
        with col3:
            status_filter = st.selectbox("Payment Status", ["All", "Paid", "Partial", "Pending"])
        
        cursor = conn.cursor()
        
        query = '''
            SELECT id, date, farmer_name, start_time, end_time, hours_used, 
                   rate_per_hour, total_bill, amount_paid, balance_due, 
                   payment_status, payment_method 
            FROM water_bills 
            WHERE date BETWEEN ? AND ?
        '''
        params = [start_date, end_date]
        
        if status_filter != "All":
            query += " AND payment_status = ?"
            params.append(status_filter)
        
        query += " ORDER BY date DESC"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=[
                'ID', 'Date', 'Farmer', 'Start Time', 'End Time', 'Hours', 
                'Rate', 'Total Bill', 'Paid', 'Balance', 'Status', 'Payment Method'
            ])
            
            st.dataframe(df, use_container_width=True)
            
            # Edit/Delete Section
            st.subheader("Edit/Delete Water Bill")
            
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                edit_id = st.number_input("Enter Bill ID to edit/delete", min_value=1, step=1, key="water_edit_id")
            
            with col2:
                if st.button("📝 Edit Bill", key="edit_water_btn"):
                    cursor.execute('SELECT * FROM water_bills WHERE id = ?', (edit_id,))
                    bill = cursor.fetchone()
                    
                    if bill:
                        with st.form("edit_water_form"):
                            st.write(f"Editing Bill ID: {edit_id}")
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                edit_date = st.date_input("Date", 
                                    value=datetime.strptime(bill[2], '%Y-%m-%d').date(), 
                                    key="edit_water_date")
                                edit_farmer = st.text_input("Farmer Name", value=bill[1], key="edit_water_farmer")
                                
                                edit_start = st.time_input("Start Time", 
                                    value=datetime.strptime(bill[3], '%H:%M:%S').time(),
                                    key="edit_water_start")
                                edit_end = st.time_input("End Time", 
                                    value=datetime.strptime(bill[4], '%H:%M:%S').time(),
                                    key="edit_water_end")
                            
                            with col2:
                                edit_rate = st.number_input("Rate per Hour", value=bill[6], key="edit_water_rate")
                                edit_hours = calculate_hours(edit_start, edit_end)
                                edit_total = edit_hours * edit_rate
                                
                                st.metric("Calculated Hours", f"{edit_hours:.2f}")
                                st.metric("Total Bill", f"PKR {edit_total:,.2f}")
                                
                                edit_paid = st.number_input("Amount Paid", value=bill[7], key="edit_water_paid")
                                edit_balance = edit_total - edit_paid
                                
                                if edit_balance > 0:
                                    st.warning(f"New Balance: PKR {edit_balance:,.2f}")
                            
                            edit_payment = st.text_input("Payment Method", value=bill[11] or "", key="edit_water_payment")
                            edit_notes = st.text_area("Notes", value=bill[12] or "", key="edit_water_notes")
                            
                            if st.form_submit_button("Update Water Bill", type="primary"):
                                try:
                                    cursor.execute('''
                                        UPDATE water_bills 
                                        SET date = ?, farmer_name = ?, start_time = ?, end_time = ?,
                                            hours_used = ?, rate_per_hour = ?, total_bill = ?,
                                            amount_paid = ?, balance_due = ?,
                                            payment_status = ?, payment_method = ?, notes = ?,
                                            updated_at = CURRENT_TIMESTAMP
                                        WHERE id = ?
                                    ''', (edit_date, edit_farmer, edit_start, edit_end,
                                          edit_hours, edit_rate, edit_total,
                                          edit_paid, edit_balance,
                                          "Paid" if edit_balance == 0 else "Partial" if edit_paid > 0 else "Pending",
                                          edit_payment, edit_notes, edit_id))
                                    
                                    # Update ledger entries
                                    cursor.execute('''
                                        DELETE FROM ledger 
                                        WHERE reference_type IN ('water_bill', 'payment') 
                                        AND reference_id = ?
                                    ''', (edit_id,))
                                    
                                    # Re-add ledger entries
                                    add_ledger_entry(
                                        transaction_date=edit_date,
                                        account_name=f"Receivable - {edit_farmer}",
                                        account_type="Asset",
                                        debit=edit_total,
                                        credit=0,
                                        reference_type="water_bill",
                                        reference_id=edit_id,
                                        description=f"Water bill for {edit_hours} hours"
                                    )
                                    
                                    add_ledger_entry(
                                        transaction_date=edit_date,
                                        account_name="Water Income",
                                        account_type="Income",
                                        debit=0,
                                        credit=edit_total,
                                        reference_type="water_bill",
                                        reference_id=edit_id,
                                        description=f"Income from {edit_farmer}"
                                    )
                                    
                                    if edit_paid > 0:
                                        if edit_payment == "Bank Transfer":
                                            debit_account = "Bank Account"
                                        else:
                                            debit_account = "Cash Account"
                                        
                                        add_ledger_entry(
                                            transaction_date=edit_date,
                                            account_name=debit_account,
                                            account_type="Asset",
                                            debit=edit_paid,
                                            credit=0,
                                            reference_type="payment",
                                            reference_id=edit_id,
                                            description=f"Payment from {edit_farmer}"
                                        )
                                        
                                        add_ledger_entry(
                                            transaction_date=edit_date,
                                            account_name=f"Receivable - {edit_farmer}",
                                            account_type="Asset",
                                            debit=0,
                                            credit=edit_paid,
                                            reference_type="payment",
                                            reference_id=edit_id,
                                            description=f"Payment received"
                                        )
                                    
                                    conn.commit()
                                    st.success("✅ Water bill updated!")
                                    st.rerun()
                                    
                                except Exception as e:
                                    conn.rollback()
                                    st.error(f"Error updating: {str(e)}")
            
            with col3:
                if st.button("🗑️ Delete Bill", type="secondary", key="delete_water_btn"):
                    try:
                        cursor.execute('DELETE FROM water_bills WHERE id = ?', (edit_id,))
                        cursor.execute('''
                            DELETE FROM ledger 
                            WHERE reference_type IN ('water_bill', 'payment') 
                            AND reference_id = ?
                        ''', (edit_id,))
                        cursor.execute('DELETE FROM payments WHERE reference_id = ? AND reference_type = "water_bill"', (edit_id,))
                        conn.commit()
                        st.success("✅ Water bill deleted!")
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error deleting: {str(e)}")
            
            # Summary
            total_bills = df['Total Bill'].sum()
            total_paid = df['Paid'].sum()
            total_balance = df['Balance'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Bills", f"PKR {total_bills:,.2f}")
            with col2:
                st.metric("Total Paid", f"PKR {total_paid:,.2f}")
            with col3:
                st.metric("Total Outstanding", f"PKR {total_balance:,.2f}")
        
        else:
            st.info("No water bills found")
    
    # ============ GENERATE REPORT ============
    with tab4:
        st.subheader("Generate Water Bills Report")
        
        col1, col2 = st.columns(2)
        with col1:
            report_start = st.date_input("Start Date", value=date.today().replace(day=1), key="water_rep_start")
        with col2:
            report_end = st.date_input("End Date", value=date.today(), key="water_rep_end")
        
        if st.button("📄 Generate PDF Report", type="primary", key="water_gen_report"):
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, farmer_name, start_time, end_time, hours_used, 
                       rate_per_hour, total_bill, amount_paid, balance_due, payment_status
                FROM water_bills 
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            ''', (report_start, report_end))
            
            data = cursor.fetchall()
            
            if data:
                pdf_data = []
                for row in data:
                    pdf_data.append([
                        str(row[0]), row[1], 
                        f"{row[2]} to {row[3]}", 
                        f"{row[4]:.2f}", 
                        f"PKR {row[5]:,.2f}", 
                        f"PKR {row[6]:,.2f}", 
                        f"PKR {row[7]:,.2f}", 
                        f"PKR {row[8]:,.2f}", 
                        row[9]
                    ])
                
                columns = ['Date', 'Farmer', 'Time Used', 'Hours', 'Rate', 'Total Bill', 'Paid', 'Balance', 'Status']
                pdf_buffer = generate_pdf_report(pdf_data, "Water Bills Report", columns)
                
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_buffer,
                    file_name=f"water_bills_{report_start}_{report_end}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("No data found")

# ============================================
# OPERATIONAL EXPENSES
# ============================================
elif menu == "💰 Operational Expenses":
    st.markdown("<h1 class='main-header'>Operational Expenses</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Expense", "💳 Make Payment", "📋 View/Edit Expenses", "📄 Generate Report"])
    
    # ============ ADD EXPENSE ============
    with tab1:
        st.subheader("Add Operational Expense")
        
        with st.form("op_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Date*", value=date.today())
                expense_type = st.selectbox("Expense Type*",
                    ["Employee Salaries", "Fuel", "Machinery Purchase", 
                     "Machinery Maintenance", "Utilities", "Rent", "Other"])
                managed_by = st.text_input("Managed By (Employee Name)")
                
            with col2:
                amount = st.number_input("Amount (PKR)*", min_value=0.0, step=100.0)
                paid_to = st.text_input("Paid To (Person/Company)")
                description = st.text_area("Description")
            
            col3, col4 = st.columns(2)
            with col3:
                payment_method = st.selectbox("Payment Method",
                    ["Cash", "Bank Transfer", "Credit", "To Be Paid"])
            with col4:
                is_paid = st.checkbox("Mark as Paid")
                if is_paid:
                    paid_amount = st.number_input("Paid Amount", 
                        min_value=0.0, max_value=amount, value=amount, step=100.0)
                else:
                    paid_amount = 0
            
            submitted = st.form_submit_button("💾 Save Expense", type="primary")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    cursor = conn.cursor()
                    try:
                        balance_due = amount - paid_amount
                        
                        cursor.execute('''
                            INSERT INTO operational_expenses 
                            (date, expense_type, managed_by, amount, paid_to, 
                             paid_amount, balance_due, description, payment_method, is_paid)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (expense_date, expense_type, managed_by, amount, paid_to,
                              paid_amount, balance_due, description, payment_method, is_paid))
                        
                        expense_id = cursor.lastrowid
                        
                        # Add to ledger
                        add_ledger_entry(
                            transaction_date=expense_date,
                            account_name=f"Operational - {expense_type}",
                            account_type="Expense",
                            debit=amount,
                            credit=0,
                            reference_type="operational_expense",
                            reference_id=expense_id,
                            description=description
                        )
                        
                        if is_paid:
                            if payment_method == "Bank Transfer":
                                credit_account = "Bank Account"
                                acc_type = "Asset"
                            else:
                                credit_account = "Cash Account"
                                acc_type = "Asset"
                        else:
                            credit_account = "Accounts Payable"
                            acc_type = "Liability"
                        
                        add_ledger_entry(
                            transaction_date=expense_date,
                            account_name=credit_account,
                            account_type=acc_type,
                            debit=0,
                            credit=amount,
                            reference_type="operational_expense",
                            reference_id=expense_id,
                            description=f"Payment for {expense_type}"
                        )
                        
                        conn.commit()
                        st.success("✅ Operational expense recorded successfully!")
                        
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error saving expense: {str(e)}")
    
    # ============ MAKE PAYMENT ============
    with tab2:
        st.subheader("Make Payment for Outstanding Expenses")
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, date, expense_type, managed_by, amount, paid_amount, balance_due, description
            FROM operational_expenses 
            WHERE balance_due > 0
            ORDER BY date DESC
        ''')
        
        unpaid_expenses = cursor.fetchall()
        
        if not unpaid_expenses:
            st.info("No outstanding operational expenses")
        else:
            exp_options = {f"{e[2]} - PKR {e[6]:,.2f} due (ID: {e[0]})": e[0] for e in unpaid_expenses}
            
            selected_exp = st.selectbox("Select Expense", list(exp_options.keys()))
            exp_id = exp_options[selected_exp]
            
            cursor.execute('SELECT * FROM operational_expenses WHERE id = ?', (exp_id,))
            expense = cursor.fetchone()
            
            if expense:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Expense Type:** {expense[2]}")
                    st.write(f"**Managed By:** {expense[3]}")
                    st.write(f"**Total Amount:** PKR {expense[4]:,.2f}")
                    st.write(f"**Already Paid:** PKR {expense[5]:,.2f}")
                    st.write(f"**Balance Due:** PKR {expense[6]:,.2f}")
                    st.write(f"**Description:** {expense[7]}")
                
                with col2:
                    with st.form("op_payment_form"):
                        payment_date = st.date_input("Payment Date", value=date.today())
                        payment_amount = st.number_input("Payment Amount", 
                            min_value=0.0, max_value=expense[6], value=expense[6], step=100.0)
                        payment_method = st.selectbox("Payment Method",
                            ["Cash", "Bank Transfer", "Mobile Payment"])
                        
                        if st.form_submit_button("💵 Record Payment", type="primary"):
                            try:
                                # Update expense
                                new_paid = expense[5] + payment_amount
                                new_balance = expense[6] - payment_amount
                                
                                cursor.execute('''
                                    UPDATE operational_expenses 
                                    SET paid_amount = ?, balance_due = ?, 
                                        is_paid = ?, payment_method = ?,
                                        updated_at = CURRENT_TIMESTAMP
                                    WHERE id = ?
                                ''', (new_paid, new_balance, 
                                      1 if new_balance == 0 else 0,
                                      payment_method, exp_id))
                                
                                # Record payment in ledger
                                if payment_method == "Bank Transfer":
                                    debit_account = "Bank Account"
                                else:
                                    debit_account = "Cash Account"
                                
                                add_ledger_entry(
                                    transaction_date=payment_date,
                                    account_name=debit_account,
                                    account_type="Asset",
                                    debit=payment_amount,
                                    credit=0,
                                    reference_type="operational_payment",
                                    reference_id=exp_id,
                                    description=f"Payment for {expense[2]}"
                                )
                                
                                add_ledger_entry(
                                    transaction_date=payment_date,
                                    account_name="Accounts Payable",
                                    account_type="Liability",
                                    debit=0,
                                    credit=payment_amount,
                                    reference_type="operational_payment",
                                    reference_id=exp_id,
                                    description=f"Payment made for {expense[2]}"
                                )
                                
                                conn.commit()
                                st.success(f"✅ Payment of PKR {payment_amount:,.2f} recorded successfully!")
                                st.rerun()
                                
                            except Exception as e:
                                conn.rollback()
                                st.error(f"Error recording payment: {str(e)}")
    
    # ============ VIEW/EDIT EXPENSES ============
    with tab3:
        st.subheader("View & Edit Operational Expenses")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", value=date.today().replace(day=1), key="op_start")
        with col2:
            end_date = st.date_input("To Date", value=date.today(), key="op_end")
        
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, date, expense_type, managed_by, amount, paid_amount, balance_due, 
                   description, payment_method, is_paid
            FROM operational_expenses 
            WHERE date BETWEEN ? AND ?
            ORDER BY date DESC
        ''', (start_date, end_date))
        
        data = cursor.fetchall()
        
        if data:
            df = pd.DataFrame(data, columns=[
                'ID', 'Date', 'Expense Type', 'Managed By', 'Amount', 'Paid', 
                'Balance', 'Description', 'Payment Method', 'Is Paid'
            ])
            
            st.dataframe(df, use_container_width=True)
            
            # Summary
            total_expense = df['Amount'].sum()
            total_paid = df['Paid'].sum()
            total_balance = df['Balance'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Expense", f"PKR {total_expense:,.2f}")
            with col2:
                st.metric("Total Paid", f"PKR {total_paid:,.2f}")
            with col3:
                st.metric("Total Outstanding", f"PKR {total_balance:,.2f}")
        else:
            st.info("No operational expenses found")
    
    # ============ GENERATE REPORT ============
    with tab4:
        st.subheader("Generate Operational Expenses Report")
        
        col1, col2 = st.columns(2)
        with col1:
            report_start = st.date_input("Start Date", value=date.today().replace(day=1), key="op_rep_start")
        with col2:
            report_end = st.date_input("End Date", value=date.today(), key="op_rep_end")
        
        if st.button("📄 Generate PDF Report", type="primary", key="op_gen_report"):
            cursor = conn.cursor()
            cursor.execute('''
                SELECT date, expense_type, managed_by, amount, paid_amount, balance_due, 
                       description, payment_method
                FROM operational_expenses 
                WHERE date BETWEEN ? AND ?
                ORDER BY date
            ''', (report_start, report_end))
            
            data = cursor.fetchall()
            
            if data:
                pdf_data = []
                for row in data:
                    pdf_data.append([
                        str(row[0]), row[1], row[2] or "", 
                        f"PKR {row[3]:,.2f}", 
                        f"PKR {row[4]:,.2f}", 
                        f"PKR {row[5]:,.2f}", 
                        row[6] or "", 
                        row[7] or ""
                    ])
                
                columns = ['Date', 'Expense Type', 'Managed By', 'Amount', 'Paid', 'Balance', 'Description', 'Payment Method']
                pdf_buffer = generate_pdf_report(pdf_data, "Operational Expenses Report", columns)
                
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_buffer,
                    file_name=f"operational_expenses_{report_start}_{report_end}.pdf",
                    mime="application/pdf"
                )
            else:
                st.warning("No data found")

# ============================================
# REPORTS & ANALYTICS
# ============================================
elif menu == "📊 Reports & Analytics":
    st.markdown("<h1 class='main-header'>Reports & Analytics</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Profit & Loss", "💰 Cash Flow", "📊 Ledger Report", "📑 Comprehensive Report"])
    
    # ============ PROFIT & LOSS ============
    with tab1:
        st.subheader("Profit & Loss Statement")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", value=date.today().replace(day=1), key="pl_start")
        with col2:
            end_date = st.date_input("To Date", value=date.today(), key="pl_end")
        
        if st.button("Generate P&L Report", type="primary"):
            cursor = conn.cursor()
            
            # Calculate Income
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM livestock_income WHERE date BETWEEN ? AND ?", 
                          (start_date, end_date))
            livestock_income = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM crop_income WHERE date BETWEEN ? AND ?", 
                          (start_date, end_date))
            crop_income = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(total_bill), 0) FROM water_bills WHERE date BETWEEN ? AND ?", 
                          (start_date, end_date))
            water_income = cursor.fetchone()[0]
            
            total_income = livestock_income + crop_income + water_income
            
            # Calculate Expenses
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM livestock_expenses WHERE date BETWEEN ? AND ?", 
                          (start_date, end_date))
            livestock_exp = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM crop_expenses WHERE date BETWEEN ? AND ?", 
                          (start_date, end_date))
            crop_exp = cursor.fetchone()[0]
            
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM operational_expenses WHERE date BETWEEN ? AND ?", 
                          (start_date, end_date))
            operational_exp = cursor.fetchone()[0]
            
            total_expenses = livestock_exp + crop_exp + operational_exp
            
            # Calculate Net Profit/Loss
            net_profit = total_income - total_expenses
            
            # Display Results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Income", f"PKR {total_income:,.2f}")
            with col2:
                st.metric("Total Expenses", f"PKR {total_expenses:,.2f}")
            with col3:
                st.metric("Net Profit/Loss", f"PKR {net_profit:,.2f}")
            
            # Detailed Breakdown
            st.subheader("Detailed Breakdown")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Income Sources")
                income_data = {
                    "Category": ["Livestock Income", "Crop Income", "Water Income", "Total Income"],
                    "Amount": [livestock_income, crop_income, water_income, total_income]
                }
                df_income = pd.DataFrame(income_data)
                st.dataframe(df_income, use_container_width=True)
                
                # Pie chart for income
                fig_income = px.pie(df_income.iloc[:-1], values='Amount', names='Category', 
                                  title='Income Distribution')
                st.plotly_chart(fig_income, use_container_width=True)
            
            with col2:
                st.markdown("#### Expense Categories")
                expense_data = {
                    "Category": ["Livestock Expenses", "Crop Expenses", "Operational Expenses", "Total Expenses"],
                    "Amount": [livestock_exp, crop_exp, operational_exp, total_expenses]
                }
                df_expense = pd.DataFrame(expense_data)
                st.dataframe(df_expense, use_container_width=True)
                
                # Pie chart for expenses
                fig_expense = px.pie(df_expense.iloc[:-1], values='Amount', names='Category', 
                                   title='Expense Distribution')
                st.plotly_chart(fig_expense, use_container_width=True)
    
    # ============ CASH FLOW ============
    with tab2:
        st.subheader("Cash Flow Statement")
        
        col1, col2 = st.columns(2)
        with col1:
            cash_start = st.date_input("From Date", value=date.today().replace(day=1), key="cash_start")
        with col2:
            cash_end = st.date_input("To Date", value=date.today(), key="cash_end")
        
        if st.button("Generate Cash Flow", type="primary"):
            cursor = conn.cursor()
            
            # Get cash inflows (income received in cash)
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM livestock_income 
                WHERE date BETWEEN ? AND ? AND payment_method IN ('Cash', 'Mobile Payment')
            ''', (cash_start, cash_end))
            cash_livestock = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM crop_income 
                WHERE date BETWEEN ? AND ? AND payment_method IN ('Cash', 'Mobile Payment')
            ''', (cash_start, cash_end))
            cash_crop = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount_paid), 0) FROM water_bills 
                WHERE date BETWEEN ? AND ? AND payment_method IN ('Cash', 'Mobile Payment')
            ''', (cash_start, cash_end))
            cash_water = cursor.fetchone()[0]
            
            total_cash_in = cash_livestock + cash_crop + cash_water
            
            # Get cash outflows (expenses paid in cash)
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM livestock_expenses 
                WHERE date BETWEEN ? AND ? AND payment_method IN ('Cash', 'Mobile Payment')
            ''', (cash_start, cash_end))
            cash_out_livestock = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM crop_expenses 
                WHERE date BETWEEN ? AND ? AND payment_method IN ('Cash', 'Mobile Payment')
            ''', (cash_start, cash_end))
            cash_out_crop = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COALESCE(SUM(amount), 0) FROM operational_expenses 
                WHERE date BETWEEN ? AND ? AND payment_method IN ('Cash', 'Mobile Payment') AND is_paid = 1
            ''', (cash_start, cash_end))
            cash_out_operational = cursor.fetchone()[0]
            
            total_cash_out = cash_out_livestock + cash_out_crop + cash_out_operational
            
            net_cash_flow = total_cash_in - total_cash_out
            
            # Display Results
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Cash Inflow", f"PKR {total_cash_in:,.2f}")
            with col2:
                st.metric("Cash Outflow", f"PKR {total_cash_out:,.2f}")
            with col3:
                st.metric("Net Cash Flow", f"PKR {net_cash_flow:,.2f}")
            
            # Cash Flow Details
            st.subheader("Cash Flow Details")
            
            cash_data = {
                "Category": [
                    "Livestock Income (Cash)", "Crop Income (Cash)", "Water Payments (Cash)",
                    "Livestock Expenses (Cash)", "Crop Expenses (Cash)", "Operational Expenses (Cash)"
                ],
                "Amount": [
                    cash_livestock, cash_crop, cash_water,
                    -cash_out_livestock, -cash_out_crop, -cash_out_operational
                ]
            }
            
            df_cash = pd.DataFrame(cash_data)
            df_cash['Type'] = df_cash['Amount'].apply(lambda x: 'Inflow' if x >= 0 else 'Outflow')
            
            fig = px.bar(df_cash, x='Category', y='Amount', color='Type',
                        title='Detailed Cash Flow',
                        color_discrete_map={'Inflow': 'green', 'Outflow': 'red'})
            st.plotly_chart(fig, use_container_width=True)
    
    # ============ LEDGER REPORT ============
    with tab3:
        st.subheader("General Ledger Report")
        
        col1, col2 = st.columns(2)
        with col1:
            ledger_start = st.date_input("From Date", value=date.today().replace(day=1), key="ledger_start")
        with col2:
            ledger_end = st.date_input("To Date", value=date.today(), key="ledger_end")
        
        if st.button("Generate Ledger Report", type="primary"):
            cursor = conn.cursor()
            cursor.execute('''
                SELECT transaction_date, account_name, account_type, debit, credit, 
                       description, reference_type, reference_id
                FROM ledger 
                WHERE transaction_date BETWEEN ? AND ?
                ORDER BY transaction_date, id
            ''', (ledger_start, ledger_end))
            
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=[
                    'Date', 'Account', 'Type', 'Debit', 'Credit', 
                    'Description', 'Reference Type', 'Reference ID'
                ])
                
                st.dataframe(df, use_container_width=True)
                
                # Summary
                total_debit = df['Debit'].sum()
                total_credit = df['Credit'].sum()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Debit", f"PKR {total_debit:,.2f}")
                with col2:
                    st.metric("Total Credit", f"PKR {total_credit:,.2f}")
                
                # Check if ledger balances
                if abs(total_debit - total_credit) < 0.01:
                    st.success("✓ Ledger is balanced")
                else:
                    st.error(f"⚠️ Ledger imbalance: PKR {abs(total_debit - total_credit):,.2f}")
            else:
                st.info("No ledger entries found")
    
    # ============ COMPREHENSIVE REPORT ============
    with tab4:
        st.subheader("Comprehensive Farm Report")
        
        col1, col2 = st.columns(2)
        with col1:
            comp_start = st.date_input("From Date", value=date.today().replace(month=1, day=1), key="comp_start")
        with col2:
            comp_end = st.date_input("To Date", value=date.today(), key="comp_end")
        
        if st.button("Generate Comprehensive PDF Report", type="primary"):
            cursor = conn.cursor()
            
            # Get all data
            reports = {}
            
            # Livestock Expenses
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM livestock_expenses WHERE date BETWEEN ? AND ?', 
                          (comp_start, comp_end))
            reports['Livestock Expenses'] = cursor.fetchone()[0]
            
            # Livestock Income
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM livestock_income WHERE date BETWEEN ? AND ?', 
                          (comp_start, comp_end))
            reports['Livestock Income'] = cursor.fetchone()[0]
            
            # Crop Expenses
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM crop_expenses WHERE date BETWEEN ? AND ?', 
                          (comp_start, comp_end))
            reports['Crop Expenses'] = cursor.fetchone()[0]
            
            # Crop Income
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM crop_income WHERE date BETWEEN ? AND ?', 
                          (comp_start, comp_end))
            reports['Crop Income'] = cursor.fetchone()[0]
            
            # Water Income
            cursor.execute('SELECT COALESCE(SUM(total_bill), 0) FROM water_bills WHERE date BETWEEN ? AND ?', 
                          (comp_start, comp_end))
            reports['Water Income'] = cursor.fetchone()[0]
            
            # Operational Expenses
            cursor.execute('SELECT COALESCE(SUM(amount), 0) FROM operational_expenses WHERE date BETWEEN ? AND ?', 
                          (comp_start, comp_end))
            reports['Operational Expenses'] = cursor.fetchone()[0]
            
            # Calculate totals
            total_income = reports['Livestock Income'] + reports['Crop Income'] + reports['Water Income']
            total_expenses = reports['Livestock Expenses'] + reports['Crop Expenses'] + reports['Operational Expenses']
            net_profit = total_income - total_expenses
            
            # Prepare data for PDF
            report_data = [
                ["Livestock Income", f"PKR {reports['Livestock Income']:,.2f}"],
                ["Crop Income", f"PKR {reports['Crop Income']:,.2f}"],
                ["Water Income", f"PKR {reports['Water Income']:,.2f}"],
                ["", ""],
                ["Total Income", f"PKR {total_income:,.2f}"],
                ["", ""],
                ["Livestock Expenses", f"PKR {reports['Livestock Expenses']:,.2f}"],
                ["Crop Expenses", f"PKR {reports['Crop Expenses']:,.2f}"],
                ["Operational Expenses", f"PKR {reports['Operational Expenses']:,.2f}"],
                ["", ""],
                ["Total Expenses", f"PKR {total_expenses:,.2f}"],
                ["", ""],
                ["Net Profit/Loss", f"PKR {net_profit:,.2f}"],
                ["Profit Margin", f"{(net_profit/total_income*100 if total_income > 0 else 0):.1f}%"]
            ]
            
            pdf_buffer = generate_pdf_report(report_data, "Comprehensive Farm Report", ['Category', 'Amount'])
            
            st.download_button(
                label="📥 Download Comprehensive Report",
                data=pdf_buffer,
                file_name=f"farm_comprehensive_report_{comp_start}_{comp_end}.pdf",
                mime="application/pdf"
            )

# ============================================
# EMPLOYEES & FARMERS
# ============================================
elif menu == "👥 Employees & Farmers":
    st.markdown("<h1 class='main-header'>Employees & Farmers Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["👨‍💼 Employees", "👨‍🌾 Farmers"])
    
    # ============ EMPLOYEES ============
    with tab1:
        st.subheader("Employee Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Add New Employee")
            with st.form("employee_form"):
                emp_name = st.text_input("Employee Name*")
                emp_phone = st.text_input("Phone Number")
                emp_designation = st.selectbox("Designation", 
                    ["Farm Manager", "Worker", "Driver", "Supervisor", "Accountant", "Other"])
                emp_salary = st.number_input("Monthly Salary (PKR)", min_value=0.0, step=1000.0)
                emp_address = st.text_area("Address")
                
                if st.form_submit_button("Add Employee", type="primary"):
                    if emp_name:
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO employees (name, phone, designation, salary, address)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (emp_name, emp_phone, emp_designation, emp_salary, emp_address))
                            conn.commit()
                            st.success(f"✅ Employee '{emp_name}' added successfully!")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error adding employee: {str(e)}")
                    else:
                        st.error("Employee name is required")
        
        with col2:
            st.markdown("#### Employee List")
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, phone, designation, salary FROM employees ORDER BY name')
            employees = cursor.fetchall()
            
            if employees:
                df_emp = pd.DataFrame(employees, columns=['ID', 'Name', 'Phone', 'Designation', 'Salary'])
                st.dataframe(df_emp, use_container_width=True)
                
                # Edit/Delete Employee
                st.markdown("#### Edit/Delete Employee")
                emp_id = st.number_input("Enter Employee ID", min_value=1, step=1)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit Employee"):
                        cursor.execute('SELECT * FROM employees WHERE id = ?', (emp_id,))
                        emp = cursor.fetchone()
                        
                        if emp:
                            with st.form("edit_employee_form"):
                                st.write(f"Editing Employee ID: {emp_id}")
                                
                                edit_name = st.text_input("Name", value=emp[1])
                                edit_phone = st.text_input("Phone", value=emp[2] or "")
                                edit_desig = st.text_input("Designation", value=emp[3] or "")
                                edit_salary = st.number_input("Salary", value=emp[4] or 0.0)
                                edit_address = st.text_area("Address", value=emp[5] or "")
                                
                                if st.form_submit_button("Update Employee"):
                                    try:
                                        cursor.execute('''
                                            UPDATE employees 
                                            SET name = ?, phone = ?, designation = ?, salary = ?, address = ?
                                            WHERE id = ?
                                        ''', (edit_name, edit_phone, edit_desig, edit_salary, edit_address, emp_id))
                                        conn.commit()
                                        st.success("✅ Employee updated!")
                                        st.rerun()
                                    except Exception as e:
                                        conn.rollback()
                                        st.error(f"Error updating: {str(e)}")
                
                with col2:
                    if st.button("Delete Employee", type="secondary"):
                        try:
                            cursor.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
                            conn.commit()
                            st.success("✅ Employee deleted!")
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error deleting: {str(e)}")
            else:
                st.info("No employees added yet")
    
    # ============ FARMERS ============
    with tab2:
        st.subheader("Farmer Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Add New Farmer")
            with st.form("farmer_form"):
                farmer_name = st.text_input("Farmer Name*")
                farmer_phone = st.text_input("Phone Number")
                farmer_address = st.text_area("Address")
                
                if st.form_submit_button("Add Farmer", type="primary"):
                    if farmer_name:
                        cursor = conn.cursor()
                        try:
                            cursor.execute('''
                                INSERT INTO farmers (name, phone, address)
                                VALUES (?, ?, ?)
                            ''', (farmer_name, farmer_phone, farmer_address))
                            conn.commit()
                            st.success(f"✅ Farmer '{farmer_name}' added successfully!")
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error adding farmer: {str(e)}")
                    else:
                        st.error("Farmer name is required")
        
        with col2:
            st.markdown("#### Farmer List")
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, phone, address FROM farmers ORDER BY name')
            farmers = cursor.fetchall()
            
            if farmers:
                df_farmers = pd.DataFrame(farmers, columns=['ID', 'Name', 'Phone', 'Address'])
                st.dataframe(df_farmers, use_container_width=True)
                
                # Farmer Outstanding Balances
                st.markdown("#### Farmer Outstanding Balances")
                cursor.execute('''
                    SELECT farmer_name, COALESCE(SUM(balance_due), 0) as total_due
                    FROM water_bills 
                    WHERE balance_due > 0
                    GROUP BY farmer_name
                    ORDER BY total_due DESC
                ''')
                outstanding = cursor.fetchall()
                
                if outstanding:
                    df_out = pd.DataFrame(outstanding, columns=['Farmer', 'Outstanding Balance'])
                    st.dataframe(df_out, use_container_width=True)
                    
                    total_outstanding = df_out['Outstanding Balance'].sum()
                    st.metric("Total Outstanding from Farmers", f"PKR {total_outstanding:,.2f}")
                else:
                    st.info("No outstanding balances from farmers")

# ============================================
# FOOTER
# ============================================
st.sidebar.markdown("---")
st.sidebar.markdown("**Farm Management System** © 2024")
st.sidebar.markdown("*Version 2.0*")

# Close database connection when done
conn.close()
