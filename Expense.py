import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
import base64
import re

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
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
        # Convert to string and handle special characters
        text = str(text)
        # Replace common problematic characters
        text = text.replace('�', '')
        # Remove any other non-printable characters
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
            max_height = 6  # Minimum row height
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
                            # REMOVED .00 formatting as requested
                            cell_text = f"{float(cell_value):,}"
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
                            # REMOVED .00 formatting as requested
                            cell_text = f"{float(cell_value):,}"
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
                    # REMOVED .00 formatting as requested
                    self.cell(col_widths[i], 7, f"{col_total:,}", 1, 0, 'R', 1)
                else:
                    self.cell(col_widths[i], 7, "", 1, 0, 'C', 1)
            self.ln()

    def calculate_column_widths(self, df, total_width, num_cols):
        """Calculate dynamic column widths based on content"""
        # Minimum widths for better readability
        min_width = 15
        max_width = total_width / 2
        
        # Estimate content width for each column
        col_widths = []
        for col in df.columns:
            # Header width
            header_width = len(self._clean_text(str(col).replace('_', ' ').title())) * 2.5
            
            # Content width estimation
            content_samples = df[col].astype(str).apply(self._clean_text).str[:30]
            max_content_len = content_samples.str.len().max()
            content_width = max_content_len * 1.8
            
            # Use the maximum of header and content width
            col_width = max(header_width, content_width, min_width)
            col_width = min(col_width, max_width)
            col_widths.append(col_width)
        
        # Normalize to fit total width
        total_current_width = sum(col_widths)
        if total_current_width > total_width:
            # Scale down proportionally
            scale_factor = total_width / total_current_width
            col_widths = [max(min_width, w * scale_factor) for w in col_widths]
        else:
            # Distribute extra space
            extra_space = total_width - total_current_width
            if extra_space > 0:
                col_widths = [w + (extra_space / num_cols) for w in col_widths]
        
        return col_widths

    def wrap_text(self, text, max_width):
        """Wrap text to fit within specified width"""
        if not text:
            return ['']
        
        # Clean the text first
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
        
        # If still too long, truncate
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
    
    # Employee details section with better spacing
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 12, pdf._clean_text(f"Employee: {emp_details['name']}"), 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, pdf._clean_text(f"Designation: {emp_details['designation']}"), 0, 1, 'L')
    # REMOVED .00 formatting as requested
    pdf.cell(0, 8, f"Base Salary: Rs. {emp_details['salary']:,}", 0, 1, 'L')
    pdf.ln(8)

    # Earnings & Deductions table with improved layout
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(224, 235, 255)
    pdf.cell(0, 10, "Earnings & Deductions", 1, 1, 'C', fill=True)
    
    # Calculate column widths for better fit
    total_width = pdf.w - 2 * pdf.l_margin
    desc_width = total_width * 0.6
    amount_width = (total_width - desc_width) / 2
    
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(desc_width, 8, "Description", 1, 0, 'C')
    pdf.cell(amount_width, 8, "Credits (Rs.)", 1, 0, 'C')
    pdf.cell(amount_width, 8, "Debits (Rs.)", 1, 1, 'C')

    pdf.set_font('Arial', '', 9)
    if ledger_df.empty:
        # Check page break before adding content
        if pdf.check_page_break(15):
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(desc_width, 8, "Description", 1, 0, 'C')
            pdf.cell(amount_width, 8, "Credits (Rs.)", 1, 0, 'C')
            pdf.cell(amount_width, 8, "Debits (Rs.)", 1, 1, 'C')
            pdf.set_font('Arial', '', 9)
        
        pdf.cell(0, 8, "No ledger activity found for this month.", 1, 1, 'C')
    else:
        for _, row in ledger_df.iterrows():
            # Wrap description text
            desc_text = pdf._clean_text(str(row['description']))
            desc_lines = pdf.wrap_text(desc_text, desc_width - 2)
            
            # REMOVED .00 formatting as requested
            credit_text = f"{row['credit']:,}" if row['credit'] > 0 else "0"
            debit_text = f"{row['debit']:,}" if row['debit'] > 0 else "0"
            
            # Calculate row height based on description lines
            row_height = max(8, len(desc_lines) * 8)
            
            # Check page break before drawing row
            if pdf.check_page_break(row_height + 5):
                # Redraw header on new page
                pdf.set_font('Arial', 'B', 10)
                pdf.cell(desc_width, 8, "Description", 1, 0, 'C')
                pdf.cell(amount_width, 8, "Credits (Rs.)", 1, 0, 'C')
                pdf.cell(amount_width, 8, "Debits (Rs.)", 1, 1, 'C')
                pdf.set_font('Arial', '', 9)
            
            # Draw description (multi-line if needed)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(desc_width, 8, desc_text, 1, 'L')
            
            # Move to credit column position
            pdf.set_xy(x + desc_width, y)
            pdf.cell(amount_width, row_height, credit_text, 1, 0, 'R')
            
            # Move to debit column position
            pdf.set_xy(x + desc_width + amount_width, y)
            pdf.cell(amount_width, row_height, debit_text, 1, 1, 'R')

    # Check page break before totals
    if pdf.check_page_break(15):
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(desc_width, 8, "Description", 1, 0, 'C')
        pdf.cell(amount_width, 8, "Credits (Rs.)", 1, 0, 'C')
        pdf.cell(amount_width, 8, "Debits (Rs.)", 1, 1, 'C')

    # Totals row
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(desc_width, 8, "Total", 1, 0, 'R')
    # REMOVED .00 formatting as requested
    pdf.cell(amount_width, 8, f"{total_credits:,}", 1, 0, 'R')
    pdf.cell(amount_width, 8, f"{total_debits:,}", 1, 1, 'R')

    pdf.ln(8)
    
    # Check page break before net salary section
    if pdf.check_page_break(20):
        pdf.ln(5)
    
    # Net Salary section with highlighted appearance
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(210, 210, 210)
    pdf.cell(desc_width, 12, "Net Salary Payable", 1, 0, 'R', fill=True)
    # REMOVED .00 formatting as requested
    pdf.cell(amount_width * 2, 12, f"Rs. {net_salary:,}", 1, 1, 'R', fill=True)
    
    pdf.ln(12)
    
    # Check page break before bank details
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
        # Fallback to UTF-8 if latin-1 fails
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
    
    # Check and add entry_type column if it doesn't exist
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
def generate_pdf_report(df, title, date_range=None, orientation='P', totals_cols=None):  # Changed to Portrait
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
        # Fallback to UTF-8 encoding
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
    
    # Check page break before summary table
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
        # Check page break before each row
        if pdf.check_page_break(10):
            pdf.set_font('Arial', 'B', 11)
            pdf.set_fill_color(224, 235, 255)
            pdf.cell(0, 8, "Category", 1, 0, 'L', 1)
            pdf.cell(0, 8, "Amount (Rs.)", 1, 1, 'R', 1)
            pdf.set_font('Arial', '', 10)
        
        pdf.cell(0, 8, category, 1, 0, 'L')
        # REMOVED .00 formatting as requested
        pdf.cell(0, 8, f"{amount:,}", 1, 1, 'R')
    
    # Check page break before balance
    if pdf.check_page_break(15):
        pdf.ln(5)
    
    # Remaining Balance (highlighted)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(210, 210, 210)
    balance_text = "Remaining Balance (Payable to Employee)" if summary_data['remaining_balance'] >= 0 else "Remaining Balance (Payable to Company)"
    pdf.cell(0, 10, balance_text, 1, 0, 'L', 1)
    # REMOVED .00 formatting as requested
    pdf.cell(0, 10, f"Rs. {abs(summary_data['remaining_balance']):,}", 1, 1, 'R', 1)
    
    pdf.ln(10)
    
    # Detailed Ledger
    if not ledger_df.empty:
        # Check page break before detailed section
        if pdf.check_page_break(20):
            pdf.ln(5)
            
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "Detailed Ledger Entries", 0, 1, 'L')
        pdf.ln(5)
        
        # Prepare data for table
        display_df = ledger_df[['entry_date', 'description', 'debit', 'credit']].copy()
        display_df.columns = ['Date', 'Description', 'Debit', 'Credit']
        
        # Format amounts - REMOVED .00 formatting as requested
        display_df['Debit'] = display_df['Debit'].apply(lambda x: f"{x:,}" if x > 0 else "0")
        display_df['Credit'] = display_df['Credit'].apply(lambda x: f"{x:,}" if x > 0 else "0")
        
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

