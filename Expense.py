import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# --- PDF Class with Header/Footer ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""

    def header(self):
        # Logo (optional - requires image file)
        # self.image('logo.png', 10, 8, 33)
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, COMPANY_NAME, 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 7, self.date_range_str, 0, 1, 'C')
        self.ln(5) # Line break

    def footer(self):
        self.set_y(-35) # Position 3.5 cm from bottom
        self.set_font('Arial', '', 10)
        
        # --- Signature Lines ---
        footer_width = self.w - self.l_margin - self.r_margin
        # --- MODIFIED: Added computerized signature ---
        self.cell(footer_width / 2, 10, "Prepared by: System (Auto-Generated)", 0, 0, 'L')
        self.cell(footer_width / 2, 10, "Approved by: _______________", 0, 1, 'R')
        self.ln(10)

        # --- Page Number and Developer Info ---
        self.set_font('Arial', 'I', 8)
        self.cell(footer_width / 2, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'L')
        self.cell(footer_width / 2, 10, DEVELOPER_INFO, 0, 0, 'R')

    def add_table(self, df, totals_cols=None):
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(224, 235, 255) # Light blue header
        
        # Calculate column widths
        num_cols = len(df.columns)
        total_width = self.w - self.l_margin - self.r_margin
        
        # Simple equal width for all columns
        col_width = total_width / num_cols
        
        # Render Headers
        for col in df.columns:
            self.cell(col_width, 7, str(col).replace('_', ' ').title(), 1, 0, 'C', 1)
        self.ln()

        # Render Data
        self.set_font('Arial', '', 8)
        self.set_fill_color(255)
        fill = False
        for index, row in df.iterrows():
            for col in df.columns:
                cell_text = str(row[col])
                # Check if this column is numeric for right alignment
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        # Format numbers nicely
                        cell_text = f"{float(row[col]):,.2f}"
                        self.cell(col_width, 6, cell_text, 'LR', 0, 'R', fill)
                    except (ValueError, TypeError):
                        self.cell(col_width, 6, cell_text, 'LR', 0, 'L', fill)
                else:
                    self.cell(col_width, 6, cell_text, 'LR', 0, 'L', fill)
            self.ln()
            fill = not fill
        
        # Draw bottom line of the table
        self.cell(total_width, 0, '', 'T', 1)
        
        # --- Add Totals Row ---
        if totals_cols:
            self.set_font('Arial', 'B', 9)
            self.set_fill_color(240, 240, 240) # Light grey for total
            grand_total = 0.0
            
            for i, col in enumerate(df.columns):
                if i == 0:
                    self.cell(col_width, 7, "GRAND TOTAL", 1, 0, 'R', 1)
                elif col in totals_cols:
                    col_total = df[col].sum()
                    self.cell(col_width, 7, f"{col_total:,.2f}", 1, 0, 'R', 1)
                else:
                    self.cell(col_width, 7, "", 1, 0, 'C', 1)
            self.ln()

# --- Database Setup ---
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Employee Table (Req 2, 5)
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT,
            salary REAL DEFAULT 0,
            bank TEXT,
            account_title TEXT,
            account_no TEXT,
            join_date DATE
        )
    ''')
    
    # Expense Categories Table (Req 3, 6, 10)
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Company Expenses Table (Req 3)
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            amount REAL NOT NULL,
            expense_date DATE NOT NULL,
            category_id INTEGER,
            employee_id INTEGER, -- For Req 11
            FOREIGN KEY (category_id) REFERENCES expense_categories (id) ON DELETE SET NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE SET NULL
        )
    ''')
    
    # Employee Ledger Table (Req 5, 11)
    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            entry_date DATE NOT NULL,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()

# --- PDF Generation Function ---
def generate_pdf_report(df, title, date_range=None, orientation='L', totals_cols=None):
    """Generates a professional PDF report from a DataFrame."""
    pdf = PDF(orientation=orientation, unit='mm', format='A4')
    pdf.report_title = title
    if date_range:
        pdf.date_range_str = f"{date_range[0].strftime('%d %b %Y')} to {date_range[1].strftime('%d %b %Y')}"
    else:
        pdf.date_range_str = "As of " + date.today().strftime('%d %b %Y')
        
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    # Add Table
    if df.empty:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, "No data found for the selected criteria.", 1, 1, 'C')
    else:
        pdf.add_table(df, totals_cols=totals_cols)
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

