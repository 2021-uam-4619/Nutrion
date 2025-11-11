import streamlit as st
import pandas as pd
from fpdf import FPDF
import base64
from io import BytesIO
from datetime import datetime

# --- Constants and Configuration ---
COMPANY_NAME = "Nutrion"
# Placeholder logo - replace with your actual logo URL
COMPANY_LOGO = "https://placehold.co/200x100/E8F5E9/4CAF50?text=Nutrion"
COMPANY_ADDRESS = "123 Wellness Avenue, Health-Town, HT 45678"

# Define the exact columns your system requires for the ledger
REQUIRED_COLUMNS = [
    'EmployeeID',
    'FullName',
    'Date',
    'Description',
    'Debit',  # Money paid to employee (e.g., salary)
    'Credit'  # Money from employee (e.g., advance repayment)
]

# --- PDF Generation Class ---
class LedgerPDF(FPDF):
    """
    Custom FPDF class to create a professional ledger PDF
    with a consistent header and footer.
    """
    def header(self):
        # 1. Logo
        # We use a try-except block for web images in case they fail to load
        try:
            # Note: FPDF requires explicit image download for web URLs
            # For simplicity, we'll use a local placeholder if URL fails
            # In a real app, you'd cache this download
            self.image(COMPANY_LOGO, 10, 8, 33, title=f"{COMPANY_NAME} Logo")
        except Exception as e:
            st.warning(f"Could not load company logo from URL: {e}")
            # Fallback to text
            self.set_font('Helvetica', 'B', 16)
            self.cell(0, 10, COMPANY_NAME, 0, 1, 'L')
            
        # 2. Company Name & Address
        self.set_font('Helvetica', 'B', 18)
        self.cell(0, 10, f"{COMPANY_NAME} - Employee Ledger", 0, 1, 'C')
        self.set_font('Helvetica', '', 10)
        self.cell(0, 5, COMPANY_ADDRESS, 0, 1, 'C')
        # 3. Line break
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        # 1. System Generated Text
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(0, 10, f"This is system generated not required any signature. (Generated on: {timestamp})", 0, 0, 'L')
        # 2. Page Number
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", 0, 0, 'R')

    def employee_ledger_page(self, employee_id, full_name, data):
        """Adds a full page for a single employee's ledger."""
        self.add_page()
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, f"Ledger for: {full_name} (ID: {employee_id})", 0, 1, 'L')
        self.ln(5)

        # Calculate running balance
        data = data.sort_values('Date')
        data['Balance'] = (data['Debit'] - data['Credit']).cumsum()
        
        # Table Header
        self.set_font('Helvetica', 'B', 10)
        self.cell(30, 10, 'Date', 1, 0, 'C')
        self.cell(85, 10, 'Description', 1, 0, 'C')
        self.cell(25, 10, 'Debit (+)', 1, 0, 'C')
        self.cell(25, 10, 'Credit (-)', 1, 0, 'C')
        self.cell(25, 10, 'Balance', 1, 1, 'C')

        # Table Rows
        self.set_font('Helvetica', '', 9)
        for _, row in data.iterrows():
            self.cell(30, 8, str(row['Date']), 1)
            self.cell(85, 8, str(row['Description']), 1)
            self.cell(25, 8, f"{row['Debit']:.2f}", 1, 0, 'R')
            self.cell(25, 8, f"{row['Credit']:.2f}", 1, 0, 'R')
            self.cell(25, 8, f"{row['Balance']:.2f}", 1, 1, 'R')
            
        # Employee Summary
        self.ln(10)
        self.set_font('Helvetica', 'B', 12)
        total_debit = data['Debit'].sum()
        total_credit = data['Credit'].sum()
        final_balance = data['Balance'].iloc[-1]
        
        self.cell(100, 8, "Employee Summary:", 0, 1)
        self.set_font('Helvetica', '', 10)
        self.cell(100, 6, f"Total Debit (Paid to Employee):", 0, 0)
        self.cell(50, 6, f"{total_debit:.2f}", 0, 1, 'R')
        self.cell(100, 6, f"Total Credit (Received from Employee):", 0, 0)
        self.cell(50, 6, f"{total_credit:.2f}", 0, 1, 'R')
        self.set_font('Helvetica', 'B', 10)
        self.cell(100, 6, f"Final Balance:", 0, 0)
        self.cell(50, 6, f"{final_balance:.2f}", 'T', 1, 'R')

    def summary_page(self, df):
        """Adds the final summary page for all employees."""
        self.add_page()
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, "Overall Company Ledger Summary", 0, 1, 'C')
        self.ln(10)
        
        self.set_font('Helvetica', 'B', 12)
        total_employees = df['EmployeeID'].nunique()
        total_debit = df['Debit'].sum()
        total_credit = df['Credit'].sum()
        net_total = total_debit - total_credit
        
        self.cell(100, 8, "Metric", 'B', 0)
        self.cell(50, 8, "Value", 'B', 1, 'R')
        self.ln(5)

        self.set_font('Helvetica', '', 12)
        self.cell(100, 8, "Total Employees Processed:", 0, 0)
        self.cell(50, 8, f"{total_employees}", 0, 1, 'R')
        
        self.cell(100, 8, "Total Debit (All Employees):", 0, 0)
        self.cell(50, 8, f"{total_debit:.2f}", 0, 1, 'R')
        
        self.cell(100, 8, "Total Credit (All Employees):", 0, 0)
        self.cell(50, 8, f"{total_credit:.2f}", 0, 1, 'R')
        self.ln(5)
        
        self.set_font('Helvetica', 'B', 12)
        self.cell(100, 8, "Net Company Payout:", 'T', 0)
        self.cell(50, 8, f"{net_total:.2f}", 'T', 1, 'R')

