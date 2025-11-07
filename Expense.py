import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, date
import tempfile
import os
from fpdf import FPDF
import io
import traceback

# Page configuration
st.set_page_config(
    page_title="💰 Company Management System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup with error handling
def init_db():
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        c = conn.cursor()
        
        # Expenses table
        c.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Employees table
        c.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                bank_account TEXT,
                bank_name TEXT,
                designation TEXT,
                salary REAL NOT NULL,
                join_date TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Salary payments table
        c.execute('''
            CREATE TABLE IF NOT EXISTS salary_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id INTEGER,
                amount REAL NOT NULL,
                payment_date TEXT NOT NULL,
                month_year TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")
        return False

# Initialize database
if not init_db():
    st.error("Failed to initialize database. Please check the error above.")

# Expense categories
EXPENSE_CATEGORIES = [
    "Guard", "Labour", "Bilty Expenses", "Office Rent", "Warehouse Rent",
    "Muhammad Asim Iqbal Salary", "Import Export", "Office Electricity", "FBR",
    "Abdul Manan Sb Salary", "Office Entertainment", "PSID", "Advance",
    "Commission", "Office Stationery Expense", "Employee Expenses", "Other Expense",
    "Company Expense", "Muhammad Abdullah Salary"
]

# Professional PDF Generator Class
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 51, 102)  # Dark blue color
        self.cell(0, 10, 'COMPANY MANAGEMENT SYSTEM', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.set_text_color(128, 128, 128)
        self.cell(0, 5, 'Professional Business Report', 0, 1, 'C')
        self.ln(8)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} - Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 51, 102)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 10, title, 0, 1, 'L', 1)
        self.ln(3)
    
    def chapter_body(self, data, headers, col_widths=None):
        self.set_font('Arial', '', 10)
        
        # Calculate column widths if not provided
        if col_widths is None:
            col_widths = [self.w / len(headers)] * len(headers)
        
        # Headers with background
        self.set_font('Arial', 'B', 10)
        self.set_fill_color(220, 220, 220)
        for i, header in enumerate(headers):
            self.cell(col_widths[i], 8, header, 1, 0, 'C', 1)
        self.ln()
        
        # Data rows
        self.set_font('Arial', '', 9)
        fill = False
        for row_idx, row in enumerate(data):
            self.set_fill_color(245, 245, 245) if fill else self.set_fill_color(255, 255, 255)
            for i, item in enumerate(row):
                self.cell(col_widths[i], 7, str(item), 1, 0, 'C', int(fill))
            self.ln()
            fill = not fill

# Database functions with error handling
def add_expense(category, amount, date, description):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            INSERT INTO expenses (category, amount, date, description)
            VALUES (?, ?, ?, ?)
        ''', (category, amount, date, description))
        conn.commit()
        conn.close()
        return True, "Expense added successfully!"
    except Exception as e:
        return False, f"Error adding expense: {str(e)}"

def get_expenses(month=None, year=None):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        df = pd.read_sql_query('''
            SELECT * FROM expenses 
            ORDER BY date DESC
        ''', conn)
        conn.close()
        
        if not df.empty and month and year:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df[(df['date'].dt.month == month) & (df['date'].dt.year == year)]
        
        return df
    except Exception as e:
        st.error(f"Error fetching expenses: {str(e)}")
        return pd.DataFrame()

def update_expense(expense_id, category, amount, date, description):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            UPDATE expenses 
            SET category=?, amount=?, date=?, description=?
            WHERE id=?
        ''', (category, amount, date, description, expense_id))
        conn.commit()
        conn.close()
        return True, "Expense updated successfully!"
    except Exception as e:
        return False, f"Error updating expense: {str(e)}"

def delete_expense(expense_id):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
        conn.commit()
        conn.close()
        return True, "Expense deleted successfully!"
    except Exception as e:
        return False, f"Error deleting expense: {str(e)}"

def add_employee(name, bank_account, bank_name, designation, salary, join_date):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            INSERT INTO employees (name, bank_account, bank_name, designation, salary, join_date)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, bank_account, bank_name, designation, salary, join_date))
        conn.commit()
        conn.close()
        return True, "Employee added successfully!"
    except Exception as e:
        return False, f"Error adding employee: {str(e)}"

def get_employees():
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        df = pd.read_sql_query('SELECT * FROM employees ORDER BY name', conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error fetching employees: {str(e)}")
        return pd.DataFrame()

def update_employee(emp_id, name, bank_account, bank_name, designation, salary, join_date):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            UPDATE employees 
            SET name=?, bank_account=?, bank_name=?, designation=?, salary=?, join_date=?
            WHERE id=?
        ''', (name, bank_account, bank_name, designation, salary, join_date, emp_id))
        conn.commit()
        conn.close()
        return True, "Employee updated successfully!"
    except Exception as e:
        return False, f"Error updating employee: {str(e)}"

