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

# --- Enhanced PDF Class with Header/Footer and Logo ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""
        self.logo_path = self.get_logo_path()

    def get_logo_path(self):
        """Get company logo path"""
        possible_paths = ['logo.png', 'logo.jpg', 'nutrion_logo.png', 'nutrion_logo.jpg']
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None

    def header(self):
        # Add company logo
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.image(self.logo_path, 10, 8, 25)
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
            self.image('', self.l_margin, self.get_y(), 40)
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

# --- Enhanced PDF Generation Functions ---
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
            join_date DATE,
            phone TEXT,
            email TEXT,
            address TEXT,
            cnic TEXT,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            type TEXT DEFAULT 'Company',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            payment_mode TEXT DEFAULT 'Cash',
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
            category TEXT,
            related_expense_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
            FOREIGN KEY (related_expense_id) REFERENCES company_expenses (id) ON DELETE SET NULL
        )
    ''')
    
    # Enhanced settings table
    c.execute('''
        CREATE TABLE IF NOT EXISTS app_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT DEFAULT 'Nutrion',
            company_address TEXT,
            company_phone TEXT,
            company_email TEXT,
            currency TEXT DEFAULT 'PKR',
            logo_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert default settings
    c.execute('''
        INSERT OR IGNORE INTO app_settings (company_name, company_address, company_phone, company_email, currency)
        VALUES (?, ?, ?, ?, ?)
    ''', (COMPANY_NAME, 'Karachi, Pakistan', '+923207429422', 'info@nutrion.com', 'PKR'))
    
    # Enhanced expense categories
    default_categories = [
        ("Guard", "Company"), ("Labour", "Company"), ("Bilty Expenses", "Company"), 
        ("Office Rent", "Company"), ("Warehouse Rent", "Company"), ("Import Export", "Company"),
        ("Office Electricity", "Company"), ("FBR", "Company"), ("Office Entertainment", "Company"),
        ("PSID", "Company"), ("Advance", "Employee"), ("Commission", "Employee"), 
        ("Office Stationery Expense", "Company"), ("Employee Expenses", "Employee"), 
        ("Other Expense", "Company"), ("Company Expense", "Company"), ("Salary", "Employee"),
        ("Travel", "Employee"), ("Medical", "Employee"), ("Bonus", "Employee"), ("Loan", "Employee")
    ]
    
    for category, cat_type in default_categories:
        c.execute("INSERT OR IGNORE INTO expense_categories (name, type) VALUES (?, ?)", (category, cat_type))
    
    # Add employee_id if not exists
    try:
        c.execute("SELECT employee_id FROM employees LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE employees ADD COLUMN employee_id TEXT UNIQUE")
        # Generate employee IDs for existing employees
        c.execute("SELECT id, name FROM employees")
        employees = c.fetchall()
        for emp in employees:
            emp_id = f"NUT{emp[0]:03d}"
            c.execute("UPDATE employees SET employee_id = ? WHERE id = ?", (emp_id, emp[0]))
    
    conn.commit()

# --- Enhanced Helper Functions ---
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
    return pd.read_sql_query("SELECT * FROM expense_categories ORDER BY type, name", conn)

