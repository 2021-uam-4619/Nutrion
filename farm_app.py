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
import tempfile
import os
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="Complete Farm Management System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database with additional features
def init_database():
    conn = sqlite3.connect('farm_management.db', check_same_thread=False)
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            payment_status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            water_supply_id INTEGER,
            farmer_name TEXT,
            amount REAL,
            payment_method TEXT,
            date TEXT,
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (water_supply_id) REFERENCES water_supply(id)
        )
    ''')
    
    # Import logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS import_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT,
            filename TEXT,
            records_imported INTEGER,
            imported_by TEXT,
            import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    .dataframe-edit {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #dee2e6;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions for import/export
def create_template(table_name):
    """Create sample template for each table"""
    templates = {
        'livestock': pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'category': ['Cow (گائے)', 'Goat (بکری)'],
            'quantity': [5, 10],
            'expense_type': ['Ghaas/Fodder (گھاس)', 'Medicine (دوائیں)'],
            'amount': [5000, 2000],
            'manager': ['Ali Khan', 'Ahmed Raza'],
            'remarks': ['Monthly fodder purchase', 'Vaccination'],
            'transaction_type': ['Expense', 'Expense']
        }),
        'crops': pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'crop_type': ['Wheat (گندم)', 'Corn'],
            'area': [10.5, 5.2],
            'expense_type': ['Fertilizer (کھاد)', 'Land Preparation'],
            'amount': [15000, 8000],
            'manager': ['Usman Ali', 'Usman Ali'],
            'remarks': ['Urea fertilizer', 'Plowing charges'],
            'transaction_type': ['Expense', 'Expense']
        }),
        'expenses': pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'category': ['Petrol', 'Electricity Bill'],
            'description': ['Fuel for tractor', 'Monthly electricity bill'],
            'amount': [5000, 15000],
            'manager': ['Bilal Ahmed', 'Bilal Ahmed'],
            'receipt_no': ['PET-001', 'ELEC-001'],
            'remarks': ['Tractor fuel', 'Main farm electricity']
        }),
        'income': pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'source': ['Goats Sale', 'Cows Sale'],
            'amount': [25000, 50000],
            'received_by': ['Ali Khan', 'Ali Khan'],
            'customer': ['Customer A', 'Customer B'],
            'receipt_no': ['GOAT-001', 'COW-001'],
            'remarks': ['Goat sale', 'Cow sale']
        }),
        'water_supply': pd.DataFrame({
            'farmer_name': ['Farmer 1', 'Farmer 2'],
            'farmer_phone': ['0301-2345678', '0302-3456789'],
            'date': ['2024-01-15', '2024-01-16'],
            'start_time': ['08:00', '09:00'],
            'end_time': ['12:00', '13:00'],
            'rate': [500, 500],
            'paid': [2000, 2500],
            'remarks': ['Morning supply', 'Morning supply']
        })
    }
    return templates.get(table_name, pd.DataFrame())

def get_download_link(df, filename, text):
    """Generate download link for DataFrame"""
    towrite = BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'
    return href

def import_data(table_name, uploaded_file):
    """Import data from Excel file to database"""
    try:
        df = pd.read_excel(uploaded_file)
        
        # Validate required columns
        required_cols = {
            'livestock': ['date', 'category', 'amount', 'transaction_type'],
            'crops': ['date', 'crop_type', 'amount', 'transaction_type'],
            'expenses': ['date', 'category', 'description', 'amount'],
            'income': ['date', 'source', 'amount'],
            'water_supply': ['farmer_name', 'date', 'rate']
        }
        
        required = required_cols.get(table_name, [])
        missing = [col for col in required if col not in df.columns]
        
        if missing:
            return False, f"Missing required columns: {', '.join(missing)}"
        
        cursor = conn.cursor()
        records_imported = 0
        
        for _, row in df.iterrows():
            try:
                if table_name == 'livestock':
                    cursor.execute("""
                        INSERT INTO livestock (date, category, quantity, expense_type, 
                                             amount, manager, remarks, transaction_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get('date', '')),
                        str(row.get('category', '')),
                        float(row.get('quantity', 0)),
                        str(row.get('expense_type', '')),
                        float(row.get('amount', 0)),
                        str(row.get('manager', '')),
                        str(row.get('remarks', '')),
                        str(row.get('transaction_type', 'Expense'))
                    ))
                
                elif table_name == 'crops':
                    cursor.execute("""
                        INSERT INTO crops (date, crop_type, area, expense_type, 
                                         amount, manager, remarks, transaction_type)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get('date', '')),
                        str(row.get('crop_type', '')),
                        float(row.get('area', 0)),
                        str(row.get('expense_type', '')),
                        float(row.get('amount', 0)),
                        str(row.get('manager', '')),
                        str(row.get('remarks', '')),
                        str(row.get('transaction_type', 'Expense'))
                    ))
                
                elif table_name == 'expenses':
                    cursor.execute("""
                        INSERT INTO expenses (date, category, description, amount, 
                                            manager, receipt_no, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get('date', '')),
                        str(row.get('category', '')),
                        str(row.get('description', '')),
                        float(row.get('amount', 0)),
                        str(row.get('manager', '')),
                        str(row.get('receipt_no', '')),
                        str(row.get('remarks', ''))
                    ))
                
                elif table_name == 'income':
                    cursor.execute("""
                        INSERT INTO income (date, source, amount, received_by, 
                                          customer, receipt_no, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get('date', '')),
                        str(row.get('source', '')),
                        float(row.get('amount', 0)),
                        str(row.get('received_by', '')),
                        str(row.get('customer', '')),
                        str(row.get('receipt_no', '')),
                        str(row.get('remarks', ''))
                    ))
                
                elif table_name == 'water_supply':
                    # Calculate hours and bill for water supply
                    start_time = str(row.get('start_time', '08:00'))
                    end_time = str(row.get('end_time', '12:00'))
                    
                    # Parse times
                    try:
                        start_dt = datetime.strptime(start_time, '%H:%M')
                        end_dt = datetime.strptime(end_time, '%H:%M')
                        hours = (end_dt - start_dt).total_seconds() / 3600
                        if hours < 0:
                            hours += 24  # Handle overnight
                    except:
                        hours = 4.0  # Default 4 hours
                    
                    rate = float(row.get('rate', 500))
                    total_bill = hours * rate
                    paid = float(row.get('paid', 0))
                    
                    cursor.execute("""
                        INSERT INTO water_supply (farmer_name, farmer_phone, date, 
                                                 start_time, end_time, hours, rate, 
                                                 total_bill, paid, balance, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(row.get('farmer_name', '')),
                        str(row.get('farmer_phone', '')),
                        str(row.get('date', '')),
                        start_time,
                        end_time,
                        hours,
                        rate,
                        total_bill,
                        paid,
                        total_bill - paid,
                        str(row.get('remarks', ''))
                    ))
                
                records_imported += 1
                
            except Exception as e:
                st.warning(f"Error in row {records_imported + 1}: {str(e)}")
                continue
        
        # Log the import
        cursor.execute("""
            INSERT INTO import_logs (table_name, filename, records_imported, imported_by)
            VALUES (?, ?, ?, ?)
        """, (table_name, uploaded_file.name, records_imported, "User"))
        
        conn.commit()
        return True, f"Successfully imported {records_imported} records"
        
    except Exception as e:
        return False, f"Import error: {str(e)}"

def update_record(table_name, record_id, update_data):
    """Update a record in the database"""
    cursor = conn.cursor()
    
    try:
        if table_name == 'livestock':
            cursor.execute("""
                UPDATE livestock 
                SET date=?, category=?, quantity=?, expense_type=?, 
                    amount=?, manager=?, remarks=?, transaction_type=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                update_data['date'],
                update_data['category'],
                update_data['quantity'],
                update_data['expense_type'],
                update_data['amount'],
                update_data['manager'],
                update_data['remarks'],
                update_data['transaction_type'],
                record_id
            ))
        
        elif table_name == 'crops':
            cursor.execute("""
                UPDATE crops 
                SET date=?, crop_type=?, area=?, expense_type=?, 
                    amount=?, manager=?, remarks=?, transaction_type=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                update_data['date'],
                update_data['crop_type'],
                update_data['area'],
                update_data['expense_type'],
                update_data['amount'],
                update_data['manager'],
                update_data['remarks'],
                update_data['transaction_type'],
                record_id
            ))
        
        elif table_name == 'expenses':
            cursor.execute("""
                UPDATE expenses 
                SET date=?, category=?, description=?, amount=?, 
                    manager=?, receipt_no=?, remarks=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                update_data['date'],
                update_data['category'],
                update_data['description'],
                update_data['amount'],
                update_data['manager'],
                update_data['receipt_no'],
                update_data['remarks'],
                record_id
            ))
        
        elif table_name == 'income':
            cursor.execute("""
                UPDATE income 
                SET date=?, source=?, amount=?, received_by=?, 
                    customer=?, receipt_no=?, remarks=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                update_data['date'],
                update_data['source'],
                update_data['amount'],
                update_data['received_by'],
                update_data['customer'],
                update_data['receipt_no'],
                update_data['remarks'],
                record_id
            ))
        
        elif table_name == 'water_supply':
            # Recalculate bill if hours or rate changed
            if 'hours' in update_data and 'rate' in update_data:
                total_bill = update_data['hours'] * update_data['rate']
                update_data['total_bill'] = total_bill
                update_data['balance'] = total_bill - update_data.get('paid', 0)
            
            cursor.execute("""
                UPDATE water_supply 
                SET farmer_name=?, farmer_phone=?, date=?, 
                    start_time=?, end_time=?, hours=?, rate=?, 
                    total_bill=?, paid=?, balance=?, remarks=?,
                    updated_at=CURRENT_TIMESTAMP
                WHERE id=?
            """, (
                update_data['farmer_name'],
                update_data['farmer_phone'],
                update_data['date'],
                update_data.get('start_time', '08:00'),
                update_data.get('end_time', '12:00'),
                update_data.get('hours', 4),
                update_data.get('rate', 500),
                update_data.get('total_bill', 2000),
                update_data.get('paid', 0),
                update_data.get('balance', 2000),
                update_data.get('remarks', ''),
                record_id
            ))
        
        conn.commit()
        return True, "Record updated successfully"
        
    except Exception as e:
        return False, f"Update error: {str(e)}"

def delete_record(table_name, record_id):
    """Delete a record from the database"""
    cursor = conn.cursor()
    
    try:
        if table_name == 'livestock':
            cursor.execute("DELETE FROM livestock WHERE id=?", (record_id,))
        elif table_name == 'crops':
            cursor.execute("DELETE FROM crops WHERE id=?", (record_id,))
        elif table_name == 'expenses':
            cursor.execute("DELETE FROM expenses WHERE id=?", (record_id,))
        elif table_name == 'income':
            cursor.execute("DELETE FROM income WHERE id=?", (record_id,))
        elif table_name == 'water_supply':
            cursor.execute("DELETE FROM water_payments WHERE water_supply_id=?", (record_id,))
            cursor.execute("DELETE FROM water_supply WHERE id=?", (record_id,))
        
        conn.commit()
        return True, "Record deleted successfully"
        
    except Exception as e:
        return False, f"Delete error: {str(e)}"

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
    
    # Quick Stats
    today = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income WHERE date = ?", (today,))
    today_income = cursor.fetchone()[0]
    
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
    
    # Recent Imports
    st.markdown("<h3 class='sub-header'>Recent Imports</h3>", unsafe_allow_html=True)
    
    cursor.execute("""
        SELECT table_name, filename, records_imported, import_date
        FROM import_logs 
        ORDER BY import_date DESC 
        LIMIT 5
    """)
    recent_imports = cursor.fetchall()
    
    if recent_imports:
        df_imports = pd.DataFrame(recent_imports, 
                                columns=['Table', 'Filename', 'Records', 'Date'])
        st.dataframe(df_imports, use_container_width=True)

# Livestock Management with Import/Export and Edit/Delete
elif menu == "🐄 Livestock Management":
    st.markdown("<h1 class='main-header'>🐄 Livestock Management</h1>", unsafe_allow_html=True)
    
    # Tabs for Livestock
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Add Record", "📊 View/Edit Records", "📈 Analysis", "📤 Import", "📥 Export"])
    
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
                        cursor = conn.cursor()
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
        st.markdown("<h3 class='sub-header'>View & Edit Livestock Records</h3>", unsafe_allow_html=True)
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_category = st.selectbox("Filter by Category", 
                                         ["All"] + ["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Sheep", "Buffalo", "Poultry", "Others"])
        with col2:
            filter_type = st.selectbox("Filter by Transaction", ["All", "Expense", "Income"])
        with col3:
            start_date = st.date_input("From Date", datetime.now() - timedelta(days=30), key="livestock_start")
            end_date = st.date_input("To Date", datetime.now(), key="livestock_end")
        
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
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        if records:
            df = pd.DataFrame(records, columns=['ID', 'Date', 'Category', 'Quantity', 
                                              'Expense Type', 'Amount', 'Manager', 
                                              'Remarks', 'Transaction Type', 'Created At', 'Updated At'])
            
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
            
            # Edit/Delete functionality
            st.markdown("### Edit Records")
            selected_id = st.selectbox("Select Record to Edit", df['ID'].tolist(), key="livestock_edit")
            
            if selected_id:
                selected_record = df[df['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_livestock_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'), key=f"date_{selected_id}")
                        edit_category = st.selectbox("Category", 
                                                   ["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Sheep", "Buffalo", "Poultry", "Others"],
                                                   index=["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Sheep", "Buffalo", "Poultry", "Others"].index(selected_record['Category']) 
                                                   if selected_record['Category'] in ["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Sheep", "Buffalo", "Poultry", "Others"] else 0,
                                                   key=f"category_{selected_id}")
                        edit_quantity = st.number_input("Quantity", value=float(selected_record['Quantity']), key=f"qty_{selected_id}")
                        edit_expense_type = st.selectbox("Expense Type", 
                                                        ["Khal (کھل)", "Chokar (چوکر)", "Tori (ٹوری)", 
                                                         "Ghaas/Fodder (گھاس)", "Medicine (دوائیں)", 
                                                         "Vaccination (ٹیکہ)", "Labor", "Others"],
                                                        index=["Khal (کھل)", "Chokar (چوکر)", "Tori (ٹوری)", 
                                                               "Ghaas/Fodder (گھاس)", "Medicine (دوائیں)", 
                                                               "Vaccination (ٹیکہ)", "Labor", "Others"].index(selected_record['Expense Type']) 
                                                        if selected_record['Expense Type'] in ["Khal (کھل)", "Chokar (چوکر)", "Tori (ٹوری)", 
                                                                                              "Ghaas/Fodder (گھاس)", "Medicine (دوائیں)", 
                                                                                              "Vaccination (ٹیکہ)", "Labor", "Others"] else 0,
                                                        key=f"exp_{selected_id}")
                    
                    with col2:
                        edit_amount = st.number_input("Amount", value=float(selected_record['Amount']), key=f"amt_{selected_id}")
                        edit_transaction = st.selectbox("Transaction Type", ["Expense", "Income"],
                                                       index=0 if selected_record['Transaction Type'] == 'Expense' else 1,
                                                       key=f"trans_{selected_id}")
                        edit_manager = st.selectbox("Manager", managers,
                                                   index=managers.index(selected_record['Manager']) if selected_record['Manager'] in managers else 0,
                                                   key=f"mgr_{selected_id}")
                        edit_remarks = st.text_area("Remarks", value=selected_record['Remarks'], key=f"rem_{selected_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record")
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record")
                    
                    if update_btn:
                        update_data = {
                            'date': edit_date.strftime("%Y-%m-%d"),
                            'category': edit_category,
                            'quantity': edit_quantity,
                            'expense_type': edit_expense_type,
                            'amount': edit_amount,
                            'manager': edit_manager,
                            'remarks': edit_remarks,
                            'transaction_type': edit_transaction
                        }
                        success, message = update_record('livestock', selected_id, update_data)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_btn:
                        if st.checkbox("Confirm deletion", key=f"confirm_del_{selected_id}"):
                            success, message = delete_record('livestock', selected_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            
            # Display data
            st.markdown("### All Records")
            st.dataframe(df.drop(columns=['Created At', 'Updated At']), use_container_width=True)
        else:
            st.info("No records found for the selected filters")
    
    with tab4:  # Import Tab
        st.markdown("<h3 class='sub-header'>Import Livestock Data</h3>", unsafe_allow_html=True)
        
        # Sample template
        st.markdown("### Download Template")
        template_df = create_template('livestock')
        st.dataframe(template_df, use_container_width=True)
        
        # Download template
        st.markdown(get_download_link(template_df, "livestock_template.xlsx", "📥 Download Template"), unsafe_allow_html=True)
        
        # Upload data
        st.markdown("### Upload Data")
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'], key="livestock_upload")
        
        if uploaded_file:
            st.info(f"Uploaded file: {uploaded_file.name}")
            
            if st.button("Import Data"):
                with st.spinner("Importing data..."):
                    success, message = import_data('livestock', uploaded_file)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    with tab5:  # Export Tab
        st.markdown("<h3 class='sub-header'>Export Livestock Data</h3>", unsafe_allow_html=True)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox("Export Format", ["Excel", "CSV"])
        
        with col2:
            export_date = st.date_input("Export data from", datetime.now() - timedelta(days=365))
        
        if st.button("Generate Export"):
            cursor = conn.cursor()
            cursor.execute("""
                SELECT date, category, quantity, expense_type, amount, 
                       manager, remarks, transaction_type
                FROM livestock 
                WHERE date >= ?
                ORDER BY date DESC
            """, (export_date.strftime("%Y-%m-%d"),))
            
            export_data = cursor.fetchall()
            
            if export_data:
                df_export = pd.DataFrame(export_data, 
                                       columns=['Date', 'Category', 'Quantity', 'Expense Type', 
                                                'Amount', 'Manager', 'Remarks', 'Transaction Type'])
                
                if export_format == "Excel":
                    st.markdown(get_download_link(df_export, "livestock_export.xlsx", "📥 Download Excel"), 
                              unsafe_allow_html=True)
                else:
                    csv = df_export.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="livestock_export.csv">📥 Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
                
                st.dataframe(df_export, use_container_width=True)
            else:
                st.info("No data to export")

# Crop Management with Import/Export and Edit/Delete
elif menu == "🌱 Crop Management":
    st.markdown("<h1 class='main-header'>🌱 Crop Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Add Record", "📊 View/Edit", "📈 Analysis", "📤 Import", "📥 Export"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Add Crop Record</h3>", unsafe_allow_html=True)
        
        with st.form("crop_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date *", datetime.now(), key="crop_date")
                # Updated crop types as requested
                crop_type = st.selectbox("Crop Type *", 
                                        ["Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)",
                                         "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", 
                                         "Fruits", "Pulses", "Others"], key="crop_type")
                area = st.number_input("Area (acres)", min_value=0.0, step=0.1, value=1.0, key="crop_area")
                # Updated expense types as requested
                expense_type = st.selectbox("Expense Type", 
                                          ["Labor (مزدوری)", "Seeds (بیج)", "Fertilizer (کھاد)",
                                           "Spray (سپرے)", "Land Preparation", "Harvesting",
                                           "Transportation", "Storage", "Others"], key="crop_expense")
            
            with col2:
                amount = st.number_input("Amount (PKR) *", min_value=0.0, step=100.0, key="crop_amount")
                transaction_type = st.selectbox("Transaction Type *", ["Expense", "Income"], key="crop_trans")
                
                cursor.execute("SELECT name FROM managers")
                managers = [m[0] for m in cursor.fetchall()]
                manager = st.selectbox("Managed By *", managers, key="crop_manager")
                
                remarks = st.text_area("Remarks", key="crop_remarks")
            
            submitted = st.form_submit_button("💾 Save Record")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    try:
                        cursor = conn.cursor()
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
        st.markdown("<h3 class='sub-header'>View & Edit Crop Records</h3>", unsafe_allow_html=True)
        
        # Get all crop records
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crops ORDER BY date DESC")
        crop_records = cursor.fetchall()
        
        if crop_records:
            df_crops = pd.DataFrame(crop_records, 
                                  columns=['ID', 'Date', 'Crop Type', 'Area', 
                                           'Expense Type', 'Amount', 'Manager', 
                                           'Remarks', 'Transaction Type', 'Created At', 'Updated At'])
            
            # Edit/Delete functionality
            st.markdown("### Edit Records")
            selected_id = st.selectbox("Select Record to Edit", df_crops['ID'].tolist(), key="crop_edit")
            
            if selected_id:
                selected_record = df_crops[df_crops['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_crop_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'), key=f"cdate_{selected_id}")
                        edit_crop_type = st.selectbox("Crop Type", 
                                                     ["Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)",
                                                      "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", 
                                                      "Fruits", "Pulses", "Others"],
                                                     index=["Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)",
                                                            "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", 
                                                            "Fruits", "Pulses", "Others"].index(selected_record['Crop Type']) 
                                                     if selected_record['Crop Type'] in ["Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)",
                                                                                        "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", 
                                                                                        "Fruits", "Pulses", "Others"] else 0,
                                                     key=f"ctype_{selected_id}")
                        edit_area = st.number_input("Area (acres)", value=float(selected_record['Area']), key=f"area_{selected_id}")
                        edit_expense_type = st.selectbox("Expense Type", 
                                                        ["Labor (مزدوری)", "Seeds (بیج)", "Fertilizer (کھاد)",
                                                         "Spray (سپرے)", "Land Preparation", "Harvesting",
                                                         "Transportation", "Storage", "Others"],
                                                        index=["Labor (مزدوری)", "Seeds (بیج)", "Fertilizer (کھاد)",
                                                               "Spray (سپرے)", "Land Preparation", "Harvesting",
                                                               "Transportation", "Storage", "Others"].index(selected_record['Expense Type']) 
                                                        if selected_record['Expense Type'] in ["Labor (مزدوری)", "Seeds (بیج)", "Fertilizer (کھاد)",
                                                                                              "Spray (سپرے)", "Land Preparation", "Harvesting",
                                                                                              "Transportation", "Storage", "Others"] else 0,
                                                        key=f"cexp_{selected_id}")
                    
                    with col2:
                        edit_amount = st.number_input("Amount", value=float(selected_record['Amount']), key=f"camt_{selected_id}")
                        edit_transaction = st.selectbox("Transaction Type", ["Expense", "Income"],
                                                       index=0 if selected_record['Transaction Type'] == 'Expense' else 1,
                                                       key=f"ctrans_{selected_id}")
                        edit_manager = st.selectbox("Manager", managers,
                                                   index=managers.index(selected_record['Manager']) if selected_record['Manager'] in managers else 0,
                                                   key=f"cmgr_{selected_id}")
                        edit_remarks = st.text_area("Remarks", value=selected_record['Remarks'], key=f"crem_{selected_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record")
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record")
                    
                    if update_btn:
                        update_data = {
                            'date': edit_date.strftime("%Y-%m-%d"),
                            'crop_type': edit_crop_type,
                            'area': edit_area,
                            'expense_type': edit_expense_type,
                            'amount': edit_amount,
                            'manager': edit_manager,
                            'remarks': edit_remarks,
                            'transaction_type': edit_transaction
                        }
                        success, message = update_record('crops', selected_id, update_data)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_btn:
                        if st.checkbox("Confirm deletion", key=f"crop_confirm_del_{selected_id}"):
                            success, message = delete_record('crops', selected_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            
            # Display all records
            st.markdown("### All Crop Records")
            st.dataframe(df_crops.drop(columns=['Created At', 'Updated At']), use_container_width=True)
    
    with tab4:  # Import Tab for Crops
        st.markdown("<h3 class='sub-header'>Import Crop Data</h3>", unsafe_allow_html=True)
        
        # Sample template
        st.markdown("### Download Template")
        template_df = create_template('crops')
        st.dataframe(template_df, use_container_width=True)
        
        # Download template
        st.markdown(get_download_link(template_df, "crops_template.xlsx", "📥 Download Template"), unsafe_allow_html=True)
        
        # Upload data
        st.markdown("### Upload Data")
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'], key="crops_upload")
        
        if uploaded_file:
            st.info(f"Uploaded file: {uploaded_file.name}")
            
            if st.button("Import Data"):
                with st.spinner("Importing data..."):
                    success, message = import_data('crops', uploaded_file)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

# Expenses Management with Import/Export and Edit/Delete
elif menu == "💰 Expenses":
    st.markdown("<h1 class='main-header'>💰 Expenses Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Add Expense", "📊 View/Edit", "📈 Analysis", "📤 Import", "📥 Export"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Add New Expense</h3>", unsafe_allow_html=True)
        
        with st.form("expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date *", datetime.now(), key="exp_date")
                # Updated categories as requested
                category = st.selectbox("Category *", 
                                      ["Salary (تنخواہ)", "Machinery (مشینری)", 
                                       "Kitchen", "Construction",
                                       "Petrol", "Diesel", 
                                       "Electricity Bill", "Turbine Bill",
                                       "Maintenance (مرمت)", "Livestock Feed",
                                       "Crop Inputs", "Transport", "Others"], key="exp_category")
                description = st.text_input("Description *", key="exp_desc")
                amount = st.number_input("Amount (PKR) *", min_value=0.0, step=100.0, key="exp_amount")
            
            with col2:
                cursor.execute("SELECT name FROM managers")
                managers = [m[0] for m in cursor.fetchall()]
                manager = st.selectbox("Managed By *", managers, key="exp_manager")
                
                receipt_no = st.text_input("Receipt No", key="exp_receipt")
                remarks = st.text_area("Remarks", key="exp_remarks")
            
            submitted = st.form_submit_button("💾 Save Expense")
            
            if submitted:
                if amount <= 0 or not description:
                    st.error("Please fill all required fields")
                else:
                    try:
                        cursor = conn.cursor()
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
        st.markdown("<h3 class='sub-header'>View & Edit Expenses</h3>", unsafe_allow_html=True)
        
        # Get all expenses
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        expenses = cursor.fetchall()
        
        if expenses:
            df_expenses = pd.DataFrame(expenses, 
                                     columns=['ID', 'Date', 'Category', 'Description',
                                              'Amount', 'Manager', 'Receipt No', 
                                              'Remarks', 'Created At', 'Updated At'])
            
            # Edit/Delete functionality
            st.markdown("### Edit Records")
            selected_id = st.selectbox("Select Record to Edit", df_expenses['ID'].tolist(), key="exp_edit")
            
            if selected_id:
                selected_record = df_expenses[df_expenses['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_expense_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'), key=f"edate_{selected_id}")
                        edit_category = st.selectbox("Category", 
                                                    ["Salary (تنخواہ)", "Machinery (مشینری)", 
                                                     "Kitchen", "Construction",
                                                     "Petrol", "Diesel", 
                                                     "Electricity Bill", "Turbine Bill",
                                                     "Maintenance (مرمت)", "Livestock Feed",
                                                     "Crop Inputs", "Transport", "Others"],
                                                    index=["Salary (تنخواہ)", "Machinery (مشینری)", 
                                                           "Kitchen", "Construction",
                                                           "Petrol", "Diesel", 
                                                           "Electricity Bill", "Turbine Bill",
                                                           "Maintenance (مرمت)", "Livestock Feed",
                                                           "Crop Inputs", "Transport", "Others"].index(selected_record['Category']) 
                                                    if selected_record['Category'] in ["Salary (تنخواہ)", "Machinery (مشینری)", 
                                                                                      "Kitchen", "Construction",
                                                                                      "Petrol", "Diesel", 
                                                                                      "Electricity Bill", "Turbine Bill",
                                                                                      "Maintenance (مرمت)", "Livestock Feed",
                                                                                      "Crop Inputs", "Transport", "Others"] else 0,
                                                    key=f"ecat_{selected_id}")
                        edit_description = st.text_input("Description", value=selected_record['Description'], key=f"edesc_{selected_id}")
                        edit_amount = st.number_input("Amount", value=float(selected_record['Amount']), key=f"eamt_{selected_id}")
                    
                    with col2:
                        edit_manager = st.selectbox("Manager", managers,
                                                   index=managers.index(selected_record['Manager']) if selected_record['Manager'] in managers else 0,
                                                   key=f"emgr_{selected_id}")
                        edit_receipt = st.text_input("Receipt No", value=selected_record['Receipt No'], key=f"erec_{selected_id}")
                        edit_remarks = st.text_area("Remarks", value=selected_record['Remarks'], key=f"erem_{selected_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record")
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record")
                    
                    if update_btn:
                        update_data = {
                            'date': edit_date.strftime("%Y-%m-%d"),
                            'category': edit_category,
                            'description': edit_description,
                            'amount': edit_amount,
                            'manager': edit_manager,
                            'receipt_no': edit_receipt,
                            'remarks': edit_remarks
                        }
                        success, message = update_record('expenses', selected_id, update_data)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_btn:
                        if st.checkbox("Confirm deletion", key=f"exp_confirm_del_{selected_id}"):
                            success, message = delete_record('expenses', selected_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            
            # Display all records
            st.markdown("### All Expense Records")
            st.dataframe(df_expenses.drop(columns=['Created At', 'Updated At']), use_container_width=True)
    
    with tab4:  # Import Tab for Expenses
        st.markdown("<h3 class='sub-header'>Import Expenses Data</h3>", unsafe_allow_html=True)
        
        # Sample template
        st.markdown("### Download Template")
        template_df = create_template('expenses')
        st.dataframe(template_df, use_container_width=True)
        
        # Download template
        st.markdown(get_download_link(template_df, "expenses_template.xlsx", "📥 Download Template"), unsafe_allow_html=True)
        
        # Upload data
        st.markdown("### Upload Data")
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'], key="expenses_upload")
        
        if uploaded_file:
            st.info(f"Uploaded file: {uploaded_file.name}")
            
            if st.button("Import Data"):
                with st.spinner("Importing data..."):
                    success, message = import_data('expenses', uploaded_file)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

# Income Management with Import/Export and Edit/Delete
elif menu == "💵 Income":
    st.markdown("<h1 class='main-header'>💵 Income Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Add Income", "📊 View/Edit", "📈 Analysis", "📤 Import", "📥 Export"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Record New Income</h3>", unsafe_allow_html=True)
        
        with st.form("income_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("Date *", datetime.now(), key="inc_date")
                # Updated income sources as requested
                source = st.selectbox("Income Source *", 
                                    ["Livestock Sale", "Goats Sale", "Beef Sale", 
                                     "Cows Sale", "Milk Sale", "Crop Sale",
                                     "Water Supply", "Rental Income", 
                                     "Consultation", "Others"], key="inc_source")
                amount = st.number_input("Amount (PKR) *", min_value=0.0, step=100.0, key="inc_amount")
                customer = st.text_input("Customer/Payer", key="inc_customer")
            
            with col2:
                cursor.execute("SELECT name FROM managers")
                managers = [m[0] for m in cursor.fetchall()]
                received_by = st.selectbox("Received By", ["None"] + managers, key="inc_received")
                
                receipt_no = st.text_input("Receipt No", key="inc_receipt")
                remarks = st.text_area("Remarks", key="inc_remarks")
            
            submitted = st.form_submit_button("💾 Save Income")
            
            if submitted:
                if amount <= 0:
                    st.error("Amount must be greater than 0")
                else:
                    try:
                        cursor = conn.cursor()
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
        st.markdown("<h3 class='sub-header'>View & Edit Income Records</h3>", unsafe_allow_html=True)
        
        # Get all income records
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM income ORDER BY date DESC")
        income_records = cursor.fetchall()
        
        if income_records:
            df_income = pd.DataFrame(income_records,
                                   columns=['ID', 'Date', 'Source', 'Amount',
                                            'Received By', 'Customer', 
                                            'Receipt No', 'Remarks', 'Created At', 'Updated At'])
            
            # Edit/Delete functionality
            st.markdown("### Edit Records")
            selected_id = st.selectbox("Select Record to Edit", df_income['ID'].tolist(), key="inc_edit")
            
            if selected_id:
                selected_record = df_income[df_income['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_income_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'), key=f"idate_{selected_id}")
                        edit_source = st.selectbox("Source", 
                                                  ["Livestock Sale", "Goats Sale", "Beef Sale", 
                                                   "Cows Sale", "Milk Sale", "Crop Sale",
                                                   "Water Supply", "Rental Income", 
                                                   "Consultation", "Others"],
                                                  index=["Livestock Sale", "Goats Sale", "Beef Sale", 
                                                         "Cows Sale", "Milk Sale", "Crop Sale",
                                                         "Water Supply", "Rental Income", 
                                                         "Consultation", "Others"].index(selected_record['Source']) 
                                                  if selected_record['Source'] in ["Livestock Sale", "Goats Sale", "Beef Sale", 
                                                                                  "Cows Sale", "Milk Sale", "Crop Sale",
                                                                                  "Water Supply", "Rental Income", 
                                                                                  "Consultation", "Others"] else 0,
                                                  key=f"isrc_{selected_id}")
                        edit_amount = st.number_input("Amount", value=float(selected_record['Amount']), key=f"iamt_{selected_id}")
                        edit_customer = st.text_input("Customer", value=selected_record['Customer'], key=f"icust_{selected_id}")
                    
                    with col2:
                        edit_received = st.selectbox("Received By", ["None"] + managers,
                                                    index=0 if selected_record['Received By'] is None else 
                                                    (managers.index(selected_record['Received By']) + 1 
                                                     if selected_record['Received By'] in managers else 0),
                                                    key=f"irec_{selected_id}")
                        edit_receipt = st.text_input("Receipt No", value=selected_record['Receipt No'], key=f"irecno_{selected_id}")
                        edit_remarks = st.text_area("Remarks", value=selected_record['Remarks'], key=f"irem_{selected_id}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record")
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record")
                    
                    if update_btn:
                        update_data = {
                            'date': edit_date.strftime("%Y-%m-%d"),
                            'source': edit_source,
                            'amount': edit_amount,
                            'received_by': edit_received if edit_received != "None" else None,
                            'customer': edit_customer,
                            'receipt_no': edit_receipt,
                            'remarks': edit_remarks
                        }
                        success, message = update_record('income', selected_id, update_data)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_btn:
                        if st.checkbox("Confirm deletion", key=f"inc_confirm_del_{selected_id}"):
                            success, message = delete_record('income', selected_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            
            # Display all records
            st.markdown("### All Income Records")
            st.dataframe(df_income.drop(columns=['Created At', 'Updated At']), use_container_width=True)
    
    with tab4:  # Import Tab for Income
        st.markdown("<h3 class='sub-header'>Import Income Data</h3>", unsafe_allow_html=True)
        
        # Sample template
        st.markdown("### Download Template")
        template_df = create_template('income')
        st.dataframe(template_df, use_container_width=True)
        
        # Download template
        st.markdown(get_download_link(template_df, "income_template.xlsx", "📥 Download Template"), unsafe_allow_html=True)
        
        # Upload data
        st.markdown("### Upload Data")
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'], key="income_upload")
        
        if uploaded_file:
            st.info(f"Uploaded file: {uploaded_file.name}")
            
            if st.button("Import Data"):
                with st.spinner("Importing data..."):
                    success, message = import_data('income', uploaded_file)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

# Water Supply Management with Import/Export and Edit/Delete
elif menu == "💧 Water Supply":
    st.markdown("<h1 class='main-header'>💧 Water Supply Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🚰 Add Supply", "📊 View/Edit", "💰 Payments", "📤 Import", "📥 Export"])
    
    with tab1:
        st.markdown("<h3 class='sub-header'>Water Supply Details</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            farmer_name = st.text_input("Farmer Name *", key="water_farmer")
            farmer_phone = st.text_input("Phone Number", key="water_phone")
            date = st.date_input("Date *", datetime.now(), key="water_date")
            rate = st.number_input("Rate per Hour (PKR) *", min_value=0.0, value=500.0, step=50.0, key="water_rate")
        
        with col2:
            st.markdown("<h3 class='sub-header'>Supply Timing</h3>", unsafe_allow_html=True)
            
            col_a, col_b = st.columns(2)
            with col_a:
                start_time = st.time_input("Start Time", datetime.now().time(), key="water_start")
            with col_b:
                end_time = st.time_input("End Time", (datetime.now() + timedelta(hours=2)).time(), key="water_end")
            
            # Calculate hours
            if start_time and end_time:
                start_dt = datetime.combine(date, start_time)
                end_dt = datetime.combine(date, end_time)
                hours = (end_dt - start_dt).total_seconds() / 3600
                if hours < 0:
                    hours += 24  # Handle overnight
                total_bill = hours * rate
                
                st.metric("Total Hours", f"{hours:.2f}")
                st.metric("Total Bill", f"PKR {total_bill:,.2f}")
        
        remarks = st.text_area("Remarks", key="water_remarks")
        
        if st.button("💾 Save Water Supply Record"):
            if farmer_name and rate > 0:
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO water_supply (farmer_name, farmer_phone, date, 
                                                 start_time, end_time, hours, rate, 
                                                 total_bill, paid, balance, remarks)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (farmer_name, farmer_phone, date.strftime("%Y-%m-%d"),
                         start_time.strftime("%H:%M"), end_time.strftime("%H:%M"),
                         hours, rate, total_bill, 0, total_bill, remarks))
                    conn.commit()
                    st.success("✅ Water supply record saved successfully!")
                except Exception as e:
                    st.error(f"Error saving record: {str(e)}")
            else:
                st.error("Please fill all required fields")
    
    with tab2:
        st.markdown("<h3 class='sub-header'>View & Edit Water Supply Records</h3>", unsafe_allow_html=True)
        
        # Get all water supply records
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM water_supply ORDER BY date DESC")
        water_records = cursor.fetchall()
        
        if water_records:
            df_water = pd.DataFrame(water_records,
                                  columns=['ID', 'Farmer Name', 'Phone', 'Date', 
                                           'Start Time', 'End Time', 'Hours', 'Rate',
                                           'Total Bill', 'Paid', 'Balance', 'Status',
                                           'Created At', 'Updated At'])
            
            # Edit/Delete functionality
            st.markdown("### Edit Records")
            selected_id = st.selectbox("Select Record to Edit", df_water['ID'].tolist(), key="water_edit")
            
            if selected_id:
                selected_record = df_water[df_water['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_water_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_farmer = st.text_input("Farmer Name", value=selected_record['Farmer Name'], key=f"wf_{selected_id}")
                        edit_phone = st.text_input("Phone", value=selected_record['Phone'], key=f"wp_{selected_id}")
                        edit_date = st.date_input("Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'), key=f"wd_{selected_id}")
                        edit_rate = st.number_input("Rate", value=float(selected_record['Rate']), key=f"wr_{selected_id}")
                    
                    with col2:
                        edit_start = st.time_input("Start Time", datetime.strptime(selected_record['Start Time'], '%H:%M').time(), key=f"ws_{selected_id}")
                        edit_end = st.time_input("End Time", datetime.strptime(selected_record['End Time'], '%H:%M').time(), key=f"we_{selected_id}")
                        edit_paid = st.number_input("Paid Amount", value=float(selected_record['Paid']), key=f"wpd_{selected_id}")
                        edit_remarks = st.text_area("Remarks", value=selected_record.get('Remarks', ''), key=f"wrem_{selected_id}")
                    
                    # Calculate new values
                    start_dt = datetime.combine(edit_date, edit_start)
                    end_dt = datetime.combine(edit_date, edit_end)
                    edit_hours = (end_dt - start_dt).total_seconds() / 3600
                    if edit_hours < 0:
                        edit_hours += 24
                    edit_total = edit_hours * edit_rate
                    edit_balance = edit_total - edit_paid
                    
                    st.info(f"Hours: {edit_hours:.2f}, Total Bill: PKR {edit_total:,.2f}, Balance: PKR {edit_balance:,.2f}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record")
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record")
                    
                    if update_btn:
                        update_data = {
                            'farmer_name': edit_farmer,
                            'farmer_phone': edit_phone,
                            'date': edit_date.strftime("%Y-%m-%d"),
                            'start_time': edit_start.strftime("%H:%M"),
                            'end_time': edit_end.strftime("%H:%M"),
                            'hours': edit_hours,
                            'rate': edit_rate,
                            'total_bill': edit_total,
                            'paid': edit_paid,
                            'balance': edit_balance,
                            'remarks': edit_remarks
                        }
                        success, message = update_record('water_supply', selected_id, update_data)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    
                    if delete_btn:
                        if st.checkbox("Confirm deletion", key=f"water_confirm_del_{selected_id}"):
                            success, message = delete_record('water_supply', selected_id)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
            
            # Display all records
            st.markdown("### All Water Supply Records")
            st.dataframe(df_water.drop(columns=['Created At', 'Updated At']), use_container_width=True)
    
    with tab4:  # Import Tab for Water Supply
        st.markdown("<h3 class='sub-header'>Import Water Supply Data</h3>", unsafe_allow_html=True)
        
        # Sample template
        st.markdown("### Download Template")
        template_df = create_template('water_supply')
        st.dataframe(template_df, use_container_width=True)
        
        # Download template
        st.markdown(get_download_link(template_df, "water_supply_template.xlsx", "📥 Download Template"), unsafe_allow_html=True)
        
        # Upload data
        st.markdown("### Upload Data")
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'], key="water_upload")
        
        if uploaded_file:
            st.info(f"Uploaded file: {uploaded_file.name}")
            
            if st.button("Import Data"):
                with st.spinner("Importing data..."):
                    success, message = import_data('water_supply', uploaded_file)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

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
            cursor = conn.cursor()
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
        
        elif report_type == "Livestock Report":
            st.markdown("<h3 class='sub-header'>Livestock Report</h3>", unsafe_allow_html=True)
            
            cursor = conn.cursor()
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
            
            cursor = conn.cursor()
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
            
            cursor = conn.cursor()
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
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Managers", "👨‍🌾 Farmers", "📋 Import Logs", "⚙️ System"])
    
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
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO managers (name, phone, designation) VALUES (?, ?, ?)",
                                 (name, phone, designation))
                    conn.commit()
                    st.success("✅ Manager added successfully!")
                else:
                    st.error("Name and designation are required")
        
        # View and delete managers
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM managers ORDER BY name")
        managers = cursor.fetchall()
        
        if managers:
            df_managers = pd.DataFrame(managers, columns=['ID', 'Name', 'Phone', 'Designation', 'Created'])
            st.dataframe(df_managers, use_container_width=True)
            
            # Delete manager
            manager_id = st.selectbox("Select Manager to Delete", df_managers['ID'].tolist())
            if st.button("Delete Manager"):
                cursor.execute("DELETE FROM managers WHERE id=?", (manager_id,))
                conn.commit()
                st.success("Manager deleted successfully!")
                st.rerun()
    
    with tab3:
        st.markdown("<h3 class='sub-header'>Import Logs</h3>", unsafe_allow_html=True)
        
        cursor = conn.cursor()
        cursor.execute("""
            SELECT table_name, filename, records_imported, imported_by, import_date
            FROM import_logs 
            ORDER BY import_date DESC
        """)
        import_logs = cursor.fetchall()
        
        if import_logs:
            df_logs = pd.DataFrame(import_logs, 
                                 columns=['Table', 'Filename', 'Records', 'Imported By', 'Date'])
            st.dataframe(df_logs, use_container_width=True)
            
            # Export logs
            if st.button("Export Import Logs"):
                st.markdown(get_download_link(df_logs, "import_logs.xlsx", "📥 Download Import Logs"), 
                          unsafe_allow_html=True)

# Export All Data
st.sidebar.markdown("---")
if st.sidebar.button("📥 Export All Data"):
    # Create Excel writer
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
        # Export each table
        tables = ['livestock', 'crops', 'water_supply', 'expenses', 'income', 'managers', 'farmers']
        for table in tables:
            cursor = conn.cursor()
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
        cursor = conn.cursor()
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
            cursor = conn.cursor()
            cursor.execute(f"DELETE FROM {table}")
        
        # Insert backup data
        for table, table_data in backup_data.items():
            columns = table_data['columns']
            data = table_data['data']
            
            if data:
                placeholders = ','.join(['?'] * len(columns))
                column_names = ','.join(columns)
                cursor = conn.cursor()
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

# Session state for storing data
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

# Run the app
if __name__ == "__main__":
    # Keep database connection open
    pass
