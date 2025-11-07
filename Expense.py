import streamlit as st
import sqlite3
import pandas as pd
from fpdf import FPDF
from datetime import datetime, date

# --- CONFIGURATION ---
# Define the expense categories from your list
EXPENSE_CATEGORIES = [
    "Guard", "Labour", "Bilty Expenses", "Office Rent", "Warehouse Rent", 
    "Muhammad Asim Iqbal Salary", "Import Export", "Office Electricity", "FBR", 
    "Abdul Manan Sb Salary", "Office Entertainment", "PSID", "Advance", 
    "Commission", "Office Stationery Expense", "Employee Expenses", "Other Expense", 
    "Company Expense", "Muhammad Abdullah Salary"
]
DB_NAME = "enterprise_data.db"

# --- DATABASE SETUP ---

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
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
        bank_details TEXT,
        salary REAL DEFAULT 0
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
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE SET NULL
    );
    """)
    
    conn.commit()
    conn.close()

# --- EMPLOYEE CRUD FUNCTIONS ---

def add_employee(name, designation, bank_details, salary):
    """Adds a new employee to the database."""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO employees (name, designation, bank_details, salary) VALUES (?, ?, ?, ?)",
            (name, designation, bank_details, salary)
        )
        conn.commit()
        conn.close()
        st.success(f"Successfully added employee: {name}")
    except Exception as e:
        st.error(f"Error adding employee: {e}")

def get_employees():
    """Fetches all employees as a Pandas DataFrame."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    return df

def update_employee(emp_id, name, designation, bank_details, salary):
    """Updates an existing employee's details."""
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE employees SET name = ?, designation = ?, bank_details = ?, salary = ? WHERE id = ?",
            (name, designation, bank_details, salary, emp_id)
        )
        conn.commit()
        conn.close()
        st.success(f"Successfully updated employee: {name}")
    except Exception as e:
        st.error(f"Error updating employee: {e}")

def delete_employee(emp_id):
    """Deletes an employee from the database."""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
        conn.commit()
        conn.close()
        st.success("Successfully deleted employee.")
    except Exception as e:
        st.error(f"Error deleting employee: {e}")

def get_employee_names():
    """Gets a list of employee names and their IDs."""
    conn = get_db_connection()
    employees = conn.execute("SELECT id, name FROM employees").fetchall()
    conn.close()
    # Create a dictionary {id: name}
    return {emp['id']: emp['name'] for emp in employees}

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
        st.success("Successfully added expense.")
    except Exception as e:
        st.error(f"Error adding expense: {e}")

