import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date, time, timedelta
import calendar
import json
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, DateTime, Boolean, Text, func, and_, desc
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import io

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="Farm Management System",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS
# ============================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E7D32;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        background: linear-gradient(90deg, #2E7D32, #4CAF50);
        color: white;
        border-radius: 10px;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 5px solid #2E7D32;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button {
        width: 100%;
        background-color: #2E7D32;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1B5E20;
    }
    .sidebar .sidebar-content {
        background-color: #f8f9fa;
    }
    .tab-container {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ============================================
# DATABASE MODELS
# ============================================
Base = declarative_base()

class LivestockExpense(Base):
    __tablename__ = 'livestock_expenses'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    animal_type = Column(String(50), nullable=False)
    expense_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    quantity = Column(Float)
    unit = Column(String(20))
    unit_price = Column(Float)
    paid_by = Column(String(100))
    payment_method = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class LivestockIncome(Base):
    __tablename__ = 'livestock_income'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    animal_type = Column(String(50), nullable=False)
    income_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    quantity = Column(Float)
    unit = Column(String(20))
    unit_price = Column(Float)
    buyer_name = Column(String(100))
    payment_method = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class CropExpense(Base):
    __tablename__ = 'crop_expenses'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    crop_name = Column(String(100), nullable=False)
    expense_type = Column(String(50), nullable=False)
    amount = Column(Float, nullable=False)
    quantity = Column(Float)
    unit = Column(String(20))
    unit_price = Column(Float)
    paid_by = Column(String(100))
    payment_method = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class CropIncome(Base):
    __tablename__ = 'crop_income'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    crop_name = Column(String(100), nullable=False)
    income_type = Column(String(50))
    amount = Column(Float, nullable=False)
    quantity = Column(Float)
    unit = Column(String(20))
    unit_price = Column(Float)
    buyer_name = Column(String(100))
    payment_method = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class WaterBill(Base):
    __tablename__ = 'water_bills'
    id = Column(Integer, primary_key=True)
    farmer_name = Column(String(100), nullable=False)
    farmer_phone = Column(String(20))
    date = Column(Date, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    hours_used = Column(Float, nullable=False)
    rate_per_hour = Column(Float, nullable=False)
    total_bill = Column(Float, nullable=False)
    amount_paid = Column(Float, default=0)
    balance_due = Column(Float, default=0)
    payment_status = Column(String(20), default='Pending')
    payment_date = Column(Date)
    payment_method = Column(String(50))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class OperationalExpense(Base):
    __tablename__ = 'operational_expenses'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    expense_type = Column(String(100), nullable=False)
    category = Column(String(50))
    managed_by = Column(String(100))
    amount = Column(Float, nullable=False)
    paid_to = Column(String(100))
    paid_amount = Column(Float, default=0)
    balance_due = Column(Float, default=0)
    description = Column(Text)
    payment_method = Column(String(50))
    is_paid = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

class LedgerEntry(Base):
    __tablename__ = 'ledger_entries'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(50))
    debit = Column(Float, default=0)
    credit = Column(Float, default=0)
    reference_type = Column(String(50))
    reference_id = Column(Integer)
    description = Column(Text)
    balance = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    payee_name = Column(String(100))
    payer_name = Column(String(100))
    amount = Column(Float, nullable=False)
    payment_method = Column(String(50))
    reference_type = Column(String(50))
    reference_id = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    role = Column(String(50))
    salary = Column(Float)
    address = Column(Text)
    joining_date = Column(Date)
    status = Column(String(20), default='Active')
    created_at = Column(DateTime, default=datetime.now)

class Farmer(Base):
    __tablename__ = 'farmers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    total_bill = Column(Float, default=0)
    total_paid = Column(Float, default=0)
    balance_due = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)

class Settings(Base):
    __tablename__ = 'settings'
    id = Column(Integer, primary_key=True)
    key = Column(String(100), nullable=False)
    value = Column(Text)
    created_at = Column(DateTime, default=datetime.now)

# ============================================
# DATABASE MANAGEMENT
# ============================================
class DatabaseManager:
    def __init__(self, db_path='farm_management.db'):
        self.db_path = db_path
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def get_session(self):
        return self.Session()
    
    def init_sample_data(self):
        """Initialize sample data for first-time users"""
        session = self.get_session()
        try:
            # Check if data already exists
            if session.query(LivestockExpense).count() == 0:
                # Add sample employees
                employees = [
                    Employee(name="Ali Ahmed", phone="03001234567", role="Farm Manager", salary=50000, joining_date=datetime.now().date()),
                    Employee(name="Bilal Khan", phone="03001234568", role="Worker", salary=25000, joining_date=datetime.now().date()),
                    Employee(name="Chaudhry Usman", phone="03001234569", role="Driver", salary=30000, joining_date=datetime.now().date()),
                ]
                for emp in employees:
                    session.add(emp)
                
                # Add sample farmers
                farmers = [
                    Farmer(name="Farmer Akbar", phone="03001234570", address="Village A"),
                    Farmer(name="Farmer Babar", phone="03001234571", address="Village B"),
                    Farmer(name="Farmer Chohan", phone="03001234572", address="Village C"),
                ]
                for farmer in farmers:
                    session.add(farmer)
                
                session.commit()
                st.success("Sample data initialized successfully!")
        except Exception as e:
            session.rollback()
            st.error(f"Error initializing sample data: {e}")
        finally:
            session.close()
    
    def get_summary_stats(self):
        """Get summary statistics for dashboard"""
        session = self.get_session()
        try:
            today = datetime.now().date()
            month_start = today.replace(day=1)
            
            # Livestock expenses this month
            livestock_exp = session.query(func.sum(LivestockExpense.amount)).filter(
                and_(
                    LivestockExpense.date >= month_start,
                    LivestockExpense.date <= today
                )
            ).scalar() or 0
            
            # Crop expenses this month
            crop_exp = session.query(func.sum(CropExpense.amount)).filter(
                and_(
                    CropExpense.date >= month_start,
                    CropExpense.date <= today
                )
            ).scalar() or 0
            
            # Water income this month
            water_inc = session.query(func.sum(WaterBill.total_bill)).filter(
                and_(
                    WaterBill.date >= month_start,
                    WaterBill.date <= today
                )
            ).scalar() or 0
            
            # Operational expenses this month
            op_exp = session.query(func.sum(OperationalExpense.amount)).filter(
                and_(
                    OperationalExpense.date >= month_start,
                    OperationalExpense.date <= today
                )
            ).scalar() or 0
            
            # Outstanding balance
            outstanding = session.query(func.sum(WaterBill.balance_due)).filter(
                WaterBill.balance_due > 0
            ).scalar() or 0
            
            # Total farmers
            total_farmers = session.query(func.count(Farmer.id)).scalar() or 0
            
            # Active employees
            active_emp = session.query(func.count(Employee.id)).filter(
                Employee.status == 'Active'
            ).scalar() or 0
            
            return {
                'livestock_expenses_month': livestock_exp,
                'crop_expenses_month': crop_exp,
                'water_income_month': water_inc,
                'operational_expenses_month': op_exp,
                'outstanding_balance': outstanding,
                'total_farmers': total_farmers,
                'active_employees': active_emp
            }
        finally:
            session.close()

