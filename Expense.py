import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
from fpdf import FPDF
import io

# --- Configuration ---
COMPANY_NAME = "Nutrion"
DEVELOPER_NAME = "DataNex Solution"
DEVELOPER_CONTACT = "+92320 7429422"
# You can host a logo online (e.g., on imgur) and paste the link here
COMPANY_LOGO_URL = "https://placehold.co/100x100/png?text=Nutrion" 

# --- Database Setup ---
DB_NAME = 'nutrion_app.db'

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False) # check_same_thread=False for Streamlit
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables if they don't exist."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Employee Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT,
            salary REAL DEFAULT 0,
            account_no TEXT,
            account_title TEXT,
            bank TEXT
        );
        """)
        
        # Expense Categories Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );
        """)
        
        # Company Expenses Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date DATE NOT NULL,
            category_id INTEGER,
            description TEXT,
            amount REAL NOT NULL,
            employee_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id),
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        );
        """)
        
        # Employee Ledger Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_date DATE NOT NULL,
            employee_id INTEGER NOT NULL,
            description TEXT,
            credit REAL DEFAULT 0,
            debit REAL DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        );
        """)
        
        conn.commit()

# --- PDF Generation Utility ---
class PDF(FPDF):
    """Custom PDF class with header and footer."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""

    def header(self):
        # Add Logo
        # Use a placeholder if no real logo is provided
        try:
            # self.image(COMPANY_LOGO_URL, 10, 8, 25) # Requires internet
            self.set_font('Arial', 'B', 10)
            self.cell(30, 25, '[Logo]', 1, 0, 'C') # Placeholder
        except Exception as e:
            self.set_font('Arial', 'B', 10)
            self.cell(30, 25, '[Logo]', 1, 0, 'C') # Placeholder

        self.set_x(40) # Position to the right of the logo
        self.set_font('Arial', 'B', 18)
        self.cell(0, 10, COMPANY_NAME, 0, 1, 'L')
        self.set_x(40)
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self.report_title, 0, 1, 'L')
        
        # Right aligned info
        header_y_pos = self.get_y()
        self.set_y(10) # Reset Y to top for right-aligned block
        if self.date_range_str:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 5, self.date_range_str, 0, 1, 'R')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 1, 'R')
        
        self.set_y(header_y_pos + 5) # Reset Y to below header
        self.ln(5)

    def footer(self):
        self.set_y(-25) # Position 2.5 cm from bottom
        self.set_font('Arial', '', 10)
        
        # Add signature lines
        page_width = self.w - 2 * self.l_margin
        line_width = page_width / 2.5 # Adjust as needed
        
        self.cell(line_width, 7, "Prepared by: _______________", 0, 0, 'L')
        self.cell(page_width - line_width, 7, "Approved by: _______________", 0, 1, 'R')
        
        self.set_y(-15) # Position 1.5 cm from bottom
        self.set_font('Arial', 'I', 8)
        self.cell(0, 5, f'Page {self.page_no()}', 0, 0, 'C')
        self.cell(0, 5, f'Developed by {DEVELOPER_NAME} ({DEVELOPER_CONTACT})', 0, 1, 'R')

    def create_table_from_df(self, df, totals_cols=None):
        """
        Creates a table in the PDF from a Pandas DataFrame.
        Optionally adds a "GRAND TOTAL" row.
        """
        if df.empty:
            self.cell(0, 10, "No data available for the selected criteria.", 0, 1, 'C')
            return

        self.set_fill_color(224, 235, 255) # Light blue header
        self.set_text_color(0)
        self.set_draw_color(128, 128, 128) # Gray border
        self.set_font('Arial', 'B', 10)
        
        # Calculate widths (better distribution)
        page_width = self.w - 2 * self.l_margin
        col_widths = [page_width * (1/len(df.columns))] * len(df.columns)
        
        # Header
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], 10, str(col).upper(), 1, 0, 'C', fill=True)
        self.ln()

        # Data
        self.set_font('Arial', '', 9)
        self.set_fill_color(245, 245, 245) # Light gray for alternating rows
        fill = False
        
        # Initialize totals
        totals = {col: 0 for col in df.columns if totals_cols and col.lower() in [tc.lower() for tc in totals_cols]}

        for index, row in df.iterrows():
            for i, col in enumerate(df.columns):
                cell_value = str(row[col])
                self.cell(col_widths[i], 10, cell_value, 1, 0, 'L', fill=fill)
                
                # Update totals
                if col in totals:
                    try:
                        totals[col] += pd.to_numeric(row[col])
                    except:
                        pass # Ignore if value is not numeric
            self.ln()
            fill = not fill
            
        # Add totals row
        if totals_cols and totals:
            self.set_font('Arial', 'B', 10)
            self.set_fill_color(210, 210, 210) # Gray for total row
            
            # Find first non-total column to put "GRAND TOTAL"
            first_col_index = -1
            for i, col in enumerate(df.columns):
                 if col not in totals:
                     first_col_index = i
                     self.cell(col_widths[i], 10, "GRAND TOTAL", 1, 0, 'R', fill=True)
                     break
            
            # Print other cells
            for i, col in enumerate(df.columns):
                if i == first_col_index:
                    continue
                
                if col in totals:
                    self.cell(col_widths[i], 10, f"{totals[col]:,.2f}", 1, 0, 'L', fill=True)
                else:
                    self.cell(col_widths[i], 10, "", 1, 0, 'L', fill=True)
            self.ln()


def generate_pdf_report(df, title, date_range=None, orientation='L', totals_cols=None):
    """Generates a PDF report from a DataFrame."""
    pdf = PDF(orientation=orientation, unit='mm', format='A4')
    pdf.report_title = title
    
    if date_range and len(date_range) == 2:
        pdf.date_range_str = f"For period: {date_range[0]} to {date_range[1]}"
        
    pdf.add_page()
    pdf.create_table_from_df(df, totals_cols=totals_cols)
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')

# --- NEW FUNCTION for Individual Salary Slips ---
def generate_individual_slip_pdf(emp_details, ledger_df, slip_month, total_credits, total_debits, net_salary):
    """Generates a formatted PDF for a single employee's salary slip."""
    pdf = PDF(orientation='P', unit='mm', format='A4')
    pdf.report_title = f"Salary Slip - {slip_month.strftime('%B %Y')}"
    pdf.date_range_str = "" # No date range needed
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Employee: {emp_details['name']}", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"Designation: {emp_details['designation']}", 0, 1, 'L')
    pdf.cell(0, 7, f"Base Salary: Rs. {emp_details['salary']:,.2f}", 0, 1, 'L')
    pdf.ln(5)

    # --- Earnings ---
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(224, 235, 255)
    pdf.cell(0, 10, "Earnings & Deductions", 1, 1, 'C', fill=True)
    
    col_width = (pdf.w - 2 * pdf.l_margin) / 3
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width * 1.5, 7, "Description", 1, 0, 'C')
    pdf.cell(col_width * 0.75, 7, "Credits (Rs.)", 1, 0, 'C')
    pdf.cell(col_width * 0.75, 7, "Debits (Rs.)", 1, 1, 'C')

    pdf.set_font('Arial', '', 9)
    if ledger_df.empty:
        pdf.cell(0, 7, "No ledger activity found for this month.", 1, 1, 'C')
    else:
        for _, row in ledger_df.iterrows():
            pdf.cell(col_width * 1.5, 7, str(row['description']), 1, 0, 'L')
            pdf.cell(col_width * 0.75, 7, f"{row['credit']:,.2f}" if row['credit'] > 0 else "0.00", 1, 0, 'R')
            pdf.cell(col_width * 0.75, 7, f"{row['debit']:,.2f}" if row['debit'] > 0 else "0.00", 1, 1, 'R')

    # --- Totals ---
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(col_width * 1.5, 7, "Total", 1, 0, 'R')
    pdf.cell(col_width * 0.75, 7, f"{total_credits:,.2f}", 1, 0, 'R')
    pdf.cell(col_width * 0.75, 7, f"{total_debits:,.2f}", 1, 1, 'R')

    # --- Net Salary ---
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(210, 210, 210)
    pdf.cell(col_width * 1.5, 10, "Net Salary Payable", 1, 0, 'R', fill=True)
    pdf.cell(col_width * 1.5, 10, f"Rs. {net_salary:,.2f}", 1, 1, 'R', fill=True)
    
    # Add bank details
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 7, "Bank Details", 0, 1, 'L')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 7, f"  Bank: {emp_details['bank']}", 0, 1, 'L')
    pdf.cell(0, 7, f"  Account Title: {emp_details['account_title']}", 0, 1, 'L')
    pdf.cell(0, 7, f"  Account No: {emp_details['account_no']}", 0, 1, 'L')

    return pdf.output(dest='S').encode('latin-1')


