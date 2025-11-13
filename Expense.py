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
                is_advance BOOLEAN DEFAULT 0,
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
                is_advance BOOLEAN DEFAULT 0,
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
            if 'is_advance' not in columns:
                c.execute("ALTER TABLE employee_ledger ADD COLUMN is_advance BOOLEAN DEFAULT 0")
        except:
            pass
        
        try:
            c.execute("PRAGMA table_info(company_expenses)")
            columns = [column[1] for column in c.fetchall()]
            if 'is_advance' not in columns:
                c.execute("ALTER TABLE company_expenses ADD COLUMN is_advance BOOLEAN DEFAULT 0")
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

# --- PDF Class ---
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
                cell_text = str(row[col]) if pd.notna(row[col]) else ""
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        cell_value = row[col]
                        if pd.isna(cell_value):
                            cell_text = ""
                        else:
                            cell_text = f"{float(cell_value):,.2f}"
                    except (ValueError, TypeError):
                        pass
                
                lines = self.wrap_text(cell_text, col_widths[i] - 1)
                line_heights.append(len(lines) * 6)
            
            row_height = max(line_heights) if line_heights else 6
            max_height = max(max_height, row_height)
            
            x_position = self.get_x()
            for i, col in enumerate(df.columns):
                cell_text = str(row[col]) if pd.notna(row[col]) else ""
                align = 'L'
                
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        cell_value = row[col]
                        if pd.isna(cell_value):
                            cell_text = ""
                            align = 'L'
                        else:
                            cell_text = f"{float(cell_value):,.2f}"
                            align = 'R'
                    except (ValueError, TypeError):
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
        if not text or text == "None" or pd.isna(text):
            return ['']
        
        text = str(text)
        words = text.split(' ')
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

# --- Helper Functions with Proper DB Handling ---
@st.cache_data(ttl=60)
def get_all_employees():
    """Get all employees with proper error handling"""
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
            
        df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
        conn.close()
        
        if 'join_date' in df.columns:
            df['join_date'] = df['join_date'].astype(str)
        return df.fillna("")
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
        return df.fillna("")
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
        exp_total = exp_total_df['total'].iloc[0] if not exp_total_df.empty and exp_total_df['total'].iloc[0] is not None else 0.0
        
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
    """Get current balance for an employee (excluding advances)"""
    try:
        conn = get_db_connection()
        if conn is None:
            return 0.0
            
        balance_df = pd.read_sql_query(
            "SELECT SUM(credit) - SUM(debit) as balance FROM employee_ledger WHERE employee_id = ? AND is_advance = 0",
            conn,
            params=(employee_id,)
        )
        conn.close()
        return balance_df['balance'].iloc[0] if not balance_df.empty and balance_df['balance'].iloc[0] is not None else 0.0
    except:
        return 0.0

def get_employee_advance_balance(employee_id):
    """Get advance balance for an employee"""
    try:
        conn = get_db_connection()
        if conn is None:
            return 0.0
            
        advance_df = pd.read_sql_query(
            "SELECT SUM(debit) - SUM(credit) as advance_balance FROM employee_ledger WHERE employee_id = ? AND is_advance = 1",
            conn,
            params=(employee_id,)
        )
        conn.close()
        return advance_df['advance_balance'].iloc[0] if not advance_df.empty and advance_df['advance_balance'].iloc[0] is not None else 0.0
    except:
        return 0.0

def get_employee_advance_details(employee_id):
    """Get advance details for an employee"""
    try:
        conn = get_db_connection()
        if conn is None:
            return 0.0, pd.DataFrame()
            
        advance_df = pd.read_sql_query(
            """
            SELECT id, entry_date, description, debit, credit 
            FROM employee_ledger 
            WHERE employee_id = ? AND is_advance = 1
            ORDER BY entry_date DESC
            """,
            conn,
            params=(employee_id,)
        )
        conn.close()
        
        total_advance = advance_df['debit'].sum() - advance_df['credit'].sum()
        return total_advance, advance_df.fillna("")
    except:
        return 0.0, pd.DataFrame()

def get_employee_ledger_entries(employee_id, start_date=None, end_date=None):
    """Get all ledger entries for an employee"""
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
            
        query = """
        SELECT id, entry_date, description, debit, credit, is_advance
        FROM employee_ledger 
        WHERE employee_id = ?
        """
        params = [employee_id]
        
        if start_date and end_date:
            query += " AND entry_date BETWEEN ? AND ?"
            params.extend([str(start_date), str(end_date)])
            
        query += " ORDER BY entry_date DESC, id DESC"
        
        ledger_df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return ledger_df.fillna("")
    except Exception as e:
        st.error(f"Error loading ledger entries: {e}")
        return pd.DataFrame()

def update_employee_ledger_entry(entry_id, entry_date, description, debit, credit, is_advance):
    """Update a ledger entry"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE employee_ledger 
            SET entry_date = ?, description = ?, debit = ?, credit = ?, is_advance = ?
            WHERE id = ?
            """,
            (str(entry_date), description, debit, credit, 1 if is_advance else 0, entry_id)
        )
        conn.commit()
        conn.close()
        clear_cache()
        return True
    except Exception as e:
        st.error(f"Error updating ledger entry: {e}")
        return False