# --- NEW FUNCTION for Individual Salary Slips ---
def generate_individual_slip_pdf(emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary):
    """Generates a formatted PDF for a single employee's salary slip."""
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.report_title = f"Salary Slip - {slip_month.strftime('%B %Y')}"
    pdf.date_range_str = "" # No date range needed
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Employee: {emp_details['name']}", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"Designation: {emp_details['designation']}", 0, 1, 'L')
    pdf.cell(0, 7, f"Base Salary: Rs. {emp_details['salary']:,.2f}", 0, 1, 'L')
    pdf.ln(5)

    # --- Earnings ---
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(224, 235, 255)
    pdf.cell(0, 10, "Earnings & Deductions", 1, 1, 'C', fill=True)
    
    col_width = (pdf.w - 2 * pdf.l_margin) / 3
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width * 1.5, 7, "Description", 1, 0, 'C')
    pdf.cell(col_width * 0.75, 7, "Credits (Rs.)", 1, 0, 'C')
    pdf.cell(col_width * 0.75, 7, "Debits (Rs.)", 1, 1, 'C')

    pdf.set_font('Arial', '', 9)
    if ledger_df.empty:
        pdf.cell(0, 7, "No ledger activity found for this month.", 1, 1, 'C')
    else:
        for _, row in ledger_df.iterrows():
            pdf.cell(col_width * 1.5, 7, str(row['description']), 1, 0, 'L')
            pdf.cell(col_width * 0.75, 7, f"{row['credit']:,.2f}" if row['credit'] > 0 else "0.00", 1, 0, 'R')
            pdf.cell(col_width * 0.75, 7, f"{row['debit']:,.2f}" if row['debit'] > 0 else "0.00", 1, 1, 'R')

    # --- Totals ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width * 1.5, 7, "Total", 1, 0, 'R')
    pdf.cell(col_width * 0.75, 7, f"{total_credits:,.2f}", 1, 0, 'R')
    pdf.cell(col_width * 0.75, 7, f"{total_debits:,.2f}", 1, 1, 'R')

    # --- Net Salary ---
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(210, 210, 210)
    pdf.cell(col_width * 1.5, 10, "Net Salary Payable", 1, 0, 'R', fill=True)
    pdf.cell(col_width * 1.5, 10, f"Rs. {net_salary:,.2f}", 1, 1, 'R', fill=True)
    
    # Add bank details
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "Bank Details", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"  Bank: {emp_details['bank']}", 0, 1, 'L')
    pdf.cell(0, 7, f"  Account Title: {emp_details['account_title']}", 0, 1, 'L')
    pdf.cell(0, 7, f"  Account No: {emp_details['account_no']}", 0, 1, 'L')

    return pdf.output(dest='S').encode('latin-1')


# --- Helper Functions ---
@st.cache_data(ttl=60)
def get_all_employees():
    conn = get_db_connection()
    return pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)

@st.cache_data(ttl=60)
def get_all_categories():
    conn = get_db_connection()
    return pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)

