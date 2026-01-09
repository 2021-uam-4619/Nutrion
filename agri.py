import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import time
import io

# Try importing FPDF for PDF generation, handle if not installed
try:
    from fpdf import FPDF
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Farm Manager Pro", layout="wide", page_icon="🚜")

# --- DATABASE MANAGEMENT ---
DB_FILE = "farm_data.db"

def init_db():
    """Initialize the SQLite database with necessary tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # Main transaction table
    c.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            module TEXT,            -- Livestock, Crop, Water, Operations
            trans_type TEXT,        -- Expense, Income, Bill, Payment
            category TEXT,          -- Cow, Wheat, Tubewell, Fuel, etc.
            subcategory TEXT,       -- Wanda, Seed, Salary, etc.
            description TEXT,
            amount REAL,
            party_name TEXT,        -- Who paid (Expense) or Who owes (Farmer)
            qty REAL,               -- For hours or units
            rate REAL,              -- For tubewell rate
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def run_query(query, params=(), fetch=False):
    """Helper to run SQL queries."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute(query, params)
        if fetch:
            data = c.fetchall()
            columns = [description[0] for description in c.description]
            df = pd.DataFrame(data, columns=columns)
            conn.close()
            return df
        else:
            conn.commit()
            conn.close()
            return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        conn.close()
        return False

# Initialize DB on load
init_db()

# --- PDF GENERATION HELPERS ---
class FarmPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, '🚜 Farm Management System', 0, 1, 'C')
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, f'Generated on: {date.today()}', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_bill_pdf(farmer, date_val, start, end, duration, rate, total):
    if not PDF_AVAILABLE: return None
    pdf = FarmPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, "WATER BILL / INVOICE", 1, 1, 'C', fill=True)
    pdf.ln(5)
    
    pdf.cell(50, 10, "Farmer Name:", 0, 0)
    pdf.cell(0, 10, farmer, 0, 1)
    
    pdf.cell(50, 10, "Date:", 0, 0)
    pdf.cell(0, 10, str(date_val), 0, 1)
    
    pdf.ln(5)
    pdf.cell(50, 10, "Usage Details:", 0, 1, 'B')
    pdf.cell(50, 10, f"Start Time: {start}", 0, 1)
    pdf.cell(50, 10, f"End Time: {end}", 0, 1)
    pdf.cell(50, 10, f"Total Hours: {duration:.2f}", 0, 1)
    pdf.cell(50, 10, f"Rate per Hour: {rate}", 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(50, 15, "Total Payable:", 0, 0)
    pdf.cell(0, 15, f"{total:,.2f} PKR", 0, 1)
    
    return pdf.output(dest='S').encode('latin-1')

def generate_ledger_pdf(df, title="Account Ledger"):
    if not PDF_AVAILABLE: return None
    pdf = FarmPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=10)
    
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.ln(5)
    
    # Table Header
    cols = ["Date", "Description", "Debit", "Credit"]
    col_widths = [30, 90, 35, 35]
    
    pdf.set_font("Arial", 'B', 10)
    for i, col in enumerate(cols):
        pdf.cell(col_widths[i], 10, col, 1, 0, 'C')
    pdf.ln()
    
    # Table Rows
    pdf.set_font("Arial", size=9)
    total_debit = 0
    total_credit = 0
    
    for _, row in df.iterrows():
        debit = row.get("Debit (They Owe Us/Paid Us Back)", 0)
        credit = row.get("Credit (We Owe Them/They Paid Us)", 0)
        total_debit += debit
        total_credit += credit
        
        pdf.cell(col_widths[0], 10, str(row["Date"]), 1)
        pdf.cell(col_widths[1], 10, str(row["Details"])[:45], 1) # Truncate long desc
        pdf.cell(col_widths[2], 10, f"{debit:,.0f}", 1, 0, 'R')
        pdf.cell(col_widths[3], 10, f"{credit:,.0f}", 1, 0, 'R')
        pdf.ln()

    # Total Row
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(col_widths[0] + col_widths[1], 10, "Total", 1, 0, 'R')
    pdf.cell(col_widths[2], 10, f"{total_debit:,.0f}", 1, 0, 'R')
    pdf.cell(col_widths[3], 10, f"{total_credit:,.0f}", 1, 0, 'R')
    
    return pdf.output(dest='S').encode('latin-1')

