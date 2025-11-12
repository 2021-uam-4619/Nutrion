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
        # Add company logo - try multiple possible locations
        logo_paths = ["logo.png", "assets/logo.png", "images/logo.png", "static/logo.png"]
        logo_found = False
        
        for logo_path in logo_paths:
            if os.path.exists(logo_path):
                try:
                    self.image(logo_path, 10, 8, 25)
                    logo_found = True
                    break
                except:
                    continue
        
        if not logo_found:
            # Create a simple text logo as fallback
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, self.company_name, 0, 1, 'C')
        
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
        
        self.cell(footer_width / 2, 10, "Prepared by: ___________________", 0, 0, 'L')
        self.cell(footer_width / 2, 10, "Approved by: _______________", 0, 1, 'R')
        self.ln(10)

        self.set_font('Arial', 'I', 8)
        self.cell(footer_width / 2, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'L')
        self.cell(footer_width / 2, 10, DEVELOPER_INFO, 0, 0, 'R')

    def add_table(self, df, totals_cols=None):
        if df.empty:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, "No data available", 1, 1, 'C')
            return
            
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(224, 235, 255)
        
        num_cols = len(df.columns)
        total_width = self.w - self.l_margin - self.r_margin - 10
        
        # Calculate column widths
        col_widths = self.calculate_column_widths(df, total_width, num_cols)
        
        # Draw header
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], 7, str(col).replace('_', ' ').title(), 1, 0, 'C', 1)
        self.ln()

        # Draw rows
        self.set_font('Arial', '', 8)
        fill = False
        
        for _, row in df.iterrows():
            # Draw each cell
            for i, col in enumerate(df.columns):
                cell_text = str(row[col])
                align = 'L'
                
                # Format numeric values
                if pd.api.types.is_numeric_dtype(df[col]):
                    try:
                        cell_value = row[col]
                        if pd.isna(cell_value):
                            cell_text = "N/A"
                        else:
                            cell_text = f"{float(cell_value):,.2f}"
                            align = 'R'
                    except (ValueError, TypeError):
                        pass
                
                # Set fill color for alternating rows
                self.set_fill_color(240, 240, 240) if fill else self.set_fill_color(255)
                self.cell(col_widths[i], 6, cell_text, 1, 0, align, 1)
            
            self.ln()
            fill = not fill
        
        # Totals row
        if totals_cols:
            self.set_font('Arial', 'B', 9)
            self.set_fill_color(240, 240, 240)
            
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
        min_width = 20
        max_width = total_width / 2
        
        col_widths = []
        for col in df.columns:
            header_width = len(str(col)) * 2
            content_width = df[col].astype(str).str.len().max() * 1.5
            col_width = max(header_width, content_width, min_width)
            col_width = min(col_width, max_width)
            col_widths.append(col_width)
        
        total_current_width = sum(col_widths)
        if total_current_width > total_width:
            scale_factor = total_width / total_current_width
            col_widths = [max(min_width, w * scale_factor) for w in col_widths]
        
        return col_widths

