import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime
import tempfile
import os
from fpdf import FPDF
import io

# Page configuration
st.set_page_config(
    page_title="Expense & Employee Management",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
def init_db():
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    
    # Expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Employees table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bank_account TEXT,
            bank_name TEXT,
            designation TEXT,
            salary REAL NOT NULL,
            join_date TEXT,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Salary payments table
    c.execute('''
        CREATE TABLE IF NOT EXISTS salary_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            month_year TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database
init_db()

# Expense categories
EXPENSE_CATEGORIES = [
    "Guard", "Labour", "Bilty Expenses", "Office Rent", "Warehouse Rent",
    "Muhammad Asim Iqbal Salary", "Import Export", "Office Electricity", "FBR",
    "Abdul Manan Sb Salary", "Office Entertainment", "PSID", "Advance",
    "Commission", "Office Stationery Expense", "Employee Expenses", "Other Expense",
    "Company Expense", "Muhammad Abdullah Salary"
]

# PDF Generator Class
class PDFReport(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Company Management Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(2)
    
    def chapter_body(self, data, headers):
        self.set_font('Arial', '', 10)
        
        # Calculate column widths
        col_width = self.w / (len(headers) + 1)
        
        # Headers
        self.set_font('Arial', 'B', 10)
        for header in headers:
            self.cell(col_width, 10, header, 1, 0, 'C')
        self.ln()
        
        # Data
        self.set_font('Arial', '', 9)
        for row in data:
            for item in row:
                self.cell(col_width, 8, str(item), 1, 0, 'C')
            self.ln()

# Database functions
def add_expense(category, amount, date, description):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO expenses (category, amount, date, description)
        VALUES (?, ?, ?, ?)
    ''', (category, amount, date, description))
    conn.commit()
    conn.close()

def get_expenses(month=None, year=None):
    conn = sqlite3.connect('company_data.db')
    df = pd.read_sql_query('''
        SELECT * FROM expenses 
        ORDER BY date DESC
    ''', conn)
    conn.close()
    
    if month and year:
        df['date'] = pd.to_datetime(df['date'])
        df = df[(df['date'].dt.month == month) & (df['date'].dt.year == year)]
    
    return df

def update_expense(expense_id, category, amount, date, description):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('''
        UPDATE expenses 
        SET category=?, amount=?, date=?, description=?
        WHERE id=?
    ''', (category, amount, date, description, expense_id))
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
    conn.commit()
    conn.close()

def add_employee(name, bank_account, bank_name, designation, salary, join_date):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO employees (name, bank_account, bank_name, designation, salary, join_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, bank_account, bank_name, designation, salary, join_date))
    conn.commit()
    conn.close()

def get_employees():
    conn = sqlite3.connect('company_data.db')
    df = pd.read_sql_query('SELECT * FROM employees ORDER BY name', conn)
    conn.close()
    return df

def update_employee(emp_id, name, bank_account, bank_name, designation, salary, join_date):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('''
        UPDATE employees 
        SET name=?, bank_account=?, bank_name=?, designation=?, salary=?, join_date=?
        WHERE id=?
    ''', (name, bank_account, bank_name, designation, salary, join_date, emp_id))
    conn.commit()
    conn.close()

def delete_employee(emp_id):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM employees WHERE id=?', (emp_id,))
    conn.commit()
    conn.close()

def record_salary_payment(employee_id, amount, payment_date, month_year):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO salary_payments (employee_id, amount, payment_date, month_year)
        VALUES (?, ?, ?, ?)
    ''', (employee_id, amount, payment_date, month_year))
    conn.commit()
    conn.close()

def get_salary_payments(month=None, year=None):
    conn = sqlite3.connect('company_data.db')
    query = '''
        SELECT sp.*, e.name, e.designation 
        FROM salary_payments sp
        JOIN employees e ON sp.employee_id = e.id
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    if month and year:
        df['payment_date'] = pd.to_datetime(df['payment_date'])
        df = df[(df['payment_date'].dt.month == month) & (df['payment_date'].dt.year == year)]
    
    return df

# Main App
def main():
    st.title("💰 Company Management System")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose Module", 
        ["Expense Management", "Employee Management", "Reports & Analytics"])
    
    if app_mode == "Expense Management":
        expense_management()
    elif app_mode == "Employee Management":
        employee_management()
    elif app_mode == "Reports & Analytics":
        reports_analytics()

