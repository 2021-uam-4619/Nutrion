# Nutrion HR & Expense Management System
# Developer: DataNex Solution
# Contact: +92320 7429422
#
# This is a single-file version combining all modules.
#
# To run:
# 1. Save this file (e.g., app.py)
# 2. Install dependencies:
#    pip install streamlit pandas openpyxl fpdf2
# 3. Run the app:
#    streamlit run app.py

import streamlit as st
import sqlite3
import pandas as pd
import os
import datetime
from fpdf import FPDF
from io import BytesIO

# --- Constants ---
DB_NAME = "hr_app.db"

# ==============================================================================
# --- DATABASE UTILITIES (from db_utils.py) ---
# ==============================================================================

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def create_tables():
    """Creates all necessary tables for the application if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # P-102, HR-201: Employee Information
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        designation TEXT,
        base_salary REAL DEFAULT 0,
        account_number TEXT,
        account_title TEXT,
        bank_name TEXT
    );
    """)

    # EX-302: Expense Categories
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    );
    """)

    # EX-301: Monthly Company Expenses
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date DATE NOT NULL,
        category_id INTEGER,
        description TEXT,
        amount REAL NOT NULL,
        FOREIGN KEY (category_id) REFERENCES expense_categories (id)
    );
    """)

    # HR-204: Employee-Added Expense Claims (Separate Ledger)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        date DATE NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'Pending',  -- Pending, Approved, Reimbursed, Rejected
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
    );
    """)

    # HR-203, HR-204: Employee Ledger (tracks all money flow)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        date DATE NOT NULL,
        description TEXT,
        debit REAL DEFAULT 0,  -- Money paid TO employee (Salary, Reimbursement)
        credit REAL DEFAULT 0, -- Money owed BY employee (Deduction, Advance)
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
    );
    """)

    conn.commit()
    conn.close()

# --- DASHBOARD STATS ---
def get_employee_count():
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
    conn.close()
    return count

def get_pending_claims_count():
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM employee_claims WHERE status = 'Pending'").fetchone()[0]
    conn.close()
    return count

def get_category_count():
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(*) FROM expense_categories").fetchone()[0]
    conn.close()
    return count

# --- EMPLOYEE CRUD (P-102) ---