# ============================================
# UTILITY FUNCTIONS
# ============================================
class FarmUtils:
    @staticmethod
    def calculate_hours(start_time, end_time):
        """Calculate hours between two times"""
        if isinstance(start_time, time) and isinstance(end_time, time):
            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = datetime.combine(datetime.today(), end_time)
        else:
            start_dt = start_time
            end_dt = end_time
        
        if end_dt < start_dt:
            end_dt = end_dt.replace(day=end_dt.day + 1)
        
        hours = (end_dt - start_dt).total_seconds() / 3600
        return round(hours, 2)
    
    @staticmethod
    def add_ledger_entry(session, date, account_name, account_type, debit, credit, 
                         reference_type, reference_id, description):
        """Add double-entry ledger entry"""
        # Calculate running balance
        prev_entry = session.query(LedgerEntry).filter(
            LedgerEntry.account_name == account_name
        ).order_by(LedgerEntry.id.desc()).first()
        
        prev_balance = prev_entry.balance if prev_entry else 0
        
        if account_type in ['Asset', 'Expense']:
            new_balance = prev_balance + debit - credit
        else:
            new_balance = prev_balance + credit - debit
        
        ledger_entry = LedgerEntry(
            date=date,
            account_name=account_name,
            account_type=account_type,
            debit=debit,
            credit=credit,
            reference_type=reference_type,
            reference_id=reference_id,
            description=description,
            balance=new_balance
        )
        
        session.add(ledger_entry)
        return ledger_entry
    
    @staticmethod
    def record_livestock_expense(session, data):
        """Record livestock expense with ledger entries"""
        expense = LivestockExpense(**data)
        session.add(expense)
        session.flush()
        
        # Debit: Livestock Expense
        FarmUtils.add_ledger_entry(
            session=session,
            date=data['date'],
            account_name='Livestock Expenses',
            account_type='Expense',
            debit=data['amount'],
            credit=0,
            reference_type='livestock',
            reference_id=expense.id,
            description=f"{data['animal_type']} - {data['expense_type']}"
        )
        
        # Credit: Cash/Bank or Accounts Payable
        if data.get('payment_method') == 'Credit':
            credit_account = 'Accounts Payable'
        elif data.get('payment_method') == 'Bank':
            credit_account = 'Bank Account'
        else:
            credit_account = 'Cash Account'
            
        FarmUtils.add_ledger_entry(
            session=session,
            date=data['date'],
            account_name=credit_account,
            account_type='Asset' if credit_account in ['Cash Account', 'Bank Account'] else 'Liability',
            debit=0,
            credit=data['amount'],
            reference_type='livestock',
            reference_id=expense.id,
            description=f"Payment for {data['animal_type']} expense"
        )
        
        return expense
    
    @staticmethod
    def record_water_bill(session, data):
        """Record water bill with ledger entries"""
        hours_used = FarmUtils.calculate_hours(data['start_time'], data['end_time'])
        total_bill = hours_used * data['rate_per_hour']
        balance_due = total_bill - data.get('amount_paid', 0)
        
        water_bill = WaterBill(
            farmer_name=data['farmer_name'],
            date=data['date'],
            start_time=datetime.combine(data['date'], data['start_time']),
            end_time=datetime.combine(data['date'], data['end_time']),
            hours_used=hours_used,
            rate_per_hour=data['rate_per_hour'],
            total_bill=total_bill,
            amount_paid=data.get('amount_paid', 0),
            balance_due=balance_due,
            payment_status='Paid' if balance_due == 0 else 'Partial' if data.get('amount_paid', 0) > 0 else 'Pending',
            payment_method=data.get('payment_method'),
            notes=data.get('notes')
        )
        
        session.add(water_bill)
        session.flush()
        
        # Update farmer balance
        farmer = session.query(Farmer).filter_by(name=data['farmer_name']).first()
        if farmer:
            farmer.total_bill += total_bill
            farmer.total_paid += data.get('amount_paid', 0)
            farmer.balance_due += balance_due
        
        # Ledger entries
        # Debit: Accounts Receivable (Farmer)
        FarmUtils.add_ledger_entry(
            session=session,
            date=data['date'],
            account_name=f"Receivable - {data['farmer_name']}",
            account_type='Asset',
            debit=total_bill,
            credit=0,
            reference_type='water',
            reference_id=water_bill.id,
            description=f"Water bill for {hours_used} hours"
        )
        
        # Credit: Water Income
        FarmUtils.add_ledger_entry(
            session=session,
            date=data['date'],
            account_name='Water Income',
            account_type='Income',
            debit=0,
            credit=total_bill,
            reference_type='water',
            reference_id=water_bill.id,
            description=f"Income from {data['farmer_name']}"
        )
        
        # If partial payment received
        if data.get('amount_paid', 0) > 0:
            payment = Payment(
                date=data['date'],
                payee_name=data['farmer_name'],
                payer_name='Farm',
                amount=data['amount_paid'],
                payment_method=data.get('payment_method', 'Cash'),
                reference_type='water',
                reference_id=water_bill.id,
                description=f"Payment for water bill"
            )
            session.add(payment)
            
            # Record payment in ledger
            FarmUtils.add_ledger_entry(
                session=session,
                date=data['date'],
                account_name='Cash Account' if data.get('payment_method') == 'Cash' else 'Bank Account',
                account_type='Asset',
                debit=data['amount_paid'],
                credit=0,
                reference_type='payment',
                reference_id=payment.id,
                description=f"Payment from {data['farmer_name']}"
            )
            
            FarmUtils.add_ledger_entry(
                session=session,
                date=data['date'],
                account_name=f"Receivable - {data['farmer_name']}",
                account_type='Asset',
                debit=0,
                credit=data['amount_paid'],
                reference_type='payment',
                reference_id=payment.id,
                description=f"Payment received"
            )
        
        return water_bill

# ============================================
# SESSION STATE INITIALIZATION
# ============================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = True
if 'current_user' not in st.session_state:
    st.session_state.current_user = "Admin"
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False

# ============================================
# DATABASE INITIALIZATION
# ============================================
@st.cache_resource
def init_database():
    db = DatabaseManager()
    if not st.session_state.db_initialized:
        db.init_sample_data()
        st.session_state.db_initialized = True
    return db

db = init_database()
utils = FarmUtils()

# ============================================
# HELPER FUNCTIONS FOR UI
# ============================================
def display_data_with_actions(df, table_name, key_suffix):
    """Display dataframe with edit/delete actions"""
    if df.empty:
        st.info("No records found.")
        return
    
    st.dataframe(df, use_container_width=True)
    
    st.subheader("Edit/Delete Records")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        record_id = st.number_input(f"Enter Record ID to edit/delete", 
                                   min_value=1, key=f"edit_id_{key_suffix}")
    
    with col2:
        if st.button("📝 Edit Record", key=f"edit_btn_{key_suffix}"):
            st.session_state[f'edit_{table_name}_{record_id}'] = True
    
    with col3:
        if st.button("🗑️ Delete Record", key=f"delete_btn_{key_suffix}"):
            session = db.get_session()
            try:
                # Find and delete record
                if table_name == 'livestock_expenses':
                    record = session.query(LivestockExpense).get(record_id)
                elif table_name == 'crop_expenses':
                    record = session.query(CropExpense).get(record_id)
                elif table_name == 'water_bills':
                    record = session.query(WaterBill).get(record_id)
                elif table_name == 'operational_expenses':
                    record = session.query(OperationalExpense).get(record_id)
                
                if record:
                    # Also delete related ledger entries
                    ledger_entries = session.query(LedgerEntry).filter(
                        and_(
                            LedgerEntry.reference_type == table_name[:-1],  # Remove 's' from table name
                            LedgerEntry.reference_id == record_id
                        )
                    ).all()
                    
                    for ledger in ledger_entries:
                        session.delete(ledger)
                    
                    session.delete(record)
                    session.commit()
                    st.success(f"Record {record_id} deleted successfully!")
                    st.rerun()
                else:
                    st.error("Record not found!")
            except Exception as e:
                session.rollback()
                st.error(f"Error deleting record: {e}")
            finally:
                session.close()

def get_profit_loss_report(start_date, end_date):
    """Generate profit and loss report"""
    session = db.get_session()
    try:
        # Livestock Income
        livestock_income = session.query(func.sum(LivestockIncome.amount)).filter(
            and_(
                LivestockIncome.date >= start_date,
                LivestockIncome.date <= end_date
            )
        ).scalar() or 0
        
        # Crop Income
        crop_income = session.query(func.sum(CropIncome.amount)).filter(
            and_(
                CropIncome.date >= start_date,
                CropIncome.date <= end_date
            )
        ).scalar() or 0
        
        # Water Income
        water_income = session.query(func.sum(WaterBill.total_bill)).filter(
            and_(
                WaterBill.date >= start_date,
                WaterBill.date <= end_date
            )
        ).scalar() or 0
        
        # Livestock Expenses
        livestock_expense = session.query(func.sum(LivestockExpense.amount)).filter(
            and_(
                LivestockExpense.date >= start_date,
                LivestockExpense.date <= end_date
            )
        ).scalar() or 0
        
        # Crop Expenses
        crop_expense = session.query(func.sum(CropExpense.amount)).filter(
            and_(
                CropExpense.date >= start_date,
                CropExpense.date <= end_date
            )
        ).scalar() or 0
        
        # Operational Expenses
        operational_expense = session.query(func.sum(OperationalExpense.amount)).filter(
            and_(
                OperationalExpense.date >= start_date,
                OperationalExpense.date <= end_date
            )
        ).scalar() or 0
        
        total_income = livestock_income + crop_income + water_income
        total_expense = livestock_expense + crop_expense + operational_expense
        net_profit = total_income - total_expense
        
        summary_data = [
            {'category': 'Livestock Income', 'income': livestock_income, 'expense': 0},
            {'category': 'Crop Income', 'income': crop_income, 'expense': 0},
            {'category': 'Water Income', 'income': water_income, 'expense': 0},
            {'category': 'Livestock Expenses', 'income': 0, 'expense': livestock_expense},
            {'category': 'Crop Expenses', 'income': 0, 'expense': crop_expense},
            {'category': 'Operational Expenses', 'income': 0, 'expense': operational_expense},
        ]
        
        summary_df = pd.DataFrame(summary_data)
        
        return {
            'summary': summary_df,
            'total_income': total_income,
            'total_expense': total_expense,
            'net_profit': net_profit
        }
    finally:
        session.close()

# ============================================
# SIDEBAR NAVIGATION
# ============================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1046/1046784.png", width=100)
st.sidebar.title("🌾 Farm Management")