def expense_management():
    st.header("💵 Expense Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add New Expense")
        
        with st.form("expense_form"):
            category = st.selectbox("Category", EXPENSE_CATEGORIES)
            amount = st.number_input("Amount", min_value=0.0, step=100.0)
            date = st.date_input("Date")
            description = st.text_area("Description")
            
            submitted = st.form_submit_button("Add Expense")
            if submitted:
                if amount > 0:
                    add_expense(category, amount, date.strftime('%Y-%m-%d'), description)
                    st.success("Expense added successfully!")
                else:
                    st.error("Please enter a valid amount")
    
    with col2:
        st.subheader("Expense Records")
        
        # Filter options
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_month = st.selectbox("Filter Month", 
                ["All"] + list(range(1, 13)), key="exp_month")
        with col_f2:
            current_year = datetime.now().year
            filter_year = st.selectbox("Filter Year", 
                ["All"] + list(range(current_year-2, current_year+1)), key="exp_year")
        
        expenses_df = get_expenses()
        
        if not expenses_df.empty:
            expenses_df['date'] = pd.to_datetime(expenses_df['date'])
            
            # Apply filters
            if filter_month != "All":
                expenses_df = expenses_df[expenses_df['date'].dt.month == filter_month]
            if filter_year != "All":
                expenses_df = expenses_df[expenses_df['date'].dt.year == filter_year]
            
            # Display expenses
            display_df = expenses_df[['id', 'category', 'amount', 'date', 'description']].copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(display_df, use_container_width=True)
            
            # Edit/Delete section
            st.subheader("Edit/Delete Expense")
            expense_ids = expenses_df['id'].tolist()
            selected_id = st.selectbox("Select Expense ID to Modify", expense_ids)
            
            if selected_id:
                selected_expense = expenses_df[expenses_df['id'] == selected_id].iloc[0]
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    with st.form("edit_expense"):
                        edit_category = st.selectbox("Category", EXPENSE_CATEGORIES, 
                                                   index=EXPENSE_CATEGORIES.index(selected_expense['category']))
                        edit_amount = st.number_input("Amount", value=float(selected_expense['amount']), 
                                                     step=100.0)
                        edit_date = st.date_input("Date", 
                                                value=datetime.strptime(selected_expense['date'], '%Y-%m-%d'))
                        edit_description = st.text_area("Description", value=selected_expense['description'])
                        
                        update_clicked = st.form_submit_button("Update Expense")
                        if update_clicked:
                            update_expense(selected_id, edit_category, edit_amount, 
                                         edit_date.strftime('%Y-%m-%d'), edit_description)
                            st.success("Expense updated successfully!")
                            st.rerun()
                
                with col_e2:
                    st.write("### Delete Expense")
                    st.write(f"**Category:** {selected_expense['category']}")
                    st.write(f"**Amount:** {selected_expense['amount']}")
                    st.write(f"**Date:** {selected_expense['date']}")
                    
                    if st.button("Delete Expense", type="secondary"):
                        delete_expense(selected_id)
                        st.success("Expense deleted successfully!")
                        st.rerun()
        else:
            st.info("No expenses recorded yet.")

