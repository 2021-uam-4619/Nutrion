import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
from fpdf import FPDF
from PIL import Image

# --- Page Configuration (P-101) ---
st.set_page_config(
    page_title="Nutrion HR & Expense Management",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- [DATABASE.PY CODE] ---
DATABASE_NAME = "nutrion_hr.db"

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    return conn

def create_tables():
    """Creates all necessary tables if they don't already exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # 1. Employees Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        designation TEXT,
        salary REAL DEFAULT 0,
        account_number TEXT,
        account_title TEXT,
        bank_name TEXT,
        join_date TEXT
    )
    """)
    # 2. Expense Categories Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS expense_categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )
    """)
    # 3. Company Expenses Table (EX-301)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        category_id INTEGER,
        description TEXT,
        amount REAL NOT NULL,
        FOREIGN KEY (category_id) REFERENCES expense_categories (id)
    )
    """)
    # 4. Employee Ledger Table (HR-203)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        date TEXT NOT NULL,
        description TEXT,
        debit REAL DEFAULT 0,  -- Money given to employee (advance) or deduction
        credit REAL DEFAULT 0, -- Money received from employee (payment) or expense
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    )
    """)
    # 5. Employee Expenses (Reimbursements) Table (HR-204)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employee_expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        employee_id INTEGER,
        date TEXT NOT NULL,
        description TEXT,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'Pending', -- 'Pending', 'Processed', 'Paid'
        FOREIGN KEY (employee_id) REFERENCES employees (id)
    )
    """)
    conn.commit()
    conn.close()

# --- Employee CRUD (P-102) ---
def add_employee(name, designation, salary, acc_num, acc_title, bank, join_date):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO employees (name, designation, salary, account_number, account_title, bank_name, join_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (name, designation, salary, acc_num, acc_title, bank, join_date)
    )
    conn.commit()
    conn.close()

def update_employee(emp_id, name, designation, salary, acc_num, acc_title, bank, join_date):
    conn = get_db_connection()
    conn.execute(
        "UPDATE employees SET name=?, designation=?, salary=?, account_number=?, account_title=?, bank_name=?, join_date=? WHERE id=?",
        (name, designation, salary, acc_num, acc_title, bank, join_date, emp_id)
    )
    conn.commit()
    conn.close()

def delete_employee(emp_id):
    conn = get_db_connection()
    conn.execute("DELETE FROM employees WHERE id=?", (emp_id,))
    conn.commit()
    conn.close()

def get_all_employees_df():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
    conn.close()
    return df

def get_employee_by_id(emp_id):
    conn = get_db_connection()
    emp = conn.execute("SELECT * FROM employees WHERE id=?", (emp_id,)).fetchone()
    conn.close()
    return emp

# --- Expense Category CRUD (EX-302) ---
def add_expense_category(name):
    try:
        conn = get_db_connection()
        conn.execute("INSERT INTO expense_categories (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
        return True, "Category added."
    except sqlite3.IntegrityError:
        conn.close()
        return False, "Category already exists."

def get_all_categories_df():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT id, name FROM expense_categories ORDER BY name", conn)
    conn.close()
    return df

# --- Company Expense CRUD (EX-301) ---
def add_company_expense(date, category_id, description, amount):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO company_expenses (date, category_id, description, amount) VALUES (?, ?, ?, ?)",
        (date, category_id, description, amount)
    )
    conn.commit()
    conn.close()

def get_company_expenses_by_date_range(start_date, end_date):
    conn = get_db_connection()
    query = """
    SELECT
        ce.date,
        ec.name as category,
        ce.description,
        ce.amount
    FROM company_expenses ce
    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
    WHERE ce.date BETWEEN ? AND ?
    ORDER BY ce.date, ec.name
    """
    df = pd.read_sql_query(query, conn, params=(start_date, end_date))
    conn.close()
    return df

# --- Employee Expense (Reimbursement) CRUD (HR-204) ---
def add_employee_expense(employee_id, date, description, amount):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO employee_expenses (employee_id, date, description, amount, status) VALUES (?, ?, ?, ?, 'Pending')",
        (employee_id, date, description, amount)
    )
    conn.commit()
    conn.close()

