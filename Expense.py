import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
from PIL import Image

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# --- PDF Class with Header/Footer (MODIFIED) ---
class PDF(FPDF):
    def header(self):
        # Add Logo
        if os.path.exists('logo.png'):
            # Calculate width to be 1/3 of the page width
            img_width = (self.w - self.l_margin - self.r_margin) / 3
            self.image('logo.png', x=self.l_margin, y=10, w=img_width)
        
        # Company Title
        self.set_font('Arial', 'B', 20)
        self.set_x(self.l_margin + 70) # Adjust X to be next to logo
        # --- FIX: Use self.title_text (set before add_page) ---
        title = getattr(self, 'title_text', 'Report') # Default title
        self.cell(0, 15, f"{COMPANY_NAME} - {title}", 0, 1, 'L')
        self.set_font('Arial', '', 10)
        self.set_x(self.l_margin + 70)
        self.cell(0, 8, f"Report Date: {date.today().strftime('%B %d, %Y')}", 0, 1, 'L')
        
        self.ln(15) # Add space after header

    def footer(self):
        footer_width = self.w - self.l_margin - self.r_margin
        
        # --- MODIFICATION: Add Signature Image ---
        self.set_y(-40) # Position 4 cm from bottom
        self.set_font('Arial', '', 10)
        
        if os.path.exists('Asim Siganture.jpg'):
            # Place signature image above the "Prepared by" line
            # Center the signature image on the left side
            sig_width = 40 # width of signature
            sig_x_pos = self.l_margin + (footer_width / 4) - (sig_width / 2)
            self.image('Asim Siganture.jpg', x=sig_x_pos, y=self.get_y(), w=sig_width)
        
        # --- Lines for Signatures ---
        self.set_y(-30) # Position 3 cm from bottom
        
        # Prepared By (Left side)
        self.cell(footer_width / 2, 10, "Prepared by: _______________", 0, 0, 'L')
        
        # Approved By (Right side)
        self.cell(footer_width / 2, 10, "Approved by: _______________", 0, 1, 'R')
        
        # --- Developer Info ---
        self.set_y(-15) # Position 1.5 cm from bottom
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128) # Grey
        
        # Left side: Date
        self.cell(footer_width / 2, 10, f"Printed on {date.today().strftime('%d-%m-%Y')}", 0, 0, 'L')
        
        # Right side: Developer Info
        self.cell(footer_width / 2, 10, DEVELOPER_INFO, 0, 0, 'R')

    def add_table(self, df, totals_cols=None):
        # Set font for table header
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(220, 220, 220) # Light grey background
        
        # Calculate column widths (equal distribution)
        num_cols = len(df.columns)
        total_width = self.w - self.l_margin - self.r_margin
        col_width = total_width / num_cols
        
        # Header
        for col in df.columns:
            self.cell(col_width, 7, col, 1, 0, 'C', 1) # 'C' = Center, 1 = Fill
        self.ln()
        
        # Set font for table data
        self.set_font('Arial', '', 8)
        
        # Data rows
        for index, row in df.iterrows():
            for col in df.columns:
                val = row[col]
                
                # --- FIX: Handle potential None/NaN values gracefully ---
                if pd.isna(val):
                    cell_text = ""
                elif isinstance(val, (int, float)) and col.lower() in ['amount', 'salary', 'deductions', 'net salary', 'debit', 'credit', 'balance', 'deduction (-)', 'payment (+)']:
                    cell_text = f"{val:,.2f}"
                else:
                    cell_text = str(val)
                
                # Align numeric columns to the right
                if isinstance(val, (int, float)):
                    align = 'R'
                else:
                    align = 'L'
                    
                self.cell(col_width, 6, cell_text, 1, 0, align)
            self.ln()
            
        # --- Add Grand Total Row ---
        if totals_cols:
            self.set_font('Arial', 'B', 8)
            self.set_fill_color(240, 240, 240) # Lighter grey for totals
            
            total_values = {}
            for col in totals_cols:
                if col in df.columns:
                    try:
                        total_values[col] = df[col].sum()
                    except TypeError:
                        total_values[col] = None
            
            # Find the first column to put "GRAND TOTAL"
            first_col_name = df.columns[0]
            first_total_col = len(df.columns)
            
            # Find the position of the first total column
            for i, col in enumerate(df.columns):
                if col in totals_cols:
                    first_total_col = i
                    break
                    
            # Add cells for GRAND TOTAL
            # Add "GRAND TOTAL" in the cells before the first total
            if first_total_col == 0:
                self.cell(col_width, 7, "GRAND TOTAL", 1, 0, 'R', 1)
            else:
                self.cell(col_width * first_total_col, 7, "GRAND TOTAL", 1, 0, 'R', 1)

            # Add the total values
            for col in df.columns[first_total_col:]:
                if col in total_values and total_values[col] is not None:
                    cell_text = f"{total_values[col]:,.2f}"
                    self.cell(col_width, 7, cell_text, 1, 0, 'R', 1)
                else:
                    self.cell(col_width, 7, "", 1, 0, 'C', 1) # Empty cell
            self.ln()


# --- Database Initialization ---
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Employees Table (Req 2)
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT,
            salary REAL DEFAULT 0,
            bank TEXT,
            account_title TEXT,
            account_no TEXT,
            join_date TEXT -- Store as 'YYYY-MM-DD' text
        )
    ''')
    
    # Expense Categories Table (Req 3, 10)
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Company Expenses Table (Req 3)
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            amount REAL NOT NULL,
            expense_date DATE NOT NULL,
            category_id INTEGER,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id) ON DELETE SET NULL
        )
    ''')
    
    # Employee Ledger Table (Req 5, 11)
    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            entry_date DATE NOT NULL,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()

# --- Helper Functions ---
@st.cache_data(ttl=60) # Cache for 1 minute
def get_dashboard_metrics():
    conn = get_db_connection()
    try:
        total_employees = conn.execute("SELECT COUNT(id) FROM employees").fetchone()[0]
        
        # Total expenses for the current month
        start_of_month = date.today().replace(day=1)
        total_expenses = conn.execute(
            "SELECT SUM(amount) FROM company_expenses WHERE expense_date >= ?",
            (str(start_of_month),)
        ).fetchone()[0]
        
        total_categories = conn.execute("SELECT COUNT(id) FROM expense_categories").fetchone()[0]
        
        return {
            "total_employees": total_employees,
            "total_expenses": total_expenses or 0,
            "total_categories": total_categories
        }
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        return {
            "total_employees": 0,
            "total_expenses": 0,
            "total_categories": 0
        }

@st.cache_data(ttl=60)
def get_all_employees():
    conn = get_db_connection()
    # FIX: Parse join_date as date object for the editor
    df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn, parse_dates=["join_date"])
    return df

@st.cache_data(ttl=60)
def get_all_categories():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)
    return df

def clear_cache():
    st.cache_data.clear()

