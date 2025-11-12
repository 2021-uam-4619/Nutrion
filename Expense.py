import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
import base64
import tempfile
import uuid

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# --- PDF Class with Enhanced Header/Footer and Logo ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""

    def header(self):
        # Add company logo (try multiple possible paths)
        logo_paths = ['logo.png', 'nutrion_logo.png', 'company_logo.png', 'assets/logo.png']
        logo_found = False
        
        for logo_path in logo_paths:
            try:
                if os.path.exists(logo_path):
                    self.image(logo_path, 10, 8, 25)
                    logo_found = True
                    break
            except:
                continue
        
        if not logo_found:
            # Create a simple text logo as fallback
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
        
        # Add signature space
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

# --- Enhanced Database Setup ---
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Enhanced employees table with more fields
    c.execute("PRAGMA table_info(employees)")
    columns = [column[1] for column in c.fetchall()]
    
    # Add missing columns if needed
    if 'join_date' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN join_date DATE")
    if 'phone' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN phone TEXT")
    if 'email' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN email TEXT")
    if 'address' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN address TEXT")
    if 'status' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN status TEXT DEFAULT 'Active'")
    
    # Enhanced employee_ledger table
    c.execute("PRAGMA table_info(employee_ledger)")
    ledger_columns = [column[1] for column in c.fetchall()]
    
    if 'related_expense_id' not in ledger_columns:
        c.execute("ALTER TABLE employee_ledger ADD COLUMN related_expense_id INTEGER")
    if 'category' not in ledger_columns:
        c.execute("ALTER TABLE employee_ledger ADD COLUMN category TEXT")
    if 'status' not in ledger_columns:
        c.execute("ALTER TABLE employee_ledger ADD COLUMN status TEXT DEFAULT 'Active'")
    
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
            join_date DATE,
            phone TEXT,
            email TEXT,
            address TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT DEFAULT 'Company',
            status TEXT DEFAULT 'Active'
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
            vendor_name TEXT,
            payment_method TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
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
            category TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (related_expense_id) REFERENCES company_expenses (id) ON DELETE SET NULL
        )
    ''')
    
    # Enhanced default categories
    default_categories = [
        ("Guard", "Employee"),
        ("Labour", "Employee"), 
        ("Bilty Expenses", "Company"),
        ("Office Rent", "Company"),
        ("Warehouse Rent", "Company"),
        ("Import Export", "Company"),
        ("Office Electricity", "Company"),
        ("FBR", "Company"),
        ("Office Entertainment", "Company"),
        ("PSID", "Company"),
        ("Advance", "Employee"),
        ("Commission", "Employee"),
        ("Office Stationery Expense", "Company"),
        ("Employee Expenses", "Employee"),
        ("Other Expense", "Company"),
        ("Company Expense", "Company"),
        ("Salary", "Employee"),
        ("Travel", "Employee"),
        ("Medical", "Employee"),
        ("Bonus", "Employee")
    ]
    
    for category_name, category_type in default_categories:
        c.execute("INSERT OR IGNORE INTO expense_categories (name, type) VALUES (?, ?)", 
                 (category_name, category_type))
    
    conn.commit()

# --- Enhanced PDF Generation Function ---
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

# --- Enhanced Helper Functions ---
@st.cache_data(ttl=60)
def get_all_employees(active_only=True):
    conn = get_db_connection()
    if active_only:
        df = pd.read_sql_query("SELECT * FROM employees WHERE status = 'Active' ORDER BY name", conn)
    else:
        df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
    
    if 'join_date' in df.columns:
        df['join_date'] = df['join_date'].astype(str)
    return df

@st.cache_data(ttl=60)
def get_all_categories():
    conn = get_db_connection()
    return pd.read_sql_query("SELECT * FROM expense_categories WHERE status = 'Active' ORDER BY name", conn)

@st.cache_data(ttl=60)
def get_dashboard_stats():
    conn = get_db_connection()
    
    # Employee count
    emp_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM employees WHERE status = 'Active'", conn)
    emp_count = emp_count_df['count'].iloc[0] if not emp_count_df.empty else 0
    
    # Current month expenses
    today = date.today()
    first_day_month = today.replace(day=1)
    last_day_month = (first_day_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    exp_total_df = pd.read_sql_query(
        "SELECT SUM(amount) as total FROM company_expenses WHERE expense_date BETWEEN ? AND ? AND status != 'Cancelled'",
        conn,
        params=(str(first_day_month), str(last_day_month))
    )
    exp_total = exp_total_df['total'].iloc[0] if not exp_total_df.empty and exp_total_df['total'].iloc[0] else 0.0
    
    # Categories count
    cat_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM expense_categories WHERE status = 'Active'", conn)
    cat_count = cat_count_df['count'].iloc[0] if not cat_count_df.empty else 0
    
    # Total salary
    salary_total_df = pd.read_sql_query("SELECT SUM(salary) as total FROM employees WHERE status = 'Active'", conn)
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
        "SELECT SUM(credit) - SUM(debit) as balance FROM employee_ledger WHERE employee_id = ? AND status = 'Active'",
        conn,
        params=(employee_id,)
    )
    return balance_df['balance'].iloc[0] if not balance_df.empty else 0.0

def get_monthly_employee_ledger(employee_id, month_date):
    """Get employee ledger for a specific month"""
    first_day = month_date.replace(day=1)
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    conn = get_db_connection()
    ledger_df = pd.read_sql_query(
        """
        SELECT entry_date, description, debit, credit, category 
        FROM employee_ledger 
        WHERE employee_id = ? AND entry_date BETWEEN ? AND ? AND status = 'Active'
        ORDER BY entry_date
        """,
        conn,
        params=(employee_id, str(first_day), str(last_day))
    )
    
    return ledger_df

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
            "SELECT SUM(debit) as total_debits FROM employee_ledger WHERE status = 'Active'",
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
        "➕ Add Expense", 
        "📊 Employee Balances", 
        "🔍 Expense History", 
        "💸 Salary Processing",
        "📄 Individual Salary Slips"
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
                        "Select Employee *",
                        options=list(employee_list.keys()),
                        format_func=lambda x: employee_list[x],
                        key="expense_employee"
                    )
                    current_balance = get_employee_balance(employee_id)
                    st.info(f"Current Balance: Rs. {current_balance:,.2f}")
                    
                with cols[1]:
                    expense_date = st.date_input("Expense Date *", date.today())
                    amount = st.number_input("Amount (Rs.) *", min_value=0.01, step=100.0)
                    category = st.text_input("Category", placeholder="e.g., Travel, Advance, Bonus")
                
                with cols[2]:
                    expense_type = st.selectbox(
                        "Expense Type *",
                        ["Personal Expense", "Travel Advance", "Loan Advance", "Other Deduction", "Bonus", "Other Credit"]
                    )
                    description = st.text_input("Description *", placeholder="e.g., Travel allowance, Meal expense")
                
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
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, category)
                                    VALUES (?, ?, ?, ?, 0, ?)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount, category)
                                )
                                message_type = "expense"
                            else:
                                # Credit entry (bonus/other credit)
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, category)
                                    VALUES (?, ?, ?, 0, ?, ?)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount, category)
                                )
                                message_type = "credit"
                            
                            conn.commit()
                            employee_name = employees_df[employees_df['id'] == employee_id]['name'].iloc[0]
                            st.success(f"✅ {expense_type} of Rs. {amount:,.2f} added to {employee_name}'s ledger as {message_type}.")
                            clear_cache()
                        except sqlite3.Error as e:
                            st.error(f"❌ Database error: {e}")
                    else:
                        st.error("❌ Please fill in all required fields (*).")
    
    with tab2:
        st.subheader("Employee Current Balances")
        
        employees_df = get_all_employees()
        if not employees_df.empty:
            # Calculate balances for all employees
            balance_data = []
            for _, emp in employees_df.iterrows():
                balance = get_employee_balance(emp['id'])
                balance_data.append({
                    'Employee ID': emp['id'],
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
                        mime="application/pdf"
                    )
            with col2:
                # Excel download
                csv = balance_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Balance Sheet (CSV)",
                    data=csv,
                    file_name="Employee_Balance_Sheet.csv",
                    mime="text/csv"
                )
        else:
            st.info("ℹ️ No employees found.")
    
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
                            category as "Category",
                            debit as "Debit",
                            credit as "Credit"
                        FROM employee_ledger 
                        WHERE employee_id = ? AND entry_date BETWEEN ? AND ? AND status = 'Active'
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
                        st.info("ℹ️ No expenses found for the selected period.")
                        
                except Exception as e:
                    st.error(f"❌ Error loading expense history: {e}")
    
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
                            # Check if already generated
                            cursor.execute(
                                "SELECT 1 FROM employee_ledger WHERE employee_id = ? AND description = ? AND entry_date = ?",
                                (emp['id'], description, str(first_day))
                            )
                            if cursor.fetchone():
                                skipped_count += 1
                                continue
                                
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, category)
                                VALUES (?, ?, ?, 0, ?, 'Salary')
                                """,
                                (emp['id'], str(first_day), description, salary)
                            )
                            processed_count += 1
                    
                    conn.commit()
                    if processed_count > 0:
                        st.success(f"✅ Salary credits generated for {processed_count} employees.")
                    if skipped_count > 0:
                        st.info(f"ℹ️ Skipped {skipped_count} employees (already processed or zero salary).")
                    clear_cache()
                    
                except Exception as e:
                    st.error(f"❌ Error generating salary credits: {e}")
        
        with col2:
            if st.button("📊 Generate Salary Sheet", use_container_width=True):
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
                        AND l.status = 'Active'
                    WHERE e.status = 'Active'
                    GROUP BY e.id, e.name, e.designation, e.salary, e.bank, e.account_title, e.account_no
                    ORDER BY e.name
                    """
                    salary_df = pd.read_sql_query(query, conn)

                    if salary_df.empty:
                        st.warning("⚠️ No salary data found.")
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
                                label="📥 Download Salary Sheet (CSV)",
                                data=csv,
                                file_name=f"Salary_Sheet_{selected_month.strftime('%Y_%m')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                        
                except Exception as e:
                    st.error(f"❌ Error generating salary sheet: {e}")
    
    with tab5:
        st.subheader("📄 Individual Salary Slips")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("⚠️ No employees found.")
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
            
            if st.button("📄 Generate Salary Slip"):
                try:
                    # Get employee details
                    emp_details = employees_df[employees_df['id'] == selected_emp_id].iloc[0]
                    
                    # Get monthly ledger
                    ledger_df = get_monthly_employee_ledger(selected_emp_id, slip_month)
                    
                    # Calculate totals
                    total_credits = ledger_df['credit'].sum()
                    total_debits = ledger_df['debit'].sum()
                    net_salary = total_credits - total_debits
                    
                    # Generate PDF
                    pdf_bytes = generate_individual_slip_pdf(
                        emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary
                    )
                    
                    # Display summary
                    st.success(f"✅ Salary slip generated for {emp_details['name']}")
                    st.info(f"**Summary:** Credits: Rs. {total_credits:,.2f} | Debits: Rs. {total_debits:,.2f} | Net: Rs. {net_salary:,.2f}")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Salary Slip (PDF)",
                        data=pdf_bytes,
                        file_name=f"Salary_Slip_{emp_details['name']}_{slip_month.strftime('%Y_%m')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"❌ Error generating salary slip: {e}")

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
                phone = st.text_input("Phone Number", placeholder="+92-XXX-XXXXXXX")
            with cols[1]:
                designation = st.text_input("Designation *", placeholder="e.g., Sales Manager, Accountant")
                account_title = st.text_input("Account Title", placeholder="e.g., Ali Ahmed")
                account_no = st.text_input("Account Number", placeholder="e.g., 0123456789")
                email = st.text_input("Email Address", placeholder="employee@company.com")
                address = st.text_area("Address", placeholder="Full residential address")
                
            submitted = st.form_submit_button("💾 Add Employee")
            if submitted:
                if not name or not designation:
                    st.error("❌ Name and Designation are required fields.")
                else:
                    try:
                        conn = get_db_connection()
                        conn.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date, phone, email, address)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (name, designation, salary, bank, account_title, account_no, str(join_date), phone, email, address)
                        )
                        conn.commit()
                        st.success(f"✅ Employee '{name}' added successfully!")
                        clear_cache()
                    except sqlite3.Error as e:
                        st.error(f"❌ Database error: {e}")

    with tab2:
        st.subheader("Manage Employees")
        
        try:
            employees_df = get_all_employees(active_only=False)
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
            display_cols = ['id', 'name', 'designation', 'salary', 'Current Balance', 'Net Payable', 'bank', 'join_date', 'status']
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
            employee_names = {row['id']: f"{row['name']} - {row['designation']} ({'Active' if row['status'] == 'Active' else 'Inactive'})" 
                            for _, row in employees_df.iterrows()}
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
                        edit_name = st.text_input("Name *", value=emp_data['name'])
                        edit_salary = st.number_input("Salary *", value=float(emp_data['salary']), step=1000.0)
                        edit_bank = st.text_input("Bank", value=emp_data['bank'])
                        edit_phone = st.text_input("Phone", value=emp_data.get('phone', ''))
                    with cols[1]:
                        edit_designation = st.text_input("Designation *", value=emp_data['designation'])
                        edit_account_title = st.text_input("Account Title", value=emp_data['account_title'])
                        edit_account_no = st.text_input("Account No", value=emp_data['account_no'])
                        edit_status = st.selectbox("Status", ["Active", "Inactive"], 
                                                index=0 if emp_data.get('status', 'Active') == 'Active' else 1)
                    
                    edit_email = st.text_input("Email", value=emp_data.get('email', ''))
                    edit_address = st.text_area("Address", value=emp_data.get('address', ''))
                    
                    join_date_value = emp_data.get('join_date')
                    if join_date_value:
                        try:
                            if isinstance(join_date_value, str):
                                join_date_value = datetime.strptime(join_date_value, '%Y-%m-%d').date()
                            else:
                                join_date_value = datetime.now().date()
                        except:
                            join_date_value = datetime.now().date()
                    else:
                        join_date_value = datetime.now().date()
                    
                    edit_join_date = st.date_input("Join Date", value=join_date_value)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        update_submitted = st.form_submit_button("💾 Update Employee")
                    with col2:
                        delete_submitted = st.form_submit_button("🗑️ Delete Employee", type="secondary")
                    
                    if update_submitted:
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                """
                                UPDATE employees SET
                                name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, account_no = ?,
                                join_date = ?, phone = ?, email = ?, address = ?, status = ?
                                WHERE id = ?
                                """,
                                (edit_name, edit_designation, edit_salary, edit_bank, edit_account_title, 
                                 edit_account_no, str(edit_join_date), edit_phone, edit_email, edit_address, 
                                 edit_status, selected_emp_id)
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
                                st.error("❌ Cannot delete employee with existing ledger entries. Please mark as inactive instead.")
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
        st.subheader("Import Employees from Excel/CSV")
        
        st.info("""
        **Import Format:**
        - Required columns: name, designation, salary
        - Optional columns: bank, account_title, account_no, join_date, phone, email, address
        - Date format: YYYY-MM-DD
        """)
        
        uploaded_file = st.file_uploader("Choose Excel or CSV file", type=['xlsx', 'csv'])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.write("Preview of data to import:")
                st.dataframe(df.head())
                
                required_cols = ['name', 'designation', 'salary']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                else:
                    if st.button("🚀 Import Employees"):
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        imported_count = 0
                        error_count = 0
                        
                        for index, row in df.iterrows():
                            try:
                                # Handle missing optional fields
                                name = str(row['name']).strip()
                                designation = str(row['designation']).strip()
                                salary = float(row['salary'])
                                bank = str(row['bank']) if 'bank' in df.columns and pd.notna(row['bank']) else ""
                                account_title = str(row['account_title']) if 'account_title' in df.columns and pd.notna(row['account_title']) else ""
                                account_no = str(row['account_no']) if 'account_no' in df.columns and pd.notna(row['account_no']) else ""
                                
                                # Handle join date
                                if 'join_date' in df.columns and pd.notna(row['join_date']):
                                    try:
                                        if isinstance(row['join_date'], str):
                                            join_date = datetime.strptime(row['join_date'], '%Y-%m-%d').date()
                                        else:
                                            join_date = row['join_date'].date()
                                    except:
                                        join_date = date.today()
                                else:
                                    join_date = date.today()
                                
                                phone = str(row['phone']) if 'phone' in df.columns and pd.notna(row['phone']) else ""
                                email = str(row['email']) if 'email' in df.columns and pd.notna(row['email']) else ""
                                address = str(row['address']) if 'address' in df.columns and pd.notna(row['address']) else ""
                                
                                cursor.execute(
                                    """
                                    INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date, phone, email, address)
                                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """,
                                    (name, designation, salary, bank, account_title, account_no, str(join_date), phone, email, address)
                                )
                                imported_count += 1
                            except Exception as e:
                                error_count += 1
                                st.warning(f"Error importing row {index + 2}: {str(e)}")
                        
                        conn.commit()
                        
                        if imported_count > 0:
                            st.success(f"✅ Successfully imported {imported_count} employees!")
                        if error_count > 0:
                            st.error(f"❌ Failed to import {error_count} employees.")
                        
                        clear_cache()
                        
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")

# --- Enhanced Company Expense Management ---
def page_expense_management():
    st.title("💼 Company Expense Management")
    
    st.info("""
    **Note:** This page is for company expenses that are NOT linked to specific employees.
    For employee-specific expenses and advances, use the **Employee Expense Management** page.
    """)
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Expense", "📋 Manage Expenses", "📊 Expense Reports"])
    
    with tab1:
        st.subheader("Add Company Expense")
        
        categories_df = get_all_categories()
        employees_df = get_all_employees()
        
        with st.form("add_company_expense", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                description = st.text_input("Description *", placeholder="e.g., Office supplies purchase")
                amount = st.number_input("Amount (Rs.) *", min_value=0.01, step=100.0)
                expense_date = st.date_input("Expense Date *", date.today())
                
                # Category selection
                category_options = {row['id']: row['name'] for _, row in categories_df.iterrows()}
                category_id = st.selectbox(
                    "Category *",
                    options=list(category_options.keys()),
                    format_func=lambda x: category_options[x]
                )
            
            with cols[1]:
                vendor_name = st.text_input("Vendor Name", placeholder="e.g., Stationery Mart")
                payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Cheque", "Card"])
                
                # Optional employee association
                employee_options = {0: "Not Employee Related"}
                employee_options.update({row['id']: row['name'] for _, row in employees_df.iterrows()})
                employee_id = st.selectbox(
                    "Related Employee (Optional)",
                    options=list(employee_options.keys()),
                    format_func=lambda x: employee_options[x]
                )
                if employee_id == 0:
                    employee_id = None
                
                status = st.selectbox("Status", ["Pending", "Approved", "Paid", "Rejected"])
            
            submitted = st.form_submit_button("💾 Add Expense")
            if submitted:
                if description and amount > 0:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id, vendor_name, payment_method, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (description, amount, str(expense_date), category_id, employee_id, vendor_name, payment_method, status)
                        )
                        
                        conn.commit()
                        st.success(f"✅ Company expense of Rs. {amount:,.2f} added successfully!")
                        clear_cache()
                    except sqlite3.Error as e:
                        st.error(f"❌ Database error: {e}")
                else:
                    st.error("❌ Please fill in all required fields (*).")
    
    with tab2:
        st.subheader("Manage Company Expenses")
        
        # Filter options
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="expense_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="expense_end")
        with col3:
            status_filter = st.selectbox("Status Filter", ["All", "Pending", "Approved", "Paid", "Rejected"])
        
        try:
            conn = get_db_connection()
            query = """
            SELECT ce.*, ec.name as category_name, e.name as employee_name
            FROM company_expenses ce
            LEFT JOIN expense_categories ec ON ce.category_id = ec.id
            LEFT JOIN employees e ON ce.employee_id = e.id
            WHERE ce.expense_date BETWEEN ? AND ?
            """
            params = [str(start_date), str(end_date)]
            
            if status_filter != "All":
                query += " AND ce.status = ?"
                params.append(status_filter)
            
            query += " ORDER BY ce.expense_date DESC"
            
            expenses_df = pd.read_sql_query(query, conn, params=params)
            
            if not expenses_df.empty:
                st.dataframe(
                    expenses_df[['expense_date', 'description', 'category_name', 'amount', 'vendor_name', 'payment_method', 'status', 'employee_name']].rename(
                        columns={
                            'expense_date': 'Date',
                            'description': 'Description',
                            'category_name': 'Category',
                            'amount': 'Amount',
                            'vendor_name': 'Vendor',
                            'payment_method': 'Payment Method',
                            'status': 'Status',
                            'employee_name': 'Employee'
                        }
                    ).style.format({
                        'Amount': 'Rs. {:,.2f}'
                    }),
                    use_container_width=True
                )
                
                # Summary
                total_amount = expenses_df['amount'].sum()
                st.success(f"**Total Expenses:** Rs. {total_amount:,.2f}")
                
                # Download options
                col1, col2 = st.columns(2)
                with col1:
                    pdf_bytes = generate_pdf_report(
                        expenses_df[['expense_date', 'description', 'category_name', 'amount', 'vendor_name', 'payment_method', 'status']].rename(
                            columns={
                                'expense_date': 'Date',
                                'description': 'Description',
                                'category_name': 'Category',
                                'amount': 'Amount',
                                'vendor_name': 'Vendor',
                                'payment_method': 'Payment Method',
                                'status': 'Status'
                            }
                        ),
                        "Company Expenses Report",
                        date_range=(start_date, end_date),
                        orientation='L',
                        totals_cols=['Amount']
                    )
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"Company_Expenses_{start_date}_{end_date}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                with col2:
                    csv = expenses_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"Company_Expenses_{start_date}_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                st.info("ℹ️ No expenses found for the selected period.")
                
        except Exception as e:
            st.error(f"❌ Error loading expenses: {e}")
    
    with tab3:
        st.subheader("Expense Analytics")
        
        try:
            conn = get_db_connection()
            
            # Monthly expense trend
            monthly_query = """
            SELECT 
                strftime('%Y-%m', expense_date) as month,
                SUM(amount) as total_amount
            FROM company_expenses 
            WHERE expense_date >= date('now', '-6 months') AND status != 'Rejected'
            GROUP BY strftime('%Y-%m', expense_date)
            ORDER BY month
            """
            monthly_df = pd.read_sql_query(monthly_query, conn)
            
            if not monthly_df.empty:
                st.subheader("📈 Monthly Expense Trend (Last 6 Months)")
                st.bar_chart(monthly_df.set_index('month')['total_amount'])
            
            # Expense by category
            category_query = """
            SELECT 
                ec.name as category,
                SUM(ce.amount) as total_amount
            FROM company_expenses ce
            JOIN expense_categories ec ON ce.category_id = ec.id
            WHERE ce.expense_date >= date('now', '-3 months') AND ce.status != 'Rejected'
            GROUP BY ec.name
            ORDER BY total_amount DESC
            """
            category_df = pd.read_sql_query(category_query, conn)
            
            if not category_df.empty:
                st.subheader("📊 Expenses by Category (Last 3 Months)")
                st.dataframe(
                    category_df.style.format({
                        'total_amount': 'Rs. {:,.2f}'
                    }),
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"❌ Error loading analytics: {e}")

# --- Enhanced Reporting ---
def page_reporting():
    st.title("📈 Reports & Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Employee Reports", 
        "💼 Company Reports", 
        "📊 Analytics Dashboard",
        "📅 Monthly Reports"
    ])
    
    with tab1:
        st.subheader("Employee Reports")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("⚠️ No employees found.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                report_type = st.selectbox(
                    "Report Type",
                    ["Salary Sheet", "Employee Ledger", "Balance Summary", "Employee Master List"]
                )
            with col2:
                report_month = st.date_input("Report Month", date.today().replace(day=1))
            
            if st.button("Generate Employee Report"):
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                try:
                    conn = get_db_connection()
                    
                    if report_type == "Salary Sheet":
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
                            AND l.status = 'Active'
                        WHERE e.status = 'Active'
                        GROUP BY e.id, e.name, e.designation, e.salary, e.bank, e.account_title, e.account_no
                        ORDER BY e.name
                        """
                        df = pd.read_sql_query(query, conn)
                        
                    elif report_type == "Employee Ledger":
                        selected_emp = st.selectbox("Select Employee", 
                                                  options=employees_df['id'].tolist(),
                                                  format_func=lambda x: employees_df[employees_df['id'] == x]['name'].iloc[0])
                        df = get_monthly_employee_ledger(selected_emp, report_month)
                        
                    elif report_type == "Balance Summary":
                        balance_data = []
                        for _, emp in employees_df.iterrows():
                            balance = get_employee_balance(emp['id'])
                            balance_data.append({
                                'Employee ID': emp['id'],
                                'Name': emp['name'],
                                'Designation': emp['designation'],
                                'Base Salary': emp['salary'],
                                'Current Balance': balance,
                                'Net Payable': emp['salary'] + balance
                            })
                        df = pd.DataFrame(balance_data)
                        
                    elif report_type == "Employee Master List":
                        df = employees_df[['name', 'designation', 'salary', 'bank', 'account_title', 'account_no', 'join_date', 'phone', 'email']].copy()
                    
                    if not df.empty:
                        st.dataframe(df, use_container_width=True)
                        
                        # Download options
                        col1, col2 = st.columns(2)
                        with col1:
                            pdf_bytes = generate_pdf_report(
                                df, 
                                f"{report_type} - {report_month.strftime('%B %Y')}",
                                date_range=(first_day, last_day) if report_type in ["Salary Sheet", "Employee Ledger"] else None,
                                orientation='L'
                            )
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_bytes,
                                file_name=f"{report_type.replace(' ', '_')}_{report_month.strftime('%Y_%m')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        with col2:
                            csv = df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"{report_type.replace(' ', '_')}_{report_month.strftime('%Y_%m')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    else:
                        st.info("ℹ️ No data found for the selected criteria.")
                        
                except Exception as e:
                    st.error(f"❌ Error generating report: {e}")
    
    with tab2:
        st.subheader("Company Expense Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="company_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="company_end")
        
        report_type = st.selectbox("Expense Report Type", 
                                 ["Detailed Expense Report", "Category Summary", "Vendor Summary"])
        
        if st.button("Generate Expense Report"):
            try:
                conn = get_db_connection()
                
                if report_type == "Detailed Expense Report":
                    query = """
                    SELECT 
                        ce.expense_date as "Date",
                        ce.description as "Description",
                        ec.name as "Category",
                        ce.amount as "Amount",
                        ce.vendor_name as "Vendor",
                        ce.payment_method as "Payment Method",
                        ce.status as "Status",
                        e.name as "Employee"
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    LEFT JOIN employees e ON ce.employee_id = e.id
                    WHERE ce.expense_date BETWEEN ? AND ? AND ce.status != 'Rejected'
                    ORDER BY ce.expense_date DESC
                    """
                    df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                    
                elif report_type == "Category Summary":
                    query = """
                    SELECT 
                        ec.name as "Category",
                        COUNT(ce.id) as "Count",
                        SUM(ce.amount) as "Total Amount"
                    FROM company_expenses ce
                    JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ? AND ce.status != 'Rejected'
                    GROUP BY ec.name
                    ORDER BY SUM(ce.amount) DESC
                    """
                    df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                    
                elif report_type == "Vendor Summary":
                    query = """
                    SELECT 
                        ce.vendor_name as "Vendor",
                        COUNT(ce.id) as "Count",
                        SUM(ce.amount) as "Total Amount"
                    FROM company_expenses ce
                    WHERE ce.expense_date BETWEEN ? AND ? AND ce.status != 'Rejected'
                    GROUP BY ce.vendor_name
                    ORDER BY SUM(ce.amount) DESC
                    """
                    df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
                if not df.empty:
                    st.dataframe(
                        df.style.format({
                            'Amount': 'Rs. {:,.2f}',
                            'Total Amount': 'Rs. {:,.2f}'
                        }) if 'Amount' in df.columns or 'Total Amount' in df.columns else df,
                        use_container_width=True
                    )
                    
                    # Download options
                    col1, col2 = st.columns(2)
                    with col1:
                        pdf_bytes = generate_pdf_report(
                            df, 
                            f"{report_type}",
                            date_range=(start_date, end_date),
                            orientation='L',
                            totals_cols=['Amount', 'Total Amount'] if 'Amount' in df.columns or 'Total Amount' in df.columns else None
                        )
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"{report_type.replace(' ', '_')}_{start_date}_{end_date}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with col2:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"{report_type.replace(' ', '_')}_{start_date}_{end_date}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                else:
                    st.info("ℹ️ No data found for the selected criteria.")
                    
            except Exception as e:
                st.error(f"❌ Error generating expense report: {e}")
    
    with tab3:
        st.subheader("Analytics Dashboard")
        
        try:
            # Key metrics
            emp_count, exp_total, cat_count, salary_total = get_dashboard_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Employees", emp_count)
            with col2:
                st.metric("Monthly Salary", f"Rs. {salary_total:,.2f}")
            with col3:
                st.metric("Monthly Expenses", f"Rs. {exp_total:,.2f}")
            with col4:
                st.metric("Expense Categories", cat_count)
            
            # Expense trends
            conn = get_db_connection()
            monthly_exp_query = """
            SELECT 
                strftime('%Y-%m', expense_date) as month,
                SUM(amount) as total_amount
            FROM company_expenses 
            WHERE expense_date >= date('now', '-12 months') AND status != 'Rejected'
            GROUP BY strftime('%Y-%m', expense_date)
            ORDER BY month
            """
            monthly_exp_df = pd.read_sql_query(monthly_exp_query, conn)
            
            if not monthly_exp_df.empty:
                st.subheader("📈 Monthly Expense Trend (Last 12 Months)")
                st.line_chart(monthly_exp_df.set_index('month')['total_amount'])
            
            # Employee salary distribution
            emp_salary_df = get_all_employees()
            if not emp_salary_df.empty:
                st.subheader("💰 Employee Salary Distribution")
                st.bar_chart(emp_salary_df.set_index('name')['salary'])
                
        except Exception as e:
            st.error(f"❌ Error loading analytics: {e}")
    
    with tab4:
        st.subheader("Monthly Consolidated Reports")
        
        report_month = st.date_input("Select Month", date.today().replace(day=1), key="consolidated_month")
        
        if st.button("Generate Monthly Consolidated Report"):
            try:
                # Generate comprehensive monthly report
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                conn = get_db_connection()
                
                # Salary Summary
                salary_query = f"""
                SELECT
                    e.name AS "Employee Name",
                    e.designation AS "Designation",
                    e.salary AS "Base Salary",
                    COALESCE(SUM(l.credit), 0) AS "Total Credits",
                    COALESCE(SUM(l.debit), 0) AS "Total Deductions",
                    (COALESCE(SUM(l.credit), 0) - COALESCE(SUM(l.debit), 0)) AS "Net Salary"
                FROM employees e
                LEFT JOIN employee_ledger l ON e.id = l.employee_id
                    AND l.entry_date BETWEEN '{first_day}' AND '{last_day}'
                    AND l.status = 'Active'
                WHERE e.status = 'Active'
                GROUP BY e.id, e.name, e.designation, e.salary
                ORDER BY e.name
                """
                salary_df = pd.read_sql_query(salary_query, conn)
                
                # Expense Summary
                expense_query = """
                SELECT 
                    ec.name as "Category",
                    COUNT(ce.id) as "Count",
                    SUM(ce.amount) as "Total Amount"
                FROM company_expenses ce
                JOIN expense_categories ec ON ce.category_id = ec.id
                WHERE ce.expense_date BETWEEN ? AND ? AND ce.status != 'Rejected'
                GROUP BY ec.name
                ORDER BY SUM(ce.amount) DESC
                """
                expense_df = pd.read_sql_query(expense_query, conn, params=(str(first_day), str(last_day)))
                
                # Create consolidated report
                st.success(f"📊 Monthly Consolidated Report - {report_month.strftime('%B %Y')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    total_salary = salary_df['Net Salary'].sum() if not salary_df.empty else 0
                    st.metric("Total Salary Payable", f"Rs. {total_salary:,.2f}")
                with col2:
                    total_expenses = expense_df['Total Amount'].sum() if not expense_df.empty else 0
                    st.metric("Total Company Expenses", f"Rs. {total_expenses:,.2f}")
                
                # Download consolidated PDF
                if st.button("📥 Download Consolidated Report (PDF)"):
                    # Create a comprehensive PDF with both salary and expense summaries
                    pdf = PDF(orientation='L', unit='mm', format='A4')
                    pdf.report_title = f"Monthly Consolidated Report - {report_month.strftime('%B %Y')}"
                    pdf.date_range_str = f"{first_day.strftime('%d %b %Y')} to {last_day.strftime('%d %b %Y')}"
                    pdf.add_page()
                    
                    # Add salary summary
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 10, "Salary Summary", 0, 1)
                    if not salary_df.empty:
                        pdf.add_table(salary_df, totals_cols=["Base Salary", "Total Credits", "Total Deductions", "Net Salary"])
                    else:
                        pdf.cell(0, 10, "No salary data available", 0, 1)
                    
                    pdf.add_page()
                    
                    # Add expense summary
                    pdf.set_font('Arial', 'B', 14)
                    pdf.cell(0, 10, "Expense Summary", 0, 1)
                    if not expense_df.empty:
                        pdf.add_table(expense_df, totals_cols=["Total Amount"])
                    else:
                        pdf.cell(0, 10, "No expense data available", 0, 1)
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    st.download_button(
                        label="Download Consolidated PDF",
                        data=pdf_bytes,
                        file_name=f"Consolidated_Report_{report_month.strftime('%Y_%m')}.pdf",
                        mime="application/pdf"
                    )
                    
            except Exception as e:
                st.error(f"❌ Error generating consolidated report: {e}")

# --- Enhanced Data Import/Export ---
def page_data_import():
    st.title("📤 Data Import & Export")
    
    tab1, tab2, tab3 = st.tabs(["📤 Export Data", "📥 Import Data", "🔄 Data Templates"])
    
    with tab1:
        st.subheader("Export Data")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 👥 Employee Data")
            employees_df = get_all_employees(active_only=False)
            if not employees_df.empty:
                csv_employees = employees_df.to_csv(index=False)
                st.download_button(
                    label="📥 Export Employees (CSV)",
                    data=csv_employees,
                    file_name="employees_export.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.info("No employee data to export")
        
        with col2:
            st.markdown("#### 💼 Expense Data")
            try:
                conn = get_db_connection()
                expenses_df = pd.read_sql_query(
                    "SELECT * FROM company_expenses ORDER BY expense_date DESC",
                    conn
                )
                if not expenses_df.empty:
                    csv_expenses = expenses_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Export Expenses (CSV)",
                        data=csv_expenses,
                        file_name="expenses_export.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.info("No expense data to export")
            except:
                st.info("No expense data to export")
        
        with col3:
            st.markdown("#### 💸 Ledger Data")
            try:
                conn = get_db_connection()
                ledger_df = pd.read_sql_query(
                    "SELECT * FROM employee_ledger ORDER BY entry_date DESC",
                    conn
                )
                if not ledger_df.empty:
                    csv_ledger = ledger_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Export Ledger (CSV)",
                        data=csv_ledger,
                        file_name="ledger_export.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                else:
                    st.info("No ledger data to export")
            except:
                st.info("No ledger data to export")
    
    with tab2:
        st.subheader("Import Data")
        
        st.info("""
        **Import Instructions:**
        - Download templates from the Templates tab
        - Fill in the data according to the template format
        - Upload the completed file here
        - Review the data before importing
        """)
        
        import_type = st.selectbox("Select Data Type to Import", 
                                 ["Employees", "Company Expenses", "Employee Ledger"])
        
        uploaded_file = st.file_uploader(f"Choose {import_type} file", type=['csv', 'xlsx'])
        
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.write("Preview of data to import:")
                st.dataframe(df.head())
                
                if st.button(f"🚀 Import {import_type}"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    imported_count = 0
                    error_count = 0
                    
                    if import_type == "Employees":
                        required_cols = ['name', 'designation', 'salary']
                        missing_cols = [col for col in required_cols if col not in df.columns]
                        
                        if missing_cols:
                            st.error(f"❌ Missing required columns: {', '.join(missing_cols)}")
                        else:
                            for index, row in df.iterrows():
                                try:
                                    name = str(row['name']).strip()
                                    designation = str(row['designation']).strip()
                                    salary = float(row['salary'])
                                    bank = str(row['bank']) if 'bank' in df.columns and pd.notna(row['bank']) else ""
                                    account_title = str(row['account_title']) if 'account_title' in df.columns and pd.notna(row['account_title']) else ""
                                    account_no = str(row['account_no']) if 'account_no' in df.columns and pd.notna(row['account_no']) else ""
                                    join_date = str(row['join_date']) if 'join_date' in df.columns and pd.notna(row['join_date']) else str(date.today())
                                    phone = str(row['phone']) if 'phone' in df.columns and pd.notna(row['phone']) else ""
                                    email = str(row['email']) if 'email' in df.columns and pd.notna(row['email']) else ""
                                    address = str(row['address']) if 'address' in df.columns and pd.notna(row['address']) else ""
                                    
                                    cursor.execute(
                                        """
                                        INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date, phone, email, address)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                        (name, designation, salary, bank, account_title, account_no, join_date, phone, email, address)
                                    )
                                    imported_count += 1
                                except Exception as e:
                                    error_count += 1
                                    st.warning(f"Error importing row {index + 2}: {str(e)}")
                    
                    elif import_type == "Company Expenses":
                        # Similar implementation for expenses
                        pass
                    
                    elif import_type == "Employee Ledger":
                        # Similar implementation for ledger
                        pass
                    
                    conn.commit()
                    
                    if imported_count > 0:
                        st.success(f"✅ Successfully imported {imported_count} records!")
                    if error_count > 0:
                        st.error(f"❌ Failed to import {error_count} records.")
                    
                    clear_cache()
                    
            except Exception as e:
                st.error(f"❌ Error reading file: {e}")
    
    with tab3:
        st.subheader("Download Import Templates")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 👥 Employee Template")
            employee_template = pd.DataFrame(columns=[
                'name', 'designation', 'salary', 'bank', 'account_title', 'account_no', 
                'join_date', 'phone', 'email', 'address'
            ])
            csv_employee_template = employee_template.to_csv(index=False)
            st.download_button(
                label="📋 Download Employee Template",
                data=csv_employee_template,
                file_name="employee_import_template.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.markdown("#### 💼 Expense Template")
            expense_template = pd.DataFrame(columns=[
                'description', 'amount', 'expense_date', 'category_id', 'vendor_name', 
                'payment_method', 'status'
            ])
            csv_expense_template = expense_template.to_csv(index=False)
            st.download_button(
                label="📋 Download Expense Template",
                data=csv_expense_template,
                file_name="expense_import_template.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col3:
            st.markdown("#### 💸 Ledger Template")
            ledger_template = pd.DataFrame(columns=[
                'employee_id', 'entry_date', 'description', 'debit', 'credit', 'category'
            ])
            csv_ledger_template = ledger_template.to_csv(index=False)
            st.download_button(
                label="📋 Download Ledger Template",
                data=csv_ledger_template,
                file_name="ledger_import_template.csv",
                mime="text/csv",
                use_container_width=True
            )

# --- Enhanced Dashboard ---
def page_dashboard():
    st.title(f"🏠 Welcome to {COMPANY_NAME} HR & Expense Manager")
    
    # Try to display company logo
    logo_paths = ['logo.png', 'nutrion_logo.png', 'company_logo.png', 'assets/logo.png']
    logo_found = False
    
    for logo_path in logo_paths:
        try:
            if os.path.exists(logo_path):
                st.image(logo_path, width=200)
                logo_found = True
                break
        except:
            continue
    
    if not logo_found:
        st.markdown(f"<h2 style='text-align: center; color: #1f77b4;'>{COMPANY_NAME}</h2>", unsafe_allow_html=True)
    
    try:
        emp_count, exp_total, cat_count, salary_total = get_dashboard_stats()
        
        st.subheader("📊 Quick Overview (Current Month)")
        cols = st.columns(4)
        with cols[0]:
            st.metric("Total Employees", f"{emp_count}")
        with cols[1]:
            st.metric("Monthly Salary", f"Rs. {salary_total:,.2f}")
        with cols[2]:
            st.metric("Company Expenses", f"Rs. {exp_total:,.2f}")
        with cols[3]:
            st.metric("Expense Categories", f"{cat_count}")
    
    except Exception as e:
        st.warning(f"Could not load dashboard stats: {e}")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👥 Add Employee", use_container_width=True):
            st.session_state.current_page = "👥 Employee Management"
            st.rerun()
    
    with col2:
        if st.button("💰 Add Expense", use_container_width=True):
            st.session_state.current_page = "💰 Employee Expense Management"
            st.rerun()
    
    with col3:
        if st.button("💸 Process Salary", use_container_width=True):
            st.session_state.current_page = "💰 Employee Expense Management"
            st.rerun()
    
    with col4:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.current_page = "📈 Reports & Analytics"
            st.rerun()
    
    st.info("""
    **📋 Navigation Guide:**
    - **💰 Employee Expenses**: Add expenses, track balances, process salaries
    - **👥 Employee Management**: Add and manage employee records
    - **💼 Company Expenses**: Log company-wide expenses
    - **📈 Reports**: Download various reports and analytics
    - **📤 Data Import**: Bulk import and export data
    """)
    
    # Recent Activity
    try:
        st.subheader("📋 Recent Activity")
        conn = get_db_connection()
        
        # Recent employees
        recent_employees = pd.read_sql_query(
            "SELECT name, designation, join_date FROM employees WHERE status = 'Active' ORDER BY created_at DESC LIMIT 5",
            conn
        )
        
        # Recent expenses
        recent_expenses = pd.read_sql_query(
            "SELECT description, amount, expense_date FROM company_expenses WHERE status != 'Rejected' ORDER BY created_at DESC LIMIT 5",
            conn
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👥 Recent Employees")
            if not recent_employees.empty:
                for _, emp in recent_employees.iterrows():
                    st.write(f"**{emp['name']}** - {emp['designation']} (Joined: {emp['join_date']})")
            else:
                st.info("No employees added yet")
        
        with col2:
            st.markdown("#### 💰 Recent Expenses")
            if not recent_expenses.empty:
                for _, exp in recent_expenses.iterrows():
                    st.write(f"**{exp['description']}** - Rs. {exp['amount']:,.2f} ({exp['expense_date']})")
            else:
                st.info("No expenses recorded yet")
                
    except Exception as e:
        st.error(f"Error loading recent activity: {e}")

# --- Main App with Enhanced Navigation ---
def main():
    st.set_page_config(
        page_title=f"{COMPANY_NAME} HR System", 
        layout="wide",
        page_icon="💰",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced Custom CSS for better UI
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        transition: transform 0.2s;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
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
        border-radius: 5px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 5px rgba(0,0,0,0.2);
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_db()

    # Sidebar with enhanced navigation
    st.sidebar.title(f"{COMPANY_NAME} HR System")
    
    # Try to display logo in sidebar
    sidebar_logo_paths = ['logo.png', 'nutrion_logo.png', 'company_logo.png', 'assets/logo.png']
    sidebar_logo_found = False
    
    for logo_path in sidebar_logo_paths:
        try:
            if os.path.exists(logo_path):
                st.sidebar.image(logo_path, width=150)
                sidebar_logo_found = True
                break
        except:
            continue
    
    if not sidebar_logo_found:
        st.sidebar.markdown(f"<h3 style='text-align: center;'>{COMPANY_NAME}</h3>", unsafe_allow_html=True)
        
    # Enhanced navigation with better grouping
    st.sidebar.markdown("### 🎯 Core Functions")
    page_options = {
        "💰 Employee Expenses": page_employee_expense_management,
        "👥 Employee Management": page_employee_management,
        "💼 Company Expenses": page_expense_management,
    }
    
    st.sidebar.markdown("### 📊 Reports & Tools")
    page_options.update({
        "📈 Reports & Analytics": page_reporting,
        "📤 Data Import/Export": page_data_import,
        "🏠 Dashboard": page_dashboard,
    })
    
    # Initialize session state for current page
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard"
    
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()), 
                                   index=list(page_options.keys()).index(st.session_state.current_page))
    
    # Update current page
    st.session_state.current_page = selected_page
    
    st.sidebar.divider()
    st.sidebar.markdown("### 🚀 Quick Actions")
    
    if st.sidebar.button("➕ Add New Employee", use_container_width=True):
        st.session_state.current_page = "👥 Employee Management"
        st.rerun()
    
    if st.sidebar.button("💸 Record Expense", use_container_width=True):
        st.session_state.current_page = "💰 Employee Expenses"
        st.rerun()
    
    if st.sidebar.button("📊 Generate Reports", use_container_width=True):
        st.session_state.current_page = "📈 Reports & Analytics"
        st.rerun()
    
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    # Render the selected page
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