def employee_management():
    st.header("👥 Employee Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add New Employee")
        
        with st.form("employee_form"):
            name = st.text_input("Full Name")
            bank_account = st.text_input("Bank Account Number")
            bank_name = st.text_input("Bank Name")
            designation = st.text_input("Designation")
            salary = st.number_input("Monthly Salary", min_value=0.0, step=1000.0)
            join_date = st.date_input("Join Date")
            
            submitted = st.form_submit_button("Add Employee")
            if submitted:
                if name and salary > 0:
                    add_employee(name, bank_account, bank_name, designation, salary, 
                               join_date.strftime('%Y-%m-%d'))
                    st.success("Employee added successfully!")
                else:
                    st.error("Please fill all required fields")
    
    with col2:
        st.subheader("Employee Records")
        
        employees_df = get_employees()
        
        if not employees_df.empty:
            display_df = employees_df[['id', 'name', 'designation', 'salary', 'join_date', 'bank_name']].copy()
            st.dataframe(display_df, use_container_width=True)
            
            # Edit/Delete section
            st.subheader("Edit/Delete Employee")
            emp_ids = employees_df['id'].tolist()
            selected_emp_id = st.selectbox("Select Employee ID to Modify", emp_ids)
            
            if selected_emp_id:
                selected_emp = employees_df[employees_df['id'] == selected_emp_id].iloc[0]
                
                col_emp1, col_emp2 = st.columns(2)
                with col_emp1:
                    with st.form("edit_employee"):
                        edit_name = st.text_input("Full Name", value=selected_emp['name'])
                        edit_bank_account = st.text_input("Bank Account", value=selected_emp['bank_account'] or "")
                        edit_bank_name = st.text_input("Bank Name", value=selected_emp['bank_name'] or "")
                        edit_designation = st.text_input("Designation", value=selected_emp['designation'] or "")
                        edit_salary = st.number_input("Salary", value=float(selected_emp['salary']), step=1000.0)
                        edit_join_date = st.date_input("Join Date", 
                                                     value=datetime.strptime(selected_emp['join_date'], '%Y-%m-%d'))
                        
                        update_clicked = st.form_submit_button("Update Employee")
                        if update_clicked:
                            update_employee(selected_emp_id, edit_name, edit_bank_account, 
                                          edit_bank_name, edit_designation, edit_salary,
                                          edit_join_date.strftime('%Y-%m-%d'))
                            st.success("Employee updated successfully!")
                            st.rerun()
                
                with col_emp2:
                    st.write("### Delete Employee")
                    st.write(f"**Name:** {selected_emp['name']}")
                    st.write(f"**Designation:** {selected_emp['designation']}")
                    st.write(f"**Salary:** {selected_emp['salary']}")
                    
                    if st.button("Delete Employee", type="secondary"):
                        delete_employee(selected_emp_id)
                        st.success("Employee deleted successfully!")
                        st.rerun()
            
            # Salary Payment Section
            st.subheader("Record Salary Payment")
            with st.form("salary_payment"):
                emp_for_payment = st.selectbox("Select Employee", 
                                             employees_df['name'].tolist(), key="salary_emp")
                payment_amount = st.number_input("Payment Amount", min_value=0.0, step=1000.0)
                payment_date = st.date_input("Payment Date")
                payment_month = st.selectbox("For Month", 
                                           [f"{datetime.now().year}-{i:02d}" for i in range(1, 13)])
                
                pay_clicked = st.form_submit_button("Record Salary Payment")
                if pay_clicked:
                    selected_emp_id = employees_df[employees_df['name'] == emp_for_payment].iloc[0]['id']
                    record_salary_payment(selected_emp_id, payment_amount, 
                                        payment_date.strftime('%Y-%m-%d'), payment_month)
                    st.success("Salary payment recorded successfully!")
        else:
            st.info("No employees added yet.")

