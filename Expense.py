import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
import uuid
import tempfile
from PIL import Image

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# --- PDF Class with Header/Footer and Logo ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""

    def header(self):
        # Add company logo
        try:
            # Try different possible logo paths
            logo_paths = ['logo.png', 'nutrion_logo.png', 'company_logo.png', 'assets/logo.png']
            logo_found = False
            for logo_path in logo_paths:
                if os.path.exists(logo_path):
                    self.image(logo_path, 10, 8, 25)
                    logo_found = True
                    break
            
            if not logo_found:
                # Create a simple text logo if image not found
                self.set_font('Arial', 'B', 16)
                self.cell(25, 10, COMPANY_NAME[:8], 0, 0, 'L')
        except:
            # Fallback if logo loading fails
            self.set_font('Arial', 'B', 16)
            self.cell(25, 10, COMPANY_NAME[:8], 0, 0, 'L')
        
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
            signature_paths = ['signature.png', 'assets/signature.png']
            sig_found = False
            for sig_path in signature_paths:
                if os.path.exists(sig_path):
                    self.image(sig_path, self.l_margin, self.get_y(), 40)
                    self.ln(15)
                    sig_found = True
                    break
            
            if not sig_found:
                self.cell(footer_width / 2, 10, "Prepared by: ___________________", 0, 0, 'L')
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
        total_width = self.w - self.l_margin - self.r_margin - 10
        
        # Calculate dynamic column widths based on content
        col_widths = self.calculate_column_widths(df, total_width, num_cols)
        
        # Draw header
        x_position = self.get_x()
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], 7, str(col).replace('_', ' ').title(), 1, 0, 'C', 1)
        self.ln()

        # Draw rows
        self.set_font('Arial', '', 8)
        self.set_fill_color(255)
        fill = False
        
        for index, row in df.iterrows():
            max_height = 6
            line_heights = []
            
            # Calculate required height for each cell in this row
            for i, col in enumerate(df.columns):
                cell_text = str(row[col])
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        cell_value = row[col]
                        if pd.isna(cell_value):
                            cell_text = "N/A"
                        else:
                            cell_text = f"{float(cell_value):,.2f}"
                    except (ValueError, TypeError):
                        pass
                
                # Calculate text height for this cell
                lines = self.wrap_text(cell_text, col_widths[i] - 1)
                line_heights.append(len(lines) * 6)
            
            # Use the maximum height for this row
            row_height = max(line_heights) if line_heights else 6
            max_height = max(max_height, row_height)
            
            # Draw each cell
            x_position = self.get_x()
            for i, col in enumerate(df.columns):
                cell_text = str(row[col])
                align = 'L'
                
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        cell_value = row[col]
                        if pd.isna(cell_value):
                            cell_text = "N/A"
                            align = 'L'
                        else:
                            cell_text = f"{float(cell_value):,.2f}"
                            align = 'R'
                    except (ValueError, TypeError):
                        align = 'L'
                
                # Wrap text and draw cell
                self.set_xy(x_position, self.get_y())
                lines = self.wrap_text(cell_text, col_widths[i] - 1)
                
                # Draw cell background
                self.set_fill_color(240, 240, 240) if fill else self.set_fill_color(255)
                self.cell(col_widths[i], max_height, '', 1, 0, 'L', 1)
                
                # Draw text
                self.set_xy(x_position + 1, self.get_y())
                text_y = self.get_y()
                for j, line in enumerate(lines):
                    self.set_xy(x_position + 1, text_y + (j * 6))
                    self.cell(col_widths[i] - 2, 6, line, 0, 0, align)
                
                x_position += col_widths[i]
            
            self.ln(max_height)
            fill = not fill
        
        # Totals row
        if totals_cols:
            self.set_font('Arial', 'B', 9)
            self.set_fill_color(240, 240, 240)
            x_position = self.get_x()
            
            for i, col in enumerate(df.columns):
                if i == 0:
                    self.cell(col_widths[i], 7, "GRAND TOTAL", 1, 0, 'R', 1)
                elif col in totals_cols:
                    col_total = pd.to_numeric(df[col], errors='coerce').sum()
                    self.cell(col_widths[i], 7, f"{col_total:,.2f}", 1, 0, 'R', 1)
                else:
                    self.cell(col_widths[i], 7, "", 1, 0, 'C', 1)
            self.ln()

    def calculate_column_widths(self, df, total_width, num_cols):
        """Calculate dynamic column widths based on content"""
        min_width = 15
        max_width = total_width / 2
        
        col_widths = []
        for col in df.columns:
            header_width = len(str(col).replace('_', ' ').title()) * 2.5
            content_samples = df[col].astype(str).str[:30]
            max_content_len = content_samples.str.len().max()
            content_width = max_content_len * 1.8
            
            col_width = max(header_width, content_width, min_width)
            col_width = min(col_width, max_width)
            col_widths.append(col_width)
        
        total_current_width = sum(col_widths)
        if total_current_width > total_width:
            scale_factor = total_width / total_current_width
            col_widths = [max(min_width, w * scale_factor) for w in col_widths]
        else:
            extra_space = total_width - total_current_width
            if extra_space > 0:
                col_widths = [w + (extra_space / num_cols) for w in col_widths]
        
        return col_widths

    def wrap_text(self, text, max_width):
        """Wrap text to fit within specified width"""
        if not text:
            return ['']
        
        words = str(text).split(' ')
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if self.get_string_width(test_line) < max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word] if self.get_string_width(word) < max_width else [word[:int(max_width/2)] + '...']
        
        if current_line:
            lines.append(' '.join(current_line))
        
        final_lines = []
        for line in lines:
            while line and self.get_string_width(line) > max_width:
                line = line[:-1]
            final_lines.append(line if line else '')
        
        return final_lines if final_lines else ['']