# --- Data Validation Functions ---
def validate_employee_data(df):
    """Validate employee data before import"""
    errors = []
    
    # Check required columns
    required_cols = ['name', 'designation', 'salary']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    # Check data types and values
    for idx, row in df.iterrows():
        # Check name
        if pd.isna(row['name']) or str(row['name']).strip() == '':
            errors.append(f"Row {idx+2}: Name is required")
        
        # Check designation
        if pd.isna(row['designation']) or str(row['designation']).strip() == '':
            errors.append(f"Row {idx+2}: Designation is required")
        
        # Check salary
        try:
            salary = float(row['salary'])
            if salary < 0:
                errors.append(f"Row {idx+2}: Salary cannot be negative")
        except (ValueError, TypeError):
            errors.append(f"Row {idx+2}: Invalid salary value")
    
    return len(errors) == 0, errors

def validate_expense_data(df):
    """Validate expense data before import"""
    errors = []
    
    # Check required columns
    required_cols = ['expense_date', 'description', 'amount', 'category_name']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    # Check data types and values
    for idx, row in df.iterrows():
        # Check expense_date
        try:
            pd.to_datetime(row['expense_date'])
        except:
            errors.append(f"Row {idx+2}: Invalid expense date")
        
        # Check description
        if pd.isna(row['description']) or str(row['description']).strip() == '':
            errors.append(f"Row {idx+2}: Description is required")
        
        # Check amount
        try:
            amount = float(row['amount'])
            if amount <= 0:
                errors.append(f"Row {idx+2}: Amount must be positive")
        except (ValueError, TypeError):
            errors.append(f"Row {idx+2}: Invalid amount value")
        
        # Check category_name
        if pd.isna(row['category_name']) or str(row['category_name']).strip() == '':
            errors.append(f"Row {idx+2}: Category name is required")
    
    return len(errors) == 0, errors

