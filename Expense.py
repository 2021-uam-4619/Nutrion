import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
from PIL import Image
import uuid # For linked deletes

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# --- PDF Class with Header/Footer (MODIFIED) ---
class PDF(FPDF):
    def header(self):
        # Professional Header (Logo Left, Title Right)
        if os.path.exists('logo.png'):
            try:
                img_width = 60 # Larger logo
                self.image('logo.png', x=self.l_margin, y=10, w=img_width)
            except Exception as e:
                pass # Ignore if logo file is corrupted
        
        title_x_pos = self.l_margin + 60 + 5 # Position title right of logo
        self.set_font('Arial', 'B', 20)
        self.set_x(title_x_pos)
        # Get title text from instance, default to 'Report'
        title = getattr(self, 'title_text', 'Report')
        self.cell(0, 15, f"{COMPANY_NAME} - {title}", 0, 1, 'L')
        
        self.set_font('Arial', '', 10)
        self.set_x(title_x_pos)
        self.cell(0, 8, f"Report Date: {date.today().strftime('%B %d, %Y')}", 0, 1, 'L')
        
        self.ln(20) # Move down 20mm after header

    def footer(self):
        footer_width = self.w - self.l_margin - self.r_margin
        
        # --- MODIFICATION: Signature ABOVE the line (based on image_bcd23d.png) ---
        
        # 1. Place signature image first, 4cm from bottom
        if os.path.exists('Asim Siganture.jpg'):
            sig_width = 30 # smaller signature
            # Position it above the "Prepared by" line
            sig_x_pos = self.l_margin + 30 # Indent a bit
            sig_y_pos = -40 # 4cm from bottom
            try:
                self.image('Asim Siganture.jpg', x=sig_x_pos, y=sig_y_pos, w=sig_width)
            except Exception as e:
                # Fallback if image is corrupted or invalid
                pass 

        # 2. Place text lines, 3cm from bottom
        self.set_y(-30) 
        self.set_font('Arial', '', 10)
        
        # --- Left Side: Prepared by ---
        text = "Prepared by: _______________"
        self.cell(footer_width / 2, 10, text, 0, 0, 'L')
        
        # --- Right Side: Approved by ---
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
        # --- NEW DYNAMIC WIDTH LOGIC ---
        self.set_font('Arial', 'B', 8)
        self.set_fill_color(220, 220, 220) # Light grey header
        
        total_width = self.w - self.l_margin - self.r_margin
        
        # Define weights for columns
        col_weights = {}
        total_weight = 0
        
        # Set base weights
        for col in df.columns:
            col_lower = col.lower()
            if 'description' in col_lower or 'name' in col_lower or 'title' in col_lower:
                weight = 3.5 # High weight
            elif 'date' in col_lower or 'category' in col_lower:
                weight = 1.5 # Medium weight
            else: # ID, Amount, Salary, etc.
                weight = 1.0 # Standard weight
            
            col_weights[col] = weight
            total_weight += weight
            
        # Calculate actual widths
        col_widths = {col: (total_width * weight) / total_weight for col, weight in col_weights.items()}

        # Draw Header
        for col in df.columns:
            self.cell(col_widths[col], 7, col, 1, 0, 'C', 1)
        self.ln()
        
        # Set data style
        self.set_font('Arial', '', 8)
        
        # Draw Data Rows
        for index, row in df.iterrows():
            # Check cell height to handle word wrap
            max_height = 6 # Min height
            for col in df.columns:
                val = str(row[col])
                if pd.isna(row[col]): val = ""
                
                # Calculate lines needed for this cell
                lines = self.multi_cell(col_widths[col], 6, val, 0, 'L', split_only=True)
                cell_lines = len(lines)
                max_height = max(max_height, cell_lines * 6)

            # Store current position
            x_start = self.get_x()
            y_start = self.get_y()
            
            # Draw cells with the calculated max height
            for col in df.columns:
                val = row[col]
                
                # Handle formatting
                if pd.isna(val):
                    cell_text = ""
                elif isinstance(val, (int, float)) and col.lower() in ['amount', 'salary', 'deductions', 'net salary', 'debit', 'credit', 'balance', 'deduction / advance (-)', 'payment / bonus (+)']:
                    cell_text = f"{val:,.2f}"
                else:
                    cell_text = str(val)
                
                # Align numbers to the right
                align = 'L'
                if isinstance(val, (int, float)):
                    align = 'R'
                    
                # Store position, draw cell, reset position
                current_x = self.get_x()
                current_y = self.get_y()
                self.multi_cell(col_widths[col], 6, cell_text, 1, align)
                self.set_xy(current_x + col_widths[col], current_y)
            
            # Move to the next line based on the max height
            self.set_xy(x_start, y_start + max_height)
            
        # Draw Totals Row
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
            
            # Find the first column that needs a total
            first_total_col = len(df.columns)
            
            for i, col in enumerate(df.columns):
                if col in totals_cols:
                    first_total_col = i
                    break
                    
            # Add "GRAND TOTAL" label, aligned right
            total_label_width = sum(col_widths[col] for col in df.columns[:first_total_col])
            
            if first_total_col == 0:
                 # If total is in first col, just write in that cell
                pass
            else:
                self.cell(total_label_width, 7, "GRAND TOTAL", 1, 0, 'R', 1)

            # Add the calculated totals
            for col in df.columns[first_total_col:]:
                col_width = col_widths[col]
                
                if col == df.columns[first_total_col] and first_total_col == 0:
                     # Handle case where total is in first column
                    cell_text = f"GRAND TOTAL: {total_values[col]:,.2f}" if col in total_values else "GRAND TOTAL"
                    self.cell(col_width, 7, cell_text, 1, 0, 'R', 1)
                elif col in total_values and total_values[col] is not None:
                    cell_text = f"{total_values[col]:,.2f}"
                    self.cell(col_width, 7, cell_text, 1, 0, 'R', 1)
                else:
                    self.cell(col_width, 7, "", 1, 0, 'C', 1) # Blank cell
            self.ln()


