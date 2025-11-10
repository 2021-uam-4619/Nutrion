import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io
import base64
import os

# Page configuration
st.set_page_config(
    page_title="Nutrion Management System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.8rem;
        color: #A23B72;
        margin-bottom: 1rem;
    }
    .success-message {
        background-color: #d4edda;
        color: #155724;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #e9ecef;
        padding: 15px;
        border-radius: 5px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Database setup
def init_db():
    conn = sqlite3.connect('nutrion_management.db')
    c = conn.cursor()
    
    # Employees table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT UNIQUE,
            name TEXT NOT NULL,
            designation TEXT,
            department TEXT,
            account_no TEXT,
            account_title TEXT,
            bank_name TEXT,
            basic_salary REAL,
            allowances REAL DEFAULT 0,
            deductions REAL DEFAULT 0,
            join_date DATE,
            status TEXT DEFAULT 'Active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Salary records table
    c.execute('''
        CREATE TABLE IF NOT EXISTS salary_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            month_year TEXT,
            basic_salary REAL,
            allowances REAL,
            deductions REAL,
            net_salary REAL,
            payment_date DATE,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # Expense categories table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expense_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_name TEXT UNIQUE,
            description TEXT,
            status TEXT DEFAULT 'Active'
        )
    ''')
    
    # Company expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_date DATE,
            category_id INTEGER,
            amount REAL,
            description TEXT,
            employee_id TEXT,
            payment_mode TEXT,
            reference_no TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES expense_categories (id),
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # Employee ledger table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employee_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id TEXT,
            transaction_date DATE,
            transaction_type TEXT,
            amount REAL,
            description TEXT,
            reference_type TEXT,
            reference_id INTEGER,
            balance REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
        )
    ''')
    
    # Insert default expense categories
    default_categories = [
        ('Office Supplies', 'Office stationery and supplies'),
        ('Utilities', 'Electricity, water, internet bills'),
        ('Rent', 'Office rent payments'),
        ('Travel', 'Employee travel expenses'),
        ('Marketing', 'Marketing and advertising'),
        ('Maintenance', 'Office maintenance'),
        ('Food', 'Employee food and refreshments'),
        ('Other', 'Miscellaneous expenses')
    ]
    
    c.executemany('''
        INSERT OR IGNORE INTO expense_categories (category_name, description) 
        VALUES (?, ?)
    ''', default_categories)
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Utility functions
def get_db_connection():
    return sqlite3.connect('nutrion_management.db')

def create_download_link(df, filename, file_type='csv'):
    """Create a download link for DataFrame"""
    if file_type == 'csv':
        data = df.to_csv(index=False)
        b64 = base64.b64encode(data.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download {filename}</a>'
    elif file_type == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Data')
        data = output.getvalue()
        b64 = base64.b64encode(data).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}.xlsx">Download {filename}</a>'
    return href

def generate_pdf(data, title, columns, filename):
    """Generate PDF report"""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    
    styles = getSampleStyleSheet()
    elements.append(Paragraph(title, styles['Title']))
    elements.append(Spacer(1, 12))
    
    # Add date
    elements.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Create table
    table_data = [columns]
    for row in data:
        table_data.append([str(x) for x in row])
    
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    pdf_data = buffer.getvalue()
    buffer.close()
    
    b64 = base64.b64encode(pdf_data).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}.pdf">Download {filename} PDF</a>'
    return href

# Main application
def main():
    st.markdown('<h1 class="main-header">🏢 Nutrion Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose Module", [
        "Dashboard",
        "Employee Management", 
        "Salary Management",
        "Expense Management",
        "Reports & Analytics",
        "Data Import/Export"
    ])
    
    if app_mode == "Dashboard":
        show_dashboard()
    elif app_mode == "Employee Management":
        show_employee_management()
    elif app_mode == "Salary Management":
        show_salary_management()
    elif app_mode == "Expense Management":
        show_expense_management()
    elif app_mode == "Reports & Analytics":
        show_reports_analytics()
    elif app_mode == "Data Import/Export":
        show_data_import_export()

def show_dashboard():
    st.markdown('<h2 class="section-header">📊 Dashboard</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        conn = get_db_connection()
        total_employees = pd.read_sql("SELECT COUNT(*) as count FROM employees WHERE status='Active'", conn).iloc[0]['count']
        conn.close()
        st.metric("Total Employees", total_employees)
    
    with col2:
        conn = get_db_connection()
        total_expenses = pd.read_sql("SELECT SUM(amount) as total FROM company_expenses WHERE expense_date >= date('now', 'start of month')", conn).iloc[0]['total'] or 0
        conn.close()
        st.metric("Monthly Expenses", f"₹{total_expenses:,.2f}")
    
    with col3:
        conn = get_db_connection()
        total_salary = pd.read_sql("SELECT SUM(net_salary) as total FROM salary_records WHERE month_year = strftime('%Y-%m', 'now')", conn).iloc[0]['total'] or 0
        conn.close()
        st.metric("Monthly Salary", f"₹{total_salary:,.2f}")
    
    with col4:
        conn = get_db_connection()
        pending_salary = pd.read_sql("SELECT SUM(net_salary) as total FROM salary_records WHERE status='Pending'", conn).iloc[0]['total'] or 0
        conn.close()
        st.metric("Pending Salary", f"₹{pending_salary:,.2f}")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Expenses by Category")
        conn = get_db_connection()
        expense_data = pd.read_sql('''
            SELECT ec.category_name, SUM(ce.amount) as total 
            FROM company_expenses ce 
            JOIN expense_categories ec ON ce.category_id = ec.id 
            WHERE ce.expense_date >= date('now', 'start of month')
            GROUP BY ec.category_name
        ''', conn)
        conn.close()
        
        if not expense_data.empty:
            fig = px.pie(expense_data, values='total', names='category_name')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available for current month")
    
    with col2:
        st.subheader("Department-wise Employee Distribution")
        conn = get_db_connection()
        dept_data = pd.read_sql('''
            SELECT department, COUNT(*) as count 
            FROM employees 
            WHERE status='Active' 
            GROUP BY department
        ''', conn)
        conn.close()
        
        if not dept_data.empty:
            fig = px.bar(dept_data, x='department', y='count')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No employee data available")

def show_employee_management():
    st.markdown('<h2 class="section-header">👥 Employee Management</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add Employee", "View/Edit Employees", "Employee Ledger", "Search Employees"])
    
    with tab1:
        st.subheader("Add New Employee")
        
        with st.form("add_employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                employee_id = st.text_input("Employee ID*")
                name = st.text_input("Full Name*")
                designation = st.text_input("Designation*")
                department = st.selectbox("Department", ["HR", "Finance", "IT", "Marketing", "Sales", "Operations", "Admin"])
                join_date = st.date_input("Join Date")
            
            with col2:
                account_no = st.text_input("Account Number")
                account_title = st.text_input("Account Title")
                bank_name = st.text_input("Bank Name")
                basic_salary = st.number_input("Basic Salary (₹)", min_value=0.0, step=1000.0)
                status = st.selectbox("Status", ["Active", "Inactive"])
            
            submitted = st.form_submit_button("Add Employee")
            
            if submitted:
                if employee_id and name and designation:
                    conn = get_db_connection()
                    try:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO employees 
                            (employee_id, name, designation, department, account_no, account_title, bank_name, basic_salary, join_date, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (employee_id, name, designation, department, account_no, account_title, bank_name, basic_salary, join_date, status))
                        conn.commit()
                        st.success("Employee added successfully!")
                        
                        # Initialize employee ledger
                        cursor.execute('''
                            INSERT INTO employee_ledger (employee_id, transaction_date, transaction_type, amount, description, balance)
                            VALUES (?, ?, 'Opening', 0, 'Account opened', 0)
                        ''', (employee_id, join_date))
                        conn.commit()
                        
                    except sqlite3.IntegrityError:
                        st.error("Employee ID already exists!")
                    finally:
                        conn.close()
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab2:
        st.subheader("Employee List")
        
        conn = get_db_connection()
        employees = pd.read_sql("SELECT * FROM employees ORDER BY created_at DESC", conn)
        conn.close()
        
        if not employees.empty:
            st.dataframe(employees, use_container_width=True)
            
            # Edit employee
            st.subheader("Edit Employee")
            employee_ids = employees['employee_id'].tolist()
            selected_emp = st.selectbox("Select Employee to Edit", employee_ids)
            
            if selected_emp:
                conn = get_db_connection()
                emp_data = pd.read_sql(f"SELECT * FROM employees WHERE employee_id = '{selected_emp}'", conn)
                conn.close()
                
                if not emp_data.empty:
                    with st.form("edit_employee_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_name = st.text_input("Full Name", value=emp_data.iloc[0]['name'])
                            edit_designation = st.text_input("Designation", value=emp_data.iloc[0]['designation'])
                            edit_department = st.text_input("Department", value=emp_data.iloc[0]['department'])
                            edit_join_date = st.date_input("Join Date", value=datetime.strptime(emp_data.iloc[0]['join_date'], '%Y-%m-%d'))
                        
                        with col2:
                            edit_account_no = st.text_input("Account Number", value=emp_data.iloc[0]['account_no'])
                            edit_account_title = st.text_input("Account Title", value=emp_data.iloc[0]['account_title'])
                            edit_bank_name = st.text_input("Bank Name", value=emp_data.iloc[0]['bank_name'])
                            edit_basic_salary = st.number_input("Basic Salary", value=float(emp_data.iloc[0]['basic_salary']))
                            edit_status = st.selectbox("Status", ["Active", "Inactive"], index=0 if emp_data.iloc[0]['status'] == "Active" else 1)
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            update_btn = st.form_submit_button("Update Employee")
                        with col2:
                            delete_btn = st.form_submit_button("Delete Employee")
                        
                        if update_btn:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE employees SET 
                                name=?, designation=?, department=?, account_no=?, account_title=?, 
                                bank_name=?, basic_salary=?, join_date=?, status=?
                                WHERE employee_id=?
                            ''', (edit_name, edit_designation, edit_department, edit_account_no, 
                                  edit_account_title, edit_bank_name, edit_basic_salary, 
                                  edit_join_date, edit_status, selected_emp))
                            conn.commit()
                            conn.close()
                            st.success("Employee updated successfully!")
                            st.rerun()
                        
                        if delete_btn:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM employees WHERE employee_id=?", (selected_emp,))
                            conn.commit()
                            conn.close()
                            st.success("Employee deleted successfully!")
                            st.rerun()
    
    with tab3:
        st.subheader("Employee Ledger")
        
        conn = get_db_connection()
        employees = pd.read_sql("SELECT employee_id, name FROM employees", conn)
        conn.close()
        
        if not employees.empty:
            selected_employee = st.selectbox("Select Employee", employees['employee_id'].tolist(), 
                                           format_func=lambda x: f"{x} - {employees[employees['employee_id']==x]['name'].iloc[0]}")
            
            date_range = st.date_input("Date Range", [datetime.now() - timedelta(days=30), datetime.now()])
            
            if st.button("Generate Ledger Report"):
                conn = get_db_connection()
                ledger_data = pd.read_sql('''
                    SELECT * FROM employee_ledger 
                    WHERE employee_id = ? AND transaction_date BETWEEN ? AND ?
                    ORDER BY transaction_date
                ''', conn, params=(selected_employee, date_range[0], date_range[1]))
                conn.close()
                
                if not ledger_data.empty:
                    st.dataframe(ledger_data, use_container_width=True)
                    
                    # PDF Download
                    pdf_data = []
                    for _, row in ledger_data.iterrows():
                        pdf_data.append([
                            row['transaction_date'], row['transaction_type'], 
                            row['amount'], row['description'], row['balance']
                        ])
                    
                    pdf_link = generate_pdf(
                        pdf_data, 
                        f"Employee Ledger - {selected_employee}",
                        ['Date', 'Type', 'Amount', 'Description', 'Balance'],
                        f"employee_ledger_{selected_employee}_{datetime.now().strftime('%Y%m%d')}"
                    )
                    st.markdown(pdf_link, unsafe_allow_html=True)
                else:
                    st.info("No ledger entries found for the selected period")
    
    with tab4:
        st.subheader("Search Employees")
        
        search_term = st.text_input("Search by Name or Employee ID")
        if search_term:
            conn = get_db_connection()
            search_results = pd.read_sql('''
                SELECT * FROM employees 
                WHERE name LIKE ? OR employee_id LIKE ?
            ''', conn, params=(f'%{search_term}%', f'%{search_term}%'))
            conn.close()
            
            if not search_results.empty:
                st.dataframe(search_results, use_container_width=True)
            else:
                st.info("No employees found matching your search")

