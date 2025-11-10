import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
import base64

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion HR Management System"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# --- Enhanced PDF Class with UTF-8 Support ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""
        self.set_auto_page_break(auto=True, margin=40)

    def header(self):
        # Add company logo
        try:
            self.image('logo.png', 10, 8, 25)
        except:
            pass
        
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, self._clean_text(COMPANY_NAME), 0, 1, 'C')
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self._clean_text(self.report_title), 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 7, self._clean_text(self.date_range_str), 0, 1, 'C')
        self.ln(5)

    def footer(self):
        # Position at 3.0 cm from bottom
        self.set_y(-30)
        self.set_font('Arial', '', 10)
        
        footer_width = self.w - self.l_margin - self.r_margin
        
        # Add signature image
        try:
            self.image('', self.l_margin, self.get_y(), 40)
            self.ln(15)
        except:
            # Prepared by section
            self.cell(footer_width / 2, 8, "Prepared by: ___________________", 0, 0, 'L')
            # Approved by section
            self.cell(footer_width / 2, 8, "Approved by: _______________", 0, 1, 'R')
        
        self.ln(5)

        self.set_font('Arial', 'I', 8)
        self.cell(footer_width / 2, 8, f'Page {self.page_no()}/{{nb}}', 0, 0, 'L')
        self.cell(footer_width / 2, 8, DEVELOPER_INFO, 0, 0, 'R')

    def _clean_text(self, text):
        """Clean text to handle encoding issues"""
        if text is None:
            return ""
        text = str(text)
        text = text.replace('�', '')
        text = ''.join(char for char in text if ord(char) >= 32 or ord(char) in [9, 10, 13])
        return text

    def check_page_break(self, height_needed):
        """Check if we need a page break for the given height"""
        if self.get_y() + height_needed > self.page_break_trigger:
            self.add_page()
            return True
        return False

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
            self.cell(col_widths[i], 7, self._clean_text(str(col).replace('_', ' ').title()), 1, 0, 'C', 1)
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
                cell_text = self._clean_text(str(row[col]))
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
            
            # Check if we need a page break before drawing this row
            if self.check_page_break(max_height + 5):
                # Redraw header on new page
                self.set_font('Arial', 'B', 9)
                self.set_fill_color(224, 235, 255)
                x_position = self.get_x()
                for i, col in enumerate(df.columns):
                    self.cell(col_widths[i], 7, self._clean_text(str(col).replace('_', ' ').title()), 1, 0, 'C', 1)
                self.ln()
                self.set_font('Arial', '', 8)
                self.set_fill_color(255)
                fill = False
            
            # Draw each cell
            x_position = self.get_x()
            for i, col in enumerate(df.columns):
                cell_text = self._clean_text(str(row[col]))
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
            # Check if we need a page break before totals
            if self.check_page_break(10):
                # Redraw header on new page
                self.set_font('Arial', 'B', 9)
                self.set_fill_color(224, 235, 255)
                x_position = self.get_x()
                for i, col in enumerate(df.columns):
                    self.cell(col_widths[i], 7, self._clean_text(str(col).replace('_', ' ').title()), 1, 0, 'C', 1)
                self.ln()
            
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
            header_width = len(self._clean_text(str(col).replace('_', ' ').title())) * 2.5
            
            content_samples = df[col].astype(str).apply(self._clean_text).str[:30]
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
        
        text = self._clean_text(text)
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
    
    # Employee details section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 12, pdf._clean_text(f"Employee: {emp_details['name']}"), 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, pdf._clean_text(f"Designation: {emp_details['designation']}"), 0, 1, 'L')
    pdf.cell(0, 8, f"Base Salary: Rs. {emp_details['salary']:,.2f}", 0, 1, 'L')
    pdf.ln(8)

    # Earnings & Deductions table
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
        if pdf.check_page_break(15):
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(desc_width, 8, "Description", 1, 0, 'C')
            pdf.cell(amount_width, 8, "Credits (Rs.)", 1, 0, 'C')
            pdf.cell(amount_width, 8, "Debits (Rs.)", 1, 1, 'C')
            pdf.set_font('Arial', '', 9)
        
        pdf.cell(0, 8, "No ledger activity found for this month.", 1, 1, 'C')
    else:
        for _, row in ledger_df.iterrows():
            desc_text = pdf._clean_text(str(row['description']))
            desc_lines = pdf.wrap_text(desc_text, desc_width - 2)
            
            credit_text = f"{row['credit']:,.2f}" if row['credit'] > 0 else "0.00"
            debit_text = f"{row['debit']:,.2f}" if row['debit'] > 0 else "0.00"
            
            row_height = max(8, len(desc_lines) * 8)
            
            if pdf.check_page_break(row_height + 5):
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(desc_width, 8, "Description", 1, 0, 'C')
                pdf.cell(amount_width, 8, "Credits (Rs.)", 1, 0, 'C')
                pdf.cell(amount_width, 8, "Debits (Rs.)", 1, 1, 'C')
                pdf.set_font('Arial', '', 9)
            
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(desc_width, 8, desc_text, 1, 'L')
            
            pdf.set_xy(x + desc_width, y)
            pdf.cell(amount_width, row_height, credit_text, 1, 0, 'R')
            
            pdf.set_xy(x + desc_width + amount_width, y)
            pdf.cell(amount_width, row_height, debit_text, 1, 1, 'R')

    if pdf.check_page_break(15):
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(desc_width, 8, "Description", 1, 0, 'C')
        pdf.cell(amount_width, 8, "Credits (Rs.)", 1, 0, 'C')
        pdf.cell(amount_width, 8, "Debits (Rs.)", 1, 1, 'C')

    # Totals row
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(desc_width, 8, "Total", 1, 0, 'R')
    pdf.cell(amount_width, 8, f"{total_credits:,.2f}", 1, 0, 'R')
    pdf.cell(amount_width, 8, f"{total_debits:,.2f}", 1, 1, 'R')

    pdf.ln(8)
    
    if pdf.check_page_break(20):
        pdf.ln(5)
    
    # Net Salary section
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(210, 210, 210)
    pdf.cell(desc_width, 12, "Net Salary Payable", 1, 0, 'R', fill=True)
    pdf.cell(amount_width * 2, 12, f"Rs. {net_salary:,.2f}", 1, 1, 'R', fill=True)
    
    pdf.ln(12)
    
    if pdf.check_page_break(25):
        pdf.ln(5)
    
    # Bank details section
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(0, 8, "Bank Details", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 6, pdf._clean_text(f"  Bank: {emp_details['bank']}"), 0, 1, 'L')
    pdf.cell(0, 6, pdf._clean_text(f"  Account Title: {emp_details['account_title']}"), 0, 1, 'L')
    pdf.cell(0, 6, pdf._clean_text(f"  Account No: {emp_details['account_no']}"), 0, 1, 'L')

    try:
        return pdf.output(dest='S').encode('latin-1')
    except UnicodeEncodeError:
        return pdf.output(dest='S').encode('utf-8')

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
    
    if 'entry_type' not in [col[1] for col in c.execute("PRAGMA table_info(employee_ledger)").fetchall()]:
        c.execute("ALTER TABLE employee_ledger ADD COLUMN entry_type TEXT DEFAULT 'REGULAR'")
    
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
            entry_type TEXT DEFAULT 'REGULAR',
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

