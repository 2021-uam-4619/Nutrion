# Streamlit Enterprise Management System
import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
import io
import time
import base64

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

DB_NAME = "enterprise_data.db"

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
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        designation TEXT,
        bank_name TEXT,
        account_title TEXT,
        account_number TEXT,
        salary REAL DEFAULT 0,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Expense Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        expense_date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        employee_id INTEGER,
        added_by TEXT DEFAULT 'System',
        status TEXT DEFAULT 'Approved',
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE SET NULL
    );
    """)
    
    # Employee Self-Service Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER NOT NULL,
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
    
    conn.commit()
    conn.close()

# --- EMPLOYEE CRUD FUNCTIONS ---
def add_employee(name, designation, bank_name, account_title, account_number, salary):
    """Adds a new employee to the database."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO employees (name, designation, bank_name, account_title, account_number, salary) VALUES (?, ?, ?, ?, ?, ?)",
            (name, designation, bank_name, account_title, account_number, salary)
        )
        employee_id = cursor.lastrowid
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
               created_date 
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
    return employee

def update_employee(emp_id, name, designation, bank_name, account_title, account_number, salary):
    """Updates an existing employee's details."""
    try:
        conn = get_db_connection()
        conn.execute(
            """UPDATE employees SET 
               name = ?, designation = ?, bank_name = ?, 
               account_title = ?, account_number = ?, salary = ? 
               WHERE id = ?""",
            (name, designation, bank_name, account_title, account_number, salary, emp_id)
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
def add_employee_expense(employee_id, expense_date, category, amount, description, receipt_uploaded=False, receipt_path=None):
    """Adds a new expense submitted by employee."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO employee_expenses 
               (employee_id, expense_date, category, amount, description, receipt_uploaded, receipt_path) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (employee_id, expense_date.strftime('%Y-%m-%d'), category, amount, description, receipt_uploaded, receipt_path)
        )
        expense_id = cursor.lastrowid
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

def approve_employee_expense(expense_id, approved_by):
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

def reject_employee_expense(expense_id, approved_by):
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
def add_expense(expense_date, category, amount, description, employee_id):
    """Adds a new expense record."""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO expenses (expense_date, category, amount, description, employee_id) VALUES (?, ?, ?, ?, ?)",
            (expense_date.strftime('%Y-%m-%d'), category, amount, description, employee_id)
        )
        conn.commit()
        conn.close()
        st.success("✅ Successfully added expense.")
        return True
    except Exception as e:
        st.error(f"❌ Error adding expense: {e}")
        return False

def get_expenses(start_date, end_date):
    """Fetches all expenses within a date range as a DataFrame."""
    conn = get_db_connection()
    query = """
    SELECT e.id, e.expense_date, e.category, e.amount, e.description, 
           IFNULL(emp.name, 'N/A') as employee_name, e.status
    FROM expenses e
    LEFT JOIN employees emp ON e.employee_id = emp.id
    WHERE e.expense_date BETWEEN ? AND ?
    ORDER BY e.expense_date DESC
    """
    df = pd.read_sql_query(query, conn, params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    conn.close()
    return df

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
        ['Salary:', f"PKR {employee['salary']:,.2f}"],
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
        ['Base Salary:', f"PKR {employee['salary']:,.2f}"],
        ['Deductions:', f"PKR {total_expenses:,.2f}"],
        ['Approved Claims:', f"PKR {total_employee_expenses:,.2f}"],
        ['Net Payable:', f"PKR {net_salary:,.2f}"]
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

# --- TEMPLATE GENERATION FUNCTIONS ---
def get_employee_import_template():
    """Generates employee import template."""
    template_data = {
        'name': ['John Doe', 'Jane Smith'],
        'designation': ['Manager', 'Accountant'],
        'bank_name': ['HBL', 'UBL'],
        'account_title': ['John Doe', 'Jane Smith'],
        'account_number': ['123456789', '987654321'],
        'salary': [50000, 40000]
    }
    df = pd.DataFrame(template_data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    return output.getvalue()

def get_expense_import_template():
    """Generates expense import template."""
    template_data = {
        'expense_date': ['2024-01-15', '2024-01-20'],
        'category': ['Office Rent', 'Transportation'],
        'amount': [25000, 5000],
        'description': ['Monthly office rent', 'Client meeting travel'],
        'employee_id': [1, 2]  # Reference to existing employee IDs
    }
    df = pd.DataFrame(template_data)
    output = io.BytesIO()
    df.to_excel(output, index=False, engine='openpyxl')
    return output.getvalue()

# --- UI PAGES ---
def page_dashboard():
    """Main dashboard page."""
    st.title("🏠 Enterprise Dashboard")
    
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
        st.metric("Total Employees", total_employees)
    with col2:
        st.metric("Monthly Payroll", f"PKR {total_salary:,.2f}")
    with col3:
        st.metric("This Month Expenses", f"PKR {monthly_expenses:,.2f}")
    with col4:
        st.metric("Pending Approvals", pending_count)
    
    # Recent Activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Employees")
        if not employees_df.empty:
            recent_employees = employees_df.head(5)[['name', 'designation', 'salary']]
            st.dataframe(recent_employees, use_container_width=True)
        else:
            st.info("No employees found")
    
    with col2:
        st.subheader("Pending Approvals")
        if not pending_expenses.empty:
            pending_display = pending_expenses.head(5)[['employee_name', 'category', 'amount', 'expense_date']]
            st.dataframe(pending_display, use_container_width=True)
        else:
            st.info("No pending approvals")

def page_employee_management():
    """Employee management with self-service features."""
    st.title("🧑‍💼 Employee Management")
    
    # Initialize session states
    if "emp_edit_mode" not in st.session_state:
        st.session_state.emp_edit_mode = False
    if "selected_emp_id" not in st.session_state:
        st.session_state.selected_emp_id = None
    if "emp_view_mode" not in st.session_state:
        st.session_state.emp_view_mode = "list"
    
    # Navigation
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📋 Employee List", use_container_width=True):
            st.session_state.emp_view_mode = "list"
    with col2:
        if st.button("➕ Add Employee", use_container_width=True):
            st.session_state.emp_view_mode = "add"
    with col3:
        if st.button("✅ Approvals", use_container_width=True):
            st.session_state.emp_view_mode = "approvals"
    
    st.divider()
    
    # Employee List View
    if st.session_state.emp_view_mode == "list":
        employees_df = get_employees()
        
        if employees_df.empty:
            st.info("👥 No employees found. Add your first employee!")
            return
        
        # Search and Filter
        col1, col2 = st.columns([2, 1])
        with col1:
            search_term = st.text_input("🔍 Search employees", placeholder="Search by name or designation...")
        with col2:
            items_per_page = st.selectbox("Items per page", [5, 10, 20], index=1)
        
        # Filter employees
        if search_term:
            filtered_employees = employees_df[
                employees_df['name'].str.contains(search_term, case=False, na=False) |
                employees_df['designation'].str.contains(search_term, case=False, na=False)
            ]
        else:
            filtered_employees = employees_df
        
        # Pagination
        total_pages = max(1, (len(filtered_employees) + items_per_page - 1) // items_per_page)
        page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        start_idx = (page_number - 1) * items_per_page
        end_idx = start_idx + items_per_page
        
        # Display employees
        for idx, employee in filtered_employees.iloc[start_idx:end_idx].iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                
                with col1:
                    st.subheader(employee['name'])
                    st.write(f"**Designation:** {employee.get('designation', 'N/A')}")
                    st.write(f"**Salary:** PKR {employee['salary']:,.2f}")
                
                with col2:
                    st.write(f"**Bank:** {employee.get('bank_name', 'N/A')}")
                    st.write(f"**Account:** {employee.get('account_number', 'N/A')}")
                    st.write(f"**Joined:** {employee.get('created_date', 'N/A')[:10]}")
                
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{employee['id']}", use_container_width=True):
                        st.session_state.emp_edit_mode = True
                        st.session_state.selected_emp_id = employee['id']
                        st.session_state.emp_view_mode = "edit"
                        st.rerun()
                
                with col4:
                    if st.button("📊 Ledger", key=f"ledger_{employee['id']}", use_container_width=True):
                        st.session_state.selected_emp_id = employee['id']
                        st.session_state.emp_view_mode = "ledger"
                        st.rerun()
                
                st.divider()
    
    # Add Employee View
    elif st.session_state.emp_view_mode == "add":
        st.header("Add New Employee")
        
        with st.form("add_employee_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("👤 Full Name *", placeholder="Enter full name")
                designation = st.text_input("💼 Designation *", placeholder="Enter designation")
                salary = st.number_input("💰 Monthly Salary (PKR) *", min_value=0.0, step=1000.0, value=30000.0)
            
            with col2:
                bank_name = st.text_input("🏦 Bank Name", placeholder="e.g., HBL, UBL, etc.")
                account_title = st.text_input("📝 Account Title", placeholder="Account holder name")
                account_number = st.text_input("🔢 Account Number", placeholder="Bank account number")
            
            submitted = st.form_submit_button("➕ Add Employee", use_container_width=True)
            if submitted:
                if not name or not designation:
                    st.error("❌ Please fill in all required fields (Name and Designation)")
                else:
                    employee_id = add_employee(name, designation, bank_name, account_title, account_number, salary)
                    if employee_id:
                        st.session_state.emp_view_mode = "list"
                        st.rerun()
    
    # Edit Employee View
    elif st.session_state.emp_view_mode == "edit" and st.session_state.selected_emp_id:
        employee = get_employee_by_id(st.session_state.selected_emp_id)
        
        if employee:
            st.header(f"Edit Employee: {employee['name']}")
            
            with st.form("edit_employee_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("👤 Full Name *", value=employee['name'])
                    designation = st.text_input("💼 Designation *", value=employee.get('designation', ''))
                    salary = st.number_input("💰 Monthly Salary (PKR) *", value=float(employee['salary']), min_value=0.0, step=1000.0)
                
                with col2:
                    bank_name = st.text_input("🏦 Bank Name", value=employee.get('bank_name', ''))
                    account_title = st.text_input("📝 Account Title", value=employee.get('account_title', ''))
                    account_number = st.text_input("🔢 Account Number", value=employee.get('account_number', ''))
                
                col1, col2, col3 = st.columns([1, 1, 1])
                with col1:
                    update_btn = st.form_submit_button("💾 Update", use_container_width=True)
                with col2:
                    delete_btn = st.form_submit_button("🗑️ Delete", use_container_width=True, type="secondary")
                with col3:
                    cancel_btn = st.form_submit_button("❌ Cancel", use_container_width=True)
                
                if update_btn:
                    if update_employee(st.session_state.selected_emp_id, name, designation, bank_name, account_title, account_number, salary):
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
            st.header(f"Employee Ledger: {employee['name']}")
            
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
            st.subheader("➕ Add New Expense Claim")
            with st.form("add_employee_expense_form", clear_on_submit=True):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    exp_date = st.date_input("📅 Date", value=date.today())
                    category = st.selectbox("📂 Category", EMPLOYEE_EXPENSE_CATEGORIES)
                
                with col2:
                    amount = st.number_input("💰 Amount (PKR)", min_value=1.0, step=100.0)
                    # receipt = st.file_uploader("📎 Receipt (Optional)", type=['pdf', 'jpg', 'png'])
                
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
                st.subheader("📋 Submitted Expenses")
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
                st.subheader("📊 System Deductions")
                if not expenses_df.empty:
                    for _, expense in expenses_df.iterrows():
                        st.write(f"🔴 **PKR {expense['amount']:,.2f}** - {expense['category']}")
                        st.write(f"   📅 {expense['expense_date']} | {expense['description']}")
                        st.divider()
                else:
                    st.info("No deductions in this period.")
            
            # PDF Download
            if download_btn:
                pdf_data = create_employee_ledger_pdf(employee, start_date, end_date, expenses_df, employee_expenses_df)
                st.download_button(
                    label="⬇️ Download PDF Ledger",
                    data=pdf_data,
                    file_name=f"Ledger_{employee['name']}_{start_date}_to_{end_date}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    # Approvals View
    elif st.session_state.emp_view_mode == "approvals":
        st.header("✅ Expense Approval Center")
        
        pending_expenses = get_all_pending_expenses()
        
        if pending_expenses.empty:
            st.success("🎉 All caught up! No pending approvals.")
            return
        
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
                        if approve_employee_expense(expense['id'], "Admin"):
                            st.success("✅ Expense approved!")
                            time.sleep(1)
                            st.rerun()
                
                with col3:
                    if st.button("❌ Reject", key=f"reject_{expense['id']}", use_container_width=True):
                        if reject_employee_expense(expense['id'], "Admin"):
                            st.error("❌ Expense rejected!")
                            time.sleep(1)
                            st.rerun()
                
                st.divider()

def page_data_import():
    """Data import page with templates."""
    st.title("📥 Data Import Center")
    
    tab1, tab2, tab3 = st.tabs(["📋 Employee Import", "💸 Expense Import", "📚 Instructions"])
    
    with tab1:
        st.header("Import Employees")
        
        # Download Template
        st.subheader("1. Download Template")
        st.info("Download the template file and fill in your employee data.")
        
        template_data = get_employee_import_template()
        st.download_button(
            label="📥 Download Employee Template (Excel)",
            data=template_data,
            file_name="employee_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # Upload and Import
        st.subheader("2. Upload Filled Template")
        uploaded_file = st.file_uploader("Choose Excel file", type=["xlsx", "xls"], key="emp_import")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.success("✅ File loaded successfully!")
                
                # Display preview
                st.subheader("Data Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                # Validation
                required_cols = ['name', 'designation', 'salary']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    if st.button("🚀 Import Employees", use_container_width=True):
                        with st.spinner("Importing employees..."):
                            conn = get_db_connection()
                            success_count = 0
                            
                            for _, row in df.iterrows():
                                try:
                                    conn.execute(
                                        "INSERT INTO employees (name, designation, bank_name, account_title, account_number, salary) VALUES (?, ?, ?, ?, ?, ?)",
                                        (row['name'], row.get('designation'), row.get('bank_name'), 
                                         row.get('account_title'), row.get('account_number'), row['salary'])
                                    )
                                    success_count += 1
                                except Exception as e:
                                    st.warning(f"Failed to import {row.get('name', 'Unknown')}: {str(e)}")
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Successfully imported {success_count} out of {len(df)} employees!")
                            st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
    
    with tab2:
        st.header("Import Expenses")
        
        # Download Template
        st.subheader("1. Download Template")
        st.info("Download the template file and fill in your expense data.")
        
        template_data = get_expense_import_template()
        st.download_button(
            label="📥 Download Expense Template (Excel)",
            data=template_data,
            file_name="expense_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        # Upload and Import
        st.subheader("2. Upload Filled Template")
        uploaded_file = st.file_uploader("Choose Excel file", type=["xlsx", "xls"], key="exp_import")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.success("✅ File loaded successfully!")
                
                # Display preview
                st.subheader("Data Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                # Validation
                required_cols = ['expense_date', 'category', 'amount']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    if st.button("🚀 Import Expenses", use_container_width=True):
                        with st.spinner("Importing expenses..."):
                            conn = get_db_connection()
                            success_count = 0
                            
                            for _, row in df.iterrows():
                                try:
                                    # Convert employee_id to None if NaN
                                    employee_id = row.get('employee_id')
                                    if pd.isna(employee_id):
                                        employee_id = None
                                    
                                    conn.execute(
                                        "INSERT INTO expenses (expense_date, category, amount, description, employee_id) VALUES (?, ?, ?, ?, ?)",
                                        (row['expense_date'], row['category'], row['amount'], 
                                         row.get('description'), employee_id)
                                    )
                                    success_count += 1
                                except Exception as e:
                                    st.warning(f"Failed to import expense: {str(e)}")
                            
                            conn.commit()
                            conn.close()
                            
                            st.success(f"✅ Successfully imported {success_count} out of {len(df)} expenses!")
                            st.balloons()
                
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
    
    with tab3:
        st.header("📚 Import Instructions")
        
        st.markdown("""
        ### Employee Import Guidelines:
        
        **Required Fields:**
        - `name`: Employee full name (Text)
        - `designation`: Job title (Text)  
        - `salary`: Monthly salary (Number)
        
        **Optional Fields:**
        - `bank_name`: Bank name (Text)
        - `account_title`: Account holder name (Text)
        - `account_number`: Bank account number (Text)
        
        ### Expense Import Guidelines:
        
        **Required Fields:**
        - `expense_date`: Date in YYYY-MM-DD format
        - `category`: Expense category from predefined list
        - `amount`: Expense amount (Number)
        
        **Optional Fields:**
        - `description`: Expense description (Text)
        - `employee_id`: Link to employee ID (Number)
        
        ### Tips:
        - Keep Excel file under 5MB
        - Ensure date formats are correct
        - Employee IDs must exist in the system
        - Categories should match predefined options
        """)

# --- MAIN APP ---
def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(
        page_title="Nutrion Enterprise Management",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sidebar .sidebar-content {
        background-color: #f0f2f6;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_db()
    
    # Sidebar Navigation
    st.sidebar.title("🏢 Nutrion Enterprise")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Navigation",
        ["🏠 Dashboard", "🧑‍💼 Employee Management", "📥 Data Import"],
        index=0
    )
    
    st.sidebar.markdown("---")
    st.sidebar.info("""
    **Quick Actions:**
    - Add employees with bank details
    - Employees can submit expenses
    - Download PDF ledgers
    - Bulk import data
    """)
    
    # Page routing
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "🧑‍💼 Employee Management":
        page_employee_management()
    elif page == "📥 Data Import":
        page_data_import()

if __name__ == "__main__":
    main()