# --- Helper Functions ---

# NEW/REFACTORED HELPER
@st.cache_data
def create_excel_template(df, sheet_name='Sheet1'):
    """Creates an in-memory Excel file from a DataFrame."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return output.getvalue()


@st.cache_data(ttl=600) # Cache for 10 minutes
def get_all_employees():
    """Fetches all employees for dropdowns."""
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT id, name FROM employees ORDER BY name", conn)
        return df

@st.cache_data(ttl=600) # Cache for 10 minutes
def get_all_categories():
    """Fetches all expense categories for dropdowns."""
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT id, name FROM expense_categories ORDER BY name", conn)
        return df

# --- Page: Dashboard (New) ---
def page_dashboard():
    st.header(f"Welcome to {COMPANY_NAME} Dashboard")
    st.info("""
    **How to use this system:**
    - **Navigation:** Use the menu on the left to move between pages.
    - **Data Entry:** Use forms (like "Log New Expense") to add new data.
    - **Edit/Delete:** Use `st.data_editor` tables (on Employee and Category pages) or selection forms (on Expense page) to manage existing data.
    - **Reports:** Download professional PDF reports from the 'Reporting', 'Salary', and 'Ledger' pages.
    """)
    
    with get_db_connection() as conn:
        total_employees = conn.execute("SELECT COUNT(*) FROM employees").fetchone()[0]
        
        first_day_month = date.today().replace(day=1)
        total_expense_month = conn.execute(
            "SELECT SUM(amount) FROM company_expenses WHERE expense_date >= ?",
            (first_day_month,)
        ).fetchone()[0]
        
        total_salary_paid = conn.execute(
            "SELECT SUM(debit) FROM employee_ledger WHERE description = 'Salary Paid' AND entry_date >= ?",
             (first_day_month,)
        ).fetchone()[0] # Note: This requires a "Salary Paid" entry

    cols = st.columns(3)
    with cols[0]:
        st.metric("Total Employees", f"{total_employees}")
    with cols[1]:
        st.metric("Total Expenses (This Month)", f"Rs. {total_expense_month or 0:,.2f}")
    with cols[2]:
        st.metric("Total Salary Paid (This Month)", f"Rs. {total_salary_paid or 0:,.2f}")

    st.divider()

    st.subheader("Recent Activity")
    cols = st.columns(2)
    with get_db_connection() as conn:
        recent_expenses = pd.read_sql_query("""
            SELECT ce.expense_date, ec.name as Category, ce.description, ce.amount
            FROM company_expenses ce
            JOIN expense_categories ec ON ce.category_id = ec.id
            ORDER BY ce.expense_date DESC
            LIMIT 5
        """, conn)

        recent_ledger = pd.read_sql_query("""
            SELECT el.entry_date, e.name as Employee, el.description, el.credit, el.debit
            FROM employee_ledger el
            JOIN employees e ON el.employee_id = e.id
            ORDER BY el.entry_date DESC
            LIMIT 5
        """, conn)

    with cols[0]:
        st.markdown("**Recent Expenses**")
        st.dataframe(recent_expenses, use_container_width=True)
    
    with cols[1]:
        st.markdown("**Recent Ledger Entries**")
        st.dataframe(recent_ledger, use_container_width=True)


# --- Page: Employee Management (Requirement 4) ---
def page_employee_management():
    st.header("Employee Management")
    st.info("Add, edit, or remove employee records. All data is saved automatically.")
    
    with st.expander("Add New Employee"):
        with st.form("new_employee_form", clear_on_submit=True):
            cols = st.columns(3)
            with cols[0]:
                name = st.text_input("Employee Name*")
                designation = st.text_input("Designation")
            with cols[1]:
                salary = st.number_input("Base Salary", min_value=0.0, step=100.0)
                bank = st.text_input("Bank Name")
            with cols[2]:
                account_no = st.text_input("Account No.")
                account_title = st.text_input("Account Title")
            
            submitted = st.form_submit_button("Add Employee")
            if submitted:
                if not name:
                    st.error("Employee Name is required.")
                else:
                    try:
                        with get_db_connection() as conn:
                            conn.execute(
                                "INSERT INTO employees (name, designation, salary, account_no, account_title, bank) VALUES (?, ?, ?, ?, ?, ?)",
                                (name, designation, salary, account_no, account_title, bank)
                            )
                            conn.commit()
                        st.success(f"Employee '{name}' added successfully.")
                        st.cache_data.clear() # Clear cache
                    except Exception as e:
                        st.error(f"Error adding employee: {e}")

    st.subheader("Edit or Delete Employees (CRUD)")
    st.info("You can directly edit, add, or delete employee records in the table below. Changes are saved automatically.")
    
    try:
        with get_db_connection() as conn:
            df_employees = pd.read_sql_query("SELECT * FROM employees", conn, index_col="id")
        
        # Use st.data_editor for full CRUD
        edited_df = st.data_editor(
            df_employees,
            num_rows="dynamic",
            use_container_width=True,
            key="employee_editor"
        )
        
        # Check for changes and update database
        if not edited_df.equals(df_employees):
            with get_db_connection() as conn:
                cursor = conn.cursor()
                
                # Find deleted rows
                deleted_ids = set(df_employees.index) - set(edited_df.index)
                for emp_id in deleted_ids:
                    # Add checks for related data before deleting
                    cursor.execute("DELETE FROM employees WHERE id = ?", (int(emp_id),))
                
                # Find added/updated rows
                for emp_id, row in edited_df.iterrows():
                    if emp_id not in df_employees.index:
                        # New row
                        cursor.execute(
                            "INSERT INTO employees (name, designation, salary, account_no, account_title, bank) VALUES (?, ?, ?, ?, ?, ?)",
                            (row['name'], row['designation'], row['salary'], row['account_no'], row['account_title'], row['bank'])
                        )
                    elif not df_employees.loc[emp_id].equals(row):
                        # Updated row
                        cursor.execute(
                            "UPDATE employees SET name=?, designation=?, salary=?, account_no=?, account_title=?, bank=? WHERE id=?",
                            (row['name'], row['designation'], row['salary'], row['account_no'], row['account_title'], row['bank'], int(emp_id))
                        )
                conn.commit()
            st.success("Changes saved!")
            st.cache_data.clear() # Clear cache
            st.rerun() # Refresh to show clean state

    except Exception as e:
        st.error(f"Error loading employee data: {e}")

# --- Page: Expense Management (Requirements 3, 10, 11) ---
def page_expense_management():
    st.header("Company Expense Management")

    tab1, tab2, tab3 = st.tabs(["Log New Expense", "Manage Logged Expenses (CRUD)", "Manage Categories"])

    # --- Manage Categories (Req 3, 10) ---
    with tab3:
        st.subheader("Manage Expense Categories")
        with st.form("new_category_form", clear_on_submit=True):
            cols = st.columns([3, 1])
            with cols[0]:
                category_name = st.text_input("New Category Name")
            with cols[1]:
                st.markdown("<br>", unsafe_allow_html=True)
                add_cat_submitted = st.form_submit_button("Add Category")
                
        if add_cat_submitted and category_name:
            try:
                with get_db_connection() as conn:
                    conn.execute("INSERT INTO expense_categories (name) VALUES (?)", (category_name,))
                    conn.commit()
                st.success(f"Category '{category_name}' added.")
                st.cache_data.clear()
            except sqlite3.IntegrityError:
                st.error(f"Category '{category_name}' already exists.")
            except Exception as e:
                st.error(f"Error: {e}")

        try:
            with get_db_connection() as conn:
                df_categories = pd.read_sql_query("SELECT * FROM expense_categories", conn, index_col="id")
            
            st.info("Edit or delete expense categories directly.")
            edited_cats_df = st.data_editor(
                df_categories,
                num_rows="dynamic",
                use_container_width=True,
                key="category_editor"
            )
            
            if not edited_cats_df.equals(df_categories):
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    # Find deleted
                    deleted_ids = set(df_categories.index) - set(edited_cats_df.index)
                    for cat_id in deleted_ids:
                        cursor.execute("DELETE FROM expense_categories WHERE id = ?", (int(cat_id),))
                    
                    # Find added/updated
                    for cat_id, row in edited_cats_df.iterrows():
                        if cat_id not in df_categories.index:
                            cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (row['name'],))
                        elif not df_categories.loc[cat_id].equals(row):
                            cursor.execute("UPDATE expense_categories SET name=? WHERE id=?", (row['name'], int(cat_id)))
                    conn.commit()
                st.success("Categories updated!")
                st.cache_data.clear()
                st.rerun()

            # Requirement 10: Download Category Sheet
            st.divider()
            if not df_categories.empty:
                pdf_bytes = generate_pdf_report(
                    df_categories.reset_index(), # Show ID in PDF
                    title="Expense Category List",
                    orientation='P'
                    # No totals_cols needed here
                )
                st.download_button(
                    label="Download Category List as PDF (Req 10)",
                    data=pdf_bytes,
                    file_name="Expense_Categories.pdf",
                    mime="application/pdf"
                )

        except Exception as e:
            st.error(f"Error loading categories: {e}")


    # --- Log New Expense (Req 3, 11) ---
    with tab1:
        st.subheader("Log New Company Expense")
        employees_df = get_all_employees()
        categories_df = get_all_categories()
        
        # Create dictionaries for selectbox
        employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
        category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
        
        if not category_list:
            st.warning("Please add at least one expense category (in Tab 3) to log expenses.")
            return

        with st.form("new_expense_form", clear_on_submit=True):
            cols = st.columns(3)
            with cols[0]:
                expense_date = st.date_input("Expense Date", date.today())
            with cols[1]:
                category_id = st.selectbox("Category", options=list(category_list.keys()), format_func=lambda x: category_list[x])
            with cols[2]:
                amount = st.number_input("Amount", min_value=0.01, step=0.01)
            
            description = st.text_area("Description")
            
            # Requirement 11: Link expense to employee ledger
            st.info("Requirement 11: Deduct from Employee Ledger?")
            link_to_employee = st.checkbox("Deduct this expense from an employee's ledger?")
            employee_id = None
            if link_to_employee:
                employee_id = st.selectbox("Select Employee", options=[None] + list(employee_list.keys()), format_func=lambda x: "Select..." if x is None else employee_list[x])
            
            expense_submitted = st.form_submit_button("Log Expense")
            
            if expense_submitted:
                if not category_id or not amount:
                    st.error("Date, Category, and Amount are required.")
                elif link_to_employee and not employee_id:
                    st.error("Please select an employee to deduct from.")
                else:
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            # 1. Log the company expense
                            cursor.execute(
                                "INSERT INTO company_expenses (expense_date, category_id, description, amount, employee_id) VALUES (?, ?, ?, ?, ?)",
                                (expense_date, category_id, description, amount, employee_id)
                            )
                            
                            # 2. (Req 11) If linked, add a DEBIT to employee ledger
                            if link_to_employee and employee_id:
                                ledger_desc = f"Expense deduction: {category_list[category_id]} - {description}"
                                cursor.execute(
                                    "INSERT INTO employee_ledger (entry_date, employee_id, description, debit) VALUES (?, ?, ?, ?)",
                                    (expense_date, employee_id, ledger_desc, amount)
                                )
                            
                            conn.commit()
                        st.success("Expense logged successfully.")
                        if link_to_employee and employee_id:
                            st.info(f"Amount of {amount} deducted from {employee_list[employee_id]}'s ledger.")
                    except Exception as e:
                        st.error(f"Error logging expense: {e}")

    # --- View/Edit/Delete Company Expenses (Req 4) ---
    with tab2:
        st.subheader("Manage Logged Expenses (CRUD)")
        try:
            with get_db_connection() as conn:
                query = """
                SELECT 
                    ce.id, 
                    ce.expense_date, 
                    ec.name AS category, 
                    ce.description, 
                    ce.amount,
                    e.name AS employee_deducted,
                    ce.category_id,
                    ce.employee_id
                FROM company_expenses ce
                LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                LEFT JOIN employees e ON ce.employee_id = e.id
                ORDER BY ce.expense_date DESC
                """
                df_expenses = pd.read_sql_query(query, conn)
            
            if df_expenses.empty:
                st.info("No expenses logged yet.")
                return

            # Create a user-friendly list for selection
            expense_options = {
                row['id']: f"ID {row['id']} | {row['expense_date']} | {row['category']} | {row['description'][:20]}... | Rs. {row['amount']}"
                for index, row in df_expenses.iterrows()
            }
            expense_options[None] = "Select an expense to edit/delete..."
            
            selected_expense_id = st.selectbox(
                "Select Expense", 
                options=expense_options.keys(),
                format_func=lambda x: expense_options[x],
                index=len(expense_options)-1 # Default to "Select..."
            )

            if selected_expense_id:
                # Get full details
                expense_details = df_expenses[df_expenses['id'] == selected_expense_id].iloc[0]
                
                # Get category list for form
                categories_df = get_all_categories()
                category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
                cat_ids = list(category_list.keys())
                
                # --- FIX for deleted category bug ---
                # Check if the expense's category still exists
                current_cat_id = expense_details['category_id']
                if pd.notna(current_cat_id) and current_cat_id not in cat_ids:
                    # The category was deleted!
                    st.error(f"Error: The original category (ID: {current_cat_id}) for this expense was deleted. Please select a new, valid category.")
                    # Add the (now invalid) ID to the list just to prevent a crash, but default to the first valid one
                    cat_ids.append(current_cat_id)
                    category_list[current_cat_id] = f"INVALID CATEGORY (ID: {current_cat_id})"
                    default_index = 0 
                elif pd.notna(current_cat_id):
                    default_index = cat_ids.index(current_cat_id)
                else:
                    # Expense had no category to begin with
                    default_index = 0
                # --- END FIX ---
                
                with st.form("edit_expense_form"):
                    st.markdown(f"**Editing Expense ID: {selected_expense_id}**")
                    
                    # Convert date from string if needed
                    try:
                        edit_date = datetime.strptime(expense_details['expense_date'], "%Y-%m-%d").date()
                    except:
                        edit_date = expense_details['expense_date']

                    cols = st.columns(3)
                    with cols[0]:
                        edit_expense_date = st.date_input("Expense Date", value=edit_date)
                    with cols[1]:
                        edit_category_id = st.selectbox("Category", 
                            options=cat_ids, 
                            format_func=lambda x: category_list[x], 
                            index=default_index # Use the safe default_index
                        )
                    with cols[2]:
                        edit_amount = st.number_input("Amount", min_value=0.01, step=0.01, value=expense_details['amount'])
                    
                    edit_description = st.text_area("Description", value=expense_details['description'])
                    
                    st.warning("Editing a linked expense does NOT automatically update the employee ledger. Please make a manual correction in the Employee Ledger page if you change the amount.")

                    form_cols = st.columns([1, 1, 3])
                    with form_cols[0]:
                        update_submitted = st.form_submit_button("Update Expense")
                    with form_cols[1]:
                        delete_submitted = st.form_submit_button("Delete Expense", type="primary")

                    if update_submitted:
                        try:
                            with get_db_connection() as conn:
                                conn.execute(
                                    "UPDATE company_expenses SET expense_date=?, category_id=?, description=?, amount=? WHERE id=?",
                                    (edit_expense_date, edit_category_id, edit_description, edit_amount, selected_expense_id)
                                )
                                conn.commit()
                            st.success(f"Expense ID {selected_expense_id} updated.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating: {e}")
                    
                    if delete_submitted:
                        try:
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                # Start transaction
                                cursor.execute("BEGIN TRANSACTION;")
                                
                                # 1. Delete the expense
                                cursor.execute("DELETE FROM company_expenses WHERE id = ?", (selected_expense_id,))
                                
                                # 2. (Req 11) If linked, add a REVERSING (CREDIT) entry to employee ledger
                                if pd.notna(expense_details['employee_id']):
                                    reversal_desc = f"Reversal: Deleted expense ID {selected_expense_id} ({expense_details['description']})"
                                    cursor.execute(
                                        "INSERT INTO employee_ledger (entry_date, employee_id, description, credit) VALUES (?, ?, ?, ?)",
                                        (date.today(), expense_details['employee_id'], reversal_desc, expense_details['amount'])
                                    )
                                
                                # Commit transaction
                                cursor.execute("COMMIT;")
                            st.success(f"Expense ID {selected_expense_id} deleted.")
                            if pd.notna(expense_details['employee_id']):
                                st.info(f"Reversing credit of {expense_details['amount']} posted to {expense_details['employee_deducted']}'s ledger.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting: {e}")
                            conn.rollback() # Rollback on error
            
            st.divider()
            st.markdown("**All Logged Expenses**")
            st.dataframe(df_expenses.drop(columns=['category_id', 'employee_id']), use_container_width=True)

        except Exception as e:
            st.error(f"Error loading expenses: {e}")

# --- Page: Salary Management (Requirement 2) ---
def page_salary_management():
    st.header("Salary Management")
    st.help("""
    Follow these steps to process monthly salaries:
    1.  **Generate Monthly Salary Credits:** Run this first. It adds the 'Base Salary' as a credit to each employee's ledger for the month.
    2.  **View & Download Salary Sheet:** After credits are generated (and any deductions are logged), run this to see the final salary calculation for all employees and download the official PDF sheet.
    3.  **Generate Individual Salary Slip:** Use this to get a detailed PDF slip for a single employee.
    """)

    st.subheader("1. Generate Monthly Salary Credits")
    st.info("This adds a 'Credit' entry (Base Salary) to each employee's ledger for the selected month. Run this first.")

    cols = st.columns(2)
    with cols[0]:
        salary_month_credit = st.date_input("Salary Month", date.today().replace(day=1), key="salary_month_credit")
    
    if st.button("Generate Salary Credits"):
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                employees = cursor.execute("SELECT id, name, salary FROM employees").fetchall()
                
                first_day = salary_month_credit.replace(day=1)
                
                added_count = 0
                for emp in employees:
                    # Check if 'Salary Credit' already exists for this month
                    exists = cursor.execute(
                        "SELECT 1 FROM employee_ledger WHERE employee_id = ? AND description = 'Monthly Salary' AND strftime('%Y-%m', entry_date) = ?",
                        (emp['id'], first_day.strftime('%Y-%m'))
                    ).fetchone()
                    
                    if not exists:
                        cursor.execute(
                            "INSERT INTO employee_ledger (entry_date, employee_id, description, credit) VALUES (?, ?, ?, ?)",
                            (first_day, emp['id'], 'Monthly Salary', emp['salary'])
                        )
                        added_count += 1
                conn.commit()
            st.success(f"Salary credits generated for {added_count} employees for {salary_month_credit.strftime('%B %Y')}.")
            if added_count == 0:
                st.info("Salary credits seem to have been already generated for this month.")
        except Exception as e:
            st.error(f"Error generating salary credits: {e}")

    st.divider()
    st.subheader("2. View & Download Monthly Salary Sheet")
    st.info("Calculates the final salary sheet based on all ledger entries for the selected month.")
    
    cols = st.columns(2)
    with cols[0]:
        salary_month_sheet = st.date_input("Salary Month", date.today().replace(day=1), key="salary_month_sheet")

    if st.button("View & Download Salary Sheet"):
        first_day = salary_month_sheet.replace(day=1)
        last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
        
        # *** IMPROVED QUERY ***
        query = f"""
        WITH MonthLedger AS (
            SELECT
                employee_id,
                SUM(credit) AS total_credits,
                SUM(debit) AS total_deductions
            FROM employee_ledger
            WHERE entry_date BETWEEN '{first_day}' AND '{last_day}'
            GROUP BY employee_id
        )
        SELECT
            e.name AS "Employee Name",
            e.designation AS "Designation",
            e.salary AS "Base Salary",
            COALESCE(ml.total_credits, 0) AS "Total Credits",
            COALESCE(ml.total_deductions, 0) AS "Total Deductions",
            (COALESCE(ml.total_credits, 0) - COALESCE(ml.total_deductions, 0)) AS "Net Salary",
            e.account_no AS "Account No.",
            e.account_title AS "Account Title",
            e.bank AS "Bank"
        FROM employees e
        LEFT JOIN MonthLedger ml ON e.id = ml.employee_id;
        """
        
        try:
            with get_db_connection() as conn:
                df_salary_sheet = pd.read_sql_query(query, conn)
            
            st.dataframe(df_salary_sheet, use_container_width=True)
            
            # Download PDF (Req 2)
            pdf_bytes = generate_pdf_report(
                df_salary_sheet, 
                title=f"Salary Sheet - {salary_month_sheet.strftime('%B %Y')}",
                totals_cols=['Base Salary', 'Total Credits', 'Total Deductions', 'Net Salary']
            )
            st.download_button(
                label="Download Salary Sheet as PDF",
                data=pdf_bytes,
                file_name=f"Salary_Sheet_{salary_month_sheet.strftime('%Y_%m')}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating salary sheet: {e}")

    st.divider()

    # --- Individual Salary Slip (Req 2) ---
    st.subheader("3. Generate Individual Salary Slip")
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    # *** ADDED CHECK FOR EMPTY EMPLOYEE LIST ***
    if not employee_list:
        st.warning("Cannot generate slip: No employees found in the system. Please add employees first.", icon="⚠️")
        return # Stop this part of the page from rendering
    
    # --- START: CORRECTED CODE FOR INDIVIDUAL SLIP ---
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
            # 1. Get employee details
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

            # 2. Get ledger entries for the month
            first_day = slip_month.replace(day=1)
            last_day = (first_day.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)
            
            with get_db_connection() as conn:
                ledger_df = pd.read_sql_query(
                    f"""
                    SELECT description, credit, debit 
                    FROM employee_ledger 
                    WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
                    ORDER BY entry_date
                    """, 
                    conn, 
                    params=(selected_emp_id, first_day, last_day)
                )

            # 3. Calculate totals
            total_credits = ledger_df['credit'].sum()
            total_debits = ledger_df['debit'].sum()
            net_salary = total_credits - total_debits

            # 4. Generate the new PDF
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
            st.error("Please ensure the selected employee exists and data is available.")
    
    # --- END: CORRECTED CODE ---


# --- Page: Employee Ledger (Requirement 5) ---
def page_employee_ledger():
        "name", "designation", "salary", "account_no", "account_title", "bank"
    ])
    
    template_categories_df = pd.DataFrame(columns=[
        "name" # Simple, just the category name
    ])
    
    template_expenses_df = pd.DataFrame(columns=[
        "expense_date (YYYY-MM-DD)", 
        "category_name", # Will be mapped to category_id
        "description", 
        "amount", 
        "employee_name (optional)" # Will be mapped to employee_id
    ])
    
    template_ledger_df = pd.DataFrame(columns=[
        "entry_date (YYYY-MM-DD)",
        "employee_name", # Will be mapped to employee_id
        "description",
        "credit",
        "debit"
    ])

    tab1, tab2, tab3, tab4 = st.tabs(["Import Employees", "Import Expense Categories", "Import Company Expenses", "Import Ledger Entries"])

    # --- TAB 1: EMPLOYEES ---
    with tab1:
        st.subheader("1. Download Employee Template")
        st.markdown("Download the template, fill it out, and upload it below.")
        st.download_button(
            label="Download Employee Template (.xlsx)",
            data=create_excel_template(template_employees_df, 'Employees'),
            file_name="employee_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("2. Upload Employee Template")
        uploaded_file_emp = st.file_uploader("Choose an Employee file", type=["xlsx", "xls"], key="emp_uploader")
        
        if uploaded_file_emp is not None:
            try:
                df_import = pd.read_excel(uploaded_file_emp, dtype=str) # Import all as string
                df_import['salary'] = pd.to_numeric(df_import['salary'], errors='coerce').fillna(0)
                
                st.dataframe(df_import)
                
                if list(df_import.columns) != list(template_employees_df.columns):
                    st.error("File columns do not match the template.")
                else:
                    if st.button("Import Employees"):
                        try:
                            with get_db_connection() as conn:
                                df_import.to_sql('employees', conn, if_exists='append', index=False)
                            st.success(f"Successfully imported {len(df_import)} employee records.")
                            st.cache_data.clear() # Clear employee cache
                        except Exception as e:
                            st.error(f"Error during import: {e}")
                            
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # --- TAB 2: EXPENSE CATEGORIES ---
    with tab2:
        st.subheader("1. Download Category Template")
        st.download_button(
            label="Download Expense Category Template (.xlsx)",
            data=create_excel_template(template_categories_df, 'Categories'),
            file_name="category_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("2. Upload Category Template")
        uploaded_file_cat = st.file_uploader("Choose a Category file", type=["xlsx", "xls"], key="cat_uploader")
        
        if uploaded_file_cat is not None:
            try:
                df_import_cat = pd.read_excel(uploaded_file_cat)
                
                st.dataframe(df_import_cat)
                
                if list(df_import_cat.columns) != list(template_categories_df.columns):
                    st.error("File columns do not match the template.")
                else:
                    if st.button("Import Categories"):
                        try:
                            with get_db_connection() as conn:
                                # Use to_sql, database UNIQUE constraint will handle duplicates
                                df_import_cat.to_sql('expense_categories', conn, if_exists='append', index=False)
                            st.success(f"Successfully imported {len(df_import_cat)} categories. Duplicates were ignored.")
                            st.cache_data.clear() # Clear category cache
                        except Exception as e:
                            st.error(f"Error during import: {e}")
                            
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # --- TAB 3: COMPANY EXPENSES ---
    with tab3:
        st.warning("Please make sure all Employees and Categories are imported *before* importing expenses.")
        st.subheader("1. Download Expense Template")
        st.download_button(
            label="Download Company Expense Template (.xlsx)",
            data=create_excel_template(template_expenses_df, 'Expenses'),
            file_name="expense_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("2. Upload Expense Template")
        uploaded_file_exp = st.file_uploader("Choose an Expense file", type=["xlsx", "xls"], key="exp_uploader")
        
        if uploaded_file_exp is not None:
            try:
                # Get mapping tables
                emp_df = get_all_employees()
                cat_df = get_all_categories()
                emp_map = {row['name']: row['id'] for _, row in emp_df.iterrows()}
                cat_map = {row['name']: row['id'] for _, row in cat_df.iterrows()}

                df_import_exp = pd.read_excel(uploaded_file_exp)
                
                # Process data
                df_import_exp['category_id'] = df_import_exp['category_name'].map(cat_map)
                df_import_exp['employee_id'] = df_import_exp['employee_name (optional)'].map(emp_map)
                
                # Clean numeric and date cols
                df_import_exp['amount'] = pd.to_numeric(df_import_exp['amount'], errors='coerce').fillna(0)
                df_import_exp['expense_date'] = pd.to_datetime(df_import_exp['expense_date (YYYY-MM-DD)']).dt.date
                
                st.dataframe(df_import_exp)
                
                # Check for errors
                failed_cats = df_import_exp[df_import_exp['category_id'].isna()]['category_name'].unique()
                if len(failed_cats) > 0:
                    st.error(f"Error: The following categories were not found: {', '.join(failed_cats)}. Please add them first.")
                else:
                    if st.button("Import Company Expenses"):
                        df_to_insert = df_import_exp[['expense_date', 'category_id', 'description', 'amount', 'employee_id']]
                        try:
                            with get_db_connection() as conn:
                                df_to_insert.to_sql('company_expenses', conn, if_exists='append', index=False)
                            st.success(f"Successfully imported {len(df_to_insert)} expenses.")
                        except Exception as e:
                            st.error(f"Error during import: {e}")

            except Exception as e:
                st.error(f"Error reading file or processing data: {e}")

    # --- TAB 4: EMPLOYEE LEDGER ENTRIES ---
    with tab4:
        st.warning("Please make sure all Employees are imported *before* importing ledger entries.")
        st.subheader("1. Download Ledger Template")
        st.download_button(
            label="Download Employee Ledger Template (.xlsx)",
            data=create_excel_template(template_ledger_df, 'Ledger'),
            file_name="ledger_import_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("2. Upload Ledger Template")
        uploaded_file_led = st.file_uploader("Choose a Ledger file", type=["xlsx", "xls"], key="led_uploader")
        
        if uploaded_file_led is not None:
            try:
                # Get mapping tables
                emp_df = get_all_employees()
                emp_map = {row['name']: row['id'] for _, row in emp_df.iterrows()}

                df_import_led = pd.read_excel(uploaded_file_led)
                
                # Process data
                df_import_led['employee_id'] = df_import_led['employee_name'].map(emp_map)
                
                # Clean numeric and date cols
                df_import_led['credit'] = pd.to_numeric(df_import_led['credit'], errors='coerce').fillna(0)
                df_import_led['debit'] = pd.to_numeric(df_import_led['debit'], errors='coerce').fillna(0)
                df_import_led['entry_date'] = pd.to_datetime(df_import_led['entry_date (YYYY-MM-DD)']).dt.date
                
                st.dataframe(df_import_led)
                
                # Check for errors
                failed_emps = df_import_led[df_import_led['employee_id'].isna()]['employee_name'].unique()
                if len(failed_emps) > 0:
                    st.error(f"Error: The following employees were not found: {', '.join(failed_emps)}. Please add them first.")
                else:
                    if st.button("Import Ledger Entries"):
                        df_to_insert = df_import_led[['entry_date', 'employee_id', 'description', 'credit', 'debit']]
                        try:
                            with get_db_connection() as conn:
                                df_to_insert.to_sql('employee_ledger', conn, if_exists='append', index=False)
                            st.success(f"Successfully imported {len(df_to_insert)} ledger entries.")
                        except Exception as e:
                            st.error(f"Error during import: {e}")

            except Exception as e:
                st.error(f"Error reading file or processing data: {e}")


# --- Main Application ---
def main():
    st.set_page_config(
        page_title=f"{COMPANY_NAME} HR & Expense",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize the database
    init_db()

    # --- Sidebar ---
    with st.sidebar:
        st.image(COMPANY_LOGO_URL, width=100)
        st.title(f"{COMPANY_NAME}")
        st.markdown("HR & Expense System")
        st.divider()
        
        page = st.radio(
            "Navigation",
            [
                "🏠 Dashboard",
                "👤 Employee Management",
                "💸 Expense Management",
                "💰 Salary Management",
                "🧾 Employee Ledger",
                "📊 Reporting",
                "⬆️ Data Import"
            ]
        )
        
        st.divider()
        st.markdown("---")
        st.markdown(f"**Developed by:**\n{DEVELOPER_NAME}")
        st.markdown(f"**Contact:**\n{DEVELOPER_CONTACT}")

    # --- Page Routing ---
    if page == "🏠 Dashboard":
        page_dashboard()
    elif page == "👤 Employee Management":
        page_employee_management()
    elif page == "💸 Expense Management":
        page_expense_management()
    elif page == "💰 Salary Management":
        page_salary_management()
    elif page == "🧾 Employee Ledger":
        page_employee_ledger()
    elif page == "📊 Reporting":
        page_reporting()
    elif page == "⬆️ Data Import":
        page_data_import()

if __name__ == "__main__":
    main()
