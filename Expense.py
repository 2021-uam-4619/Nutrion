import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
import json
import uuid
import tempfile
from PIL import Image
import base64

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# --- PDF Class with Enhanced Header/Footer ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""
        self.logo_path = "logo.png"  # Company logo path

    def header(self):
        # Add company logo
        try:
            if os.path.exists(self.logo_path):
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

# --- Helper Functions ---
@st.cache_data(ttl=60)
def get_all_employees():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
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

def get_employee_balance(employee_id):
    """Get current balance for an employee"""
    conn = get_db_connection()
    balance_df = pd.read_sql_query(
        "SELECT SUM(credit) - SUM(debit) as balance FROM employee_ledger WHERE employee_id = ?",
        conn,
        params=(employee_id,)
    )
    return balance_df['balance'].iloc[0] if not balance_df.empty else 0.0

# --- Enhanced Import/Export System ---
class DataImportExport:
    def __init__(self):
        self.conn = get_db_connection()
    
    def export_employees_to_excel(self):
        """Export all employees to Excel format"""
        employees_df = get_all_employees()
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            employees_df.to_excel(writer, sheet_name='Employees', index=False)
            
            # Add formatting
            workbook = writer.book
            worksheet = writer.sheets['Employees']
            
            # Add header formatting
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            for col_num, value in enumerate(employees_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            worksheet.set_column('A:A', 20)
            worksheet.set_column('B:H', 15)
        
        output.seek(0)
        return output
    
    def export_transactions_to_excel(self, start_date=None, end_date=None):
        """Export transactions to Excel format"""
        query = """
        SELECT e.name as employee_name, el.entry_date, el.description, 
               el.debit, el.credit, el.credit - el.debit as balance
        FROM employee_ledger el
        JOIN employees e ON el.employee_id = e.id
        """
        params = []
        
        if start_date and end_date:
            query += " WHERE el.entry_date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        
        query += " ORDER BY el.entry_date DESC"
        
        transactions_df = pd.read_sql_query(query, self.conn, params=params)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Transactions']
            
            # Format headers
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#FFE699',
                'border': 1
            })
            
            for col_num, value in enumerate(transactions_df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            
            # Set column widths
            worksheet.set_column('A:A', 25)
            worksheet.set_column('B:B', 15)
            worksheet.set_column('C:C', 40)
            worksheet.set_column('D:F', 15)
        
        output.seek(0)
        return output
    
    def import_employees_from_excel(self, uploaded_file):
        """Import employees from Excel file"""
        try:
            df = pd.read_excel(uploaded_file)
            required_columns = ['name', 'designation', 'salary']
            
            # Check if required columns exist
            if not all(col in df.columns for col in required_columns):
                st.error(f"Missing required columns. Required: {required_columns}")
                return False
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    # Handle missing values
                    name = str(row['name']).strip()
                    if not name:
                        error_count += 1
                        continue
                    
                    designation = str(row.get('designation', '')).strip()
                    salary = float(row.get('salary', 0))
                    bank = str(row.get('bank', '')).strip()
                    account_title = str(row.get('account_title', '')).strip()
                    account_no = str(row.get('account_no', '')).strip()
                    join_date = row.get('join_date', date.today())
                    
                    # Convert join_date to string if it's a datetime
                    if hasattr(join_date, 'strftime'):
                        join_date = join_date.strftime('%Y-%m-%d')
                    else:
                        join_date = str(join_date)
                    
                    # Insert into database
                    cursor = self.conn.cursor()
                    cursor.execute('''
                        INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (name, designation, salary, bank, account_title, account_no, join_date))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    st.warning(f"Error importing row {index + 2}: {str(e)}")
            
            self.conn.commit()
            st.success(f"Successfully imported {success_count} employees. Failed: {error_count}")
            clear_cache()
            return True
            
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")
            return False
    
    def import_transactions_from_excel(self, uploaded_file):
        """Import transactions from Excel file"""
        try:
            df = pd.read_excel(uploaded_file)
            required_columns = ['employee_name', 'entry_date', 'description', 'debit', 'credit']
            
            if not all(col in df.columns for col in required_columns):
                st.error(f"Missing required columns. Required: {required_columns}")
                return False
            
            success_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                try:
                    employee_name = str(row['employee_name']).strip()
                    description = str(row['description']).strip()
                    debit = float(row.get('debit', 0))
                    credit = float(row.get('credit', 0))
                    entry_date = row['entry_date']
                    
                    # Convert date to string
                    if hasattr(entry_date, 'strftime'):
                        entry_date = entry_date.strftime('%Y-%m-%d')
                    else:
                        entry_date = str(entry_date)
                    
                    # Get employee ID
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT id FROM employees WHERE name = ?", (employee_name,))
                    result = cursor.fetchone()
                    
                    if not result:
                        st.warning(f"Employee '{employee_name}' not found. Skipping row {index + 2}")
                        error_count += 1
                        continue
                    
                    employee_id = result[0]
                    
                    # Insert transaction
                    cursor.execute('''
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (employee_id, entry_date, description, debit, credit))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    st.warning(f"Error importing row {index + 2}: {str(e)}")
            
            self.conn.commit()
            st.success(f"Successfully imported {success_count} transactions. Failed: {error_count}")
            clear_cache()
            return True
            
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")
            return False

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
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                                    VALUES (?, ?, ?, ?, 0)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount)
                                )
                                message_type = "expense"
                            else:
                                # Credit entry (bonus/other credit)
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                                    VALUES (?, ?, ?, 0, ?)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount)
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
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                                VALUES (?, ?, ?, 0, ?)
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
            
            if st.button("Generate Salary Slip", use_container_width=True):
                try:
                    first_day = slip_month.replace(day=1)
                    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                    
                    # Get employee details
                    conn = get_db_connection()
                    emp_details_df = pd.read_sql_query(
                        "SELECT * FROM employees WHERE id = ?", 
                        conn, 
                        params=(selected_emp_id,)
                    )
                    
                    if emp_details_df.empty:
                        st.error("Employee not found.")
                        return
                    
                    emp_details = emp_details_df.iloc[0].to_dict()
                    
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
                        label=f"📥 Download {emp_details['name']}'s Salary Slip",
                        data=pdf_bytes,
                        file_name=f"Salary_Slip_{employee_name}_{slip_month.strftime('%Y_%m')}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
                except Exception as e:
                    st.error(f"Error generating salary slip: {e}")