# --- PDF Generation Function with UTF-8 Support ---
def generate_pdf_report(df, title, date_range=None, orientation='L', totals_cols=None):
    pdf = PDF(orientation=orientation, unit='mm', format='A4')
    pdf.report_title = title
    if date_range:
        pdf.date_range_str = f"{date_range[0].strftime('%d %b %Y')} to {date_range[1].strftime('%d %b %Y')}"
    else:
        pdf.date_range_str = "As of " + date.today().strftime('%d %b %Y')
        
    pdf.set_auto_page_break(auto=True, margin=40)
    pdf.set_left_margin(10)
    pdf.set_right_margin(10)
    pdf.add_page()
    
    if df.empty:
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, "No data found for the selected criteria.", 1, 1, 'C')
    else:
        pdf.add_table(df, totals_cols=totals_cols)
    
    try:
        return pdf.output(dest='S').encode('latin-1')
    except UnicodeEncodeError:
        return pdf.output(dest='S').encode('utf-8')

# --- Enhanced Ledger Summary PDF ---
def generate_ledger_summary_pdf(employee_name, ledger_df, summary_data, date_range=None):
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.report_title = f"Employee Ledger Summary - {employee_name}"
    
    if date_range:
        pdf.date_range_str = f"{date_range[0].strftime('%d %b %Y')} to {date_range[1].strftime('%d %b %Y')}"
    else:
        pdf.date_range_str = "All Time Records"
        
    pdf.add_page()
    
    # Summary Section
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Ledger Summary", 0, 1, 'L')
    pdf.ln(5)
    
    if pdf.check_page_break(50):
        pdf.ln(5)
    
    # Summary table
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(224, 235, 255)
    pdf.cell(0, 8, "Category", 1, 0, 'L', 1)
    pdf.cell(0, 8, "Amount (Rs.)", 1, 1, 'R', 1)
    
    pdf.set_font('Arial', '', 10)
    categories = [
        ("Total Expenses", summary_data['total_expenses']),
        ("Total Advances", summary_data['total_advances']),
        ("Total Salary", summary_data['total_salary']),
        ("Total Payments", summary_data['total_payments']),
        ("Total Credits", summary_data['total_credits']),
        ("Total Debits", summary_data['total_debits'])
    ]
    
    for category, amount in categories:
        if pdf.check_page_break(10):
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(224, 235, 255)
            pdf.cell(0, 8, "Category", 1, 0, 'L', 1)
            pdf.cell(0, 8, "Amount (Rs.)", 1, 1, 'R', 1)
            pdf.set_font('Arial', '', 10)
        
        pdf.cell(0, 8, category, 1, 0, 'L')
        pdf.cell(0, 8, f"{amount:,.2f}", 1, 1, 'R')
    
    if pdf.check_page_break(15):
        pdf.ln(5)
    
    # Remaining Balance (highlighted)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(210, 210, 210)
    balance_text = "Remaining Balance (Payable to Employee)" if summary_data['remaining_balance'] >= 0 else "Remaining Balance (Payable to Company)"
    pdf.cell(0, 10, balance_text, 1, 0, 'L', 1)
    pdf.cell(0, 10, f"Rs. {abs(summary_data['remaining_balance']):,.2f}", 1, 1, 'R', 1)
    
    pdf.ln(10)
    
    # Detailed Ledger
    if not ledger_df.empty:
        if pdf.check_page_break(20):
            pdf.ln(5)
            
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "Detailed Ledger Entries", 0, 1, 'L')
        pdf.ln(5)
        
        display_df = ledger_df[['entry_date', 'description', 'debit', 'credit']].copy()
        display_df.columns = ['Date', 'Description', 'Debit', 'Credit']
        
        display_df['Debit'] = display_df['Debit'].apply(lambda x: f"{x:,.2f}" if x > 0 else "0.00")
        display_df['Credit'] = display_df['Credit'].apply(lambda x: f"{x:,.2f}" if x > 0 else "0.00")
        
        pdf.add_table(display_df)
    
    try:
        return pdf.output(dest='S').encode('latin-1')
    except UnicodeEncodeError:
        return pdf.output(dest='S').encode('utf-8')

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

# --- Data Management Functions ---
def clean_database_text():
    """Clean text data in database to prevent encoding issues"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Clean employees table
        employees = pd.read_sql_query("SELECT * FROM employees", conn)
        for _, emp in employees.iterrows():
            cursor.execute(
                "UPDATE employees SET name=?, designation=?, bank=?, account_title=?, account_no=? WHERE id=?",
                (
                    clean_text(emp['name']),
                    clean_text(emp['designation']),
                    clean_text(emp['bank']),
                    clean_text(emp['account_title']),
                    clean_text(emp['account_no']),
                    emp['id']
                )
            )
        
        # Clean expense categories
        categories = pd.read_sql_query("SELECT * FROM expense_categories", conn)
        for _, cat in categories.iterrows():
            cursor.execute(
                "UPDATE expense_categories SET name=? WHERE id=?",
                (clean_text(cat['name']), cat['id'])
            )
        
        # Clean company expenses
        expenses = pd.read_sql_query("SELECT * FROM company_expenses", conn)
        for _, exp in expenses.iterrows():
            cursor.execute(
                "UPDATE company_expenses SET description=? WHERE id=?",
                (clean_text(exp['description']), exp['id'])
            )
        
        # Clean employee ledger
        ledger = pd.read_sql_query("SELECT * FROM employee_ledger", conn)
        for _, led in ledger.iterrows():
            cursor.execute(
                "UPDATE employee_ledger SET description=? WHERE id=?",
                (clean_text(led['description']), led['id'])
            )
        
        conn.commit()
        st.success("Database text data cleaned successfully!")
        clear_cache()
        
    except Exception as e:
        st.error(f"Error cleaning database: {e}")

def clean_text(text):
    """Clean text to remove problematic characters"""
    if text is None:
        return ""
    text = str(text)
    text = ''.join(char for char in text if ord(char) >= 32 or ord(char) in [9, 10, 13])
    return text

def delete_all_data():
    """Delete all data from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM employee_ledger")
        cursor.execute("DELETE FROM company_expenses")
        cursor.execute("DELETE FROM employees")
        cursor.execute("DELETE FROM expense_categories")
        
        # Reset auto-increment counters
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('employees', 'expense_categories', 'company_expenses', 'employee_ledger')")
        
        # Re-populate default categories
        default_categories = [
            "Guard", "Labour", "Bilty Expenses", "Office Rent", "Warehouse Rent",
            "Import Export", "Office Electricity", "FBR", "Office Entertainment",
            "PSID", "Advance", "Commission", "Office Stationery Expense",
            "Employee Expenses", "Other Expense", "Company Expense", "Salary"
        ]
        
        for category in default_categories:
            cursor.execute("INSERT OR IGNORE INTO expense_categories (name) VALUES (?)", (category,))
        
        conn.commit()
        st.success("All data deleted successfully! Default categories have been restored.")
        clear_cache()
        
    except Exception as e:
        st.error(f"Error deleting data: {e}")

