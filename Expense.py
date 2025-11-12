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

# --- Fixed Database Setup ---
def get_db_connection():
    """Create a new database connection for each operation"""
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def init_db():
    """Initialize database with proper error handling"""
    try:
        conn = get_db_connection()
        if conn is None:
            st.error("Failed to connect to database")
            return
            
        c = conn.cursor()
        
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
        
        # Safely add columns if they don't exist using PRAGMA
        try:
            c.execute("PRAGMA table_info(employees)")
            columns = [column[1] for column in c.fetchall()]
            if 'join_date' not in columns:
                c.execute("ALTER TABLE employees ADD COLUMN join_date DATE")
        except:
            pass
        
        try:
            c.execute("PRAGMA table_info(employee_ledger)")
            columns = [column[1] for column in c.fetchall()]
            if 'related_expense_id' not in columns:
                c.execute("ALTER TABLE employee_ledger ADD COLUMN related_expense_id INTEGER")
        except:
            pass
        
        # Pre-populate expense categories
        default_categories = [
            "Guard", "Labour", "Bilty Expenses", "Office Rent", "Warehouse Rent",
            "Import Export", "Office Electricity", "FBR", "Office Entertainment",
            "PSID", "Advance", "Commission", "Office Stationery Expense",
            "Employee Expenses", "Other Expense", "Company Expense", "Salary"
        ]
        
        for category in default_categories:
            try:
                c.execute("INSERT OR IGNORE INTO expense_categories (name) VALUES (?)", (category,))
            except:
                pass
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Database initialization error: {e}")

# --- Enhanced PDF Class with None Handling ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""
        self.logo_path = "logo.png"

    def header(self):
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
        
        col_widths = self.calculate_column_widths(df, total_width, num_cols)
        
        x_position = self.get_x()
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], 7, str(col).replace('_', ' ').title(), 1, 0, 'C', 1)
        self.ln()

        self.set_font('Arial', '', 8)
        self.set_fill_color(255)
        fill = False
        
        for index, row in df.iterrows():
            max_height = 6
            line_heights = []
            
            for i, col in enumerate(df.columns):
                cell_text = str(row[col])
                # Handle None values and empty strings
                if cell_text in ['None', 'NaN', '']:
                    cell_text = "N/A"
                elif pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        cell_value = row[col]
                        if pd.isna(cell_value):
                            cell_text = "N/A"
                        else:
                            cell_text = f"{float(cell_value):,.2f}"
                    except (ValueError, TypeError):
                        cell_text = "N/A"
                
                lines = self.wrap_text(cell_text, col_widths[i] - 1)
                line_heights.append(len(lines) * 6)
            
            row_height = max(line_heights) if line_heights else 6
            max_height = max(max_height, row_height)
            
            x_position = self.get_x()
            for i, col in enumerate(df.columns):
                cell_text = str(row[col])
                # Handle None values and empty strings
                if cell_text in ['None', 'NaN', '']:
                    cell_text = "N/A"
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
                        cell_text = "N/A"
                        align = 'L'
                
                self.set_xy(x_position, self.get_y())
                lines = self.wrap_text(cell_text, col_widths[i] - 1)
                
                self.set_fill_color(240, 240, 240) if fill else self.set_fill_color(255)
                self.cell(col_widths[i], max_height, '', 1, 0, 'L', 1)
                
                self.set_xy(x_position + 1, self.get_y())
                text_y = self.get_y()
                for j, line in enumerate(lines):
                    self.set_xy(x_position + 1, text_y + (j * 6))
                    self.cell(col_widths[i] - 2, 6, line, 0, 0, align)
                
                x_position += col_widths[i]
            
            self.ln(max_height)
            fill = not fill
        
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
        min_width = 15
        max_width = total_width / 2
        
        col_widths = []
        for col in df.columns:
            header_width = len(str(col).replace('_', ' ').title()) * 2.5
            content_samples = df[col].astype(str).str[:30]
            # Handle None values in content samples
            content_samples = content_samples.replace(['None', 'NaN'], 'N/A')
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
        if not text or text in ['None', 'NaN']:
            return ['N/A']
        
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
            final_lines.append(line if line else 'N/A')
        
        return final_lines if final_lines else ['N/A']

