import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import json
import time
import os
from io import BytesIO
import base64
import plotly.graph_objects as go
import plotly.express as px
from PIL import Image
import warnings
warnings.filterwarnings('ignore')

# Set page config
st.set_page_config(
    page_title="Complete Farm Management System",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match the original design
def load_css():
    st.markdown("""
    <style>
    /* Main Container */
    .main-container {
        max-width: 1600px;
        margin: 0 auto;
        background: white;
        border-radius: 15px;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
        overflow: hidden;
    }
    
    /* Header */
    .header {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        color: white;
        padding: 25px;
        text-align: center;
        border-bottom: 5px solid #27ae60;
        position: relative;
        overflow: hidden;
    }
    
    .header h1 {
        font-size: 2.8rem;
        margin-bottom: 10px;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    
    .header .subtitle {
        font-size: 1.3rem;
        opacity: 0.95;
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #34495e;
        padding: 5px;
        border-radius: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #2c3e50;
        border-radius: 5px 5px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        color: white !important;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #27ae60 !important;
        color: white !important;
    }
    
    /* Cards */
    .section-card {
        background: white;
        border-radius: 12px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
        border-left: 5px solid #3498db;
    }
    
    .section-card h3 {
        color: #2c3e50;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #ecf0f1;
        font-size: 1.5rem;
        font-weight: 700;
    }
    
    /* Form Elements */
    .stTextInput>div>div>input, .stNumberInput>div>div>input,
    .stSelectbox>div>div>select, .stTextArea>div>textarea {
        border: 2px solid #ddd;
        border-radius: 6px;
        padding: 10px;
    }
    
    .stButton>button {
        padding: 12px 25px;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        transition: all 0.3s ease;
    }
    
    /* Tables */
    .data-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 20px;
        background: white;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    .data-table th {
        background: linear-gradient(135deg, #2c3e50, #34495e);
        color: white;
        padding: 15px;
        text-align: left;
        font-weight: 600;
    }
    
    .data-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #eee;
    }
    
    /* Dashboard Cards */
    .dashboard-card {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        padding: 25px;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
        text-align: center;
        border-top: 4px solid #3498db;
    }
    
    .dashboard-card .value {
        font-size: 2.8rem;
        font-weight: 800;
        color: #27ae60;
        margin: 15px 0;
    }
    
    /* Timer */
    .timer-display {
        font-size: 3.5rem;
        font-weight: bold;
        color: #2c3e50;
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        padding: 25px;
        border-radius: 12px;
        text-align: center;
        border: 3px solid #3498db;
    }
    
    /* Status Messages */
    .status-success {
        padding: 15px 20px;
        border-radius: 8px;
        margin: 15px 0;
        background: linear-gradient(135deg, #d4edda, #c3e6cb);
        color: #155724;
        border: 1px solid #b1dfbb;
    }
    
    .status-error {
        padding: 15px 20px;
        border-radius: 8px;
        margin: 15px 0;
        background: linear-gradient(135deg, #f8d7da, #f5c6cb);
        color: #721c24;
        border: 1px solid #f1b0b7;
    }
    
    /* Ledger */
    .ledger-container {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        margin-top: 20px;
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #dee2e6;
    }
    
    .ledger-entry {
        display: flex;
        justify-content: space-between;
        padding: 12px 15px;
        border-bottom: 1px solid #ddd;
    }
    
    .ledger-entry.debit {
        border-left: 4px solid #e74c3c;
        background: linear-gradient(90deg, rgba(231, 76, 60, 0.05), transparent);
    }
    
    .ledger-entry.credit {
        border-left: 4px solid #27ae60;
        background: linear-gradient(90deg, rgba(39, 174, 96, 0.05), transparent);
    }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    # Data storage
    if 'livestock_data' not in st.session_state:
        st.session_state.livestock_data = pd.DataFrame(columns=[
            'id', 'date', 'category', 'expense_type', 'quantity', 
            'amount', 'manager', 'remarks', 'transaction_type'
        ])
    
    if 'crop_data' not in st.session_state:
        st.session_state.crop_data = pd.DataFrame(columns=[
            'id', 'date', 'crop_type', 'area', 'expense_type',
            'amount', 'manager', 'remarks', 'transaction_type'
        ])
    
    if 'water_supply_data' not in st.session_state:
        st.session_state.water_supply_data = pd.DataFrame(columns=[
            'id', 'farmer_name', 'farmer_phone', 'start_time', 'end_time',
            'hours', 'rate', 'total_bill', 'paid', 'balance', 'date'
        ])
    
    if 'expenses_data' not in st.session_state:
        st.session_state.expenses_data = pd.DataFrame(columns=[
            'id', 'date', 'category', 'description', 'amount',
            'manager', 'receipt_no', 'remarks'
        ])
    
    if 'income_data' not in st.session_state:
        st.session_state.income_data = pd.DataFrame(columns=[
            'id', 'date', 'source', 'amount', 'received_by',
            'customer', 'receipt_no', 'remarks'
        ])
    
    if 'payments_data' not in st.session_state:
        st.session_state.payments_data = pd.DataFrame(columns=[
            'id', 'farmer_name', 'amount', 'payment_method', 'date', 'remarks'
        ])
    
    # Managers and Farmers
    if 'managers' not in st.session_state:
        st.session_state.managers = [
            {"id": 1, "name": "Manager 1", "phone": "0300-1234567", "designation": "Senior Manager"},
            {"id": 2, "name": "Manager 2", "phone": "0312-7654321", "designation": "Field Manager"},
            {"id": 3, "name": "Manager 3", "phone": "0321-9876543", "designation": "Accounts Manager"}
        ]
    
    if 'farmers' not in st.session_state:
        st.session_state.farmers = [
            {"id": 1, "name": "Farmer 1", "phone": "0300-1111111", "address": "Farm Area 1"},
            {"id": 2, "name": "Farmer 2", "phone": "0300-2222222", "address": "Farm Area 2"},
            {"id": 3, "name": "Farmer 3", "phone": "0300-3333333", "address": "Farm Area 3"}
        ]
    
    # Timer
    if 'timer_running' not in st.session_state:
        st.session_state.timer_running = False
    if 'timer_start' not in st.session_state:
        st.session_state.timer_start = None
    if 'timer_seconds' not in st.session_state:
        st.session_state.timer_seconds = 0
    
    # Current IDs
    if 'next_livestock_id' not in st.session_state:
        st.session_state.next_livestock_id = 1
    if 'next_crop_id' not in st.session_state:
        st.session_state.next_crop_id = 1
    if 'next_water_id' not in st.session_state:
        st.session_state.next_water_id = 1
    if 'next_expense_id' not in st.session_state:
        st.session_state.next_expense_id = 1
    if 'next_income_id' not in st.session_state:
        st.session_state.next_income_id = 1
    if 'next_payment_id' not in st.session_state:
        st.session_state.next_payment_id = 1
    
    # Report state
    if 'generate_report' not in st.session_state:
        st.session_state.generate_report = False

# Load CSS and initialize
load_css()
init_session_state()

# Header
st.markdown("""
<div class="header">
    <h1>🚜 Farm Management System</h1>
    <div class="subtitle">Complete Solution for Farm Operations & Management</div>
</div>
""", unsafe_allow_html=True)

# Utility Functions
def get_next_id(id_type):
    id_var = f'next_{id_type}_id'
    current_id = st.session_state[id_var]
    st.session_state[id_var] += 1
    return current_id

def convert_dates(df, date_columns=['date']):
    """Convert date columns to datetime format"""
    df = df.copy()
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def save_data():
    """Save all data to JSON files"""
    try:
        data_to_save = {
            'livestock': st.session_state.livestock_data.to_dict('records'),
            'crop': st.session_state.crop_data.to_dict('records'),
            'water_supply': st.session_state.water_supply_data.to_dict('records'),
            'expenses': st.session_state.expenses_data.to_dict('records'),
            'income': st.session_state.income_data.to_dict('records'),
            'payments': st.session_state.payments_data.to_dict('records'),
            'managers': st.session_state.managers,
            'farmers': st.session_state.farmers
        }
        
        # Convert dates to strings for JSON serialization
        for key in ['livestock', 'crop', 'water_supply', 'expenses', 'income', 'payments']:
            if key in data_to_save:
                for record in data_to_save[key]:
                    if 'date' in record and pd.notna(record['date']):
                        if isinstance(record['date'], (pd.Timestamp, datetime)):
                            record['date'] = record['date'].strftime('%Y-%m-%d')
        
        with open('farm_data.json', 'w') as f:
            json.dump(data_to_save, f, indent=4, default=str)
        
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def load_data():
    """Load data from JSON files"""
    try:
        if not os.path.exists('farm_data.json'):
            return False
            
        with open('farm_data.json', 'r') as f:
            data = json.load(f)
        
        # Load DataFrames
        st.session_state.livestock_data = pd.DataFrame(data.get('livestock', []))
        st.session_state.crop_data = pd.DataFrame(data.get('crop', []))
        st.session_state.water_supply_data = pd.DataFrame(data.get('water_supply', []))
        st.session_state.expenses_data = pd.DataFrame(data.get('expenses', []))
        st.session_state.income_data = pd.DataFrame(data.get('income', []))
        st.session_state.payments_data = pd.DataFrame(data.get('payments', []))
        
        # Convert date strings to datetime
        st.session_state.livestock_data = convert_dates(st.session_state.livestock_data)
        st.session_state.crop_data = convert_dates(st.session_state.crop_data)
        st.session_state.water_supply_data = convert_dates(st.session_state.water_supply_data)
        st.session_state.expenses_data = convert_dates(st.session_state.expenses_data)
        st.session_state.income_data = convert_dates(st.session_state.income_data)
        st.session_state.payments_data = convert_dates(st.session_state.payments_data)
        
        # Load managers and farmers
        st.session_state.managers = data.get('managers', st.session_state.managers)
        st.session_state.farmers = data.get('farmers', st.session_state.farmers)
        
        # Update next IDs
        if not st.session_state.livestock_data.empty and 'id' in st.session_state.livestock_data.columns:
            st.session_state.next_livestock_id = int(st.session_state.livestock_data['id'].max()) + 1
        if not st.session_state.crop_data.empty and 'id' in st.session_state.crop_data.columns:
            st.session_state.next_crop_id = int(st.session_state.crop_data['id'].max()) + 1
        if not st.session_state.water_supply_data.empty and 'id' in st.session_state.water_supply_data.columns:
            st.session_state.next_water_id = int(st.session_state.water_supply_data['id'].max()) + 1
        if not st.session_state.expenses_data.empty and 'id' in st.session_state.expenses_data.columns:
            st.session_state.next_expense_id = int(st.session_state.expenses_data['id'].max()) + 1
        if not st.session_state.income_data.empty and 'id' in st.session_state.income_data.columns:
            st.session_state.next_income_id = int(st.session_state.income_data['id'].max()) + 1
        if not st.session_state.payments_data.empty and 'id' in st.session_state.payments_data.columns:
            st.session_state.next_payment_id = int(st.session_state.payments_data['id'].max()) + 1
        
        return True
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return False

def format_currency(value):
    return f"PKR {value:,.2f}"

# Timer Functions
def start_timer():
    if not st.session_state.timer_running:
        st.session_state.timer_running = True
        st.session_state.timer_start = datetime.now()

def stop_timer():
    if st.session_state.timer_running:
        st.session_state.timer_running = False
        elapsed = datetime.now() - st.session_state.timer_start
        st.session_state.timer_seconds += elapsed.total_seconds()

def reset_timer():
    st.session_state.timer_running = False
    st.session_state.timer_start = None
    st.session_state.timer_seconds = 0

def get_timer_display():
    total_seconds = st.session_state.timer_seconds
    if st.session_state.timer_running:
        elapsed = datetime.now() - st.session_state.timer_start
        total_seconds += elapsed.total_seconds()
    
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

# Create tabs
tabs = st.tabs([
    "🏠 Livestock", "🌱 Crop", "💧 Water Supply", 
    "💰 Expenses", "📈 Income", "📊 Reports"
])

# Tab 1: Livestock Management
with tabs[0]:
    st.markdown("<div class='section-card'><h3>🐄 Livestock Management (Cow/Beef/Goat)</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        livestock_category = st.selectbox(
            "Category *",
            ["", "Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Others (دیگر)"],
            key="tab1_livestock_category"
        )
    
    with col2:
        livestock_quantity = st.number_input("Quantity (تعداد)", min_value=0, key="tab1_livestock_quantity")
    
    with col3:
        livestock_expense_type = st.selectbox(
            "Expense Type (اخراجات کی قسم)",
            ["Khal (کھل)", "Chokar (چوکر)", "Tori (ٹوری)", "Ghaas/Fodder (گھاس)", 
             "Medicine (دوائیں)", "Vaccination (ٹیکہ)", "Others (دیگر)"],
            key="tab1_livestock_expense_type"
        )
    
    with col4:
        livestock_amount = st.number_input("Amount (PKR) *", min_value=0.0, key="tab1_livestock_amount")
    
    col5, col6, col7 = st.columns(3)
    with col5:
        expense_manager = st.selectbox(
            "Expense Managed By *",
            [""] + [m["name"] for m in st.session_state.managers],
            key="tab1_expense_manager"
        )
    
    with col6:
        livestock_date = st.date_input("Date *", value=date.today(), key="tab1_livestock_date")
    
    with col7:
        livestock_remarks = st.text_area("Remarks (ریمارکس)", key="tab1_livestock_remarks")
    
    col8, col9, col10 = st.columns([1, 1, 2])
    with col8:
        if st.button("➕ Add Expense", type="primary", use_container_width=True, key="tab1_add_expense"):
            if livestock_category and livestock_amount > 0 and expense_manager:
                new_entry = {
                    'id': get_next_id('livestock'),
                    'date': livestock_date,
                    'category': livestock_category,
                    'expense_type': livestock_expense_type,
                    'quantity': livestock_quantity,
                    'amount': livestock_amount,
                    'manager': expense_manager,
                    'remarks': livestock_remarks,
                    'transaction_type': 'expense'
                }
                st.session_state.livestock_data = pd.concat([
                    st.session_state.livestock_data,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)
                # Convert date to datetime
                st.session_state.livestock_data = convert_dates(st.session_state.livestock_data)
                save_data()
                st.success("Livestock expense added successfully!")
            else:
                st.error("Please fill all required fields")
    
    with col9:
        if st.button("🧹 Clear Form", use_container_width=True, key="tab1_clear_form"):
            st.rerun()
    
    # Livestock Ledger
    st.markdown("<div class='section-card'><h3>📖 Livestock Ledger (کھاتا)</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ledger_category_filter = st.selectbox(
            "Filter by Category",
            ["All Categories", "Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Others (دیگر)"],
            key="tab1_ledger_category_filter"
        )
    
    with col2:
        ledger_date_from = st.date_input("From Date", key="tab1_ledger_date_from", value=None)
    
    with col3:
        ledger_date_to = st.date_input("To Date", key="tab1_ledger_date_to", value=None)
    
    with col4:
        if st.button("🔍 Filter Ledger", use_container_width=True, key="tab1_filter_ledger"):
            pass
    
    # Display ledger - FIXED DATE COMPARISON
    if not st.session_state.livestock_data.empty:
        filtered_data = st.session_state.livestock_data.copy()
        
        # Ensure date column is datetime
        filtered_data = convert_dates(filtered_data)
        
        if ledger_category_filter != "All Categories":
            # Remove the language part for comparison
            category_english = ledger_category_filter.split(" (")[0]
            filtered_data = filtered_data[filtered_data['category'].str.contains(category_english, na=False)]
        
        if ledger_date_from:
            # Convert to datetime for comparison
            filtered_data = filtered_data[filtered_data['date'] >= pd.Timestamp(ledger_date_from)]
        
        if ledger_date_to:
            filtered_data = filtered_data[filtered_data['date'] <= pd.Timestamp(ledger_date_to)]
        
        if not filtered_data.empty:
            # Format date for display
            display_df = filtered_data.copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No records found for the selected filters.")
    else:
        st.info("No livestock records available.")
    
    # Statistics
    st.markdown("<div class='section-card'><h3>📊 Livestock Statistics</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.livestock_data.empty:
        # Convert dates for calculation
        calc_data = convert_dates(st.session_state.livestock_data)
        
        # Apply filters for statistics
        if ledger_date_from:
            calc_data = calc_data[calc_data['date'] >= pd.Timestamp(ledger_date_from)]
        if ledger_date_to:
            calc_data = calc_data[calc_data['date'] <= pd.Timestamp(ledger_date_to)]
        if ledger_category_filter != "All Categories":
            category_english = ledger_category_filter.split(" (")[0]
            calc_data = calc_data[calc_data['category'].str.contains(category_english, na=False)]
        
        col1, col2, col3 = st.columns(3)
        with col1:
            total_expenses = calc_data[calc_data['transaction_type'] == 'expense']['amount'].sum()
            st.metric("Total Expenses", format_currency(total_expenses), key="tab1_total_expenses")
        
        with col2:
            total_income = calc_data[calc_data['transaction_type'] == 'income']['amount'].sum()
            st.metric("Total Income", format_currency(total_income), key="tab1_total_income")
        
        with col3:
            net_balance = total_income - total_expenses
            st.metric("Net Balance", format_currency(net_balance), delta_color="inverse", key="tab1_net_balance")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Expenses", format_currency(0), key="tab1_total_expenses_empty")
        with col2:
            st.metric("Total Income", format_currency(0), key="tab1_total_income_empty")
        with col3:
            st.metric("Net Balance", format_currency(0), key="tab1_net_balance_empty")

# Tab 2: Crop Management
with tabs[1]:
    st.markdown("<div class='section-card'><h3>🌱 Crop Management (فصل)</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        crop_type = st.selectbox(
            "Crop Type (فصل کی قسم)",
            ["", "Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)", 
             "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", "Others (دیگر)"],
            key="tab2_crop_type"
        )
    
    with col2:
        crop_area = st.number_input("Area (ایکڑ)", min_value=0.0, key="tab2_crop_area")
    
    with col3:
        crop_expense_type = st.selectbox(
            "Expense Type (اخراجات کی قسم)",
            ["Labor (مزدوری)", "Seeds (بیج)", "Fertilizer (کھاد)", 
             "Spray (سپرے)", "Land Preparation", "Others (دیگر)"],
            key="tab2_crop_expense_type"
        )
    
    with col4:
        crop_amount = st.number_input("Amount (PKR) *", min_value=0.0, key="tab2_crop_amount")
    
    col5, col6, col7 = st.columns(3)
    with col5:
        crop_manager = st.selectbox(
            "Expense Managed By *",
            [""] + [m["name"] for m in st.session_state.managers],
            key="tab2_crop_manager"
        )
    
    with col6:
        crop_date = st.date_input("Date *", value=date.today(), key="tab2_crop_date")
    
    with col7:
        crop_remarks = st.text_area("Remarks (ریمارکس)", key="tab2_crop_remarks")
    
    col8, col9 = st.columns(2)
    with col8:
        if st.button("➕ Add Crop Expense", type="primary", use_container_width=True, key="tab2_add_crop_expense"):
            if crop_type and crop_amount > 0 and crop_manager:
                new_entry = {
                    'id': get_next_id('crop'),
                    'date': crop_date,
                    'crop_type': crop_type,
                    'area': crop_area,
                    'expense_type': crop_expense_type,
                    'amount': crop_amount,
                    'manager': crop_manager,
                    'remarks': crop_remarks,
                    'transaction_type': 'expense'
                }
                st.session_state.crop_data = pd.concat([
                    st.session_state.crop_data,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)
                # Convert date to datetime
                st.session_state.crop_data = convert_dates(st.session_state.crop_data)
                save_data()
                st.success("Crop expense added successfully!")
            else:
                st.error("Please fill all required fields")
    
    # Crop Data Table
    st.markdown("<div class='section-card'><h3>📋 Crop Records (رکارڈز)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.crop_data.empty:
        # Format date for display
        display_df = st.session_state.crop_data.copy()
        display_df = convert_dates(display_df)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No crop records available.")

# Tab 3: Water Supply
with tabs[2]:
    st.markdown("<div class='section-card'><h3>💧 Water Supply to Farmers (کسانوں کو پانی کی سپلائی)</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        farmer_name = st.text_input("Farmer Name (کسان کا نام) *", key="tab3_farmer_name")
    
    with col2:
        farmer_phone = st.text_input("Phone Number (فون نمبر)", key="tab3_farmer_phone")
    
    with col3:
        water_rate = st.number_input("Rate per Hour (فی گھنٹہ ریٹ) *", min_value=0.0, value=500.0, key="tab3_water_rate")
    
    with col4:
        water_date = st.date_input("Date *", value=date.today(), key="tab3_water_date")
    
    # Timer Section
    st.markdown("<div class='section-card'><h3>⏱️ Water Supply Timer (ٹائمر)</h3></div>", unsafe_allow_html=True)
    
    st.markdown(f"<div class='timer-display'>{get_timer_display()}</div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("▶️ Start Timer", type="primary", use_container_width=True, key="tab3_start_timer"):
            start_timer()
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Timer", type="secondary", use_container_width=True, key="tab3_stop_timer"):
            stop_timer()
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset Timer", use_container_width=True, key="tab3_reset_timer"):
            reset_timer()
            st.rerun()
    
    with col4:
        manual_hours = st.number_input("Manual Hours", min_value=0.0, key="tab3_manual_hours", value=0.0)
    
    # Timer calculation
    total_hours = st.session_state.timer_seconds / 3600
    if manual_hours > 0:
        total_hours = manual_hours
    total_bill = total_hours * water_rate
    
    col5, col6, col7, col8 = st.columns(4)
    with col5:
        start_time_display = st.session_state.timer_start.strftime("%H:%M:%S") if st.session_state.timer_start else ""
        st.text_input("Start Time", value=start_time_display, disabled=True, key="tab3_start_time")
    with col6:
        end_time_display = datetime.now().strftime("%H:%M:%S") if st.session_state.timer_running else ""
        st.text_input("End Time", value=end_time_display, disabled=True, key="tab3_end_time")
    with col7:
        st.number_input("Total Hours", value=round(total_hours, 2), disabled=True, key="tab3_total_hours")
    with col8:
        st.number_input("Total Bill", value=round(total_bill, 2), disabled=True, key="tab3_total_bill")
    
    # Save Water Supply
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Record", type="primary", use_container_width=True, key="tab3_save_record"):
            if farmer_name and water_rate > 0:
                new_entry = {
                    'id': get_next_id('water'),
                    'farmer_name': farmer_name,
                    'farmer_phone': farmer_phone,
                    'hours': round(total_hours, 2),
                    'rate': water_rate,
                    'total_bill': round(total_bill, 2),
                    'paid': 0,
                    'balance': round(total_bill, 2),
                    'date': water_date
                }
                st.session_state.water_supply_data = pd.concat([
                    st.session_state.water_supply_data,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)
                # Convert date to datetime
                st.session_state.water_supply_data = convert_dates(st.session_state.water_supply_data)
                save_data()
                st.success("Water supply record saved successfully!")
    
    # Farmer Ledger
    st.markdown("<div class='section-card'><h3>📖 Farmer Ledger Management (کسان کھاتا)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.water_supply_data.empty:
        farmer_names = list(st.session_state.water_supply_data['farmer_name'].unique())
    else:
        farmer_names = []
    
    col1, col2 = st.columns(2)
    with col1:
        select_farmer = st.selectbox(
            "Select Farmer (کسان منتخب کریں)",
            [""] + farmer_names,
            key="tab3_select_farmer"
        )
    
    # Payment Management
    st.markdown("<h4>Payment Management (ادائیگی کا انتظام)</h4>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        payment_amount = st.number_input("Payment Amount (ادائیگی کی رقم)", min_value=0.0, key="tab3_payment_amount", value=0.0)
    
    with col2:
        payment_date = st.date_input("Payment Date (ادائیگی کی تاریخ)", value=date.today(), key="tab3_payment_date")
    
    with col3:
        payment_method = st.selectbox(
            "Payment Method (ادائیگی کا طریقہ)",
            ["Cash (نقد)", "Bank Transfer (بینک)", "Check (چیک)"],
            key="tab3_payment_method"
        )
    
    with col4:
        if st.button("💰 Record Payment", type="primary", use_container_width=True, key="tab3_record_payment"):
            if select_farmer and payment_amount > 0:
                new_payment = {
                    'id': get_next_id('payment'),
                    'farmer_name': select_farmer,
                    'amount': payment_amount,
                    'payment_method': payment_method,
                    'date': payment_date,
                    'remarks': 'Payment recorded'
                }
                st.session_state.payments_data = pd.concat([
                    st.session_state.payments_data,
                    pd.DataFrame([new_payment])
                ], ignore_index=True)
                
                # Update water supply balance
                if not st.session_state.water_supply_data.empty:
                    mask = st.session_state.water_supply_data['farmer_name'] == select_farmer
                    if mask.any():
                        st.session_state.water_supply_data.loc[mask, 'paid'] += payment_amount
                        st.session_state.water_supply_data.loc[mask, 'balance'] -= payment_amount
                        # Convert date to datetime
                        st.session_state.water_supply_data = convert_dates(st.session_state.water_supply_data)
                
                # Convert payment data date to datetime
                st.session_state.payments_data = convert_dates(st.session_state.payments_data)
                save_data()
                st.success("Payment recorded successfully!")

# Tab 4: Expenses
with tabs[3]:
    st.markdown("<div class='section-card'><h3>💰 Consolidated Expenses (کل اخراجات)</h3></div>", unsafe_allow_html=True)
    
    # Updated expense categories with new additions
    expense_categories = [
        "", "Salary (تنخواہ)", "Machinery (مشینری)", "Fuel (پیٹرول/ڈیزل)", 
        "Maintenance (مرمت)", "Kitchen", "Construction", "Petrol", 
        "Diesel", "Electricity Bill", "Turbine Bill", "Others (دیگر)"
    ]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        expense_category = st.selectbox(
            "Expense Category (اخراجات کی قسم) *",
            expense_categories,
            key="tab4_expense_category"
        )
    
    with col2:
        expense_description = st.text_input("Description (تفصیل) *", key="tab4_expense_description")
    
    with col3:
        expense_amount = st.number_input("Amount (PKR) *", min_value=0.0, key="tab4_expense_amount")
    
    with col4:
        expense_date = st.date_input("Date *", value=date.today(), key="tab4_expense_date")
    
    col5, col6, col7 = st.columns(3)
    with col5:
        expense_managed_by = st.selectbox(
            "Managed By (منتظم) *",
            [""] + [m["name"] for m in st.session_state.managers],
            key="tab4_expense_managed_by"
        )
    
    with col6:
        expense_receipt_no = st.text_input("Receipt No (رسید نمبر)", key="tab4_expense_receipt_no")
    
    with col7:
        expense_remarks = st.text_area("Remarks (ریمارکس)", key="tab4_expense_remarks")
    
    col8, col9 = st.columns(2)
    with col8:
        if st.button("➕ Add Expense", type="primary", use_container_width=True, key="tab4_add_expense"):
            if expense_category and expense_description and expense_amount > 0 and expense_managed_by:
                new_entry = {
                    'id': get_next_id('expense'),
                    'date': expense_date,
                    'category': expense_category,
                    'description': expense_description,
                    'amount': expense_amount,
                    'manager': expense_managed_by,
                    'receipt_no': expense_receipt_no,
                    'remarks': expense_remarks
                }
                st.session_state.expenses_data = pd.concat([
                    st.session_state.expenses_data,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)
                # Convert date to datetime
                st.session_state.expenses_data = convert_dates(st.session_state.expenses_data)
                save_data()
                st.success("Expense added successfully!")
            else:
                st.error("Please fill all required fields")
    
    # Expenses Statistics
    st.markdown("<div class='section-card'><h3>📊 Expense Statistics</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    if not st.session_state.expenses_data.empty:
        # Convert dates for calculation
        expenses_data = convert_dates(st.session_state.expenses_data)
        
        today = date.today()
        month_start = date(today.year, today.month, 1)
        
        with col1:
            today_expenses = expenses_data[
                expenses_data['date'].dt.date == today
            ]['amount'].sum()
            st.metric("Today's Expenses", format_currency(today_expenses), key="tab4_today_expenses")
        
        with col2:
            month_expenses = expenses_data[
                (expenses_data['date'].dt.date >= month_start) &
                (expenses_data['date'].dt.date <= today)
            ]['amount'].sum()
            st.metric("This Month", format_currency(month_expenses), key="tab4_month_expenses")
        
        with col3:
            total_expenses = expenses_data['amount'].sum()
            st.metric("Total Expenses", format_currency(total_expenses), key="tab4_total_expenses")
    else:
        with col1:
            st.metric("Today's Expenses", format_currency(0), key="tab4_today_expenses_empty")
        with col2:
            st.metric("This Month", format_currency(0), key="tab4_month_expenses_empty")
        with col3:
            st.metric("Total Expenses", format_currency(0), key="tab4_total_expenses_empty")
    
    # All Expenses Table
    st.markdown("<div class='section-card'><h3>📋 All Expenses (تمام اخراجات)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.expenses_data.empty:
        # Format date for display
        display_df = st.session_state.expenses_data.copy()
        display_df = convert_dates(display_df)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No expense records available.")

# Tab 5: Income
with tabs[4]:
    st.markdown("<div class='section-card'><h3>📈 Income</h3></div>", unsafe_allow_html=True)
    
    # Updated income sources with new additions
    income_sources = [
        "", "Livestock Sale", "Goats", "Beef", "Cows", 
        "Crop Sale", "Water Supply", "Others"
    ]
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        income_source = st.selectbox(
            "Income Source (آمدنی کا ذریعہ) *",
            income_sources,
            key="tab5_income_source"
        )
    
    with col2:
        income_amount = st.number_input("Amount (PKR) *", min_value=0.0, key="tab5_income_amount")
    
    with col3:
        income_date = st.date_input("Date *", value=date.today(), key="tab5_income_date")
    
    with col4:
        income_received_by = st.selectbox(
            "Received By (وصول کنندہ)",
            [""] + [m["name"] for m in st.session_state.managers],
            key="tab5_income_received_by"
        )
    
    col5, col6, col7 = st.columns(3)
    with col5:
        income_customer = st.text_input("Customer/Payer (گاہک/ادا کرنے والا)", key="tab5_income_customer")
    
    with col6:
        income_receipt_no = st.text_input("Receipt No (رسید نمبر)", key="tab5_income_receipt_no")
    
    with col7:
        income_remarks = st.text_area("Remarks (ریمارکس)", key="tab5_income_remarks")
    
    col8, col9 = st.columns(2)
    with col8:
        if st.button("➕ Add Income", type="primary", use_container_width=True, key="tab5_add_income"):
            if income_source and income_amount > 0:
                new_entry = {
                    'id': get_next_id('income'),
                    'date': income_date,
                    'source': income_source,
                    'amount': income_amount,
                    'received_by': income_received_by,
                    'customer': income_customer,
                    'receipt_no': income_receipt_no,
                    'remarks': income_remarks
                }
                st.session_state.income_data = pd.concat([
                    st.session_state.income_data,
                    pd.DataFrame([new_entry])
                ], ignore_index=True)
                # Convert date to datetime
                st.session_state.income_data = convert_dates(st.session_state.income_data)
                save_data()
                st.success("Income recorded successfully!")
            else:
                st.error("Please fill all required fields")
    
    # Income Dashboard
    st.markdown("<div class='section-card'><h3>📊 Income Dashboard</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate livestock income
    livestock_income = 0
    crop_income = 0
    water_income = 0
    total_income = 0
    
    if not st.session_state.income_data.empty:
        income_data = convert_dates(st.session_state.income_data)
        
        # Livestock income (including Goats, Beef, Cows)
        livestock_keywords = ['Livestock', 'Goats', 'Beef', 'Cows']
        for keyword in livestock_keywords:
            mask = income_data['source'].astype(str).str.contains(keyword, na=False, case=False)
            livestock_income += income_data[mask]['amount'].sum()
    
    if not st.session_state.crop_data.empty:
        crop_data = convert_dates(st.session_state.crop_data)
        crop_income = crop_data[crop_data['transaction_type'] == 'income']['amount'].sum()
    
    if not st.session_state.water_supply_data.empty:
        water_income = st.session_state.water_supply_data['paid'].sum()
    
    if not st.session_state.income_data.empty:
        other_income = income_data[
            ~income_data['source'].astype(str).str.contains('|'.join(['Livestock', 'Goats', 'Beef', 'Cows', 'Crop']), na=False, case=False)
        ]['amount'].sum()
        total_income = livestock_income + crop_income + water_income + other_income
    else:
        total_income = livestock_income + crop_income + water_income
    
    with col1:
        st.metric("Livestock Income", format_currency(livestock_income), key="tab5_livestock_income")
    
    with col2:
        st.metric("Crop Income", format_currency(crop_income), key="tab5_crop_income")
    
    with col3:
        st.metric("Water Supply Income", format_currency(water_income), key="tab5_water_income")
    
    with col4:
        st.metric("Total Income", format_currency(total_income), key="tab5_total_income")
    
    # Income Records
    st.markdown("<div class='section-card'><h3>📋 Income Records (آمدنی کے رکارڈز)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.income_data.empty:
        # Format date for display
        display_df = st.session_state.income_data.copy()
        display_df = convert_dates(display_df)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No income records available.")

# Tab 6: Reports
with tabs[5]:
    st.markdown("<div class='section-card'><h3>📊 Comprehensive Reports (جامع رپورٹس)</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        report_type = st.selectbox(
            "Report Type (رپورٹ کی قسم)",
            ["Summary Report", "Expense Report", "Income Report", 
             "Livestock Report", "Crops Report", "Water Report"],
            key="tab6_report_type"
        )
    
    with col2:
        report_category = st.selectbox(
            "Category (زمرہ)",
            ["All (سب)", "Livestock (مویشی)", "Crop (فصل)", "Water (پانی)"],
            key="tab6_report_category"
        )
    
    with col3:
        report_date_from = st.date_input("From Date (تاریخ سے)", key="tab6_report_date_from", value=None)
    
    with col4:
        report_date_to = st.date_input("To Date (تاریخ تک)", key="tab6_report_date_to", value=None)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📈 Generate Report", type="primary", use_container_width=True, key="tab6_generate_report"):
            st.session_state.generate_report = True
    
    # Report Preview
    if st.session_state.generate_report:
        st.markdown("<div class='section-card'><h3>📄 Report Preview (رپورٹ پیش نظارہ)</h3></div>", unsafe_allow_html=True)
        
        # Calculate summary statistics with date filtering
        income_data_filtered = st.session_state.income_data.copy()
        water_data_filtered = st.session_state.water_supply_data.copy()
        expenses_data_filtered = st.session_state.expenses_data.copy()
        livestock_data_filtered = st.session_state.livestock_data.copy()
        crop_data_filtered = st.session_state.crop_data.copy()
        
        # Apply date filters if provided
        if report_date_from:
            income_data_filtered = convert_dates(income_data_filtered)
            income_data_filtered = income_data_filtered[income_data_filtered['date'] >= pd.Timestamp(report_date_from)]
            
            water_data_filtered = convert_dates(water_data_filtered)
            water_data_filtered = water_data_filtered[water_data_filtered['date'] >= pd.Timestamp(report_date_from)]
            
            expenses_data_filtered = convert_dates(expenses_data_filtered)
            expenses_data_filtered = expenses_data_filtered[expenses_data_filtered['date'] >= pd.Timestamp(report_date_from)]
            
            livestock_data_filtered = convert_dates(livestock_data_filtered)
            livestock_data_filtered = livestock_data_filtered[livestock_data_filtered['date'] >= pd.Timestamp(report_date_from)]
            
            crop_data_filtered = convert_dates(crop_data_filtered)
            crop_data_filtered = crop_data_filtered[crop_data_filtered['date'] >= pd.Timestamp(report_date_from)]
        
        if report_date_to:
            income_data_filtered = convert_dates(income_data_filtered)
            income_data_filtered = income_data_filtered[income_data_filtered['date'] <= pd.Timestamp(report_date_to)]
            
            water_data_filtered = convert_dates(water_data_filtered)
            water_data_filtered = water_data_filtered[water_data_filtered['date'] <= pd.Timestamp(report_date_to)]
            
            expenses_data_filtered = convert_dates(expenses_data_filtered)
            expenses_data_filtered = expenses_data_filtered[expenses_data_filtered['date'] <= pd.Timestamp(report_date_to)]
            
            livestock_data_filtered = convert_dates(livestock_data_filtered)
            livestock_data_filtered = livestock_data_filtered[livestock_data_filtered['date'] <= pd.Timestamp(report_date_to)]
            
            crop_data_filtered = convert_dates(crop_data_filtered)
            crop_data_filtered = crop_data_filtered[crop_data_filtered['date'] <= pd.Timestamp(report_date_to)]
        
        # Apply category filter
        if report_category != "All (سب)":
            category_map = {
                "Livestock (مویشی)": "Livestock",
                "Crop (فصل)": "Crop",
                "Water (پانی)": "Water"
            }
            selected_category = category_map.get(report_category, "")
            
            if selected_category == "Livestock":
                # Filter livestock-related data
                income_data_filtered = income_data_filtered[
                    income_data_filtered['source'].astype(str).str.contains('Livestock|Goats|Beef|Cows', na=False, case=False)
                ]
            elif selected_category == "Crop":
                # Filter crop-related data
                income_data_filtered = income_data_filtered[
                    income_data_filtered['source'].astype(str).str.contains('Crop', na=False, case=False)
                ]
                expenses_data_filtered = expenses_data_filtered[
                    expenses_data_filtered['category'].astype(str).str.contains('Crop', na=False, case=False)
                ]
            elif selected_category == "Water":
                # Filter water-related data
                income_data_filtered = income_data_filtered[
                    income_data_filtered['source'].astype(str).str.contains('Water', na=False, case=False)
                ]
        
        # Calculate totals
        total_income = income_data_filtered['amount'].sum() + water_data_filtered['paid'].sum()
        total_expenses = (
            expenses_data_filtered['amount'].sum() +
            livestock_data_filtered[livestock_data_filtered['transaction_type'] == 'expense']['amount'].sum() +
            crop_data_filtered[crop_data_filtered['transaction_type'] == 'expense']['amount'].sum()
        )
        
        net_profit = total_income - total_expenses
        profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
        
        # Display financial summary
        st.markdown("### Financial Summary (مالی خلاصہ)")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Income", format_currency(total_income), key="tab6_total_income")
        with col2:
            st.metric("Total Expenses", format_currency(total_expenses), key="tab6_total_expenses")
        with col3:
            st.metric("Net Profit", format_currency(net_profit), delta_color="inverse", key="tab6_net_profit")
        with col4:
            st.metric("Profit Margin", f"{profit_margin:.2f}%", key="tab6_profit_margin")
        
        # Report-specific content
        if report_type == "Summary Report":
            st.markdown("### Detailed Breakdown")
            
            # Income by source
            if not income_data_filtered.empty:
                st.subheader("Income by Source")
                income_by_source = income_data_filtered.groupby('source')['amount'].sum().reset_index()
                if not income_by_source.empty:
                    fig1 = px.pie(
                        income_by_source,
                        values='amount',
                        names='source',
                        title='Income by Source'
                    )
                    st.plotly_chart(fig1, use_container_width=True, key="tab6_income_pie")
            
            # Expenses by category
            if not expenses_data_filtered.empty:
                st.subheader("Expenses by Category")
                expenses_by_category = expenses_data_filtered.groupby('category')['amount'].sum().reset_index()
                if not expenses_by_category.empty:
                    fig2 = px.bar(
                        expenses_by_category,
                        x='category',
                        y='amount',
                        title='Expenses by Category',
                        color='amount'
                    )
                    st.plotly_chart(fig2, use_container_width=True, key="tab6_expenses_bar")
        
        elif report_type == "Livestock Report":
            st.markdown("### Livestock Report")
            if not livestock_data_filtered.empty:
                st.dataframe(livestock_data_filtered, use_container_width=True)
            else:
                st.info("No livestock data available for the selected filters.")
        
        elif report_type == "Crops Report":
            st.markdown("### Crops Report")
            if not crop_data_filtered.empty:
                st.dataframe(crop_data_filtered, use_container_width=True)
            else:
                st.info("No crop data available for the selected filters.")
        
        elif report_type == "Water Report":
            st.markdown("### Water Supply Report")
            if not water_data_filtered.empty:
                st.dataframe(water_data_filtered, use_container_width=True)
            else:
                st.info("No water supply data available for the selected filters.")
        
        # Export options
        st.markdown("### Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            # Export to CSV
            @st.cache_data
            def convert_df_to_csv(df):
                return df.to_csv(index=False).encode('utf-8')
            
            # Combine relevant data based on report type
            if report_type == "Summary Report":
                export_df = pd.concat([
                    income_data_filtered,
                    expenses_data_filtered,
                    livestock_data_filtered,
                    crop_data_filtered,
                    water_data_filtered
                ], ignore_index=True)
            elif report_type == "Livestock Report":
                export_df = livestock_data_filtered
            elif report_type == "Crops Report":
                export_df = crop_data_filtered
            elif report_type == "Water Report":
                export_df = water_data_filtered
            else:
                export_df = income_data_filtered
            
            if not export_df.empty:
                csv = convert_df_to_csv(export_df)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv,
                    file_name=f"{report_type.replace(' ', '_')}_{date.today()}.csv",
                    mime="text/csv",
                    key="tab6_download_csv"
                )
            else:
                st.warning("No data to export")
        
        with col2:
            # Clear report button
            if st.button("Clear Report", use_container_width=True, key="tab6_clear_report"):
                st.session_state.generate_report = False
                st.rerun()

# Sidebar for data management
with st.sidebar:
    st.markdown("## 🗃️ Data Management")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Save All Data", use_container_width=True, key="sidebar_save_data"):
            if save_data():
                st.success("Data saved successfully!")
    
    with col2:
        if st.button("📂 Load Data", use_container_width=True, key="sidebar_load_data"):
            if load_data():
                st.success("Data loaded successfully!")
            else:
                st.info("No saved data found. Starting with empty dataset.")
    
    st.divider()
    
    st.markdown("## 👥 Manage Users")
    
    # Add new manager
    with st.expander("Add New Manager"):
        new_manager_name = st.text_input("Manager Name", key="sidebar_new_manager_name")
        new_manager_phone = st.text_input("Phone", key="sidebar_new_manager_phone")
        new_manager_designation = st.text_input("Designation", key="sidebar_new_manager_designation")
        
        if st.button("Add Manager", key="sidebar_add_manager"):
            if new_manager_name:
                new_manager = {
                    "id": len(st.session_state.managers) + 1,
                    "name": new_manager_name,
                    "phone": new_manager_phone,
                    "designation": new_manager_designation
                }
                st.session_state.managers.append(new_manager)
                save_data()
                st.success("Manager added successfully!")
                st.rerun()
    
    # Add new farmer
    with st.expander("Add New Farmer"):
        new_farmer_name = st.text_input("Farmer Name", key="sidebar_new_farmer_name")
        new_farmer_phone = st.text_input("Farmer Phone", key="sidebar_new_farmer_phone")
        new_farmer_address = st.text_input("Address", key="sidebar_new_farmer_address")
        
        if st.button("Add Farmer", key="sidebar_add_farmer"):
            if new_farmer_name:
                new_farmer = {
                    "id": len(st.session_state.farmers) + 1,
                    "name": new_farmer_name,
                    "phone": new_farmer_phone,
                    "address": new_farmer_address
                }
                st.session_state.farmers.append(new_farmer)
                save_data()
                st.success("Farmer added successfully!")
                st.rerun()
    
    st.divider()
    
    # System Statistics
    st.markdown("## 📈 System Statistics")
    
    total_records = (
        len(st.session_state.livestock_data) + 
        len(st.session_state.crop_data) + 
        len(st.session_state.water_supply_data) +
        len(st.session_state.expenses_data) +
        len(st.session_state.income_data)
    )
    
    st.metric("Total Records", total_records, key="sidebar_total_records")
    
    # Quick Actions
    st.markdown("## ⚡ Quick Actions")
    
    if st.button("Clear All Data", type="secondary", key="sidebar_clear_all_data"):
        st.warning("This will clear all data. Are you sure?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Clear All", key="sidebar_confirm_clear"):
                # Reinitialize session state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                init_session_state()
                st.success("All data cleared!")
                st.rerun()
        with col2:
            if st.button("Cancel", key="sidebar_cancel_clear"):
                st.rerun()

# Auto-save every 30 seconds
if 'last_save' not in st.session_state:
    st.session_state.last_save = time.time()

if time.time() - st.session_state.last_save > 30:
    save_data()
    st.session_state.last_save = time.time()

# Load data on startup
if 'data_loaded' not in st.session_state:
    load_data()
    st.session_state.data_loaded = True
