#code
import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io

# --- Simple Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# --- Simple Database Setup ---
def get_db_connection():
    try:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        st.error(f"Database connection error: {e}")
        return None

def init_db():
    try:
        conn = get_db_connection()
        if conn is None:
            return
            
        c = conn.cursor()
        
        # Simple tables
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
                FOREIGN KEY (category_id) REFERENCES expense_categories (id),
                FOREIGN KEY (employee_id) REFERENCES employees (id)
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
                is_advance BOOLEAN DEFAULT 0,
                FOREIGN KEY (employee_id) REFERENCES employees (id)
            )
        ''')
        
        # Default categories
        default_categories = ["Salary", "Employee Expenses", "Company Expense", "Advance", "Other Expense"]
        for category in default_categories:
            try:
                c.execute("INSERT OR IGNORE INTO expense_categories (name) VALUES (?)", (category,))
            except:
                pass
        
        conn.commit()
        conn.close()
        
    except Exception as e:
        st.error(f"Database initialization error: {e}")

# --- Simple PDF Class ---
class SimplePDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""

    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, COMPANY_NAME, 0, 1, 'C')
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 7, self.date_range_str, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        footer_text = f"{COMPANY_NAME} | {DEVELOPER_INFO} | Page {self.page_no()}/{{nb}}"
        self.cell(0, 10, footer_text, 0, 0, 'C')

    def add_simple_table(self, df, total_amount=0):
        self.set_font('Arial', 'B', 10)
        
        # Simple column widths
        if len(df.columns) == 4:
            col_widths = [40, 80, 30, 40]
        else:
            col_widths = [50, 80, 40]
        
        # Headers
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], 10, str(col), 1, 0, 'C')
        self.ln()
        
        # Data
        self.set_font('Arial', '', 9)
        for index, row in df.iterrows():
            for i, col in enumerate(df.columns):
                self.cell(col_widths[i], 10, str(row[col])[:30], 1, 0, 'L')
            self.ln()
        
        # Total
        if total_amount > 0:
            self.set_font('Arial', 'B', 10)
            self.cell(sum(col_widths[:-1]), 10, "TOTAL", 1, 0, 'R')
            self.cell(col_widths[-1], 10, f"Rs. {total_amount:,.2f}", 1, 1, 'R')

# --- Simple Helper Functions ---
def get_all_employees():
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
        df = pd.read_sql_query("SELECT id, name, designation, salary FROM employees ORDER BY name", conn)
        conn.close()
        return df.fillna("")
    except:
        return pd.DataFrame()

def get_all_categories():
    try:
        conn = get_db_connection()
        if conn is None:
            return pd.DataFrame()
        df = pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)
        conn.close()
        return df.fillna("")
    except:
        return pd.DataFrame()

def clear_cache():
    st.cache_data.clear()

# --- Simple Pages ---
def simple_dashboard():
    st.title("🏠 Main Dashboard")
    
    st.markdown("### Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("👥 Add Employee", use_container_width=True):
            st.session_state.current_page = "Add Employee"
            st.rerun()
    
    with col2:
        if st.button("💰 Add Expense", use_container_width=True):
            st.session_state.current_page = "Add Expense"
            st.rerun()
    
    with col3:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.current_page = "View Reports"
            st.rerun()
    
    with col4:
        if st.button("💸 Pay Salary", use_container_width=True):
            st.session_state.current_page = "Pay Salary"
            st.rerun()
    
    st.markdown("---")
    
    # Recent activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👥 Employees")
        employees_df = get_all_employees()
        if not employees_df.empty:
            st.write(f"**Total Employees:** {len(employees_df)}")
            st.write(f"**Total Monthly Salary:** Rs. {employees_df['salary'].sum():,.2f}")
            for _, emp in employees_df.head(3).iterrows():
                st.write(f"• {emp['name']} - {emp['designation']}")
        else:
            st.info("No employees added yet")
    
    with col2:
        st.subheader("💰 Recent Expenses")
        try:
            conn = get_db_connection()
            if conn:
                expenses_df = pd.read_sql_query(
                    "SELECT description, amount FROM company_expenses ORDER BY expense_date DESC LIMIT 5",
                    conn
                )
                conn.close()
                if not expenses_df.empty:
                    total_expenses = expenses_df['amount'].sum()
                    st.write(f"**Total Expenses:** Rs. {total_expenses:,.2f}")
                    for _, exp in expenses_df.iterrows():
                        st.write(f"• {exp['description'][:30]} - Rs. {exp['amount']:,.0f}")
                else:
                    st.info("No expenses recorded")
            else:
                st.info("No expenses recorded")
        except:
            st.info("No expenses recorded")

def simple_add_employee():
    st.title("👥 Add New Employee")
    
    with st.form("simple_employee_form", clear_on_submit=True):
        st.subheader("Employee Information")
        
        name = st.text_input("📛 Full Name", placeholder="Enter employee name")
        designation = st.text_input("💼 Designation", placeholder="Enter job title")
        salary = st.number_input("💰 Monthly Salary (Rs.)", min_value=0, value=0, step=1000)
        
        st.subheader("Bank Details (Optional)")
        bank = st.text_input("🏦 Bank Name", placeholder="Bank name")
        account_title = st.text_input("📋 Account Title", placeholder="Account holder name")
        account_no = st.text_input("🔢 Account Number", placeholder="Account number")
        
        if st.form_submit_button("💾 Save Employee", use_container_width=True):
            if name and designation:
                try:
                    conn = get_db_connection()
                    if conn is None:
                        st.error("❌ Database connection failed")
                        return
                        
                    conn.execute(
                        """
                        INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (name, designation, salary, bank, account_title, account_no, str(date.today()))
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"✅ Employee '{name}' added successfully!")
                    clear_cache()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter at least Name and Designation")

def simple_add_expense():
    st.title("💰 Add New Expense")
    
    categories_df = get_all_categories()
    employees_df = get_all_employees()
    
    with st.form("simple_expense_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            description = st.text_input("📝 Description", placeholder="What is this expense for?")
            amount = st.number_input("💵 Amount (Rs.)", min_value=1, value=0, step=100)
            expense_date = st.date_input("📅 Date", date.today())
        
        with col2:
            # Simple category selection
            if not categories_df.empty:
                category_options = {row['id']: row['name'] for _, row in categories_df.iterrows()}
                category_id = st.selectbox("📂 Category", options=list(category_options.keys()), 
                                         format_func=lambda x: category_options[x])
            else:
                category_id = 1
            
            # Simple employee selection
            employee_options = [None]
            employee_names = {None: "💼 Company Expense (No employee)"}
            if not employees_df.empty:
                employee_options.extend([row['id'] for _, row in employees_df.iterrows()])
                employee_names.update({row['id']: f"👤 {row['name']}" for _, row in employees_df.iterrows()})
            
            employee_id = st.selectbox("👤 Employee", options=employee_options, format_func=lambda x: employee_names[x])
            
            is_advance = st.checkbox("💳 This is an advance payment")
        
        if st.form_submit_button("💾 Save Expense", use_container_width=True):
            if description and amount > 0:
                try:
                    conn = get_db_connection()
                    if conn is None:
                        st.error("❌ Database connection failed")
                        return
                        
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id, is_advance)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (description, amount, str(expense_date), category_id, employee_id, 1 if is_advance else 0)
                    )
                    
                    # If linked to employee, add to ledger
                    if employee_id is not None:
                        if is_advance:
                            # Advance - employee owes company
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                                VALUES (?, ?, ?, ?, 0, 1)
                                """,
                                (employee_id, str(expense_date), f"Advance: {description}", amount)
                            )
                        else:
                            # Expense claim - company owes employee
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                                VALUES (?, ?, ?, 0, ?, 0)
                                """,
                                (employee_id, str(expense_date), f"Expense: {description}", amount)
                            )
                    
                    conn.commit()
                    conn.close()
                    st.success("✅ Expense saved successfully!")
                    clear_cache()
                except Exception as e:
                    st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter description and amount")

def simple_pay_salary():
    st.title("💸 Pay Salary")
    
    employees_df = get_all_employees()
    if employees_df.empty:
        st.warning("👥 No employees found. Please add employees first.")
        return
    
    st.info("""
    **How to pay salary:**
    1. Select the salary month
    2. Select employees to pay
    3. Review and generate salary slips
    """)
    
    col1, col2 = st.columns(2)
    with col1:
        salary_month = st.date_input("📅 Salary Month", date.today().replace(day=1))
    
    st.subheader("👥 Select Employees")
    
    # Show all employees with checkboxes
    selected_employees = []
    for _, emp in employees_df.iterrows():
        if st.checkbox(f"{emp['name']} - {emp['designation']} (Rs. {emp['salary']:,.0f})", key=f"emp_{emp['id']}"):
            selected_employees.append(emp)
    
    if selected_employees:
        st.subheader("💰 Salary Summary")
        total_salary = sum(emp['salary'] for emp in selected_employees)
        st.write(f"**Total Salary to Pay:** Rs. {total_salary:,.2f}")
        
        if st.button("🖨️ Generate Salary Slips", use_container_width=True):
            # Simple salary slip generation
            try:
                pdf = SimplePDF()
                pdf.report_title = f"Salary Sheet - {salary_month.strftime('%B %Y')}"
                pdf.date_range_str = f"Generated on {date.today().strftime('%d %b %Y')}"
                pdf.add_page()
                
                # Simple table
                data = []
                for emp in selected_employees:
                    data.append({
                        'Employee': emp['name'],
                        'Designation': emp['designation'],
                        'Salary': f"Rs. {emp['salary']:,.2f}"
                    })
                
                df = pd.DataFrame(data)
                pdf.add_simple_table(df, total_salary)
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                
                st.download_button(
                    label="📥 Download Salary Sheet",
                    data=pdf_bytes,
                    file_name=f"Salary_{salary_month.strftime('%Y_%m')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
                st.success(f"✅ Salary slips generated for {len(selected_employees)} employees!")
                
            except Exception as e:
                st.error(f"❌ Error generating salary slips: {e}")

def simple_view_reports():
    st.title("📊 View Reports")
    
    tab1, tab2, tab3 = st.tabs(["📋 Employee Report", "💰 Expense Report", "🏦 Bank Details"])
    
    with tab1:
        st.subheader("👥 Employee Report")
        
        employees_df = get_all_employees()
        if not employees_df.empty:
            # Simple employee table
            display_df = employees_df[['name', 'designation', 'salary']].copy()
            display_df.columns = ['Name', 'Designation', 'Monthly Salary']
            
            st.dataframe(
                display_df.style.format({'Monthly Salary': 'Rs. {:,.2f}'}),
                use_container_width=True
            )
            
            total_salary = employees_df['salary'].sum()
            st.metric("💰 Total Monthly Salary", f"Rs. {total_salary:,.2f}")
            
            # Download button
            if st.button("📥 Download Employee List", use_container_width=True):
                pdf = SimplePDF()
                pdf.report_title = "Employee List"
                pdf.date_range_str = f"As of {date.today().strftime('%d %b %Y')}"
                pdf.add_page()
                pdf.add_simple_table(display_df, total_salary)
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1')
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name="Employee_List.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("👥 No employees found")
    
    with tab2:
        st.subheader("💰 Expense Report")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", date.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", date.today())
        
        if st.button("🔍 Show Expenses", use_container_width=True):
            try:
                conn = get_db_connection()
                if conn is None:
                    st.error("❌ Database connection failed")
                    return
                    
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
                conn.close()
                
                if not expenses_df.empty:
                    expenses_df = expenses_df.fillna("Company")
                    simple_df = expenses_df[['description', 'amount', 'expense_date', 'category']].copy()
                    simple_df.columns = ['Description', 'Amount', 'Date', 'Category']
                    
                    st.dataframe(
                        simple_df.style.format({'Amount': 'Rs. {:,.2f}'}),
                        use_container_width=True
                    )
                    
                    total_expenses = expenses_df['amount'].sum()
                    st.metric("💰 Total Expenses", f"Rs. {total_expenses:,.2f}")
                    
                    # Download button
                    pdf = SimplePDF()
                    pdf.report_title = "Expense Report"
                    pdf.date_range_str = f"From {start_date} to {end_date}"
                    pdf.add_page()
                    pdf.add_simple_table(simple_df, total_expenses)
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin-1')
                    st.download_button(
                        label="📥 Download Expense Report",
                        data=pdf_bytes,
                        file_name=f"Expense_Report_{start_date}_{end_date}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                else:
                    st.info("💸 No expenses found for this period")
                    
            except Exception as e:
                st.error(f"❌ Error loading expenses: {e}")
    
    with tab3:
        st.subheader("🏦 Employee Bank Details")
        
        employees_df = get_all_employees()
        if not employees_df.empty:
            bank_data = []
            for _, emp in employees_df.iterrows():
                if emp.get('bank') or emp.get('account_no'):
                    bank_data.append({
                        'Name': emp['name'],
                        'Bank': emp.get('bank', 'Not provided'),
                        'Account Title': emp.get('account_title', 'Not provided'),
                        'Account No': emp.get('account_no', 'Not provided')
                    })
            
            if bank_data:
                bank_df = pd.DataFrame(bank_data)
                st.dataframe(bank_df, use_container_width=True)
            else:
                st.info("🏦 No bank details available")
        else:
            st.info("👥 No employees found")

def simple_employee_advances():
    st.title("💳 Employee Advances")
    
    employees_df = get_all_employees()
    if employees_df.empty:
        st.warning("👥 No employees found")
        return
    
    st.info("""
    **Manage employee advances:**
    - Give advance to employee
    - View advance balances
    - Settle advances
    """)
    
    tab1, tab2 = st.tabs(["➕ Give Advance", "📊 View Advances"])
    
    with tab1:
        st.subheader("➕ Give Advance to Employee")
        
        with st.form("advance_form"):
            employee_options = {row['id']: row['name'] for _, row in employees_df.iterrows()}
            employee_id = st.selectbox("👤 Select Employee", options=list(employee_options.keys()), 
                                     format_func=lambda x: employee_options[x])
            
            amount = st.number_input("💵 Advance Amount (Rs.)", min_value=1, value=0, step=1000)
            description = st.text_input("📝 Purpose", placeholder="Reason for advance")
            advance_date = st.date_input("📅 Date", date.today())
            
            if st.form_submit_button("💾 Give Advance", use_container_width=True):
                if amount > 0 and description:
                    try:
                        conn = get_db_connection()
                        if conn is None:
                            st.error("❌ Database connection failed")
                            return
                            
                        cursor = conn.cursor()
                        # Add to company expenses
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, employee_id, is_advance)
                            VALUES (?, ?, ?, ?, ?, 1)
                            """,
                            (description, amount, str(advance_date), 4, employee_id)  # category_id 4 = Advance
                        )
                        
                        # Add to employee ledger as debit (employee owes company)
                        cursor.execute(
                            """
                            INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, is_advance)
                            VALUES (?, ?, ?, ?, 0, 1)
                            """,
                            (employee_id, str(advance_date), f"Advance: {description}", amount)
                        )
                        
                        conn.commit()
                        conn.close()
                        st.success("✅ Advance given successfully!")
                        clear_cache()
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.error("❌ Please enter amount and purpose")
    
    with tab2:
        st.subheader("📊 Employee Advance Balances")
        
        try:
            conn = get_db_connection()
            if conn is None:
                st.error("❌ Database connection failed")
                return
                
            advance_df = pd.read_sql_query(
                """
                SELECT 
                    e.name as employee_name,
                    SUM(CASE WHEN l.is_advance = 1 THEN l.debit - l.credit ELSE 0 END) as advance_balance
                FROM employees e
                LEFT JOIN employee_ledger l ON e.id = l.employee_id
                GROUP BY e.id, e.name
                HAVING advance_balance > 0
                ORDER BY advance_balance DESC
                """,
                conn
            )
            conn.close()
            
            if not advance_df.empty:
                st.dataframe(
                    advance_df.style.format({'advance_balance': 'Rs. {:,.2f}'}),
                    use_container_width=True
                )
                
                total_advances = advance_df['advance_balance'].sum()
                st.metric("💰 Total Outstanding Advances", f"Rs. {total_advances:,.2f}")
            else:
                st.info("✅ No outstanding advances")
                
        except Exception as e:
            st.error(f"❌ Error loading advances: {e}")

# --- Simple Main App ---
def main():
    st.set_page_config(
        page_title=f"{COMPANY_NAME} Simple HR System", 
        layout="wide",
        page_icon="💰",
        initial_sidebar_state="expanded"
    )
    
    # Simple CSS for better appearance
    st.markdown("""
    <style>
    .main-header {
        font-size: 2rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stButton button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-size: 16px;
    }
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox select {
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Initialize database
    init_db()
    
    # Simple sidebar
    st.sidebar.title(f"🏢 {COMPANY_NAME}")
    st.sidebar.markdown("---")
    
    # Simple navigation
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    menu_options = {
        "🏠 Dashboard": simple_dashboard,
        "👥 Add Employee": simple_add_employee,
        "💰 Add Expense": simple_add_expense,
        "💸 Pay Salary": simple_pay_salary,
        "📊 View Reports": simple_view_reports,
        "💳 Employee Advances": simple_employee_advances
    }
    
    selected_page = st.sidebar.radio("📋 Navigation", list(menu_options.keys()))
    st.session_state.current_page = selected_page
    
    st.sidebar.markdown("---")
    st.sidebar.info(DEVELOPER_INFO)
    
    # Show current page
    page_function = menu_options[selected_page]
    page_function()

if __name__ == "__main__":
    main()