def generate_excel_template(columns, filename):
    df = pd.DataFrame(columns=columns)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Import')
    output.seek(0)
    return output, filename

# --- Page: Dashboard ---
def page_dashboard():
    st.title(f"{COMPANY_NAME} Dashboard")
    st.text(f"Welcome to your HR & Expense Management System.")
    
    metrics = get_dashboard_metrics()
    
    cols = st.columns(3)
    cols[0].metric(label="Total Employees", value=metrics["total_employees"])
    cols[1].metric(label="Total Expenses (Current Month)", value=f"PKR {metrics['total_expenses']:,.2f}")
    cols[2].metric(label="Total Expense Categories", value=metrics["total_categories"])
    
    st.divider()
    
    st.subheader("Quick Links")
    c1, c2, c3 = st.columns(3)
    if c1.button("Manage Employees", use_container_width=True):
        st.session_state.page = "Manage Employees"
        st.rerun()
    if c2.button("Log New Expense", use_container_width=True):
        st.session_state.page = "Expense Management"
        st.rerun()
    if c3.button("View Employee Ledger", use_container_width=True):
        st.session_state.page = "Employee Ledger"
        st.rerun()

# --- Page: Employee Management (Requirement 4) ---
def page_employee_management():
    st.title("Manage Employees")
    
    # --- Add New Employee Form ---
    st.subheader("Add New Employee")
    with st.form("new_employee_form", clear_on_submit=True):
        cols = st.columns(2)
        name = cols[0].text_input("Name", placeholder="e.g., Alice Smith")
        designation = cols[1].text_input("Designation", placeholder="e.g., Sales Manager")
        
        cols = st.columns(3)
        salary = cols[0].number_input("Base Salary (PKR)", min_value=0.0, format="%.2f")
        join_date = cols[1].date_input("Joining Date", date.today())
        bank = cols[2].text_input("Bank", placeholder="e.g., HBL")
        
        cols = st.columns(2)
        account_title = cols[0].text_input("Account Title", placeholder="e.g., Alice T Smith")
        account_no = cols[1].text_input("Account No.", placeholder="e.g., 00123456789")
        
        submitted = st.form_submit_button("Add Employee")
        if submitted:
            if not name or salary <= 0:
                st.error("Please provide at least a Name and a valid Salary.")
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
                    st.success(f"Employee '{name}' added successfully.")
                    clear_cache()
                except sqlite3.IntegrityError:
                    st.error(f"Error: An employee with this name might already exist.")
                except Exception as e:
                    st.error(f"An error occurred: {e}")

    st.divider()
    
    # --- Edit/Delete Employees ---
    st.subheader("Edit or Delete Employees")
    st.info("Use this table to edit, add, or delete employees. Click 'Save Changes' to update the database.")
    
    try:
        employees_df = get_all_employees()
        
        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("Name", required=True),
            "designation": st.column_config.TextColumn("Designation"),
            "salary": st.column_config.NumberColumn("Salary", min_value=0, format="%.2f"),
            "bank": st.column_config.TextColumn("Bank"),
            "account_title": st.column_config.TextColumn("Account Title"),
            "account_no": st.column_config.TextColumn("Account No."),
            "join_date": st.column_config.DateColumn("Join Date", format="YYYY-MM-DD") # Handle as date
        }
        
        # Display the data editor
        edited_df = st.data_editor(
            employees_df,
            column_config=column_config,
            num_rows="dynamic", # Allow adding/deleting rows
            use_container_width=True,
            key="employee_editor"
        )
        
        if st.button("Save Employee Changes"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                # Get IDs from the database and the editor
                db_ids = set(employees_df['id'])
                edited_ids = set(edited_df.dropna(subset=['id'])['id']) # Get non-NA IDs
                
                # --- Find Deleted Rows ---
                deleted_ids = db_ids - edited_ids
                if deleted_ids:
                    for emp_id in deleted_ids:
                        cursor.execute("DELETE FROM employees WHERE id = ?", (int(emp_id),))
                        cursor.execute("DELETE FROM employee_ledger WHERE employee_id = ?", (int(emp_id),)) # Cascade delete
                    st.toast(f"Deleted {len(deleted_ids)} employee(s).")
                
                # --- Find Updated/Added Rows ---
                for index, row in edited_df.iterrows():
                    # FIX: Handle NaT/NaN dates
                    join_date_str = None
                    if pd.notna(row['join_date']):
                        join_date_str = row['join_date'].strftime('%Y-%m-%d')
                    
                    if pd.isna(row['id']):
                        # New Row (Add)
                        cursor.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (row['name'], row['designation'], row['salary'], row['bank'], row['account_title'], row['account_no'], join_date_str)
                        )
                    else:
                        # Existing Row (Update)
                        cursor.execute(
                            """
                            UPDATE employees 
                            SET name=?, designation=?, salary=?, bank=?, account_title=?, account_no=?, join_date=?
                            WHERE id=?
                            """,
                            (row['name'], row['designation'], row['salary'], row['bank'], row['account_title'], row['account_no'], join_date_str, int(row['id']))
                        )
                
                conn.commit()
                st.success("Employee data saved successfully.")
                clear_cache()
                st.rerun()
                
            except Exception as e:
                conn.rollback()
                st.error(f"Error saving changes: {e}")
                
    except Exception as e:
        st.error(f"Error loading employees: {e}")
        st.error("If this is a 'type' error, it might be due to a recent edit. Try refreshing.")