# --- SIDEBAR & STYLING ---
st.markdown("""
<style>
    .metric-container {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 45px; white-space: pre-wrap; background-color: #f0f2f6; border-radius: 5px 5px 0 0; }
    .stTabs [aria-selected="true"] { background-color: #ffffff; border-top: 3px solid #0068c9; }
    h3 { color: #333; }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🚜 Farm Manager Pro")
if not PDF_AVAILABLE:
    st.sidebar.warning("⚠️ `fpdf` library not found. PDF features disabled.\nRun `pip install fpdf` to enable.")

# --- HELPER FUNCTIONS ---
def save_transaction(date_val, module, trans_type, category, subcategory, desc, amount, party, qty=0, rate=0):
    query = '''
    INSERT INTO transactions (date, module, trans_type, category, subcategory, description, amount, party_name, qty, rate)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    run_query(query, (date_val, module, trans_type, category, subcategory, desc, amount, party, qty, rate))
    st.toast(f"✅ Saved: {subcategory} - {amount}")
    time.sleep(0.5)
    st.rerun()

def delete_transaction(tid):
    run_query("DELETE FROM transactions WHERE id = ?", (tid,))
    st.toast("🗑️ Record Deleted")
    time.sleep(0.5)
    st.rerun()

# --- TABS ---
tab_dash, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏠 Dashboard",
    "🐄 Livestock", 
    "🌾 Crops", 
    "💧 Water/Tubewell", 
    "⚙️ Operations", 
    "📊 Reports"
])

# ==============================================================================
# TAB 0: DASHBOARD
# ==============================================================================
with tab_dash:
    st.header("Farm Overview")
    
    # Global Metrics
    df_all = run_query("SELECT * FROM transactions", fetch=True)
    if not df_all.empty:
        total_income = df_all[df_all['trans_type'].isin(['Income', 'Bill'])]['amount'].sum()
        total_expense = df_all[df_all['trans_type'] == 'Expense']['amount'].sum()
        net_profit = total_income - total_expense
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Income", f"{total_income:,.0f} PKR", delta="All Time")
        c2.metric("Total Expenses", f"{total_expense:,.0f} PKR", delta="All Time", delta_color="inverse")
        c3.metric("Net Profit", f"{net_profit:,.0f} PKR", delta_color="normal" if net_profit >= 0 else "inverse")
        
        st.divider()
        
        # Quick Recent Activity
        st.subheader("📝 Recent Activity")
        st.dataframe(
            df_all[['date', 'module', 'trans_type', 'description', 'amount', 'party_name']].sort_values(by='date', ascending=False).head(5),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Welcome! Start by adding records in the tabs above.")

# ==============================================================================
# TAB 1: LIVESTOCK
# ==============================================================================
with tab1:
    st.header("Livestock Management")
    
    # 1. Metrics
    df_ls = run_query("SELECT * FROM transactions WHERE module='Livestock'", fetch=True)
    ls_exp = df_ls[df_ls['trans_type'] == 'Expense']['amount'].sum() if not df_ls.empty else 0
    ls_inc = df_ls[df_ls['trans_type'] == 'Income']['amount'].sum() if not df_ls.empty else 0
    
    m1, m2 = st.columns(2)
    m1.metric("Total Livestock Expense", f"{ls_exp:,.0f}")
    m2.metric("Total Livestock Income", f"{ls_inc:,.0f}")
    
    st.divider()

    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        with st.expander("➕ Add New Entry", expanded=True):
            with st.form("livestock_form"):
                date_ls = st.date_input("Date", date.today())
                ls_type = st.selectbox("Animal Type", ["Cow", "Goat", "Buffalo", "Other"])
                ls_action = st.selectbox("Transaction Type", ["Expense", "Income"])
                
                if ls_action == "Expense":
                    ls_item = st.selectbox("Item", ["Wanda", "Chokar", "Khal", "Tori", "Khas", "Medicine", "Other"])
                    ls_party = st.text_input("Paid By", value="Cash", help="Enter name if credit, else Cash")
                else:
                    ls_item = st.selectbox("Source", ["Milk Sale", "Animal Sale", "Manure Sale"])
                    ls_party = "Cash" 
                    
                ls_desc = st.text_input("Description", placeholder="e.g. 5 Bags")
                ls_amount = st.number_input("Amount", min_value=0.0, step=100.0)
                
                if st.form_submit_button("Save Entry", type="primary"):
                    save_transaction(date_ls, "Livestock", ls_action, ls_type, ls_item, ls_desc, ls_amount, ls_party)

    with col2:
        st.subheader("History")
        if not df_ls.empty:
            df_ls_show = df_ls.sort_values(by='date', ascending=False)
            st.dataframe(df_ls_show[['date', 'trans_type', 'subcategory', 'description', 'amount', 'party_name']], use_container_width=True, hide_index=True)
            
            # Simple delete
            with st.expander("🗑️ Delete Record"):
                del_id = st.selectbox("Select Record to Delete", df_ls_show['id'].tolist(), format_func=lambda x: f"ID {x}")
                if st.button("Delete Selected", key="del_ls"):
                    delete_transaction(del_id)
        else:
            st.info("No records yet.")

# ==============================================================================
# TAB 2: CROPS
# ==============================================================================
with tab2:
    st.header("Crop Management")
    
    # Metrics
    df_cr = run_query("SELECT * FROM transactions WHERE module='Crop'", fetch=True)
    cr_exp = df_cr[df_cr['trans_type'] == 'Expense']['amount'].sum() if not df_cr.empty else 0
    
    st.metric("Total Crop Investment", f"{cr_exp:,.0f}")
    st.divider()

    col1, col2 = st.columns([1, 1.5])
    with col1:
        with st.expander("➕ Add Crop Transaction", expanded=True):
            with st.form("crop_form"):
                date_cr = st.date_input("Date", date.today())
                cr_crop = st.text_input("Crop Name", value="Wheat")
                cr_action = st.selectbox("Type", ["Expense", "Income"])
                
                if cr_action == "Expense":
                    cr_item = st.selectbox("Category", ["Khad (Fertilizer)", "Spray", "Seed", "Diesel", "Labor", "Other"])
                    cr_party = st.text_input("Paid By", value="Cash", help="Person name if credit")
                else:
                    cr_item = st.selectbox("Source", ["Crop Sale", "Straw Sale"])
                    cr_party = st.text_input("Sold To", value="Cash")
                    
                cr_desc = st.text_input("Details", placeholder="Qty / Remarks")
                cr_amount = st.number_input("Amount", min_value=0.0, step=100.0)

                if st.form_submit_button("Save Entry", type="primary"):
                    save_transaction(date_cr, "Crop", cr_action, cr_crop, cr_item, cr_desc, cr_amount, cr_party)

    with col2:
        st.subheader("Crop History")
        if not df_cr.empty:
            df_cr_show = df_cr.sort_values(by='date', ascending=False)
            st.dataframe(df_cr_show[['date', 'trans_type', 'category', 'subcategory', 'description', 'amount']], use_container_width=True, hide_index=True)
            
             # Simple delete
            with st.expander("🗑️ Delete Record"):
                del_id_cr = st.selectbox("Select Record", df_cr_show['id'].tolist(), format_func=lambda x: f"ID {x}")
                if st.button("Delete Selected", key="del_cr"):
                    delete_transaction(del_id_cr)

# ==============================================================================
# TAB 3: WATER / TUBEWELL
# ==============================================================================
with tab3:
    st.header("Tubewell Billing")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        with st.container(border=True):
            st.subheader("⏱️ Calculate Bill")
            with st.form("water_form"):
                date_wt = st.date_input("Date", date.today())
                farmer_name = st.text_input("Farmer Name")
                
                c1, c2 = st.columns(2)
                t_start = c1.time_input("Start Time", value=datetime.strptime("08:00", "%H:%M").time())
                t_end = c2.time_input("End Time", value=datetime.strptime("10:00", "%H:%M").time())
                rate_per_hr = st.number_input("Rate/Hour", value=1500.0)
                
                # Calculation
                t1 = timedelta(hours=t_start.hour, minutes=t_start.minute)
                t2 = timedelta(hours=t_end.hour, minutes=t_end.minute)
                duration = (t2 - t1).total_seconds() / 3600
                if duration < 0: duration += 24
                est_bill = duration * rate_per_hr
                
                st.info(f"⏳ **{duration:.2f} hrs** | 💰 **{est_bill:,.0f} PKR**")
                
                submitted_wt = st.form_submit_button("Generate Bill", type="primary")
                if submitted_wt and farmer_name:
                    desc = f"{t_start} to {t_end}"
                    save_transaction(date_wt, "Water", "Bill", "Tubewell", "Water Usage", desc, est_bill, farmer_name, qty=duration, rate=rate_per_hr)
            
            # PDF Download for LAST Transaction if it was a bill
            if PDF_AVAILABLE and submitted_wt and farmer_name:
                pdf_bytes = generate_bill_pdf(farmer_name, date_wt, t_start, t_end, duration, rate_per_hr, est_bill)
                if pdf_bytes:
                    st.download_button(
                        label="📄 Download PDF Bill",
                        data=pdf_bytes,
                        file_name=f"Bill_{farmer_name}_{date_wt}.pdf",
                        mime="application/pdf"
                    )

    with col2:
        with st.container(border=True):
            st.subheader("💵 Receive Payment")
            with st.form("water_payment"):
                pay_date = st.date_input("Date", date.today())
                pay_farmer = st.text_input("Farmer Name (Payer)")
                pay_amount = st.number_input("Amount Received", min_value=1.0)
                pay_desc = st.text_input("Note", "Cash Received")
                
                if st.form_submit_button("Record Payment", type="primary"):
                    save_transaction(pay_date, "Water", "Payment", "Tubewell", "Recovery", pay_desc, pay_amount, pay_farmer)

    st.subheader("Recent Water Log")
    df_wt = run_query("SELECT * FROM transactions WHERE module='Water' ORDER BY date DESC", fetch=True)
    if not df_wt.empty:
        st.dataframe(df_wt[['date', 'party_name', 'trans_type', 'amount', 'qty', 'description']], use_container_width=True)

# ==============================================================================
# TAB 4: OPERATIONAL EXPENSES
# ==============================================================================
with tab4:
    st.header("Operations & Salaries")
    
    col1, col2 = st.columns([1, 1.5])
    
    with col1:
        with st.expander("➕ Add Expense / Salary", expanded=True):
            with st.form("ops_form"):
                date_op = st.date_input("Date", date.today())
                op_cat = st.selectbox("Category", ["Salaries", "Fuel", "Machinery Purchase", "Maintenance", "Misc"])
                op_desc = st.text_input("Description", placeholder="e.g. Salary for Month June")
                op_amount = st.number_input("Amount", min_value=0.0)
                op_manager = st.text_input("Managed/Paid By", value="Cash", help="Who paid this? 'Cash' or Employee Name")
                
                if st.form_submit_button("Record Expense", type="primary"):
                    save_transaction(date_op, "Operations", "Expense", "General", op_cat, op_desc, op_amount, op_manager)

    with col2:
        with st.container(border=True):
            st.subheader("Settlement / Reimbursement")
            st.caption("Use this when you pay back an employee or supplier.")
            with st.form("settle_form"):
                c1, c2 = st.columns(2)
                set_date = c1.date_input("Date", date.today())
                set_person = c2.text_input("Person Name")
                set_amount = st.number_input("Amount Paid", min_value=1.0)
                set_note = st.text_input("Note", "Reimbursement / Salary Clearance")
                
                if st.form_submit_button("Record Payment"):
                    save_transaction(set_date, "Operations", "Payment", "General", "Reimbursement", set_note, set_amount, set_person)

    st.subheader("Operations Log")
    df_op = run_query("SELECT * FROM transactions WHERE module='Operations' ORDER BY date DESC", fetch=True)
    if not df_op.empty:
        st.dataframe(df_op[['date', 'subcategory', 'description', 'amount', 'party_name']], use_container_width=True)

# ==============================================================================
# TAB 5: REPORTS
# ==============================================================================
with tab5:
    st.header("📊 Financial Reports & Ledger")
    
    df = run_query("SELECT * FROM transactions", fetch=True)
    
    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        
        # --- FILTERS ---
        with st.container(border=True):
            st.subheader("🔍 Filter Data")
            colf1, colf2, colf3 = st.columns(3)
            start_date = colf1.date_input("Start Date", date.today().replace(day=1))
            end_date = colf2.date_input("End Date", date.today())
            filter_party = colf3.multiselect("Filter by Person", options=df['party_name'].unique())

        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        if filter_party:
            mask = mask & (df['party_name'].isin(filter_party))
        
        filtered_df = df.loc[mask].copy()
        
        # --- LEDGER PROCESSING ---
        ledger_data = []
        for index, row in filtered_df.iterrows():
            debit, credit = 0, 0
            party = row['party_name']
            
            # Logic: 
            # If Water Bill -> Debit Farmer. If Water Payment -> Credit Farmer.
            # If Expense (Paid by Person) -> Credit Person. If Reimbursed -> Debit Person.
            if row['module'] == 'Water':
                if row['trans_type'] == 'Bill': debit = row['amount']
                elif row['trans_type'] == 'Payment': credit = row['amount']
            elif row['module'] in ['Operations', 'Livestock', 'Crop']:
                if row['trans_type'] == 'Expense' and party.lower() != 'cash': credit = row['amount']
                elif row['trans_type'] == 'Payment': debit = row['amount']
                elif row['trans_type'] == 'Income' and party.lower() != 'cash': debit = row['amount']
            
            if party.lower() != 'cash':
                ledger_data.append({
                    "Date": row['date'].date(),
                    "Name": party,
                    "Module": row['module'],
                    "Details": f"{row['subcategory']} - {row['description']}",
                    "Debit (They Owe Us/Paid Us Back)": debit,
                    "Credit (We Owe Them/They Paid Us)": credit
                })

        ledger_df = pd.DataFrame(ledger_data)
        
        # --- REPORT VIEW ---
        tab_r1, tab_r2 = st.tabs(["📜 Detailed Ledger", "💰 Balances & PDF"])
        
        with tab_r1:
            st.dataframe(ledger_df, use_container_width=True)
        
        with tab_r2:
            if not ledger_df.empty:
                # Balance Calculation
                balance_df = ledger_df.groupby("Name")[["Debit (They Owe Us/Paid Us Back)", "Credit (We Owe Them/They Paid Us)"]].sum().reset_index()
                balance_df["Net Balance"] = balance_df["Debit (They Owe Us/Paid Us Back)"] - balance_df["Credit (We Owe Them/They Paid Us)"]
                balance_df["Status"] = balance_df["Net Balance"].apply(lambda x: "Collect" if x > 0 else ("Pay" if x < 0 else "Settled"))
                
                st.dataframe(balance_df, use_container_width=True)
                
                # PDF DOWNLOAD FOR LEDGER
                if PDF_AVAILABLE:
                    st.divider()
                    st.subheader("Download Report")
                    
                    # Generate PDF for the filtered view
                    if st.button("Generate PDF Ledger for Selected Period"):
                        pdf_bytes = generate_ledger_pdf(ledger_df, title=f"Ledger: {start_date} to {end_date}")
                        if pdf_bytes:
                            st.download_button(
                                label="⬇️ Download PDF",
                                data=pdf_bytes,
                                file_name=f"Ledger_{start_date}_{end_date}.pdf",
                                mime="application/pdf"
                            )
            else:
                st.info("No credit transactions found for this period.")
    else:
        st.warning("No data found.")