def export_database():
    """Export database as SQL file"""
    try:
        conn = get_db_connection()
        
        # Get all table data
        tables = ['employees', 'expense_categories', 'company_expenses', 'employee_ledger']
        export_data = {}
        
        for table in tables:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            export_data[table] = df
        
        # Create SQL export
        sql_export = ""
        for table, data in export_data.items():
            if not data.empty:
                sql_export += f"-- Data for table: {table}\n"
                for _, row in data.iterrows():
                    columns = ', '.join(data.columns)
                    values = ', '.join([f"'{str(value).replace("'", "''")}'" if isinstance(value, str) else str(value) for value in row])
                    sql_export += f"INSERT INTO {table} ({columns}) VALUES ({values});\n"
                sql_export += "\n"
        
        return sql_export.encode('utf-8'), "database_export.sql"
        
    except Exception as e:
        st.error(f"Error exporting database: {e}")
        return None, None

# --- Enhanced Employee Ledger Functions ---
def add_employee_advance():
    st.subheader("Add Employee Advance")
    
    employees_df = get_all_employees()
    if employees_df.empty:
        st.warning("No employees found. Please add employees first.")
        return
        
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    with st.form("employee_advance_form"):
        cols = st.columns(2)
        with cols[0]:
            employee_id = st.selectbox(
                "Select Employee",
                options=list(employee_list.keys()),
                format_func=lambda x: employee_list[x]
            )
            advance_date = st.date_input("Advance Date", date.today())
        with cols[1]:
            amount = st.number_input("Advance Amount", min_value=0.01, step=100.0)
            description = st.text_input("Description", placeholder="e.g., Salary advance, Emergency advance")
        
        submitted = st.form_submit_button("Add Advance")
        if submitted:
            if employee_id and amount > 0 and description:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        """
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, entry_type)
                        VALUES (?, ?, ?, ?, 0, 'ADVANCE')
                        """,
                        (employee_id, str(advance_date), clean_text(description), amount)
                    )
                    
                    conn.commit()
                    st.success(f"Advance of Rs. {amount:,.2f} added to {employee_list[employee_id]}'s ledger.")
                    clear_cache()
                except sqlite3.Error as e:
                    st.error(f"Database error: {e}")
            else:
                st.error("Please fill in all fields.")

def add_employee_payment():
    st.subheader("Add Employee Payment")
    
    employees_df = get_all_employees()
    if employees_df.empty:
        st.warning("No employees found. Please add employees first.")
        return
        
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    with st.form("employee_payment_form"):
        cols = st.columns(2)
        with cols[0]:
            employee_id = st.selectbox(
                "Select Employee",
                options=list(employee_list.keys()),
                format_func=lambda x: employee_list[x]
            )
            payment_date = st.date_input("Payment Date", date.today())
        with cols[1]:
            amount = st.number_input("Payment Amount", min_value=0.01, step=100.0)
            description = st.text_input("Description", placeholder="e.g., Salary payment, Expense reimbursement")
        
        submitted = st.form_submit_button("Add Payment")
        if submitted:
            if employee_id and amount > 0 and description:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    cursor.execute(
                        """
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, entry_type)
                        VALUES (?, ?, ?, 0, ?, 'PAYMENT')
                        """,
                        (employee_id, str(payment_date), clean_text(description), amount)
                    )
                    
                    conn.commit()
                    st.success(f"Payment of Rs. {amount:,.2f} added to {employee_list[employee_id]}'s ledger.")
                    clear_cache()
                except sqlite3.Error as e:
                    st.error(f"Database error: {e}")
            else:
                st.error("Please fill in all fields.")

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
                    
                    cursor.execute(
                        """
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, entry_type)
                        VALUES (?, ?, ?, ?, 0, 'EXPENSE')
                        """,
                        (employee_id, str(expense_date), clean_text(f"Personal Expense: {description}"), amount)
                    )
                    
                    conn.commit()
                    st.success(f"Personal expense of Rs. {amount:,.2f} added to {employee_list[employee_id]}'s ledger.")
                    clear_cache()
                except sqlite3.Error as e:
                    st.error(f"Database error: {e}")
            else:
                st.error("Please fill in all fields.")

# --- Enhanced Ledger Summary Function ---
def get_employee_ledger_summary(employee_id, start_date=None, end_date=None):
    """Get comprehensive ledger summary for an employee"""
    conn = get_db_connection()
    
    # Check if entry_type column exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(employee_ledger)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'entry_type' not in columns:
        # If entry_type doesn't exist, use description-based categorization
        query = """
            SELECT 
                CASE 
                    WHEN description LIKE 'Advance:%' THEN 'ADVANCE'
                    WHEN description LIKE 'Payment:%' THEN 'PAYMENT' 
                    WHEN description LIKE 'Personal Expense:%' THEN 'EXPENSE'
                    WHEN description LIKE 'Company Expense:%' THEN 'EXPENSE'
                    WHEN description LIKE 'Monthly Salary Credit%' THEN 'SALARY'
                    ELSE 'REGULAR'
                END as entry_type,
                SUM(debit) as total_debit,
                SUM(credit) as total_credit
            FROM employee_ledger 
            WHERE employee_id = ?
        """
    else:
        # Use entry_type column if it exists
        query = """
            SELECT 
                entry_type,
                SUM(debit) as total_debit,
                SUM(credit) as total_credit
            FROM employee_ledger 
            WHERE employee_id = ?
        """
    
    params = [employee_id]
    
    # Add date filter if provided
    if start_date and end_date:
        query += " AND entry_date BETWEEN ? AND ?"
        params.extend([str(start_date), str(end_date)])
    
    query += " GROUP BY entry_type"
    
    summary_df = pd.read_sql_query(query, conn, params=params)
    
    # Calculate totals
    total_expenses = summary_df[summary_df['entry_type'].isin(['EXPENSE', 'REGULAR'])]['total_debit'].sum()
    total_advances = summary_df[summary_df['entry_type'] == 'ADVANCE']['total_debit'].sum()
    total_salary = summary_df[summary_df['entry_type'] == 'SALARY']['total_credit'].sum()
    total_payments = summary_df[summary_df['entry_type'] == 'PAYMENT']['total_credit'].sum()
    
    # Calculate remaining balance
    total_credits = total_salary + total_payments
    total_debits = total_expenses + total_advances
    remaining_balance = total_credits - total_debits
    
    return {
        'total_expenses': total_expenses,
        'total_advances': total_advances,
        'total_salary': total_salary,
        'total_payments': total_payments,
        'total_credits': total_credits,
        'total_debits': total_debits,
        'remaining_balance': remaining_balance
    }

def get_employee_ledger_with_type(employee_id, start_date=None, end_date=None):
    """Get employee ledger with entry_type handling"""
    conn = get_db_connection()
    
    # Check if entry_type column exists
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(employee_ledger)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'entry_type' not in columns:
        # If entry_type doesn't exist, use description-based categorization
        query = """
            SELECT 
                id,
                entry_date AS "Date",
                description AS "Description",
                CASE 
                    WHEN description LIKE 'Advance:%' THEN 'ADVANCE'
                    WHEN description LIKE 'Payment:%' THEN 'PAYMENT' 
                    WHEN description LIKE 'Personal Expense:%' THEN 'EXPENSE'
                    WHEN description LIKE 'Company Expense:%' THEN 'EXPENSE'
                    WHEN description LIKE 'Monthly Salary Credit%' THEN 'SALARY'
                    ELSE 'REGULAR'
                END as "Type",
                credit AS "Credit",
                debit AS "Debit"
            FROM employee_ledger
            WHERE employee_id = ?
        """
    else:
        # Use entry_type column if it exists
        query = """
            SELECT 
                id,
                entry_date AS "Date",
                description AS "Description",
                entry_type AS "Type",
                credit AS "Credit",
                debit AS "Debit"
            FROM employee_ledger
            WHERE employee_id = ?
        """
    
    params = [employee_id]
    
    # Add date filter if provided
    if start_date and end_date:
        query += " AND entry_date BETWEEN ? AND ?"
        params.extend([str(start_date), str(end_date)])
    
    query += " ORDER BY entry_date ASC"
    
    return pd.read_sql_query(query, conn, params=params)

# --- User Settings Page ---
def page_user_settings():
    st.title("⚙️ User Settings & Data Management")
    
    st.warning("""
    **Important:** Use these tools carefully. Data deletion cannot be undone.
    """)
    
    tab1, tab2, tab3 = st.tabs(["Database Maintenance", "Data Export", "Data Deletion"])
    
    with tab1:
        st.subheader("Database Maintenance")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Clean Database Text", help="Clean all text data to fix encoding issues"):
                clean_database_text()
        
        with col2:
            if st.button("🗂️ Rebuild Database", help="Rebuild database structure"):
                try:
                    init_db()
                    st.success("Database rebuilt successfully!")
                except Exception as e:
                    st.error(f"Error rebuilding database: {e}")
        
        st.info("""
        **Database Maintenance Tools:**
        - **Clean Database Text**: Removes problematic characters that cause encoding errors
        - **Rebuild Database**: Recreates database tables with proper structure
        """)
    
    with tab2:
        st.subheader("Data Export")
        
        if st.button("📤 Export Database as SQL", help="Export all data as SQL file"):
            sql_data, filename = export_database()
            if sql_data:
                st.download_button(
                    label="Download SQL Export",
                    data=sql_data,
                    file_name=filename,
                    mime="application/sql"
                )
        
        st.info("""
        **Data Export:**
        - Export all data as SQL file for backup
        - Can be imported into other database systems
        """)
    
    with tab3:
        st.subheader("Data Deletion")
        
        st.error("""
        ⚠️ **Danger Zone** ⚠️
        
        These actions will permanently delete data and cannot be undone.
        """)
        
        # Safety confirmation
        confirmation = st.text_input("Type 'DELETE ALL DATA' to confirm:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete All Data", 
                        disabled=confirmation != "DELETE ALL DATA",
                        help="Permanently delete all data from the system"):
                delete_all_data()
        
        with col2:
            if st.button("🔄 Clear Cache", help="Clear application cache"):
                clear_cache()
                st.success("Cache cleared successfully!")
        
        st.info("""
        **Data Deletion Options:**
        - **Delete All Data**: Permanently removes all employees, expenses, categories, and ledger entries
        - **Clear Cache**: Clears temporary application data (does not delete database records)
        """)

# --- Main App Pages ---
def page_dashboard():
    st.title(f"🏠 Welcome to {COMPANY_NAME}")
    
    # Try to display logo
    try:
        st.image('logo.png', width=200)
    except:
        st.info("💡 *To add your company logo, save an image file named 'logo.png' in the same folder*")
    
    # Quick stats
    try:
        emp_count, exp_total, cat_count = get_dashboard_stats()
        
        st.subheader("📊 Quick Overview (Current Month)")
        cols = st.columns(3)
        with cols[0]:
            st.metric("👥 Total Employees", f"{emp_count}")
        with cols[1]:
            st.metric("💰 Expenses This Month", f"Rs. {exp_total:,.2f}")
        with cols[2]:
            st.metric("📂 Expense Categories", f"{cat_count}")
    
    except Exception as e:
        st.warning(f"Could not load dashboard stats: {e}")
    
    # Quick actions
    st.subheader("🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👤 Add New Employee"):
            st.session_state.page = "Employee Management"
            st.rerun()
    
    with col2:
        if st.button("💰 Log New Expense"):
            st.session_state.page = "Expense Management"
            st.rerun()
    
    with col3:
        if st.button("💳 Process Salaries"):
            st.session_state.page = "Salary Management"
            st.rerun()
    
    # Getting Started Guide
    st.subheader("📋 Getting Started Guide")
    
    with st.expander("🎯 Step-by-Step Setup Instructions"):
        st.markdown("""
        1. **👥 Add Employees** - Start by adding your employees with their basic information
        2. **💰 Set Up Expense Categories** - Manage your expense categories in Expense Management
        3. **📝 Record Expenses** - Log company expenses and assign them to employees if needed
        4. **💸 Track Employee Expenses** - Record personal expenses, advances, and payments
        5. **💳 Process Salaries** - Generate monthly salary credits and slips
        6. **📊 Generate Reports** - Download various reports for accounting
        """)
    
    with st.expander("📚 Understanding the System"):
        st.markdown("""
        **Key Features:**
        - **Employee Management**: Complete employee database with bank details
        - **Expense Tracking**: Both company and employee personal expenses
        - **Salary Processing**: Automated salary calculations with PDF slips
        - **Ledger System**: Individual financial tracking for each employee
        - **Reporting**: Comprehensive PDF reports for all data
        
        **Accounting Flow:**
        - Credits (Salary, Payments) increase employee balance
        - Debits (Expenses, Advances) decrease employee balance
        - Net Salary = Total Credits - Total Debits
        """)

def page_employee_management():
    st.title("👥 Employee Management")
    
    # Add New Employee Section
    with st.expander("➕ Add New Employee", expanded=True):
        with st.form("new_employee_form", clear_on_submit=True):
            st.subheader("Employee Details")
            
            cols = st.columns(2)
            with cols[0]:
                name = st.text_input("Full Name *", placeholder="e.g., Ali Ahmed")
                salary = st.number_input("Monthly Base Salary (Rs.) *", min_value=0.0, step=1000.0, value=30000.0)
                bank = st.text_input("Bank Name", placeholder="e.g., HBL, UBL, MCB")
                join_date = st.date_input("Joining Date", date.today())
            with cols[1]:
                designation = st.text_input("Designation *", placeholder="e.g., Sales Manager, Accountant")
                account_title = st.text_input("Account Title", placeholder="e.g., Ali Ahmed")
                account_no = st.text_input("Account Number", placeholder="e.g., 0123456789")
                
            st.caption("Fields marked with * are required")
            
            submitted = st.form_submit_button("✅ Add Employee")
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
                            (clean_text(name), clean_text(designation), salary, clean_text(bank), 
                             clean_text(account_title), clean_text(account_no), str(join_date))
                        )
                        conn.commit()
                        st.success(f"✅ Employee '{name}' added successfully!")
                        clear_cache()
                    except sqlite3.Error as e:
                        st.error(f"❌ Database error: {e}")

    st.divider()

    # Manage Employees Section
    st.subheader("📋 Manage Existing Employees")
    
    try:
        employees_df = get_all_employees()
        if employees_df.empty:
            st.info("ℹ️ No employees found. Add your first employee using the form above.")
            return

        if 'join_date' in employees_df.columns:
            employees_df['join_date'] = employees_df['join_date'].astype(str)

        st.info("💡 **Editing Instructions:** Click on any cell to edit, press Enter to save changes. Use the + icon to add new rows or the 🗑️ icon to delete.")

        edited_df = st.data_editor(
            employees_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("Full Name", required=True),
                "designation": st.column_config.TextColumn("Designation", required=True),
                "salary": st.column_config.NumberColumn("Monthly Salary (Rs.)", format="%.2f"),
                "join_date": st.column_config.TextColumn("Join Date")
            },
            key="employee_editor"
        )

        if st.button("💾 Save All Changes"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            original_ids = set(employees_df['id'])
            current_ids = set(edited_df['id'].dropna())
            
            # Handle deletions
            deleted_ids = original_ids - current_ids
            if deleted_ids:
                for del_id in deleted_ids:
                    cursor.execute("DELETE FROM employees WHERE id = ?", (int(del_id),))
                st.success(f"✅ Deleted {len(deleted_ids)} employee(s).")

            # Handle updates and insertions
            for _, row in edited_df.iterrows():
                join_date_str = str(row['join_date']) if pd.notna(row['join_date']) else None
                
                if pd.isna(row['id']):
                    # New employee
                    if row['name'] and row['designation']:
                        cursor.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (clean_text(row['name']), clean_text(row['designation']), row['salary'], 
                             clean_text(row['bank']), clean_text(row['account_title']), 
                             clean_text(row['account_no']), join_date_str)
                        )
                else:
                    # Update existing employee
                    cursor.execute(
                        """
                        UPDATE employees SET
                        name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, account_no = ?, join_date = ?
                        WHERE id = ?
                        """,
                        (clean_text(row['name']), clean_text(row['designation']), row['salary'], 
                         clean_text(row['bank']), clean_text(row['account_title']), 
                         clean_text(row['account_no']), join_date_str, int(row['id']))
                    )
            
            conn.commit()
            st.success("✅ All changes saved successfully!")
            clear_cache()
            st.rerun()

    except Exception as e:
        st.error(f"❌ Error loading employees: {e}")