# --- NEW: Helper for Dashboard Stats ---
@st.cache_data(ttl=60)
def get_dashboard_stats():
    """Fetches key stats for the dashboard."""
    conn = get_db_connection()
    
    # 1. Total Employees
    emp_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM employees", conn)
    emp_count = emp_count_df['count'].iloc[0] if not emp_count_df.empty else 0
    
    # 2. Total Expenses (Current Month)
    today = date.today()
    first_day_month = today.replace(day=1)
    last_day_month = (first_day_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    exp_total_df = pd.read_sql_query(
        "SELECT SUM(amount) as total FROM company_expenses WHERE expense_date BETWEEN ? AND ?",
        conn,
        params=(str(first_day_month), str(last_day_month))
    )
    exp_total = exp_total_df['total'].iloc[0] if not exp_total_df.empty and exp_total_df['total'].iloc[0] else 0.0
    
    # 3. Total Categories
    cat_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM expense_categories", conn)
    cat_count = cat_count_df['count'].iloc[0] if not cat_count_df.empty else 0
    
    return emp_count, exp_total, cat_count

def clear_cache():
    st.cache_data.clear()

def generate_excel_template(columns, file_name):
    """Creates a downloadable empty Excel template."""
    df_template = pd.DataFrame(columns=columns)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_template.to_excel(writer, index=False, sheet_name='Sheet1')
        worksheet = writer.sheets['Sheet1']
        # Add comments as instructions
        worksheet.write_comment('A1', 'Do not change the column names. Fill data in rows below.')
    output.seek(0)
    return output, file_name

# --- Main App Pages ---
def page_dashboard():
    st.title(f"Welcome to {COMPANY_NAME} HR & Expense Manager")
    
    # --- NEW: Dashboard Stats ---
    try:
        emp_count, exp_total, cat_count = get_dashboard_stats()
        
        st.subheader("At-a-Glance (Current Month)")
        cols = st.columns(3)
        cols[0].metric("Total Employees", f"{emp_count}")
        cols[1].metric("Expenses (This Month)", f"Rs. {exp_total:,.2f}")
        cols[2].metric("Expense Categories", f"{cat_count}")
    
    except Exception as e:
        st.warning(f"Could not load dashboard stats: {e}")
    
    st.info("""
    Use the navigation menu on the left to manage your company's data:
    - **Dashboard**: This page.
    - **Employee Management**: Add, view, edit, and delete employee records.
    - **Expense Management**: Log company expenses and manage expense categories.
    - **Salary Management**: Generate monthly salary sheets and individual pay slips.
    - **Employee Ledger**: View detailed financial ledgers for each employee.
    - **Reporting**: Download summary reports for expenses and categories.
    - **Data Import**: Bulk-import existing data using Excel templates.
    """)
    st.image("https://placehold.co/800x300/e0e0e0/777?text=Nutrion+Company+Dashboard", use_column_width=True)

def page_employee_management():
    st.title("Employee Management")
    
    # --- Add New Employee Form ---
    st.subheader("Add New Employee")
    with st.form("new_employee_form", clear_on_submit=True):
        cols = st.columns(2)
        with cols[0]:
            name = st.text_input("Name", placeholder="e.g., Alice Smith")
            salary = st.number_input("Base Salary (Monthly)", min_value=0.0, step=1000.0)
            bank = st.text_input("Bank", placeholder="e.g., HBL")
            join_date = st.date_input("Joining Date", date.today())
        with cols[1]:
            designation = st.text_input("Designation", placeholder="e.g., Sales Manager")
            account_title = st.text_input("Account Title", placeholder="e.g., Alice Smith")
            account_no = st.text_input("Account No", placeholder="e.g., 0123456789")
            
        submitted = st.form_submit_button("Add Employee")
        if submitted:
            if not name or not designation:
                st.error("Name and Designation are required.")
            else:
                try:
                    conn = get_db_connection()
                    conn.execute(
                        """
                        INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (name, designation, salary, bank, account_title, account_no, str(join_date))
                    )
                    conn.commit()
                    st.success(f"Employee '{name}' added successfully.")
                    clear_cache()
                except sqlite3.Error as e:
                    st.error(f"Database error: {e}")

    st.divider()

    # --- Manage Existing Employees (Req 4) ---
    st.subheader("Manage Employees")
    try:
        employees_df = get_all_employees()
        if employees_df.empty:
            st.info("No employees found. Add employees using the form above.")
            return

        # Use st.data_editor for CRUD
        edited_df = st.data_editor(
            employees_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "join_date": st.column_config.DateColumn("Join Date", format="YYYY-MM-DD")
            },
            key="employee_editor"
        )

        # Detect changes and update DB
        if st.button("Save Changes"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # 1. Detect Updates/Deletions
            original_ids = set(employees_df['id'])
            current_ids = set(edited_df['id'].dropna()) # Get IDs from edited df
            
            # Deletions
            deleted_ids = original_ids - current_ids
            if deleted_ids:
                for del_id in deleted_ids:
                    cursor.execute("DELETE FROM employees WHERE id = ?", (int(del_id),))
                st.success(f"Deleted {len(deleted_ids)} employee(s).")

            # Updates & Additions
            for _, row in edited_df.iterrows():
                if pd.isna(row['id']):
                    # New Row (Addition)
                    if row['name']: # Only add if name is present
                        cursor.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (row['name'], row['designation'], row['salary'], row['bank'], row['account_title'], row['account_no'], row['join_date'])
                        )
                else:
                    # Existing Row (Update)
                    cursor.execute(
                        """
                        UPDATE employees SET
                        name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, account_no = ?, join_date = ?
                        WHERE id = ?
                        """,
                        (row['name'], row['designation'], row['salary'], row['bank'], row['account_title'], row['account_no'], row['join_date'], int(row['id']))
                    )
            
            conn.commit()
            st.success("Changes saved successfully.")
            clear_cache()
            st.rerun() # Rerun to show fresh data

    except Exception as e:
        st.error(f"Error loading employees: {e}")


def page_expense_management():
    st.title("Expense Management")

    # --- Log New Expense (Req 3) ---
    st.subheader("Log New Company Expense")
    
    # Get categories for dropdown
    categories_df = get_all_categories()
    category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
    
    # Get employees for dropdown (Req 11)
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    # Add a "None" option for expenses not tied to an employee
    employee_list_with_none = {0: "N/A (General Company Expense)"}
    employee_list_with_none.update(employee_list)

    if not category_list:
        st.warning("No expense categories found. Please add categories below before logging expenses.", icon="⚠️")
        
    with st.form("new_expense_form", clear_on_submit=True):
        cols = st.columns(3)
        with cols[0]:
            expense_date = st.date_input("Expense Date", date.today())
        with cols[1]:
            amount = st.number_input("Amount", min_value=0.01, step=100.0)
        with cols[2]:
            category_id = st.selectbox("Category", options=list(category_list.keys()), format_func=lambda x: category_list[x], disabled=not category_list)
        
        description = st.text_input("Description", placeholder="e.g., Office electricity bill")
        
        # Req 11: Link expense to employee
        st.info("If this expense is an advance or deduction for an employee, select their name. (Req 11)")
        employee_id = st.selectbox("Employee (Optional)", options=list(employee_list_with_none.keys()), format_func=lambda x: employee_list_with_none[x])

        submitted = st.form_submit_button("Log Expense")
        if submitted:
            if amount > 0 and category_id:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # 1. Log the company expense
                    cursor.execute(
                        """
                        INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (description, amount, str(expense_date), category_id, employee_id if employee_id != 0 else None)
                    )
                    
                    # 2. (Req 11) If linked to employee, add as a DEBIT to their ledger
                    if employee_id != 0:
                        ledger_desc = f"Expense: {description}"
                        cursor.execute(
                            """
                            INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                            VALUES (?, ?, ?, ?, 0)
                            """,
                            (employee_id, str(expense_date), ledger_desc, amount)
                        )
                        st.success(f"Expense logged and Rs. {amount} debited from {employee_list[employee_id]}'s ledger.")
                    else:
                        st.success("Company expense logged successfully.")
                    
                    conn.commit()
                    clear_cache()
                except sqlite3.Error as e:
                    st.error(f"Database error: {e}")
            else:
                st.error("Please fill in all fields (Amount and Category).")

    st.divider()
    
    # --- Manage Expense Categories (Req 3, 10) ---
    st.subheader("Manage Expense Categories")
    try:
        categories_df = get_all_categories()
        
        edited_df = st.data_editor(
            categories_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={"id": st.column_config.NumberColumn("ID", disabled=True)},
            key="category_editor"
        )
        
        if st.button("Save Category Changes"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            original_ids = set(categories_df['id'])
            current_ids = set(edited_df['id'].dropna())
            
            deleted_ids = original_ids - current_ids
            if deleted_ids:
                for del_id in deleted_ids:
                    cursor.execute("DELETE FROM expense_categories WHERE id = ?", (int(del_id),))
                st.success(f"Deleted {len(deleted_ids)} category(s).")

            for _, row in edited_df.iterrows():
                if pd.isna(row['id']):
                    if row['name']:
                        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (row['name'],))
                else:
                    cursor.execute("UPDATE expense_categories SET name = ? WHERE id = ?", (row['name'], int(row['id'])))
            
            conn.commit()
            st.success("Category changes saved successfully.")
            clear_cache()
            st.rerun()

    except Exception as e:
        st.error(f"Error loading categories: {e}")

    st.divider()

    # --- Manage Logged Expenses (Req 4) ---
    st.subheader("Manage Logged Expenses")
    try:
        conn = get_db_connection()
        expenses_df = pd.read_sql_query(
            """
            SELECT 
                ce.id, 
                ce.expense_date, 
                ce.description, 
                ce.amount, 
                ec.name as category,
                e.name as employee,
                ce.category_id, -- Keep for editing
                ce.employee_id -- Keep for editing
            FROM company_expenses ce
            LEFT JOIN expense_categories ec ON ce.category_id = ec.id
            LEFT JOIN employees e ON ce.employee_id = e.id
            ORDER BY ce.expense_date DESC
            """, conn
        )

        if expenses_df.empty:
            st.info("No expenses logged yet.")
            return

        cols_to_show = ['id', 'expense_date', 'description', 'amount', 'category', 'employee']
        
        # --- Display in a non-editable table first ---
        st.dataframe(expenses_df[cols_to_show], use_container_width=True)

        # --- Edit/Delete Section ---
        st.markdown("---")
        st.markdown("**Edit or Delete an Expense**")
        expense_ids = expenses_df['id'].tolist()
        expense_to_edit = st.selectbox("Select Expense ID to Edit/Delete", options=expense_ids, format_func=lambda x: f"ID: {x} - {expenses_df[expenses_df['id'] == x]['description'].values[0]}", index=None)

        if expense_to_edit:
            expense_details = expenses_df[expenses_df['id'] == expense_to_edit].iloc[0]
            
            # Delete Button
            if st.button(f"Delete Expense ID {expense_to_edit}", type="primary"):
                try:
                    conn = get_db_connection()
                    conn.execute("DELETE FROM company_expenses WHERE id = ?", (int(expense_to_edit),))
                    # Note: This does not auto-reverse the ledger entry (complex operation)
                    conn.commit()
                    st.success(f"Expense ID {expense_to_edit} deleted. (Ledger entry not auto-reversed)")
                    clear_cache()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting expense: {e}")
            
            # Edit Form
            with st.expander("Edit Expense Details"):
                # Get category list for form
                categories_df = get_all_categories()
                category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
                cat_ids = list(category_list.keys())
                
                # --- FIX for deleted category bug ---
                # Check if the expense's category still exists
                current_cat_id = expense_details['category_id']
                if pd.notna(current_cat_id) and current_cat_id not in cat_ids:
                    # The category was deleted!
                    st.error(f"Error: The original category (ID: {current_cat_id}) for this expense was deleted. Please select a new, valid category.")
                    # Add the (now invalid) ID to the list just to prevent a crash, but default to the first valid one
                    cat_ids.append(current_cat_id)
                    category_list[current_cat_id] = f"INVALID CATEGORY (ID: {current_cat_id})"
                    default_index = 0 
                elif pd.notna(current_cat_id):
                    default_index = cat_ids.index(current_cat_id)
                else:
                    # Expense had no category to begin with
                    default_index = 0
                # --- END FIX ---
                
                with st.form("edit_expense_form"):
                    edit_date = st.date_input("Expense Date", value=pd.to_datetime(expense_details['expense_date']))
                    edit_amount = st.number_input("Amount", value=expense_details['amount'])
                    
                    cols = st.columns(3)
                    with cols[0]:
                        edit_desc = st.text_input("Description", value=expense_details['description'])
                    with cols[1]:
                        edit_category_id = st.selectbox("Category", 
                            options=cat_ids, 
                            format_func=lambda x: category_list[x], 
                            index=default_index # Use the safe default_index
                        )
                    with cols[2]:
                        # Note: Editing employee link is complex as it affects ledgers. Disabled for simplicity.
                        st.text_input("Employee (Read-only)", value=expense_details.get('employee', 'N/A'), disabled=True)
                        st.help("To change an employee-linked expense, please delete this and create a new one. This prevents ledger errors.")

                    update_submitted = st.form_submit_button("Save Changes")
                    if update_submitted:
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                """
                                UPDATE company_expenses 
                                SET expense_date = ?, amount = ?, description = ?, category_id = ?
                                WHERE id = ?
                                """,
                                (str(edit_date), edit_amount, edit_desc, edit_category_id, expense_to_edit)
                            )
                            conn.commit()
                            st.success(f"Expense ID {expense_to_edit} updated.")
                            clear_cache()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating expense: {e}")

    except Exception as e:
        st.error(f"Error loading expenses: {e}")