def delete_employee(emp_id):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('DELETE FROM employees WHERE id=?', (emp_id,))
        conn.commit()
        conn.close()
        return True, "Employee deleted successfully!"
    except Exception as e:
        return False, f"Error deleting employee: {str(e)}"

def record_salary_payment(employee_id, amount, payment_date, month_year):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        c = conn.cursor()
        c.execute('''
            INSERT INTO salary_payments (employee_id, amount, payment_date, month_year)
            VALUES (?, ?, ?, ?)
        ''', (employee_id, amount, payment_date, month_year))
        conn.commit()
        conn.close()
        return True, "Salary payment recorded successfully!"
    except Exception as e:
        return False, f"Error recording salary payment: {str(e)}"

def get_salary_payments(month=None, year=None):
    try:
        conn = sqlite3.connect('company_data.db', check_same_thread=False)
        query = '''
            SELECT sp.*, e.name, e.designation 
            FROM salary_payments sp
            JOIN employees e ON sp.employee_id = e.id
        '''
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if not df.empty and month and year:
            df['payment_date'] = pd.to_datetime(df['payment_date'], errors='coerce')
            df = df[(df['payment_date'].dt.month == month) & (df['payment_date'].dt.year == year)]
        
        return df
    except Exception as e:
        st.error(f"Error fetching salary payments: {str(e)}")
        return pd.DataFrame()

# Custom CSS for professional look
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f3d7a;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        color: #2e5b9b;
        border-bottom: 2px solid #2e5b9b;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        color: #721c24;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2e5b9b;
    }