def add_employee(name, designation, base_salary, acc_num, acc_title, bank):
    """Adds a new employee to the database."""
    conn = get_db_connection()
    conn.execute("""
        INSERT INTO employees (name, designation, base_salary, account_number, account_title, bank_name)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (name, designation, base_salary, acc_num, acc_title, bank))
    conn.commit()
    conn.close()

def update_employee(id, name, designation, base_salary, acc_num, acc_title, bank):
    """Updates an existing employee's details."""
    conn = get_db_connection()
    conn.execute("""
        UPDATE employees
        SET name = ?, designation = ?, base_salary = ?, account_number = ?, account_title = ?, bank_name = ?
        WHERE id = ?
    """, (name, designation, base_salary, acc_num, acc_title, bank, id))
    conn.commit()
    conn.close()

def delete_employee(id):
    """Deletes an employee from the database."""
    conn = get_db_connection()
    # Using ON DELETE CASCADE, related claims and ledger entries will also be deleted.
    conn.execute("DELETE FROM employees WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def get_all_employees():
    """Fetches all employees as a Pandas DataFrame."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM employees", conn)
    conn.close()
    return df

def get_employee_by_id(id):
    """Fetches a single employee's details by their ID."""
    conn = get_db_connection()
    employee = conn.execute("SELECT * FROM employees WHERE id = ?", (id,)).fetchone()
    conn.close()
    return employee # Returns a sqlite3.Row object (dict-like)

# --- (TO-DO) ---
# Add CRUD functions for:
# - expense_categories
# - company_expenses
# - employee_claims
# - employee_ledger

# ==============================================================================
# --- PDF UTILITIES (from pdf_utils.py) ---
# ==============================================================================

class PDF(FPDF):
    """
    Custom PDF class to handle headers and footers for reports.
    """
    def header(self):
        # Logo or Title
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Nutrion Ltd. - Confidential Report', 0, 1, 'C')
        self.set_font('Arial', '', 8)
        self.cell(0, 5, f'Generated on: {datetime.date.today()}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        # Page number
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_pdf_report(data_df, title):
    """
    A stub function to generate a PDF from a Pandas DataFrame.
    This needs to be significantly expanded.
    """
    st.write(f"--- STUB: Generating PDF for '{title}' ---")
    st.dataframe(data_df)
    st.write("--- END STUB ---")
    
    # --- Example of actual FPDF logic (to be built) ---
    # pdf = PDF()
    # pdf.add_page()
    # pdf.set_font("Arial", size=16)
    # pdf.cell(200, 10, txt=title, ln=True, align='C')
    #
    # # Add table headers
    # pdf.set_font("Arial", 'B', 10)
    # for col in data_df.columns:
    #     pdf.cell(40, 10, col, 1, 0, 'C')
    # pdf.ln()
    #
    # # Add table rows
    # pdf.set_font("Arial", '', 10)
    # for index, row in data_df.iterrows():
    #     for col in data_df.columns:
    #         pdf.cell(40, 10, str(row[col]), 1, 0, 'L')
    #     pdf.ln()
    #
    # # Save the PDF to a byte buffer
    # from io import BytesIO
    # pdf_bytes = pdf.output(dest='S').encode('latin-1')
    # return pdf_bytes
    
    st.error("PDF generation logic (DOC-401) is not yet implemented.")
    return None

# ==============================================================================
# --- PAGE DEFINITIONS (from app.py and pages/) ---
# ==============================================================================

# --- PAGE 1: Dashboard (from app.py) ---
def show_dashboard():
    st.title("Welcome to the Nutrion HR & Expense Portal")
    st.header("Dashboard Overview")

    # Get some quick stats
    try:
        total_employees = get_employee_count()
        pending_claims = get_pending_claims_count()
        total_categories = get_category_count()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Employees", total_employees)
        col2.metric("Pending Expense Claims", pending_claims)
        col3.metric("Expense Categories", total_categories)

        st.info("Select a module from the sidebar on the left to begin.")

        st.header("Developer To-Do List")
        st.markdown("""
            This is the foundational code. Here are the next steps based on the project plan:
            -   **Employee Management**:
                -   Add PDF export button for individual salary slip (HR-202) using `generate_pdf_report`.
            -   **Employee Ledgers**:
                -   Build UI for `employee_claims` (Add/Approve/Reimburse) (HR-204).
                -   Build UI to view `employee_ledger` (HR-203).
                -   **Logic (HR-204):** When a claim is "Reimbursed", add a 'Debit' entry to the `employee_ledger`.
            -   **Company Expenses**:
                -   Build CRUD for `expense_categories` (EX-302).
                -   Build CRUD for `company_expenses` (EX-301).
                -   Add "Download Category Sheet" button (EX-302).
            -   **Reports**:
                -   Build Salary Sheet Generator (HR-201).
                -   Build Monthly Company Expense Report (EX-301).
                -   Build Categorized Expense Download (EX-303).
                -   Ensure all have date-range filters (DOC-402) and use `generate_pdf_report` (DOC-401).
            -   **Data Import**:
                -   Implement `pandas` logic to read uploaded Excel and insert data into tables (P-103).
            -   **PDF Generation**:
                -   Implement the actual PDF generation logic in `generate_pdf_report`.
        """)

    except Exception as e:
        st.error(f"Error connecting to database. Please ensure 'hr_app.db' is writable. \nError: {e}")
        if not os.path.exists("hr_app.db"):
            st.warning("Database file 'hr_app.db' not found. It should be created automatically.")

# --- PAGE 2: Employees (from pages/1_Employees.py) ---
def show_employees():
    st.title("👥 Employee Management")
    st.write("Manage employee details, salary, and bank information (P-102).")

    # --- Tabs for CRUD Operations ---
    tab1, tab2, tab3 = st.tabs(["View All Employees", "Add New Employee", "Update/Delete Employee"])

    # --- TAB 1: View All Employees (R in CRUD) ---
    with tab1:
        st.header("Current Employee Roster")
        try:
            employee_df = get_all_employees()
            if employee_df.empty:
                st.info("No employees found. Add one in the 'Add New Employee' tab.")
            else:
                st.dataframe(employee_df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Could not load employees: {e}")

    # --- TAB 2: Add New Employee (C in CRUD) ---
    with tab2:
        st.header("Add a New Employee")
        with st.form("add_employee_form", clear_on_submit=True):
            st.subheader("Employee Details")
            col1, col2 = st.columns(2)
            name = col1.text_input("Full Name *")
            designation = col2.text_input("Designation")
            base_salary = st.number_input("Base Salary (Monthly)", min_value=0.0, step=100.0)
            
            st.subheader("Bank Details (for HR-201)")
            b_col1, b_col2, b_col3 = st.columns(3)
            bank_name = b_col1.text_input("Bank Name")
            acc_title = b_col2.text_input("Account Title")
            acc_num = b_col3.text_input("Account Number")

            submitted = st.form_submit_button("Add Employee")
            if submitted:
                if not name:
                    st.warning("Employee Name is required.")
                else:
                    try:
                        add_employee(name, designation, base_salary, acc_num, acc_title, bank_name)
                        st.success(f"✅ Successfully added employee: {name}")
                    except Exception as e:
                        st.error(f"Error adding employee: {e}")

    # --- TAB 3: Update/Delete Employee (U & D in CRUD) ---
    with tab3:
        st.header("Edit or Remove an Employee")
        
        try:
            # Get a list of employees for the selectbox
            all_employees = get_all_employees()
            if all_employees.empty:
                st.info("No employees to edit or delete.")
            else:
                # Create a list of 'Name (ID: #)' for the selectbox
                employee_options = [f"{name} (ID: {id})" for id, name in zip(all_employees['id'], all_employees['name'])]
                selected_option = st.selectbox("Select Employee to Edit", employee_options, index=None, placeholder="Search for an employee...")

                if selected_option:
                    # Extract the ID from the selected option string
                    selected_id = int(selected_option.split(" (ID: ")[1].replace(")", ""))
                    
                    # Fetch the full details for the selected employee
                    emp_data = get_employee_by_id(selected_id)

                    if emp_data:
                        st.subheader(f"Editing: {emp_data['name']}")
                        
                        with st.form(f"update_form_{selected_id}", clear_on_submit=False):
                            # Load existing data into the form
                            u_name = st.text_input("Full Name *", value=emp_data['name'])
                            u_designation = st.text_input("Designation", value=emp_data['designation'])
                            u_base_salary = st.number_input("Base Salary (Monthly)", min_value=0.0, step=100.0, value=emp_data['base_salary'])
                            
                            st.subheader("Bank Details")
                            u_b_col1, u_b_col2, u_b_col3 = st.columns(3)
                            u_bank_name = u_b_col1.text_input("Bank Name", value=emp_data['bank_name'])
                            u_acc_title = u_b_col2.text_input("Account Title", value=emp_data['account_title'])
                            u_acc_num = u_b_col3.text_input("Account Number", value=emp_data['account_number'])

                            # Update and Delete buttons
                            col_submit, col_delete = st.columns(2)
                            
                            update_submitted = col_submit.form_submit_button("Save Changes")
                            delete_submitted = col_delete.form_submit_button("❌ Delete Employee", type="secondary")

                            if update_submitted:
                                if not u_name:
                                    st.warning("Employee Name is required.")
                                else:
                                    update_employee(selected_id, u_name, u_designation, u_base_salary, u_acc_num, u_acc_title, u_bank_name)
                                    st.success(f"✅ Successfully updated: {u_name}")
                                    st.rerun() # Rerun to refresh the selectbox and form

                            if delete_submitted:
                                # IMPORTANT: Add a confirmation step in a real app!
                                # For this plan, we proceed directly.
                                delete_employee(selected_id)
                                st.success(f"🗑️ Successfully deleted: {emp_data['name']}")
                                st.rerun() # Rerun to refresh the list

                        st.info("TO-DO (HR-202): Add a 'Download Salary Slip' button here.")
                        st.button(f"Download Salary Slip for {emp_data['name']} (Stub)")

        except Exception as e:
            st.error(f"Could not load employee list: {e}")

# --- PAGE 3: Ledgers (from pages/2_Ledgers.py) ---
def show_ledgers():
    st.title("🧾 Employee Ledgers & Claims")

    st.info("This is a placeholder for the Employee Ledger and Expense Claim modules.")

    st.header("To-Do: Employee Expense Claims (HR-204)")
    st.write("Build a form for employees (or admin) to submit expense claims (to `employee_claims` table).")
    st.write("Build a view for admin to 'Approve', 'Reject', or 'Reimburse' claims.")
    st.write("**Logic:** When a claim is 'Reimbursed', its status is updated, AND a new 'Debit' entry is added to the `employee_ledger` table for that employee.")

    st.header("To-Do: Employee Ledger Management (HR-203)")
    st.write("Build a view to display the full transaction history for a selected employee from the `employee_ledger` table.")
    st.write("This ledger will show salary payments, deductions, and reimbursements.")
    st.write("Implement PDF export for this ledger (DOC-401).")

# --- PAGE 4: Expenses (from pages/3_Expenses.py) ---
def show_expenses():
    st.title("💸 Company Expense Management")

    st.info("This is a placeholder for the Company Expense and Category modules.")

    st.header("To-Do: Expense Category Management (EX-302)")
    st.write("Build a CRUD interface (Create, Read, Update, Delete) for the `expense_categories` table.")
    st.write("Add a button: 'Download Category Sheet (PDF)' that uses `generate_pdf_report` (Requirement EX-302).")

    st.header("To-Do: Monthly Expense Reporting (EX-301)")
    st.write("Build a form to add new entries to the `company_expenses` table (with date, category, description, amount).")
    st.write("Build a view to see all company expenses, with filters for date range and category.")

    st.header("To-Do: Categorized Expense Download (EX-303)")
    st.write("This will likely be part of the 'Reports' page. It needs to query `company_expenses` by date range, group by category, and export as PDF.")

# --- PAGE 5: Reports (from pages/4_Reports.py) ---
def show_reports():
    st.title("📊 HR & Expense Reports")

    st.info("This is a placeholder for all PDF report generation.")
    st.write("All reports must support date-range filtering (DOC-402) and be in a professional PDF format (DOC-401, DOC-403) using `generate_pdf_report`.")

    st.header("To-Do: Salary Sheet Generation (HR-201)")
    st.write("Create a button 'Generate Monthly Salary Sheet'.")
    st.write("This will query the `employees` table and list all details: Account Number, Account Title, Bank Name, Name, Designation, Salary, and a column for Deductions (which will come from the `employee_ledger`).")
    st.write("This should be downloadable as a PDF.")

    st.header("To-Do: Individual Salary Slip (HR-202)")
    st.write("This feature is likely best placed on the 'Employee Management' page.")
    st.write("When an admin selects an employee, they can click a button to generate a PDF slip for that month, detailing base salary, deductions, and net pay.")

    st.header("To-Do: Monthly Company Expense Report (EX-301)")
    st.write("Add date-range selectors (start_date, end_date).")
    st.write("Query `company_expenses` within that range, grouped by category.")
    st.write("Display the report in-app and provide a 'Download PDF' button.")

    st.header("To-Do: Categorized Expense Download (EX-303)")
    st.write("This is very similar to the above (EX-301). This might be the same feature, just ensure the output is grouped by category.")

# --- PAGE 6: Data Import (from pages/5_Data_Import.py) ---
def show_data_import():
    st.title("📥 Data Import from Excel (P-103)")

    st.warning("This is a powerful feature. Ensure you have backups before importing large amounts of data.")

    st.header("To-Do: Implement Excel Import Logic")
    st.write("Provide an Excel template for users to download.")
    st.download_button("Download Employee Template", data="NAME,DESIGNATION,BASE_SALARY,ACCOUNT_NUMBER,ACCOUNT_TITLE,BANK_NAME", file_name="employee_template.csv")

    uploaded_file = st.file_uploader("Upload Excel or CSV File", type=["xlsx", "xls", "csv"])

    if uploaded_file is not None:
        st.write("File Uploaded! Now, implement the following:")
        st.markdown("""
            1.  Read the file using `pd.read_excel(uploaded_file)` or `pd.read_csv(uploaded_file)`.
            2.  Display the first 5 rows to the user for confirmation.
            3.  Let the user select the target table (e.g., "Employees", "Company Expenses").
            4.  Validate the columns.
            5.  On 'Import' button click, loop through the DataFrame rows and call the appropriate database function (e.g., `add_employee(...)`).
        """)

        # Example of reading the file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            st.write("File Preview:")
            st.dataframe(df.head(), use_container_width=True)
        except Exception as e:
            st.error(f"Error reading file: {e}")

# ==============================================================================
# --- MAIN APPLICATION LOGIC ---
# ==============================================================================

def main():
    # --- PAGE CONFIGURATION ---
    st.set_page_config(
        page_title="Nutrion HR & Expense Portal",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # --- DATABASE INITIALIZATION ---
    # This function will create all necessary tables if they don't exist
    create_tables()

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.image("https://placehold.co/400x100/000000/FFFFFF?text=NUTRION+LTD.", use_column_width=True)
        st.title("HR & Expense Portal")
        st.write("Welcome to the management system.")
        
        # Page selection
        page_options = {
            "Dashboard": "🏠",
            "Employee Management": "👥",
            "Employee Ledgers": "🧾",
            "Company Expenses": "💸",
            "Reports": "📊",
            "Data Import": "📥"
        }
        
        selected_page = st.radio(
            "Modules",
            options=page_options.keys(),
            format_func=lambda page: f"{page_options[page]} {page}" # Add icons
        )
        
        st.write("---")
        st.info("Developed by DataNex Solution\nContact: +92320 7429422")

    # --- PAGE ROUTING ---
    if selected_page == "Dashboard":
        show_dashboard()
    elif selected_page == "Employee Management":
        show_employees()
    elif selected_page == "Employee Ledgers":
        show_ledgers()
    elif selected_page == "Company Expenses":
        show_expenses()
    elif selected_page == "Reports":
        show_reports()
    elif selected_page == "Data Import":
        show_data_import()

if __name__ == "__main__":
    main()
