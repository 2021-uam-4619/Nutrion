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
import json
import os
from io import BytesIO
import tempfile

# Page configuration
st.set_page_config(
    page_title="Complete Farm Management System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional look
st.markdown("""
<style>
    /* Main Styles */
    .main-header {
        font-size: 2.8rem;
        color: #2c3e50;
        text-align: center;
        margin-bottom: 1.5rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .sub-header {
        font-size: 1.8rem;
        color: #34495e;
        margin-bottom: 1.5rem;
        font-weight: 700;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
    }
    
    .section-card {
        background: white;
        padding: 25px;
        border-radius: 15px;
        margin-bottom: 25px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border-left: 6px solid #3498db;
        transition: all 0.3s ease;
    }
    
    .section-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.12);
    }
    
    /* Button Styles */
    .stButton > button {
        border-radius: 8px;
        padding: 12px 24px;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s ease;
        border: none;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .btn-success {
        background: linear-gradient(135deg, #27ae60, #219653) !important;
        color: white !important;
    }
    
    .btn-primary {
        background: linear-gradient(135deg, #3498db, #2980b9) !important;
        color: white !important;
    }
    
    .btn-warning {
        background: linear-gradient(135deg, #f39c12, #e67e22) !important;
        color: white !important;
    }
    
    .btn-danger {
        background: linear-gradient(135deg, #e74c3c, #c0392b) !important;
        color: white !important;
    }
    
    .btn-info {
        background: linear-gradient(135deg, #17a2b8, #138496) !important;
        color: white !important;
    }
    
    /* Form Styles */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div,
    .stDateInput > div > div > input,
    .stTimeInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 2px solid #ddd;
        padding: 12px;
        font-size: 16px;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus,
    .stDateInput > div > div > input:focus,
    .stTimeInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #3498db;
        box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.2);
    }
    
    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff, #f8f9fa);
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.08);
        border-top: 4px solid #3498db;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.12);
    }
    
    /* Dataframe Styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Status Messages */
    .stAlert {
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
    }
    
    /* Sidebar Styling */
    .css-1d391kg {
        background: linear-gradient(135deg, #2c3e50, #34495e);
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #3498db !important;
        color: white !important;
        border-color: #3498db !important;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database with proper structure
def init_database():
    conn = sqlite3.connect('farm_management.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # Drop tables if they exist to start fresh
    tables = ['livestock', 'crops', 'water_supply', 'expenses', 'income', 'managers', 'farmers', 'water_payments', 'import_logs']
    for table in tables:
        try:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        except:
            pass
    
    # Livestock table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS livestock (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity REAL DEFAULT 0,
            expense_type TEXT,
            amount REAL NOT NULL,
            manager TEXT NOT NULL,
            remarks TEXT,
            transaction_type TEXT CHECK(transaction_type IN ('expense', 'income')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crop table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            crop_type TEXT NOT NULL,
            area REAL DEFAULT 0,
            expense_type TEXT,
            amount REAL NOT NULL,
            manager TEXT NOT NULL,
            remarks TEXT,
            transaction_type TEXT CHECK(transaction_type IN ('expense', 'income')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Water supply table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS water_supply (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            farmer_name TEXT NOT NULL,
            farmer_phone TEXT,
            date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            hours REAL DEFAULT 0,
            rate REAL NOT NULL,
            total_bill REAL NOT NULL,
            paid REAL DEFAULT 0,
            balance REAL NOT NULL,
            payment_status TEXT DEFAULT 'pending',
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            manager TEXT NOT NULL,
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
            date TEXT NOT NULL,
            source TEXT NOT NULL,
            amount REAL NOT NULL,
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
            name TEXT NOT NULL UNIQUE,
            phone TEXT,
            designation TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Farmers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS farmers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
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
    
    # Insert default managers
    default_managers = [
        ("Ali Khan", "0300-1234567", "Farm Manager"),
        ("Ahmed Raza", "0312-9876543", "Livestock Manager"),
        ("Usman Ali", "0333-4567890", "Crop Manager"),
        ("Bilal Ahmed", "0345-1122334", "Finance Manager")
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO managers (name, phone, designation) VALUES (?, ?, ?)",
        default_managers
    )
    
    # Insert default farmers
    default_farmers = [
        ("Farmer 1", "0301-2345678", "Village A"),
        ("Farmer 2", "0302-3456789", "Village B"),
        ("Farmer 3", "0303-4567890", "Village C")
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO farmers (name, phone, address) VALUES (?, ?, ?)",
        default_farmers
    )
    
    conn.commit()
    return conn

# Initialize database
conn = init_database()

# Helper functions
def show_message(message, type="success"):
    """Show status message"""
    if type == "success":
        st.success(message)
    elif type == "error":
        st.error(message)
    elif type == "warning":
        st.warning(message)
    elif type == "info":
        st.info(message)

def get_managers():
    """Get list of managers from database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM managers ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def get_farmers():
    """Get list of farmers from database"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM farmers ORDER BY name")
    return [row[0] for row in cursor.fetchall()]

def add_manager(name, phone, designation):
    """Add new manager"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO managers (name, phone, designation) VALUES (?, ?, ?)",
            (name, phone, designation)
        )
        conn.commit()
        return True, "Manager added successfully!"
    except sqlite3.IntegrityError:
        return False, "Manager with this name already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def add_farmer(name, phone, address):
    """Add new farmer"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO farmers (name, phone, address) VALUES (?, ?, ?)",
            (name, phone, address)
        )
        conn.commit()
        return True, "Farmer added successfully!"
    except sqlite3.IntegrityError:
        return False, "Farmer with this name already exists!"
    except Exception as e:
        return False, f"Error: {str(e)}"

def get_download_link(df, filename, text):
    """Generate download link for DataFrame"""
    towrite = BytesIO()
    df.to_excel(towrite, index=False, engine='openpyxl')
    towrite.seek(0)
    b64 = base64.b64encode(towrite.read()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">{text}</a>'
    return href

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
            'transaction_type': ['expense', 'expense']
        }),
        'crops': pd.DataFrame({
            'date': ['2024-01-15', '2024-01-16'],
            'crop_type': ['Wheat (گندم)', 'Corn'],
            'area': [10.5, 5.2],
            'expense_type': ['Fertilizer (کھاد)', 'Land Preparation'],
            'amount': [15000, 8000],
            'manager': ['Usman Ali', 'Usman Ali'],
            'remarks': ['Urea fertilizer', 'Plowing charges'],
            'transaction_type': ['expense', 'expense']
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

def import_data(table_name, uploaded_file, user_name="User"):
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
        errors = []
        
        for idx, row in df.iterrows():
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
                        str(row.get('transaction_type', 'expense')).lower()
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
                        str(row.get('transaction_type', 'expense')).lower()
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
                    start_time = str(row.get('start_time', '08:00'))
                    end_time = str(row.get('end_time', '12:00'))
                    
                    # Calculate hours
                    try:
                        start_dt = datetime.strptime(start_time, '%H:%M')
                        end_dt = datetime.strptime(end_time, '%H:%M')
                        hours = (end_dt - start_dt).total_seconds() / 3600
                        if hours < 0:
                            hours += 24
                    except:
                        hours = 4.0
                    
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
                errors.append(f"Row {idx+2}: {str(e)}")
                continue
        
        # Log the import
        cursor.execute("""
            INSERT INTO import_logs (table_name, filename, records_imported, imported_by)
            VALUES (?, ?, ?, ?)
        """, (table_name, uploaded_file.name, records_imported, user_name))
        
        conn.commit()
        
        if errors:
            return True, f"Imported {records_imported} records with {len(errors)} errors"
        else:
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
                update_data['transaction_type'].lower(),
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
                update_data['transaction_type'].lower(),
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
            # Recalculate hours
            try:
                start_dt = datetime.strptime(update_data['start_time'], '%H:%M')
                end_dt = datetime.strptime(update_data['end_time'], '%H:%M')
                hours = (end_dt - start_dt).total_seconds() / 3600
                if hours < 0:
                    hours += 24
            except:
                hours = update_data.get('hours', 0)
            
            total_bill = hours * update_data['rate']
            balance = total_bill - update_data['paid']
            
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
                update_data['start_time'],
                update_data['end_time'],
                hours,
                update_data['rate'],
                total_bill,
                update_data['paid'],
                balance,
                update_data['remarks'],
                record_id
            ))
        
        conn.commit()
        return True, "Record updated successfully!"
        
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
            # Delete related payments first
            cursor.execute("DELETE FROM water_payments WHERE water_supply_id=?", (record_id,))
            cursor.execute("DELETE FROM water_supply WHERE id=?", (record_id,))
        
        conn.commit()
        return True, "Record deleted successfully!"
        
    except Exception as e:
        return False, f"Delete error: {str(e)}"

def export_data(table_name, format='excel'):
    """Export data from database"""
    cursor = conn.cursor()
    
    # Define column mappings for each table
    column_mappings = {
        'livestock': ['id', 'date', 'category', 'quantity', 'expense_type', 
                     'amount', 'manager', 'remarks', 'transaction_type', 'created_at'],
        'crops': ['id', 'date', 'crop_type', 'area', 'expense_type', 
                 'amount', 'manager', 'remarks', 'transaction_type', 'created_at'],
        'expenses': ['id', 'date', 'category', 'description', 'amount', 
                    'manager', 'receipt_no', 'remarks', 'created_at'],
        'income': ['id', 'date', 'source', 'amount', 'received_by', 
                  'customer', 'receipt_no', 'remarks', 'created_at'],
        'water_supply': ['id', 'farmer_name', 'farmer_phone', 'date', 'start_time', 
                        'end_time', 'hours', 'rate', 'total_bill', 'paid', 
                        'balance', 'remarks', 'created_at']
    }
    
    columns = column_mappings.get(table_name, [])
    if not columns:
        return None
    
    # Build query
    query = f"SELECT {', '.join(columns)} FROM {table_name} ORDER BY date DESC"
    cursor.execute(query)
    data = cursor.fetchall()
    
    if not data:
        return None
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=columns)
    return df

# Sidebar Navigation
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white; margin-bottom: 30px;'>🌾 Farm Management</h1>", unsafe_allow_html=True)
    
    menu = st.selectbox(
        "Navigation",
        ["📊 Dashboard", "🐄 Livestock", "🌱 Crops", "💧 Water Supply", "💰 Expenses", "💵 Income", "📈 Reports", "⚙️ Settings"]
    )
    
    st.markdown("---")
    
    # Quick Stats
    today = datetime.now().strftime("%Y-%m-%d")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income WHERE date = ?", (today,))
    today_income = cursor.fetchone()[0]
    
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?", (today,))
    today_expenses = cursor.fetchone()[0]
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("💰 Today's Income", f"PKR {today_income:,.0f}")
    with col2:
        st.metric("💸 Today's Expenses", f"PKR {today_expenses:,.0f}")
    
    st.markdown("---")
    st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# Dashboard
if menu == "📊 Dashboard":
    st.markdown("<h1 class='main-header'>🏡 Complete Farm Management System</h1>", unsafe_allow_html=True)
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income")
        total_income = cursor.fetchone()[0]
        st.metric("💰 Total Income", f"PKR {total_income:,.0f}", delta="+12%")
    
    with col2:
        cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
        total_expenses = cursor.fetchone()[0]
        st.metric("💸 Total Expenses", f"PKR {total_expenses:,.0f}", delta="+5%")
    
    with col3:
        net_balance = total_income - total_expenses
        st.metric("⚖️ Net Balance", f"PKR {net_balance:,.0f}", 
                 delta_color="inverse" if net_balance < 0 else "normal")
    
    with col4:
        cursor.execute("SELECT COUNT(DISTINCT farmer_name) FROM water_supply")
        total_farmers = cursor.fetchone()[0]
        st.metric("👨‍🌾 Active Farmers", total_farmers, delta="+3")
    
    # Charts Section
    st.markdown("---")
    st.markdown("<h2 class='sub-header'>📊 Financial Overview</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Income by Source
        cursor.execute("""
            SELECT source, SUM(amount) as total 
            FROM income 
            WHERE date >= date('now', '-30 days')
            GROUP BY source 
            ORDER BY total DESC
        """)
        income_data = cursor.fetchall()
        
        if income_data:
            df_income = pd.DataFrame(income_data, columns=['Source', 'Amount'])
            fig = px.pie(df_income, values='Amount', names='Source', 
                        title="Income by Source (Last 30 Days)",
                        color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Expense Trend
        cursor.execute("""
            SELECT date, SUM(amount) as daily_expense 
            FROM expenses 
            WHERE date >= date('now', '-30 days')
            GROUP BY date 
            ORDER BY date
        """)
        expense_trend = cursor.fetchall()
        
        if expense_trend:
            df_expense = pd.DataFrame(expense_trend, columns=['Date', 'Amount'])
            fig = px.line(df_expense, x='Date', y='Amount', markers=True,
                         title="Expense Trend (Last 30 Days)",
                         line_shape='spline')
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent Transactions
    st.markdown("<h2 class='sub-header'>🔄 Recent Transactions</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📈 Recent Income**")
        cursor.execute("""
            SELECT date, source, amount, received_by 
            FROM income 
            ORDER BY date DESC 
            LIMIT 8
        """)
        recent_income = cursor.fetchall()
        
        if recent_income:
            df_recent_income = pd.DataFrame(recent_income, 
                                          columns=['Date', 'Source', 'Amount', 'Received By'])
            st.dataframe(df_recent_income, use_container_width=True)
    
    with col2:
        st.markdown("**📉 Recent Expenses**")
        cursor.execute("""
            SELECT date, category, amount, manager 
            FROM expenses 
            ORDER BY date DESC 
            LIMIT 8
        """)
        recent_expenses = cursor.fetchall()
        
        if recent_expenses:
            df_recent_expenses = pd.DataFrame(recent_expenses,
                                            columns=['Date', 'Category', 'Amount', 'Manager'])
            st.dataframe(df_recent_expenses, use_container_width=True)

# Livestock Management
elif menu == "🐄 Livestock":
    st.markdown("<h1 class='main-header'>🐄 Livestock Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Record", "📋 View/Edit Records", "📤 Import Data", "📥 Export Data"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Add New Livestock Record</h2>", unsafe_allow_html=True)
        
        with st.form("livestock_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("📅 Date *", datetime.now())
                category = st.selectbox("🏷️ Category *", 
                                       ["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Sheep", "Buffalo", "Poultry", "Others"])
                quantity = st.number_input("🔢 Quantity", min_value=0.0, step=1.0, value=1.0)
                expense_type = st.selectbox("💰 Expense Type", 
                                          ["Khal (کھل)", "Chokar (چوکر)", "Tori (ٹوری)", 
                                           "Ghaas/Fodder (گھاس)", "Medicine (دوائیں)", 
                                           "Vaccination (ٹیکہ)", "Labor", "Others"])
            
            with col2:
                amount = st.number_input("💵 Amount (PKR) *", min_value=0.0, step=100.0)
                transaction_type = st.selectbox("🔄 Transaction Type *", ["expense", "income"])
                
                managers = get_managers()
                if managers:
                    manager = st.selectbox("👤 Managed By *", managers)
                else:
                    manager = st.text_input("👤 Manager Name *")
                
                remarks = st.text_area("📝 Remarks")
            
            submitted = st.form_submit_button("💾 Save Record", use_container_width=True)
            
            if submitted:
                if amount <= 0:
                    show_message("❌ Amount must be greater than 0", "error")
                elif not manager:
                    show_message("❌ Manager is required", "error")
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
                        show_message("✅ Livestock record saved successfully!", "success")
                    except Exception as e:
                        show_message(f"❌ Error saving record: {str(e)}", "error")
    
    with tab2:
        st.markdown("<h2 class='sub-header'>View & Manage Livestock Records</h2>", unsafe_allow_html=True)
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_category = st.selectbox("Filter by Category", 
                                         ["All"] + ["Cow (گائے)", "Beef (بیف)", "Goat (بکری)", "Sheep", "Buffalo", "Poultry", "Others"])
        with col2:
            filter_type = st.selectbox("Filter by Transaction", ["All", "expense", "income"])
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
        
        query += " AND date BETWEEN ? AND ? ORDER BY date DESC"
        params.extend([start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")])
        
        cursor = conn.cursor()
        cursor.execute(query, params)
        records = cursor.fetchall()
        
        if records:
            df = pd.DataFrame(records, columns=['ID', 'Date', 'Category', 'Quantity', 
                                              'Expense Type', 'Amount', 'Manager', 
                                              'Remarks', 'Transaction Type', 'Created At', 'Updated At'])
            
            # Display metrics
            total_expenses = df[df['Transaction Type'] == 'expense']['Amount'].sum()
            total_income = df[df['Transaction Type'] == 'income']['Amount'].sum()
            net_balance = total_income - total_expenses
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💸 Total Expenses", f"PKR {total_expenses:,.0f}")
            with col2:
                st.metric("💰 Total Income", f"PKR {total_income:,.0f}")
            with col3:
                st.metric("⚖️ Net Balance", f"PKR {net_balance:,.0f}")
            
            # Edit/Delete Section
            st.markdown("---")
            st.markdown("<h3>✏️ Edit Records</h3>", unsafe_allow_html=True)
            
            selected_id = st.selectbox("Select Record to Edit", df['ID'].tolist())
            
            if selected_id:
                selected_record = df[df['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_livestock_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("📅 Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'))
                        edit_category = st.text_input("🏷️ Category", value=selected_record['Category'])
                        edit_quantity = st.number_input("🔢 Quantity", value=float(selected_record['Quantity']))
                        edit_expense_type = st.text_input("💰 Expense Type", value=selected_record['Expense Type'])
                    
                    with col2:
                        edit_amount = st.number_input("💵 Amount", value=float(selected_record['Amount']))
                        edit_transaction = st.selectbox("🔄 Transaction Type", ["expense", "income"],
                                                       index=0 if selected_record['Transaction Type'] == 'expense' else 1)
                        edit_manager = st.text_input("👤 Manager", value=selected_record['Manager'])
                        edit_remarks = st.text_area("📝 Remarks", value=selected_record['Remarks'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record", use_container_width=True)
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record", use_container_width=True)
                    
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
                            show_message(message, "success")
                            st.rerun()
                        else:
                            show_message(message, "error")
                    
                    if delete_btn:
                        if st.checkbox("⚠️ Confirm deletion", key=f"confirm_del_{selected_id}"):
                            success, message = delete_record('livestock', selected_id)
                            if success:
                                show_message(message, "success")
                                st.rerun()
                            else:
                                show_message(message, "error")
            
            # Display all records
            st.markdown("---")
            st.markdown("<h3>📋 All Records</h3>", unsafe_allow_html=True)
            display_cols = ['Date', 'Category', 'Quantity', 'Expense Type', 'Amount', 
                          'Manager', 'Remarks', 'Transaction Type']
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("📭 No records found for the selected filters")
    
    with tab3:
        st.markdown("<h2 class='sub-header'>📤 Import Livestock Data</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Download Template")
            template_df = create_template('livestock')
            st.dataframe(template_df, use_container_width=True)
            
            # Download template button
            st.markdown(get_download_link(template_df, "livestock_template.xlsx", "📥 Download Excel Template"), 
                      unsafe_allow_html=True)
        
        with col2:
            st.markdown("### Upload Instructions")
            st.info("""
            **Required Columns:**
            - date (YYYY-MM-DD)
            - category
            - amount
            - transaction_type (expense/income)
            
            **Optional Columns:**
            - quantity
            - expense_type
            - manager
            - remarks
            """)
        
        st.markdown("---")
        st.markdown("### Upload Data File")
        
        uploaded_file = st.file_uploader("Choose Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file:
            st.success(f"✅ File uploaded: {uploaded_file.name}")
            
            if st.button("🚀 Import Data", use_container_width=True):
                with st.spinner("Importing data..."):
                    success, message = import_data('livestock', uploaded_file)
                    if success:
                        show_message(message, "success")
                    else:
                        show_message(message, "error")
    
    with tab4:
        st.markdown("<h2 class='sub-header'>📥 Export Livestock Data</h2>", unsafe_allow_html=True)
        
        # Export options
        export_format = st.selectbox("Select Export Format", ["Excel", "CSV"])
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM livestock ORDER BY date DESC")
        export_data = cursor.fetchall()
        
        if export_data:
            df_export = pd.DataFrame(export_data, 
                                   columns=['ID', 'Date', 'Category', 'Quantity', 'Expense Type', 
                                           'Amount', 'Manager', 'Remarks', 'Transaction Type', 
                                           'Created At', 'Updated At'])
            
            # Display preview
            st.markdown("### Data Preview")
            st.dataframe(df_export.head(10), use_container_width=True)
            
            # Export buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if export_format == "Excel":
                    st.markdown(get_download_link(df_export, "livestock_export.xlsx", "📥 Download Excel"), 
                              unsafe_allow_html=True)
                else:
                    csv = df_export.to_csv(index=False)
                    b64 = base64.b64encode(csv.encode()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="livestock_export.csv">📥 Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
            
            with col2:
                if st.button("🔄 Refresh Data", use_container_width=True):
                    st.rerun()
        else:
            st.info("📭 No data available for export")

# Crop Management
elif menu == "🌱 Crops":
    st.markdown("<h1 class='main-header'>🌱 Crop Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Record", "📋 View/Edit Records", "📤 Import Data", "📥 Export Data"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Add New Crop Record</h2>", unsafe_allow_html=True)
        
        with st.form("crop_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("📅 Date *", datetime.now())
                crop_type = st.selectbox("🌾 Crop Type *", 
                                        ["Wheat (گندم)", "Rice (چاول)", "Cotton (کپاس)",
                                         "Kheera (Cucumber)", "Corn", "Vegetables (سبزیاں)", 
                                         "Fruits", "Pulses", "Others"])
                area = st.number_input("📏 Area (acres)", min_value=0.0, step=0.1, value=1.0)
                expense_type = st.selectbox("💰 Expense Type", 
                                          ["Labor (مزدوری)", "Seeds (بیج)", "Fertilizer (کھاد)",
                                           "Spray (سپرے)", "Land Preparation", "Harvesting",
                                           "Transportation", "Storage", "Others"])
            
            with col2:
                amount = st.number_input("💵 Amount (PKR) *", min_value=0.0, step=100.0)
                transaction_type = st.selectbox("🔄 Transaction Type *", ["expense", "income"])
                
                managers = get_managers()
                if managers:
                    manager = st.selectbox("👤 Managed By *", managers)
                else:
                    manager = st.text_input("👤 Manager Name *")
                
                remarks = st.text_area("📝 Remarks")
            
            submitted = st.form_submit_button("💾 Save Record", use_container_width=True)
            
            if submitted:
                if amount <= 0:
                    show_message("❌ Amount must be greater than 0", "error")
                elif not manager:
                    show_message("❌ Manager is required", "error")
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
                        show_message("✅ Crop record saved successfully!", "success")
                    except Exception as e:
                        show_message(f"❌ Error saving record: {str(e)}", "error")
    
    with tab2:
        st.markdown("<h2 class='sub-header'>View & Manage Crop Records</h2>", unsafe_allow_html=True)
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM crops ORDER BY date DESC")
        records = cursor.fetchall()
        
        if records:
            df = pd.DataFrame(records, columns=['ID', 'Date', 'Crop Type', 'Area', 'Expense Type',
                                              'Amount', 'Manager', 'Remarks', 'Transaction Type',
                                              'Created At', 'Updated At'])
            
            # Display metrics
            total_area = df['Area'].sum()
            total_expenses = df[df['Transaction Type'] == 'expense']['Amount'].sum()
            total_income = df[df['Transaction Type'] == 'income']['Amount'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📏 Total Area", f"{total_area:,.1f} acres")
            with col2:
                st.metric("💸 Total Expenses", f"PKR {total_expenses:,.0f}")
            with col3:
                st.metric("💰 Total Income", f"PKR {total_income:,.0f}")
            
            # Edit/Delete Section
            st.markdown("---")
            st.markdown("<h3>✏️ Edit Records</h3>", unsafe_allow_html=True)
            
            selected_id = st.selectbox("Select Record to Edit", df['ID'].tolist(), key="crop_edit")
            
            if selected_id:
                selected_record = df[df['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_crop_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("📅 Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'))
                        edit_crop_type = st.text_input("🌾 Crop Type", value=selected_record['Crop Type'])
                        edit_area = st.number_input("📏 Area", value=float(selected_record['Area']))
                        edit_expense_type = st.text_input("💰 Expense Type", value=selected_record['Expense Type'])
                    
                    with col2:
                        edit_amount = st.number_input("💵 Amount", value=float(selected_record['Amount']))
                        edit_transaction = st.selectbox("🔄 Transaction Type", ["expense", "income"],
                                                       index=0 if selected_record['Transaction Type'] == 'expense' else 1)
                        edit_manager = st.text_input("👤 Manager", value=selected_record['Manager'])
                        edit_remarks = st.text_area("📝 Remarks", value=selected_record['Remarks'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record", use_container_width=True)
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record", use_container_width=True)
                    
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
                            show_message(message, "success")
                            st.rerun()
                        else:
                            show_message(message, "error")
                    
                    if delete_btn:
                        if st.checkbox("⚠️ Confirm deletion", key=f"crop_confirm_del_{selected_id}"):
                            success, message = delete_record('crops', selected_id)
                            if success:
                                show_message(message, "success")
                                st.rerun()
                            else:
                                show_message(message, "error")
            
            # Display all records
            st.markdown("---")
            st.markdown("<h3>📋 All Records</h3>", unsafe_allow_html=True)
            display_cols = ['Date', 'Crop Type', 'Area', 'Expense Type', 'Amount', 
                          'Manager', 'Remarks', 'Transaction Type']
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("📭 No records found")

# Expenses Management
elif menu == "💰 Expenses":
    st.markdown("<h1 class='main-header'>💰 Expenses Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Expense", "📋 View/Edit Expenses", "📤 Import Data", "📥 Export Data"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Add New Expense</h2>", unsafe_allow_html=True)
        
        with st.form("expense_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("📅 Date *", datetime.now())
                category = st.selectbox("🏷️ Category *", 
                                      ["Salary (تنخواہ)", "Machinery (مشینری)", 
                                       "Kitchen", "Construction",
                                       "Petrol", "Diesel", 
                                       "Electricity Bill", "Turbine Bill",
                                       "Maintenance (مرمت)", "Livestock Feed",
                                       "Crop Inputs", "Transport", "Others"])
                description = st.text_input("📝 Description *")
                amount = st.number_input("💵 Amount (PKR) *", min_value=0.0, step=100.0)
            
            with col2:
                managers = get_managers()
                if managers:
                    manager = st.selectbox("👤 Managed By *", managers)
                else:
                    manager = st.text_input("👤 Manager Name *")
                
                receipt_no = st.text_input("🧾 Receipt No")
                remarks = st.text_area("📋 Remarks")
            
            submitted = st.form_submit_button("💾 Save Expense", use_container_width=True)
            
            if submitted:
                if amount <= 0 or not description:
                    show_message("❌ Please fill all required fields", "error")
                elif not manager:
                    show_message("❌ Manager is required", "error")
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
                        show_message("✅ Expense recorded successfully!", "success")
                    except Exception as e:
                        show_message(f"❌ Error saving expense: {str(e)}", "error")
    
    with tab2:
        st.markdown("<h2 class='sub-header'>View & Manage Expenses</h2>", unsafe_allow_html=True)
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM expenses ORDER BY date DESC")
        records = cursor.fetchall()
        
        if records:
            df = pd.DataFrame(records, columns=['ID', 'Date', 'Category', 'Description',
                                              'Amount', 'Manager', 'Receipt No', 
                                              'Remarks', 'Created At', 'Updated At'])
            
            # Display metrics
            total_amount = df['Amount'].sum()
            avg_amount = df['Amount'].mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💸 Total Expenses", f"PKR {total_amount:,.0f}")
            with col2:
                st.metric("📊 Average Expense", f"PKR {avg_amount:,.0f}")
            with col3:
                st.metric("📈 Number of Expenses", len(df))
            
            # Edit/Delete Section
            st.markdown("---")
            st.markdown("<h3>✏️ Edit Records</h3>", unsafe_allow_html=True)
            
            selected_id = st.selectbox("Select Record to Edit", df['ID'].tolist(), key="exp_edit")
            
            if selected_id:
                selected_record = df[df['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_expense_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("📅 Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'))
                        edit_category = st.text_input("🏷️ Category", value=selected_record['Category'])
                        edit_description = st.text_input("📝 Description", value=selected_record['Description'])
                        edit_amount = st.number_input("💵 Amount", value=float(selected_record['Amount']))
                    
                    with col2:
                        edit_manager = st.text_input("👤 Manager", value=selected_record['Manager'])
                        edit_receipt = st.text_input("🧾 Receipt No", value=selected_record['Receipt No'])
                        edit_remarks = st.text_area("📋 Remarks", value=selected_record['Remarks'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record", use_container_width=True)
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record", use_container_width=True)
                    
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
                            show_message(message, "success")
                            st.rerun()
                        else:
                            show_message(message, "error")
                    
                    if delete_btn:
                        if st.checkbox("⚠️ Confirm deletion", key=f"exp_confirm_del_{selected_id}"):
                            success, message = delete_record('expenses', selected_id)
                            if success:
                                show_message(message, "success")
                                st.rerun()
                            else:
                                show_message(message, "error")
            
            # Display all records
            st.markdown("---")
            st.markdown("<h3>📋 All Expenses</h3>", unsafe_allow_html=True)
            display_cols = ['Date', 'Category', 'Description', 'Amount', 
                          'Manager', 'Receipt No', 'Remarks']
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("📭 No expenses found")

# Income Management
elif menu == "💵 Income":
    st.markdown("<h1 class='main-header'>💵 Income Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Income", "📋 View/Edit Income", "📤 Import Data", "📥 Export Data"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Add New Income</h2>", unsafe_allow_html=True)
        
        with st.form("income_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                date = st.date_input("📅 Date *", datetime.now())
                source = st.selectbox("💰 Income Source *", 
                                    ["Livestock Sale", "Goats Sale", "Beef Sale", 
                                     "Cows Sale", "Milk Sale", "Crop Sale",
                                     "Water Supply", "Rental Income", 
                                     "Consultation", "Others"])
                amount = st.number_input("💵 Amount (PKR) *", min_value=0.0, step=100.0)
                customer = st.text_input("👤 Customer/Payer")
            
            with col2:
                managers = get_managers()
                if managers:
                    received_by = st.selectbox("🤝 Received By", managers)
                else:
                    received_by = st.text_input("🤝 Received By")
                
                receipt_no = st.text_input("🧾 Receipt No")
                remarks = st.text_area("📋 Remarks")
            
            submitted = st.form_submit_button("💾 Save Income", use_container_width=True)
            
            if submitted:
                if amount <= 0:
                    show_message("❌ Amount must be greater than 0", "error")
                else:
                    try:
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO income (date, source, amount, received_by, 
                                              customer, receipt_no, remarks)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (date.strftime("%Y-%m-%d"), source, amount,
                             received_by, customer, receipt_no, remarks))
                        conn.commit()
                        show_message("✅ Income recorded successfully!", "success")
                    except Exception as e:
                        show_message(f"❌ Error saving income: {str(e)}", "error")
    
    with tab2:
        st.markdown("<h2 class='sub-header'>View & Manage Income</h2>", unsafe_allow_html=True)
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM income ORDER BY date DESC")
        records = cursor.fetchall()
        
        if records:
            df = pd.DataFrame(records, columns=['ID', 'Date', 'Source', 'Amount',
                                              'Received By', 'Customer', 
                                              'Receipt No', 'Remarks', 
                                              'Created At', 'Updated At'])
            
            # Display metrics
            total_income = df['Amount'].sum()
            avg_income = df['Amount'].mean()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Total Income", f"PKR {total_income:,.0f}")
            with col2:
                st.metric("📊 Average Income", f"PKR {avg_income:,.0f}")
            with col3:
                st.metric("📈 Number of Records", len(df))
            
            # Edit/Delete Section
            st.markdown("---")
            st.markdown("<h3>✏️ Edit Records</h3>", unsafe_allow_html=True)
            
            selected_id = st.selectbox("Select Record to Edit", df['ID'].tolist(), key="inc_edit")
            
            if selected_id:
                selected_record = df[df['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_income_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_date = st.date_input("📅 Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'))
                        edit_source = st.text_input("💰 Source", value=selected_record['Source'])
                        edit_amount = st.number_input("💵 Amount", value=float(selected_record['Amount']))
                        edit_customer = st.text_input("👤 Customer", value=selected_record['Customer'])
                    
                    with col2:
                        edit_received = st.text_input("🤝 Received By", value=selected_record['Received By'])
                        edit_receipt = st.text_input("🧾 Receipt No", value=selected_record['Receipt No'])
                        edit_remarks = st.text_area("📋 Remarks", value=selected_record['Remarks'])
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record", use_container_width=True)
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record", use_container_width=True)
                    
                    if update_btn:
                        update_data = {
                            'date': edit_date.strftime("%Y-%m-%d"),
                            'source': edit_source,
                            'amount': edit_amount,
                            'received_by': edit_received,
                            'customer': edit_customer,
                            'receipt_no': edit_receipt,
                            'remarks': edit_remarks
                        }
                        success, message = update_record('income', selected_id, update_data)
                        if success:
                            show_message(message, "success")
                            st.rerun()
                        else:
                            show_message(message, "error")
                    
                    if delete_btn:
                        if st.checkbox("⚠️ Confirm deletion", key=f"inc_confirm_del_{selected_id}"):
                            success, message = delete_record('income', selected_id)
                            if success:
                                show_message(message, "success")
                                st.rerun()
                            else:
                                show_message(message, "error")
            
            # Display all records
            st.markdown("---")
            st.markdown("<h3>📋 All Income Records</h3>", unsafe_allow_html=True)
            display_cols = ['Date', 'Source', 'Amount', 'Received By', 
                          'Customer', 'Receipt No', 'Remarks']
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("📭 No income records found")

# Water Supply Management
elif menu == "💧 Water Supply":
    st.markdown("<h1 class='main-header'>💧 Water Supply Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Supply", "📋 View/Edit Records", "📤 Import Data", "📥 Export Data"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>Add Water Supply Record</h2>", unsafe_allow_html=True)
        
        with st.form("water_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                farmer_name = st.text_input("👨‍🌾 Farmer Name *")
                farmer_phone = st.text_input("📞 Phone Number")
                date = st.date_input("📅 Date *", datetime.now())
                rate = st.number_input("💵 Rate per Hour (PKR) *", min_value=0.0, value=500.0, step=50.0)
            
            with col2:
                col_a, col_b = st.columns(2)
                with col_a:
                    start_time = st.time_input("⏰ Start Time", datetime.now().time())
                with col_b:
                    end_time = st.time_input("⏰ End Time", (datetime.now() + timedelta(hours=2)).time())
                
                paid = st.number_input("💰 Paid Amount", min_value=0.0, step=100.0, value=0.0)
                remarks = st.text_area("📋 Remarks")
            
            # Calculate hours and bill
            start_dt = datetime.combine(date, start_time)
            end_dt = datetime.combine(date, end_time)
            hours = (end_dt - start_dt).total_seconds() / 3600
            if hours < 0:
                hours += 24
            total_bill = hours * rate
            balance = total_bill - paid
            
            # Display calculations
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("⏱️ Total Hours", f"{hours:.2f}")
            with col2:
                st.metric("💰 Total Bill", f"PKR {total_bill:,.0f}")
            with col3:
                st.metric("⚖️ Balance", f"PKR {balance:,.0f}")
            
            submitted = st.form_submit_button("💾 Save Record", use_container_width=True)
            
            if submitted:
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
                             hours, rate, total_bill, paid, balance, remarks))
                        conn.commit()
                        show_message("✅ Water supply record saved successfully!", "success")
                    except Exception as e:
                        show_message(f"❌ Error saving record: {str(e)}", "error")
                else:
                    show_message("❌ Please fill all required fields", "error")
    
    with tab2:
        st.markdown("<h2 class='sub-header'>View & Manage Water Supply</h2>", unsafe_allow_html=True)
        
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM water_supply ORDER BY date DESC")
        records = cursor.fetchall()
        
        if records:
            df = pd.DataFrame(records, columns=['ID', 'Farmer Name', 'Phone', 'Date', 
                                              'Start Time', 'End Time', 'Hours', 'Rate',
                                              'Total Bill', 'Paid', 'Balance', 'Status',
                                              'Remarks', 'Created At', 'Updated At'])
            
            # Display metrics
            total_bill = df['Total Bill'].sum()
            total_paid = df['Paid'].sum()
            total_balance = df['Balance'].sum()
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("💰 Total Bill", f"PKR {total_bill:,.0f}")
            with col2:
                st.metric("💸 Total Paid", f"PKR {total_paid:,.0f}")
            with col3:
                st.metric("⚖️ Total Balance", f"PKR {total_balance:,.0f}")
            
            # Edit/Delete Section
            st.markdown("---")
            st.markdown("<h3>✏️ Edit Records</h3>", unsafe_allow_html=True)
            
            selected_id = st.selectbox("Select Record to Edit", df['ID'].tolist(), key="water_edit")
            
            if selected_id:
                selected_record = df[df['ID'] == selected_id].iloc[0]
                
                with st.form(f"edit_water_{selected_id}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        edit_farmer = st.text_input("👨‍🌾 Farmer Name", value=selected_record['Farmer Name'])
                        edit_phone = st.text_input("📞 Phone", value=selected_record['Phone'])
                        edit_date = st.date_input("📅 Date", datetime.strptime(selected_record['Date'], '%Y-%m-%d'))
                        edit_rate = st.number_input("💵 Rate", value=float(selected_record['Rate']))
                    
                    with col2:
                        edit_start = st.time_input("⏰ Start Time", datetime.strptime(selected_record['Start Time'], '%H:%M').time())
                        edit_end = st.time_input("⏰ End Time", datetime.strptime(selected_record['End Time'], '%H:%M').time())
                        edit_paid = st.number_input("💰 Paid Amount", value=float(selected_record['Paid']))
                        edit_remarks = st.text_area("📋 Remarks", value=selected_record['Remarks'])
                    
                    # Recalculate
                    start_dt = datetime.combine(edit_date, edit_start)
                    end_dt = datetime.combine(edit_date, edit_end)
                    edit_hours = (end_dt - start_dt).total_seconds() / 3600
                    if edit_hours < 0:
                        edit_hours += 24
                    edit_total = edit_hours * edit_rate
                    edit_balance = edit_total - edit_paid
                    
                    st.info(f"**Calculated:** Hours: {edit_hours:.2f}, Total Bill: PKR {edit_total:,.0f}, Balance: PKR {edit_balance:,.0f}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        update_btn = st.form_submit_button("📝 Update Record", use_container_width=True)
                    with col2:
                        delete_btn = st.form_submit_button("🗑️ Delete Record", use_container_width=True)
                    
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
                            show_message(message, "success")
                            st.rerun()
                        else:
                            show_message(message, "error")
                    
                    if delete_btn:
                        if st.checkbox("⚠️ Confirm deletion", key=f"water_confirm_del_{selected_id}"):
                            success, message = delete_record('water_supply', selected_id)
                            if success:
                                show_message(message, "success")
                                st.rerun()
                            else:
                                show_message(message, "error")
            
            # Display all records
            st.markdown("---")
            st.markdown("<h3>📋 All Records</h3>", unsafe_allow_html=True)
            display_cols = ['Farmer Name', 'Phone', 'Date', 'Start Time', 'End Time',
                          'Hours', 'Rate', 'Total Bill', 'Paid', 'Balance', 'Remarks']
            st.dataframe(df[display_cols], use_container_width=True)
        else:
            st.info("📭 No water supply records found")

# Reports
elif menu == "📈 Reports":
    st.markdown("<h1 class='main-header'>📈 Comprehensive Reports</h1>", unsafe_allow_html=True)
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Financial Summary", "Livestock Report", "Crop Report", "Water Supply Report", 
         "Expense Analysis", "Income Analysis", "Manager Performance"]
    )
    
    col1, col2 = st.columns(2)
    with col1:
        from_date = st.date_input("From Date", datetime.now() - timedelta(days=30))
    with col2:
        to_date = st.date_input("To Date", datetime.now())
    
    if st.button("📊 Generate Report", use_container_width=True):
        cursor = conn.cursor()
        
        if report_type == "Financial Summary":
            st.markdown("<h2 class='sub-header'>💰 Financial Summary Report</h2>", unsafe_allow_html=True)
            
            # Get total income
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM income WHERE date BETWEEN ? AND ?", 
                         (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
            total_income = cursor.fetchone()[0]
            
            # Get total expenses
            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date BETWEEN ? AND ?", 
                         (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
            total_expenses = cursor.fetchone()[0]
            
            net_profit = total_income - total_expenses
            profit_margin = (net_profit / total_income * 100) if total_income > 0 else 0
            
            # Display KPIs
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("💰 Total Income", f"PKR {total_income:,.0f}")
            with col2:
                st.metric("💸 Total Expenses", f"PKR {total_expenses:,.0f}")
            with col3:
                st.metric("⚖️ Net Profit", f"PKR {net_profit:,.0f}")
            with col4:
                st.metric("📈 Profit Margin", f"{profit_margin:.1f}%")
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Income by source
                cursor.execute("""
                    SELECT source, SUM(amount) as total 
                    FROM income 
                    WHERE date BETWEEN ? AND ?
                    GROUP BY source 
                    ORDER BY total DESC
                """, (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
                income_data = cursor.fetchall()
                
                if income_data:
                    df_income = pd.DataFrame(income_data, columns=['Source', 'Amount'])
                    fig = px.bar(df_income, x='Source', y='Amount', title="Income by Source")
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Expenses by category
                cursor.execute("""
                    SELECT category, SUM(amount) as total 
                    FROM expenses 
                    WHERE date BETWEEN ? AND ?
                    GROUP BY category 
                    ORDER BY total DESC
                """, (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
                expense_data = cursor.fetchall()
                
                if expense_data:
                    df_expense = pd.DataFrame(expense_data, columns=['Category', 'Amount'])
                    fig = px.pie(df_expense, values='Amount', names='Category', title="Expenses by Category")
                    st.plotly_chart(fig, use_container_width=True)
        
        elif report_type == "Livestock Report":
            st.markdown("<h2 class='sub-header'>🐄 Livestock Report</h2>", unsafe_allow_html=True)
            
            cursor.execute("""
                SELECT category, transaction_type, SUM(amount) as total_amount, 
                       SUM(quantity) as total_quantity
                FROM livestock 
                WHERE date BETWEEN ? AND ?
                GROUP BY category, transaction_type
                ORDER BY total_amount DESC
            """, (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
            
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=['Category', 'Type', 'Amount', 'Quantity'])
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_animals = df['Quantity'].sum()
                    st.metric("🐮 Total Animals", f"{total_animals:,.0f}")
                with col2:
                    livestock_income = df[df['Type'] == 'income']['Amount'].sum()
                    st.metric("💰 Livestock Income", f"PKR {livestock_income:,.0f}")
                with col3:
                    livestock_expenses = df[df['Type'] == 'expense']['Amount'].sum()
                    st.metric("💸 Livestock Expenses", f"PKR {livestock_expenses:,.0f}")
                
                st.dataframe(df, use_container_width=True)
        
        elif report_type == "Crop Report":
            st.markdown("<h2 class='sub-header'>🌱 Crop Report</h2>", unsafe_allow_html=True)
            
            cursor.execute("""
                SELECT crop_type, transaction_type, SUM(amount) as total_amount,
                       SUM(area) as total_area
                FROM crops
                WHERE date BETWEEN ? AND ?
                GROUP BY crop_type, transaction_type
                ORDER BY total_amount DESC
            """, (from_date.strftime("%Y-%m-%d"), to_date.strftime("%Y-%m-%d")))
            
            data = cursor.fetchall()
            
            if data:
                df = pd.DataFrame(data, columns=['Crop Type', 'Type', 'Amount', 'Area'])
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_area = df['Area'].sum()
                    st.metric("📏 Total Area", f"{total_area:,.1f} acres")
                with col2:
                    crop_income = df[df['Type'] == 'income']['Amount'].sum()
                    st.metric("💰 Crop Income", f"PKR {crop_income:,.0f}")
                with col3:
                    crop_expenses = df[df['Type'] == 'expense']['Amount'].sum()
                    st.metric("💸 Crop Expenses", f"PKR {crop_expenses:,.0f}")
                
                st.dataframe(df, use_container_width=True)

# Settings
elif menu == "⚙️ Settings":
    st.markdown("<h1 class='main-header'>⚙️ System Settings</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Manage Managers", "👨‍🌾 Manage Farmers", "💾 Backup/Restore", "📊 System Info"])
    
    with tab1:
        st.markdown("<h2 class='sub-header'>👥 Manage Managers</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Add New Manager")
            with st.form("add_manager_form", clear_on_submit=True):
                name = st.text_input("👤 Manager Name *")
                phone = st.text_input("📞 Phone Number")
                designation = st.text_input("🏷️ Designation *")
                
                if st.form_submit_button("➕ Add Manager", use_container_width=True):
                    if name and designation:
                        success, message = add_manager(name, phone, designation)
                        if success:
                            show_message(message, "success")
                            st.rerun()
                        else:
                            show_message(message, "error")
                    else:
                        show_message("❌ Name and designation are required", "error")
        
        with col2:
            st.markdown("### Existing Managers")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM managers ORDER BY name")
            managers = cursor.fetchall()
            
            if managers:
                df_managers = pd.DataFrame(managers, columns=['ID', 'Name', 'Phone', 'Designation', 'Created'])
                st.dataframe(df_managers[['Name', 'Phone', 'Designation']], use_container_width=True)
            else:
                st.info("📭 No managers found")
    
    with tab2:
        st.markdown("<h2 class='sub-header'>👨‍🌾 Manage Farmers</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Add New Farmer")
            with st.form("add_farmer_form", clear_on_submit=True):
                name = st.text_input("👨‍🌾 Farmer Name *")
                phone = st.text_input("📞 Phone Number")
                address = st.text_input("🏠 Address")
                
                if st.form_submit_button("➕ Add Farmer", use_container_width=True):
                    if name:
                        success, message = add_farmer(name, phone, address)
                        if success:
                            show_message(message, "success")
                            st.rerun()
                        else:
                            show_message(message, "error")
                    else:
                        show_message("❌ Farmer name is required", "error")
        
        with col2:
            st.markdown("### Existing Farmers")
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM farmers ORDER BY name")
            farmers = cursor.fetchall()
            
            if farmers:
                df_farmers = pd.DataFrame(farmers, columns=['ID', 'Name', 'Phone', 'Address', 'Created'])
                st.dataframe(df_farmers[['Name', 'Phone', 'Address']], use_container_width=True)
            else:
                st.info("📭 No farmers found")
    
    with tab3:
        st.markdown("<h2 class='sub-header'>💾 Backup & Restore</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Create Backup")
            if st.button("💾 Create Full Backup", use_container_width=True):
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
                href = f'<a href="data:application/json;base64,{b64}" download="farm_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json">📥 Download Backup</a>'
                st.markdown(href, unsafe_allow_html=True)
                show_message("✅ Backup created successfully!", "success")
        
        with col2:
            st.markdown("### Restore Backup")
            uploaded_file = st.file_uploader("Choose backup file", type=['json'])
            
            if uploaded_file and st.button("🔄 Restore Backup", use_container_width=True):
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
                    show_message("✅ Backup restored successfully!", "success")
                    st.rerun()
                except Exception as e:
                    show_message(f"❌ Error restoring backup: {str(e)}", "error")

# Footer with export options
st.sidebar.markdown("---")
st.sidebar.markdown("### 📤 Export Options")

if st.sidebar.button("📥 Export All Data", use_container_width=True):
    # Create Excel writer
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
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
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="farm_data_export.xlsx">📥 Download Full Data Export</a>'
    st.sidebar.markdown(href, unsafe_allow_html=True)

st.sidebar.markdown("---")
st.sidebar.markdown("""
<div style='text-align: center; color: #666; font-size: 14px;'>
    <p>🌾 <b>Complete Farm Management System</b></p>
    <p>Version 3.0 • © 2024</p>
</div>
""", unsafe_allow_html=True)

# Close database connection
conn.close()