# --- Database Setup with Error Handling ---
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def safe_alter_table(cursor, table_name, column_name, column_type):
    """Safely alter table to add column if it doesn't exist"""
    try:
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
        return True
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            return True  # Column already exists
        st.warning(f"Could not add column {column_name} to {table_name}: {e}")
        return False

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Create tables with all required columns
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
    
    # Safely add any missing columns to existing tables
    tables_columns = {
        'employees': [
            ('department', 'TEXT'),
            ('phone', 'TEXT'),
            ('email', 'TEXT'),
            ('status', 'TEXT DEFAULT "Active"'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ],
        'employee_ledger': [
            ('type', 'TEXT DEFAULT "General"'),
            ('status', 'TEXT DEFAULT "Processed"'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ],
        'company_expenses': [
            ('payment_method', 'TEXT DEFAULT "Cash"'),
            ('reference_no', 'TEXT'),
            ('status', 'TEXT DEFAULT "Pending"'),
            ('created_at', 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        ],
        'expense_categories': [
            ('type', 'TEXT DEFAULT "General"')
        ]
    }
    
    for table, columns in tables_columns.items():
        for column_name, column_type in columns:
            safe_alter_table(c, table, column_name, column_type)
    
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
        ("Salary", "HR")
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
    try:
        df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
        return df
    except Exception as e:
        st.error(f"Error loading employees: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_all_categories():
    conn = get_db_connection()
    try:
        return pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)
    except Exception as e:
        st.error(f"Error loading categories: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def get_dashboard_stats():
    conn = get_db_connection()
    
    try:
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
    except Exception as e:
        st.error(f"Error loading dashboard stats: {e}")
        return 0, 0.0, 0, 0.0

def clear_cache():
    st.cache_data.clear()

def get_employee_balance(employee_id):
    """Get current balance for an employee"""
    conn = get_db_connection()
    try:
        balance_df = pd.read_sql_query(
            "SELECT SUM(credit) - SUM(debit) as balance FROM employee_ledger WHERE employee_id = ?",
            conn,
            params=(employee_id,)
        )
        return balance_df['balance'].iloc[0] if not balance_df.empty and balance_df['balance'].iloc[0] is not None else 0.0
    except Exception as e:
        st.error(f"Error calculating balance: {e}")
        return 0.0

def get_monthly_employee_ledger(employee_id, month_date):
    """Get ledger entries for a specific month"""
    first_day = month_date.replace(day=1)
    last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
    
    conn = get_db_connection()
    try:
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
    except Exception as e:
        st.error(f"Error loading ledger: {e}")
        return pd.DataFrame()

# --- Dashboard Page ---
def page_dashboard():
    st.markdown(f'<div class="main-header">{COMPANY_NAME} HR & Expense Manager</div>', unsafe_allow_html=True)
    
    # Quick Stats
    try:
        emp_count, exp_total, cat_count, salary_total = get_dashboard_stats()
        
        st.subheader("📊 Quick Overview (Current Month)")
        cols = st.columns(4)
        with cols[0]:
            st.metric("Total Employees", emp_count)
        with cols[1]:
            st.metric("Company Expenses", f"Rs. {exp_total:,.2f}")
        with cols[2]:
            st.metric("Expense Categories", cat_count)
        with cols[3]:
            st.metric("Monthly Salary", f"Rs. {salary_total:,.2f}")
    
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
                st.write(f"**{emp['name']}** - {emp.get('designation', 'N/A')} (Rs. {emp['salary']:,.2f})")
        else:
            st.info("No employees added yet")
    
    with col2:
        st.subheader("📈 Recent Expenses")
        conn = get_db_connection()
        try:
            recent_expenses = pd.read_sql_query(
                "SELECT ce.description, ce.amount, ce.expense_date, ec.name as category "
                "FROM company_expenses ce JOIN expense_categories ec ON ce.category_id = ec.id "
                "ORDER BY ce.expense_date DESC LIMIT 5",
                conn
            )
            if not recent_expenses.empty:
                for _, exp in recent_expenses.iterrows():
                    st.write(f"**{exp['description']}** - Rs. {exp['amount']:,.2f} ({exp['category']})")
            else:
                st.info("No expenses recorded")
        except Exception as e:
            st.error(f"Error loading expenses: {e}")
    
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
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Expense", "📊 Employee Balances", "🔍 Expense History", "💸 Salary Processing"])
    
    with tab1:
        st.subheader("Add Employee Expense/Advance")
        
        employees_df = get_all_employees()
        if employees_df.empty:
            st.warning("No employees found. Please add employees first.")
        else:
            with st.form("add_employee_expense"):
                cols = st.columns(3)
                with cols[0]:
                    employee_id = st.selectbox(
                        "Select Employee",
                        options=employees_df['id'].tolist(),
                        format_func=lambda x: f"{employees_df[employees_df['id'] == x]['name'].iloc[0]} - {employees_df[employees_df['id'] == x]['designation'].iloc[0]}"
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
                                cursor.execute(
                                    """
                                    INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, type)
                                    VALUES (?, ?, ?, ?, 0, ?)
                                    """,
                                    (employee_id, str(expense_date), f"{expense_type}: {description}", amount, expense_type)
                                )
                                message_type = "expense"
                            else:
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
                        except sqlite3.Error as e:
                            st.error(f"Database error: {e}")
                    else:
                        st.error("Please fill in all required fields.")
    
    with tab2:
        st.subheader("Employee Current Balances")
        
        employees_df = get_all_employees()
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
            st.dataframe(balance_df, use_container_width=True)
            
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
            cols = st.columns(3)
            with cols[0]:
                selected_emp_id = st.selectbox(
                    "Select Employee",
                    options=employees_df['id'].tolist(),
                    format_func=lambda x: employees_df[employees_df['id'] == x]['name'].iloc[0]
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
                        SELECT entry_date as "Date", description as "Description",
                               type as "Type", debit as "Debit", credit as "Credit"
                        FROM employee_ledger 
                        WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                        ORDER BY entry_date DESC
                        """,
                        conn,
                        params=(selected_emp_id, str(start_date), str(end_date))
                    )
                    
                    if not history_df.empty:
                        st.dataframe(history_df, use_container_width=True)
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
                    for _, emp in employees_df.iterrows():
                        salary = emp['salary']
                        if salary <= 0:
                            continue
                        
                        description = f"Monthly Salary Credit - {selected_month.strftime('%B %Y')}"
                        cursor.execute(
                            """
                            INSERT OR IGNORE INTO employee_ledger (employee_id, entry_date, description, debit, credit, type)
                            VALUES (?, ?, ?, 0, ?, 'Salary Credit')
                            """,
                            (emp['id'], str(first_day), description, salary)
                        )
                        processed_count += 1
                    
                    conn.commit()
                    st.success(f"Salary credits generated for {processed_count} employees.")
                    clear_cache()
                except Exception as e:
                    st.error(f"Error generating salary credits: {e}")
        
        with col2:
            if st.button("📊 Generate Salary Sheet", use_container_width=True):
                try:
                    conn = get_db_connection()
                    query = f"""
                    SELECT e.name AS "Employee Name", e.designation AS "Designation",
                           e.salary AS "Base Salary", COALESCE(SUM(l.credit), 0) AS "Total Credits",
                           COALESCE(SUM(l.debit), 0) AS "Total Deductions",
                           (COALESCE(SUM(l.credit), 0) - COALESCE(SUM(l.debit), 0)) AS "Net Salary"
                    FROM employees e
                    LEFT JOIN employee_ledger l ON e.id = l.employee_id
                        AND l.entry_date BETWEEN '{first_day}' AND '{last_day}'
                    GROUP BY e.id, e.name, e.designation, e.salary
                    ORDER BY e.name
                    """
                    salary_df = pd.read_sql_query(query, conn)

                    if not salary_df.empty:
                        st.dataframe(salary_df, use_container_width=True)
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
                    else:
                        st.warning("No salary data found.")
                except Exception as e:
                    st.error(f"Error generating salary sheet: {e}")

# --- Employee Management ---
def page_employee_management():
    st.title("👥 Employee Management")
    
    tab1, tab2 = st.tabs(["➕ Add New Employee", "📋 Manage Employees"])
    
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

            st.dataframe(employees_df, use_container_width=True)

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
                    
                    col1, col2 = st.columns(2)
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
                            conn.execute("DELETE FROM employees WHERE id = ?", (selected_emp_id,))
                            conn.commit()
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
    
    tab1, tab2 = st.tabs(["➕ Add Expense", "📋 Expense List"])
    
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
                payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Cheque", "Card"])
            
            submitted = st.form_submit_button("💾 Add Expense")
            if submitted:
                if description and amount > 0:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, payment_method)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (description, amount, str(expense_date), category_id, payment_method)
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
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", date.today())
        
        if st.button("🔍 Filter Expenses"):
            try:
                conn = get_db_connection()
                expenses_df = pd.read_sql_query(
                    """
                    SELECT ce.description, ce.amount, ce.expense_date, ec.name as category, ce.payment_method
                    FROM company_expenses ce
                    JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    ORDER BY ce.expense_date DESC
                    """,
                    conn,
                    params=(str(start_date), str(end_date))
                )
                
                if not expenses_df.empty:
                    st.dataframe(expenses_df, use_container_width=True)
                    total_amount = expenses_df['amount'].sum()
                    st.metric("Total Expenses", f"Rs. {total_amount:,.2f}")
                else:
                    st.info("No expenses found for the selected criteria.")
            except Exception as e:
                st.error(f"Error loading expenses: {e}")

# --- Reports Page ---
def page_reporting():
    st.title("📈 Reports & Analytics")
    
    tab1, tab2 = st.tabs(["📋 Employee Reports", "💼 Company Reports"])
    
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
                    ["Salary Sheet", "Employee Master List"]
                )
            with col2:
                report_month = st.date_input("Report Month", date.today().replace(day=1))
            
            if st.button("Generate Employee Report"):
                first_day = report_month.replace(day=1)
                last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
                
                if report_type == "Salary Sheet":
                    conn = get_db_connection()
                    query = f"""
                    SELECT e.name AS "Employee Name", e.designation AS "Designation",
                           e.salary AS "Base Salary", COALESCE(SUM(l.credit), 0) AS "Total Credits",
                           COALESCE(SUM(l.debit), 0) AS "Total Deductions",
                           (COALESCE(SUM(l.credit), 0) - COALESCE(SUM(l.debit), 0)) AS "Net Salary"
                    FROM employees e
                    LEFT JOIN employee_ledger l ON e.id = l.employee_id
                        AND l.entry_date BETWEEN '{first_day}' AND '{last_day}'
                    GROUP BY e.id, e.name, e.designation, e.salary
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
                    report_df = employees_df[['name', 'designation', 'salary', 'bank', 'account_title', 'account_no', 'join_date']]
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
        
        if st.button("Generate Expense Report"):
            conn = get_db_connection()
            try:
                expenses_df = pd.read_sql_query(
                    """
                    SELECT ce.expense_date as "Date", ce.description as "Description", 
                           ec.name as "Category", ce.amount as "Amount", ce.payment_method as "Payment Method"
                    FROM company_expenses ce
                    JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    ORDER BY ce.expense_date DESC
                    """,
                    conn,
                    params=(str(start_date), str(end_date))
                )
                
                if not expenses_df.empty:
                    st.dataframe(expenses_df, use_container_width=True)
                    pdf_bytes = generate_pdf_report(
                        expenses_df,
                        "Company Expenses Report",
                        date_range=(start_date, end_date),
                        totals_cols=['Amount']
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
    
    # Navigation
    page_options = [
        "🏠 Dashboard",
        "💰 Employee Expenses", 
        "👥 Employee Management",
        "💼 Company Expenses",
        "📈 Reports"
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

if __name__ == "__main__":
    main()
