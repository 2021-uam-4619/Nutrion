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
    
    /* Edit/Delete buttons */
    .edit-btn {
        background: linear-gradient(135deg, #3498db, #2980b9);
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
        margin-right: 5px;
    }
    
    .delete-btn {
        background: linear-gradient(135deg, #e74c3c, #c0392b);
        color: white;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 12px;
    }
    
    /* Modal overlay */
    .modal-overlay {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: rgba(0, 0, 0, 0.5);
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 1000;
    }
    
    .modal-content {
        background: white;
        padding: 30px;
        border-radius: 12px;
        max-width: 800px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
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
    
    # Editing states
    if 'editing_record' not in st.session_state:
        st.session_state.editing_record = None
    if 'editing_tab' not in st.session_state:
        st.session_state.editing_tab = None
    if 'show_edit_modal' not in st.session_state:
        st.session_state.show_edit_modal = False
    
    # Farmer ledger state
    if 'selected_farmer_ledger' not in st.session_state:
        st.session_state.selected_farmer_ledger = None

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
    return f"PKR {value:,.0f}"

def create_excel_template(tab_name):
    """Create Excel template for different tabs with sample data"""
    if tab_name == "livestock":
        template_df = pd.DataFrame([
            {
                'id': 1,
                'date': '2024-01-15',
                'category': 'Cow (گائے)',
                'expense_type': 'Khal (کھل)',
                'quantity': 10,
                'amount': 5000,
                'manager': 'Manager 1',
                'remarks': 'Monthly feed purchase',
                'transaction_type': 'expense'
            },
            {
                'id': 2,
                'date': '2024-01-20',
                'category': 'Goat (بکری)',
                'expense_type': 'Medicine (دوائیں)',
                'quantity': 5,
                'amount': 2500,
                'manager': 'Manager 2',
                'remarks': 'Vaccination',
                'transaction_type': 'expense'
            }
        ])
    elif tab_name == "crop":
        template_df = pd.DataFrame([
            {
                'id': 1,
                'date': '2024-01-10',
                'crop_type': 'Wheat (گندم)',
                'area': 10,
                'expense_type': 'Fertilizer (کھاد)',
                'amount': 15000,
                'manager': 'Manager 1',
                'remarks': 'Urea fertilizer',
                'transaction_type': 'expense'
            },
            {
                'id': 2,
                'date': '2024-01-25',
                'crop_type': 'Rice (چاول)',
                'area': 8,
                'expense_type': 'Labor (مزدوری)',
                'amount': 12000,
                'manager': 'Manager 3',
                'remarks': 'Harvesting labor',
                'transaction_type': 'expense'
            }
        ])
    elif tab_name == "water_supply":
        template_df = pd.DataFrame([
            {
                'id': 1,
                'farmer_name': 'Farmer 1',
                'farmer_phone': '0300-1111111',
                'start_time': '08:00',
                'end_time': '12:00',
                'hours': 4,
                'rate': 500,
                'total_bill': 2000,
                'paid': 1000,
                'balance': 1000,
                'date': '2024-01-15'
            },
            {
                'id': 2,
                'farmer_name': 'Farmer 2',
                'farmer_phone': '0300-2222222',
                'start_time': '09:00',
                'end_time': '11:30',
                'hours': 2.5,
                'rate': 500,
                'total_bill': 1250,
                'paid': 1250,
                'balance': 0,
                'date': '2024-01-20'
            }
        ])
    elif tab_name == "expenses":
        template_df = pd.DataFrame([
            {
                'id': 1,
                'date': '2024-01-05',
                'category': 'Salary (تنخواہ)',
                'description': 'January salary for workers',
                'amount': 50000,
                'manager': 'Manager 1',
                'receipt_no': 'SAL-001',
                'remarks': 'Paid via bank transfer'
            },
            {
                'id': 2,
                'date': '2024-01-12',
                'category': 'Fuel (پیٹرول/ڈیزل)',
                'description': 'Diesel for tractor',
                'amount': 15000,
                'manager': 'Manager 2',
                'receipt_no': 'FUEL-001',
                'remarks': 'From Shell station'
            }
        ])
    elif tab_name == "income":
        template_df = pd.DataFrame([
            {
                'id': 1,
                'date': '2024-01-18',
                'source': 'Livestock Sale',
                'amount': 75000,
                'received_by': 'Manager 1',
                'customer': 'Local Market',
                'receipt_no': 'INC-001',
                'remarks': 'Sold 2 cows'
            },
            {
                'id': 2,
                'date': '2024-01-22',
                'source': 'Crop Sale',
                'amount': 120000,
                'received_by': 'Manager 3',
                'customer': 'Grain Merchant',
                'receipt_no': 'INC-002',
                'remarks': 'Wheat harvest sold'
            }
        ])
    elif tab_name == "payments":
        template_df = pd.DataFrame([
            {
                'id': 1,
                'farmer_name': 'Farmer 1',
                'amount': 1000,
                'payment_method': 'Cash (نقد)',
                'date': '2024-01-16',
                'remarks': 'Partial payment for water supply'
            },
            {
                'id': 2,
                'farmer_name': 'Farmer 2',
                'amount': 1250,
                'payment_method': 'Bank Transfer (بینک)',
                'date': '2024-01-21',
                'remarks': 'Full payment cleared'
            }
        ])
    else:
        return None
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Template')
    
    return output.getvalue()

def import_excel_data(file, tab_name):
    """Import data from Excel file"""
    try:
        df = pd.read_excel(file)
        
        if tab_name == "livestock":
            required_cols = ['date', 'category', 'amount']
            if all(col in df.columns for col in required_cols):
                # Generate new IDs starting from next available
                start_id = st.session_state.next_livestock_id
                df['id'] = range(start_id, start_id + len(df))
                st.session_state.next_livestock_id += len(df)
                
                # Set default values for missing columns
                if 'transaction_type' not in df.columns:
                    df['transaction_type'] = 'expense'
                if 'quantity' not in df.columns:
                    df['quantity'] = 0
                if 'expense_type' not in df.columns:
                    df['expense_type'] = 'Others (دیگر)'
                if 'manager' not in df.columns:
                    df['manager'] = st.session_state.managers[0]['name'] if st.session_state.managers else ''
                if 'remarks' not in df.columns:
                    df['remarks'] = ''
                
                st.session_state.livestock_data = pd.concat(
                    [st.session_state.livestock_data, df], ignore_index=True
                )
                st.session_state.livestock_data = convert_dates(st.session_state.livestock_data)
                return True, f"Successfully imported {len(df)} livestock records"
        
        elif tab_name == "crop":
            required_cols = ['date', 'crop_type', 'amount']
            if all(col in df.columns for col in required_cols):
                start_id = st.session_state.next_crop_id
                df['id'] = range(start_id, start_id + len(df))
                st.session_state.next_crop_id += len(df)
                
                if 'transaction_type' not in df.columns:
                    df['transaction_type'] = 'expense'
                if 'area' not in df.columns:
                    df['area'] = 0
                if 'expense_type' not in df.columns:
                    df['expense_type'] = 'Others (دیگر)'
                if 'manager' not in df.columns:
                    df['manager'] = st.session_state.managers[0]['name'] if st.session_state.managers else ''
                if 'remarks' not in df.columns:
                    df['remarks'] = ''
                
                st.session_state.crop_data = pd.concat(
                    [st.session_state.crop_data, df], ignore_index=True
                )
                st.session_state.crop_data = convert_dates(st.session_state.crop_data)
                return True, f"Successfully imported {len(df)} crop records"
        
        elif tab_name == "water_supply":
            required_cols = ['farmer_name', 'hours', 'rate', 'total_bill', 'date']
            if all(col in df.columns for col in required_cols):
                start_id = st.session_state.next_water_id
                df['id'] = range(start_id, start_id + len(df))
                st.session_state.next_water_id += len(df)
                
                if 'paid' not in df.columns:
                    df['paid'] = 0
                if 'balance' not in df.columns:
                    df['balance'] = df['total_bill'] - df.get('paid', 0)
                if 'farmer_phone' not in df.columns:
                    df['farmer_phone'] = ''
                if 'start_time' not in df.columns:
                    df['start_time'] = ''
                if 'end_time' not in df.columns:
                    df['end_time'] = ''
                
                st.session_state.water_supply_data = pd.concat(
                    [st.session_state.water_supply_data, df], ignore_index=True
                )
                st.session_state.water_supply_data = convert_dates(st.session_state.water_supply_data)
                return True, f"Successfully imported {len(df)} water supply records"
        
        elif tab_name == "expenses":
            required_cols = ['date', 'category', 'description', 'amount']
            if all(col in df.columns for col in required_cols):
                start_id = st.session_state.next_expense_id
                df['id'] = range(start_id, start_id + len(df))
                st.session_state.next_expense_id += len(df)
                
                if 'manager' not in df.columns:
                    df['manager'] = st.session_state.managers[0]['name'] if st.session_state.managers else ''
                if 'receipt_no' not in df.columns:
                    df['receipt_no'] = ''
                if 'remarks' not in df.columns:
                    df['remarks'] = ''
                
                st.session_state.expenses_data = pd.concat(
                    [st.session_state.expenses_data, df], ignore_index=True
                )
                st.session_state.expenses_data = convert_dates(st.session_state.expenses_data)
                return True, f"Successfully imported {len(df)} expense records"
        
        elif tab_name == "income":
            required_cols = ['date', 'source', 'amount']
            if all(col in df.columns for col in required_cols):
                start_id = st.session_state.next_income_id
                df['id'] = range(start_id, start_id + len(df))
                st.session_state.next_income_id += len(df)
                
                if 'received_by' not in df.columns:
                    df['received_by'] = st.session_state.managers[0]['name'] if st.session_state.managers else ''
                if 'customer' not in df.columns:
                    df['customer'] = ''
                if 'receipt_no' not in df.columns:
                    df['receipt_no'] = ''
                if 'remarks' not in df.columns:
                    df['remarks'] = ''
                
                st.session_state.income_data = pd.concat(
                    [st.session_state.income_data, df], ignore_index=True
                )
                st.session_state.income_data = convert_dates(st.session_state.income_data)
                return True, f"Successfully imported {len(df)} income records"
        
        elif tab_name == "payments":
            required_cols = ['farmer_name', 'amount', 'date']
            if all(col in df.columns for col in required_cols):
                start_id = st.session_state.next_payment_id
                df['id'] = range(start_id, start_id + len(df))
                st.session_state.next_payment_id += len(df)
                
                if 'payment_method' not in df.columns:
                    df['payment_method'] = 'Cash (نقد)'
                if 'remarks' not in df.columns:
                    df['remarks'] = ''
                
                st.session_state.payments_data = pd.concat(
                    [st.session_state.payments_data, df], ignore_index=True
                )
                st.session_state.payments_data = convert_dates(st.session_state.payments_data)
                return True, f"Successfully imported {len(df)} payment records"
        
        return False, "Excel file doesn't have required columns"
    
    except Exception as e:
        return False, f"Error importing Excel: {str(e)}"

def delete_record(tab_name, record_id):
    """Delete a record from specified tab"""
    try:
        if tab_name == "livestock":
            st.session_state.livestock_data = st.session_state.livestock_data[
                st.session_state.livestock_data['id'] != record_id
            ].reset_index(drop=True)
        elif tab_name == "crop":
            st.session_state.crop_data = st.session_state.crop_data[
                st.session_state.crop_data['id'] != record_id
            ].reset_index(drop=True)
        elif tab_name == "water_supply":
            st.session_state.water_supply_data = st.session_state.water_supply_data[
                st.session_state.water_supply_data['id'] != record_id
            ].reset_index(drop=True)
        elif tab_name == "expenses":
            st.session_state.expenses_data = st.session_state.expenses_data[
                st.session_state.expenses_data['id'] != record_id
            ].reset_index(drop=True)
        elif tab_name == "income":
            st.session_state.income_data = st.session_state.income_data[
                st.session_state.income_data['id'] != record_id
            ].reset_index(drop=True)
        elif tab_name == "payments":
            st.session_state.payments_data = st.session_state.payments_data[
                st.session_state.payments_data['id'] != record_id
            ].reset_index(drop=True)
        
        save_data()
        return True
    except Exception as e:
        st.error(f"Error deleting record: {str(e)}")
        return False

def show_edit_modal(tab_name, record):
    """Show modal for editing record"""
    st.session_state.editing_tab = tab_name
    st.session_state.editing_record = record
    st.session_state.show_edit_modal = True

def update_record(tab_name, record_id, updated_data):
    """Update a record in specified tab"""
    try:
        if tab_name == "livestock":
            mask = st.session_state.livestock_data['id'] == record_id
            if mask.any():
                for key, value in updated_data.items():
                    st.session_state.livestock_data.loc[mask, key] = value
                st.session_state.livestock_data = convert_dates(st.session_state.livestock_data)
        
        elif tab_name == "crop":
            mask = st.session_state.crop_data['id'] == record_id
            if mask.any():
                for key, value in updated_data.items():
                    st.session_state.crop_data.loc[mask, key] = value
                st.session_state.crop_data = convert_dates(st.session_state.crop_data)
        
        elif tab_name == "water_supply":
            mask = st.session_state.water_supply_data['id'] == record_id
            if mask.any():
                for key, value in updated_data.items():
                    st.session_state.water_supply_data.loc[mask, key] = value
                st.session_state.water_supply_data = convert_dates(st.session_state.water_supply_data)
        
        elif tab_name == "expenses":
            mask = st.session_state.expenses_data['id'] == record_id
            if mask.any():
                for key, value in updated_data.items():
                    st.session_state.expenses_data.loc[mask, key] = value
                st.session_state.expenses_data = convert_dates(st.session_state.expenses_data)
        
        elif tab_name == "income":
            mask = st.session_state.income_data['id'] == record_id
            if mask.any():
                for key, value in updated_data.items():
                    st.session_state.income_data.loc[mask, key] = value
                st.session_state.income_data = convert_dates(st.session_state.income_data)
        
        elif tab_name == "payments":
            mask = st.session_state.payments_data['id'] == record_id
            if mask.any():
                for key, value in updated_data.items():
                    st.session_state.payments_data.loc[mask, key] = value
                st.session_state.payments_data = convert_dates(st.session_state.payments_data)
        
        save_data()
        return True
    except Exception as e:
        st.error(f"Error updating record: {str(e)}")
        return False

def get_farmer_ledger_details(farmer_name):
    """Get complete ledger details for a farmer"""
    if not farmer_name:
        return None
    
    # Initialize empty DataFrames if they don't exist
    if not hasattr(st.session_state, 'payments_data'):
        st.session_state.payments_data = pd.DataFrame(columns=['id', 'farmer_name', 'amount', 'payment_method', 'date', 'remarks'])
    
    if not hasattr(st.session_state, 'water_supply_data'):
        st.session_state.water_supply_data = pd.DataFrame(columns=['id', 'farmer_name', 'farmer_phone', 'start_time', 'end_time', 'hours', 'rate', 'total_bill', 'paid', 'balance', 'date'])
    
    # Get water supply records
    water_records = pd.DataFrame()
    if 'farmer_name' in st.session_state.water_supply_data.columns:
        water_records = st.session_state.water_supply_data[
            st.session_state.water_supply_data['farmer_name'] == farmer_name
        ].copy()
    
    # Get payment records
    payment_records = pd.DataFrame()
    if 'farmer_name' in st.session_state.payments_data.columns:
        payment_records = st.session_state.payments_data[
            st.session_state.payments_data['farmer_name'] == farmer_name
        ].copy()
    
    # Convert dates
    water_records = convert_dates(water_records)
    payment_records = convert_dates(payment_records)
    
    # Calculate totals
    total_water_bill = water_records['total_bill'].sum() if not water_records.empty else 0
    total_paid = water_records['paid'].sum() if not water_records.empty else 0
    total_payments = payment_records['amount'].sum() if not payment_records.empty else 0
    current_balance = total_water_bill - total_paid - total_payments
    
    return {
        'farmer_name': farmer_name,
        'water_records': water_records,
        'payment_records': payment_records,
        'total_water_bill': total_water_bill,
        'total_paid': total_paid,
        'total_payments': total_payments,
        'current_balance': current_balance
    }

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
    "💰 Expenses", "📈 Income", "📊 Reports", "👤 Farmer Ledger"
])

# Tab 1: Livestock Management
with tabs[0]:
    st.markdown("<div class='section-card'><h3>🐄 Livestock Management (Cow/Beef/Goat)</h3></div>", unsafe_allow_html=True)
    
    # Excel Import Section
    with st.expander("📤 Import Excel Data"):
        col1, col2 = st.columns(2)
        with col1:
            template_data = create_excel_template("livestock")
            st.download_button(
                label="📥 Download Template",
                data=template_data,
                file_name="livestock_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'], key="tab1_excel_upload")
            if uploaded_file:
                if st.button("Import Data", key="tab1_import"):
                    success, message = import_excel_data(uploaded_file, "livestock")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
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
                st.session_state.livestock_data = convert_dates(st.session_state.livestock_data)
                save_data()
                st.success("Livestock expense added successfully!")
                st.rerun()
            else:
                st.error("Please fill all required fields")
    
    with col9:
        if st.button("🧹 Clear Form", use_container_width=True, key="tab1_clear_form"):
            st.rerun()
    
    # Livestock Data Table with Edit/Delete
    st.markdown("<div class='section-card'><h3>📋 Livestock Records (مویشیوں کے رکارڈز)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.livestock_data.empty:
        display_df = st.session_state.livestock_data.copy()
        display_df = convert_dates(display_df)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        # Display the dataframe with edit/delete buttons
        for idx, row in display_df.iterrows():
            cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1, 1])
            with cols[0]:
                st.write(row['id'])
            with cols[1]:
                st.write(row['date'])
            with cols[2]:
                st.write(row['category'])
            with cols[3]:
                st.write(row['expense_type'])
            with cols[4]:
                st.write(row['quantity'])
            with cols[5]:
                st.write(format_currency(row['amount']))
            with cols[6]:
                st.write(row['manager'])
            with cols[7]:
                # Safely handle remarks column
                remarks_text = str(row['remarks']) if 'remarks' in row and pd.notna(row['remarks']) else ""
                st.write(remarks_text[:20] + '...' if len(remarks_text) > 20 else remarks_text)
            with cols[8]:
                if st.button("✏️", key=f"edit_livestock_{row['id']}_{idx}"):
                    show_edit_modal("livestock", row)
            with cols[9]:
                if st.button("🗑️", key=f"delete_livestock_{row['id']}_{idx}"):
                    if delete_record("livestock", row['id']):
                        st.success(f"Record {row['id']} deleted successfully!")
                        st.rerun()
    else:
        st.info("No livestock records available.")
    
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
    
    # Display ledger
    if not st.session_state.livestock_data.empty:
        filtered_data = st.session_state.livestock_data.copy()
        filtered_data = convert_dates(filtered_data)
        
        if ledger_category_filter != "All Categories":
            category_english = ledger_category_filter.split(" (")[0]
            filtered_data = filtered_data[filtered_data['category'].str.contains(category_english, na=False)]
        
        if ledger_date_from:
            filtered_data = filtered_data[filtered_data['date'] >= pd.Timestamp(ledger_date_from)]
        
        if ledger_date_to:
            filtered_data = filtered_data[filtered_data['date'] <= pd.Timestamp(ledger_date_to)]
        
        if not filtered_data.empty:
            display_df = filtered_data.copy()
            display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No records found for the selected filters.")
    
    # Statistics
    st.markdown("<div class='section-card'><h3>📊 Livestock Statistics</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.livestock_data.empty:
        calc_data = convert_dates(st.session_state.livestock_data)
        
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
            st.metric("Livestock Total Expenses", format_currency(total_expenses))
        
        with col2:
            total_income = calc_data[calc_data['transaction_type'] == 'income']['amount'].sum()
            st.metric("Livestock Total Income", format_currency(total_income))
        
        with col3:
            net_balance = total_income - total_expenses
            st.metric("Livestock Net Balance", format_currency(net_balance), delta_color="inverse")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Livestock Expenses (No Data)", format_currency(0))
        with col2:
            st.metric("Livestock Income (No Data)", format_currency(0))
        with col3:
            st.metric("Livestock Balance (No Data)", format_currency(0))

# Tab 2: Crop Management
with tabs[1]:
    st.markdown("<div class='section-card'><h3>🌱 Crop Management (فصل)</h3></div>", unsafe_allow_html=True)
    
    # Excel Import Section
    with st.expander("📤 Import Excel Data"):
        col1, col2 = st.columns(2)
        with col1:
            template_data = create_excel_template("crop")
            st.download_button(
                label="📥 Download Template",
                data=template_data,
                file_name="crop_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'], key="tab2_excel_upload")
            if uploaded_file:
                if st.button("Import Data", key="tab2_import"):
                    success, message = import_excel_data(uploaded_file, "crop")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
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
                st.session_state.crop_data = convert_dates(st.session_state.crop_data)
                save_data()
                st.success("Crop expense added successfully!")
                st.rerun()
            else:
                st.error("Please fill all required fields")
    
    # Crop Data Table with Edit/Delete
    st.markdown("<div class='section-card'><h3>📋 Crop Records (رکارڈز)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.crop_data.empty:
        display_df = st.session_state.crop_data.copy()
        display_df = convert_dates(display_df)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        for idx, row in display_df.iterrows():
            cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1, 1])
            with cols[0]:
                st.write(row['id'])
            with cols[1]:
                st.write(row['date'])
            with cols[2]:
                st.write(row['crop_type'])
            with cols[3]:
                st.write(row['area'])
            with cols[4]:
                st.write(row['expense_type'])
            with cols[5]:
                st.write(format_currency(row['amount']))
            with cols[6]:
                st.write(row['manager'])
            with cols[7]:
                # Safely handle remarks column
                remarks_text = str(row['remarks']) if 'remarks' in row and pd.notna(row['remarks']) else ""
                st.write(remarks_text[:20] + '...' if len(remarks_text) > 20 else remarks_text)
            with cols[8]:
                if st.button("✏️", key=f"edit_crop_{row['id']}_{idx}"):
                    show_edit_modal("crop", row)
            with cols[9]:
                if st.button("🗑️", key=f"delete_crop_{row['id']}_{idx}"):
                    if delete_record("crop", row['id']):
                        st.success(f"Record {row['id']} deleted successfully!")
                        st.rerun()
    else:
        st.info("No crop records available.")
    
    # Crop Statistics (NEW)
    st.markdown("<div class='section-card'><h3>📊 Crop Statistics</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.crop_data.empty:
        crop_data = convert_dates(st.session_state.crop_data)
        
        # Filter by date if needed
        col1, col2 = st.columns(2)
        with col1:
            crop_date_from = st.date_input("From Date", key="crop_date_from", value=None)
        with col2:
            crop_date_to = st.date_input("To Date", key="crop_date_to", value=None)
        
        if crop_date_from:
            crop_data = crop_data[crop_data['date'] >= pd.Timestamp(crop_date_from)]
        if crop_date_to:
            crop_data = crop_data[crop_data['date'] <= pd.Timestamp(crop_date_to)]
        
        # Calculate statistics
        total_expenses = crop_data[crop_data['transaction_type'] == 'expense']['amount'].sum()
        total_income = crop_data[crop_data['transaction_type'] == 'income']['amount'].sum()
        net_balance = total_income - total_expenses
        
        # Expenses by crop type
        expenses_by_crop = crop_data[crop_data['transaction_type'] == 'expense'].groupby('crop_type')['amount'].sum().reset_index()
        
        # Expenses by expense type
        expenses_by_type = crop_data[crop_data['transaction_type'] == 'expense'].groupby('expense_type')['amount'].sum().reset_index()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Crop Expenses", format_currency(total_expenses))
        with col2:
            st.metric("Total Crop Income", format_currency(total_income))
        with col3:
            st.metric("Crop Net Balance", format_currency(net_balance), delta_color="inverse")
        
        if not expenses_by_crop.empty:
            st.subheader("Expenses by Crop Type")
            fig1 = px.pie(expenses_by_crop, values='amount', names='crop_type', title='Crop Expenses Distribution')
            st.plotly_chart(fig1, use_container_width=True)
        
        if not expenses_by_type.empty:
            st.subheader("Expenses by Type")
            fig2 = px.bar(expenses_by_type, x='expense_type', y='amount', title='Expense Type Breakdown')
            st.plotly_chart(fig2, use_container_width=True)
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Crop Expenses (No Data)", format_currency(0))
        with col2:
            st.metric("Crop Income (No Data)", format_currency(0))
        with col3:
            st.metric("Crop Balance (No Data)", format_currency(0))

# Tab 3: Water Supply
with tabs[2]:
    st.markdown("<div class='section-card'><h3>💧 Water Supply to Farmers (کسانوں کو پانی کی سپلائی)</h3></div>", unsafe_allow_html=True)
    
    # Excel Import Section
    with st.expander("📤 Import Excel Data"):
        col1, col2 = st.columns(2)
        with col1:
            template_data = create_excel_template("water_supply")
            st.download_button(
                label="📥 Download Template",
                data=template_data,
                file_name="water_supply_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'], key="tab3_excel_upload")
            if uploaded_file:
                if st.button("Import Data", key="tab3_import"):
                    success, message = import_excel_data(uploaded_file, "water_supply")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
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
                st.session_state.water_supply_data = convert_dates(st.session_state.water_supply_data)
                save_data()
                st.success("Water supply record saved successfully!")
                st.rerun()
    
    # Water Supply Records with Edit/Delete
    st.markdown("<div class='section-card'><h3>📋 Water Supply Records (پانی سپلائی کے رکارڈز)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.water_supply_data.empty:
        display_df = st.session_state.water_supply_data.copy()
        display_df = convert_dates(display_df)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        for idx, row in display_df.iterrows():
            cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1])
            with cols[0]:
                st.write(row['id'])
            with cols[1]:
                st.write(row['farmer_name'])
            with cols[2]:
                st.write(row['farmer_phone'] if pd.notna(row['farmer_phone']) else "")
            with cols[3]:
                st.write(row['date'])
            with cols[4]:
                st.write(f"{row['hours']:.2f}")
            with cols[5]:
                st.write(format_currency(row['rate']))
            with cols[6]:
                st.write(format_currency(row['total_bill']))
            with cols[7]:
                st.write(format_currency(row['paid']))
            with cols[8]:
                balance = row['balance']
                st.write(format_currency(balance))
            with cols[9]:
                status = "Paid" if balance <= 0 else "Pending"
                st.write(status)
            with cols[10]:
                if st.button("✏️", key=f"edit_water_{row['id']}_{idx}"):
                    show_edit_modal("water_supply", row)
            with cols[11]:
                if st.button("🗑️", key=f"delete_water_{row['id']}_{idx}"):
                    if delete_record("water_supply", row['id']):
                        st.success(f"Record {row['id']} deleted successfully!")
                        st.rerun()
    else:
        st.info("No water supply records available.")
    
    # Payment Management Section (NEW)
    st.markdown("<div class='section-card'><h3>💰 Water Supply Payment Management</h3></div>", unsafe_allow_html=True)
    
    # Excel Import for Payments
    with st.expander("📤 Import Payment Excel Data"):
        col1, col2 = st.columns(2)
        with col1:
            template_data = create_excel_template("payments")
            st.download_button(
                label="📥 Download Template",
                data=template_data,
                file_name="payments_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'], key="tab3_payment_excel_upload")
            if uploaded_file:
                if st.button("Import Payment Data", key="tab3_payment_import"):
                    success, message = import_excel_data(uploaded_file, "payments")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    # Add new payment
    st.markdown("#### Add New Payment")
    
    # Get unique farmer names
    farmer_names = []
    if not st.session_state.water_supply_data.empty and 'farmer_name' in st.session_state.water_supply_data.columns:
        farmer_names = list(st.session_state.water_supply_data['farmer_name'].unique())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        payment_farmer = st.selectbox(
            "Select Farmer",
            [""] + farmer_names,
            key="tab3_payment_farmer"
        )
    
    with col2:
        payment_amount = st.number_input("Payment Amount", min_value=0.0, key="tab3_payment_amount")
    
    with col3:
        payment_method = st.selectbox(
            "Payment Method",
            ["Cash (نقد)", "Bank Transfer (بینک)", "Check (چیک)"],
            key="tab3_payment_method"
        )
    
    col4, col5 = st.columns(2)
    with col4:
        payment_date = st.date_input("Payment Date", value=date.today(), key="tab3_payment_date")
    
    with col5:
        payment_remarks = st.text_input("Remarks", key="tab3_payment_remarks")
    
    if st.button("💳 Record Payment", type="primary", key="tab3_record_payment"):
        if payment_farmer and payment_amount > 0:
            # Add to payments data
            new_payment = {
                'id': get_next_id('payment'),
                'farmer_name': payment_farmer,
                'amount': payment_amount,
                'payment_method': payment_method,
                'date': payment_date,
                'remarks': payment_remarks
            }
            st.session_state.payments_data = pd.concat([
                st.session_state.payments_data,
                pd.DataFrame([new_payment])
            ], ignore_index=True)
            
            # Update water supply balance
            if not st.session_state.water_supply_data.empty:
                mask = st.session_state.water_supply_data['farmer_name'] == payment_farmer
                if mask.any():
                    # Find unpaid bills
                    unpaid_bills = st.session_state.water_supply_data[mask & (st.session_state.water_supply_data['balance'] > 0)]
                    remaining_payment = payment_amount
                    
                    for _, bill in unpaid_bills.iterrows():
                        if remaining_payment <= 0:
                            break
                        
                        bill_idx = bill.name
                        current_balance = st.session_state.water_supply_data.loc[bill_idx, 'balance']
                        payment_to_apply = min(remaining_payment, current_balance)
                        
                        st.session_state.water_supply_data.loc[bill_idx, 'paid'] += payment_to_apply
                        st.session_state.water_supply_data.loc[bill_idx, 'balance'] -= payment_to_apply
                        remaining_payment -= payment_to_apply
            
            st.session_state.payments_data = convert_dates(st.session_state.payments_data)
            st.session_state.water_supply_data = convert_dates(st.session_state.water_supply_data)
            
            save_data()
            st.success("Payment recorded successfully!")
            st.rerun()
        else:
            st.error("Please select a farmer and enter payment amount")
    
    # Display Payment Records
    st.markdown("#### Payment Records")
    if not st.session_state.payments_data.empty:
        payment_display = st.session_state.payments_data.copy()
        payment_display = convert_dates(payment_display)
        payment_display['date'] = payment_display['date'].dt.strftime('%Y-%m-%d')
        
        for idx, row in payment_display.iterrows():
            cols = st.columns([1, 2, 2, 2, 2, 2, 1, 1])
            with cols[0]:
                st.write(row['id'])
            with cols[1]:
                st.write(row['farmer_name'])
            with cols[2]:
                st.write(row['date'])
            with cols[3]:
                st.write(format_currency(row['amount']))
            with cols[4]:
                st.write(row['payment_method'])
            with cols[5]:
                # Safely handle remarks column
                remarks_text = str(row['remarks']) if 'remarks' in row and pd.notna(row['remarks']) else ""
                st.write(remarks_text[:20] + '...' if len(remarks_text) > 20 else remarks_text)
            with cols[6]:
                if st.button("✏️", key=f"edit_payment_{row['id']}_{idx}"):
                    show_edit_modal("payments", row)
            with cols[7]:
                if st.button("🗑️", key=f"delete_payment_{row['id']}_{idx}"):
                    if delete_record("payments", row['id']):
                        st.success(f"Record {row['id']} deleted successfully!")
                        st.rerun()
    else:
        st.info("No payment records available.")

# Tab 4: Expenses
with tabs[3]:
    st.markdown("<div class='section-card'><h3>💰 Consolidated Expenses (کل اخراجات)</h3></div>", unsafe_allow_html=True)
    
    # Excel Import Section
    with st.expander("📤 Import Excel Data"):
        col1, col2 = st.columns(2)
        with col1:
            template_data = create_excel_template("expenses")
            st.download_button(
                label="📥 Download Template",
                data=template_data,
                file_name="expenses_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'], key="tab4_excel_upload")
            if uploaded_file:
                if st.button("Import Data", key="tab4_import"):
                    success, message = import_excel_data(uploaded_file, "expenses")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
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
                st.session_state.expenses_data = convert_dates(st.session_state.expenses_data)
                save_data()
                st.success("Expense added successfully!")
                st.rerun()
            else:
                st.error("Please fill all required fields")
    
    # Expenses Data Table with Edit/Delete
    st.markdown("<div class='section-card'><h3>📋 All Expenses (تمام اخراجات)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.expenses_data.empty:
        display_df = st.session_state.expenses_data.copy()
        display_df = convert_dates(display_df)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        for idx, row in display_df.iterrows():
            cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1, 1])
            with cols[0]:
                st.write(row['id'])
            with cols[1]:
                st.write(row['date'])
            with cols[2]:
                st.write(row['category'])
            with cols[3]:
                st.write(row['description'][:20] + '...' if len(str(row['description'])) > 20 else row['description'])
            with cols[4]:
                st.write(format_currency(row['amount']))
            with cols[5]:
                st.write(row['manager'])
            with cols[6]:
                st.write(row['receipt_no'] if pd.notna(row['receipt_no']) else "")
            with cols[7]:
                # Safely handle remarks column
                remarks_text = str(row['remarks']) if 'remarks' in row and pd.notna(row['remarks']) else ""
                st.write(remarks_text[:20] + '...' if len(remarks_text) > 20 else remarks_text)
            with cols[8]:
                if st.button("✏️", key=f"edit_expense_{row['id']}_{idx}"):
                    show_edit_modal("expenses", row)
            with cols[9]:
                if st.button("🗑️", key=f"delete_expense_{row['id']}_{idx}"):
                    if delete_record("expenses", row['id']):
                        st.success(f"Record {row['id']} deleted successfully!")
                        st.rerun()
    else:
        st.info("No expense records available.")
    
    # Expenses Statistics
    st.markdown("<div class='section-card'><h3>📊 Expense Statistics</h3></div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    if not st.session_state.expenses_data.empty:
        expenses_data = convert_dates(st.session_state.expenses_data)
        
        today = date.today()
        month_start = date(today.year, today.month, 1)
        
        with col1:
            today_expenses = expenses_data[
                expenses_data['date'].dt.date == today
            ]['amount'].sum()
            st.metric("Today's Expenses", format_currency(today_expenses))
        
        with col2:
            month_expenses = expenses_data[
                (expenses_data['date'].dt.date >= month_start) &
                (expenses_data['date'].dt.date <= today)
            ]['amount'].sum()
            st.metric("This Month Expenses", format_currency(month_expenses))
        
        with col3:
            total_expenses = expenses_data['amount'].sum()
            st.metric("Total Expenses", format_currency(total_expenses))
        
        # Expenses by category chart
        st.markdown("#### Expenses by Category")
        expenses_by_category = expenses_data.groupby('category')['amount'].sum().reset_index()
        if not expenses_by_category.empty:
            fig = px.pie(expenses_by_category, values='amount', names='category', title='Expense Distribution by Category')
            st.plotly_chart(fig, use_container_width=True)
    else:
        with col1:
            st.metric("Today's Expenses (No Data)", format_currency(0))
        with col2:
            st.metric("This Month Expenses (No Data)", format_currency(0))
        with col3:
            st.metric("Total Expenses (No Data)", format_currency(0))

# Tab 5: Income
with tabs[4]:
    st.markdown("<div class='section-card'><h3>📈 Income</h3></div>", unsafe_allow_html=True)
    
    # Excel Import Section
    with st.expander("📤 Import Excel Data"):
        col1, col2 = st.columns(2)
        with col1:
            template_data = create_excel_template("income")
            st.download_button(
                label="📥 Download Template",
                data=template_data,
                file_name="income_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        with col2:
            uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx'], key="tab5_excel_upload")
            if uploaded_file:
                if st.button("Import Data", key="tab5_import"):
                    success, message = import_excel_data(uploaded_file, "income")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
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
                st.session_state.income_data = convert_dates(st.session_state.income_data)
                save_data()
                st.success("Income recorded successfully!")
                st.rerun()
            else:
                st.error("Please fill all required fields")
    
    # Income Data Table with Edit/Delete
    st.markdown("<div class='section-card'><h3>📋 Income Records (آمدنی کے رکارڈز)</h3></div>", unsafe_allow_html=True)
    
    if not st.session_state.income_data.empty:
        display_df = st.session_state.income_data.copy()
        display_df = convert_dates(display_df)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        for idx, row in display_df.iterrows():
            cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1, 1])
            with cols[0]:
                st.write(row['id'])
            with cols[1]:
                st.write(row['date'])
            with cols[2]:
                st.write(row['source'])
            with cols[3]:
                st.write(format_currency(row['amount']))
            with cols[4]:
                st.write(row['received_by'] if pd.notna(row['received_by']) else "")
            with cols[5]:
                st.write(row['customer'] if pd.notna(row['customer']) else "")
            with cols[6]:
                st.write(row['receipt_no'] if pd.notna(row['receipt_no']) else "")
            with cols[7]:
                # Safely handle remarks column
                remarks_text = str(row['remarks']) if 'remarks' in row and pd.notna(row['remarks']) else ""
                st.write(remarks_text[:20] + '...' if len(remarks_text) > 20 else remarks_text)
            with cols[8]:
                if st.button("✏️", key=f"edit_income_{row['id']}_{idx}"):
                    show_edit_modal("income", row)
            with cols[9]:
                if st.button("🗑️", key=f"delete_income_{row['id']}_{idx}"):
                    if delete_record("income", row['id']):
                        st.success(f"Record {row['id']} deleted successfully!")
                        st.rerun()
    else:
        st.info("No income records available.")
    
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
        st.metric("Livestock Income", format_currency(livestock_income))
    
    with col2:
        st.metric("Crop Income", format_currency(crop_income))
    
    with col3:
        st.metric("Water Supply Income", format_currency(water_income))
    
    with col4:
        st.metric("Total Income", format_currency(total_income))
    
    # Income by source chart
    st.markdown("#### Income by Source")
    if not st.session_state.income_data.empty:
        income_by_source = income_data.groupby('source')['amount'].sum().reset_index()
        if not income_by_source.empty:
            fig = px.pie(income_by_source, values='amount', names='source', title='Income Distribution by Source')
            st.plotly_chart(fig, use_container_width=True)
# Tab 6: Reports
with tabs[5]:
    st.markdown("<div class='section-card'><h3>📊 Comprehensive Reports (جامع رپورٹس)</h3></div>", unsafe_allow_html=True)
    
    # Report Configuration Section
    with st.container():
        st.markdown("### Report Configuration (رپورٹ ترتیب)")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            report_type = st.selectbox(
                "Report Type (رپورٹ کی قسم)",
                ["Summary Report", "Expense Report", "Income Report", 
                 "Livestock Report", "Crops Report", "Water Report", 
                 "Financial Statement", "Performance Analysis"],
                key="tab6_report_type"
            )
        
        with col2:
            report_category = st.selectbox(
                "Category (زمرہ)",
                ["All (سب)", "Livestock (مویشی)", "Crop (فصل)", "Water (پانی)", "Financial (مالی)"],
                key="tab6_report_category"
            )
        
        with col3:
            report_date_from = st.date_input("From Date (تاریخ سے)", key="tab6_report_date_from", value=None)
        
        with col4:
            report_date_to = st.date_input("To Date (تاریخ تک)", key="tab6_report_date_to", value=None)
    
    # Action Buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📈 Generate Report", type="primary", use_container_width=True, key="tab6_generate_report"):
            st.session_state.generate_report = True
            st.session_state.report_generated = False
    
    with col2:
        if st.button("🔄 Reset Filters", use_container_width=True, key="tab6_reset_filters"):
            st.session_state.generate_report = False
            st.rerun()
    
    with col3:
        st.download_button(
            label="📄 Quick Export CSV",
            data="",
            file_name="report.csv",
            disabled=True,
            use_container_width=True,
            key="tab6_quick_export"
        )
    
    with col4:
        if st.button("📊 Preview Data", use_container_width=True, key="tab6_preview"):
            st.session_state.preview_data = True

    # Report Preview
    if st.session_state.get('generate_report', False):
        st.markdown("<div class='section-card'><h3>📄 Report Preview (رپورٹ پیش نظارہ)</h3></div>", unsafe_allow_html=True)
        
        # Calculate summary statistics with date filtering
        income_data_filtered = st.session_state.income_data.copy()
        water_data_filtered = st.session_state.water_supply_data.copy()
        expenses_data_filtered = st.session_state.expenses_data.copy()
        livestock_data_filtered = st.session_state.livestock_data.copy()
        crop_data_filtered = st.session_state.crop_data.copy()
        
        # Apply date filters if provided
        def filter_by_date(df, date_col='date'):
            df = convert_dates(df.copy())
            if 'date' not in df.columns:
                return df
            if report_date_from:
                df = df[df['date'] >= pd.Timestamp(report_date_from)]
            if report_date_to:
                df = df[df['date'] <= pd.Timestamp(report_date_to)]
            return df
        
        income_data_filtered = filter_by_date(income_data_filtered)
        water_data_filtered = filter_by_date(water_data_filtered)
        expenses_data_filtered = filter_by_date(expenses_data_filtered)
        livestock_data_filtered = filter_by_date(livestock_data_filtered)
        crop_data_filtered = filter_by_date(crop_data_filtered)
        
        # Apply category filter
        if report_category != "All (سب)":
            category_map = {
                "Livestock (مویشی)": "Livestock",
                "Crop (فصل)": "Crop",
                "Water (پانی)": "Water",
                "Financial (مالی)": "Financial"
            }
            selected_category = category_map.get(report_category, "")
            
            if selected_category == "Livestock":
                income_data_filtered = income_data_filtered[
                    income_data_filtered['source'].astype(str).str.contains('Livestock|Goats|Beef|Cows', na=False, case=False)
                ]
            elif selected_category == "Crop":
                income_data_filtered = income_data_filtered[
                    income_data_filtered['source'].astype(str).str.contains('Crop', na=False, case=False)
                ]
                expenses_data_filtered = expenses_data_filtered[
                    expenses_data_filtered['category'].astype(str).str.contains('Crop', na=False, case=False)
                ]
            elif selected_category == "Water":
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
        
        # Create report summary
        report_summary = {
            "report_type": report_type,
            "date_range": f"{report_date_from} to {report_date_to}" if report_date_from and report_date_to else "All Dates",
            "category": report_category,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "profit_margin": profit_margin,
            "generated_date": date.today().strftime("%Y-%m-%d")
        }
        
        # Store report data in session state for PDF generation
        st.session_state.report_data = {
            'summary': report_summary,
            'income': income_data_filtered,
            'expenses': expenses_data_filtered,
            'livestock': livestock_data_filtered,
            'crops': crop_data_filtered,
            'water': water_data_filtered
        }
        
        # Display financial summary in a styled container
        with st.container():
            st.markdown("### Financial Summary (مالی خلاصہ)")
            summary_cols = st.columns(4)
            
            metrics_config = [
                ("Total Income", format_currency(total_income), "📈", "#2ecc71"),
                ("Total Expenses", format_currency(total_expenses), "📉", "#e74c3c"),
                ("Net Profit", format_currency(net_profit), "💰", "#f39c12"),
                ("Profit Margin", f"{profit_margin:.2f}%", "📊", "#3498db")
            ]
            
            for idx, (title, value, icon, color) in enumerate(metrics_config):
                with summary_cols[idx]:
                    st.markdown(f"""
                    <div style="background-color: {color}20; padding: 15px; border-radius: 10px; border-left: 5px solid {color}; margin: 5px 0;">
                        <div style="font-size: 12px; color: #7f8c8d;">{title}</div>
                        <div style="font-size: 24px; font-weight: bold; color: {color};">{icon} {value}</div>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Report-specific content
        st.markdown("---")
        
        if report_type == "Summary Report":
            st.markdown("### Detailed Breakdown")
            
            tab1, tab2, tab3, tab4 = st.tabs(["📊 Income Analysis", "💸 Expense Analysis", "📈 Trends", "📋 Data Tables"])
            
            with tab1:
                if not income_data_filtered.empty:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.subheader("Income by Source")
                        income_by_source = income_data_filtered.groupby('source')['amount'].sum().reset_index()
                        if not income_by_source.empty:
                            fig1 = px.pie(
                                income_by_source,
                                values='amount',
                                names='source',
                                title='Income Distribution by Source',
                                color_discrete_sequence=px.colors.sequential.Blues_r
                            )
                            st.plotly_chart(fig1, use_container_width=True)
                    
                    with col2:
                        st.subheader("Top Income Sources")
                        top_income = income_by_source.nlargest(5, 'amount')
                        fig2 = px.bar(
                            top_income,
                            x='source',
                            y='amount',
                            title='Top 5 Income Sources',
                            color='amount',
                            color_continuous_scale='Viridis'
                        )
                        st.plotly_chart(fig2, use_container_width=True)
            
            with tab2:
                if not expenses_data_filtered.empty:
                    st.subheader("Expenses by Category")
                    expenses_by_category = expenses_data_filtered.groupby('category')['amount'].sum().reset_index()
                    if not expenses_by_category.empty:
                        fig2 = px.bar(
                            expenses_by_category,
                            x='category',
                            y='amount',
                            title='Expenses Breakdown',
                            color='amount',
                            color_continuous_scale='Reds'
                        )
                        st.plotly_chart(fig2, use_container_width=True)
            
            with tab3:
                # Time series analysis
                if not income_data_filtered.empty:
                    income_data_filtered['date'] = pd.to_datetime(income_data_filtered['date'])
                    monthly_income = income_data_filtered.resample('M', on='date')['amount'].sum().reset_index()
                    fig3 = px.line(
                        monthly_income,
                        x='date',
                        y='amount',
                        title='Monthly Income Trend',
                        markers=True
                    )
                    st.plotly_chart(fig3, use_container_width=True)
            
            with tab4:
                st.dataframe(income_data_filtered.head(20), use_container_width=True)
        
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
        
        # Export options section
        st.markdown("---")
        st.markdown("### Export Options (برآمد کے اختیارات)")
        
        # Create two columns for export buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export to CSV
            @st.cache_data
            def convert_df_to_csv(df):
                return df.to_csv(index=False, encoding='utf-8-sig')
            
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
                csv_data = convert_df_to_csv(export_df)
                st.download_button(
                    label="📥 Download CSV",
                    data=csv_data,
                    file_name=f"{report_type.replace(' ', '_')}_{date.today()}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    help="Export data in CSV format for Excel/Google Sheets"
                )
            else:
                st.button("📥 Download CSV", disabled=True, use_container_width=True)
        
        with col2:
            # Export to Excel
            if not export_df.empty:
                @st.cache_data
                def convert_df_to_excel(df):
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        df.to_excel(writer, index=False, sheet_name='Report')
                    return output.getvalue()
                
                excel_data = convert_df_to_excel(export_df)
                st.download_button(
                    label="📊 Download Excel",
                    data=excel_data,
                    file_name=f"{report_type.replace(' ', '_')}_{date.today()}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    help="Export data in Excel format with better formatting"
                )
            else:
                st.button("📊 Download Excel", disabled=True, use_container_width=True)
        
        with col3:
            # PDF Export with simple template
if not export_df.empty:
    # Create simple PDF generation function
    def generate_simple_pdf():
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO
        from reportlab.lib import colors
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20, bottomMargin=20)
        elements = []
        
        # Simple styles
        styles = getSampleStyleSheet()
        
        # Title
        elements.append(Paragraph(f"{report_type}", styles['Title']))
        elements.append(Paragraph(f"Date: {date.today().strftime('%Y-%m-%d')}", styles['Normal']))
        if report_date_from and report_date_to:
            elements.append(Paragraph(f"Period: {report_date_from} to {report_date_to}", styles['Normal']))
        elements.append(Spacer(1, 15))
        
        # Summary Section
        elements.append(Paragraph("Summary", styles['Heading2']))
        
        # Simple summary table
        summary_data = [
            ["Total Income", format_currency(total_income)],
            ["Total Expenses", format_currency(total_expenses)],
            ["Net Profit", format_currency(net_profit)],
            ["Profit Margin", f"{profit_margin:.2f}%"],
            ["Category", report_category],
            ["Total Records", len(export_df)]
        ]
        
        summary_table = Table(summary_data, colWidths=[200, 200])
        summary_table.setStyle(TableStyle([
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 15))
        
        # Data Table Section
        elements.append(Paragraph("Data Details", styles['Heading2']))
        
        # Limit rows for PDF
        pdf_df = export_df.head(100).copy()
        
        # Prepare table data
        table_data = [pdf_df.columns.tolist()] + pdf_df.values.tolist()
        
        # Simple table
        data_table = Table(table_data, repeatRows=1)
        data_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(data_table)
        
        # Simple footer
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Generated on {date.today().strftime('%Y-%m-%d %H:%M')}", 
                                 styles['Italic']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    # Download PDF button - SIMPLIFIED
    if st.button("📄 Download PDF", use_container_width=True, key="tab6_download_pdf"):
        try:
            with st.spinner("Generating PDF..."):
                pdf_bytes = generate_simple_pdf()
                st.download_button(
                    label="⬇️ Download PDF File",
                    data=pdf_bytes,
                    file_name=f"{report_type.replace(' ', '_')}_{date.today().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            st.success("PDF generated successfully!")
        except Exception as e:
            st.error(f"Error: {str(e)}")
            st.info("Install required packages: pip install reportlab")
        # Additional actions row
        st.markdown("---")
        action_col1, action_col2 = st.columns(2)
        
        with action_col1:
            if st.button("🖨️ Print Report", use_container_width=True, key="tab6_print"):
                st.info("Use your browser's print function (Ctrl+P) to print this report")
        
        with action_col2:
            if st.button("🗑️ Clear Report", use_container_width=True, key="tab6_clear_report"):
                st.session_state.generate_report = False
                st.session_state.report_data = None
                st.rerun()
        
        # Report statistics
        with st.expander("📊 Report Statistics"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Income Records", len(income_data_filtered))
            with col2:
                st.metric("Expense Records", len(expenses_data_filtered))
            with col3:
                st.metric("Total Records", len(export_df))
# Tab 7: Farmer Ledger Details - FIXED VERSION
with tabs[6]:
    st.markdown("<div class='section-card'><h3>👤 Farmer Ledger Details (کسان کھاتا کی تفصیل)</h3></div>", unsafe_allow_html=True)
    
    # Select Farmer
    col1, col2 = st.columns([2, 1])
    with col1:
        # Get unique farmer names from water supply and payments data
        water_farmers = []
        payment_farmers = []
        
        if not st.session_state.water_supply_data.empty and 'farmer_name' in st.session_state.water_supply_data.columns:
            water_farmers = list(st.session_state.water_supply_data['farmer_name'].unique())
        
        if not st.session_state.payments_data.empty and 'farmer_name' in st.session_state.payments_data.columns:
            payment_farmers = list(st.session_state.payments_data['farmer_name'].unique())
        
        all_farmers = list(set(water_farmers + payment_farmers))
        
        selected_farmer = st.selectbox(
            "Select Farmer (کسان منتخب کریں)",
            [""] + all_farmers,
            key="tab7_select_farmer"
        )
    
    with col2:
        if st.button("🔍 View Ledger", type="primary", use_container_width=True, key="tab7_view_ledger"):
            if selected_farmer:
                st.session_state.selected_farmer_ledger = selected_farmer
            else:
                st.warning("Please select a farmer first")
    
    # Display Farmer Ledger
    if st.session_state.selected_farmer_ledger:
        farmer_name = st.session_state.selected_farmer_ledger
        ledger_details = get_farmer_ledger_details(farmer_name)
        
        if ledger_details:
            st.markdown(f"### 📊 Ledger for {farmer_name}")
            
            # Summary Cards
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Water Bill", format_currency(ledger_details['total_water_bill']))
            with col2:
                st.metric("Total Paid", format_currency(ledger_details['total_paid']))
            with col3:
                st.metric("Additional Payments", format_currency(ledger_details['total_payments']))
            with col4:
                balance_color = "normal"
                if ledger_details['current_balance'] > 0:
                    balance_color = "inverse"
                st.metric("Current Balance", format_currency(ledger_details['current_balance']), delta_color=balance_color)
            
            # Water Supply Records - FIXED: No remarks column
            st.markdown("#### 💧 Water Supply Records")
            if not ledger_details['water_records'].empty:
                water_display = ledger_details['water_records'].copy()
                water_display = convert_dates(water_display)
                water_display['date'] = water_display['date'].dt.strftime('%Y-%m-%d')
                water_display['status'] = water_display['balance'].apply(lambda x: 'Paid' if x <= 0 else 'Pending')
                
                # Display water records - FIXED: 10 columns without remarks
                for idx, row in water_display.iterrows():
                    cols = st.columns([1, 2, 2, 2, 2, 2, 2, 2, 1, 1])  # 10 columns
                    with cols[0]:
                        st.write(row['id'])
                    with cols[1]:
                        st.write(row['date'])
                    with cols[2]:
                        st.write(f"{row['hours']:.2f}")
                    with cols[3]:
                        st.write(format_currency(row['rate']))
                    with cols[4]:
                        st.write(format_currency(row['total_bill']))
                    with cols[5]:
                        st.write(format_currency(row['paid']))
                    with cols[6]:
                        st.write(format_currency(row['balance']))
                    with cols[7]:
                        st.write(row['status'])
                    with cols[8]:
                        if st.button("✏️", key=f"tab7_edit_water_{row['id']}_{idx}"):
                            show_edit_modal("water_supply", row)
                    with cols[9]:
                        if st.button("🗑️", key=f"tab7_delete_water_{row['id']}_{idx}"):
                            if delete_record("water_supply", row['id']):
                                st.success(f"Record {row['id']} deleted successfully!")
                                st.rerun()
            else:
                st.info("No water supply records found for this farmer.")
            
            # Payment Records - FIXED: With remarks column
            st.markdown("#### 💰 Payment History")
            if not ledger_details['payment_records'].empty:
                payment_display = ledger_details['payment_records'].copy()
                payment_display = convert_dates(payment_display)
                payment_display['date'] = payment_display['date'].dt.strftime('%Y-%m-%d')
                
                # Display payment records - FIXED: 7 columns with remarks
                for idx, row in payment_display.iterrows():
                    cols = st.columns([1, 2, 2, 2, 2, 1, 1])  # 7 columns
                    with cols[0]:
                        st.write(row['id'])
                    with cols[1]:
                        st.write(row['date'])
                    with cols[2]:
                        st.write(format_currency(row['amount']))
                    with cols[3]:
                        st.write(row['payment_method'] if pd.notna(row['payment_method']) else "")
                    with cols[4]:
                        # Safely handle remarks column
                        remarks_text = str(row['remarks']) if 'remarks' in row and pd.notna(row['remarks']) else ""
                        st.write(remarks_text[:20] + '...' if len(remarks_text) > 20 else remarks_text)
                    with cols[5]:
                        if st.button("✏️", key=f"tab7_edit_payment_{row['id']}_{idx}"):
                            show_edit_modal("payments", row)
                    with cols[6]:
                        if st.button("🗑️", key=f"tab7_delete_payment_{row['id']}_{idx}"):
                            if delete_record("payments", row['id']):
                                st.success(f"Record {row['id']} deleted successfully!")
                                st.rerun()
            else:
                st.info("No payment records found for this farmer.")
            
            # Add New Payment Section
            st.markdown("---")
            st.markdown("#### 📝 Add New Payment")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                new_payment_amount = st.number_input("Payment Amount", min_value=0.0, key="tab7_new_payment_amount")
            
            with col2:
                new_payment_date = st.date_input("Payment Date", value=date.today(), key="tab7_new_payment_date")
            
            with col3:
                new_payment_method = st.selectbox(
                    "Payment Method",
                    ["Cash (نقد)", "Bank Transfer (بینک)", "Check (چیک)"],
                    key="tab7_new_payment_method"
                )
            
            with col4:
                new_payment_remarks = st.text_input("Remarks", key="tab7_new_payment_remarks")
            
            if st.button("💳 Record Payment", type="primary", key="tab7_record_payment"):
                if new_payment_amount > 0:
                    new_payment = {
                        'id': get_next_id('payment'),
                        'farmer_name': farmer_name,
                        'amount': new_payment_amount,
                        'payment_method': new_payment_method,
                        'date': new_payment_date,
                        'remarks': new_payment_remarks
                    }
                    st.session_state.payments_data = pd.concat([
                        st.session_state.payments_data,
                        pd.DataFrame([new_payment])
                    ], ignore_index=True)
                    
                    # Update water supply balance
                    if not st.session_state.water_supply_data.empty and 'farmer_name' in st.session_state.water_supply_data.columns:
                        mask = st.session_state.water_supply_data['farmer_name'] == farmer_name
                        if mask.any():
                            # Find the oldest unpaid bill to apply payment
                            unpaid_bills = st.session_state.water_supply_data[mask & (st.session_state.water_supply_data['balance'] > 0)]
                            if not unpaid_bills.empty:
                                # Apply payment to the oldest unpaid bill
                                oldest_bill_idx = unpaid_bills.index[0]
                                current_balance = st.session_state.water_supply_data.loc[oldest_bill_idx, 'balance']
                                payment_to_apply = min(new_payment_amount, current_balance)
                                
                                st.session_state.water_supply_data.loc[oldest_bill_idx, 'paid'] += payment_to_apply
                                st.session_state.water_supply_data.loc[oldest_bill_idx, 'balance'] -= payment_to_apply
                    
                    st.session_state.payments_data = convert_dates(st.session_state.payments_data)
                    st.session_state.water_supply_data = convert_dates(st.session_state.water_supply_data)
                    
                    save_data()
                    st.success("Payment recorded successfully!")
                    st.rerun()
                else:
                    st.error("Please enter a valid payment amount")
        else:
            st.info("No ledger details available for this farmer.")
    else:
        st.info("👈 Select a farmer and click 'View Ledger' to see details")

# Edit Modal
if st.session_state.show_edit_modal and st.session_state.editing_record is not None:
    # Create a container for the modal
    modal_container = st.container()
    with modal_container:
        # Add some custom CSS to create modal effect
        st.markdown("""
        <style>
        .modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
            z-index: 1000;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .modal-content {
            background: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 800px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 20px 40px rgba(0,0,0,0.3);
            z-index: 1001;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="modal-backdrop">', unsafe_allow_html=True)
        st.markdown('<div class="modal-content">', unsafe_allow_html=True)
        
        tab_name = st.session_state.editing_tab
        record = st.session_state.editing_record
        
        st.markdown(f"### ✏️ Edit Record #{record['id']}")
        
        if tab_name == "livestock":
            col1, col2 = st.columns(2)
            with col1:
                edit_date = st.date_input("Date", value=pd.to_datetime(record['date']).date() if pd.notna(record['date']) else date.today(), key="edit_livestock_date")
                edit_category = st.selectbox("Category", ["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Others (دیگر)"], 
                                            index=0, key="edit_livestock_category")
                if 'category' in record:
                    if record['category'] == "Cow (گائے)":
                        edit_category = "Cow (گائے)"
                    elif record['category'] == "Beef (بیف)":
                        edit_category = "Beef (بیف)"
                    elif record['category'] == "Goat (بکری)":
                        edit_category = "Goat (بکری)"
                    else:
                        edit_category = "Others (دیگر)"
            with col2:
                edit_amount = st.number_input("Amount", value=float(record['amount']) if 'amount' in record else 0.0, key="edit_livestock_amount")
                edit_manager = st.selectbox("Manager", [m["name"] for m in st.session_state.managers],
                                           index=0, key="edit_livestock_manager")
                if 'manager' in record:
                    for i, manager in enumerate(st.session_state.managers):
                        if manager["name"] == record['manager']:
                            edit_manager = manager["name"]
                            break
            
            edit_remarks = st.text_area("Remarks", value=record['remarks'] if 'remarks' in record else "", key="edit_livestock_remarks")
        
        elif tab_name == "crop":
            col1, col2 = st.columns(2)
            with col1:
                edit_date = st.date_input("Date", value=pd.to_datetime(record['date']).date() if pd.notna(record['date']) else date.today(), key="edit_crop_date")
                edit_crop_type = st.selectbox("Crop Type", ["Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)", "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", "Others (دیگر)"],
                                             index=0, key="edit_crop_type")
                if 'crop_type' in record:
                    crop_types = ["Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)", "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", "Others (دیگر)"]
                    if record['crop_type'] in crop_types:
                        edit_crop_type = record['crop_type']
            with col2:
                edit_amount = st.number_input("Amount", value=float(record['amount']) if 'amount' in record else 0.0, key="edit_crop_amount")
                edit_manager = st.selectbox("Manager", [m["name"] for m in st.session_state.managers],
                                           index=0, key="edit_crop_manager")
                if 'manager' in record:
                    for i, manager in enumerate(st.session_state.managers):
                        if manager["name"] == record['manager']:
                            edit_manager = manager["name"]
                            break
            
            edit_remarks = st.text_area("Remarks", value=record['remarks'] if 'remarks' in record else "", key="edit_crop_remarks")
        
        elif tab_name == "water_supply":
            col1, col2, col3 = st.columns(3)
            with col1:
                edit_date = st.date_input("Date", value=pd.to_datetime(record['date']).date() if pd.notna(record['date']) else date.today(), key="edit_water_date")
                edit_farmer_name = st.text_input("Farmer Name", value=record['farmer_name'] if 'farmer_name' in record else "", key="edit_water_farmer")
            with col2:
                edit_hours = st.number_input("Hours", value=float(record['hours']) if 'hours' in record else 0.0, key="edit_water_hours")
                edit_rate = st.number_input("Rate", value=float(record['rate']) if 'rate' in record else 0.0, key="edit_water_rate")
            with col3:
                edit_paid = st.number_input("Paid", value=float(record['paid']) if 'paid' in record else 0.0, key="edit_water_paid")
                edit_total_bill = st.number_input("Total Bill", value=float(record['total_bill']) if 'total_bill' in record else 0.0, key="edit_water_total")
        
        elif tab_name == "expenses":
            col1, col2 = st.columns(2)
            with col1:
                edit_date = st.date_input("Date", value=pd.to_datetime(record['date']).date() if pd.notna(record['date']) else date.today(), key="edit_expense_date")
                edit_category = st.selectbox("Category", ["Salary (تنخواہ)", "Machinery (مشینری)", "Fuel (پیٹرول/ڈیزل)", "Maintenance (مرمت)", "Kitchen", "Construction", "Petrol", "Diesel", "Electricity Bill", "Turbine Bill", "Others (دیگر)"],
                                            index=0, key="edit_expense_category")
                if 'category' in record:
                    categories = ["Salary (تنخواہ)", "Machinery (مشینری)", "Fuel (پیٹرول/ڈیزل)", "Maintenance (مرمت)", "Kitchen", "Construction", "Petrol", "Diesel", "Electricity Bill", "Turbine Bill", "Others (دیگر)"]
                    if record['category'] in categories:
                        edit_category = record['category']
            with col2:
                edit_amount = st.number_input("Amount", value=float(record['amount']) if 'amount' in record else 0.0, key="edit_expense_amount")
                edit_manager = st.selectbox("Manager", [m["name"] for m in st.session_state.managers],
                                           index=0, key="edit_expense_manager")
                if 'manager' in record:
                    for i, manager in enumerate(st.session_state.managers):
                        if manager["name"] == record['manager']:
                            edit_manager = manager["name"]
                            break
            
            edit_description = st.text_input("Description", value=record['description'] if 'description' in record else "", key="edit_expense_desc")
            edit_remarks = st.text_area("Remarks", value=record['remarks'] if 'remarks' in record else "", key="edit_expense_remarks")
        
        elif tab_name == "income":
            col1, col2 = st.columns(2)
            with col1:
                edit_date = st.date_input("Date", value=pd.to_datetime(record['date']).date() if pd.notna(record['date']) else date.today(), key="edit_income_date")
                edit_source = st.selectbox("Source", ["Livestock Sale", "Goats", "Beef", "Cows", "Crop Sale", "Water Supply", "Others"],
                                          index=0, key="edit_income_source")
                if 'source' in record:
                    sources = ["Livestock Sale", "Goats", "Beef", "Cows", "Crop Sale", "Water Supply", "Others"]
                    if record['source'] in sources:
                        edit_source = record['source']
            with col2:
                edit_amount = st.number_input("Amount", value=float(record['amount']) if 'amount' in record else 0.0, key="edit_income_amount")
                edit_received_by = st.selectbox("Received By", [m["name"] for m in st.session_state.managers],
                                               index=0, key="edit_income_received")
                if 'received_by' in record:
                    for i, manager in enumerate(st.session_state.managers):
                        if manager["name"] == record['received_by']:
                            edit_received_by = manager["name"]
                            break
            
            edit_customer = st.text_input("Customer", value=record['customer'] if 'customer' in record else "", key="edit_income_customer")
            edit_remarks = st.text_area("Remarks", value=record['remarks'] if 'remarks' in record else "", key="edit_income_remarks")
        
        elif tab_name == "payments":
            col1, col2 = st.columns(2)
            with col1:
                edit_date = st.date_input("Date", value=pd.to_datetime(record['date']).date() if pd.notna(record['date']) else date.today(), key="edit_payment_date")
                edit_farmer_name = st.text_input("Farmer Name", value=record['farmer_name'] if 'farmer_name' in record else "", key="edit_payment_farmer")
            with col2:
                edit_amount = st.number_input("Amount", value=float(record['amount']) if 'amount' in record else 0.0, key="edit_payment_amount")
                edit_method = st.selectbox("Payment Method", ["Cash (نقد)", "Bank Transfer (بینک)", "Check (چیک)"],
                                          index=0, key="edit_payment_method")
                if 'payment_method' in record:
                    methods = ["Cash (نقد)", "Bank Transfer (بینک)", "Check (چیک)"]
                    if record['payment_method'] in methods:
                        edit_method = record['payment_method']
            
            edit_remarks = st.text_area("Remarks", value=record['remarks'] if 'remarks' in record else "", key="edit_payment_remarks")
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("💾 Save Changes", type="primary", use_container_width=True, key="modal_save"):
                # Prepare updated data
                updated_data = {}
                
                if tab_name == "livestock":
                    updated_data = {
                        'date': edit_date,
                        'category': edit_category,
                        'amount': edit_amount,
                        'manager': edit_manager,
                        'remarks': edit_remarks
                    }
                elif tab_name == "crop":
                    updated_data = {
                        'date': edit_date,
                        'crop_type': edit_crop_type,
                        'amount': edit_amount,
                        'manager': edit_manager,
                        'remarks': edit_remarks
                    }
                elif tab_name == "water_supply":
                    updated_data = {
                        'date': edit_date,
                        'farmer_name': edit_farmer_name,
                        'hours': edit_hours,
                        'rate': edit_rate,
                        'total_bill': edit_total_bill,
                        'paid': edit_paid,
                        'balance': edit_total_bill - edit_paid
                    }
                elif tab_name == "expenses":
                    updated_data = {
                        'date': edit_date,
                        'category': edit_category,
                        'description': edit_description,
                        'amount': edit_amount,
                        'manager': edit_manager,
                        'remarks': edit_remarks
                    }
                elif tab_name == "income":
                    updated_data = {
                        'date': edit_date,
                        'source': edit_source,
                        'amount': edit_amount,
                        'received_by': edit_received_by,
                        'customer': edit_customer,
                        'remarks': edit_remarks
                    }
                elif tab_name == "payments":
                    updated_data = {
                        'date': edit_date,
                        'farmer_name': edit_farmer_name,
                        'amount': edit_amount,
                        'payment_method': edit_method,
                        'remarks': edit_remarks
                    }
                
                # Update the record
                if update_record(tab_name, record['id'], updated_data):
                    st.success("Record updated successfully!")
                    st.session_state.show_edit_modal = False
                    st.session_state.editing_record = None
                    st.session_state.editing_tab = None
                    st.rerun()
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True, key="modal_cancel"):
                st.session_state.show_edit_modal = False
                st.session_state.editing_record = None
                st.session_state.editing_tab = None
                st.rerun()
        
        with col3:
            if st.button("🗑️ Delete", type="secondary", use_container_width=True, key="modal_delete"):
                if delete_record(tab_name, record['id']):
                    st.success("Record deleted successfully!")
                    st.session_state.show_edit_modal = False
                    st.session_state.editing_record = None
                    st.session_state.editing_tab = None
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

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
        len(st.session_state.income_data) +
        len(st.session_state.payments_data)
    )
    
    st.metric("System Total Records", total_records)
    
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