def get_pending_expenses_df():
    conn = get_db_connection()
    query = """
    SELECT
        ee.id,
        e.name as employee,
        ee.date,
        ee.description,
        ee.amount
    FROM employee_expenses ee
    JOIN employees e ON ee.employee_id = e.id
    WHERE ee.status = 'Pending'
    ORDER BY ee.date
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# --- HR-204 Logic ---
def process_employee_expense(expense_id):
    conn = get_db_connection()
    expense = conn.execute("SELECT * FROM employee_expenses WHERE id=?", (expense_id,)).fetchone()
    if not expense:
        conn.close()
        return False, "Expense not found."
    try:
        conn.execute(
            "INSERT INTO employee_ledger (employee_id, date, description, credit) VALUES (?, ?, ?, ?)",
            (expense['employee_id'], datetime.now().strftime("%Y-%m-%d"),
             f"Reimbursement: {expense['description']}", expense['amount'])
        )
        conn.execute("UPDATE employee_expenses SET status='Processed' WHERE id=?", (expense_id,))
        conn.commit()
        conn.close()
        return True, "Expense processed and ledger updated."
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, f"Error: {e}"

# --- Payroll & Ledger Functions (HR-201, HR-202, HR-203) ---
def get_employee_ledger_balance(employee_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT (SUM(debit) - SUM(credit)) FROM employee_ledger WHERE employee_id=?",
        (employee_id,)
    )
    result = cursor.fetchone()
    conn.close()
    balance = result[0] if result[0] is not None else 0
    return balance

def get_employee_ledger_df(employee_id, start_date, end_date):
    conn = get_db_connection()
    query = """
    SELECT
        date,
        description,
        debit,
        credit
    FROM employee_ledger
    WHERE employee_id = ? AND date BETWEEN ? AND ?
    ORDER BY date
    """
    df = pd.read_sql_query(query, conn, params=(employee_id, start_date, end_date))
    
    if not df.empty:
        df['balance'] = (df['debit'].fillna(0) - df['credit'].fillna(0)).cumsum()
    else:
        df['balance'] = pd.Series(dtype='float64')
    conn.close()
    return df

def get_salary_sheet_data(month_year_str):
    conn = get_db_connection()
    query = """
    SELECT
        id, name, designation, salary,
        account_number, account_title, bank_name
    FROM employees
    """
    employees_df = pd.read_sql_query(query, conn)
    
    start_date = f"{month_year_str}-01"
    end_date = (pd.to_datetime(start_date) + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")

    ledger_debits_query = """
    SELECT employee_id, SUM(debit) as deductions
    FROM employee_ledger
    WHERE date BETWEEN ? AND ?
    GROUP BY employee_id
    """
    deductions_df = pd.read_sql_query(ledger_debits_query, conn, params=(start_date, end_date))

    reimbursements_query = """
    SELECT employee_id, SUM(amount) as reimbursements
    FROM employee_expenses
    WHERE status = 'Processed' AND date BETWEEN ? AND ?
    GROUP BY employee_id
    """
    reimbursements_df = pd.read_sql_query(reimbursements_query, conn, params=(start_date, end_date))

    final_sheet = employees_df.merge(deductions_df, left_on='id', right_on='employee_id', how='left')
    final_sheet = final_sheet.merge(reimbursements_df, left_on='id', right_on='employee_id', how='left')
    
    final_sheet['salary'] = final_sheet['salary'].fillna(0)
    final_sheet['deductions'] = final_sheet['deductions'].fillna(0)
    final_sheet['reimbursements'] = final_sheet['reimbursements'].fillna(0)
    final_sheet['net_salary'] = final_sheet['salary'] - final_sheet['deductions'] + final_sheet['reimbursements']
    
    final_cols = [
        'name', 'designation', 'salary', 'deductions', 'reimbursements', 'net_salary',
        'account_number', 'account_title', 'bank_name'
    ]
    final_cols = [col for col in final_cols if col in final_sheet.columns]
    final_sheet = final_sheet[final_cols]
    conn.close()
    return final_sheet

def get_salary_slip_data(employee_id, month_year_str):
    conn = get_db_connection()
    start_date = f"{month_year_str}-01"
    end_date = (pd.to_datetime(start_date) + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
    
    employee = conn.execute("SELECT * FROM employees WHERE id=?", (employee_id,)).fetchone()
    earnings = [{"description": "Base Salary", "amount": employee['salary']}]

    reimbursements_query = """
    SELECT description, amount
    FROM employee_expenses
    WHERE employee_id = ? AND status IN ('Processed', 'Pending') AND date BETWEEN ? AND ?
    """
    reimburse_rows = conn.execute(reimbursements_query, (employee_id, start_date, end_date)).fetchall()
    reimbursements = [{"description": r['description'], "amount": r['amount']} for r in reimburse_rows]
    
    deductions_query = """
    SELECT description, debit
    FROM employee_ledger
    WHERE employee_id = ? AND debit > 0 AND date BETWEEN ? AND ?
    """
    deduction_rows = conn.execute(deductions_query, (employee_id, start_date, end_date)).fetchall()
    deductions = [{"description": d['description'], "amount": d['debit']} for d in deduction_rows]
    conn.close()

    total_earnings = sum(e['amount'] for e in earnings) + sum(r['amount'] for r in reimbursements)
    total_deductions = sum(d['amount'] for d in deductions)
    net_pay = total_earnings - total_deductions
    
    slip_data = {
        "month": datetime.strptime(month_year_str, "%Y-%m").strftime("%B %Y"),
        "earnings": earnings,
        "reimbursements": reimbursements,
        "deductions": deductions,
        "total_earnings": total_earnings,
        "total_deductions": total_deductions,
        "net_pay": net_pay
    }
    return employee, slip_data

# --- Dashboard Functions ---
def get_employee_count():
    conn = get_db_connection()
    count = conn.execute("SELECT COUNT(id) FROM employees").fetchone()[0]
    conn.close()
    return count

def get_total_pending_reimbursements():
    conn = get_db_connection()
    total = conn.execute("SELECT SUM(amount) FROM employee_expenses WHERE status='Pending'").fetchone()[0]
    conn.close()
    return total if total else 0

def get_expenses_current_month():
    conn = get_db_connection()
    start_date = datetime.now().strftime("%Y-%m-01")
    end_date = (pd.to_datetime(start_date) + pd.offsets.MonthEnd(0)).strftime("%Y-%m-%d")
    total = conn.execute(
        "SELECT SUM(amount) FROM company_expenses WHERE date BETWEEN ? AND ?",
        (start_date, end_date)
    ).fetchone()[0]
    conn.close()
    return total if total else 0

# --- [PDF_GENERATOR.PY CODE] ---
class PDF(FPDF):
    """Custom PDF class with header and footer."""
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'Nutrion - Confidential Report', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'HR & Expense Management System', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
        self.cell(0, 10, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'R')

def _draw_table(pdf, df, col_widths):
    """Helper function to draw a DataFrame table in FPDF."""
    pdf.set_font('Arial', 'B', 10)
    pdf.set_fill_color(220, 220, 220)
    for i, col in enumerate(df.columns):
        pdf.cell(col_widths[i], 7, str(col), 1, 0, 'C', 1)
    pdf.ln()

    pdf.set_font('Arial', '', 9)
    pdf.set_fill_color(255)
    for index, row in df.iterrows():
        for i, item in enumerate(row):
            align = 'L'
            if isinstance(item, (int, float)):
                item = f"{item:,.2f}"
                align = 'R'
            pdf.cell(col_widths[i], 6, str(item), 1, 0, align, 1)
        pdf.ln()

def generate_salary_slip_pdf(employee, slip_data):
    """Generates the individual salary slip PDF (HR-202)."""
    pdf = PDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Employee Salary Slip', 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"Pay Period: {slip_data['month']}", 0, 1, 'C')
    pdf.ln(10)

    pdf.set_font('Arial', 'B', 11)
    pdf.cell(95, 7, 'Employee Details', 1, 0, 'C')
    pdf.cell(10, 7, '', 0, 0)
    pdf.cell(85, 7, 'Bank Details', 1, 1, 'C')

    pdf.set_font('Arial', '', 10)
    pdf.cell(30, 6, 'Employee Name:', 0, 0)
    pdf.cell(65, 6, employee['name'], 0, 0)
    pdf.cell(10, 6, '', 0, 0)
    pdf.cell(30, 6, 'Bank Name:', 0, 0)
    pdf.cell(55, 6, employee['bank_name'], 0, 1)
    # ... (rest of slip details) ...
    pdf.cell(30, 6, 'Designation:', 0, 0)
    pdf.cell(65, 6, employee['designation'], 0, 0)
    pdf.cell(10, 6, '', 0, 0)
    pdf.cell(30, 6, 'Account Title:', 0, 0)
    pdf.cell(55, 6, employee['account_title'], 0, 1)
    pdf.cell(30, 6, 'Employee ID:', 0, 0)
    pdf.cell(65, 6, str(employee['id']), 0, 0)
    pdf.cell(10, 6, '', 0, 0)
    pdf.cell(30, 6, 'Account #:', 0, 0)
    pdf.cell(55, 6, employee['account_number'], 0, 1)
    pdf.ln(10)

    col_width_desc = 65
    col_width_amt = 30
    total_width = col_width_desc + col_width_amt
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(total_width, 7, 'Earnings & Reimbursements', 1, 0, 'C')
    pdf.cell(10, 7, '', 0, 0)
    pdf.cell(total_width, 7, 'Deductions', 1, 1, 'C')

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width_desc, 6, 'Description', 1, 0, 'C')
    pdf.cell(col_width_amt, 6, 'Amount (Rs)', 1, 0, 'C')
    pdf.cell(10, 6, '', 0, 0)
    pdf.cell(col_width_desc, 6, 'Description', 1, 0, 'C')
    pdf.cell(col_width_amt, 6, 'Amount (Rs)', 1, 1, 'C')
    
    pdf.set_font('Arial', '', 10)
    max_rows = max(
        len(slip_data['earnings']) + len(slip_data['reimbursements']), 
        len(slip_data['deductions'])
    )
    earnings_list = slip_data['earnings'] + slip_data['reimbursements']
    deductions_list = slip_data['deductions']
    
    for i in range(max_rows):
        if i < len(earnings_list):
            pdf.cell(col_width_desc, 6, earnings_list[i]['description'], 1, 0, 'L')
            pdf.cell(col_width_amt, 6, f"{earnings_list[i]['amount']:,.2f}", 1, 0, 'R')
        else:
            pdf.cell(col_width_desc, 6, '', 1, 0)
            pdf.cell(col_width_amt, 6, '', 1, 0)
        pdf.cell(10, 6, '', 0, 0)
        if i < len(deductions_list):
            pdf.cell(col_width_desc, 6, deductions_list[i]['description'], 1, 0, 'L')
            pdf.cell(col_width_amt, 6, f"{deductions_list[i]['amount']:,.2f}", 1, 0, 'R')
        else:
            pdf.cell(col_width_desc, 6, '', 1, 0)
            pdf.cell(col_width_amt, 6, '', 1, 0)
        pdf.ln()

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width_desc, 6, 'Total Earnings', 1, 0, 'R')
    pdf.cell(col_width_amt, 6, f"{slip_data['total_earnings']:,.2f}", 1, 0, 'R')
    pdf.cell(10, 6, '', 0, 0)
    pdf.cell(col_width_desc, 6, 'Total Deductions', 1, 0, 'R')
    pdf.cell(col_width_amt, 6, f"{slip_data['total_deductions']:,.2f}", 1, 1, 'R')
    pdf.ln(5)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(total_width * 2 + 10, 10, f"Net Pay: Rs. {slip_data['net_pay']:,.2f}", 1, 1, 'C', 1)
    return pdf.output(dest='S').encode('latin-1')

def generate_expense_report_pdf(df, start_date, end_date):
    """Generates the Monthly Company Expense Report (EX-301)."""
    pdf = PDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Company Expense Report', 0, 1, 'C')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"Period: {start_date} to {end_date}", 0, 1, 'C')
    pdf.ln(10)
    category_summary = df.groupby('category')['amount'].sum().reset_index()
    total_expense = df['amount'].sum()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, 'Summary by Category', 0, 1, 'L')
    summary_widths = [100, 90]
    _draw_table(pdf, category_summary, summary_widths)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(summary_widths[0], 7, 'Total Expenses', 1, 0, 'R')
    pdf.cell(summary_widths[1], 7, f'Rs. {total_expense:,.2f}', 1, 1, 'R')
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, 'Detailed Expense List', 0, 1, 'L')
    detail_widths = [25, 40, 95, 30]
    _draw_table(pdf, df, detail_widths)
    return pdf.output(dest='S').encode('latin-1')

def generate_category_sheet_pdf(df):
    """Generates the Expense Category Sheet (EX-302)."""
    pdf = PDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Expense Category Sheet', 0, 1, 'C')
    pdf.ln(10)
    _draw_table(pdf, df, col_widths=[20, 170])
    return pdf.output(dest='S').encode('latin-1')

def generate_employee_ledger_pdf(employee, df, start_date, end_date, start_balance):
    """Generates the Employee Ledger Report (HR-203)."""
    pdf = PDF('P', 'mm', 'A4')
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Employee Ledger Report', 0, 1, 'C')
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 7, 'Employee:', 0, 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"{employee['name']} (ID: {employee['id']})", 0, 1)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 7, 'Period:', 0, 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"{start_date} to {end_date}", 0, 1)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 7, 'Opening Balance:', 0, 0)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, f"Rs. {start_balance:,.2f}", 0, 1)
    pdf.ln(10)
    df_display = df.copy()
    df_display['balance'] = df_display['balance'] + start_balance
    final_balance = df_display['balance'].iloc[-1] if not df_display.empty else start_balance
    _draw_table(pdf, df_display, col_widths=[25, 95, 20, 20, 30])
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(160, 7, 'Closing Balance:', 1, 0, 'R')
    pdf.cell(30, 7, f"Rs. {final_balance:,.2f}", 1, 1, 'R')
    return pdf.output(dest='S').encode('latin-1')

# --- [HELPER FUNCTIONS] ---

# This function is used by multiple pages
def get_employee_options():
    try:
        df = get_all_employees_df()
        if df.empty:
            return []
        options = list(zip(df['id'], df['name'] + " (" + df['designation'].fillna('N/A') + ")"))
        return options
    except Exception as e:
        st.error(f"Could not load employee list: {e}")
        return []

# This function is used by multiple pages
def get_month_year_selector():
    current_year = datetime.now().year
    current_month = datetime.now().month
    col1, col2 = st.columns(2)
    with col1:
        year = st.selectbox("Select Year", options=range(current_year + 1, current_year - 5, -1), index=0)
    with col2:
        month = st.selectbox("Select Month", options=range(1, 13), format_func=lambda m: datetime(2000, m, 1).strftime('%B'), index=current_month - 1)
    return f"{year:04d}-{month:02d}"

# This function is used by multiple pages
def get_date_range_selector():
    st.write("Select a date range:")
    col1, col2 = st.columns(2)
    today = datetime.now().date()
    with col1:
        start_date = st.date_input("Start Date", value=today.replace(day=1))
    with col2:
        end_date = st.date_input("End Date", value=today)
    if start_date > end_date:
        st.error("Start date cannot be after end date.")
        return None, None
    return str(start_date), str(end_date)


# --- [PAGE FUNCTIONS] ---

def dashboard_page():
    """Renders the main application dashboard."""
    st.title("Dashboard")
    st.write("Welcome to the Nutrion HR & Expense Management System.")
    st.header("Key Metrics")
    try:
        total_employees = get_employee_count()
        total_pending_reimbursements = get_total_pending_reimbursements()
        expenses_this_month = get_expenses_current_month()
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Employees", f"{total_employees}")
        col2.metric("Pending Reimbursements", f"Rs. {total_pending_reimbursements:,.2f}")
        col3.metric("Expenses (Current Month)", f"Rs. {expenses_this_month:,.2f}")
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
        st.info("Please ensure the database is set up.")

def employee_management_page():
    """Renders the Employee Management (CRUD) page."""
    st.title("👥 Employee Management (P-102)")
    st.write("Create, Read, Update, and Delete employee records.")
    tab_view, tab_add, tab_update, tab_delete = st.tabs([
        "View All Employees", "Add New Employee", "Update Employee", "Delete Employee"
    ])

    with tab_view:
        st.header("Current Employee Roster")
        try:
            employees_df = get_all_employees_df()
            if employees_df.empty:
                st.info("No employees found. Add employees in the 'Add New Employee' tab.")
            else:
                st.dataframe(employees_df, use_container_width=True)
        except Exception as e:
            st.error(f"Error loading employees: {e}")

    with tab_add:
        st.header("Add New Employee")
        with st.form("add_employee_form", clear_on_submit=True):
            st.subheader("Personal & Role Details")
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Full Name", key="add_name")
                designation = st.text_input("Designation", key="add_des")
            with col2:
                salary = st.number_input("Monthly Salary (Rs)", min_value=0.0, step=1000.0, key="add_sal")
                join_date = st.date_input("Joining Date", key="add_join", value=datetime.now())
            st.subheader("Bank Account Details (HR-201)")
            col1, col2, col3 = st.columns(3)
            with col1:
                bank_name = st.text_input("Bank Name", key="add_bank")
            with col2:
                acc_title = st.text_input("Account Title (exact as per bank)", key="add_title")
            with col3:
                acc_num = st.text_input("Account Number", key="add_num")
            submitted = st.form_submit_button("Add Employee")
            if submitted:
                if not all([name, designation, salary, join_date]):
                    st.warning("Please fill in all Personal & Role fields.")
                else:
                    try:
                        add_employee(name, designation, salary, acc_num, acc_title, bank_name, str(join_date))
                        st.success(f"Employee '{name}' added successfully!")
                    except Exception as e:
                        st.error(f"Error adding employee: {e}")

    employee_options = get_employee_options()

    with tab_update:
        st.header("Update Existing Employee")
        if not employee_options:
            st.warning("No employees available to update.")
        else:
            selected_option = st.selectbox(
                "Select Employee to Update",
                options=employee_options,
                format_func=lambda x: x[1],
                key="update_select"
            )
            if selected_option:
                selected_id = selected_option[0]
                try:
                    emp_data = get_employee_by_id(selected_id)
                    if not emp_data:
                        st.error("Employee not found.")
                    else:
                        with st.form(f"update_form_{selected_id}"):
                            st.subheader(f"Editing: {emp_data['name']}")
                            st.subheader("Personal & Role Details")
                            col1, col2 = st.columns(2)
                            with col1:
                                up_name = st.text_input("Full Name", value=emp_data['name'], key="up_name")
                                up_des = st.text_input("Designation", value=emp_data['designation'], key="up_des")
                            with col2:
                                up_sal = st.number_input("Monthly Salary (Rs)", min_value=0.0, step=1000.0, value=emp_data['salary'], key="up_sal")
                                up_join = st.date_input("Joining Date", value=datetime.fromisoformat(emp_data['join_date']), key="up_join")
                            st.subheader("Bank Account Details")
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                up_bank = st.text_input("Bank Name", value=emp_data['bank_name'], key="up_bank")
                            with col2:
                                up_title = st.text_input("Account Title", value=emp_data['account_title'], key="up_title")
                            with col3:
                                up_num = st.text_input("Account Number", value=emp_data['account_number'], key="up_num")
                            update_submitted = st.form_submit_button("Update Employee")
                            if update_submitted:
                                try:
                                    update_employee(selected_id, up_name, up_des, up_sal, up_num, up_title, up_bank, str(up_join))
                                    st.success(f"Employee '{up_name}' updated successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating employee: {e}")
                except Exception as e:
                    st.error(f"Error fetching employee data: {e}")

    with tab_delete:
        st.header("Delete Employee")
        st.warning("⚠️ This action is permanent and cannot be undone.")
        if not employee_options:
            st.warning("No employees available to delete.")
        else:
            delete_option = st.selectbox(
                "Select Employee to Delete",
                options=employee_options,
                format_func=lambda x: x[1],
                key="delete_select"
            )
            if delete_option:
                delete_id = delete_option[0]
                delete_name = delete_option[1]
                if st.button(f"Delete {delete_name}", type="primary"):
                    try:
                        delete_employee(delete_id)
                        st.success(f"Employee '{delete_name}' has been deleted.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error deleting employee. They may have dependent records. Error: {e}")

def expense_management_page():
    """Renders the Expense Management page."""
    st.title("💸 Expense Management")
    try:
        category_df = get_all_categories_df()
        category_options = list(zip(category_df['id'], category_df['name']))
    except Exception as e:
        st.error(f"Could not load expense categories: {e}")
        category_options = []
    employee_options = get_employee_options()

    tab_company, tab_employee, tab_categories = st.tabs([
        "Company Expenses (EX-301)", "Employee Reimbursements (HR-204)", "Expense Categories (EX-302)"
    ])

    with tab_company:
        st.header("Log New Company Expense")
        st.write("Log general company expenses (e.g., rent, utilities, supplies).")
        with st.form("company_expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Expense Date", value=datetime.now())
                if not category_options:
                    st.warning("Please add expense categories in the 'Expense Categories' tab.")
                    category_id = None
                else:
                    cat_option = st.selectbox("Expense Category", options=category_options, format_func=lambda x: x[1])
                    category_id = cat_option[0] if cat_option else None
            with col2:
                amount = st.number_input("Amount (Rs)", min_value=0.01, step=10.0)
                description = st.text_area("Description / Vendor")
            submitted = st.form_submit_button("Log Expense")
            if submitted:
                if not all([date, category_id, amount, description]):
                    st.warning("Please fill in all fields.")
                else:
                    try:
                        add_company_expense(str(date), category_id, description, amount)
                        st.success("Company expense logged successfully!")
                    except Exception as e:
                        st.error(f"Error logging expense: {e}")

    with tab_employee:
        st.header("Manage Employee Reimbursements")
        sub_tab_add, sub_tab_process = st.tabs(["Submit New Employee Expense", "Process Pending Expenses"])
        with sub_tab_add:
            st.subheader("Submit New Expense for Reimbursement")
            with st.form("employee_expense_form", clear_on_submit=True):
                if not employee_options:
                    st.warning("No employees found. Please add an employee first.")
                    emp_id = None
                else:
                    emp_option = st.selectbox("Employee", options=employee_options, format_func=lambda x: x[1])
                    emp_id = emp_option[0] if emp_option else None
                date = st.date_input("Expense Date", value=datetime.now())
                amount = st.number_input("Amount (Rs)", min_value=0.01, step=10.0)
                description = st.text_area("Description (e.g., 'Travel for client meeting')")
                submitted = st.form_submit_button("Submit Expense")
                if submitted:
                    if not all([emp_id, date, amount, description]):
                        st.warning("Please fill in all fields.")
                    else:
                        try:
                            add_employee_expense(emp_id, str(date), description, amount)
                            st.success("Employee expense submitted and is pending processing.")
                        except Exception as e:
                            st.error(f"Error submitting expense: {e}")
        with sub_tab_process:
            st.subheader("Process Pending Reimbursements (HR-204)")
            st.markdown("""
            **Processing Logic (HR-204):** When you "Process" an expense, it is marked as 'Processed' 
            and a **credit** entry is added to the employee's ledger. 
            This *deducts* from their advance balance (as per requirement 11).
            """)
            try:
                pending_df = get_pending_expenses_df()
                if pending_df.empty:
                    st.info("No pending employee expenses to process.")
                else:
                    pending_df['Process'] = False
                    edited_df = st.data_editor(
                        pending_df,
                        column_config={
                            "id": None,
                            "Process": st.column_config.CheckboxColumn(required=True),
                            "amount": st.column_config.NumberColumn(format="Rs. %.2f")
                        },
                        disabled=["employee", "date", "description", "amount"],
                        hide_index=True, use_container_width=True
                    )
                    if st.button("Process Selected Expenses"):
                        processed_count = 0
                        error_count = 0
                        to_process = edited_df[edited_df['Process']]
                        original_ids = pending_df.iloc[to_process.index]['id']
                        if original_ids.empty:
                            st.warning("No expenses selected for processing.")
                        else:
                            with st.spinner("Processing..."):
                                for expense_id in original_ids:
                                    try:
                                        success, message = process_employee_expense(expense_id)
                                        if success:
                                            processed_count += 1
                                        else:
                                            st.error(f"Failed to process {expense_id}: {message}")
                                            error_count += 1
                                    except Exception as e:
                                        st.error(f"Error processing {expense_id}: {e}")
                                        error_count += 1
                            st.success(f"Successfully processed {processed_count} expenses.")
                            if error_count > 0:
                                st.error(f"Failed to process {error_count} expenses.")
                            st.rerun()
            except Exception as e:
                st.error(f"Error loading pending expenses: {e}")

    with tab_categories:
        st.header("Manage Expense Categories")
        col1, col2 = st.columns([1, 2])
        with col1:
            st.subheader("Add New Category")
            with st.form("category_form", clear_on_submit=True):
                new_category_name = st.text_input("New Category Name")
                submitted = st.form_submit_button("Add Category")
                if submitted:
                    if not new_category_name:
                        st.warning("Category name cannot be empty.")
                    else:
                        success, message = add_expense_category(new_category_name)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        with col2:
            st.subheader("Current Categories")
            if category_df.empty:
                st.info("No categories defined.")
            else:
                st.dataframe(category_df, use_container_width=True, hide_index=True)
                try:
                    pdf_bytes = generate_category_sheet_pdf(category_df)
                    st.download_button(
                        label="Download Category Sheet (PDF)",
                        data=pdf_bytes,
                        file_name="Expense_Category_Sheet.pdf",
                        mime="application/pdf"
                    )
                except Exception as e:
                    st.error(f"Error generating PDF: {e}")

def payroll_page():
    """Renders the Payroll page."""
    st.title("📄 Payroll")
    employee_options = get_employee_options()

    st.header("Generate Full Salary Sheet (HR-201)")
    st.write("Generate a comprehensive salary sheet for all employees for a selected month.")
    month_year_sheet = get_month_year_selector()

    if st.button("Generate Salary Sheet"):
        with st.spinner(f"Generating sheet for {month_year_sheet}..."):
            try:
                sheet_df = get_salary_sheet_data(month_year_sheet)
                st.success("Salary sheet generated successfully.")
                st.dataframe(sheet_df, use_container_width=True)
                st.download_button(
                    label="Download Sheet as CSV",
                    data=sheet_df.to_csv(index=False).encode('utf-8'),
                    file_name=f"Salary_Sheet_{month_year_sheet}.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"Error generating salary sheet: {e}")
                st.exception(e)

    st.divider()

    st.header("Generate Individual Salary Slip (HR-202)")
    st.write("Generate a detailed, downloadable PDF salary slip for a single employee.")
    if not employee_options:
        st.warning("No employees found. Please add an employee first.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            emp_option = st.selectbox("Select Employee", options=employee_options, format_func=lambda x: x[1])
            emp_id = emp_option[0] if emp_option else None
        with col2:
            st.write("Select Pay Period:")
            month_year_slip = get_month_year_selector()

        if st.button("Generate Salary Slip"):
            if not emp_id:
                st.warning("Please select an employee.")
            else:
                with st.spinner("Generating slip..."):
                    try:
                        employee, slip_data = get_salary_slip_data(emp_id, month_year_slip)
                        st.subheader(f"Salary Slip for {employee['name']}")
                        st.text(f"Pay Period: {slip_data['month']}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Earnings & Reimbursements**")
                            earnings_df = pd.DataFrame(slip_data['earnings'] + slip_data['reimbursements'])
                            st.dataframe(earnings_df, hide_index=True)
                            st.metric("Total", f"Rs. {slip_data['total_earnings']:,.2f}")
                        with col2:
                            st.markdown("**Deductions**")
                            deductions_df = pd.DataFrame(slip_data['deductions'])
                            st.dataframe(deductions_df, hide_index=True)
                            st.metric("Total", f"Rs. {slip_data['total_deductions']:,.2f}")
                        
                        st.metric("**Net Pay (Total Earnings - Total Deductions)**", f"Rs. {slip_data['net_pay']:,.2f}")
                        
                        pdf_bytes = generate_salary_slip_pdf(employee, slip_data)
                        st.download_button(
                            label="Download Salary Slip (PDF)",
                            data=pdf_bytes,
                            file_name=f"Salary_Slip_{employee['name']}_{month_year_slip}.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"Error generating salary slip: {e}")
                        st.exception(e)

def reporting_page():
    """Renders the Reporting page."""
    st.title("📊 Reporting")

    st.header("Company Expense Report (EX-301, EX-303)")
    st.write("Generate a detailed report of all company expenses, organized by category, for a specific date range.")
    start_date_ex, end_date_ex = get_date_range_selector()

    if st.button("Generate Expense Report"):
        if start_date_ex and end_date_ex:
            with st.spinner("Fetching expense data..."):
                try:
                    expense_df = get_company_expenses_by_date_range(start_date_ex, end_date_ex)
                    if expense_df.empty:
                        st.info("No company expenses found for this period.")
                    else:
                        st.subheader("Report Summary")
                        summary_df = expense_df.groupby('category')['amount'].sum().reset_index()
                        summary_df = summary_df.sort_values(by='amount', ascending=False)
                        total = expense_df['amount'].sum()
                        
                        col1, col2 = st.columns([1,2])
                        with col1:
                            st.metric("Total Expenses", f"Rs. {total:,.2f}")
                            st.dataframe(summary_df, use_container_width=True, hide_index=True)
                        with col2:
                            st.bar_chart(summary_df.set_index('category')['amount'])
                        
                        st.subheader("Detailed Expense Log")
                        st.dataframe(expense_df, use_container_width=True)
                        
                        pdf_bytes = generate_expense_report_pdf(expense_df, start_date_ex, end_date_ex)
                        st.download_button(
                            label="Download Report (PDF)",
                            data=pdf_bytes,
                            file_name=f"Expense_Report_{start_date_ex}_to_{end_date_ex}.pdf",
                            mime="application/pdf"
                        )
                except Exception as e:
                    st.error(f"Error generating report: {e}")

    st.divider()

    st.header("Employee Ledger Report (HR-203)")
    st.write("View the detailed ledger for a single employee, showing all debits, credits, and a running balance.")
    employee_options = get_employee_options()

    if not employee_options:
        st.warning("No employees found. Please add an employee first.")
    else:
        emp_option = st.selectbox("Select Employee", options=employee_options, format_func=lambda x: x[1], key="ledger_emp_select")
        emp_id = emp_option[0] if emp_option else None
        start_date_ledger, end_date_ledger = get_date_range_selector()

        if st.button("Generate Ledger Report"):
            if emp_id and start_date_ledger and end_date_ledger:
                with st.spinner("Generating ledger..."):
                    try:
                        current_balance = get_employee_ledger_balance(emp_id)
                        st.metric(f"Current Ledger Balance for {emp_option[1]}", f"Rs. {current_balance:,.2f}")
                        st.info("Positive balance: employee owes company. Negative balance: company owes employee.")

                        ledger_df = get_employee_ledger_df(emp_id, start_date_ledger, end_date_ledger)
                        
                        if ledger_df.empty:
                            st.info("No ledger entries found for this employee in this period.")
                        else:
                            st.subheader(f"Ledger Entries: {start_date_ledger} to {end_date_ledger}")
                            st.dataframe(ledger_df, use_container_width=True)
                            
                            employee_details = get_employee_by_id(emp_id)
                            pdf_bytes = generate_employee_ledger_pdf(employee_details, ledger_df, start_date_ledger, end_date_ledger, 0)
                            
                            st.download_button(
                                label="Download Ledger (PDF)",
                                data=pdf_bytes,
                                file_name=f"Ledger_{emp_option[1]}_{start_date_ledger}_to_{end_date_ledger}.pdf",
                                mime="application/pdf"
                            )
                    except Exception as e:
                        st.error(f"Error generating ledger: {e}")

def data_import_page():
    """Renders the Data Import page."""
    st.title("📥 Data Import Utility (P-103)")
    st.header("Import Employees from Excel")
    st.write("Upload an Excel file to bulk-add employees to the system.")

    EXPECTED_COLUMNS = [
        'name', 'designation', 'salary', 'account_number', 
        'account_title', 'bank_name', 'join_date'
    ]

    st.subheader("1. Download Template")
    st.info("Please create an Excel file with the following columns:")
    st.code(f"{', '.join(EXPECTED_COLUMNS)}")
    st.markdown("`join_date` should be in `YYYY-MM-DD` format.")

    st.subheader("2. Upload Your File")
    uploaded_file = st.file_uploader("Choose an Excel file (.xlsx, .xls)", type=['xlsx', 'xls'])

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            st.write("File Preview (first 5 rows):")
            st.dataframe(df.head())
            
            missing_cols = [col for col in EXPECTED_COLUMNS if col not in df.columns]
            if missing_cols:
                st.error(f"Upload failed. Missing columns: {', '.join(missing_cols)}")
            else:
                st.success("File columns are valid.")
                df = df[EXPECTED_COLUMNS]
                df['salary'] = pd.to_numeric(df['salary'], errors='coerce').fillna(0)
                df['join_date'] = pd.to_datetime(df['join_date'], errors='coerce').dt.strftime('%Y-%m-%d')
                df = df.fillna('')
                
                st.subheader("3. Import Data")
                st.write(f"Found **{len(df)}** records to import.")
                
                if st.button("Start Import"):
                    with st.spinner("Importing records..."):
                        success_count = 0
                        error_count = 0
                        errors = []
                        for index, row in df.iterrows():
                            try:
                                if not row['name'] or not row['designation']:
                                    raise ValueError("Name and Designation are required.")
                                add_employee(
                                    name=row['name'], designation=row['designation'], salary=row['salary'],
                                    acc_num=row['account_number'], acc_title=row['account_title'],
                                    bank=row['bank_name'], join_date=row['join_date']
                                )
                                success_count += 1
                            except Exception as e:
                                error_count += 1
                                errors.append(f"Row {index+2}: {row['name']} - Error: {e}")
                    
                    st.success(f"Import complete! Successfully added {success_count} employees.")
                    if error_count > 0:
                        st.error(f"Failed to import {error_count} records.")
                        with st.expander("View Errors"):
                            for error in errors:
                                st.code(error, language=None)
        except Exception as e:
            st.error(f"An error occurred while reading the file: {e}")

# --- [AUTHENTICATION & PAGE ROUTING] ---

def login_page():
    """Renders the login form."""
    st.title("Nutrion HR & Expense Management")
    st.subheader("Developed by DataNex Solution")
    
    REAL_PASSWORD = "nutrion" # Hardcoded password
    with st.form("login_form"):
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        if submitted:
            if password == REAL_PASSWORD:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Incorrect password")

def main_app():
    """Renders the main application after login, with sidebar navigation."""
    st.sidebar.success("You are logged in.")
    st.sidebar.title("Nutrion Portal")
    st.sidebar.write("Developer: DataNex Solution")
    st.sidebar.write("Contact: +92320 7429422")
    st.sidebar.divider()
    
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        [
            "Dashboard", 
            "Employee Management", 
            "Expense Management", 
            "Payroll", 
            "Reporting", 
            "Data Import"
        ]
    )

    if page == "Dashboard":
        dashboard_page()
    elif page == "Employee Management":
        employee_management_page()
    elif page == "Expense Management":
        expense_management_page()
    elif page == "Payroll":
        payroll_page()
    elif page == "Reporting":
        reporting_page()
    elif page == "Data Import":
        data_import_page()

# --- App Entry Point ---
create_tables()  # Ensure tables exist on every run

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if st.session_state["authenticated"]:
    main_app()
else:
    login_page()
