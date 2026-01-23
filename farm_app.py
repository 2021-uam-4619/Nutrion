import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import json
import io
from pathlib import Path
import base64
import uuid

# Set page configuration
st.set_page_config(
    page_title="Complete Farm Management System",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
def init_database():
    conn = sqlite3.connect('farm_management.db')
    cursor = conn.cursor()
    
    # Livestock table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livestock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            category TEXT NOT NULL,
            expense_type TEXT,
            quantity INTEGER,
            amount REAL NOT NULL,
            manager TEXT,
            remarks TEXT,
            transaction_type TEXT CHECK(transaction_type IN ('expense', 'income')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crop table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            crop_type TEXT NOT NULL,
            area REAL,
            expense_type TEXT,
            amount REAL NOT NULL,
            manager TEXT,
            remarks TEXT,
            transaction_type TEXT CHECK(transaction_type IN ('expense', 'income')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Water supply table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_supply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            farmer_name TEXT NOT NULL,
            farmer_phone TEXT,
            start_time TIME,
            end_time TIME,
            hours REAL,
            rate REAL NOT NULL,
            total_bill REAL NOT NULL,
            paid REAL DEFAULT 0,
            balance REAL NOT NULL,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Expenses table (updated with new categories)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            manager TEXT,
            receipt_no TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Income table (updated with new categories)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
            received_by TEXT,
            customer TEXT,
            receipt_no TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Managers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS managers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            designation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Farmers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Water payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT NOT NULL,
            amount REAL NOT NULL,
            payment_method TEXT,
            date DATE NOT NULL,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    return conn

# Get database connection
@st.cache_resource
def get_connection():
    return init_database()

# Initialize session state for water timer
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'timer_seconds' not in st.session_state:
    st.session_state.timer_seconds = 0
if 'timer_start_time' not in st.session_state:
    st.session_state.timer_start_time = None
if 'tab_counter' not in st.session_state:
    st.session_state.tab_counter = 0

# Function to generate unique keys
def generate_key(widget_name, tab_name=""):
    return f"{tab_name}_{widget_name}_{uuid.uuid4().hex[:8]}"

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        border-bottom: 5px solid #27ae60;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 4px solid #3498db;
        margin-bottom: 1rem;
    }
    
    .ledger-entry {
        padding: 0.75rem;
        border-bottom: 1px solid #e0e0e0;
        margin-bottom: 0.5rem;
    }
    
    .ledger-entry.credit {
        border-left: 4px solid #27ae60;
        background: linear-gradient(90deg, rgba(39, 174, 96, 0.05), transparent);
    }
    
    .ledger-entry.debit {
        border-left: 4px solid #e74c3c;
        background: linear-gradient(90deg, rgba(231, 76, 60, 0.05), transparent);
    }
    
    .tab-content {
        padding: 1.5rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #e4edf5 100%);
        border-radius: 10px;
        margin-top: 1rem;
    }
    
    .stButton button {
        width: 100%;
    }
    
    .stDateInput {
        width: 100%;
    }
    
    .stSelectbox {
        width: 100%;
    }
    
    .stNumberInput {
        width: 100%;
    }
    
    .stTextInput {
        width: 100%;
    }
    
    .stTextArea {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1 style="margin: 0; font-size: 2.8rem;">🚜 Complete Farm Management System</h1>
    <p style="margin: 0; font-size: 1.2rem; opacity: 0.9;">Complete Solution for Farm Operations & Management</p>
</div>
""", unsafe_allow_html=True)

# Main tabs
tabs = st.tabs(["🏠 Dashboard", "🐄 Livestock", "🌾 Crop", "💧 Water Supply", "💰 Expenses", "💵 Income", "📊 Reports"])

# ==================== DASHBOARD TAB ====================
with tabs[0]:
    conn = get_connection()
    
    st.markdown("## 📊 Farm Dashboard")
    
    # Get current date for filtering
    today = datetime.now().date()
    first_day_of_month = today.replace(day=1)
    
    # Calculate metrics
    # Total Income
    income_df = pd.read_sql("SELECT SUM(amount) as total FROM income", conn)
    total_income = income_df['total'].iloc[0] or 0
    
    # Total Expenses
    expenses_df = pd.read_sql("SELECT SUM(amount) as total FROM expenses", conn)
    total_expenses = expenses_df['total'].iloc[0] or 0
    
    # Livestock Expenses
    livestock_expenses_df = pd.read_sql("SELECT SUM(amount) as total FROM livestock WHERE transaction_type='expense'", conn)
    livestock_expenses = livestock_expenses_df['total'].iloc[0] or 0
    
    # Livestock Income
    livestock_income_df = pd.read_sql("SELECT SUM(amount) as total FROM livestock WHERE transaction_type='income'", conn)
    livestock_income = livestock_income_df['total'].iloc[0] or 0
    
    # Crop Expenses
    crop_expenses_df = pd.read_sql("SELECT SUM(amount) as total FROM crops WHERE transaction_type='expense'", conn)
    crop_expenses = crop_expenses_df['total'].iloc[0] or 0
    
    # Crop Income
    crop_income_df = pd.read_sql("SELECT SUM(amount) as total FROM crops WHERE transaction_type='income'", conn)
    crop_income = crop_income_df['total'].iloc[0] or 0
    
    # Water Supply Income
    water_income_df = pd.read_sql("SELECT SUM(paid) as total FROM water_supply", conn)
    water_income = water_income_df['total'].iloc[0] or 0
    
    # Display metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Income", f"PKR {total_income:,.0f}")
    with col2:
        st.metric("Total Expenses", f"PKR {total_expenses:,.0f}")
    with col3:
        net_profit = total_income - total_expenses
        st.metric("Net Profit", f"PKR {net_profit:,.0f}", 
                 delta=f"{(net_profit/total_income*100 if total_income > 0 else 0):.1f}%" if net_profit >= 0 else None)
    with col4:
        profit_margin = (net_profit/total_income*100) if total_income > 0 else 0
        st.metric("Profit Margin", f"{profit_margin:.1f}%")
    
    # Income breakdown chart
    st.markdown("### Income Breakdown")
    income_data = {
        'Category': ['Livestock', 'Crop', 'Water Supply'],
        'Amount': [livestock_income, crop_income, water_income]
    }
    
    if any(income_data['Amount']):
        fig = px.pie(income_data, values='Amount', names='Category', 
                    color_discrete_sequence=px.colors.sequential.Greens)
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent transactions
    st.markdown("### Recent Transactions")
    
    # Get recent livestock transactions
    recent_livestock = pd.read_sql("""
        SELECT date, category, amount, transaction_type 
        FROM livestock 
        ORDER BY date DESC LIMIT 10
    """, conn)
    
    # Get recent crop transactions
    recent_crops = pd.read_sql("""
        SELECT date, crop_type as category, amount, transaction_type 
        FROM crops 
        ORDER BY date DESC LIMIT 10
    """, conn)
    
    # Get recent expenses
    recent_expenses = pd.read_sql("""
        SELECT date, category, amount, 'expense' as transaction_type 
        FROM expenses 
        ORDER BY date DESC LIMIT 10
    """, conn)
    
    # Get recent income
    recent_income = pd.read_sql("""
        SELECT date, source as category, amount, 'income' as transaction_type 
        FROM income 
        ORDER BY date DESC LIMIT 10
    """, conn)
    
    # Combine all recent transactions
    recent_transactions = pd.concat([
        recent_livestock,
        recent_crops,
        recent_expenses,
        recent_income
    ], ignore_index=True)
    
    if not recent_transactions.empty:
        recent_transactions = recent_transactions.sort_values('date', ascending=False)
        st.dataframe(recent_transactions, use_container_width=True, hide_index=True)
    else:
        st.info("No transactions recorded yet.")

# ==================== LIVESTOCK TAB ====================
with tabs[1]:
    conn = get_connection()
    
    st.markdown("## 🐄 Livestock Management")
    
    # Create two columns for form and ledger
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Add Livestock Record")
        
        with st.form(key="livestock_form"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                date = st.date_input("Date *", value=datetime.now().date(), key="livestock_date")
                category = st.selectbox("Category *", 
                                      ["", "Cow", "Beef", "Goat", "Others"],
                                      key="livestock_category")
                expense_type = st.selectbox("Expense Type", 
                                          ["", "Khal", "Chokar", "Tori", "Ghaas/Fodder", 
                                           "Medicine", "Vaccination", "Others"],
                                          key="livestock_expense_type")
                quantity = st.number_input("Quantity", min_value=0, value=0, key="livestock_quantity")
            
            with col_b:
                amount = st.number_input("Amount (PKR) *", min_value=0.0, value=0.0, key="livestock_amount")
                # Get managers from database
                managers_df = pd.read_sql("SELECT name FROM managers", conn)
                managers = managers_df['name'].tolist() if not managers_df.empty else []
                manager = st.selectbox("Expense Managed By *", [""] + managers, key="livestock_manager")
                transaction_type = st.selectbox("Transaction Type *", 
                                              ["expense", "income"], key="livestock_transaction_type")
                remarks = st.text_area("Remarks", key="livestock_remarks")
            
            submitted = st.form_submit_button("Add Record")
            
            if submitted:
                if not category or amount <= 0 or not manager:
                    st.error("Please fill all required fields (*)")
                else:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO livestock 
                        (date, category, expense_type, quantity, amount, manager, remarks, transaction_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (date, category, expense_type if expense_type else None, 
                         quantity, amount, manager, remarks, transaction_type))
                    conn.commit()
                    st.success("Livestock record added successfully!")
                    st.rerun()
    
    with col2:
        st.markdown("### Livestock Ledger")
        
        # Filter options
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filter_category = st.selectbox("Filter by Category", 
                                         ["All"] + ["Cow", "Beef", "Goat", "Others"],
                                         key="livestock_filter_category")
        with col_f2:
            date_from = st.date_input("From Date", value=None, key="livestock_date_from")
        with col_f3:
            date_to = st.date_input("To Date", value=None, key="livestock_date_to")
        
        # Build query based on filters
        query = "SELECT * FROM livestock WHERE 1=1"
        params = []
        
        if filter_category != "All":
            query += " AND category = ?"
            params.append(filter_category)
        
        if date_from:
            query += " AND date >= ?"
            params.append(date_from)
        
        if date_to:
            query += " AND date <= ?"
            params.append(date_to)
        
        query += " ORDER BY date DESC"
        
        livestock_data = pd.read_sql(query, conn, params=params)
        
        if not livestock_data.empty:
            # Calculate totals
            total_expenses = livestock_data[livestock_data['transaction_type'] == 'expense']['amount'].sum()
            total_income = livestock_data[livestock_data['transaction_type'] == 'income']['amount'].sum()
            net_balance = total_income - total_expenses
            
            # Display metrics
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Total Expenses", f"PKR {total_expenses:,.0f}")
            with col_m2:
                st.metric("Total Income", f"PKR {total_income:,.0f}")
            with col_m3:
                st.metric("Net Balance", f"PKR {net_balance:,.0f}")
            
            # Display ledger
            st.markdown("#### Ledger Entries")
            for _, row in livestock_data.iterrows():
                entry_class = "credit" if row['transaction_type'] == 'income' else "debit"
                st.markdown(f"""
                <div class="ledger-entry {entry_class}">
                    <strong>{row['date']}</strong> - {row['category']}<br>
                    <small>{row['expense_type'] or row['transaction_type']} - {row['remarks'] or ''}</small><br>
                    <strong style="color: {'#27ae60' if row['transaction_type'] == 'income' else '#e74c3c'}">
                        {'+' if row['transaction_type'] == 'income' else '-'} PKR {row['amount']:,.0f}
                    </strong>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No livestock records found.")
    
    # Livestock Statistics and Data Table
    st.markdown("### Livestock Statistics & Records")
    
    if not livestock_data.empty:
        # Summary statistics
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            total_cows = livestock_data[livestock_data['category'] == 'Cow']['quantity'].sum()
            st.metric("Total Cows", int(total_cows))
        with col_s2:
            total_beef = livestock_data[livestock_data['category'] == 'Beef']['quantity'].sum()
            st.metric("Total Beef", int(total_beef))
        with col_s3:
            total_goats = livestock_data[livestock_data['category'] == 'Goat']['quantity'].sum()
            st.metric("Total Goats", int(total_goats))
        with col_s4:
            total_quantity = livestock_data['quantity'].sum()
            total_expense_amount = livestock_data[livestock_data['transaction_type'] == 'expense']['amount'].sum()
            avg_cost_per_animal = total_expense_amount / total_quantity if total_quantity > 0 else 0
            st.metric("Avg Cost/Animal", f"PKR {avg_cost_per_animal:,.0f}")
        
        # Display data table
        st.dataframe(livestock_data[['date', 'category', 'transaction_type', 'quantity', 
                                    'amount', 'manager', 'remarks']], 
                    use_container_width=True, hide_index=True)
        
        # Export options
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            if st.button("📥 Export to Excel", key="export_livestock_excel"):
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    livestock_data.to_excel(writer, sheet_name='Livestock', index=False)
                st.download_button(
                    label="Download Excel",
                    data=buffer.getvalue(),
                    file_name=f"livestock_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_livestock_excel"
                )
        
        with col_e2:
            if st.button("📄 Export to CSV", key="export_livestock_csv"):
                csv = livestock_data.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"livestock_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="download_livestock_csv"
                )
    else:
        st.info("No livestock data available to display.")

# ==================== CROP TAB ====================
with tabs[2]:
    conn = get_connection()
    
    st.markdown("## 🌾 Crop Management")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Add Crop Record")
        
        with st.form(key="crop_form"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                date = st.date_input("Crop Date *", value=datetime.now().date(), key="crop_date")
                crop_type = st.selectbox("Crop Type *", 
                                       ["", "Wheat", "Rice", "Cotton", "Kheera (Cucumber)", 
                                        "Corn", "Vegetables", "Others"],
                                       key="crop_type_select")
                area = st.number_input("Area (acres)", min_value=0.0, value=0.0, key="crop_area")
                expense_type = st.selectbox("Expense Type", 
                                          ["", "Labor", "Seeds", "Fertilizer", "Spray", 
                                           "Land Preparation", "Others"],
                                          key="crop_expense_type")
            
            with col_b:
                amount = st.number_input("Crop Amount (PKR) *", min_value=0.0, value=0.0, key="crop_amount")
                managers_df = pd.read_sql("SELECT name FROM managers", conn)
                managers = managers_df['name'].tolist() if not managers_df.empty else []
                manager = st.selectbox("Crop Manager *", [""] + managers, key="crop_manager")
                transaction_type = st.selectbox("Crop Transaction Type *", 
                                              ["expense", "income"], key="crop_transaction_type")
                remarks = st.text_area("Crop Remarks", key="crop_remarks")
            
            submitted = st.form_submit_button("Add Crop Record")
            
            if submitted:
                if not crop_type or amount <= 0 or not manager:
                    st.error("Please fill all required fields (*)")
                else:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO crops 
                        (date, crop_type, area, expense_type, amount, manager, remarks, transaction_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (date, crop_type, area, expense_type if expense_type else None, 
                         amount, manager, remarks, transaction_type))
                    conn.commit()
                    st.success("Crop record added successfully!")
                    st.rerun()
    
    with col2:
        st.markdown("### Crop Ledger")
        
        # Filter options
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filter_crop = st.selectbox("Filter by Crop Type", 
                                     ["All"] + ["Wheat", "Rice", "Cotton", "Kheera (Cucumber)", 
                                               "Corn", "Vegetables", "Others"],
                                     key="crop_filter_type")
        with col_f2:
            crop_date = st.date_input("Filter Date", value=None, key="crop_filter_date")
        
        # Build query
        query = "SELECT * FROM crops WHERE 1=1"
        params = []
        
        if filter_crop != "All":
            query += " AND crop_type = ?"
            params.append(filter_crop)
        
        if crop_date:
            query += " AND date = ?"
            params.append(crop_date)
        
        query += " ORDER BY date DESC"
        
        crop_data = pd.read_sql(query, conn, params=params)
        
        if not crop_data.empty:
            # Calculate totals
            total_crop_expenses = crop_data[crop_data['transaction_type'] == 'expense']['amount'].sum()
            total_crop_income = crop_data[crop_data['transaction_type'] == 'income']['amount'].sum()
            total_area = crop_data['area'].sum()
            
            # Display metrics
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Total Area", f"{total_area:.1f} acres")
            with col_m2:
                st.metric("Crop Expenses", f"PKR {total_crop_expenses:,.0f}")
            with col_m3:
                st.metric("Crop Income", f"PKR {total_crop_income:,.0f}")
            
            # Display ledger
            st.markdown("#### Ledger Entries")
            for _, row in crop_data.iterrows():
                entry_class = "credit" if row['transaction_type'] == 'income' else "debit"
                st.markdown(f"""
                <div class="ledger-entry {entry_class}">
                    <strong>{row['date']}</strong> - {row['crop_type']}<br>
                    <small>{row['expense_type'] or row['transaction_type']} - {row['area']} acres</small><br>
                    <strong style="color: {'#27ae60' if row['transaction_type'] == 'income' else '#e74c3c'}">
                        {'+' if row['transaction_type'] == 'income' else '-'} PKR {row['amount']:,.0f}
                    </strong>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No crop records found.")
    
    # Crop Statistics
    st.markdown("### Crop Statistics")
    
    if not crop_data.empty:
        # Crop type distribution
        crop_summary = crop_data.groupby('crop_type').agg({
            'amount': 'sum',
            'area': 'sum'
        }).reset_index()
        
        if not crop_summary.empty:
            fig = px.bar(crop_summary, x='crop_type', y='amount', 
                        title="Crop Revenue by Type",
                        color='crop_type')
            st.plotly_chart(fig, use_container_width=True)
        
        # Display detailed data
        st.dataframe(crop_data[['date', 'crop_type', 'area', 'transaction_type', 
                               'amount', 'manager', 'remarks']], 
                    use_container_width=True, hide_index=True)

# ==================== WATER SUPPLY TAB ====================
with tabs[3]:
    conn = get_connection()
    
    st.markdown("## 💧 Water Supply Management")
    
    # Timer Section
    st.markdown("### Water Supply Timer")
    
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    
    with col_t1:
        if st.button("▶️ Start Timer", type="primary", key="start_timer"):
            if not st.session_state.timer_running:
                st.session_state.timer_running = True
                st.session_state.timer_start_time = datetime.now()
                st.rerun()
    
    with col_t2:
        if st.button("⏹️ Stop Timer", key="stop_timer"):
            if st.session_state.timer_running:
                st.session_state.timer_running = False
                st.session_state.timer_seconds += (datetime.now() - st.session_state.timer_start_time).total_seconds()
                st.rerun()
    
    with col_t3:
        if st.button("🔄 Reset Timer", key="reset_timer"):
            st.session_state.timer_running = False
            st.session_state.timer_seconds = 0
            st.rerun()
    
    with col_t4:
        hours = st.session_state.timer_seconds / 3600
        if st.session_state.timer_running:
            current_seconds = st.session_state.timer_seconds + (datetime.now() - st.session_state.timer_start_time).total_seconds()
            hours = current_seconds / 3600
        
        st.metric("Total Hours", f"{hours:.2f}")
    
    # Water Supply Form
    st.markdown("### Add Water Supply Record")
    
    with st.form(key="water_supply_form"):
        col_w1, col_w2 = st.columns(2)
        
        with col_w1:
            farmer_name = st.text_input("Farmer Name *", key="water_farmer_name")
            farmer_phone = st.text_input("Phone Number", key="water_farmer_phone")
            rate = st.number_input("Rate per Hour (PKR) *", min_value=0.0, value=500.0, key="water_rate")
            date = st.date_input("Supply Date *", value=datetime.now().date(), key="water_date")
        
        with col_w2:
            # Manual time input
            manual_hours = st.number_input("Manual Hours (override)", min_value=0.0, value=hours, step=0.1, key="water_manual_hours")
            start_time = st.time_input("Start Time", value=datetime.now().time(), key="water_start_time")
            end_time = st.time_input("End Time", value=(datetime.now() + timedelta(hours=1)).time(), key="water_end_time")
            
            # Calculate bill
            total_hours = manual_hours
            total_bill = total_hours * rate
            paid = st.number_input("Amount Paid", min_value=0.0, value=0.0, key="water_paid")
            balance = total_bill - paid
            remarks = st.text_area("Water Supply Remarks", key="water_remarks")
        
        submitted = st.form_submit_button("💾 Save Water Supply Record")
        
        if submitted:
            if not farmer_name or rate <= 0:
                st.error("Please fill all required fields (*)")
            else:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO water_supply 
                    (date, farmer_name, farmer_phone, start_time, end_time, 
                     hours, rate, total_bill, paid, balance, remarks)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (date, farmer_name, farmer_phone, start_time, end_time,
                     total_hours, rate, total_bill, paid, balance, remarks))
                conn.commit()
                st.success("Water supply record saved successfully!")
                st.rerun()
    
    # Farmer Ledger Management
    st.markdown("### Farmer Ledger")
    
    # Get unique farmers
    farmers_df = pd.read_sql("SELECT DISTINCT farmer_name FROM water_supply", conn)
    farmers = farmers_df['farmer_name'].tolist() if not farmers_df.empty else []
    
    if farmers:
        selected_farmer = st.selectbox("Select Farmer", farmers, key="farmer_select")
        
        if selected_farmer:
            # Get farmer's water supply records
            farmer_records = pd.read_sql(
                "SELECT * FROM water_supply WHERE farmer_name = ? ORDER BY date DESC",
                conn, params=(selected_farmer,)
            )
            
            # Get farmer's payments
            payments_df = pd.read_sql(
                "SELECT * FROM water_payments WHERE farmer_name = ? ORDER BY date DESC",
                conn, params=(selected_farmer,)
            )
            
            # Calculate totals
            total_bill = farmer_records['total_bill'].sum()
            total_paid = farmer_records['paid'].sum() + payments_df['amount'].sum()
            balance = total_bill - total_paid
            
            # Display summary
            col_sum1, col_sum2, col_sum3 = st.columns(3)
            with col_sum1:
                st.metric("Total Bill", f"PKR {total_bill:,.0f}")
            with col_sum2:
                st.metric("Total Paid", f"PKR {total_paid:,.0f}")
            with col_sum3:
                color = "normal" if balance <= 0 else "inverse"
                st.metric("Balance", f"PKR {balance:,.0f}")
            
            # Payment form
            st.markdown("#### Record Payment")
            with st.form(key="payment_form"):
                col_p1, col_p2, col_p3 = st.columns(3)
                with col_p1:
                    payment_amount = st.number_input("Payment Amount", min_value=0.0, key="payment_amount")
                with col_p2:
                    payment_date = st.date_input("Payment Date", value=datetime.now().date(), key="payment_date")
                with col_p3:
                    payment_method = st.selectbox("Payment Method", 
                                                ["Cash", "Bank Transfer", "Check"],
                                                key="payment_method")
                
                if st.form_submit_button("💳 Record Payment"):
                    if payment_amount > 0:
                        cursor = conn.cursor()
                        cursor.execute('''
                            INSERT INTO water_payments 
                            (farmer_name, amount, payment_method, date, remarks)
                            VALUES (?, ?, ?, ?, ?)
                        ''', (selected_farmer, payment_amount, payment_method, 
                             payment_date, "Payment recorded"))
                        
                        conn.commit()
                        st.success("Payment recorded successfully!")
                        st.rerun()
            
            # Display ledger entries
            st.markdown("#### Ledger Entries")
            
            # Combine water supply and payments
            for _, record in farmer_records.iterrows():
                st.markdown(f"""
                <div class="ledger-entry debit">
                    <strong>{record['date']}</strong> - Water Supply<br>
                    <small>{record['hours']} hours @ PKR {record['rate']}/hour</small><br>
                    <strong style="color: #e74c3c;">PKR {record['total_bill']:,.0f}</strong>
                </div>
                """, unsafe_allow_html=True)
            
            for _, payment in payments_df.iterrows():
                st.markdown(f"""
                <div class="ledger-entry credit">
                    <strong>{payment['date']}</strong> - Payment Received<br>
                    <small>{payment['payment_method']}</small><br>
                    <strong style="color: #27ae60;">+ PKR {payment['amount']:,.0f}</strong>
                </div>
                """, unsafe_allow_html=True)
    
    # Display all water supply records
    st.markdown("### All Water Supply Records")
    water_data = pd.read_sql("SELECT * FROM water_supply ORDER BY date DESC", conn)
    
    if not water_data.empty:
        st.dataframe(water_data[['date', 'farmer_name', 'hours', 'rate', 
                                'total_bill', 'paid', 'balance', 'remarks']],
                    use_container_width=True, hide_index=True)
    else:
        st.info("No water supply records found.")

# ==================== EXPENSES TAB ====================
with tabs[4]:
    conn = get_connection()
    
    st.markdown("## 💰 Expenses Management")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Add Expense")
        
        with st.form(key="expense_form"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                date = st.date_input("Expense Date *", value=datetime.now().date(), key="expense_date")
                # Updated categories as requested
                category = st.selectbox("Category *", 
                                      ["", "Salary", "Machinery", "Petrol", "Diesel", 
                                       "Electricity Bill", "Turbine Bill", "Kitchen", 
                                       "Construction", "Maintenance", "Others"],
                                      key="expense_category")
                description = st.text_input("Description *", key="expense_description")
                amount = st.number_input("Amount (PKR) *", min_value=0.0, value=0.0, key="expense_amount")
            
            with col_b:
                managers_df = pd.read_sql("SELECT name FROM managers", conn)
                managers = managers_df['name'].tolist() if not managers_df.empty else []
                manager = st.selectbox("Managed By *", [""] + managers, key="expense_manager")
                receipt_no = st.text_input("Receipt No", key="expense_receipt_no")
                remarks = st.text_area("Expense Remarks", key="expense_remarks")
            
            submitted = st.form_submit_button("Add Expense")
            
            if submitted:
                if not category or not description or amount <= 0 or not manager:
                    st.error("Please fill all required fields (*)")
                else:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO expenses 
                        (date, category, description, amount, manager, receipt_no, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (date, category, description, amount, manager, receipt_no, remarks))
                    conn.commit()
                    st.success("Expense added successfully!")
                    st.rerun()
    
    with col2:
        st.markdown("### Expense Statistics")
        
        # Get expense data
        expense_data = pd.read_sql("SELECT * FROM expenses", conn)
        
        if not expense_data.empty:
            # Calculate metrics
            today = datetime.now().date()
            today_expenses = expense_data[expense_data['date'] == today]['amount'].sum()
            
            current_month = today.month
            current_year = today.year
            month_expenses = expense_data[
                (expense_data['date'].apply(lambda x: x.month) == current_month) &
                (expense_data['date'].apply(lambda x: x.year) == current_year)
            ]['amount'].sum()
            
            total_expenses = expense_data['amount'].sum()
            
            # Display metrics
            col_m1, col_m2, col_m3 = st.columns(3)
            with col_m1:
                st.metric("Today's Expenses", f"PKR {today_expenses:,.0f}")
            with col_m2:
                st.metric("This Month", f"PKR {month_expenses:,.0f}")
            with col_m3:
                st.metric("Total Expenses", f"PKR {total_expenses:,.0f}")
            
            # Expense by category chart
            category_summary = expense_data.groupby('category')['amount'].sum().reset_index()
            if not category_summary.empty:
                fig = px.pie(category_summary, values='amount', names='category',
                            title="Expenses by Category")
                st.plotly_chart(fig, use_container_width=True)
    
    # Manager Ledger
    st.markdown("### Manager Expense Ledger")
    
    # Get unique managers
    managers_expense = expense_data['manager'].unique().tolist() if not expense_data.empty else []
    
    if managers_expense:
        selected_manager = st.selectbox("Select Manager", managers_expense, key="manager_select")
        
        if selected_manager:
            # Filter expenses by manager
            manager_expenses = expense_data[expense_data['manager'] == selected_manager]
            
            # Date range filter
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                manager_date_from = st.date_input("From Date", value=None, key="manager_date_from")
            with col_d2:
                manager_date_to = st.date_input("To Date", value=None, key="manager_date_to")
            
            # Apply date filters
            if manager_date_from:
                manager_expenses = manager_expenses[manager_expenses['date'] >= manager_date_from]
            if manager_date_to:
                manager_expenses = manager_expenses[manager_expenses['date'] <= manager_date_to]
            
            # Display manager expenses
            total_manager_expenses = manager_expenses['amount'].sum()
            
            st.metric(f"Total Expenses by {selected_manager}", 
                     f"PKR {total_manager_expenses:,.0f}")
            
            for _, expense in manager_expenses.iterrows():
                st.markdown(f"""
                <div class="ledger-entry">
                    <strong>{expense['date']}</strong> - {expense['category']}<br>
                    <small>{expense['description']}</small><br>
                    <strong style="color: #e74c3c;">PKR {expense['amount']:,.0f}</strong>
                </div>
                """, unsafe_allow_html=True)
    
    # All Expenses Table
    st.markdown("### All Expenses")
    if not expense_data.empty:
        st.dataframe(expense_data[['date', 'category', 'description', 
                                  'amount', 'manager', 'receipt_no', 'remarks']],
                    use_container_width=True, hide_index=True)
    else:
        st.info("No expense records found.")

# ==================== INCOME TAB ====================
with tabs[5]:
    conn = get_connection()
    
    st.markdown("## 💵 Income Management")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### Add Income")
        
        with st.form(key="income_form"):
            col_a, col_b = st.columns(2)
            
            with col_a:
                date = st.date_input("Income Date *", value=datetime.now().date(), key="income_date")
                # Updated income sources as requested
                source = st.selectbox("Income Source *", 
                                    ["", "Goats", "Beef", "Cows", "Crop Sale", 
                                     "Water Supply", "Others"],
                                    key="income_source")
                amount = st.number_input("Income Amount (PKR) *", min_value=0.0, value=0.0, key="income_amount")
                customer = st.text_input("Customer/Payer", key="income_customer")
            
            with col_b:
                managers_df = pd.read_sql("SELECT name FROM managers", conn)
                managers = managers_df['name'].tolist() if not managers_df.empty else []
                received_by = st.selectbox("Received By", [""] + managers, key="income_received_by")
                receipt_no = st.text_input("Receipt No", key="income_receipt_no")
                remarks = st.text_area("Income Remarks", key="income_remarks")
            
            submitted = st.form_submit_button("Add Income")
            
            if submitted:
                if not source or amount <= 0:
                    st.error("Please fill all required fields (*)")
                else:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT INTO income 
                        (date, source, amount, received_by, customer, receipt_no, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (date, source, amount, received_by, customer, receipt_no, remarks))
                    conn.commit()
                    st.success("Income added successfully!")
                    st.rerun()
    
    with col2:
        st.markdown("### Income Dashboard")
        
        # Get all income data
        income_data = pd.read_sql("SELECT * FROM income", conn)
        
        # Get livestock income
        livestock_income_df = pd.read_sql(
            "SELECT SUM(amount) as total FROM livestock WHERE transaction_type='income'",
            conn
        )
        livestock_income = livestock_income_df['total'].iloc[0] or 0
        
        # Get crop income
        crop_income_df = pd.read_sql(
            "SELECT SUM(amount) as total FROM crops WHERE transaction_type='income'",
            conn
        )
        crop_income = crop_income_df['total'].iloc[0] or 0
        
        # Get water supply income
        water_income_df = pd.read_sql(
            "SELECT SUM(paid) as total FROM water_supply",
            conn
        )
        water_income = water_income_df['total'].iloc[0] or 0
        
        # Get other income from income table
        other_income = income_data['amount'].sum() if not income_data.empty else 0
        
        # Calculate totals
        total_income = livestock_income + crop_income + water_income + other_income
        
        # Display metrics
        col_i1, col_i2, col_i3, col_i4 = st.columns(4)
        
        with col_i1:
            st.metric("Livestock Income", f"PKR {livestock_income:,.0f}")
        with col_i2:
            st.metric("Crop Income", f"PKR {crop_income:,.0f}")
        with col_i3:
            st.metric("Water Supply Income", f"PKR {water_income:,.0f}")
        with col_i4:
            st.metric("Total Income", f"PKR {total_income:,.0f}")
        
        # Income by source chart
        income_by_source = pd.DataFrame({
            'Source': ['Livestock', 'Crops', 'Water Supply', 'Others'],
            'Amount': [livestock_income, crop_income, water_income, other_income]
        })
        
        if any(income_by_source['Amount']):
            fig = px.bar(income_by_source, x='Source', y='Amount',
                        title="Income by Source",
                        color='Source')
            st.plotly_chart(fig, use_container_width=True)
    
    # All Income Records
    st.markdown("### All Income Records")
    
    # Combine all income sources
    all_income_data = []
    
    # Add livestock income
    livestock_income_records = pd.read_sql(
        "SELECT date, category as source, amount, 'Livestock' as type FROM livestock WHERE transaction_type='income'",
        conn
    )
    if not livestock_income_records.empty:
        all_income_data.append(livestock_income_records)
    
    # Add crop income
    crop_income_records = pd.read_sql(
        "SELECT date, crop_type as source, amount, 'Crops' as type FROM crops WHERE transaction_type='income'",
        conn
    )
    if not crop_income_records.empty:
        all_income_data.append(crop_income_records)
    
    # Add water income
    water_income_records = pd.read_sql(
        "SELECT date, farmer_name as source, paid as amount, 'Water Supply' as type FROM water_supply WHERE paid > 0",
        conn
    )
    if not water_income_records.empty:
        all_income_data.append(water_income_records)
    
    # Add other income
    other_income_records = pd.read_sql(
        "SELECT date, source, amount, 'Other' as type FROM income",
        conn
    )
    if not other_income_records.empty:
        all_income_data.append(other_income_records)
    
    if all_income_data:
        combined_income = pd.concat(all_income_data, ignore_index=True)
        if not combined_income.empty:
            st.dataframe(combined_income, use_container_width=True, hide_index=True)
        else:
            st.info("No income records found.")
    else:
        st.info("No income records found.")

# ==================== REPORTS TAB ====================
with tabs[6]:
    conn = get_connection()
    
    st.markdown("## 📊 Comprehensive Reports")
    
    # Report Filters
    st.markdown("### Report Filters")
    
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    
    with col_r1:
        report_type = st.selectbox("Report Type", 
                                 ["Summary Report", "Livestock Report", "Crops Report", 
                                  "Water Report", "Expense Report", "Income Report", 
                                  "Balance Sheet"],
                                 key="report_type_select")
    
    with col_r2:
        category = st.selectbox("Category", 
                              ["All", "Livestock", "Crops", "Water Supply", "Expenses", "Income"],
                              key="report_category")
    
    with col_r3:
        date_from = st.date_input("From Date", value=None, key="report_date_from")
    
    with col_r4:
        date_to = st.date_input("To Date", value=None, key="report_date_to")
    
    # Generate Report Button
    if st.button("📈 Generate Report", type="primary", key="generate_report"):
        # Based on report type, generate different reports
        if report_type == "Summary Report":
            st.markdown("### 📋 Financial Summary Report")
            
            # Calculate summary statistics
            # Get all data
            livestock_df = pd.read_sql("SELECT * FROM livestock", conn)
            crops_df = pd.read_sql("SELECT * FROM crops", conn)
            water_df = pd.read_sql("SELECT * FROM water_supply", conn)
            expenses_df = pd.read_sql("SELECT * FROM expenses", conn)
            income_df = pd.read_sql("SELECT * FROM income", conn)
            
            # Apply date filters
            if date_from:
                livestock_df = livestock_df[livestock_df['date'] >= date_from]
                crops_df = crops_df[crops_df['date'] >= date_from]
                water_df = water_df[water_df['date'] >= date_from]
                expenses_df = expenses_df[expenses_df['date'] >= date_from]
                income_df = income_df[income_df['date'] >= date_from]
            
            if date_to:
                livestock_df = livestock_df[livestock_df['date'] <= date_to]
                crops_df = crops_df[crops_df['date'] <= date_to]
                water_df = water_df[water_df['date'] <= date_to]
                expenses_df = expenses_df[expenses_df['date'] <= date_to]
                income_df = income_df[income_df['date'] <= date_to]
            
            # Calculate totals
            total_livestock_income = livestock_df[livestock_df['transaction_type'] == 'income']['amount'].sum()
            total_livestock_expenses = livestock_df[livestock_df['transaction_type'] == 'expense']['amount'].sum()
            
            total_crop_income = crops_df[crops_df['transaction_type'] == 'income']['amount'].sum()
            total_crop_expenses = crops_df[crops_df['transaction_type'] == 'expense']['amount'].sum()
            
            total_water_income = water_df['paid'].sum()
            total_water_bill = water_df['total_bill'].sum()
            
            total_expenses = expenses_df['amount'].sum()
            total_other_income = income_df['amount'].sum()
            
            # Grand totals
            grand_total_income = total_livestock_income + total_crop_income + total_water_income + total_other_income
            grand_total_expense = total_livestock_expenses + total_crop_expenses + total_expenses
            net_balance = grand_total_income - grand_total_expense
            profit_margin = (net_balance / grand_total_income * 100) if grand_total_income > 0 else 0
            
            # Display summary
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                st.metric("Total Income", f"PKR {grand_total_income:,.0f}")
            with col_s2:
                st.metric("Total Expenses", f"PKR {grand_total_expense:,.0f}")
            with col_s3:
                st.metric("Net Balance", f"PKR {net_balance:,.0f}")
            with col_s4:
                st.metric("Profit Margin", f"{profit_margin:.1f}%")
            
            # Detailed breakdown
            st.markdown("#### Detailed Breakdown")
            
            breakdown_data = pd.DataFrame({
                'Category': ['Livestock Income', 'Livestock Expenses', 'Crop Income', 
                            'Crop Expenses', 'Water Supply Income', 'Water Supply Bill',
                            'Other Income', 'Other Expenses'],
                'Amount': [total_livestock_income, total_livestock_expenses,
                          total_crop_income, total_crop_expenses,
                          total_water_income, total_water_bill,
                          total_other_income, total_expenses]
            })
            
            st.dataframe(breakdown_data, use_container_width=True, hide_index=True)
            
            # Financial health assessment
            st.markdown("#### Financial Health Assessment")
            if net_balance > 0:
                st.success("✅ Good - Your farm is operating at a profit.")
            elif net_balance == 0:
                st.warning("⚠️  Break-even - Your income equals your expenses.")
            else:
                st.error("❌ Needs Improvement - Your expenses exceed your income.")
        
        elif report_type == "Livestock Report":
            st.markdown("### 🐄 Livestock Report")
            
            livestock_df = pd.read_sql("SELECT * FROM livestock", conn)
            
            if date_from:
                livestock_df = livestock_df[livestock_df['date'] >= date_from]
            if date_to:
                livestock_df = livestock_df[livestock_df['date'] <= date_to]
            
            if not livestock_df.empty:
                # Summary by category
                category_summary = livestock_df.groupby('category').agg({
                    'amount': 'sum',
                    'quantity': 'sum'
                }).reset_index()
                
                st.dataframe(category_summary, use_container_width=True, hide_index=True)
                
                # Chart
                if not category_summary.empty:
                    fig = px.bar(category_summary, x='category', y='amount',
                                title="Livestock Revenue by Category",
                                color='category')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detailed records
                st.dataframe(livestock_df, use_container_width=True, hide_index=True)
            else:
                st.info("No livestock records found for the selected period.")
        
        elif report_type == "Crops Report":
            st.markdown("### 🌾 Crops Report")
            
            crops_df = pd.read_sql("SELECT * FROM crops", conn)
            
            if date_from:
                crops_df = crops_df[crops_df['date'] >= date_from]
            if date_to:
                crops_df = crops_df[crops_df['date'] <= date_to]
            
            if not crops_df.empty:
                # Summary by crop type
                crop_summary = crops_df.groupby('crop_type').agg({
                    'amount': 'sum',
                    'area': 'sum'
                }).reset_index()
                
                st.dataframe(crop_summary, use_container_width=True, hide_index=True)
                
                # Chart
                if not crop_summary.empty:
                    fig = px.pie(crop_summary, values='amount', names='crop_type',
                                title="Crop Revenue Distribution")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detailed records
                st.dataframe(crops_df, use_container_width=True, hide_index=True)
            else:
                st.info("No crop records found for the selected period.")
        
        elif report_type == "Water Report":
            st.markdown("### 💧 Water Supply Report")
            
            water_df = pd.read_sql("SELECT * FROM water_supply", conn)
            
            if date_from:
                water_df = water_df[water_df['date'] >= date_from]
            if date_to:
                water_df = water_df[water_df['date'] <= date_to]
            
            if not water_df.empty:
                # Summary by farmer
                farmer_summary = water_df.groupby('farmer_name').agg({
                    'total_bill': 'sum',
                    'paid': 'sum',
                    'balance': 'sum',
                    'hours': 'sum'
                }).reset_index()
                
                st.dataframe(farmer_summary, use_container_width=True, hide_index=True)
                
                # Collection efficiency
                total_bill = water_df['total_bill'].sum()
                total_paid = water_df['paid'].sum()
                collection_rate = (total_paid / total_bill * 100) if total_bill > 0 else 0
                
                col_w1, col_w2, col_w3 = st.columns(3)
                with col_w1:
                    st.metric("Total Bill", f"PKR {total_bill:,.0f}")
                with col_w2:
                    st.metric("Total Collected", f"PKR {total_paid:,.0f}")
                with col_w3:
                    st.metric("Collection Rate", f"{collection_rate:.1f}%")
                
                # Detailed records
                st.dataframe(water_df, use_container_width=True, hide_index=True)
            else:
                st.info("No water supply records found for the selected period.")
        
        elif report_type == "Expense Report":
            st.markdown("### 💰 Expense Report")
            
            expenses_df = pd.read_sql("SELECT * FROM expenses", conn)
            
            if date_from:
                expenses_df = expenses_df[expenses_df['date'] >= date_from]
            if date_to:
                expenses_df = expenses_df[expenses_df['date'] <= date_to]
            
            if not expenses_df.empty:
                # Summary by category
                category_summary = expenses_df.groupby('category')['amount'].sum().reset_index()
                
                st.dataframe(category_summary, use_container_width=True, hide_index=True)
                
                # Chart
                if not category_summary.empty:
                    fig = px.bar(category_summary, x='category', y='amount',
                                title="Expenses by Category",
                                color='category')
                    st.plotly_chart(fig, use_container_width=True)
                
                # Detailed records
                st.dataframe(expenses_df, use_container_width=True, hide_index=True)
            else:
                st.info("No expense records found for the selected period.")
        
        elif report_type == "Income Report":
            st.markdown("### 💵 Income Report")
            
            # Get all income data
            income_sources = []
            
            # Livestock income
            livestock_income = pd.read_sql(
                "SELECT date, category as source, amount FROM livestock WHERE transaction_type='income'",
                conn
            )
            if not livestock_income.empty:
                income_sources.append(livestock_income)
            
            # Crop income
            crop_income = pd.read_sql(
                "SELECT date, crop_type as source, amount FROM crops WHERE transaction_type='income'",
                conn
            )
            if not crop_income.empty:
                income_sources.append(crop_income)
            
            # Water income
            water_income = pd.read_sql(
                "SELECT date, farmer_name as source, paid as amount FROM water_supply",
                conn
            )
            if not water_income.empty:
                income_sources.append(water_income)
            
            # Other income
            other_income = pd.read_sql(
                "SELECT date, source, amount FROM income",
                conn
            )
            if not other_income.empty:
                income_sources.append(other_income)
            
            if income_sources:
                combined_income = pd.concat(income_sources, ignore_index=True)
                
                if date_from:
                    combined_income = combined_income[combined_income['date'] >= date_from]
                if date_to:
                    combined_income = combined_income[combined_income['date'] <= date_to]
                
                if not combined_income.empty:
                    # Summary by source
                    source_summary = combined_income.groupby('source')['amount'].sum().reset_index()
                    
                    st.dataframe(source_summary, use_container_width=True, hide_index=True)
                    
                    # Chart
                    if not source_summary.empty:
                        fig = px.pie(source_summary, values='amount', names='source',
                                    title="Income by Source")
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Detailed records
                    st.dataframe(combined_income, use_container_width=True, hide_index=True)
                else:
                    st.info("No income records found for the selected period.")
            else:
                st.info("No income records found.")
        
        elif report_type == "Balance Sheet":
            st.markdown("### ⚖️ Balance Sheet")
            
            # Get all data
            livestock_df = pd.read_sql("SELECT * FROM livestock", conn)
            crops_df = pd.read_sql("SELECT * FROM crops", conn)
            water_df = pd.read_sql("SELECT * FROM water_supply", conn)
            expenses_df = pd.read_sql("SELECT * FROM expenses", conn)
            income_df = pd.read_sql("SELECT * FROM income", conn)
            
            # Apply date filters
            if date_from:
                livestock_df = livestock_df[livestock_df['date'] >= date_from]
                crops_df = crops_df[crops_df['date'] >= date_from]
                water_df = water_df[water_df['date'] >= date_from]
                expenses_df = expenses_df[expenses_df['date'] >= date_from]
                income_df = income_df[income_df['date'] >= date_from]
            
            if date_to:
                livestock_df = livestock_df[livestock_df['date'] <= date_to]
                crops_df = crops_df[crops_df['date'] <= date_to]
                water_df = water_df[water_df['date'] <= date_to]
                expenses_df = expenses_df[expenses_df['date'] <= date_to]
                income_df = income_df[income_df['date'] <= date_to]
            
            # Calculate assets (income)
            livestock_income = livestock_df[livestock_df['transaction_type'] == 'income']['amount'].sum()
            crop_income = crops_df[crops_df['transaction_type'] == 'income']['amount'].sum()
            water_income = water_df['paid'].sum()
            other_income = income_df['amount'].sum()
            total_assets = livestock_income + crop_income + water_income + other_income
            
            # Calculate liabilities (expenses)
            livestock_expenses = livestock_df[livestock_df['transaction_type'] == 'expense']['amount'].sum()
            crop_expenses = crops_df[crops_df['transaction_type'] == 'expense']['amount'].sum()
            other_expenses = expenses_df['amount'].sum()
            total_liabilities = livestock_expenses + crop_expenses + other_expenses
            
            # Calculate equity
            equity = total_assets - total_liabilities
            
            # Display balance sheet
            col_bs1, col_bs2 = st.columns(2)
            
            with col_bs1:
                st.markdown("#### Assets (Income)")
                assets_data = pd.DataFrame({
                    'Category': ['Livestock Sales', 'Crop Sales', 'Water Supply', 'Other Income'],
                    'Amount': [livestock_income, crop_income, water_income, other_income]
                })
                st.dataframe(assets_data, use_container_width=True, hide_index=True)
                st.metric("Total Assets", f"PKR {total_assets:,.0f}")
            
            with col_bs2:
                st.markdown("#### Liabilities (Expenses)")
                liabilities_data = pd.DataFrame({
                    'Category': ['Livestock Expenses', 'Crop Expenses', 'Other Expenses'],
                    'Amount': [livestock_expenses, crop_expenses, other_expenses]
                })
                st.dataframe(liabilities_data, use_container_width=True, hide_index=True)
                st.metric("Total Liabilities", f"PKR {total_liabilities:,.0f}")
            
            st.markdown("---")
            col_eq1, col_eq2, col_eq3 = st.columns(3)
            with col_eq2:
                delta_value = f"{(equity/total_assets*100 if total_assets > 0 else 0):.1f}%" if equity >= 0 else None
                st.metric("Owner's Equity", f"PKR {equity:,.0f}", delta=delta_value)
    
    # Export Options
    st.markdown("---")
    st.markdown("### Export Options")
    
    col_e1, col_e2, col_e3 = st.columns(3)
    
    with col_e1:
        if st.button("📥 Export to Excel", key="export_excel_report"):
            # Create Excel file with all data
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                # Write each table to a separate sheet
                for table_name in ['livestock', 'crops', 'water_supply', 'expenses', 'income']:
                    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                    if not df.empty:
                        df.to_excel(writer, sheet_name=table_name.capitalize(), index=False)
            
            st.download_button(
                label="Download Full Excel Report",
                data=buffer.getvalue(),
                file_name=f"farm_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_report"
            )
    
    with col_e2:
        if st.button("📄 Export to CSV", key="export_csv_report"):
            # Create a zip file with all CSV files
            import zipfile
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, 'w') as zip_file:
                for table_name in ['livestock', 'crops', 'water_supply', 'expenses', 'income']:
                    df = pd.read_sql(f"SELECT * FROM {table_name}", conn)
                    if not df.empty:
                        csv_buffer = io.StringIO()
                        df.to_csv(csv_buffer, index=False)
                        zip_file.writestr(f"{table_name}.csv", csv_buffer.getvalue())
            
            st.download_button(
                label="Download CSV Bundle",
                data=buffer.getvalue(),
                file_name=f"farm_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                key="download_csv_report"
            )
    
    with col_e3:
        if st.button("📊 Generate PDF Report", key="generate_pdf_report"):
            st.info("PDF generation feature would be implemented with reportlab or similar library.")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("## 🚜 Farm Management")
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    
    if st.button("🔄 Refresh All Data", key="refresh_data"):
        st.rerun()
    
    # Add Manager Form
    st.markdown("---")
    st.markdown("### 👥 Add Manager")
    
    with st.form(key="sidebar_manager_form"):
        manager_name = st.text_input("Manager Name", key="sidebar_manager_name")
        manager_phone = st.text_input("Phone Number", key="sidebar_manager_phone")
        manager_designation = st.text_input("Designation", key="sidebar_manager_designation")
        
        if st.form_submit_button("Add Manager", key="sidebar_add_manager"):
            if manager_name:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO managers (name, phone, designation)
                    VALUES (?, ?, ?)
                ''', (manager_name, manager_phone, manager_designation))
                conn.commit()
                st.success(f"Manager {manager_name} added!")
                st.rerun()
    
    # Add Farmer Form
    st.markdown("---")
    st.markdown("### 👨‍🌾 Add Farmer")
    
    with st.form(key="sidebar_farmer_form"):
        farmer_name = st.text_input("Farmer Name", key="sidebar_farmer_name")
        farmer_phone = st.text_input("Farmer Phone", key="sidebar_farmer_phone")
        farmer_address = st.text_area("Address", key="sidebar_farmer_address")
        
        if st.form_submit_button("Add Farmer", key="sidebar_add_farmer"):
            if farmer_name:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO farmers (name, phone, address)
                    VALUES (?, ?, ?)
                ''', (farmer_name, farmer_phone, farmer_address))
                conn.commit()
                st.success(f"Farmer {farmer_name} added!")
                st.rerun()
    
    # Database Stats
    st.markdown("---")
    st.markdown("### 📊 Database Statistics")
    
    conn = get_connection()
    
    try:
        # Count records in each table
        tables = ['livestock', 'crops', 'water_supply', 'expenses', 'income']
        for table in tables:
            count_df = pd.read_sql(f"SELECT COUNT(*) as count FROM {table}", conn)
            count = count_df['count'].iloc[0]
            st.write(f"**{table.capitalize()}:** {count} records")
    except:
        st.write("Database not initialized yet.")
    
    # Backup and Restore
    st.markdown("---")
    st.markdown("### 💾 Data Management")
    
    col_b1, col_b2 = st.columns(2)
    
    with col_b1:
        if st.button("💾 Backup", key="backup_db"):
            # Create backup of database
            import shutil
            shutil.copy2('farm_management.db', f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')
            st.success("Database backed up successfully!")
    
    with col_b2:
        uploaded_file = st.file_uploader("Restore", type=['db'], key="restore_db_upload")
        if uploaded_file is not None:
            if st.button("Restore Database", key="restore_db"):
                with open('farm_management.db', 'wb') as f:
                    f.write(uploaded_file.getbuffer())
                st.success("Database restored successfully!")
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; font-size: 0.9rem;">
    <p>🚜 Complete Farm Management System • Developed for Modern Agriculture • © 2024</p>
</div>
""", unsafe_allow_html=True)