# --- Enhanced Employee Management ---
def page_employee_management():
    st.title("👥 Employee Management")
    
    tab1, tab2 = st.tabs(["➕ Add New Employee", "📋 Manage Employees"])
    
    with tab1:
        st.subheader("Add New Employee")
        with st.form("new_employee_form", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                name = st.text_input("Full Name", placeholder="e.g., Ali Ahmed")
                salary = st.number_input("Monthly Base Salary (Rs.)", min_value=0.0, step=1000.0, value=0.0)
                bank = st.text_input("Bank Name", placeholder="e.g., HBL, UBL, MCB")
                join_date = st.date_input("Joining Date", date.today())
            with cols[1]:
                designation = st.text_input("Designation", placeholder="e.g., Sales Manager, Accountant")
                account_title = st.text_input("Account Title", placeholder="e.g., Ali Ahmed")
                account_no = st.text_input("Account Number", placeholder="e.g., 0123456789")
                
            submitted = st.form_submit_button("💾 Add Employee")
            if submitted:
                if not name or not designation:
                    st.error("❌ Name and Designation are required fields.")
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
            display_cols = ['id', 'name', 'designation', 'salary', 'Current Balance', 'Net Payable', 'bank', 'join_date']
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
                    with cols[1]:
                        edit_designation = st.text_input("Designation", value=emp_data['designation'])
                        edit_account_title = st.text_input("Account Title", value=emp_data['account_title'])
                        edit_account_no = st.text_input("Account No", value=emp_data['account_no'])
                    
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
                                name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, account_no = ?
                                WHERE id = ?
                                """,
                                (edit_name, edit_designation, edit_salary, edit_bank, edit_account_title, edit_account_no, selected_emp_id)
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

# --- Enhanced Company Expense Management ---
def page_expense_management():
    st.title("💼 Company Expense Management")
    
    st.info("""
    **Note:** This page is for company expenses that are NOT linked to specific employees.
    For employee-specific expenses and advances, use the **Employee Expense Management** page.
    """)
    
    tab1, tab2, tab3 = st.tabs(["➕ Add Expense", "📋 View Expenses", "📊 Expense Reports"])
    
    with tab1:
        st.subheader("Add Company Expense")
        
        categories_df = get_all_categories()
        employees_df = get_all_employees()
        
        with st.form("add_company_expense"):
            cols = st.columns(2)
            with cols[0]:
                description = st.text_input("Description", placeholder="e.g., Office supplies purchase")
                amount = st.number_input("Amount (Rs.)", min_value=0.01, step=100.0)
                expense_date = st.date_input("Expense Date", date.today())
            with cols[1]:
                category_id = st.selectbox(
                    "Category",
                    options=[row['id'] for row in categories_df.to_dict('records')],
                    format_func=lambda x: categories_df[categories_df['id'] == x]['name'].iloc[0]
                )
                employee_id = st.selectbox(
                    "Related Employee (Optional)",
                    options=[None] + [row['id'] for row in employees_df.to_dict('records')],
                    format_func=lambda x: "None" if x is None else employees_df[employees_df['id'] == x]['name'].iloc[0]
                )
            
            submitted = st.form_submit_button("💾 Add Expense")
            if submitted:
                if description and amount > 0:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (description, amount, str(expense_date), category_id, employee_id)
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
        
        # Filter options
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
                    SELECT 
                        ce.description,
                        ce.amount,
                        ce.expense_date,
                        ec.name as category,
                        e.name as employee_name
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    LEFT JOIN employees e ON ce.employee_id = e.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    ORDER BY ce.expense_date DESC
                    """,
                    conn,
                    params=(str(start_date), str(end_date))
                )
                
                if not expenses_df.empty:
                    st.dataframe(
                        expenses_df.style.format({'amount': 'Rs. {:,.2f}'}),
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
            report_month = st.date_input("Report Month", date.today().replace(day=1), key="exp_report_month")
        with col2:
            report_type = st.selectbox("Report Type", ["Category-wise", "Monthly Summary"])
        
        if st.button("📊 Generate Report"):
            try:
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                conn = get_db_connection()
                
                if report_type == "Category-wise":
                    report_df = pd.read_sql_query(
                        """
                        SELECT 
                            ec.name as Category,
                            COUNT(ce.id) as Count,
                            SUM(ce.amount) as Total_Amount
                        FROM company_expenses ce
                        JOIN expense_categories ec ON ce.category_id = ec.id
                        WHERE ce.expense_date BETWEEN ? AND ?
                        GROUP BY ec.name
                        ORDER BY Total_Amount DESC
                        """,
                        conn,
                        params=(str(first_day), str(last_day))
                    )
                else:
                    report_df = pd.read_sql_query(
                        """
                        SELECT 
                            strftime('%Y-%m', expense_date) as Month,
                            COUNT(id) as Count,
                            SUM(amount) as Total_Amount
                        FROM company_expenses
                        WHERE expense_date BETWEEN ? AND ?
                        GROUP BY strftime('%Y-%m', expense_date)
                        ORDER BY Month
                        """,
                        conn,
                        params=(str(first_day), str(last_day))
                    )
                
                if not report_df.empty:
                    st.dataframe(
                        report_df.style.format({'Total_Amount': 'Rs. {:,.2f}'}),
                        use_container_width=True
                    )
                    
                    # Download PDF
                    pdf_bytes = generate_pdf_report(
                        report_df,
                        f"Expense Report - {report_type}",
                        date_range=(first_day, last_day),
                        totals_cols=["Total_Amount"]
                    )
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"Expense_Report_{report_month.strftime('%Y_%m')}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.info("No data found for the selected period.")
                    
            except Exception as e:
                st.error(f"Error generating report: {e}")

# --- Enhanced Reporting System ---
def page_reporting():
    st.title("📈 Reports & Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Employee Reports", "💼 Company Reports", "📊 Analytics", "📅 Custom Reports"])
    
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
            
            if st.button("Generate Employee Report", key="gen_emp_report"):
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                try:
                    conn = get_db_connection()
                    
                    if report_type == "Salary Sheet":
                        query = """
                        SELECT 
                            e.name AS "Employee Name",
                            e.designation AS "Designation",
                            e.salary AS "Base Salary",
                            COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? THEN l.credit ELSE 0 END), 0) AS "Total Credits",
                            COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? THEN l.debit ELSE 0 END), 0) AS "Total Deductions",
                            (COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? THEN l.credit ELSE 0 END), 0) - 
                             COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? THEN l.debit ELSE 0 END), 0)) AS "Net Salary"
                        FROM employees e
                        LEFT JOIN employee_ledger l ON e.id = l.employee_id
                        GROUP BY e.id, e.name, e.designation, e.salary
                        ORDER BY e.name
                        """
                        params = [str(first_day), str(last_day)] * 4
                        report_df = pd.read_sql_query(query, conn, params=params)
                        
                    elif report_type == "Balance Summary":
                        balance_data = []
                        for _, emp in employees_df.iterrows():
                            balance = get_employee_balance(emp['id'])
                            balance_data.append({
                                'Employee Name': emp['name'],
                                'Designation': emp['designation'],
                                'Base Salary': emp['salary'],
                                'Current Balance': balance,
                                'Net Payable': emp['salary'] + balance
                            })
                        report_df = pd.DataFrame(balance_data)
                    
                    if not report_df.empty:
                        st.dataframe(report_df, use_container_width=True)
                        
                        # Download options
                        pdf_bytes = generate_pdf_report(
                            report_df,
                            f"Employee {report_type} - {report_month.strftime('%B %Y')}",
                            date_range=(first_day, last_day),
                            orientation='L'
                        )
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.download_button(
                                label="📥 Download PDF",
                                data=pdf_bytes,
                                file_name=f"Employee_{report_type}_{report_month.strftime('%Y_%m')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                        with col2:
                            csv = report_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"Employee_{report_type}_{report_month.strftime('%Y_%m')}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
                    
                except Exception as e:
                    st.error(f"Error generating report: {e}")
    
    with tab2:
        st.subheader("Company Expense Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="comp_report_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="comp_report_end")
        
        report_type = st.selectbox("Report Type", ["Detailed", "Summary by Category", "Monthly Trend"])
        
        if st.button("Generate Company Report", key="gen_comp_report"):
            try:
                conn = get_db_connection()
                
                if report_type == "Detailed":
                    query = """
                    SELECT 
                        ce.description,
                        ce.amount,
                        ce.expense_date,
                        ec.name as category,
                        e.name as employee_name
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    LEFT JOIN employees e ON ce.employee_id = e.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    ORDER BY ce.expense_date DESC
                    """
                    report_df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
                elif report_type == "Summary by Category":
                    query = """
                    SELECT 
                        ec.name as Category,
                        COUNT(ce.id) as Count,
                        SUM(ce.amount) as Total_Amount
                    FROM company_expenses ce
                    JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    GROUP BY ec.name
                    ORDER BY Total_Amount DESC
                    """
                    report_df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
                else:  # Monthly Trend
                    query = """
                    SELECT 
                        strftime('%Y-%m', expense_date) as Month,
                        COUNT(id) as Count,
                        SUM(amount) as Total_Amount
                    FROM company_expenses
                    WHERE expense_date BETWEEN ? AND ?
                    GROUP BY strftime('%Y-%m', expense_date)
                    ORDER BY Month
                    """
                    report_df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
                if not report_df.empty:
                    st.dataframe(report_df, use_container_width=True)
                    
                    total_amount = report_df['Total_Amount'].sum() if 'Total_Amount' in report_df.columns else report_df['amount'].sum()
                    st.metric("Total Amount", f"Rs. {total_amount:,.2f}")
                    
                    # Download options
                    pdf_bytes = generate_pdf_report(
                        report_df,
                        f"Company Expense Report - {report_type}",
                        date_range=(start_date, end_date)
                    )
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"Company_Expense_Report_{start_date}_{end_date}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    with col2:
                        csv = report_df.to_csv(index=False)
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"Company_Expense_Report_{start_date}_{end_date}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                else:
                    st.info("No data found for the selected period.")
                    
            except Exception as e:
                st.error(f"Error generating company report: {e}")
    
    with tab3:
        st.subheader("Analytics Dashboard")
        
        # Quick stats
        try:
            emp_count, exp_total, cat_count = get_dashboard_stats()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Employees", emp_count)
            with col2:
                st.metric("Monthly Expenses", f"Rs. {exp_total:,.2f}")
            with col3:
                st.metric("Expense Categories", cat_count)
                
        except Exception as e:
            st.warning(f"Could not load analytics: {e}")
    
    with tab4:
        st.subheader("Custom Reports")
        
        st.info("Create custom reports by selecting specific criteria")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="custom_start")
            include_employees = st.checkbox("Include Employee Data", value=True)
        with col2:
            end_date = st.date_input("End Date", date.today(), key="custom_end")
            include_expenses = st.checkbox("Include Expense Data", value=True)
        
        if st.button("Generate Custom Report"):
            try:
                report_data = []
                
                if include_employees:
                    # Employee data
                    employees_df = get_all_employees()
                    for _, emp in employees_df.iterrows():
                        balance = get_employee_balance(emp['id'])
                        report_data.append({
                            'Type': 'Employee',
                            'Name': emp['name'],
                            'Designation': emp['designation'],
                            'Amount': emp['salary'],
                            'Balance': balance,
                            'Date': emp.get('join_date', 'N/A')
                        })
                
                if include_expenses:
                    # Expense data
                    conn = get_db_connection()
                    expenses_df = pd.read_sql_query(
                        """
                        SELECT 
                            'Expense' as Type,
                            description as Name,
                            '' as Designation,
                            amount as Amount,
                            '' as Balance,
                            expense_date as Date
                        FROM company_expenses
                        WHERE expense_date BETWEEN ? AND ?
                        """,
                        conn,
                        params=(str(start_date), str(end_date))
                    )
                    if not expenses_df.empty:
                        report_data.extend(expenses_df.to_dict('records'))
                
                if report_data:
                    report_df = pd.DataFrame(report_data)
                    st.dataframe(report_df, use_container_width=True)
                    
                    # Download options
                    pdf_bytes = generate_pdf_report(
                        report_df,
                        "Custom Report",
                        date_range=(start_date, end_date)
                    )
                    
                    st.download_button(
                        label="📥 Download Custom Report PDF",
                        data=pdf_bytes,
                        file_name=f"Custom_Report_{start_date}_{end_date}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.info("No data found for the selected criteria.")
                    
            except Exception as e:
                st.error(f"Error generating custom report: {e}")

# --- Enhanced Data Import/Export System ---
def page_data_import():
    st.title("📤 Data Import & Export")
    
    importer = DataImportExport()
    
    tab1, tab2, tab3 = st.tabs(["📥 Import Data", "📤 Export Data", "🔄 Templates"])
    
    with tab1:
        st.subheader("Import Data from Excel")
        
        st.info("""
        **Instructions:**
        - Download the template first
        - Fill in the data according to the template format
        - Upload the filled template to import data
        """)
        
        import_type = st.selectbox("Select Data Type to Import", 
                                 ["Employees", "Transactions"])
        
        uploaded_file = st.file_uploader(f"Upload {import_type} Excel File", 
                                       type=['xlsx', 'xls'],
                                       key=f"upload_{import_type}")
        
        if uploaded_file is not None:
            if st.button(f"Import {import_type}", use_container_width=True):
                with st.spinner(f"Importing {import_type}..."):
                    if import_type == "Employees":
                        success = importer.import_employees_from_excel(uploaded_file)
                    else:
                        success = importer.import_transactions_from_excel(uploaded_file)
                    
                    if success:
                        st.success(f"✅ {import_type} imported successfully!")
                    else:
                        st.error(f"❌ Failed to import {import_type}")
    
    with tab2:
        st.subheader("Export Data to Excel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 👥 Employee Data")
            if st.button("Export Employees to Excel", use_container_width=True):
                excel_data = importer.export_employees_to_excel()
                st.download_button(
                    label="📥 Download Employees Excel",
                    data=excel_data,
                    file_name=f"Employees_Export_{date.today().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("### 💸 Transaction Data")
            col21, col22 = st.columns(2)
            with col21:
                trans_start = st.date_input("Start Date", date.today().replace(day=1), key="export_start")
            with col22:
                trans_end = st.date_input("End Date", date.today(), key="export_end")
            
            if st.button("Export Transactions to Excel", use_container_width=True):
                excel_data = importer.export_transactions_to_excel(trans_start, trans_end)
                st.download_button(
                    label="📥 Download Transactions Excel",
                    data=excel_data,
                    file_name=f"Transactions_Export_{trans_start}_{trans_end}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
    
    with tab3:
        st.subheader("Download Templates")
        
        st.info("Download these templates to ensure proper data formatting for import.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👥 Employee Template")
            # Create employee template
            emp_template_df = pd.DataFrame(columns=[
                'name', 'designation', 'salary', 'bank', 'account_title', 
                'account_no', 'join_date'
            ])
            emp_template_output = io.BytesIO()
            with pd.ExcelWriter(emp_template_output, engine='xlsxwriter') as writer:
                emp_template_df.to_excel(writer, index=False, sheet_name='Employees')
            emp_template_output.seek(0)
            
            st.download_button(
                label="📥 Download Employee Template",
                data=emp_template_output.getvalue(),
                file_name="Employee_Import_Template.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
        
        with col2:
            st.markdown("#### 💸 Transaction Template")
            # Create transaction template
            trans_template_df = pd.DataFrame(columns=[
                'employee_name', 'entry_date', 'description', 'debit', 'credit'
            ])
            trans_template_output = io.BytesIO()
            with pd.ExcelWriter(trans_template_output, engine='xlsxwriter') as writer:
                trans_template_df.to_excel(writer, index=False, sheet_name='Transactions')
            trans_template_output.seek(0)
            
            st.download_button(
                label="📥 Download Transaction Template",
                data=trans_template_output.getvalue(),
                file_name="Transaction_Import_Template.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
        
        st.markdown("---")
        st.markdown("**📝 Template Instructions:**")
        st.markdown("""
        - **Employee Template:** Fill in employee details. 'name' and 'designation' are required.
        - **Transaction Template:** Fill in transaction details. 'employee_name' must match existing employees.
        - **Dates:** Use YYYY-MM-DD format for dates
        - **Amounts:** Use numbers only, no currency symbols
        """)

# --- Enhanced Dashboard ---
def page_dashboard():
    st.title(f"🏠 Welcome to {COMPANY_NAME} HR & Expense Manager")
    
    try:
        st.image('logo.png', width=200)
    except:
        pass
    
    # Quick Stats
    try:
        emp_count, exp_total, cat_count = get_dashboard_stats()
        
        st.subheader("📊 Quick Overview (Current Month)")
        cols = st.columns(4)
        with cols[0]:
            st.metric("Total Employees", f"{emp_count}")
        with cols[1]:
            st.metric("Company Expenses", f"Rs. {exp_total:,.2f}")
        with cols[2]:
            st.metric("Expense Categories", f"{cat_count}")
        with cols[3]:
            # Calculate total salary
            employees_df = get_all_employees()
            total_salary = employees_df['salary'].sum() if not employees_df.empty else 0
            st.metric("Total Monthly Salary", f"Rs. {total_salary:,.2f}")
    
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
            st.info("No employees found")
    
    with col2:
        st.subheader("💼 Recent Expenses")
        try:
            conn = get_db_connection()
            recent_expenses = pd.read_sql_query(
                """
                SELECT description, amount, expense_date 
                FROM company_expenses 
                ORDER BY expense_date DESC 
                LIMIT 5
                """,
                conn
            )
            if not recent_expenses.empty:
                for _, exp in recent_expenses.iterrows():
                    st.write(f"**{exp['description']}** - Rs. {exp['amount']:,.2f} ({exp['expense_date']})")
            else:
                st.info("No expenses recorded")
        except:
            st.info("No expenses recorded")
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    cols = st.columns(4)
    
    with cols[0]:
        if st.button("➕ Add Employee", use_container_width=True):
            st.session_state.current_page = "👥 Employee Management"
            st.rerun()
    
    with cols[1]:
        if st.button("💰 Add Expense", use_container_width=True):
            st.session_state.current_page = "💰 Employee Expense Management"
            st.rerun()
    
    with cols[2]:
        if st.button("📊 Generate Reports", use_container_width=True):
            st.session_state.current_page = "📈 Reports & Analytics"
            st.rerun()
    
    with cols[3]:
        if st.button("📤 Import Data", use_container_width=True):
            st.session_state.current_page = "📤 Data Import & Export"
            st.rerun()
    
    st.info("""
    **📋 Navigation Guide:**
    - **💰 Employee Expenses**: Add expenses, track balances, process salaries
    - **👥 Employee Management**: Add and manage employee records
    - **💼 Company Expenses**: Log company-wide expenses
    - **📈 Reports**: Download various reports
    - **📤 Data Import**: Bulk import data
    """)

# --- Enhanced Settings Page ---
def page_settings():
    st.title("⚙️ System Settings")
    
    tab1, tab2, tab3 = st.tabs(["🏢 Company Settings", "🔧 System Config", "📊 Database Info"])
    
    with tab1:
        st.subheader("Company Information")
        
        with st.form("company_settings"):
            company_name = st.text_input("Company Name", value=COMPANY_NAME)
            developer_info = st.text_area("Developer Information", value=DEVELOPER_INFO)
            
            # Logo upload
            logo_file = st.file_uploader("Upload Company Logo", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("💾 Save Settings"):
                # Save logo if uploaded
                if logo_file is not None:
                    try:
                        with open("logo.png", "wb") as f:
                            f.write(logo_file.getbuffer())
                        st.success("✅ Logo uploaded successfully!")
                    except Exception as e:
                        st.error(f"Error saving logo: {e}")
                
                st.success("✅ Settings saved successfully!")
    
    with tab2:
        st.subheader("System Configuration")
        
        st.info("System configuration options will be implemented here.")
        
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Enable Email Notifications", value=False)
            st.checkbox("Auto-backup Data", value=True)
        with col2:
            st.selectbox("Default Currency", ["PKR - Pakistani Rupee", "USD - US Dollar"])
            st.number_input("Data Retention (Months)", min_value=1, max_value=60, value=24)
    
    with tab3:
        st.subheader("Database Information")
        
        try:
            conn = get_db_connection()
            
            # Table sizes
            tables = ['employees', 'employee_ledger', 'company_expenses', 'expense_categories']
            table_data = []
            
            for table in tables:
                count_df = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn)
                count = count_df['count'].iloc[0]
                table_data.append({'Table': table, 'Records': count})
            
            table_df = pd.DataFrame(table_data)
            st.dataframe(table_df, use_container_width=True)
            
            # Database size
            db_size = os.path.getsize(DB_FILE) / (1024 * 1024)  # Size in MB
            st.metric("Database Size", f"{db_size:.2f} MB")
            
            # Backup option
            if st.button("💾 Create Backup", use_container_width=True):
                backup_name = f"backup_{date.today().strftime('%Y%m%d')}.db"
                import shutil
                shutil.copy2(DB_FILE, backup_name)
                st.success(f"✅ Backup created: {backup_name}")
            
        except Exception as e:
            st.error(f"Error accessing database: {e}")

# --- Enhanced Main App with Improved Navigation ---
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
        st.sidebar.markdown(f"### {COMPANY_NAME}")
        
    # Initialize session state for page navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard"
    
    # Navigation options
    st.sidebar.markdown("### 🎯 Core Functions")
    page_options = {
        "🏠 Dashboard": page_dashboard,
        "💰 Employee Expenses": page_employee_expense_management,
        "👥 Employee Management": page_employee_management,
        "💼 Company Expenses": page_expense_management,
    }
    
    st.sidebar.markdown("### 📊 Reports & Tools")
    page_options.update({
        "📈 Reports & Analytics": page_reporting,
        "📤 Data Import & Export": page_data_import,
        "⚙️ Settings": page_settings,
    })
    
    # Navigation radio buttons
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()), 
                                   index=list(page_options.keys()).index(st.session_state.current_page))
    
    # Update current page
    st.session_state.current_page = selected_page
    
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    # Quick actions in sidebar
    st.sidebar.markdown("### ⚡ Quick Actions")
    if st.sidebar.button("➕ Add New Employee", use_container_width=True):
        st.session_state.current_page = "👥 Employee Management"
        st.rerun()
        
    if st.sidebar.button("💸 Record Expense", use_container_width=True):
        st.session_state.current_page = "💰 Employee Expenses"
        st.rerun()
    
    # Render the selected page
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