# --- Page: Expense Management (Requirement 3, 4, 10, 11) ---
def page_expense_management():
    st.title("Expense Management")

    # --- Log New Expense (Req 3) ---
    st.subheader("Log New Company Expense")
    st.info("Use this form to log general company expenses. This does NOT affect any employee's ledger.")
    
    # Get categories for dropdown
    categories_df = get_all_categories()
    category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
    
    if not category_list:
        st.warning("No expense categories found. Please add categories below before logging expenses.", icon="⚠️")
        
    with st.form("new_expense_form", clear_on_submit=True):
        cols = st.columns(3)
        with cols[0]:
            expense_date = st.date_input("Expense Date", date.today())
        with cols[1]:
            amount = st.number_input("Amount (PKR)", min_value=0.01)
        with cols[2]:
            category_id = st.selectbox("Category", options=list(category_list.keys()), format_func=lambda x: category_list[x], disabled=not category_list)
        
        description = st.text_input("Description", placeholder="e.g., Office electricity bill")
        
        submitted = st.form_submit_button("Log Expense")
        if submitted:
            if amount <= 0 or not description or not category_id:
                st.error("Please fill in all fields (Description, Amount, Category).")
            else:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # 1. Log the company expense
                    cursor.execute(
                        """
                        INSERT INTO company_expenses (description, amount, expense_date, category_id)
                        VALUES (?, ?, ?, ?)
                        """,
                        (description, amount, str(expense_date), category_id)
                    )
                    
                    st.success("Company expense logged successfully.")
                    
                    conn.commit()
                    clear_cache()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error logging expense: {e}")

    st.divider()

    # --- Manage Logged Expenses (Req 4) ---
    st.subheader("Manage Logged Expenses")
    st.info("Select an expense ID from the table to delete or edit it.")
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
                ce.category_id -- Keep for editing
            FROM company_expenses ce
            LEFT JOIN expense_categories ec ON ce.category_id = ec.id
            ORDER BY ce.expense_date DESC
            """, conn
        )

        if expenses_df.empty:
            st.info("No expenses logged yet.")
        else:
            cols_to_show = ['id', 'expense_date', 'description', 'amount', 'category']
            st.dataframe(expenses_df[cols_to_show], use_container_width=True, hide_index=True)
            
            st.subheader("Delete or Edit Expense")
            expense_ids = expenses_df['id'].tolist()
            expense_to_edit = st.selectbox("Select Expense ID to Manage", options=expense_ids)
            
            expense_details = expenses_df.loc[expenses_df['id'] == expense_to_edit].iloc[0]
            
            # Delete Button
            if st.button(f"Delete Expense ID {expense_to_edit}", type="primary"):
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    # Check if this expense is linked to a ledger (it shouldn't be, but good to check)
                    cursor.execute("DELETE FROM company_expenses WHERE id = ?", (int(expense_to_edit),))
                    conn.commit()
                    st.success(f"Expense ID {expense_to_edit} deleted.")
                    clear_cache()
                    st.rerun()
                except Exception as e:
                    conn.rollback()
                    st.error(f"Error deleting: {e}")
            
            # Edit Form
            with st.expander("Edit Expense Details"):
                
                # Get category list for form
                categories_df = get_all_categories()
                category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
                cat_ids = list(category_list.keys())
                
                default_index = 0
                if expense_details['category_id'] in cat_ids:
                    default_index = cat_ids.index(expense_details['category_id'])
                
                with st.form("edit_expense_form"):
                    edit_date = st.date_input("Expense Date", value=pd.to_datetime(expense_details['expense_date']))
                    edit_amount = st.number_input("Amount", value=expense_details['amount'])
                    
                    cols = st.columns(2)
                    with cols[0]:
                        edit_desc = st.text_input("Description", value=expense_details['description'])
                    with cols[1]:
                        edit_category_id = st.selectbox("Category", 
                            options=cat_ids, 
                            format_func=lambda x: category_list.get(x, "Invalid"), 
                            index=default_index
                        )

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
                                (str(edit_date), edit_amount, edit_desc, edit_category_id, int(expense_to_edit))
                            )
                            conn.commit()
                            st.success(f"Expense ID {expense_to_edit} updated.")
                            clear_cache()
                            st.rerun()
                        except Exception as e:
                            conn.rollback()
                            st.error(f"Error updating: {e}")

    except Exception as e:
        st.error(f"Error loading expenses: {e}")


    st.divider()

    # --- Manage Expense Categories (Req 3, 10) ---
    st.subheader("Manage Expense Categories")
    st.info("Use this table to add, rename, or delete expense categories.")
    
    try:
        categories_df = get_all_categories()
        
        column_config = {
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "name": st.column_config.TextColumn("Category Name", required=True),
        }
        
        edited_cats_df = st.data_editor(
            categories_df,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="category_editor"
        )
        
        if st.button("Save Category Changes"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                db_ids = set(categories_df['id'])
                edited_ids = set(edited_cats_df.dropna(subset=['id'])['id'])
                
                # --- Find Deleted Rows ---
                deleted_ids = db_ids - edited_ids
                if deleted_ids:
                    for cat_id in deleted_ids:
                        cursor.execute("DELETE FROM expense_categories WHERE id = ?", (int(cat_id),))
                        # Expenses linked to this are set to NULL, not deleted
                    st.toast(f"Deleted {len(deleted_ids)} category(s).")
                
                # --- Find Updated/Added Rows ---
                for index, row in edited_cats_df.iterrows():
                    if not row['name']:
                        st.error(f"Row {index} 'name' cannot be empty. Aborting save.")
                        raise Exception("Category name cannot be empty.")
                        
                    if pd.isna(row['id']):
                        # New Row (Add)
                        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (row['name'],))
                    else:
                        # Existing Row (Update)
                        cursor.execute("UPDATE expense_categories SET name=? WHERE id=?", (row['name'], int(row['id'])))
                
                conn.commit()
                st.success("Category data saved successfully.")
                clear_cache()
                st.rerun()
                
            except sqlite3.IntegrityError:
                conn.rollback()
                st.error("Error saving: A category with that name already exists. Please check for duplicates.")
            except Exception as e:
                conn.rollback()
                st.error(f"Error saving changes: {e}")

    except Exception as e:
        st.error(f"Error loading categories: {e}")

# --- Page: Salary Management (Requirement 2) ---
def page_salary_management():
    st.title("Salary Management")
    
    st.info("Follow these steps to process monthly salaries:\n"
            "1. **Generate Monthly Salary Credits:** Run this first. It adds the 'Base Salary' as a credit to each employee's ledger for the month.\n"
            "2. **View & Download Salary Sheet:** After credits are generated (and any deductions are logged), use this to see the final pay.\n"
            "3. **Generate Individual Salary Slip:** Download a PDF slip for a single employee.")

    # --- 1. Generate Monthly Salary Credits ---
    st.subheader("1. Generate Monthly Salary Credits")
    st.warning("Run this **only once** per month. Running it again for the same month will create duplicate entries.")
    
    today = date.today()
    default_month = today.month
    default_year = today.year
    
    with st.form("generate_salaries_form"):
        cols = st.columns(2)
        salary_month = cols[0].number_input("For Month", min_value=1, max_value=12, value=default_month)
        salary_year = cols[1].number_input("For Year", min_value=2020, max_value=2100, value=default_year)
        
        submitted = st.form_submit_button("Generate Salary Credits for All Employees")
        
        if submitted:
            conn = get_db_connection()
            cursor = conn.cursor()
            employees = get_all_employees()
            
            if employees.empty:
                st.error("No employees found to generate salaries for.")
                return

            try:
                count = 0
                with st.spinner(f"Generating salary credits for {len(employees)} employees..."):
                    # Use the 1st of the month for the entry date
                    entry_date = date(salary_year, salary_month, 1)
                    
                    for index, emp in employees.iterrows():
                        description = f"Monthly Salary Credit for {entry_date.strftime('%B %Y')}"
                        
                        # Check if this exact entry already exists
                        exists = cursor.execute(
                            """
                            SELECT 1 FROM employee_ledger 
                            WHERE employee_id = ? AND description = ? AND credit = ?
                            """,
                            (int(emp['id']), description, float(emp['salary']))
                        ).fetchone()
                        
                        if not exists:
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, credit)
                                VALUES (?, ?, ?, ?)
                                """,
                                (int(emp['id']), str(entry_date), description, float(emp['salary']))
                            )
                            count += 1
                        
                conn.commit()
                if count > 0:
                    st.success(f"Successfully generated {count} new salary credit entries.")
                else:
                    st.info("No new entries were created. Salaries for this period might already be generated.")
                clear_cache()
                
            except Exception as e:
                conn.rollback()
                st.error(f"Error generating salaries: {e}")

    st.divider()

    # --- 2. View & Download Salary Sheet ---
    st.subheader("2. View & Download Salary Sheet")
    st.text("This sheet calculates the Net Salary based on all ledger entries for the selected month.")
    
    cols = st.columns(2)
    sheet_month = cols[0].number_input("Select Month", min_value=1, max_value=12, value=default_month, key="sheet_month")
    sheet_year = cols[1].number_input("Select Year", min_value=2020, max_value=2100, value=default_year, key="sheet_year")
    
    try:
        df = get_salary_sheet(sheet_month, sheet_year)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if not df.empty:
            pdf_data = generate_salary_sheet_pdf(df, sheet_month, sheet_year)
            st.download_button(
                label="Download Salary Sheet as PDF (Req 1)",
                data=pdf_data,
                file_name=f"Salary_Sheet_{sheet_year}_{sheet_month:02d}.pdf",
                mime="application/pdf"
            )
            
    except Exception as e:
        st.error(f"Error generating salary sheet: {e}")

    st.divider()
    
    # --- 3. Generate Individual Salary Slip ---
    st.subheader("3. Generate Individual Salary Slip (Req 2)")
    
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}

    if not employee_list:
        st.error("No employees found. Please add employees first.", icon="⚠️")
        return

    cols = st.columns(3)
    slip_emp_id = cols[0].selectbox(
        "Select Employee", 
        options=list(employee_list.keys()), 
        format_func=lambda x: employee_list[x]
    )
    slip_month = cols[1].number_input("Select Month", min_value=1, max_value=12, value=default_month, key="slip_month")
    slip_year = cols[2].number_input("Select Year", min_value=2020, max_value=2100, value=default_year, key="slip_year")
    
    if st.button("Generate Individual Slip"):
        try:
            pdf_data = generate_individual_slip_pdf(slip_emp_id, slip_month, slip_year)
            st.download_button(
                label=f"Download Slip for {employee_list[slip_emp_id]}",
                data=pdf_data,
                file_name=f"Salary_Slip_{employee_list[slip_emp_id]}_{slip_year}_{slip_month:02d}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF slip: {e}")


