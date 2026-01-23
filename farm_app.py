import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import base64
import io
from PIL import Image
import json

# Page configuration
st.set_page_config(
    page_title="Complete Farm Management System",
    page_icon="🌾",
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
            date TEXT,
            category TEXT,
            quantity REAL,
            expense_type TEXT,
            amount REAL,
            manager TEXT,
            remarks TEXT,
            transaction_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crop table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            crop_type TEXT,
            area REAL,
            expense_type TEXT,
            amount REAL,
            manager TEXT,
            remarks TEXT,
            transaction_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Water supply table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_supply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT,
            farmer_phone TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            hours REAL,
            rate REAL,
            total_bill REAL,
            paid REAL,
            balance REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            category TEXT,
            description TEXT,
            amount REAL,
            manager TEXT,
            receipt_no TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Income table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS income (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            source TEXT,
            amount REAL,
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
            name TEXT,
            phone TEXT,
            designation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Farmers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Water payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT,
            amount REAL,
            payment_method TEXT,
            date TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add sample managers if table is empty
    cursor.execute("SELECT COUNT(*) FROM managers")
    if cursor.fetchone()[0] == 0:
        sample_managers = [
            ("Ali Khan", "0300-1234567", "Farm Manager"),
            ("Ahmed Raza", "0312-9876543", "Livestock Manager"),
            ("Usman Ali", "0333-4567890", "Crop Manager"),
            ("Bilal Ahmed", "0345-1122334", "Finance Manager")
        ]
        cursor.executemany("INSERT INTO managers (name, phone, designation) VALUES (?, ?, ?)", sample_managers)
    
    # Add sample farmers if table is empty
    cursor.execute("SELECT COUNT(*) FROM farmers")
    if cursor.fetchone()[0] == 0:
        sample_farmers = [
            ("Farmer 1", "0301-2345678", "Village A"),
            ("Farmer 2", "0302-3456789", "Village B"),
            ("Farmer 3", "0303-4567890", "Village C")
        ]
        cursor.executemany("INSERT INTO farmers (name, phone, address) VALUES (?, ?, ?)", sample_farmers)
    
    conn.commit()
    return conn

# Database connection
conn = init_database()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #34495e;
        margin-bottom: 1rem;
        font-weight: 600;
    }
    .card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
        border-left: 5px solid #3498db;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .status-success {
        background-color: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    .status-error {
        background-color: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1046/1046769.png", width=100)
    st.title("🌾 Farm Management")
    
    menu = st.selectbox("Navigation", [
        "📊 Dashboard",
        "🐄 Livestock Management",
        "🌱 Crop Management",
        "💧 Water Supply",
        "💰 Expenses",
        "💵 Income",
        "📈 Reports",
        "⚙️ Settings"
    ])
    
    st.divider()
    
    # Quick Stats in Sidebar
    today = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    
    # Today's income
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income WHERE date = ?", (today,))
    today_income = cursor.fetchone()[0]
    
    # Today's expenses
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?", (today,))
    today_expenses = cursor.fetchone()[0]
    
    st.metric("Today's Income", f"PKR {today_income:,.2f}")
    st.metric("Today's Expenses", f"PKR {today_expenses:,.2f}")
    
    st.divider()
    st.caption(f"System Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Dashboard
if menu == "📊 Dashboard":
    st.markdown("<h1 class='main-header'>🏡 Complete Farm Management System</h1>", unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income")
        total_income = cursor.fetchone()[0]
        st.metric("Total Income", f"PKR {total_income:,.2f}", delta="+12%")
    
    with col2:
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
        total_expenses = cursor.fetchone()[0]
        st.metric("Total Expenses", f"PKR {total_expenses:,.2f}", delta="-5%")
    
    with col3:
        net_balance = total_income - total_expenses
        st.metric("Net Balance", f"PKR {net_balance:,.2f}", 
                 delta_color="inverse" if net_balance < 0 else "normal")
    
    with col4:
        cursor.execute("SELECT COUNT(DISTINCT farmer_name) FROM water_supply")
        total_farmers = cursor.fetchone()[0]
        st.metric("Active Farmers", total_farmers, delta="+3")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h3 class='sub-header'>Income by Source</h3>", unsafe_allow_html=True)
        
        # Get income data
        cursor.execute("""
            SELECT source, SUM(amount) as total 
            FROM income 
            GROUP BY source 
            ORDER BY total DESC
        """)
        income_data = cursor.fetchall()
        
        if income_data:
            df_income = pd.DataFrame(income_data, columns=['Source', 'Amount'])
            fig = px.pie(df_income, values='Amount', names='Source', 
                        color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("<h3 class='sub-header'>Expense Trend</h3>", unsafe_allow_html=True)
        
        # Get expense trend
        cursor.execute("""
            SELECT date, SUM(amount) as daily_expense 
            FROM expenses 
            GROUP BY date 
            ORDER BY date DESC 
            LIMIT 30
        """)
        expense_trend = cursor.fetchall()
        
        if expense_trend:
            df_expense = pd.DataFrame(expense_trend, columns=['Date', 'Amount'])
            fig = px.line(df_expense, x='Date', y='Amount', markers=True,
                         title="Last 30 Days Expense Trend")
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent Transactions
    st.markdown("<h3 class='sub-header'>Recent Transactions</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Recent Income**")
        cursor.execute("""
            SELECT date, source, amount, received_by 
            FROM income 
            ORDER BY date DESC 
            LIMIT 5
        """)
        recent_income = cursor.fetchall()
        
        if recent_income:
            df_recent_income = pd.DataFrame(recent_income, 
                                          columns=['Date', 'Source', 'Amount', 'Received By'])
            st.dataframe(df_recent_income, use_container_width=True)
    
    with col2:
        st.markdown("**Recent Expenses**")
        cursor.execute("""
            SELECT date, category, amount, manager 
            FROM expenses 
            ORDER BY date DESC 
            LIMIT 5
        """)
        recent_expenses = cursor.fetchall()
        
        if recent_expenses:
            df_recent_expenses = pd.DataFrame(recent_expenses,
                                            columns=['Date', 'Category', 'Amount', 'Manager'])
            st.dataframe(df_recent_expenses, use_container_width=True)

# Livestock Management
elif menu == "🐄 Livestock Management":
    st.markdown("<h1 class='main-header'>🐄 Livestock Management</h1>", unsafe_allow_html=True)
    
    # Tabs for Livestock
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Record", "📊 View Records", "📈 Analysis", "📤 Import/Export"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Add Livestock Record</h3>", unsafe_allow_html=True)
        
        with st.form("livestock_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date *", datetime.now())
                category = st.selectbox("Category *", 
                                       ["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Sheep", "Buffalo", "Poultry", "Others"])
                quantity = st.number_input("Quantity", min_value=0.0, step=1.0, value=1.0)
                expense_type = st.selectbox("Expense Type", 
                                          ["Khal (کھل)", "Chokar (چوکر)", "Tori (ٹوری)", 
                                           "Ghaas/Fodder (گھاس)", "Medicine (دوائیں)", 
                                           "Vaccination (ٹیکہ)", "Labor", "Others"])
            
            with col2:
                amount = st.number_input("Amount (PKR) *", min_value=0.0, step=100.0)
                transaction_type = st.selectbox("Transaction Type *", ["Expense", "Income"])
                
                # Get managers
                cursor.execute("SELECT name FROM managers")
                managers = [m[0] for m in cursor.fetchall()]
                manager = st.selectbox("Managed By *", managers)
                
                remarks = st.text_area("Remarks")
            
            submitted = st.form_submit_button("💾 Save Record")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO livestock (date, category, quantity, expense_type, 
                                                 amount, manager, remarks, transaction_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (date.strftime("%Y-%m-%d"), category, quantity, expense_type, 
                             amount, manager, remarks, transaction_type))
                        conn.commit()
                        st.success("✅ Livestock record saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving record: {str(e)}")
    
    with tab2:
        st.markdown("<h3 class='sub-header'>Livestock Records</h3>", unsafe_allow_html=True)
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_category = st.selectbox("Filter by Category", 
                                         ["All"] + ["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Sheep", "Buffalo", "Poultry", "Others"])
        with col2:
            filter_type = st.selectbox("Filter by Transaction", ["All", "Expense", "Income"])
        with col3:
            start_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
            end_date = st.date_input("To Date", datetime.now())
        
        # Build query
        query = "SELECT * FROM livestock WHERE 1=1"
        params = []
        
        if filter_category != "All":
            query += " AND category = ?"
            params.append(filter_category)
        
        if filter_type != "All":
            query += " AND transaction_type = ?"
            params.append(filter_type)
        
        query += " AND date BETWEEN ? AND ?"
        params.extend([start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])
        
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        if records:
            df = pd.DataFrame(records, columns=['ID', 'Date', 'Category', 'Quantity', 
                                              'Expense Type', 'Amount', 'Manager', 
                                              'Remarks', 'Transaction Type', 'Created At'])
            
            # Display metrics
            total_expenses = df[df['Transaction Type'] == 'Expense']['Amount'].sum()
            total_income = df[df['Transaction Type'] == 'Income']['Amount'].sum()
            net_balance = total_income - total_expenses
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Expenses", f"PKR {total_expenses:,.2f}")
            with col2:
                st.metric("Total Income", f"PKR {total_income:,.2f}")
            with col3:
                st.metric("Net Balance", f"PKR {net_balance:,.2f}")
            
            # Display data
            st.dataframe(df, use_container_width=True)
            
            # Action buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Download as Excel"):
                    excel_buffer = io.BytesIO()
                    df.to_excel(excel_buffer, index=False)
                    excel_buffer.seek(0)
                    b64 = base64.b64encode(excel_buffer.read()).decode()
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="livestock_records.xlsx">Download Excel File</a>'
                    st.markdown(href, unsafe_allow_html=True)
            
            with col2:
                if st.button("🗑️ Delete Selected"):
                    selected_ids = st.multiselect("Select records to delete", df['ID'].tolist())
                    if st.button("Confirm Delete"):
                        for record_id in selected_ids:
                            cursor.execute("DELETE FROM livestock WHERE id = ?", (record_id,))
                        conn.commit()
                        st.success(f"Deleted {len(selected_ids)} records")
                        st.rerun()
        else:
            st.info("No records found for the selected filters")
    
    with tab3:
        st.markdown("<h3 class='sub-header'>Livestock Analysis</h3>", unsafe_allow_html=True)
        
        # Get data for analysis
        cursor.execute("""
            SELECT category, transaction_type, SUM(amount) as total_amount
            FROM livestock
            GROUP BY category, transaction_type
            ORDER BY total_amount DESC
        """)
        analysis_data = cursor.fetchall()
        
        if analysis_data:
            df_analysis = pd.DataFrame(analysis_data, columns=['Category', 'Type', 'Amount'])
            
            # Stacked bar chart
            fig = px.bar(df_analysis, x='Category', y='Amount', color='Type',
                        title="Livestock Expenses vs Income by Category",
                        color_discrete_map={'Expense': '#e74c3c', 'Income': '#27ae60'})
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly trend
            cursor.execute("""
                SELECT strftime('%Y-%m', date) as month, 
                       transaction_type,
                       SUM(amount) as total
                FROM livestock
                GROUP BY strftime('%Y-%m', date), transaction_type
                ORDER BY month
            """)
            monthly_data = cursor.fetchall()
            
            if monthly_data:
                df_monthly = pd.DataFrame(monthly_data, columns=['Month', 'Type', 'Amount'])
                fig2 = px.line(df_monthly, x='Month', y='Amount', color='Type',
                             title="Monthly Trend",
                             markers=True)
                st.plotly_chart(fig2, use_container_width=True)

# Crop Management (Updated as requested)
elif menu == "🌱 Crop Management":
    st.markdown("<h1 class='main-header'>🌱 Crop Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Add Record", "📊 View Records", "📈 Analysis"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Add Crop Record</h3>", unsafe_allow_html=True)
        
        with st.form("crop_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date *", datetime.now())
                # Updated crop types as requested
                crop_type = st.selectbox("Crop Type *", 
                                        ["Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)",
                                         "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", 
                                         "Fruits", "Pulses", "Others"])
                area = st.number_input("Area (acres)", min_value=0.0, step=0.1, value=1.0)
                # Updated expense types as requested (removed Irrigation, added Land Preparation)
                expense_type = st.selectbox("Expense Type", 
                                          ["Labor (مزدوری)", "Seeds (بیج)", "Fertilizer (کھاد)",
                                           "Spray (سپرے)", "Land Preparation", "Harvesting",
                                           "Transportation", "Storage", "Others"])
            
            with col2:
                amount = st.number_input("Amount (PKR) *", min_value=0.0, step=100.0)
                transaction_type = st.selectbox("Transaction Type *", ["Expense", "Income"])
                
                cursor.execute("SELECT name FROM managers")
                managers = [m[0] for m in cursor.fetchall()]
                manager = st.selectbox("Managed By *", managers)
                
                remarks = st.text_area("Remarks")
            
            submitted = st.form_submit_button("💾 Save Record")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO crops (date, crop_type, area, expense_type, 
                                             amount, manager, remarks, transaction_type)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (date.strftime("%Y-%m-%d"), crop_type, area, expense_type,
                             amount, manager, remarks, transaction_type))
                        conn.commit()
                        st.success("✅ Crop record saved successfully!")
                    except Exception as e:
                        st.error(f"Error saving record: {str(e)}")
    
    with tab2:
        st.markdown("<h3 class='sub-header'>Crop Records</h3>", unsafe_allow_html=True)
        
        # Display crop data
        cursor.execute("SELECT * FROM crops ORDER BY date DESC")
        crop_records = cursor.fetchall()
        
        if crop_records:
            df_crops = pd.DataFrame(crop_records, 
                                  columns=['ID', 'Date', 'Crop Type', 'Area', 
                                           'Expense Type', 'Amount', 'Manager', 
                                           'Remarks', 'Transaction Type', 'Created At'])
            
            # Calculate metrics
            total_area = df_crops['Area'].sum()
            total_expenses = df_crops[df_crops['Transaction Type'] == 'Expense']['Amount'].sum()
            total_income = df_crops[df_crops['Transaction Type'] == 'Income']['Amount'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Area", f"{total_area:,.2f} acres")
            with col2:
                st.metric("Crop Expenses", f"PKR {total_expenses:,.2f}")
            with col3:
                st.metric("Crop Income", f"PKR {total_income:,.2f}")
            
            st.dataframe(df_crops, use_container_width=True)

# Water Supply
elif menu == "💧 Water Supply":
    st.markdown("<h1 class='main-header'>💧 Water Supply Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["🚰 Add Supply", "👨‍🌾 Farmer Ledger", "💰 Payments", "📊 Records"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("<h3 class='sub-header'>Water Supply Details</h3>", unsafe_allow_html=True)
            
            farmer_name = st.text_input("Farmer Name *")
            farmer_phone = st.text_input("Phone Number")
            date = st.date_input("Date *", datetime.now())
            rate = st.number_input("Rate per Hour (PKR) *", min_value=0.0, value=500.0, step=50.0)
        
        with col2:
            st.markdown("<h3 class='sub-header'>Supply Timing</h3>", unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                start_time = st.time_input("Start Time", datetime.now().time())
            with col_b:
                end_time = st.time_input("End Time", (datetime.now() + timedelta(hours=2)).time())
            
            # Calculate hours
            if start_time and end_time:
                start_dt = datetime.combine(date, start_time)
                end_dt = datetime.combine(date, end_time)
                hours = (end_dt - start_dt).total_seconds() / 3600
                total_bill = hours * rate
                
                st.metric("Total Hours", f"{hours:.2f}")
                st.metric("Total Bill", f"PKR {total_bill:,.2f}")
        
        if st.button("💾 Save Water Supply Record"):
            if farmer_name and rate > 0:
                cursor.execute("""
                    INSERT INTO water_supply (farmer_name, farmer_phone, date, 
                                             start_time, end_time, hours, rate, 
                                             total_bill, paid, balance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (farmer_name, farmer_phone, date.strftime("%Y-%m-%d"),
                     start_time.strftime("%H:%M"), end_time.strftime("%H:%M"),
                     hours, rate, total_bill, 0, total_bill))
                conn.commit()
                st.success("✅ Water supply record saved successfully!")
            else:
                st.error("Please fill all required fields")
    
    with tab2:
        st.markdown("<h3 class='sub-header'>Farmer Ledger</h3>", unsafe_allow_html=True)
        
        cursor.execute("SELECT DISTINCT farmer_name FROM water_supply")
        farmers = [f[0] for f in cursor.fetchall()]
        
        selected_farmer = st.selectbox("Select Farmer", farmers)
        
        if selected_farmer:
            # Get all supplies for farmer
            cursor.execute("""
                SELECT date, hours, rate, total_bill, paid, balance
                FROM water_supply
                WHERE farmer_name = ?
                ORDER BY date DESC
            """, (selected_farmer,))
            supplies = cursor.fetchall()
            
            if supplies:
                df_supplies = pd.DataFrame(supplies,
                                         columns=['Date', 'Hours', 'Rate', 'Total Bill', 'Paid', 'Balance'])
                
                total_bill = df_supplies['Total Bill'].sum()
                total_paid = df_supplies['Paid'].sum()
                total_balance = total_bill - total_paid
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Bill", f"PKR {total_bill:,.2f}")
                with col2:
                    st.metric("Total Paid", f"PKR {total_paid:,.2f}")
                with col3:
                    st.metric("Outstanding", f"PKR {total_balance:,.2f}", 
                             delta_color="inverse" if total_balance > 0 else "normal")
                
                st.dataframe(df_supplies, use_container_width=True)

# Expenses Management (Updated as requested)
elif menu == "💰 Expenses":
    st.markdown("<h1 class='main-header'>💰 Expenses Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Add Expense", "📊 View Expenses", "📈 Analysis"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Add New Expense</h3>", unsafe_allow_html=True)
        
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date *", datetime.now())
                # Updated categories as requested
                category = st.selectbox("Category *", 
                                      ["Salary (تنخواہ)", "Machinery (مشینری)", 
                                       "Kitchen", "Construction",
                                       "Petrol", "Diesel", 
                                       "Electricity Bill", "Turbine Bill",
                                       "Maintenance (مرمت)", "Livestock Feed",
                                       "Crop Inputs", "Transport", "Others"])
                description = st.text_input("Description *")
                amount = st.number_input("Amount (PKR) *", min_value=0.0, step=100.0)
            
            with col2:
                cursor.execute("SELECT name FROM managers")
                managers = [m[0] for m in cursor.fetchall()]
                manager = st.selectbox("Managed By *", managers)
                
                receipt_no = st.text_input("Receipt No")
                remarks = st.text_area("Remarks")
            
            submitted = st.form_submit_button("💾 Save Expense")
            
            if submitted:
                if amount <= 0 or not description:
                    st.error("Please fill all required fields")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO expenses (date, category, description, amount, 
                                                manager, receipt_no, remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (date.strftime("%Y-%m-%d"), category, description, amount,
                             manager, receipt_no, remarks))
                        conn.commit()
                        st.success("✅ Expense recorded successfully!")
                    except Exception as e:
                        st.error(f"Error saving expense: {str(e)}")
    
    with tab2:
        st.markdown("<h3 class='sub-header'>All Expenses</h3>", unsafe_allow_html=True)
        
        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("To Date", datetime.now())
        
        # Category filter
        cursor.execute("SELECT DISTINCT category FROM expenses")
        categories = ["All"] + [c[0] for c in cursor.fetchall()]
        selected_category = st.selectbox("Filter by Category", categories)
        
        # Query with filters
        query = "SELECT * FROM expenses WHERE date BETWEEN ? AND ?"
        params = [start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")]
        
        if selected_category != "All":
            query += " AND category = ?"
            params.append(selected_category)
        
        query += " ORDER BY date DESC"
        
        cursor.execute(query, params)
        expenses = cursor.fetchall()
        
        if expenses:
            df_expenses = pd.DataFrame(expenses, 
                                     columns=['ID', 'Date', 'Category', 'Description',
                                              'Amount', 'Manager', 'Receipt No', 
                                              'Remarks', 'Created At'])
            
            total_amount = df_expenses['Amount'].sum()
            avg_amount = df_expenses['Amount'].mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Expenses", f"PKR {total_amount:,.2f}")
            with col2:
                st.metric("Average per Expense", f"PKR {avg_amount:,.2f}")
            with col3:
                st.metric("Number of Expenses", len(df_expenses))
            
            st.dataframe(df_expenses, use_container_width=True)
        else:
            st.info("No expenses found for the selected filters")

# Income Management (Updated as requested)
elif menu == "💵 Income":
    st.markdown("<h1 class='main-header'>💵 Income Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Add Income", "📊 View Income", "📈 Analysis"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Record New Income</h3>", unsafe_allow_html=True)
        
        with st.form("income_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date *", datetime.now())
                # Updated income sources as requested
                source = st.selectbox("Income Source *", 
                                    ["Livestock Sale", "Goats Sale", "Beef Sale", 
                                     "Cows Sale", "Milk Sale", "Crop Sale",
                                     "Water Supply", "Rental Income", 
                                     "Consultation", "Others"])
                amount = st.number_input("Amount (PKR) *", min_value=0.0, step=100.0)
                customer = st.text_input("Customer/Payer")
            
            with col2:
                cursor.execute("SELECT name FROM managers")
                managers = [m[0] for m in cursor.fetchall()]
                received_by = st.selectbox("Received By", ["None"] + managers)
                
                receipt_no = st.text_input("Receipt No")
                remarks = st.text_area("Remarks")
            
            submitted = st.form_submit_button("💾 Save Income")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    try:
                        cursor.execute("""
                            INSERT INTO income (date, source, amount, received_by, 
                                              customer, receipt_no, remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (date.strftime("%Y-%m-%d"), source, amount,
                             received_by if received_by != "None" else None,
                             customer, receipt_no, remarks))
                        conn.commit()
                        st.success("✅ Income recorded successfully!")
                    except Exception as e:
                        st.error(f"Error saving income: {str(e)}")
    
    with tab2:
        # Income analysis dashboard
        st.markdown("<h3 class='sub-header'>Income Dashboard</h3>", unsafe_allow_html=True)
        
        # Get income by source
        cursor.execute("""
            SELECT source, SUM(amount) as total_amount
            FROM income
            GROUP BY source
            ORDER BY total_amount DESC
        """)
        income_by_source = cursor.fetchall()
        
        if income_by_source:
            df_income = pd.DataFrame(income_by_source, columns=['Source', 'Amount'])
            
            # Create columns for metrics
            col1, col2, col3, col4 = st.columns(4)
            
            # Calculate specific income types
            livestock_income = df_income[df_income['Source'].str.contains('Livestock|Goats|Beef|Cows|Milk')]['Amount'].sum()
            crop_income = df_income[df_income['Source'].str.contains('Crop')]['Amount'].sum()
            water_income = df_income[df_income['Source'].str.contains('Water')]['Amount'].sum()
            total_income = df_income['Amount'].sum()
            
            with col1:
                st.metric("Livestock Income", f"PKR {livestock_income:,.2f}")
            with col2:
                st.metric("Crop Income", f"PKR {crop_income:,.2f}")
            with col3:
                st.metric("Water Income", f"PKR {water_income:,.2f}")
            with col4:
                st.metric("Total Income", f"PKR {total_income:,.2f}")
            
            # Bar chart
            fig = px.bar(df_income, x='Source', y='Amount',
                        title="Income by Source",
                        color='Amount',
                        color_continuous_scale='Viridis')
            st.plotly_chart(fig, use_container_width=True)
            
            # Display all income records
            cursor.execute("SELECT * FROM income ORDER BY date DESC")
            all_income = cursor.fetchall()
            
            if all_income:
                df_all_income = pd.DataFrame(all_income,
                                           columns=['ID', 'Date', 'Source', 'Amount',
                                                    'Received By', 'Customer', 
                                                    'Receipt No', 'Remarks', 'Created At'])
                st.dataframe(df_all_income, use_container_width=True)

# Reports (Updated as requested)
elif menu == "📈 Reports":
    st.markdown("<h1 class='main-header'>📈 Comprehensive Reports</h1>", unsafe_allow_html=True)
    
    # Report type selection
    report_type = st.selectbox("Select Report Type", 
                              ["Summary Report", "Livestock Report", "Crops Report", 
                               "Water Supply Report", "Expense Report", "Income Report",
                               "Manager Report", "Balance Sheet"])
    
    # Date range for all reports
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
    with col2:
        to_date = st.date_input("To Date", datetime.now())
    
    # Generate report button
    if st.button("📊 Generate Report"):
        if report_type == "Summary Report":
            st.markdown("<h3 class='sub-header'>Financial Summary Report</h3>", unsafe_allow_html=True)
            
            # Get all data
            cursor.execute("""
                SELECT 'Income' as type, source as category, amount, date 
                FROM income 
                WHERE date BETWEEN ? AND ?
                UNION ALL
                SELECT 'Expense' as type, category, amount, date 
                FROM expenses 
                WHERE date BETWEEN ? AND ?
            """, (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d"),
                  from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
            
            summary_data = cursor.fetchall()
            
            if summary_data:
                df_summary = pd.DataFrame(summary_data, columns=['Type', 'Category', 'Amount', 'Date'])
                
                # Calculate totals
                total_income = df_summary[df_summary['Type'] == 'Income']['Amount'].sum()
                total_expenses = df_summary[df_summary['Type'] == 'Expense']['Amount'].sum()
                net_profit = total_income - total_expenses
                profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
                
                # Display KPIs
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Income", f"PKR {total_income:,.2f}")
                with col2:
                    st.metric("Total Expenses", f"PKR {total_expenses:,.2f}")
                with col3:
                    st.metric("Net Profit", f"PKR {net_profit:,.2f}")
                with col4:
                    st.metric("Profit Margin", f"{profit_margin:.1f}%")
                
                # Detailed breakdown
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Income Breakdown**")
                    income_by_source = df_summary[df_summary['Type'] == 'Income'].groupby('Category')['Amount'].sum()
                    if not income_by_source.empty:
                        st.dataframe(income_by_source.reset_index())
                
                with col2:
                    st.markdown("**Expense Breakdown**")
                    expense_by_category = df_summary[df_summary['Type'] == 'Expense'].groupby('Category')['Amount'].sum()
                    if not expense_by_category.empty:
                        st.dataframe(expense_by_category.reset_index())
        
        elif report_type == "Livestock Report":
            st.markdown("<h3 class='sub-header'>Livestock Report</h3>", unsafe_allow_html=True)
            
            cursor.execute("""
                SELECT category, transaction_type, SUM(amount) as total_amount, 
                       SUM(quantity) as total_quantity
                FROM livestock 
                WHERE date BETWEEN ? AND ?
                GROUP BY category, transaction_type
                ORDER BY total_amount DESC
            """, (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
            
            livestock_data = cursor.fetchall()
            
            if livestock_data:
                df_livestock = pd.DataFrame(livestock_data, 
                                          columns=['Category', 'Type', 'Amount', 'Quantity'])
                
                # Display metrics
                total_animals = df_livestock['Quantity'].sum()
                livestock_income = df_livestock[df_livestock['Type'] == 'Income']['Amount'].sum()
                livestock_expenses = df_livestock[df_livestock['Type'] == 'Expense']['Amount'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Animals", f"{total_animals:,.0f}")
                with col2:
                    st.metric("Livestock Income", f"PKR {livestock_income:,.2f}")
                with col3:
                    st.metric("Livestock Expenses", f"PKR {livestock_expenses:,.2f}")
                
                st.dataframe(df_livestock, use_container_width=True)
        
        elif report_type == "Crops Report":
            st.markdown("<h3 class='sub-header'>Crops Report</h3>", unsafe_allow_html=True)
            
            cursor.execute("""
                SELECT crop_type, transaction_type, SUM(amount) as total_amount,
                       SUM(area) as total_area
                FROM crops
                WHERE date BETWEEN ? AND ?
                GROUP BY crop_type, transaction_type
                ORDER BY total_amount DESC
            """, (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
            
            crops_data = cursor.fetchall()
            
            if crops_data:
                df_crops = pd.DataFrame(crops_data,
                                      columns=['Crop Type', 'Type', 'Amount', 'Area'])
                
                total_area = df_crops['Area'].sum()
                crop_income = df_crops[df_crops['Type'] == 'Income']['Amount'].sum()
                crop_expenses = df_crops[df_crops['Type'] == 'Expense']['Amount'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Area", f"{total_area:,.2f} acres")
                with col2:
                    st.metric("Crop Income", f"PKR {crop_income:,.2f}")
                with col3:
                    st.metric("Crop Expenses", f"PKR {crop_expenses:,.2f}")
                
                st.dataframe(df_crops, use_container_width=True)
        
        elif report_type == "Water Supply Report":
            st.markdown("<h3 class='sub-header'>Water Supply Report</h3>", unsafe_allow_html=True)
            
            cursor.execute("""
                SELECT farmer_name, SUM(hours) as total_hours,
                       SUM(total_bill) as total_bill,
                       SUM(paid) as total_paid,
                       SUM(balance) as total_balance
                FROM water_supply
                WHERE date BETWEEN ? AND ?
                GROUP BY farmer_name
                ORDER BY total_bill DESC
            """, (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
            
            water_data = cursor.fetchall()
            
            if water_data:
                df_water = pd.DataFrame(water_data,
                                      columns=['Farmer', 'Total Hours', 'Total Bill', 
                                               'Total Paid', 'Outstanding'])
                
                total_hours = df_water['Total Hours'].sum()
                total_bill = df_water['Total Bill'].sum()
                total_paid = df_water['Total Paid'].sum()
                collection_rate = (total_paid / total_bill * 100) if total_bill > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Hours", f"{total_hours:,.2f}")
                with col2:
                    st.metric("Total Revenue", f"PKR {total_bill:,.2f}")
                with col3:
                    st.metric("Amount Collected", f"PKR {total_paid:,.2f}")
                with col4:
                    st.metric("Collection Rate", f"{collection_rate:.1f}%")
                
                st.dataframe(df_water, use_container_width=True)

# Settings
elif menu == "⚙️ Settings":
    st.markdown("<h1 class='main-header'>⚙️ System Settings</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👥 Managers", "👨‍🌾 Farmers", "⚙️ System"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Manage Managers</h3>", unsafe_allow_html=True)
        
        # Add new manager
        with st.form("manager_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Manager Name")
                phone = st.text_input("Phone Number")
            with col2:
                designation = st.text_input("Designation")
            
            if st.form_submit_button("➕ Add Manager"):
                if name and designation:
                    cursor.execute("INSERT INTO managers (name, phone, designation) VALUES (?, ?, ?)",
                                 (name, phone, designation))
                    conn.commit()
                    st.success("✅ Manager added successfully!")
                else:
                    st.error("Name and designation are required")
        
        # View managers
        cursor.execute("SELECT * FROM managers ORDER BY name")
        managers = cursor.fetchall()
        
        if managers:
            df_managers = pd.DataFrame(managers, columns=['ID', 'Name', 'Phone', 'Designation', 'Created'])
            st.dataframe(df_managers, use_container_width=True)
    
    with tab2:
        st.markdown("<h3 class='sub-header'>Manage Farmers</h3>", unsafe_allow_html=True)
        
        # Add new farmer
        with st.form("farmer_form"):
            col1, col2 = st.columns(2)
            with col1:
                farmer_name = st.text_input("Farmer Name")
                farmer_phone = st.text_input("Phone")
            with col2:
                farmer_address = st.text_input("Address")
            
            if st.form_submit_button("➕ Add Farmer"):
                if farmer_name:
                    cursor.execute("INSERT INTO farmers (name, phone, address) VALUES (?, ?, ?)",
                                 (farmer_name, farmer_phone, farmer_address))
                    conn.commit()
                    st.success("✅ Farmer added successfully!")
                else:
                    st.error("Farmer name is required")
        
        # View farmers
        cursor.execute("SELECT * FROM farmers ORDER BY name")
        farmers = cursor.fetchall()
        
        if farmers:
            df_farmers = pd.DataFrame(farmers, columns=['ID', 'Name', 'Phone', 'Address', 'Created'])
            st.dataframe(df_farmers, use_container_width=True)

# Export functionality
st.sidebar.markdown("---")
if st.sidebar.button("📥 Export All Data"):
    # Create Excel writer
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        # Export each table
        tables = ['livestock', 'crops', 'water_supply', 'expenses', 'income', 'managers', 'farmers']
        for table in tables:
            cursor.execute(f"SELECT * FROM {table}")
            data = cursor.fetchall()
            if data:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                df = pd.DataFrame(data, columns=columns)
                df.to_excel(writer, sheet_name=table, index=False)
    
    excel_buffer.seek(0)
    b64 = base64.b64encode(excel_buffer.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="farm_data_export.xlsx">Download Full Data Export</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

# Backup functionality
if st.sidebar.button("💾 Create Backup"):
    backup_data = {}
    tables = ['livestock', 'crops', 'water_supply', 'expenses', 'income', 'managers', 'farmers']
    
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        data = cursor.fetchall()
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        backup_data[table] = {
            'columns': columns,
            'data': data
        }
    
    backup_json = json.dumps(backup_data, default=str)
    b64 = base64.b64encode(backup_json.encode()).decode()
    href = f'<a href="data:application/json;base64,{b64}" download="farm_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">Download Backup</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

# Restore functionality
uploaded_file = st.sidebar.file_uploader("Restore from Backup", type=['json'])
if uploaded_file and st.sidebar.button("🔄 Restore Backup"):
    try:
        backup_data = json.load(uploaded_file)
        
        # Clear existing data
        for table in backup_data.keys():
            cursor.execute(f"DELETE FROM {table}")
        
        # Insert backup data
        for table, table_data in backup_data.items():
            columns = table_data['columns']
            data = table_data['data']
            
            if data:
                placeholders = ','.join(['?'] * len(columns))
                column_names = ','.join(columns)
                cursor.executemany(f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})", data)
        
        conn.commit()
        st.sidebar.success("✅ Backup restored successfully!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Error restoring backup: {str(e)}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("© 2024 Farm Management System v2.0")
st.sidebar.caption("Developed with ❤️ for Modern Farming")

# Close database connection when done
conn.close()
