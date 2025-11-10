import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime, timedelta
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import tempfile
import os

# Database setup
def init_db():
    conn = sqlite3.connect('nutrition_company.db')
    c = conn.cursor()
    
    # Employees table
    c.execute('''CREATE TABLE IF NOT EXISTS employees
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  designation TEXT,
                  account_no TEXT,
                  account_title TEXT,
                  bank TEXT,
                  basic_salary REAL,
                  allowances REAL,
                  deductions REAL,
                  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Expenses table
    c.execute('''CREATE TABLE IF NOT EXISTS expenses
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  date DATE,
                  category TEXT,
                  description TEXT,
                  amount REAL,
                  employee_id INTEGER,
                  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (employee_id) REFERENCES employees (id))''')
    
    # Salary records table
    c.execute('''CREATE TABLE IF NOT EXISTS salary_records
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  employee_id INTEGER,
                  month_year TEXT,
                  basic_salary REAL,
                  allowances REAL,
                  deductions REAL,
                  net_salary REAL,
                  payment_date DATE,
                  created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (employee_id) REFERENCES employees (id))''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

class PDFGenerator:
    @staticmethod
    def generate_salary_slip(employee_data, salary_data, date_range):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        p.setFont("Helvetica-Bold", 16)
        p.drawString(100, height - 50, "Nutrition Company - Salary Slip")
        p.setFont("Helvetica", 10)
        p.drawString(100, height - 70, f"Period: {date_range['start']} to {date_range['end']}")
        
        # Employee Details
        y_position = height - 120
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y_position, "Employee Details:")
        p.setFont("Helvetica", 10)
        
        details = [
            f"Name: {employee_data['name']}",
            f"Designation: {employee_data['designation']}",
            f"Account No: {employee_data['account_no']}",
            f"Account Title: {employee_data['account_title']}",
            f"Bank: {employee_data['bank']}"
        ]
        
        for detail in details:
            y_position -= 20
            p.drawString(100, y_position, detail)
        
        # Salary Details
        y_position -= 40
        p.setFont("Helvetica-Bold", 12)
        p.drawString(100, y_position, "Salary Details:")
        p.setFont("Helvetica", 10)
        
        salary_details = [
            f"Basic Salary: ${salary_data['basic_salary']:,.2f}",
            f"Allowances: ${salary_data['allowances']:,.2f}",
            f"Deductions: ${salary_data['deductions']:,.2f}",
            f"Net Salary: ${salary_data['net_salary']:,.2f}"
        ]
        
        for detail in salary_details:
            y_position -= 20
            p.drawString(100, y_position, detail)
        
        p.save()
        buffer.seek(0)
        return buffer

    @staticmethod
    def generate_expense_report(expenses, date_range, category=None):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Header
        p.setFont("Helvetica-Bold", 16)
        title = "Nutrition Company - Expense Report"
        if category:
            title += f" - {category}"
        p.drawString(100, height - 50, title)
        p.setFont("Helvetica", 10)
        p.drawString(100, height - 70, f"Period: {date_range['start']} to {date_range['end']}")
        
        # Expenses Table Header
        y_position = height - 120
        p.setFont("Helvetica-Bold", 10)
        headers = ["Date", "Category", "Description", "Employee", "Amount"]
        col_widths = [80, 80, 150, 100, 80]
        
        x_position = 50
        for i, header in enumerate(headers):
            p.drawString(x_position, y_position, header)
            x_position += col_widths[i]
        
        # Expenses Data
        y_position -= 20
        p.setFont("Helvetica", 8)
        total_amount = 0
        
        for expense in expenses:
            if y_position < 100:
                p.showPage()
                y_position = height - 50
                p.setFont("Helvetica", 8)
            
            x_position = 50
            p.drawString(x_position, y_position, str(expense['date']))
            x_position += col_widths[0]
            p.drawString(x_position, y_position, expense['category'])
            x_position += col_widths[1]
            p.drawString(x_position, y_position, expense['description'][:30])
            x_position += col_widths[2]
            p.drawString(x_position, y_position, expense.get('employee_name', 'N/A'))
            x_position += col_widths[3]
            amount = f"${expense['amount']:,.2f}"
            p.drawString(x_position, y_position, amount)
            
            total_amount += expense['amount']
            y_position -= 15
        
        # Total
        y_position -= 20
        p.setFont("Helvetica-Bold", 10)
        p.drawString(400, y_position, f"Total: ${total_amount:,.2f}")
        
        p.save()
        buffer.seek(0)
        return buffer