st.sidebar.markdown(f"**User:** {st.session_state.current_user}")
st.sidebar.markdown(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")

menu_options = [
    "🏠 Dashboard",
    "🐄 Livestock Management",
    "🌱 Crop Management",
    "💧 Water Income",
    "💰 Operational Expenses",
    "📊 Reports & Analytics",
    "🧾 General Ledger",
    "👥 Farmers & Employees",
    "⚙️ Settings"
]

selected_menu = st.sidebar.selectbox("Navigation", menu_options)

# ============================================
# DASHBOARD PAGE
# ============================================
if selected_menu == "🏠 Dashboard":
    st.markdown("<h1 class='main-header'>Farm Management Dashboard</h1>", unsafe_allow_html=True)
    
    # Get summary statistics
    stats = db.get_summary_stats()
    
    # KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Monthly Income", 
            f"PKR {stats['water_income_month']:,.0f}"
        )
    
    with col2:
        total_expenses = stats['livestock_expenses_month'] + stats['crop_expenses_month'] + stats['operational_expenses_month']
        st.metric(
            "Monthly Expenses", 
            f"PKR {total_expenses:,.0f}"
        )
    
    with col3:
        st.metric(
            "Outstanding Balance", 
            f"PKR {stats['outstanding_balance']:,.0f}"
        )
    
    with col4:
        st.metric(
            "Active Employees", 
            f"{stats['active_employees']}"
        )
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Monthly Income Distribution")
        
        income_data = pd.DataFrame({
            'Category': ['Water', 'Livestock', 'Crops'],
            'Amount': [
                stats['water_income_month'],
                stats['livestock_expenses_month'] * 0.5,
                stats['crop_expenses_month'] * 0.7
            ]
        })
        
        fig = px.pie(income_data, values='Amount', names='Category', hole=0.3)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("Expense Breakdown")
        
        expense_data = pd.DataFrame({
            'Category': ['Livestock', 'Crops', 'Operations'],
            'Amount': [
                stats['livestock_expenses_month'],
                stats['crop_expenses_month'],
                stats['operational_expenses_month']
            ]
        })
        
        fig = px.bar(expense_data, x='Category', y='Amount', color='Category')
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent Activity
    st.subheader("Recent Activity")
    
    col1, col2 = st.columns(2)
    
    with col1:
        session = db.get_session()
        try:
            recent_expenses = session.query(LivestockExpense)\
                .order_by(desc(LivestockExpense.date))\
                .limit(5)\
                .all()
            
            if recent_expenses:
                expense_list = []
                for exp in recent_expenses:
                    expense_list.append({
                        'Date': exp.date,
                        'Type': f"{exp.animal_type} - {exp.expense_type}",
                        'Amount': f"PKR {exp.amount:,.0f}"
                    })
                
                df_expenses = pd.DataFrame(expense_list)
                st.dataframe(df_expenses, use_container_width=True, hide_index=True)
            else:
                st.info("No recent expenses")
        finally:
            session.close()
    
    with col2:
        session = db.get_session()
        try:
            recent_bills = session.query(WaterBill)\
                .order_by(desc(WaterBill.date))\
                .limit(5)\
                .all()
            
            if recent_bills:
                bill_list = []
                for bill in recent_bills:
                    bill_list.append({
                        'Date': bill.date,
                        'Farmer': bill.farmer_name,
                        'Bill': f"PKR {bill.total_bill:,.0f}",
                        'Status': bill.payment_status
                    })
                
                df_bills = pd.DataFrame(bill_list)
                st.dataframe(df_bills, use_container_width=True, hide_index=True)
            else:
                st.info("No recent water bills")
        finally:
            session.close()

