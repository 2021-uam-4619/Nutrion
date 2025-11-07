import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
import tempfile
import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

# Initialize database
def init_db():
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    
    # Expenses table
    c.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            amount REAL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Employees table
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            designation TEXT,
            bank_account TEXT,
            bank_name TEXT,
            salary REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def add_expense(date, category, amount, description):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('INSERT INTO expenses (date, category, amount, description) VALUES (?, ?, ?, ?)',
              (date, category, amount, description))
    conn.commit()
    conn.close()

def get_expenses(month=None, year=None):
    conn = sqlite3.connect('company_data.db')
    if month and year:
        expenses = pd.read_sql('SELECT * FROM expenses WHERE strftime("%m", date) = ? AND strftime("%Y", date) = ?', 
                             conn, params=(f"{month:02d}", str(year)))
    else:
        expenses = pd.read_sql('SELECT * FROM expenses ORDER BY date DESC', conn)
    conn.close()
    return expenses

def update_expense(expense_id, date, category, amount, description):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('''UPDATE expenses SET date=?, category=?, amount=?, description=? WHERE id=?''',
              (date, category, amount, description, expense_id))
    conn.commit()
    conn.close()

def delete_expense(expense_id):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM expenses WHERE id=?', (expense_id,))
    conn.commit()
    conn.close()

def add_employee(name, designation, bank_account, bank_name, salary):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('INSERT INTO employees (name, designation, bank_account, bank_name, salary) VALUES (?, ?, ?, ?, ?)',
              (name, designation, bank_account, bank_name, salary))
    conn.commit()
    conn.close()

def get_employees():
    conn = sqlite3.connect('company_data.db')
    employees = pd.read_sql('SELECT * FROM employees ORDER BY name', conn)
    conn.close()
    return employees

def update_employee(employee_id, name, designation, bank_account, bank_name, salary):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('''UPDATE employees SET name=?, designation=?, bank_account=?, bank_name=?, salary=? WHERE id=?''',
              (name, designation, bank_account, bank_name, salary, employee_id))
    conn.commit()
    conn.close()

def delete_employee(employee_id):
    conn = sqlite3.connect('company_data.db')
    c = conn.cursor()
    c.execute('DELETE FROM employees WHERE id=?', (employee_id,))
    conn.commit()
    conn.close()

def generate_expense_pdf(expenses_df, month, year):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title = Paragraph(f"Expense Report - {month}/{year}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Prepare data for table
    data = [['ID', 'Date', 'Category', 'Amount', 'Description']]
    total = 0
    
    for _, row in expenses_df.iterrows():
        data.append([
            str(row['id']),
            row['date'],
            row['category'],
            f"Rs. {row['amount']:,.2f}",
            row['description']
        ])
        total += row['amount']
    
    # Add total row
    data.append(['', '', 'TOTAL', f"Rs. {total:,.2f}", ''])
    
    # Create table
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -2), colors.beige),
        ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