# --- Helper Functions ---

@st.cache_data
def get_template_csv():
    """Creates an in-memory CSV template for download."""
    template_df = pd.DataFrame(
        columns=REQUIRED_COLUMNS,
        data=[
            ['EMP-001', 'John Doe', '2023-10-01', 'Salary - October', 5000.00, 0.00],
            ['EMP-001', 'John Doe', '2023-10-15', 'Salary Advance', 0.00, 500.00],
            ['EMP-002', 'Jane Smith', '2023-10-01', 'Salary - October', 5500.00, 0.00],
        ]
    )
    # Use BytesIO to create an in-memory file-like object
    towrite = BytesIO()
    template_df.to_csv(towrite, index=False, encoding='utf-8')
    towrite.seek(0) # Rewind to the start of the stream
    return towrite.read()

def validate_data(df):
    """
    Checks the uploaded DataFrame against system requirements.
    Returns a list of error strings. If the list is empty, data is valid.
    """
    errors = []
    
    # 1. Check for missing columns
    uploaded_cols = set(df.columns)
    required_cols_set = set(REQUIRED_COLUMNS)
    
    missing_cols = required_cols_set - uploaded_cols
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return errors # Stop here, as other checks will fail

    # 2. Check for empty rows (all NaN)
    df.dropna(how='all', inplace=True)
    if df.empty:
        errors.append("The uploaded file is empty or contains only empty rows.")
        return errors

    # 3. Row-by-row validation for data types and required fields
    for index, row in df.iterrows():
        row_num = index + 2 # (for 1-based indexing + header)

        # Check for missing but required values
        if pd.isnull(row['EmployeeID']):
            errors.append(f"Row {row_num}: 'EmployeeID' is missing.")
        if pd.isnull(row['FullName']):
            errors.append(f"Row {row_num}: 'FullName' is missing.")

        # Check Date format
        try:
            pd.to_datetime(row['Date'])
        except Exception:
            errors.append(f"Row {row_num}: 'Date' column has an invalid format ('{row['Date']}')")

        # Check Debit/Credit numeric format
        try:
            pd.to_numeric(row['Debit'])
        except Exception:
            errors.append(f"Row {row_num}: 'Debit' column has non-numeric value ('{row['Debit']}')")
            
        try:
            pd.to_numeric(row['Credit'])
        except Exception:
            errors.append(f"Row {row_num}: 'Credit' column has non-numeric value ('{row['Credit']}')")

    # Fill NaNs in Debit/Credit with 0 after checks
    df['Debit'] = pd.to_numeric(df['Debit'], errors='coerce').fillna(0)
    df['Credit'] = pd.to_numeric(df['Credit'], errors='coerce').fillna(0)
    
    return errors

