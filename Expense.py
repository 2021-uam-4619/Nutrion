import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import sqlite3
import json
from fpdf import FPDF
import io
import base64
import tempfile
import os

# Page configuration
st.set_page_config(
    page_title="Nutrion Management System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #A23B72;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
def init_db():
    conn = sqlite3.connect('nutrion_management.db')
    c = conn.cursor()
    
    # Employees table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            name TEXT NOT NULL,
            designation TEXT,
            department TEXT,
            account_no TEXT,
            account_title TEXT,
            bank_name TEXT,
            basic_salary REAL,
            allowances REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            join_date DATE,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Expense categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Company expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date DATE,
            category_id INTEGER,
            amount REAL,
            description TEXT,
            paid_to TEXT,
            payment_method TEXT,
            reference_no TEXT,
            employee_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    # Employee ledger table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            transaction_date DATE,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            balance REAL,
            reference_type TEXT,
            reference_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    # Salary records table
    c.execute('''
        CREATE TABLE IF NOT EXISTS salary_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            salary_month DATE,
            basic_salary REAL,
            allowances REAL,
            deductions REAL,
            net_salary REAL,
            payment_date DATE,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    # Insert default expense categories
    default_categories = [
        ('Office Supplies', 'Stationery and office materials'),
        ('Utilities', 'Electricity, water, internet bills'),
        ('Travel', 'Business travel expenses'),
        ('Equipment', 'Office equipment and maintenance'),
        ('Marketing', 'Advertising and promotional expenses'),
        ('Professional Fees', 'Consultancy and professional services'),
        ('Rent', 'Office rent and maintenance'),
        ('Others', 'Miscellaneous expenses')
    ]
    
    c.executemany('''
        INSERT OR IGNORE INTO expense_categories (category_name, description)
        VALUES (?, ?)
    ''', default_categories)
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Database connection helper
def get_db_connection():
    return sqlite3.connect('nutrion_management.db')

# PDF Generation Class
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Nutrion Management System', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.cell(0, 10, 'Professional Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 8, body)
        self.ln()

# Utility functions
def create_download_link(val, filename):
    b64 = base64.b64encode(val)
    return f'<a href="data:application/octet-stream;base64,{b64.decode()}" download="{filename}.pdf">Download PDF</a>'

def format_currency(amount):
    return f"₹{amount:,.2f}"

# Main application
def main():
    st.markdown('<div class="main-header">🏢 Nutrion Management System</div>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose Module", [
        "Dashboard",
        "Employee Management",
        "Salary Management",
        "Expense Management",
        "Reports & Analytics",
        "Data Import/Export"
    ])
    
    if app_mode == "Dashboard":
        show_dashboard()
    elif app_mode == "Employee Management":
        show_employee_management()
    elif app_mode == "Salary Management":
        show_salary_management()
    elif app_mode == "Expense Management":
        show_expense_management()
    elif app_mode == "Reports & Analytics":
        show_reports_analytics()
    elif app_mode == "Data Import/Export":
        show_data_import_export()

# Dashboard
def show_dashboard():
    st.markdown('<div class="section-header">📊 Dashboard</div>', unsafe_allow_html=True)
    
    conn = get_db_connection()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Total Employees
    total_employees = conn.execute('SELECT COUNT(*) FROM employees WHERE status = "Active"').fetchone()[0]
    col1.metric("Total Employees", total_employees)
    
    # Total Monthly Salary
    total_salary = conn.execute('SELECT SUM(basic_salary + allowances - deductions) FROM employees WHERE status = "Active"').fetchone()[0] or 0
    col2.metric("Monthly Salary Budget", format_currency(total_salary))
    
    # Current Month Expenses
    current_month = datetime.now().strftime('%Y-%m')
    monthly_expenses = conn.execute('''
        SELECT SUM(amount) FROM company_expenses 
        WHERE strftime("%Y-%m", expense_date) = ?
    ''', (current_month,)).fetchone()[0] or 0
    col3.metric("Current Month Expenses", format_currency(monthly_expenses))
    
    # Pending Salary Payments
    pending_salary = conn.execute('''
        SELECT SUM(net_salary) FROM salary_records 
        WHERE status = "Pending" AND strftime("%Y-%m", salary_month) = ?
    ''', (current_month,)).fetchone()[0] or 0
    col4.metric("Pending Salary", format_currency(pending_salary))
    
    conn.close()
    
    # Recent activities and charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Recent Expenses by Category")
        conn = get_db_connection()
        expense_data = pd.read_sql('''
            SELECT ec.category_name, SUM(ce.amount) as total_amount
            FROM company_expenses ce
            JOIN expense_categories ec ON ce.category_id = ec.id
            WHERE strftime("%Y-%m", ce.expense_date) = ?
            GROUP BY ec.category_name
        ''', conn, params=(current_month,))
        conn.close()
        
        if not expense_data.empty:
            st.bar_chart(expense_data.set_index('category_name'))
        else:
            st.info("No expense data available for current month")
    
    with col2:
        st.subheader("Department-wise Employee Distribution")
        conn = get_db_connection()
        dept_data = pd.read_sql('''
            SELECT department, COUNT(*) as count 
            FROM employees 
            WHERE status = "Active" 
            GROUP BY department
        ''', conn)
        conn.close()
        
        if not dept_data.empty:
            st.bar_chart(dept_data.set_index('department'))
        else:
            st.info("No employee data available")

# Employee Management
def show_employee_management():
    st.markdown('<div class="section-header">👥 Employee Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add Employee", "View/Edit Employees", "Employee Ledger", "Search & Filter"])
    
    with tab1:
        st.subheader("Add New Employee")
        
        with st.form("add_employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                employee_id = st.text_input("Employee ID*")
                name = st.text_input("Full Name*")
                designation = st.text_input("Designation*")
                department = st.selectbox("Department", ["HR", "Finance", "IT", "Sales", "Marketing", "Operations", "Admin"])
                join_date = st.date_input("Join Date", date.today())
            
            with col2:
                account_no = st.text_input("Account Number*")
                account_title = st.text_input("Account Title*")
                bank_name = st.text_input("Bank Name*")
                basic_salary = st.number_input("Basic Salary*", min_value=0.0, step=1000.0)
                allowances = st.number_input("Allowances", min_value=0.0, step=500.0)
                deductions = st.number_input("Deductions", min_value=0.0, step=500.0)
            
            submitted = st.form_submit_button("Add Employee")
            
            if submitted:
                if not all([employee_id, name, designation, account_no, account_title, bank_name]):
                    st.error("Please fill all required fields (*)")
                else:
                    conn = get_db_connection()
                    try:
                        conn.execute('''
                            INSERT INTO employees 
                            (employee_id, name, designation, department, account_no, account_title, bank_name, basic_salary, allowances, deductions, join_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (employee_id, name, designation, department, account_no, account_title, bank_name, basic_salary, allowances, deductions, join_date))
                        conn.commit()
                        st.success("Employee added successfully!")
                    except sqlite3.IntegrityError:
                        st.error("Employee ID already exists!")
                    finally:
                        conn.close()
    
    with tab2:
        st.subheader("Employee Records")
        
        conn = get_db_connection()
        employees = pd.read_sql('SELECT * FROM employees ORDER BY created_at DESC', conn)
        conn.close()
        
        if not employees.empty:
            for _, emp in employees.iterrows():
                with st.expander(f"{emp['name']} - {emp['designation']} ({emp['employee_id']})"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write(f"**Department:** {emp['department']}")
                        st.write(f"**Join Date:** {emp['join_date']}")
                        st.write(f"**Status:** {emp['status']}")
                    
                    with col2:
                        st.write(f"**Bank:** {emp['bank_name']}")
                        st.write(f"**Account No:** {emp['account_no']}")
                        st.write(f"**Account Title:** {emp['account_title']}")
                    
                    with col3:
                        st.write(f"**Basic Salary:** {format_currency(emp['basic_salary'])}")
                        st.write(f"**Allowances:** {format_currency(emp['allowances'])}")
                        st.write(f"**Deductions:** {format_currency(emp['deductions'])}")
                        st.write(f"**Net Salary:** {format_currency(emp['basic_salary'] + emp['allowances'] - emp['deductions'])}")
                    
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        if st.button("Edit", key=f"edit_{emp['id']}"):
                            st.session_state[f'edit_employee_{emp["id"]}'] = True
                    
                    with col_delete:
                        if st.button("Delete", key=f"delete_{emp['id']}"):
                            conn = get_db_connection()
                            conn.execute('DELETE FROM employees WHERE id = ?', (emp['id'],))
                            conn.commit()
                            conn.close()
                            st.success("Employee deleted successfully!")
                            st.rerun()
                    
                    if st.session_state.get(f'edit_employee_{emp["id"]}', False):
                        edit_employee_form(emp)
        else:
            st.info("No employees found. Add some employees to get started.")
    
    with tab3:
        st.subheader("Employee Ledger")
        
        conn = get_db_connection()
        employees = pd.read_sql('SELECT id, employee_id, name FROM employees WHERE status = "Active"', conn)
        conn.close()
        
        if not employees.empty:
            employee_options = {f"{row['name']} ({row['employee_id']})": row['id'] for _, row in employees.iterrows()}
            selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
            
            if selected_employee:
                employee_id = employee_options[selected_employee]
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input("Start Date", date.today().replace(day=1))
                with col2:
                    end_date = st.date_input("End Date", date.today())
                
                if st.button("Generate Ledger Report"):
                    generate_employee_ledger(employee_id, start_date, end_date)
        else:
            st.info("No active employees found.")

    with tab4:
        st.subheader("Search & Filter Employees")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            search_name = st.text_input("Search by Name")
        with col2:
            search_department = st.selectbox("Filter by Department", ["All"] + ["HR", "Finance", "IT", "Sales", "Marketing", "Operations", "Admin"])
        with col3:
            search_status = st.selectbox("Filter by Status", ["All", "Active", "Inactive"])
        
        conn = get_db_connection()
        query = "SELECT * FROM employees WHERE 1=1"
        params = []
        
        if search_name:
            query += " AND name LIKE ?"
            params.append(f"%{search_name}%")
        
        if search_department != "All":
            query += " AND department = ?"
            params.append(search_department)
        
        if search_status != "All":
            query += " AND status = ?"
            params.append(search_status)
        
        query += " ORDER BY name"
        
        filtered_employees = pd.read_sql(query, conn, params=params)
        conn.close()
        
        st.dataframe(filtered_employees, use_container_width=True)

def edit_employee_form(employee):
    st.subheader(f"Edit Employee: {employee['name']}")
    
    with st.form(f"edit_employee_{employee['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name*", value=employee['name'])
            designation = st.text_input("Designation*", value=employee['designation'])
            department = st.selectbox("Department", ["HR", "Finance", "IT", "Sales", "Marketing", "Operations", "Admin"], 
                                    index=["HR", "Finance", "IT", "Sales", "Marketing", "Operations", "Admin"].index(employee['department']))
            status = st.selectbox("Status", ["Active", "Inactive"], index=0 if employee['status'] == "Active" else 1)
        
        with col2:
            account_no = st.text_input("Account Number*", value=employee['account_no'])
            account_title = st.text_input("Account Title*", value=employee['account_title'])
            bank_name = st.text_input("Bank Name*", value=employee['bank_name'])
            basic_salary = st.number_input("Basic Salary*", value=float(employee['basic_salary']), min_value=0.0, step=1000.0)
            allowances = st.number_input("Allowances", value=float(employee['allowances']), min_value=0.0, step=500.0)
            deductions = st.number_input("Deductions", value=float(employee['deductions']), min_value=0.0, step=500.0)
        
        submitted = st.form_submit_button("Update Employee")
        
        if submitted:
            if not all([name, designation, account_no, account_title, bank_name]):
                st.error("Please fill all required fields (*)")
            else:
                conn = get_db_connection()
                conn.execute('''
                    UPDATE employees 
                    SET name=?, designation=?, department=?, account_no=?, account_title=?, bank_name=?, 
                    basic_salary=?, allowances=?, deductions=?, status=?
                    WHERE id=?
                ''', (name, designation, department, account_no, account_title, bank_name, basic_salary, allowances, deductions, status, employee['id']))
                conn.commit()
                conn.close()
                
                st.session_state[f'edit_employee_{employee["id"]}'] = False
                st.success("Employee updated successfully!")
                st.rerun()

def generate_employee_ledger(employee_id, start_date, end_date):
    conn = get_db_connection()
    
    # Get employee details
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
    
    # Get ledger entries
    ledger_entries = pd.read_sql('''
        SELECT * FROM employee_ledger 
        WHERE employee_id = ? AND transaction_date BETWEEN ? AND ?
        ORDER BY transaction_date, created_at
    ''', conn, params=(employee_id, start_date, end_date))
    
    conn.close()
    
    if not ledger_entries.empty:
        # Generate PDF
        pdf = PDFReport()
        pdf.add_page()
        
        # Header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Employee Ledger Report', 0, 1, 'C')
        pdf.ln(5)
        
        # Employee Details
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, f"Employee: {employee['name']}", 0, 1)
        pdf.cell(0, 8, f"Employee ID: {employee['employee_id']}", 0, 1)
        pdf.cell(0, 8, f"Designation: {employee['designation']}", 0, 1)
        pdf.cell(0, 8, f"Period: {start_date} to {end_date}", 0, 1)
        pdf.ln(10)
        
        # Ledger Table Header
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(30, 8, 'Date', 1, 0, 'C', True)
        pdf.cell(70, 8, 'Description', 1, 0, 'C', True)
        pdf.cell(25, 8, 'Debit', 1, 0, 'C', True)
        pdf.cell(25, 8, 'Credit', 1, 0, 'C', True)
        pdf.cell(30, 8, 'Balance', 1, 1, 'C', True)
        
        # Ledger Entries
        pdf.set_font('Arial', '', 10)
        for _, entry in ledger_entries.iterrows():
            pdf.cell(30, 8, str(entry['transaction_date']), 1)
            pdf.cell(70, 8, entry['description'][:40], 1)
            pdf.cell(25, 8, format_currency(entry['debit']), 1)
            pdf.cell(25, 8, format_currency(entry['credit']), 1)
            pdf.cell(30, 8, format_currency(entry['balance']), 1, 1)
        
        # Save PDF to bytes
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        
        st.markdown(create_download_link(pdf_bytes, f"Employee_Ledger_{employee['employee_id']}_{start_date}_to_{end_date}"), unsafe_allow_html=True)
        
        # Display ledger in app
        st.subheader("Ledger Entries")
        st.dataframe(ledger_entries, use_container_width=True)
    else:
        st.info("No ledger entries found for the selected period.")

# Salary Management
def show_salary_management():
    st.markdown('<div class="section-header">💰 Salary Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Generate Salary", "Salary Records", "Salary Slips"])
    
    with tab1:
        st.subheader("Generate Monthly Salary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            salary_month = st.date_input("Salary Month", date.today().replace(day=1))
            payment_date = st.date_input("Payment Date", date.today())
        
        with col2:
            include_employees = st.multiselect("Select Employees", 
                                            get_active_employees_list(),
                                            default=get_active_employees_list())
        
        if st.button("Generate Salary Sheet"):
            generate_salary_sheet(salary_month, payment_date, include_employees)
    
    with tab2:
        st.subheader("Salary Records")
        
        conn = get_db_connection()
        salary_records = pd.read_sql('''
            SELECT sr.*, e.name, e.employee_id, e.designation
            FROM salary_records sr
            JOIN employees e ON sr.employee_id = e.id
            ORDER BY sr.salary_month DESC, e.name
        ''', conn)
        conn.close()
        
        if not salary_records.empty:
            st.dataframe(salary_records, use_container_width=True)
        else:
            st.info("No salary records found.")
    
    with tab3:
        st.subheader("Generate Individual Salary Slip")
        
        conn = get_db_connection()
        employees = pd.read_sql('SELECT id, employee_id, name FROM employees WHERE status = "Active"', conn)
        conn.close()
        
        if not employees.empty:
            employee_options = {f"{row['name']} ({row['employee_id']})": row['id'] for _, row in employees.iterrows()}
            selected_employee = st.selectbox("Select Employee", list(employee_options.keys()))
            
            col1, col2 = st.columns(2)
            
            with col1:
                salary_month = st.date_input("Salary Month", date.today().replace(day=1), key="slip_month")
            
            if st.button("Generate Salary Slip"):
                employee_id = employee_options[selected_employee]
                generate_individual_salary_slip(employee_id, salary_month)
        else:
            st.info("No active employees found.")

def get_active_employees_list():
    conn = get_db_connection()
    employees = pd.read_sql('SELECT id, name, employee_id FROM employees WHERE status = "Active"', conn)
    conn.close()
    return [f"{row['name']} ({row['employee_id']})" for _, row in employees.iterrows()]

def generate_salary_sheet(salary_month, payment_date, include_employees):
    conn = get_db_connection()
    
    # Extract employee IDs from selection
    employee_ids = []
    for emp_str in include_employees:
        emp_id = emp_str.split('(')[-1].split(')')[0]
        employee = conn.execute('SELECT id FROM employees WHERE employee_id = ?', (emp_id,)).fetchone()
        if employee:
            employee_ids.append(employee[0])
    
    if not employee_ids:
        st.error("No valid employees selected!")
        return
    
    # Generate salary for each employee
    salary_data = []
    for emp_id in employee_ids:
        employee = conn.execute('SELECT * FROM employees WHERE id = ?', (emp_id,)).fetchone()
        
        if employee:
            basic_salary = employee['basic_salary']
            allowances = employee['allowances']
            deductions = employee['deductions']
            net_salary = basic_salary + allowances - deductions
            
            # Insert salary record
            conn.execute('''
                INSERT OR REPLACE INTO salary_records 
                (employee_id, salary_month, basic_salary, allowances, deductions, net_salary, payment_date, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (emp_id, salary_month, basic_salary, allowances, deductions, net_salary, payment_date, 'Generated'))
            
            salary_data.append({
                'Employee ID': employee['employee_id'],
                'Name': employee['name'],
                'Designation': employee['designation'],
                'Bank': employee['bank_name'],
                'Account No': employee['account_no'],
                'Account Title': employee['account_title'],
                'Basic Salary': basic_salary,
                'Allowances': allowances,
                'Deductions': deductions,
                'Net Salary': net_salary
            })
    
    conn.commit()
    
    # Generate PDF salary sheet
    pdf = PDFReport()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Salary Sheet', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Salary Month: {salary_month.strftime('%B %Y')}", 0, 1)
    pdf.cell(0, 8, f"Payment Date: {payment_date}", 0, 1)
    pdf.cell(0, 8, f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
    pdf.ln(10)
    
    # Salary Table
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font('Arial', 'B', 10)
    
    headers = ['Emp ID', 'Name', 'Designation', 'Bank', 'Account No', 'Net Salary']
    widths = [20, 35, 30, 30, 35, 30]
    
    for i, header in enumerate(headers):
        pdf.cell(widths[i], 8, header, 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font('Arial', '', 9)
    total_salary = 0
    for data in salary_data:
        pdf.cell(widths[0], 8, data['Employee ID'], 1)
        pdf.cell(widths[1], 8, data['Name'][:20], 1)
        pdf.cell(widths[2], 8, data['Designation'][:15], 1)
        pdf.cell(widths[3], 8, data['Bank'][:15], 1)
        pdf.cell(widths[4], 8, data['Account No'], 1)
        pdf.cell(widths[5], 8, format_currency(data['Net Salary']), 1, 1)
        total_salary += data['Net Salary']
    
    # Total
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(sum(widths[:-1]), 8, 'TOTAL SALARY', 1, 0, 'R', True)
    pdf.cell(widths[5], 8, format_currency(total_salary), 1, 1, 'C', True)
    
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    
    st.success(f"Salary sheet generated for {len(salary_data)} employees!")
    st.markdown(create_download_link(pdf_bytes, f"Salary_Sheet_{salary_month.strftime('%Y_%m')}"), unsafe_allow_html=True)
    
    # Display salary data in app
    st.subheader("Generated Salary Data")
    st.dataframe(pd.DataFrame(salary_data), use_container_width=True)
    
    conn.close()

def generate_individual_salary_slip(employee_id, salary_month):
    conn = get_db_connection()
    
    # Get employee details and salary record
    employee = conn.execute('SELECT * FROM employees WHERE id = ?', (employee_id,)).fetchone()
    salary_record = conn.execute('''
        SELECT * FROM salary_records 
        WHERE employee_id = ? AND salary_month = ?
    ''', (employee_id, salary_month)).fetchone()
    
    if not salary_record:
        st.error("Salary record not found for the selected month!")
        conn.close()
        return
    
    # Generate PDF salary slip
    pdf = PDFReport()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'SALARY SLIP', 0, 1, 'C')
    pdf.ln(5)
    
    # Company and Employee Details
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, 'Nutrion Company', 0, 1, 'C')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, 'Salary Slip - Confidential', 0, 1, 'C')
    pdf.ln(10)
    
    # Employee Details
    col_width = 90
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width, 8, 'Employee Name:')
    pdf.set_font('Arial', '', 10)
    pdf.cell(col_width, 8, employee['name'])
    pdf.cell(col_width, 8, f"Month: {salary_month.strftime('%B %Y')}", 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width, 8, 'Employee ID:')
    pdf.set_font('Arial', '', 10)
    pdf.cell(col_width, 8, employee['employee_id'])
    pdf.cell(col_width, 8, f"Payment Date: {salary_record['payment_date']}", 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width, 8, 'Designation:')
    pdf.set_font('Arial', '', 10)
    pdf.cell(col_width, 8, employee['designation'])
    pdf.cell(col_width, 8, f"Bank: {employee['bank_name']}", 0, 1)
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width, 8, 'Department:')
    pdf.set_font('Arial', '', 10)
    pdf.cell(col_width, 8, employee['department'])
    pdf.cell(col_width, 8, f"Account No: {employee['account_no']}", 0, 1)
    pdf.ln(10)
    
    # Salary Breakdown
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'EARNINGS', 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(140, 8, 'Basic Salary', 1)
    pdf.cell(50, 8, format_currency(salary_record['basic_salary']), 1, 1, 'R')
    
    pdf.cell(140, 8, 'Allowances', 1)
    pdf.cell(50, 8, format_currency(salary_record['allowances']), 1, 1, 'R')
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(140, 8, 'Total Earnings', 1)
    pdf.cell(50, 8, format_currency(salary_record['basic_salary'] + salary_record['allowances']), 1, 1, 'R')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, 'DEDUCTIONS', 1, 1, 'C', True)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(140, 8, 'Total Deductions', 1)
    pdf.cell(50, 8, format_currency(salary_record['deductions']), 1, 1, 'R')
    pdf.ln(5)
    
    # Net Salary
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(100, 100, 100)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(140, 10, 'NET SALARY', 1, 0, 'C', True)
    pdf.cell(50, 10, format_currency(salary_record['net_salary']), 1, 1, 'C', True)
    
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    
    st.success("Salary slip generated successfully!")
    st.markdown(create_download_link(pdf_bytes, f"Salary_Slip_{employee['employee_id']}_{salary_month.strftime('%Y_%m')}"), unsafe_allow_html=True)
    
    conn.close()

# Expense Management
def show_expense_management():
    st.markdown('<div class="section-header">💸 Expense Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add Expense", "View Expenses", "Expense Categories", "Monthly Reports"])
    
    with tab1:
        st.subheader("Add Company Expense")
        
        with st.form("add_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Expense Date*", date.today())
                
                conn = get_db_connection()
                categories = pd.read_sql('SELECT * FROM expense_categories', conn)
                category_options = {row['category_name']: row['id'] for _, row in categories.iterrows()}
                conn.close()
                
                category_name = st.selectbox("Category*", list(category_options.keys()))
                amount = st.number_input("Amount*", min_value=0.0, step=100.0)
                description = st.text_area("Description")
            
            with col2:
                paid_to = st.text_input("Paid To")
                payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Cheque", "Card"])
                reference_no = st.text_input("Reference Number")
                
                # Link to employee if applicable
                conn = get_db_connection()
                employees = pd.read_sql('SELECT id, name, employee_id FROM employees WHERE status = "Active"', conn)
                conn.close()
                
                employee_options = ["None"] + [f"{row['name']} ({row['employee_id']})" for _, row in employees.iterrows()]
                linked_employee = st.selectbox("Link to Employee (if applicable)", employee_options)
            
            submitted = st.form_submit_button("Add Expense")
            
            if submitted:
                if not all([expense_date, category_name, amount]):
                    st.error("Please fill all required fields (*)")
                else:
                    category_id = category_options[category_name]
                    employee_id = None
                    
                    if linked_employee != "None":
                        emp_id_str = linked_employee.split('(')[-1].split(')')[0]
                        conn = get_db_connection()
                        employee = conn.execute('SELECT id FROM employees WHERE employee_id = ?', (emp_id_str,)).fetchone()
                        if employee:
                            employee_id = employee[0]
                    
                    conn = get_db_connection()
                    conn.execute('''
                        INSERT INTO company_expenses 
                        (expense_date, category_id, amount, description, paid_to, payment_method, reference_no, employee_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (expense_date, category_id, amount, description, paid_to, payment_method, reference_no, employee_id))
                    
                    # If linked to employee, update employee ledger
                    if employee_id:
                        # Get current balance
                        ledger = conn.execute('''
                            SELECT balance FROM employee_ledger 
                            WHERE employee_id = ? 
                            ORDER BY transaction_date DESC, created_at DESC 
                            LIMIT 1
                        ''', (employee_id,)).fetchone()
                        
                        current_balance = ledger[0] if ledger else 0
                        new_balance = current_balance - amount
                        
                        conn.execute('''
                            INSERT INTO employee_ledger 
                            (employee_id, transaction_date, description, debit, credit, balance, reference_type, reference_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (employee_id, expense_date, f"Expense: {description}", amount, 0, new_balance, 'expense', conn.lastrowid))
                    
                    conn.commit()
                    conn.close()
                    
                    st.success("Expense added successfully!")
    
    with tab2:
        st.subheader("Expense Records")
        
        conn = get_db_connection()
        expenses = pd.read_sql('''
            SELECT ce.*, ec.category_name, e.name as employee_name
            FROM company_expenses ce
            JOIN expense_categories ec ON ce.category_id = ec.id
            LEFT JOIN employees e ON ce.employee_id = e.id
            ORDER BY ce.expense_date DESC
        ''', conn)
        conn.close()
        
        if not expenses.empty:
            for _, expense in expenses.iterrows():
                with st.expander(f"{expense['expense_date']} - {expense['category_name']} - {format_currency(expense['amount'])}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Description:** {expense['description']}")
                        st.write(f"**Paid To:** {expense['paid_to']}")
                        st.write(f"**Payment Method:** {expense['payment_method']}")
                    
                    with col2:
                        st.write(f"**Reference No:** {expense['reference_no']}")
                        if expense['employee_name']:
                            st.write(f"**Linked Employee:** {expense['employee_name']}")
                        st.write(f"**Added On:** {expense['created_at']}")
                    
                    col_edit, col_delete = st.columns(2)
                    
                    with col_edit:
                        if st.button("Edit", key=f"edit_expense_{expense['id']}"):
                            st.session_state[f'edit_expense_{expense["id"]}'] = True
                    
                    with col_delete:
                        if st.button("Delete", key=f"delete_expense_{expense['id']}"):
                            conn = get_db_connection()
                            conn.execute('DELETE FROM company_expenses WHERE id = ?', (expense['id'],))
                            conn.commit()
                            conn.close()
                            st.success("Expense deleted successfully!")
                            st.rerun()
                    
                    if st.session_state.get(f'edit_expense_{expense["id"]}', False):
                        edit_expense_form(expense)
        else:
            st.info("No expenses found. Add some expenses to get started.")
    
    with tab3:
        st.subheader("Expense Categories")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Add New Category")
            with st.form("add_category_form"):
                category_name = st.text_input("Category Name")
                description = st.text_area("Description")
                
                if st.form_submit_button("Add Category"):
                    if category_name:
                        conn = get_db_connection()
                        try:
                            conn.execute('INSERT INTO expense_categories (category_name, description) VALUES (?, ?)', 
                                       (category_name, description))
                            conn.commit()
                            st.success("Category added successfully!")
                        except sqlite3.IntegrityError:
                            st.error("Category name already exists!")
                        finally:
                            conn.close()
        
        with col2:
            st.subheader("Existing Categories")
            conn = get_db_connection()
            categories = pd.read_sql('SELECT * FROM expense_categories ORDER BY category_name', conn)
            conn.close()
            
            for _, category in categories.iterrows():
                col_del, col_name = st.columns([1, 4])
                with col_del:
                    if st.button("🗑️", key=f"del_cat_{category['id']}"):
                        conn = get_db_connection()
                        # Check if category is used in expenses
                        used = conn.execute('SELECT COUNT(*) FROM company_expenses WHERE category_id = ?', 
                                          (category['id'],)).fetchone()[0]
                        if used > 0:
                            st.error("Cannot delete category that is used in expenses!")
                        else:
                            conn.execute('DELETE FROM expense_categories WHERE id = ?', (category['id'],))
                            conn.commit()
                            st.success("Category deleted successfully!")
                            st.rerun()
                        conn.close()
                with col_name:
                    st.write(f"**{category['category_name']}** - {category['description']}")
    
    with tab4:
        st.subheader("Monthly Expense Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="exp_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="exp_end")
        
        if st.button("Generate Expense Report"):
            generate_expense_report(start_date, end_date)

def edit_expense_form(expense):
    st.subheader("Edit Expense")
    
    conn = get_db_connection()
    categories = pd.read_sql('SELECT * FROM expense_categories', conn)
    category_options = {row['category_name']: row['id'] for _, row in categories.iterrows()}
    conn.close()
    
    with st.form(f"edit_expense_{expense['id']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            expense_date = st.date_input("Expense Date", value=datetime.strptime(expense['expense_date'], '%Y-%m-%d').date())
            category_name = st.selectbox("Category", list(category_options.keys()), 
                                       index=list(category_options.keys()).index(expense['category_name']))
            amount = st.number_input("Amount", value=float(expense['amount']), min_value=0.0, step=100.0)
            description = st.text_area("Description", value=expense['description'])
        
        with col2:
            paid_to = st.text_input("Paid To", value=expense['paid_to'] or "")
            payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Cheque", "Card"],
                                        index=["Cash", "Bank Transfer", "Cheque", "Card"].index(expense['payment_method']))
            reference_no = st.text_input("Reference Number", value=expense['reference_no'] or "")
        
        submitted = st.form_submit_button("Update Expense")
        
        if submitted:
            category_id = category_options[category_name]
            
            conn = get_db_connection()
            conn.execute('''
                UPDATE company_expenses 
                SET expense_date=?, category_id=?, amount=?, description=?, paid_to=?, payment_method=?, reference_no=?
                WHERE id=?
            ''', (expense_date, category_id, amount, description, paid_to, payment_method, reference_no, expense['id']))
            conn.commit()
            conn.close()
            
            st.session_state[f'edit_expense_{expense["id"]}'] = False
            st.success("Expense updated successfully!")
            st.rerun()

def generate_expense_report(start_date, end_date):
    conn = get_db_connection()
    
    # Get expense data
    expenses = pd.read_sql('''
        SELECT ce.expense_date, ec.category_name, ce.amount, ce.description, ce.paid_to, ce.payment_method,
               e.name as employee_name
        FROM company_expenses ce
        JOIN expense_categories ec ON ce.category_id = ec.id
        LEFT JOIN employees e ON ce.employee_id = e.id
        WHERE ce.expense_date BETWEEN ? AND ?
        ORDER BY ce.expense_date, ec.category_name
    ''', conn, params=(start_date, end_date))
    
    # Get category-wise summary
    category_summary = pd.read_sql('''
        SELECT ec.category_name, SUM(ce.amount) as total_amount
        FROM company_expenses ce
        JOIN expense_categories ec ON ce.category_id = ec.id
        WHERE ce.expense_date BETWEEN ? AND ?
        GROUP BY ec.category_name
        ORDER BY total_amount DESC
    ''', conn, params=(start_date, end_date))
    
    conn.close()
    
    if not expenses.empty:
        # Generate PDF report
        pdf = PDFReport()
        pdf.add_page()
        
        # Header
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Expense Report', 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f"Period: {start_date} to {end_date}", 0, 1)
        pdf.cell(0, 8, f"Total Expenses: {format_currency(expenses['amount'].sum())}", 0, 1)
        pdf.cell(0, 8, f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
        pdf.ln(10)
        
        # Category Summary
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Category-wise Summary', 0, 1)
        
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(120, 8, 'Category', 1, 0, 'C', True)
        pdf.cell(60, 8, 'Total Amount', 1, 1, 'C', True)
        
        pdf.set_font('Arial', '', 10)
        for _, category in category_summary.iterrows():
            pdf.cell(120, 8, category['category_name'], 1)
            pdf.cell(60, 8, format_currency(category['total_amount']), 1, 1, 'R')
        
        pdf.ln(10)
        
        # Detailed Expenses
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Detailed Expenses', 0, 1)
        
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font('Arial', 'B', 8)
        headers = ['Date', 'Category', 'Amount', 'Description', 'Paid To', 'Payment Method']
        widths = [25, 30, 25, 50, 30, 30]
        
        for i, header in enumerate(headers):
            pdf.cell(widths[i], 8, header, 1, 0, 'C', True)
        pdf.ln()
        
        pdf.set_font('Arial', '', 7)
        for _, expense in expenses.iterrows():
            pdf.cell(widths[0], 8, str(expense['expense_date']), 1)
            pdf.cell(widths[1], 8, expense['category_name'][:15], 1)
            pdf.cell(widths[2], 8, format_currency(expense['amount']), 1)
            pdf.cell(widths[3], 8, expense['description'][:40], 1)
            pdf.cell(widths[4], 8, expense['paid_to'][:15] if expense['paid_to'] else '', 1)
            pdf.cell(widths[5], 8, expense['payment_method'], 1, 1)
        
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        
        st.success(f"Expense report generated with {len(expenses)} records!")
        st.markdown(create_download_link(pdf_bytes, f"Expense_Report_{start_date}_to_{end_date}"), unsafe_allow_html=True)
        
        # Display data in app
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Category-wise Summary")
            st.dataframe(category_summary, use_container_width=True)
        
        with col2:
            st.subheader("Detailed Expenses")
            st.dataframe(expenses, use_container_width=True)
    else:
        st.info("No expenses found for the selected period.")

# Reports & Analytics
def show_reports_analytics():
    st.markdown('<div class="section-header">📈 Reports & Analytics</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Financial Summary", "Employee Reports", "Expense Analysis", "Custom Reports"])
    
    with tab1:
        st.subheader("Financial Summary")
        
        col1, col2 = st.columns(2)
        
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="fin_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="fin_end")
        
        if st.button("Generate Financial Summary"):
            generate_financial_summary(start_date, end_date)
    
    with tab2:
        st.subheader("Employee Reports")
        
        report_type = st.selectbox("Report Type", [
            "Employee Master List",
            "Department-wise Summary",
            "Salary Analysis",
            "Employee Status Report"
        ])
        
        if st.button("Generate Employee Report"):
            generate_employee_report(report_type)
    
    with tab3:
        st.subheader("Expense Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            analysis_type = st.selectbox("Analysis Type", [
                "Monthly Trend",
                "Category Distribution",
                "Payment Method Analysis",
                "Top Expenses"
            ])
        with col2:
            year = st.selectbox("Year", range(2020, datetime.now().year + 1), index=datetime.now().year - 2020)
        
        if st.button("Generate Expense Analysis"):
            generate_expense_analysis(analysis_type, year)
    
    with tab4:
        st.subheader("Custom Reports")
        
        st.info("Custom reporting feature allows you to create tailored reports based on specific criteria.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            report_entity = st.selectbox("Report On", ["Employees", "Expenses", "Salaries", "Ledger"])
            date_range = st.checkbox("Include Date Range", value=True)
        
        with col2:
            if date_range:
                col_start, col_end = st.columns(2)
                with col_start:
                    custom_start = st.date_input("Start Date", date.today().replace(day=1))
                with col_end:
                    custom_end = st.date_input("End Date", date.today())
        
        include_charts = st.checkbox("Include Charts", value=True)
        
        if st.button("Generate Custom Report"):
            generate_custom_report(report_entity, custom_start if date_range else None, custom_end if date_range else None, include_charts)

def generate_financial_summary(start_date, end_date):
    conn = get_db_connection()
    
    # Total Salary
    total_salary = conn.execute('''
        SELECT SUM(net_salary) FROM salary_records 
        WHERE salary_month BETWEEN ? AND ? AND status = 'Generated'
    ''', (start_date, end_date)).fetchone()[0] or 0
    
    # Total Expenses
    total_expenses = conn.execute('''
        SELECT SUM(amount) FROM company_expenses 
        WHERE expense_date BETWEEN ? AND ?
    ''', (start_date, end_date)).fetchone()[0] or 0
    
    # Employee count
    active_employees = conn.execute('SELECT COUNT(*) FROM employees WHERE status = "Active"').fetchone()[0]
    
    # Category-wise expenses
    category_expenses = pd.read_sql('''
        SELECT ec.category_name, SUM(ce.amount) as total
        FROM company_expenses ce
        JOIN expense_categories ec ON ce.category_id = ec.id
        WHERE ce.expense_date BETWEEN ? AND ?
        GROUP BY ec.category_name
        ORDER BY total DESC
    ''', conn, params=(start_date, end_date))
    
    conn.close()
    
    # Generate PDF report
    pdf = PDFReport()
    pdf.add_page()
    
    # Header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Financial Summary Report', 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Period: {start_date} to {end_date}", 0, 1)
    pdf.cell(0, 8, f"Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
    pdf.ln(10)
    
    # Key Metrics
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Key Financial Metrics', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 8, f"Total Salary Expenses: {format_currency(total_salary)}", 0, 1)
    pdf.cell(0, 8, f"Total Operating Expenses: {format_currency(total_expenses)}", 0, 1)
    pdf.cell(0, 8, f"Total Expenses: {format_currency(total_salary + total_expenses)}", 0, 1)
    pdf.cell(0, 8, f"Active Employees: {active_employees}", 0, 1)
    pdf.ln(10)
    
    # Category-wise breakdown
    if not category_expenses.empty:
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Expense Breakdown by Category', 0, 1)
        
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(120, 8, 'Category', 1, 0, 'C', True)
        pdf.cell(60, 8, 'Amount', 1, 1, 'C', True)
        
        pdf.set_font('Arial', '', 10)
        for _, row in category_expenses.iterrows():
            pdf.cell(120, 8, row['category_name'], 1)
            pdf.cell(60, 8, format_currency(row['total']), 1, 1, 'R')
    
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    
    # Display in app
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total Salary", format_currency(total_salary))
        st.metric("Total Operating Expenses", format_currency(total_expenses))
    
    with col2:
        st.metric("Total Expenses", format_currency(total_salary + total_expenses))
        st.metric("Active Employees", active_employees)
    
    if not category_expenses.empty:
        st.subheader("Expense Breakdown by Category")
        st.bar_chart(category_expenses.set_index('category_name'))
    
    st.markdown(create_download_link(pdf_bytes, f"Financial_Summary_{start_date}_to_{end_date}"), unsafe_allow_html=True)

# Data Import/Export
def show_data_import_export():
    st.markdown('<div class="section-header">📤 Data Import/Export</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Import Data", "Export Data", "Templates"])
    
    with tab1:
        st.subheader("Import Data from Excel")
        
        import_type = st.selectbox("Select Data Type to Import", [
            "Employees",
            "Expenses",
            "Salary Records"
        ])
        
        uploaded_file = st.file_uploader(f"Upload Excel file for {import_type}", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head(), use_container_width=True)
                
                if st.button(f"Import {import_type}"):
                    import_data(import_type, df)
                    st.success(f"{import_type} data imported successfully!")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with tab2:
        st.subheader("Export Data")
        
        export_type = st.selectbox("Select Data Type to Export", [
            "Employees",
            "Expenses",
            "Salary Records",
            "Expense Categories",
            "Employee Ledger"
        ])
        
        col1, col2 = st.columns(2)
        
        with col1:
            if export_type in ["Expenses", "Salary Records", "Employee Ledger"]:
                exp_start_date = st.date_input("Start Date", date.today().replace(day=1), key="export_start")
            file_format = st.selectbox("Export Format", ["Excel", "CSV"])
        
        with col2:
            if export_type in ["Expenses", "Salary Records", "Employee Ledger"]:
                exp_end_date = st.date_input("End Date", date.today(), key="export_end")
        
        if st.button("Export Data"):
            export_data(export_type, exp_start_date if 'exp_start_date' in locals() else None, 
                       exp_end_date if 'exp_end_date' in locals() else None, file_format)
    
    with tab3:
        st.subheader("Download Excel Templates")
        
        template_type = st.selectbox("Select Template Type", [
            "Employee Template",
            "Expense Template",
            "Salary Template"
        ])
        
        if st.button("Download Template"):
            download_template(template_type)

def import_data(data_type, df):
    conn = get_db_connection()
    
    try:
        if data_type == "Employees":
            for _, row in df.iterrows():
                conn.execute('''
                    INSERT OR REPLACE INTO employees 
                    (employee_id, name, designation, department, account_no, account_title, bank_name, 
                     basic_salary, allowances, deductions, join_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row.get('employee_id'), row.get('name'), row.get('designation'), row.get('department'),
                    row.get('account_no'), row.get('account_title'), row.get('bank_name'),
                    row.get('basic_salary', 0), row.get('allowances', 0), row.get('deductions', 0),
                    row.get('join_date'), row.get('status', 'Active')
                ))
        
        elif data_type == "Expenses":
            for _, row in df.iterrows():
                # Get category ID
                category_name = row.get('category_name')
                category = conn.execute('SELECT id FROM expense_categories WHERE category_name = ?', (category_name,)).fetchone()
                
                if category:
                    category_id = category[0]
                    conn.execute('''
                        INSERT INTO company_expenses 
                        (expense_date, category_id, amount, description, paid_to, payment_method, reference_no)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('expense_date'), category_id, row.get('amount'), row.get('description'),
                        row.get('paid_to'), row.get('payment_method'), row.get('reference_no')
                    ))
        
        conn.commit()
        
    except Exception as e:
        st.error(f"Error importing data: {str(e)}")
        conn.rollback()
    finally:
        conn.close()

def export_data(data_type, start_date, end_date, file_format):
    conn = get_db_connection()
    
    try:
        if data_type == "Employees":
            df = pd.read_sql('SELECT * FROM employees', conn)
            filename = "employees_export"
        
        elif data_type == "Expenses":
            query = '''
                SELECT ce.*, ec.category_name, e.name as employee_name
                FROM company_expenses ce
                JOIN expense_categories ec ON ce.category_id = ec.id
                LEFT JOIN employees e ON ce.employee_id = e.id
            '''
            if start_date and end_date:
                query += ' WHERE ce.expense_date BETWEEN ? AND ?'
                df = pd.read_sql(query, conn, params=(start_date, end_date))
            else:
                df = pd.read_sql(query, conn)
            filename = f"expenses_export_{start_date}_to_{end_date}" if start_date and end_date else "expenses_export"
        
        elif data_type == "Salary Records":
            query = '''
                SELECT sr.*, e.name, e.employee_id, e.designation
                FROM salary_records sr
                JOIN employees e ON sr.employee_id = e.id
            '''
            if start_date and end_date:
                query += ' WHERE sr.salary_month BETWEEN ? AND ?'
                df = pd.read_sql(query, conn, params=(start_date, end_date))
            else:
                df = pd.read_sql(query, conn)
            filename = f"salary_export_{start_date}_to_{end_date}" if start_date and end_date else "salary_export"
        
        elif data_type == "Expense Categories":
            df = pd.read_sql('SELECT * FROM expense_categories', conn)
            filename = "expense_categories_export"
        
        elif data_type == "Employee Ledger":
            query = '''
                SELECT el.*, e.name, e.employee_id
                FROM employee_ledger el
                JOIN employees e ON el.employee_id = e.id
            '''
            if start_date and end_date:
                query += ' WHERE el.transaction_date BETWEEN ? AND ?'
                df = pd.read_sql(query, conn, params=(start_date, end_date))
            else:
                df = pd.read_sql(query, conn)
            filename = f"ledger_export_{start_date}_to_{end_date}" if start_date and end_date else "ledger_export"
        
        if file_format == "Excel":
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Data')
            output.seek(0)
            st.download_button(
                label="Download Excel File",
                data=output,
                file_name=f"{filename}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:  # CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV File",
                data=csv,
                file_name=f"{filename}.csv",
                mime="text/csv"
            )
    
    except Exception as e:
        st.error(f"Error exporting data: {str(e)}")
    finally:
        conn.close()

def download_template(template_type):
    if template_type == "Employee Template":
        df = pd.DataFrame(columns=[
            'employee_id', 'name', 'designation', 'department', 'account_no',
            'account_title', 'bank_name', 'basic_salary', 'allowances', 'deductions', 'join_date'
        ])
        filename = "employee_template.xlsx"
    
    elif template_type == "Expense Template":
        df = pd.DataFrame(columns=[
            'expense_date', 'category_name', 'amount', 'description', 'paid_to', 'payment_method', 'reference_no'
        ])
        filename = "expense_template.xlsx"
    
    elif template_type == "Salary Template":
        df = pd.DataFrame(columns=[
            'employee_id', 'salary_month', 'basic_salary', 'allowances', 'deductions', 'payment_date'
        ])
        filename = "salary_template.xlsx"
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Template')
    output.seek(0)
    
    st.download_button(
        label=f"Download {template_type}",
        data=output,
        file_name=filename,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Additional helper functions for employee reports and expense analysis
def generate_employee_report(report_type):
    conn = get_db_connection()
    
    if report_type == "Employee Master List":
        df = pd.read_sql('SELECT * FROM employees ORDER BY department, name', conn)
        filename = "employee_master_list"
    
    elif report_type == "Department-wise Summary":
        df = pd.read_sql('''
            SELECT department, COUNT(*) as employee_count, 
                   AVG(basic_salary) as avg_salary,
                   SUM(basic_salary + allowances - deductions) as total_salary_budget
            FROM employees 
            WHERE status = "Active"
            GROUP BY department
            ORDER BY employee_count DESC
        ''', conn)
        filename = "department_summary"
    
    elif report_type == "Salary Analysis":
        df = pd.read_sql('''
            SELECT department, 
                   MIN(basic_salary) as min_salary,
                   MAX(basic_salary) as max_salary,
                   AVG(basic_salary) as avg_salary,
               COUNT(*) as employee_count
            FROM employees 
            WHERE status = "Active"
            GROUP BY department
        ''', conn)
        filename = "salary_analysis"
    
    elif report_type == "Employee Status Report":
        df = pd.read_sql('''
            SELECT status, COUNT(*) as count,
                   AVG(basic_salary) as avg_salary
            FROM employees 
            GROUP BY status
        ''', conn)
        filename = "employee_status_report"
    
    conn.close()
    
    # Generate PDF
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'{report_type} Report', 0, 1, 'C')
    pdf.ln(10)
    
    # Create table
    col_widths = [pdf.w / len(df.columns)] * len(df.columns)
    
    # Header
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font('Arial', 'B', 10)
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 8, str(col).replace('_', ' ').title(), 1, 0, 'C', True)
    pdf.ln()
    
    # Data
    pdf.set_font('Arial', '', 8)
    for _, row in df.iterrows():
        for i, value in enumerate(row):
            pdf.cell(col_widths[i], 8, str(value), 1)
        pdf.ln()
    
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    
    st.dataframe(df, use_container_width=True)
    st.markdown(create_download_link(pdf_bytes, filename), unsafe_allow_html=True)

def generate_expense_analysis(analysis_type, year):
    conn = get_db_connection()
    
    if analysis_type == "Monthly Trend":
        df = pd.read_sql('''
            SELECT strftime("%Y-%m", expense_date) as month, SUM(amount) as total
            FROM company_expenses
            WHERE strftime("%Y", expense_date) = ?
            GROUP BY month
            ORDER BY month
        ''', conn, params=(str(year),))
        filename = f"monthly_expense_trend_{year}"
    
    elif analysis_type == "Category Distribution":
        df = pd.read_sql('''
            SELECT ec.category_name, SUM(ce.amount) as total
            FROM company_expenses ce
            JOIN expense_categories ec ON ce.category_id = ec.id
            WHERE strftime("%Y", ce.expense_date) = ?
            GROUP BY ec.category_name
            ORDER BY total DESC
        ''', conn, params=(str(year),))
        filename = f"category_distribution_{year}"
    
    elif analysis_type == "Payment Method Analysis":
        df = pd.read_sql('''
            SELECT payment_method, SUM(amount) as total, COUNT(*) as transaction_count
            FROM company_expenses
            WHERE strftime("%Y", expense_date) = ?
            GROUP BY payment_method
            ORDER BY total DESC
        ''', conn, params=(str(year),))
        filename = f"payment_method_analysis_{year}"
    
    elif analysis_type == "Top Expenses":
        df = pd.read_sql('''
            SELECT expense_date, ec.category_name, amount, description, paid_to
            FROM company_expenses ce
            JOIN expense_categories ec ON ce.category_id = ec.id
            WHERE strftime("%Y", expense_date) = ?
            ORDER BY amount DESC
            LIMIT 20
        ''', conn, params=(str(year),))
        filename = f"top_expenses_{year}"
    
    conn.close()
    
    # Display chart
    if analysis_type in ["Monthly Trend", "Category Distribution"]:
        if analysis_type == "Monthly Trend":
            st.line_chart(df.set_index('month'))
        else:
            st.bar_chart(df.set_index('category_name'))
    
    # Generate PDF
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'{analysis_type} - {year}', 0, 1, 'C')
    pdf.ln(10)
    
    # Table
    col_widths = [pdf.w / len(df.columns)] * len(df.columns)
    
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font('Arial', 'B', 10)
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 8, str(col).replace('_', ' ').title(), 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font('Arial', '', 8)
    for _, row in df.iterrows():
        for i, value in enumerate(row):
            pdf.cell(col_widths[i], 8, str(value), 1)
        pdf.ln()
    
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    
    st.dataframe(df, use_container_width=True)
    st.markdown(create_download_link(pdf_bytes, filename), unsafe_allow_html=True)

def generate_custom_report(entity, start_date, end_date, include_charts):
    conn = get_db_connection()
    
    if entity == "Employees":
        query = 'SELECT * FROM employees'
        if start_date and end_date:
            query += ' WHERE join_date BETWEEN ? AND ?'
            df = pd.read_sql(query, conn, params=(start_date, end_date))
        else:
            df = pd.read_sql(query, conn)
        filename = "custom_employee_report"
    
    elif entity == "Expenses":
        query = '''
            SELECT ce.*, ec.category_name, e.name as employee_name
            FROM company_expenses ce
            JOIN expense_categories ec ON ce.category_id = ec.id
            LEFT JOIN employees e ON ce.employee_id = e.id
        '''
        if start_date and end_date:
            query += ' WHERE ce.expense_date BETWEEN ? AND ?'
            df = pd.read_sql(query, conn, params=(start_date, end_date))
        else:
            df = pd.read_sql(query, conn)
        filename = "custom_expense_report"
    
    elif entity == "Salaries":
        query = '''
            SELECT sr.*, e.name, e.employee_id, e.designation
            FROM salary_records sr
            JOIN employees e ON sr.employee_id = e.id
        '''
        if start_date and end_date:
            query += ' WHERE sr.salary_month BETWEEN ? AND ?'
            df = pd.read_sql(query, conn, params=(start_date, end_date))
        else:
            df = pd.read_sql(query, conn)
        filename = "custom_salary_report"
    
    elif entity == "Ledger":
        query = '''
            SELECT el.*, e.name, e.employee_id
            FROM employee_ledger el
            JOIN employees e ON el.employee_id = e.id
        '''
        if start_date and end_date:
            query += ' WHERE el.transaction_date BETWEEN ? AND ?'
            df = pd.read_sql(query, conn, params=(start_date, end_date))
        else:
            df = pd.read_sql(query, conn)
        filename = "custom_ledger_report"
    
    conn.close()
    
    # Generate PDF
    pdf = PDFReport()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'Custom {entity} Report', 0, 1, 'C')
    
    if start_date and end_date:
        pdf.set_font('Arial', '', 12)
        pdf.cell(0, 8, f'Period: {start_date} to {end_date}', 0, 1)
    
    pdf.ln(10)
    
    # Table
    col_widths = [pdf.w / len(df.columns)] * len(df.columns)
    
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font('Arial', 'B', 8)
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 8, str(col).replace('_', ' ').title(), 1, 0, 'C', True)
    pdf.ln()
    
    pdf.set_font('Arial', '', 7)
    for _, row in df.iterrows():
        for i, value in enumerate(row):
            pdf.cell(col_widths[i], 8, str(value), 1)
        pdf.ln()
    
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    
    st.success(f"Custom report generated with {len(df)} records!")
    st.dataframe(df, use_container_width=True)
    
    if include_charts and entity == "Expenses" and not df.empty:
        st.subheader("Visual Analysis")
        category_summary = df.groupby('category_name')['amount'].sum().sort_values(ascending=False)
        st.bar_chart(category_summary)
    
    st.markdown(create_download_link(pdf_bytes, filename), unsafe_allow_html=True)

if __name__ == "__main__":
    main()