# --- Database Initialization ---
@st.cache_resource
def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables."""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Employees Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            designation TEXT,
            salary REAL DEFAULT 0,
            bank TEXT,
            account_title TEXT,
            account_no TEXT,
            join_date TEXT
        )
    ''')
    
    # Expense Categories Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')
    
    # Company Expenses Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT,
            amount REAL NOT NULL,
            expense_date DATE NOT NULL,
            category_id INTEGER,
            linked_id TEXT UNIQUE, -- For cascade deletes
            FOREIGN KEY (category_id) REFERENCES expense_categories (id) ON DELETE SET NULL
        )
    ''')
    
    # Employee Ledger Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            entry_date DATE NOT NULL,
            description TEXT,
            debit REAL DEFAULT 0,
            credit REAL DEFAULT 0,
            linked_id TEXT UNIQUE, -- For cascade deletes
            FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
        )
    ''')
    
    # --- Add 'linked_id' columns if they don't exist (for existing users) ---
    # This ensures smooth updates for users with older db files
    try:
        c.execute("ALTER TABLE company_expenses ADD COLUMN linked_id TEXT UNIQUE")
    except sqlite3.OperationalError:
        pass # Column already exists
    try:
        c.execute("ALTER TABLE employee_ledger ADD COLUMN linked_id TEXT UNIQUE")
    except sqlite3.OperationalError:
        pass # Column already exists
    
    conn.commit()

# --- Helper Functions ---
@st.cache_data(ttl=60)
def get_dashboard_metrics():
    """Fetches key metrics for the dashboard."""
    conn = get_db_connection()
    try:
        total_employees = conn.execute("SELECT COUNT(id) FROM employees").fetchone()[0]
        
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
        return {"total_employees": 0, "total_expenses": 0, "total_categories": 0}

@st.cache_data(ttl=60)
def get_all_employees():
    """Fetches all employees as a DataFrame."""
    conn = get_db_connection()
    # MODIFIED: Parse join_date as date object for data_editor
    try:
        df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn, parse_dates=["join_date"])
    except pd.errors.ParserError:
        st.error("Error reading 'join_date' from database. Please check for invalid date formats.")
        df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
        df['join_date'] = pd.to_datetime(df['join_date'], errors='coerce')
    except Exception as e:
        st.error(f"Error fetching employees: {e}")
        df = pd.DataFrame(columns=["id", "name", "designation", "salary", "bank", "account_title", "account_no", "join_date"])
    return df

@st.cache_data(ttl=60)
def get_all_categories():
    """Fetches all expense categories as a DataFrame."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)
    return df

