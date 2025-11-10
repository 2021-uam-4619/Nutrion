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
        # Add company logo
        try:
            self.image('logo.png', 10, 8, 25)
        except:
            pass
        
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, COMPANY_NAME, 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 7, self.date_range_str, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-35)
        self.set_font('Arial', '', 10)
        
        footer_width = self.w - self.l_margin - self.r_margin
        
        # Add signature image
        try:
            self.image('Asim Siganture.jpg', self.l_margin, self.get_y(), 40)
            self.ln(15)
        except:
            self.cell(footer_width / 2, 10, "Prepared by: ___________________", 0, 0, 'L')
        
        self.cell(footer_width / 2, 10, "Approved by: _______________", 0, 1, 'R')
        self.ln(10)

        self.set_font('Arial', 'I', 8)
        self.cell(footer_width / 2, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'L')
        self.cell(footer_width / 2, 10, DEVELOPER_INFO, 0, 0, 'R')

    def add_table(self, df, totals_cols=None):
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(224, 235, 255)
        
        num_cols = len(df.columns)
        total_width = self.w - self.l_margin - self.r_margin
        col_width = total_width / num_cols
        
        for col in df.columns:
            self.cell(col_width, 7, str(col).replace('_', ' ').title(), 1, 0, 'C', 1)
        self.ln()

        self.set_font('Arial', '', 8)
        self.set_fill_color(255)
        fill = False
        for index, row in df.iterrows():
            for col in df.columns:
                cell_text = str(row[col])
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        cell_value = row[col]
                        if pd.isna(cell_value):
                            cell_text = "N/A"
                            align = 'L'
                        else:
                            cell_text = f"{float(cell_value):,.2f}"
                            align = 'R'
                        self.cell(col_width, 6, cell_text, 'LR', 0, align, fill)
                    except (ValueError, TypeError):
                        self.cell(col_width, 6, cell_text, 'LR', 0, 'L', fill)
                else:
                    self.cell(col_width, 6, cell_text, 'LR', 0, 'L', fill)
            self.ln()
            fill = not fill
        
        self.cell(total_width, 0, '', 'T', 1)
        
        if totals_cols:
            self.set_font('Arial', 'B', 9)
            self.set_fill_color(240, 240, 240)
            grand_total = 0.0
            
            for i, col in enumerate(df.columns):
                if i == 0:
                    self.cell(col_width, 7, "GRAND TOTAL", 1, 0, 'R', 1)
                elif col in totals_cols:
                    col_total = pd.to_numeric(df[col], errors='coerce').sum()
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
    
    # Check and update employees table
    c.execute("PRAGMA table_info(employees)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'join_date' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN join_date DATE")
        st.success("Updated employees table with join_date column.")
    
    # Check and update employee_ledger table
    c.execute("PRAGMA table_info(employee_ledger)")
    ledger_columns = [column[1] for column in c.fetchall()]
    
    if 'related_expense_id' not in ledger_columns:
        c.execute("ALTER TABLE employee_ledger ADD COLUMN related_expense_id INTEGER")
        st.success("Updated employee_ledger table with related_expense_id column.")
    
    # Create tables if they don't exist
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
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            amount REAL NOT NULL,
            expense_date DATE NOT NULL,
            category_id INTEGER,
            employee_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id) ON DELETE SET NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE SET NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            entry_date DATE NOT NULL,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            related_expense_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (related_expense_id) REFERENCES company_expenses (id) ON DELETE SET NULL
        )
    ''')
    
    # Pre-populate expense categories
    default_categories = [
        "Guard", "Labour", "Bilty Expenses", "Office Rent", "Warehouse Rent",
        "Import Export", "Office Electricity", "FBR", "Office Entertainment",
        "PSID", "Advance", "Commission", "Office Stationery Expense",
        "Employee Expenses", "Other Expense", "Company Expense", "Salary"
    ]
    
    for category in default_categories:
        c.execute("INSERT OR IGNORE INTO expense_categories (name) VALUES (?)", (category,))
    
    conn.commit()

# --- PDF Generation Function ---
def generate_pdf_report(df, title, date_range=None, orientation='L', totals_cols=None):
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
    
    if df.empty:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, "No data found for the selected criteria.", 1, 1, 'C')
    else:
        pdf.add_table(df, totals_cols=totals_cols)
    
    return pdf.output(dest='S').encode('latin-1')

def generate_individual_slip_pdf(emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.report_title = f"Salary Slip - {slip_month.strftime('%B %Y')}"
    pdf.date_range_str = ""
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Employee: {emp_details['name']}", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"Designation: {emp_details['designation']}", 0, 1, 'L')
    pdf.cell(0, 7, f"Base Salary: Rs. {emp_details['salary']:,.2f}", 0, 1, 'L')
    pdf.ln(5)

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

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width * 1.5, 7, "Total", 1, 0, 'R')
    pdf.cell(col_width * 0.75, 7, f"{total_credits:,.2f}", 1, 0, 'R')
    pdf.cell(col_width * 0.75, 7, f"{total_debits:,.2f}", 1, 1, 'R')

    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(210, 210, 210)
    pdf.cell(col_width * 1.5, 10, "Net Salary Payable", 1, 0, 'R', fill=True)
    pdf.cell(col_width * 1.5, 10, f"Rs. {net_salary:,.2f}", 1, 1, 'R', fill=True)
    
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
    df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
    # Convert join_date to string for compatibility with data editor
    if 'join_date' in df.columns:
        df['join_date'] = df['join_date'].astype(str)
    return df

@st.cache_data(ttl=60)
def get_all_categories():
    conn = get_db_connection()
    return pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)

@st.cache_data(ttl=60)
def get_dashboard_stats():
    conn = get_db_connection()
    
    emp_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM employees", conn)
    emp_count = emp_count_df['count'].iloc[0] if not emp_count_df.empty else 0
    
    today = date.today()
    first_day_month = today.replace(day=1)
    last_day_month = (first_day_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    exp_total_df = pd.read_sql_query(
        "SELECT SUM(amount) as total FROM company_expenses WHERE expense_date BETWEEN ? AND ?",
        conn,
        params=(str(first_day_month), str(last_day_month))
    )
    exp_total = exp_total_df['total'].iloc[0] if not exp_total_df.empty and exp_total_df['total'].iloc[0] else 0.0
    
    cat_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM expense_categories", conn)
    cat_count = cat_count_df['count'].iloc[0] if not cat_count_df.empty else 0
    
    return emp_count, exp_total, cat_count

def clear_cache():
    st.cache_data.clear()

def generate_excel_template(columns, file_name):
    df_template = pd.DataFrame(columns=columns)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_template.to_excel(writer, index=False, sheet_name='Sheet1')
        worksheet = writer.sheets['Sheet1']
        worksheet.write_comment('A1', 'Do not change the column names. Fill data in rows below.')
    output.seek(0)
    return output, file_name

# --- Employee Personal Expense Function ---
def add_employee_personal_expense():
    st.subheader("Add Employee Personal Expense")
    
    employees_df = get_all_employees()
    if employees_df.empty:
        st.warning("No employees found. Please add employees first.")
        return
        
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    with st.form("employee_personal_expense_form"):
        cols = st.columns(2)
        with cols[0]:
            employee_id = st.selectbox(
                "Select Employee",
                options=list(employee_list.keys()),
                format_func=lambda x: employee_list[x]
            )
            expense_date = st.date_input("Expense Date", date.today())
        with cols[1]:
            amount = st.number_input("Amount", min_value=0.01, step=100.0)
            description = st.text_input("Description", placeholder="e.g., Travel allowance, Meal expense")
        
        submitted = st.form_submit_button("Add Personal Expense")
        if submitted:
            if employee_id and amount > 0 and description:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Add debit to employee ledger
                    cursor.execute(
                        """
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                        VALUES (?, ?, ?, ?, 0)
                        """,
                        (employee_id, str(expense_date), f"Personal Expense: {description}", amount)
                    )
                    
                    conn.commit()
                    st.success(f"Personal expense of Rs. {amount:,.2f} added to {employee_list[employee_id]}'s ledger.")
                    clear_cache()
                except sqlite3.Error as e:
                    st.error(f"Database error: {e}")
            else:
                st.error("Please fill in all fields.")

# --- Main App Pages ---
def page_dashboard():
    st.title(f"Welcome to {COMPANY_NAME} HR & Expense Manager")
    
    # Add company logo to dashboard
    try:
        st.image('logo.png', width=200)
    except:
        pass
    
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
    - **Employee Personal Expenses**: Add personal expenses that will be deducted from employee salary.
    - **Salary Management**: Generate monthly salary sheets and individual pay slips.
    - **Employee Ledger**: View detailed financial ledgers for each employee.
    - **Reporting**: Download summary reports for expenses and categories.
    - **Data Import**: Bulk-import existing data using Excel templates.
    """)

def page_employee_management():
    st.title("Employee Management")
    
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

    st.subheader("Manage Employees")
    st.markdown("""
    Use the table below to edit or delete employees.
    - **To Edit:** Click on any cell, make your change, and press Enter.
    - **To Delete:** Click the `x` icon at the end of a row.
    - **To Add:** Click the `+` icon at the bottom to add a new row.
    
    **You must click the 'Save Changes' button below the table to apply all edits.**
    """)
    try:
        employees_df = get_all_employees()
        if employees_df.empty:
            st.info("No employees found. Add employees using the form above.")
            return

        # Convert join_date to string for data editor compatibility
        if 'join_date' in employees_df.columns:
            employees_df['join_date'] = employees_df['join_date'].astype(str)

        edited_df = st.data_editor(
            employees_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "join_date": st.column_config.TextColumn("Join Date")
            },
            key="employee_editor"
        )

        if st.button("Save Changes"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            original_ids = set(employees_df['id'])
            current_ids = set(edited_df['id'].dropna())
            
            deleted_ids = original_ids - current_ids
            if deleted_ids:
                for del_id in deleted_ids:
                    cursor.execute("DELETE FROM employees WHERE id = ?", (int(del_id),))
                st.success(f"Deleted {len(deleted_ids)} employee(s).")

            for _, row in edited_df.iterrows():
                join_date_str = str(row['join_date']) if pd.notna(row['join_date']) else None
                
                if pd.isna(row['id']):
                    if row['name']:
                        cursor.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (row['name'], row['designation'], row['salary'], row['bank'], row['account_title'], row['account_no'], join_date_str)
                        )
                else:
                    cursor.execute(
                        """
                        UPDATE employees SET
                        name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, account_no = ?, join_date = ?
                        WHERE id = ?
                        """,
                        (row['name'], row['designation'], row['salary'], row['bank'], row['account_title'], row['account_no'], join_date_str, int(row['id']))
                    )
            
            conn.commit()
            st.success("Changes saved successfully.")
            clear_cache()
            st.rerun()

    except Exception as e:
        st.error(f"Error loading employees: {e}")

def page_expense_management():
    st.title("Expense Management")

    st.subheader("Log New Company Expense")
    
    categories_df = get_all_categories()
    category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
    
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
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
        
        st.info("If this expense is an advance or deduction for an employee, select their name. This amount will be deducted from their salary.")
        employee_id = st.selectbox("Employee (Optional)", options=list(employee_list_with_none.keys()), format_func=lambda x: employee_list_with_none[x])

        submitted = st.form_submit_button("Log Expense")
        if submitted:
            if amount > 0 and category_id:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        """
                        INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (description, amount, str(expense_date), category_id, employee_id if employee_id != 0 else None)
                    )
                    
                    expense_id = cursor.lastrowid
                    
                    if employee_id != 0:
                        ledger_desc = f"Company Expense: {description} (Ref ID: {expense_id})"
                        cursor.execute(
                            """
                            INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, related_expense_id)
                            VALUES (?, ?, ?, ?, 0, ?)
                            """,
                            (employee_id, str(expense_date), ledger_desc, amount, expense_id)
                        )
                        st.success(f"Company expense logged and Rs. {amount:,.2f} will be deducted from {employee_list[employee_id]}'s salary.")
                    else:
                        st.success("Company expense logged successfully.")
                    
                    conn.commit()
                    clear_cache()
                except sqlite3.Error as e:
                    st.error(f"Database error: {e}")
            else:
                st.error("Please fill in all fields (Amount and Category).")

    st.divider()
    
    st.subheader("Manage Expense Categories")
    st.markdown("""
    Use the table below to edit or delete categories.
    - **To Edit:** Click on the 'name' cell, make your change, and press Enter.
    - **To Delete:** Click the `x` icon at the end of a row.
    - **To Add:** Click the `+` icon at the bottom and add a new name.
    
    **You must click the 'Save Category Changes' button below the table to apply all edits.**
    """)
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
                ce.category_id,
                ce.employee_id
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
        
        st.dataframe(expenses_df[cols_to_show], use_container_width=True)

        st.markdown("---")
        st.markdown("**Edit or Delete an Expense**")
        expense_ids = expenses_df['id'].tolist()
        expense_to_edit = st.selectbox("Select Expense ID to Edit/Delete", options=expense_ids, format_func=lambda x: f"ID: {x} - {expenses_df[expenses_df['id'] == x]['description'].values[0]}", index=None)

        if expense_to_edit:
            expense_details = expenses_df[expenses_df['id'] == expense_to_edit].iloc[0]
            
            if st.button(f"Delete Expense ID {expense_to_edit}", type="primary"):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Delete related ledger entry if exists
                    cursor.execute(
                        "DELETE FROM employee_ledger WHERE related_expense_id = ?",
                        (int(expense_to_edit),)
                    )
                    
                    cursor.execute("DELETE FROM company_expenses WHERE id = ?", (int(expense_to_edit),))
                    conn.commit()
                    st.success(f"Expense ID {expense_to_edit} and its related ledger entry deleted.")
                    clear_cache()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting expense: {e}")
            
            with st.expander("Edit Expense Details"):
                if pd.notna(expense_details['employee_id']):
                    st.warning("""
                    **Accounting Warning:** This expense is linked to an employee's ledger. 
                    Editing the amount here will **NOT** automatically update their ledger, which may cause accounting errors.
                    
                    **Recommendation:** To change the amount, please **delete** this expense (which will also remove the ledger debit) and **create a new one** with the correct amount.
                    """, icon="⚠️")

                categories_df = get_all_categories()
                category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
                cat_ids = list(category_list.keys())
                
                current_cat_id = expense_details['category_id']
                if pd.notna(current_cat_id) and current_cat_id not in cat_ids:
                    st.error(f"Error: The original category (ID: {current_cat_id}) for this expense was deleted. Please select a new, valid category.")
                    cat_ids.append(current_cat_id)
                    category_list[current_cat_id] = f"INVALID CATEGORY (ID: {current_cat_id})"
                    default_index = 0 
                elif pd.notna(current_cat_id):
                    default_index = cat_ids.index(current_cat_id)
                else:
                    default_index = 0
                
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
                            index=default_index
                        )
                    with cols[2]:
                        st.text_input("Employee (Read-only)", value=expense_details.get('employee', 'N/A'), disabled=True)

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

# --- Employee Personal Expenses Page ---
def page_employee_personal_expenses():
    st.title("Employee Personal Expenses")
    
    st.info("""
    Use this page to add personal expenses for employees. These expenses will be deducted from their salary.
    Examples: Travel allowance, meal expenses, phone bills, etc.
    """)
    
    add_employee_personal_expense()
    
    st.divider()
    
    st.subheader("Recent Personal Expenses")
    try:
        conn = get_db_connection()
        personal_expenses_df = pd.read_sql_query(
            """
            SELECT 
                el.entry_date as "Date",
                e.name as "Employee",
                el.description as "Description",
                el.debit as "Amount"
            FROM employee_ledger el
            JOIN employees e ON el.employee_id = e.id
            WHERE el.description LIKE 'Personal Expense:%'
            ORDER BY el.entry_date DESC
            LIMIT 50
            """, conn
        )
        
        if not personal_expenses_df.empty:
            st.dataframe(personal_expenses_df, use_container_width=True)
        else:
            st.info("No personal expenses recorded yet.")
            
    except Exception as e:
        st.error(f"Error loading personal expenses: {e}")

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
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    st.divider()

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

    st.subheader("2. View & Download Salary Sheet")
    st.markdown("This sheet calculates the Net Salary based on all ledger entries for the selected month.")
    
    if st.button("Generate Salary Sheet"):
        try:
            conn = get_db_connection()
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

    st.subheader("3. Generate Individual Salary Slip")
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    if not employee_list:
        st.warning("Cannot generate slip: No employees found in the system. Please add employees first.", icon="⚠️")
        return
    
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

            first_day_slip = slip_month.replace(day=1)
            last_day_slip = (first_day_slip.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            with get_db_connection() as conn:
                ledger_df = pd.read_sql_query(
                    """
                    SELECT description, credit, debit 
                    FROM employee_ledger 
                    WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                    ORDER BY entry_date
                    """, 
                    conn, 
                    params=(selected_emp_id, first_day_slip, last_day_slip)
                )

            total_credits = ledger_df['credit'].sum()
            total_debits = ledger_df['debit'].sum()
            net_salary = total_credits - total_debits

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
    
    show_all_time = st.checkbox("Show All-Time Ledger? (Disables date filter)", key="all_time_toggle")

    cols = st.columns(2)
    today = date.today()
    with cols[0]:
        start_date = st.date_input("Start Date", today.replace(day=1), disabled=show_all_time)
    with cols[1]:
        end_date = st.date_input("End Date", today, disabled=show_all_time)

    if selected_emp_id:
        if not show_all_time and start_date > end_date:
            st.error("Start Date cannot be after End Date.")
            return

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
        st.subheader(f"Ledger History")

        try:
            conn = get_db_connection()
            
            if show_all_time:
                query = """
                    SELECT 
                        entry_date AS "Date",
                        description AS "Description",
                        credit AS "Credit",
                        debit AS "Debit"
                    FROM employee_ledger
                    WHERE employee_id = ?
                    ORDER BY entry_date ASC
                """
                params = (selected_emp_id,)
                date_range = (None, None)
            else:
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
                params = (selected_emp_id, str(start_date), str(end_date))
                date_range = (start_date, end_date)

            ledger_df = pd.read_sql_query(query, conn, params=params)

            balance_df = ledger_df.copy()
            balance_df['Balance'] = (balance_df['Credit'] - balance_df['Debit']).cumsum()
            
            st.dataframe(balance_df, use_container_width=True)
            
            final_balance = balance_df['Balance'].iloc[-1] if not balance_df.empty else 0
            if not show_all_time:
                st.metric(label="Balance (in selected date range)", value=f"Rs. {final_balance:,.2f}")

            if st.button("Download Ledger (PDF)"):
                pdf_bytes = generate_pdf_report(
                    balance_df, 
                    f"Ledger for {employee_list[selected_emp_id]}", 
                    date_range=date_range if not show_all_time else None,
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

def page_reporting():
    st.title("Download Reports")
    
    st.header("Company Expense Report")
    st.markdown("Full report of all company expenses, filterable by date and category.")
    
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
            "Filter by Category", 
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
                
                report_df = pd.read_sql_query(query, conn, params=params)
                
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

    st.header("Expense Category Sheet")
    st.markdown("Downloads a simple list of all defined expense categories.")
    
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

def page_data_import():
    st.title("Data Import")
    st.warning("Use this page to import old data. Please use the exact templates provided.", icon="⚠️")

    tab1, tab2, tab3, tab4 = st.tabs(["Import Employees", "Import Categories", "Import Expenses", "Import Ledger Entries"])

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

    with tab3:
        st.subheader("1. Download Expense Template")
        st.markdown("In the template, use the Category *Name* (e.g., 'Office Supplies') and Employee *Name* (e.g., 'Alice Smith'). Leave Employee Name blank for general expenses.")
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
                            emp_id = emp_map.get(row['employee_name'])
                            
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
                            
                            expense_id = cursor.lastrowid
                            
                            if emp_id:
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, related_expense_id)
                                    VALUES (?, ?, ?, ?, 0, ?)
                                    """,
                                    (emp_id, row['expense_date'], f"Imported Expense: {row['description']}", row['amount'], expense_id)
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

    with tab4:
        st.subheader("1. Download Ledger Template")
        st.markdown("Use the Employee *Name* (e.g., 'Alice Smith'). Fill in EITHER debit OR credit for each row, not both.")
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
                df = pd.read_excel(uploaded_file).fillna(0)
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
    
    init_db()

    st.sidebar.title(f"{COMPANY_NAME} Portal")
    # Add logo to sidebar
    try:
        st.sidebar.image('logo.png', width=150)
    except:
        pass
        
    page_options = {
        "Dashboard": page_dashboard,
        "Employee Management": page_employee_management,
        "Expense Management": page_expense_management,
        "Employee Personal Expenses": page_employee_personal_expenses,
        "Salary Management": page_salary_management,
        "Employee Ledger": page_employee_ledger,
        "Reporting": page_reporting,
        "Data Import": page_data_import,
    }
    
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()))
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