def validate_ledger_data(df):
    """Validate ledger data before import"""
    errors = []
    
    # Check required columns
    required_cols = ['employee_name', 'entry_date', 'description', 'debit', 'credit', 'entry_type']
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")
    
    if errors:
        return False, errors
    
    # Check data types and values
    valid_entry_types = ['SALARY', 'EXPENSE', 'ADVANCE', 'PAYMENT', 'REGULAR']
    
    for idx, row in df.iterrows():
        # Check employee_name
        if pd.isna(row['employee_name']) or str(row['employee_name']).strip() == '':
            errors.append(f"Row {idx+2}: Employee name is required")
        
        # Check entry_date
        try:
            pd.to_datetime(row['entry_date'])
        except:
            errors.append(f"Row {idx+2}: Invalid entry date")
        
        # Check description
        if pd.isna(row['description']) or str(row['description']).strip() == '':
            errors.append(f"Row {idx+2}: Description is required")
        
        # Check debit and credit
        try:
            debit = float(row['debit'])
            credit = float(row['credit'])
            if debit < 0 or credit < 0:
                errors.append(f"Row {idx+2}: Debit and credit cannot be negative")
            if debit > 0 and credit > 0:
                errors.append(f"Row {idx+2}: Both debit and credit cannot be positive in same row")
        except (ValueError, TypeError):
            errors.append(f"Row {idx+2}: Invalid debit or credit value")
        
        # Check entry_type
        if row['entry_type'] not in valid_entry_types:
            errors.append(f"Row {idx+2}: Invalid entry type. Must be one of: {', '.join(valid_entry_types)}")
    
    return len(errors) == 0, errors

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
    # Remove problematic characters and non-printable characters
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
    st.title("User Settings & Data Management")
    
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
    st.title(f"Welcome to {COMPANY_NAME} HR & Expense Manager")
    
    try:
        st.image('logo.png', width=200)
    except:
        pass
    
    try:
        emp_count, exp_total, cat_count = get_dashboard_stats()
        
        st.subheader("At-a-Glance (Current Month)")
        cols = st.columns(3)
        with cols[0]:
            st.metric("Total Employees", f"{emp_count}")
        with cols[1]:
            # REMOVED .00 formatting as requested
            st.metric("Expenses (This Month)", f"Rs. {exp_total:,}")
        with cols[2]:
            st.metric("Expense Categories", f"{cat_count}")
    
    except Exception as e:
        st.warning(f"Could not load dashboard stats: {e}")
    
    st.info("""
    Use the navigation menu on the left to manage your company's data:
    - **Dashboard**: This page.
    - **Employee Management**: Add, view, edit, and delete employee records.
    - **Expense Management**: Log company expenses and manage expense categories.
    - **Employee Personal Expenses**: Add personal expenses that will be deducted from employee salary.
    - **Salary Management**: Generate monthly salary sheets and individual pay slips.
    - **Employee Ledger**: View detailed financial ledgers for each employee with comprehensive summary.
    - **Reporting**: Download summary reports for expenses and categories.
    - **Data Import**: Bulk-import existing data using Excel templates.
    - **User Settings**: Database maintenance and data management tools.
    """)