</style>
""", unsafe_allow_html=True)

# Main App
def main():
    st.markdown('<h1 class="main-header">💰 Company Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🧭 Navigation")
        app_mode = st.radio("Choose Module", 
            ["📊 Dashboard", "💵 Expense Management", "👥 Employee Management", "📈 Reports & Analytics"])
        
        st.markdown("---")
        st.markdown("### 📊 Quick Stats")
        
        # Quick stats
        try:
            expenses_df = get_expenses()
            employees_df = get_employees()
            
            if not expenses_df.empty:
                current_month = datetime.now().month
                current_year = datetime.now().year
                monthly_expenses = expenses_df[
                    (pd.to_datetime(expenses_df['date']).dt.month == current_month) &
                    (pd.to_datetime(expenses_df['date']).dt.year == current_year)
                ]['amount'].sum()
                st.metric("💰 Monthly Expenses", f"₹{monthly_expenses:,.2f}")
            
            if not employees_df.empty:
                total_salary = employees_df['salary'].sum()
                st.metric("👥 Total Employees", len(employees_df))
                st.metric("💸 Monthly Salary", f"₹{total_salary:,.2f}")
        except:
            pass

    if app_mode == "📊 Dashboard":
        dashboard()
    elif app_mode == "💵 Expense Management":
        expense_management()
    elif app_mode == "👥 Employee Management":
        employee_management()
    elif app_mode == "📈 Reports & Analytics":
        reports_analytics()

def dashboard():
    st.markdown('<h2 class="section-header">📊 Dashboard Overview</h2>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 💰 Financial Summary")
        expenses_df = get_expenses()
        if not expenses_df.empty:
            total_expenses = expenses_df['amount'].sum()
            current_month_expenses = expenses_df[
                pd.to_datetime(expenses_df['date']).dt.month == datetime.now().month
            ]['amount'].sum()
            
            st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
            st.metric("Current Month", f"₹{current_month_expenses:,.2f}")
    
    with col2:
        st.markdown("### 👥 Employee Summary")
        employees_df = get_employees()
        if not employees_df.empty:
            total_salary = employees_df['salary'].sum()
            st.metric("Total Employees", len(employees_df))
            st.metric("Monthly Salary", f"₹{total_salary:,.2f}")
    
    with col3:
        st.markdown("### 📈 Recent Activity")
        st.info("""
        - **Expense Management**: Add, edit, delete expenses
        - **Employee Management**: Manage employee records
        - **Reports**: Generate professional PDF reports
        - **Data Import/Export**: CSV support available
        """)

def expense_management():
    st.markdown('<h2 class="section-header">💵 Expense Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ➕ Add New Expense")
        
        with st.form("expense_form", clear_on_submit=True):
            category = st.selectbox("Category", EXPENSE_CATEGORIES, key="category_select")
            amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0, format="%.2f")
            expense_date = st.date_input("Date", value=date.today())
            description = st.text_area("Description", placeholder="Enter expense details...")
            
            submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)
            if submitted:
                if amount > 0:
                    success, message = add_expense(
                        category, 
                        amount, 
                        expense_date.strftime('%Y-%m-%d'), 
                        description
                    )
                    if success:
                        st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-box">Please enter a valid amount</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📋 Expense Records")
        
        # Filter options
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_month = st.selectbox("Filter Month", 
                ["All"] + list(range(1, 13)), key="exp_month")
        with col_f2:
            current_year = datetime.now().year
            filter_year = st.selectbox("Filter Year", 
                ["All"] + list(range(current_year-2, current_year+1)), key="exp_year")
        with col_f3:
            st.write("")  # Spacer
            if st.button("🔄 Refresh Data", use_container_width=True):
                st.rerun()
        
        expenses_df = get_expenses()
        
        if not expenses_df.empty:
            # Convert date column
            expenses_df['date'] = pd.to_datetime(expenses_df['date'], errors='coerce')
            
            # Apply filters
            if filter_month != "All":
                expenses_df = expenses_df[expenses_df['date'].dt.month == filter_month]
            if filter_year != "All":
                expenses_df = expenses_df[expenses_df['date'].dt.year == filter_year]
            
            # Display expenses
            display_df = expenses_df[['id', 'category', 'amount', 'date', 'description']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
            
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Edit/Delete section
            st.markdown("### ✏️ Edit/Delete Expense")
            expense_ids = expenses_df['id'].tolist()
            if expense_ids:
                selected_id = st.selectbox("Select Expense ID to Modify", expense_ids, key="expense_edit")
                
                if selected_id:
                    selected_expense = expenses_df[expenses_df['id'] == selected_id].iloc[0]
                    
                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        with st.form("edit_expense"):
                            st.write("#### Edit Expense")
                            edit_category = st.selectbox("Category", EXPENSE_CATEGORIES, 
                                                       index=EXPENSE_CATEGORIES.index(selected_expense['category']), 
                                                       key="edit_category")
                            edit_amount = st.number_input("Amount", value=float(selected_expense['amount']), 
                                                         step=100.0, format="%.2f", key="edit_amount")
                            edit_date = st.date_input("Date", 
                                                    value=selected_expense['date'].to_pydatetime(), 
                                                    key="edit_date")
                            edit_description = st.text_area("Description", 
                                                          value=selected_expense['description'] or "", 
                                                          key="edit_desc")
                            
                            update_clicked = st.form_submit_button("🔄 Update Expense", use_container_width=True)
                            if update_clicked:
                                success, message = update_expense(
                                    selected_id, edit_category, edit_amount, 
                                    edit_date.strftime('%Y-%m-%d'), edit_description
                                )
                                if success:
                                    st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
                                    st.rerun()
                                else:
                                    st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)
                    
                    with col_e2:
                        st.markdown("#### ❌ Delete Expense")
                        st.markdown(f"""
                        <div class="metric-card">
                            <b>Category:</b> {selected_expense['category']}<br>
                            <b>Amount:</b> ₹{selected_expense['amount']:,.2f}<br>
                            <b>Date:</b> {selected_expense['date'].strftime('%Y-%m-%d')}<br>
                            <b>Description:</b> {selected_expense['description'] or 'N/A'}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🗑️ Delete Expense", use_container_width=True, type="secondary"):
                            success, message = delete_expense(selected_id)
                            if success:
                                st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
                                st.rerun()
                            else:
                                st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)
            else:
                st.info("No expenses to edit.")
        else:
            st.info("📝 No expenses recorded yet. Start by adding your first expense above.")