class DatabaseManager:
    @staticmethod
    def get_connection():
        return sqlite3.connect('nutrition_company.db')
    
    @staticmethod
    def execute_query(query, params=()):
        conn = DatabaseManager.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor
    
    @staticmethod
    def fetch_all(query, params=()):
        cursor = DatabaseManager.execute_query(query, params)
        results = cursor.fetchall()
        cursor.connection.close()
        return [dict(row) for row in results]
    
    @staticmethod
    def fetch_one(query, params=()):
        cursor = DatabaseManager.execute_query(query, params)
        result = cursor.fetchone()
        cursor.connection.close()
        return dict(result) if result else None

def main():
    st.set_page_config(
        page_title="Nutrition Company Management System",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏢 Nutrition Company Management System")
    st.markdown("---")
    
    # Sidebar navigation
    menu = [
        "Dashboard",
        "Employee Management", 
        "Salary Management",
        "Expense Management",
        "Reports & Analytics",
        "Data Import/Export"
    ]
    
    choice = st.sidebar.selectbox("Navigation", menu)
    
    if choice == "Dashboard":
        show_dashboard()
    elif choice == "Employee Management":
        show_employee_management()
    elif choice == "Salary Management":
        show_salary_management()
    elif choice == "Expense Management":
        show_expense_management()
    elif choice == "Reports & Analytics":
        show_reports_analytics()
    elif choice == "Data Import/Export":
        show_data_import_export()

def show_dashboard():
    st.header("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Total Employees
    employees = DatabaseManager.fetch_all("SELECT COUNT(*) as count FROM employees")
    col1.metric("Total Employees", employees[0]['count'])
    
    # Total Expenses this month
    current_month = datetime.now().strftime("%Y-%m")
    expenses = DatabaseManager.fetch_all(
        "SELECT SUM(amount) as total FROM expenses WHERE strftime('%Y-%m', date) = ?",
        (current_month,)
    )
    total_expenses = expenses[0]['total'] or 0
    col2.metric("Monthly Expenses", f"${total_expenses:,.2f}")
    
    # Total Salary this month
    salaries = DatabaseManager.fetch_all(
        "SELECT SUM(net_salary) as total FROM salary_records WHERE strftime('%Y-%m', payment_date) = ?",
        (current_month,)
    )
    total_salaries = salaries[0]['total'] or 0
    col3.metric("Monthly Salary", f"${total_salaries:,.2f}")
    
    # Recent activities
    col4.metric("System Status", "Active", "OK")
    
    # Recent Expenses
    st.subheader("Recent Expenses")
    recent_expenses = DatabaseManager.fetch_all(
        "SELECT e.*, emp.name as employee_name FROM expenses e LEFT JOIN employees emp ON e.employee_id = emp.id ORDER BY e.date DESC LIMIT 10"
    )
    if recent_expenses:
        st.dataframe(pd.DataFrame(recent_expenses))
    else:
        st.info("No recent expenses found")

def show_employee_management():
    st.header("👥 Employee Management")
    
    tab1, tab2, tab3 = st.tabs(["Add Employee", "View/Edit Employees", "Employee Ledger"])
    
    with tab1:
        st.subheader("Add New Employee")
        
        with st.form("employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Full Name*")
                designation = st.text_input("Designation*")
                account_no = st.text_input("Account Number*")
                
            with col2:
                account_title = st.text_input("Account Title*")
                bank = st.text_input("Bank Name*")
                basic_salary = st.number_input("Basic Salary*", min_value=0.0, step=100.0)
            
            allowances = st.number_input("Allowances", min_value=0.0, step=50.0)
            deductions = st.number_input("Deductions", min_value=0.0, step=50.0)
            
            if st.form_submit_button("Add Employee"):
                if name and designation and account_no and account_title and bank and basic_salary:
                    DatabaseManager.execute_query(
                        """INSERT INTO employees 
                        (name, designation, account_no, account_title, bank, basic_salary, allowances, deductions)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                        (name, designation, account_no, account_title, bank, basic_salary, allowances, deductions)
                    )
                    st.success("Employee added successfully!")
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab2:
        st.subheader("Employee List")
        employees = DatabaseManager.fetch_all("SELECT * FROM employees ORDER BY name")
        
        if employees:
            df = pd.DataFrame(employees)
            st.dataframe(df, use_container_width=True)
            
            # Edit/Delete functionality
            st.subheader("Edit/Delete Employee")
            employee_names = [emp['name'] for emp in employees]
            selected_employee = st.selectbox("Select Employee to Edit", employee_names)
            
            if selected_employee:
                employee = DatabaseManager.fetch_one("SELECT * FROM employees WHERE name = ?", (selected_employee,))
                
                if employee:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        with st.form("edit_employee_form"):
                            new_name = st.text_input("Name", value=employee['name'])
                            new_designation = st.text_input("Designation", value=employee['designation'])
                            new_account_no = st.text_input("Account No", value=employee['account_no'])
                            new_account_title = st.text_input("Account Title", value=employee['account_title'])
                            
                            if st.form_submit_button("Update Employee"):
                                DatabaseManager.execute_query(
                                    """UPDATE employees SET name=?, designation=?, account_no=?, account_title=?
                                    WHERE id=?""",
                                    (new_name, new_designation, new_account_no, new_account_title, employee['id'])
                                )
                                st.success("Employee updated successfully!")
                                st.rerun()
                    
                    with col2:
                        if st.button("Delete Employee", type="secondary"):
                            DatabaseManager.execute_query("DELETE FROM employees WHERE id=?", (employee['id'],))
                            st.success("Employee deleted successfully!")
                            st.rerun()
    
    with tab3:
        st.subheader("Employee Ledger")
        
        employees = DatabaseManager.fetch_all("SELECT id, name FROM employees ORDER BY name")
        if employees:
            employee_options = {emp['name']: emp['id'] for emp in employees}
            selected_employee_name = st.selectbox("Select Employee", list(employee_options.keys()))
            
            if selected_employee_name:
                employee_id = employee_options[selected_employee_name]
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
                with col2:
                    end_date = st.date_input("End Date", datetime.now())
                
                # Get employee expenses and salary data
                expenses = DatabaseManager.fetch_all(
                    """SELECT e.date, e.category, e.description, e.amount 
                    FROM expenses e 
                    WHERE e.employee_id = ? AND e.date BETWEEN ? AND ?
                    ORDER BY e.date""",
                    (employee_id, start_date, end_date)
                )
                
                salaries = DatabaseManager.fetch_all(
                    """SELECT payment_date, net_salary 
                    FROM salary_records 
                    WHERE employee_id = ? AND payment_date BETWEEN ? AND ?
                    ORDER BY payment_date""",
                    (employee_id, start_date, end_date)
                )
                
                # Display ledger
                st.subheader(f"Ledger for {selected_employee_name}")
                
                ledger_data = []
                for expense in expenses:
                    ledger_data.append({
                        'Date': expense['date'],
                        'Type': 'Expense',
                        'Description': expense['description'],
                        'Amount': f"-${expense['amount']:,.2f}",
                        'Category': expense['category']
                    })
                
                for salary in salaries:
                    ledger_data.append({
                        'Date': salary['payment_date'],
                        'Type': 'Salary',
                        'Description': 'Salary Payment',
                        'Amount': f"+${salary['net_salary']:,.2f}",
                        'Category': 'Income'
                    })
                
                if ledger_data:
                    ledger_df = pd.DataFrame(ledger_data)
                    st.dataframe(ledger_df, use_container_width=True)
                    
                    # Download PDF
                    if st.button("Download Ledger PDF"):
                        date_range = {'start': start_date, 'end': end_date}
                        employee_data = DatabaseManager.fetch_one(
                            "SELECT * FROM employees WHERE id = ?", (employee_id,)
                        )
                        
                        pdf_buffer = PDFGenerator.generate_expense_report(
                            expenses, date_range, f"Employee: {selected_employee_name}"
                        )
                        
                        st.download_button(
                            label="Download PDF",
                            data=pdf_buffer.getvalue(),
                            file_name=f"ledger_{selected_employee_name}_{start_date}_{end_date}.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.info("No transactions found for the selected period")

def show_salary_management():
    st.header("💰 Salary Management")
    
    tab1, tab2, tab3 = st.tabs(["Generate Salary", "Salary Records", "Individual Salary Slip"])
    
    with tab1:
        st.subheader("Generate Salary Sheet")
        
        employees = DatabaseManager.fetch_all("SELECT * FROM employees ORDER BY name")
        if employees:
            # Date selection
            col1, col2 = st.columns(2)
            with col1:
                salary_month = st.selectbox("Select Month", [
                    "January", "February", "March", "April", "May", "June",
                    "July", "August", "September", "October", "November", "December"
                ])
            with col2:
                salary_year = st.number_input("Year", min_value=2020, max_value=2030, value=datetime.now().year)
            
            # Display salary preview
            st.subheader("Salary Preview")
            salary_data = []
            
            for emp in employees:
                net_salary = emp['basic_salary'] + emp['allowances'] - emp['deductions']
                salary_data.append({
                    'Employee': emp['name'],
                    'Designation': emp['designation'],
                    'Basic Salary': emp['basic_salary'],
                    'Allowances': emp['allowances'],
                    'Deductions': emp['deductions'],
                    'Net Salary': net_salary,
                    'Account No': emp['account_no'],
                    'Bank': emp['bank']
                })
            
            salary_df = pd.DataFrame(salary_data)
            st.dataframe(salary_df, use_container_width=True)
            
            # Generate salary records
            if st.button("Generate Salary Records"):
                month_year = f"{salary_month} {salary_year}"
                payment_date = f"{salary_year}-{list(range(1,13))[['January','February','March','April','May','June','July','August','September','October','November','December'].index(salary_month)]:02d}-01"
                
                for emp in employees:
                    net_salary = emp['basic_salary'] + emp['allowances'] - emp['deductions']
                    DatabaseManager.execute_query(
                        """INSERT INTO salary_records 
                        (employee_id, month_year, basic_salary, allowances, deductions, net_salary, payment_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (emp['id'], month_year, emp['basic_salary'], emp['allowances'], emp['deductions'], net_salary, payment_date)
                    )
                
                st.success("Salary records generated successfully!")
    
    with tab2:
        st.subheader("Salary Records")
        
        salary_records = DatabaseManager.fetch_all(
            """SELECT sr.*, e.name as employee_name, e.designation 
            FROM salary_records sr 
            JOIN employees e ON sr.employee_id = e.id 
            ORDER BY sr.payment_date DESC"""
        )
        
        if salary_records:
            df = pd.DataFrame(salary_records)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No salary records found")
    
    with tab3:
        st.subheader("Individual Salary Slip")
        
        employees = DatabaseManager.fetch_all("SELECT id, name FROM employees ORDER BY name")
        if employees:
            employee_options = {emp['name']: emp['id'] for emp in employees}
            selected_employee_name = st.selectbox("Select Employee for Salary Slip", list(employee_options.keys()))
            
            if selected_employee_name:
                employee_id = employee_options[selected_employee_name]
                
                col1, col2 = st.columns(2)
                with col1:
                    start_date = st.date_input("Salary Period Start", datetime.now().replace(day=1))
                with col2:
                    end_date = st.date_input("Salary Period End", datetime.now())
                
                # Get salary data
                salary_data = DatabaseManager.fetch_one(
                    """SELECT * FROM salary_records 
                    WHERE employee_id = ? AND payment_date BETWEEN ? AND ? 
                    ORDER BY payment_date DESC LIMIT 1""",
                    (employee_id, start_date, end_date)
                )
                
                employee_data = DatabaseManager.fetch_one(
                    "SELECT * FROM employees WHERE id = ?", (employee_id,)
                )
                
                if salary_data and employee_data:
                    st.subheader("Salary Slip Preview")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Employee Details:**")
                        st.write(f"Name: {employee_data['name']}")
                        st.write(f"Designation: {employee_data['designation']}")
                        st.write(f"Account No: {employee_data['account_no']}")
                        st.write(f"Bank: {employee_data['bank']}")
                    
                    with col2:
                        st.write("**Salary Details:**")
                        st.write(f"Basic Salary: ${salary_data['basic_salary']:,.2f}")
                        st.write(f"Allowances: ${salary_data['allowances']:,.2f}")
                        st.write(f"Deductions: ${salary_data['deductions']:,.2f}")
                        st.write(f"**Net Salary: ${salary_data['net_salary']:,.2f}**")
                    
                    # Download PDF
                    if st.button("Download Salary Slip PDF"):
                        date_range = {'start': start_date, 'end': end_date}
                        pdf_buffer = PDFGenerator.generate_salary_slip(employee_data, salary_data, date_range)
                        
                        st.download_button(
                            label="Download Salary Slip",
                            data=pdf_buffer.getvalue(),
                            file_name=f"salary_slip_{employee_data['name']}_{start_date}.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.warning("No salary data found for the selected period")

def show_expense_management():
    st.header("💸 Expense Management")
    
    tab1, tab2, tab3 = st.tabs(["Add Expense", "View/Edit Expenses", "Expense Categories"])
    
    with tab1:
        st.subheader("Add New Expense")
        
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Date*", datetime.now())
                category = st.selectbox("Category*", [
                    "Office Supplies", "Utilities", "Travel", "Equipment", 
                    "Marketing", "Maintenance", "Software", "Other"
                ])
                amount = st.number_input("Amount*", min_value=0.0, step=10.0)
            
            with col2:
                employees = DatabaseManager.fetch_all("SELECT id, name FROM employees ORDER BY name")
                employee_options = {emp['name']: emp['id'] for emp in employees}
                employee_options["Company Expense"] = None
                selected_employee = st.selectbox("Employee (if applicable)", list(employee_options.keys()))
                
                description = st.text_area("Description*")
            
            if st.form_submit_button("Add Expense"):
                if expense_date and category and amount and description:
                    employee_id = employee_options[selected_employee]
                    
                    DatabaseManager.execute_query(
                        """INSERT INTO expenses (date, category, description, amount, employee_id)
                        VALUES (?, ?, ?, ?, ?)""",
                        (expense_date, category, description, amount, employee_id)
                    )
                    st.success("Expense added successfully!")
                else:
                    st.error("Please fill all required fields (*)")
    
    with tab2:
        st.subheader("Expense Records")
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        
        # Category filter
        categories = DatabaseManager.fetch_all("SELECT DISTINCT category FROM expenses")
        category_list = [cat['category'] for cat in categories]
        selected_category = st.selectbox("Filter by Category", ["All"] + category_list)
        
        # Query expenses
        query = """SELECT e.*, emp.name as employee_name 
                  FROM expenses e LEFT JOIN employees emp ON e.employee_id = emp.id 
                  WHERE e.date BETWEEN ? AND ?"""
        params = [start_date, end_date]
        
        if selected_category != "All":
            query += " AND e.category = ?"
            params.append(selected_category)
        
        query += " ORDER BY e.date DESC"
        expenses = DatabaseManager.fetch_all(query, params)
        
        if expenses:
            df = pd.DataFrame(expenses)
            st.dataframe(df, use_container_width=True)
            
            # Edit/Delete functionality
            st.subheader("Edit/Delete Expense")
            expense_descriptions = [f"{exp['date']} - {exp['description']} - ${exp['amount']}" for exp in expenses]
            selected_expense_desc = st.selectbox("Select Expense to Edit", expense_descriptions)
            
            if selected_expense_desc:
                selected_index = expense_descriptions.index(selected_expense_desc)
                expense = expenses[selected_index]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    with st.form("edit_expense_form"):
                        new_date = st.date_input("Date", value=datetime.strptime(expense['date'], '%Y-%m-%d'))
                        new_category = st.selectbox("Category", category_list, index=category_list.index(expense['category']))
                        new_amount = st.number_input("Amount", value=float(expense['amount']))
                        new_description = st.text_area("Description", value=expense['description'])
                        
                        if st.form_submit_button("Update Expense"):
                            DatabaseManager.execute_query(
                                """UPDATE expenses SET date=?, category=?, amount=?, description=?
                                WHERE id=?""",
                                (new_date, new_category, new_amount, new_description, expense['id'])
                            )
                            st.success("Expense updated successfully!")
                            st.rerun()
                
                with col2:
                    if st.button("Delete Expense", type="secondary"):
                        DatabaseManager.execute_query("DELETE FROM expenses WHERE id=?", (expense['id'],))
                        st.success("Expense deleted successfully!")
                        st.rerun()
        else:
            st.info("No expenses found for the selected period")
    
    with tab3:
        st.subheader("Expense Categories Report")
        
        col1, col2 = st.columns(2)
        with col1:
            cat_start_date = st.date_input("Category Start Date", datetime.now() - timedelta(days=30), key="cat_start")
        with col2:
            cat_end_date = st.date_input("Category End Date", datetime.now(), key="cat_end")
        
        # Category-wise summary
        category_summary = DatabaseManager.fetch_all(
            """SELECT category, SUM(amount) as total_amount, COUNT(*) as count
            FROM expenses 
            WHERE date BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total_amount DESC""",
            (cat_start_date, cat_end_date)
        )
        
        if category_summary:
            st.subheader("Category-wise Summary")
            cat_df = pd.DataFrame(category_summary)
            st.dataframe(cat_df, use_container_width=True)
            
            # Download category report
            if st.button("Download Category Report PDF"):
                expenses_for_report = DatabaseManager.fetch_all(
                    """SELECT e.*, emp.name as employee_name 
                    FROM expenses e LEFT JOIN employees emp ON e.employee_id = emp.id 
                    WHERE e.date BETWEEN ? AND ?
                    ORDER BY e.category, e.date""",
                    (cat_start_date, cat_end_date)
                )
                
                date_range = {'start': cat_start_date, 'end': cat_end_date}
                pdf_buffer = PDFGenerator.generate_expense_report(expenses_for_report, date_range)
                
                st.download_button(
                    label="Download Category Report",
                    data=pdf_buffer.getvalue(),
                    file_name=f"expense_categories_{cat_start_date}_{cat_end_date}.pdf",
                    mime="application/pdf"
                )

def show_reports_analytics():
    st.header("📈 Reports & Analytics")
    
    tab1, tab2, tab3 = st.tabs(["Financial Reports", "Analytics", "Custom Reports"])
    
    with tab1:
        st.subheader("Financial Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            report_start_date = st.date_input("Report Start Date", datetime.now().replace(day=1))
        with col2:
            report_end_date = st.date_input("Report End Date", datetime.now())
        
        # Generate comprehensive report
        if st.button("Generate Financial Report"):
            # Expenses summary
            expenses_summary = DatabaseManager.fetch_all(
                """SELECT category, SUM(amount) as total 
                FROM expenses 
                WHERE date BETWEEN ? AND ?
                GROUP BY category""",
                (report_start_date, report_end_date)
            )
            
            # Salary summary
            salary_summary = DatabaseManager.fetch_all(
                """SELECT SUM(net_salary) as total_salary 
                FROM salary_records 
                WHERE payment_date BETWEEN ? AND ?""",
                (report_start_date, report_end_date)
            )
            
            # Employee-wise expenses
            employee_expenses = DatabaseManager.fetch_all(
                """SELECT e.name, SUM(exp.amount) as total_expenses
                FROM expenses exp
                JOIN employees e ON exp.employee_id = e.id
                WHERE exp.date BETWEEN ? AND ?
                GROUP BY e.name
                ORDER BY total_expenses DESC""",
                (report_start_date, report_end_date)
            )
            
            # Display reports
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Expenses by Category")
                if expenses_summary:
                    exp_df = pd.DataFrame(expenses_summary)
                    st.dataframe(exp_df, use_container_width=True)
                
                st.subheader("Employee Expenses")
                if employee_expenses:
                    emp_exp_df = pd.DataFrame(employee_expenses)
                    st.dataframe(emp_exp_df, use_container_width=True)
            
            with col2:
                st.subheader("Financial Summary")
                total_expenses = sum(exp['total'] for exp in expenses_summary) if expenses_summary else 0
                total_salary = salary_summary[0]['total_salary'] if salary_summary else 0
                
                st.metric("Total Expenses", f"${total_expenses:,.2f}")
                st.metric("Total Salary", f"${total_salary:,.2f}")
                st.metric("Total Expenditure", f"${total_expenses + total_salary:,.2f}")
    
    with tab2:
        st.subheader("Analytics Dashboard")
        
        # Monthly trends
        monthly_data = DatabaseManager.fetch_all(
            """SELECT strftime('%Y-%m', date) as month, 
                   SUM(amount) as monthly_expenses
            FROM expenses 
            GROUP BY strftime('%Y-%m', date)
            ORDER BY month DESC
            LIMIT 12"""
        )
        
        if monthly_data:
            monthly_df = pd.DataFrame(monthly_data)
            st.subheader("Monthly Expense Trends")
            st.line_chart(monthly_df.set_index('month')['monthly_expenses'])
        
        # Category distribution
        category_data = DatabaseManager.fetch_all(
            """SELECT category, SUM(amount) as total 
            FROM expenses 
            WHERE date >= date('now', '-30 days')
            GROUP BY category"""
        )
        
        if category_data:
            cat_df = pd.DataFrame(category_data)
            st.subheader("Recent Category Distribution")
            st.bar_chart(cat_df.set_index('category')['total'])

def show_data_import_export():
    st.header("📥 Data Import/Export")
    
    tab1, tab2, tab3 = st.tabs(["Import Data", "Export Data", "Templates"])
    
    with tab1:
        st.subheader("Import Data from Excel")
        
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                if st.button("Import Data"):
                    # This is a simplified import - you'd want to add more validation
                    if 'name' in df.columns and 'designation' in df.columns:
                        for _, row in df.iterrows():
                            DatabaseManager.execute_query(
                                """INSERT INTO employees 
                                (name, designation, account_no, account_title, bank, basic_salary, allowances, deductions)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                (row.get('name'), row.get('designation'), row.get('account_no', ''),
                                 row.get('account_title', ''), row.get('bank', ''), row.get('basic_salary', 0),
                                 row.get('allowances', 0), row.get('deductions', 0))
                            )
                        st.success("Data imported successfully!")
                    else:
                        st.error("Invalid Excel format. Please use the provided template.")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with tab2:
        st.subheader("Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_type = st.selectbox("Export Type", ["Employees", "Expenses", "Salary Records"])
        
        with col2:
            export_format = st.selectbox("Format", ["Excel", "CSV"])
        
        if st.button("Generate Export"):
            if export_type == "Employees":
                data = DatabaseManager.fetch_all("SELECT * FROM employees")
                df = pd.DataFrame(data)
            elif export_type == "Expenses":
                data = DatabaseManager.fetch_all(
                    """SELECT e.*, emp.name as employee_name 
                    FROM expenses e LEFT JOIN employees emp ON e.employee_id = emp.id"""
                )
                df = pd.DataFrame(data)
            else:  # Salary Records
                data = DatabaseManager.fetch_all(
                    """SELECT sr.*, e.name as employee_name 
                    FROM salary_records sr JOIN employees e ON sr.employee_id = e.id"""
                )
                df = pd.DataFrame(data)
            
            if export_format == "Excel":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Data', index=False)
                buffer.seek(0)
                
                st.download_button(
                    label="Download Excel",
                    data=buffer.getvalue(),
                    file_name=f"{export_type.lower()}_export.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{export_type.lower()}_export.csv",
                    mime="text/csv"
                )
    
    with tab3:
        st.subheader("Download Templates")
        
        st.info("Download these templates to ensure proper data formatting for imports")
        
        # Employee template
        employee_template = pd.DataFrame(columns=[
            'name', 'designation', 'account_no', 'account_title', 'bank', 
            'basic_salary', 'allowances', 'deductions'
        ])
        
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            employee_template.to_excel(writer, sheet_name='Employees', index=False)
        buffer.seek(0)
        
        st.download_button(
            label="Download Employee Template",
            data=buffer.getvalue(),
            file_name="employee_template.xlsx",
            mime="application/vnd.ms-excel"
        )

if __name__ == "__main__":
    main()
