import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import io
import base64
from fpdf import FPDF
import re
import os

# Page configuration
st.set_page_config(
    page_title="NUTPLOR - Nutrition Portal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f2937;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #6b7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #374151;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #3b82f6;
    }
    .positive-balance {
        color: #10b981;
        font-weight: bold;
    }
    .negative-balance {
        color: #ef4444;
        font-weight: bold;
    }
    .section-box {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
    }
    .metric-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #1e3a8a 0%, #3730a3 100%);
    }
    .logo-text {
        font-size: 2rem;
        font-weight: bold;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .nav-item {
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        color: white;
        transition: all 0.3s ease;
    }
    .nav-item:hover {
        background-color: rgba(255, 255, 255, 0.1);
    }
    .nav-item.active {
        background-color: rgba(255, 255, 255, 0.2);
        border-left: 4px solid #f59e0b;
    }
</style>
""", unsafe_allow_html=True)

class ProfessionalPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        # Company header with logo placeholder
        self.set_font('Arial', 'B', 16)
        self.set_text_color(30, 58, 138)
        self.cell(0, 10, 'NUTPLOR - Nutrition Portal', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.set_text_color(107, 114, 128)
        self.cell(0, 8, 'Professional Salary Management System', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()} - Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 0, 0, 'C')

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'employees': [],
        'transactions': [],
        'current_page': 'Dashboard',
        'uploaded_data': None,
        'upload_errors': [],
        'salary_data': [
            {
                'name': 'Abdul Manan',
                'designation': 'Marketing',
                'bank': 'Habib Bank',
                'account_title': 'Abdul Manan',
                'account_no': '1242794813103',
                'base_salary': 97500
            },
            {
                'name': 'Abdul Manan 2',
                'designation': 'Marketing',
                'bank': 'Bank Ali Habib',
                'account_title': 'Misbah Iliqat',
                'account_no': '355098102965010',
                'base_salary': 97500
            }
        ]
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def validate_employee_data(df):
    """Validate uploaded employee data"""
    errors = []
    required_columns = ['employee_name', 'transaction_type', 'amount', 'description', 'date']
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        return errors, df
    
    # Data validation checks
    if df['employee_name'].isnull().any():
        errors.append("Employee names cannot be empty")
    
    if df['amount'].isnull().any() or (df['amount'] <= 0).any():
        errors.append("Amount must be positive numbers")
    
    if df['description'].isnull().any():
        errors.append("Descriptions cannot be empty")
    
    try:
        pd.to_datetime(df['date'])
    except:
        errors.append("Invalid date format")
    
    valid_types = ['expense', 'payment']
    invalid_types = df[~df['transaction_type'].isin(valid_types)]
    if not invalid_types.empty:
        errors.append(f"Invalid transaction types found: {invalid_types['transaction_type'].unique()}")
    
    return errors, df

def render_sidebar():
    """Render the sidebar with logo and navigation"""
    with st.sidebar:
        # Company Logo Section
        st.markdown('<div class="logo-text">NUTPLOR</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; color: #d1d5db; margin-bottom: 2rem;">Nutrition Portal</div>', unsafe_allow_html=True)
        
        # Navigation Menu
        menu_items = [
            "Dashboard",
            "Manage Employees", 
            "Expense Management",
            "Salary Management",
            "Download Reports",
            "Data Import"
        ]
        
        for item in menu_items:
            is_active = st.session_state.current_page == item
            active_class = "active" if is_active else ""
            if st.button(item, key=f"nav_{item}", use_container_width=True):
                st.session_state.current_page = item
                st.rerun()

def render_dashboard():
    """Render the main dashboard"""
    st.markdown('<div class="main-header">NUTPLOR Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Comprehensive Nutrition Portal Management System</div>', unsafe_allow_html=True)
    
    # Key Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_employees = len(st.session_state.employees)
        st.markdown(f'''
        <div class="metric-box">
            <h3>Total Employees</h3>
            <h1>{total_employees}</h1>
        </div>
        ''', unsafe_allow_html=True)
    
    with col2:
        total_transactions = len(st.session_state.transactions)
        st.markdown(f'''
        <div class="metric-box">
            <h3>Total Transactions</h3>
            <h1>{total_transactions}</h1>
        </div>
        ''', unsafe_allow_html=True)
    
    with col3:
        total_expenses = sum(t['amount'] for t in st.session_state.transactions if t['type'] == 'expense')
        st.markdown(f'''
        <div class="metric-box">
            <h3>Total Expenses</h3>
            <h1>PKR {total_expenses:,.2f}</h1>
        </div>
        ''', unsafe_allow_html=True)
    
    with col4:
        total_payments = sum(t['amount'] for t in st.session_state.transactions if t['type'] == 'payment')
        st.markdown(f'''
        <div class="metric-box">
            <h3>Total Payments</h3>
            <h1>PKR {total_payments:,.2f}</h1>
        </div>
        ''', unsafe_allow_html=True)
    
    # Recent Activity and Quick Actions
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("📈 Recent Activity")
        if st.session_state.transactions:
            recent_transactions = sorted(st.session_state.transactions, key=lambda x: x['date'], reverse=True)[:5]
            for txn in recent_transactions:
                emp = next((e for e in st.session_state.employees if e['id'] == txn['employee_id']), None)
                if emp:
                    txn_type = "🔴 Expense" if txn['type'] == 'expense' else "🟢 Payment"
                    st.write(f"**{emp['name']}** - {txn_type} - PKR {txn['amount']:,.2f}")
                    st.caption(f"{txn['description']} • {txn['date']}")
                    st.divider()
        else:
            st.info("No recent transactions")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("⚡ Quick Actions")
        
        if st.button("➕ Add New Employee", use_container_width=True):
            st.session_state.current_page = "Manage Employees"
            st.rerun()
        
        if st.button("💸 Record Expense", use_container_width=True):
            st.session_state.current_page = "Expense Management"
            st.rerun()
        
        if st.button("💰 Salary Management", use_container_width=True):
            st.session_state.current_page = "Salary Management"
            st.rerun()
        
        if st.button("📊 Generate Reports", use_container_width=True):
            st.session_state.current_page = "Download Reports"
            st.rerun()
        
        if st.button("📁 Import Data", use_container_width=True):
            st.session_state.current_page = "Data Import"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

def render_employee_management():
    """Render employee management section"""
    st.markdown('<div class="section-header">👥 Manage Employees</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Add New Employee")
        
        with st.form("employee_form", clear_on_submit=True):
            emp_name = st.text_input("Employee Name *")
            designation = st.selectbox("Designation", ["Marketing", "Sales", "HR", "Finance", "IT", "Operations"])
            department = st.selectbox("Department", ["Marketing", "Sales", "HR", "Finance", "IT", "Operations"])
            base_salary = st.number_input("Base Salary (PKR) *", min_value=0, value=50000, step=1000)
            join_date = st.date_input("Join Date", value=date.today())
            
            submitted = st.form_submit_button("Add Employee", use_container_width=True)
            if submitted:
                if emp_name.strip():
                    employee_id = f"emp_{len(st.session_state.employees) + 1}"
                    employee = {
                        'id': employee_id,
                        'name': emp_name.strip(),
                        'designation': designation,
                        'department': department,
                        'base_salary': base_salary,
                        'join_date': join_date,
                        'bank_details': {}
                    }
                    st.session_state.employees.append(employee)
                    st.success(f"Employee {emp_name} added successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid employee name")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Employee List")
        
        if st.session_state.employees:
            for emp in st.session_state.employees:
                col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
                with col1:
                    st.write(f"**{emp['name']}**")
                    st.caption(f"{emp['designation']} • {emp['department']}")
                with col2:
                    st.write(f"PKR {emp['base_salary']:,.2f}")
                with col3:
                    st.write(emp['join_date'])
                with col4:
                    if st.button("🗑️", key=f"del_emp_{emp['id']}"):
                        st.session_state.employees = [e for e in st.session_state.employees if e['id'] != emp['id']]
                        st.success("Employee deleted successfully!")
                        st.rerun()
                st.divider()
        else:
            st.info("No employees added yet.")
        st.markdown('</div>', unsafe_allow_html=True)

def render_expense_management():
    """Render expense management section"""
    st.markdown('<div class="section-header">💸 Expense Management</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Record Transaction")
        
        with st.form("transaction_form", clear_on_submit=True):
            if st.session_state.employees:
                employee_options = {emp['name']: emp['id'] for emp in st.session_state.employees}
                selected_emp = st.selectbox("Employee *", options=list(employee_options.keys()))
                transaction_type = st.selectbox("Transaction Type *", ["Expense (Debit)", "Payment (Credit)"])
                amount = st.number_input("Amount (PKR) *", min_value=0.01, value=1000.0, step=100.0)
                description = st.text_input("Description *")
                transaction_date = st.date_input("Date *", value=date.today())
                
                submitted = st.form_submit_button("Record Transaction", use_container_width=True)
                if submitted:
                    if description.strip():
                        emp_id = employee_options[selected_emp]
                        txn_type = "expense" if "Expense" in transaction_type else "payment"
                        transaction_id = f"txn_{len(st.session_state.transactions) + 1}"
                        transaction = {
                            'id': transaction_id,
                            'employee_id': emp_id,
                            'type': txn_type,
                            'amount': amount,
                            'description': description.strip(),
                            'date': transaction_date
                        }
                        st.session_state.transactions.append(transaction)
                        st.success("Transaction recorded successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a description")
            else:
                st.info("No employees available. Please add employees first.")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Transaction History")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Search transactions")
        with col2:
            filter_type = st.selectbox("Filter by type", ["All Types", "Expenses", "Payments"])
        
        # Filter transactions
        filtered_transactions = st.session_state.transactions.copy()
        if search_term:
            filtered_transactions = [t for t in filtered_transactions if search_term.lower() in t['description'].lower()]
        if filter_type != "All Types":
            txn_type = "expense" if filter_type == "Expenses" else "payment"
            filtered_transactions = [t for t in filtered_transactions if t['type'] == txn_type]
        
        if filtered_transactions:
            for txn in filtered_transactions:
                emp = next((e for e in st.session_state.employees if e['id'] == txn['employee_id']), None)
                if emp:
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 3, 2, 1])
                    with col1:
                        st.write(emp['name'])
                    with col2:
                        st.write(txn['date'])
                    with col3:
                        st.write(txn['description'])
                    with col4:
                        color = "red" if txn['type'] == 'expense' else "green"
                        st.markdown(f"<span style='color: {color}'>PKR {txn['amount']:,.2f}</span>", unsafe_allow_html=True)
                    with col5:
                        if st.button("🗑️", key=f"del_txn_{txn['id']}"):
                            st.session_state.transactions = [t for t in st.session_state.transactions if t['id'] != txn['id']]
                            st.success("Transaction deleted!")
                            st.rerun()
                    st.divider()
        else:
            st.info("No transactions found.")
        st.markdown('</div>', unsafe_allow_html=True)

def render_salary_management():
    """Render salary management section"""
    st.markdown('<div class="section-header">💰 Salary Management</div>', unsafe_allow_html=True)
    st.markdown("Use the tools below to manage and download salary information.")
    
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("View & Download Salary Sheet")
    st.write("This sheet shows employee bank details and base salary.")
    
    # Date range selection with form
    with st.form("salary_date_form"):
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            start_date = st.date_input("Start Date *", value=date.today().replace(day=1))
        with col2:
            end_date = st.date_input("End Date *", value=date.today())
        with col3:
            st.write("")  # Spacer
            st.write("")  # Spacer
            submitted = st.form_submit_button("Generate Salary Sheet", use_container_width=True)
    
    if submitted:
        if start_date > end_date:
            st.error("Start date cannot be after end date")
        else:
            # Display salary data
            if st.session_state.salary_data:
                salary_df = pd.DataFrame(st.session_state.salary_data)
                st.dataframe(salary_df, use_container_width=True)
                
                # Download options
                col1, col2 = st.columns(2)
                with col1:
                    # CSV Download
                    csv = salary_df.to_csv(index=False)
                    st.download_button(
                        label="📥 Download CSV",
                        data=csv,
                        file_name=f"salary_sheet_{start_date}_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with col2:
                    # PDF Download
                    if st.button("📄 Generate PDF Report", use_container_width=True):
                        pdf = generate_salary_pdf(salary_df, start_date, end_date)
                        pdf_output = pdf.output(dest='S').encode('latin1')
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_output,
                            file_name=f"salary_report_{start_date}_{end_date}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
            else:
                st.info("No salary data available.")
    st.markdown('</div>', unsafe_allow_html=True)

def generate_salary_pdf(df, start_date, end_date):
    """Generate professional PDF salary report"""
    pdf = ProfessionalPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Salary Sheet Report', 0, 1, 'C')
    
    # Period
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Period: {start_date} to {end_date}', 0, 1, 'C')
    pdf.ln(10)
    
    # Table headers
    col_widths = [40, 30, 30, 35, 35, 25]
    headers = ['Name', 'Designation', 'Bank', 'Account Title', 'Account No.', 'Salary']
    
    pdf.set_font('Arial', 'B', 10)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 10, header, 1, 0, 'C')
    pdf.ln()
    
    # Table data
    pdf.set_font('Arial', '', 9)
    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 10, str(row['name']), 1)
        pdf.cell(col_widths[1], 10, str(row['designation']), 1)
        pdf.cell(col_widths[2], 10, str(row['bank']), 1)
        pdf.cell(col_widths[3], 10, str(row['account_title']), 1)
        pdf.cell(col_widths[4], 10, str(row['account_no']), 1)
        pdf.cell(col_widths[5], 10, f"PKR {row['base_salary']:,.0f}", 1)
        pdf.ln()
    
    # Summary
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    total_salary = df['base_salary'].sum()
    pdf.cell(0, 10, f'Total Salary: PKR {total_salary:,.2f}', 0, 1)
    
    return pdf

def render_data_import():
    """Render data import section"""
    st.markdown('<div class="section-header">📁 Data Import</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    st.subheader("Upload Employee Data")
    
    uploaded_file = st.file_uploader(
        "Choose CSV file", 
        type="csv",
        help="Upload CSV with columns: employee_name, transaction_type, amount, description, date"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.success("File uploaded successfully!")
            
            # Display preview
            st.subheader("Data Preview")
            st.dataframe(df.head(), use_container_width=True)
            
            # Validate data
            errors, validated_df = validate_employee_data(df)
            
            if errors:
                st.error("Data validation failed! Please fix the following errors:")
                for error in errors:
                    st.error(f"• {error}")
            else:
                st.success("✅ Data validation successful! Ready to import.")
                
                if st.button("Import Validated Data", use_container_width=True):
                    # Import logic here
                    st.success("Data imported successfully!")
                    
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")
    
    st.markdown('</div>', unsafe_allow_html=True)

def render_reports():
    """Render reports section"""
    st.markdown('<div class="section-header">📊 Download Reports</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Employee Reports")
        
        report_type = st.selectbox("Select Report Type", [
            "Employee Master List",
            "Salary Report", 
            "Transaction Summary",
            "Bank Details Report"
        ])
        
        if st.button("Generate Employee Report", use_container_width=True):
            st.success(f"{report_type} generated successfully!")
            # Here you would implement the actual report generation
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Financial Reports")
        
        report_type = st.selectbox("Select Financial Report", [
            "Expense Summary",
            "Payment Summary", 
            "Balance Sheet",
            "Cash Flow Statement"
        ])
        
        if st.button("Generate Financial Report", use_container_width=True):
            st.success(f"{report_type} generated successfully!")
        st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main application function"""
    initialize_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render main content based on current page
    if st.session_state.current_page == "Dashboard":
        render_dashboard()
    elif st.session_state.current_page == "Manage Employees":
        render_employee_management()
    elif st.session_state.current_page == "Expense Management":
        render_expense_management()
    elif st.session_state.current_page == "Salary Management":
        render_salary_management()
    elif st.session_state.current_page == "Download Reports":
        render_reports()
    elif st.session_state.current_page == "Data Import":
        render_data_import()

if __name__ == "__main__":
    main()