def clear_cache():
    """Clears all streamlit cache."""
    st.cache_data.clear()

def generate_excel_template(columns, filename):
    """Creates a blank Excel template for data import."""
    df = pd.DataFrame(columns=columns)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Import')
    output.seek(0)
    return output, filename

# --- Session State Date Handling ---
def persist_date(key, default_value):
    """Ensures a date value is saved in session state."""
    if key not in st.session_state:
        st.session_state[key] = default_value
    # Ensure it's a date object, not string
    if isinstance(st.session_state[key], str):
        try:
            st.session_state[key] = datetime.strptime(st.session_state[key], '%Y-%m-%d').date()
        except ValueError:
            st.session_state[key] = default_value

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
    if c3.button("Salary Management", use_container_width=True):
        st.session_state.page = "Salary Management"
        st.rerun()

# --- Page: Employee Management (Requirement 4) ---
def page_employee_management():
    st.title("Manage Employees")
    
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
    
    st.subheader("Edit or Delete Employees")
    st.text("Use this table to edit, add, or delete employees. Click 'Save Changes' to update the database.")
    
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
            "join_date": st.column_config.DateColumn("Join Date", format="YYYY-MM-DD") # Config for editor
        }
        
        edited_df = st.data_editor(
            employees_df,
            column_config=column_config,
            num_rows="dynamic",
            use_container_width=True,
            key="employee_editor"
        )
        
        if st.button("Save Employee Changes"):
            conn = get_db_connection()
            cursor = conn.cursor()
            
            try:
                db_ids = set(employees_df['id'])
                edited_ids = set(edited_df.dropna(subset=['id'])['id'])
                
                # --- Handle Deletions ---
                deleted_ids = db_ids - edited_ids
                if deleted_ids:
                    for emp_id in deleted_ids:
                        cursor.execute("DELETE FROM employees WHERE id = ?", (int(emp_id),))
                    st.toast(f"Deleted {len(deleted_ids)} employee(s) and their ledger entries.")
                
                # --- Handle Additions/Updates ---
                for index, row in edited_df.iterrows():
                    join_date_str = None
                    if pd.notna(row['join_date']):
                        # Convert date object back to string for database
                        try:
                            join_date_str = row['join_date'].strftime('%Y-%m-%d')
                        except AttributeError: # Handle if it's already a string
                            join_date_str = str(row['join_date']).split(" ")[0]
                    
                    if pd.isna(row['id']):
                        # Add new row
                        cursor.execute(
                            """
                            INSERT INTO employees (name, designation, salary, bank, account_title, account_no, join_date)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (row['name'], row['designation'], row['salary'], row['bank'], row['account_title'], row['account_no'], join_date_str)
                        )
                    else:
                        # Update existing row
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
        st.dataframe(pd.DataFrame(columns=["id", "name", "designation", "salary"])) # Show empty on error

# --- Page: Expense Management (Requirement 3, 4, 10, 11) ---
def page_expense_management():
    st.title("Expense Management")

    # --- Log New Expense (Req 3) ---
    st.subheader("Log New Company Expense")
    
    # Get categories for dropdown
    categories_df = get_all_categories()
    category_list = {row['id']: row['name'] for index, row in categories_df.iterrows()}
    
    # Get employees for dropdown
    employees_df = get_all_employees()
    employee_list = {row['id']: row['name'] for index, row in employees_df.iterrows()}
    
    if not category_list:
        st.warning("No expense categories found. Please add categories below before logging expenses.", icon="⚠️")
        
    with st.form("new_expense_form", clear_on_submit=True):
        
        # --- NEW: Link to Employee ---
        is_employee_payment = st.checkbox("Is this expense a payment to an employee? (Links to ledger)")
        
        emp_id = None
        if is_employee_payment:
            if not employee_list:
                st.error("No employees found. Cannot link to employee.")
                is_employee_payment = False
            else:
                emp_id = st.selectbox("Select Employee", options=list(employee_list.keys()), format_func=lambda x: employee_list[x])

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
            elif is_employee_payment and not emp_id:
                st.error("Please select an employee for this linked payment.")
            else:
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    
                    linked_id = None
                    
                    # --- NEW: Dual-Insert Logic ---
                    if is_employee_payment:
                        linked_id = str(uuid.uuid4()) # Generate a unique ID for linking
                        
                        # 1. Insert into employee ledger as a DEBIT
                        ledger_desc = f"Company-Paid Expense: {description}"
                        cursor.execute(
                            """
                            INSERT INTO employee_ledger (employee_id, entry_date, description, debit, credit, linked_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (emp_id, str(expense_date), ledger_desc, amount, 0, linked_id)
                        )
                        
                        # 2. Log the company expense with employee name
                        expense_desc = f"(Employee: {employee_list[emp_id]}) {description}"
                        cursor.execute(
                            """
                            INSERT INTO company_expenses (description, amount, expense_date, category_id, linked_id)
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (expense_desc, amount, str(expense_date), category_id, linked_id)
                        )
                        st.success("Expense logged and linked to employee ledger.")
                        
                    else:
                        # --- Original Logic ---
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
    st.text("Select an expense ID from the table to delete or edit it.")
    try:
        conn = get_db_connection()
        # --- FIX: Removed bad comment ---
        expenses_df = pd.read_sql_query(
            """
            SELECT 
                ce.id, 
                ce.expense_date, 
                ce.description, 
                ce.amount, 
                ec.name as category,
                ce.category_id,
                ce.linked_id
            FROM company_expenses ce
            LEFT JOIN expense_categories ec ON ce.category_id = ec.id
            ORDER BY ce.expense_date DESC
            """, conn
        )

        if expenses_df.empty:
            st.info("No expenses logged yet.")
        else:
            cols_to_show = ['id', 'expense_date', 'description', 'amount', 'category']
            
            # --- FIX: Added column_config to widen description ---
            st.dataframe(
                expenses_df[cols_to_show], 
                use_container_width=True, 
                hide_index=True,
                column_config={
                    "description": st.column_config.TextColumn("Description", width="large")
                }
            )
            
            st.subheader("Delete or Edit Expense")
            expense_ids = expenses_df['id'].tolist()
            expense_to_edit = st.selectbox("Select Expense ID to Manage", options=expense_ids)
            
            if expense_to_edit: # Check if an ID is selected
                expense_details = expenses_df.loc[expenses_df['id'] == expense_to_edit].iloc[0]
                linked_id = expense_details['linked_id']
                
                # --- MODIFICATION: Cascade Delete ---
                if st.button(f"Delete Expense ID {expense_to_edit}", type="primary"):
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        
                        # 1. Delete from company_expenses
                        cursor.execute("DELETE FROM company_expenses WHERE id = ?", (int(expense_to_edit),))
                        
                        # 2. If it's linked, delete from employee_ledger too
                        if linked_id:
                            cursor.execute("DELETE FROM employee_ledger WHERE linked_id = ?", (linked_id,))
                            st.success(f"Expense ID {expense_to_edit} deleted from expenses AND employee ledger.")
                        else:
                            st.success(f"Expense ID {expense_to_edit} deleted.")
                            
                        conn.commit()
                        clear_cache()
                        st.rerun()
                    except Exception as e:
                        conn.rollback()
                        st.error(f"Error deleting: {e}")
                
                # Edit Form
                with st.expander("Edit Expense Details"):
                    if linked_id:
                        st.warning("This is a linked expense. Editing it here will **not** update the employee's ledger. To edit safely, please delete this entry and create a new one.", icon="⚠️")
                    
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
                                index=default_index,
                                disabled=not cat_ids
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
    st.text("Use this table to add, rename, or delete expense categories.")
    
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
                
                deleted_ids = db_ids - edited_ids
                if deleted_ids:
                    for cat_id in deleted_ids:
                        cursor.execute("DELETE FROM expense_categories WHERE id = ?", (int(cat_id),))
                    st.toast(f"Deleted {len(deleted_ids)} category(s).")
                
                for index, row in edited_cats_df.iterrows():
                    if not row['name']:
                        st.error(f"Row {index} 'name' cannot be empty. Aborting save.")
                        raise Exception("Category name cannot be empty.")
                        
                    if pd.isna(row['id']):
                        cursor.execute("INSERT INTO expense_categories (name) VALUES (?)", (row['name'],))
                    else:
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
    
    st.text("Follow these steps to process monthly salaries:\n"
            "1. Generate Monthly Salary Credits: Run this first.\n"
            "2. View & Download Salary Sheet: After credits are generated, use this.\n"
            "3. Generate Individual Salary Slip: Download a PDF slip for one employee.")

    # --- 1. Generate Monthly Salary Credits ---
    st.subheader("1. Generate Monthly Salary Credits")
    st.warning("Run this **only once** per month. Running it again for the same month will create duplicate entries.")
    
    today = date.today()
    # --- NEW: Use session state for dates ---
    if 'salary_month' not in st.session_state:
        st.session_state.salary_month = today.month
    if 'salary_year' not in st.session_state:
        st.session_state.salary_year = today.year
    
    with st.form("generate_salaries_form"):
        cols = st.columns(2)
        salary_month = cols[0].number_input("For Month", min_value=1, max_value=12, key="salary_month")
        salary_year = cols[1].number_input("For Year", min_value=2020, max_value=2100, key="salary_year")
        
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
                    entry_date = date(salary_year, salary_month, 1)
                    
                    for index, emp in employees.iterrows():
                        description = f"Monthly Salary Credit for {entry_date.strftime('%B %Y')}"
                        
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
    
    # --- NEW: Use session state for dates ---
    persist_date('sheet_start', today.replace(day=1))
    persist_date('sheet_end', today)
    
    cols = st.columns(2)
    sheet_start = cols[0].date_input("Start Date", key="sheet_start")
    sheet_end = cols[1].date_input("End Date", key="sheet_end")
    
    try:
        df = get_salary_sheet(sheet_start, sheet_end)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if not df.empty:
            pdf_data = generate_salary_sheet_pdf(df, sheet_start, sheet_end)
            st.download_button(
                label="Download Salary Sheet as PDF (Req 1)",
                data=pdf_data,
                file_name=f"Salary_Sheet_{sheet_start}_to_{sheet_end}.pdf",
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

    # --- NEW: Use session state for dates ---
    persist_date('slip_start', today.replace(day=1))
    persist_date('slip_end', today)
    
    if 'slip_emp_id' not in st.session_state or st.session_state.slip_emp_id not in employee_list:
        st.session_state.slip_emp_id = list(employee_list.keys())[0]

    cols = st.columns(3)
    slip_emp_id = cols[0].selectbox(
        "Select Employee", 
        options=list(employee_list.keys()), 
        format_func=lambda x: employee_list[x],
        key="slip_emp_id" # Use key to save state
    )
    slip_start = cols[1].date_input("Period Start Date", key="slip_start")
    slip_end = cols[2].date_input("Period End Date", key="slip_end")
    
    if st.button("Generate Individual Slip"):
        try:
            pdf_data = generate_individual_slip_pdf(slip_emp_id, slip_start, slip_end)
            st.download_button(
                label=f"Download Slip for {employee_list[slip_emp_id]}",
                data=pdf_data,
                file_name=f"Salary_Slip_{employee_list[slip_emp_id]}_{slip_start}_to_{slip_end}.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF slip: {e}")


@st.cache_data(ttl=60)
def get_salary_sheet(start_date, end_date):
    """Calculates the salary sheet for all employees for a given period."""
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
        (COALESCE(SUM(el.credit), 0) - COALESCE(SUM(el.debit), 0)) AS "Net Salary"
    FROM employees e
    LEFT JOIN employee_ledger el ON e.id = el.employee_id
        AND el.entry_date BETWEEN ? AND ?
    GROUP BY e.id
    ORDER BY e.name
    """
    df = pd.read_sql_query(query, conn, params=(str(start_date), str(end_date)))
    return df

def generate_salary_sheet_pdf(df, start_date, end_date):
    """Generates a PDF for the main salary sheet."""
    pdf = PDF('L', 'mm', 'A4') # Landscape
    pdf.title_text = f"Salary Sheet"
    pdf.add_page()
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Period: {start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}", 0, 1, 'L')
    pdf.ln(5)
    pdf.add_table(df, totals_cols=["Base Salary", "Other Credits (Bonus/Reimb.)", "Deductions (Advance)", "Net Salary"])
    return pdf.output(dest='S').encode('latin-1')

def generate_individual_slip_pdf(employee_id, start_date, end_date):
    """Generates a detailed PDF salary slip for a single employee."""
    conn = get_db_connection()
    
    emp = conn.execute("SELECT * FROM employees WHERE id = ?", (employee_id,)).fetchone()
    if not emp:
        raise Exception("Employee not found.")
        
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
    
    total_credits = ledger_df['Credits (+)'].sum()
    total_deductions = ledger_df['Deductions (-)'].sum()
    net_salary = total_credits - total_deductions
    
    pdf = PDF('P', 'mm', 'A4') # Portrait
    pdf.title_text = f"Salary Slip - {emp['name']}"
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Employee Information", 0, 1, 'L')
    pdf.set_font('Arial', '', 11)
    
    info_data = {
        "Employee Name:": emp['name'],
        "Designation:": emp['designation'],
        "Pay Period:": f"{start_date.strftime('%d-%m-%Y')} to {end_date.strftime('%d-%m-%Y')}",
        "Bank:": f"{emp['bank']} (A/C: {emp['account_no']})"
    }
    
    for key, val in info_data.items():
        pdf.set_font('Arial', 'B', 11)
        pdf.cell(40, 8, key, 0, 0, 'L')
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, str(val), 0, 1, 'L')

    pdf.ln(10)
    
    # --- Earnings ---
    earnings_df = ledger_df[ledger_df['Credits (+)'] > 0][['Date', 'Description', 'Credits (+)']]
    deductions_df = ledger_df[ledger_df['Deductions (-)'] > 0][['Date', 'Description', 'Deductions (-)']]

    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Earnings & Credits", 0, 1, 'L')
    if not earnings_df.empty:
        pdf.add_table(earnings_df, totals_cols=['Credits (+)'])
    else:
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 10, "No earnings entries this period.", 0, 1, 'L')

    pdf.ln(10)

    # --- Deductions ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Advances & Deductions", 0, 1, 'L')
    if not deductions_df.empty:
        pdf.add_table(deductions_df, totals_cols=['Deductions (-)'])
    else:
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 10, "No deduction entries this period.", 0, 1, 'L')
        
    pdf.ln(10)
    
    # --- Summary ---
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Salary Summary", 0, 1, 'L')
    
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
    
    # --- Net Salary (Highlighted) ---
    pdf.set_font('Arial', 'B', 12)
    pdf.set_fill_color(220, 220, 220)
    pdf.cell(90, 10, "Net Salary Payable:", 'LB', 0, 'R', 1)
    pdf.cell(90, 10, f"{net_salary:,.2f} PKR", 'RB', 1, 'L', 1)
    
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
    # --- NEW: Use session state for dates ---
    persist_date('report_start_date', today.replace(day=1))
    persist_date('report_end_date', today)
    
    cols = st.columns(2)
    report_start_date = cols[0].date_input("Start Date", key="report_start_date")
    report_end_date = cols[1].date_input("End Date", key="report_end_date")
    
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
                    LEFT JOIN expense_categories ec ON ce.category_id = ce.id
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
                totals_cols = None
            
            # Fix: Use con=conn for pandas
            df = pd.read_sql_query(query, conn, params=params)
            
            if df.empty:
                st.warning("No data found for the selected criteria.")
                return

            pdf = PDF('P', 'mm', 'A4')
            pdf.title_text = report_title
            pdf.add_page()
            pdf.add_table(df, totals_cols=totals_cols)
            
            pdf_data = pdf.output(dest='S').encode('latin-1')
            
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

    # --- Import Employees ---
    with tab1:
        st.subheader("1. Download Employee Template")
        cols = ["name", "designation", "salary", "bank", "account_title", "account_no", "join_date"]
        excel_data, file_name = generate_excel_template(cols, "employee_import_template.xlsx")
        st.download_button(label="Download Template", data=excel_data, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.subheader("2. Upload Completed File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="emp_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                errors = []
                required_cols = ["name", "designation", "salary", "bank", "account_title", "account_no", "join_date"]
                for col in required_cols:
                    if col not in df.columns:
                        errors.append(f"Missing required column: '{col}'")
                
                if errors:
                    st.error("File format error. Please fix and re-upload:")
                    st.json(errors)
                else:
                    # --- Validation Logic ---
                    for i, row in df.iterrows():
                        if not row['name']:
                            errors.append(f"Row {i+2}: 'name' cannot be empty.")
                        try: pd.to_numeric(row['salary'])
                        except: errors.append(f"Row {i+2}: 'salary' is not a valid number (Value: {row['salary']}).")
                        try: pd.to_datetime(row['join_date'])
                        except: errors.append(f"Row {i+2}: 'join_date' is not a valid date (Value: {row['join_date']}). Should be YYYY-MM-DD.")
                    
                    if errors:
                        st.error(f"Found {len(errors)} data errors. Please fix in your file and re-upload:")
                        st.json(errors[:10])
                    else:
                        st.success("File validation passed!")
                        st.dataframe(df)
                        if st.button("Import Employees"):
                            conn = get_db_connection()
                            try:
                                with st.spinner("Importing..."):
                                    df['join_date'] = pd.to_datetime(df['join_date']).dt.strftime('%Y-%m-%d')
                                    df.to_sql("employees", conn, if_exists="append", index=False)
                                st.success(f"Successfully imported {len(df)} employee records.")
                                clear_cache()
                            except Exception as e:
                                st.error(f"Error importing to database: {e}. Check if data is valid.")
                
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # --- Import Categories ---
    with tab2:
        st.subheader("1. Download Category Template")
        cols = ["name"]
        excel_data, file_name = generate_excel_template(cols, "category_import_template.xlsx")
        st.download_button(label="Download Template", data=excel_data, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.subheader("2. Upload Completed File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="cat_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                errors = []
                if 'name' not in df.columns:
                    errors.append("Missing required column: 'name'")
                else:
                    for i, row in df.iterrows():
                        if not row['name']:
                            errors.append(f"Row {i+2}: 'name' cannot be empty.")
                    
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

    # --- Import Expenses ---
    with tab3:
        st.subheader("1. Download Expense Template")
        st.markdown("In the template, use the Category *Name* (e.g., 'Office Supplies').")
        cols = ["expense_date", "description", "amount", "category_name"]
        excel_data, file_name = generate_excel_template(cols, "expense_import_template.xlsx")
        st.download_button(label="Download Template", data=excel_data, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.subheader("2. Upload Completed File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="exp_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                errors = []
                required_cols = ["expense_date", "description", "amount", "category_name"]
                for col in required_cols:
                    if col not in df.columns:
                        errors.append(f"Missing required column: '{col}'")
                
                if errors:
                    st.error("File format error. Please fix and re-upload:")
                    st.json(errors)
                else:
                    cat_df = get_all_categories()
                    cat_map = {row['name']: row['id'] for _, row in cat_df.iterrows()}
                    
                    for i, row in df.iterrows():
                        try: pd.to_datetime(row['expense_date'])
                        except: errors.append(f"Row {i+2}: 'expense_date' is not a valid date.")
                        try: pd.to_numeric(row['amount'])
                        except: errors.append(f"Row {i+2}: 'amount' is not a valid number.")
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

    # --- Import Ledger Entries ---
    with tab4:
        st.subheader("1. Download Ledger Template")
        st.markdown("In the template, use the Employee *Name* (e.g., 'Alice Smith').")
        cols = ["employee_name", "entry_date", "description", "debit", "credit"]
        excel_data, file_name = generate_excel_template(cols, "ledger_import_template.xlsx")
        st.download_button(label="Download Template", data=excel_data, file_name=file_name, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        
        st.subheader("2. Upload Completed File")
        uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx", key="led_upload")

        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file).fillna(0)
                
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
                        try: pd.to_datetime(row['entry_date'])
                        except: errors.append(f"Row {i+2}: 'entry_date' is not a valid date.")
                        try: pd.to_numeric(row['debit'])
                        except: errors.append(f"Row {i+2}: 'debit' is not a valid number.")
                        try: pd.to_numeric(row['credit'])
                        except: errors.append(f"Row {i+2}: 'credit' is not a valid number.")
                        if row['debit'] != 0 and row['credit'] != 0:
                            errors.append(f"Row {i+2}: Cannot have both 'debit' and 'credit' in the same row.")
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
    # Set page config
    try:
        page_icon_img = Image.open('logo.png')
    except Exception:
        page_icon_img = None
    
    st.set_page_config(page_title=f"{COMPANY_NAME} App", layout="wide", page_icon=page_icon_img)
    
    # --- Professional UI Styling ---
    st.markdown("""
        <style>
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
            .stApp { background-color: var(--background-color); color: var(--text-color); }
            h1 { color: var(--title-color) !important; }
            .stButton > button {
                border: 2px solid var(--brand-blue);
                background-color: var(--brand-blue);
                color: white;
                border-radius: 8px;
                transition: all 0.2s;
            }
            .stButton > button:hover { background-color: white; color: var(--brand-blue); border-color: var(--brand-blue); }
            .stButton > button[kind="primary"] { border: 2px solid #D32F2F; background-color: #D32F2F; }
            .stButton > button[kind="primary"]:hover { background-color: white; color: #D32F2F; }
            div[data-testid="stMetric"], div[data-testid="stForm"], div[data-testid="stExpander"], .stDataFrame {
                border-radius: 10px;
                box-shadow: var(--shadow);
                border: 1px solid var(--border-color);
                background-color: var(--card-background);
            }
            div[data-testid="stMetric"] { padding: 20px 25px; }
            div[data-testid="stForm"] { padding: 25px; }
            div[data-testid="stSidebarUserContent"] {
                background-color: var(--sidebar-background);
                border-radius: 10px;
                margin: 10px;
                box-shadow: var(--shadow);
                padding: 20px;
            }
            button[data-baseweb="tab"] { border-radius: 8px 8px 0 0; }
            button[data-baseweb="tab"][aria-selected="true"] {
                background-color: var(--brand-blue-light);
                color: var(--brand-blue);
                border-bottom: 2px solid var(--brand-blue);
            }
        </style>
    """, unsafe_allow_html=True)

    # Initialize the database
    init_db()
    
    # --- Sidebar Navigation ---
    with st.sidebar:
        if os.path.exists('logo.png'):
            try:
                st.image('logo.png', use_column_width=True)
            except Exception as e:
                st.warning("logo.png found but could not be loaded.")
        else:
            st.warning("logo.png not found. Please add it to the app folder.")
            
        st.title(f"{COMPANY_NAME} Portal")
        
        PAGES = {
            "Dashboard": page_dashboard,
            "Manage Employees": page_employee_management,
            "Expense Management": page_expense_management,
            "Salary Management": page_salary_management,
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
        st.info(f"Version 3.0 (PDF Fix)\n{DEVELOPER_INFO}") # Version bump

    # --- Run the selected page ---
    page_function = PAGES[st.session_state.page]
    page_function()

if __name__ == "__main__":
    main()
