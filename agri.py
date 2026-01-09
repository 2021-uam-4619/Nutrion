import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import time

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Farm Manager & Accounting", layout="wide", page_icon="🚜")

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

# --- SIDEBAR & STYLING ---
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        margin: 5px;
        border-left: 5px solid #2e7bcf;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #f9f9f9; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #e6f3ff; border-bottom: 3px solid #0068c9; }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🚜 Farm Manager")
st.sidebar.info("Double-entry accounting system with automated ledgers.")

# --- HELPER FUNCTIONS ---
def save_transaction(date_val, module, trans_type, category, subcategory, desc, amount, party, qty=0, rate=0):
    query = '''
    INSERT INTO transactions (date, module, trans_type, category, subcategory, description, amount, party_name, qty, rate)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    run_query(query, (date_val, module, trans_type, category, subcategory, desc, amount, party, qty, rate))
    st.toast(f"Entry Saved: {subcategory} - {amount}")
    time.sleep(0.5)
    st.rerun()

def delete_transaction(tid):
    run_query("DELETE FROM transactions WHERE id = ?", (tid,))
    st.toast("Transaction Deleted")
    time.sleep(0.5)
    st.rerun()

# --- TABS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🐄 Tab 1: Livestock", 
    "🌾 Tab 2: Crops", 
    "💧 Tab 3: Water/Tubewell", 
    "⚙️ Tab 4: Operations", 
    "📊 Tab 5: Reports & Ledger"
])

# ==============================================================================
# TAB 1: LIVESTOCK
# ==============================================================================
with tab1:
    st.header("Livestock Management (Cow / Goat / Others)")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add Expense / Income")
        with st.form("livestock_form"):
            date_ls = st.date_input("Date", date.today())
            ls_type = st.selectbox("Animal Type", ["Cow", "Goat", "Buffalo", "Other"])
            ls_action = st.selectbox("Transaction Type", ["Expense", "Income"])
            
            # Dynamic Subcategories
            if ls_action == "Expense":
                ls_item = st.selectbox("Item", ["Wanda", "Chokar", "Khal", "Tori", "Khas", "Medicine", "Other"])
            else:
                ls_item = st.selectbox("Source", ["Milk Sale", "Animal Sale", "Manure Sale"])
                
            ls_desc = st.text_input("Description", placeholder="e.g. 5 Bags")
            ls_amount = st.number_input("Amount", min_value=0.0, step=100.0)
            
            # Who paid?
            if ls_action == "Expense":
                ls_party = st.text_input("Paid By (Person Name)", value="Cash", help="Enter 'Cash' if farm paid, or person name if credit")
            else:
                ls_party = "Cash" # Income usually goes to cash
                
            submitted_ls = st.form_submit_button("Save Entry")
            if submitted_ls:
                save_transaction(date_ls, "Livestock", ls_action, ls_type, ls_item, ls_desc, ls_amount, ls_party)

    with col2:
        st.subheader("Recent Records")
        df_ls = run_query("SELECT * FROM transactions WHERE module='Livestock' ORDER BY date DESC", fetch=True)
        
        if not df_ls.empty:
            st.dataframe(df_ls[['id', 'date', 'trans_type', 'category', 'subcategory', 'description', 'amount', 'party_name']], use_container_width=True)
            
            # Delete functionality
            del_id = st.number_input("Enter ID to Delete (Livestock)", min_value=0, step=1)
            if st.button("Delete Record", key="del_ls"):
                if del_id in df_ls['id'].values:
                    delete_transaction(del_id)
                else:
                    st.error("ID not found.")
        else:
            st.info("No livestock records found.")

# ==============================================================================
# TAB 2: CROPS
# ==============================================================================
with tab2:
    st.header("Crop Management")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add Crop Expense / Income")
        with st.form("crop_form"):
            date_cr = st.date_input("Date", date.today(), key="cr_date")
            cr_crop = st.text_input("Crop Name", value="Wheat")
            cr_action = st.selectbox("Transaction Type", ["Expense", "Income"], key="cr_type")
            
            if cr_action == "Expense":
                cr_item = st.selectbox("Expense Item", ["Khad (Fertilizer)", "Spray", "Seed", "Diesel", "Labor", "Other"])
            else:
                cr_item = st.selectbox("Income Source", ["Crop Sale", "Straw Sale"])
                
            cr_desc = st.text_input("Details", placeholder="e.g. Urea 2 bags")
            cr_amount = st.number_input("Amount", min_value=0.0, step=100.0, key="cr_amt")
            
            # Ledger Link
            if cr_action == "Expense":
                cr_party = st.text_input("Paid By (Person)", value="Cash", key="cr_party", help="Who paid for this?")
            else:
                cr_party = st.text_input("Sold To (Customer)", value="Cash", help="Leave Cash if immediate payment")

            submitted_cr = st.form_submit_button("Save Crop Entry")
            if submitted_cr:
                save_transaction(date_cr, "Crop", cr_action, cr_crop, cr_item, cr_desc, cr_amount, cr_party)

    with col2:
        st.subheader("Crop Ledger")
        df_cr = run_query("SELECT * FROM transactions WHERE module='Crop' ORDER BY date DESC", fetch=True)
        if not df_cr.empty:
            st.dataframe(df_cr[['id', 'date', 'trans_type', 'category', 'subcategory', 'description', 'amount', 'party_name']], use_container_width=True)
            
            del_id_cr = st.number_input("Enter ID to Delete (Crop)", min_value=0, step=1)
            if st.button("Delete Record", key="del_cr"):
                if del_id_cr in df_cr['id'].values:
                    delete_transaction(del_id_cr)
        else:
            st.info("No crop records found.")

# ==============================================================================
# TAB 3: WATER / TUBEWELL
# ==============================================================================
with tab3:
    st.header("Tubewell Water Income")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Calculate & Record Bill")
        with st.form("water_form"):
            date_wt = st.date_input("Date", date.today(), key="wt_date")
            farmer_name = st.text_input("Farmer Name")
            
            t_start = st.time_input("Start Time", value=datetime.strptime("08:00", "%H:%M").time())
            t_end = st.time_input("End Time", value=datetime.strptime("10:00", "%H:%M").time())
            rate_per_hr = st.number_input("Rate per Hour", value=1500.0)
            
            # Auto Calc Logic preview
            t1 = timedelta(hours=t_start.hour, minutes=t_start.minute)
            t2 = timedelta(hours=t_end.hour, minutes=t_end.minute)
            duration = (t2 - t1).total_seconds() / 3600
            if duration < 0: duration += 24 # Handle overnight
            
            est_bill = duration * rate_per_hr
            st.markdown(f"**Used Time:** {duration:.2f} hrs | **Total Bill:** :green[{est_bill:,.0f}]")
            
            submitted_wt = st.form_submit_button("Create Bill (Debit Farmer)")
            if submitted_wt and farmer_name:
                desc = f"{t_start} to {t_end}"
                # Recording as Income (Bill Generated)
                # Party Name is the Farmer (Who owes us)
                save_transaction(date_wt, "Water", "Bill", "Tubewell", "Water Usage", desc, est_bill, farmer_name, qty=duration, rate=rate_per_hr)

    with col2:
        st.subheader("Receive Payment")
        with st.form("water_payment"):
            pay_date = st.date_input("Date", date.today())
            pay_farmer = st.text_input("Farmer Name (Payer)")
            pay_amount = st.number_input("Amount Received", min_value=1.0)
            pay_desc = st.text_input("Note", "Cash Received")
            
            sub_pay = st.form_submit_button("Receive Payment (Credit Farmer)")
            if sub_pay and pay_farmer:
                # Type Payment means we received money against the debt
                save_transaction(pay_date, "Water", "Payment", "Tubewell", "Recovery", pay_desc, pay_amount, pay_farmer)

    st.divider()
    st.subheader("Water Ledger (Recent)")
    df_wt = run_query("SELECT * FROM transactions WHERE module='Water' ORDER BY date DESC", fetch=True)
    if not df_wt.empty:
        st.dataframe(df_wt[['id', 'date', 'trans_type', 'description', 'qty', 'rate', 'amount', 'party_name']], use_container_width=True)
        
        del_id_wt = st.number_input("Enter ID to Delete (Water)", min_value=0, step=1)
        if st.button("Delete Record", key="del_wt"):
            if del_id_wt in df_wt['id'].values:
                delete_transaction(del_id_wt)

# ==============================================================================
# TAB 4: OPERATIONAL EXPENSES
# ==============================================================================
with tab4:
    st.header("Operational & Salary Expenses")
    st.info("Track salaries, fuel, and machinery maintenance. Manage who paid for it.")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Add Expense")
        with st.form("ops_form"):
            date_op = st.date_input("Date", date.today(), key="op_date")
            op_cat = st.selectbox("Category", ["Salaries", "Fuel", "Machinery Purchase", "Maintenance", "Misc"])
            op_desc = st.text_input("Description", placeholder="e.g. Tractor Oil Change")
            op_amount = st.number_input("Amount", min_value=0.0)
            
            # The "Managed By" logic
            op_manager = st.text_input("Managed By / Paid By", value="Cash", help="If an employee paid from pocket, write their name. If farm cash, write Cash.")
            
            sub_op = st.form_submit_button("Record Expense")
            if sub_op:
                save_transaction(date_op, "Operations", "Expense", "General", op_cat, op_desc, op_amount, op_manager)
    
    with col2:
        st.subheader("Settle Balance (Pay Back)")
        with st.expander("Make Payment to Employee/Person"):
            with st.form("settle_form"):
                set_date = st.date_input("Date", date.today())
                set_person = st.text_input("Person Name")
                set_amount = st.number_input("Amount Paid", min_value=1.0)
                set_note = st.text_input("Note", "Reimbursement")
                
                if st.form_submit_button("Record Payment"):
                    # We are paying them back. 
                    # Type: Payment (reduces their credit balance)
                    save_transaction(set_date, "Operations", "Payment", "General", "Reimbursement", set_note, set_amount, set_person)

        st.subheader("Operations Log")
        df_op = run_query("SELECT * FROM transactions WHERE module='Operations' ORDER BY date DESC", fetch=True)
        if not df_op.empty:
            st.dataframe(df_op[['id', 'date', 'subcategory', 'description', 'amount', 'party_name']], use_container_width=True)
            
            del_id_op = st.number_input("Enter ID to Delete (Ops)", min_value=0, step=1)
            if st.button("Delete Record", key="del_op"):
                if del_id_op in df_op['id'].values:
                    delete_transaction(del_id_op)

# ==============================================================================
# TAB 5: REPORTS
# ==============================================================================
with tab5:
    st.header("📊 Financial Reports & Ledger")
    
    # Fetch all data
    df = run_query("SELECT * FROM transactions", fetch=True)
    
    if df.empty:
        st.warning("No data available.")
    else:
        df['date'] = pd.to_datetime(df['date'])
        
        # --- FILTERS ---
        colf1, colf2, colf3 = st.columns(3)
        with colf1:
            start_date = st.date_input("Start Date", date.today().replace(day=1))
        with colf2:
            end_date = st.date_input("End Date", date.today())
        with colf3:
            filter_party = st.multiselect("Filter by Person/Farmer", options=df['party_name'].unique())

        # Filter Logic
        mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
        if filter_party:
            mask = mask & (df['party_name'].isin(filter_party))
        
        filtered_df = df.loc[mask].copy()
        
        # --- TABULAR LEDGER LOGIC ---
        # Concept: 
        # For Expenses: If 'Cash', Farm spent money. If 'Person', Person gets Credit (we owe them).
        # For Income: If 'Cash', Farm got money. If 'Person', Person gets Debit (they owe us).
        # For Bills (Water): Farmer gets Debit (owes us).
        # For Payments (Water): Farmer gets Credit (paid us).
        
        ledger_data = []
        
        for index, row in filtered_df.iterrows():
            # Defaults
            debit = 0
            credit = 0
            party = row['party_name']
            
            if row['module'] == 'Water':
                if row['trans_type'] == 'Bill':
                    # Farmer used water -> Farmer Debit (Receivable)
                    debit = row['amount']
                    credit = 0
                elif row['trans_type'] == 'Payment':
                    # Farmer paid -> Farmer Credit
                    debit = 0
                    credit = row['amount']
            
            elif row['module'] == 'Operations' or row['module'] == 'Livestock' or row['module'] == 'Crop':
                if row['trans_type'] == 'Expense':
                    if party.lower() != 'cash':
                        # Person paid for us -> Person Credit (Payable)
                        credit = row['amount']
                        debit = 0
                elif row['trans_type'] == 'Payment': # Reimbursement
                     # We paid person back -> Person Debit
                     debit = row['amount']
                     credit = 0
                elif row['trans_type'] == 'Income':
                     # Usually Cash, but if sold on credit
                     if party.lower() != 'cash':
                         debit = row['amount']
            
            # Only add to ledger if it involves a specific person (not Cash)
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
        
        # --- DISPLAY SECTIONS ---
        
        st.subheader("1. Profit & Loss Summary (Farm View)")
        pl_col1, pl_col2, pl_col3 = st.columns(3)
        
        # Simple Income vs Expense calculation
        total_income = filtered_df[filtered_df['trans_type'].isin(['Income', 'Bill'])]['amount'].sum()
        total_expense = filtered_df[filtered_df['trans_type'] == 'Expense']['amount'].sum()
        
        pl_col1.metric("Total Income/Billings", f"{total_income:,.0f}")
        pl_col2.metric("Total Expenses", f"{total_expense:,.0f}")
        pl_col3.metric("Net Profit", f"{total_income - total_expense:,.0f}", delta_color="normal")

        st.divider()

        st.subheader("2. Person/Farmer Ledger (Detailed)")
        if not ledger_df.empty:
            # Group by person to calculate running balances
            st.dataframe(ledger_df, use_container_width=True)
            
            st.subheader("3. Outstanding Balances")
            balance_df = ledger_df.groupby("Name")[["Debit (They Owe Us/Paid Us Back)", "Credit (We Owe Them/They Paid Us)"]].sum().reset_index()
            balance_df["Net Balance"] = balance_df["Debit (They Owe Us/Paid Us Back)"] - balance_df["Credit (We Owe Them/They Paid Us)"]
            
            def get_status(val):
                if val > 0: return "Collect from them"
                elif val < 0: return "Pay them"
                else: return "Settled"
                
            balance_df["Status"] = balance_df["Net Balance"].apply(get_status)
            st.dataframe(balance_df, use_container_width=True)
            
        else:
            st.info("No credit/debit transactions with individuals in this period.")
            
        st.divider()
        st.subheader("4. Raw Data Export")
        st.dataframe(filtered_df)