# --- Enhanced PDF Generation with None Handling ---
def generate_individual_slip_pdf(emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary):
    """Generate individual salary slip PDF with proper None handling"""
    try:
        pdf = PDF(orientation='P', unit='mm', format='A4')
        pdf.report_title = f"Salary Slip - {slip_month.strftime('%B %Y')}"
        pdf.date_range_str = ""
        pdf.add_page()
        
        # Handle None values in employee details
        emp_name = emp_details.get('name', 'N/A')
        emp_designation = emp_details.get('designation', 'N/A')
        emp_salary = emp_details.get('salary', 0)
        emp_bank = emp_details.get('bank', 'N/A')
        emp_account_title = emp_details.get('account_title', 'N/A')
        emp_account_no = emp_details.get('account_no', 'N/A')
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 12, f"Employee: {emp_name}", 0, 1, 'L')
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f"Designation: {emp_designation}", 0, 1, 'L')
        pdf.cell(0, 8, f"Base Salary: Rs. {emp_salary:,.2f}", 0, 1, 'L')
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
            # Handle None values in ledger data
            ledger_df = ledger_df.fillna(0)
            for _, row in ledger_df.iterrows():
                desc_text = str(row['description']) if pd.notna(row['description']) else "N/A"
                desc_lines = pdf.wrap_text(desc_text, desc_width - 2)
                
                credit_val = row['credit'] if pd.notna(row['credit']) else 0
                debit_val = row['debit'] if pd.notna(row['debit']) else 0
                
                credit_text = f"{credit_val:,.2f}" if credit_val > 0 else "0.00"
                debit_text = f"{debit_val:,.2f}" if debit_val > 0 else "0.00"
                
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
        pdf.cell(0, 6, f"  Bank: {emp_bank}", 0, 1, 'L')
        pdf.cell(0, 6, f"  Account Title: {emp_account_title}", 0, 1, 'L')
        pdf.cell(0, 6, f"  Account No: {emp_account_no}", 0, 1, 'L')

        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

def generate_pdf_report(df, title, date_range=None, orientation='L', totals_cols=None):
    """Generate PDF report with proper None handling"""
    try:
        # Handle None values in the dataframe
        df = df.fillna('N/A')
        
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
    except Exception as e:
        st.error(f"Error generating PDF report: {e}")
        return None

# --- Helper Functions with Proper DB Handling ---
@st.cache_data(ttl=60)
def get_all_employees():
    """Get all employees with proper error handling and None handling"""
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
            
        df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
        conn.close()
        
        # Handle None values in the dataframe
        df = df.fillna('')
        if 'join_date' in df.columns:
            df['join_date'] = df['join_date'].astype(str)
        return df
    except Exception as e:
        st.error(f"Error loading employees: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_all_categories():
    """Get all expense categories"""
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
            
        df = pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)
        conn.close()
        return df.fillna('')
    except:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        conn = get_db_connection()
        if conn is None:
            return 0, 0.0, 0
            
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
        
        conn.close()
        return emp_count, exp_total, cat_count
    except:
        return 0, 0.0, 0

def clear_cache():
    """Clear Streamlit cache"""
    st.cache_data.clear()

def get_employee_balance(employee_id):
    """Get current balance for an employee"""
    try:
        conn = get_db_connection()
        if conn is None:
            return 0.0
            
        balance_df = pd.read_sql_query(
            "SELECT SUM(credit) - SUM(debit) as balance FROM employee_ledger WHERE employee_id = ?",
            conn,
            params=(employee_id,)
        )
        conn.close()
        return balance_df['balance'].iloc[0] if not balance_df.empty and balance_df['balance'].iloc[0] is not None else 0.0
    except:
        return 0.0

