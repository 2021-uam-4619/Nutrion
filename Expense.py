# Streamlit Simple Employee Management System
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import uuid

# Database setup
DB_NAME = "simple_employee.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Employee Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        designation TEXT,
        phone TEXT,
        salary REAL DEFAULT 0,
        join_date TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Expense Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id TEXT PRIMARY KEY,
        employee_id TEXT NOT NULL,
        expense_date TEXT NOT NULL,
        category TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        created_date TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    );
    """)
    
    conn.commit()
    conn.close()

# Employee Functions
def add_employee(name, designation, phone, salary):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        employee_id = str(uuid.uuid4())
        
        cursor.execute(
            "INSERT INTO employees (id, name, designation, phone, salary) VALUES (?, ?, ?, ?, ?)",
            (employee_id, name, designation, phone, salary)
        )
        conn.commit()
        conn.close()
        return employee_id
    except Exception as e:
        st.error(f"Error adding employee: {e}")
        return None

def get_employees():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
    conn.close()
    return df

def get_employee_by_id(emp_id):
    conn = sqlite3.connect(DB_NAME)
    employee = conn.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()
    conn.close()
    return employee

# Expense Functions
def add_expense(employee_id, expense_date, category, amount, description):
    try:
        conn = sqlite3.connect(DB_NAME)
        expense_id = str(uuid.uuid4())
        
        conn.execute(
            "INSERT INTO expenses (id, employee_id, expense_date, category, amount, description) VALUES (?, ?, ?, ?, ?, ?)",
            (expense_id, employee_id, expense_date.strftime('%Y-%m-%d'), category, amount, description)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error adding expense: {e}")
        return False

def get_employee_expenses(employee_id, start_date, end_date):
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT expense_date, category, description, amount 
    FROM expenses 
    WHERE employee_id = ? AND expense_date BETWEEN ? AND ?
    ORDER BY expense_date
    """
    df = pd.read_sql_query(query, conn, params=(employee_id, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    conn.close()
    return df

def get_monthly_expenses(month_year):
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT e.name, exp.category, SUM(exp.amount) as total_amount
    FROM expenses exp
    JOIN employees e ON exp.employee_id = e.id
    WHERE strftime('%Y-%m', exp.expense_date) = ?
    GROUP BY e.name, exp.category
    ORDER BY e.name, total_amount DESC
    """
    df = pd.read_sql_query(query, conn, params=(month_year,))
    conn.close()
    return df

# Main App
def main():
    st.set_page_config(page_title="Employee Management", layout="wide")
    init_db()
    
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2563eb;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #374151;
        margin-bottom: 1rem;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 0.5rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="main-header">🧑‍💼 Simple Employee Management</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Employee Management", "Expense Ledger", "Monthly Reports"])
    
    if page == "Employee Management":
        show_employee_management()
    elif page == "Expense Ledger":
        show_expense_ledger()
    elif page == "Monthly Reports":
        show_monthly_reports()

def show_employee_management():
    st.markdown('<div class="section-header">👥 Employee Management</div>', unsafe_allow_html=True)
    
    # Add Employee Form
    with st.form("add_employee_form"):
        st.subheader("Add New Employee")
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Employee Name")
            designation = st.text_input("Designation")
        with col2:
            phone = st.text_input("Phone Number")
            salary = st.number_input("Monthly Salary", min_value=0, value=30000)
        
        if st.form_submit_button("Add Employee"):
            if name and designation:
                employee_id = add_employee(name, designation, phone, salary)
                if employee_id:
                    st.success(f"Employee {name} added successfully!")
            else:
                st.error("Please fill all required fields")
    
    st.divider()
    
    # Employee List
    st.subheader("Employee List")
    employees_df = get_employees()
    
    if not employees_df.empty:
        # Display in a nice format
        for _, employee in employees_df.iterrows():
            col1, col2, col3 = st.columns([3, 2, 1])
            
            with col1:
                st.write(f"**{employee['name']}**")
                st.write(f"Designation: {employee['designation']}")
            
            with col2:
                st.write(f"Salary: ₹{employee['salary']:,.2f}")
                if employee['phone']:
                    st.write(f"Phone: {employee['phone']}")
            
            with col3:
                if st.button("View Ledger", key=f"ledger_{employee['id']}"):
                    st.session_state.selected_employee = employee['id']
                    st.session_state.page = "Expense Ledger"
                    st.rerun()
            
            st.divider()
    else:
        st.info("No employees found. Add your first employee above.")

def show_expense_ledger():
    st.markdown('<div class="section-header">💰 Expense Ledger</div>', unsafe_allow_html=True)
    
    employees_df = get_employees()
    
    if employees_df.empty:
        st.info("No employees found. Please add employees first.")
        return
    
    # Employee Selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        employee_options = {row['id']: row['name'] for _, row in employees_df.iterrows()}
        selected_employee_id = st.selectbox(
            "Select Employee",
            options=list(employee_options.keys()),
            format_func=lambda x: employee_options[x]
        )
    
    with col2:
        selected_employee = get_employee_by_id(selected_employee_id)
        if selected_employee:
            st.metric("Current Salary", f"₹{selected_employee[4]:,.2f}")
    
    # Add Expense Form
    with st.form("add_expense_form"):
        st.subheader("Add Expense/Deduction")
        col1, col2 = st.columns(2)
        
        with col1:
            expense_date = st.date_input("Date", value=date.today())
            amount = st.number_input("Amount", min_value=1.0, step=100.0)
        
        with col2:
            category = st.selectbox("Category", [
                "Salary Advance", "Loan Deduction", "Fine", "Insurance", 
                "Tax Deduction", "Other Deduction", "Bonus", "Increment"
            ])
            description = st.text_input("Description")
        
        if st.form_submit_button("Add Expense"):
            if amount > 0 and description:
                if add_expense(selected_employee_id, expense_date, category, amount, description):
                    st.success("Expense added successfully!")
            else:
                st.error("Please fill all required fields")
    
    st.divider()
    
    # Expense History
    st.subheader("Expense History")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=date.today().replace(day=1))
    with col2:
        end_date = st.date_input("To Date", value=date.today())
    
    expenses_df = get_employee_expenses(selected_employee_id, start_date, end_date)
    
    if not expenses_df.empty:
        total_expenses = expenses_df['amount'].sum()
        remaining_salary = selected_employee[4] - total_expenses
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Salary", f"₹{selected_employee[4]:,.2f}")
        col2.metric("Total Deductions", f"₹{total_expenses:,.2f}")
        col3.metric("Net Payable", f"₹{remaining_salary:,.2f}", 
                   delta=f"-{total_expenses:,.2f}" if total_expenses > 0 else None)
        
        # Display expenses
        for _, expense in expenses_df.iterrows():
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                st.write(f"**{expense['expense_date']}**")
                st.write(f"*{expense['category']}*")
            
            with col2:
                st.write(expense['description'])
            
            with col3:
                st.write(f"**₹{expense['amount']:,.2f}**")
            
            st.divider()
    else:
        st.info("No expenses found for this period.")

def show_monthly_reports():
    st.markdown('<div class="section-header">📊 Monthly Reports</div>', unsafe_allow_html=True)
    
    # Month Selection
    current_year = datetime.now().year
    months = [
        f"{current_year}-01", f"{current_year}-02", f"{current_year}-03", f"{current_year}-04",
        f"{current_year}-05", f"{current_year}-06", f"{current_year}-07", f"{current_year}-08", 
        f"{current_year}-09", f"{current_year}-10", f"{current_year}-11", f"{current_year}-12"
    ]
    month_names = {
        f"{current_year}-01": "January", f"{current_year}-02": "February", f"{current_year}-03": "March",
        f"{current_year}-04": "April", f"{current_year}-05": "May", f"{current_year}-06": "June",
        f"{current_year}-07": "July", f"{current_year}-08": "August", f"{current_year}-09": "September",
        f"{current_year}-10": "October", f"{current_year}-11": "November", f"{current_year}-12": "December"
    }
    
    selected_month = st.selectbox("Select Month", options=months, format_func=lambda x: month_names[x])
    
    # Generate Report
    if st.button("Generate Monthly Report"):
        expenses_df = get_monthly_expenses(selected_month)
        
        if not expenses_df.empty:
            st.subheader(f"Monthly Expense Report - {month_names[selected_month]} {current_year}")
            
            # Summary by Employee
            st.write("### Summary by Employee")
            employee_summary = expenses_df.groupby('name')['total_amount'].sum().reset_index()
            
            for _, employee in employee_summary.iterrows():
                st.write(f"**{employee['name']}**: ₹{employee['total_amount']:,.2f}")
            
            st.divider()
            
            # Detailed Breakdown
            st.write("### Detailed Breakdown")
            
            for employee_name in expenses_df['name'].unique():
                st.write(f"#### {employee_name}")
                employee_expenses = expenses_df[expenses_df['name'] == employee_name]
                
                for _, expense in employee_expenses.iterrows():
                    col1, col2 = st.columns([3, 2])
                    with col1:
                        st.write(f"{expense['category']}")
                    with col2:
                        st.write(f"₹{expense['total_amount']:,.2f}")
                
                st.divider()
            
            # Download as CSV
            csv = expenses_df.to_csv(index=False)
            st.download_button(
                label="Download CSV Report",
                data=csv,
                file_name=f"monthly_report_{selected_month}.csv",
                mime="text/csv"
            )
            
        else:
            st.info(f"No expenses found for {month_names[selected_month]} {current_year}")

if __name__ == "__main__":
    main()
