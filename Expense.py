import streamlit as st
import pandas as pd
from datetime import datetime
import io

from utils.database import DatabaseManager
from utils.pdf_generator import PDFGenerator
from utils.excel_handler import ExcelHandler

# Page configuration
st.set_page_config(
    page_title="Nutrion Management System",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'db_manager' not in st.session_state:
    st.session_state.db_manager = DatabaseManager()
if 'pdf_generator' not in st.session_state:
    st.session_state.pdf_generator = PDFGenerator()
if 'excel_handler' not in st.session_state:
    st.session_state.excel_handler = ExcelHandler()

def main():
    st.sidebar.title("🏢 Nutrion Management")
    
    menu_options = [
        "Dashboard",
        "Employee Management",
        "Salary Processing",
        "Company Expenses",
        "Expense Categories",
        "Employee Ledger",
        "Data Import/Export",
        "Reports"
    ]
    
    choice = st.sidebar.selectbox("Navigation", menu_options)
    
    if choice == "Dashboard":
        show_dashboard()
    elif choice == "Employee Management":
        employee_management()
    elif choice == "Salary Processing":
        salary_processing()
    elif choice == "Company Expenses":
        company_expenses()
    elif choice == "Expense Categories":
        expense_categories()
    elif choice == "Employee Ledger":
        employee_ledger()
    elif choice == "Data Import/Export":
        data_import_export()
    elif choice == "Reports":
        reports_section()

def show_dashboard():
    st.title("📊 Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Get data for dashboard
    employees = st.session_state.db_manager.get_employees()
    expenses = st.session_state.db_manager.get_company_expenses()
    
    with col1:
        st.metric("Total Employees", len(employees))
    with col2:
        total_expenses = expenses['amount'].sum() if not expenses.empty else 0
        st.metric("Total Expenses", f"Rs. {total_expenses:,.2f}")
    with col3:
        avg_salary = employees['basic_salary'].mean() if not employees.empty else 0
        st.metric("Average Salary", f"Rs. {avg_salary:,.2f}")
    with col4:
        active_employees = len(employees[employees['status'] == 'Active'])
        st.metric("Active Employees", active_employees)
    
    # Recent activities
    st.subheader("Recent Activities")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Recent Employees**")
        if not employees.empty:
            st.dataframe(employees[['employee_id', 'name', 'designation']].head(), use_container_width=True)
        else:
            st.info("No employees found")
    
    with col2:
        st.write("**Recent Expenses**")
        if not expenses.empty:
            recent_expenses = expenses[['date', 'category_name', 'amount', 'description']].head()
            st.dataframe(recent_expenses, use_container_width=True)
        else:
            st.info("No expenses found")

def employee_management():
    st.title("👥 Employee Management")
    
    tab1, tab2, tab3 = st.tabs(["Add Employee", "View/Edit Employees", "Employee Details"])
    
    with tab1:
        st.subheader("Add New Employee")
        
        with st.form("add_employee_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                employee_id = st.text_input("Employee ID*")
                name = st.text_input("Full Name*")
                designation = st.text_input("Designation*")
                basic_salary = st.number_input("Basic Salary*", min_value=0.0, step=1000.0)
            
            with col2:
                account_no = st.text_input("Account Number*")
                account_title = st.text_input("Account Title*")
                bank_name = st.text_input("Bank Name*")
                joining_date = st.date_input("Joining Date*")
            
            submitted = st.form_submit_button("Add Employee")
            
            if submitted:
                if all([employee_id, name, designation, account_no, account_title, bank_name]):
                    employee_data = (
                        employee_id, name, designation, account_no, 
                        account_title, bank_name, basic_salary, joining_date
                    )
                    
                    if st.session_state.db_manager.add_employee(employee_data):
                        st.success("Employee added successfully!")
                    else:
                        st.error("Failed to add employee. Employee ID might already exist.")
                else:
                    st.error("Please fill all required fields!")
    
    with tab2:
        st.subheader("Employee List")
        
        employees = st.session_state.db_manager.get_employees()
        if not employees.empty:
            # Display editable table
            edited_df = st.data_editor(
                employees[['employee_id', 'name', 'designation', 'basic_salary', 'status']],
                use_container_width=True,
                num_rows="dynamic"
            )
            
            if st.button("Update Employees"):
                # Implementation for batch updates
                st.info("Batch update functionality would be implemented here")
        
        else:
            st.info("No employees found")
    
    with tab3:
        st.subheader("Employee Details")
        
        employees = st.session_state.db_manager.get_employees()
        if not employees.empty:
            selected_employee = st.selectbox(
                "Select Employee",
                options=employees['employee_id'].tolist(),
                format_func=lambda x: f"{x} - {employees[employees['employee_id'] == x]['name'].iloc[0]}"
            )
            
            if selected_employee:
                employee_data = employees[employees['employee_id'] == selected_employee].iloc[0]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Personal Details**")
                    st.write(f"Name: {employee_data['name']}")
                    st.write(f"Designation: {employee_data['designation']}")
                    st.write(f"Joining Date: {employee_data['joining_date']}")
                    st.write(f"Status: {employee_data['status']}")
                
                with col2:
                    st.write("**Bank Details**")
                    st.write(f"Account No: {employee_data['account_no']}")
                    st.write(f"Account Title: {employee_data['account_title']}")
                    st.write(f"Bank: {employee_data['bank_name']}")
                    st.write(f"Basic Salary: Rs. {employee_data['basic_salary']:,.2f}")
                
                # Edit/Delete options
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Edit Employee", key="edit_emp"):
                        st.session_state.editing_employee = selected_employee
                        st.rerun()
                
                with col2:
                    if st.button("Delete Employee", type="secondary"):
                        if st.session_state.db_manager.delete_employee(selected_employee):
                            st.success("Employee deleted successfully!")
                            st.rerun()

def salary_processing():
    st.title("💰 Salary Processing")
    
    tab1, tab2, tab3 = st.tabs(["Process Salary", "Salary History", "Generate Salary Slip"])
    
    with tab1:
        st.subheader("Process Employee Salary")
        
        employees = st.session_state.db_manager.get_employees()
        if not employees.empty:
            selected_employee = st.selectbox(
                "Select Employee",
                options=employees['employee_id'].tolist(),
                format_func=lambda x: f"{x} - {employees[employees['employee_id'] == x]['name'].iloc[0]}"
            )
            
            if selected_employee:
                employee_data = employees[employees['employee_id'] == selected_employee].iloc[0]
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    month_year = st.text_input("Month-Year (e.g., Jan-2024)*")
                    basic_salary = st.number_input(
                        "Basic Salary", 
                        value=float(employee_data['basic_salary']),
                        min_value=0.0
                    )
                
                with col2:
                    allowances = st.number_input("Allowances", min_value=0.0, value=0.0)
                    deductions = st.number_input("Deductions", min_value=0.0, value=0.0)
                
                with col3:
                    net_salary = basic_salary + allowances - deductions
                    st.metric("Net Salary", f"Rs. {net_salary:,.2f}")
                    payment_date = st.date_input("Payment Date*")
                
                if st.button("Process Salary"):
                    if month_year and payment_date:
                        salary_data = (
                            selected_employee,
                            month_year,
                            basic_salary,
                            allowances,
                            deductions,
                            net_salary,
                            payment_date,
                            'Paid'
                        )
                        
                        if st.session_state.db_manager.process_salary(salary_data):
                            st.success("Salary processed successfully!")
                        else:
                            st.error("Failed to process salary")
                    else:
                        st.error("Please fill all required fields!")
        else:
            st.info("No employees found")
    
    with tab2:
        st.subheader("Salary History")
        # Implementation for salary history view
        st.info("Salary history functionality would be implemented here")
    
    with tab3:
        st.subheader("Generate Salary Slip")
        # Implementation for salary slip generation
        st.info("Salary slip generation functionality would be implemented here")

def company_expenses():
    st.title("💼 Company Expenses")
    
    tab1, tab2 = st.tabs(["Add Expense", "View Expenses"])
    
    with tab1:
        st.subheader("Add Company Expense")
        
        categories = st.session_state.db_manager.get_expense_categories()
        employees = st.session_state.db_manager.get_employees()
        
        with st.form("add_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Expense Date*")
                category_id = st.selectbox(
                    "Category*",
                    options=categories['id'].tolist(),
                    format_func=lambda x: categories[categories['id'] == x]['category_name'].iloc[0]
                )
                amount = st.number_input("Amount*", min_value=0.0, step=100.0)
            
            with col2:
                description = st.text_area("Description*")
                employee_id = st.selectbox(
                    "Assign to Employee (Optional)",
                    options=[None] + employees['employee_id'].tolist(),
                    format_func=lambda x: "Select Employee" if x is None else 
                    f"{x} - {employees[employees['employee_id'] == x]['name'].iloc[0]}"
                )
                reference_no = st.text_input("Reference No")
            
            submitted = st.form_submit_button("Add Expense")
            
            if submitted:
                if all([expense_date, category_id, amount, description]):
                    expense_data = (
                        expense_date,
                        category_id,
                        amount,
                        description,
                        employee_id if employee_id else None,
                        reference_no
                    )
                    
                    if st.session_state.db_manager.add_company_expense(expense_data):
                        st.success("Expense added successfully!")
                    else:
                        st.error("Failed to add expense")
                else:
                    st.error("Please fill all required fields!")
    
    with tab2:
        st.subheader("Expense Records")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date")
        with col2:
            end_date = st.date_input("End Date")
        
        if st.button("Load Expenses"):
            expenses = st.session_state.db_manager.get_company_expenses(start_date, end_date)
            
            if not expenses.empty:
                st.dataframe(expenses, use_container_width=True)
                
                # Download option
                pdf_bytes = st.session_state.pdf_generator.generate_expense_report(
                    expenses, start_date, end_date, {'name': 'Nutrion'}
                )
                
                st.download_button(
                    label="Download Expense Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"expense_report_{start_date}_to_{end_date}.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("No expenses found for the selected period")

def expense_categories():
    st.title("📋 Expense Categories")
    
    tab1, tab2 = st.tabs(["Add Category", "View Categories"])
    
    with tab1:
        st.subheader("Add New Category")
        
        with st.form("add_category_form"):
            category_name = st.text_input("Category Name*")
            description = st.text_area("Description")
            
            submitted = st.form_submit_button("Add Category")
            
            if submitted:
                if category_name:
                    if st.session_state.db_manager.add_expense_category(category_name, description):
                        st.success("Category added successfully!")
                    else:
                        st.error("Category already exists!")
                else:
                    st.error("Please enter category name!")
    
    with tab2:
        st.subheader("Category List")
        
        categories = st.session_state.db_manager.get_expense_categories()
        if not categories.empty:
            st.dataframe(categories, use_container_width=True)
        else:
            st.info("No categories found")

def employee_ledger():
    st.title("📒 Employee Ledger")
    
    employees = st.session_state.db_manager.get_employees()
    
    if not employees.empty:
        selected_employee = st.selectbox(
            "Select Employee",
            options=employees['employee_id'].tolist(),
            format_func=lambda x: f"{x} - {employees[employees['employee_id'] == x]['name'].iloc[0]}"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", key="ledger_start")
        with col2:
            end_date = st.date_input("End Date", key="ledger_end")
        
        if st.button("Load Ledger"):
            ledger = st.session_state.db_manager.get_employee_ledger(selected_employee, start_date, end_date)
            employee_info = employees[employees['employee_id'] == selected_employee].iloc[0]
            
            if not ledger.empty:
                st.subheader(f"Ledger for {employee_info['name']}")
                st.dataframe(ledger, use_container_width=True)
                
                # Download PDF
                pdf_bytes = st.session_state.pdf_generator.generate_employee_ledger(
                    ledger, employee_info, start_date, end_date
                )
                
                st.download_button(
                    label="Download Ledger (PDF)",
                    data=pdf_bytes,
                    file_name=f"ledger_{selected_employee}_{start_date}_to_{end_date}.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("No ledger entries found for the selected period")
    else:
        st.info("No employees found")

def data_import_export():
    st.title("📥 Data Import/Export")
    
    tab1, tab2, tab3 = st.tabs(["Import Employees", "Import Expenses", "Export Templates"])
    
    with tab1:
        st.subheader("Import Employees from Excel")
        
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'], key="emp_import")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                if st.button("Import Employees"):
                    success_count, error_count = st.session_state.excel_handler.process_employee_import(
                        df, st.session_state.db_manager
                    )
                    st.success(f"Import completed: {success_count} successful, {error_count} failed")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with tab2:
        st.subheader("Import Expenses from Excel")
        
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'], key="exp_import")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                st.write("Preview of uploaded data:")
                st.dataframe(df.head())
                
                if st.button("Import Expenses"):
                    success_count, error_count = st.session_state.excel_handler.process_expense_import(
                        df, st.session_state.db_manager
                    )
                    st.success(f"Import completed: {success_count} successful, {error_count} failed")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    with tab3:
        st.subheader("Download Templates")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download Employee Template"):
                template_df = st.session_state.excel_handler.generate_employee_template()
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    template_df.to_excel(writer, sheet_name='Employees', index=False)
                
                st.download_button(
                    label="Download Excel Template",
                    data=output.getvalue(),
                    file_name="employee_template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col2:
            if st.button("Download Expense Template"):
                template_df = st.session_state.excel_handler.generate_expense_template()
                
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    template_df.to_excel(writer, sheet_name='Expenses', index=False)
                
                st.download_button(
                    label="Download Excel Template",
                    data=output.getvalue(),
                    file_name="expense_template.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

def reports_section():
    st.title("📈 Reports")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Expense Summary", "Salary Summary", "Employee Summary"]
    )
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="report_start")
    with col2:
        end_date = st.date_input("End Date", key="report_end")
    
    if st.button("Generate Report"):
        if report_type == "Expense Summary":
            expenses = st.session_state.db_manager.get_company_expenses(start_date, end_date)
            
            if not expenses.empty:
                # Category-wise summary
                category_summary = expenses.groupby('category_name')['amount'].sum().reset_index()
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Expense by Category")
                    st.dataframe(category_summary, use_container_width=True)
                
                with col2:
                    st.subheader("Visualization")
                    # Simple bar chart using streamlit
                    st.bar_chart(category_summary.set_index('category_name'))
                
                # Download PDF report
                pdf_bytes = st.session_state.pdf_generator.generate_expense_report(
                    expenses, start_date, end_date, {'name': 'Nutrion'}
                )
                
                st.download_button(
                    label="Download Detailed Report (PDF)",
                    data=pdf_bytes,
                    file_name=f"expense_report_{start_date}_to_{end_date}.pdf",
                    mime="application/pdf"
                )
            else:
                st.info("No expenses found for the selected period")

if __name__ == "__main__":
    main()