def get_expenses(start_date, end_date):
    """Fetches all expenses within a date range as a DataFrame."""
    conn = get_db_connection()
    query = """
    SELECT e.id, e.expense_date, e.category, e.amount, e.description, 
           IFNULL(emp.name, 'N/A') as employee_name
    FROM expenses e
    LEFT JOIN employees emp ON e.employee_id = emp.id
    WHERE e.expense_date BETWEEN ? AND ?
    ORDER BY e.expense_date DESC
    """
    df = pd.read_sql_query(query, conn, params=(start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')))
    conn.close()
    return df

def delete_expense(expense_id):
    """Deletes an expense from the database."""
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()
        st.success("Successfully deleted expense.")
    except Exception as e:
        st.error(f"Error deleting expense: {e}")

# --- PDF REPORTING FUNCTIONS ---

class PDF(FPDF):
    """Custom PDF class to handle headers and footers."""
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.title, 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def create_salary_slip_pdf(employee, report_month_year):
    """Generates a salary slip PDF for an employee."""
    pdf = PDF()
    pdf.title = f'Salary Slip for {report_month_year}'
    pdf.add_page()
    pdf.set_font('Arial', '', 12)
    
    pdf.cell(50, 10, 'Employee Name:', 0, 0)
    pdf.cell(0, 10, employee['name'], 0, 1)
    
    pdf.cell(50, 10, 'Designation:', 0, 0)
    pdf.cell(0, 10, employee['designation'], 0, 1)
    
    pdf.cell(50, 10, 'Bank Details:', 0, 0)
    pdf.cell(0, 10, employee['bank_details'], 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    
    pdf.cell(50, 10, 'Description', 1, 0)
    pdf.cell(0, 10, 'Amount (PKR)', 1, 1, 'R')
    
    pdf.set_font('Arial', '', 12)
    pdf.cell(50, 10, 'Monthly Salary', 1, 0)
    pdf.cell(0, 10, f"{employee['salary']:,.2f}", 1, 1, 'R')
    
    # You can add deductions or bonuses here
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(50, 10, 'Total Salary', 1, 0)
    pdf.cell(0, 10, f"{employee['salary']:,.2f}", 1, 1, 'R')
    
    # Return as bytes for download
    return pdf.output(dest='S').encode('latin-1')

def create_expense_report_pdf(start_date, end_date):
    """Generates a PDF report for all expenses in a date range."""
    df = get_expenses(start_date, end_date)
    
    pdf = PDF()
    pdf.title = f'Expense Report ({start_date} to {end_date})'
    pdf.add_page(orientation='L') # Landscape
    pdf.set_font('Arial', '', 10)
    
    # Table Header
    col_widths = [15, 30, 50, 30, 110, 30] # Adjust widths as needed
    headers = ['ID', 'Date', 'Category', 'Amount', 'Description', 'Employee']
    
    pdf.set_font('Arial', 'B', 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()

    # Table Rows
    pdf.set_font('Arial', '', 9)
    if df.empty:
        pdf.cell(sum(col_widths), 10, 'No expenses found for this period.', 1, 1, 'C')
    else:
        for _, row in df.iterrows():
            pdf.cell(col_widths[0], 10, str(row['id']), 1, 0)
            pdf.cell(col_widths[1], 10, row['expense_date'], 1, 0)
            pdf.cell(col_widths[2], 10, row['category'], 1, 0)
            pdf.cell(col_widths[3], 10, f"{row['amount']:,.2f}", 1, 0, 'R')
            pdf.cell(col_widths[4], 10, str(row['description'])[:60], 1, 0) # Truncate description
            pdf.cell(col_widths[5], 10, row['employee_name'], 1, 1)
    
    # Total
    total_expenses = df['amount'].sum()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(sum(col_widths[:-2]), 10, 'Total Expenses:', 1, 0, 'R')
    pdf.cell(col_widths[-2] + col_widths[-1], 10, f'PKR {total_expenses:,.2f}', 1, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1')


# --- UI PAGES ---

def page_dashboard():
    """Main dashboard page."""
    st.title("🏠 Dashboard")
    st.write("Welcome to your Enterprise Management System.")

    # Get data for metrics
    today = date.today()
    start_of_month = today.replace(day=1)
    
    employees_df = get_employees()
    expenses_df = get_expenses(start_of_month, today)
    
    total_employees = len(employees_df)
    total_salary_payroll = employees_df['salary'].sum()
    monthly_expenses = expenses_df['amount'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Employees", f"{total_employees}")
    col2.metric("Total Monthly Payroll", f"PKR {total_salary_payroll:,.2f}")
    col3.metric("Expenses (This Month)", f"PKR {monthly_expenses:,.2f}")

    st.subheader("Monthly Expenses by Category")
    if not expenses_df.empty:
        category_summary = expenses_df.groupby('category')['amount'].sum().sort_values(ascending=False)
        st.bar_chart(category_summary)
    else:
        st.info("No expenses logged this month.")


def page_employee_management():
    """Page for managing employees (CRUD)."""
    st.title("🧑‍💼 Employee Management")
    
    # --- Add New Employee ---
    st.header("Add New Employee")
    with st.form("add_employee_form", clear_on_submit=True):
        name = st.text_input("Name", placeholder="e.g., Muhammad Asim Iqbal")
        designation = st.text_input("Designation", placeholder="e.g., Manager")
        bank_details = st.text_input("Bank Details", placeholder="e.g., Bank Al-Falah, 0123-...")
        salary = st.number_input("Monthly Salary (PKR)", min_value=0.0, step=1000.0)
        
        submitted = st.form_submit_button("Add Employee")
        if submitted and name:
            add_employee(name, designation, bank_details, salary)
        elif submitted:
            st.warning("Please provide an employee name.")
            
    st.divider()

    # --- View and Edit/Delete Employees ---
    st.header("Manage Existing Employees")
    employees_df = get_employees()
    
    if employees_df.empty:
        st.info("No employees found. Add one using the form above.")
        return

    st.dataframe(employees_df, use_container_width=True)

    # --- Edit / Delete Section ---
    employee_list = employees_df['name'].tolist()
    # Add a blank option to avoid auto-selecting
    selected_name = st.selectbox("Select Employee to Edit or Delete", [""] + employee_list)

    if selected_name:
        selected_emp = employees_df[employees_df['name'] == selected_name].iloc[0]
        emp_id = int(selected_emp['id']) # Ensure ID is Python int

        col1, col2 = st.columns([2, 1])

        with col1:
            st.subheader(f"Edit {selected_name}")
            with st.form(f"edit_form_{emp_id}"):
                # Pre-fill form with existing data
                name = st.text_input("Name", value=selected_emp['name'])
                designation = st.text_input("Designation", value=selected_emp['designation'])
                bank_details = st.text_input("Bank Details", value=selected_emp['bank_details'])
                salary = st.number_input("Monthly Salary (PKR)", value=float(selected_emp['salary']), min_value=0.0, step=1000.0)
                
                updated = st.form_submit_button("Update Employee")
                if updated:
                    update_employee(emp_id, name, designation, bank_details, salary)
                    st.rerun() # Refresh the page to show changes

        with col2:
            st.subheader(f"Delete {selected_name}")
            st.warning("This action is permanent.")
            if st.button("Delete Employee", type="primary", key=f"delete_{emp_id}"):
                delete_employee(emp_id)
                st.rerun() # Refresh the page


def page_expense_management():
    """Page for managing expenses (CRUD)."""
    st.title("💸 Expense Management")

    # --- Add New Expense ---
    st.header("Add New Expense")
    
    # Get employee names for dropdown
    emp_names_dict = get_employee_names()
    # Create a list for the selectbox: [(id, name), ...]
    # Add a "None" option
    emp_options = [(None, "N/A (General Expense)")] + list(emp_names_dict.items())

    with st.form("add_expense_form", clear_on_submit=True):
        expense_date = st.date_input("Expense Date", value=datetime.today())
        category = st.selectbox("Category", EXPENSE_CATEGORIES)
        amount = st.number_input("Amount (PKR)", min_value=0.01, step=10.0)
        
        # Use format_func to display names, but pass ID as the value
        selected_employee = st.selectbox(
            "Link to Employee (Optional)", 
            options=[opt[0] for opt in emp_options], # Pass IDs
            format_func=lambda x: dict(emp_options).get(x, "N/A") # Show names
        )
        
        description = st.text_area("Description (Optional)")
        
        submitted = st.form_submit_button("Add Expense")
        if submitted:
            add_expense(expense_date, category, amount, description, selected_employee)

    st.divider()

    # --- View and Delete Expenses ---
    st.header("Manage Existing Expenses")
    
    col1, col2 = st.columns(2)
    today = datetime.today()
    start_of_month = today.replace(day=1)
    
    with col1:
        start_date = st.date_input("Start Date", value=start_of_month)
    with col2:
        end_date = st.date_input("End Date", value=today)

    expenses_df = get_expenses(start_date, end_date)
    st.dataframe(expenses_df, use_container_width=True)

    if not expenses_df.empty:
        # --- Delete Section ---
        expense_ids = expenses_df['id'].tolist()
        selected_id = st.selectbox("Select Expense ID to Delete", [""] + expense_ids)

        if selected_id:
            if st.button("Delete Selected Expense", type="primary", key=f"delete_exp_{selected_id}"):
                delete_expense(selected_id)
                st.rerun()
    else:
        st.info("No expenses found for the selected period.")


def page_reports_and_ledgers():
    """Page for generating reports."""
    st.title("📊 Reports & Ledgers")

    # --- Monthly Expense Report ---
    st.header("Monthly Expense Report")
    st.write("Generate a PDF report of all expenses for a selected period.")
    
    col1, col2 = st.columns(2)
    today = datetime.today()
    start_of_month = today.replace(day=1)
    with col1:
        report_start_date = st.date_input("Report Start Date", value=start_of_month, key="rep_start")
    with col2:
        report_end_date = st.date_input("Report End Date", value=today, key="rep_end")

    if st.button("Generate Expense Report"):
        pdf_data = create_expense_report_pdf(report_start_date, report_end_date)
        st.download_button(
            label="Download PDF Report",
            data=pdf_data,
            file_name=f"Expense_Report_{report_start_date}_to_{report_end_date}.pdf",
            mime="application/pdf"
        )
        
    st.divider()

    # --- Employee Ledger / Salary Slip ---
    st.header("Generate Salary Slip")
    st.write("Generate a professional PDF salary slip for an employee.")
    
    emp_names_dict = get_employee_names()
    if not emp_names_dict:
        st.warning("No employees found. Please add an employee first.", icon="🧑‍💼")
        return
        
    emp_options = list(emp_names_dict.items())
    selected_emp_id = st.selectbox(
        "Select Employee", 
        options=[opt[0] for opt in emp_options],
        format_func=lambda x: emp_names_dict.get(x)
    )
    
    report_month = st.date_input("Select Month/Year for Report", value=datetime.today(), format="YYYY-MM")
    report_month_year = report_month.strftime("%B %Y")
    
    if st.button("Generate Salary Slip"):
        # Fetch the selected employee's full details
        conn = get_db_connection()
        employee_data = conn.execute("SELECT * FROM employees WHERE id = ?", (selected_emp_id,)).fetchone()
        conn.close()
        
        if employee_data:
            pdf_data = create_salary_slip_pdf(employee_data, report_month_year)
            st.download_button(
                label="Download Salary Slip",
                data=pdf_data,
                file_name=f"Salary_Slip_{employee_data['name']}_{report_month.strftime('%Y_%m')}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Could not find employee data.")

def page_data_import():
    """Page for importing data from CSV/Excel."""
    st.title("📥 Data Import")

    # --- Import Employees ---
    st.header("Import Employees")
    st.write("Upload a CSV or Excel file with employee data.")
    st.info("""
    **Required Format:**
    - `name` (text)
    - `designation` (text)
    - `bank_details` (text)
    - `salary` (number)
    """)
    
    uploaded_file = st.file_uploader("Choose an Employee file", type=["csv", "xlsx"], key="emp_uploader")
    
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write("**File Preview:**")
            st.dataframe(df.head())
            
            if st.button("Import Employees"):
                conn = get_db_connection()
                with st.spinner("Importing..."):
                    for _, row in df.iterrows():
                        conn.execute(
                            "INSERT INTO employees (name, designation, bank_details, salary) VALUES (?, ?, ?, ?)",
                            (row['name'], row['designation'], row['bank_details'], row['salary'])
                        )
                    conn.commit()
                conn.close()
                st.success(f"Successfully imported {len(df)} employees!")
                
        except Exception as e:
            st.error(f"An error occurred during import: {e}")

    # --- Import Expenses (Similar logic) ---
    st.header("Import Expenses")
    st.write("Upload a CSV or Excel file with expense data.")
    st.info("""
    **Required Format:**
    - `expense_date` (YYYY-MM-DD)
    - `category` (must match one of the predefined categories)
    - `amount` (number)
    - `description` (text, optional)
    - `employee_id` (number, optional - must match an ID in the employees table)
    """)
    
    uploaded_expense_file = st.file_uploader("Choose an Expense file", type=["csv", "xlsx"], key="exp_uploader")
    
    if uploaded_expense_file:
        try:
            if uploaded_expense_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_expense_file)
            else:
                df = pd.read_excel(uploaded_expense_file)
            
            st.write("**File Preview:**")
            st.dataframe(df.head())
            
            if st.button("Import Expenses"):
                conn = get_db_connection()
                with st.spinner("Importing..."):
                    for _, row in df.iterrows():
                        # Basic validation
                        if row['category'] not in EXPENSE_CATEGORIES:
                            st.warning(f"Skipping row: Category '{row['category']}' not found.")
                            continue
                        
                        conn.execute(
                            "INSERT INTO expenses (expense_date, category, amount, description, employee_id) VALUES (?, ?, ?, ?, ?)",
                            (row['expense_date'], row['category'], row['amount'], 
                             row.get('description'), row.get('employee_id'))
                        )
                    conn.commit()
                conn.close()
                st.success(f"Successfully imported expenses!")
                
        except Exception as e:
            st.error(f"An error occurred during import: {e}")


# --- MAIN APP ---

def main():
    """Main function to run the Streamlit app."""
    st.set_page_config(page_title="Enterprise Management", layout="wide")
    
    # Initialize the database
    init_db()

    # Sidebar Navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["🏠 Dashboard", "🧑‍💼 Employee Management", "💸 Expense Management", "📊 Reports & Ledgers", "📥 Data Import"]
    )

    # Page routing
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "🧑‍💼 Employee Management":
        page_employee_management()
    elif page == "💸 Expense Management":
        page_expense_management()
    elif page == "📊 Reports & Ledgers":
        page_reports_and_ledgers()
    elif page == "📥 Data Import":
        page_data_import()

if __name__ == "__main__":
    main()