# ============================================
# LIVESTOCK MANAGEMENT PAGE
# ============================================
elif selected_menu == "🐄 Livestock Management":
    st.markdown("<h1 class='main-header'>Livestock Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Expense", "💰 Add Income", "📊 View Records", "📈 Reports"])
    
    with tab1:
        st.subheader("Add Livestock Expense")
        
        with st.form("livestock_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Date", datetime.now())
                animal_type = st.selectbox("Animal Type", 
                    ["Cow", "Goat", "Sheep", "Buffalo", "Chicken", "Other"])
                expense_type = st.selectbox("Expense Type",
                    ["Wanda (Feed)", "Chokar", "Khal", "Tori", "Khas", 
                     "Medicine", "Veterinary", "Labor", "Other"])
                
            with col2:
                amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0)
                quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
                unit_price = st.number_input("Unit Price", min_value=0.0, step=10.0)
            
            col3, col4 = st.columns(2)
            
            with col3:
                paid_by = st.selectbox("Paid By", 
                    ["Cash", "Bank Transfer", "Credit", "Employee Advance"])
                payment_method = st.selectbox("Payment Method",
                    ["Cash", "Bank Transfer", "Check", "Mobile Payment"])
            
            with col4:
                notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("💾 Save Expense", type="primary")
            
            if submitted:
                session = db.get_session()
                try:
                    expense_data = {
                        'date': expense_date,
                        'animal_type': animal_type,
                        'expense_type': expense_type,
                        'amount': amount,
                        'paid_by': paid_by,
                        'payment_method': payment_method,
                        'quantity': quantity if quantity > 0 else None,
                        'unit_price': unit_price if unit_price > 0 else None,
                        'notes': notes if notes else None
                    }
                    
                    utils.record_livestock_expense(session, expense_data)
                    session.commit()
                    st.success("✅ Livestock expense recorded successfully!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error saving expense: {e}")
                finally:
                    session.close()
    
    with tab2:
        st.subheader("Add Livestock Income")
        
        with st.form("livestock_income_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                income_date = st.date_input("Income Date", datetime.now(), key="income_date")
                animal_type = st.selectbox("Animal Type", 
                    ["Cow", "Goat", "Sheep", "Buffalo", "Chicken", "Other"],
                    key="income_animal")
                income_type = st.selectbox("Income Type",
                    ["Milk Sale", "Animal Sale", "Manure Sale", "Other"],
                    key="income_type")
                
            with col2:
                amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0, key="income_amount")
                quantity = st.number_input("Quantity", min_value=0.0, step=1.0, key="income_qty")
                unit_price = st.number_input("Unit Price", min_value=0.0, step=10.0, key="income_price")
            
            buyer_name = st.text_input("Buyer Name (if any)")
            payment_method = st.selectbox("Payment Method",
                ["Cash", "Bank Transfer", "Check", "Mobile Payment"],
                key="income_payment")
            notes = st.text_area("Notes", key="income_notes")
            
            submitted = st.form_submit_button("💰 Record Income", type="primary")
            
            if submitted:
                session = db.get_session()
                try:
                    income = LivestockIncome(
                        date=income_date,
                        animal_type=animal_type,
                        income_type=income_type,
                        amount=amount,
                        quantity=quantity if quantity > 0 else None,
                        unit_price=unit_price if unit_price > 0 else None,
                        buyer_name=buyer_name if buyer_name else None,
                        payment_method=payment_method,
                        notes=notes if notes else None
                    )
                    
                    session.add(income)
                    
                    # Ledger entry for income
                    utils.add_ledger_entry(
                        session=session,
                        date=income_date,
                        account_name='Livestock Income',
                        account_type='Income',
                        debit=0,
                        credit=amount,
                        reference_type='livestock_income',
                        reference_id=income.id,
                        description=f"{animal_type} - {income_type}"
                    )
                    
                    # Ledger entry for cash/bank
                    if payment_method == 'Bank':
                        cash_account = 'Bank Account'
                    else:
                        cash_account = 'Cash Account'
                        
                    utils.add_ledger_entry(
                        session=session,
                        date=income_date,
                        account_name=cash_account,
                        account_type='Asset',
                        debit=amount,
                        credit=0,
                        reference_type='livestock_income',
                        reference_id=income.id,
                        description=f"Payment received for {income_type}"
                    )
                    
                    session.commit()
                    st.success("✅ Livestock income recorded successfully!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error saving income: {e}")
                finally:
                    session.close()
    
    with tab3:
        st.subheader("View Livestock Records")
        
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Start Date", 
                datetime.now().replace(day=1))
        with col2:
            end_date = st.date_input("End Date", datetime.now())
        with col3:
            record_type = st.selectbox("Record Type", 
                ["All", "Expenses", "Income"])
        
        # Fetch and display data
        session = db.get_session()
        try:
            if record_type in ["All", "Expenses"]:
                st.subheader("Expenses")
                expenses = session.query(LivestockExpense)\
                    .filter(and_(
                        LivestockExpense.date >= start_date,
                        LivestockExpense.date <= end_date
                    ))\
                    .order_by(desc(LivestockExpense.date))\
                    .all()
                
                if expenses:
                    expense_data = []
                    for exp in expenses:
                        expense_data.append({
                            'ID': exp.id,
                            'Date': exp.date,
                            'Animal': exp.animal_type,
                            'Type': exp.expense_type,
                            'Amount': exp.amount,
                            'Paid By': exp.paid_by,
                            'Method': exp.payment_method,
                            'Notes': exp.notes
                        })
                    
                    df_expenses = pd.DataFrame(expense_data)
                    display_data_with_actions(df_expenses, 'livestock_expenses', 'livestock_exp')
                else:
                    st.info("No expense records found")
            
            if record_type in ["All", "Income"]:
                st.subheader("Income")
                incomes = session.query(LivestockIncome)\
                    .filter(and_(
                        LivestockIncome.date >= start_date,
                        LivestockIncome.date <= end_date
                    ))\
                    .order_by(desc(LivestockIncome.date))\
                    .all()
                
                if incomes:
                    income_data = []
                    for inc in incomes:
                        income_data.append({
                            'ID': inc.id,
                            'Date': inc.date,
                            'Animal': inc.animal_type,
                            'Type': inc.income_type,
                            'Amount': inc.amount,
                            'Buyer': inc.buyer_name,
                            'Method': inc.payment_method,
                            'Notes': inc.notes
                        })
                    
                    df_incomes = pd.DataFrame(income_data)
                    st.dataframe(df_incomes, use_container_width=True)
                else:
                    st.info("No income records found")
        finally:
            session.close()
    
    with tab4:
        st.subheader("Livestock Reports")
        
        session = db.get_session()
        try:
            # Total expenses by animal type
            expense_summary = session.query(
                LivestockExpense.animal_type,
                func.sum(LivestockExpense.amount).label('total')
            ).group_by(LivestockExpense.animal_type).all()
            
            if expense_summary:
                df_exp_summary = pd.DataFrame(expense_summary, columns=['Animal Type', 'Total Expense'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(df_exp_summary, use_container_width=True)
                
                with col2:
                    fig = px.pie(df_exp_summary, values='Total Expense', names='Animal Type', 
                                title='Expenses by Animal Type')
                    st.plotly_chart(fig, use_container_width=True)
        finally:
            session.close()

# ============================================
# CROP MANAGEMENT PAGE
# ============================================
elif selected_menu == "🌱 Crop Management":
    st.markdown("<h1 class='main-header'>Crop Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Add Expense", "📊 View Records", "📈 Analysis"])
    
    with tab1:
        st.subheader("Add Crop Expense")
        
        with st.form("crop_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Date", datetime.now(), key="crop_date")
                crop_name = st.selectbox("Crop Name",
                    ["Wheat", "Rice", "Cotton", "Sugarcane", "Maize", 
                     "Vegetables", "Fruits", "Other"], key="crop_name")
                expense_type = st.selectbox("Expense Type",
                    ["Khad (Fertilizer)", "Sapry (Spray)", "Seed", 
                     "Irrigation", "Labor", "Land Preparation", "Harvesting", "Other"],
                    key="crop_exp_type")
                
            with col2:
                amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0, key="crop_amount")
                quantity = st.number_input("Quantity", min_value=0.0, step=1.0, key="crop_qty")
                unit = st.selectbox("Unit", 
                    ["KG", "Liters", "Bags", "Acres", "Hours", "Other"],
                    key="crop_unit")
            
            paid_by = st.selectbox("Paid By",
                ["Cash", "Bank Transfer", "Credit", "Employee Advance"],
                key="crop_paid_by")
            payment_method = st.selectbox("Payment Method",
                ["Cash", "Bank Transfer", "Check", "Mobile Payment"],
                key="crop_payment")
            notes = st.text_area("Notes", key="crop_notes")
            
            submitted = st.form_submit_button("💾 Save Crop Expense", type="primary")
            
            if submitted:
                session = db.get_session()
                try:
                    crop_expense = CropExpense(
                        date=expense_date,
                        crop_name=crop_name,
                        expense_type=expense_type,
                        amount=amount,
                        quantity=quantity if quantity > 0 else None,
                        unit=unit,
                        paid_by=paid_by,
                        payment_method=payment_method,
                        notes=notes if notes else None
                    )
                    
                    session.add(crop_expense)
                    session.flush()
                    
                    # Ledger entries
                    utils.add_ledger_entry(
                        session=session,
                        date=expense_date,
                        account_name='Crop Expenses',
                        account_type='Expense',
                        debit=amount,
                        credit=0,
                        reference_type='crop',
                        reference_id=crop_expense.id,
                        description=f"{crop_name} - {expense_type}"
                    )
                    
                    if paid_by == 'Credit':
                        credit_account = 'Accounts Payable'
                    elif payment_method == 'Bank':
                        credit_account = 'Bank Account'
                    else:
                        credit_account = 'Cash Account'
                        
                    utils.add_ledger_entry(
                        session=session,
                        date=expense_date,
                        account_name=credit_account,
                        account_type='Asset' if credit_account in ['Cash Account', 'Bank Account'] else 'Liability',
                        debit=0,
                        credit=amount,
                        reference_type='crop',
                        reference_id=crop_expense.id,
                        description=f"Payment for {crop_name} expense"
                    )
                    
                    session.commit()
                    st.success("✅ Crop expense recorded successfully!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error saving crop expense: {e}")
                finally:
                    session.close()
    
    with tab2:
        st.subheader("View Crop Records")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", 
                datetime.now().replace(day=1), key="crop_start")
        with col2:
            end_date = st.date_input("End Date", datetime.now(), key="crop_end")
        
        crop_filter = st.selectbox("Filter by Crop", 
            ["All Crops", "Wheat", "Rice", "Cotton", "Sugarcane", "Maize", "Vegetables"])
        
        session = db.get_session()
        try:
            query = session.query(CropExpense)\
                .filter(and_(
                    CropExpense.date >= start_date,
                    CropExpense.date <= end_date
                ))
            
            if crop_filter != "All Crops":
                query = query.filter(CropExpense.crop_name == crop_filter)
            
            expenses = query.order_by(desc(CropExpense.date)).all()
            
            if expenses:
                expense_data = []
                for exp in expenses:
                    expense_data.append({
                        'ID': exp.id,
                        'Date': exp.date,
                        'Crop': exp.crop_name,
                        'Expense Type': exp.expense_type,
                        'Amount': exp.amount,
                        'Quantity': exp.quantity,
                        'Unit': exp.unit,
                        'Paid By': exp.paid_by,
                        'Notes': exp.notes
                    })
                
                df = pd.DataFrame(expense_data)
                display_data_with_actions(df, 'crop_expenses', 'crop')
                
                total_expense = df['Amount'].sum()
                st.metric("Total Expenses in Period", f"PKR {total_expense:,.2f}")
            else:
                st.info("No crop expense records found")
        finally:
            session.close()
    
    with tab3:
        st.subheader("Crop Analysis")
        
        session = db.get_session()
        try:
            crop_summary = session.query(
                CropExpense.crop_name,
                func.sum(CropExpense.amount).label('total_expense')
            ).group_by(CropExpense.crop_name).all()
            
            if crop_summary:
                df_crops = pd.DataFrame(crop_summary, columns=['Crop', 'Total Expense'])
                
                col1, col2 = st.columns(2)
                with col1:
                    st.dataframe(df_crops.sort_values('Total Expense', ascending=False), 
                               use_container_width=True)
                
                with col2:
                    fig = px.bar(df_crops, x='Crop', y='Total Expense',
                                title='Expenses by Crop')
                    st.plotly_chart(fig, use_container_width=True)
        finally:
            session.close()