def create_pdf(df):
    """
    Generates the full PDF from the validated DataFrame.
    """
    pdf = LedgerPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.alias_nb_pages() # Allows for total page count '{nb}'

    # Group by employee and create a page for each
    grouped = df.groupby('EmployeeID')
    
    for employee_id, data in grouped:
        # Get the full name (assuming it's consistent for the ID)
        full_name = data['FullName'].iloc[0]
        pdf.employee_ledger_page(employee_id, full_name, data)
        
    # Add the final summary page
    pdf.summary_page(df)
    
    # Return PDF as bytes
    return pdf.output(dest='S').encode('latin-1')


# --- Streamlit App Main Function ---
def main():
    st.set_page_config(page_title=f"{COMPANY_NAME} Ledger System", layout="wide")
    
    # --- Initialize Session State ---
    # Hum validated data aur pdf ko state mein save karenge taaki tabs switch karne par delete na ho
    if 'validated_df' not in st.session_state:
        st.session_state.validated_df = None
    if 'pdf_bytes' not in st.session_state:
        st.session_state.pdf_bytes = None
        
    # --- Header & Branding ---
    col1, col2 = st.columns([1, 4])
    with col1:
        st.image(COMPANY_LOGO, width=150)
    with col2:
        st.title(f"{COMPANY_NAME} Employee Ledger System")
        st.write(COMPANY_ADDRESS)
    
    st.markdown("---")

    # --- Create Tabs ---
    tab1, tab2, tab3 = st.tabs(["Step 1: Download Template", "Step 2: Upload & Validate", "Step 3: Generate Report"])

    # --- Tab 1: Download Template ---
    with tab1:
        st.header("Step 1: Download the Template")
        st.markdown("Download the official CSV template. Please fill in your employee data using this exact format.")
        
        template_data = get_template_csv()
        st.download_button(
            label="Download Template (template_ledger.csv)",
            data=template_data,
            file_name="employee_ledger_template.csv",
            mime="text/csv"
        )
        st.info("Template bharne ke baad, 'Step 2: Upload & Validate' tab par jayen.")

    # --- Tab 2: Upload Data ---
    with tab2:
        st.header("Step 2: Upload Your Filled Template")
        uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
        
        # Reset state if new file is uploaded
        if uploaded_file:
            st.session_state.validated_df = None
            st.session_state.pdf_bytes = None
            
            try:
                df = pd.read_csv(uploaded_file)
                
                # --- Validation ---
                validation_errors = validate_data(df)
                
                if validation_errors:
                    st.error("Upload Failed! Aapki file mein errors hain. Please unhe theek karke dobara upload karein.")
                    with st.expander("Click to see all errors"):
                        for error in validation_errors:
                            st.write(f"- {error}")
                else:
                    st.success("File Uploaded and Validated Successfully!")
                    
                    # Clean data (post-validation)
                    df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%Y-%m-%d')
                    df['Debit'] = pd.to_numeric(df['Debit']).fillna(0)
                    df['Credit'] = pd.to_numeric(df['Credit']).fillna(0)
                    
                    st.subheader("Validated Employee Ledger Data")
                    st.dataframe(df)
                    
                    # --- Pre-generate PDF and store in session state ---
                    with st.spinner("Generating PDF... This may take a moment."):
                        pdf_bytes = create_pdf(df)
                        st.session_state.validated_df = df
                        st.session_state.pdf_bytes = pdf_bytes
                    
                    st.success("PDF report generate ho gaya hai. Download karne ke liye 'Step 3: Generate Report' tab par jayen.")
            
            except Exception as e:
                st.error(f"An unexpected error occurred while processing the file: {e}")
                st.write("Please ensure your file is a standard CSV.")

    # --- Tab 3: Download PDF ---
    with tab3:
        st.header("Step 3: Download PDF Report")
        
        if st.session_state.pdf_bytes is not None:
            st.markdown("Aapka PDF report tayyar hai. Download karne ke liye neeche diye gaye button par click karein.")
            
            st.download_button(
                label="Download All Ledgers (PDF)",
                data=st.session_state.pdf_bytes,
                file_name=f"{COMPANY_NAME}_Employee_Ledgers_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )
        else:
            st.info("PDF report generate karne ke liye, pehle 'Step 2: Upload & Validate' tab mein CSV file upload karein.")

if __name__ == "__main__":
    main()