def generate_salary_slip(employee, month, year):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title = Paragraph(f"SALARY SLIP - {month}/{year}", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Employee details
    details = [
        f"Employee Name: {employee['name']}",
        f"Designation: {employee['designation']}",
        f"Bank: {employee['bank_name']}",
        f"Account No: {employee['bank_account']}",
        f"Salary: Rs. {employee['salary']:,.2f}"
    ]
    
    for detail in details:
        elements.append(Paragraph(detail, styles['Normal']))
        elements.append(Spacer(1, 6))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer

def main():
    st.set_page_config(page_title="Company Management System", layout="wide")
    
    st.title("🏢 Company Management System")
    
    # Sidebar navigation
    menu = st.sidebar.selectbox("Navigation", [
        "Expense Management", 
        "Employee Management", 
        "Monthly Reports",
        "Data Import"
    ])
    
    if menu == "Expense Management":
        st.header("💰 Expense Management")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Add Expense", "View Expenses", "Edit Expense", "Delete Expense"])
        
        with tab1:
            st.subheader("Add New Expense")
            with st.form("add_expense_form"):
                col1, col2 = st.columns(2)
                with col1:
                    date = st.date_input("Date")
                    category = st.selectbox("Category", EXPENSE_CATEGORIES)
                with col2:
                    amount = st.number_input("Amount (Rs.)", min_value=0.0, step=100.0)
                    description = st.text_input("Description")
                
                submitted = st.form_submit_button("Add Expense")
                if submitted:
                    add_expense(date.strftime('%Y-%m-%d'), category, amount, description)
                    st.success("Expense added successfully!")
        
        with tab2:
            st.subheader("All Expenses")
            expenses_df = get_expenses()
            if not expenses_df.empty:
                st.dataframe(expenses_df.drop(columns=['created_at']), use_container_width=True)
            else:
                st.info("No expenses recorded yet.")
        
        with tab3:
            st.subheader("Edit Expense")
            expenses_df = get_expenses()
            if not expenses_df.empty:
                expense_id = st.selectbox("Select Expense to Edit", 
                                        expenses_df['id'].tolist(),
                                        format_func=lambda x: f"ID {x}: {expenses_df[expenses_df['id']==x]['description'].iloc[0]}")
                
                selected_expense = expenses_df[expenses_df['id'] == expense_id].iloc[0]
                
                with st.form("edit_expense_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_date = st.date_input("Date", value=datetime.strptime(selected_expense['date'], '%Y-%m-%d'))
                        edit_category = st.selectbox("Category", EXPENSE_CATEGORIES, 
                                                   index=EXPENSE_CATEGORIES.index(selected_expense['category']))
                    with col2:
                        edit_amount = st.number_input("Amount (Rs.)", value=float(selected_expense['amount']))
                        edit_description = st.text_input("Description", value=selected_expense['description'])
                    
                    submitted = st.form_submit_button("Update Expense")
                    if submitted:
                        update_expense(expense_id, edit_date.strftime('%Y-%m-%d'), edit_category, edit_amount, edit_description)
                        st.success("Expense updated successfully!")
                        st.rerun()
            else:
                st.info("No expenses to edit.")
        
        with tab4:
            st.subheader("Delete Expense")
            expenses_df = get_expenses()
            if not expenses_df.empty:
                expense_id = st.selectbox("Select Expense to Delete", 
                                        expenses_df['id'].tolist(),
                                        format_func=lambda x: f"ID {x}: {expenses_df[expenses_df['id']==x]['description'].iloc[0]}")
                
                if st.button("Delete Expense", type="secondary"):
                    delete_expense(expense_id)
                    st.success("Expense deleted successfully!")
                    st.rerun()
            else:
                st.info("No expenses to delete.")
    
    elif menu == "Employee Management":
        st.header("👥 Employee Management")
        
        tab1, tab2, tab3, tab4 = st.tabs(["Add Employee", "View Employees", "Edit Employee", "Delete Employee"])
        
        with tab1:
            st.subheader("Add New Employee")
            with st.form("add_employee_form"):
                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("Employee Name")
                    designation = st.text_input("Designation")
                    salary = st.number_input("Salary (Rs.)", min_value=0.0, step=1000.0)
                with col2:
                    bank_name = st.text_input("Bank Name")
                    bank_account = st.text_input("Bank Account Number")
                
                submitted = st.form_submit_button("Add Employee")
                if submitted:
                    add_employee(name, designation, bank_account, bank_name, salary)
                    st.success("Employee added successfully!")
        
        with tab2:
            st.subheader("All Employees")
            employees_df = get_employees()
            if not employees_df.empty:
                st.dataframe(employees_df.drop(columns=['created_at']), use_container_width=True)
                
                # Total salary calculation
                total_salary = employees_df['salary'].sum()
                st.metric("Total Monthly Salary", f"Rs. {total_salary:,.2f}")
            else:
                st.info("No employees added yet.")
        
        with tab3:
            st.subheader("Edit Employee")
            employees_df = get_employees()
            if not employees_df.empty:
                employee_id = st.selectbox("Select Employee to Edit", 
                                         employees_df['id'].tolist(),
                                         format_func=lambda x: f"ID {x}: {employees_df[employees_df['id']==x]['name'].iloc[0]}")
                
                selected_employee = employees_df[employees_df['id'] == employee_id].iloc[0]
                
                with st.form("edit_employee_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        edit_name = st.text_input("Employee Name", value=selected_employee['name'])
                        edit_designation = st.text_input("Designation", value=selected_employee['designation'])
                        edit_salary = st.number_input("Salary (Rs.)", value=float(selected_employee['salary']))
                    with col2:
                        edit_bank_name = st.text_input("Bank Name", value=selected_employee['bank_name'])
                        edit_bank_account = st.text_input("Bank Account Number", value=selected_employee['bank_account'])
                    
                    submitted = st.form_submit_button("Update Employee")
                    if submitted:
                        update_employee(employee_id, edit_name, edit_designation, edit_bank_account, edit_bank_name, edit_salary)
                        st.success("Employee updated successfully!")
                        st.rerun()
            else:
                st.info("No employees to edit.")
        
        with tab4:
            st.subheader("Delete Employee")
            employees_df = get_employees()
            if not employees_df.empty:
                employee_id = st.selectbox("Select Employee to Delete", 
                                         employees_df['id'].tolist(),
                                         format_func=lambda x: f"ID {x}: {employees_df[employees_df['id']==x]['name'].iloc[0]}")
                
                if st.button("Delete Employee", type="secondary"):
                    delete_employee(employee_id)
                    st.success("Employee deleted successfully!")
                    st.rerun()
            else:
                st.info("No employees to delete.")
    
    elif menu == "Monthly Reports":
        st.header("📊 Monthly Reports")
        
        col1, col2 = st.columns(2)
        with col1:
            year = st.selectbox("Select Year", range(2020, 2031), index=3)
        with col2:
            month = st.selectbox("Select Month", range(1, 13), format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
        
        # Expense Report
        st.subheader("Expense Report")
        monthly_expenses = get_expenses(month, year)
        
        if not monthly_expenses.empty:
            # Display summary
            total_expenses = monthly_expenses['amount'].sum()
            st.metric("Total Monthly Expenses", f"Rs. {total_expenses:,.2f}")
            
            # Category-wise breakdown
            category_totals = monthly_expenses.groupby('category')['amount'].sum().reset_index()
            st.subheader("Category-wise Breakdown")
            st.dataframe(category_totals, use_container_width=True)
            
            # Generate PDF
            if st.button("Generate Expense PDF Report"):
                pdf_buffer = generate_expense_pdf(monthly_expenses, month, year)
                st.download_button(
                    label="Download Expense Report PDF",
                    data=pdf_buffer,
                    file_name=f"expense_report_{month}_{year}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No expenses found for selected month.")
        
        # Salary Slips
        st.subheader("Salary Slips")
        employees_df = get_employees()
        
        if not employees_df.empty:
            employee_for_slip = st.selectbox("Select Employee for Salary Slip", 
                                           employees_df['name'].tolist())
            
            selected_employee = employees_df[employees_df['name'] == employee_for_slip].iloc[0]
            
            if st.button("Generate Salary Slip"):
                pdf_buffer = generate_salary_slip(selected_employee, month, year)
                st.download_button(
                    label=f"Download {selected_employee['name']} Salary Slip",
                    data=pdf_buffer,
                    file_name=f"salary_slip_{selected_employee['name']}_{month}_{year}.pdf",
                    mime="application/pdf"
                )
        else:
            st.info("No employees available for salary slips.")
    
    elif menu == "Data Import":
        st.header("📁 Data Import")
        
        tab1, tab2 = st.tabs(["Import Expenses", "Import Employees"])
        
        with tab1:
            st.subheader("Import Expenses from CSV/Excel")
            uploaded_file = st.file_uploader("Choose expenses file", type=['csv', 'xlsx'], key="expenses")
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.write("Preview of uploaded data:")
                    st.dataframe(df.head())
                    
                    # Check required columns
                    required_cols = ['date', 'category', 'amount', 'description']
                    if all(col in df.columns for col in required_cols):
                        if st.button("Import Expenses"):
                            conn = sqlite3.connect('company_data.db')
                            df.to_sql('expenses', conn, if_exists='append', index=False)
                            conn.close()
                            st.success(f"Successfully imported {len(df)} expenses!")
                    else:
                        st.error(f"File must contain these columns: {required_cols}")
                        
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        
        with tab2:
            st.subheader("Import Employees from CSV/Excel")
            uploaded_file = st.file_uploader("Choose employees file", type=['csv', 'xlsx'], key="employees")
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.write("Preview of uploaded data:")
                    st.dataframe(df.head())
                    
                    # Check required columns
                    required_cols = ['name', 'designation', 'bank_account', 'bank_name', 'salary']
                    if all(col in df.columns for col in required_cols):
                        if st.button("Import Employees"):
                            conn = sqlite3.connect('company_data.db')
                            df.to_sql('employees', conn, if_exists='append', index=False)
                            conn.close()
                            st.success(f"Successfully imported {len(df)} employees!")
                    else:
                        st.error(f"File must contain these columns: {required_cols}")
                        
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")

if __name__ == "__main__":
    main()