def page_employee_management():
    st.title("Employee Management")
    
    st.subheader("Add New Employee")
    with st.form("new_employee_form", clear_on_submit=True):
        cols = st.columns(2)
        with cols[0]:
            name = st.text_input("Name", placeholder="e.g., Alice Smith")
            salary = st.number_input("Base Salary (Monthly)", min_value=0.0, step=1000.0, format="%.0f")  # Remove decimal places
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
                        (clean_text(name), clean_text(designation), salary, clean_text(bank), clean_text(account_title), clean_text(account_no), str(join_date))
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

        if 'join_date' in employees_df.columns:
            employees_df['join_date'] = employees_df['join_date'].astype(str)

        edited_df = st.data_editor(
            employees_df,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "join_date": st.column_config.TextColumn("Join Date"),
                "salary": st.column_config.NumberColumn("Salary", format="%d")  # Remove decimal places
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
                            (clean_text(row['name']), clean_text(row['designation']), row['salary'], clean_text(row['bank']), clean_text(row['account_title']), clean_text(row['account_no']), join_date_str)
                        )
                else:
                    cursor.execute(
                        """
                        UPDATE employees SET
                        name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, account_no = ?, join_date = ?
                        WHERE id = ?
                        """,
                        (clean_text(row['name']), clean_text(row['designation']), row['salary'], clean_text(row['bank']), clean_text(row['account_title']), clean_text(row['account_no']), join_date_str, int(row['id']))
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
            amount = st.number_input("Amount", min_value=0.01, step=100.0, format="%.0f")  # Remove decimal places
        with cols[2]:
            category_id = st.selectbox("Category", options=list(category_list.keys()), format_func=lambda x: category_list[x], disabled=not category_list)
        
        description = st.text_input("Description", placeholder="e.g., Office electricity bill")
        
        st.info("If this expense is an advance or deduction for an employee, select their name. This amount will be added to their ledger.")
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
                        (clean_text(description), amount, str(expense_date), category_id, employee_id if employee_id != 0 else None)
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
                        st.success(f"Company expense logged and Rs. {amount:,.0f} added to {employee_list[employee_id]}'s ledger.")  # Remove decimal places
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
                        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (clean_text(row['name']),))
                else:
                    cursor.execute("UPDATE expense_categories SET name = ? WHERE id = ?", (clean_text(row['name']), int(row['id'])))
            
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
                    edit_amount = st.number_input("Amount", value=expense_details['amount'], format="%.0f")  # Remove decimal places
                    
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
                                (str(edit_date), edit_amount, clean_text(edit_desc), edit_category_id, expense_to_edit)
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
    st.title("Employee Personal Expenses & Advances")
    
    st.info("""
    Use this page to manage employee financial transactions:
    - **Personal Expenses**: These expenses will be recorded in employee ledger
    - **Advances**: Employee advances that will be tracked separately
    - **Payments**: Direct payments to employees
    """)
    
    tab1, tab2, tab3 = st.tabs(["Personal Expenses", "Employee Advances", "Employee Payments"])
    
    with tab1:
        add_employee_personal_expense()
    
    with tab2:
        add_employee_advance()
    
    with tab3:
        add_employee_payment()
    
    st.divider()
    
    st.subheader("Recent Financial Transactions")
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
            st.info("No financial transactions recorded yet.")
            
    except Exception as e:
        st.error(f"Error loading transactions: {e}")

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
                        WHERE employee_id = ? AND description = ? AND entry_type = 'SALARY'
                        """,
                        (emp['id'], description)
                    )
                    if cursor.fetchone():
                        skipped_count += 1
                        continue
                        
                    cursor.execute(
                        """
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, entry_type)
                        VALUES (?, ?, ?, 0, ?, 'SALARY')
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
                st.warning("No salary data to display. Did you add employees and generate credits?")
                return

            st.dataframe(salary_df)
            
            pdf_bytes = generate_pdf_report(
                salary_df, 
                f"Salary Sheet - {selected_month.strftime('%B %Y')}", 
                date_range=(first_day, last_day),
                orientation='P',  # Changed to Portrait
                totals_cols=["Base Salary", "Salary Credits", "Expense Deductions", "Advance Deductions", "Total Credits", "Total Deductions", "Net Salary"]
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
    
    show_all_time = st.checkbox("Show All-Time Ledger? (Disables date filter)", value=True, key="all_time_toggle")

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
            # Get comprehensive ledger summary
            summary_data = get_employee_ledger_summary(
                selected_emp_id, 
                None if show_all_time else start_date, 
                None if show_all_time else end_date
            )
            
            # Display summary metrics
            st.subheader("Ledger Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                # REMOVED .00 formatting as requested
                st.metric("Total Expenses", f"Rs. {summary_data['total_expenses']:,}")
            with col2:
                st.metric("Total Advances", f"Rs. {summary_data['total_advances']:,}")
            with col3:
                st.metric("Total Salary", f"Rs. {summary_data['total_salary']:,}")
            with col4:
                st.metric("Total Payments", f"Rs. {summary_data['total_payments']:,}")
            
            # Display remaining balance with appropriate color
            balance_col1, balance_col2 = st.columns([1, 1])
            with balance_col1:
                if summary_data['remaining_balance'] >= 0:
                    st.success(f"**Balance Payable to Employee: Rs. {summary_data['remaining_balance']:,}**")
                else:
                    st.error(f"**Balance Payable to Company: Rs. {abs(summary_data['remaining_balance']):,}**")
            
            with balance_col2:
                st.metric("Net Balance", f"Rs. {summary_data['remaining_balance']:,}")
        
        except Exception as e:
            st.error(f"Error fetching ledger summary: {e}")
        
        st.divider()
        st.subheader(f"Ledger History - {employee_list[selected_emp_id]}")

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
                    if st.button("Download Ledger (PDF)"):
                        pdf_bytes = generate_ledger_summary_pdf(
                            employee_list[selected_emp_id],
                            ledger_df,
                            summary_data,
                            date_range=None if show_all_time else (start_date, end_date)
                        )
                        
                        st.download_button(
                            label="Download Ledger PDF",
                            data=pdf_bytes,
                            file_name=f"Ledger_Summary_{employee_list[selected_emp_id].replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                
                with col2:
                    if st.button("Download Detailed Ledger (PDF)"):
                        detailed_df = display_df.copy()
                        detailed_df.columns = [col.replace('_', ' ').title() for col in detailed_df.columns]
                        
                        pdf_bytes = generate_pdf_report(
                            detailed_df, 
                            f"Detailed Ledger - {employee_list[selected_emp_id]}", 
                            date_range=None if show_all_time else (start_date, end_date),
                            orientation='P',  # Changed to Portrait
                            totals_cols=["Credit", "Debit"]
                        )
                        
                        st.download_button(
                            label="Download Detailed PDF",
                            data=pdf_bytes,
                            file_name=f"Detailed_Ledger_{employee_list[selected_emp_id].replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.info("No ledger entries found for the selected criteria.")

        except Exception as e:
            st.error(f"Error fetching ledger: {e}")

        st.divider()
        
        # Delete Ledger Entries Section
        st.subheader("Manage Ledger Entries")
        st.warning("""
        **Warning:** Deleting ledger entries can affect salary calculations and accounting records. 
        Only delete entries that were created by mistake.
        """)
        
        try:
            conn = get_db_connection()
            
            # Get ledger entries with IDs for deletion
            if show_all_time:
                delete_query = """
                    SELECT 
                        id,
                        entry_date AS "Date",
                        description AS "Description",
                        entry_type AS "Type",
                        credit AS "Credit",
                        debit AS "Debit",
                        related_expense_id
                    FROM employee_ledger
                    WHERE employee_id = ?
                    ORDER BY entry_date DESC
                """
                delete_params = (selected_emp_id,)
            else:
                delete_query = """
                    SELECT 
                        id,
                        entry_date AS "Date",
                        description AS "Description",
                        entry_type AS "Type",
                        credit AS "Credit",
                        debit AS "Debit",
                        related_expense_id
                    FROM employee_ledger
                    WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                    ORDER BY entry_date DESC
                """
                delete_params = (selected_emp_id, str(start_date), str(end_date))
            
            delete_df = pd.read_sql_query(delete_query, conn, params=delete_params)
            
            if not delete_df.empty:
                # Create a user-friendly display for selection
                delete_df['Display'] = delete_df.apply(
                    lambda row: f"ID: {row['id']} | {row['Date']} | {row['Type']} | {row['Description']} | Credit: {row['Credit']} | Debit: {row['Debit']}", 
                    axis=1
                )
                
                ledger_entries = delete_df['Display'].tolist()
                ledger_ids = delete_df['id'].tolist()
                related_expense_ids = delete_df['related_expense_id'].tolist()
                
                selected_entry = st.selectbox(
                    "Select Ledger Entry to Delete",
                    options=ledger_entries,
                    key="delete_ledger_select"
                )
                
                if selected_entry:
                    # Find the selected entry details
                    selected_index = ledger_entries.index(selected_entry)
                    selected_id = ledger_ids[selected_index]
                    selected_expense_id = related_expense_ids[selected_index]
                    
                    st.error(f"**Selected Entry:** {selected_entry}")
                    
                    # Show warning if this is linked to a company expense
                    if pd.notna(selected_expense_id):
                        st.warning("""
                        ⚠️ **This ledger entry is linked to a company expense!**
                        
                        **Deleting this entry will:**
                        - Remove the debit from employee's ledger
                        - **BUT** the company expense will remain in the system
                        - This may cause accounting inconsistencies
                        
                        **Recommended:** Delete the expense from the Expense Management page instead.
                        """)
                    
                    col1, col2 = st.columns([1, 4])
                    with col1:
                        if st.button("🗑️ Delete Entry", type="secondary"):
                            try:
                                conn = get_db_connection()
                                cursor = conn.cursor()
                                
                                # Delete the ledger entry
                                cursor.execute(
                                    "DELETE FROM employee_ledger WHERE id = ?",
                                    (int(selected_id),)
                                )
                                
                                conn.commit()
                                st.success(f"Ledger entry ID {selected_id} deleted successfully!")
                                clear_cache()
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error deleting ledger entry: {e}")
                    
                    with col2:
                        if st.button("🔄 Refresh List"):
                            clear_cache()
                            st.rerun()
            
            else:
                st.info("No ledger entries found to delete.")
                
        except Exception as e:
            st.error(f"Error loading ledger entries for deletion: {e}")

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
                    orientation='P',  # Changed to Portrait
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
                orientation='P'  # Changed to Portrait
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
                # Fix date columns - convert to string
                if 'join_date' in df.columns:
                    df['join_date'] = pd.to_datetime(df['join_date']).dt.strftime('%Y-%m-%d')
                
                st.dataframe(df)
                
                if st.button("Import Employees"):
                    # Validate data before import
                    is_valid, errors = validate_employee_data(df)
                    
                    if not is_valid:
                        st.error("Data validation failed. Please fix the following errors:")
                        for error in errors:
                            st.error(error)
                        return
                    
                    conn = get_db_connection()
                    try:
                        with st.spinner("Importing..."):
                            # Clean text data before import
                            for col in df.columns:
                                if df[col].dtype == 'object':
                                    df[col] = df[col].apply(lambda x: clean_text(str(x)) if pd.notnull(x) else x)
                            
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
                                # Clean text data before import
                                df['name'] = df['name'].apply(lambda x: clean_text(str(x)) if pd.notnull(x) else x)
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
                
                # FIX: Convert date columns to string format
                if 'expense_date' in df.columns:
                    df['expense_date'] = pd.to_datetime(df['expense_date']).dt.strftime('%Y-%m-%d')
                
                st.dataframe(df)
                
                if st.button("Import Expenses"):
                    # Validate data before import
                    is_valid, errors = validate_expense_data(df)
                    
                    if not is_valid:
                        st.error("Data validation failed. Please fix the following errors:")
                        for error in errors:
                            st.error(error)
                        return
                    
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
                            cat_id = cat_map.get(clean_text(row['category_name']))
                            emp_id = emp_map.get(clean_text(row['employee_name']))
                            
                            if not cat_id:
                                error_list.append(f"Category '{row['category_name']}' not found.")
                                continue
                            
                            # Handle empty employee names
                            if pd.isna(row['employee_name']) or row['employee_name'] == '':
                                emp_id = None
                            
                            cursor.execute(
                                """
                                INSERT INTO company_expenses (expense_date, description, amount, category_id, employee_id)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (row['expense_date'], clean_text(row['description']), row['amount'], cat_id, emp_id)
                            )
                            
                            expense_id = cursor.lastrowid
                            
                            if emp_id:
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, related_expense_id, entry_type)
                                    VALUES (?, ?, ?, ?, 0, ?, 'EXPENSE')
                                    """,
                                    (emp_id, row['expense_date'], clean_text(f"Imported Expense: {row['description']}"), row['amount'], expense_id)
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
        st.markdown("Use the Employee *Name* (e.g., 'Alice Smith'). Fill in EITHER debit OR credit for each row, not both. Add entry_type: SALARY, EXPENSE, ADVANCE, or PAYMENT.")
        cols = ["employee_name", "entry_date", "description", "debit", "credit", "entry_type"]
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
                
                # FIX: Convert date columns to string format
                if 'entry_date' in df.columns:
                    df['entry_date'] = pd.to_datetime(df['entry_date']).dt.strftime('%Y-%m-%d')
                
                st.dataframe(df)

                if st.button("Import Ledger Entries"):
                    # Validate data before import
                    is_valid, errors = validate_ledger_data(df)
                    
                    if not is_valid:
                        st.error("Data validation failed. Please fix the following errors:")
                        for error in errors:
                            st.error(error)
                        return
                    
                    emp_df = get_all_employees()
                    emp_map = {row['name']: row['id'] for _, row in emp_df.iterrows()}

                    conn = get_db_connection()
                    cursor = conn.cursor()
                    imported_count = 0
                    error_list = []

                    with st.spinner("Processing and importing ledger entries..."):
                        for _, row in df.iterrows():
                            emp_id = emp_map.get(clean_text(row['employee_name']))
                            
                            if not emp_id:
                                error_list.append(f"Employee '{row['employee_name']}' not found.")
                                continue
                            
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, entry_type)
                                VALUES (?, ?, ?, ?, ?, ?)
                                """,
                                (emp_id, row['entry_date'], clean_text(row['description']), row['debit'], row['credit'], row['entry_type'])
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
    st.set_page_config(
        page_title=f"{COMPANY_NAME} App", 
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
    </style>
    """, unsafe_allow_html=True)
    
    init_db()

    st.sidebar.title(f"{COMPANY_NAME} Portal")
    try:
        st.sidebar.image('logo.png', width=150)
    except:
        pass
        
    page_options = {
        "📊 Dashboard": page_dashboard,
        "👥 Employee Management": page_employee_management,
        "💰 Expense Management": page_expense_management,
        "💸 Employee Personal Expenses": page_employee_personal_expenses,
        "💳 Salary Management": page_salary_management,
        "📋 Employee Ledger": page_employee_ledger,
        "📈 Reporting": page_reporting,
        "📤 Data Import": page_data_import,
        "⚙️ User Settings": page_user_settings,
    }
    
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()))
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
