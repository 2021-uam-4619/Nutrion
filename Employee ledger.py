import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import io
import base64
from fpdf import FPDF
import re

# Page configuration
st.set_page_config(
    page_title="NUTRION - Employee Ledger System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
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
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-box {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border-left: 4px solid #3b82f6;
    }
</style>
""", unsafe_allow_html=True)

class PDFGenerator(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
    
    def header(self):
        # Add company logo (you would replace this with your actual logo)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'NUTRION', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.cell(0, 10, 'Employee Ledger Report', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def validate_employee_data(df):
    """Validate employee data from uploaded file"""
    errors = []
    required_columns = ['employee_name', 'transaction_type', 'amount', 'description', 'date']
    
    # Check required columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        return errors, df
    
    # Check for empty values
    for col in required_columns:
        if df[col].isnull().any():
            empty_rows = df[df[col].isnull()].index.tolist()
            errors.append(f"Empty values in column '{col}' at rows: {empty_rows}")
    
    # Validate transaction types
    valid_types = ['expense', 'payment']
    invalid_types = df[~df['transaction_type'].isin(valid_types)]
    if not invalid_types.empty:
        errors.append(f"Invalid transaction types: {invalid_types['transaction_type'].unique()}")
    
    # Validate amount (must be numeric and positive)
    try:
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        invalid_amounts = df[df['amount'].isnull() | (df['amount'] <= 0)]
        if not invalid_amounts.empty:
            errors.append(f"Invalid amounts at rows: {invalid_amounts.index.tolist()}")
    except:
        errors.append("Amount column must contain numeric values")
    
    # Validate date format
    try:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        invalid_dates = df[df['date'].isnull()]
        if not invalid_dates.empty:
            errors.append(f"Invalid date format at rows: {invalid_dates.index.tolist()}")
    except:
        errors.append("Date column must be in valid date format")
    
    # Validate employee names (non-empty strings)
    invalid_names = df[df['employee_name'].isnull() | (df['employee_name'].str.strip() == '')]
    if not invalid_names.empty:
        errors.append(f"Invalid employee names at rows: {invalid_names.index.tolist()}")
    
    return errors, df

def initialize_session_state():
    """Initialize session state variables"""
    if 'employees' not in st.session_state:
        st.session_state.employees = []
    if 'transactions' not in st.session_state:
        st.session_state.transactions = []
    if 'uploaded_data' not in st.session_state:
        st.session_state.uploaded_data = None
    if 'upload_errors' not in st.session_state:
        st.session_state.upload_errors = []

def add_employee(name, initial_balance=0):
    """Add a new employee"""
    employee_id = f"emp_{len(st.session_state.employees) + 1}"
    employee = {
        'id': employee_id,
        'name': name,
        'initial_balance': initial_balance
    }
    st.session_state.employees.append(employee)
    
    # Add initial balance as transaction if not zero
    if initial_balance != 0:
        transaction_type = 'payment' if initial_balance > 0 else 'expense'
        add_transaction(
            employee_id=employee_id,
            transaction_type=transaction_type,
            amount=abs(initial_balance),
            description="Initial balance",
            transaction_date=date.today()
        )

def add_transaction(employee_id, transaction_type, amount, description, transaction_date):
    """Add a new transaction"""
    transaction_id = f"txn_{len(st.session_state.transactions) + 1}"
    transaction = {
        'id': transaction_id,
        'employee_id': employee_id,
        'type': transaction_type,
        'amount': amount,
        'description': description,
        'date': transaction_date
    }
    st.session_state.transactions.append(transaction)

def get_employee_ledger():
    """Calculate ledger for all employees"""
    ledger = []
    for employee in st.session_state.employees:
        employee_transactions = [t for t in st.session_state.transactions if t['employee_id'] == employee['id']]
        
        total_expenses = sum(t['amount'] for t in employee_transactions if t['type'] == 'expense')
        total_payments = sum(t['amount'] for t in employee_transactions if t['type'] == 'payment')
        balance = total_expenses - total_payments
        
        ledger.append({
            'id': employee['id'],
            'name': employee['name'],
            'total_expenses': total_expenses,
            'total_payments': total_payments,
            'balance': balance
        })
    
    return ledger

def generate_pdf_report(employee_id, start_date=None, end_date=None):
    """Generate PDF report for an employee"""
    employee = next((e for e in st.session_state.employees if e['id'] == employee_id), None)
    if not employee:
        return None
    
    # Filter transactions
    transactions = [t for t in st.session_state.transactions if t['employee_id'] == employee_id]
    if start_date:
        transactions = [t for t in transactions if t['date'] >= start_date]
    if end_date:
        transactions = [t for t in transactions if t['date'] <= end_date]
    
    # Sort by date
    transactions.sort(key=lambda x: x['date'])
    
    # Calculate running balance
    running_balance = 0
    transaction_data = []
    for t in transactions:
        if t['type'] == 'expense':
            running_balance += t['amount']
        else:
            running_balance -= t['amount']
        
        transaction_data.append({
            'date': t['date'],
            'type': t['type'].title(),
            'description': t['description'],
            'amount': t['amount'],
            'balance': running_balance
        })
    
    # Create PDF
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Employee information
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, f"Employee: {employee['name']}", 0, 1)
    
    # Period information
    period_text = "All Time"
    if start_date or end_date:
        start_str = start_date.strftime('%Y-%m-%d') if start_date else "Beginning"
        end_str = end_date.strftime('%Y-%m-%d') if end_date else "Today"
        period_text = f"Period: {start_str} to {end_str}"
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, period_text, 0, 1)
    pdf.ln(5)
    
    # Summary metrics
    total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'expense')
    total_payments = sum(t['amount'] for t in transactions if t['type'] == 'payment')
    final_balance = total_expenses - total_payments
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(60, 8, "Total Expenses:", 0, 0)
    pdf.cell(30, 8, f"PKR {total_expenses:.2f}", 0, 1)
    pdf.cell(60, 8, "Total Payments:", 0, 0)
    pdf.cell(30, 8, f"PKR {total_payments:.2f}", 0, 1)
    pdf.cell(60, 8, "Current Balance:", 0, 0)
    balance_text = f"PKR {abs(final_balance):.2f} ({'Due' if final_balance > 0 else 'Advance'})"
    pdf.cell(30, 8, balance_text, 0, 1)
    pdf.ln(5)
    
    # Transaction table header
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(25, 8, "Date", 1, 0, 'C')
    pdf.cell(20, 8, "Type", 1, 0, 'C')
    pdf.cell(70, 8, "Description", 1, 0, 'C')
    pdf.cell(25, 8, "Amount", 1, 0, 'C')
    pdf.cell(35, 8, "Balance", 1, 1, 'C')
    
    # Transaction rows
    pdf.set_font('Arial', '', 9)
    for t in transaction_data:
        pdf.cell(25, 8, t['date'].strftime('%Y-%m-%d'), 1, 0)
        pdf.cell(20, 8, t['type'], 1, 0)
        pdf.cell(70, 8, t['description'][:30], 1, 0)  # Limit description length
        pdf.cell(25, 8, f"PKR {t['amount']:.2f}", 1, 0, 'R')
        balance_display = f"PKR {abs(t['balance']):.2f} {'(Due)' if t['balance'] > 0 else '(Advance)'}"
        pdf.cell(35, 8, balance_display, 1, 1, 'R')
    
    return pdf

def main():
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">NUTRION</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Employee Ledger System</div>', unsafe_allow_html=True)
    st.markdown("Track expenses, payments, and balances for all employees")
    
    # Main layout
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Add Employee Section
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Add New Employee")
        
        with st.form("employee_form"):
            emp_name = st.text_input("Employee Name", key="emp_name")
            initial_balance = st.number_input("Initial Balance (PKR)", value=0.0, step=100.0, key="initial_balance")
            
            if st.form_submit_button("Add Employee", use_container_width=True):
                if emp_name.strip():
                    add_employee(emp_name.strip(), initial_balance)
                    st.success(f"Employee {emp_name} added successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid employee name")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Record Transaction Section
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Record Transaction")
        
        with st.form("transaction_form"):
            if st.session_state.employees:
                employee_options = {emp['name']: emp['id'] for emp in st.session_state.employees}
                selected_emp = st.selectbox("Employee", options=list(employee_options.keys()))
                transaction_type = st.selectbox("Transaction Type", ["Expense (Debit)", "Payment (Credit)"])
                amount = st.number_input("Amount (PKR)", min_value=0.01, step=100.0)
                description = st.text_input("Description")
                transaction_date = st.date_input("Date", value=date.today())
                
                if st.form_submit_button("Record Transaction", use_container_width=True):
                    if description.strip():
                        emp_id = employee_options[selected_emp]
                        txn_type = "expense" if "Expense" in transaction_type else "payment"
                        add_transaction(emp_id, txn_type, amount, description.strip(), transaction_date)
                        st.success("Transaction recorded successfully!")
                        st.rerun()
                    else:
                        st.error("Please enter a description")
            else:
                st.info("No employees available. Please add an employee first.")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Data Upload Section
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Upload Employee Data")
        
        uploaded_file = st.file_uploader("Choose CSV file", type="csv", 
                                        help="Upload CSV with columns: employee_name, transaction_type, amount, description, date")
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                errors, validated_df = validate_employee_data(df)
                
                if errors:
                    st.session_state.upload_errors = errors
                    st.session_state.uploaded_data = validated_df
                    st.error("Data validation failed! Please fix the errors below:")
                    for error in errors:
                        st.error(f"• {error}")
                else:
                    st.session_state.upload_errors = []
                    st.session_state.uploaded_data = validated_df
                    st.success("Data validation successful! Ready to import.")
                    
                    if st.button("Import Validated Data", use_container_width=True):
                        # Import validated data
                        for _, row in validated_df.iterrows():
                            # Find or create employee
                            employee = next((e for e in st.session_state.employees if e['name'] == row['employee_name']), None)
                            if not employee:
                                employee_id = f"emp_{len(st.session_state.employees) + 1}"
                                employee = {
                                    'id': employee_id,
                                    'name': row['employee_name'],
                                    'initial_balance': 0
                                }
                                st.session_state.employees.append(employee)
                            else:
                                employee_id = employee['id']
                            
                            # Add transaction
                            transaction_id = f"txn_{len(st.session_state.transactions) + 1}"
                            transaction = {
                                'id': transaction_id,
                                'employee_id': employee_id,
                                'type': row['transaction_type'],
                                'amount': float(row['amount']),
                                'description': row['description'],
                                'date': row['date'].date() if isinstance(row['date'], pd.Timestamp) else row['date']
                            }
                            st.session_state.transactions.append(transaction)
                        
                        st.success("Data imported successfully!")
                        st.session_state.uploaded_data = None
                        st.rerun()
                        
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
        
        # Show preview of uploaded data if available
        if st.session_state.uploaded_data is not None and not st.session_state.upload_errors:
            st.subheader("Data Preview")
            st.dataframe(st.session_state.uploaded_data.head(), use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Employee Ledger Section
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Employee Ledger")
        
        if st.session_state.employees:
            ledger = get_employee_ledger()
            
            # Search functionality
            search_term = st.text_input("Search employee", placeholder="Type to search...")
            
            if search_term:
                ledger = [emp for emp in ledger if search_term.lower() in emp['name'].lower()]
            
            # Display ledger
            if ledger:
                ledger_df = pd.DataFrame(ledger)
                
                # Format the display
                display_df = ledger_df.copy()
                display_df['total_expenses'] = display_df['total_expenses'].apply(lambda x: f"PKR {x:.2f}")
                display_df['total_payments'] = display_df['total_payments'].apply(lambda x: f"PKR {x:.2f}")
                display_df['balance_display'] = display_df.apply(
                    lambda x: f"PKR {abs(x['balance']):.2f} {'(Due)' if x['balance'] > 0 else '(Advance)'}", 
                    axis=1
                )
                
                # Create a styled dataframe
                for idx, row in ledger_df.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
                    
                    with col1:
                        st.write(f"**{row['name']}**")
                    
                    with col2:
                        st.write(f"PKR {row['total_expenses']:.2f}")
                    
                    with col3:
                        st.write(f"PKR {row['total_payments']:.2f}")
                    
                    with col4:
                        balance_class = "negative-balance" if row['balance'] > 0 else "positive-balance"
                        balance_text = f"PKR {abs(row['balance']):.2f} {'(Due)' if row['balance'] > 0 else '(Advance)'}"
                        st.markdown(f'<span class="{balance_class}">{balance_text}</span>', unsafe_allow_html=True)
                    
                    with col5:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("📊", key=f"view_{row['id']}", help="View Ledger"):
                                st.session_state.selected_employee = row['id']
                        with col_b:
                            if st.button("🗑️", key=f"delete_{row['id']}", help="Delete Employee"):
                                st.session_state.employees = [e for e in st.session_state.employees if e['id'] != row['id']]
                                st.session_state.transactions = [t for t in st.session_state.transactions if t['employee_id'] != row['id']]
                                st.success("Employee deleted successfully!")
                                st.rerun()
                    
                    st.divider()
                
                # Export functionality
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Export to CSV", use_container_width=True):
                        csv = ledger_df.to_csv(index=False)
                        st.download_button(
                            label="Download CSV",
                            data=csv,
                            file_name="employee_ledger.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                
                with col2:
                    if st.button("Reset All Data", use_container_width=True):
                        st.session_state.employees = []
                        st.session_state.transactions = []
                        st.success("All data reset successfully!")
                        st.rerun()
            else:
                st.info("No employees match your search criteria.")
        else:
            st.info("No employees added yet. Use the form to add employees or upload data.")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Transaction Management Section
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.subheader("Transaction Management")
        
        if st.session_state.transactions:
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                transaction_search = st.text_input("Search transactions", placeholder="Search by description or employee...")
            with col2:
                transaction_filter = st.selectbox("Filter by type", ["All Types", "Expenses", "Payments"])
            
            # Filter transactions
            filtered_transactions = st.session_state.transactions.copy()
            
            if transaction_search:
                filtered_transactions = [
                    t for t in filtered_transactions 
                    if transaction_search.lower() in t['description'].lower() or
                    any(transaction_search.lower() in e['name'].lower() 
                        for e in st.session_state.employees if e['id'] == t['employee_id'])
                ]
            
            if transaction_filter != "All Types":
                filter_type = "expense" if transaction_filter == "Expenses" else "payment"
                filtered_transactions = [t for t in filtered_transactions if t['type'] == filter_type]
            
            # Display transactions
            if filtered_transactions:
                for transaction in filtered_transactions:
                    employee = next((e for e in st.session_state.employees if e['id'] == transaction['employee_id']), None)
                    if employee:
                        col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1.5, 3, 2, 1])
                        
                        with col1:
                            st.write(transaction['date'].strftime('%Y-%m-%d') if isinstance(transaction['date'], date) else str(transaction['date']))
                        
                        with col2:
                            st.write(employee['name'])
                        
                        with col3:
                            type_color = "red" if transaction['type'] == 'expense' else "green"
                            type_text = "Expense" if transaction['type'] == 'expense' else "Payment"
                            st.markdown(f'<span style="color: {type_color}">{type_text}</span>', unsafe_allow_html=True)
                        
                        with col4:
                            st.write(transaction['description'])
                        
                        with col5:
                            amount_color = "red" if transaction['type'] == 'expense' else "green"
                            st.markdown(f'<span style="color: {amount_color}">PKR {transaction["amount"]:.2f}</span>', unsafe_allow_html=True)
                        
                        with col6:
                            if st.button("🗑️", key=f"del_txn_{transaction['id']}", help="Delete Transaction"):
                                st.session_state.transactions = [t for t in st.session_state.transactions if t['id'] != transaction['id']]
                                st.success("Transaction deleted successfully!")
                                st.rerun()
                        
                        st.divider()
            else:
                st.info("No transactions match your search criteria.")
        else:
            st.info("No transactions recorded yet.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Employee Detail Modal (using expander)
    if 'selected_employee' in st.session_state:
        employee = next((e for e in st.session_state.employees if e['id'] == st.session_state.selected_employee), None)
        if employee:
            with st.expander(f"Employee Details - {employee['name']}", expanded=True):
                # Calculate employee metrics
                employee_transactions = [t for t in st.session_state.transactions if t['employee_id'] == employee['id']]
                total_expenses = sum(t['amount'] for t in employee_transactions if t['type'] == 'expense')
                total_payments = sum(t['amount'] for t in employee_transactions if t['type'] == 'payment')
                balance = total_expenses - total_payments
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Expenses", f"PKR {total_expenses:.2f}")
                with col2:
                    st.metric("Total Payments", f"PKR {total_payments:.2f}")
                with col3:
                    balance_label = "Balance Due" if balance > 0 else "Advance Balance"
                    st.metric(balance_label, f"PKR {abs(balance):.2f}")
                
                # Date range for PDF export
                st.subheader("Export to PDF")
                col1, col2, col3 = st.columns([2, 2, 1])
                with col1:
                    start_date = st.date_input("Start Date", value=None, key="pdf_start")
                with col2:
                    end_date = st.date_input("End Date", value=None, key="pdf_end")
                with col3:
                    if st.button("Generate PDF", use_container_width=True):
                        pdf = generate_pdf_report(employee['id'], start_date, end_date)
                        if pdf:
                            pdf_output = pdf.output(dest='S').encode('latin1')
                            st.download_button(
                                label="Download PDF",
                                data=pdf_output,
                                file_name=f"ledger_{employee['name'].replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True
                            )
                
                # Transaction history
                st.subheader("Transaction History")
                if employee_transactions:
                    # Sort by date
                    employee_transactions.sort(key=lambda x: x['date'])
                    
                    # Calculate running balance
                    running_balance = 0
                    for transaction in employee_transactions:
                        col1, col2, col3, col4, col5 = st.columns([2, 1.5, 3, 2, 2])
                        
                        with col1:
                            st.write(transaction['date'].strftime('%Y-%m-%d') if isinstance(transaction['date'], date) else str(transaction['date']))
                        
                        with col2:
                            type_color = "red" if transaction['type'] == 'expense' else "green"
                            type_text = "Expense" if transaction['type'] == 'expense' else "Payment"
                            st.markdown(f'<span style="color: {type_color}">{type_text}</span>', unsafe_allow_html=True)
                        
                        with col3:
                            st.write(transaction['description'])
                        
                        with col4:
                            amount_color = "red" if transaction['type'] == 'expense' else "green"
                            st.markdown(f'<span style="color: {amount_color}">PKR {transaction["amount"]:.2f}</span>', unsafe_allow_html=True)
                        
                        with col5:
                            # Update running balance
                            if transaction['type'] == 'expense':
                                running_balance += transaction['amount']
                            else:
                                running_balance -= transaction['amount']
                            
                            balance_class = "negative-balance" if running_balance > 0 else "positive-balance"
                            balance_text = f"PKR {abs(running_balance):.2f} {'(Due)' if running_balance > 0 else '(Advance)'}"
                            st.markdown(f'<span class="{balance_class}">{balance_text}</span>', unsafe_allow_html=True)
                        
                        st.divider()
                else:
                    st.info("No transactions recorded for this employee.")

if __name__ == "__main__":
    main()