def delete_employee_ledger_entry(entry_id):
    """Delete a ledger entry"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        cursor.execute("DELETE FROM employee_ledger WHERE id = ?", (entry_id,))
        conn.commit()
        conn.close()
        clear_cache()
        return True
    except Exception as e:
        st.error(f"Error deleting ledger entry: {e}")
        return False

def update_company_expense(expense_id, description, amount, expense_date, category_id, employee_id, is_advance):
    """Update a company expense"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE company_expenses 
            SET description = ?, amount = ?, expense_date = ?, category_id = ?, employee_id = ?, is_advance = ?
            WHERE id = ?
            """,
            (description, amount, str(expense_date), category_id, employee_id, 1 if is_advance else 0, expense_id)
        )
        conn.commit()
        conn.close()
        clear_cache()
        return True
    except Exception as e:
        st.error(f"Error updating expense: {e}")
        return False

def delete_company_expense(expense_id):
    """Delete a company expense"""
    try:
        conn = get_db_connection()
        if conn is None:
            return False
            
        cursor = conn.cursor()
        # First delete related ledger entries
        cursor.execute("DELETE FROM employee_ledger WHERE related_expense_id = ?", (expense_id,))
        # Then delete the expense
        cursor.execute("DELETE FROM company_expenses WHERE id = ?", (expense_id,))
        conn.commit()
        conn.close()
        clear_cache()
        return True
    except Exception as e:
        st.error(f"Error deleting expense: {e}")
        return False

# --- PDF Generation Functions ---
def generate_employee_ledger_pdf(employee_name, ledger_df, start_date, end_date):
    """Generate employee ledger PDF"""
    try:
        pdf = PDF(orientation='L', unit='mm', format='A4')
        pdf.report_title = f"Employee Ledger - {employee_name}"
        pdf.date_range_str = f"From {start_date} to {end_date}"
        pdf.add_page()
        
        if ledger_df.empty:
            pdf.set_font('Arial', 'I', 10)
            pdf.cell(0, 10, "No ledger entries found for the selected period.", 1, 1, 'C')
        else:
            # Prepare data for PDF
            pdf_data = ledger_df[['entry_date', 'description', 'debit', 'credit']].copy()
            pdf_data.columns = ['Date', 'Description', 'Debit', 'Credit']
            pdf_data['Date'] = pdf_data['Date'].astype(str)
            
            pdf.add_table(pdf_data, totals_cols=['Debit', 'Credit'])
            
            # Add summary
            total_debit = ledger_df['debit'].sum()
            total_credit = ledger_df['credit'].sum()
            net_balance = total_credit - total_debit
            
            pdf.ln(10)
            pdf.set_font('Arial', 'B', 10)
            pdf.cell(0, 8, f"Total Debit: Rs. {total_debit:,.2f} | Total Credit: Rs. {total_credit:,.2f} | Net Balance: Rs. {net_balance:,.2f}", 0, 1, 'L')

        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

def generate_individual_slip_pdf(emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary, advance_deduction=0):
    """Generate individual salary slip PDF"""
    try:
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
                desc_text = str(row['description']) if pd.notna(row['description']) else ""
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

        # Add advance deduction if any
        if advance_deduction > 0:
            pdf.set_font('Arial', '', 9)
            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(desc_width, 8, "Advance Deduction", 1, 'L')
            pdf.set_xy(x + desc_width, y)
            pdf.cell(amount_width, 8, "0.00", 1, 0, 'R')
            pdf.set_xy(x + desc_width + amount_width, y)
            pdf.cell(amount_width, 8, f"{advance_deduction:,.2f}", 1, 1, 'R')

        pdf.set_font('Arial', 'B', 10)
        pdf.cell(desc_width, 8, "Total", 1, 0, 'R')
        pdf.cell(amount_width, 8, f"{total_credits:,.2f}", 1, 0, 'R')
        total_debits_with_advance = total_debits + advance_deduction
        pdf.cell(amount_width, 8, f"{total_debits_with_advance:,.2f}", 1, 1, 'R')

        pdf.ln(8)
        
        pdf.set_font('Arial', 'B', 14)
        pdf.set_fill_color(210, 210, 210)
        net_salary_with_advance = net_salary - advance_deduction
        pdf.cell(desc_width, 12, "Net Salary Payable", 1, 0, 'R', fill=True)
        pdf.cell(amount_width * 2, 12, f"Rs. {net_salary_with_advance:,.2f}", 1, 1, 'R', fill=True)
        
        if advance_deduction > 0:
            pdf.ln(5)
            pdf.set_font('Arial', 'I', 9)
            pdf.cell(0, 6, f"Note: Advance deduction of Rs. {advance_deduction:,.2f} has been applied", 0, 1, 'L')
        
        pdf.ln(12)
        
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(0, 8, "Bank Details", 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        bank_info = emp_details.get('bank', '')
        account_title = emp_details.get('account_title', '')
        account_no = emp_details.get('account_no', '')
        
        pdf.cell(0, 6, f"  Bank: {bank_info if bank_info else 'N/A'}", 0, 1, 'L')
        pdf.cell(0, 6, f"  Account Title: {account_title if account_title else 'N/A'}", 0, 1, 'L')
        pdf.cell(0, 6, f"  Account No: {account_no if account_no else 'N/A'}", 0, 1, 'L')

        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Error generating PDF: {e}")
        return None

def generate_pdf_report(df, title, date_range=None, orientation='L', totals_cols=None):
    """Generate PDF report"""
    try:
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
            # Replace NaN values with empty strings
            df = df.fillna("")
            pdf.add_table(df, totals_cols=totals_cols)
        
        return pdf.output(dest='S').encode('latin-1')
    except Exception as e:
        st.error(f"Error generating PDF report: {e}")
        return None

# --- Data Import/Export System ---
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

    def export_expenses_to_excel(self):
        """Export all expenses to Excel format"""
        try:
            conn = get_db_connection()
            if conn is None:
                return io.BytesIO()
                
            expenses_df = pd.read_sql_query('''
                SELECT 
                    ce.description,
                    ce.amount,
                    ce.expense_date,
                    ec.name as category,
                    e.name as employee_name,
                    CASE WHEN ce.is_advance = 1 THEN 'Yes' ELSE 'No' END as is_advance
                FROM company_expenses ce
                LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                LEFT JOIN employees e ON ce.employee_id = e.id
                ORDER BY ce.expense_date DESC
            ''', conn)
            conn.close()
            
            output = io.BytesIO()
            
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                expenses_df.to_excel(writer, sheet_name='Expenses', index=False)
                
                workbook = writer.book
                worksheet = writer.sheets['Expenses']
                
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                for col_num, value in enumerate(expenses_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                worksheet.set_column('A:A', 30)
                worksheet.set_column('B:F', 15)
            
            output.seek(0)
            return output
        except Exception as e:
            st.error(f"Error exporting expenses: {e}")
            return io.BytesIO()
    
    def import_employees_from_excel(self, uploaded_file):
        """Import employees from Excel file"""
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
                    
                    if hasattr(join_date, 'strftime'):
                        join_date = join_date.strftime('%Y-%m-%d')
                    else:
                        join_date = str(join_date)
                    
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

    def import_expenses_from_excel(self, uploaded_file):
        """Import expenses from Excel file"""
        try:
            df = pd.read_excel(uploaded_file)
            required_columns = ['description', 'amount', 'expense_date', 'category']
            
            if not all(col in df.columns for col in required_columns):
                st.error(f"Missing required columns. Required: {required_columns}")
                return False
            
            success_count = 0
            error_count = 0
            
            conn = get_db_connection()
            if conn is None:
                return False
            
            # Get all categories and employees for lookup
            categories_df = get_all_categories()
            employees_df = get_all_employees()
            
            category_map = {row['name'].lower(): row['id'] for _, row in categories_df.iterrows()}
            employee_map = {row['name'].lower(): row['id'] for _, row in employees_df.iterrows()}
                
            for index, row in df.iterrows():
                try:
                    description = str(row['description']).strip()
                    if not description:
                        error_count += 1
                        continue
                    
                    amount = float(row['amount'])
                    expense_date = row['expense_date']
                    category_name = str(row['category']).strip().lower()
                    is_advance = row.get('is_advance', False)
                    
                    # Handle expense date
                    if hasattr(expense_date, 'strftime'):
                        expense_date = expense_date.strftime('%Y-%m-%d')
                    else:
                        expense_date = str(expense_date)
                    
                    # Get or create category
                    if category_name in category_map:
                        category_id = category_map[category_name]
                    else:
                        # Create new category
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (category_name.title(),))
                        category_id = cursor.lastrowid
                        category_map[category_name] = category_id
                    
                    # Get employee ID if provided
                    employee_id = None
                    if 'employee_name' in df.columns and pd.notna(row.get('employee_name')):
                        employee_name = str(row['employee_name']).strip().lower()
                        if employee_name in employee_map:
                            employee_id = employee_map[employee_name]
                    
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id, is_advance)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (description, amount, expense_date, category_id, employee_id, 1 if is_advance else 0))
                    
                    # If expense is linked to an employee and is not advance, add to ledger as credit (expense claim)
                    if employee_id is not None and not is_advance:
                        cursor.execute(
                            """
                            INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, related_expense_id, is_advance)
                            VALUES (?, ?, ?, 0, ?, ?, 0)
                            """,
                            (employee_id, expense_date, f"Expense Claim: {description}", amount, cursor.lastrowid)
                        )
                    # If it's an advance, add to ledger as debit (employee owes company)
                    elif employee_id is not None and is_advance:
                        cursor.execute(
                            """
                            INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, related_expense_id, is_advance)
                            VALUES (?, ?, ?, ?, 0, ?, 1)
                            """,
                            (employee_id, expense_date, f"Advance: {description}", amount, cursor.lastrowid)
                        )
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    st.error(f"Error in row {index + 2}: {str(e)}")
            
            conn.commit()
            conn.close()
            st.success(f"Successfully imported {success_count} expenses. Failed: {error_count}")
            clear_cache()
            return True
            
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")
            return False

# --- Employee Expense Management System ---
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
                    "SELECT SUM(debit) as total_debits FROM employee_ledger WHERE is_advance = 0",
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
    
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "➕ Add Expense/Advance", "📊 Employee Balances", "🔍 Expense History", 
        "💸 Salary Processing", "📄 Salary Slips", "💰 Advance Details", "✏️ Edit Entries"
    ])
    
    with tab1:
        st.subheader("Add Employee Expense Claim or Advance")
        
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
                    advance_balance = get_employee_advance_balance(employee_id)
                    st.info(f"Current Balance: Rs. {current_balance:,.2f}")
                    st.info(f"Advance Balance: Rs. {advance_balance:,.2f}")
                    
                with cols[1]:
                    expense_date = st.date_input("Date", date.today())
                    amount = st.number_input("Amount (Rs.)", min_value=0.01, step=100.0, format="%.2f")
                
                with cols[2]:
                    transaction_type = st.selectbox(
                        "Transaction Type",
                        ["Expense Claim", "Advance Payment", "Advance Settlement", "Other Adjustment"]
                    )
                    description = st.text_input("Description", placeholder="e.g., Travel allowance, Meal expense")
                
                submitted = st.form_submit_button("💾 Add Transaction")
                if submitted:
                    if employee_id and amount > 0 and description:
                        try:
                            conn = get_db_connection()
                            if conn is None:
                                st.error("Database connection failed")
                                return
                                
                            cursor = conn.cursor()
                            
                            if transaction_type == "Expense Claim":
                                # Expense claim - credit to employee (company owes employee)
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                                    VALUES (?, ?, ?, 0, ?, 0)
                                    """,
                                    (employee_id, str(expense_date), f"Expense Claim: {description}", amount)
                                )
                                message_type = "expense claim"
                                
                            elif transaction_type == "Advance Payment":
                                # Advance payment - debit to employee (employee owes company)
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                                    VALUES (?, ?, ?, ?, 0, 1)
                                    """,
                                    (employee_id, str(expense_date), f"Advance: {description}", amount)
                                )
                                message_type = "advance payment"
                                
                            elif transaction_type == "Advance Settlement":
                                # Advance settlement - credit to employee (reducing advance balance)
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                                    VALUES (?, ?, ?, 0, ?, 1)
                                    """,
                                    (employee_id, str(expense_date), f"Advance Settlement: {description}", amount)
                                )
                                message_type = "advance settlement"
                                
                            else:  # Other Adjustment
                                # Let user choose debit or credit
                                adjustment_type = st.radio("Adjustment Type", ["Credit to Employee", "Debit to Employee"])
                                if adjustment_type == "Credit to Employee":
                                    cursor.execute(
                                        """
                                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                                        VALUES (?, ?, ?, 0, ?, 0)
                                        """,
                                        (employee_id, str(expense_date), f"Adjustment: {description}", amount)
                                    )
                                else:
                                    cursor.execute(
                                        """
                                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                                        VALUES (?, ?, ?, ?, 0, 0)
                                        """,
                                        (employee_id, str(expense_date), f"Adjustment: {description}", amount)
                                    )
                                message_type = "adjustment"
                            
                            conn.commit()
                            conn.close()
                            employee_name = employees_df[employees_df['id'] == employee_id]['name'].iloc[0]
                            st.success(f"{transaction_type} of Rs. {amount:,.2f} added to {employee_name}'s ledger as {message_type}.")
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
                advance_balance = get_employee_advance_balance(emp['id'])
                balance_data.append({
                    'Employee ID': emp['id'],
                    'Name': emp['name'],
                    'Designation': emp['designation'],
                    'Base Salary': emp['salary'],
                    'Expense Balance': balance,  # Company owes employee
                    'Advance Balance': advance_balance,  # Employee owes company
                    'Net Payable': emp['salary'] + balance - advance_balance
                })
            
            balance_df = pd.DataFrame(balance_data).fillna("")
            
            st.dataframe(
                balance_df.style.format({
                    'Base Salary': 'Rs. {:,.2f}',
                    'Expense Balance': 'Rs. {:,.2f}',
                    'Advance Balance': 'Rs. {:,.2f}',
                    'Net Payable': 'Rs. {:,.2f}'
                }),
                use_container_width=True
            )
            
            if st.button("📥 Download Balance Sheet"):
                pdf_bytes = generate_pdf_report(
                    balance_df, 
                    "Employee Balance Sheet",
                    orientation='L',
                    totals_cols=["Base Salary", "Expense Balance", "Advance Balance", "Net Payable"]
                )
                if pdf_bytes:
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
            
            if st.button("🔍 Show Ledger History"):
                ledger_df = get_employee_ledger_entries(selected_emp_id, start_date, end_date)
                
                if not ledger_df.empty:
                    # Display the ledger
                    display_df = ledger_df[['entry_date', 'description', 'debit', 'credit']].copy()
                    display_df.columns = ['Date', 'Description', 'Debit', 'Credit']
                    
                    st.dataframe(
                        display_df.style.format({
                            'Debit': 'Rs. {:,.2f}',
                            'Credit': 'Rs. {:,.2f}'
                        }),
                        use_container_width=True
                    )
                    
                    total_debit = ledger_df['debit'].sum()
                    total_credit = ledger_df['credit'].sum()
                    net_balance = total_credit - total_debit
                    
                    st.metric("Net Balance for Period", f"Rs. {net_balance:,.2f}")
                    
                    # Download PDF option
                    employee_name = employee_list[selected_emp_id]
                    pdf_bytes = generate_employee_ledger_pdf(employee_name, ledger_df, start_date, end_date)
                    if pdf_bytes:
                        st.download_button(
                            label="📥 Download Ledger PDF",
                            data=pdf_bytes,
                            file_name=f"Ledger_{employee_name}_{start_date}_{end_date}.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.info("No ledger entries found for the selected period.")
    
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
        
        # Advance deduction option
        deduct_advances = st.checkbox("Deduct Advances from Salary", value=True)
        
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
                                "SELECT 1 FROM employee_ledger WHERE employee_id = ? AND description = ? AND entry_date BETWEEN ? AND ?",
                                (emp['id'], description, str(first_day), str(last_day))
                            )
                            if cursor.fetchone():
                                skipped_count += 1
                                continue
                                
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                                VALUES (?, ?, ?, 0, ?, 0)
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
                        
                    # Build query based on whether to deduct advances
                    if deduct_advances:
                        query = f"""
                        SELECT
                            e.name AS "Employee Name",
                            e.designation AS "Designation",
                            e.salary AS "Base Salary",
                            COALESCE(SUM(CASE WHEN l.is_advance = 0 THEN l.credit ELSE 0 END), 0) AS "Total Credits",
                            COALESCE(SUM(CASE WHEN l.is_advance = 0 THEN l.debit ELSE 0 END), 0) AS "Total Deductions",
                            COALESCE(SUM(CASE WHEN l.is_advance = 1 THEN l.debit - l.credit ELSE 0 END), 0) AS "Advance Balance",
                            (COALESCE(SUM(CASE WHEN l.is_advance = 0 THEN l.credit ELSE 0 END), 0) - 
                             COALESCE(SUM(CASE WHEN l.is_advance = 0 THEN l.debit ELSE 0 END), 0) -
                             COALESCE(SUM(CASE WHEN l.is_advance = 1 THEN l.debit - l.credit ELSE 0 END), 0)) AS "Net Salary",
                            e.bank AS "Bank",
                            e.account_title AS "Account Title",
                            e.account_no AS "Account No"
                        FROM employees e
                        LEFT JOIN employee_ledger l ON e.id = l.employee_id
                            AND l.entry_date BETWEEN '{first_day}' AND '{last_day}'
                        GROUP BY e.id, e.name, e.designation, e.salary, e.bank, e.account_title, e.account_no
                        ORDER BY e.name
                        """
                    else:
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
                        salary_df = salary_df.fillna("")
                        st.dataframe(salary_df, use_container_width=True)
                        
                        total_base = salary_df['Base Salary'].sum()
                        total_net = salary_df['Net Salary'].sum()
                        total_deductions = salary_df['Total Deductions'].sum()
                        
                        if deduct_advances:
                            total_advances = salary_df['Advance Balance'].sum()
                            st.success(f"**Summary:** Base Salary: Rs. {total_base:,.2f} | Deductions: Rs. {total_deductions:,.2f} | Advances: Rs. {total_advances:,.2f} | Net Payable: Rs. {total_net:,.2f}")
                        else:
                            st.success(f"**Summary:** Base Salary: Rs. {total_base:,.2f} | Deductions: Rs. {total_deductions:,.2f} | Net Payable: Rs. {total_net:,.2f}")
                        
                        pdf_bytes = generate_pdf_report(
                            salary_df, 
                            f"Salary Sheet - {selected_month.strftime('%B %Y')}", 
                            date_range=(first_day, last_day),
                            orientation='L',
                            totals_cols=["Base Salary", "Total Credits", "Total Deductions", "Net Salary"] + (["Advance Balance"] if deduct_advances else [])
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
            
            deduct_advance_slip = st.checkbox("Deduct Advance from Salary Slip", value=True, key="slip_advance")
            
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
                    
                    # Get ledger entries for the month
                    ledger_df = pd.read_sql_query(
                        """
                        SELECT description, debit, credit, is_advance
                        FROM employee_ledger 
                        WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                        ORDER BY entry_date
                        """,
                        conn,
                        params=(selected_emp_id, str(first_day), str(last_day))
                    )
                    conn.close()
                    
                    # Calculate totals
                    regular_entries = ledger_df[ledger_df['is_advance'] == 0]
                    total_credits = regular_entries['credit'].sum()
                    total_debits = regular_entries['debit'].sum()
                    net_salary = total_credits - total_debits
                    
                    # Calculate advance deduction if requested
                    advance_deduction = 0
                    if deduct_advance_slip:
                        advance_entries = ledger_df[ledger_df['is_advance'] == 1]
                        advance_deduction = advance_entries['debit'].sum() - advance_entries['credit'].sum()
                    
                    pdf_bytes = generate_individual_slip_pdf(
                        emp_details, regular_entries.fillna(""), slip_month, total_credits, total_debits, net_salary, advance_deduction
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
        st.subheader("Employee Advance Details")
        
        if employees_df.empty:
            st.warning("No employees found.")
        else:
            employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
            
            selected_emp_id = st.selectbox(
                "Select Employee",
                options=list(employee_list.keys()),
                format_func=lambda x: employee_list[x],
                key="advance_employee"
            )
            
            if selected_emp_id:
                total_advance, advance_df = get_employee_advance_details(selected_emp_id)
                
                st.metric("Total Advance Balance", f"Rs. {total_advance:,.2f}")
                
                if not advance_df.empty:
                    st.subheader("Advance Transaction History")
                    
                    # Display advance transactions
                    display_df = advance_df[['entry_date', 'description', 'debit', 'credit']].copy()
                    display_df.columns = ['Date', 'Description', 'Debit', 'Credit']
                    
                    st.dataframe(
                        display_df.style.format({
                            'Debit': 'Rs. {:,.2f}',
                            'Credit': 'Rs. {:,.2f}'
                        }),
                        use_container_width=True
                    )
                    
                    # Download advance details PDF
                    if st.button("📥 Download Advance Details PDF"):
                        pdf_bytes = generate_pdf_report(
                            display_df,
                            f"Advance Details - {employee_list[selected_emp_id]}",
                            orientation='L',
                            totals_cols=['Debit', 'Credit']
                        )
                        if pdf_bytes:
                            st.download_button(
                                label="Download PDF",
                                data=pdf_bytes,
                                file_name=f"Advance_Details_{employee_list[selected_emp_id]}.pdf",
                                mime="application/pdf"
                            )
                else:
                    st.info("No advance transactions found for this employee.")
    
    with tab7:
        st.subheader("Edit/Delete Ledger Entries")
        
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
                    key="edit_employee"
                )
            with col2:
                # Get all ledger entries for the employee
                ledger_df = get_employee_ledger_entries(selected_emp_id)
                
                if not ledger_df.empty:
                    # Create a list of entries for selection
                    entry_options = {}
                    for _, row in ledger_df.iterrows():
                        entry_date = row['entry_date']
                        desc = row['description'][:50]  # Truncate long descriptions
                        debit = row['debit']
                        credit = row['credit']
                        entry_type = "Advance" if row['is_advance'] == 1 else "Regular"
                        option_text = f"{entry_date} - {desc} - Debit: {debit:,.2f} - Credit: {credit:,.2f} - {entry_type}"
                        entry_options[option_text] = row['id']
                    
                    selected_entry = st.selectbox(
                        "Select Entry to Edit/Delete",
                        options=list(entry_options.keys())
                    )
                    
                    if selected_entry:
                        entry_id = entry_options[selected_entry]
                        entry_data = ledger_df[ledger_df['id'] == entry_id].iloc[0]
                        
                        st.subheader("Edit Entry")
                        with st.form("edit_ledger_form"):
                            col1, col2 = st.columns(2)
                            with col1:
                                new_date = st.date_input("Date", value=datetime.strptime(entry_data['entry_date'], '%Y-%m-%d').date())
                                new_description = st.text_input("Description", value=entry_data['description'])
                            with col2:
                                new_debit = st.number_input("Debit Amount", value=float(entry_data['debit']), min_value=0.0, format="%.2f")
                                new_credit = st.number_input("Credit Amount", value=float(entry_data['credit']), min_value=0.0, format="%.2f")
                                new_is_advance = st.checkbox("Is Advance Entry", value=bool(entry_data['is_advance']))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                update_clicked = st.form_submit_button("💾 Update Entry")
                            with col2:
                                delete_clicked = st.form_submit_button("🗑️ Delete Entry")
                            
                            if update_clicked:
                                if update_employee_ledger_entry(entry_id, new_date, new_description, new_debit, new_credit, new_is_advance):
                                    st.success("Entry updated successfully!")
                                    st.rerun()
                            
                            if delete_clicked:
                                if delete_employee_ledger_entry(entry_id):
                                    st.success("Entry deleted successfully!")
                                    st.rerun()
                else:
                    st.info("No ledger entries found for this employee.")

# --- Employee Management ---
def page_employee_management():
    st.title("👥 Employee Management")
    
    tab1, tab2 = st.tabs(["➕ Add New Employee", "📋 Manage Employees"])
    
    with tab1:
        st.subheader("Add New Employee")
        with st.form("new_employee_form", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                name = st.text_input("Full Name", placeholder="e.g., Ali Ahmed")
                salary = st.number_input("Monthly Base Salary (Rs.)", min_value=0.0, step=1000.0, value=0.0, format="%.2f")
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
                        if conn is None:
                            st.error("Database connection failed")
                            return
                            
                        conn.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (name, designation, salary, bank, account_title, account_no, str(join_date))
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

            balance_data = []
            advance_data = []
            for _, emp in employees_df.iterrows():
                balance = get_employee_balance(emp['id'])
                advance_balance = get_employee_advance_balance(emp['id'])
                balance_data.append(balance)
                advance_data.append(advance_balance)
            
            employees_df['Expense Balance'] = balance_data
            employees_df['Advance Balance'] = advance_data
            employees_df['Net Payable'] = employees_df['salary'] + employees_df['Expense Balance'] - employees_df['Advance Balance']

            display_cols = ['id', 'name', 'designation', 'salary', 'Advance Balance', 'Expense Balance', 'Net Payable', 'bank', 'join_date']
            if all(col in employees_df.columns for col in display_cols):
                display_df = employees_df[display_cols].copy().fillna("")
                
                st.dataframe(
                    display_df.style.format({
                        'salary': 'Rs. {:,.2f}',
                        'Advance Balance': 'Rs. {:,.2f}',
                        'Expense Balance': 'Rs. {:,.2f}',
                        'Net Payable': 'Rs. {:,.2f}'
                    }),
                    use_container_width=True
                )

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
                        edit_salary = st.number_input("Salary", value=float(emp_data['salary']), step=1000.0, format="%.2f")
                        edit_bank = st.text_input("Bank", value=emp_data.get('bank', ''))
                    with cols[1]:
                        edit_designation = st.text_input("Designation", value=emp_data['designation'])
                        edit_account_title = st.text_input("Account Title", value=emp_data.get('account_title', ''))
                        edit_account_no = st.text_input("Account No", value=emp_data.get('account_no', ''))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        update_submitted = st.form_submit_button("💾 Update Employee")
                    with col2:
                        delete_submitted = st.form_submit_button("🗑️ Delete Employee", type="secondary")
                    
                    if update_submitted:
                        try:
                            conn = get_db_connection()
                            if conn is None:
                                st.error("Database connection failed")
                                return
                                
                            conn.execute(
                                """
                                UPDATE employees SET
                                name = ?, designation = ?, salary = ?, bank = ?, account_title = ?, account_no = ?
                                WHERE id = ?
                                """,
                                (edit_name, edit_designation, edit_salary, edit_bank, edit_account_title, edit_account_no, selected_emp_id)
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

# --- Company Expense Management ---
def page_expense_management():
    st.title("💼 Company Expense Management")
    
    st.info("""
    **Note:** This page is for company expenses. Use the Employee Expense Management page for employee-specific transactions.
    """)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Expense", "📋 View Expenses", "📊 Expense Reports", "✏️ Edit Expenses"])
    
    with tab1:
        st.subheader("Add Company Expense")
        
        categories_df = get_all_categories()
        employees_df = get_all_employees()
        
        with st.form("add_company_expense", clear_on_submit=True):
            cols = st.columns(2)
            with cols[0]:
                description = st.text_input("Description", placeholder="e.g., Office supplies purchase")
                amount = st.number_input("Amount (Rs.)", min_value=0.01, step=100.0, format="%.2f")
                expense_date = st.date_input("Expense Date", date.today())
            with cols[1]:
                if not categories_df.empty:
                    category_options = {row['id']: row['name'] for _, row in categories_df.iterrows()}
                    category_id = st.selectbox(
                        "Category",
                        options=list(category_options.keys()),
                        format_func=lambda x: category_options[x]
                    )
                else:
                    category_id = 1
                    st.info("Using default category")
                
                # Check if this is an advance
                is_advance = st.checkbox("This is an Advance Payment")
                
                employee_options = [None]
                employee_names = {None: "None (Company Expense)"}
                if not employees_df.empty:
                    employee_options.extend([row['id'] for _, row in employees_df.iterrows()])
                    employee_names.update({row['id']: f"{row['name']} - {row['designation']}" for _, row in employees_df.iterrows()})
                
                employee_id = st.selectbox(
                    "Related Employee (Optional)",
                    options=employee_options,
                    format_func=lambda x: employee_names[x]
                )
            
            submitted = st.form_submit_button("💾 Add Expense")
            if submitted:
                if description and amount > 0:
                    try:
                        conn = get_db_connection()
                        if conn is None:
                            st.error("Database connection failed")
                            return
                            
                        cursor = conn.cursor()
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id, is_advance)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (description, amount, str(expense_date), category_id, employee_id, 1 if is_advance else 0)
                        )
                        
                        # If expense is linked to an employee and is NOT an advance, add to ledger as credit (expense claim)
                        if employee_id is not None and not is_advance:
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, related_expense_id, is_advance)
                                VALUES (?, ?, ?, 0, ?, ?, 0)
                                """,
                                (employee_id, str(expense_date), f"Expense Claim: {description}", amount, cursor.lastrowid)
                            )
                        # If it's an advance to employee, add to ledger as debit
                        elif employee_id is not None and is_advance:
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, related_expense_id, is_advance)
                                VALUES (?, ?, ?, ?, 0, ?, 1)
                                """,
                                (employee_id, str(expense_date), f"Advance: {description}", amount, cursor.lastrowid)
                            )
                        
                        conn.commit()
                        conn.close()
                        st.success("✅ Company expense added successfully!")
                        clear_cache()
                    except Exception as e:
                        st.error(f"❌ Database error: {e}")
                else:
                    st.error("❌ Please fill in all required fields.")
    
    with tab2:
        st.subheader("Company Expenses")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="comp_exp_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="comp_exp_end")
        
        if st.button("🔍 Load Expenses"):
            try:
                conn = get_db_connection()
                if conn is None:
                    st.error("Database connection failed")
                    return
                    
                expenses_df = pd.read_sql_query(
                    """
                    SELECT 
                        ce.id,
                        ce.description,
                        ce.amount,
                        ce.expense_date,
                        ec.name as category,
                        e.name as employee_name,
                        CASE WHEN ce.is_advance = 1 THEN 'Yes' ELSE 'No' END as is_advance
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    LEFT JOIN employees e ON ce.employee_id = e.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    ORDER BY ce.expense_date DESC
                    """,
                    conn,
                    params=(str(start_date), str(end_date))
                )
                conn.close()
                
                if not expenses_df.empty:
                    expenses_df = expenses_df.fillna("")
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
            report_type = st.selectbox("Report Type", ["Category-wise", "Monthly Summary", "Employee-wise"])
        
        if st.button("📊 Generate Report"):
            try:
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                conn = get_db_connection()
                if conn is None:
                    st.error("Database connection failed")
                    return
                    
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
                elif report_type == "Monthly Summary":
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
                else:  # Employee-wise
                    report_df = pd.read_sql_query(
                        """
                        SELECT 
                            e.name as Employee,
                            COUNT(ce.id) as Count,
                            SUM(ce.amount) as Total_Amount
                        FROM company_expenses ce
                        LEFT JOIN employees e ON ce.employee_id = e.id
                        WHERE ce.expense_date BETWEEN ? AND ?
                        GROUP BY e.name
                        ORDER BY Total_Amount DESC
                        """,
                        conn,
                        params=(str(first_day), str(last_day))
                    )
                conn.close()
                
                if not report_df.empty:
                    report_df = report_df.fillna("")
                    st.dataframe(
                        report_df.style.format({'Total_Amount': 'Rs. {:,.2f}'}),
                        use_container_width=True
                    )
                    
                    pdf_bytes = generate_pdf_report(
                        report_df,
                        f"Expense Report - {report_type}",
                        date_range=(first_day, last_day),
                        totals_cols=["Total_Amount"]
                    )
                    if pdf_bytes:
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
    
    with tab4:
        st.subheader("Edit/Delete Company Expenses")
        
        try:
            conn = get_db_connection()
            if conn is None:
                st.error("Database connection failed")
                return
                
            expenses_df = pd.read_sql_query(
                """
                SELECT 
                    ce.id,
                    ce.description,
                    ce.amount,
                    ce.expense_date,
                    ec.name as category,
                    e.name as employee_name,
                    ce.is_advance
                FROM company_expenses ce
                LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                LEFT JOIN employees e ON ce.employee_id = e.id
                ORDER BY ce.expense_date DESC
                LIMIT 100
                """,
                conn
            )
            conn.close()
            
            if not expenses_df.empty:
                expenses_df = expenses_df.fillna("")
                
                # Create selection options
                expense_options = {}
                for _, row in expenses_df.iterrows():
                    option_text = f"{row['expense_date']} - {row['description']} - Rs. {row['amount']:,.2f}"
                    if row['employee_name']:
                        option_text += f" - {row['employee_name']}"
                    if row['is_advance']:
                        option_text += " - [Advance]"
                    expense_options[option_text] = row['id']
                
                selected_expense = st.selectbox(
                    "Select Expense to Edit/Delete",
                    options=list(expense_options.keys())
                )
                
                if selected_expense:
                    expense_id = expense_options[selected_expense]
                    expense_data = expenses_df[expenses_df['id'] == expense_id].iloc[0]
                    
                    st.subheader("Edit Expense")
                    with st.form("edit_company_expense_form"):
                        categories_df = get_all_categories()
                        employees_df = get_all_employees()
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            new_description = st.text_input("Description", value=expense_data['description'])
                            new_amount = st.number_input("Amount", value=float(expense_data['amount']), min_value=0.01, format="%.2f")
                            new_date = st.date_input("Date", value=datetime.strptime(expense_data['expense_date'], '%Y-%m-%d').date())
                        with col2:
                            # Category selection
                            category_options = {row['name']: row['id'] for _, row in categories_df.iterrows()}
                            current_category = expense_data['category']
                            current_category_id = list(category_options.keys())[list(category_options.values()).index(current_category)] if current_category in category_options.values() else list(category_options.values())[0]
                            new_category_id = st.selectbox("Category", options=list(category_options.values()), 
                                                         format_func=lambda x: list(category_options.keys())[list(category_options.values()).index(x)])
                            
                            # Employee selection
                            employee_options = {None: "None"}
                            employee_options.update({row['id']: row['name'] for _, row in employees_df.iterrows()})
                            current_employee = expense_data['employee_name']
                            current_employee_id = None
                            if current_employee:
                                for emp_id, emp_name in employee_options.items():
                                    if emp_id is not None and emp_name == current_employee:
                                        current_employee_id = emp_id
                                        break
                            
                            new_employee_id = st.selectbox("Employee", options=list(employee_options.keys()), 
                                                         format_func=lambda x: employee_options[x],
                                                         index=list(employee_options.keys()).index(current_employee_id) if current_employee_id in employee_options else 0)
                            
                            new_is_advance = st.checkbox("Is Advance", value=bool(expense_data['is_advance']))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            update_clicked = st.form_submit_button("💾 Update Expense")
                        with col2:
                            delete_clicked = st.form_submit_button("🗑️ Delete Expense")
                        
                        if update_clicked:
                            if update_company_expense(expense_id, new_description, new_amount, new_date, new_category_id, new_employee_id, new_is_advance):
                                st.success("Expense updated successfully!")
                                st.rerun()
                        
                        if delete_clicked:
                            if delete_company_expense(expense_id):
                                st.success("Expense deleted successfully!")
                                st.rerun()
            else:
                st.info("No expenses found.")
                
        except Exception as e:
            st.error(f"Error loading expenses: {e}")