def reports_analytics():
    st.header("📊 Reports & Analytics")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Expense Reports", "Employee Reports", "Salary Ledger", "Data Import/Export"])
    
    with tab1:
        st.subheader("Expense Reports")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            report_month = st.selectbox("Select Month", list(range(1, 13)), key="rep_month")
        with col_r2:
            current_year = datetime.now().year
            report_year = st.selectbox("Select Year", 
                                     list(range(current_year-2, current_year+1)), key="rep_year")
        
        expenses_df = get_expenses(report_month, report_year)
        
        if not expenses_df.empty:
            # Summary
            total_expenses = expenses_df['amount'].sum()
            category_summary = expenses_df.groupby('category')['amount'].sum().reset_index()
            
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
                st.dataframe(category_summary, use_container_width=True)
            
            with col_s2:
                st.bar_chart(category_summary.set_index('category'))
            
            # Generate PDF
            if st.button("Generate Expense PDF Report"):
                pdf = PDFReport()
                pdf.add_page()
                
                pdf.chapter_title(f"Expense Report - {report_month}/{report_year}")
                
                # Prepare data for PDF
                pdf_data = []
                headers = ['ID', 'Category', 'Amount', 'Date', 'Description']
                
                for _, row in expenses_df.iterrows():
                    pdf_data.append([
                        row['id'],
                        row['category'],
                        f"₹{row['amount']:,.2f}",
                        row['date'],
                        row['description'] or '-'
                    ])
                
                pdf.chapter_body(pdf_data, headers)
                
                # Summary
                pdf.ln(10)
                pdf.chapter_title("Summary")
                pdf.set_font('Arial', 'B', 11)
                pdf.cell(0, 10, f'Total Expenses: ₹{total_expenses:,.2f}', 0, 1)
                
                # Save to bytes
                pdf_output = pdf.output(dest='S').encode('latin1')
                
                st.download_button(
                    label="Download Expense PDF",
                    data=pdf_output,
                    file_name=f"expense_report_{report_year}_{report_month}.pdf",
                    mime="application/pdf"
                )
        
        else:
            st.info("No expenses found for the selected period.")
    
    with tab2:
        st.subheader("Employee Reports")
        
        employees_df = get_employees()
        
        if not employees_df.empty:
            total_salary = employees_df['salary'].sum()
            active_employees = len(employees_df)
            
            col_emp1, col_emp2, col_emp3 = st.columns(3)
            with col_emp1:
                st.metric("Total Employees", active_employees)
            with col_emp2:
                st.metric("Total Monthly Salary", f"₹{total_salary:,.2f}")
            with col_emp3:
                avg_salary = total_salary / active_employees if active_employees > 0 else 0
                st.metric("Average Salary", f"₹{avg_salary:,.2f}")
            
            st.dataframe(employees_df, use_container_width=True)
            
            # Generate Salary Slip
            st.subheader("Generate Salary Slip")
            selected_emp_slip = st.selectbox("Select Employee", 
                                           employees_df['name'].tolist(), key="slip_emp")
            slip_month = st.selectbox("Select Month", 
                                    [f"{datetime.now().year}-{i:02d}" for i in range(1, 13)], key="slip_month")
            
            if st.button("Generate Salary Slip"):
                emp_data = employees_df[employees_df['name'] == selected_emp_slip].iloc[0]
                
                pdf = PDFReport()
                pdf.add_page()
                
                # Salary Slip Header
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, 'SALARY SLIP', 0, 1, 'C')
                pdf.ln(5)
                
                # Employee Details
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, f'Employee Details', 0, 1)
                pdf.set_font('Arial', '', 11)
                pdf.cell(0, 8, f'Name: {emp_data["name"]}', 0, 1)
                pdf.cell(0, 8, f'Designation: {emp_data["designation"]}', 0, 1)
                pdf.cell(0, 8, f'Bank: {emp_data["bank_name"]}', 0, 1)
                pdf.cell(0, 8, f'Account: {emp_data["bank_account"]}', 0, 1)
                pdf.ln(5)
                
                # Salary Details
                pdf.set_font('Arial', 'B', 12)
                pdf.cell(0, 10, f'Salary Details for {slip_month}', 0, 1)
                pdf.set_font('Arial', '', 11)
                pdf.cell(0, 8, f'Basic Salary: ₹{emp_data["salary"]:,.2f}', 0, 1)
                pdf.cell(0, 8, f'Total Amount: ₹{emp_data["salary"]:,.2f}', 0, 1)
                pdf.ln(10)
                
                pdf.set_font('Arial', 'I', 10)
                pdf.cell(0, 8, 'Generated on: ' + datetime.now().strftime('%Y-%m-%d %H:%M'), 0, 1)
                
                pdf_output = pdf.output(dest='S').encode('latin1')
                
                st.download_button(
                    label="Download Salary Slip",
                    data=pdf_output,
                    file_name=f"salary_slip_{emp_data['name']}_{slip_month}.pdf",
                    mime="application/pdf"
                )
    
    with tab3:
        st.subheader("Salary Ledger")
        
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            ledger_month = st.selectbox("Select Month", list(range(1, 13)), key="led_month")
        with col_l2:
            ledger_year = st.selectbox("Select Year", 
                                     list(range(current_year-2, current_year+1)), key="led_year")
        
        salary_payments = get_salary_payments(ledger_month, ledger_year)
        
        if not salary_payments.empty:
            total_paid = salary_payments['amount'].sum()
            
            st.metric("Total Salary Paid", f"₹{total_paid:,.2f}")
            st.dataframe(salary_payments, use_container_width=True)
        else:
            st.info("No salary payments recorded for the selected period.")
    
    with tab4:
        st.subheader("Data Import/Export")
        
        col_io1, col_io2 = st.columns(2)
        
        with col_io1:
            st.write("### Export Data")
            
            export_type = st.selectbox("Select Data to Export", 
                                     ["Expenses", "Employees", "Salary Payments"])
            
            if st.button("Export to CSV"):
                if export_type == "Expenses":
                    data = get_expenses()
                elif export_type == "Employees":
                    data = get_employees()
                else:
                    data = get_salary_payments()
                
                csv = data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"{export_type.lower()}_export.csv",
                    mime="text/csv"
                )
        
        with col_io2:
            st.write("### Import Data")
            
            import_type = st.selectbox("Select Data to Import", 
                                     ["Expenses", "Employees"], key="import_type")
            
            uploaded_file = st.file_uploader("Choose CSV file", type=['csv'])
            
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    st.write("Preview of data to import:")
                    st.dataframe(df.head())
                    
                    if st.button("Import Data"):
                        # This is a basic implementation - you might want to add more validation
                        conn = sqlite3.connect('company_data.db')
                        if import_type == "Expenses":
                            df.to_sql('expenses', conn, if_exists='append', index=False)
                        else:
                            df.to_sql('employees', conn, if_exists='append', index=False)
                        conn.close()
                        st.success("Data imported successfully!")
                except Exception as e:
                    st.error(f"Error importing data: {str(e)}")

if __name__ == "__main__":
    main()