# --- Enhanced Data Import/Export System ---
class DataImportExport:
    def __init__(self):
        pass
    
    def export_employees_to_excel(self):
        """Export all employees to Excel format"""
        try:
            employees_df = get_all_employees()
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                employees_df.to_excel(writer, sheet_name='Employees', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Employees']
                
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
        except Exception as e:
            st.error(f"Error exporting employees: {e}")
            return io.BytesIO()
    
    def import_employees_from_excel(self, uploaded_file):
        """Import employees from Excel file with proper None handling"""
        try:
            df = pd.read_excel(uploaded_file)
            required_columns = ['name', 'designation', 'salary']
            
            if not all(col in df.columns for col in required_columns):
                st.error(f"Missing required columns. Required: {required_columns}")
                return False
            
            success_count = 0
            error_count = 0
            
            conn = get_db_connection()
            if conn is None:
                return False
                
            for index, row in df.iterrows():
                try:
                    name = str(row['name']).strip() if pd.notna(row['name']) else ""
                    if not name:
                        error_count += 1
                        continue
                    
                    designation = str(row.get('designation', '')).strip() if pd.notna(row.get('designation')) else ""
                    salary = float(row.get('salary', 0)) if pd.notna(row.get('salary')) else 0.0
                    bank = str(row.get('bank', '')).strip() if pd.notna(row.get('bank')) else ""
                    account_title = str(row.get('account_title', '')).strip() if pd.notna(row.get('account_title')) else ""
                    account_no = str(row.get('account_no', '')).strip() if pd.notna(row.get('account_no')) else ""
                    join_date = row.get('join_date', date.today())
                    
                    if hasattr(join_date, 'strftime'):
                        join_date = join_date.strftime('%Y-%m-%d')
                    else:
                        join_date = str(join_date) if pd.notna(join_date) else date.today().strftime('%Y-%m-%d')
                    
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (name, designation, salary, bank, account_title, account_no, join_date))
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
            
            conn.commit()
            conn.close()
            st.success(f"Successfully imported {success_count} employees. Failed: {error_count}")
            clear_cache()
            return True
            
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")
            return False