def employee_management():
    st.markdown('<h2 class="section-header">👥 Employee Management</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("### ➕ Add New Employee")
        
        with st.form("employee_form", clear_on_submit=True):
            name = st.text_input("Full Name *", placeholder="Enter employee full name")
            bank_account = st.text_input("Bank Account Number", placeholder="Account number")
            bank_name = st.text_input("Bank Name", placeholder="Bank name")
            designation = st.text_input("Designation", placeholder="Job title")
            salary = st.number_input("Monthly Salary (₹) *", min_value=0.0, step=1000.0, format="%.2f")
            join_date = st.date_input("Join Date", value=date.today())
            
            submitted = st.form_submit_button("💾 Add Employee", use_container_width=True)
            if submitted:
                if name and salary > 0:
                    success, message = add_employee(name, bank_account, bank_name, designation, salary, 
                                   join_date.strftime('%Y-%m-%d'))
                    if success:
                        st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="error-box">Please fill all required fields (*)</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown("### 📋 Employee Records")
        
        employees_df = get_employees()
        
        if not employees_df.empty:
            display_df = employees_df[['id', 'name', 'designation', 'salary', 'join_date', 'bank_name']].copy()
            display_df['salary'] = display_df['salary'].apply(lambda x: f"₹{x:,.2f}")
            st.dataframe(display_df, use_container_width=True, height=400)
            
            # Edit/Delete section
            st.markdown("### ✏️ Edit/Delete Employee")
            emp_ids = employees_df['id'].tolist()
            if emp_ids:
                selected_emp_id = st.selectbox("Select Employee ID to Modify", emp_ids, key="emp_edit")
                
                if selected_emp_id:
                    selected_emp = employees_df[employees_df['id'] == selected_emp_id].iloc[0]
                    
                    col_emp1, col_emp2 = st.columns(2)
                    with col_emp1:
                        with st.form("edit_employee"):
                            st.write("#### Edit Employee")
                            edit_name = st.text_input("Full Name", value=selected_emp['name'], key="edit_name")
                            edit_bank_account = st.text_input("Bank Account", value=selected_emp['bank_account'] or "", key="edit_bank_acc")
                            edit_bank_name = st.text_input("Bank Name", value=selected_emp['bank_name'] or "", key="edit_bank_name")
                            edit_designation = st.text_input("Designation", value=selected_emp['designation'] or "", key="edit_designation")
                            edit_salary = st.number_input("Salary", value=float(selected_emp['salary']), step=1000.0, format="%.2f", key="edit_salary")
                            edit_join_date = st.date_input("Join Date", 
                                                         value=datetime.strptime(selected_emp['join_date'], '%Y-%m-%d'), 
                                                         key="edit_join_date")
                            
                            update_clicked = st.form_submit_button("🔄 Update Employee", use_container_width=True)
                            if update_clicked:
                                success, message = update_employee(selected_emp_id, edit_name, edit_bank_account, 
                                              edit_bank_name, edit_designation, edit_salary,
                                              edit_join_date.strftime('%Y-%m-%d'))
                                if success:
                                    st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
                                    st.rerun()
                                else:
                                    st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)
                    
                    with col_emp2:
                        st.markdown("#### ❌ Delete Employee")
                        st.markdown(f"""
                        <div class="metric-card">
                            <b>Name:</b> {selected_emp['name']}<br>
                            <b>Designation:</b> {selected_emp['designation'] or 'N/A'}<br>
                            <b>Salary:</b> ₹{selected_emp['salary']:,.2f}<br>
                            <b>Join Date:</b> {selected_emp['join_date']}<br>
                            <b>Bank:</b> {selected_emp['bank_name'] or 'N/A'}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button("🗑️ Delete Employee", use_container_width=True, type="secondary"):
                            success, message = delete_employee(selected_emp_id)
                            if success:
                                st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
                                st.rerun()
                            else:
                                st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)
            
            # Salary Payment Section
            st.markdown("### 💸 Record Salary Payment")
            with st.form("salary_payment"):
                emp_for_payment = st.selectbox("Select Employee", 
                                             employees_df['name'].tolist(), key="salary_emp")
                payment_amount = st.number_input("Payment Amount (₹)", min_value=0.0, step=1000.0, format="%.2f")
                payment_date = st.date_input("Payment Date", value=date.today())
                payment_month = st.selectbox("For Month", 
                                           [f"{datetime.now().year}-{i:02d}" for i in range(1, 13)])
                
                pay_clicked = st.form_submit_button("💳 Record Salary Payment", use_container_width=True)
                if pay_clicked:
                    selected_emp_id = employees_df[employees_df['name'] == emp_for_payment].iloc[0]['id']
                    success, message = record_salary_payment(selected_emp_id, payment_amount, 
                                        payment_date.strftime('%Y-%m-%d'), payment_month)
                    if success:
                        st.markdown(f'<div class="success-box">{message}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="error-box">{message}</div>', unsafe_allow_html=True)
        else:
            st.info("👥 No employees added yet. Start by adding your first employee above.")

# [Rest of the code for reports_analytics and other functions remains the same...]

def reports_analytics():
    st.markdown('<h2 class="section-header">📊 Reports & Analytics</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Expense Reports", "👥 Employee Reports", "💰 Salary Ledger", "📁 Data Import/Export"])
    
    with tab1:
        st.markdown("### 📈 Expense Reports")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            report_month = st.selectbox("Select Month", list(range(1, 13)), key="rep_month")
        with col_r2:
            current_year = datetime.now().year
            report_year = st.selectbox("Select Year", 
                                     list(range(current_year-2, current_year+1)), key="rep_year")
        
        expenses_df = get_expenses(report_month, report_year)
        
        if not expenses_df.empty:
            # Summary
            total_expenses = expenses_df['amount'].sum()
            category_summary = expenses_df.groupby('category')['amount'].sum().reset_index()
            category_summary = category_summary.sort_values('amount', ascending=False)
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.metric("💰 Total Expenses", f"₹{total_expenses:,.2f}")
                st.markdown("#### 📋 Category Summary")
                st.dataframe(category_summary, use_container_width=True)
            
            with col_s2:
                st.markdown("#### 📊 Expense Distribution")
                st.bar_chart(category_summary.set_index('category'))
            
            # Generate PDF
            if st.button("📄 Generate Expense PDF Report", use_container_width=True):
                pdf = PDFReport()
                pdf.add_page()
                
                pdf.chapter_title(f"Expense Report - {report_month}/{report_year}")
                
                # Prepare data for PDF
                pdf_data = []
                headers = ['ID', 'Category', 'Amount', 'Date', 'Description']
                col_widths = [15, 40, 30, 25, 80]
                
                for _, row in expenses_df.iterrows():
                    pdf_data.append([
                        row['id'],
                        row['category'],
                        f"₹{row['amount']:,.2f}",
                        row['date'],
                        row['description'] or '-'
                    ])
                
                pdf.chapter_body(pdf_data, headers, col_widths)
                
                # Summary
                pdf.ln(10)
                pdf.chapter_title("Summary")
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, f'Total Expenses: ₹{total_expenses:,.2f}', 0, 1)
                pdf.cell(0, 10, f'Number of Expenses: {len(expenses_df)}', 0, 1)
                
                # Save to bytes
                pdf_output = pdf.output(dest='S').encode('latin1')
                
                st.download_button(
                    label="📥 Download Expense PDF",
                    data=pdf_output,
                    file_name=f"expense_report_{report_year}_{report_month:02d}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
        
        else:
            st.info("No expenses found for the selected period.")
    
    with tab2:
        st.markdown("### 👥 Employee Reports")
        
        employees_df = get_employees()
        
        if not employees_df.empty:
            total_salary = employees_df['salary'].sum()
            active_employees = len(employees_df)
            
            col_emp1, col_emp2, col_emp3 = st.columns(3)
            with col_emp1:
                st.metric("Total Employees", active_employees)
            with col_emp2:
                st.metric("Total Monthly Salary", f"₹{total_salary:,.2f}")
            with col_emp3:
                avg_salary = total_salary / active_employees if active_employees > 0 else 0
                st.metric("Average Salary", f"₹{avg_salary:,.2f}")
            
            st.dataframe(employees_df, use_container_width=True)
            
            # Generate Salary Slip
            st.markdown("### 🎫 Generate Salary Slip")
            selected_emp_slip = st.selectbox("Select Employee", 
                                           employees_df['name'].tolist(), key="slip_emp")
            slip_month = st.selectbox("Select Month", 
                                    [f"{datetime.now().year}-{i:02d}" for i in range(1, 13)], key="slip_month")
            
            if st.button("📄 Generate Salary Slip", use_container_width=True):
                emp_data = employees_df[employees_df['name'] == selected_emp_slip].iloc[0]
                
                pdf = PDFReport()
                pdf.add_page()
                
                # Salary Slip Header
                pdf.set_font('Arial', 'B', 18)
                pdf.set_text_color(0, 51, 102)
                pdf.cell(0, 15, 'SALARY SLIP', 0, 1, 'C')
                pdf.set_font('Arial', 'I', 12)
                pdf.set_text_color(128, 128, 128)
                pdf.cell(0, 8, f'For the month of {slip_month}', 0, 1, 'C')
                pdf.ln(10)
                
                # Employee Details
                pdf.set_font('Arial', 'B', 12)
                pdf.set_text_color(0, 51, 102)
                pdf.cell(0, 10, 'Employee Details', 0, 1)
                pdf.set_font('Arial', '', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 7, f'Name: {emp_data["name"]}', 0, 1)
                pdf.cell(0, 7, f'Designation: {emp_data["designation"] or "N/A"}', 0, 1)
                pdf.cell(0, 7, f'Bank: {emp_data["bank_name"] or "N/A"}', 0, 1)
                pdf.cell(0, 7, f'Account: {emp_data["bank_account"] or "N/A"}', 0, 1)
                pdf.ln(8)
                
                # Salary Details
                pdf.set_font('Arial', 'B', 12)
                pdf.set_text_color(0, 51, 102)
                pdf.cell(0, 10, 'Salary Details', 0, 1)
                pdf.set_font('Arial', '', 11)
                pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 7, f'Basic Salary: ₹{emp_data["salary"]:,.2f}', 0, 1)
                pdf.cell(0, 7, f'Total Amount: ₹{emp_data["salary"]:,.2f}', 0, 1)
                pdf.ln(10)
                
                pdf.set_font('Arial', 'I', 10)
                pdf.set_text_color(128, 128, 128)
                pdf.cell(0, 8, 'Generated on: ' + datetime.now().strftime('%Y-%m-%d %H:%M'), 0, 1)
                
                pdf_output = pdf.output(dest='S').encode('latin1')
                
                st.download_button(
                    label="📥 Download Salary Slip",
                    data=pdf_output,
                    file_name=f"salary_slip_{emp_data['name'].replace(' ', '_')}_{slip_month}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    
    with tab3:
        st.markdown("### 💰 Salary Ledger")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            ledger_month = st.selectbox("Select Month", list(range(1, 13)), key="led_month")
        with col_l2:
            ledger_year = st.selectbox("Select Year", 
                                     list(range(current_year-2, current_year+1)), key="led_year")
        
        salary_payments = get_salary_payments(ledger_month, ledger_year)
        
        if not salary_payments.empty:
            total_paid = salary_payments['amount'].sum()
            
            st.metric("Total Salary Paid", f"₹{total_paid:,.2f}")
            st.dataframe(salary_payments, use_container_width=True)
        else:
            st.info("No salary payments recorded for the selected period.")
    
    with tab4:
        st.markdown("### 📁 Data Import/Export")
        
        col_io1, col_io2 = st.columns(2)
        
        with col_io1:
            st.markdown("#### 📤 Export Data")
            
            export_type = st.selectbox("Select Data to Export", 
                                     ["Expenses", "Employees", "Salary Payments"])
            
            if st.button("📥 Export to CSV", use_container_width=True):
                if export_type == "Expenses":
                    data = get_expenses()
                elif export_type == "Employees":
                    data = get_employees()
                else:
                    data = get_salary_payments()
                
                if not data.empty:
                    csv = data.to_csv(index=False)
                    st.download_button(
                        label="💾 Download CSV",
                        data=csv,
                        file_name=f"{export_type.lower()}_export.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.warning(f"No {export_type.lower()} data to export.")
        
        with col_io2:
            st.markdown("#### 📥 Import Data")
            
            import_type = st.selectbox("Select Data to Import", 
                                     ["Expenses", "Employees"], key="import_type")
            
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'], key="file_uploader")
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.success(f"✅ File loaded successfully! {len(df)} records found.")
                    st.write("Preview of data to import:")
                    st.dataframe(df.head(), use_container_width=True)
                    
                    if st.button("🚀 Import Data", use_container_width=True):
                        # This is a basic implementation - you might want to add more validation
                        conn = sqlite3.connect('company_data.db', check_same_thread=False)
                        if import_type == "Expenses":
                            df.to_sql('expenses', conn, if_exists='append', index=False)
                        else:
                            df.to_sql('employees', conn, if_exists='append', index=False)
                        conn.close()
                        st.success("✅ Data imported successfully!")
                except Exception as e:
                    st.error(f"❌ Error importing data: {str(e)}")

if __name__ == "__main__":
    main()