# ============================================
# WATER INCOME PAGE
# ============================================
elif selected_menu == "💧 Water Income":
    st.markdown("<h1 class='main-header'>Water Income Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Bill", "💰 Record Payment", "📊 View Bills", "📈 Outstanding"])
    
    with tab1:
        st.subheader("Create Water Bill")
        
        with st.form("water_bill_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                session = db.get_session()
                farmers = session.query(Farmer).all()
                farmer_names = [f.name for f in farmers]
                session.close()
                
                if not farmer_names:
                    farmer_names = ["New Farmer"]
                
                farmer_name = st.selectbox("Farmer Name", farmer_names)
                if farmer_name == "New Farmer":
                    farmer_name = st.text_input("Enter New Farmer Name")
                
                bill_date = st.date_input("Date", datetime.now())
                
                col1a, col1b = st.columns(2)
                with col1a:
                    start_time = st.time_input("Start Time", datetime.now().time())
                with col1b:
                    end_time = st.time_input("End Time", 
                        (datetime.now() + timedelta(hours=2)).time())
            
            with col2:
                rate_per_hour = st.number_input("Rate per Hour (PKR)", 
                    min_value=0.0, value=500.0, step=50.0)
                
                hours_used = utils.calculate_hours(start_time, end_time)
                total_bill = hours_used * rate_per_hour
                
                st.metric("Hours Used", f"{hours_used:.2f}")
                st.metric("Total Bill", f"PKR {total_bill:,.2f}")
                
                amount_paid = st.number_input("Amount Paid Now", 
                    min_value=0.0, max_value=total_bill, value=0.0, step=100.0)
                balance_due = total_bill - amount_paid
                
                if balance_due > 0:
                    st.warning(f"Balance Due: PKR {balance_due:,.2f}")
                else:
                    st.success("Fully Paid!")
            
            payment_method = st.selectbox("Payment Method",
                ["Cash", "Bank Transfer", "Check", "Mobile Payment", "Credit"])
            notes = st.text_area("Notes")
            
            submitted = st.form_submit_button("💧 Generate Bill", type="primary")
            
            if submitted:
                session = db.get_session()
                try:
                    farmer = session.query(Farmer).filter_by(name=farmer_name).first()
                    if not farmer:
                        farmer = Farmer(name=farmer_name)
                        session.add(farmer)
                    
                    bill_data = {
                        'farmer_name': farmer_name,
                        'date': bill_date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'rate_per_hour': rate_per_hour,
                        'amount_paid': amount_paid,
                        'payment_method': payment_method if amount_paid > 0 else None,
                        'notes': notes if notes else None
                    }
                    
                    utils.record_water_bill(session, bill_data)
                    session.commit()
                    
                    st.success(f"✅ Water bill created successfully!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error creating bill: {e}")
                finally:
                    session.close()
    
    with tab2:
        st.subheader("Record Payment for Existing Bill")
        
        session = db.get_session()
        try:
            unpaid_bills = session.query(WaterBill)\
                .filter(WaterBill.balance_due > 0)\
                .all()
            
            if not unpaid_bills:
                st.info("No outstanding bills found")
            else:
                bill_options = {f"{b.farmer_name} - PKR {b.balance_due:,.2f} (Bill #{b.id})": b.id 
                               for b in unpaid_bills}
                
                selected_bill = st.selectbox("Select Bill", list(bill_options.keys()))
                bill_id = bill_options[selected_bill]
                
                bill = session.query(WaterBill).get(bill_id)
                
                if bill:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Farmer:** {bill.farmer_name}")
                        st.write(f"**Total Bill:** PKR {bill.total_bill:,.2f}")
                        st.write(f"**Already Paid:** PKR {bill.amount_paid:,.2f}")
                        st.write(f"**Balance Due:** PKR {bill.balance_due:,.2f}")
                    
                    with col2:
                        payment_date = st.date_input("Payment Date", datetime.now())
                        payment_amount = st.number_input("Payment Amount", 
                            min_value=0.0, max_value=bill.balance_due, 
                            value=bill.balance_due, step=100.0)
                        payment_method = st.selectbox("Payment Method",
                            ["Cash", "Bank Transfer", "Check", "Mobile Payment"])
                        
                        if st.button("💳 Record Payment", type="primary"):
                            bill.amount_paid += payment_amount
                            bill.balance_due -= payment_amount
                            bill.payment_status = 'Paid' if bill.balance_due == 0 else 'Partial'
                            bill.payment_date = payment_date
                            bill.payment_method = payment_method
                            
                            farmer = session.query(Farmer).filter_by(name=bill.farmer_name).first()
                            if farmer:
                                farmer.total_paid += payment_amount
                                farmer.balance_due -= payment_amount
                            
                            # Record payment
                            payment = Payment(
                                date=payment_date,
                                payee_name=bill.farmer_name,
                                payer_name='Farm',
                                amount=payment_amount,
                                payment_method=payment_method,
                                reference_type='water',
                                reference_id=bill.id,
                                description=f"Payment for water bill #{bill.id}"
                            )
                            session.add(payment)
                            
                            session.commit()
                            st.success(f"✅ Payment of PKR {payment_amount:,.2f} recorded successfully!")
                            st.rerun()
        finally:
            session.close()
    
    with tab3:
        st.subheader("View Water Bills")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            start_date = st.date_input("Start Date", 
                datetime.now().replace(day=1), key="water_start")
        with col2:
            end_date = st.date_input("End Date", datetime.now(), key="water_end")
        with col3:
            status_filter = st.selectbox("Payment Status",
                ["All", "Paid", "Partial", "Pending"])
        
        session = db.get_session()
        try:
            query = session.query(WaterBill)\
                .filter(and_(
                    WaterBill.date >= start_date,
                    WaterBill.date <= end_date
                ))
            
            if status_filter != "All":
                query = query.filter(WaterBill.payment_status == status_filter)
            
            bills = query.order_by(desc(WaterBill.date)).all()
            
            if bills:
                bill_data = []
                for bill in bills:
                    bill_data.append({
                        'ID': bill.id,
                        'Date': bill.date,
                        'Farmer': bill.farmer_name,
                        'Hours': bill.hours_used,
                        'Rate': bill.rate_per_hour,
                        'Total Bill': bill.total_bill,
                        'Paid': bill.amount_paid,
                        'Balance': bill.balance_due,
                        'Status': bill.payment_status,
                        'Method': bill.payment_method
                    })
                
                df = pd.DataFrame(bill_data)
                display_data_with_actions(df, 'water_bills', 'water')
                
                total_bills = df['Total Bill'].sum()
                total_paid = df['Paid'].sum()
                total_balance = df['Balance'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Bills", f"PKR {total_bills:,.2f}")
                with col2:
                    st.metric("Total Paid", f"PKR {total_paid:,.2f}")
                with col3:
                    st.metric("Total Outstanding", f"PKR {total_balance:,.2f}")
            else:
                st.info("No water bills found")
        finally:
            session.close()
    
    with tab4:
        st.subheader("Outstanding Balances")
        
        session = db.get_session()
        try:
            farmers = session.query(Farmer)\
                .filter(Farmer.balance_due > 0)\
                .order_by(desc(Farmer.balance_due))\
                .all()
            
            if farmers:
                farmer_data = []
                for farmer in farmers:
                    farmer_data.append({
                        'Name': farmer.name,
                        'Phone': farmer.phone,
                        'Total Bills': farmer.total_bill,
                        'Total Paid': farmer.total_paid,
                        'Balance Due': farmer.balance_due
                    })
                
                df = pd.DataFrame(farmer_data)
                st.dataframe(df, use_container_width=True)
                
                fig = px.bar(df, x='Name', y='Balance Due', 
                           title='Outstanding Balances by Farmer')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("🎉 No outstanding balances!")
        finally:
            session.close()

# ============================================
# OPERATIONAL EXPENSES PAGE
# ============================================
elif selected_menu == "💰 Operational Expenses":
    st.markdown("<h1 class='main-header'>Operational Expenses</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📝 Add Expense", "💳 Make Payment", "📊 View Expenses"])
    
    with tab1:
        st.subheader("Add Operational Expense")
        
        with st.form("operational_expense_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                expense_date = st.date_input("Date", datetime.now(), key="op_date")
                expense_type = st.selectbox("Expense Type",
                    ["Employee Salaries", "Fuel", "Machinery Purchase", 
                     "Machinery Maintenance", "Utilities", "Rent", 
                     "Insurance", "Office Supplies", "Other"],
                    key="op_type")
                
                category = st.selectbox("Category",
                    ["Employee", "Fuel", "Machinery", "Maintenance", "Administrative", "Other"],
                    key="op_category")
                
            with col2:
                amount = st.number_input("Amount (PKR)", min_value=0.0, step=100.0, key="op_amount")
                managed_by = st.text_input("Managed By (Employee Name)", key="op_manager")
                paid_to = st.text_input("Paid To", key="op_paid_to")
            
            description = st.text_area("Description", key="op_desc")
            
            col3, col4 = st.columns(2)
            with col3:
                payment_method = st.selectbox("Payment Method",
                    ["Cash", "Bank Transfer", "Check", "Credit", "To Be Paid"],
                    key="op_payment")
            with col4:
                is_paid = st.checkbox("Mark as Paid", key="op_paid")
                if is_paid:
                    paid_amount = st.number_input("Paid Amount", 
                        min_value=0.0, max_value=amount, value=amount, key="op_paid_amt")
            
            submitted = st.form_submit_button("💾 Save Expense", type="primary")
            
            if submitted:
                session = db.get_session()
                try:
                    paid_amt = paid_amount if is_paid else 0
                    balance = amount - paid_amt
                    
                    op_expense = OperationalExpense(
                        date=expense_date,
                        expense_type=expense_type,
                        category=category,
                        managed_by=managed_by,
                        amount=amount,
                        paid_to=paid_to,
                        paid_amount=paid_amt,
                        balance_due=balance,
                        description=description,
                        payment_method=payment_method if is_paid else None,
                        is_paid=is_paid
                    )
                    
                    session.add(op_expense)
                    session.flush()
                    
                    # Ledger entries
                    utils.add_ledger_entry(
                        session=session,
                        date=expense_date,
                        account_name=f"Operational - {expense_type}",
                        account_type='Expense',
                        debit=amount,
                        credit=0,
                        reference_type='operational',
                        reference_id=op_expense.id,
                        description=description
                    )
                    
                    if is_paid:
                        if payment_method == 'Bank':
                            credit_account = 'Bank Account'
                        else:
                            credit_account = 'Cash Account'
                    else:
                        credit_account = 'Accounts Payable'
                    
                    utils.add_ledger_entry(
                        session=session,
                        date=expense_date,
                        account_name=credit_account,
                        account_type='Asset' if credit_account in ['Cash Account', 'Bank Account'] else 'Liability',
                        debit=0,
                        credit=amount,
                        reference_type='operational',
                        reference_id=op_expense.id,
                        description=f"Payment for {expense_type}"
                    )
                    
                    session.commit()
                    st.success("✅ Operational expense recorded successfully!")
                except Exception as e:
                    session.rollback()
                    st.error(f"Error saving expense: {e}")
                finally:
                    session.close()
    
    with tab2:
        st.subheader("Make Payment for Outstanding Expenses")
        
        session = db.get_session()
        try:
            unpaid_expenses = session.query(OperationalExpense)\
                .filter(OperationalExpense.balance_due > 0)\
                .all()
            
            if not unpaid_expenses:
                st.info("No outstanding operational expenses")
            else:
                exp_options = {f"{exp.expense_type} - PKR {exp.balance_due:,.2f} (ID: {exp.id})": exp.id 
                              for exp in unpaid_expenses}
                
                selected_exp = st.selectbox("Select Expense", list(exp_options.keys()))
                exp_id = exp_options[selected_exp]
                
                expense = session.query(OperationalExpense).get(exp_id)
                
                if expense:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Expense Type:** {expense.expense_type}")
                        st.write(f"**Managed By:** {expense.managed_by}")
                        st.write(f"**Total Amount:** PKR {expense.amount:,.2f}")
                        st.write(f"**Already Paid:** PKR {expense.paid_amount:,.2f}")
                        st.write(f"**Balance Due:** PKR {expense.balance_due:,.2f}")
                        st.write(f"**Description:** {expense.description}")
                    
                    with col2:
                        payment_date = st.date_input("Payment Date", datetime.now(), key="op_pay_date")
                        payment_amount = st.number_input("Payment Amount", 
                            min_value=0.0, max_value=expense.balance_due, 
                            value=expense.balance_due, step=100.0, key="op_pay_amt")
                        payment_method = st.selectbox("Payment Method",
                            ["Cash", "Bank Transfer", "Check", "Mobile Payment"],
                            key="op_pay_method")
                        
                        if st.button("💵 Record Payment", type="primary"):
                            expense.paid_amount += payment_amount
                            expense.balance_due -= payment_amount
                            expense.is_paid = expense.balance_due == 0
                            expense.payment_method = payment_method
                            
                            if payment_method == 'Bank':
                                debit_account = 'Bank Account'
                            else:
                                debit_account = 'Cash Account'
                            
                            utils.add_ledger_entry(
                                session=session,
                                date=payment_date,
                                account_name=debit_account,
                                account_type='Asset',
                                debit=payment_amount,
                                credit=0,
                                reference_type='operational',
                                reference_id=expense.id,
                                description=f"Payment for {expense.expense_type}"
                            )
                            
                            utils.add_ledger_entry(
                                session=session,
                                date=payment_date,
                                account_name='Accounts Payable',
                                account_type='Liability',
                                debit=0,
                                credit=payment_amount,
                                reference_type='operational',
                                reference_id=expense.id,
                                description=f"Payment made"
                            )
                            
                            session.commit()
                            st.success(f"✅ Payment of PKR {payment_amount:,.2f} recorded successfully!")
                            st.rerun()
        finally:
            session.close()
    
    with tab3:
        st.subheader("View Operational Expenses")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", 
                datetime.now().replace(day=1), key="op_start")
        with col2:
            end_date = st.date_input("End Date", datetime.now(), key="op_end")
        
        category_filter = st.selectbox("Filter by Category",
            ["All", "Employee", "Fuel", "Machinery", "Maintenance", "Administrative"])
        
        session = db.get_session()
        try:
            query = session.query(OperationalExpense)\
                .filter(and_(
                    OperationalExpense.date >= start_date,
                    OperationalExpense.date <= end_date
                ))
            
            if category_filter != "All":
                query = query.filter(OperationalExpense.category == category_filter)
            
            expenses = query.order_by(desc(OperationalExpense.date)).all()
            
            if expenses:
                expense_data = []
                for exp in expenses:
                    expense_data.append({
                        'ID': exp.id,
                        'Date': exp.date,
                        'Type': exp.expense_type,
                        'Category': exp.category,
                        'Managed By': exp.managed_by,
                        'Amount': exp.amount,
                        'Paid': exp.paid_amount,
                        'Balance': exp.balance_due,
                        'Status': 'Paid' if exp.is_paid else 'Partial' if exp.paid_amount > 0 else 'Unpaid',
                        'Description': exp.description
                    })
                
                df = pd.DataFrame(expense_data)
                display_data_with_actions(df, 'operational_expenses', 'op')
                
                total_expense = df['Amount'].sum()
                total_paid = df['Paid'].sum()
                total_balance = df['Balance'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Expense", f"PKR {total_expense:,.2f}")
                with col2:
                    st.metric("Total Paid", f"PKR {total_paid:,.2f}")
                with col3:
                    st.metric("Total Outstanding", f"PKR {total_balance:,.2f}")
            else:
                st.info("No operational expenses found")
        finally:
            session.close()

# ============================================
# REPORTS & ANALYTICS PAGE
# ============================================
elif selected_menu == "📊 Reports & Analytics":
    st.markdown("<h1 class='main-header'>Reports & Analytics</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Profit & Loss", "💰 Cash Flow", "📊 Summary", "📁 Export"])
    
    with tab1:
        st.subheader("Profit & Loss Statement")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("From Date", 
                datetime.now().replace(day=1), key="pl_start")
        with col2:
            end_date = st.date_input("To Date", datetime.now(), key="pl_end")
        
        if st.button("Generate Report", type="primary"):
            report = get_profit_loss_report(start_date, end_date)
            
            if report:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Income", f"PKR {report['total_income']:,.2f}")
                with col2:
                    st.metric("Total Expenses", f"PKR {report['total_expense']:,.2f}")
                with col3:
                    profit_color = "green" if report['net_profit'] >= 0 else "red"
                    st.metric("Net Profit/Loss", 
                            f"PKR {report['net_profit']:,.2f}")
                
                st.subheader("Detailed Breakdown")
                
                income_df = report['summary'][report['summary']['income'] > 0]
                expense_df = report['summary'][report['summary']['expense'] > 0]
                
                col1, col2 = st.columns(2)
                with col1:
                    if not income_df.empty:
                        st.write("**Income Sources**")
                        income_df = income_df.rename(columns={'income': 'Amount'})
                        income_df = income_df[['category', 'Amount']]
                        st.dataframe(income_df, use_container_width=True, hide_index=True)
                        
                        fig = px.pie(income_df, values='Amount', names='category',
                                    title='Income Distribution')
                        st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    if not expense_df.empty:
                        st.write("**Expense Categories**")
                        expense_df = expense_df.rename(columns={'expense': 'Amount'})
                        expense_df = expense_df[['category', 'Amount']]
                        st.dataframe(expense_df, use_container_width=True, hide_index=True)
                        
                        fig = px.pie(expense_df, values='Amount', names='category',
                                    title='Expense Distribution')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data found for the selected period")
    
    with tab2:
        st.subheader("Cash Flow Statement")
        
        start_date = st.date_input("Start Date", 
            datetime.now().replace(day=1), key="cash_start")
        end_date = st.date_input("End Date", datetime.now(), key="cash_end")
        
        session = db.get_session()
        try:
            cash_flow = session.query(
                LedgerEntry.date,
                func.sum(LedgerEntry.debit).label('debit'),
                func.sum(LedgerEntry.credit).label('credit')
            ).filter(and_(
                LedgerEntry.date >= start_date,
                LedgerEntry.date <= end_date,
                LedgerEntry.account_name.in_(['Cash Account', 'Bank Account'])
            )).group_by(LedgerEntry.date).order_by(LedgerEntry.date).all()
            
            if cash_flow:
                cash_data = []
                for cf in cash_flow:
                    cash_data.append({
                        'date': cf.date,
                        'cash_inflow': cf.debit,
                        'cash_outflow': cf.credit,
                        'net_cash_flow': cf.debit - cf.credit
                    })
                
                df = pd.DataFrame(cash_data)
                
                fig = go.Figure()
                fig.add_trace(go.Bar(x=df['date'], y=df['cash_inflow'],
                                    name='Cash Inflow', marker_color='green'))
                fig.add_trace(go.Bar(x=df['date'], y=df['cash_outflow'],
                                    name='Cash Outflow', marker_color='red'))
                fig.update_layout(title='Daily Cash Flow', barmode='group')
                st.plotly_chart(fig, use_container_width=True)
                
                total_inflow = df['cash_inflow'].sum()
                total_outflow = df['cash_outflow'].sum()
                net_flow = total_inflow - total_outflow
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Inflow", f"PKR {total_inflow:,.2f}")
                with col2:
                    st.metric("Total Outflow", f"PKR {total_outflow:,.2f}")
                with col3:
                    st.metric("Net Cash Flow", f"PKR {net_flow:,.2f}")
                
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No cash flow data available")
        finally:
            session.close()
    
    with tab3:
        st.subheader("Summary Reports")
        
        report_type = st.selectbox("Select Report Type",
            ["Monthly Summary", "Category-wise Summary", "Payment Status", "Employee Performance"])
        
        if report_type == "Monthly Summary":
            session = db.get_session()
            try:
                monthly_data = session.query(
                    func.strftime('%Y-%m', LedgerEntry.date).label('month'),
                    func.count(LedgerEntry.id).label('transactions'),
                    func.sum(LedgerEntry.debit).label('total_debit'),
                    func.sum(LedgerEntry.credit).label('total_credit')
                ).group_by('month').order_by(desc('month')).all()
                
                if monthly_data:
                    monthly_list = []
                    for md in monthly_data:
                        monthly_list.append({
                            'Month': md.month,
                            'Transactions': md.transactions,
                            'Total Debit': md.total_debit or 0,
                            'Total Credit': md.total_credit or 0,
                            'Net Balance': (md.total_debit or 0) - (md.total_credit or 0)
                        })
                    
                    df_monthly = pd.DataFrame(monthly_list)
                    st.dataframe(df_monthly, use_container_width=True)
                    
                    fig = px.line(df_monthly, x='Month', y='Net Balance',
                                title='Monthly Net Balance Trend')
                    st.plotly_chart(fig, use_container_width=True)
            finally:
                session.close()
    
    with tab4:
        st.subheader("Export Data")
        
        export_type = st.selectbox("Select Data to Export",
            ["Livestock Expenses", "Crop Expenses", "Water Bills", 
             "Operational Expenses", "Ledger Entries", "All Data"])
        
        col1, col2 = st.columns(2)
        with col1:
            export_start = st.date_input("Start Date", 
                datetime.now().replace(day=1), key="export_start")
        with col2:
            export_end = st.date_input("End Date", datetime.now(), key="export_end")
        
        if st.button("📥 Export to Excel", type="primary"):
            with st.spinner("Exporting data..."):
                session = db.get_session()
                try:
                    if export_type == "All Data":
                        # Create Excel writer
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            # Export each table
                            tables = [
                                ('Livestock Expenses', LivestockExpense),
                                ('Crop Expenses', CropExpense),
                                ('Water Bills', WaterBill),
                                ('Operational Expenses', OperationalExpense),
                                ('Ledger Entries', LedgerEntry)
                            ]
                            
                            for table_name, model in tables:
                                query = session.query(model).filter(
                                    and_(
                                        model.date >= export_start,
                                        model.date <= export_end
                                    )
                                ).all()
                                
                                if query:
                                    data = []
                                    for item in query:
                                        row = {}
                                        for column in model.__table__.columns:
                                            row[column.name] = getattr(item, column.name)
                                        data.append(row)
                                    
                                    df = pd.DataFrame(data)
                                    df.to_excel(writer, sheet_name=table_name[:31], index=False)
                        
                        output.seek(0)
                        st.download_button(
                            label="📥 Download Excel File",
                            data=output,
                            file_name="farm_data_export.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )
                    else:
                        # Export single table
                        if export_type == "Livestock Expenses":
                            model = LivestockExpense
                        elif export_type == "Crop Expenses":
                            model = CropExpense
                        elif export_type == "Water Bills":
                            model = WaterBill
                        elif export_type == "Operational Expenses":
                            model = OperationalExpense
                        elif export_type == "Ledger Entries":
                            model = LedgerEntry
                        
                        query = session.query(model).filter(
                            and_(
                                model.date >= export_start,
                                model.date <= export_end
                            )
                        ).all()
                        
                        if query:
                            data = []
                            for item in query:
                                row = {}
                                for column in model.__table__.columns:
                                    row[column.name] = getattr(item, column.name)
                                data.append(row)
                            
                            df = pd.DataFrame(data)
                            
                            output = io.BytesIO()
                            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                df.to_excel(writer, index=False)
                            output.seek(0)
                            
                            st.download_button(
                                label="📥 Download Excel File",
                                data=output,
                                file_name=f"{export_type.lower().replace(' ', '_')}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.warning("No data found for export")
                finally:
                    session.close()

# ============================================
# GENERAL LEDGER PAGE
# ============================================
elif selected_menu == "🧾 General Ledger":
    st.markdown("<h1 class='main-header'>General Ledger</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📖 View Ledger", "📊 Trial Balance", "🔍 Account Details"])
    
    with tab1:
        st.subheader("General Ledger Entries")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            ledger_start = st.date_input("Start Date", 
                datetime.now().replace(day=1), key="ledger_start")
        with col2:
            ledger_end = st.date_input("End Date", datetime.now(), key="ledger_end")
        with col3:
            account_filter = st.text_input("Filter by Account Name (optional)")
        
        session = db.get_session()
        try:
            query = session.query(LedgerEntry)\
                .filter(and_(
                    LedgerEntry.date >= ledger_start,
                    LedgerEntry.date <= ledger_end
                ))
            
            if account_filter:
                query = query.filter(LedgerEntry.account_name.like(f"%{account_filter}%"))
            
            entries = query.order_by(LedgerEntry.date, LedgerEntry.id).all()
            
            if entries:
                ledger_data = []
                for entry in entries:
                    ledger_data.append({
                        'ID': entry.id,
                        'Date': entry.date,
                        'Account': entry.account_name,
                        'Type': entry.account_type,
                        'Debit': entry.debit,
                        'Credit': entry.credit,
                        'Balance': entry.balance,
                        'Reference': f"{entry.reference_type} #{entry.reference_id}" if entry.reference_id else '',
                        'Description': entry.description
                    })
                
                df = pd.DataFrame(ledger_data)
                st.dataframe(df, use_container_width=True)
                
                total_debit = df['Debit'].sum()
                total_credit = df['Credit'].sum()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Debit", f"PKR {total_debit:,.2f}")
                with col2:
                    st.metric("Total Credit", f"PKR {total_credit:,.2f}")
                
                if abs(total_debit - total_credit) > 0.01:
                    st.error(f"⚠️ Imbalance detected: PKR {abs(total_debit - total_credit):,.2f}")
                else:
                    st.success("✓ Ledger is balanced")
            else:
                st.info("No ledger entries found")
        finally:
            session.close()
    
    with tab2:
        st.subheader("Trial Balance")
        
        trial_date = st.date_input("As of Date", datetime.now(), key="trial_date")
        
        if st.button("Generate Trial Balance", type="primary"):
            session = db.get_session()
            try:
                trial_data = session.query(
                    LedgerEntry.account_name,
                    LedgerEntry.account_type,
                    func.sum(LedgerEntry.debit).label('total_debit'),
                    func.sum(LedgerEntry.credit).label('total_credit')
                ).filter(LedgerEntry.date <= trial_date)\
                 .group_by(LedgerEntry.account_name, LedgerEntry.account_type)\
                 .order_by(LedgerEntry.account_type, LedgerEntry.account_name).all()
                
                if trial_data:
                    trial_list = []
                    for td in trial_data:
                        trial_list.append({
                            'Account Name': td.account_name,
                            'Account Type': td.account_type,
                            'Total Debit': td.total_debit or 0,
                            'Total Credit': td.total_credit or 0
                        })
                    
                    df_trial = pd.DataFrame(trial_list)
                    st.dataframe(df_trial, use_container_width=True)
                    
                    total_debit = df_trial['Total Debit'].sum()
                    total_credit = df_trial['Total Credit'].sum()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Debit", f"PKR {total_debit:,.2f}")
                    with col2:
                        st.metric("Total Credit", f"PKR {total_credit:,.2f}")
                    
                    if abs(total_debit - total_credit) < 0.01:
                        st.success("✅ Trial Balance is balanced!")
                    else:
                        st.error(f"❌ Trial Balance is not balanced! Difference: PKR {abs(total_debit - total_credit):,.2f}")
                else:
                    st.info("No data for trial balance")
            finally:
                session.close()
    
    with tab3:
        st.subheader("Account Details")
        
        session = db.get_session()
        try:
            accounts = session.query(LedgerEntry.account_name)\
                .distinct()\
                .order_by(LedgerEntry.account_name)\
                .all()
            
            account_list = [acc[0] for acc in accounts]
            
            selected_account = st.selectbox("Select Account", account_list)
            
            if selected_account:
                account_details = session.query(LedgerEntry)\
                    .filter(LedgerEntry.account_name == selected_account)\
                    .order_by(LedgerEntry.date)\
                    .all()
                
                if account_details:
                    details_data = []
                    for detail in account_details:
                        details_data.append({
                            'Date': detail.date,
                            'Debit': detail.debit,
                            'Credit': detail.credit,
                            'Balance': detail.balance,
                            'Description': detail.description,
                            'Reference': f"{detail.reference_type} #{detail.reference_id}" if detail.reference_id else ''
                        })
                    
                    df_details = pd.DataFrame(details_data)
                    st.dataframe(df_details, use_container_width=True)
                    
                    current_balance = account_details[-1].balance
                    account_type = account_details[0].account_type
                    
                    st.metric(f"Current Balance ({account_type})", 
                            f"PKR {current_balance:,.2f}")
                    
                    if len(details_data) > 1:
                        fig = px.line(df_details, x='Date', y='Balance',
                                    title=f'{selected_account} - Balance Trend')
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No transactions for this account")
        finally:
            session.close()

# ============================================
# FARMERS & EMPLOYEES PAGE
# ============================================
elif selected_menu == "👥 Farmers & Employees":
    st.markdown("<h1 class='main-header'>Farmers & Employees Management</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["👨‍🌾 Farmers", "👨‍💼 Employees", "➕ Add New"])
    
    with tab1:
        st.subheader("Farmers List")
        
        session = db.get_session()
        try:
            farmers = session.query(Farmer).all()
            
            if farmers:
                farmer_data = []
                for farmer in farmers:
                    farmer_data.append({
                        'ID': farmer.id,
                        'Name': farmer.name,
                        'Phone': farmer.phone,
                        'Address': farmer.address,
                        'Total Bills': farmer.total_bill,
                        'Total Paid': farmer.total_paid,
                        'Balance Due': farmer.balance_due
                    })
                
                df = pd.DataFrame(farmer_data)
                st.dataframe(df, use_container_width=True)
                
                total_farmers = len(farmers)
                total_outstanding = sum(f.balance_due for f in farmers)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Farmers", total_farmers)
                with col2:
                    st.metric("Total Outstanding", f"PKR {total_outstanding:,.2f}")
            else:
                st.info("No farmers registered yet")
        finally:
            session.close()
    
    with tab2:
        st.subheader("Employees List")
        
        session = db.get_session()
        try:
            employees = session.query(Employee).all()
            
            if employees:
                employee_data = []
                for emp in employees:
                    employee_data.append({
                        'ID': emp.id,
                        'Name': emp.name,
                        'Phone': emp.phone,
                        'Role': emp.role,
                        'Salary': emp.salary,
                        'Joining Date': emp.joining_date,
                        'Status': emp.status
                    })
                
                df = pd.DataFrame(employee_data)
                st.dataframe(df, use_container_width=True)
                
                active_employees = sum(1 for e in employees if e.status == 'Active')
                total_salary = sum(e.salary for e in employees if e.status == 'Active')
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Active Employees", active_employees)
                with col2:
                    st.metric("Monthly Salary Expense", f"PKR {total_salary:,.2f}")
            else:
                st.info("No employees registered yet")
        finally:
            session.close()
    
    with tab3:
        st.subheader("Add New Record")
        
        record_type = st.radio("Add New", ["Farmer", "Employee"])
        
        if record_type == "Farmer":
            with st.form("new_farmer_form"):
                name = st.text_input("Farmer Name")
                phone = st.text_input("Phone Number")
                address = st.text_area("Address")
                
                if st.form_submit_button("Add Farmer", type="primary"):
                    session = db.get_session()
                    try:
                        farmer = Farmer(
                            name=name,
                            phone=phone,
                            address=address
                        )
                        session.add(farmer)
                        session.commit()
                        st.success(f"✅ Farmer '{name}' added successfully!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Error adding farmer: {e}")
                    finally:
                        session.close()
        
        else:
            with st.form("new_employee_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    name = st.text_input("Employee Name")
                    phone = st.text_input("Employee Phone")
                    role = st.selectbox("Role", 
                        ["Farm Manager", "Worker", "Driver", "Supervisor", "Accountant", "Other"])
                
                with col2:
                    salary = st.number_input("Monthly Salary", min_value=0.0, step=1000.0)
                    joining_date = st.date_input("Joining Date", datetime.now())
                    status = st.selectbox("Status", ["Active", "Inactive"])
                
                address = st.text_area("Address")
                
                if st.form_submit_button("Add Employee", type="primary"):
                    session = db.get_session()
                    try:
                        employee = Employee(
                            name=name,
                            phone=phone,
                            role=role,
                            salary=salary,
                            address=address,
                            joining_date=joining_date,
                            status=status
                        )
                        session.add(employee)
                        session.commit()
                        st.success(f"✅ Employee '{name}' added successfully!")
                    except Exception as e:
                        session.rollback()
                        st.error(f"Error adding employee: {e}")
                    finally:
                        session.close()

# ============================================
# SETTINGS PAGE
# ============================================
elif selected_menu == "⚙️ Settings":
    st.markdown("<h1 class='main-header'>Settings</h1>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🔄 System Settings", "📁 Backup & Restore", "ℹ️ About"])
    
    with tab1:
        st.subheader("System Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Default Rates**")
            default_water_rate = st.number_input("Default Water Rate per Hour", 
                value=500.0, step=50.0)
            
            st.write("**Expense Categories**")
            livestock_categories = st.text_area("Livestock Expense Categories",
                "Wanda,Chokar,Khal,Tori,Khas,Medicine,Veterinary,Labor,Other")
            crop_categories = st.text_area("Crop Expense Categories",
                "Khad,Sapry,Seed,Irrigation,Land Preparation,Harvesting,Labor,Other")
        
        with col2:
            st.write("**Payment Methods**")
            payment_methods = st.text_area("Available Payment Methods",
                "Cash,Bank Transfer,Check,Mobile Payment,Credit")
            
            st.write("**Animal Types**")
            animal_types = st.text_area("Livestock Animal Types",
                "Cow,Goat,Sheep,Buffalo,Chicken,Other")
        
        if st.button("Save Settings", type="primary"):
            session = db.get_session()
            try:
                # Save settings to database
                settings_to_save = {
                    'default_water_rate': default_water_rate,
                    'livestock_categories': livestock_categories,
                    'crop_categories': crop_categories,
                    'payment_methods': payment_methods,
                    'animal_types': animal_types
                }
                
                for key, value in settings_to_save.items():
                    setting = session.query(Settings).filter_by(key=key).first()
                    if setting:
                        setting.value = str(value)
                    else:
                        setting = Settings(key=key, value=str(value))
                        session.add(setting)
                
                session.commit()
                st.success("Settings saved successfully!")
            except Exception as e:
                session.rollback()
                st.error(f"Error saving settings: {e}")
            finally:
                session.close()
    
    with tab2:
        st.subheader("Backup & Restore")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Backup Database**")
            if st.button("Create Backup", key="backup"):
                import shutil
                try:
                    backup_name = f"farm_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    shutil.copy2('farm_management.db', backup_name)
                    st.success(f"Backup created: {backup_name}")
                except Exception as e:
                    st.error(f"Error creating backup: {e}")
        
        with col2:
            st.write("**Restore Database**")
            uploaded_file = st.file_uploader("Choose backup file", type=['db'])
            
            if uploaded_file is not None:
                if st.button("Restore from Backup", type="primary"):
                    st.warning("⚠️ This will replace all current data. Are you sure?")
                    
                    confirm = st.checkbox("Yes, I understand this will replace all data")
                    if confirm and st.button("Confirm Restore"):
                        try:
                            with open('farm_management_restored.db', 'wb') as f:
                                f.write(uploaded_file.getvalue())
                            st.success("Backup file uploaded. To complete restoration, replace the existing database file.")
                        except Exception as e:
                            st.error(f"Error restoring backup: {e}")
    
    with tab3:
        st.subheader("About Farm Management System")
        
        st.write("### 🌾 Farm Management System v1.0")
        st.write("A comprehensive farm management solution with integrated accounting.")
        st.write("**Features:**")
        st.write("- Livestock expense and income tracking")
        st.write("- Crop management with expense recording")
        st.write("- Water bill generation and payment tracking")
        st.write("- Operational expense management")
        st.write("- Double-entry accounting system")
        st.write("- Profit & loss reporting")
        st.write("- Farmer and employee management")
        st.write("**Developed with:** Streamlit, SQLite, Plotly")
        st.write("**Contact:** farm@management.com")
        st.write("**Version:** 1.0.0")
        
        st.info("For support and feature requests, please contact the administrator.")

# ============================================
# FOOTER
# ============================================
st.sidebar.markdown("---")
st.sidebar.markdown("**Farm Management System** © 2024")
st.sidebar.markdown("*Version 1.0*")

# ============================================
# RUN INSTRUCTIONS
# ============================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚀 How to Run")
st.sidebar.markdown("1. Save this file as `farm_app.py`")
st.sidebar.markdown("2. Install requirements:")
st.sidebar.markdown("```bash\npip install streamlit pandas plotly sqlalchemy openpyxl\n```")
st.sidebar.markdown("3. Run the app:")
st.sidebar.markdown("```bash\nstreamlit run farm_app.py\n```")

# Initialize database on first run
if not st.session_state.db_initialized:
    db.init_sample_data()
    st.session_state.db_initialized = True