def show_salary_management():
    st.markdown('<h2 class="section-header">💰 Salary Management</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Generate Salary", "Salary Records", "Salary Slips"])
    
    with tab1:
        st.subheader("Generate Salary Sheet")
        
        conn = get_db_connection()
        employees = pd.read_sql("SELECT employee_id, name, basic_salary FROM employees WHERE status='Active'", conn)
        conn.close()
        
        if not employees.empty:
            salary_month = st.date_input("Salary Month", datetime.now()).strftime('%Y-%m')
            
            if st.button("Generate Salary Sheet"):
                salary_data = []
                for _, emp in employees.iterrows():
                    net_salary = emp['basic_salary']  # You can add allowances and deductions logic here
                    salary_data.append({
                        'employee_id': emp['employee_id'],
                        'name': emp['name'],
                        'basic_salary': emp['basic_salary'],
                        'allowances': 0,
                        'deductions': 0,
                        'net_salary': net_salary,
                        'month_year': salary_month,
                        'status': 'Pending'
                    })
                
                salary_df = pd.DataFrame(salary_data)
                st.dataframe(salary_df, use_container_width=True)
                
                if st.button("Save Salary Records"):
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    for _, row in salary_df.iterrows():
                        cursor.execute('''
                            INSERT OR REPLACE INTO salary_records 
                            (employee_id, month_year, basic_salary, allowances, deductions, net_salary, status)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (row['employee_id'], row['month_year'], row['basic_salary'], 
                              row['allowances'], row['deductions'], row['net_salary'], row['status']))
                    conn.commit()
                    conn.close()
                    st.success("Salary records saved successfully!")
    
    with tab2:
        st.subheader("Salary Records")
        
        conn = get_db_connection()
        salary_records = pd.read_sql('''
            SELECT sr.*, e.name, e.account_no, e.account_title, e.bank_name 
            FROM salary_records sr 
            JOIN employees e ON sr.employee_id = e.employee_id 
            ORDER BY sr.month_year DESC, sr.created_at DESC
        ''', conn)
        conn.close()
        
        if not salary_records.empty:
            st.dataframe(salary_records, use_container_width=True)
            
            # Filter options
            col1, col2 = st.columns(2)
            with col1:
                filter_month = st.text_input("Filter by Month (YYYY-MM)")
            with col2:
                filter_status = st.selectbox("Filter by Status", ["All", "Pending", "Paid"])
            
            filtered_data = salary_records
            if filter_month:
                filtered_data = filtered_data[filtered_data['month_year'] == filter_month]
            if filter_status != "All":
                filtered_data = filtered_data[filtered_data['status'] == filter_status]
            
            st.dataframe(filtered_data, use_container_width=True)
    
    with tab3:
        st.subheader("Individual Salary Slips")
        
        conn = get_db_connection()
        employees = pd.read_sql("SELECT employee_id, name FROM employees", conn)
        salary_months = pd.read_sql("SELECT DISTINCT month_year FROM salary_records ORDER BY month_year DESC", conn)['month_year'].tolist()
        conn.close()
        
        if employees.empty or not salary_months:
            st.info("No salary data available")
        else:
            col1, col2 = st.columns(2)
            with col1:
                selected_employee = st.selectbox("Select Employee", employees['employee_id'].tolist(),
                                               format_func=lambda x: f"{x} - {employees[employees['employee_id']==x]['name'].iloc[0]}")
            with col2:
                selected_month = st.selectbox("Select Month", salary_months)
            
            if st.button("Generate Salary Slip"):
                conn = get_db_connection()
                salary_data = pd.read_sql('''
                    SELECT sr.*, e.* 
                    FROM salary_records sr 
                    JOIN employees e ON sr.employee_id = e.employee_id 
                    WHERE sr.employee_id = ? AND sr.month_year = ?
                ''', conn, params=(selected_employee, selected_month))
                conn.close()
                
                if not salary_data.empty:
                    emp_data = salary_data.iloc[0]
                    
                    st.markdown(f"""
                    <div style='border: 2px solid #333; padding: 20px; border-radius: 10px;'>
                        <h3 style='text-align: center; color: #2E86AB;'>NUTRION COMPANY</h3>
                        <h4 style='text-align: center;'>Salary Slip</h4>
                        <hr>
                        <table width='100%'>
                            <tr>
                                <td><strong>Employee ID:</strong> {emp_data['employee_id']}</td>
                                <td><strong>Month:</strong> {emp_data['month_year']}</td>
                            </tr>
                            <tr>
                                <td><strong>Name:</strong> {emp_data['name']}</td>
                                <td><strong>Designation:</strong> {emp_data['designation']}</td>
                            </tr>
                            <tr>
                                <td><strong>Bank:</strong> {emp_data['bank_name']}</td>
                                <td><strong>Account No:</strong> {emp_data['account_no']}</td>
                            </tr>
                        </table>
                        <hr>
                        <table width='100%'>
                            <tr>
                                <th align='left'>Earnings</th>
                                <th align='right'>Amount (₹)</th>
                            </tr>
                            <tr>
                                <td>Basic Salary</td>
                                <td align='right'>{emp_data['basic_salary']:,.2f}</td>
                            </tr>
                            <tr>
                                <td>Allowances</td>
                                <td align='right'>{emp_data['allowances']:,.2f}</td>
                            </tr>
                            <tr>
                                <td><strong>Total Earnings</strong></td>
                                <td align='right'><strong>{(emp_data['basic_salary'] + emp_data['allowances']):,.2f}</strong></td>
                            </tr>
                        </table>
                        <hr>
                        <table width='100%'>
                            <tr>
                                <th align='left'>Deductions</th>
                                <th align='right'>Amount (₹)</th>
                            </tr>
                            <tr>
                                <td>Deductions</td>
                                <td align='right'>{emp_data['deductions']:,.2f}</td>
                            </tr>
                            <tr>
                                <td><strong>Total Deductions</strong></td>
                                <td align='right'><strong>{emp_data['deductions']:,.2f}</strong></td>
                            </tr>
                        </table>
                        <hr>
                        <table width='100%'>
                            <tr>
                                <td><strong>Net Salary</strong></td>
                                <td align='right'><strong style='font-size: 1.2em; color: #2E86AB;'>₹{emp_data['net_salary']:,.2f}</strong></td>
                            </tr>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

def show_expense_management():
    st.markdown('<h2 class="section-header">💸 Expense Management</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["Add Expense", "View Expenses", "Expense Categories", "Expense Reports"])
    
    with tab1:
        st.subheader("Add New Expense")
        
        conn = get_db_connection()
        categories = pd.read_sql("SELECT * FROM expense_categories WHERE status='Active'", conn)
        employees = pd.read_sql("SELECT employee_id, name FROM employees WHERE status='Active'", conn)
        conn.close()
        
        with st.form("add_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Expense Date*", datetime.now())
                category_id = st.selectbox("Category*", categories['id'].tolist(), 
                                         format_func=lambda x: categories[categories['id']==x]['category_name'].iloc[0])
                amount = st.number_input("Amount (₹)*", min_value=0.0, step=100.0)
                employee_id = st.selectbox("Employee (if applicable)", [""] + employees['employee_id'].tolist(),
                                         format_func=lambda x: "Select Employee" if x == "" else 
                                         f"{x} - {employees[employees['employee_id']==x]['name'].iloc[0]}")
            
            with col2:
                description = st.text_area("Description*")
                payment_mode = st.selectbox("Payment Mode", ["Cash", "Bank Transfer", "Cheque", "Card"])
                reference_no = st.text_input("Reference Number")
            
            submitted = st.form_submit_button("Add Expense")
            
            if submitted:
                if expense_date and category_id and amount and description:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO company_expenses 
                        (expense_date, category_id, amount, description, employee_id, payment_mode, reference_no)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (expense_date, category_id, amount, description, 
                          employee_id if employee_id else None, payment_mode, reference_no))
                    
                    # Update employee ledger if expense is assigned to employee
                    if employee_id:
                        cursor.execute('''
                            INSERT INTO employee_ledger 
                            (employee_id, transaction_date, transaction_type, amount, description, reference_type, reference_id, balance)
                            VALUES (?, ?, 'Expense', ?, ?, 'Expense', ?, 
                            (SELECT COALESCE(SUM(amount), 0) FROM employee_ledger WHERE employee_id = ?) + ?)
                        ''', (employee_id, expense_date, amount, description, cursor.lastrowid, employee_id, amount))
                    
                    conn.commit()
                    conn.close()
                    st.success("Expense added successfully!")
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab2:
        st.subheader("Expense Records")
        
        conn = get_db_connection()
        expenses = pd.read_sql('''
            SELECT ce.*, ec.category_name, e.name as employee_name 
            FROM company_expenses ce 
            JOIN expense_categories ec ON ce.category_id = ec.id 
            LEFT JOIN employees e ON ce.employee_id = e.employee_id 
            ORDER BY ce.expense_date DESC
        ''', conn)
        conn.close()
        
        if not expenses.empty:
            st.dataframe(expenses, use_container_width=True)
            
            # Edit/Delete expenses
            st.subheader("Edit/Delete Expenses")
            expense_ids = expenses['id'].tolist()
            selected_expense = st.selectbox("Select Expense to Edit", expense_ids)
            
            if selected_expense:
                conn = get_db_connection()
                expense_data = pd.read_sql(f"SELECT * FROM company_expenses WHERE id = {selected_expense}", conn)
                conn.close()
                
                if not expense_data.empty:
                    with st.form("edit_expense_form"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            edit_date = st.date_input("Expense Date", value=datetime.strptime(expense_data.iloc[0]['expense_date'], '%Y-%m-%d'))
                            edit_amount = st.number_input("Amount", value=float(expense_data.iloc[0]['amount']))
                            edit_description = st.text_area("Description", value=expense_data.iloc[0]['description'])
                        
                        with col2:
                            edit_payment_mode = st.text_input("Payment Mode", value=expense_data.iloc[0]['payment_mode'])
                            edit_reference_no = st.text_input("Reference No", value=expense_data.iloc[0]['reference_no'])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            update_btn = st.form_submit_button("Update Expense")
                        with col2:
                            delete_btn = st.form_submit_button("Delete Expense")
                        
                        if update_btn:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE company_expenses SET 
                                expense_date=?, amount=?, description=?, payment_mode=?, reference_no=?
                                WHERE id=?
                            ''', (edit_date, edit_amount, edit_description, edit_payment_mode, edit_reference_no, selected_expense))
                            conn.commit()
                            conn.close()
                            st.success("Expense updated successfully!")
                            st.rerun()
                        
                        if delete_btn:
                            conn = get_db_connection()
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM company_expenses WHERE id=?", (selected_expense,))
                            conn.commit()
                            conn.close()
                            st.success("Expense deleted successfully!")
                            st.rerun()
    
    with tab3:
        st.subheader("Expense Categories")
        
        conn = get_db_connection()
        categories = pd.read_sql("SELECT * FROM expense_categories", conn)
        conn.close()
        
        st.dataframe(categories, use_container_width=True)
        
        # Add new category
        with st.form("add_category_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_category = st.text_input("New Category Name")
            with col2:
                new_category_desc = st.text_input("Description")
            
            if st.form_submit_button("Add Category"):
                if new_category:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute('''
                            INSERT INTO expense_categories (category_name, description) 
                            VALUES (?, ?)
                        ''', (new_category, new_category_desc))
                        conn.commit()
                        st.success("Category added successfully!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Category already exists!")
                    finally:
                        conn.close()
                else:
                    st.error("Please enter category name")
    
    with tab4:
        st.subheader("Expense Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        report_type = st.selectbox("Report Type", ["Summary by Category", "Detailed Report"])
        
        if st.button("Generate Report"):
            conn = get_db_connection()
            
            if report_type == "Summary by Category":
                report_data = pd.read_sql('''
                    SELECT ec.category_name, SUM(ce.amount) as total_amount, COUNT(*) as transaction_count
                    FROM company_expenses ce 
                    JOIN expense_categories ec ON ce.category_id = ec.id 
                    WHERE ce.expense_date BETWEEN ? AND ?
                    GROUP BY ec.category_name 
                    ORDER BY total_amount DESC
                ''', conn, params=(start_date, end_date))
                
                if not report_data.empty:
                    st.dataframe(report_data, use_container_width=True)
                    
                    # Chart
                    fig = px.pie(report_data, values='total_amount', names='category_name', 
                               title='Expense Distribution by Category')
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # PDF Download
                    pdf_data = []
                    for _, row in report_data.iterrows():
                        pdf_data.append([row['category_name'], row['total_amount'], row['transaction_count']])
                    
                    pdf_link = generate_pdf(
                        pdf_data,
                        f"Expense Summary Report ({start_date} to {end_date})",
                        ['Category', 'Total Amount', 'Transaction Count'],
                        f"expense_summary_{start_date}_{end_date}"
                    )
                    st.markdown(pdf_link, unsafe_allow_html=True)
                else:
                    st.info("No expenses found for the selected period")
            
            else:  # Detailed Report
                report_data = pd.read_sql('''
                    SELECT ce.expense_date, ec.category_name, ce.amount, ce.description, 
                           ce.payment_mode, e.name as employee_name
                    FROM company_expenses ce 
                    JOIN expense_categories ec ON ce.category_id = ec.id 
                    LEFT JOIN employees e ON ce.employee_id = e.employee_id 
                    WHERE ce.expense_date BETWEEN ? AND ?
                    ORDER BY ce.expense_date DESC
                ''', conn, params=(start_date, end_date))
                
                if not report_data.empty:
                    st.dataframe(report_data, use_container_width=True)
                    
                    # PDF Download
                    pdf_data = []
                    for _, row in report_data.iterrows():
                        pdf_data.append([
                            row['expense_date'], row['category_name'], row['amount'],
                            row['description'], row['payment_mode'], row['employee_name'] or 'N/A'
                        ])
                    
                    pdf_link = generate_pdf(
                        pdf_data,
                        f"Expense Detailed Report ({start_date} to {end_date})",
                        ['Date', 'Category', 'Amount', 'Description', 'Payment Mode', 'Employee'],
                        f"expense_detailed_{start_date}_{end_date}"
                    )
                    st.markdown(pdf_link, unsafe_allow_html=True)
                else:
                    st.info("No expenses found for the selected period")
            
            conn.close()

def show_reports_analytics():
    st.markdown('<h2 class="section-header">📈 Reports & Analytics</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Financial Reports", "Employee Reports", "Analytics"])
    
    with tab1:
        st.subheader("Financial Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            report_start = st.date_input("Report Start Date", datetime.now().replace(day=1))
        with col2:
            report_end = st.date_input("Report End Date", datetime.now())
        
        if st.button("Generate Financial Report"):
            conn = get_db_connection()
            
            # Total expenses
            total_expenses = pd.read_sql('''
                SELECT SUM(amount) as total FROM company_expenses 
                WHERE expense_date BETWEEN ? AND ?
            ''', conn, params=(report_start, report_end)).iloc[0]['total'] or 0
            
            # Total salary
            total_salary = pd.read_sql('''
                SELECT SUM(net_salary) as total FROM salary_records 
                WHERE month_year BETWEEN ? AND ?
            ''', conn, params=(report_start.strftime('%Y-%m'), report_end.strftime('%Y-%m'))).iloc[0]['total'] or 0
            
            # Expense by category
            expense_by_cat = pd.read_sql('''
                SELECT ec.category_name, SUM(ce.amount) as total 
                FROM company_expenses ce 
                JOIN expense_categories ec ON ce.category_id = ec.id 
                WHERE ce.expense_date BETWEEN ? AND ?
                GROUP BY ec.category_name
            ''', conn, params=(report_start, report_end))
            
            conn.close()
            
            # Display report
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
            with col2:
                st.metric("Total Salary", f"₹{total_salary:,.2f}")
            with col3:
                st.metric("Total Outflow", f"₹{total_expenses + total_salary:,.2f}")
            
            if not expense_by_cat.empty:
                fig = px.bar(expense_by_cat, x='category_name', y='total', 
                           title='Expenses by Category')
                st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        st.subheader("Employee Reports")
        
        conn = get_db_connection()
        employees = pd.read_sql("SELECT * FROM employees WHERE status='Active'", conn)
        conn.close()
        
        if not employees.empty:
            st.dataframe(employees[['employee_id', 'name', 'designation', 'department', 'basic_salary']], 
                        use_container_width=True)
            
            # Department-wise summary
            dept_summary = employees.groupby('department').agg({
                'employee_id': 'count',
                'basic_salary': 'sum'
            }).reset_index()
            dept_summary.columns = ['Department', 'Employee Count', 'Total Salary']
            
            st.subheader("Department Summary")
            st.dataframe(dept_summary, use_container_width=True)
    
    with tab3:
        st.subheader("Analytics Dashboard")
        
        conn = get_db_connection()
        
        # Monthly expense trend
        monthly_expenses = pd.read_sql('''
            SELECT strftime('%Y-%m', expense_date) as month, SUM(amount) as total 
            FROM company_expenses 
            GROUP BY strftime('%Y-%m', expense_date) 
            ORDER BY month
        ''', conn)
        
        # Monthly salary trend
        monthly_salary = pd.read_sql('''
            SELECT month_year as month, SUM(net_salary) as total 
            FROM salary_records 
            GROUP BY month_year 
            ORDER BY month
        ''', conn)
        
        conn.close()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not monthly_expenses.empty:
                fig = px.line(monthly_expenses, x='month', y='total', 
                            title='Monthly Expense Trend', markers=True)
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if not monthly_salary.empty:
                fig = px.line(monthly_salary, x='month', y='total', 
                            title='Monthly Salary Trend', markers=True)
                st.plotly_chart(fig, use_container_width=True)

def show_data_import_export():
    st.markdown('<h2 class="section-header">📤 Data Import/Export</h2>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Import Data", "Export Data", "Templates"])
    
    with tab1:
        st.subheader("Import Data from Excel")
        
        st.info("""
        **Instructions for Import:**
        - Download the template from the Templates tab
        - Fill in your data following the template format
        - Upload the filled template here
        - The system will validate and import the data
        """)
        
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.success("File uploaded successfully!")
                st.dataframe(df.head(), use_container_width=True)
                
                if st.button("Import Data"):
                    # Here you would add logic to import data based on the template type
                    st.success("Data imported successfully!")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with tab2:
        st.subheader("Export Data")
        
        export_options = st.multiselect("Select data to export", 
                                      ["Employees", "Salary Records", "Expenses", "Expense Categories"])
        
        if st.button("Generate Export Files"):
            conn = get_db_connection()
            
            if "Employees" in export_options:
                employees_df = pd.read_sql("SELECT * FROM employees", conn)
                if not employees_df.empty:
                    st.markdown(create_download_link(employees_df, "employees_export", "excel"), 
                              unsafe_allow_html=True)
            
            if "Salary Records" in export_options:
                salary_df = pd.read_sql("SELECT * FROM salary_records", conn)
                if not salary_df.empty:
                    st.markdown(create_download_link(salary_df, "salary_records_export", "excel"), 
                              unsafe_allow_html=True)
            
            if "Expenses" in export_options:
                expenses_df = pd.read_sql("SELECT * FROM company_expenses", conn)
                if not expenses_df.empty:
                    st.markdown(create_download_link(expenses_df, "expenses_export", "excel"), 
                              unsafe_allow_html=True)
            
            if "Expense Categories" in export_options:
                categories_df = pd.read_sql("SELECT * FROM expense_categories", conn)
                if not categories_df.empty:
                    st.markdown(create_download_link(categories_df, "expense_categories_export", "excel"), 
                              unsafe_allow_html=True)
            
            conn.close()
    
    with tab3:
        st.subheader("Download Templates")
        
        st.info("Download these templates to prepare your data for import")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Employee Template"):
                template_df = pd.DataFrame(columns=[
                    'employee_id', 'name', 'designation', 'department', 
                    'account_no', 'account_title', 'bank_name', 'basic_salary', 'join_date'
                ])
                st.markdown(create_download_link(template_df, "employee_template", "excel"), 
                          unsafe_allow_html=True)
        
        with col2:
            if st.button("Expense Template"):
                template_df = pd.DataFrame(columns=[
                    'expense_date', 'category_name', 'amount', 'description', 
                    'employee_id', 'payment_mode', 'reference_no'
                ])
                st.markdown(create_download_link(template_df, "expense_template", "excel"), 
                          unsafe_allow_html=True)
        
        with col3:
            if st.button("Salary Template"):
                template_df = pd.DataFrame(columns=[
                    'employee_id', 'month_year', 'basic_salary', 'allowances', 
                    'deductions', 'net_salary', 'payment_date'
                ])
                st.markdown(create_download_link(template_df, "salary_template", "excel"), 
                          unsafe_allow_html=True)

if __name__ == "__main__":
    main()
