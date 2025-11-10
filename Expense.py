# app.py
import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import sqlite3
import io
from fpdf import FPDF
import tempfile
import os
import plotly.express as px
import plotly.graph_objects as go
from streamlit_option_menu import option_menu

# Page configuration
st.set_page_config(
    page_title="Nutrion HR & Expense Management",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database initialization
def init_db():
    conn = sqlite3.connect('hr_expense.db', check_same_thread=False)
    c = conn.cursor()
    
    # Employees table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            name TEXT NOT NULL,
            designation TEXT,
            department TEXT,
            bank_account TEXT,
            account_title TEXT,
            bank_name TEXT,
            basic_salary REAL,
            joining_date DATE,
            status TEXT DEFAULT 'Active',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Expense categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_code TEXT UNIQUE,
            category_name TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    # Employee ledger table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            transaction_date DATE,
            description TEXT,
            transaction_type TEXT,
            amount REAL,
            balance REAL,
            reference TEXT,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # Company expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date DATE,
            category_id INTEGER,
            description TEXT,
            amount REAL,
            employee_id TEXT,
            approved_by TEXT,
            status TEXT DEFAULT 'Pending',
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id),
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # Salary records table
    c.execute('''
        CREATE TABLE IF NOT EXISTS salary_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            salary_month DATE,
            basic_salary REAL,
            allowances REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            net_salary REAL,
            status TEXT DEFAULT 'Pending',
            paid_date DATE,
            created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # Insert default expense categories if not exists
    default_categories = [
        ('TRAVEL', 'Travel Expenses', 'Business travel costs'),
        ('MEALS', 'Meals & Entertainment', 'Client meetings and team meals'),
        ('OFFICE', 'Office Supplies', 'Office stationery and supplies'),
        ('SOFTWARE', 'Software Licenses', 'Software subscriptions'),
        ('HARDWARE', 'Hardware Equipment', 'Computers and equipment'),
        ('MARKETING', 'Marketing Expenses', 'Advertising and promotion'),
        ('UTILITIES', 'Utilities', 'Electricity, internet, phone'),
        ('MAINTENANCE', 'Maintenance', 'Equipment maintenance'),
        ('TRAINING', 'Training & Development', 'Employee training programs'),
        ('OTHER', 'Other Expenses', 'Miscellaneous expenses')
    ]
    
    for category in default_categories:
        c.execute('''
            INSERT OR IGNORE INTO expense_categories (category_code, category_name, description)
            VALUES (?, ?, ?)
        ''', category)
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .section-header {
        font-size: 1.8rem;
        color: #1f77b4;
        margin-bottom: 1rem;
        font-weight: bold;
        border-bottom: 2px solid #1f77b4;
        padding-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.3rem;
        color: #2e86ab;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #155724;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #0c5460;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
        color: #856404;
    }
    .metric-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #1f77b4;
    }
    .metric-label {
        font-size: 1rem;
        color: #6c757d;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

# Database functions
def get_connection():
    return sqlite3.connect('hr_expense.db', check_same_thread=False)

# Employee Management Functions
def add_employee(employee_data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO employees 
            (employee_id, name, designation, department, bank_account, account_title, bank_name, basic_salary, joining_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', employee_data)
        # Initialize ledger with zero balance
        c.execute('''
            INSERT INTO employee_ledger (employee_id, transaction_date, description, transaction_type, amount, balance)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (employee_data[0], employee_data[8], 'Initial Balance', 'Opening', 0, 0))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding employee: {str(e)}")
        return False
    finally:
        conn.close()

def get_employees():
    conn = get_connection()
    df = pd.read_sql('SELECT * FROM employees WHERE status = "Active" ORDER BY name', conn)
    conn.close()
    return df

def update_employee(employee_id, update_data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE employees 
            SET name=?, designation=?, department=?, bank_account=?, account_title=?, bank_name=?, basic_salary=?
            WHERE employee_id=?
        ''', (*update_data, employee_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating employee: {str(e)}")
        return False
    finally:
        conn.close()

def delete_employee(employee_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('UPDATE employees SET status="Inactive" WHERE employee_id=?', (employee_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting employee: {str(e)}")
        return False
    finally:
        conn.close()

# Expense Category Functions
def add_expense_category(category_data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO expense_categories (category_code, category_name, description)
            VALUES (?, ?, ?)
        ''', category_data)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding category: {str(e)}")
        return False
    finally:
        conn.close()

def get_expense_categories():
    conn = get_connection()
    df = pd.read_sql('SELECT * FROM expense_categories WHERE status = "Active" ORDER BY category_name', conn)
    conn.close()
    return df

def update_expense_category(category_id, update_data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            UPDATE expense_categories 
            SET category_code=?, category_name=?, description=?
            WHERE id=?
        ''', (*update_data, category_id))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error updating category: {str(e)}")
        return False
    finally:
        conn.close()

def delete_expense_category(category_id):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('UPDATE expense_categories SET status="Inactive" WHERE id=?', (category_id,))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error deleting category: {str(e)}")
        return False
    finally:
        conn.close()

# Expense Management Functions
def add_company_expense(expense_data):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO company_expenses 
            (expense_date, category_id, description, amount, employee_id, approved_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', expense_data)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding expense: {str(e)}")
        return False
    finally:
        conn.close()

def get_company_expenses(start_date=None, end_date=None):
    conn = get_connection()
    query = '''
        SELECT ce.*, ec.category_name, e.name as employee_name 
        FROM company_expenses ce
        LEFT JOIN expense_categories ec ON ce.category_id = ec.id
        LEFT JOIN employees e ON ce.employee_id = e.employee_id
        WHERE 1=1
    '''
    params = []
    
    if start_date:
        query += ' AND ce.expense_date >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND ce.expense_date <= ?'
        params.append(end_date)
    
    query += ' ORDER BY ce.expense_date DESC'
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# Employee Ledger Functions
def get_employee_ledger(employee_id):
    conn = get_connection()
    df = pd.read_sql('''
        SELECT * FROM employee_ledger 
        WHERE employee_id = ? 
        ORDER BY transaction_date DESC, created_date DESC
    ''', conn, params=(employee_id,))
    conn.close()
    return df

def add_ledger_entry(entry_data):
    conn = get_connection()
    c = conn.cursor()
    try:
        # Get current balance
        c.execute('SELECT balance FROM employee_ledger WHERE employee_id = ? ORDER BY id DESC LIMIT 1', (entry_data[0],))
        result = c.fetchone()
        current_balance = result[0] if result else 0
        
        # Calculate new balance based on transaction type
        if entry_data[3] in ['Salary', 'Reimbursement']:
            new_balance = current_balance + entry_data[4]
        else:  # Expense, Deduction
            new_balance = current_balance - entry_data[4]
        
        c.execute('''
            INSERT INTO employee_ledger 
            (employee_id, transaction_date, description, transaction_type, amount, balance, reference)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (*entry_data, new_balance))
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error adding ledger entry: {str(e)}")
        return False
    finally:
        conn.close()