@st.cache_data(ttl=60)
def get_salary_sheet(month, year):
    # Calculate start and end of the month
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    
    conn = get_db_connection()
    query = """
    SELECT
        e.name AS "Name",
        e.designation AS "Designation",
        e.bank AS "Bank",
        e.account_title AS "Account Title",
        e.account_no AS "Account No.",
        e.salary AS "Base Salary",
        COALESCE(SUM(CASE WHEN el.credit > 0 AND el.description NOT LIKE 'Monthly Salary Credit%' THEN el.credit ELSE 0 END), 0) AS "Other Credits (Bonus/Reimb.)",
        COALESCE(SUM(el.debit), 0) AS "Deductions (Advance)",
        (e.salary + COALESCE(SUM(el.credit), 0) - COALESCE(SUM(el.debit), 0)) AS "Net Salary"
    FROM employees e
    LEFT JOIN employee_ledger el ON e.id = el.employee_id
        AND el.entry_date BETWEEN ? AND ?
    GROUP BY e.id
    ORDER BY e.name
    """
    df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
    return df

def generate_salary_sheet_pdf(df, month, year):
    pdf = PDF('L', 'mm', 'A4') # Landscape
    # --- FIX: Set title_text attribute, don't call method ---
    pdf.title_text = f"Salary Sheet - {datetime(2000, month, 1).strftime('%B')} {year}"
    pdf.add_page()
    
    # Add table
    pdf.add_table(df, totals_cols=["Base Salary", "Other Credits (Bonus/Reimb.)", "Deductions (Advance)", "Net Salary"])
    
    return pdf.output(dest='S').encode('latin-1')

def generate_individual_slip_pdf(employee_id, month, year):
    conn = get_db_connection()
    
    # 1. Get Employee Details
    emp = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if not emp:
        raise Exception("Employee not found.")
        
    # 2. Get Ledger Entries for the month
    start_date = date(year, month, 1)
    end_date = (start_date + timedelta(days=31)).replace(day=1) - timedelta(days=1)
    
    ledger_df = pd.read_sql_query(
        """
        SELECT 
            entry_date AS "Date",
            description AS "Description",
            credit AS "Credits (+)",
            debit AS "Deductions (-)"
        FROM employee_ledger
        WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
        ORDER BY entry_date
        """,
        conn,
        params=(employee_id, str(start_date), str(end_date))
    )
    
    # 3. Calculate Totals
    total_credits = ledger_df['Credits (+)'].sum()
    total_deductions = ledger_df['Deductions (-)'].sum()
    net_salary = total_credits - total_deductions
    base_salary = emp['salary']
    
    # 4. Create PDF
    pdf = PDF('P', 'mm', 'A4') # Portrait
    # --- FIX: Set title_text attribute, don't call method ---
    pdf.title_text = f"Salary Slip - {emp['name']}"
    pdf.add_page()
    
    pdf.set_font('Arial', '', 11)
    
    # --- Employee Info Table ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Employee Information", 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    
    info_data = {
        "Employee Name:": emp['name'],
        "Designation:": emp['designation'],
        "Pay Period:": f"{datetime(year, month, 1).strftime('%B %Y')}",
        "Bank:": f"{emp['bank']} (A/C: {emp['account_no']})"
    }
    
    for key, val in info_data.items():
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(40, 8, key, 0, 0, 'L')
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, val, 0, 1, 'L')

    pdf.ln(10)
    
    # --- Earnings & Deductions Tables ---
    # Create two dataframes for the table
    earnings_df = ledger_df[ledger_df['Credits (+)'] > 0][['Date', 'Description', 'Credits (+)']]
    deductions_df = ledger_df[ledger_df['Deductions (-)'] > 0][['Date', 'Description', 'Deductions (-)']]

    # Add Earnings Table
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Earnings & Credits", 0, 1, 'L')
    if not earnings_df.empty:
        pdf.add_table(earnings_df, totals_cols=['Credits (+)'])
    else:
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 10, "No earnings entries this month.", 0, 1, 'L')

    pdf.ln(10)

    # Add Deductions Table
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Advances & Deductions", 0, 1, 'L')
    if not deductions_df.empty:
        pdf.add_table(deductions_df, totals_cols=['Deductions (-)'])
    else:
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 10, "No deduction entries this month.", 0, 1, 'L')
        
    pdf.ln(10)
    
    # --- Summary ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Salary Summary", 0, 1, 'L')
    
    # Set fill color for summary box
    pdf.set_fill_color(245, 245, 245)
    pdf.set_line_width(0.5)
    pdf.set_draw_color(200, 200, 200)

    summary_data = {
        "Total Credits / Earnings:": f"{total_credits:,.2f} PKR",
        "Total Advances / Deductions:": f"{total_deductions:,.2f} PKR",
    }
    
    for key, val in summary_data.items():
        pdf.set_font('Arial', '', 11)
        pdf.cell(90, 8, key, 'L', 0, 'R', 1)
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(90, 8, val, 'R', 1, 'L', 1)
    
    # Net Salary (Highlight)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(90, 10, "Net Salary Payable:", 'LB', 0, 'R', 1)
    pdf.cell(90, 10, f"{net_salary:,.2f} PKR", 'RB', 1, 'L', 1)
    
    return pdf.output(dest='S').encode('latin-1')