@st.cache_data(ttl=60)
def get_dashboard_stats():
    conn = get_db_connection()
    
    emp_count_df = pd.read_sql_query("SELECT COUNT(id) as count FROM employees WHERE status = 'Active'", conn)
    emp_count = emp_count_df['count'].iloc[0] if not emp_count_df.empty else 0
    
    today = date.today()
    first_day_month = today.replace(day=1)
    last_day_month = (first_day_month.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    # Company expenses for current month
    exp_total_df = pd.read_sql_query(
        "SELECT SUM(amount) as total FROM company_expenses WHERE expense_date BETWEEN ? AND ?",
        conn,
        params=(str(first_day_month), str(last_day_month))
    )
    exp_total = exp_total_df['total'].iloc[0] if not exp_total_df.empty and exp_total_df['total'].iloc[0] else 0.0
    
    # Employee expenses for current month
    emp_exp_total_df = pd.read_sql_query(
        "SELECT SUM(debit) as total FROM employee_ledger WHERE entry_date BETWEEN ? AND ?",
        conn,
        params=(str(first_day_month), str(last_day_month))
    )
    emp_exp_total = emp_exp_total_df['total'].iloc[0] if not emp_exp_total_df.empty and emp_exp_total_df['total'].iloc[0] else 0.0
    
    total_salary_df = pd.read_sql_query("SELECT SUM(salary) as total FROM employees WHERE status = 'Active'", conn)
    total_salary = total_salary_df['total'].iloc[0] if not total_salary_df.empty and total_salary_df['total'].iloc[0] else 0.0
    
    return emp_count, exp_total, emp_exp_total, total_salary

def clear_cache():
    st.cache_data.clear()

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
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT MAX(id) FROM employees")
    max_id = c.fetchone()[0]
    next_id = (max_id or 0) + 1
    return f"NUT{next_id:03d}"

# --- Enhanced Import/Export Functions ---
def import_employees_from_excel(file):
    """Import employees from Excel file"""
    try:
        df = pd.read_excel(file)
        required_cols = ['name', 'designation', 'salary']
        
        if not all(col in df.columns for col in required_cols):
            st.error(f"Excel file must contain columns: {', '.join(required_cols)}")
            return False
        
        conn = get_db_connection()
        c = conn.cursor()
        
        success_count = 0
        for _, row in df.iterrows():
            try:
                employee_id = generate_employee_id()
                c.execute('''
                    INSERT INTO employees (employee_id, name, designation, salary, bank, account_title, account_no, join_date, phone, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    employee_id,
                    row['name'],
                    row.get('designation', ''),
                    float(row['salary']),
                    row.get('bank', ''),
                    row.get('account_title', ''),
                    row.get('account_no', ''),
                    row.get('join_date', date.today().isoformat()),
                    row.get('phone', ''),
                    row.get('email', '')
                ))
                success_count += 1
            except Exception as e:
                st.warning(f"Failed to import employee {row['name']}: {str(e)}")
        
        conn.commit()
        clear_cache()
        st.success(f"Successfully imported {success_count} employees!")
        return True
        
    except Exception as e:
        st.error(f"Error importing file: {str(e)}")
        return False

def export_employees_to_excel():
    """Export employees to Excel format"""
    employees_df = get_all_employees()
    if employees_df.empty:
        st.warning("No employees to export")
        return None
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        employees_df.to_excel(writer, index=False, sheet_name='Employees')
        
        # Add formatting
        workbook = writer.book
        worksheet = writer.sheets['Employees']
        
        # Add header format
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        for col_num, value in enumerate(employees_df.columns.values):
            worksheet.write(0, col_num, value, header_format)
    
    output.seek(0)
    return output

# --- Enhanced Dashboard ---
def page_dashboard():
    st.title(f"🏠 Welcome to {COMPANY_NAME} HR & Expense Manager")
    
    try:
        st.image('logo.png', width=200)
    except:
        pass
    
    try:
        emp_count, company_exp_total, emp_exp_total, total_salary = get_dashboard_stats()
        
        st.subheader("📊 Quick Overview (Current Month)")
        cols = st.columns(4)
        with cols[0]:
            st.metric("Total Employees", f"{emp_count}")
        with cols[1]:
            st.metric("Company Expenses", f"Rs. {company_exp_total:,.2f}")
        with cols[2]:
            st.metric("Employee Expenses", f"Rs. {emp_exp_total:,.2f}")
        with cols[3]:
            st.metric("Total Salary", f"Rs. {total_salary:,.2f}")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        quick_cols = st.columns(4)
        
        with quick_cols[0]:
            if st.button("👥 Add Employee", use_container_width=True):
                st.session_state.current_page = "Employee Management"
                st.session_state.active_tab = "➕ Add New Employee"
                st.rerun()
        
        with quick_cols[1]:
            if st.button("💰 Add Expense", use_container_width=True):
                st.session_state.current_page = "Employee Expenses"
                st.session_state.active_tab = "➕ Add Expense"
                st.rerun()
        
        with quick_cols[2]:
            if st.button("💸 Process Salary", use_container_width=True):
                st.session_state.current_page = "Employee Expenses"
                st.session_state.active_tab = "💸 Salary Processing"
                st.rerun()
        
        with quick_cols[3]:
            if st.button("📊 Generate Reports", use_container_width=True):
                st.session_state.current_page = "Reports & Analytics"
                st.rerun()
        
        # Recent activity
        st.subheader("📈 Recent Activity")
        activity_cols = st.columns(2)
        
        with activity_cols[0]:
            st.markdown("**Recent Employees**")
            employees_df = get_all_employees()
            if not employees_df.empty:
                recent_employees = employees_df.head(5)
                for _, emp in recent_employees.iterrows():
                    st.write(f"• {emp['name']} - {emp['designation']} (Rs. {emp['salary']:,.2f})")
            else:
                st.info("No employees added yet")
        
        with activity_cols[1]:
            st.markdown("**Recent Expenses**")
            conn = get_db_connection()
            recent_expenses = pd.read_sql_query('''
                SELECT 'Company' as type, description, amount, expense_date as date 
                FROM company_expenses 
                UNION ALL
                SELECT 'Employee' as type, description, debit as amount, entry_date as date
                FROM employee_ledger 
                WHERE debit > 0
                ORDER BY date DESC LIMIT 5
            ''', conn)
            
            if not recent_expenses.empty:
                for _, exp in recent_expenses.iterrows():
                    st.write(f"• {exp['type']}: {exp['description']} - Rs. {exp['amount']:,.2f}")
            else:
                st.info("No recent expenses")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# --- Enhanced Employee Management ---
def page_employee_management():
    st.title("👥 Employee Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add New Employee", "📋 Manage Employees", "📤 Import/Export"])
    
    with tab1:
        st.subheader("Add New Employee")
        with st.form("new_employee_form", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                name = st.text_input("Full Name *", placeholder="e.g., Ali Ahmed")
                designation = st.text_input("Designation *", placeholder="e.g., Sales Manager")
                salary = st.number_input("Monthly Base Salary (Rs.) *", min_value=0.0, step=1000.0, value=0.0)
                phone = st.text_input("Phone Number", placeholder="+92-XXX-XXXXXXX")
                email = st.text_input("Email Address", placeholder="employee@company.com")
            with cols[1]:
                bank = st.text_input("Bank Name", placeholder="e.g., HBL, UBL, MCB")
                account_title = st.text_input("Account Title", placeholder="e.g., Ali Ahmed")
                account_no = st.text_input("Account Number", placeholder="e.g., 0123456789")
                join_date = st.date_input("Joining Date", date.today())
                cnic = st.text_input("CNIC", placeholder="XXXXX-XXXXXXX-X")
                
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
                            account_no, join_date, phone, email, cnic)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (employee_id, name, designation, salary, bank, account_title, account_no, 
                             str(join_date), phone, email, cnic)
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
            display_cols = ['employee_id', 'name', 'designation', 'salary', 'Current Balance', 'Net Payable', 'bank', 'join_date']
            display_df = employees_df[display_cols].copy()
            
            st.dataframe(
                display_df.style.format({
                    'salary': 'Rs. {:,.2f}',
                    'Current Balance': 'Rs. {:,.2f}',
                    'Net Payable': 'Rs. {:,.2f}'
                }),
                use_container_width=True,
                height=400
            )

            # Edit/Delete section
            st.subheader("Edit Employee Details")
            employee_names = {row['id']: f"{row['employee_id']} - {row['name']}" for _, row in employees_df.iterrows()}
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
                        edit_designation = st.text_input("Designation *", value=emp_data['designation'])
                        edit_salary = st.number_input("Salary *", value=float(emp_data['salary']), step=1000.0)
                        edit_phone = st.text_input("Phone", value=emp_data.get('phone', ''))
                    with cols[1]:
                        edit_bank = st.text_input("Bank", value=emp_data.get('bank', ''))
                        edit_account_title = st.text_input("Account Title", value=emp_data.get('account_title', ''))
                        edit_account_no = st.text_input("Account No", value=emp_data.get('account_no', ''))
                        edit_email = st.text_input("Email", value=emp_data.get('email', ''))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        update_submitted = st.form_submit_button("💾 Update Employee")
                    with col2:
                        delete_submitted = st.form_submit_button("🗑️ Delete Employee", type="secondary")
                    with col3:
                        deactivate_submitted = st.form_submit_button("🚫 Deactivate Employee")
                    
                    if update_submitted:
                        try:
                            conn = get_db_connection()
                            conn.execute(
                                """
                                UPDATE employees SET
                                name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, 
                                account_no = ?, phone = ?, email = ?
                                WHERE id = ?
                                """,
                                (edit_name, edit_designation, edit_salary, edit_bank, edit_account_title, 
                                 edit_account_no, edit_phone, edit_email, selected_emp_id)
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
                                st.error("❌ Cannot delete employee with existing ledger entries. Please clear ledger first or deactivate instead.")
                            else:
                                conn.execute("DELETE FROM employees WHERE id = ?", (selected_emp_id,))
                                conn.commit()
                                st.success("✅ Employee deleted successfully!")
                                clear_cache()
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting employee: {e}")
                    
                    if deactivate_submitted:
                        try:
                            conn = get_db_connection()
                            conn.execute("UPDATE employees SET status = 'Inactive' WHERE id = ?", (selected_emp_id,))
                            conn.commit()
                            st.success("✅ Employee deactivated successfully!")
                            clear_cache()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deactivating employee: {e}")

        except Exception as e:
            st.error(f"❌ Error loading employees: {e}")

    with tab3:
        st.subheader("📤 Import/Export Employees")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 📥 Import Employees")
            st.info("Upload Excel file with employee data. Required columns: name, designation, salary")
            
            uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
            if uploaded_file is not None:
                if st.button("Import Data"):
                    with st.spinner("Importing employees..."):
                        if import_employees_from_excel(uploaded_file):
                            st.rerun()
        
        with col2:
            st.markdown("### 📤 Export Employees")
            st.info("Download all employees data in Excel format")
            
            if st.button("Export to Excel"):
                excel_file = export_employees_to_excel()
                if excel_file:
                    st.download_button(
                        label="📥 Download Excel File",
                        data=excel_file,
                        file_name=f"nutrion_employees_{date.today()}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

# --- Enhanced Employee Expense Management ---
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
        "💸 Salary Processing", "📄 Salary Slips"
    ])
    
    with tab1:
        st.subheader("Add Employee Expense/Advance")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("No employees found. Please add employees first.")
        else:
            employee_list = {row['id']: f"{row['employee_id']} - {row['name']} - {row['designation']} (Salary: Rs. {row['salary']:,.2f})" 
                           for index, row in employees_df.iterrows()}
            
            with st.form("add_employee_expense"):
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
                    category = st.selectbox("Category", ["Advance", "Travel", "Medical", "Loan", "Bonus", "Other"])
                
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
                    'Employee ID': emp['employee_id'],
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
            employee_list = {row['id']: f"{row['employee_id']} - {row['name']}" for index, row in employees_df.iterrows()}
            
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
                        e.account_no AS "Account No"
                    FROM employees e
                    LEFT JOIN employee_ledger l ON e.id = l.employee_id
                        AND l.entry_date BETWEEN '{first_day}' AND '{last_day}'
                    WHERE e.status = 'Active'
                    GROUP BY e.id, e.employee_id, e.name, e.designation, e.salary, e.bank, e.account_title, e.account_no
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
            employee_list = {row['id']: f"{row['employee_id']} - {row['name']}" for index, row in employees_df.iterrows()}
            
            cols = st.columns(3)
            with cols[0]:
                selected_emp_id = st.selectbox(
                    "Select Employee",
                    options=list(employee_list.keys()),
                    format_func=lambda x: employee_list[x],
                    key="slip_employee"
                )
            with cols[1]:
                slip_month = st.date_input("Salary Month", date.today().replace(day=1), key="slip_month")
            with cols[2]:
                st.write("")  # Spacer
                st.write("")  # Spacer
                generate_slip = st.button("Generate Salary Slip", use_container_width=True)
            
            if generate_slip and selected_emp_id:
                try:
                    first_day = slip_month.replace(day=1)
                    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                    
                    conn = get_db_connection()
                    
                    # Get employee details
                    emp_details_df = pd.read_sql_query(
                        "SELECT * FROM employees WHERE id = ?", 
                        conn, 
                        params=(selected_emp_id,)
                    )
                    
                    if not emp_details_df.empty:
                        emp_details = emp_details_df.iloc[0]
                        
                        # Get ledger entries for the month
                        ledger_df = pd.read_sql_query(
                            """
                            SELECT description, debit, credit 
                            FROM employee_ledger 
                            WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                            ORDER BY entry_date
                            """,
                            conn,
                            params=(selected_emp_id, str(first_day), str(last_day))
                        )
                        
                        total_credits = ledger_df['credit'].sum()
                        total_debits = ledger_df['debit'].sum()
                        net_salary = total_credits - total_debits
                        
                        # Generate PDF
                        pdf_bytes = generate_individual_slip_pdf(
                            emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary
                        )
                        
                        employee_name = emp_details['name'].replace(' ', '_')
                        st.download_button(
                            label="📄 Download Salary Slip",
                            data=pdf_bytes,
                            file_name=f"Salary_Slip_{employee_name}_{slip_month.strftime('%B_%Y')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                        
                        # Show summary
                        st.success(f"Salary slip generated for {emp_details['name']}")
                        st.metric("Net Salary Payable", f"Rs. {net_salary:,.2f}")
                        
                except Exception as e:
                    st.error(f"Error generating salary slip: {e}")

# --- Enhanced Company Expense Management ---
def page_company_expense_management():
    st.title("💼 Company Expense Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Expense", "📋 Expense History", "📊 Expense Analysis"])
    
    with tab1:
        st.subheader("Add Company Expense")
        
        with st.form("company_expense_form"):
            cols = st.columns(2)
            with cols[0]:
                description = st.text_input("Description *", placeholder="e.g., Office supplies purchase")
                amount = st.number_input("Amount (Rs.) *", min_value=0.01, step=100.0)
                expense_date = st.date_input("Expense Date *", date.today())
            with cols[1]:
                categories_df = get_all_categories()
                company_categories = categories_df[categories_df['type'] == 'Company']['name'].tolist()
                category = st.selectbox("Category *", company_categories)
                payment_mode = st.selectbox("Payment Mode", ["Cash", "Bank Transfer", "Cheque", "Card"])
                reference_no = st.text_input("Reference No", placeholder="Optional")
            
            submitted = st.form_submit_button("💾 Add Expense")
            if submitted:
                if description and amount > 0 and category:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        # Get category ID
                        cursor.execute("SELECT id FROM expense_categories WHERE name = ?", (category,))
                        category_result = cursor.fetchone()
                        
                        if category_result:
                            category_id = category_result[0]
                            
                            cursor.execute(
                                """
                                INSERT INTO company_expenses (description, amount, expense_date, category_id, payment_mode, reference_no)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (description, amount, str(expense_date), category_id, payment_mode, reference_no)
                            )
                            
                            conn.commit()
                            st.success(f"Company expense of Rs. {amount:,.2f} added successfully!")
                            clear_cache()
                        else:
                            st.error("Invalid category selected.")
                            
                    except sqlite3.Error as e:
                        st.error(f"Database error: {e}")
                else:
                    st.error("Please fill in all required fields.")
    
    with tab2:
        st.subheader("Company Expense History")
        
        cols = st.columns(3)
        with cols[0]:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="comp_start")
        with cols[1]:
            end_date = st.date_input("End Date", date.today(), key="comp_end")
        with cols[2]:
            st.write("")  # Spacer
            st.write("")  # Spacer
            show_expenses = st.button("Show Expenses", use_container_width=True)
        
        if show_expenses:
            try:
                conn = get_db_connection()
                expenses_df = pd.read_sql_query(
                    """
                    SELECT 
                        ce.description as "Description",
                        ce.amount as "Amount",
                        ce.expense_date as "Date",
                        ec.name as "Category",
                        ce.payment_mode as "Payment Mode",
                        ce.reference_no as "Reference",
                        ce.status as "Status"
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
                        expenses_df.style.format({'Amount': 'Rs. {:,.2f}'}),
                        use_container_width=True
                    )
                    
                    total_expenses = expenses_df['Amount'].sum()
                    st.metric("Total Company Expenses", f"Rs. {total_expenses:,.2f}")
                    
                    # Download option
                    pdf_bytes = generate_pdf_report(
                        expenses_df,
                        "Company Expenses Report",
                        date_range=(start_date, end_date),
                        orientation='L',
                        totals_cols=['Amount']
                    )
                    st.download_button(
                        label="📥 Download Expense Report",
                        data=pdf_bytes,
                        file_name=f"Company_Expenses_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.info("No company expenses found for the selected period.")
                    
            except Exception as e:
                st.error(f"Error loading expenses: {e}")
    
    with tab3:
        st.subheader("Expense Analysis")
        
        try:
            conn = get_db_connection()
            
            # Monthly expense trend
            monthly_expenses = pd.read_sql_query('''
                SELECT 
                    strftime('%Y-%m', expense_date) as month,
                    SUM(amount) as total_amount
                FROM company_expenses 
                WHERE expense_date >= date('now', '-6 months')
                GROUP BY month
                ORDER BY month
            ''', conn)
            
            if not monthly_expenses.empty:
                st.markdown("**Monthly Expense Trend**")
                st.line_chart(monthly_expenses.set_index('month'))
            
            # Expense by category
            category_expenses = pd.read_sql_query('''
                SELECT 
                    ec.name as category,
                    SUM(ce.amount) as total_amount
                FROM company_expenses ce
                JOIN expense_categories ec ON ce.category_id = ec.id
                WHERE ce.expense_date >= date('now', '-3 months')
                GROUP BY ec.name
                ORDER BY total_amount DESC
            ''', conn)
            
            if not category_expenses.empty:
                st.markdown("**Expenses by Category (Last 3 Months)**")
                st.dataframe(
                    category_expenses.style.format({'total_amount': 'Rs. {:,.2f}'}),
                    use_container_width=True
                )
                
        except Exception as e:
            st.error(f"Error loading analysis: {e}")

# --- Enhanced Reports & Analytics ---
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
                    ["Salary Sheet", "Employee Ledger", "Balance Summary", "Attendance Summary"]
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
                            e.employee_id as "Employee ID",
                            e.name AS "Employee Name",
                            e.designation AS "Designation",
                            e.salary AS "Base Salary",
                            COALESCE(SUM(l.credit), 0) AS "Total Credits",
                            COALESCE(SUM(l.debit), 0) AS "Total Deductions",
                            (COALESCE(SUM(l.credit), 0) - COALESCE(SUM(l.debit), 0)) AS "Net Salary"
                        FROM employees e
                        LEFT JOIN employee_ledger l ON e.id = l.employee_id
                            AND l.entry_date BETWEEN '{first_day}' AND '{last_day}'
                        WHERE e.status = 'Active'
                        GROUP BY e.id, e.employee_id, e.name, e.designation, e.salary
                        ORDER BY e.name
                        """
                        
                        df = pd.read_sql_query(query, conn)
                        st.dataframe(df, use_container_width=True)
                        
                        pdf_bytes = generate_pdf_report(
                            df, 
                            f"Salary Sheet - {report_month.strftime('%B %Y')}", 
                            date_range=(first_day, last_day),
                            orientation='L',
                            totals_cols=["Base Salary", "Total Credits", "Total Deductions", "Net Salary"]
                        )
                        
                    elif report_type == "Employee Ledger":
                        # Let user select employee
                        employee_list = {row['id']: f"{row['employee_id']} - {row['name']}" for _, row in employees_df.iterrows()}
                        selected_emp = st.selectbox("Select Employee", options=list(employee_list.keys()), format_func=lambda x: employee_list[x])
                        
                        if selected_emp:
                            query = """
                            SELECT 
                                entry_date as "Date",
                                description as "Description",
                                category as "Category",
                                debit as "Debit",
                                credit as "Credit"
                            FROM employee_ledger 
                            WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                            ORDER BY entry_date
                            """
                            df = pd.read_sql_query(query, conn, params=(selected_emp, str(first_day), str(last_day)))
                            st.dataframe(df, use_container_width=True)
                            
                            emp_name = employees_df[employees_df['id'] == selected_emp]['name'].iloc[0]
                            pdf_bytes = generate_pdf_report(
                                df, 
                                f"Ledger - {emp_name} - {report_month.strftime('%B %Y')}", 
                                date_range=(first_day, last_day),
                                orientation='L',
                                totals_cols=["Debit", "Credit"]
                            )
                    
                    if st.button("Download PDF Report"):
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"{report_type}_{report_month.strftime('%Y_%m')}.pdf",
                            mime="application/pdf"
                        )
                        
                except Exception as e:
                    st.error(f"Error generating report: {e}")
    
    with tab2:
        st.subheader("Company Expense Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="report_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="report_end")
        
        report_type = st.selectbox("Report Type", ["Detailed Expenses", "Category Summary", "Payment Mode Summary"])
        
        if st.button("Generate Company Report"):
            try:
                conn = get_db_connection()
                
                if report_type == "Detailed Expenses":
                    query = """
                    SELECT 
                        ce.description as "Description",
                        ce.amount as "Amount",
                        ce.expense_date as "Date",
                        ec.name as "Category",
                        ce.payment_mode as "Payment Mode",
                        ce.reference_no as "Reference"
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ?
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
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    GROUP BY ec.name
                    ORDER BY "Total Amount" DESC
                    """
                    df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
                elif report_type == "Payment Mode Summary":
                    query = """
                    SELECT 
                        payment_mode as "Payment Mode",
                        COUNT(id) as "Count",
                        SUM(amount) as "Total Amount"
                    FROM company_expenses
                    WHERE expense_date BETWEEN ? AND ?
                    GROUP BY payment_mode
                    ORDER BY "Total Amount" DESC
                    """
                    df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
                if not df.empty:
                    st.dataframe(df, use_container_width=True)
                    
                    pdf_bytes = generate_pdf_report(
                        df, 
                        f"Company {report_type} - {start_date} to {end_date}", 
                        date_range=(start_date, end_date),
                        orientation='L',
                        totals_cols=["Amount", "Total Amount"] if "Amount" in df.columns or "Total Amount" in df.columns else None
                    )
                    
                    st.download_button(
                        label="📥 Download PDF",
                        data=pdf_bytes,
                        file_name=f"Company_{report_type}_{start_date}_{end_date}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.info("No data found for the selected criteria.")
                    
            except Exception as e:
                st.error(f"Error generating report: {e}")
    
    with tab3:
        st.subheader("Business Analytics")
        
        try:
            conn = get_db_connection()
            
            # Overall statistics
            st.markdown("### 📊 Business Overview")
            cols = st.columns(4)
            
            with cols[0]:
                total_employees = len(get_all_employees())
                st.metric("Total Employees", total_employees)
            
            with cols[1]:
                total_salary = get_all_employees()['salary'].sum()
                st.metric("Monthly Salary", f"Rs. {total_salary:,.2f}")
            
            with cols[2]:
                company_expenses = pd.read_sql_query(
                    "SELECT SUM(amount) as total FROM company_expenses WHERE expense_date >= date('now', '-30 days')",
                    conn
                )
                comp_exp = company_expenses['total'].iloc[0] or 0
                st.metric("Monthly Company Expenses", f"Rs. {comp_exp:,.2f}")
            
            with cols[3]:
                emp_expenses = pd.read_sql_query(
                    "SELECT SUM(debit) as total FROM employee_ledger WHERE entry_date >= date('now', '-30 days')",
                    conn
                )
                emp_exp = emp_expenses['total'].iloc[0] or 0
                st.metric("Monthly Employee Expenses", f"Rs. {emp_exp:,.2f}")
            
            # Expense trends
            st.markdown("### 📈 Expense Trends")
            trend_cols = st.columns(2)
            
            with trend_cols[0]:
                monthly_trend = pd.read_sql_query('''
                    SELECT 
                        strftime('%Y-%m', expense_date) as month,
                        SUM(amount) as company_expenses
                    FROM company_expenses 
                    WHERE expense_date >= date('now', '-6 months')
                    GROUP BY month
                    ORDER BY month
                ''', conn)
                
                if not monthly_trend.empty:
                    st.line_chart(monthly_trend.set_index('month'))
            
            with trend_cols[1]:
                category_dist = pd.read_sql_query('''
                    SELECT 
                        ec.name as category,
                        SUM(ce.amount) as amount
                    FROM company_expenses ce
                    JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date >= date('now', '-3 months')
                    GROUP BY ec.name
                    ORDER BY amount DESC
                    LIMIT 10
                ''', conn)
                
                if not category_dist.empty:
                    st.bar_chart(category_dist.set_index('category'))
                    
        except Exception as e:
            st.error(f"Error loading analytics: {e}")
    
    with tab4:
        st.subheader("Data Export")
        
        st.info("Export all data for backup or external analysis")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Export Employees Data"):
                employees_df = get_all_employees()
                if not employees_df.empty:
                    csv = employees_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Employees CSV",
                        data=csv,
                        file_name=f"nutrion_employees_{date.today()}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            if st.button("Export Expense Data"):
                conn = get_db_connection()
                expenses_df = pd.read_sql_query('''
                    SELECT 
                        e.name as employee_name,
                        el.entry_date,
                        el.description,
                        el.category,
                        el.debit,
                        el.credit
                    FROM employee_ledger el
                    LEFT JOIN employees e ON el.employee_id = e.id
                    UNION ALL
                    SELECT 
                        'Company' as employee_name,
                        ce.expense_date as entry_date,
                        ce.description,
                        ec.name as category,
                        ce.amount as debit,
                        0 as credit
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                ''', conn)
                
                if not expenses_df.empty:
                    csv = expenses_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Expenses CSV",
                        data=csv,
                        file_name=f"nutrion_expenses_{date.today()}.csv",
                        mime="text/csv"
                    )
        
        with col3:
            if st.button("Export Salary Data"):
                conn = get_db_connection()
                salary_df = pd.read_sql_query('''
                    SELECT 
                        e.employee_id,
                        e.name,
                        e.designation,
                        e.salary as base_salary,
                        SUM(el.credit) as total_credits,
                        SUM(el.debit) as total_debits,
                        (SUM(el.credit) - SUM(el.debit)) as net_salary
                    FROM employees e
                    LEFT JOIN employee_ledger el ON e.id = el.employee_id
                    WHERE e.status = 'Active'
                    GROUP BY e.id, e.employee_id, e.name, e.designation, e.salary
                ''', conn)
                
                if not salary_df.empty:
                    csv = salary_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Salary CSV",
                        data=csv,
                        file_name=f"nutrion_salary_{date.today()}.csv",
                        mime="text/csv"
                    )

# --- Settings Page ---
def page_settings():
    st.title("⚙️ System Settings")
    
    tab1, tab2 = st.tabs(["Company Settings", "System Maintenance"])
    
    with tab1:
        st.subheader("Company Information")
        
        conn = get_db_connection()
        settings_df = pd.read_sql_query("SELECT * FROM app_settings WHERE id = 1", conn)
        
        if not settings_df.empty:
            settings = settings_df.iloc[0]
        else:
            settings = {
                'company_name': COMPANY_NAME,
                'company_address': '',
                'company_phone': '',
                'company_email': '',
                'currency': 'PKR'
            }
        
        with st.form("company_settings"):
            company_name = st.text_input("Company Name", value=settings['company_name'])
            company_address = st.text_area("Company Address", value=settings.get('company_address', ''))
            company_phone = st.text_input("Phone Number", value=settings.get('company_phone', ''))
            company_email = st.text_input("Email Address", value=settings.get('company_email', ''))
            currency = st.selectbox("Currency", ["PKR", "USD", "EUR", "GBP"], 
                                  index=["PKR", "USD", "EUR", "GBP"].index(settings.get('currency', 'PKR')))
            
            # Logo upload
            uploaded_logo = st.file_uploader("Upload Company Logo", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("💾 Save Settings"):
                try:
                    # Save logo if uploaded
                    logo_path = None
                    if uploaded_logo is not None:
                        # Save the uploaded file
                        logo_path = "company_logo.png"
                        with open(logo_path, "wb") as f:
                            f.write(uploaded_logo.getbuffer())
                    
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE app_settings 
                        SET company_name = ?, company_address = ?, company_phone = ?, company_email = ?, currency = ?, logo_path = ?
                        WHERE id = 1
                    ''', (company_name, company_address, company_phone, company_email, currency, logo_path))
                    conn.commit()
                    
                    st.success("✅ Company settings updated successfully!")
                    clear_cache()
                    
                except Exception as e:
                    st.error(f"Error saving settings: {e}")
    
    with tab2:
        st.subheader("System Maintenance")
        
        st.warning("⚠️ These actions affect the entire system. Proceed with caution.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Clear Cache", use_container_width=True):
                clear_cache()
                st.success("✅ Cache cleared successfully!")
            
            if st.button("📊 Update Statistics", use_container_width=True):
                clear_cache()
                st.success("✅ Statistics updated successfully!")
        
        with col2:
            if st.button("🗑️ Clear All Data", type="secondary", use_container_width=True):
                st.error("🚨 This will delete ALL data! This action cannot be undone.")
                confirm = st.text_input("Type 'DELETE ALL' to confirm")
                if confirm == "DELETE ALL":
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM employees")
                        cursor.execute("DELETE FROM employee_ledger")
                        cursor.execute("DELETE FROM company_expenses")
                        conn.commit()
                        st.success("✅ All data has been cleared!")
                        clear_cache()
                    except Exception as e:
                        st.error(f"Error clearing data: {e}")

# --- Enhanced Main App with improved navigation ---
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
    
    # Initialize database
    init_db()

    # Sidebar navigation
    st.sidebar.title(f"{COMPANY_NAME} HR System")
    try:
        st.sidebar.image('logo.png', width=150)
    except:
        pass
        
    # Navigation options
    st.sidebar.markdown("### 🎯 Core Functions")
    page_options = {
        "🏠 Dashboard": page_dashboard,
        "👥 Employee Management": page_employee_management,
        "💰 Employee Expenses": page_employee_expense_management,
        "💼 Company Expenses": page_company_expense_management,
        "📈 Reports & Analytics": page_reporting,
        "⚙️ Settings": page_settings,
    }
    
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()))
    
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    # Display selected page
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