# --- Continue with the rest of the code (Reporting, Data Import, Dashboard, Settings, Main)...
# [The rest of the code remains the same as in the previous implementation]
# ... (Reporting, Data Import, Dashboard, Settings, Main functions)

# --- Reporting System ---
def page_reporting():
    st.title("📈 Reports & Analytics")
    
    tab1, tab2, tab3 = st.tabs(["📋 Employee Reports", "💼 Company Reports", "📊 Analytics"])
    
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
                    ["Salary Sheet", "Balance Summary", "Advance Summary"],
                    key="emp_report_type"
                )
            with col2:
                report_month = st.date_input("Report Month", date.today().replace(day=1), key="emp_report_month")
            
            if st.button("Generate Employee Report", key="gen_emp_report"):
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                try:
                    conn = get_db_connection()
                    if conn is None:
                        st.error("Database connection failed")
                        return
                        
                    if report_type == "Salary Sheet":
                        query = """
                        SELECT 
                            e.name AS "Employee Name",
                            e.designation AS "Designation",
                            e.salary AS "Base Salary",
                            COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? AND l.is_advance = 0 THEN l.credit ELSE 0 END), 0) AS "Total Credits",
                            COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? AND l.is_advance = 0 THEN l.debit ELSE 0 END), 0) AS "Total Deductions",
                            COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? AND l.is_advance = 1 THEN l.debit - l.credit ELSE 0 END), 0) AS "Advance Balance",
                            (COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? AND l.is_advance = 0 THEN l.credit ELSE 0 END), 0) - 
                             COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? AND l.is_advance = 0 THEN l.debit ELSE 0 END), 0) -
                             COALESCE(SUM(CASE WHEN l.entry_date BETWEEN ? AND ? AND l.is_advance = 1 THEN l.debit - l.credit ELSE 0 END), 0)) AS "Net Salary"
                        FROM employees e
                        LEFT JOIN employee_ledger l ON e.id = l.employee_id
                        GROUP BY e.id, e.name, e.designation, e.salary
                        ORDER BY e.name
                        """
                        params = [str(first_day), str(last_day)] * 6
                        report_df = pd.read_sql_query(query, conn, params=params)
                        
                    elif report_type == "Balance Summary":
                        balance_data = []
                        for _, emp in employees_df.iterrows():
                            balance = get_employee_balance(emp['id'])
                            advance_balance = get_employee_advance_balance(emp['id'])
                            balance_data.append({
                                'Employee Name': emp['name'],
                                'Designation': emp['designation'],
                                'Base Salary': emp['salary'],
                                'Expense Balance': balance,
                                'Advance Balance': advance_balance,
                                'Net Payable': emp['salary'] + balance - advance_balance
                            })
                        report_df = pd.DataFrame(balance_data)
                    
                    else:  # Advance Summary
                        advance_data = []
                        for _, emp in employees_df.iterrows():
                            advance_balance = get_employee_advance_balance(emp['id'])
                            if advance_balance > 0:
                                advance_data.append({
                                    'Employee Name': emp['name'],
                                    'Designation': emp['designation'],
                                    'Advance Balance': advance_balance,
                                    'Base Salary': emp['salary']
                                })
                        report_df = pd.DataFrame(advance_data)
                    
                    conn.close()
                    
                    if not report_df.empty:
                        report_df = report_df.fillna("")
                        st.dataframe(report_df, use_container_width=True)
                        
                        pdf_bytes = generate_pdf_report(
                            report_df,
                            f"Employee {report_type} - {report_month.strftime('%B %Y')}",
                            date_range=(first_day, last_day),
                            orientation='L'
                        )
                        
                        if pdf_bytes:
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
                    else:
                        st.info("No data found for the selected report type.")
                    
                except Exception as e:
                    st.error(f"Error generating report: {e}")
    
    with tab2:
        st.subheader("Company Expense Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1), key="comp_report_start")
        with col2:
            end_date = st.date_input("End Date", date.today(), key="comp_report_end")
        
        report_type = st.selectbox("Report Type", ["Detailed", "Summary by Category", "Employee-wise"])
        
        if st.button("Generate Company Report", key="gen_comp_report"):
            try:
                conn = get_db_connection()
                if conn is None:
                    st.error("Database connection failed")
                    return
                    
                if report_type == "Detailed":
                    query = """
                    SELECT 
                        ce.description,
                        ce.amount,
                        ce.expense_date,
                        ec.name as category,
                        e.name as employee_name,
                        CASE WHEN ce.is_advance = 1 THEN 'Yes' ELSE 'No' END as is_advance
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
                
                else:  # Employee-wise
                    query = """
                    SELECT 
                        e.name as Employee,
                        COUNT(ce.id) as Count,
                        SUM(ce.amount) as Total_Amount
                    FROM company_expenses ce
                    LEFT JOIN employees e ON ce.employee_id = e.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    GROUP BY e.name
                    ORDER BY Total_Amount DESC
                    """
                    report_df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
                
                conn.close()
                
                if not report_df.empty:
                    report_df = report_df.fillna("")
                    st.dataframe(report_df, use_container_width=True)
                    
                    total_amount = report_df['Total_Amount'].sum() if 'Total_Amount' in report_df.columns else report_df['amount'].sum()
                    st.metric("Total Amount", f"Rs. {total_amount:,.2f}")
                    
                    pdf_bytes = generate_pdf_report(
                        report_df,
                        f"Company Expense Report - {report_type}",
                        date_range=(start_date, end_date)
                    )
                    
                    if pdf_bytes:
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

# --- Data Import/Export ---
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
                                 ["Employees", "Expenses"])
        
        uploaded_file = st.file_uploader(f"Upload {import_type} Excel File", 
                                       type=['xlsx', 'xls'],
                                       key=f"upload_{import_type}")
        
        if uploaded_file is not None:
            if st.button(f"Import {import_type}", use_container_width=True):
                with st.spinner(f"Importing {import_type}..."):
                    if import_type == "Employees":
                        success = importer.import_employees_from_excel(uploaded_file)
                    else:
                        success = importer.import_expenses_from_excel(uploaded_file)
                    
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
            st.markdown("### 💼 Expense Data")
            if st.button("Export Expenses to Excel", use_container_width=True):
                excel_data = importer.export_expenses_to_excel()
                st.download_button(
                    label="📥 Download Expenses Excel",
                    data=excel_data,
                    file_name=f"Expenses_Export_{date.today().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.ms-excel",
                    use_container_width=True
                )
    
    with tab3:
        st.subheader("Download Templates")
        
        st.info("Download these templates to ensure proper data formatting for import.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 👥 Employee Template")
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
            st.markdown("#### 💼 Expense Template")
            # Create sample expense data for template
            expense_template_df = pd.DataFrame({
                'description': [
                    'Office supplies purchase',
                    'Client meeting expenses',
                    'Employee advance'
                ],
                'amount': [15000.00, 8500.00, 5000.00],
                'expense_date': [
                    date.today().strftime('%Y-%m-%d'),
                    (date.today() - timedelta(days=5)).strftime('%Y-%m-%d'),
                    (date.today() - timedelta(days=10)).strftime('%Y-%m-%d')
                ],
                'category': [
                    'Office Stationery Expense',
                    'Office Entertainment',
                    'Advance'
                ],
                'employee_name': [
                    '',
                    'Ali Ahmed',
                    'Sara Khan'
                ],
                'is_advance': [False, False, True]
            })
            
            expense_template_output = io.BytesIO()
            with pd.ExcelWriter(expense_template_output, engine='xlsxwriter') as writer:
                expense_template_df.to_excel(writer, index=False, sheet_name='Expenses')
            expense_template_output.seek(0)
            
            st.download_button(
                label="📥 Download Expense Template",
                data=expense_template_output.getvalue(),
                file_name="Expense_Import_Template.xlsx",
                mime="application/vnd.ms-excel",
                use_container_width=True
            )
            
            st.markdown("""
            **Expense Template Columns:**
            - **description**: Expense description (required)
            - **amount**: Amount in rupees (required)
            - **expense_date**: Date of expense (required, format: YYYY-MM-DD)
            - **category**: Expense category (required)
            - **employee_name**: Employee name if expense is for specific employee (optional)
            - **is_advance**: Mark as TRUE if this is an advance payment
            """)

# --- Dashboard ---
def page_dashboard():
    st.title(f"🏠 Welcome to {COMPANY_NAME} HR & Expense Manager")
    
    try:
        st.image('logo.png', width=200)
    except:
        pass
    
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
            employees_df = get_all_employees()
            total_salary = employees_df['salary'].sum() if not employees_df.empty else 0
            st.metric("Total Monthly Salary", f"Rs. {total_salary:,.2f}")
    
    except Exception as e:
        st.warning(f"Could not load dashboard stats: {e}")
    
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
            if conn:
                recent_expenses = pd.read_sql_query(
                    """
                    SELECT description, amount, expense_date 
                    FROM company_expenses 
                    ORDER BY expense_date DESC 
                    LIMIT 5
                    """,
                    conn
                )
                conn.close()
                if not recent_expenses.empty:
                    recent_expenses = recent_expenses.fillna("")
                    for _, exp in recent_expenses.iterrows():
                        st.write(f"**{exp['description']}** - Rs. {exp['amount']:,.2f} ({exp['expense_date']})")
                else:
                    st.info("No expenses recorded")
            else:
                st.info("No expenses recorded")
        except:
            st.info("No expenses recorded")
    
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

# --- Settings ---
def page_settings():
    st.title("⚙️ System Settings")
    
    tab1, tab2 = st.tabs(["🏢 Company Settings", "📊 Database Info"])
    
    with tab1:
        st.subheader("Company Information")
        
        with st.form("company_settings"):
            company_name = st.text_input("Company Name", value=COMPANY_NAME)
            developer_info = st.text_area("Developer Information", value=DEVELOPER_INFO)
            
            logo_file = st.file_uploader("Upload Company Logo", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("💾 Save Settings"):
                if logo_file is not None:
                    try:
                        with open("logo.png", "wb") as f:
                            f.write(logo_file.getbuffer())
                        st.success("✅ Logo uploaded successfully!")
                    except Exception as e:
                        st.error(f"Error saving logo: {e}")
                
                st.success("✅ Settings saved successfully!")
    
    with tab2:
        st.subheader("Database Information")
        
        try:
            conn = get_db_connection()
            if conn is None:
                st.error("Database connection failed")
                return
                
            tables = ['employees', 'employee_ledger', 'company_expenses', 'expense_categories']
            table_data = []
            
            for table in tables:
                try:
                    count_df = pd.read_sql_query(f"SELECT COUNT(*) as count FROM {table}", conn)
                    count = count_df['count'].iloc[0]
                    table_data.append({'Table': table, 'Records': count})
                except:
                    table_data.append({'Table': table, 'Records': 0})
            
            conn.close()
            
            table_df = pd.DataFrame(table_data)
            st.dataframe(table_df, use_container_width=True)
            
            try:
                db_size = os.path.getsize(DB_FILE) / (1024 * 1024)
                st.metric("Database Size", f"{db_size:.2f} MB")
            except:
                st.metric("Database Size", "Unknown")
            
            if st.button("💾 Create Backup", use_container_width=True):
                try:
                    backup_name = f"backup_{date.today().strftime('%Y%m%d')}.db"
                    import shutil
                    shutil.copy2(DB_FILE, backup_name)
                    st.success(f"✅ Backup created: {backup_name}")
                except Exception as e:
                    st.error(f"Error creating backup: {e}")
            
        except Exception as e:
            st.error(f"Error accessing database: {e}")

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
