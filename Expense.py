import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
import base64
import tempfile
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go

# --- Constants ---
DB_FILE = "nutrion_hr.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92 320 7429422"

# --- Custom CSS for Better UI ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #2c3e50 0%, #3498db 100%);
    }
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: 500;
    }
    .stButton button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        color: white;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 12px;
        border-radius: 5px;
        border: 1px solid #c3e6cb;
        margin: 10px 0;
    }
    .warning-message {
        background-color: #fff3cd;
        color: #856404;
        padding: 12px;
        border-radius: 5px;
        border: 1px solid #ffeaa7;
        margin: 10px 0;
    }
    .info-message {
        background-color: #d1ecf1;
        color: #0c5460;
        padding: 12px;
        border-radius: 5px;
        border: 1px solid #bee5eb;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# --- PDF Class with Header/Footer and Logo ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""
        self.company_name = COMPANY_NAME

    def header(self):
        # Add company logo
        logo_path = "logo.png"
        if os.path.exists(logo_path):
            try:
                self.image(logo_path, 10, 8, 25)
            except:
                pass
        
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, self.company_name, 0, 1, 'C')
        self.set_font('Arial', 'B', 14)
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
            signature_path = "signature.png"
            if os.path.exists(signature_path):
                self.image(signature_path, self.l_margin, self.get_y(), 40)
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
    
    if 'join_date' not in columns:
        c.execute("ALTER TABLE employees ADD COLUMN join_date DATE")
    
    # Check and update employee_ledger table
    c.execute("PRAGMA table_info(employee_ledger)")
    ledger_columns = [column[1] for column in c.fetchall()]
    
    if 'related_expense_id' not in ledger_columns:
        c.execute("ALTER TABLE employee_ledger ADD COLUMN related_expense_id INTEGER")
    
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
            department TEXT,
            phone TEXT,
            email TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT DEFAULT 'General'
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
            payment_method TEXT DEFAULT 'Cash',
            reference_no TEXT,
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
            type TEXT DEFAULT 'General',
            status TEXT DEFAULT 'Processed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (related_expense_id) REFERENCES company_expenses (id) ON DELETE SET NULL
        )
    ''')
    
    # Pre-populate expense categories
    default_categories = [
        ("Guard", "Security"),
        ("Labour", "Operations"),
        ("Bilty Expenses", "Logistics"),
        ("Office Rent", "Administration"),
        ("Warehouse Rent", "Operations"),
        ("Import Export", "Logistics"),
        ("Office Electricity", "Administration"),
        ("FBR", "Tax"),
        ("Office Entertainment", "Administration"),
        ("PSID", "Tax"),
        ("Advance", "Finance"),
        ("Commission", "Sales"),
        ("Office Stationery Expense", "Administration"),
        ("Employee Expenses", "HR"),
        ("Other Expense", "General"),
        ("Company Expense", "General"),
        ("Salary", "HR"),
        ("Travel", "Operations"),
        ("Meals", "Operations"),
        ("Fuel", "Operations"),
        ("Maintenance", "Operations"),
        ("Marketing", "Sales"),
        ("Training", "HR")
    ]
    
    for category, category_type in default_categories:
        c.execute("INSERT OR IGNORE INTO expense_categories (name, type) VALUES (?, ?)", (category, category_type))
    
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
@st.cache_data(ttl=300)
def get_all_employees():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
    if 'join_date' in df.columns:
        df['join_date'] = df['join_date'].astype(str)
    return df

@st.cache_data(ttl=300)
def get_all_categories():
    conn = get_db_connection()
    return pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)

@st.cache_data(ttl=300)
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
    
    # Total salary expense
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

def get_monthly_employee_ledger(employee_id, month_date):
    """Get ledger entries for a specific month"""
    first_day = month_date.replace(day=1)
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    conn = get_db_connection()
    ledger_df = pd.read_sql_query(
        """
        SELECT entry_date, description, debit, credit 
        FROM employee_ledger 
        WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
        ORDER BY entry_date
        """,
        conn,
        params=(employee_id, str(first_day), str(last_day))
    )
    return ledger_df

# --- Dashboard Page ---
def page_dashboard():
    st.markdown(f'<div class="main-header">{COMPANY_NAME} HR & Expense Manager</div>', unsafe_allow_html=True)
    
    try:
        st.image('logo.png', width=150)
    except:
        pass
    
    # Quick Stats
    try:
        emp_count, exp_total, cat_count, salary_total = get_dashboard_stats()
        
        st.subheader("📊 Quick Overview (Current Month)")
        cols = st.columns(4)
        with cols[0]:
            st.markdown(f'<div class="metric-card">👥 Total Employees<br><h3>{emp_count}</h3></div>', unsafe_allow_html=True)
        with cols[1]:
            st.markdown(f'<div class="metric-card">💰 Company Expenses<br><h3>Rs. {exp_total:,.2f}</h3></div>', unsafe_allow_html=True)
        with cols[2]:
            st.markdown(f'<div class="metric-card">📂 Expense Categories<br><h3>{cat_count}</h3></div>', unsafe_allow_html=True)
        with cols[3]:
            st.markdown(f'<div class="metric-card">💵 Monthly Salary<br><h3>Rs. {salary_total:,.2f}</h3></div>', unsafe_allow_html=True)
    
    except Exception as e:
        st.warning(f"Could not load dashboard stats: {e}")
    
    # Recent Activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Recent Employees")
        employees_df = get_all_employees()
        if not employees_df.empty:
            recent_employees = employees_df.head(5)
            for _, emp in recent_employees.iterrows():
                st.write(f"**{emp['name']}** - {emp['designation']} (Rs. {emp['salary']:,.2f})")
        else:
            st.info("No employees added yet")
    
    with col2:
        st.subheader("📈 Expense Summary")
        conn = get_db_connection()
        expense_summary = pd.read_sql_query(
            "SELECT ec.name as category, SUM(ce.amount) as total FROM company_expenses ce JOIN expense_categories ec ON ce.category_id = ec.id WHERE strftime('%Y-%m', ce.expense_date) = strftime('%Y-%m', 'now') GROUP BY ec.name ORDER BY total DESC LIMIT 5",
            conn
        )
        
        if not expense_summary.empty:
            for _, exp in expense_summary.iterrows():
                st.write(f"**{exp['category']}**: Rs. {exp['total']:,.2f}")
        else:
            st.info("No expenses recorded this month")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    cols = st.columns(4)
    
    with cols[0]:
        if st.button("➕ Add Employee", use_container_width=True):
            st.session_state.current_page = "👥 Employee Management"
            st.rerun()
    
    with cols[1]:
        if st.button("💰 Add Expense", use_container_width=True):
            st.session_state.current_page = "💼 Company Expenses"
            st.rerun()
    
    with cols[2]:
        if st.button("📊 Generate Reports", use_container_width=True):
            st.session_state.current_page = "📈 Reports"
            st.rerun()
    
    with cols[3]:
        if st.button("💸 Process Salary", use_container_width=True):
            st.session_state.current_page = "💰 Employee Expenses"
            st.rerun()

# --- Employee Expense Management ---
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
    
    # Main Tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["➕ Add Expense", "📊 Employee Balances", "🔍 Expense History", "💸 Salary Processing", "📄 Salary Slips"])
    
    with tab1:
        st.subheader("Add Employee Expense/Advance")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("No employees found. Please add employees first.")
        else:
            employee_list = {row['id']: f"{row['name']} - {row['designation']} (Salary: Rs. {row['salary']:,.2f})" 
                           for index, row in employees_df.iterrows()}
            
            with st.form("add_employee_expense"):
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
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, type)
                                    VALUES (?, ?, ?, ?, 0, ?)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount, expense_type)
                                )
                                message_type = "expense"
                            else:
                                # Credit entry (bonus/other credit)
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, type)
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
                    'Employee ID': emp['id'],
                    'Name': emp['name'],
                    'Designation': emp['designation'],
                    'Base Salary': emp['salary'],
                    'Current Balance': balance,
                    'Net Payable': emp['salary'] + balance
                })
            
            balance_df = pd.DataFrame(balance_data)
            
            # Display with color coding
            st.dataframe(
                balance_df.style.format({
                    'Base Salary': 'Rs. {:,.2f}',
                    'Current Balance': 'Rs. {:,.2f}',
                    'Net Payable': 'Rs. {:,.2f}'
                }).applymap(lambda x: 'color: red' if isinstance(x, (int, float)) and x < 0 else 'color: black'),
                use_container_width=True
            )
            
            # Download option
            if st.button("📥 Download Balance Sheet"):
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
                            type as "Type",
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
                        
                        st.metric("Net Balance for Period", f"Rs. {net_balance:,.2f}")
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
                            # Check if already generated
                            cursor.execute(
                                "SELECT 1 FROM employee_ledger WHERE employee_id = ? AND description = ?",
                                (emp['id'], description)
                            )
                            if cursor.fetchone():
                                skipped_count += 1
                                continue
                                
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, type)
                                VALUES (?, ?, ?, 0, ?, 'Salary Credit')
                                """,
                                (emp['id'], str(first_day), description, salary)
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
                        st.warning("No salary data found.")
                    else:
                        st.dataframe(salary_df, use_container_width=True)
                        
                        # Show summary
                        total_base = salary_df['Base Salary'].sum()
                        total_net = salary_df['Net Salary'].sum()
                        total_deductions = salary_df['Total Deductions'].sum()
                        
                        st.success(f"**Summary:** Base Salary: Rs. {total_base:,.2f} | Deductions: Rs. {total_deductions:,.2f} | Net Payable: Rs. {total_net:,.2f}")
                        
                        # Download button
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
                        
                except Exception as e:
                    st.error(f"Error generating salary sheet: {e}")

    with tab5:
        st.subheader("Individual Salary Slips")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("No employees found.")
        else:
            employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
            
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
                    
                    # Get ledger for the month
                    ledger_df = get_monthly_employee_ledger(selected_emp_id, slip_month)
                    
                    # Calculate totals
                    total_credits = ledger_df['credit'].sum()
                    total_debits = ledger_df['debit'].sum()
                    net_salary = total_credits - total_debits
                    
                    # Generate PDF
                    pdf_bytes = generate_individual_slip_pdf(
                        emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary
                    )
                    
                    # Download button
                    st.download_button(
                        label=f"📥 Download Salary Slip for {emp_details['name']}",
                        data=pdf_bytes,
                        file_name=f"Salary_Slip_{emp_details['name']}_{slip_month.strftime('%B_%Y')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error generating salary slip: {e}")

# --- Employee Management ---
def page_employee_management():
    st.title("👥 Employee Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add New Employee", "📋 Manage Employees", "📊 Employee Analytics"])
    
    with tab1:
        st.subheader("Add New Employee")
        with st.form("new_employee_form", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                name = st.text_input("Full Name *", placeholder="e.g., Ali Ahmed")
                salary = st.number_input("Monthly Base Salary (Rs.) *", min_value=0.0, step=1000.0, value=0.0)
                bank = st.text_input("Bank Name", placeholder="e.g., HBL, UBL, MCB")
                join_date = st.date_input("Joining Date", date.today())
                department = st.text_input("Department", placeholder="e.g., Sales, IT, HR")
            with cols[1]:
                designation = st.text_input("Designation *", placeholder="e.g., Sales Manager, Accountant")
                account_title = st.text_input("Account Title", placeholder="e.g., Ali Ahmed")
                account_no = st.text_input("Account Number", placeholder="e.g., 0123456789")
                phone = st.text_input("Phone Number", placeholder="e.g., 0300-1234567")
                email = st.text_input("Email Address", placeholder="e.g., ali.ahmed@company.com")
                
            submitted = st.form_submit_button("💾 Add Employee")
            if submitted:
                if not name or not designation:
                    st.error("❌ Name and Designation are required fields.")
                else:
                    try:
                        conn = get_db_connection()
                        conn.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date, department, phone, email)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (name, designation, salary, bank, account_title, account_no, str(join_date), department, phone, email)
                        )
                        conn.commit()
                        st.success(f"✅ Employee '{name}' added successfully!")
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
            display_cols = ['id', 'name', 'designation', 'department', 'salary', 'Current Balance', 'Net Payable', 'bank', 'join_date', 'phone']
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
            employee_names = {row['id']: row['name'] for _, row in employees_df.iterrows()}
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
                        edit_bank = st.text_input("Bank", value=emp_data['bank'])
                        edit_department = st.text_input("Department", value=emp_data.get('department', ''))
                    with cols[1]:
                        edit_designation = st.text_input("Designation", value=emp_data['designation'])
                        edit_account_title = st.text_input("Account Title", value=emp_data['account_title'])
                        edit_account_no = st.text_input("Account No", value=emp_data['account_no'])
                        edit_phone = st.text_input("Phone", value=emp_data.get('phone', ''))
                    
                    edit_email = st.text_input("Email", value=emp_data.get('email', ''))
                    edit_status = st.selectbox("Status", ["Active", "Inactive"], 
                                             index=0 if emp_data.get('status', 'Active') == 'Active' else 1)
                    
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
                                department = ?, phone = ?, email = ?, status = ?
                                WHERE id = ?
                                """,
                                (edit_name, edit_designation, edit_salary, edit_bank, edit_account_title, edit_account_no,
                                 edit_department, edit_phone, edit_email, edit_status, selected_emp_id)
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
        st.subheader("Employee Analytics")
        
        employees_df = get_all_employees()
        if not employees_df.empty:
            # Department-wise distribution
            if 'department' in employees_df.columns:
                dept_counts = employees_df['department'].value_counts()
                fig1 = px.pie(values=dept_counts.values, names=dept_counts.index, 
                             title="Department Distribution")
                st.plotly_chart(fig1, use_container_width=True)
            
            # Salary distribution
            fig2 = px.histogram(employees_df, x='salary', nbins=10, 
                               title="Salary Distribution")
            st.plotly_chart(fig2, use_container_width=True)
            
            # Balance overview
            balance_data = []
            for _, emp in employees_df.iterrows():
                balance = get_employee_balance(emp['id'])
                balance_data.append({
                    'Name': emp['name'],
                    'Balance': balance,
                    'Status': 'Due' if balance > 0 else 'Advance' if balance < 0 else 'Settled'
                })
            
            balance_df = pd.DataFrame(balance_data)
            fig3 = px.bar(balance_df, x='Name', y='Balance', color='Status',
                         title="Employee Balances Overview")
            st.plotly_chart(fig3, use_container_width=True)

# --- Company Expense Management ---
def page_expense_management():
    st.title("💼 Company Expense Management")
    
    st.info("""
    **Note:** This page is for company expenses that are NOT linked to specific employees.
    For employee-specific expenses and advances, use the **Employee Expense Management** page.
    """)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Expense", "📋 Expense List", "📊 Expense Analytics", "🗂️ Categories"])
    
    with tab1:
        st.subheader("Add Company Expense")
        
        categories_df = get_all_categories()
        employees_df = get_all_employees()
        
        with st.form("add_company_expense"):
            cols = st.columns(2)
            with cols[0]:
                description = st.text_input("Description *", placeholder="e.g., Office supplies purchase")
                amount = st.number_input("Amount (Rs.) *", min_value=0.01, step=100.0)
                category_id = st.selectbox(
                    "Category *",
                    options=categories_df['id'].tolist(),
                    format_func=lambda x: categories_df[categories_df['id'] == x]['name'].iloc[0]
                )
            with cols[1]:
                expense_date = st.date_input("Expense Date *", date.today())
                employee_id = st.selectbox(
                    "Related Employee (Optional)",
                    options=[None] + employees_df['id'].tolist(),
                    format_func=lambda x: "Select..." if x is None else employees_df[employees_df['id'] == x]['name'].iloc[0]
                )
                payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Cheque", "Card"])
            
            reference_no = st.text_input("Reference No (Optional)", placeholder="e.g., Invoice number")
            
            submitted = st.form_submit_button("💾 Add Expense")
            if submitted:
                if description and amount > 0:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id, payment_method, reference_no)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (description, amount, str(expense_date), category_id, 
                             employee_id if employee_id else None, payment_method, reference_no)
                        )
                        
                        conn.commit()
                        st.success("✅ Company expense added successfully!")
                        clear_cache()
                    except sqlite3.Error as e:
                        st.error(f"❌ Database error: {e}")
                else:
                    st.error("❌ Please fill in all required fields.")
    
    with tab2:
        st.subheader("Company Expenses")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", date.today())
        with col3:
            categories_df = get_all_categories()
            selected_category = st.selectbox(
                "Filter by Category",
                options=["All"] + categories_df['id'].tolist(),
                format_func=lambda x: "All Categories" if x == "All" else categories_df[categories_df['id'] == x]['name'].iloc[0]
            )
        
        if st.button("🔍 Filter Expenses"):
            try:
                conn = get_db_connection()
                query = """
                SELECT ce.id, ce.description, ce.amount, ce.expense_date, ec.name as category, 
                       e.name as employee_name, ce.payment_method, ce.reference_no
                FROM company_expenses ce
                LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                LEFT JOIN employees e ON ce.employee_id = e.id
                WHERE ce.expense_date BETWEEN ? AND ?
                """
                params = [str(start_date), str(end_date)]
                
                if selected_category != "All":
                    query += " AND ce.category_id = ?"
                    params.append(selected_category)
                
                query += " ORDER BY ce.expense_date DESC"
                
                expenses_df = pd.read_sql_query(query, conn, params=params)
                
                if not expenses_df.empty:
                    st.dataframe(
                        expenses_df.style.format({
                            'amount': 'Rs. {:,.2f}'
                        }),
                        use_container_width=True
                    )
                    
                    total_amount = expenses_df['amount'].sum()
                    st.metric("Total Expenses", f"Rs. {total_amount:,.2f}")
                    
                    # Download option
                    pdf_bytes = generate_pdf_report(
                        expenses_df,
                        "Company Expenses Report",
                        date_range=(start_date, end_date),
                        totals_cols=['amount']
                    )
                    st.download_button(
                        label="📥 Download Expenses Report",
                        data=pdf_bytes,
                        file_name=f"Company_Expenses_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.info("No expenses found for the selected criteria.")
                    
            except Exception as e:
                st.error(f"Error loading expenses: {e}")
    
    with tab3:
        st.subheader("Expense Analytics")
        
        try:
            conn = get_db_connection()
            
            # Monthly trend
            monthly_expenses = pd.read_sql_query("""
                SELECT strftime('%Y-%m', expense_date) as month, SUM(amount) as total
                FROM company_expenses
                GROUP BY month
                ORDER BY month
            """, conn)
            
            if not monthly_expenses.empty:
                fig1 = px.line(monthly_expenses, x='month', y='total', 
                              title="Monthly Expense Trend")
                st.plotly_chart(fig1, use_container_width=True)
            
            # Category-wise breakdown
            category_expenses = pd.read_sql_query("""
                SELECT ec.name as category, SUM(ce.amount) as total
                FROM company_expenses ce
                JOIN expense_categories ec ON ce.category_id = ec.id
                GROUP BY ec.name
                ORDER BY total DESC
            """, conn)
            
            if not category_expenses.empty:
                fig2 = px.pie(category_expenses, values='total', names='category',
                             title="Expenses by Category")
                st.plotly_chart(fig2, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error loading analytics: {e}")
    
    with tab4:
        st.subheader("Expense Categories")
        
        categories_df = get_all_categories()
        st.dataframe(categories_df, use_container_width=True)
        
        with st.form("add_category_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_category = st.text_input("New Category Name")
            with col2:
                category_type = st.selectbox("Category Type", ["General", "Administration", "Operations", "Sales", "HR", "Tax", "Security", "Logistics"])
            
            if st.form_submit_button("➕ Add Category"):
                if new_category:
                    try:
                        conn = get_db_connection()
                        conn.execute(
                            "INSERT OR IGNORE INTO expense_categories (name, type) VALUES (?, ?)",
                            (new_category, category_type)
                        )
                        conn.commit()
                        st.success("✅ Category added successfully!")
                        clear_cache()
                        st.rerun()
                    except sqlite3.Error as e:
                        st.error(f"❌ Database error: {e}")
                else:
                    st.error("❌ Please enter a category name.")

# --- Reports Page ---
def page_reporting():
    st.title("📈 Reports & Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Employee Reports", "💼 Company Reports", "📊 Analytics Dashboard", "📤 Data Export"])
    
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
                    ["Salary Sheet", "Employee Ledger", "Balance Summary", "Employee Master List"]
                )
            with col2:
                report_month = st.date_input("Report Month", date.today().replace(day=1))
            
            if st.button("Generate Employee Report"):
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                if report_type == "Salary Sheet":
                    conn = get_db_connection()
                    query = f"""
                    SELECT
                        e.name AS "Employee Name",
                        e.designation AS "Designation",
                        e.department AS "Department",
                        e.salary AS "Base Salary",
                        COALESCE(SUM(l.credit), 0) AS "Total Credits",
                        COALESCE(SUM(l.debit), 0) AS "Total Deductions",
                        (COALESCE(SUM(l.credit), 0) - COALESCE(SUM(l.debit), 0)) AS "Net Salary"
                    FROM employees e
                    LEFT JOIN employee_ledger l ON e.id = l.employee_id
                        AND l.entry_date BETWEEN '{first_day}' AND '{last_day}'
                    GROUP BY e.id, e.name, e.designation, e.department, e.salary
                    ORDER BY e.name
                    """
                    report_df = pd.read_sql_query(query, conn)
                    
                    if not report_df.empty:
                        st.dataframe(report_df, use_container_width=True)
                        pdf_bytes = generate_pdf_report(
                            report_df,
                            f"Salary Sheet - {report_month.strftime('%B %Y')}",
                            date_range=(first_day, last_day),
                            orientation='L',
                            totals_cols=["Base Salary", "Total Credits", "Total Deductions", "Net Salary"]
                        )
                        st.download_button(
                            label="📥 Download Salary Sheet",
                            data=pdf_bytes,
                            file_name=f"Salary_Sheet_{report_month.strftime('%Y_%m')}.pdf",
                            mime="application/pdf"
                        )
                
                elif report_type == "Employee Master List":
                    report_df = employees_df[['name', 'designation', 'department', 'salary', 'bank', 'account_title', 'account_no', 'join_date']]
                    st.dataframe(report_df, use_container_width=True)
                    pdf_bytes = generate_pdf_report(
                        report_df,
                        "Employee Master List",
                        orientation='L'
                    )
                    st.download_button(
                        label="📥 Download Employee List",
                        data=pdf_bytes,
                        file_name="Employee_Master_List.pdf",
                        mime="application/pdf"
                    )
    
    with tab2:
        st.subheader("Company Expense Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="report_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="report_end")
        
        report_type = st.selectbox(
            "Expense Report Type",
            ["Detailed Expense Report", "Category Summary", "Payment Method Summary"]
        )
        
        if st.button("Generate Expense Report"):
            conn = get_db_connection()
            
            if report_type == "Detailed Expense Report":
                query = """
                SELECT ce.expense_date as "Date", ce.description as "Description", 
                       ec.name as "Category", ce.amount as "Amount", 
                       ce.payment_method as "Payment Method", ce.reference_no as "Reference"
                FROM company_expenses ce
                JOIN expense_categories ec ON ce.category_id = ec.id
                WHERE ce.expense_date BETWEEN ? AND ?
                ORDER BY ce.expense_date DESC
                """
                report_df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
            elif report_type == "Category Summary":
                query = """
                SELECT ec.name as "Category", SUM(ce.amount) as "Total Amount"
                FROM company_expenses ce
                JOIN expense_categories ec ON ce.category_id = ec.id
                WHERE ce.expense_date BETWEEN ? AND ?
                GROUP BY ec.name
                ORDER BY SUM(ce.amount) DESC
                """
                report_df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
            elif report_type == "Payment Method Summary":
                query = """
                SELECT payment_method as "Payment Method", SUM(amount) as "Total Amount"
                FROM company_expenses
                WHERE expense_date BETWEEN ? AND ?
                GROUP BY payment_method
                ORDER BY SUM(amount) DESC
                """
                report_df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
            
            if not report_df.empty:
                st.dataframe(report_df, use_container_width=True)
                
                pdf_bytes = generate_pdf_report(
                    report_df,
                    f"{report_type} - {start_date} to {end_date}",
                    date_range=(start_date, end_date),
                    totals_cols=['Amount'] if 'Amount' in report_df.columns else ['Total Amount']
                )
                st.download_button(
                    label="📥 Download Report",
                    data=pdf_bytes,
                    file_name=f"{report_type.replace(' ', '_')}_{start_date}_{end_date}.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("No data found for the selected criteria.")
    
    with tab3:
        st.subheader("Analytics Dashboard")
        
        # Employee analytics
        employees_df = get_all_employees()
        if not employees_df.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                # Department distribution
                if 'department' in employees_df.columns:
                    dept_data = employees_df['department'].value_counts().reset_index()
                    dept_data.columns = ['Department', 'Count']
                    fig1 = px.bar(dept_data, x='Department', y='Count', title="Employees by Department")
                    st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                # Salary distribution
                fig2 = px.box(employees_df, y='salary', title="Salary Distribution")
                st.plotly_chart(fig2, use_container_width=True)
        
        # Expense analytics
        conn = get_db_connection()
        expense_trend = pd.read_sql_query("""
            SELECT strftime('%Y-%m', expense_date) as month, SUM(amount) as total
            FROM company_expenses
            GROUP BY month
            ORDER BY month
            LIMIT 12
        """, conn)
        
        if not expense_trend.empty:
            fig3 = px.line(expense_trend, x='month', y='total', 
                          title="Monthly Expense Trend (Last 12 Months)")
            st.plotly_chart(fig3, use_container_width=True)
    
    with tab4:
        st.subheader("Data Export")
        
        st.info("Export your data for external analysis or backup purposes.")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Export Employees"):
                employees_df = get_all_employees()
                csv = employees_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="employees_export.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📥 Export Expenses"):
                conn = get_db_connection()
                expenses_df = pd.read_sql_query("""
                    SELECT ce.*, ec.name as category_name, e.name as employee_name
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    LEFT JOIN employees e ON ce.employee_id = e.id
                """, conn)
                csv = expenses_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="expenses_export.csv",
                    mime="text/csv"
                )
        
        with col3:
            if st.button("📥 Export Ledger"):
                conn = get_db_connection()
                ledger_df = pd.read_sql_query("""
                    SELECT el.*, e.name as employee_name
                    FROM employee_ledger el
                    JOIN employees e ON el.employee_id = e.id
                """, conn)
                csv = ledger_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="ledger_export.csv",
                    mime="text/csv"
                )

# --- Data Import Page ---
def page_data_import():
    st.title("📤 Data Import")
    
    st.info("""
    **Import Data Instructions:**
    - Download the template for the data you want to import
    - Fill in the data following the template format
    - Upload the filled template to import data
    - Do not modify the column names in the template
    """)
    
    tab1, tab2, tab3 = st.tabs(["👥 Import Employees", "💼 Import Expenses", "📋 Import Ledger"])
    
    with tab1:
        st.subheader("Import Employees")
        
        # Download template
        employee_template_cols = ['name', 'designation', 'salary', 'bank', 'account_title', 'account_no', 'join_date', 'department', 'phone', 'email']
        template_output, template_name = generate_excel_template(employee_template_cols, "employee_import_template.xlsx")
        
        st.download_button(
            label="📋 Download Employee Template",
            data=template_output,
            file_name=template_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        # Upload and import
        uploaded_file = st.file_uploader("Choose employee import file", type=['xlsx', 'xls'], key="employee_import")
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of data to import:")
                st.dataframe(df.head())
                
                if st.button("Import Employees", key="import_employees"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    imported_count = 0
                    error_count = 0
                    
                    for _, row in df.iterrows():
                        try:
                            # Handle date conversion
                            join_date = row.get('join_date')
                            if pd.isna(join_date):
                                join_date = date.today()
                            elif isinstance(join_date, str):
                                join_date = datetime.strptime(join_date, '%Y-%m-%d').date()
                            else:
                                join_date = join_date.date() if hasattr(join_date, 'date') else date.today()
                            
                            cursor.execute(
                                """
                                INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date, department, phone, email)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    row['name'],
                                    row.get('designation', ''),
                                    float(row.get('salary', 0)),
                                    row.get('bank', ''),
                                    row.get('account_title', ''),
                                    row.get('account_no', ''),
                                    str(join_date),
                                    row.get('department', ''),
                                    row.get('phone', ''),
                                    row.get('email', '')
                                )
                            )
                            imported_count += 1
                        except Exception as e:
                            error_count += 1
                            st.error(f"Error importing row {_ + 2}: {e}")
                    
                    conn.commit()
                    st.success(f"✅ Successfully imported {imported_count} employees.")
                    if error_count > 0:
                        st.warning(f"⚠️ {error_count} records failed to import.")
                    
                    clear_cache()
                    
            except Exception as e:
                st.error(f"Error reading file: {e}")
    
    with tab2:
        st.subheader("Import Company Expenses")
        
        # Download template
        expense_template_cols = ['description', 'amount', 'expense_date', 'category_name', 'payment_method', 'reference_no']
        template_output, template_name = generate_excel_template(expense_template_cols, "expense_import_template.xlsx")
        
        st.download_button(
            label="📋 Download Expense Template",
            data=template_output,
            file_name=template_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.info("**Note:** For category_name, use existing category names from the system.")
        
        # Upload and import
        uploaded_file = st.file_uploader("Choose expense import file", type=['xlsx', 'xls'], key="expense_import")
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of data to import:")
                st.dataframe(df.head())
                
                if st.button("Import Expenses", key="import_expenses"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    imported_count = 0
                    error_count = 0
                    
                    for _, row in df.iterrows():
                        try:
                            # Get category ID
                            category_name = row.get('category_name', '')
                            cursor.execute("SELECT id FROM expense_categories WHERE name = ?", (category_name,))
                            category_result = cursor.fetchone()
                            
                            if category_result:
                                category_id = category_result[0]
                            else:
                                # Create new category if it doesn't exist
                                cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (category_name,))
                                category_id = cursor.lastrowid
                            
                            # Handle date conversion
                            expense_date = row.get('expense_date')
                            if pd.isna(expense_date):
                                expense_date = date.today()
                            elif isinstance(expense_date, str):
                                expense_date = datetime.strptime(expense_date, '%Y-%m-%d').date()
                            else:
                                expense_date = expense_date.date() if hasattr(expense_date, 'date') else date.today()
                            
                            cursor.execute(
                                """
                                INSERT INTO company_expenses (description, amount, expense_date, category_id, payment_method, reference_no)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (
                                    row['description'],
                                    float(row['amount']),
                                    str(expense_date),
                                    category_id,
                                    row.get('payment_method', 'Cash'),
                                    row.get('reference_no', '')
                                )
                            )
                            imported_count += 1
                        except Exception as e:
                            error_count += 1
                            st.error(f"Error importing row {_ + 2}: {e}")
                    
                    conn.commit()
                    st.success(f"✅ Successfully imported {imported_count} expenses.")
                    if error_count > 0:
                        st.warning(f"⚠️ {error_count} records failed to import.")
                    
                    clear_cache()
                    
            except Exception as e:
                st.error(f"Error reading file: {e}")

# --- Main App ---
def main():
    st.set_page_config(
        page_title=f"{COMPANY_NAME} HR System", 
        layout="wide",
        page_icon="💰",
        initial_sidebar_state="expanded"
    )
    
    # Initialize database
    init_db()
    
    # Initialize session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard"
    
    # Sidebar navigation
    st.sidebar.title(f"{COMPANY_NAME} HR System")
    try:
        st.sidebar.image('logo.png', width=150)
    except:
        pass
    
    # Navigation
    st.sidebar.markdown("### 🎯 Core Functions")
    page_options = [
        "🏠 Dashboard",
        "💰 Employee Expenses", 
        "👥 Employee Management",
        "💼 Company Expenses",
        "📈 Reports",
        "📤 Data Import"
    ]
    
    selected_page = st.sidebar.radio("Navigation", page_options, index=page_options.index(st.session_state.current_page))
    
    # Update current page
    st.session_state.current_page = selected_page
    
    # Footer in sidebar
    st.sidebar.markdown("---")
    st.sidebar.info(DEVELOPER_INFO)
    
    # Render the selected page
    if selected_page == "🏠 Dashboard":
        page_dashboard()
    elif selected_page == "💰 Employee Expenses":
        page_employee_expense_management()
    elif selected_page == "👥 Employee Management":
        page_employee_management()
    elif selected_page == "💼 Company Expenses":
        page_expense_management()
    elif selected_page == "📈 Reports":
        page_reporting()
    elif selected_page == "📤 Data Import":
        page_data_import()

if __name__ == "__main__":
    main()
