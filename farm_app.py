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
import tempfile
import uuid

# Set page config
st.set_page_config(
    page_title="Complete Farm Management System",
    page_icon="🚜",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
/* Main Container */
.main-container {
    max-width: 1600px;
    margin: 0 auto;
}

/* Header */
.header {
    background: linear-gradient(135deg, #2c3e50, #34495e);
    color: white;
    padding: 25px;
    text-align: center;
    border-bottom: 5px solid #27ae60;
    border-radius: 10px;
    margin-bottom: 20px;
}

/* Cards */
.section-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 20px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    border-left: 5px solid #3498db;
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

/* Dashboard Cards */
.dashboard-card {
    background: linear-gradient(135deg, #ffffff, #f8f9fa);
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08);
    text-align: center;
    border-top: 4px solid #3498db;
    margin: 10px;
}

/* Timer */
.timer-display {
    font-size: 3rem;
    font-weight: bold;
    color: #2c3e50;
    background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    padding: 20px;
    border-radius: 10px;
    text-align: center;
    border: 3px solid #3498db;
    margin: 15px 0;
}

/* Status Messages */
.status-success {
    padding: 10px 15px;
    border-radius: 6px;
    margin: 10px 0;
    background: #d4edda;
    color: #155724;
    border: 1px solid #b1dfbb;
}

.status-error {
    padding: 10px 15px;
    border-radius: 6px;
    margin: 10px 0;
    background: #f8d7da;
    color: #721c24;
    border: 1px solid #f1b0b7;
}

/* Form Styling */
.stTextInput>div>div>input, .stNumberInput>div>div>input,
.stSelectbox>div>div>select, .stTextArea>div>textarea {
    border: 2px solid #ddd;
    border-radius: 6px;
    padding: 8px;
}

.stButton>button {
    width: 100%;
    margin: 5px 0;
}

/* Ledger */
.ledger-container {
    background: #f8f9fa;
    border-radius: 8px;
    padding: 15px;
    margin-top: 15px;
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #dee2e6;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background-color: #34495e;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    color: white;
    padding: 10px 20px;
}

.stTabs [aria-selected="true"] {
    background-color: #27ae60;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    # Initialize all data storage
    default_columns = {
        'livestock': ['id', 'date', 'category', 'expense_type', 'quantity', 'amount', 'manager', 'remarks', 'transaction_type'],
        'crop': ['id', 'date', 'crop_type', 'area', 'expense_type', 'amount', 'manager', 'remarks', 'transaction_type'],
        'water_supply': ['id', 'farmer_name', 'farmer_phone', 'start_time', 'end_time', 'hours', 'rate', 'total_bill', 'paid', 'balance', 'date'],
        'expenses': ['id', 'date', 'category', 'description', 'amount', 'manager', 'receipt_no', 'remarks'],
        'income': ['id', 'date', 'source', 'amount', 'received_by', 'customer', 'receipt_no', 'remarks'],
        'payments': ['id', 'farmer_name', 'amount', 'payment_method', 'date', 'remarks'],
        'farmers': ['id', 'name', 'phone', 'address'],
        'managers': ['id', 'name', 'phone', 'designation']
    }
    
    for data_type, columns in default_columns.items():
        if f'{data_type}_data' not in st.session_state:
            st.session_state[f'{data_type}_data'] = pd.DataFrame(columns=columns)
    
    # Timer state
    if 'timer_running' not in st.session_state:
        st.session_state.timer_running = False
    if 'timer_start' not in st.session_state:
        st.session_state.timer_start = None
    if 'timer_seconds' not in st.session_state:
        st.session_state.timer_seconds = 0
    
    # Edit state
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False
    if 'editing_id' not in st.session_state:
        st.session_state.editing_id = None
    if 'editing_type' not in st.session_state:
        st.session_state.editing_type = None
    
    # Load data automatically
    if 'data_loaded' not in st.session_state:
        load_all_data()
        st.session_state.data_loaded = True

# Utility functions
def get_next_id(data_type):
    data = st.session_state[f'{data_type}_data']
    if not data.empty and 'id' in data.columns:
        return int(data['id'].max()) + 1
    return 1

def format_currency(value):
    return f"PKR {float(value):,.2f}"

def save_all_data():
    """Save all data to JSON files"""
    try:
        data_to_save = {}
        for data_type in ['livestock', 'crop', 'water_supply', 'expenses', 'income', 'payments', 'farmers', 'managers']:
            df = st.session_state[f'{data_type}_data']
            # Convert Timestamps to strings for JSON serialization
            if not df.empty:
                for col in df.columns:
                    if pd.api.types.is_datetime64_any_dtype(df[col]):
                        df[col] = df[col].dt.strftime('%Y-%m-%d')
            data_to_save[data_type] = df.to_dict('records')
        
        with open('farm_data.json', 'w') as f:
            json.dump(data_to_save, f, indent=4, default=str)
        
        return True
    except Exception as e:
        st.error(f"Error saving data: {str(e)}")
        return False

def load_all_data():
    """Load all data from JSON files"""
    try:
        if os.path.exists('farm_data.json'):
            with open('farm_data.json', 'r') as f:
                data = json.load(f)
            
            for data_type, records in data.items():
                if records:
                    df = pd.DataFrame(records)
                    # Convert date strings back to datetime
                    for col in df.columns:
                        if 'date' in col.lower():
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                    st.session_state[f'{data_type}_data'] = df
                else:
                    st.session_state[f'{data_type}_data'] = pd.DataFrame()
            
            return True
        return False
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return False

# Auto-save decorator
def auto_save(func):
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        save_all_data()
        return result
    return wrapper

# Timer functions
def start_timer():
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

# Initialize
init_session_state()

# Header
st.markdown("""
<div class="header">
    <h1 style="margin:0; padding:0;">🚜 Complete Farm Management System</h1>
    <p style="margin:10px 0 0 0; font-size:1.2rem;">Complete Solution for Farm Operations & Management</p>
</div>
""", unsafe_allow_html=True)

# Create tabs
tabs = st.tabs([
    "🏠 Livestock", "🌱 Crop", "💧 Water Supply", 
    "💰 Expenses", "📈 Income", "📊 Reports", "📁 Data Management"
])

# ==================== TAB 1: LIVESTOCK ====================
with tabs[0]:
    st.markdown("<div class='section-card'><h3>🐄 Livestock Management</h3></div>", unsafe_allow_html=True)
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_livestock = len(st.session_state.livestock_data)
        st.metric("Total Records", total_livestock)
    with col2:
        total_exp = st.session_state.livestock_data['amount'].sum() if not st.session_state.livestock_data.empty else 0
        st.metric("Total Amount", format_currency(total_exp))
    with col3:
        avg_amount = st.session_state.livestock_data['amount'].mean() if not st.session_state.livestock_data.empty else 0
        st.metric("Average", format_currency(avg_amount))
    with col4:
        recent_count = len(st.session_state.livestock_data[st.session_state.livestock_data['date'] >= pd.Timestamp(date.today() - timedelta(days=7))]) if not st.session_state.livestock_data.empty else 0
        st.metric("Last 7 Days", recent_count)
    
    # Form
    with st.form("livestock_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.selectbox("Category *", ["Cow", "Beef", "Goat", "Sheep", "Buffalo", "Other"])
            quantity = st.number_input("Quantity", min_value=0, value=1)
            expense_type = st.selectbox("Expense Type", ["Feed", "Medicine", "Vaccination", "Labor", "Equipment", "Other"])
        
        with col2:
            amount = st.number_input("Amount (PKR) *", min_value=0.0, value=0.0)
            manager = st.text_input("Managed By *", value="")
            transaction_type = st.selectbox("Transaction Type", ["Expense", "Income"])
        
        with col3:
            entry_date = st.date_input("Date *", value=date.today())
            remarks = st.text_area("Remarks")
        
        submitted = st.form_submit_button("💾 Save Record", use_container_width=True)
        if submitted:
            if amount > 0 and manager and category:
                new_record = {
                    'id': str(uuid.uuid4())[:8],
                    'date': entry_date,
                    'category': category,
                    'expense_type': expense_type,
                    'quantity': quantity,
                    'amount': amount,
                    'manager': manager,
                    'remarks': remarks,
                    'transaction_type': transaction_type
                }
                st.session_state.livestock_data = pd.concat([
                    st.session_state.livestock_data,
                    pd.DataFrame([new_record])
                ], ignore_index=True)
                save_all_data()
                st.success("Record saved successfully!")
                st.rerun()
    
    # Data Display & Edit
    st.markdown("<div class='section-card'><h3>📋 Livestock Records</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.livestock_data.empty:
        # Search and Filter
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Search records", "")
        with col2:
            filter_category = st.selectbox("Filter by category", ["All"] + list(st.session_state.livestock_data['category'].unique()))
        
        # Filter data
        display_data = st.session_state.livestock_data.copy()
        if search_term:
            mask = display_data.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
            display_data = display_data[mask]
        if filter_category != "All":
            display_data = display_data[display_data['category'] == filter_category]
        
        # Display table with edit/delete options
        for idx, row in display_data.iterrows():
            with st.expander(f"{row['date']} - {row['category']} - {format_currency(row['amount'])}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**Type:** {row['expense_type']} | **Qty:** {row['quantity']}")
                    st.write(f"**Manager:** {row['manager']}")
                    st.write(f"**Remarks:** {row['remarks']}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_livestock_{row['id']}"):
                        st.session_state.edit_mode = True
                        st.session_state.editing_id = row['id']
                        st.session_state.editing_type = 'livestock'
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_livestock_{row['id']}"):
                        st.session_state.livestock_data = st.session_state.livestock_data[st.session_state.livestock_data['id'] != row['id']]
                        save_all_data()
                        st.success("Record deleted!")
                        st.rerun()
    
    # Import/Export Section
    st.markdown("<div class='section-card'><h3>📁 Data Import/Export</h3></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        # Download template
        template_data = pd.DataFrame(columns=['date', 'category', 'expense_type', 'quantity', 'amount', 'manager', 'remarks', 'transaction_type'])
        csv = template_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Template",
            data=csv,
            file_name="livestock_template.csv",
            mime="text/csv"
        )
    
    with col2:
        # Upload and import
        uploaded_file = st.file_uploader("Upload CSV file", type=['csv'], key="livestock_upload")
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                required_cols = ['date', 'category', 'amount', 'manager']
                if all(col in df.columns for col in required_cols):
                    df['id'] = [str(uuid.uuid4())[:8] for _ in range(len(df))]
                    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
                    df['quantity'] = df.get('quantity', 1)
                    df['transaction_type'] = df.get('transaction_type', 'Expense')
                    
                    st.session_state.livestock_data = pd.concat([st.session_state.livestock_data, df], ignore_index=True)
                    save_all_data()
                    st.success(f"Successfully imported {len(df)} records!")
                    st.rerun()
                else:
                    st.error(f"Missing required columns. Required: {required_cols}")
            except Exception as e:
                st.error(f"Error importing file: {str(e)}")

# ==================== TAB 2: CROP ====================
with tabs[1]:
    st.markdown("<div class='section-card'><h3>🌱 Crop Management</h3></div>", unsafe_allow_html=True)
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_crops = len(st.session_state.crop_data)
        st.metric("Total Records", total_crops)
    with col2:
        total_area = st.session_state.crop_data['area'].sum() if not st.session_state.crop_data.empty else 0
        st.metric("Total Area", f"{total_area:.2f} acres")
    with col3:
        total_amount = st.session_state.crop_data['amount'].sum() if not st.session_state.crop_data.empty else 0
        st.metric("Total Amount", format_currency(total_amount))
    with col4:
        unique_crops = st.session_state.crop_data['crop_type'].nunique() if not st.session_state.crop_data.empty else 0
        st.metric("Crop Types", unique_crops)
    
    # Form
    with st.form("crop_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            crop_type = st.selectbox("Crop Type *", ["Wheat", "Rice", "Cotton", "Kheera (Cucumber)", "Corn", "Sugarcane", "Vegetables", "Fruits", "Other"])
            area = st.number_input("Area (acres) *", min_value=0.0, value=0.0)
            expense_type = st.selectbox("Expense Type", ["Land Preparation", "Seeds", "Fertilizer", "Pesticides", "Irrigation", "Labor", "Harvesting", "Transport", "Other"])
        
        with col2:
            amount = st.number_input("Amount (PKR) *", min_value=0.0, value=0.0)
            manager = st.text_input("Managed By *", value="")
            transaction_type = st.selectbox("Transaction Type", ["Expense", "Income"])
        
        with col3:
            crop_date = st.date_input("Date *", value=date.today())
            remarks = st.text_area("Remarks")
        
        submitted = st.form_submit_button("💾 Save Record", use_container_width=True)
        if submitted:
            if amount > 0 and manager and crop_type and area > 0:
                new_record = {
                    'id': str(uuid.uuid4())[:8],
                    'date': crop_date,
                    'crop_type': crop_type,
                    'area': area,
                    'expense_type': expense_type,
                    'amount': amount,
                    'manager': manager,
                    'remarks': remarks,
                    'transaction_type': transaction_type
                }
                st.session_state.crop_data = pd.concat([
                    st.session_state.crop_data,
                    pd.DataFrame([new_record])
                ], ignore_index=True)
                save_all_data()
                st.success("Record saved successfully!")
                st.rerun()
    
    # Data Display & Edit
    st.markdown("<div class='section-card'><h3>📋 Crop Records</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.crop_data.empty:
        # Search and Filter
        col1, col2 = st.columns(2)
        with col1:
            search_term = st.text_input("Search crop records", "", key="crop_search")
        with col2:
            filter_crop = st.selectbox("Filter by crop type", ["All"] + list(st.session_state.crop_data['crop_type'].unique()), key="crop_filter")
        
        # Filter data
        display_data = st.session_state.crop_data.copy()
        if search_term:
            mask = display_data.apply(lambda row: row.astype(str).str.contains(search_term, case=False).any(), axis=1)
            display_data = display_data[mask]
        if filter_crop != "All":
            display_data = display_data[display_data['crop_type'] == filter_crop]
        
        # Display table with edit/delete options
        for idx, row in display_data.iterrows():
            with st.expander(f"{row['date']} - {row['crop_type']} ({row['area']} acres) - {format_currency(row['amount'])}"):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**Expense Type:** {row['expense_type']}")
                    st.write(f"**Manager:** {row['manager']}")
                    st.write(f"**Remarks:** {row['remarks']}")
                
                with col2:
                    if st.button("✏️ Edit", key=f"edit_crop_{row['id']}"):
                        st.session_state.edit_mode = True
                        st.session_state.editing_id = row['id']
                        st.session_state.editing_type = 'crop'
                        st.rerun()
                
                with col3:
                    if st.button("🗑️ Delete", key=f"delete_crop_{row['id']}"):
                        st.session_state.crop_data = st.session_state.crop_data[st.session_state.crop_data['id'] != row['id']]
                        save_all_data()
                        st.success("Record deleted!")
                        st.rerun()

# ==================== TAB 3: WATER SUPPLY ====================
with tabs[2]:
    st.markdown("<div class='section-card'><h3>💧 Water Supply Management</h3></div>", unsafe_allow_html=True)
    
    # Timer Section
    st.markdown("<div class='timer-display'>" + get_timer_display() + "</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("▶️ Start Timer", use_container_width=True):
            start_timer()
            st.rerun()
    with col2:
        if st.button("⏹️ Stop Timer", use_container_width=True):
            stop_timer()
            st.rerun()
    with col3:
        if st.button("🔄 Reset Timer", use_container_width=True):
            reset_timer()
            st.rerun()
    
    # Form
    with st.form("water_form"):
        col1, col2 = st.columns(2)
        with col1:
            farmer_name = st.text_input("Farmer Name *", value="")
            farmer_phone = st.text_input("Phone Number", value="")
            rate = st.number_input("Rate per Hour (PKR) *", min_value=0.0, value=500.0)
        
        with col2:
            water_date = st.date_input("Date *", value=date.today())
            manual_hours = st.number_input("Manual Hours (if no timer)", min_value=0.0, value=0.0)
            remarks = st.text_area("Remarks")
        
        # Calculate hours
        hours = st.session_state.timer_seconds / 3600 if manual_hours == 0 else manual_hours
        total_bill = hours * rate
        
        st.write(f"**Calculated Hours:** {hours:.2f}")
        st.write(f"**Total Bill:** {format_currency(total_bill)}")
        
        submitted = st.form_submit_button("💾 Save Water Supply Record", use_container_width=True)
        if submitted:
            if farmer_name and rate > 0 and hours > 0:
                new_record = {
                    'id': str(uuid.uuid4())[:8],
                    'farmer_name': farmer_name,
                    'farmer_phone': farmer_phone,
                    'hours': hours,
                    'rate': rate,
                    'total_bill': total_bill,
                    'paid': 0.0,
                    'balance': total_bill,
                    'date': water_date
                }
                st.session_state.water_supply_data = pd.concat([
                    st.session_state.water_supply_data,
                    pd.DataFrame([new_record])
                ], ignore_index=True)
                save_all_data()
                st.success("Water supply record saved!")
                st.rerun()
    
    # Farmer Ledger Section
    st.markdown("<div class='section-card'><h3>👨‍🌾 Farmer Ledger</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.water_supply_data.empty:
        # Select farmer
        farmers = st.session_state.water_supply_data['farmer_name'].unique()
        selected_farmer = st.selectbox("Select Farmer", farmers)
        
        if selected_farmer:
            # Get farmer records
            farmer_records = st.session_state.water_supply_data[st.session_state.water_supply_data['farmer_name'] == selected_farmer]
            farmer_payments = st.session_state.payments_data[st.session_state.payments_data['farmer_name'] == selected_farmer]
            
            # Calculate totals
            total_bill = farmer_records['total_bill'].sum()
            total_paid = farmer_records['paid'].sum()
            balance = total_bill - total_paid
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Bill", format_currency(total_bill))
            with col2:
                st.metric("Total Paid", format_currency(total_paid))
            with col3:
                st.metric("Balance", format_currency(balance))
            
            # Payment form
            with st.form("payment_form"):
                payment_amount = st.number_input("Payment Amount", min_value=0.0, value=0.0)
                payment_method = st.selectbox("Payment Method", ["Cash", "Bank Transfer", "Check", "Mobile Payment"])
                payment_date = st.date_input("Payment Date", value=date.today())
                payment_remarks = st.text_input("Remarks")
                
                if st.form_submit_button("💳 Record Payment"):
                    if payment_amount > 0:
                        # Update water supply record
                        idx = st.session_state.water_supply_data['farmer_name'] == selected_farmer
                        st.session_state.water_supply_data.loc[idx, 'paid'] += payment_amount
                        st.session_state.water_supply_data.loc[idx, 'balance'] -= payment_amount
                        
                        # Add payment record
                        payment_record = {
                            'id': str(uuid.uuid4())[:8],
                            'farmer_name': selected_farmer,
                            'amount': payment_amount,
                            'payment_method': payment_method,
                            'date': payment_date,
                            'remarks': payment_remarks
                        }
                        st.session_state.payments_data = pd.concat([
                            st.session_state.payments_data,
                            pd.DataFrame([payment_record])
                        ], ignore_index=True)
                        
                        save_all_data()
                        st.success("Payment recorded!")
                        st.rerun()

# ==================== TAB 4: EXPENSES ====================
with tabs[3]:
    st.markdown("<div class='section-card'><h3>💰 Expense Management</h3></div>", unsafe_allow_html=True)
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        today_exp = st.session_state.expenses_data[
            st.session_state.expenses_data['date'] == pd.Timestamp(date.today())
        ]['amount'].sum() if not st.session_state.expenses_data.empty else 0
        st.metric("Today", format_currency(today_exp))
    
    with col2:
        month_start = date.today().replace(day=1)
        month_exp = st.session_state.expenses_data[
            st.session_state.expenses_data['date'] >= pd.Timestamp(month_start)
        ]['amount'].sum() if not st.session_state.expenses_data.empty else 0
        st.metric("This Month", format_currency(month_exp))
    
    with col3:
        total_exp = st.session_state.expenses_data['amount'].sum() if not st.session_state.expenses_data.empty else 0
        st.metric("Total", format_currency(total_exp))
    
    with col4:
        avg_exp = st.session_state.expenses_data['amount'].mean() if not st.session_state.expenses_data.empty else 0
        st.metric("Average", format_currency(avg_exp))
    
    # Form
    with st.form("expense_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            category = st.selectbox("Category *", [
                "Kitchen", "Construction", "Petrol", "Diesel", 
                "Electricity Bill", "Turbine Bill", "Salary", 
                "Maintenance", "Transport", "Office", "Other"
            ])
            description = st.text_input("Description *", value="")
        
        with col2:
            amount = st.number_input("Amount (PKR) *", min_value=0.0, value=0.0)
            manager = st.text_input("Managed By *", value="")
        
        with col3:
            expense_date = st.date_input("Date *", value=date.today())
            receipt_no = st.text_input("Receipt Number")
            remarks = st.text_area("Remarks")
        
        submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)
        if submitted:
            if amount > 0 and manager and description and category:
                new_record = {
                    'id': str(uuid.uuid4())[:8],
                    'date': expense_date,
                    'category': category,
                    'description': description,
                    'amount': amount,
                    'manager': manager,
                    'receipt_no': receipt_no,
                    'remarks': remarks
                }
                st.session_state.expenses_data = pd.concat([
                    st.session_state.expenses_data,
                    pd.DataFrame([new_record])
                ], ignore_index=True)
                save_all_data()
                st.success("Expense saved!")
                st.rerun()
    
    # Expense Analysis
    st.markdown("<div class='section-card'><h3>📊 Expense Analysis</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.expenses_data.empty:
        # Category breakdown
        category_totals = st.session_state.expenses_data.groupby('category')['amount'].sum().reset_index()
        fig = px.pie(category_totals, values='amount', names='category', title='Expenses by Category')
        st.plotly_chart(fig, use_container_width=True)

# ==================== TAB 5: INCOME ====================
with tabs[4]:
    st.markdown("<div class='section-card'><h3>📈 Income Management</h3></div>", unsafe_allow_html=True)
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        livestock_income = st.session_state.income_data[
            st.session_state.income_data['source'].isin(['Goats', 'Beef', 'Cows', 'Livestock Sale'])
        ]['amount'].sum() if not st.session_state.income_data.empty else 0
        st.metric("Livestock", format_currency(livestock_income))
    
    with col2:
        crop_income = st.session_state.income_data[
            st.session_state.income_data['source'] == 'Crop Sale'
        ]['amount'].sum() if not st.session_state.income_data.empty else 0
        st.metric("Crops", format_currency(crop_income))
    
    with col3:
        water_income = st.session_state.water_supply_data['paid'].sum() if not st.session_state.water_supply_data.empty else 0
        st.metric("Water Supply", format_currency(water_income))
    
    with col4:
        total_income = st.session_state.income_data['amount'].sum() + water_income if not st.session_state.income_data.empty else water_income
        st.metric("Total Income", format_currency(total_income))
    
    # Form
    with st.form("income_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            source = st.selectbox("Income Source *", [
                "Goats", "Beef", "Cows", "Livestock Sale", 
                "Crop Sale", "Water Supply", "Milk Sale",
                "Other Sales", "Services", "Other"
            ])
            amount = st.number_input("Amount (PKR) *", min_value=0.0, value=0.0)
        
        with col2:
            customer = st.text_input("Customer/Payer", value="")
            received_by = st.text_input("Received By *", value="")
        
        with col3:
            income_date = st.date_input("Date *", value=date.today())
            receipt_no = st.text_input("Receipt Number")
            remarks = st.text_area("Remarks")
        
        submitted = st.form_submit_button("💾 Save Income", use_container_width=True)
        if submitted:
            if amount > 0 and received_by and source:
                new_record = {
                    'id': str(uuid.uuid4())[:8],
                    'date': income_date,
                    'source': source,
                    'amount': amount,
                    'received_by': received_by,
                    'customer': customer,
                    'receipt_no': receipt_no,
                    'remarks': remarks
                }
                st.session_state.income_data = pd.concat([
                    st.session_state.income_data,
                    pd.DataFrame([new_record])
                ], ignore_index=True)
                save_all_data()
                st.success("Income recorded!")
                st.rerun()

# ==================== TAB 6: REPORTS ====================
with tabs[5]:
    st.markdown("<div class='section-card'><h3>📊 Comprehensive Reports</h3></div>", unsafe_allow_html=True)
    
    # Report Type Selection
    report_type = st.selectbox("Select Report Type", [
        "Financial Summary", "Livestock Report", "Crop Report", 
        "Water Supply Report", "Expense Report", "Income Report",
        "Balance Sheet"
    ])
    
    # Date Range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("From Date", value=date.today() - timedelta(days=30))
    with col2:
        end_date = st.date_input("To Date", value=date.today())
    
    if st.button("Generate Report", use_container_width=True):
        # Filter data by date
        mask = lambda df: (df['date'] >= pd.Timestamp(start_date)) & (df['date'] <= pd.Timestamp(end_date))
        
        # Calculate totals
        livestock_total = st.session_state.livestock_data[mask(st.session_state.livestock_data)]['amount'].sum() if not st.session_state.livestock_data.empty else 0
        crop_total = st.session_state.crop_data[mask(st.session_state.crop_data)]['amount'].sum() if not st.session_state.crop_data.empty else 0
        water_total = st.session_state.water_supply_data[mask(st.session_state.water_supply_data)]['paid'].sum() if not st.session_state.water_supply_data.empty else 0
        expense_total = st.session_state.expenses_data[mask(st.session_state.expenses_data)]['amount'].sum() if not st.session_state.expenses_data.empty else 0
        income_total = st.session_state.income_data[mask(st.session_state.income_data)]['amount'].sum() if not st.session_state.income_data.empty else 0
        
        if report_type == "Financial Summary":
            st.markdown("<h4>Financial Summary Report</h4>", unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                total_income = income_total + water_total
                st.metric("Total Income", format_currency(total_income))
            with col2:
                total_expenses = expense_total + livestock_total + crop_total
                st.metric("Total Expenses", format_currency(total_expenses))
            with col3:
                net_profit = total_income - total_expenses
                st.metric("Net Profit", format_currency(net_profit), delta_color="inverse")
            with col4:
                profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
                st.metric("Profit Margin", f"{profit_margin:.1f}%")
            
            # Create charts
            fig1 = px.bar(
                x=['Livestock', 'Crops', 'Water', 'Other Income', 'Expenses'],
                y=[livestock_total, crop_total, water_total, income_total, expense_total],
                title="Financial Overview",
                labels={'x': 'Category', 'y': 'Amount (PKR)'}
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        elif report_type == "Livestock Report":
            st.dataframe(st.session_state.livestock_data[mask(st.session_state.livestock_data)], use_container_width=True)
        
        elif report_type == "Crop Report":
            st.dataframe(st.session_state.crop_data[mask(st.session_state.crop_data)], use_container_width=True)
        
        elif report_type == "Water Supply Report":
            st.dataframe(st.session_state.water_supply_data[mask(st.session_state.water_supply_data)], use_container_width=True)
        
        elif report_type == "Expense Report":
            st.dataframe(st.session_state.expenses_data[mask(st.session_state.expenses_data)], use_container_width=True)
        
        elif report_type == "Income Report":
            st.dataframe(st.session_state.income_data[mask(st.session_state.income_data)], use_container_width=True)
        
        elif report_type == "Balance Sheet":
            # Create balance sheet
            assets = total_income + water_total
            liabilities = total_expenses
            equity = assets - liabilities
            
            st.markdown("### Balance Sheet")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Assets**")
                st.write(f"Total Income: {format_currency(assets)}")
            
            with col2:
                st.markdown("**Liabilities & Equity**")
                st.write(f"Total Expenses: {format_currency(liabilities)}")
                st.write(f"Owner's Equity: {format_currency(equity)}")
            
            st.markdown(f"**Total Assets = Total Liabilities + Equity**")
            st.markdown(f"{format_currency(assets)} = {format_currency(liabilities)} + {format_currency(equity)}")

# ==================== TAB 7: DATA MANAGEMENT ====================
with tabs[6]:
    st.markdown("<div class='section-card'><h3>📁 Data Management</h3></div>", unsafe_allow_html=True)
    
    # Backup and Restore
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 💾 Backup Data")
        if st.button("Create Backup", use_container_width=True):
            save_all_data()
            st.success("Backup created successfully!")
        
        # Download backup
        backup_data = {}
        for data_type in ['livestock', 'crop', 'water_supply', 'expenses', 'income', 'payments']:
            backup_data[data_type] = st.session_state[f'{data_type}_data'].to_dict('records')
        
        json_str = json.dumps(backup_data, indent=4, default=str)
        st.download_button(
            label="Download Backup File",
            data=json_str,
            file_name=f"farm_backup_{date.today()}.json",
            mime="application/json"
        )
    
    with col2:
        st.markdown("### 📂 Restore Data")
        uploaded_backup = st.file_uploader("Upload Backup File", type=['json'])
        if uploaded_backup is not None:
            if st.button("Restore from Backup", use_container_width=True):
                try:
                    backup_data = json.load(uploaded_backup)
                    for data_type, records in backup_data.items():
                        if records:
                            df = pd.DataFrame(records)
                            st.session_state[f'{data_type}_data'] = df
                    save_all_data()
                    st.success("Data restored successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error restoring data: {str(e)}")
    
    # Data Statistics
    st.markdown("<div class='section-card'><h3>📊 System Statistics</h3></div>", unsafe_allow_html=True)
    
    stats_cols = st.columns(4)
    with stats_cols[0]:
        total_records = sum(len(st.session_state[f'{dt}_data']) for dt in ['livestock', 'crop', 'water_supply', 'expenses', 'income'])
        st.metric("Total Records", total_records)
    
    with stats_cols[1]:
        today_records = sum(len(st.session_state[f'{dt}_data'][
            st.session_state[f'{dt}_data']['date'] == pd.Timestamp(date.today())
        ]) for dt in ['livestock', 'crop', 'water_supply', 'expenses', 'income'])
        st.metric("Today's Records", today_records)
    
    with stats_cols[2]:
        unique_managers = set()
        for dt in ['livestock', 'crop', 'expenses', 'income']:
            if 'manager' in st.session_state[f'{dt}_data'].columns:
                unique_managers.update(st.session_state[f'{dt}_data']['manager'].dropna().unique())
        st.metric("Unique Managers", len(unique_managers))
    
    with stats_cols[3]:
        unique_farmers = len(st.session_state.water_supply_data['farmer_name'].unique()) if not st.session_state.water_supply_data.empty else 0
        st.metric("Unique Farmers", unique_farmers)
    
    # Bulk Operations
    st.markdown("<div class='section-card'><h3>⚡ Bulk Operations</h3></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Refresh All Data", use_container_width=True):
            load_all_data()
            st.success("Data refreshed!")
            st.rerun()
    
    with col2:
        if st.button("🗑️ Clear All Data", use_container_width=True, type="secondary"):
            if st.checkbox("I understand this will delete ALL data permanently"):
                if st.button("Confirm Delete ALL Data", type="primary"):
                    for data_type in ['livestock', 'crop', 'water_supply', 'expenses', 'income', 'payments']:
                        st.session_state[f'{data_type}_data'] = pd.DataFrame()
                    save_all_data()
                    st.success("All data cleared!")
                    st.rerun()

# Edit Modal (when edit_mode is True)
if st.session_state.edit_mode and st.session_state.editing_id and st.session_state.editing_type:
    data_type = st.session_state.editing_type
    record_id = st.session_state.editing_id
    
    # Get the record to edit
    df = st.session_state[f'{data_type}_data']
    record = df[df['id'] == record_id].iloc[0]
    
    # Create edit form
    with st.form(f"edit_{data_type}_form"):
        st.markdown(f"### ✏️ Edit {data_type.title()} Record")
        
        # Dynamically create form fields based on record
        form_data = {}
        for col in df.columns:
            if col != 'id':
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    form_data[col] = st.date_input(col, value=record[col].date())
                elif pd.api.types.is_numeric_dtype(df[col]):
                    form_data[col] = st.number_input(col, value=float(record[col]))
                else:
                    form_data[col] = st.text_input(col, value=str(record[col]))
        
        col1, col2 = st.columns(2)
        with col1:
            save = st.form_submit_button("💾 Save Changes", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("❌ Cancel", use_container_width=True)
        
        if save:
            # Update the record
            for col, value in form_data.items():
                df.loc[df['id'] == record_id, col] = value
            
            st.session_state[f'{data_type}_data'] = df
            save_all_data()
            st.session_state.edit_mode = False
            st.session_state.editing_id = None
            st.session_state.editing_type = None
            st.success("Record updated successfully!")
            st.rerun()
        
        if cancel:
            st.session_state.edit_mode = False
            st.session_state.editing_id = None
            st.session_state.editing_type = None
            st.rerun()

# Footer with auto-save status
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.caption(f"📊 Total System Records: {sum(len(st.session_state[f'{dt}_data']) for dt in ['livestock', 'crop', 'water_supply', 'expenses', 'income'])}")
with col2:
    st.caption("💾 Auto-save: Active | Data saved automatically")

# Auto-save every 30 seconds
if 'last_save' not in st.session_state:
    st.session_state.last_save = time.time()

if time.time() - st.session_state.last_save > 30:
    save_all_data()
    st.session_state.last_save = time.time()
    # Show auto-save notification
    st.toast("💾 Data auto-saved!", icon="✅")