def generate_individual_slip_pdf(emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.report_title = f"Salary Slip - {slip_month.strftime('%B %Y')}"
    pdf.date_range_str = ""
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 12, f"Employee: {emp_details['name']}", 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Designation: {emp_details['designation']}", 0, 1, 'L')
    pdf.cell(0, 8, f"Base Salary: Rs. {emp_details['salary']:,.2f}", 0, 1, 'L')
    pdf.ln(8)

    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(224, 235, 255)
    pdf.cell(0, 10, "Earnings & Deductions", 1, 1, 'C', fill=True)
    
    total_width = pdf.w - 2 * pdf.l_margin
    desc_width = total_width * 0.6
    amount_width = (total_width - desc_width) / 2
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(desc_width, 8, "Description", 1, 0, 'C')
    pdf.cell(amount_width, 8, "Credits (Rs.)", 1, 0, 'C')
    pdf.cell(amount_width, 8, "Debits (Rs.)", 1, 1, 'C')

    pdf.set_font('Arial', '', 9)
    if ledger_df.empty:
        pdf.cell(0, 8, "No ledger activity found for this month.", 1, 1, 'C')
    else:
        for _, row in ledger_df.iterrows():
            desc_text = str(row['description'])
            desc_lines = pdf.wrap_text(desc_text, desc_width - 2)
            
            credit_text = f"{row['credit']:,.2f}" if row['credit'] > 0 else "0.00"
            debit_text = f"{row['debit']:,.2f}" if row['debit'] > 0 else "0.00"
            
            row_height = max(8, len(desc_lines) * 8)
            
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(desc_width, 8, desc_text, 1, 'L')
            
            pdf.set_xy(x + desc_width, y)
            pdf.cell(amount_width, row_height, credit_text, 1, 0, 'R')
            
            pdf.set_xy(x + desc_width + amount_width, y)
            pdf.cell(amount_width, row_height, debit_text, 1, 1, 'R')

    pdf.set_font('Arial', 'B', 10)
    pdf.cell(desc_width, 8, "Total", 1, 0, 'R')
    pdf.cell(amount_width, 8, f"{total_credits:,.2f}", 1, 0, 'R')
    pdf.cell(amount_width, 8, f"{total_debits:,.2f}", 1, 1, 'R')

    pdf.ln(8)
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(210, 210, 210)
    pdf.cell(desc_width, 12, "Net Salary Payable", 1, 0, 'R', fill=True)
    pdf.cell(amount_width * 2, 12, f"Rs. {net_salary:,.2f}", 1, 1, 'R', fill=True)
    
    pdf.ln(12)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, "Bank Details", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, f"  Bank: {emp_details['bank']}", 0, 1, 'L')
    pdf.cell(0, 6, f"  Account Title: {emp_details['account_title']}", 0, 1, 'L')
    pdf.cell(0, 6, f"  Account No: {emp_details['account_no']}", 0, 1, 'L')

    return pdf.output(dest='S').encode('latin-1')

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
    
    required_columns = {
        'join_date': 'DATE',
        'employee_id': 'TEXT',
        'status': 'TEXT DEFAULT "Active"',
        'bank_branch': 'TEXT',
        'cnic': 'TEXT'
    }
    
    for col, col_type in required_columns.items():
        if col not in columns:
            c.execute(f"ALTER TABLE employees ADD COLUMN {col} {col_type}")
    
    # Check and update employee_ledger table
    c.execute("PRAGMA table_info(employee_ledger)")
    ledger_columns = [column[1] for column in c.fetchall()]
    
    required_ledger_columns = {
        'related_expense_id': 'INTEGER',
        'transaction_type': 'TEXT DEFAULT "Salary"',
        'month_year': 'TEXT'
    }
    
    for col, col_type in required_ledger_columns.items():
        if col not in ledger_columns:
            c.execute(f"ALTER TABLE employee_ledger ADD COLUMN {col} {col_type}")
    
    # Create tables if they don't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            name TEXT NOT NULL,
            designation TEXT,
            salary REAL DEFAULT 0,
            bank TEXT,
            account_title TEXT,
            account_no TEXT,
            bank_branch TEXT,
            cnic TEXT,
            join_date DATE,
            status TEXT DEFAULT "Active",
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT DEFAULT "Company"
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
            payment_method TEXT DEFAULT "Cash",
            reference_no TEXT,
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
            transaction_type TEXT DEFAULT "Salary",
            month_year TEXT,
            related_expense_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (related_expense_id) REFERENCES company_expenses (id) ON DELETE SET NULL
        )
    ''')
    
    # Pre-populate expense categories
    default_categories = [
        ("Guard", "Company"), ("Labour", "Company"), ("Bilty Expenses", "Company"), 
        ("Office Rent", "Company"), ("Warehouse Rent", "Company"), ("Import Export", "Company"),
        ("Office Electricity", "Company"), ("FBR", "Company"), ("Office Entertainment", "Company"),
        ("PSID", "Company"), ("Advance", "Employee"), ("Commission", "Employee"), 
        ("Office Stationery Expense", "Company"), ("Employee Expenses", "Employee"), 
        ("Other Expense", "Company"), ("Company Expense", "Company"), ("Salary", "Employee"),
        ("Travel", "Employee"), ("Medical", "Employee"), ("Bonus", "Employee")
    ]
    
    for category_name, category_type in default_categories:
        c.execute("INSERT OR IGNORE INTO expense_categories (name, type) VALUES (?, ?)", 
                 (category_name, category_type))
    
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

# --- Helper Functions ---
@st.cache_data(ttl=60)
def get_all_employees():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM employees WHERE status = 'Active' ORDER BY name", conn)
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
    
    emp_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM employees WHERE status = 'Active'", conn)
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
    
    # Calculate total salary payable
    salary_total_df = pd.read_sql_query(
        "SELECT SUM(salary) as total FROM employees WHERE status = 'Active'",
        conn
    )
    salary_total = salary_total_df['total'].iloc[0] if not salary_total_df.empty and salary_total_df['total'].iloc[0] else 0.0
    
    return emp_count, exp_total, cat_count, salary_total

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

def get_employee_balance(employee_id):
    """Get current balance for an employee"""
    conn = get_db_connection()
    balance_df = pd.read_sql_query(
        "SELECT SUM(credit) - SUM(debit) as balance FROM employee_ledger WHERE employee_id = ?",
        conn,
        params=(employee_id,)
    )
    return balance_df['balance'].iloc[0] if not balance_df.empty else 0.0

def generate_employee_id():
    """Generate unique employee ID"""
    return f"NUT{datetime.now().strftime('%y%m%d')}{uuid.uuid4().hex[:4].upper()}"

# --- Enhanced Employee Expense Management System ---
def page_employee_expense_management():
    st.title("💰 Employee Expense Management")
    
    # Quick Stats
    employees_df = get_all_employees()
    if not employees_df.empty:
        cols = st.columns(4)
        total_employees = len(employees_df)
        total_salary = employees_df['salary'].sum()
        
        # Calculate total expenses and advances
        conn = get_db_connection()
        expenses_df = pd.read_sql_query(
            "SELECT SUM(debit) as total_debits FROM employee_ledger",
            conn
        )
        total_expenses = expenses_df['total_debits'].iloc[0] if not expenses_df.empty else 0
        
        with cols[0]:
            st.metric("Total Employees", total_employees)
        with cols[1]:
            st.metric("Total Monthly Salary", f"Rs. {total_salary:,.2f}")
        with cols[2]:
            st.metric("Total Employee Expenses", f"Rs. {total_expenses:,.2f}")
        with cols[3]:
            net_payable = total_salary - total_expenses
            st.metric("Net Salary Payable", f"Rs. {net_payable:,.2f}")
    
    st.divider()
    
    # Main Tabs for different functionalities
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Add Expense", "📊 Employee Balances", "🔍 Expense History", 
        "💸 Salary Processing", "🧾 Individual Salary Slips"
    ])
    
    with tab1:
        st.subheader("Add Employee Expense/Advance")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("No employees found. Please add employees first.")
        else:
            employee_list = {row['id']: f"{row['name']} - {row['designation']} (Salary: Rs. {row['salary']:,.2f})" 
                           for index, row in employees_df.iterrows()}
            
            with st.form("add_employee_expense", clear_on_submit=True):
                cols = st.columns(3)
                with cols[0]:
                    employee_id = st.selectbox(
                        "Select Employee",
                        options=list(employee_list.keys()),
                        format_func=lambda x: employee_list[x],
                        key="expense_employee"
                    )
                    current_balance = get_employee_balance(employee_id)
                    st.info(f"Current Balance: Rs. {current_balance:,.2f}")
                    
                with cols[1]:
                    expense_date = st.date_input("Expense Date", date.today())
                    amount = st.number_input("Amount (Rs.)", min_value=0.01, step=100.0)
                    categories = get_all_categories()
                    expense_category = st.selectbox(
                        "Category",
                        options=categories['id'].tolist(),
                        format_func=lambda x: categories[categories['id'] == x]['name'].iloc[0]
                    )
                
                with cols[2]:
                    expense_type = st.selectbox(
                        "Expense Type",
                        ["Personal Expense", "Travel Advance", "Loan Advance", "Other Deduction", "Bonus", "Other Credit"]
                    )
                    description = st.text_input("Description", placeholder="e.g., Travel allowance, Meal expense")
                
                submitted = st.form_submit_button("💾 Add Expense")
                if submitted:
                    if employee_id and amount > 0 and description:
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            
                            # Determine if it's debit or credit
                            if expense_type in ["Personal Expense", "Travel Advance", "Loan Advance", "Other Deduction"]:
                                # Debit entry (expense/advance)
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, transaction_type)
                                    VALUES (?, ?, ?, ?, 0, ?)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount, expense_type)
                                )
                                message_type = "expense"
                            else:
                                # Credit entry (bonus/other credit)
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, transaction_type)
                                    VALUES (?, ?, ?, 0, ?, ?)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount, expense_type)
                                )
                                message_type = "credit"
                            
                            conn.commit()
                            employee_name = employees_df[employees_df['id'] == employee_id]['name'].iloc[0]
                            st.success(f"{expense_type} of Rs. {amount:,.2f} added to {employee_name}'s ledger as {message_type}.")
                            clear_cache()
                            st.rerun()
                        except sqlite3.Error as e:
                            st.error(f"Database error: {e}")
                    else:
                        st.error("Please fill in all required fields.")
    
    with tab2:
        st.subheader("Employee Current Balances")
        
        employees_df = get_all_employees()
        if not employees_df.empty:
            # Calculate balances for all employees
            balance_data = []
            for _, emp in employees_df.iterrows():
                balance = get_employee_balance(emp['id'])
                balance_data.append({
                    'Employee ID': emp.get('employee_id', 'N/A'),
                    'Name': emp['name'],
                    'Designation': emp['designation'],
                    'Base Salary': emp['salary'],
                    'Current Balance': balance,
                    'Net Payable': emp['salary'] + balance
                })
            
            balance_df = pd.DataFrame(balance_data)
            
            # Display with color coding
            styled_df = balance_df.style.format({
                'Base Salary': 'Rs. {:,.2f}',
                'Current Balance': 'Rs. {:,.2f}',
                'Net Payable': 'Rs. {:,.2f}'
            }).applymap(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else 'color: black')
            
            st.dataframe(styled_df, use_container_width=True)
            
            # Download option
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download Balance Sheet (PDF)"):
                    pdf_bytes = generate_pdf_report(
                        balance_df, 
                        "Employee Balance Sheet",
                        orientation='L',
                        totals_cols=["Base Salary", "Current Balance", "Net Payable"]
                    )
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes,
                        file_name="Employee_Balance_Sheet.pdf",
                        mime="application/pdf",
                        key="balance_pdf"
                    )
            with col2:
                # Excel download
                csv = balance_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Balance Sheet (Excel)",
                    data=csv,
                    file_name="Employee_Balance_Sheet.csv",
                    mime="text/csv",
                    key="balance_csv"
                )
        else:
            st.info("No employees found.")
    
    with tab3:
        st.subheader("Expense History")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("No employees found.")
        else:
            employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
            
            cols = st.columns(3)
            with cols[0]:
                selected_emp_id = st.selectbox(
                    "Select Employee",
                    options=list(employee_list.keys()),
                    format_func=lambda x: employee_list[x],
                    key="history_employee"
                )
            with cols[1]:
                start_date = st.date_input("Start Date", date.today().replace(day=1))
            with cols[2]:
                end_date = st.date_input("End Date", date.today())
            
            if st.button("🔍 Show Expense History"):
                try:
                    conn = get_db_connection()
                    history_df = pd.read_sql_query(
                        """
                        SELECT 
                            entry_date as "Date",
                            description as "Description",
                            transaction_type as "Type",
                            debit as "Debit",
                            credit as "Credit"
                        FROM employee_ledger 
                        WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                        ORDER BY entry_date DESC
                        """,
                        conn,
                        params=(selected_emp_id, str(start_date), str(end_date))
                    )
                    
                    if not history_df.empty:
                        st.dataframe(
                            history_df.style.format({
                                'Debit': 'Rs. {:,.2f}',
                                'Credit': 'Rs. {:,.2f}'
                            }),
                            use_container_width=True
                        )
                        
                        total_debit = history_df['Debit'].sum()
                        total_credit = history_df['Credit'].sum()
                        net_balance = total_credit - total_debit
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Debits", f"Rs. {total_debit:,.2f}")
                        with col2:
                            st.metric("Total Credits", f"Rs. {total_credit:,.2f}")
                        with col3:
                            st.metric("Net Balance", f"Rs. {net_balance:,.2f}")
                    else:
                        st.info("No expenses found for the selected period.")
                        
                except Exception as e:
                    st.error(f"Error loading expense history: {e}")
    
    with tab4:
        st.subheader("Salary Processing")
        
        st.info("""
        **Salary Processing Steps:**
        1. Add all employee expenses and advances throughout the month
        2. Generate salary credits for all employees
        3. Review and download salary sheets
        4. Process payments
        """)
        
        selected_month = st.date_input("Select Salary Month", date.today().replace(day=1), key="salary_month")
        first_day = selected_month.replace(day=1)
        last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Generate Salary Credits", use_container_width=True):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    employees_df = get_all_employees()
                    
                    processed_count = 0
                    skipped_count = 0
                    
                    with st.spinner("Processing salary credits..."):
                        for _, emp in employees_df.iterrows():
                            salary = emp['salary']
                            if salary <= 0:
                                skipped_count += 1
                                continue
                            
                            description = f"Monthly Salary Credit - {selected_month.strftime('%B %Y')}"
                            month_year = selected_month.strftime('%Y-%m')
                            
                            # Check if already generated for this month
                            cursor.execute(
                                "SELECT 1 FROM employee_ledger WHERE employee_id = ? AND description = ? AND month_year = ?",
                                (emp['id'], description, month_year)
                            )
                            if cursor.fetchone():
                                skipped_count += 1
                                continue
                                
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, transaction_type, month_year)
                                VALUES (?, ?, ?, 0, ?, 'Salary', ?)
                                """,
                                (emp['id'], str(first_day), description, salary, month_year)
                            )
                            processed_count += 1
                    
                    conn.commit()
                    if processed_count > 0:
                        st.success(f"Salary credits generated for {processed_count} employees.")
                    if skipped_count > 0:
                        st.info(f"Skipped {skipped_count} employees (already processed or zero salary).")
                    clear_cache()
                    
                except Exception as e:
                    st.error(f"Error generating salary credits: {e}")
        
        with col2:
            if st.button("📊 Generate Salary Sheet", use_container_width=True):
                try:
                    conn = get_db_connection()
                    query = f"""
                    SELECT
                        e.employee_id as "Employee ID",
                        e.name AS "Employee Name",
                        e.designation AS "Designation",
                        e.salary AS "Base Salary",
                        COALESCE(SUM(l.credit), 0) AS "Total Credits",
                        COALESCE(SUM(l.debit), 0) AS "Total Deductions",
                        (COALESCE(SUM(l.credit), 0) - COALESCE(SUM(l.debit), 0)) AS "Net Salary",
                        e.bank AS "Bank",
                        e.account_title AS "Account Title",
                        e.account_no AS "Account No",
                        e.bank_branch AS "Branch"
                    FROM employees e
                    LEFT JOIN employee_ledger l ON e.id = l.employee_id
                        AND l.month_year = '{selected_month.strftime('%Y-%m')}'
                    WHERE e.status = 'Active'
                    GROUP BY e.id, e.name, e.designation, e.salary, e.bank, e.account_title, e.account_no, e.bank_branch
                    ORDER BY e.name
                    """
                    salary_df = pd.read_sql_query(query, conn)

                    if salary_df.empty:
                        st.warning("No salary data found.")
                    else:
                        st.dataframe(salary_df.style.format({
                            'Base Salary': 'Rs. {:,.2f}',
                            'Total Credits': 'Rs. {:,.2f}',
                            'Total Deductions': 'Rs. {:,.2f}',
                            'Net Salary': 'Rs. {:,.2f}'
                        }), use_container_width=True)
                        
                        # Show summary
                        total_base = salary_df['Base Salary'].sum()
                        total_net = salary_df['Net Salary'].sum()
                        total_deductions = salary_df['Total Deductions'].sum()
                        
                        st.success(f"**Summary:** Base Salary: Rs. {total_base:,.2f} | Deductions: Rs. {total_deductions:,.2f} | Net Payable: Rs. {total_net:,.2f}")
                        
                        # Download buttons
                        col1, col2 = st.columns(2)
                        with col1:
                            pdf_bytes = generate_pdf_report(
                                salary_df, 
                                f"Salary Sheet - {selected_month.strftime('%B %Y')}", 
                                date_range=(first_day, last_day),
                                orientation='L',
                                totals_cols=["Base Salary", "Total Credits", "Total Deductions", "Net Salary"]
                            )
                            st.download_button(
                                label="📥 Download Salary Sheet (PDF)",
                                data=pdf_bytes,
                                file_name=f"Salary_Sheet_{selected_month.strftime('%Y_%m')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        with col2:
                            csv = salary_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download Salary Sheet (Excel)",
                                data=csv,
                                file_name=f"Salary_Sheet_{selected_month.strftime('%Y_%m')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                except Exception as e:
                    st.error(f"Error generating salary sheet: {e}")

    with tab5:
        st.subheader("🧾 Individual Salary Slips")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("No employees found.")
        else:
            employee_list = {row['id']: f"{row['name']} - {row['designation']}" 
                           for index, row in employees_df.iterrows()}
            
            col1, col2 = st.columns(2)
            with col1:
                selected_emp_id = st.selectbox(
                    "Select Employee",
                    options=list(employee_list.keys()),
                    format_func=lambda x: employee_list[x],
                    key="slip_employee"
                )
            with col2:
                slip_month = st.date_input("Salary Month", date.today().replace(day=1), key="slip_month")
            
            if st.button("Generate Salary Slip"):
                try:
                    conn = get_db_connection()
                    
                    # Get employee details
                    emp_df = pd.read_sql_query(
                        "SELECT * FROM employees WHERE id = ?", 
                        conn, 
                        params=(selected_emp_id,)
                    )
                    
                    if not emp_df.empty:
                        emp_details = emp_df.iloc[0].to_dict()
                        
                        # Get ledger entries for the month
                        month_year = slip_month.strftime('%Y-%m')
                        ledger_df = pd.read_sql_query(
                            """
                            SELECT description, debit, credit 
                            FROM employee_ledger 
                            WHERE employee_id = ? AND month_year = ?
                            ORDER BY entry_date
                            """,
                            conn,
                            params=(selected_emp_id, month_year)
                        )
                        
                        total_credits = ledger_df['credit'].sum()
                        total_debits = ledger_df['debit'].sum()
                        net_salary = total_credits - total_debits
                        
                        # Generate PDF
                        pdf_bytes = generate_individual_slip_pdf(
                            emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary
                        )
                        
                        st.success(f"Salary slip generated for {emp_details['name']}")
                        
                        st.download_button(
                            label="📥 Download Salary Slip",
                            data=pdf_bytes,
                            file_name=f"Salary_Slip_{emp_details['name']}_{slip_month.strftime('%B_%Y')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                    else:
                        st.error("Employee not found.")
                        
                except Exception as e:
                    st.error(f"Error generating salary slip: {e}")

# --- Enhanced Employee Management ---
def page_employee_management():
    st.title("👥 Employee Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add New Employee", "📋 Manage Employees", "📤 Import Employees"])
    
    with tab1:
        st.subheader("Add New Employee")
        with st.form("new_employee_form", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                name = st.text_input("Full Name *", placeholder="e.g., Ali Ahmed")
                salary = st.number_input("Monthly Base Salary (Rs.) *", min_value=0.0, step=1000.0, value=0.0)
                bank = st.text_input("Bank Name", placeholder="e.g., HBL, UBL, MCB")
                join_date = st.date_input("Joining Date", date.today())
                cnic = st.text_input("CNIC", placeholder="XXXXX-XXXXXXX-X")
            with cols[1]:
                designation = st.text_input("Designation *", placeholder="e.g., Sales Manager, Accountant")
                account_title = st.text_input("Account Title", placeholder="e.g., Ali Ahmed")
                account_no = st.text_input("Account Number", placeholder="e.g., 0123456789")
                bank_branch = st.text_input("Bank Branch", placeholder="e.g., Main Branch, Karachi")
                status = st.selectbox("Status", ["Active", "Inactive"])
                
            submitted = st.form_submit_button("💾 Add Employee")
            if submitted:
                if not name or not designation:
                    st.error("❌ Name and Designation are required fields.")
                else:
                    try:
                        conn = get_db_connection()
                        employee_id = generate_employee_id()
                        
                        conn.execute(
                            """
                            INSERT INTO employees (employee_id, name, designation, salary, bank, account_title, 
                                                account_no, bank_branch, cnic, join_date, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (employee_id, name, designation, salary, bank, account_title, account_no, 
                             bank_branch, cnic, str(join_date), status)
                        )
                        conn.commit()
                        st.success(f"✅ Employee '{name}' added successfully with ID: {employee_id}!")
                        clear_cache()
                    except sqlite3.Error as e:
                        st.error(f"❌ Database error: {e}")

    with tab2:
        st.subheader("Manage Employees")
        
        try:
            employees_df = get_all_employees()
            if employees_df.empty:
                st.info("ℹ️ No employees found. Add employees using the form above.")
                return

            # Add current balance to display
            balance_data = []
            for _, emp in employees_df.iterrows():
                balance = get_employee_balance(emp['id'])
                balance_data.append(balance)
            
            employees_df['Current Balance'] = balance_data
            employees_df['Net Payable'] = employees_df['salary'] + employees_df['Current Balance']

            # Display employee list with balances
            display_cols = ['employee_id', 'name', 'designation', 'salary', 'Current Balance', 'Net Payable', 'bank', 'join_date', 'status']
            display_df = employees_df[display_cols].copy()
            
            st.dataframe(
                display_df.style.format({
                    'salary': 'Rs. {:,.2f}',
                    'Current Balance': 'Rs. {:,.2f}',
                    'Net Payable': 'Rs. {:,.2f}'
                }),
                use_container_width=True
            )

            # Edit/Delete section
            st.subheader("Edit Employee Details")
            employee_names = {row['id']: f"{row['name']} ({row['employee_id']})" for _, row in employees_df.iterrows()}
            selected_emp_id = st.selectbox(
                "Select Employee to Edit",
                options=list(employee_names.keys()),
                format_func=lambda x: employee_names[x]
            )
            
            if selected_emp_id:
                emp_data = employees_df[employees_df['id'] == selected_emp_id].iloc[0]
                
                with st.form("edit_employee_form"):
                    cols = st.columns(2)
                    with cols[0]:
                        edit_name = st.text_input("Name", value=emp_data['name'])
                        edit_salary = st.number_input("Salary", value=float(emp_data['salary']), step=1000.0)
                        edit_bank = st.text_input("Bank", value=emp_data.get('bank', ''))
                        edit_join_date = st.date_input("Join Date", 
                                                     value=datetime.strptime(emp_data['join_date'], '%Y-%m-%d').date() 
                                                     if emp_data['join_date'] else date.today())
                        edit_cnic = st.text_input("CNIC", value=emp_data.get('cnic', ''))
                    with cols[1]:
                        edit_designation = st.text_input("Designation", value=emp_data['designation'])
                        edit_account_title = st.text_input("Account Title", value=emp_data.get('account_title', ''))
                        edit_account_no = st.text_input("Account No", value=emp_data.get('account_no', ''))
                        edit_bank_branch = st.text_input("Bank Branch", value=emp_data.get('bank_branch', ''))
                        edit_status = st.selectbox("Status", ["Active", "Inactive"], 
                                                 index=0 if emp_data.get('status', 'Active') == 'Active' else 1)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        update_submitted = st.form_submit_button("💾 Update Employee")
                    with col2:
                        delete_submitted = st.form_submit_button("🗑️ Delete Employee", type="secondary")
                    with col3:
                        if st.form_submit_button("📄 Generate Employee Report"):
                            # Generate individual employee report
                            try:
                                conn = get_db_connection()
                                transactions = pd.read_sql_query(
                                    "SELECT * FROM employee_ledger WHERE employee_id = ? ORDER BY entry_date DESC",
                                    conn, params=(selected_emp_id,)
                                )
                                
                                report_df = pd.DataFrame({
                                    'Employee ID': [emp_data.get('employee_id', 'N/A')],
                                    'Name': [emp_data['name']],
                                    'Designation': [emp_data['designation']],
                                    'Base Salary': [emp_data['salary']],
                                    'Current Balance': [get_employee_balance(selected_emp_id)],
                                    'Total Transactions': [len(transactions)]
                                })
                                
                                pdf_bytes = generate_pdf_report(
                                    report_df, 
                                    f"Employee Report - {emp_data['name']}",
                                    orientation='P'
                                )
                                
                                st.download_button(
                                    label="Download Employee Report",
                                    data=pdf_bytes,
                                    file_name=f"Employee_Report_{emp_data['name']}.pdf",
                                    mime="application/pdf"
                                )
                            except Exception as e:
                                st.error(f"Error generating report: {e}")
                    
                    if update_submitted:
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                """
                                UPDATE employees SET
                                name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, 
                                account_no = ?, bank_branch = ?, cnic = ?, join_date = ?, status = ?
                                WHERE id = ?
                                """,
                                (edit_name, edit_designation, edit_salary, edit_bank, edit_account_title, 
                                 edit_account_no, edit_bank_branch, edit_cnic, str(edit_join_date), edit_status, selected_emp_id)
                            )
                            conn.commit()
                            st.success("✅ Employee updated successfully!")
                            clear_cache()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error updating employee: {e}")
                    
                    if delete_submitted:
                        try:
                            conn = get_db_connection()
                            # Check if employee has ledger entries
                            ledger_check = pd.read_sql_query(
                                "SELECT COUNT(*) as count FROM employee_ledger WHERE employee_id = ?",
                                conn,
                                params=(selected_emp_id,)
                            )
                            
                            if ledger_check['count'].iloc[0] > 0:
                                st.error("❌ Cannot delete employee with existing ledger entries. Please clear ledger first.")
                            else:
                                conn.execute("DELETE FROM employees WHERE id = ?", (selected_emp_id,))
                                conn.commit()
                                st.success("✅ Employee deleted successfully!")
                                clear_cache()
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting employee: {e}")

        except Exception as e:
            st.error(f"❌ Error loading employees: {e}")

    with tab3:
        st.subheader("Import Employees from Excel")
        
        st.info("""
        **Import Instructions:**
        - Download the template below
        - Fill in employee data
        - Upload the filled template
        - Required fields: Name, Designation, Salary
        """)
        
        # Download template
        template_cols = ['name', 'designation', 'salary', 'bank', 'account_title', 'account_no', 'bank_branch', 'cnic']
        template_output, template_name = generate_excel_template(template_cols, "employee_import_template.xlsx")
        
        st.download_button(
            label="📥 Download Import Template",
            data=template_output.getvalue(),
            file_name=template_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                if st.button("Import Employees"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    imported_count = 0
                    error_count = 0
                    
                    for _, row in df.iterrows():
                        try:
                            if pd.notna(row['name']) and pd.notna(row['designation']):
                                employee_id = generate_employee_id()
                                salary = float(row['salary']) if pd.notna(row['salary']) else 0.0
                                
                                cursor.execute(
                                    """
                                    INSERT INTO employees (employee_id, name, designation, salary, bank, account_title, 
                                                        account_no, bank_branch, cnic, join_date, status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (employee_id, row['name'], row['designation'], salary,
                                     row.get('bank', ''), row.get('account_title', ''), row.get('account_no', ''),
                                     row.get('bank_branch', ''), row.get('cnic', ''), str(date.today()), 'Active')
                                )
                                imported_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            error_count += 1
                            st.warning(f"Error importing {row.get('name', 'Unknown')}: {str(e)}")
                    
                    conn.commit()
                    st.success(f"✅ Successfully imported {imported_count} employees!")
                    if error_count > 0:
                        st.warning(f"⚠️ Failed to import {error_count} records.")
                    clear_cache()
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

# --- Enhanced Company Expense Management ---
def page_expense_management():
    st.title("💼 Company Expense Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Expense", "📋 Expense History", "📊 Expense Reports"])
    
    with tab1:
        st.subheader("Add Company Expense")
        
        with st.form("add_company_expense", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                description = st.text_input("Description *", placeholder="e.g., Office supplies purchase")
                amount = st.number_input("Amount (Rs.) *", min_value=0.01, step=100.0)
                expense_date = st.date_input("Expense Date *", date.today())
            with cols[1]:
                categories = get_all_categories()
                category_id = st.selectbox(
                    "Category *",
                    options=categories['id'].tolist(),
                    format_func=lambda x: categories[categories['id'] == x]['name'].iloc[0]
                )
                payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Cheque", "Card"])
                reference_no = st.text_input("Reference No", placeholder="Optional")
            
            submitted = st.form_submit_button("💾 Add Expense")
            if submitted:
                if description and amount > 0:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, payment_method, reference_no)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (description, amount, str(expense_date), category_id, payment_method, reference_no)
                        )
                        conn.commit()
                        st.success("✅ Company expense added successfully!")
                        clear_cache()
                    except sqlite3.Error as e:
                        st.error(f"❌ Database error: {e}")
                else:
                    st.error("❌ Please fill all required fields.")
    
    with tab2:
        st.subheader("Expense History")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="comp_exp_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="comp_exp_end")
        
        if st.button("🔍 Load Expenses"):
            try:
                conn = get_db_connection()
                expenses_df = pd.read_sql_query(
                    """
                    SELECT ce.description, ce.amount, ce.expense_date, ce.payment_method, ce.reference_no,
                           ec.name as category
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    ORDER BY ce.expense_date DESC
                    """,
                    conn,
                    params=(str(start_date), str(end_date))
                )
                
                if not expenses_df.empty:
                    st.dataframe(
                        expenses_df.style.format({
                            'amount': 'Rs. {:,.2f}'
                        }),
                        use_container_width=True
                    )
                    
                    total_expenses = expenses_df['amount'].sum()
                    st.metric("Total Expenses", f"Rs. {total_expenses:,.2f}")
                else:
                    st.info("No expenses found for the selected period.")
                    
            except Exception as e:
                st.error(f"Error loading expenses: {e}")
    
    with tab3:
        st.subheader("Expense Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            report_type = st.selectbox("Report Type", ["Monthly Summary", "Category-wise", "Detailed"])
        with col2:
            report_month = st.date_input("Report Month", date.today().replace(day=1), key="report_month")
        
        if st.button("Generate Report"):
            try:
                conn = get_db_connection()
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                if report_type == "Monthly Summary":
                    summary_df = pd.read_sql_query(
                        """
                        SELECT 
                            ec.name as Category,
                            COUNT(ce.id) as Count,
                            SUM(ce.amount) as Total
                        FROM company_expenses ce
                        LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                        WHERE ce.expense_date BETWEEN ? AND ?
                        GROUP BY ec.name
                        ORDER BY Total DESC
                        """,
                        conn,
                        params=(str(first_day), str(last_day))
                    )
                    
                    if not summary_df.empty:
                        st.dataframe(
                            summary_df.style.format({
                                'Total': 'Rs. {:,.2f}'
                            }),
                            use_container_width=True
                        )
                        
                        # Download PDF
                        pdf_bytes = generate_pdf_report(
                            summary_df,
                            f"Expense Summary - {report_month.strftime('%B %Y')}",
                            date_range=(first_day, last_day),
                            totals_cols=["Total"]
                        )
                        
                        st.download_button(
                            label="📥 Download Report (PDF)",
                            data=pdf_bytes,
                            file_name=f"Expense_Summary_{report_month.strftime('%Y_%m')}.pdf",
                            mime="application/pdf"
                        )
                    else:
                        st.info("No expenses found for the selected period.")
                        
            except Exception as e:
                st.error(f"Error generating report: {e}")

# --- Enhanced Reporting ---
def page_reporting():
    st.title("📈 Reports & Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Employee Reports", "💼 Company Reports", "📊 Analytics", "📤 Export Data"
    ])
    
    with tab1:
        st.subheader("Employee Reports")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("No employees found.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                report_type = st.selectbox(
                    "Report Type",
                    ["Salary Sheet", "Employee Ledger", "Balance Summary", "Attendance Summary"],
                    key="emp_report_type"
                )
            with col2:
                report_month = st.date_input("Report Month", date.today().replace(day=1), key="emp_report_month")
            
            if st.button("Generate Employee Report"):
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                try:
                    conn = get_db_connection()
                    
                    if report_type == "Salary Sheet":
                        query = f"""
                        SELECT
                            e.employee_id as "Employee ID",
                            e.name AS "Employee Name",
                            e.designation AS "Designation",
                            e.salary AS "Base Salary",
                            COALESCE(SUM(l.credit), 0) AS "Total Credits",
                            COALESCE(SUM(l.debit), 0) AS "Total Deductions",
                            (COALESCE(SUM(l.credit), 0) - COALESCE(SUM(l.debit), 0)) AS "Net Salary"
                        FROM employees e
                        LEFT JOIN employee_ledger l ON e.id = l.employee_id
                            AND l.month_year = '{report_month.strftime('%Y-%m')}'
                        WHERE e.status = 'Active'
                        GROUP BY e.id, e.name, e.designation, e.salary
                        ORDER BY e.name
                        """
                        
                        report_df = pd.read_sql_query(query, conn)
                        
                        if not report_df.empty:
                            st.dataframe(report_df.style.format({
                                'Base Salary': 'Rs. {:,.2f}',
                                'Total Credits': 'Rs. {:,.2f}',
                                'Total Deductions': 'Rs. {:,.2f}',
                                'Net Salary': 'Rs. {:,.2f}'
                            }), use_container_width=True)
                            
                            # Download options
                            col1, col2 = st.columns(2)
                            with col1:
                                pdf_bytes = generate_pdf_report(
                                    report_df,
                                    f"Salary Sheet - {report_month.strftime('%B %Y')}",
                                    date_range=(first_day, last_day),
                                    orientation='L',
                                    totals_cols=["Base Salary", "Total Credits", "Total Deductions", "Net Salary"]
                                )
                                st.download_button(
                                    label="📥 Download PDF",
                                    data=pdf_bytes,
                                    file_name=f"Salary_Sheet_{report_month.strftime('%Y_%m')}.pdf",
                                    mime="application/pdf"
                                )
                            with col2:
                                csv = report_df.to_csv(index=False)
                                st.download_button(
                                    label="📥 Download Excel",
                                    data=csv,
                                    file_name=f"Salary_Sheet_{report_month.strftime('%Y_%m')}.csv",
                                    mime="text/csv"
                                )
                    
                    elif report_type == "Balance Summary":
                        balance_data = []
                        for _, emp in employees_df.iterrows():
                            balance = get_employee_balance(emp['id'])
                            balance_data.append({
                                'Employee ID': emp.get('employee_id', 'N/A'),
                                'Name': emp['name'],
                                'Designation': emp['designation'],
                                'Base Salary': emp['salary'],
                                'Current Balance': balance,
                                'Net Payable': emp['salary'] + balance
                            })
                        
                        balance_df = pd.DataFrame(balance_data)
                        st.dataframe(balance_df.style.format({
                            'Base Salary': 'Rs. {:,.2f}',
                            'Current Balance': 'Rs. {:,.2f}',
                            'Net Payable': 'Rs. {:,.2f}'
                        }), use_container_width=True)
                        
                except Exception as e:
                    st.error(f"Error generating report: {e}")
    
    with tab4:
        st.subheader("Data Export")
        
        st.info("Export data for backup or external analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Employees Data"):
                employees_df = get_all_employees()
                if not employees_df.empty:
                    csv = employees_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Employees CSV",
                        data=csv,
                        file_name=f"employees_export_{date.today().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            if st.button("Export Salary Data"):
                try:
                    conn = get_db_connection()
                    salary_df = pd.read_sql_query(
                        """
                        SELECT e.employee_id, e.name, e.designation, e.salary, 
                               l.entry_date, l.description, l.debit, l.credit, l.transaction_type
                        FROM employees e
                        LEFT JOIN employee_ledger l ON e.id = l.employee_id
                        WHERE e.status = 'Active'
                        ORDER BY e.name, l.entry_date
                        """,
                        conn
                    )
                    
                    if not salary_df.empty:
                        csv = salary_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Salary Data CSV",
                            data=csv,
                            file_name=f"salary_data_export_{date.today().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"Error exporting salary data: {e}")
        
        with col3:
            if st.button("Export Expense Data"):
                try:
                    conn = get_db_connection()
                    expense_df = pd.read_sql_query(
                        """
                        SELECT ce.description, ce.amount, ce.expense_date, ce.payment_method, ce.reference_no,
                               ec.name as category, e.name as employee_name
                        FROM company_expenses ce
                        LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                        LEFT JOIN employees e ON ce.employee_id = e.id
                        ORDER BY ce.expense_date DESC
                        """,
                        conn
                    )
                    
                    if not expense_df.empty:
                        csv = expense_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download Expense Data CSV",
                            data=csv,
                            file_name=f"expense_data_export_{date.today().strftime('%Y%m%d')}.csv",
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"Error exporting expense data: {e}")

# --- Enhanced Dashboard ---
def page_dashboard():
    st.title(f"🏠 Welcome to {COMPANY_NAME} HR & Expense Manager")
    
    # Try to display logo
    try:
        logo_paths = ['logo.png', 'nutrion_logo.png', 'company_logo.png', 'assets/logo.png']
        logo_found = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                st.image(logo_path, width=200)
                logo_found = True
                break
        if not logo_found:
            st.write(f"## {COMPANY_NAME}")
    except:
        st.write(f"## {COMPANY_NAME}")
    
    try:
        emp_count, exp_total, cat_count, salary_total = get_dashboard_stats()
        
        st.subheader("📊 Quick Overview (Current Month)")
        cols = st.columns(4)
        with cols[0]:
            st.metric("Total Employees", f"{emp_count}")
        with cols[1]:
            st.metric("Company Expenses", f"Rs. {exp_total:,.2f}")
        with cols[2]:
            st.metric("Expense Categories", f"{cat_count}")
        with cols[3]:
            st.metric("Total Salary Pool", f"Rs. {salary_total:,.2f}")
        
        # Recent Activity
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("👥 Recent Employees")
            employees_df = get_all_employees()
            if not employees_df.empty:
                for _, emp in employees_df.head(5).iterrows():
                    balance = get_employee_balance(emp['id'])
                    balance_status = "Due" if balance > 0 else "Advance" if balance < 0 else "Settled"
                    st.write(f"**{emp['name']}** - {emp['designation']} - {balance_status}")
            else:
                st.info("No employees found")
        
        with col2:
            st.subheader("💰 Recent Expenses")
            try:
                conn = get_db_connection()
                recent_expenses = pd.read_sql_query(
                    "SELECT description, amount, expense_date FROM company_expenses ORDER BY expense_date DESC LIMIT 5",
                    conn
                )
                if not recent_expenses.empty:
                    for _, exp in recent_expenses.iterrows():
                        st.write(f"**{exp['description']}** - Rs. {exp['amount']:,.2f} ({exp['expense_date']})")
                else:
                    st.info("No expenses recorded")
            except:
                st.info("No expenses recorded")
    
    except Exception as e:
        st.warning(f"Could not load dashboard stats: {e}")
    
    st.info("""
    **📋 Navigation Guide:**
    - **💰 Employee Expenses**: Add expenses, track balances, process salaries
    - **👥 Employee Management**: Add and manage employee records
    - **💼 Company Expenses**: Log company-wide expenses
    - **📈 Reports**: Download various reports
    - **📤 Data Import**: Bulk import data
    """)

# --- Enhanced Data Import ---
def page_data_import():
    st.title("📤 Data Import")
    st.info("Use this page to import existing data from Excel files.")
    
    tab1, tab2, tab3 = st.tabs(["Import Employees", "Import Expenses", "Import Transactions"])
    
    with tab1:
        st.subheader("Import Employees")
        
        st.info("""
        **Required columns:** name, designation, salary
        **Optional columns:** bank, account_title, account_no, bank_branch, cnic
        """)
        
        # Download template
        template_cols = ['name', 'designation', 'salary', 'bank', 'account_title', 'account_no', 'bank_branch', 'cnic']
        template_output, template_name = generate_excel_template(template_cols, "employee_import_template.xlsx")
        
        st.download_button(
            label="📥 Download Employee Template",
            data=template_output.getvalue(),
            file_name=template_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        uploaded_file = st.file_uploader("Upload Employee Excel File", type=['xlsx', 'xls'], key="emp_import")
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                if st.button("Import Employees Data"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    imported_count = 0
                    error_count = 0
                    
                    for _, row in df.iterrows():
                        try:
                            if pd.notna(row['name']) and pd.notna(row['designation']):
                                employee_id = generate_employee_id()
                                salary = float(row['salary']) if pd.notna(row['salary']) else 0.0
                                
                                cursor.execute(
                                    """
                                    INSERT OR IGNORE INTO employees (employee_id, name, designation, salary, bank, account_title, 
                                                                    account_no, bank_branch, cnic, join_date, status)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (employee_id, row['name'], row['designation'], salary,
                                     row.get('bank', ''), row.get('account_title', ''), row.get('account_no', ''),
                                     row.get('bank_branch', ''), row.get('cnic', ''), str(date.today()), 'Active')
                                )
                                imported_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            error_count += 1
                    
                    conn.commit()
                    st.success(f"✅ Successfully imported {imported_count} employees!")
                    if error_count > 0:
                        st.warning(f"⚠️ Failed to import {error_count} records (missing required fields).")
                    clear_cache()
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
    
    with tab2:
        st.subheader("Import Company Expenses")
        
        st.info("""
        **Required columns:** description, amount, expense_date, category
        **Date format:** YYYY-MM-DD
        """)
        
        # Get categories for mapping
        categories = get_all_categories()
        category_mapping = {row['name']: row['id'] for _, row in categories.iterrows()}
        
        uploaded_file = st.file_uploader("Upload Expenses Excel File", type=['xlsx', 'xls'], key="exp_import")
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                if st.button("Import Expenses Data"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    imported_count = 0
                    error_count = 0
                    
                    for _, row in df.iterrows():
                        try:
                            if (pd.notna(row['description']) and pd.notna(row['amount']) and 
                                pd.notna(row['expense_date']) and pd.notna(row['category'])):
                                
                                category_id = category_mapping.get(row['category'])
                                if category_id:
                                    cursor.execute(
                                        """
                                        INSERT INTO company_expenses (description, amount, expense_date, category_id, payment_method)
                                        VALUES (?, ?, ?, ?, ?)
                                        """,
                                        (row['description'], float(row['amount']), str(row['expense_date']), 
                                         category_id, row.get('payment_method', 'Cash'))
                                    )
                                    imported_count += 1
                                else:
                                    error_count += 1
                            else:
                                error_count += 1
                        except Exception as e:
                            error_count += 1
                    
                    conn.commit()
                    st.success(f"✅ Successfully imported {imported_count} expenses!")
                    if error_count > 0:
                        st.warning(f"⚠️ Failed to import {error_count} records.")
                    clear_cache()
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

# --- Main App with enhanced navigation ---
def main():
    st.set_page_config(
        page_title=f"{COMPANY_NAME} HR System", 
        layout="wide",
        page_icon="💰",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        color: #155724;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        color: #856404;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        color: #0c5460;
    }
    .stButton button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    init_db()

    st.sidebar.title(f"{COMPANY_NAME} HR System")
    try:
        logo_paths = ['logo.png', 'nutrion_logo.png', 'company_logo.png', 'assets/logo.png']
        logo_found = False
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                st.sidebar.image(logo_path, width=150)
                logo_found = True
                break
        if not logo_found:
            st.sidebar.write(f"### {COMPANY_NAME}")
    except:
        st.sidebar.write(f"### {COMPANY_NAME}")
        
    # Improved navigation with better grouping
    st.sidebar.markdown("### 🎯 Core Functions")
    page_options = {
        "💰 Employee Expenses": page_employee_expense_management,
        "👥 Employee Management": page_employee_management,
        "💼 Company Expenses": page_expense_management,
    }
    
    st.sidebar.markdown("### 📊 Reports & Tools")
    page_options.update({
        "📈 Reports": page_reporting,
        "📤 Data Import": page_data_import,
        "🏠 Dashboard": page_dashboard,
    })
    
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()))
    st.sidebar.divider()
    
    # Quick Actions
    st.sidebar.markdown("### ⚡ Quick Actions")
    if st.sidebar.button("➕ Add New Employee", key="sidebar_add_emp"):
        st.session_state.current_page = "👥 Employee Management"
        st.rerun()
    
    if st.sidebar.button("💸 Process Salaries", key="sidebar_salary"):
        st.session_state.current_page = "💰 Employee Expenses"
        st.rerun()
    
    if st.sidebar.button("📊 Generate Reports", key="sidebar_reports"):
        st.session_state.current_page = "📈 Reports"
        st.rerun()
    
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
