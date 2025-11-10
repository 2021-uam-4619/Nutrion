import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from fpdf import FPDF
import io

# --- Configuration ---
COMPANY_NAME = "Nutrion"
DEVELOPER_NAME = "DataNex Solution"
DEVELOPER_CONTACT = "+92320 7429422"

# --- Database Setup ---
DB_NAME = 'nutrion_app.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Employee Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT,
            salary REAL DEFAULT 0,
            account_no TEXT,
            account_title TEXT,
            bank TEXT
        );
        """)
        
        # Expense Categories Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """)
        
        # Company Expenses Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date DATE NOT NULL,
            category_id INTEGER,
            description TEXT,
            amount REAL NOT NULL,
            employee_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        );
        """)
        
        # Employee Ledger Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            employee_id INTEGER NOT NULL,
            description TEXT,
            credit REAL DEFAULT 0,
            debit REAL DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        );
        """)
        
        conn.commit()

# --- PDF Generation Utility ---
class PDF(FPDF):
    """Custom PDF class with header and footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""

    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, COMPANY_NAME, 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        if self.date_range_str:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 5, self.date_range_str, 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f'Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, f'Page {self.page_no()}', 0, 0, 'C')
        self.cell(0, 5, f'Developed by {DEVELOPER_NAME} ({DEVELOPER_CONTACT})', 0, 0, 'R')

    def create_table_from_df(self, df):
        """Creates a table in the PDF from a Pandas DataFrame."""
        if df.empty:
            self.cell(0, 10, "No data available for the selected criteria.", 0, 1, 'C')
            return

        self.set_font('Arial', 'B', 10)
        col_widths = []
        
        # Dynamically calculate column widths (simple version)
        page_width = self.w - 2 * self.l_margin
        default_width = page_width / len(df.columns)
        
        for col in df.columns:
            col_widths.append(default_width)
            self.cell(default_width, 10, str(col).upper(), 1, 0, 'C')
        self.ln()

        self.set_font('Arial', '', 9)
        for index, row in df.iterrows():
            for i, col in enumerate(df.columns):
                self.cell(col_widths[i], 10, str(row[col]), 1, 0, 'L')
            self.ln()

def generate_pdf_report(df, title, date_range=None):
    """Generates a PDF report from a DataFrame."""
    pdf = PDF(orientation='L', unit='mm', format='A4') # Landscape
    pdf.report_title = title
    
    if date_range and len(date_range) == 2:
        pdf.date_range_str = f"For period: {date_range[0]} to {date_range[1]}"
        
    pdf.add_page()
    pdf.create_table_from_df(df)
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

# --- Helper Functions ---
def get_all_employees():
    """Fetches all employees for dropdowns."""
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT id, name FROM employees ORDER BY name", conn)
        return df

def get_all_categories():
    """Fetches all expense categories for dropdowns."""
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT id, name FROM expense_categories ORDER BY name", conn)
        return df

# --- Page: Employee Management (Requirement 4) ---
def page_employee_management():
    st.header("Employee Management")
    
    st.subheader("Add New Employee")
    with st.form("new_employee_form", clear_on_submit=True):
        cols = st.columns(3)
        with cols[0]:
            name = st.text_input("Employee Name*")
            designation = st.text_input("Designation")
            salary = st.number_input("Base Salary", min_value=0.0, step=100.0)
        with cols[1]:
            account_no = st.text_input("Account No.")
            account_title = st.text_input("Account Title")
            bank = st.text_input("Bank Name")
        
        submitted = st.form_submit_button("Add Employee")
        if submitted:
            if not name:
                st.error("Employee Name is required.")
            else:
                try:
                    with get_db_connection() as conn:
                        conn.execute(
                            "INSERT INTO employees (name, designation, salary, account_no, account_title, bank) VALUES (?, ?, ?, ?, ?, ?)",
                            (name, designation, salary, account_no, account_title, bank)
                        )
                        conn.commit()
                    st.success(f"Employee '{name}' added successfully.")
                except Exception as e:
                    st.error(f"Error adding employee: {e}")

    st.subheader("Edit/Delete Employees")
    st.info("You can directly edit, add, or delete employee records in the table below. Changes are saved automatically.")
    
    try:
        with get_db_connection() as conn:
            df_employees = pd.read_sql_query("SELECT * FROM employees", conn, index_col="id")
        
        # Use st.data_editor for full CRUD
        edited_df = st.data_editor(
            df_employees,
            num_rows="dynamic",
            use_container_width=True
        )
        
        # Check for changes and update database
        if not edited_df.equals(df_employees):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Find deleted rows
                deleted_ids = set(df_employees.index) - set(edited_df.index)
                for emp_id in deleted_ids:
                    cursor.execute("DELETE FROM employees WHERE id = ?", (int(emp_id),))
                
                # Find added/updated rows
                for emp_id, row in edited_df.iterrows():
                    if emp_id not in df_employees.index:
                        # New row
                        cursor.execute(
                            "INSERT INTO employees (name, designation, salary, account_no, account_title, bank) VALUES (?, ?, ?, ?, ?, ?)",
                            (row['name'], row['designation'], row['salary'], row['account_no'], row['account_title'], row['bank'])
                        )
                    else:
                        # Updated row
                        cursor.execute(
                            "UPDATE employees SET name=?, designation=?, salary=?, account_no=?, account_title=?, bank=? WHERE id=?",
                            (row['name'], row['designation'], row['salary'], row['account_no'], row['account_title'], row['bank'], int(emp_id))
                        )
                conn.commit()
            st.success("Changes saved!")
            st.rerun() # Refresh to show clean state

    except Exception as e:
        st.error(f"Error loading employee data: {e}")

# --- Page: Expense Management (Requirements 3, 10, 11) ---
def page_expense_management():
    st.header("Company Expense Management")

    # --- Manage Categories (Req 3) ---
    st.subheader("Manage Expense Categories")
    with st.form("new_category_form", clear_on_submit=True):
        cols = st.columns([3, 1])
        with cols[0]:
            category_name = st.text_input("New Category Name")
        with cols[1]:
            st.text("") # for alignment
            st.text("") # for alignment
            add_cat_submitted = st.form_submit_button("Add Category")
            
    if add_cat_submitted and category_name:
        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO expense_categories (name) VALUES (?)", (category_name,))
                conn.commit()
            st.success(f"Category '{category_name}' added.")
        except sqlite3.IntegrityError:
            st.error(f"Category '{category_name}' already exists.")
        except Exception as e:
            st.error(f"Error: {e}")

    try:
        with get_db_connection() as conn:
            df_categories = pd.read_sql_query("SELECT * FROM expense_categories", conn, index_col="id")
        
        st.info("Edit or delete expense categories directly.")
        edited_cats_df = st.data_editor(
            df_categories,
            num_rows="dynamic",
            use_container_width=True
        )
        
        if not edited_cats_df.equals(df_categories):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # Find deleted
                deleted_ids = set(df_categories.index) - set(edited_cats_df.index)
                for cat_id in deleted_ids:
                    cursor.execute("DELETE FROM expense_categories WHERE id = ?", (int(cat_id),))
                
                # Find added/updated
                for cat_id, row in edited_cats_df.iterrows():
                    if cat_id not in df_categories.index:
                        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (row['name'],))
                    else:
                        cursor.execute("UPDATE expense_categories SET name=? WHERE id=?", (row['name'], int(cat_id)))
                conn.commit()
            st.success("Categories updated!")
            st.rerun()

    except Exception as e:
        st.error(f"Error loading categories: {e}")

    st.divider()

    # --- Log New Expense (Req 3, 11) ---
    st.subheader("Log New Company Expense")
    employees_df = get_all_employees()
    categories_df = get_all_categories()
    
    # Create dictionaries for selectbox
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
    
    if not category_list:
        st.warning("Please add at least one expense category to log expenses.")
        return

    with st.form("new_expense_form", clear_on_submit=True):
        cols = st.columns(3)
        with cols[0]:
            expense_date = st.date_input("Expense Date", date.today())
        with cols[1]:
            category_id = st.selectbox("Category", options=list(category_list.keys()), format_func=lambda x: category_list[x])
        with cols[2]:
            amount = st.number_input("Amount", min_value=0.01, step=0.01)
        
        description = st.text_area("Description")
        
        # Requirement 11: Link expense to employee ledger
        st.warning("Requirement 11: Deduct from Employee Ledger?")
        link_to_employee = st.checkbox("Deduct this expense from an employee's ledger?")
        employee_id = None
        if link_to_employee:
            employee_id = st.selectbox("Select Employee", options=[None] + list(employee_list.keys()), format_func=lambda x: "Select..." if x is None else employee_list[x])
        
        expense_submitted = st.form_submit_button("Log Expense")
        
        if expense_submitted:
            if not category_id or not amount:
                st.error("Date, Category, and Amount are required.")
            elif link_to_employee and not employee_id:
                st.error("Please select an employee to deduct from.")
            else:
                try:
                    with get_db_connection() as conn:
                        cursor = conn.cursor()
                        # 1. Log the company expense
                        cursor.execute(
                            "INSERT INTO company_expenses (expense_date, category_id, description, amount, employee_id) VALUES (?, ?, ?, ?, ?)",
                            (expense_date, category_id, description, amount, employee_id)
                        )
                        
                        # 2. (Req 11) If linked, add a DEBIT to employee ledger
                        if link_to_employee and employee_id:
                            ledger_desc = f"Expense deduction: {category_list[category_id]} - {description}"
                            cursor.execute(
                                "INSERT INTO employee_ledger (entry_date, employee_id, description, debit) VALUES (?, ?, ?, ?)",
                                (expense_date, employee_id, ledger_desc, amount)
                            )
                        
                        conn.commit()
                    st.success("Expense logged successfully.")
                    if link_to_employee and employee_id:
                        st.info(f"Amount of {amount} deducted from {employee_list[employee_id]}'s ledger.")
                except Exception as e:
                    st.error(f"Error logging expense: {e}")

    # --- View/Edit Company Expenses (Req 4) ---
    st.subheader("Manage Logged Expenses")
    try:
        with get_db_connection() as conn:
            # Join to get category name
            query = """
            SELECT 
                ce.id, 
                ce.expense_date, 
                ec.name AS category, 
                ce.description, 
                ce.amount,
                e.name AS employee_deducted
            FROM company_expenses ce
            LEFT JOIN expense_categories ec ON ce.category_id = ec.id
            LEFT JOIN employees e ON ce.employee_id = e.id
            ORDER BY ce.expense_date DESC
            """
            df_expenses = pd.read_sql_query(query, conn, index_col="id")
        
        st.info("You can edit/delete expenses below. Note: Editing here does not automatically update linked employee ledgers. For that, please add a new manual ledger entry.")
        st.dataframe(df_expenses, use_container_width=True) # Use dataframe for view-only, as editing is complex

    except Exception as e:
        st.error(f"Error loading expenses: {e}")

# --- Page: Salary Management (Requirement 2) ---
def page_salary_management():
    st.header("Salary Management")

    st.subheader("Generate Monthly Salary Sheet")
    st.info("This will calculate net salary for all employees for a given month, considering their base salary and any ledger deductions.")

    cols = st.columns(2)
    with cols[0]:
        salary_month = st.date_input("Salary Month", date.today().replace(day=1))
    
    if st.button("1. Generate Salary Credits"):
        st.warning("This will add a 'Credit' entry to each employee's ledger for their base salary. This is step 1.")
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                employees = cursor.execute("SELECT id, name, salary FROM employees").fetchall()
                
                # Check if already generated for this month
                first_day = salary_month.replace(day=1)
                
                added_count = 0
                for emp in employees:
                    # Check if 'Salary Credit' already exists for this month
                    exists = cursor.execute(
                        "SELECT 1 FROM employee_ledger WHERE employee_id = ? AND description = 'Monthly Salary' AND strftime('%Y-%m', entry_date) = ?",
                        (emp['id'], first_day.strftime('%Y-%m'))
                    ).fetchone()
                    
                    if not exists:
                        cursor.execute(
                            "INSERT INTO employee_ledger (entry_date, employee_id, description, credit) VALUES (?, ?, ?, ?)",
                            (first_day, emp['id'], 'Monthly Salary', emp['salary'])
                        )
                        added_count += 1
                conn.commit()
            st.success(f"Salary credits generated for {added_count} employees for {salary_month.strftime('%B %Y')}.")
            if added_count == 0:
                st.info("Salary credits seem to have been already generated for this month.")
        except Exception as e:
            st.error(f"Error generating salary credits: {e}")

    if st.button("2. View & Download Salary Sheet"):
        st.info("This calculates the final salary sheet based on ledger entries for the selected month.")
        
        first_day = salary_month.replace(day=1)
        last_day = (first_day.replace(day=28) + pd.DateOffset(days=4)).replace(day=1) - pd.DateOffset(days=1)
        
        query = f"""
        WITH MonthLedger AS (
            SELECT
                employee_id,
                SUM(credit) AS total_credits,
                SUM(debit) AS total_deductions
            FROM employee_ledger
            WHERE entry_date BETWEEN '{first_day}' AND '{last_day}'
            GROUP BY employee_id
        )
        SELECT
            e.name AS "Employee Name",
            e.designation AS "Designation",
            e.salary AS "Base Salary",
            COALESCE(ml.total_deductions, 0) AS "Deductions",
            (e.salary - COALESCE(ml.total_deductions, 0)) AS "Net Salary",
            e.account_no AS "Account No.",
            e.account_title AS "Account Title",
            e.bank AS "Bank"
        FROM employees e
        LEFT JOIN MonthLedger ml ON e.id = ml.employee_id;
        """
        
        try:
            with get_db_connection() as conn:
                df_salary_sheet = pd.read_sql_query(query, conn)
            
            st.dataframe(df_salary_sheet, use_container_width=True)
            
            # Download PDF (Req 2)
            pdf_bytes = generate_pdf_report(
                df_salary_sheet, 
                title=f"Salary Sheet - {salary_month.strftime('%B %Y')}"
            )
            st.download_button(
                label="Download Salary Sheet as PDF",
                data=pdf_bytes,
                file_name=f"Salary_Sheet_{salary_month.strftime('%Y_%m')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating salary sheet: {e}")

    st.divider()

    # --- Individual Salary Slip (Req 2) ---
    st.subheader("Individual Salary Slip")
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    cols = st.columns(2)
    with cols[0]:
        emp_id = st.selectbox("Select Employee", options=list(employee_list.keys()), format_func=lambda x: employee_list[x])
    with cols[1]:
        slip_month = st.date_input("For Month", date.today().replace(day=1), key="slip_month")
    
    if st.button("Generate & Download Slip"):
        first_day = slip_month.replace(day=1)
        last_day = (first_day.replace(day=28) + pd.DateOffset(days=4)).replace(day=1) - pd.DateOffset(days=1)
        
        try:
            with get_db_connection() as conn:
                # 1. Get Employee Details
                emp_details = conn.execute("SELECT * FROM employees WHERE id = ?", (emp_id,)).fetchone()
                
                # 2. Get Ledger entries for the month
                ledger_query = f"""
                SELECT description, credit, debit 
                FROM employee_ledger 
                WHERE employee_id = {emp_id} AND entry_date BETWEEN '{first_day}' AND '{last_day}'
                """
                df_ledger = pd.read_sql_query(ledger_query, conn)
            
            # Create DataFrames for PDF
            base_salary = emp_details['salary']
            total_deductions = df_ledger['debit'].sum()
            net_salary = base_salary - total_deductions # Assuming credit is only salary

            df_summary = pd.DataFrame({
                "Description": ["Base Salary", "Total Deductions", "Net Salary"],
                "Amount": [base_salary, total_deductions, net_salary]
            })
            
            df_deductions = df_ledger[df_ledger['debit'] > 0][['description', 'debit']]

            # Generate PDF
            pdf = PDF(orientation='P', unit='mm', format='A4')
            pdf.report_title = f"Salary Slip - {employee_list[emp_id]}"
            pdf.date_range_str = f"For Month: {slip_month.strftime('%B %Y')}"
            pdf.add_page()
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "Employee Details", 0, 1)
            pdf.set_font('Arial', '', 10)
            pdf.cell(40, 7, "Name:", 0, 0)
            pdf.cell(0, 7, f"{emp_details['name']}", 0, 1)
            pdf.cell(40, 7, "Designation:", 0, 0)
            pdf.cell(0, 7, f"{emp_details['designation']}", 0, 1)
            pdf.ln(5)
            
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, "Salary Summary", 0, 1)
            pdf.create_table_from_df(df_summary)
            pdf.ln(10)
            
            if not df_deductions.empty:
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, "Deduction Details", 0, 1)
                pdf.create_table_from_df(df_deductions)

            pdf_bytes = pdf.output(dest='S').encode('latin-1')
            
            st.download_button(
                label="Download Salary Slip",
                data=pdf_bytes,
                file_name=f"Salary_Slip_{employee_list[emp_id]}_{slip_month.strftime('%Y_%m')}.pdf",
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"Error generating slip: {e}")

# --- Page: Employee Ledger (Requirement 5) ---
def page_employee_ledger():
    st.header("Employee Ledger")
    
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    if not employee_list:
        st.warning("No employees found. Please add employees first.")
        return

    st.subheader("View Employee Ledger")
    cols = st.columns(3)
    with cols[0]:
        emp_id = st.selectbox("Select Employee", options=list(employee_list.keys()), format_func=lambda x: employee_list[x])
    with cols[1]:
        start_date = st.date_input("Start Date", date.today().replace(day=1))
    with cols[2]:
        end_date = st.date_input("End Date", date.today())
        
    if st.button("Fetch Ledger"):
        if emp_id and start_date and end_date:
            try:
                query = f"""
                SELECT 
                    entry_date, 
                    description, 
                    credit, 
                    debit
                FROM employee_ledger
                WHERE employee_id = {emp_id} AND entry_date BETWEEN '{start_date}' AND '{end_date}'
                ORDER BY entry_date
                """
                with get_db_connection() as conn:
                    df_ledger = pd.read_sql_query(query, conn)
                
                if df_ledger.empty:
                    st.info("No ledger entries found for this period.")
                    return

                # Calculate running balance
                df_ledger['balance'] = (df_ledger['credit'] - df_ledger['debit']).cumsum()
                
                st.dataframe(df_ledger, use_container_width=True)
                
                # Download PDF (Req 5)
                pdf_bytes = generate_pdf_report(
                    df_ledger,
                    title=f"Ledger for {employee_list[emp_id]}",
                    date_range=(start_date, end_date)
                )
                
                st.download_button(
                    label="Download Ledger as PDF",
                    data=pdf_bytes,
                    file_name=f"Ledger_{employee_list[emp_id]}_{start_date}_to_{end_date}.pdf",
                    mime="application/pdf"
                )
            
            except Exception as e:
                st.error(f"Error fetching ledger: {e}")
        else:
            st.error("All fields are required.")

    st.divider()
    st.subheader("Manual Ledger Entry")
    st.info("Manually add a credit or debit to an employee's ledger (e.g., for bonuses, advances, or corrections).")
    with st.form("manual_ledger_form", clear_on_submit=True):
        cols = st.columns(3)
        with cols[0]:
            manual_emp_id = st.selectbox("Employee", options=list(employee_list.keys()), format_func=lambda x: employee_list[x], key="manual_emp")
        with cols[1]:
            entry_type = st.radio("Entry Type", ["Credit", "Debit"])
        with cols[2]:
            manual_date = st.date_input("Entry Date", date.today())
            
        manual_amount = st.number_input("Amount", min_value=0.01)
        manual_desc = st.text_input("Description (e.g., 'Cash Advance', 'Performance Bonus')")
        
        manual_submitted = st.form_submit_button("Add Manual Entry")
        
        if manual_submitted:
            credit = manual_amount if entry_type == "Credit" else 0
            debit = manual_amount if entry_type == "Debit" else 0
            
            try:
                with get_db_connection() as conn:
                    conn.execute(
                        "INSERT INTO employee_ledger (entry_date, employee_id, description, credit, debit) VALUES (?, ?, ?, ?, ?)",
                        (manual_date, manual_emp_id, manual_desc, credit, debit)
                    )
                    conn.commit()
                st.success(f"Manual {entry_type} entry of {manual_amount} added for {employee_list[manual_emp_id]}.")
            except Exception as e:
                st.error(f"Error adding manual entry: {e}")

# --- Page: Reporting (Requirement 1, 6) ---
def page_reporting():
    st.header("Reports & Downloads")

    st.subheader("Company Expense Report (Req 6)")
    st.info("Download an expense report, filtered by category and date range.")
    
    categories_df = get_all_categories()
    category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
    
    cols = st.columns(2)
    with cols[0]:
        exp_start_date = st.date_input("Start Date", date.today().replace(day=1), key="rep_start")
    with cols[1]:
        exp_end_date = st.date_input("End Date", date.today(), key="rep_end")
    
    selected_categories = st.multiselect(
        "Filter by Category (optional)",
        options=list(category_list.keys()),
        format_func=lambda x: category_list[x]
    )
    
    if st.button("Generate Expense Report"):
        try:
            query = f"""
            SELECT 
                ce.expense_date, 
                ec.name AS category, 
                ce.description, 
                ce.amount,
                e.name AS employee_deducted
            FROM company_expenses ce
            LEFT JOIN expense_categories ec ON ce.category_id = ec.id
            LEFT JOIN employees e ON ce.employee_id = e.id
            WHERE ce.expense_date BETWEEN '{exp_start_date}' AND '{exp_end_date}'
            """
            
            if selected_categories:
                cat_ids_str = ", ".join(map(str, selected_categories))
                query += f" AND ce.category_id IN ({cat_ids_str})"
                
            query += " ORDER BY ce.expense_date"
            
            with get_db_connection() as conn:
                df_expense_report = pd.read_sql_query(query, conn)
                
            st.dataframe(df_expense_report, use_container_width=True)
            
            pdf_bytes = generate_pdf_report(
                df_expense_report,
                title="Company Expense Report",
                date_range=(exp_start_date, exp_end_date)
            )
            
            st.download_button(
                label="Download Expense Report as PDF",
                data=pdf_bytes,
                file_name=f"Expense_Report_{exp_start_date}_to_{exp_end_date}.pdf",
                mime="application/pdf"
            )
            
        except Exception as e:
            st.error(f"Error generating report: {e}")

    # Other reports (like ledger and salary) are handled in their respective pages.
    st.subheader("Other Reports")
    st.info("Salary Sheets and Employee Ledgers can be downloaded from their respective pages in the 'Salary Management' and 'Employee Ledger' sections.")

# --- Page: Data Import (Requirement 7) ---
def page_data_import():
    st.header("Data Import")
    st.info("Use this page to import your old employee data from an Excel file.")

    st.subheader("1. Download Excel Template")
    st.markdown("Download the template, fill it out, and upload it in step 2.")
    
    # Create template DataFrame
    template_df = pd.DataFrame(columns=[
        "name", "designation", "salary", "account_no", "account_title", "bank"
    ])
    
    # Convert to Excel in-memory
    @st.cache_data
    def get_template_excel():
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            template_df.to_excel(writer, index=False, sheet_name='Employees')
        return output.getvalue()

    st.download_button(
        label="Download Employee Template (.xlsx)",
        data=get_template_excel(),
        file_name="employee_import_template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("2. Upload Completed Template")
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])
    
    if uploaded_file is not None:
        try:
            df_import = pd.read_excel(uploaded_file)
            st.dataframe(df_import)
            
            # Validate columns
            if list(df_import.columns) != list(template_df.columns):
                st.error("File columns do not match the template. Please download and use the provided template.")
            else:
                if st.button("Import Data"):
                    try:
                        with get_db_connection() as conn:
                            df_import.to_sql('employees', conn, if_exists='append', index=False)
                        st.success(f"Successfully imported {len(df_import)} employee records.")
                    except Exception as e:
                        st.error(f"Error during import: {e}")
                        
        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- Main Application ---
def main():
    st.set_page_config(
        page_title=f"{COMPANY_NAME} HR & Expense",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize the database
    init_db()

    # --- Sidebar ---
    with st.sidebar:
        st.title(f"{COMPANY_NAME}")
        st.markdown("HR & Expense System")
        st.divider()
        
        page = st.radio(
            "Navigation",
            [
                "Employee Management",
                "Expense Management",
                "Salary Management",
                "Employee Ledger",
                "Reporting",
                "Data Import"
            ]
        )
        
        st.divider()
        st.markdown("---")
        st.markdown(f"**Developed by:**\n{DEVELOPER_NAME}")
        st.markdown(f"**Contact:**\n{DEVELOPER_CONTACT}")

    # --- Page Routing ---
    if page == "Employee Management":
        page_employee_management()
    elif page == "Expense Management":
        page_expense_management()
    elif page == "Salary Management":
        page_salary_management()
    elif page == "Employee Ledger":
        page_employee_ledger()
    elif page == "Reporting":
        page_reporting()
    elif page == "Data Import":
        page_data_import()

if __name__ == "__main__":
    main()