# --- Enhanced Employee Management with Better Data Handling ---
def page_employee_management():
    st.title("👥 Employee Management")
    
    tab1, tab2, tab3 = st.tabs(["➕ Add New Employee", "📋 Manage Employees", "🔧 Bulk Operations"])
    
    with tab1:
        st.subheader("Add New Employee")
        with st.form("new_employee_form", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                name = st.text_input("Full Name *", placeholder="e.g., Ali Ahmed")
                salary = st.number_input("Monthly Base Salary (Rs.) *", min_value=0.0, step=1000.0, value=0.0)
                bank = st.text_input("Bank Name", placeholder="e.g., HBL, UBL, MCB")
                join_date = st.date_input("Joining Date", date.today())
            with cols[1]:
                designation = st.text_input("Designation *", placeholder="e.g., Sales Manager, Accountant")
                account_title = st.text_input("Account Title", placeholder="e.g., Ali Ahmed")
                account_no = st.text_input("Account Number", placeholder="e.g., 0123456789")
                
            submitted = st.form_submit_button("💾 Add Employee")
            if submitted:
                if not name or not designation:
                    st.error("❌ Name and Designation are required fields.")
                else:
                    try:
                        conn = get_db_connection()
                        if conn is None:
                            st.error("Database connection failed")
                            return
                            
                        # Handle empty strings for optional fields
                        bank_val = bank if bank else ""
                        account_title_val = account_title if account_title else ""
                        account_no_val = account_no if account_no else ""
                            
                        conn.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (name, designation, salary, bank_val, account_title_val, account_no_val, str(join_date))
                        )
                        conn.commit()
                        conn.close()
                        st.success(f"✅ Employee '{name}' added successfully!")
                        clear_cache()
                    except Exception as e:
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
            if all(col in employees_df.columns for col in display_cols):
                display_df = employees_df[display_cols].copy()
                
                # Format display - replace empty strings with "Not Set"
                for col in ['bank', 'account_title', 'account_no']:
                    if col in display_df.columns:
                        display_df[col] = display_df[col].replace('', 'Not Set')
                
                st.dataframe(
                    display_df.style.format({
                        'salary': 'Rs. {:,.2f}',
                        'Current Balance': 'Rs. {:,.2f}',
                        'Net Payable': 'Rs. {:,.2f}'
                    }),
                    use_container_width=True
                )

            # Enhanced Edit/Delete section
            st.subheader("Edit Employee Details")
            employee_names = {row['id']: f"{row['name']} - {row['designation']}" for _, row in employees_df.iterrows()}
            selected_emp_id = st.selectbox(
                "Select Employee to Edit",
                options=list(employee_names.keys()),
                format_func=lambda x: employee_names[x]
            )
            
            if selected_emp_id:
                emp_data = employees_df[employees_df['id'] == selected_emp_id].iloc[0]
                
                with st.form("edit_employee_form"):
                    st.markdown(f"### Editing: {emp_data['name']}")
                    
                    cols = st.columns(2)
                    with cols[0]:
                        edit_name = st.text_input("Name *", value=emp_data['name'])
                        edit_salary = st.number_input("Salary *", value=float(emp_data['salary']), step=1000.0)
                        edit_bank = st.text_input("Bank", value=emp_data.get('bank', ''))
                    with cols[1]:
                        edit_designation = st.text_input("Designation *", value=emp_data['designation'])
                        edit_account_title = st.text_input("Account Title", value=emp_data.get('account_title', ''))
                        edit_account_no = st.text_input("Account No", value=emp_data.get('account_no', ''))
                    
                    # Display current balance
                    current_balance = get_employee_balance(selected_emp_id)
                    st.info(f"Current Balance: Rs. {current_balance:,.2f}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        update_submitted = st.form_submit_button("💾 Update Employee", use_container_width=True)
                    with col2:
                        delete_submitted = st.form_submit_button("🗑️ Delete Employee", type="secondary", use_container_width=True)
                    with col3:
                        if st.form_submit_button("📄 Generate Salary Slip", use_container_width=True):
                            # Generate salary slip for current month
                            slip_month = date.today().replace(day=1)
                            first_day = slip_month.replace(day=1)
                            last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                            
                            try:
                                conn = get_db_connection()
                                if conn is None:
                                    st.error("Database connection failed")
                                    return
                                    
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
                                conn.close()
                                
                                total_credits = ledger_df['credit'].sum()
                                total_debits = ledger_df['debit'].sum()
                                net_salary = total_credits - total_debits
                                
                                pdf_bytes = generate_individual_slip_pdf(
                                    emp_data, ledger_df, slip_month, total_credits, total_debits, net_salary
                                )
                                
                                if pdf_bytes:
                                    employee_name = emp_data['name'].replace(' ', '_')
                                    st.download_button(
                                        label=f"📥 Download {emp_data['name']}'s Salary Slip",
                                        data=pdf_bytes,
                                        file_name=f"Salary_Slip_{employee_name}_{slip_month.strftime('%Y_%m')}.pdf",
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                                    
                            except Exception as e:
                                st.error(f"Error generating salary slip: {e}")
                    
                    if update_submitted:
                        if not edit_name or not edit_designation:
                            st.error("❌ Name and Designation are required fields.")
                        else:
                            try:
                                conn = get_db_connection()
                                if conn is None:
                                    st.error("Database connection failed")
                                    return
                                    
                                # Handle empty strings for optional fields
                                edit_bank_val = edit_bank if edit_bank else ""
                                edit_account_title_val = edit_account_title if edit_account_title else ""
                                edit_account_no_val = edit_account_no if edit_account_no else ""
                                    
                                conn.execute(
                                    """
                                    UPDATE employees SET
                                    name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, account_no = ?
                                    WHERE id = ?
                                    """,
                                    (edit_name, edit_designation, edit_salary, edit_bank_val, edit_account_title_val, edit_account_no_val, selected_emp_id)
                                )
                                conn.commit()
                                conn.close()
                                st.success("✅ Employee updated successfully!")
                                clear_cache()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error updating employee: {e}")
                    
                    if delete_submitted:
                        try:
                            conn = get_db_connection()
                            if conn is None:
                                st.error("Database connection failed")
                                return
                                
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
                                conn.close()
                                st.success("✅ Employee deleted successfully!")
                                clear_cache()
                                st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting employee: {e}")

        except Exception as e:
            st.error(f"❌ Error loading employees: {e}")
    
    with tab3:
        st.subheader("Bulk Operations")
        
        importer = DataImportExport()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📤 Export Employees")
            if st.button("Export All Employees to Excel", use_container_width=True):
                excel_data = importer.export_employees_to_excel()
                st.download_button(
                    label="📥 Download Employees Excel",
                    data=excel_data,
                    file_name=f"Employees_Export_{date.today().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
        
        with col2:
            st.markdown("#### 📥 Import Employees")
            uploaded_file = st.file_uploader("Upload Excel File", type=['xlsx', 'xls'], key="bulk_import")
            
            if uploaded_file is not None:
                if st.button("Import Employees from Excel", use_container_width=True):
                    with st.spinner("Importing employees..."):
                        success = importer.import_employees_from_excel(uploaded_file)
                        if success:
                            st.success("✅ Employees imported successfully!")
                        else:
                            st.error("❌ Failed to import employees")

# --- Enhanced Employee Expense Management with Better Data Handling ---
def page_employee_expense_management():
    st.title("💰 Employee Expense Management")
    
    employees_df = get_all_employees()
    if not employees_df.empty:
        cols = st.columns(4)
        total_employees = len(employees_df)
        total_salary = employees_df['salary'].sum()
        
        try:
            conn = get_db_connection()
            if conn:
                expenses_df = pd.read_sql_query(
                    "SELECT SUM(debit) as total_debits FROM employee_ledger",
                    conn
                )
                conn.close()
                total_expenses = expenses_df['total_debits'].iloc[0] if not expenses_df.empty and expenses_df['total_debits'].iloc[0] is not None else 0
            else:
                total_expenses = 0
        except:
            total_expenses = 0
        
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
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["➕ Add Expense", "📊 Employee Balances", "🔍 Expense History", "💸 Salary Processing", "📄 Salary Slips", "🔄 Manage Transactions"])
    
    with tab1:
        st.subheader("Add Employee Expense/Advance")
        
        if employees_df.empty:
            st.warning("No employees found. Please add employees first.")
        else:
            employee_list = {row['id']: f"{row['name']} - {row['designation']} (Salary: Rs. {row['salary']:,.2f})" 
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
                            if conn is None:
                                st.error("Database connection failed")
                                return
                                
                            cursor = conn.cursor()
                            
                            if expense_type in ["Personal Expense", "Travel Advance", "Loan Advance", "Other Deduction"]:
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                                    VALUES (?, ?, ?, ?, 0)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount)
                                )
                                message_type = "expense"
                            else:
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                                    VALUES (?, ?, ?, 0, ?)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount)
                                )
                                message_type = "credit"
                            
                            conn.commit()
                            conn.close()
                            employee_name = employees_df[employees_df['id'] == employee_id]['name'].iloc[0]
                            st.success(f"{expense_type} of Rs. {amount:,.2f} added to {employee_name}'s ledger as {message_type}.")
                            clear_cache()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Database error: {e}")
                    else:
                        st.error("Please fill in all required fields.")
    
    with tab2:
        st.subheader("Employee Current Balances")
        
        if not employees_df.empty:
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
            
            st.dataframe(
                balance_df.style.format({
                    'Base Salary': 'Rs. {:,.2f}',
                    'Current Balance': 'Rs. {:,.2f}',
                    'Net Payable': 'Rs. {:,.2f}'
                }),
                use_container_width=True
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Download Balance Sheet PDF"):
                    pdf_bytes = generate_pdf_report(
                        balance_df, 
                        "Employee Balance Sheet",
                        orientation='L',
                        totals_cols=["Base Salary", "Current Balance", "Net Payable"]
                    )
                    if pdf_bytes:
                        st.download_button(
                            label="Download PDF",
                            data=pdf_bytes,
                            file_name="Employee_Balance_Sheet.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            with col2:
                csv = balance_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Balance Sheet CSV",
                    data=csv,
                    file_name="Employee_Balance_Sheet.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("No employees found.")
    
    with tab3:
        st.subheader("Expense History")
        
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
                    if conn is None:
                        st.error("Database connection failed")
                        return
                        
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
                    conn.close()
                    
                    if not history_df.empty:
                        # Handle None values in display
                        history_df = history_df.fillna(0)
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
                        
                        # Download options
                        col1, col2 = st.columns(2)
                        with col1:
                            pdf_bytes = generate_pdf_report(
                                history_df,
                                f"Expense History - {employee_list[selected_emp_id]}",
                                date_range=(start_date, end_date)
                            )
                            if pdf_bytes:
                                st.download_button(
                                    label="📥 Download PDF",
                                    data=pdf_bytes,
                                    file_name=f"Expense_History_{employee_list[selected_emp_id]}_{start_date}_{end_date}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True
                                )
                        with col2:
                            csv = history_df.to_csv(index=False)
                            st.download_button(
                                label="📥 Download CSV",
                                data=csv,
                                file_name=f"Expense_History_{employee_list[selected_emp_id]}_{start_date}_{end_date}.csv",
                                mime="text/csv",
                                use_container_width=True
                            )
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
                    if conn is None:
                        st.error("Database connection failed")
                        return
                        
                    cursor = conn.cursor()
                    
                    processed_count = 0
                    skipped_count = 0
                    
                    with st.spinner("Processing salary credits..."):
                        for _, emp in employees_df.iterrows():
                            salary = emp['salary']
                            if salary <= 0:
                                skipped_count += 1
                                continue
                            
                            description = f"Monthly Salary Credit - {selected_month.strftime('%B %Y')}"
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
                    conn.close()
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
                    if conn is None:
                        st.error("Database connection failed")
                        return
                        
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
                    conn.close()

                    if salary_df.empty:
                        st.warning("No salary data found.")
                    else:
                        # Handle None values in display
                        salary_df = salary_df.fillna('Not Set')
                        st.dataframe(salary_df, use_container_width=True)
                        
                        total_base = salary_df['Base Salary'].sum()
                        total_net = salary_df['Net Salary'].sum()
                        total_deductions = salary_df['Total Deductions'].sum()
                        
                        st.success(f"**Summary:** Base Salary: Rs. {total_base:,.2f} | Deductions: Rs. {total_deductions:,.2f} | Net Payable: Rs. {total_net:,.2f}")
                        
                        pdf_bytes = generate_pdf_report(
                            salary_df, 
                            f"Salary Sheet - {selected_month.strftime('%B %Y')}", 
                            date_range=(first_day, last_day),
                            orientation='L',
                            totals_cols=["Base Salary", "Total Credits", "Total Deductions", "Net Salary"]
                        )
                        if pdf_bytes:
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
                    
                    conn = get_db_connection()
                    if conn is None:
                        st.error("Database connection failed")
                        return
                        
                    emp_details_df = pd.read_sql_query(
                        "SELECT * FROM employees WHERE id = ?", 
                        conn, 
                        params=(selected_emp_id,)
                    )
                    
                    if emp_details_df.empty:
                        st.error("Employee not found.")
                        conn.close()
                        return
                    
                    emp_details = emp_details_df.iloc[0].to_dict()
                    
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
                    conn.close()
                    
                    total_credits = ledger_df['credit'].sum()
                    total_debits = ledger_df['debit'].sum()
                    net_salary = total_credits - total_debits
                    
                    pdf_bytes = generate_individual_slip_pdf(
                        emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary
                    )
                    
                    if pdf_bytes:
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
    
    with tab6:
        st.subheader("Manage Transactions")
        
        try:
            conn = get_db_connection()
            if conn is None:
                st.error("Database connection failed")
                return
                
            transactions_df = pd.read_sql_query(
                """
                SELECT 
                    el.id,
                    e.name as employee_name,
                    el.entry_date,
                    el.description,
                    el.debit,
                    el.credit
                FROM employee_ledger el
                JOIN employees e ON el.employee_id = e.id
                ORDER BY el.entry_date DESC
                LIMIT 100
                """,
                conn
            )
            conn.close()
            
            if not transactions_df.empty:
                st.dataframe(
                    transactions_df.style.format({
                        'debit': 'Rs. {:,.2f}',
                        'credit': 'Rs. {:,.2f}'
                    }),
                    use_container_width=True
                )
                
                # Transaction management
                st.subheader("Edit/Delete Transaction")
                transaction_list = {row['id']: f"{row['employee_name']} - {row['description']} - {row['entry_date']}" 
                                  for _, row in transactions_df.iterrows()}
                selected_trans_id = st.selectbox(
                    "Select Transaction",
                    options=list(transaction_list.keys()),
                    format_func=lambda x: transaction_list[x]
                )
                
                if selected_trans_id:
                    trans_data = transactions_df[transactions_df['id'] == selected_trans_id].iloc[0]
                    
                    with st.form("edit_transaction_form"):
                        st.markdown(f"### Editing Transaction: {trans_data['description']}")
                        
                        cols = st.columns(2)
                        with cols[0]:
                            edit_description = st.text_input("Description *", value=trans_data['description'])
                            edit_debit = st.number_input("Debit Amount", value=float(trans_data['debit']), min_value=0.0, step=100.0)
                        with cols[1]:
                            edit_credit = st.number_input("Credit Amount", value=float(trans_data['credit']), min_value=0.0, step=100.0)
                            edit_date = st.date_input("Date *", value=datetime.strptime(trans_data['entry_date'], '%Y-%m-%d').date())
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_submitted = st.form_submit_button("💾 Update Transaction", use_container_width=True)
                        with col2:
                            delete_submitted = st.form_submit_button("🗑️ Delete Transaction", type="secondary", use_container_width=True)
                        
                        if update_submitted:
                            if not edit_description:
                                st.error("❌ Description is required.")
                            else:
                                try:
                                    conn = get_db_connection()
                                    if conn is None:
                                        st.error("Database connection failed")
                                        return
                                        
                                    conn.execute(
                                        """
                                        UPDATE employee_ledger SET
                                        description = ?, debit = ?, credit = ?, entry_date = ?
                                        WHERE id = ?
                                        """,
                                        (edit_description, edit_debit, edit_credit, str(edit_date), selected_trans_id)
                                    )
                                    conn.commit()
                                    conn.close()
                                    st.success("✅ Transaction updated successfully!")
                                    clear_cache()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error updating transaction: {e}")
                        
                        if delete_submitted:
                            try:
                                conn = get_db_connection()
                                if conn is None:
                                    st.error("Database connection failed")
                                    return
                                    
                                conn.execute("DELETE FROM employee_ledger WHERE id = ?", (selected_trans_id,))
                                conn.commit()
                                conn.close()
                                st.success("✅ Transaction deleted successfully!")
                                clear_cache()
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting transaction: {e}")
            else:
                st.info("No transactions found.")
                
        except Exception as e:
            st.error(f"Error loading transactions: {e}")

# The rest of the functions (page_expense_management, page_reporting, page_data_import, page_dashboard, page_settings) remain the same as in the previous code
# They should also include similar None value handling as shown above

# --- Main App ---
def main():
    st.set_page_config(
        page_title=f"{COMPANY_NAME} HR System", 
        layout="wide",
        page_icon="💰",
        initial_sidebar_state="expanded"
    )
    
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
    .stButton button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_db()
    
    st.sidebar.title(f"{COMPANY_NAME} HR System")
    try:
        st.sidebar.image('logo.png', width=150)
    except:
        st.sidebar.markdown(f"### {COMPANY_NAME}")
        
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard"
    
    page_options = {
        "🏠 Dashboard": page_dashboard,
        "💰 Employee Expenses": page_employee_expense_management,
        "👥 Employee Management": page_employee_management,
        "💼 Company Expenses": page_expense_management,
        "📈 Reports & Analytics": page_reporting,
        "📤 Data Import & Export": page_data_import,
        "⚙️ Settings": page_settings,
    }
    
    selected_page = st.sidebar.radio("Navigation", list(page_options.keys()), 
                                   index=list(page_options.keys()).index(st.session_state.current_page))
    
    st.session_state.current_page = selected_page
    
    st.sidebar.divider()
    st.sidebar.info(DEVELOPER_INFO)
    
    st.sidebar.markdown("### ⚡ Quick Actions")
    if st.sidebar.button("➕ Add New Employee", use_container_width=True):
        st.session_state.current_page = "👥 Employee Management"
        st.rerun()
        
    if st.sidebar.button("💸 Record Expense", use_container_width=True):
        st.session_state.current_page = "💰 Employee Expenses"
        st.rerun()
    
    page_function = page_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