def page_expense_management():
    st.title("💰 Expense Management")

    # Log New Expense Section
    with st.expander("➕ Log New Company Expense", expanded=True):
        categories_df = get_all_categories()
        category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
        
        employees_df = get_all_employees()
        employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
        employee_list_with_none = {0: "🏢 General Company Expense (No employee)"}
        employee_list_with_none.update(employee_list)

        if not category_list:
            st.warning("⚠️ No expense categories found. Please add categories in the section below.", icon="⚠️")
            
        with st.form("new_expense_form", clear_on_submit=True):
            cols = st.columns(3)
            with cols[0]:
                expense_date = st.date_input("Expense Date *", date.today())
            with cols[1]:
                amount = st.number_input("Amount (Rs.) *", min_value=0.01, step=100.0, value=1000.0)
            with cols[2]:
                category_id = st.selectbox("Category *", 
                                         options=list(category_list.keys()), 
                                         format_func=lambda x: category_list[x], 
                                         disabled=not category_list)
            
            description = st.text_input("Description *", placeholder="e.g., Office electricity bill for January")
            
            st.info("💡 **Employee Assignment:** If this expense should be deducted from an employee's salary, select their name below.")
            employee_id = st.selectbox("Assign to Employee (Optional)", 
                                     options=list(employee_list_with_none.keys()), 
                                     format_func=lambda x: employee_list_with_none[x])

            st.caption("Fields marked with * are required")
            submitted = st.form_submit_button("✅ Log Expense")
            if submitted:
                if amount > 0 and category_id and description:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (clean_text(description), amount, str(expense_date), category_id, 
                             employee_id if employee_id != 0 else None)
                        )
                        
                        expense_id = cursor.lastrowid
                        
                        if employee_id != 0:
                            ledger_desc = f"Company Expense: {description} (Ref ID: {expense_id})"
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, related_expense_id, entry_type)
                                VALUES (?, ?, ?, ?, 0, ?, 'EXPENSE')
                                """,
                                (employee_id, str(expense_date), clean_text(ledger_desc), amount, expense_id)
                            )
                            st.success(f"✅ Company expense logged and Rs. {amount:,.2f} deducted from {employee_list[employee_id]}'s ledger.")
                        else:
                            st.success("✅ Company expense logged successfully.")
                        
                        conn.commit()
                        clear_cache()
                    except sqlite3.Error as e:
                        st.error(f"❌ Database error: {e}")
                else:
                    st.error("❌ Please fill in all required fields (Amount, Category, and Description).")

    st.divider()
    
    # Manage Categories Section
    st.subheader("📂 Manage Expense Categories")
    
    try:
        categories_df = get_all_categories()
        
        st.info("💡 **Editing Instructions:** Click on any category name to edit, press Enter to save. Use + to add new categories or 🗑️ to delete.")
        
        edited_df = st.data_editor(
            categories_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "name": st.column_config.TextColumn("Category Name", required=True)
            },
            key="category_editor"
        )
        
        if st.button("💾 Save Category Changes"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            original_ids = set(categories_df['id'])
            current_ids = set(edited_df['id'].dropna())
            
            # Handle deletions
            deleted_ids = original_ids - current_ids
            if deleted_ids:
                for del_id in deleted_ids:
                    cursor.execute("DELETE FROM expense_categories WHERE id = ?", (int(del_id),))
                st.success(f"✅ Deleted {len(deleted_ids)} category(s).")

            # Handle updates and insertions
            for _, row in edited_df.iterrows():
                if pd.isna(row['id']):
                    # New category
                    if row['name']:
                        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (clean_text(row['name']),))
                else:
                    # Update existing category
                    cursor.execute("UPDATE expense_categories SET name = ? WHERE id = ?", 
                                 (clean_text(row['name']), int(row['id'])))
            
            conn.commit()
            st.success("✅ Category changes saved successfully!")
            clear_cache()
            st.rerun()

    except Exception as e:
        st.error(f"❌ Error loading categories: {e}")

    st.divider()

    # View and Manage Expenses Section
    st.subheader("📊 View and Manage Expenses")
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
            st.info("ℹ️ No expenses logged yet. Use the form above to add your first expense.")
            return

        # Display expenses in a clean table
        display_df = expenses_df[['id', 'expense_date', 'description', 'amount', 'category', 'employee']]
        display_df.columns = ['ID', 'Date', 'Description', 'Amount', 'Category', 'Employee']
        
        st.dataframe(display_df, use_container_width=True)

        # Expense actions
        st.subheader("🛠️ Expense Actions")
        expense_ids = expenses_df['id'].tolist()
        
        if expense_ids:
            selected_expense_id = st.selectbox(
                "Select Expense to Manage",
                options=expense_ids,
                format_func=lambda x: f"ID: {x} - {expenses_df[expenses_df['id'] == x]['description'].values[0]}",
                index=None
            )

            if selected_expense_id:
                expense_details = expenses_df[expenses_df['id'] == selected_expense_id].iloc[0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"🗑️ Delete Expense ID {selected_expense_id}", type="secondary"):
                        try:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            
                            # Delete related ledger entry first
                            cursor.execute(
                                "DELETE FROM employee_ledger WHERE related_expense_id = ?",
                                (int(selected_expense_id),)
                            )
                            
                            # Delete the expense
                            cursor.execute("DELETE FROM company_expenses WHERE id = ?", (int(selected_expense_id),))
                            conn.commit()
                            st.success(f"✅ Expense ID {selected_expense_id} and its related ledger entry deleted.")
                            clear_cache()
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting expense: {e}")

    except Exception as e:
        st.error(f"❌ Error loading expenses: {e}")

# Continue with the rest of the pages in a similar improved format...
# For brevity, I'll show the pattern for one more page and you can apply the same improvements to others

def page_employee_personal_expenses():
    st.title("💸 Employee Personal Expenses & Advances")
    
    st.info("""
    💡 **Use this page to manage employee financial transactions:**
    - **Personal Expenses**: Employee expenses that will be deducted from salary
    - **Advances**: Employee advances that need to be repaid
    - **Payments**: Salary payments or reimbursements to employees
    """)
    
    tab1, tab2, tab3 = st.tabs(["💰 Personal Expenses", "🏦 Employee Advances", "💳 Employee Payments"])
    
    with tab1:
        add_employee_personal_expense()
    
    with tab2:
        add_employee_advance()
    
    with tab3:
        add_employee_payment()
    
    st.divider()
    
    st.subheader("📋 Recent Financial Transactions")
    try:
        conn = get_db_connection()
        transactions_df = pd.read_sql_query(
            """
            SELECT 
                el.entry_date as "Date",
                e.name as "Employee",
                el.entry_type as "Type",
                el.description as "Description",
                el.debit as "Debit",
                el.credit as "Credit"
            FROM employee_ledger el
            JOIN employees e ON el.employee_id = e.id
            WHERE el.entry_type IN ('EXPENSE', 'ADVANCE', 'PAYMENT')
            ORDER BY el.entry_date DESC
            LIMIT 50
            """, conn
        )
        
        if not transactions_df.empty:
            st.dataframe(transactions_df, use_container_width=True)
        else:
            st.info("ℹ️ No financial transactions recorded yet.")
            
    except Exception as e:
        st.error(f"❌ Error loading transactions: {e}")

def page_salary_management():
    st.title("💳 Salary Management")

    st.info("""
    💡 **Follow these steps to process monthly salaries:**
    1. **Generate Monthly Salary Credits** - Run this first to add base salary as credit
    2. **View & Download Salary Sheet** - Get the complete payroll sheet after deductions
    3. **Generate Individual Salary Slip** - Download detailed PDF slip for each employee
    """)
    
    selected_month = st.date_input("📅 Select Month for Salary Processing", 
                                 date.today().replace(day=1),
                                 help="Select the first day of the month you want to process salaries for")
    
    first_day = selected_month.replace(day=1)
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    st.divider()

    # Step 1: Generate Salary Credits
    st.subheader("1. Generate Monthly Salary Credits")
    
    with st.expander("ℹ️ About Salary Credits"):
        st.markdown("""
        This step adds each employee's base salary as a **credit** to their ledger for the selected month.
        - Only employees with positive base salary will be processed
        - Prevents duplicate salary credits for the same month
        - Must be run before generating salary sheets
        """)
    
    if st.button("🔄 Generate Salary Credits for All Employees", type="primary"):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            employees_df = get_all_employees()
            
            if employees_df.empty:
                st.error("❌ No employees found. Please add employees first.")
                return

            processed_count = 0
            skipped_count = 0
            results = []
            
            with st.spinner(f"🔄 Processing salaries for {selected_month.strftime('%B %Y')}..."):
                for _, emp in employees_df.iterrows():
                    salary = emp['salary']
                    if salary <= 0:
                        skipped_count += 1
                        results.append(f"❌ {emp['name']}: Salary is 0 or negative")
                        continue
                    
                    description = f"Monthly Salary Credit - {selected_month.strftime('%B %Y')}"
                    
                    # Check if salary already generated for this month
                    cursor.execute(
                        """
                        SELECT 1 FROM employee_ledger 
                        WHERE employee_id = ? AND description = ? AND entry_type = 'SALARY'
                        """,
                        (emp['id'], description)
                    )
                    
                    if cursor.fetchone():
                        skipped_count += 1
                        results.append(f"⚠️ {emp['name']}: Salary already generated")
                        continue
                        
                    # Add salary credit
                    cursor.execute(
                        """
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, entry_type)
                        VALUES (?, ?, ?, 0, ?, 'SALARY')
                        """,
                        (emp['id'], str(first_day), description, salary)
                    )
                    processed_count += 1
                    results.append(f"✅ {emp['name']}: Rs. {salary:,.2f} credited")
            
            conn.commit()
            
            # Show results
            st.subheader("📊 Processing Results")
            for result in results:
                if "✅" in result:
                    st.success(result)
                elif "⚠️" in result:
                    st.warning(result)
                else:
                    st.error(result)
            
            st.metric("✅ Processed", processed_count)
            st.metric("⚠️ Skipped", skipped_count)
            
            clear_cache()
        
        except Exception as e:
            st.error(f"❌ Error generating salary credits: {e}")

    st.divider()

    # Step 2: Salary Sheet
    st.subheader("2. View & Download Salary Sheet")
    
    if st.button("📊 Generate Salary Sheet", type="primary"):
        try:
            conn = get_db_connection()
            query = f"""
            SELECT
                e.name AS "Employee Name",
                e.designation AS "Designation",
                e.salary AS "Base Salary",
                COALESCE(SUM(CASE WHEN l.entry_type = 'SALARY' THEN l.credit ELSE 0 END), 0) AS "Salary Credits",
                COALESCE(SUM(CASE WHEN l.entry_type = 'EXPENSE' THEN l.debit ELSE 0 END), 0) AS "Expense Deductions",
                COALESCE(SUM(CASE WHEN l.entry_type = 'ADVANCE' THEN l.debit ELSE 0 END), 0) AS "Advance Deductions",
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
                st.warning("⚠️ No salary data to display. Did you add employees and generate salary credits?")
                return

            # Display the salary sheet
            st.dataframe(salary_df, use_container_width=True)
            
            # Generate and download PDF
            pdf_bytes = generate_pdf_report(
                salary_df, 
                f"Salary Sheet - {selected_month.strftime('%B %Y')}", 
                date_range=(first_day, last_day),
                orientation='L',
                totals_cols=["Base Salary", "Salary Credits", "Expense Deductions", "Advance Deductions", "Total Credits", "Total Deductions", "Net Salary"]
            )
            
            st.download_button(
                label="📥 Download Salary Sheet (PDF)",
                data=pdf_bytes,
                file_name=f"Salary_Sheet_{selected_month.strftime('%Y_%m')}.pdf",
                mime="application/pdf",
                type="primary"
            )
        except Exception as e:
            st.error(f"❌ Error generating salary sheet: {e}")

    st.divider()

    # Step 3: Individual Salary Slips
    st.subheader("3. Generate Individual Salary Slip")
    
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    if not employee_list:
        st.warning("⚠️ No employees found. Please add employees first.", icon="⚠️")
        return
    
    cols = st.columns(2)
    with cols[0]:
        emp_ids = list(employee_list.keys())
        selected_emp_id = st.selectbox(
            "👤 Select Employee", 
            options=emp_ids, 
            format_func=lambda x: employee_list[x],
            key="slip_emp_select"
        )
    with cols[1]:
        slip_month = st.date_input("📅 Salary Month", 
                                 date.today().replace(day=1), 
                                 key="slip_month_picker")

    if st.button("📄 Generate Salary Slip", type="primary"):
        try:
            with get_db_connection() as conn:
                emp_details_df = pd.read_sql_query(
                    "SELECT * FROM employees WHERE id = ?", 
                    conn, 
                    params=(selected_emp_id,)
                )
                if emp_details_df.empty:
                    st.error(f"❌ Employee ID {selected_emp_id} not found.")
                    return
                emp_details = emp_details_df.iloc[0]

            first_day_slip = slip_month.replace(day=1)
            last_day_slip = (first_day_slip.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            with get_db_connection() as conn:
                ledger_df = pd.read_sql_query(
                    """
                    SELECT description, credit, debit, entry_type
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

            # Show summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Credits", f"Rs. {total_credits:,.2f}")
            with col2:
                st.metric("Total Deductions", f"Rs. {total_debits:,.2f}")
            with col3:
                st.metric("Net Salary", f"Rs. {net_salary:,.2f}")

            # Generate PDF
            pdf_bytes = generate_individual_slip_pdf(
                emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary
            )
            
            st.download_button(
                label=f"📥 Download Slip for {emp_details['name']}",
                data=pdf_bytes,
                file_name=f"Salary_Slip_{emp_details['name'].replace(' ', '_')}_{slip_month.strftime('%Y_%m')}.pdf",
                mime="application/pdf",
                type="primary"
            )
            st.success("✅ Salary slip PDF is ready for download!")
        
        except Exception as e:
            st.error(f"❌ Error generating individual slip: {e}")

# Continue with the remaining pages (Employee Ledger, Reporting, Data Import) following the same pattern...

def page_employee_ledger():
    st.title("📋 Employee Ledger Management")

    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    if not employee_list:
        st.error("❌ No employees found. Please add employees first.", icon="⚠️")
        return

    emp_ids = list(employee_list.keys())
    selected_emp_id = st.selectbox(
        "👤 Select Employee", 
        options=emp_ids, 
        format_func=lambda x: employee_list[x]
    )
    
    show_all_time = st.checkbox("📅 Show All-Time Ledger (Disables date filter)", value=True, key="all_time_toggle")

    cols = st.columns(2)
    today = date.today()
    with cols[0]:
        start_date = st.date_input("Start Date", today.replace(day=1), disabled=show_all_time)
    with cols[1]:
        end_date = st.date_input("End Date", today, disabled=show_all_time)

    if selected_emp_id:
        if not show_all_time and start_date > end_date:
            st.error("❌ Start Date cannot be after End Date.")
            return

        try:
            # Get comprehensive ledger summary
            summary_data = get_employee_ledger_summary(
                selected_emp_id, 
                None if show_all_time else start_date, 
                None if show_all_time else end_date
            )
            
            # Display summary metrics
            st.subheader("💰 Ledger Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Expenses", f"Rs. {summary_data['total_expenses']:,.2f}")
            with col2:
                st.metric("Total Advances", f"Rs. {summary_data['total_advances']:,.2f}")
            with col3:
                st.metric("Total Salary", f"Rs. {summary_data['total_salary']:,.2f}")
            with col4:
                st.metric("Total Payments", f"Rs. {summary_data['total_payments']:,.2f}")
            
            # Display remaining balance with appropriate color
            balance_col1, balance_col2 = st.columns([1, 1])
            with balance_col1:
                if summary_data['remaining_balance'] >= 0:
                    st.success(f"**💰 Balance Payable to Employee: Rs. {summary_data['remaining_balance']:,.2f}**")
                else:
                    st.error(f"**💸 Balance Payable to Company: Rs. {abs(summary_data['remaining_balance']):,.2f}**")
            
            with balance_col2:
                st.metric("Net Balance", f"Rs. {summary_data['remaining_balance']:,.2f}")
        
        except Exception as e:
            st.error(f"❌ Error fetching ledger summary: {e}")
        
        st.divider()
        st.subheader(f"📊 Ledger History - {employee_list[selected_emp_id]}")

        try:
            ledger_df = get_employee_ledger_with_type(
                selected_emp_id, 
                None if show_all_time else start_date, 
                None if show_all_time else end_date
            )

            if not ledger_df.empty:
                # Calculate running balance
                ledger_df['Balance'] = (ledger_df['Credit'] - ledger_df['Debit']).cumsum()
                
                # Display without the ID column
                display_df = ledger_df.drop('id', axis=1) if 'id' in ledger_df.columns else ledger_df
                st.dataframe(display_df, use_container_width=True)
                
                # Download buttons
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("📥 Download Ledger Summary (PDF)"):
                        pdf_bytes = generate_ledger_summary_pdf(
                            employee_list[selected_emp_id],
                            ledger_df,
                            summary_data,
                            date_range=None if show_all_time else (start_date, end_date)
                        )
                        
                        st.download_button(
                            label="📥 Download Ledger PDF",
                            data=pdf_bytes,
                            file_name=f"Ledger_Summary_{employee_list[selected_emp_id].replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                
                with col2:
                    if st.button("📥 Download Detailed Ledger (PDF)"):
                        detailed_df = display_df.copy()
                        detailed_df.columns = [col.replace('_', ' ').title() for col in detailed_df.columns]
                        
                        pdf_bytes = generate_pdf_report(
                            detailed_df, 
                            f"Detailed Ledger - {employee_list[selected_emp_id]}", 
                            date_range=None if show_all_time else (start_date, end_date),
                            orientation='L',
                            totals_cols=["Credit", "Debit"]
                        )
                        
                        st.download_button(
                            label="📥 Download Detailed PDF",
                            data=pdf_bytes,
                            file_name=f"Detailed_Ledger_{employee_list[selected_emp_id].replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.info("ℹ️ No ledger entries found for the selected criteria.")

        except Exception as e:
            st.error(f"❌ Error fetching ledger: {e}")

def page_reporting():
    st.title("📈 Download Reports")
    
    st.header("💰 Company Expense Report")
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
        category_list_with_all = {all_cat_id: "📂 ALL CATEGORIES"}
        category_list_with_all.update(category_list)
        
        selected_cat_id = st.selectbox(
            "Filter by Category", 
            options=list(category_list_with_all.keys()), 
            format_func=lambda x: category_list_with_all[x]
        )
    
    if st.button("📊 Generate Expense Report (PDF)", type="primary"):
        if report_start_date > report_end_date:
            st.error("❌ Start Date cannot be after End Date.")
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
                
                if report_df.empty:
                    st.warning("⚠️ No expenses found for the selected criteria.")
                else:
                    pdf_bytes = generate_pdf_report(
                        report_df, 
                        report_title,
                        date_range=(report_start_date, report_end_date),
                        orientation='L',
                        totals_cols=["Amount"]
                    )
                    
                    st.download_button(
                        label="📥 Download Expense Report PDF",
                        data=pdf_bytes,
                        file_name="Expense_Report.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            except Exception as e:
                st.error(f"❌ Error generating expense report: {e}")

    st.divider()

    st.header("📂 Expense Category Sheet")
    st.markdown("Downloads a simple list of all defined expense categories.")
    
    if st.button("📥 Generate Category Sheet (PDF)", type="primary"):
        try:
            cat_df = get_all_categories()
            cat_df = cat_df.rename(columns={"id": "Category ID", "name": "Category Name"})
            
            pdf_bytes = generate_pdf_report(
                cat_df, 
                "Expense Category Sheet",
                orientation='P'
            )
            
            st.download_button(
                label="📥 Download Category Sheet PDF",
                data=pdf_bytes,
                file_name="Expense_Category_Sheet.pdf",
                mime="application/pdf",
                type="primary"
            )
        except Exception as e:
            st.error(f"❌ Error generating category sheet: {e}")

def page_data_import():
    st.title("📤 Data Import")
    st.warning("⚠️ Use this page to import existing data. Please use the exact templates provided.", icon="⚠️")

    tab1, tab2, tab3, tab4 = st.tabs(["👥 Import Employees", "📂 Import Categories", "💰 Import Expenses", "📋 Import Ledger Entries"])

    with tab1:
        st.subheader("1. Download Employee Template")
        cols = ["name", "designation", "salary", "bank", "account_title", "account_no", "join_date"]
        excel_data, file_name = generate_excel_template(cols, "employee_import_template.xlsx")
        st.download_button(
            label="📥 Download Employee Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary"
        )
        
        st.subheader("2. Upload Employee Excel File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="emp_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                # Fix date columns - convert to string
                if 'join_date' in df.columns:
                    df['join_date'] = pd.to_datetime(df['join_date']).dt.strftime('%Y-%m-%d')
                
                st.dataframe(df)
                
                if st.button("✅ Import Employees", type="primary"):
                    conn = get_db_connection()
                    try:
                        with st.spinner("🔄 Importing..."):
                            # Clean text data before import
                            for col in df.columns:
                                if df[col].dtype == 'object':
                                    df[col] = df[col].apply(lambda x: clean_text(str(x)) if pd.notnull(x) else x)
                            
                            df.to_sql("employees", conn, if_exists="append", index=False)
                        st.success(f"✅ Successfully imported {len(df)} employee records.")
                        clear_cache()
                    except Exception as e:
                        st.error(f"❌ Error importing to database: {e}. Check if data is valid.")
            except Exception as e:
                st.error(f"❌ Error reading Excel file: {e}")

    # Similar improvements for other tabs (Categories, Expenses, Ledger)
    # ... [rest of the data import functions with similar UI improvements]

# --- Main App ---
def main():
    st.set_page_config(
        page_title=f"{COMPANY_NAME}", 
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
    .stButton button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_db()

    # Sidebar
    st.sidebar.title(f"🏢 {COMPANY_NAME}")
    try:
        st.sidebar.image('logo.png', width=150)
    except:
        st.sidebar.info("💡 Add your logo as 'logo.png'")
        
    # Navigation
    page_options = {
        "🏠 Dashboard": page_dashboard,
        "👥 Employee Management": page_employee_management,
        "💰 Expense Management": page_expense_management,
        "💸 Employee Personal Expenses": page_employee_personal_expenses,
        "💳 Salary Management": page_salary_management,
        "📋 Employee Ledger": page_employee_ledger,
        "📈 Reporting": page_reporting,
        "📤 Data Import": page_data_import,
        "⚙️ User Settings": page_user_settings,
    }
    
    # Initialize session state for page navigation
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 Dashboard"
    
    # Sidebar navigation
    selected_page = st.sidebar.radio("📱 Navigation", list(page_options.keys()))
    
    # Update session state when selection changes
    if selected_page != st.session_state.page:
        st.session_state.page = selected_page
    
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    # Display selected page
    page_function = page_options[st.session_state.page]
    page_function()

if __name__ == "__main__":
    main()
