# Streamlit Enterprise Management System - Professional Version
import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io
import time
import uuid
import base64
from datetime import datetime, date, timedelta

# --- CONFIGURATION ---
EXPENSE_CATEGORIES = [
    "Guard", "Labour", "Bilty Expenses", "Office Rent", "Warehouse Rent", 
    "Muhammad Asim Iqbal Salary", "Import Export", "Office Electricity", "FBR", 
    "Abdul Manan Sb Salary", "Office Entertainment", "PSID", "Advance", 
    "Commission", "Office Stationery Expense", "Employee Expenses", "Other Expense", 
    "Company Expense", "Muhammad Abdullah Salary",
    "Fine", "Other Deduction", 
    "Employee Expense Claim", "Employee Expense Payment" 
]

EMPLOYEE_EXPENSE_CATEGORIES = [
    "Travel Expense", "Meal Allowance", "Transportation", "Office Supplies",
    "Client Entertainment", "Phone Bill", "Internet Bill", "Other Expense"
]

DB_NAME = "nutrion_enterprise.db"

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 1rem;
        border-bottom: 3px solid #667eea;
        padding-bottom: 0.5rem;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border-left: 5px solid #667eea;
        transition: transform 0.3s ease;
    }
    .card:hover {
        transform: translateY(-5px);
    }
    .positive {
        color: #10b981;
        font-weight: bold;
        font-size: 1.1em;
    }
    .negative {
        color: #ef4444;
        font-weight: bold;
        font-size: 1.1em;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
        margin: 0.5rem;
    }
    .footer {
        background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
        color: white;
        padding: 2rem;
        text-align: center;
        margin-top: 3rem;
        border-radius: 15px;
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1.5rem;
        border-radius: 25px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: scale(1.05);
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
    }
    .success-message {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .warning-message {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .info-card {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .form-container {
        background: white;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    .data-table {
        background: white;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
    }
    .search-box {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .edit-btn {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        margin-right: 0.5rem;
        color: white !important;
        border: none !important;
    }
    .delete-btn {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: white !important;
        border: none !important;
    }
    .update-btn {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        margin-right: 0.5rem;
    }
    .quick-action-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 15px;
        font-weight: 600;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        width: 100%;
        margin: 0.5rem 0;
    }
    .quick-action-btn:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
    }
    .download-btn {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        margin: 0.2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- DATABASE SETUP ---
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database and creates tables if they don't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Employee Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        designation TEXT,
        bank_name TEXT,
        account_title TEXT,
        account_number TEXT,
        salary REAL DEFAULT 0,
        phone TEXT DEFAULT '',
        email TEXT DEFAULT '',
        department TEXT DEFAULT '',
        join_date TEXT DEFAULT CURRENT_TIMESTAMP,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Expense Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id TEXT PRIMARY KEY,
        expense_date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        employee_id TEXT,
        added_by TEXT DEFAULT 'System',
        status TEXT DEFAULT 'Approved',
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE SET NULL
    );
    """)
    
    # Employee Self-Service Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_expenses (
        id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        expense_date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        receipt_uploaded BOOLEAN DEFAULT 0,
        receipt_path TEXT,
        status TEXT DEFAULT 'Pending',
        approved_by TEXT,
        approved_date TEXT,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
    );
    """)
    
    # Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id TEXT PRIMARY KEY,
        company_name TEXT DEFAULT 'Nutrion Enterprise',
        company_address TEXT DEFAULT 'Karachi, Pakistan',
        company_phone TEXT DEFAULT '+92-320-7429422',
        company_email TEXT DEFAULT 'info@nutrion.com',
        currency TEXT DEFAULT 'PKR',
        created_date TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Insert default settings if not exists
    cursor.execute("""
    INSERT OR IGNORE INTO settings (id, company_name, company_address, company_phone, company_email, currency)
    VALUES ('default', 'Nutrion Enterprise', 'Karachi, Pakistan', '+92-320-7429422', 'info@nutrion.com', 'PKR')
    """)
    
    # Add missing columns to existing tables if they don't exist
    try:
        cursor.execute("SELECT phone FROM employees LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE employees ADD COLUMN phone TEXT DEFAULT ''")
    
    try:
        cursor.execute("SELECT email FROM employees LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE employees ADD COLUMN email TEXT DEFAULT ''")
    
    try:
        cursor.execute("SELECT department FROM employees LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("ALTER TABLE employees ADD COLUMN department TEXT DEFAULT ''")
    
    conn.commit()
    conn.close()

# --- SETTINGS MANAGEMENT ---
class SettingsManager:
    def __init__(self):
        init_db()

    def get_settings(self):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('SELECT * FROM settings WHERE id = "default"')
        row = c.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'company_name': row[1],
                'company_address': row[2],
                'company_phone': row[3],
                'company_email': row[4],
                'currency': row[5],
                'created_date': row[6]
            }
        return None

    def update_settings(self, company_name, company_address, company_phone, company_email, currency):
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            UPDATE settings 
            SET company_name = ?, company_address = ?, company_phone = ?, company_email = ?, currency = ?
            WHERE id = "default"
        ''', (company_name, company_address, company_phone, company_email, currency))
        conn.commit()
        conn.close()

# --- EMPLOYEE CRUD FUNCTIONS ---
def add_employee(name, designation, bank_name, account_title, account_number, salary, phone="", email="", department=""):
    """Adds a new employee to the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        employee_id = str(uuid.uuid4())
        
        cursor.execute(
            """INSERT INTO employees (id, name, designation, bank_name, account_title, account_number, salary, phone, email, department) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (employee_id, name, designation, bank_name, account_title, account_number, salary, phone, email, department)
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Successfully added employee: {name}")
        return employee_id
    except Exception as e:
        st.error(f"❌ Error adding employee: {e}")
        return None

def get_employees():
    """Fetches all employees as a Pandas DataFrame."""
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT id, name, designation, bank_name, account_title, account_number, salary, 
               phone, email, department, join_date, created_date 
        FROM employees 
        ORDER BY name
    """, conn)
    conn.close()
    
    if 'account_number' in df.columns:
        df['account_number'] = df['account_number'].astype(str).fillna('')
        
    return df

def get_employee_by_id(emp_id):
    """Fetches a single employee by ID."""
    conn = get_db_connection()
    employee = conn.execute(
        "SELECT * FROM employees WHERE id = ?", (emp_id,)
    ).fetchone()
    conn.close()
    return dict(employee) if employee else None

def update_employee(emp_id, name, designation, bank_name, account_title, account_number, salary, phone, email, department):
    """Updates an existing employee's details."""
    try:
        conn = get_db_connection()
        conn.execute(
            """UPDATE employees SET 
               name = ?, designation = ?, bank_name = ?, 
               account_title = ?, account_number = ?, salary = ?,
               phone = ?, email = ?, department = ?
               WHERE id = ?""",
            (name, designation, bank_name, account_title, account_number, salary, phone, email, department, emp_id)
        )
        conn.commit()
        conn.close()
        st.success(f"✅ Successfully updated employee: {name}")
        return True
    except Exception as e:
        st.error(f"❌ Error updating employee: {e}")
        return False

def delete_employee(emp_id):
    """Deletes an employee from the database."""
    try:
        conn = get_db_connection()
        employee = get_employee_by_id(emp_id)
        employee_name = employee['name'] if employee else "Unknown"
        
        conn.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
        conn.commit()
        conn.close()
        st.success(f"✅ Successfully deleted employee: {employee_name}")
        return True
    except Exception as e:
        st.error(f"❌ Error deleting employee: {e}")
        return False

def get_employee_names():
    """Gets a list of employee names and their IDs."""
    conn = get_db_connection()
    employees = conn.execute("SELECT id, name FROM employees ORDER BY name").fetchall()
    conn.close()
    return {emp['id']: emp['name'] for emp in employees}

# --- EMPLOYEE SELF-SERVICE FUNCTIONS ---
def add_employee_expense(employee_id, expense_date, category, amount, description):
    """Adds a new expense submitted by employee."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        expense_id = str(uuid.uuid4())
        
        cursor.execute(
            """INSERT INTO employee_expenses 
               (id, employee_id, expense_date, category, amount, description) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (expense_id, employee_id, expense_date.strftime('%Y-%m-%d'), category, amount, description)
        )
        conn.commit()
        conn.close()
        return expense_id, True
    except Exception as e:
        st.error(f"❌ Error adding employee expense: {e}")
        return None, False

def get_employee_expenses(employee_id, status_filter="All"):
    """Gets expenses submitted by a specific employee."""
    conn = get_db_connection()
    
    if status_filter == "All":
        query = "SELECT * FROM employee_expenses WHERE employee_id = ? ORDER BY expense_date DESC"
        params = (employee_id,)
    else:
        query = "SELECT * FROM employee_expenses WHERE employee_id = ? AND status = ? ORDER BY expense_date DESC"
        params = (employee_id, status_filter)
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_all_pending_expenses():
    """Gets all pending expenses for approval."""
    conn = get_db_connection()
    df = pd.read_sql_query("""
        SELECT ee.*, e.name as employee_name 
        FROM employee_expenses ee 
        JOIN employees e ON ee.employee_id = e.id 
        WHERE ee.status = 'Pending' 
        ORDER BY ee.expense_date DESC
    """, conn)
    conn.close()
    return df

def approve_employee_expense(expense_id, approved_by="Admin"):
    """Approves an employee expense."""
    try:
        conn = get_db_connection()
        conn.execute(
            """UPDATE employee_expenses SET 
               status = 'Approved', approved_by = ?, approved_date = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (approved_by, expense_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Error approving expense: {e}")
        return False

def reject_employee_expense(expense_id, approved_by="Admin"):
    """Rejects an employee expense."""
    try:
        conn = get_db_connection()
        conn.execute(
            """UPDATE employee_expenses SET 
               status = 'Rejected', approved_by = ?, approved_date = CURRENT_TIMESTAMP 
               WHERE id = ?""",
            (approved_by, expense_id)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"❌ Error rejecting expense: {e}")
        return False

# --- EXPENSE CRUD FUNCTIONS ---
def add_expense(expense_date, category, amount, description, employee_id=None):
    """Adds a new expense record."""
    try:
        conn = get_db_connection()
        expense_id = str(uuid.uuid4())
        
        conn.execute(
            "INSERT INTO expenses (id, expense_date, category, amount, description, employee_id) VALUES (?, ?, ?, ?, ?, ?)",
            (expense_id, expense_date.strftime('%Y-%m-%d'), category, amount, description, employee_id)
        )
        conn.commit()
        conn.close()
        st.success("✅ Successfully added expense.")
        return True
    except Exception as e:
        st.error(f"❌ Error adding expense: {e}")
        return False

def get_expenses(start_date=None, end_date=None):
    """Fetches all expenses within a date range as a DataFrame."""
    conn = get_db_connection()
    
    if start_date and end_date:
        query = """
        SELECT e.id, e.expense_date, e.category, e.amount, e.description, 
               IFNULL(emp.name, 'N/A') as employee_name, e.status, e.employee_id
        FROM expenses e
        LEFT JOIN employees emp ON e.employee_id = emp.id
        WHERE e.expense_date BETWEEN ? AND ?
        ORDER BY e.expense_date DESC
        """
        params = (start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
    else:
        query = """
        SELECT e.id, e.expense_date, e.category, e.amount, e.description, 
               IFNULL(emp.name, 'N/A') as employee_name, e.status, e.employee_id
        FROM expenses e
        LEFT JOIN employees emp ON e.employee_id = emp.id
        ORDER BY e.expense_date DESC
        """
        params = ()
    
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def get_expense_by_id(expense_id):
    """Fetches a single expense by ID."""
    conn = get_db_connection()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ?", (expense_id,)
    ).fetchone()
    conn.close()
    return dict(expense) if expense else None

def update_expense(expense_id, expense_date, category, amount, description, employee_id=None):
    """Updates an existing expense."""
    try:
        conn = get_db_connection()
        conn.execute(
            """UPDATE expenses SET 
               expense_date = ?, category = ?, amount = ?, description = ?, employee_id = ?
               WHERE id = ?""",
            (expense_date.strftime('%Y-%m-%d'), category, amount, description, employee_id, expense_id)
        )
        conn.commit()
        conn.close()
        st.success("✅ Successfully updated expense.")
        return True
    except Exception as e:
        st.error(f"❌ Error updating expense: {e}")
        return False

def delete_expense(expense_id):
    """Deletes an expense from the database."""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()
        st.success("✅ Successfully deleted expense.")
        return True
    except Exception as e:
        st.error(f"❌ Error deleting expense: {e}")
        return False

def get_expenses_for_employee(employee_id, start_date, end_date):
    """Fetches all SALARY DEDUCTIONS for a specific employee."""
    conn = get_db_connection()
    query = """
    SELECT expense_date, category, description, amount
    FROM expenses
    WHERE employee_id = ? AND expense_date BETWEEN ? AND ?
    AND category NOT IN ('Employee Expense Claim', 'Employee Expense Payment')
    ORDER BY expense_date ASC
    """
    df = pd.read_sql_query(query, conn, params=(employee_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    conn.close()
    return df

def get_employee_expense_ledger(employee_id, start_date, end_date):
    """Fetches claims and payments for an employee's expense ledger."""
    conn = get_db_connection()
    query = """
    SELECT id, expense_date, category, description, amount
    FROM expenses
    WHERE employee_id = ? 
      AND (category = 'Employee Expense Claim' OR category = 'Employee Expense Payment')
      AND expense_date BETWEEN ? AND ?
    ORDER BY expense_date ASC
    """
    df = pd.read_sql_query(query, conn, params=(employee_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    conn.close()
    return df

# --- PDF REPORTING FUNCTIONS ---
class PDF(FPDF):
    """Custom PDF class with professional styling."""
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(41, 128, 185)
        self.cell(0, 10, 'NUTRION ENTERPRISE', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.set_text_color(128, 128, 128)
        self.cell(0, 8, self.title, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} | Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

def create_employee_ledger_pdf(employee, start_date, end_date, expenses_df, employee_expenses_df):
    """Generates a comprehensive PDF ledger for employee."""
    settings_manager = SettingsManager()
    settings = settings_manager.get_settings()
    
    pdf = PDF()
    pdf.title = f'Employee Ledger - {start_date} to {end_date}'
    pdf.add_page()
    
    # Employee Information
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, 'Employee Information', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    info_data = [
        ['Name:', employee['name']],
        ['Designation:', employee.get('designation', 'N/A')],
        ['Bank:', employee.get('bank_name', 'N/A')],
        ['Account:', f"{employee.get('account_title', 'N/A')} - {employee.get('account_number', 'N/A')}"],
        ['Salary:', f"{settings['currency']} {employee['salary']:,.2f}"],
        ['Period:', f"{start_date} to {end_date}"]
    ]
    
    for label, value in info_data:
        pdf.cell(40, 8, label, 0, 0)
        pdf.cell(0, 8, str(value), 0, 1)
    
    pdf.ln(10)
    
    # Expense Summary
    total_expenses = expenses_df['amount'].sum() if not expenses_df.empty else 0
    total_employee_expenses = employee_expenses_df[employee_expenses_df['status'] == 'Approved']['amount'].sum() if not employee_expenses_df.empty else 0
    net_salary = employee['salary'] - total_expenses
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, 'Financial Summary', 0, 1)
    pdf.set_font('Arial', '', 11)
    
    summary_data = [
        ['Base Salary:', f"{settings['currency']} {employee['salary']:,.2f}"],
        ['Deductions:', f"{settings['currency']} {total_expenses:,.2f}"],
        ['Approved Claims:', f"{settings['currency']} {total_employee_expenses:,.2f}"],
        ['Net Payable:', f"{settings['currency']} {net_salary:,.2f}"]
    ]
    
    for label, value in summary_data:
        pdf.cell(50, 8, label, 0, 0)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, value, 0, 1)
        pdf.set_font('Arial', '', 11)
    
    pdf.ln(10)
    
    # Employee Submitted Expenses
    if not employee_expenses_df.empty:
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(41, 128, 185)
        pdf.cell(0, 10, 'Employee Submitted Expenses', 0, 1)
        
        # Table header
        pdf.set_fill_color(41, 128, 185)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(25, 8, 'Date', 1, 0, 'C', True)
        pdf.cell(40, 8, 'Category', 1, 0, 'C', True)
        pdf.cell(80, 8, 'Description', 1, 0, 'C', True)
        pdf.cell(25, 8, 'Amount', 1, 0, 'C', True)
        pdf.cell(20, 8, 'Status', 1, 1, 'C', True)
        
        # Table rows
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 9)
        
        for _, row in employee_expenses_df.iterrows():
            pdf.cell(25, 8, row['expense_date'], 1, 0)
            pdf.cell(40, 8, row['category'][:25], 1, 0)
            pdf.cell(80, 8, str(row['description'])[:45], 1, 0)
            pdf.cell(25, 8, f"{row['amount']:,.2f}", 1, 0, 'R')
            
            # Color code status
            if row['status'] == 'Approved':
                pdf.set_text_color(0, 128, 0)
            elif row['status'] == 'Rejected':
                pdf.set_text_color(255, 0, 0)
            else:
                pdf.set_text_color(255, 165, 0)
                
            pdf.cell(20, 8, row['status'], 1, 1, 'C')
            pdf.set_text_color(0, 0, 0)
        
        pdf.ln(5)
    
    # System Deductions
    if not expenses_df.empty:
        pdf.set_font('Arial', 'B', 14)
        pdf.set_text_color(41, 128, 185)
        pdf.cell(0, 10, 'System Deductions', 0, 1)
        
        # Table header
        pdf.set_fill_color(41, 128, 185)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(25, 8, 'Date', 1, 0, 'C', True)
        pdf.cell(50, 8, 'Category', 1, 0, 'C', True)
        pdf.cell(70, 8, 'Description', 1, 0, 'C', True)
        pdf.cell(35, 8, 'Amount', 1, 1, 'C', True)
        
        # Table rows
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 9)
        
        for _, row in expenses_df.iterrows():
            pdf.cell(25, 8, row['expense_date'], 1, 0)
            pdf.cell(50, 8, row['category'][:30], 1, 0)
            pdf.cell(70, 8, str(row['description'])[:45], 1, 0)
            pdf.cell(35, 8, f"{row['amount']:,.2f}", 1, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

def create_salary_slip_pdf(employee, month_year, deductions=0, net_salary=None):
    """Generates a professional salary slip PDF with account details."""
    settings_manager = SettingsManager()
    settings = settings_manager.get_settings()
    
    pdf = PDF()
    pdf.title = f'Salary Slip - {month_year}'
    pdf.add_page()
    
    # Header with company info
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, settings['company_name'], 0, 1, 'C')
    pdf.set_font('Arial', 'I', 12)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 8, 'Salary Slip', 0, 1, 'C')
    pdf.cell(0, 8, f'For the month of {month_year}', 0, 1, 'C')
    pdf.ln(10)
    
    # Employee Details Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, 'Employee Details', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    employee_details = [
        ['Employee Name:', employee['name']],
        ['Designation:', employee.get('designation', 'N/A')],
        ['Employee ID:', employee['id'][:8]],
        ['Department:', employee.get('department', 'N/A')],
        ['Payment Month:', month_year],
        ['Payment Date:', datetime.now().strftime('%d-%b-%Y')]
    ]
    
    for label, value in employee_details:
        pdf.cell(50, 8, label, 0, 0)
        pdf.cell(0, 8, str(value), 0, 1)
    
    pdf.ln(10)
    
    # Bank Details Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, 'Bank Details', 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.set_text_color(0, 0, 0)
    
    bank_details = [
        ['Bank Name:', employee.get('bank_name', 'N/A')],
        ['Account Title:', employee.get('account_title', 'N/A')],
        ['Account Number:', employee.get('account_number', 'N/A')]
    ]
    
    for label, value in bank_details:
        pdf.cell(45, 8, label, 0, 0)
        pdf.cell(0, 8, str(value), 0, 1)
    
    pdf.ln(10)
    
    # Salary Breakdown Section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, 'Salary Breakdown', 0, 1)
    
    # Table header
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(100, 10, 'Description', 1, 0, 'C', True)
    pdf.cell(0, 10, 'Amount (PKR)', 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 11)
    
    # Basic Salary
    pdf.cell(100, 10, 'Basic Salary', 1, 0)
    pdf.cell(0, 10, f"{employee['salary']:,.2f}", 1, 1, 'R')
    
    # Deductions
    if deductions > 0:
        pdf.cell(100, 10, 'Total Deductions', 1, 0)
        pdf.cell(0, 10, f"({deductions:,.2f})", 1, 1, 'R')
    
    # Net Salary
    net_salary = net_salary or (employee['salary'] - deductions)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(100, 10, 'Net Salary Payable', 1, 0)
    pdf.set_text_color(0, 128, 0)  # Green for net salary
    pdf.cell(0, 10, f"{net_salary:,.2f}", 1, 1, 'R')
    pdf.set_text_color(0, 0, 0)
    
    pdf.ln(15)
    
    # Authorization Section
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, '_________________________', 0, 1, 'R')
    pdf.cell(0, 8, 'Authorized Signature', 0, 1, 'R')
    
    pdf.ln(10)
    
    # Footer Note
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 6, f"Note: This is a computer generated salary slip and does not require signature. For any queries, please contact {settings['company_phone']} or email {settings['company_email']}")
    
    return pdf.output(dest='S').encode('latin-1')

def create_bulk_salary_sheet_pdf(employees_data, month_year):
    """Generates a bulk salary sheet PDF for all employees."""
    settings_manager = SettingsManager()
    settings = settings_manager.get_settings()
    
    pdf = PDF()
    pdf.title = f'Salary Sheet - {month_year}'
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 18)
    pdf.set_text_color(41, 128, 185)
    pdf.cell(0, 10, settings['company_name'], 0, 1, 'C')
    pdf.set_font('Arial', 'I', 14)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 8, f'Monthly Salary Sheet - {month_year}', 0, 1, 'C')
    pdf.ln(5)
    
    # Summary
    total_salary = sum(emp['salary'] for emp in employees_data)
    total_deductions = sum(emp.get('deductions', 0) for emp in employees_data)
    total_net = sum(emp.get('net_salary', emp['salary']) for emp in employees_data)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, f'Total Employees: {len(employees_data)} | Total Salary: PKR {total_salary:,.2f} | Total Net: PKR {total_net:,.2f}', 0, 1)
    pdf.ln(5)
    
    # Table Header
    pdf.set_fill_color(41, 128, 185)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 9)
    
    # Adjust column widths for better fit
    col_widths = [40, 30, 30, 40, 25, 25, 25]
    headers = ['Employee', 'Designation', 'Bank', 'Account No', 'Salary', 'Deductions', 'Net Pay']
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C', True)
    pdf.ln()
    
    # Table Rows
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 8)
    
    for emp in employees_data:
        # Employee name (truncate if too long)
        pdf.cell(col_widths[0], 8, emp['name'][:18], 1, 0)
        # Designation
        pdf.cell(col_widths[1], 8, emp.get('designation', '')[:12], 1, 0)
        # Bank name
        pdf.cell(col_widths[2], 8, emp.get('bank_name', '')[:12], 1, 0)
        # Account number
        pdf.cell(col_widths[3], 8, str(emp.get('account_number', ''))[:15], 1, 0)
        # Salary
        pdf.cell(col_widths[4], 8, f"{emp['salary']:,.0f}", 1, 0, 'R')
        # Deductions
        deductions = emp.get('deductions', 0)
        pdf.cell(col_widths[5], 8, f"{deductions:,.0f}", 1, 0, 'R')
        # Net Pay
        net_salary = emp.get('net_salary', emp['salary'] - deductions)
        pdf.cell(col_widths[6], 8, f"{net_salary:,.0f}", 1, 1, 'R')
    
    # Total Row
    pdf.set_font('Arial', 'B', 9)
    pdf.cell(sum(col_widths[:4]), 8, 'TOTALS:', 1, 0, 'R')
    pdf.cell(col_widths[4], 8, f"{total_salary:,.0f}", 1, 0, 'R')
    pdf.cell(col_widths[5], 8, f"{total_deductions:,.0f}", 1, 0, 'R')
    pdf.cell(col_widths[6], 8, f"{total_net:,.0f}", 1, 1, 'R')
    
    pdf.ln(10)
    
    # Footer
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 8, f'Generated on: {datetime.now().strftime("%d-%b-%Y %H:%M")}', 0, 1, 'C')
    pdf.cell(0, 8, f'Prepared by: {settings["company_name"]} HR Department', 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- EXPENSE MANAGEMENT FUNCTIONS ---
def page_expense_management_enhanced():
    """Enhanced expense management with edit/delete functionality."""
    st.markdown('<div class="sub-header">💸 Expense Management</div>', unsafe_allow_html=True)
    
    # Initialize session states
    if "expense_view_mode" not in st.session_state:
        st.session_state.expense_view_mode = "add"
    if "selected_expense_id" not in st.session_state:
        st.session_state.selected_expense_id = None
    
    # Navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Add Expense", use_container_width=True):
            st.session_state.expense_view_mode = "add"
    with col2:
        if st.button("📋 View Expenses", use_container_width=True):
            st.session_state.expense_view_mode = "view"
    with col3:
        if st.button("📊 Expense Reports", use_container_width=True):
            st.session_state.expense_view_mode = "reports"
    
    st.divider()
    
    # Add New Expense
    if st.session_state.expense_view_mode == "add":
        st.markdown("### ➕ Add New Expense")
        
        with st.form("add_expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Expense Date", value=date.today())
                category = st.selectbox("Category", EXPENSE_CATEGORIES)
                amount = st.number_input("Amount (PKR)", min_value=0.01, step=10.0)
            
            with col2:
                description = st.text_area("Description", placeholder="Detailed description of the expense")
                # Employee selection (optional)
                employees = get_employees()
                if not employees.empty:
                    employee_options = ["N/A (General Expense)"] + employees['id'].tolist()
                    employee_display = ["N/A (General Expense)"] + employees['name'].tolist()
                    
                    selected_employee = st.selectbox(
                        "Link to Employee (Optional)",
                        options=employee_options,
                        format_func=lambda x: employee_display[employee_options.index(x)] if x in employee_options else "N/A"
                    )
                    employee_id = None if selected_employee == "N/A (General Expense)" else selected_employee
                else:
                    employee_id = None
                    st.info("No employees available")
            
            submitted = st.form_submit_button("💾 Add Expense", use_container_width=True)
            if submitted:
                if add_expense(expense_date, category, amount, description, employee_id):
                    st.session_state.expense_view_mode = "view"
                    st.rerun()

    # View and Manage Expenses
    elif st.session_state.expense_view_mode == "view":
        st.markdown("### 📋 Expense Records")
        
        # Date Range Filter
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start_date = st.date_input("Start Date", value=date.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", value=date.today())
        with col3:
            st.write("")
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        expenses_df = get_expenses(start_date, end_date)
        
        if not expenses_df.empty:
            # Display summary
            total_expenses = expenses_df['amount'].sum()
            st.metric("Total Expenses in Period", f"PKR {total_expenses:,.2f}")
            
            # Display expenses in editable format
            for idx, expense in expenses_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**Date:** {expense['expense_date']}")
                        st.write(f"**Category:** {expense['category']}")
                        st.write(f"**Amount:** PKR {expense['amount']:,.2f}")
                    
                    with col2:
                        st.write(f"**Employee:** {expense['employee_name']}")
                        st.write(f"**Description:** {expense['description'][:50]}{'...' if len(str(expense['description'])) > 50 else ''}")
                    
                    with col3:
                        if st.button("✏️ Edit", key=f"edit_{expense['id']}", use_container_width=True):
                            st.session_state.expense_view_mode = "edit"
                            st.session_state.selected_expense_id = expense['id']
                            st.rerun()
                    
                    with col4:
                        if st.button("🗑️ Delete", key=f"delete_{expense['id']}", use_container_width=True):
                            if delete_expense(expense['id']):
                                st.rerun()
                    
                    st.divider()
        else:
            st.info("💰 No expenses found for the selected period.")

    # Edit Expense
    elif st.session_state.expense_view_mode == "edit" and st.session_state.selected_expense_id:
        expense = get_expense_by_id(st.session_state.selected_expense_id)
        
        if expense:
            st.markdown(f"### ✏️ Edit Expense")
            
            with st.form("edit_expense_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    expense_date = st.date_input("Expense Date", 
                                               value=datetime.strptime(expense['expense_date'], '%Y-%m-%d').date())
                    category = st.selectbox("Category", EXPENSE_CATEGORIES, 
                                          index=EXPENSE_CATEGORIES.index(expense['category']) if expense['category'] in EXPENSE_CATEGORIES else 0)
                    amount = st.number_input("Amount (PKR)", value=float(expense['amount']), min_value=0.01, step=10.0)
                
                with col2:
                    description = st.text_area("Description", value=expense['description'])
                    # Employee selection
                    employees = get_employees()
                    if not employees.empty:
                        employee_options = ["N/A (General Expense)"] + employees['id'].tolist()
                        employee_display = ["N/A (General Expense)"] + employees['name'].tolist()
                        
                        current_employee = expense['employee_id'] if expense['employee_id'] else "N/A (General Expense)"
                        selected_employee = st.selectbox(
                            "Link to Employee",
                            options=employee_options,
                            index=employee_options.index(current_employee) if current_employee in employee_options else 0,
                            format_func=lambda x: employee_display[employee_options.index(x)] if x in employee_options else "N/A"
                        )
                        employee_id = None if selected_employee == "N/A (General Expense)" else selected_employee
                    else:
                        employee_id = None
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    update_btn = st.form_submit_button("💾 Update", use_container_width=True)
                with col2:
                    delete_btn = st.form_submit_button("🗑️ Delete", use_container_width=True, type="secondary")
                with col3:
                    cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if update_btn:
                    if update_expense(expense['id'], expense_date, category, amount, description, employee_id):
                        st.session_state.expense_view_mode = "view"
                        st.session_state.selected_expense_id = None
                        st.rerun()
                
                if delete_btn:
                    if delete_expense(expense['id']):
                        st.session_state.expense_view_mode = "view"
                        st.session_state.selected_expense_id = None
                        st.rerun()
                
                if cancel_btn:
                    st.session_state.expense_view_mode = "view"
                    st.session_state.selected_expense_id = None
                    st.rerun()

    # Expense Reports
    elif st.session_state.expense_view_mode == "reports":
        st.markdown("### 📊 Expense Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.selectbox("Report Type", 
                                     ["Category-wise Summary", "Monthly Trends", "Employee-wise Expenses"])
        
        with col2:
            report_month = st.selectbox("Select Month", 
                                      [datetime.now().strftime("%B %Y"),
                                       (datetime.now() - relativedelta(months=1)).strftime("%B %Y")])
        
        # Generate reports based on selection
        if report_type == "Category-wise Summary":
            expenses_df = get_expenses()
            if not expenses_df.empty:
                category_summary = expenses_df.groupby('category')['amount'].sum().reset_index()
                category_summary = category_summary.sort_values('amount', ascending=False)
                
                st.markdown("#### Category-wise Expense Summary")
                for _, row in category_summary.iterrows():
                    st.write(f"**{row['category']}:** PKR {row['amount']:,.2f}")
            else:
                st.info("No expense data available for reporting.")
        
        elif report_type == "Monthly Trends":
            st.info("Monthly trend analysis will be displayed here.")
            # Implement monthly trend analysis
        
        elif report_type == "Employee-wise Expenses":
            employees = get_employees()
            if not employees.empty:
                st.markdown("#### Employee-wise Expense Summary")
                for _, emp in employees.iterrows():
                    emp_expenses = get_expenses_for_employee(emp['id'], 
                                                           date.today().replace(day=1), 
                                                           date.today())
                    total_emp_expenses = emp_expenses['amount'].sum() if not emp_expenses.empty else 0
                    st.write(f"**{emp['name']}:** PKR {total_emp_expenses:,.2f}")

# --- ENHANCED EMPLOYEE MANAGEMENT ---
def page_employee_management_enhanced():
    """Enhanced employee management with fixed PDF generation."""
    st.markdown('<div class="sub-header">🧑‍💼 Employee Management</div>', unsafe_allow_html=True)
    
    # Initialize session states
    if "emp_view_mode" not in st.session_state:
        st.session_state.emp_view_mode = "list"
    if "selected_emp_id" not in st.session_state:
        st.session_state.selected_emp_id = None
    
    # Navigation
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("📋 Employee List", use_container_width=True):
            st.session_state.emp_view_mode = "list"
    with col2:
        if st.button("➕ Add Employee", use_container_width=True):
            st.session_state.emp_view_mode = "add"
    with col3:
        if st.button("💸 Transactions", use_container_width=True):
            st.session_state.emp_view_mode = "transactions"
    with col4:
        if st.button("✅ Approvals", use_container_width=True):
            st.session_state.emp_view_mode = "approvals"
    with col5:
        if st.button("💰 Salary Slips", use_container_width=True):
            st.session_state.emp_view_mode = "salary_slips"
    
    st.divider()
    
    # Employee List View
    if st.session_state.emp_view_mode == "list":
        st.markdown("### 📋 Employee List")
        
        # Search functionality
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("🔍 Search employees", placeholder="Search by name, designation, or department...")
        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        employees_df = get_employees()
        
        # Filter employees
        if search_query:
            filtered_employees = employees_df[
                employees_df['name'].str.contains(search_query, case=False, na=False) |
                employees_df['designation'].str.contains(search_query, case=False, na=False) |
                employees_df['department'].str.contains(search_query, case=False, na=False)
            ]
        else:
            filtered_employees = employees_df
        
        if filtered_employees.empty:
            st.info("👥 No employees found. Add your first employee!")
        else:
            # Display employees in cards
            for idx, employee in filtered_employees.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{employee['name']}**")
                        st.write(f"**Designation:** {employee.get('designation', 'N/A')}")
                        st.write(f"**Department:** {employee.get('department', 'N/A')}")
                        st.write(f"**Salary:** PKR {employee['salary']:,.2f}")
                    
                    with col2:
                        st.write(f"**Bank:** {employee.get('bank_name', 'N/A')}")
                        st.write(f"**Account:** {employee.get('account_number', 'N/A')}")
                        if employee.get('phone'):
                            st.write(f"**Phone:** {employee['phone']}")
                        if employee.get('email'):
                            st.write(f"**Email:** {employee['email']}")
                    
                    with col3:
                        if st.button("✏️ Edit", key=f"edit_{employee['id']}", use_container_width=True):
                            st.session_state.emp_view_mode = "edit"
                            st.session_state.selected_emp_id = employee['id']
                            st.rerun()
                    
                    with col4:
                        if st.button("📊 Ledger", key=f"ledger_{employee['id']}", use_container_width=True):
                            st.session_state.emp_view_mode = "ledger"
                            st.session_state.selected_emp_id = employee['id']
                            st.rerun()
                    
                    st.divider()

    # Add Employee View
    elif st.session_state.emp_view_mode == "add":
        st.markdown("### ➕ Add New Employee")
        
        with st.form("add_employee_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("👤 Full Name *", placeholder="Enter full name")
                designation = st.text_input("💼 Designation *", placeholder="Enter designation")
                salary = st.number_input("💰 Monthly Salary (PKR) *", min_value=0.0, step=1000.0, value=30000.0)
                phone = st.text_input("📞 Phone Number", placeholder="+92-300-1234567")
                email = st.text_input("📧 Email Address", placeholder="employee@company.com")
            
            with col2:
                bank_name = st.text_input("🏦 Bank Name", placeholder="e.g., HBL, UBL, etc.")
                account_title = st.text_input("📝 Account Title", placeholder="Account holder name")
                account_number = st.text_input("🔢 Account Number", placeholder="Bank account number")
                department = st.text_input("🏢 Department", placeholder="e.g., Sales, IT, HR")
            
            submitted = st.form_submit_button("➕ Add Employee", use_container_width=True)
            if submitted:
                if not name or not designation:
                    st.error("❌ Please fill in all required fields (Name and Designation)")
                else:
                    employee_id = add_employee(name, designation, bank_name, account_title, account_number, salary, phone, email, department)
                    if employee_id:
                        st.session_state.emp_view_mode = "list"
                        st.rerun()

    # Edit Employee View
    elif st.session_state.emp_view_mode == "edit" and st.session_state.selected_emp_id:
        employee = get_employee_by_id(st.session_state.selected_emp_id)
        
        if employee:
            st.markdown(f"### ✏️ Edit Employee: {employee['name']}")
            
            with st.form("edit_employee_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("👤 Full Name *", value=employee['name'])
                    designation = st.text_input("💼 Designation *", value=employee.get('designation', ''))
                    salary = st.number_input("💰 Monthly Salary (PKR) *", value=float(employee['salary']), min_value=0.0, step=1000.0)
                    phone = st.text_input("📞 Phone Number", value=employee.get('phone', ''))
                    email = st.text_input("📧 Email Address", value=employee.get('email', ''))
                
                with col2:
                    bank_name = st.text_input("🏦 Bank Name", value=employee.get('bank_name', ''))
                    account_title = st.text_input("📝 Account Title", value=employee.get('account_title', ''))
                    account_number = st.text_input("🔢 Account Number", value=employee.get('account_number', ''))
                    department = st.text_input("🏢 Department", value=employee.get('department', ''))
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    update_btn = st.form_submit_button("💾 Update", use_container_width=True)
                with col2:
                    delete_btn = st.form_submit_button("🗑️ Delete", use_container_width=True, type="secondary")
                with col3:
                    cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if update_btn:
                    if update_employee(st.session_state.selected_emp_id, name, designation, bank_name, account_title, account_number, salary, phone, email, department):
                        st.session_state.emp_view_mode = "list"
                        st.session_state.selected_emp_id = None
                        st.rerun()
                
                if delete_btn:
                    if delete_employee(st.session_state.selected_emp_id):
                        st.session_state.emp_view_mode = "list"
                        st.session_state.selected_emp_id = None
                        st.rerun()
                
                if cancel_btn:
                    st.session_state.emp_view_mode = "list"
                    st.session_state.selected_emp_id = None
                    st.rerun()

    # Employee Ledger View
    elif st.session_state.emp_view_mode == "ledger" and st.session_state.selected_emp_id:
        employee = get_employee_by_id(st.session_state.selected_emp_id)
        
        if employee:
            st.markdown(f"### 📊 Employee Ledger: {employee['name']}")
            
            # Date Range Selection
            col1, col2, col3 = st.columns(3)
            with col1:
                start_date = st.date_input("From Date", value=date.today().replace(day=1))
            with col2:
                end_date = st.date_input("To Date", value=date.today())
            with col3:
                st.write("")  # Spacer
                download_btn = st.button("📥 Download PDF Ledger", use_container_width=True)
            
            # Get data
            expenses_df = get_expenses_for_employee(employee['id'], start_date, end_date)
            employee_expenses_df = get_employee_expenses(employee['id'])
            
            # Display Summary
            total_deductions = expenses_df['amount'].sum() if not expenses_df.empty else 0
            total_claims = employee_expenses_df[employee_expenses_df['status'] == 'Approved']['amount'].sum() if not employee_expenses_df.empty else 0
            net_salary = employee['salary'] - total_deductions
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Base Salary", f"PKR {employee['salary']:,.2f}")
            col2.metric("Deductions", f"PKR {total_deductions:,.2f}")
            col3.metric("Approved Claims", f"PKR {total_claims:,.2f}")
            col4.metric("Net Payable", f"PKR {net_salary:,.2f}")
            
            # Employee Self-Service Section
            st.markdown("#### ➕ Add New Expense Claim")
            with st.form("add_employee_expense_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    exp_date = st.date_input("📅 Date", value=date.today())
                    category = st.selectbox("📂 Category", EMPLOYEE_EXPENSE_CATEGORIES)
                
                with col2:
                    amount = st.number_input("💰 Amount (PKR)", min_value=1.0, step=100.0)
                
                with col3:
                    description = st.text_area("📝 Description", placeholder="Describe the expense...", height=100)
                
                submitted = st.form_submit_button("✅ Submit Expense Claim", use_container_width=True)
                if submitted:
                    expense_id, success = add_employee_expense(
                        employee['id'], exp_date, category, amount, description
                    )
                    if success:
                        st.success("✅ Expense claim submitted for approval!")
                        st.rerun()
            
            # Display Expenses
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📋 Submitted Expenses")
                if not employee_expenses_df.empty:
                    for _, expense in employee_expenses_df.iterrows():
                        status_color = {
                            'Approved': '🟢',
                            'Rejected': '🔴', 
                            'Pending': '🟡'
                        }.get(expense['status'], '⚪')
                        
                        st.write(f"{status_color} **PKR {expense['amount']:,.2f}** - {expense['category']}")
                        st.write(f"   📅 {expense['expense_date']} | {expense['description']}")
                        st.write(f"   📊 Status: {expense['status']}")
                        st.divider()
                else:
                    st.info("No expense claims submitted yet.")
            
            with col2:
                st.markdown("#### 📊 System Deductions")
                if not expenses_df.empty:
                    for _, expense in expenses_df.iterrows():
                        st.write(f"🔴 **PKR {expense['amount']:,.2f}** - {expense['category']}")
                        st.write(f"   📅 {expense['expense_date']} | {expense['description']}")
                        st.divider()
                else:
                    st.info("No deductions in this period.")
            
            # PDF Download
            if download_btn:
                try:
                    pdf_data = create_employee_ledger_pdf(employee, start_date, end_date, expenses_df, employee_expenses_df)
                    st.download_button(
                        label="⬇️ Download PDF Ledger",
                        data=pdf_data,
                        file_name=f"Ledger_{employee['name']}_{start_date}_to_{end_date}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")

    # Approvals View
    elif st.session_state.emp_view_mode == "approvals":
        st.markdown("### ✅ Expense Approval Center")
        
        pending_expenses = get_all_pending_expenses()
        
        if pending_expenses.empty:
            st.success("🎉 All caught up! No pending approvals.")
        else:
            for _, expense in pending_expenses.iterrows():
                with st.container():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    
                    with col1:
                        st.write(f"**{expense['employee_name']}**")
                        st.write(f"**Category:** {expense['category']}")
                        st.write(f"**Amount:** PKR {expense['amount']:,.2f}")
                        st.write(f"**Date:** {expense['expense_date']}")
                        st.write(f"**Description:** {expense['description']}")
                    
                    with col2:
                        if st.button("✅ Approve", key=f"approve_{expense['id']}", use_container_width=True):
                            if approve_employee_expense(expense['id']):
                                st.success("✅ Expense approved!")
                                time.sleep(1)
                                st.rerun()
                    
                    with col3:
                        if st.button("❌ Reject", key=f"reject_{expense['id']}", use_container_width=True):
                            if reject_employee_expense(expense['id']):
                                st.error("❌ Expense rejected!")
                                time.sleep(1)
                                st.rerun()
                    
                    st.divider()

    # Transactions Management
    elif st.session_state.emp_view_mode == "transactions":
        st.markdown("### 💸 Transaction Management")
        
        # Add new transaction form
        st.markdown("#### ➕ Record New Transaction")
        with st.form("add_transaction_form"):
            employees = get_employees()
            
            if not employees.empty:
                col1, col2 = st.columns(2)
                with col1:
                    employee_id = st.selectbox("Select Employee", 
                                             options=employees['id'].tolist(),
                                             format_func=lambda x: employees[employees['id'] == x]['name'].iloc[0])
                    transaction_type = st.selectbox("Transaction Type", ["Deduction", "Payment", "Claim"])
                    amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0)
                with col2:
                    description = st.text_input("Description", placeholder="Brief description of transaction")
                    category = st.selectbox("Category", EXPENSE_CATEGORIES)
                    transaction_date = st.date_input("Date", value=date.today())
                
                submitted = st.form_submit_button("💾 Record Transaction", use_container_width=True)
                if submitted:
                    if description and amount > 0:
                        if add_expense(transaction_date, category, amount, description, employee_id):
                            st.success("✅ Transaction recorded successfully!")
                            st.rerun()
                    else:
                        st.error("❌ Please fill all required fields correctly")
            else:
                st.info("👥 No employees found. Please add employees first.")

    # Salary Slips View
    elif st.session_state.emp_view_mode == "salary_slips":
        st.markdown("### 💰 Salary Slips & Sheets")
        
        employees = get_employees()
        
        if employees.empty:
            st.info("👥 No employees found. Please add employees first.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📄 Individual Salary Slips")
                selected_employee = st.selectbox("Select Employee", 
                                               options=employees['id'].tolist(),
                                               format_func=lambda x: employees[employees['id'] == x]['name'].iloc[0],
                                               key="salary_emp_select")
                
                month_year = st.selectbox("Select Month", 
                                        options=[datetime.now().strftime("%B %Y"), 
                                                (datetime.now() - relativedelta(months=1)).strftime("%B %Y")],
                                        key="salary_month_select")
                
                if selected_employee:
                    employee = get_employee_by_id(selected_employee)
                    
                    if employee:
                        # Calculate deductions for the month
                        month_start = datetime.now().replace(day=1).date()
                        month_end = (month_start + relativedelta(months=1) - timedelta(days=1))
                        deductions_df = get_expenses_for_employee(selected_employee, month_start, month_end)
                        total_deductions = deductions_df['amount'].sum() if not deductions_df.empty else 0
                        net_salary = employee['salary'] - total_deductions
                        
                        st.metric("Basic Salary", f"PKR {employee['salary']:,.2f}")
                        st.metric("Total Deductions", f"PKR {total_deductions:,.2f}")
                        st.metric("Net Salary", f"PKR {net_salary:,.2f}")
                        
                        if st.button("📄 Generate Salary Slip", use_container_width=True, key="gen_slip"):
                            try:
                                pdf_data = create_salary_slip_pdf(employee, month_year, total_deductions, net_salary)
                                st.download_button(
                                    label="📥 Download Salary Slip",
                                    data=pdf_data,
                                    file_name=f"Salary_Slip_{employee['name']}_{month_year.replace(' ', '_')}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                            except Exception as e:
                                st.error(f"Error generating salary slip: {e}")
            
            with col2:
                st.markdown("#### 📊 Bulk Salary Sheet")
                bulk_month_year = st.selectbox("Select Month for Bulk Sheet", 
                                             options=[datetime.now().strftime("%B %Y"), 
                                                     (datetime.now() - relativedelta(months=1)).strftime("%B %Y")],
                                             key="bulk_month_select")
                
                # Prepare employee data for bulk sheet
                employees_data = []
                for _, emp in employees.iterrows():
                    month_start = datetime.now().replace(day=1).date()
                    month_end = (month_start + relativedelta(months=1) - timedelta(days=1))
                    deductions_df = get_expenses_for_employee(emp['id'], month_start, month_end)
                    total_deductions = deductions_df['amount'].sum() if not deductions_df.empty else 0
                    
                    employees_data.append({
                        'name': emp['name'],
                        'designation': emp.get('designation', ''),
                        'bank_name': emp.get('bank_name', ''),
                        'account_number': emp.get('account_number', ''),
                        'salary': emp['salary'],
                        'deductions': total_deductions,
                        'net_salary': emp['salary'] - total_deductions
                    })
                
                total_salary = sum(emp['salary'] for emp in employees_data)
                total_net = sum(emp['net_salary'] for emp in employees_data)
                
                st.metric("Total Employees", len(employees_data))
                st.metric("Total Salary", f"PKR {total_salary:,.2f}")
                st.metric("Total Net Payable", f"PKR {total_net:,.2f}")
                
                if st.button("📋 Generate Bulk Salary Sheet", use_container_width=True, key="gen_bulk"):
                    try:
                        pdf_data = create_bulk_salary_sheet_pdf(employees_data, bulk_month_year)
                        st.download_button(
                            label="📥 Download Salary Sheet",
                            data=pdf_data,
                            file_name=f"Salary_Sheet_{bulk_month_year.replace(' ', '_')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Error generating bulk salary sheet: {e}")

# --- MAIN APP ---
def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Nutrion Enterprise Management",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    init_db()
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard"
    
    # Sidebar Navigation
    st.sidebar.markdown("""
    <div style='background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); padding: 2rem; border-radius: 15px; color: white; text-align: center;'>
        <h2>Nutrion Enterprise</h2>
        <p>Business Management System</p>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    app_mode = st.sidebar.selectbox(
        "Navigation",
        ["🏠 Dashboard", "🧑‍💼 Employee Management", "💸 Expense Management", "📥 Data Import", "⚙️ Settings"],
        index=["🏠 Dashboard", "🧑‍💼 Employee Management", "💸 Expense Management", "📥 Data Import", "⚙️ Settings"].index(st.session_state.current_page)
    )

    # Update current page
    st.session_state.current_page = app_mode

    # Quick actions in sidebar
    st.sidebar.markdown("### ⚡ Quick Actions")
    if st.sidebar.button("➕ Add Employee", use_container_width=True, key="sidebar_add_emp"):
        st.session_state.current_page = "🧑‍💼 Employee Management"
        st.session_state.emp_view_mode = "add"
        st.rerun()
        
    if st.sidebar.button("💸 Add Expense", use_container_width=True, key="sidebar_add_exp"):
        st.session_state.current_page = "💸 Expense Management"
        st.rerun()
        
    if st.sidebar.button("💰 Salary Slips", use_container_width=True, key="sidebar_salary"):
        st.session_state.current_page = "🧑‍💼 Employee Management"
        st.session_state.emp_view_mode = "salary_slips"
        st.rerun()

    # System info in sidebar
    st.sidebar.markdown("---")
    employees_df = get_employees()
    total_employees = len(employees_df)
    
    today = date.today()
    start_of_month = today.replace(day=1)
    expenses_df = get_expenses(start_of_month, today)
    monthly_expenses = expenses_df['amount'].sum()
    
    pending_expenses = get_all_pending_expenses()
    pending_count = len(pending_expenses)
    
    st.sidebar.markdown(f"**System Overview:**")
    st.sidebar.markdown(f"👥 Employees: **{total_employees}**")
    st.sidebar.markdown(f"💰 Monthly Expenses: **PKR {monthly_expenses:,.2f}**")
    st.sidebar.markdown(f"✅ Pending Approvals: **{pending_count}**")

    # Footer in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style='text-align: center; color: #666;'>
        <p><strong>Need Help?</strong></p>
        <p>📞 +92-320-7429422</p>
        <p>📧 info@nutrion.com</p>
    </div>
    """, unsafe_allow_html=True)

    # Main header
    st.markdown('<div class="main-header">Nutrion Enterprise Management System</div>', unsafe_allow_html=True)

    # Render the selected page
    if st.session_state.current_page == "🏠 Dashboard":
        page_dashboard()
    elif st.session_state.current_page == "🧑‍💼 Employee Management":
        page_employee_management_enhanced()
    elif st.session_state.current_page == "💸 Expense Management":
        page_expense_management_enhanced()
    elif st.session_state.current_page == "📥 Data Import":
        page_data_import()
    else:  # Settings
        page_settings()

    # Render footer
    render_footer()

# --- DASHBOARD AND OTHER PAGES (keep existing implementations) ---
def page_dashboard():
    """Main dashboard page."""
    st.markdown('<div class="sub-header">🏠 Enterprise Dashboard</div>', unsafe_allow_html=True)
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    
    employees_df = get_employees()
    total_employees = len(employees_df)
    total_salary = employees_df['salary'].sum()
    
    today = date.today()
    start_of_month = today.replace(day=1)
    expenses_df = get_expenses(start_of_month, today)
    monthly_expenses = expenses_df['amount'].sum()
    
    pending_expenses = get_all_pending_expenses()
    pending_count = len(pending_expenses)
    
    with col1:
        st.markdown(f'<div class="metric-card">👥 Total Employees<br>{total_employees}</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card">💰 Monthly Payroll<br>PKR {total_salary:,.2f}</div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card">💸 This Month Expenses<br>PKR {monthly_expenses:,.2f}</div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card">✅ Pending Approvals<br>{pending_count}</div>', unsafe_allow_html=True)
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("➕ Add New Employee", use_container_width=True, key="quick_add_emp"):
            st.session_state.current_page = "🧑‍💼 Employee Management"
            st.session_state.emp_view_mode = "add"
            st.rerun()

    with col2:
        if st.button("💸 Record Transaction", use_container_width=True, key="quick_add_trans"):
            st.session_state.current_page = "🧑‍💼 Employee Management"
            st.session_state.emp_view_mode = "transactions"
            st.rerun()

    with col3:
        if st.button("💰 Add Expense", use_container_width=True, key="quick_add_exp"):
            st.session_state.current_page = "💸 Expense Management"
            st.rerun()

    with col4:
        if st.button("✅ Approve Expenses", use_container_width=True, key="quick_approve"):
            st.session_state.current_page = "🧑‍💼 Employee Management"
            st.session_state.emp_view_mode = "approvals"
            st.rerun()

def page_data_import():
    """Data import page with templates."""
    st.markdown('<div class="sub-header">📥 Data Import Center</div>', unsafe_allow_html=True)
    st.info("Data import functionality - Implementation details would go here")

def page_settings():
    """System settings page."""
    st.markdown('<div class="sub-header">⚙️ System Settings</div>', unsafe_allow_html=True)
    st.info("System settings functionality - Implementation details would go here")

def render_footer():
    """Render the footer."""
    st.markdown("---")
    st.markdown("""
    <div style='background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%); color: white; padding: 2rem; border-radius: 15px; text-align: center;'>
        <h3>Nutrion Enterprise Management System</h3>
        <p>Advanced Business Management Solutions</p>
        <p>For any query please feel free to contact: <strong>+92-320-7429422</strong></p>
        <p>📧 Email: info@nutrion.com</p>
        <p style="margin-top: 1rem; font-size: 0.9rem; opacity: 0.8;">
            &copy; 2024 Nutrion Enterprise. All rights reserved.
        </p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