# Salary Management Functions
def generate_salary_records(salary_month, employees_df):
    conn = get_connection()
    c = conn.cursor()
    try:
        for _, employee in employees_df.iterrows():
            # Calculate salary with standard deductions (10%)
            basic_salary = employee['basic_salary']
            deductions = basic_salary * 0.1
            net_salary = basic_salary - deductions
            
            c.execute('''
                INSERT OR REPLACE INTO salary_records 
                (employee_id, salary_month, basic_salary, deductions, net_salary, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee['employee_id'], salary_month, basic_salary, deductions, net_salary, 'Generated'))
            
            # Add to ledger
            add_ledger_entry((
                employee['employee_id'],
                salary_month,
                f'Salary for {salary_month.strftime("%B %Y")}',
                'Salary',
                net_salary,
                f'SAL-{salary_month.strftime("%Y%m")}'
            ))
        
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error generating salary records: {str(e)}")
        return False
    finally:
        conn.close()

def get_salary_records(salary_month=None):
    conn = get_connection()
    query = '''
        SELECT sr.*, e.name, e.designation, e.department, e.bank_account, e.account_title, e.bank_name
        FROM salary_records sr
        JOIN employees e ON sr.employee_id = e.employee_id
        WHERE 1=1
    '''
    params = []
    
    if salary_month:
        query += ' AND sr.salary_month = ?'
        params.append(salary_month)
    
    query += ' ORDER BY e.name'
    
    df = pd.read_sql(query, conn, params=params)
    conn.close()
    return df

# PDF Generation Class
class PDFGenerator(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Nutrion HR & Expense Management System', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 8, 'DataNex Solution - Streamlit Web Application', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(3)
    
    def add_table(self, headers, data, col_widths):
        self.set_font('Arial', 'B', 10)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 10, header, 1, 0, 'C')
        self.ln()
        
        self.set_font('Arial', '', 8)
        for row in data:
            for i, item in enumerate(row):
                self.cell(col_widths[i], 10, str(item), 1, 0, 'L')
            self.ln()

# Main Application
def main():
    st.markdown('<div class="main-header">🏢 Nutrion HR & Expense Management System</div>', unsafe_allow_html=True)
    
    # Horizontal navigation menu
    with st.sidebar:
        selected = option_menu(
            menu_title="Main Menu",
            options=["Dashboard", "Employee Management", "Payroll Management", "Expense Management", "Reports & Analytics", "Data Import/Export"],
            icons=["house", "people", "cash-coin", "receipt", "graph-up", "cloud-arrow-down"],
            menu_icon="cast",
            default_index=0,
            styles={
                "container": {"padding": "5px", "background-color": "#f8f9fa"},
                "icon": {"color": "orange", "font-size": "18px"}, 
                "nav-link": {"font-size": "16px", "text-align": "left", "margin":"0px", "--hover-color": "#eee"},
                "nav-link-selected": {"background-color": "#1f77b4"},
            }
        )
    
    if selected == "Dashboard":
        show_dashboard()
    elif selected == "Employee Management":
        show_employee_management()
    elif selected == "Payroll Management":
        show_payroll_management()
    elif selected == "Expense Management":
        show_expense_management()
    elif selected == "Reports & Analytics":
        show_reports_analytics()
    elif selected == "Data Import/Export":
        show_data_import_export()

def show_dashboard():
    st.markdown('<div class="section-header">📊 Dashboard Overview</div>', unsafe_allow_html=True)
    
    # Get statistics
    employees_df = get_employees()
    total_employees = len(employees_df)
    total_salary = employees_df['basic_salary'].sum() if not employees_df.empty else 0
    
    expenses_df = get_company_expenses()
    total_expenses = expenses_df['amount'].sum() if not expenses_df.empty else 0
    
    # Monthly expenses
    current_month = date.today().replace(day=1)
    monthly_expenses_df = get_company_expenses(current_month, date.today())
    monthly_expenses = monthly_expenses_df['amount'].sum() if not monthly_expenses_df.empty else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">{total_employees}</div>
                <div class="metric-label">Total Employees</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">${total_salary:,.0f}</div>
                <div class="metric-label">Monthly Salary Budget</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">${total_expenses:,.0f}</div>
                <div class="metric-label">Total Expenses</div>
            </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        st.markdown(f'''
            <div class="metric-card">
                <div class="metric-value">${monthly_expenses:,.0f}</div>
                <div class="metric-label">This Month Expenses</div>
            </div>
        ''', unsafe_allow_html=True)
    
    # Charts and recent activities
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="sub-header">📈 Department-wise Employee Distribution</div>', unsafe_allow_html=True)
        if not employees_df.empty:
            dept_counts = employees_df['department'].value_counts()
            fig = px.pie(values=dept_counts.values, names=dept_counts.index, 
                        title="Employees by Department")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No employee data available")
    
    with col2:
        st.markdown('<div class="sub-header">💰 Expense Distribution by Category</div>', unsafe_allow_html=True)
        if not expenses_df.empty:
            category_expenses = expenses_df.groupby('category_name')['amount'].sum()
            fig = px.bar(x=category_expenses.values, y=category_expenses.index, 
                        orientation='h', title="Expenses by Category")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available")
    
    # Recent Activities
    st.markdown('<div class="sub-header">🕒 Recent Activities</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Recent Employees**")
        if not employees_df.empty:
            recent_employees = employees_df.head(5)[['name', 'designation', 'department']]
            st.dataframe(recent_employees, use_container_width=True)
        else:
            st.info("No employees found")
    
    with col2:
        st.markdown("**Recent Expenses**")
        if not expenses_df.empty:
            recent_expenses = expenses_df.head(5)[['expense_date', 'description', 'amount', 'category_name']]
            st.dataframe(recent_expenses, use_container_width=True)
        else:
            st.info("No expenses found")

def show_employee_management():
    st.markdown('<div class="section-header">👥 Employee Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Add Employee", "View Employees", "Update Employee", "Delete Employee", "Employee Ledger"])
    
    with tab1:
        st.markdown('<div class="sub-header">➕ Add New Employee</div>', unsafe_allow_html=True)
        with st.form("add_employee_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                employee_id = st.text_input("Employee ID*", placeholder="EMP001")
                name = st.text_input("Full Name*", placeholder="John Doe")
                designation = st.text_input("Designation*", placeholder="Software Engineer")
                department = st.selectbox("Department*", ["HR", "Finance", "IT", "Sales", "Marketing", "Operations", "Management"])
                
            with col2:
                bank_account = st.text_input("Bank Account Number*", placeholder="1234567890")
                account_title = st.text_input("Account Title*", placeholder="John Doe")
                bank_name = st.text_input("Bank Name*", placeholder="ABC Bank")
                basic_salary = st.number_input("Basic Salary*", min_value=0.0, step=100.0, value=3000.0)
                joining_date = st.date_input("Joining Date*", value=date.today())
            
            submitted = st.form_submit_button("Add Employee", type="primary")
            if submitted:
                if all([employee_id, name, designation, bank_account, account_title, bank_name, basic_salary]):
                    employee_data = (employee_id, name, designation, department, bank_account, 
                                   account_title, bank_name, basic_salary, joining_date)
                    if add_employee(employee_data):
                        st.success("✅ Employee added successfully!")
                else:
                    st.error("❌ Please fill all required fields!")
    
    with tab2:
        st.markdown('<div class="sub-header">📋 Employee List</div>', unsafe_allow_html=True)
        employees_df = get_employees()
        if not employees_df.empty:
            # Display key information
            display_df = employees_df[['employee_id', 'name', 'designation', 'department', 'basic_salary', 'joining_date']]
            st.dataframe(display_df, use_container_width=True)
            
            # Export option
            if st.button("Export Employee List as CSV"):
                csv = display_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"employees_{date.today()}.csv",
                    mime="text/csv"
                )
        else:
            st.info("ℹ️ No employees found. Add some employees to get started.")
    
    with tab3:
        st.markdown('<div class="sub-header">✏️ Update Employee</div>', unsafe_allow_html=True)
        employees_df = get_employees()
        if not employees_df.empty:
            employee_to_update = st.selectbox("Select Employee to Update", 
                                            employees_df['employee_id'].tolist(),
                                            format_func=lambda x: f"{x} - {employees_df[employees_df['employee_id'] == x]['name'].iloc[0]}")
            
            employee_data = employees_df[employees_df['employee_id'] == employee_to_update].iloc[0]
            
            with st.form("update_employee_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    update_name = st.text_input("Full Name*", value=employee_data['name'])
                    update_designation = st.text_input("Designation*", value=employee_data['designation'])
                    update_department = st.selectbox("Department", 
                                                   ["HR", "Finance", "IT", "Sales", "Marketing", "Operations", "Management"],
                                                   index=["HR", "Finance", "IT", "Sales", "Marketing", "Operations", "Management"].index(employee_data['department']))
                    
                with col2:
                    update_bank_account = st.text_input("Bank Account Number*", value=employee_data['bank_account'])
                    update_account_title = st.text_input("Account Title*", value=employee_data['account_title'])
                    update_bank_name = st.text_input("Bank Name*", value=employee_data['bank_name'])
                    update_basic_salary = st.number_input("Basic Salary*", min_value=0.0, step=100.0, 
                                                        value=float(employee_data['basic_salary']))
                
                submitted = st.form_submit_button("Update Employee", type="primary")
                if submitted:
                    update_data = (update_name, update_designation, update_department, update_bank_account,
                                 update_account_title, update_bank_name, update_basic_salary)
                    if update_employee(employee_to_update, update_data):
                        st.success("✅ Employee updated successfully!")
        else:
            st.info("ℹ️ No employees available to update.")
    
    with tab4:
        st.markdown('<div class="sub-header">🗑️ Delete Employee</div>', unsafe_allow_html=True)
        employees_df = get_employees()
        if not employees_df.empty:
            employee_to_delete = st.selectbox("Select Employee to Delete", 
                                            employees_df['employee_id'].tolist(),
                                            format_func=lambda x: f"{x} - {employees_df[employees_df['employee_id'] == x]['name'].iloc[0]}",
                                            key="delete_select")
            
            if st.button("Delete Employee", type="primary"):
                if delete_employee(employee_to_delete):
                    st.success("✅ Employee deleted successfully!")
                    st.rerun()
        else:
            st.info("ℹ️ No employees available to delete.")
    
    with tab5:
        st.markdown('<div class="sub-header">📒 Employee Ledger</div>', unsafe_allow_html=True)
        employees_df = get_employees()
        if not employees_df.empty:
            selected_employee = st.selectbox("Select Employee", 
                                           employees_df['employee_id'].tolist(),
                                           format_func=lambda x: f"{x} - {employees_df[employees_df['employee_id'] == x]['name'].iloc[0]}",
                                           key="ledger_select")
            
            ledger_df = get_employee_ledger(selected_employee)
            if not ledger_df.empty:
                st.dataframe(ledger_df[['transaction_date', 'description', 'transaction_type', 'amount', 'balance']], 
                           use_container_width=True)
                
                # Add new ledger entry
                with st.expander("Add Ledger Entry"):
                    with st.form("add_ledger_entry"):
                        col1, col2 = st.columns(2)
                        with col1:
                            entry_date = st.date_input("Transaction Date", value=date.today())
                            entry_type = st.selectbox("Transaction Type", ["Salary", "Expense", "Reimbursement", "Deduction", "Other"])
                        with col2:
                            entry_amount = st.number_input("Amount", min_value=0.0, step=100.0)
                            entry_description = st.text_input("Description")
                        
                        submitted = st.form_submit_button("Add Entry", type="primary")
                        if submitted:
                            if entry_description and entry_amount > 0:
                                if add_ledger_entry((selected_employee, entry_date, entry_description, entry_type, entry_amount, "")):
                                    st.success("✅ Ledger entry added successfully!")
                                    st.rerun()
                            else:
                                st.error("❌ Please fill all fields!")
            else:
                st.info("ℹ️ No ledger entries found for this employee.")
        else:
            st.info("ℹ️ No employees available.")

def show_payroll_management():
    st.markdown('<div class="section-header">💰 Payroll Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Generate Salary Sheet", "Individual Salary Slip", "Salary Records"])
    
    with tab1:
        st.markdown('<div class="sub-header">📊 Generate Salary Sheet</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            salary_month = st.date_input("Salary Month", value=date.today().replace(day=1), key="salary_month")
        with col2:
            include_deductions = st.checkbox("Include Standard Deductions (10%)", value=True)
        
        if st.button("Generate Salary Sheet", type="primary"):
            employees_df = get_employees()
            if not employees_df.empty:
                # Calculate salary sheet
                salary_sheet = employees_df.copy()
                if include_deductions:
                    salary_sheet['deductions'] = salary_sheet['basic_salary'] * 0.1
                else:
                    salary_sheet['deductions'] = 0
                
                salary_sheet['net_salary'] = salary_sheet['basic_salary'] - salary_sheet['deductions']
                
                st.subheader("Salary Sheet Preview")
                display_columns = ['employee_id', 'name', 'designation', 'bank_account', 
                                 'account_title', 'bank_name', 'basic_salary', 'deductions', 'net_salary']
                st.dataframe(salary_sheet[display_columns], use_container_width=True)
                
                # Save salary records
                if st.button("Save Salary Records", type="secondary"):
                    if generate_salary_records(salary_month, employees_df):
                        st.success("✅ Salary records generated and saved successfully!")
                
                # PDF Export
                st.markdown("---")
                st.subheader("Export Options")
                
                if st.button("Export Salary Sheet as PDF"):
                    pdf = PDFGenerator()
                    pdf.add_page()
                    pdf.chapter_title(f"Salary Sheet - {salary_month.strftime('%B %Y')}")
                    
                    # Add generation date
                    pdf.set_font('Arial', 'I', 10)
                    pdf.cell(0, 8, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 0, 1)
                    pdf.ln(5)
                    
                    # Create table
                    headers = ['Emp ID', 'Name', 'Designation', 'Bank Account', 'Basic Salary', 'Deductions', 'Net Salary']
                    col_widths = [20, 35, 30, 35, 25, 25, 25]
                    
                    data = []
                    for _, row in salary_sheet.iterrows():
                        data.append([
                            str(row['employee_id']),
                            str(row['name']),
                            str(row['designation']),
                            str(row['bank_account']),
                            f"${row['basic_salary']:.2f}",
                            f"${row['deductions']:.2f}",
                            f"${row['net_salary']:.2f}"
                        ])
                    
                    pdf.add_table(headers, data, col_widths)
                    
                    # Add summary
                    pdf.ln(10)
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, f"Total Employees: {len(salary_sheet)}", 0, 1)
                    pdf.cell(0, 10, f"Total Salary: ${salary_sheet['net_salary'].sum():.2f}", 0, 1)
                    
                    pdf_output = pdf.output(dest='S').encode('latin1')
                    st.download_button(
                        label="Download Salary Sheet PDF",
                        data=pdf_output,
                        file_name=f"salary_sheet_{salary_month.strftime('%Y_%m')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            else:
                st.info("ℹ️ No employees found. Please add employees first.")
    
    with tab2:
        st.markdown('<div class="sub-header">🧾 Individual Salary Slip</div>', unsafe_allow_html=True)
        
        employees_df = get_employees()
        if not employees_df.empty:
            selected_employee = st.selectbox("Select Employee", 
                                           employees_df['employee_id'].tolist(),
                                           format_func=lambda x: f"{x} - {employees_df[employees_df['employee_id'] == x]['name'].iloc[0]}",
                                           key="slip_employee")
            slip_month = st.date_input("Salary Month", value=date.today().replace(day=1), key="slip_month")
            
            if st.button("Generate Salary Slip", type="primary"):
                employee_data = employees_df[employees_df['employee_id'] == selected_employee].iloc[0]
                
                # Calculate salary components
                basic_salary = employee_data['basic_salary']
                deductions = basic_salary * 0.1
                net_salary = basic_salary - deductions
                
                # Generate PDF salary slip
                pdf = PDFGenerator()
                pdf.add_page()
                
                pdf.chapter_title("SALARY SLIP")
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, f"Month: {slip_month.strftime('%B %Y')}", 0, 1)
                pdf.ln(5)
                
                # Company and Employee details
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(40, 8, "Company:", 0)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 8, "Nutrion", 0, 1)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(40, 8, "Employee ID:", 0)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 8, str(employee_data['employee_id']), 0, 1)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(40, 8, "Name:", 0)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 8, str(employee_data['name']), 0, 1)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(40, 8, "Designation:", 0)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 8, str(employee_data['designation']), 0, 1)
                
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(40, 8, "Department:", 0)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 8, str(employee_data['department']), 0, 1)
                
                pdf.ln(10)
                
                # Salary breakdown table
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Salary Breakdown", 0, 1)
                pdf.ln(3)
                
                # Earnings
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(100, 8, "Earnings", 1, 0)
                pdf.cell(40, 8, "Amount ($)", 1, 1)
                
                pdf.set_font('Arial', '', 10)
                pdf.cell(100, 8, "Basic Salary", 1, 0)
                pdf.cell(40, 8, f"{basic_salary:.2f}", 1, 1)
                
                # Deductions
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(100, 8, "Deductions", 1, 0)
                pdf.cell(40, 8, "Amount ($)", 1, 1)
                
                pdf.set_font('Arial', '', 10)
                pdf.cell(100, 8, "Tax & Other Deductions", 1, 0)
                pdf.cell(40, 8, f"{deductions:.2f}", 1, 1)
                
                # Net Salary
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(100, 8, "Net Salary Payable", 1, 0)
                pdf.cell(40, 8, f"{net_salary:.2f}", 1, 1)
                
                # Bank details
                pdf.ln(10)
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(0, 8, "Bank Transfer Details:", 0, 1)
                pdf.set_font('Arial', '', 10)
                pdf.cell(0, 8, f"Bank: {employee_data['bank_name']}", 0, 1)
                pdf.cell(0, 8, f"Account: {employee_data['bank_account']} - {employee_data['account_title']}", 0, 1)
                
                pdf_output = pdf.output(dest='S').encode('latin1')
                st.download_button(
                    label="Download Salary Slip PDF",
                    data=pdf_output,
                    file_name=f"salary_slip_{selected_employee}_{slip_month.strftime('%Y_%m')}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
                
                # Display preview
                st.success(f"Salary slip generated for {employee_data['name']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Basic Salary", f"${basic_salary:.2f}")
                with col2:
                    st.metric("Deductions", f"${deductions:.2f}")
                with col3:
                    st.metric("Net Salary", f"${net_salary:.2f}")
        else:
            st.info("ℹ️ No employees found. Please add employees first.")
    
    with tab3:
        st.markdown('<div class="sub-header">📋 Salary Records History</div>', unsafe_allow_html=True)
        
        # Filter by month
        salary_month_filter = st.date_input("Filter by Month", value=date.today().replace(day=1), key="records_month")
        
        salary_records = get_salary_records(salary_month_filter)
        if not salary_records.empty:
            st.dataframe(salary_records[['employee_id', 'name', 'designation', 'basic_salary', 'deductions', 'net_salary', 'status']], 
                       use_container_width=True)
            
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Employees", len(salary_records))
            with col2:
                st.metric("Total Salary", f"${salary_records['net_salary'].sum():.2f}")
            with col3:
                st.metric("Average Salary", f"${salary_records['net_salary'].mean():.2f}")
        else:
            st.info("ℹ️ No salary records found for the selected month.")

def show_expense_management():
    st.markdown('<div class="section-header">💼 Expense Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Expense Categories", "Add Expense", "Expense Reports", "All Expenses"])
    
    with tab1:
        st.markdown('<div class="sub-header">📂 Expense Category Management</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            with st.form("add_category_form", clear_on_submit=True):
                st.subheader("Add New Category")
                category_code = st.text_input("Category Code*", placeholder="TRAVEL")
                category_name = st.text_input("Category Name*", placeholder="Travel Expenses")
                category_description = st.text_area("Description", placeholder="Business travel costs")
                
                submitted = st.form_submit_button("Add Category", type="primary")
                if submitted:
                    if category_code and category_name:
                        if add_expense_category((category_code.upper(), category_name, category_description)):
                            st.success("✅ Category added successfully!")
                            st.rerun()
                    else:
                        st.error("❌ Please fill required fields!")
        
        with col2:
            st.subheader("Existing Categories")
            categories_df = get_expense_categories()
            if not categories_df.empty:
                for _, category in categories_df.iterrows():
                    with st.expander(f"{category['category_code']} - {category['category_name']}"):
                        st.write(f"**Description:** {category['description']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Edit", key=f"edit_{category['id']}"):
                                st.session_state.editing_category = category['id']
                        with col2:
                            if st.button("Delete", key=f"delete_{category['id']}"):
                                if delete_expense_category(category['id']):
                                    st.success("✅ Category deleted successfully!")
                                    st.rerun()
                
                # Export categories as PDF
                st.markdown("---")
                if st.button("Export Categories as PDF", type="secondary"):
                    pdf = PDFGenerator()
                    pdf.add_page()
                    pdf.chapter_title("Expense Categories List")
                    
                    headers = ['Category Code', 'Category Name', 'Description']
                    col_widths = [35, 50, 105]
                    
                    data = []
                    for _, row in categories_df.iterrows():
                        data.append([
                            str(row['category_code']),
                            str(row['category_name']),
                            str(row['description'])
                        ])
                    
                    pdf.add_table(headers, data, col_widths)
                    
                    pdf_output = pdf.output(dest='S').encode('latin1')
                    st.download_button(
                        label="Download Categories PDF",
                        data=pdf_output,
                        file_name="expense_categories.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            else:
                st.info("ℹ️ No expense categories found.")
    
    with tab2:
        st.markdown('<div class="sub-header">➕ Add New Expense</div>', unsafe_allow_html=True)
        
        with st.form("add_expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Expense Date*", value=date.today())
                
                categories_df = get_expense_categories()
                if not categories_df.empty:
                    category_options = {row['id']: f"{row['category_code']} - {row['category_name']}" for _, row in categories_df.iterrows()}
                    selected_category = st.selectbox("Category*", options=list(category_options.keys()), 
                                                   format_func=lambda x: category_options[x])
                else:
                    st.error("No categories available. Please add categories first.")
                    selected_category = None
                
                description = st.text_area("Description*", placeholder="Detailed description of the expense")
            
            with col2:
                amount = st.number_input("Amount*", min_value=0.0, step=10.0, value=0.0)
                
                employees_df = get_employees()
                if not employees_df.empty:
                    employee_options = {row['employee_id']: f"{row['employee_id']} - {row['name']}" for _, row in employees_df.iterrows()}
                    selected_employee = st.selectbox("Employee", options=list(employee_options.keys()), 
                                                   format_func=lambda x: employee_options[x])
                else:
                    selected_employee = None
                
                approved_by = st.text_input("Approved By", placeholder="Manager name")
            
            submitted = st.form_submit_button("Add Expense", type="primary")
            if submitted:
                if selected_category and description and amount > 0:
                    expense_data = (expense_date, selected_category, description, amount, selected_employee, approved_by)
                    if add_company_expense(expense_data):
                        st.success("✅ Expense added successfully!")
                        
                        # If employee is selected, add to their ledger
                        if selected_employee:
                            add_ledger_entry((
                                selected_employee,
                                expense_date,
                                f"Expense: {description}",
                                "Expense",
                                amount,
                                f"EXP-{expense_date.strftime('%Y%m%d')}"
                            ))
                else:
                    st.error("❌ Please fill all required fields!")
    
    with tab3:
        st.markdown('<div class="sub-header">📊 Expense Reports</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", value=date.today())
        
        if st.button("Generate Expense Report", type="primary"):
            expenses_df = get_company_expenses(start_date, end_date)
            
            if not expenses_df.empty:
                # Summary statistics
                total_expenses = expenses_df['amount'].sum()
                avg_expense = expenses_df['amount'].mean()
                expense_count = len(expenses_df)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Expenses", f"${total_expenses:.2f}")
                with col2:
                    st.metric("Number of Expenses", expense_count)
                with col3:
                    st.metric("Average Expense", f"${avg_expense:.2f}")
                with col4:
                    st.metric("Date Range", f"{start_date} to {end_date}")
                
                # Category-wise breakdown
                st.subheader("Category-wise Breakdown")
                category_summary = expenses_df.groupby('category_name')['amount'].agg(['sum', 'count']).reset_index()
                category_summary.columns = ['Category', 'Total Amount', 'Number of Expenses']
                st.dataframe(category_summary, use_container_width=True)
                
                # Charts
                col1, col2 = st.columns(2)
                with col1:
                    fig = px.pie(category_summary, values='Total Amount', names='Category', 
                                title="Expense Distribution by Category")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Monthly trend (if data spans multiple months)
                    expenses_df['month'] = pd.to_datetime(expenses_df['expense_date']).dt.to_period('M')
                    monthly_expenses = expenses_df.groupby('month')['amount'].sum().reset_index()
                    monthly_expenses['month'] = monthly_expenses['month'].astype(str)
                    
                    fig = px.bar(monthly_expenses, x='month', y='amount', 
                                title="Monthly Expense Trend")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Export report
                st.markdown("---")
                st.subheader("Export Report")
                
                if st.button("Export Expense Report as PDF"):
                    pdf = PDFGenerator()
                    pdf.add_page()
                    pdf.chapter_title(f"Expense Report - {start_date} to {end_date}")
                    
                    # Summary
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, "Summary", 0, 1)
                    pdf.set_font('Arial', '', 10)
                    pdf.cell(0, 8, f"Total Expenses: ${total_expenses:.2f}", 0, 1)
                    pdf.cell(0, 8, f"Number of Expenses: {expense_count}", 0, 1)
                    pdf.cell(0, 8, f"Average Expense: ${avg_expense:.2f}", 0, 1)
                    pdf.ln(10)
                    
                    # Category breakdown
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, "Category-wise Breakdown", 0, 1)
                    
                    headers = ['Category', 'Total Amount', 'Count']
                    col_widths = [80, 50, 30]
                    
                    data = []
                    for _, row in category_summary.iterrows():
                        data.append([
                            str(row['Category']),
                            f"${row['Total Amount']:.2f}",
                            str(row['Number of Expenses'])
                        ])
                    
                    pdf.add_table(headers, data, col_widths)
                    
                    pdf_output = pdf.output(dest='S').encode('latin1')
                    st.download_button(
                        label="Download Expense Report PDF",
                        data=pdf_output,
                        file_name=f"expense_report_{start_date}_{end_date}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                
                # Export category-wise details
                st.subheader("Category-wise Detailed Export")
                categories = expenses_df['category_name'].unique()
                selected_category = st.selectbox("Select Category for Detailed Export", categories)
                
                if selected_category:
                    category_expenses = expenses_df[expenses_df['category_name'] == selected_category]
                    csv = category_expenses[['expense_date', 'description', 'amount', 'employee_name']].to_csv(index=False)
                    st.download_button(
                        label=f"Download {selected_category} Expenses CSV",
                        data=csv,
                        file_name=f"{selected_category.lower()}_expenses_{start_date}_{end_date}.csv",
                        mime="text/csv",
                        type="secondary"
                    )
            else:
                st.info("ℹ️ No expenses found for the selected date range.")
    
    with tab4:
        st.markdown('<div class="sub-header">📋 All Expenses</div>', unsafe_allow_html=True)
        
        expenses_df = get_company_expenses()
        if not expenses_df.empty:
            # Filters
            col1, col2, col3 = st.columns(3)
            with col1:
                category_filter = st.selectbox("Filter by Category", ["All"] + list(expenses_df['category_name'].unique()))
            with col2:
                status_filter = st.selectbox("Filter by Status", ["All"] + list(expenses_df['status'].unique()))
            with col3:
                search_term = st.text_input("Search Description")
            
            # Apply filters
            filtered_df = expenses_df.copy()
            if category_filter != "All":
                filtered_df = filtered_df[filtered_df['category_name'] == category_filter]
            if status_filter != "All":
                filtered_df = filtered_df[filtered_df['status'] == status_filter]
            if search_term:
                filtered_df = filtered_df[filtered_df['description'].str.contains(search_term, case=False, na=False)]
            
            st.dataframe(filtered_df[['expense_date', 'category_name', 'description', 'amount', 'employee_name', 'status']], 
                       use_container_width=True)
        else:
            st.info("ℹ️ No expenses recorded yet.")

def show_reports_analytics():
    st.markdown('<div class="section-header">📈 Reports & Analytics</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Monthly Reports", "Analytics Dashboard", "Custom Reports"])
    
    with tab1:
        st.markdown('<div class="sub-header">📅 Monthly Reports</div>', unsafe_allow_html=True)
        
        report_month = st.date_input("Select Month", value=date.today().replace(day=1), key="monthly_report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Generate Monthly Expense Report", type="primary"):
                start_date = report_month.replace(day=1)
                if report_month.month == 12:
                    end_date = report_month.replace(year=report_month.year + 1, month=1, day=1) - timedelta(days=1)
                else:
                    end_date = report_month.replace(month=report_month.month + 1, day=1) - timedelta(days=1)
                
                expenses_df = get_company_expenses(start_date, end_date)
                salary_records = get_salary_records(report_month)
                
                if not expenses_df.empty or not salary_records.empty:
                    # Create comprehensive monthly report
                    pdf = PDFGenerator()
                    pdf.add_page()
                    pdf.chapter_title(f"Monthly Comprehensive Report - {report_month.strftime('%B %Y')}")
                    
                    # Salary Summary
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, "Salary Summary", 0, 1)
                    if not salary_records.empty:
                        total_salary = salary_records['net_salary'].sum()
                        pdf.set_font('Arial', '', 10)
                        pdf.cell(0, 8, f"Total Employees: {len(salary_records)}", 0, 1)
                        pdf.cell(0, 8, f"Total Salary Paid: ${total_salary:.2f}", 0, 1)
                        pdf.cell(0, 8, f"Average Salary: ${salary_records['net_salary'].mean():.2f}", 0, 1)
                    else:
                        pdf.cell(0, 8, "No salary records for this month", 0, 1)
                    pdf.ln(5)
                    
                    # Expense Summary
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, "Expense Summary", 0, 1)
                    if not expenses_df.empty:
                        total_expenses = expenses_df['amount'].sum()
                        pdf.set_font('Arial', '', 10)
                        pdf.cell(0, 8, f"Total Expenses: ${total_expenses:.2f}", 0, 1)
                        pdf.cell(0, 8, f"Number of Expense Entries: {len(expenses_df)}", 0, 1)
                        
                        # Top expense categories
                        category_expenses = expenses_df.groupby('category_name')['amount'].sum().nlargest(5)
                        pdf.cell(0, 8, "Top 5 Expense Categories:", 0, 1)
                        for category, amount in category_expenses.items():
                            pdf.cell(20, 8, "", 0, 0)
                            pdf.cell(0, 8, f"- {category}: ${amount:.2f}", 0, 1)
                    else:
                        pdf.cell(0, 8, "No expenses for this month", 0, 1)
                    
                    pdf_output = pdf.output(dest='S').encode('latin1')
                    st.download_button(
                        label="Download Monthly Report PDF",
                        data=pdf_output,
                        file_name=f"monthly_report_{report_month.strftime('%Y_%m')}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
                else:
                    st.info("ℹ️ No data available for the selected month.")
        
        with col2:
            if st.button("Generate Employee Summary Report", type="secondary"):
                employees_df = get_employees()
                if not employees_df.empty:
                    pdf = PDFGenerator()
                    pdf.add_page()
                    pdf.chapter_title("Employee Summary Report")
                    
                    headers = ['Employee ID', 'Name', 'Designation', 'Department', 'Salary']
                    col_widths = [25, 40, 35, 30, 30]
                    
                    data = []
                    for _, employee in employees_df.iterrows():
                        data.append([
                            str(employee['employee_id']),
                            str(employee['name']),
                            str(employee['designation']),
                            str(employee['department']),
                            f"${employee['basic_salary']:.2f}"
                        ])
                    
                    pdf.add_table(headers, data, col_widths)
                    
                    # Department summary
                    pdf.ln(10)
                    pdf.set_font('Arial', 'B', 12)
                    pdf.cell(0, 10, "Department Summary", 0, 1)
                    
                    dept_summary = employees_df.groupby('department').agg({
                        'employee_id': 'count',
                        'basic_salary': 'sum'
                    }).reset_index()
                    
                    dept_headers = ['Department', 'Employees', 'Total Salary']
                    dept_widths = [50, 30, 40]
                    
                    dept_data = []
                    for _, dept in dept_summary.iterrows():
                        dept_data.append([
                            str(dept['department']),
                            str(dept['employee_id']),
                            f"${dept['basic_salary']:.2f}"
                        ])
                    
                    pdf.add_table(dept_headers, dept_data, dept_widths)
                    
                    pdf_output = pdf.output(dest='S').encode('latin1')
                    st.download_button(
                        label="Download Employee Report PDF",
                        data=pdf_output,
                        file_name="employee_summary_report.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
    
    with tab2:
        st.markdown('<div class="sub-header">📊 Analytics Dashboard</div>', unsafe_allow_html=True)
        
        # Expense analytics
        expenses_df = get_company_expenses()
        employees_df = get_employees()
        
        if not expenses_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Expense trend over time
                expenses_df['month'] = pd.to_datetime(expenses_df['expense_date']).dt.to_period('M')
                monthly_trend = expenses_df.groupby('month')['amount'].sum().reset_index()
                monthly_trend['month'] = monthly_trend['month'].astype(str)
                
                fig = px.line(monthly_trend, x='month', y='amount', 
                            title="Monthly Expense Trend", markers=True)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Category distribution
                category_dist = expenses_df.groupby('category_name')['amount'].sum().reset_index()
                fig = px.pie(category_dist, values='amount', names='category_name',
                           title="Expense Distribution by Category")
                st.plotly_chart(fig, use_container_width=True)
        
        if not employees_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Department distribution
                dept_dist = employees_df['department'].value_counts()
                fig = px.bar(x=dept_dist.values, y=dept_dist.index, orientation='h',
                           title="Employees by Department")
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Salary distribution
                fig = px.histogram(employees_df, x='basic_salary', 
                                 title="Salary Distribution", nbins=10)
                st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        st.markdown('<div class="sub-header">🔍 Custom Reports</div>', unsafe_allow_html=True)
        
        st.info("Custom reporting features will be implemented based on specific business requirements.")

def show_data_import_export():
    st.markdown('<div class="section-header">📤 Data Import/Export</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Import Data", "Export Data", "System Backup"])
    
    with tab1:
        st.markdown('<div class="sub-header">📥 Import Data from Excel</div>', unsafe_allow_html=True)
        
        st.info("""
        **Excel Template Requirements:**
        - File format: .xlsx or .xls
        - First row should contain headers
        - Required columns depend on data type
        """)
        
        import_type = st.selectbox("Select Data Type to Import", 
                                 ["Employees", "Expenses", "Expense Categories"])
        
        uploaded_file = st.file_uploader(f"Choose Excel file for {import_type}", 
                                       type=['xlsx', 'xls'], key="import_file")
        
        if uploaded_file is not None:
            try:
                # Read the Excel file
                excel_data = pd.read_excel(uploaded_file)
                st.success("✅ File uploaded successfully!")
                
                st.subheader("Preview of Uploaded Data")
                st.dataframe(excel_data.head(), use_container_width=True)
                
                # Show import options
                if st.button("Import Data to System", type="primary"):
                    if import_type == "Employees":
                        # Process employee import
                        success_count = 0
                        for _, row in excel_data.iterrows():
                            try:
                                employee_data = (
                                    str(row.get('employee_id', '')),
                                    str(row.get('name', '')),
                                    str(row.get('designation', '')),
                                    str(row.get('department', 'Other')),
                                    str(row.get('bank_account', '')),
                                    str(row.get('account_title', '')),
                                    str(row.get('bank_name', '')),
                                    float(row.get('basic_salary', 0)),
                                    row.get('joining_date', date.today())
                                )
                                if add_employee(employee_data):
                                    success_count += 1
                            except Exception as e:
                                st.error(f"Error importing employee {row.get('employee_id', 'unknown')}: {str(e)}")
                        
                        st.success(f"✅ Successfully imported {success_count} out of {len(excel_data)} employees")
                    
                    elif import_type == "Expenses":
                        # Process expense import
                        success_count = 0
                        categories_df = get_expense_categories()
                        category_map = {row['category_name']: row['id'] for _, row in categories_df.iterrows()}
                        
                        for _, row in excel_data.iterrows():
                            try:
                                category_name = str(row.get('category_name', ''))
                                category_id = category_map.get(category_name)
                                if not category_id:
                                    st.warning(f"Category '{category_name}' not found. Using default.")
                                    category_id = categories_df.iloc[0]['id']
                                
                                expense_data = (
                                    row.get('expense_date', date.today()),
                                    category_id,
                                    str(row.get('description', '')),
                                    float(row.get('amount', 0)),
                                    str(row.get('employee_id', '')),
                                    str(row.get('approved_by', ''))
                                )
                                if add_company_expense(expense_data):
                                    success_count += 1
                            except Exception as e:
                                st.error(f"Error importing expense: {str(e)}")
                        
                        st.success(f"✅ Successfully imported {success_count} out of {len(excel_data)} expenses")
                    
                    elif import_type == "Expense Categories":
                        # Process category import
                        success_count = 0
                        for _, row in excel_data.iterrows():
                            try:
                                category_data = (
                                    str(row.get('category_code', '')).upper(),
                                    str(row.get('category_name', '')),
                                    str(row.get('description', ''))
                                )
                                if add_expense_category(category_data):
                                    success_count += 1
                            except Exception as e:
                                st.error(f"Error importing category: {str(e)}")
                        
                        st.success(f"✅ Successfully imported {success_count} out of {len(excel_data)} categories")
                    
                    st.rerun()
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
        
        # Download templates
        st.markdown("---")
        st.subheader("Download Import Templates")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Employee Template"):
                sample_employees = pd.DataFrame({
                    'employee_id': ['EMP001', 'EMP002'],
                    'name': ['John Doe', 'Jane Smith'],
                    'designation': ['Manager', 'Developer'],
                    'department': ['IT', 'IT'],
                    'bank_account': ['123456789', '987654321'],
                    'account_title': ['John Doe', 'Jane Smith'],
                    'bank_name': ['ABC Bank', 'XYZ Bank'],
                    'basic_salary': [5000.00, 4000.00],
                    'joining_date': [date.today(), date.today()]
                })
                csv = sample_employees.to_csv(index=False)
                st.download_button(
                    label="Download Employee Template",
                    data=csv,
                    file_name="employee_import_template.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Expense Template"):
                sample_expenses = pd.DataFrame({
                    'expense_date': [date.today(), date.today()],
                    'category_name': ['Travel', 'Meals'],
                    'description': ['Client meeting travel', 'Team lunch'],
                    'amount': [250.00, 120.00],
                    'employee_id': ['EMP001', 'EMP002'],
                    'approved_by': ['Manager', 'Manager']
                })
                csv = sample_expenses.to_csv(index=False)
                st.download_button(
                    label="Download Expense Template",
                    data=csv,
                    file_name="expense_import_template.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("Category Template"):
                sample_categories = pd.DataFrame({
                    'category_code': ['TRAVEL', 'MEALS'],
                    'category_name': ['Travel Expenses', 'Meals & Entertainment'],
                    'description': ['Business travel costs', 'Client meals and team entertainment']
                })
                csv = sample_categories.to_csv(index=False)
                st.download_button(
                    label="Download Category Template",
                    data=csv,
                    file_name="category_import_template.csv",
                    mime="text/csv"
                )
    
    with tab2:
        st.markdown('<div class="sub-header">📤 Export Data</div>', unsafe_allow_html=True)
        
        export_options = st.multiselect("Select data to export", 
                                      ["Employees", "Salary Records", "Expenses", "Expense Categories", "Employee Ledgers"])
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today().replace(day=1), key="export_start")
        with col2:
            end_date = st.date_input("End Date", value=date.today(), key="export_end")
        
        if st.button("Generate Export Files", type="primary"):
            if export_options:
                # Create a zip file with all selected exports
                import zipfile
                import io
                
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    
                    if "Employees" in export_options:
                        employees_df = get_employees()
                        if not employees_df.empty:
                            csv_data = employees_df.to_csv(index=False)
                            zip_file.writestr("employees.csv", csv_data)
                    
                    if "Salary Records" in export_options:
                        salary_df = get_salary_records()
                        if not salary_df.empty:
                            # Filter by date range if needed
                            salary_df['salary_month'] = pd.to_datetime(salary_df['salary_month'])
                            filtered_salary = salary_df[
                                (salary_df['salary_month'] >= pd.Timestamp(start_date)) & 
                                (salary_df['salary_month'] <= pd.Timestamp(end_date))
                            ]
                            if not filtered_salary.empty:
                                csv_data = filtered_salary.to_csv(index=False)
                                zip_file.writestr("salary_records.csv", csv_data)
                    
                    if "Expenses" in export_options:
                        expenses_df = get_company_expenses(start_date, end_date)
                        if not expenses_df.empty:
                            csv_data = expenses_df.to_csv(index=False)
                            zip_file.writestr("expenses.csv", csv_data)
                    
                    if "Expense Categories" in export_options:
                        categories_df = get_expense_categories()
                        if not categories_df.empty:
                            csv_data = categories_df.to_csv(index=False)
                            zip_file.writestr("expense_categories.csv", csv_data)
                    
                    if "Employee Ledgers" in export_options:
                        employees_df = get_employees()
                        for _, employee in employees_df.iterrows():
                            ledger_df = get_employee_ledger(employee['employee_id'])
                            if not ledger_df.empty:
                                csv_data = ledger_df.to_csv(index=False)
                                zip_file.writestr(f"ledger_{employee['employee_id']}.csv", csv_data)
                
                zip_buffer.seek(0)
                st.download_button(
                    label="Download All Export Files (ZIP)",
                    data=zip_buffer,
                    file_name=f"hr_export_{date.today()}.zip",
                    mime="application/zip",
                    type="primary"
                )
                
                st.success("✅ Export files generated successfully!")
            else:
                st.error("❌ Please select at least one option to export.")
    
    with tab3:
        st.markdown('<div class="sub-header">💾 System Backup</div>', unsafe_allow_html=True)
        
        st.info("""
        **System Backup Features:**
        - Backup entire database
        - Download backup file
        - Restore from backup (coming soon)
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Create Database Backup", type="primary"):
                # Create a backup of the SQLite database
                backup_data = None
                with open('hr_expense.db', 'rb') as f:
                    backup_data = f.read()
                
                if backup_data:
                    st.download_button(
                        label="Download Database Backup",
                        data=backup_data,
                        file_name=f"hr_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db",
                        mime="application/octet-stream",
                        type="primary"
                    )
                    st.success("✅ Database backup created successfully!")
        
        with col2:
            st.warning("**Restore Feature**")
            st.info("Database restore functionality will be implemented in the next version.")

# Footer
def show_footer():
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col2:
        st.markdown(
            "<div style='text-align: center; color: #666;'>"
            "Developed by <b>DataNex Solution</b> | "
            "Contact: +92320 7429422 | "
            "© 2024 Nutrion HR & Expense Management System"
            "</div>", 
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
    show_footer()