# --- Page: Employee Ledger (Requirement 5) ---
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
    
    # --- NEW FEATURE: Add Manual Ledger Entry ---
    st.subheader("Add New Ledger Entry")
    st.info("Use this form to record advances, deductions, or bonuses for an employee.")
    with st.form("new_ledger_entry", clear_on_submit=True):
        cols = st.columns(3)
        with cols[0]:
            entry_emp_id = st.selectbox(
                "Select Employee", 
                options=emp_ids, 
                format_func=lambda x: employee_list[x],
                index=emp_ids.index(selected_emp_id) if selected_emp_id in emp_ids else 0,
                key="manual_emp_select"
            )
        with cols[1]:
            entry_date = st.date_input("Entry Date", date.today())
        with cols[2]:
            # --- MODIFICATION: Simplified English terms ---
            entry_type = st.radio(
                "Entry Type", 
                [
                    "Advance / Deduction (Amount Subtracted)", 
                    "Company-Paid Personal Expense (Deduction)",
                    "Reimbursement / Bonus (Amount Added)"
                ]
            )
        
        entry_desc = st.text_input("Description", placeholder="e.g., Cash advance for travel")
        entry_amount = st.number_input("Amount", min_value=0.01)
        
        entry_submitted = st.form_submit_button("Add Ledger Entry")
        
        if entry_submitted:
            if entry_amount > 0 and entry_desc:
                # --- MODIFICATION: Logic updated to match new terms ---
                debit = entry_amount if ("Deduction" in entry_type or "Expense" in entry_type) else 0
                credit = entry_amount if "Bonus" in entry_type else 0
                
                try:
                    conn = get_db_connection()
                    conn.execute(
                        """
                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (entry_emp_id, str(entry_date), entry_desc, debit, credit)
                    )
                    conn.commit()
                    st.success(f"Ledger entry added for {employee_list[entry_emp_id]}.")
                    clear_cache()
                    st.rerun()
                except Exception as e:
                    st.error(f"Database error: {e}")
            else:
                st.error("Please provide a description and amount.")
    
    st.divider()
    
    # --- View Ledger (Req 5, 1) ---
    st.subheader(f"Ledger for: {employee_list.get(selected_emp_id)}")
    
    # --- NEW: All-Time Ledger Toggle ---
    show_all_time = st.checkbox("Show All-Time Ledger? (Disables date filter)", key="all_time_toggle")
    
    today = date.today()
    first_day_of_month = today.replace(day=1)
    
    cols = st.columns(2)
    start_date = cols[0].date_input("Start Date", first_day_of_month, disabled=show_all_time)
    end_date = cols[1].date_input("End Date", today, disabled=show_all_time)
    
    if show_all_time:
        start_date = date(1970, 1, 1)
        end_date = date(2100, 12, 31)

    if start_date > end_date:
        st.error("Start Date must be before End Date.")
        return
        
    try:
        # Get full ledger for all-time balance calculation
        full_ledger_df = get_employee_ledger(selected_emp_id, date(1970, 1, 1), date(2100, 12, 31))
        
        # Get filtered ledger for display
        filtered_ledger_df = get_employee_ledger(selected_emp_id, start_date, end_date)
        
        # --- Calculate Balances ---
        all_time_balance = 0
        if not full_ledger_df.empty:
            all_time_balance = full_ledger_df['credit'].sum() - full_ledger_df['debit'].sum()
            
        range_balance = 0
        if not filtered_ledger_df.empty:
            range_balance = filtered_ledger_df['credit'].sum() - filtered_ledger_df['debit'].sum()
            
            # Add running balance column for the *filtered* range
            filtered_ledger_df.sort_values(by='entry_date', inplace=True)
            filtered_ledger_df['Balance'] = filtered_ledger_df['credit'].cumsum() - filtered_ledger_df['debit'].cumsum()
        else:
            # If empty, create an empty df with correct columns for the editor
            filtered_ledger_df = pd.DataFrame(columns=['id', 'entry_date', 'description', 'credit', 'debit'])


        # --- Display Metrics ---
        st.metric(
            "All-Time Ledger Balance (Total Payable)",
            f"PKR {all_time_balance:,.2f}",
            help="Total credits minus total debits over the employee's entire history."
        )
        
        # --- MODIFICATION: Rename columns for display ---
        # --- FIX: Move Dataframe, subheader, and button INSIDE the check ---
        if not filtered_ledger_df.empty:
            display_df = filtered_ledger_df.rename(columns={
                'entry_date': 'Entry Date',
                'description': 'Description',
                'debit': 'Deduction / Advance (-)',
                'credit': 'Payment / Bonus (+)',
                'Balance': 'Running Balance (in range)'
            })
            
            # Columns to show
            cols_to_show = ['Entry Date', 'Description', 'Payment / Bonus (+)', 'Deduction / Advance (-)', 'Running Balance (in range)']
            
            st.dataframe(
                display_df.set_index('Entry Date')[cols_to_show],
                use_container_width=True
            )
            
            # --- Display Range Balance ---
            st.subheader(f"Balance for selected date range: PKR {range_balance:,.2f}")
            
            # --- Download PDF ---
            pdf_data = generate_ledger_pdf(display_df, employee_list.get(selected_emp_id), start_date, end_date, all_time_balance)
            st.download_button(
                label="Download Ledger as PDF",
                data=pdf_data,
                file_name=f"Ledger_{employee_list.get(selected_emp_id)}_{start_date}_to_{end_date}.pdf",
                mime="application/pdf"
            )
        else:
            # --- FIX: Handle case where no entries are found ---
            st.info("No ledger entries found for this employee in this period.")
        
        st.divider()
        
        # --- NEW: Edit/Delete Ledger Entries ---
        st.subheader("Edit or Delete Ledger Entries")
        st.info("You can edit or delete entries for the selected employee *within the date range specified above*.")
        
        try:
            # Use the filtered DF we already fetched
            edit_df = filtered_ledger_df.copy()
            
            # Re-fetch with ID for saving
            if not edit_df.empty:
                conn = get_db_connection()
                # Get IDs for the date range
                ids_in_range = tuple(edit_df['id'].tolist())
                query = f"""
                    SELECT id, entry_date, description, credit, debit, employee_id
                    FROM employee_ledger
                    WHERE id IN {ids_in_range}
                    ORDER BY entry_date
                """
                ledger_for_edit_df = pd.read_sql_query(query, conn, parse_dates=["entry_date"])
            else:
                ledger_for_edit_df = pd.DataFrame(columns=['id', 'entry_date', 'description', 'credit', 'debit', 'employee_id'])

            
            column_config = {
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "employee_id": None, # Hide this column
                "entry_date": st.column_config.DateColumn("Date", format="YYYY-MM-DD", required=True),
                "description": st.column_config.TextColumn("Description", required=True),
                "credit": st.column_config.NumberColumn("Payment (+)", format="%.2f", min_value=0),
                "debit": st.column_config.NumberColumn("Deduction (-)", format="%.2f", min_value=0),
            }
            
            edited_ledger_df = st.data_editor(
                ledger_for_edit_df,
                column_config=column_config,
                num_rows="dynamic", # Allow deleting
                use_container_width=True,
                key="ledger_editor"
            )
            
            if st.button("Save Ledger Changes"):
                conn = get_db_connection()
                cursor = conn.cursor()
                
                try:
                    db_ids = set(ledger_for_edit_df['id'])
                    edited_ids = set(edited_ledger_df.dropna(subset=['id'])['id'])
                    
                    # --- Find Deleted Rows ---
                    deleted_ids = db_ids - edited_ids
                    if deleted_ids:
                        for entry_id in deleted_ids:
                            cursor.execute("DELETE FROM employee_ledger WHERE id = ?", (int(entry_id),))
                        st.toast(f"Deleted {len(deleted_ids)} ledger entry(s).")

                    # --- Find Updated/Added Rows ---
                    for index, row in edited_ledger_df.iterrows():
                        if pd.isna(row['id']):
                            # This is a new row, but we should use the form for this.
                            # For safety, we'll add it, but it's better to use the form.
                            cursor.execute(
                                """
                                INSERT INTO employee_ledger (employee_id, entry_date, description, credit, debit)
                                VALUES (?, ?, ?, ?, ?)
                                """,
                                (selected_emp_id, row['entry_date'].strftime('%Y-%m-%d'), row['description'], row['credit'], row['debit'])
                            )
                        else:
                            # Existing Row (Update)
                            cursor.execute(
                                """
                                UPDATE employee_ledger 
                                SET entry_date=?, description=?, credit=?, debit=?
                                WHERE id=?
                                """,
                                (row['entry_date'].strftime('%Y-%m-%d'), row['description'], row['credit'], row['debit'], int(row['id']))
                            )
                    
                    conn.commit()
                    st.success("Ledger changes saved successfully.")
                    clear_cache()
                    st.rerun()

                except Exception as e:
                    conn.rollback()
                    st.error(f"Error saving ledger changes: {e}")

        except Exception as e:
            st.error(f"Error loading ledger editor: {e}")

    # --- FIX: Add the missing 'except' block ---
    except Exception as e:
        st.error(f"Error fetching ledger: {e}")

@st.cache_data(ttl=60)
def get_employee_ledger(employee_id, start_date, end_date):
    conn = get_db_connection()
    query = """
    SELECT id, entry_date, description, debit, credit
    FROM employee_ledger
    WHERE employee_id = ? AND entry_date BETWEEN ? AND ?
    ORDER BY entry_date
    """
    df = pd.read_sql_query(query, conn, params=(employee_id, str(start_date), str(end_date)))
    return df

def generate_ledger_pdf(df, employee_name, start_date, end_date, all_time_balance):
    pdf = PDF('P', 'mm', 'A4') # Portrait
    # --- FIX: Set title_text attribute, don't call method ---
    pdf.title_text = "Employee Ledger"
    pdf.add_page()
    
    # Add Employee Info
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Ledger Statement for: {employee_name}", 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    if start_date == date(1970, 1, 1):
        pdf.cell(0, 8, "Period: All-Time", 0, 1, 'L')
    else:
        pdf.cell(0, 8, f"Period: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}", 0, 1, 'L')

    # Add All-Time Balance
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"All-Time Ledger Balance (Total Payable): {all_time_balance:,.2f} PKR", 0, 1, 'L')
    pdf.ln(5)
    
    # Add table
    cols_for_pdf = ['Entry Date', 'Description', 'Payment / Bonus (+)', 'Deduction / Advance (-)', 'Running Balance (in range)']
    pdf.add_table(df[cols_for_pdf], totals_cols=['Payment / Bonus (+)', 'Deduction / Advance (-)'])
    
    return pdf.output(dest='S').encode('latin-1')


# --- Page: Reporting (Requirement 1, 6, 10) ---
def page_reporting():
    st.title("Download Reports")
    st.info("Select a report type and date range, then click 'Generate PDF'.")
    
    report_type = st.selectbox(
        "Select Report",
        [
            "Company Expense Report (All)",
            "Company Expense Report (Category-wise)",
            "Expense Category List"
        ]
    )
    
    today = date.today()
    first_day_of_month = today.replace(day=1)
    
    cols = st.columns(2)
    report_start_date = cols[0].date_input("Start Date", first_day_of_month)
    report_end_date = cols[1].date_input("End Date", today)
    
    # Category selection (for category-wise report)
    selected_category_id = None
    if "Category-wise" in report_type:
        categories_df = get_all_categories()
        category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
        if not category_list:
            st.error("No expense categories found. Please add categories first.")
            return
        
        selected_category_id = st.selectbox("Select Expense Category", options=list(category_list.keys()), format_func=lambda x: category_list[x])

    if st.button("Generate PDF Report"):
        if report_start_date > report_end_date:
            st.error("Start Date must be before End Date.")
            return
            
        try:
            conn = get_db_connection()
            
            if report_type == "Company Expense Report (All)":
                query = """
                    SELECT 
                        ce.expense_date AS "Date",
                        ce.description AS "Description",
                        ec.name AS "Category",
                        ce.amount AS "Amount"
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ?
                    ORDER BY ce.expense_date
                """
                params = [str(report_start_date), str(report_end_date)]
                report_title = "Company Expense Report"
                totals_cols = ["Amount"]
                
            elif report_type == "Company Expense Report (Category-wise)":
                query = """
                    SELECT 
                        ce.expense_date AS "Date",
                        ce.description AS "Description",
                        ec.name AS "Category",
                        ce.amount AS "Amount"
                    FROM company_expenses ce
                    LEFT JOIN expense_categories ec ON ce.category_id = ec.id
                    WHERE ce.expense_date BETWEEN ? AND ? AND ce.category_id = ?
                    ORDER BY ce.expense_date
                """
                params = [str(report_start_date), str(report_end_date), selected_category_id]
                category_name = category_list.get(selected_category_id, "Unknown")
                report_title = f"Expense Report: {category_name}"
                totals_cols = ["Amount"]

            elif report_type == "Expense Category List":
                query = "SELECT id AS \"ID\", name AS \"Category Name\" FROM expense_categories ORDER BY name"
                params = []
                report_title = "Expense Category List"
                totals_cols = None # No totals for this report
            
            # Fetch data
            df = pd.read_sql_query(query, conn, params=params)
            
            if df.empty:
                st.warning("No data found for the selected criteria.")
                return

            # Generate PDF
            pdf = PDF('P', 'mm', 'A4')
            # --- FIX: Set title_text attribute, don't call method ---
            pdf.title_text = report_title
            pdf.add_page()
            pdf.add_table(df, totals_cols=totals_cols)
            
            pdf_data = pdf.output(dest='S').encode('latin-1')
            
            # Download Button
            st.download_button(
                label="Click to Download PDF",
                data=pdf_data,
                file_name=f"{report_title.replace(' ', '_')}_{date.today()}.pdf",
                mime="application/pdf"
            )

        except Exception as e:
            st.error(f"Error generating report: {e}")

# --- Page: Data Import (Requirement 7) ---
def page_data_import():
    st.title("Data Import (Req 7)")
    st.warning("Please validate your files before importing. Incorrect data can cause issues.")
    st.info("If any row in a file has an error, the **entire file will be rejected** until all errors are fixed.")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Import Employees", "Import Categories", "Import Expenses", "Import Ledger Entries"])

    # --- Tab 1: Import Employees ---
    with tab1:
        st.subheader("1. Download Employee Template")
        cols = ["name", "designation", "salary", "bank", "account_title", "account_no", "join_date"]
        excel_data, file_name = generate_excel_template(cols, "employee_import_template.xlsx")
        st.download_button(
            label="Download Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("2. Upload Completed File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="emp_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                # --- NEW VALIDATION LOGIC ---
                errors = []
                required_cols = ["name", "designation", "salary", "bank", "account_title", "account_no", "join_date"]
                for col in required_cols:
                    if col not in df.columns:
                        errors.append(f"Missing required column: '{col}'")
                
                if errors:
                    st.error("File format error. Please fix and re-upload:")
                    st.json(errors)
                else:
                    # Validate data types
                    for i, row in df.iterrows():
                        if not row['name']:
                            errors.append(f"Row {i+2}: 'name' cannot be empty.")
                        try:
                            pd.to_numeric(row['salary'])
                        except:
                            errors.append(f"Row {i+2}: 'salary' is not a valid number (Value: {row['salary']}).")
                        try:
                            # Try parsing the date
                            pd.to_datetime(row['join_date'])
                        except:
                            errors.append(f"Row {i+2}: 'join_date' is not a valid date (Value: {row['join_date']}). Should be YYYY-MM-DD.")
                    
                    if errors:
                        st.error(f"Found {len(errors)} data errors. Please fix in your file and re-upload:")
                        st.json(errors[:10]) # Show first 10 errors
                    else:
                        st.success("File validation passed!")
                        st.dataframe(df)
                        if st.button("Import Employees"):
                            conn = get_db_connection()
                            try:
                                with st.spinner("Importing..."):
                                    # Convert date to string for DB
                                    df['join_date'] = pd.to_datetime(df['join_date']).dt.strftime('%Y-%m-%d')
                                    df.to_sql("employees", conn, if_exists="append", index=False)
                                st.success(f"Successfully imported {len(df)} employee records.")
                                clear_cache()
                            except Exception as e:
                                st.error(f"Error importing to database: {e}. Check if data is valid.")
                
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # --- Tab 2: Import Categories ---
    with tab2:
        st.subheader("1. Download Category Template")
        cols = ["name"]
        excel_data, file_name = generate_excel_template(cols, "category_import_template.xlsx")
        st.download_button(
            label="Download Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("2. Upload Completed File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="cat_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                # --- NEW VALIDATION LOGIC ---
                errors = []
                if 'name' not in df.columns:
                    errors.append("Missing required column: 'name'")
                else:
                    # Check for empty names
                    for i, row in df.iterrows():
                        if not row['name']:
                            errors.append(f"Row {i+2}: 'name' cannot be empty.")
                    
                    # Check for duplicates against DB
                    db_cats = get_all_categories()['name'].tolist()
                    for i, row in df.iterrows():
                        if row['name'] in db_cats:
                            errors.append(f"Row {i+2}: Category '{row['name']}' already exists in the database.")

                if errors:
                    st.error(f"Found {len(errors)} data errors. Please fix in your file and re-upload:")
                    st.json(errors[:10])
                else:
                    st.success("File validation passed!")
                    st.dataframe(df)
                    if st.button("Import Categories"):
                        conn = get_db_connection()
                        try:
                            with st.spinner("Importing..."):
                                df.to_sql("expense_categories", conn, if_exists="append", index=False)
                            st.success(f"Successfully imported {len(df)} categories.")
                            clear_cache()
                        except Exception as e:
                            st.error(f"Error importing to database: {e}. Check for duplicates in your file.")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # --- Tab 3: Import Expenses ---
    with tab3:
        st.subheader("1. Download Expense Template")
        st.markdown("In the template, use the Category *Name* (e.g., 'Office Supplies').")
        cols = ["expense_date", "description", "amount", "category_name"]
        excel_data, file_name = generate_excel_template(cols, "expense_import_template.xlsx")
        st.download_button(
            label="Download Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("2. Upload Completed File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="exp_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                # --- NEW VALIDATION LOGIC ---
                errors = []
                required_cols = ["expense_date", "description", "amount", "category_name"]
                for col in required_cols:
                    if col not in df.columns:
                        errors.append(f"Missing required column: '{col}'")
                
                if errors:
                    st.error("File format error. Please fix and re-upload:")
                    st.json(errors)
                else:
                    # Get mappings
                    cat_df = get_all_categories()
                    cat_map = {row['name']: row['id'] for _, row in cat_df.iterrows()}
                    
                    for i, row in df.iterrows():
                        # Validate data types
                        try:
                            pd.to_datetime(row['expense_date'])
                        except:
                            errors.append(f"Row {i+2}: 'expense_date' is not a valid date.")
                        try:
                            pd.to_numeric(row['amount'])
                        except:
                            errors.append(f"Row {i+2}: 'amount' is not a valid number.")
                        # Validate foreign keys
                        if row['category_name'] not in cat_map:
                            errors.append(f"Row {i+2}: Category '{row['category_name']}' not found in database.")
                    
                    if errors:
                        st.error(f"Found {len(errors)} data errors. Please fix in your file and re-upload:")
                        st.json(errors[:10])
                    else:
                        st.success("File validation passed!")
                        st.dataframe(df)
                        if st.button("Import Expenses"):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            imported_count = 0

                            with st.spinner("Processing and importing expenses..."):
                                for _, row in df.iterrows():
                                    cat_id = cat_map.get(row['category_name'])
                                    
                                    cursor.execute(
                                        """
                                        INSERT INTO company_expenses (expense_date, description, amount, category_id)
                                        VALUES (?, ?, ?, ?)
                                        """,
                                        (pd.to_datetime(row['expense_date']).strftime('%Y-%m-%d'), row['description'], row['amount'], cat_id)
                                    )
                                    imported_count += 1
                            
                            conn.commit()
                            st.success(f"Successfully imported {imported_count} expense records.")
                            clear_cache()
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # --- Tab 4: Import Ledger Entries ---
    with tab4:
        st.subheader("1. Download Ledger Template")
        st.markdown("In the template, use the Employee *Name* (e.g., 'Alice Smith').")
        cols = ["employee_name", "entry_date", "description", "debit", "credit"]
        excel_data, file_name = generate_excel_template(cols, "ledger_import_template.xlsx")
        st.download_button(
            label="Download Template",
            data=excel_data,
            file_name=file_name,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
        st.subheader("2. Upload Completed File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="led_upload")

        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file).fillna(0) # Fill NaNs with 0
                
                # --- NEW VALIDATION LOGIC ---
                errors = []
                required_cols = ["employee_name", "entry_date", "description", "debit", "credit"]
                for col in required_cols:
                    if col not in df.columns:
                        errors.append(f"Missing required column: '{col}'")

                if errors:
                    st.error("File format error. Please fix and re-upload:")
                    st.json(errors)
                else:
                    emp_df = get_all_employees()
                    emp_map = {row['name']: row['id'] for _, row in emp_df.iterrows()}
                    
                    for i, row in df.iterrows():
                        # Validate data types
                        try:
                            pd.to_datetime(row['entry_date'])
                        except:
                            errors.append(f"Row {i+2}: 'entry_date' is not a valid date.")
                        try:
                            pd.to_numeric(row['debit'])
                        except:
                            errors.append(f"Row {i+2}: 'debit' is not a valid number.")
                        try:
                            pd.to_numeric(row['credit'])
                        except:
                            errors.append(f"Row {i+2}: 'credit' is not a valid number.")
                        if row['debit'] != 0 and row['credit'] != 0:
                            errors.append(f"Row {i+2}: Cannot have both 'debit' and 'credit' in the same row.")
                        # Validate foreign keys
                        if row['employee_name'] not in emp_map:
                            errors.append(f"Row {i+2}: Employee '{row['employee_name']}' not found in database.")
                    
                    if errors:
                        st.error(f"Found {len(errors)} data errors. Please fix in your file and re-upload:")
                        st.json(errors[:10])
                    else:
                        st.success("File validation passed!")
                        st.dataframe(df)
                        if st.button("Import Ledger Entries"):
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            imported_count = 0

                            with st.spinner("Processing and importing ledger entries..."):
                                for _, row in df.iterrows():
                                    emp_id = emp_map.get(row['employee_name'])
                                    
                                    cursor.execute(
                                        """
                                        INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit)
                                        VALUES (?, ?, ?, ?, ?)
                                        """,
                                        (emp_id, pd.to_datetime(row['entry_date']).strftime('%Y-%m-%d'), row['description'], row['debit'], row['credit'])
                                    )
                                    imported_count += 1
                            
                            conn.commit()
                            st.success(f"Successfully imported {imported_count} ledger entries.")
                            clear_cache()
            except Exception as e:
                st.error(f"Error reading file: {e}")

# --- Main App ---
def main():
    # --- MODIFICATION: Set page config with logo ---
    try:
        page_icon_img = Image.open('logo.png')
    except FileNotFoundError:
        page_icon_img = None # Fallback
    
    st.set_page_config(page_title=f"{COMPANY_NAME} App", layout="wide", page_icon=page_icon_img)
    
    # --- NEW: Add custom CSS for UI ---
    st.markdown("""
        <style>
            /* --- Brand Colors --- */
            :root {
                --brand-blue: #004A99;
                --brand-blue-light: #E6F0FF;
                --background-color: #F4F7FC;
                --sidebar-background: #FFFFFF;
                --card-background: #FFFFFF;
                --text-color: #0F172A;
                --title-color: #004A99;
                --border-color: #E2E8F0;
                --shadow: 0 4px 12px rgba(0, 74, 153, 0.08);
            }
            
            /* --- General App --- */
            .stApp {
                background-color: var(--background-color);
                color: var(--text-color);
            }
            
            /* --- Titles --- */
            h1 {
                color: var(--title-color) !important;
            }
            
            /* --- Buttons --- */
            .stButton > button {
                border: 2px solid var(--brand-blue);
                background-color: var(--brand-blue);
                color: white;
                border-radius: 8px;
                transition: all 0.2s;
            }
            .stButton > button:hover {
                background-color: white;
                color: var(--brand-blue);
                border-color: var(--brand-blue);
            }
            .stButton > button[kind="primary"] {
                border: 2px solid #D32F2F; /* Red for delete */
                background-color: #D32F2F;
            }
            .stButton > button[kind="primary"]:hover {
                background-color: white;
                color: #D32F2F;
            }
            
            /* --- Forms & Cards --- */
            div[data-testid="stMetric"],
            div[data-testid="stForm"],
            div[data-testid="stExpander"],
            .stDataFrame {
                border-radius: 10px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
                background-color: var(--card-background);
            }
            div[data-testid="stMetric"] {
                padding: 20px 25px;
            }
            div[data-testid="stForm"] {
                padding: 25px;
            }
            
            /* --- Sidebar --- */
            div[data-testid="stSidebarUserContent"] {
                background-color: var(--sidebar-background);
                border-radius: 10px;
                margin: 10px;
                box-shadow: var(--shadow);
                padding: 20px;
            }
            
            /* --- Tabs --- */
            button[data-baseweb="tab"] {
                border-radius: 8px 8px 0 0;
            }
            button[data-baseweb="tab"][aria-selected="true"] {
                background-color: var(--brand-blue-light);
                color: var(--brand-blue);
                border-bottom: 2px solid var(--brand-blue);
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize DB
    init_db()
    
    # --- Sidebar Navigation ---
    with st.sidebar:
        # Add Logo
        if os.path.exists('logo.png'):
            st.image('logo.png', use_column_width=True)
        else:
            st.warning("logo.png not found. Please add it to the app folder.")
            
        st.title(f"{COMPANY_NAME} Portal")
        
        PAGES = {
            "Dashboard": page_dashboard,
            "Manage Employees": page_employee_management,
            "Expense Management": page_expense_management,
            "Salary Management": page_salary_management,
            "Employee Ledger": page_employee_ledger,
            "Download Reports": page_reporting,
            "Data Import": page_data_import,
        }
        
        if "page" not in st.session_state:
            st.session_state.page = "Dashboard"

        def set_page(page_name):
            st.session_state.page = page_name

        for page_name, page_func in PAGES.items():
            st.button(page_name, on_click=set_page, args=(page_name,), use_container_width=True)
            
        st.divider()
        st.info(f"Version 2.1\n{DEVELOPER_INFO}")

    # Run the selected page function
    page_function = PAGES[st.session_state.page]
    page_function()

if __name__ == "__main__":
    main()