def page_salary_management():
    st.title("Salary Management")

    st.info("""
    Follow these steps to process monthly salaries:
    1. **Generate Monthly Salary Credits:** Run this first. It adds the 'Base Salary' as a credit to each employee's ledger for the month.
    2. **View & Download Salary Sheet:** After credits are generated (and any deductions are logged), use this to get the final payroll sheet.
    3. **Generate Individual Salary Slip:** Download a detailed slip for a single employee.
    """)
    
    selected_month = st.date_input("Select Month for Salary Processing", date.today().replace(day=1))
    first_day = selected_month.replace(day=1)
    # Find last day of the month
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    st.divider()

    # --- Step 1: Generate Monthly Credits ---
    st.subheader("1. Generate Monthly Salary Credits")
    if st.button("Generate Credits for All Employees"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            employees_df = get_all_employees()
            if employees_df.empty:
                st.error("No employees found.")
                return

            processed_count = 0
            skipped_count = 0
            
            with st.spinner(f"Processing salaries for {selected_month.strftime('%B %Y')}..."):
                for _, emp in employees_df.iterrows():
                    salary = emp['salary']
                    if salary <= 0:
                        skipped_count += 1
                        continue
                    
                    # Check if credit already exists for this month
                    description = f"Monthly Salary Credit - {selected_month.strftime('%B %Y')}"
                    cursor.execute(
                        """
                        SELECT 1 FROM employee_ledger 
                        WHERE employee_id = ? AND description = ?
                        """,
                        (emp['id'], description)
                    )
                    if cursor.fetchone():
                        skipped_count += 1
                        continue
                        
                    # Add credit to ledger
                    cursor.execute(
                        """
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                        VALUES (?, ?, ?, 0, ?)
                        """,
                        (emp['id'], str(first_day), description, salary)
                    )
                    processed_count += 1
            
            conn.commit()
            if processed_count > 0:
                st.success(f"Successfully generated salary credits for {processed_count} employee(s).")
            if skipped_count > 0:
                st.info(f"Skipped {skipped_count} employee(s) (salary already generated or base salary is 0).")
            clear_cache()
        
        except Exception as e:
            st.error(f"Error generating salary credits: {e}")

    st.divider()

    # --- Step 2: Download Salary Sheet (Req 2) ---
    st.subheader("2. View & Download Salary Sheet")
    st.help("This sheet calculates the Net Salary based on all ledger entries for the selected month.")
    
    if st.button("Generate Salary Sheet"):
        try:
            conn = get_db_connection()
            # This query joins employees with their ledger summary for the month
            query = f"""
            SELECT
                e.name AS "Employee Name",
                e.designation AS "Designation",
                e.salary AS "Base Salary",
                COALESCE(SUM(l.credit), 0) AS "Total Credits",
                COALESCE(SUM(l.debit), 0) AS "Total Deductions",
                (COALESCE(SUM(l.credit), 0) - COALESCE(SUM(l.debit), 0)) AS "Net Salary",
                e.bank AS "Bank",
                e.account_title AS "Account Title",
                e.account_no AS "Account No"
            FROM employees e
            LEFT JOIN employee_ledger l ON e.id = l.employee_id
                AND l.entry_date BETWEEN '{first_day}' AND '{last_day}'
            GROUP BY e.id, e.name, e.designation, e.salary, e.bank, e.account_title, e.account_no
            ORDER BY e.name
            """
            salary_df = pd.read_sql_query(query, conn)

            if salary_df.empty:
                st.warning("No salary data to display. Did you add employees and generate credits?")
                return

            st.dataframe(salary_df)
            
            pdf_bytes = generate_pdf_report(
                salary_df, 
                f"Salary Sheet - {selected_month.strftime('%B %Y')}", 
                date_range=(first_day, last_day),
                orientation='L',
                totals_cols=["Base Salary", "Total Credits", "Total Deductions", "Net Salary"]
            )
            
            st.download_button(
                label="Download Salary Sheet (PDF)",
                data=pdf_bytes,
                file_name=f"Salary_Sheet_{selected_month.strftime('%Y_%m')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating salary sheet: {e}")

    st.divider()

    # --- Individual Salary Slip (Req 2) ---
    st.subheader("3. Generate Individual Salary Slip")
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    # *** ADDED CHECK FOR EMPTY EMPLOYEE LIST ***
    if not employee_list:
        st.warning("Cannot generate slip: No employees found in the system. Please add employees first.", icon="⚠️")
        return # Stop this part of the page from rendering
    
    # --- START: CORRECTED CODE FOR INDIVIDUAL SLIP ---
    cols = st.columns(2)
    with cols[0]:
        emp_ids = list(employee_list.keys())
        selected_emp_id = st.selectbox(
            "Select Employee", 
            options=emp_ids, 
            format_func=lambda x: employee_list[x],
            key="slip_emp_select"
        )
    with cols[1]:
        slip_month = st.date_input("Salary Month", date.today().replace(day=1), key="slip_month_picker")

    if st.button("Generate Individual Salary Slip"):
        try:
            # 1. Get employee details
            with get_db_connection() as conn:
                emp_details_df = pd.read_sql_query(
                    "SELECT * FROM employees WHERE id = ?", 
                    conn, 
                    params=(selected_emp_id,)
                )
                if emp_details_df.empty:
                    st.error(f"Employee ID {selected_emp_id} not found.")
                    return
                emp_details = emp_details_df.iloc[0]

            # 2. Get ledger entries for the month
            first_day_slip = slip_month.replace(day=1)
            last_day_slip = (first_day_slip.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            with get_db_connection() as conn:
                ledger_df = pd.read_sql_query(
                    f"""
                    SELECT description, credit, debit 
                    FROM employee_ledger 
                    WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                    ORDER BY entry_date
                    """, 
                    conn, 
                    params=(selected_emp_id, first_day_slip, last_day_slip)
                )

            # 3. Calculate totals
            total_credits = ledger_df['credit'].sum()
            total_debits = ledger_df['debit'].sum()
            net_salary = total_credits - total_debits

            # 4. Generate the new PDF
            pdf_bytes = generate_individual_slip_pdf(
                emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary
            )
            
            st.download_button(
                label=f"Download Slip for {emp_details['name']}",
                data=pdf_bytes,
                file_name=f"Salary_Slip_{emp_details['name'].replace(' ', '_')}_{slip_month.strftime('%Y_%m')}.pdf",
                mime="application/pdf"
            )
            st.success("Salary slip PDF is ready for download.")
        
        except Exception as e:
            st.error(f"Error generating individual slip: {e}")
            st.error("Please ensure the selected employee exists and data is available.")
    
    # --- END: CORRECTED CODE ---


# --- Page: Employee Ledger (Requirement 5) ---
def page_employee_ledger():
    st.title("Employee Ledger Management")

    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    if not employee_list:
        st.error("No employees found. Please add employees first.", icon="⚠️")
        return

    emp_ids = list(employee_list.keys())
    selected_emp_id = st.selectbox(
        "Select Employee", 
        options=emp_ids, 
        format_func=lambda x: employee_list[x]
    )

    # Date Range Filter
    cols = st.columns(2)
    today = date.today()
    with cols[0]:
        start_date = st.date_input("Start Date", today.replace(day=1))
    with cols[1]:
        end_date = st.date_input("End Date", today)

    if selected_emp_id and start_date and end_date:
        if start_date > end_date:
            st.error("Start Date cannot be after End Date.")
            return

        # --- NEW: Get All-Time Balance ---
        try:
            conn = get_db_connection()
            all_time_df = pd.read_sql_query(
                "SELECT (COALESCE(SUM(credit), 0) - COALESCE(SUM(debit), 0)) as balance FROM employee_ledger WHERE employee_id = ?",
                conn,
                params=(selected_emp_id,)
            )
            all_time_balance = all_time_df['balance'].iloc[0] if not all_time_df.empty else 0
            st.metric(label=f"All-Time Balance for {employee_list[selected_emp_id]}", value=f"Rs. {all_time_balance:,.2f}")
        
        except Exception as e:
            st.error(f"Error fetching all-time balance: {e}")
        
        st.divider()
        st.subheader(f"Ledger History (for date range)")
        # --- END NEW ---

        try:
            conn = get_db_connection()
            query = """
                SELECT 
                    entry_date AS "Date",
                    description AS "Description",
                    credit AS "Credit",
                    debit AS "Debit"
                FROM employee_ledger
                WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                ORDER BY entry_date ASC
            """
            ledger_df = pd.read_sql_query(conn=conn, sql=query, params=(selected_emp_id, str(start_date), str(end_date)))

            # Calculate running balance
            balance_df = ledger_df.copy()
            balance_df['Balance'] = (balance_df['Credit'] - balance_df['Debit']).cumsum()
            
            st.dataframe(balance_df, use_container_width=True)
            
            # Show final balance
            final_balance = balance_df['Balance'].iloc[-1] if not balance_df.empty else 0
            st.metric(label="Current Balance (in range)", value=f"Rs. {final_balance:,.2f}")

            # Download PDF (Req 5)
            if st.button("Download Ledger (PDF)"):
                pdf_bytes = generate_pdf_report(
                    balance_df, 
                    f"Ledger for {employee_list[selected_emp_id]}", 
                    date_range=(start_date, end_date),
                    orientation='P',
                    totals_cols=["Credit", "Debit"]
                )
                
                st.download_button(
                    label="Download Ledger PDF",
                    data=pdf_bytes,
                    file_name=f"Ledger_{employee_list[selected_emp_id].replace(' ', '_')}.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Error fetching ledger: {e}")


# --- Page: Reporting (Requirement 3, 6, 10) ---
def page_reporting():
    st.title("Download Reports")
    
    # --- Report 1: Company Expense Report (Req 3) ---
    st.header("Company Expense Report")
    st.help("Full report of all company expenses, filterable by date and category.")
    
    # Filters
    categories_df = get_all_categories()
    category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
    
    cols = st.columns(3)
    with cols[0]:
        report_start_date = st.date_input("Start Date", date.today().replace(day=1), key="rep_start")
    with cols[1]:
        report_end_date = st.date_input("End Date", date.today(), key="rep_end")
    with cols[2]:
        all_cat_id = 0
        category_list_with_all = {all_cat_id: "ALL CATEGORIES"}
        category_list_with_all.update(category_list)
        
        selected_cat_id = st.selectbox(
            "Filter by Category (Req 6)", 
            options=list(category_list_with_all.keys()), 
            format_func=lambda x: category_list_with_all[x]
        )
    
    if st.button("Generate Expense Report (PDF)"):
        if report_start_date > report_end_date:
            st.error("Start Date cannot be after End Date.")
        else:
            try:
                conn = get_db_connection()
                query = """
                    SELECT 
                        ce.expense_date AS "Date",
                        ce.description AS "Description",
                        ec.name AS "Category",
                        e.name AS "Employee",
                        ce.amount AS "Amount"
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    LEFT JOIN employees e ON ce.employee_id = e.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                """
                params = [str(report_start_date), str(report_end_date)]
                
                report_title = "Company Expense Report"
                if selected_cat_id != all_cat_id:
                    query += " AND ce.category_id = ?"
                    params.append(selected_cat_id)
                    report_title = f"Expense Report: {category_list[selected_cat_id]}"

                query += " ORDER BY ce.expense_date"
                
                report_df = pd.read_sql_query(conn=conn, sql=query, params=params)
                
                pdf_bytes = generate_pdf_report(
                    report_df, 
                    report_title,
                    date_range=(report_start_date, report_end_date),
                    orientation='L',
                    totals_cols=["Amount"]
                )
                
                st.download_button(
                    label="Download Expense Report PDF",
                    data=pdf_bytes,
                    file_name="Expense_Report.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Error generating expense report: {e}")

    st.divider()

    # --- Report 2: Expense Category Sheet (Req 10) ---
    st.header("Expense Category Sheet")
    st.help("Downloads a simple list of all defined expense categories.")
    
    if st.button("Generate Category Sheet (PDF)"):
        try:
            cat_df = get_all_categories()
            cat_df = cat_df.rename(columns={"id": "Category ID", "name": "Category Name"})
            
            pdf_bytes = generate_pdf_report(
                cat_df, 
                "Expense Category Sheet",
                orientation='P'
            )
            
            st.download_button(
                label="Download Category Sheet PDF",
                data=pdf_bytes,
                file_name="Expense_Category_Sheet.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating category sheet: {e}")


# --- Page: Data Import (Requirement 7) ---
def page_data_import():
    st.title("Data Import (Req 7)")
    st.warning("Use this page to import old data. Please use the exact templates provided.", icon="⚠️")

    tab1, tab2, tab3, tab4 = st.tabs(["Import Employees", "Import Categories", "Import Expenses", "Import Ledger Entries"])

    # --- Tab 1: Import Employees ---
    with tab1:
        st.subheader("1. Download Employee Template")
        cols = ["name", "designation", "salary", "bank", "account_title", "account_no", "join_date"]
        excel_data, file_name = generate_excel_template(cols, "employee_import_template.xlsx")
        st.download_button(
            label="Download Employee Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("2. Upload Employee Excel File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="emp_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df)
                
                if st.button("Import Employees"):
                    conn = get_db_connection()
                    try:
                        with st.spinner("Importing..."):
                            df.to_sql("employees", conn, if_exists="append", index=False)
                        st.success(f"Successfully imported {len(df)} employee records.")
                        clear_cache()
                    except Exception as e:
                        st.error(f"Error importing to database: {e}. Check if data is valid.")
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")

    # --- Tab 2: Import Categories ---
    with tab2:
        st.subheader("1. Download Category Template")
        cols = ["name"]
        excel_data, file_name = generate_excel_template(cols, "category_import_template.xlsx")
        st.download_button(
            label="Download Category Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("2. Upload Category Excel File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="cat_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                if 'name' not in df.columns:
                    st.error("Excel file must contain a 'name' column.")
                else:
                    st.dataframe(df)
                    if st.button("Import Categories"):
                        conn = get_db_connection()
                        try:
                            with st.spinner("Importing..."):
                                df.to_sql("expense_categories", conn, if_exists="append", index=False)
                            st.success(f"Successfully imported {len(df)} categories.")
                            clear_cache()
                        except Exception as e:
                            st.error(f"Error importing to database: {e}. Check for duplicates.")
            except Exception as e:
                st.error(f"Error reading Excel file: {e}")

    # --- Tab 3: Import Expenses ---
    with tab3:
        st.subheader("1. Download Expense Template")
        st.help("In the template, use the Category *Name* (e.g., 'Office Supplies') and Employee *Name* (e.g., 'Alice Smith'). Leave Employee Name blank for general expenses.")
        cols = ["expense_date", "description", "amount", "category_name", "employee_name"]
        excel_data, file_name = generate_excel_template(cols, "expense_import_template.xlsx")
        st.download_button(
            label="Download Expense Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("2. Upload Expense Excel File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="exp_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.dataframe(df)
                
                if st.button("Import Expenses"):
                    # Get mappings from names to IDs
                    cat_df = get_all_categories()
                    cat_map = {row['name']: row['id'] for _, row in cat_df.iterrows()}
                    emp_df = get_all_employees()
                    emp_map = {row['name']: row['id'] for _, row in emp_df.iterrows()}

                    conn = get_db_connection()
                    cursor = conn.cursor()
                    imported_count = 0
                    error_list = []

                    with st.spinner("Processing and importing expenses..."):
                        for _, row in df.iterrows():
                            cat_id = cat_map.get(row['category_name'])
                            emp_id = emp_map.get(row['employee_name']) # Will be None if blank or not found
                            
                            if not cat_id:
                                error_list.append(f"Category '{row['category_name']}' not found.")
                                continue
                            
                            cursor.execute(
                                """
                                INSERT INTO company_expenses (expense_date, description, amount, category_id, employee_id)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (row['expense_date'], row['description'], row['amount'], cat_id, emp_id)
                            )
                            
                            # Also add to ledger if employee is linked
                            if emp_id:
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                                    VALUES (?, ?, ?, ?, 0)
                                    """,
                                    (emp_id, row['expense_date'], f"Imported Expense: {row['description']}", row['amount'])
                                )
                            imported_count += 1
                    
                    conn.commit()
                    st.success(f"Successfully imported {imported_count} expense records.")
                    if error_list:
                        st.error("Some rows failed to import:")
                        st.json(error_list)
                    clear_cache()
            except Exception as e:
                st.error(f"Error processing file: {e}")

    # --- Tab 4: Import Ledger Entries ---
    with tab4:
        st.subheader("1. Download Ledger Template")
        st.help("Use the Employee *Name* (e.g., 'Alice Smith'). Fill in EITHER debit OR credit for each row, not both.")
        cols = ["employee_name", "entry_date", "description", "debit", "credit"]
        excel_data, file_name = generate_excel_template(cols, "ledger_import_template.xlsx")
        st.download_button(
            label="Download Ledger Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("2. Upload Ledger Excel File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="led_upload")

        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file).fillna(0) # Fill NaNs with 0
                st.dataframe(df)

                if st.button("Import Ledger Entries"):
                    emp_df = get_all_employees()
                    emp_map = {row['name']: row['id'] for _, row in emp_df.iterrows()}

                    conn = get_db_connection()
                    cursor = conn.cursor()
                    imported_count = 0
                    error_list = []

                    with st.spinner("Processing and importing ledger entries..."):
                        for _, row in df.iterrows():
                            emp_id = emp_map.get(row['employee_name'])
                            
                            if not emp_id:
                                error_list.append(f"Employee '{row['employee_name']}' not found.")
                                continue
                            
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (emp_id, row['entry_date'], row['description'], row['debit'], row['credit'])
                            )
                            imported_count += 1
                    
                    conn.commit()
                    st.success(f"Successfully imported {imported_count} ledger entries.")
                    if error_list:
                        st.error("Some rows failed to import:")
                        st.json(error_list)
                    clear_cache()
            except Exception as e:
                st.error(f"Error processing file: {e}")

# --- Main App ---
def main():
    st.set_page_config(page_title=f"{COMPANY_NAME} App", layout="wide")
    
    # Initialize DB
    init_db()

    # --- Sidebar Navigation ---
    st.sidebar.title(f"{COMPANY_NAME} Portal")
    page_options = {
        "Dashboard": page_dashboard,
        "Employee Management": page_employee_management,
        "Expense Management": page_expense_management,
        "Salary Management": page_salary_management,
        "Employee Ledger": page_employee_ledger,
        "Reporting": page_reporting,
        "Data Import": page_data_import,
    }
    
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()))
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    # --- Load Selected Page ---
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
