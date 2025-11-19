import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
import os
import json
import uuid
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Nutrion Logistics Pro",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for ultra-professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.8rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 800;
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #667eea;
        text-align: center;
    }
    .urgent-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #ff6b6b;
        text-align: center;
    }
    .success-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #00b894;
        text-align: center;
    }
    .shipment-item {
        background: white;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08);
        border-left: 4px solid;
        transition: transform 0.2s ease;
    }
    .shipment-item:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.12);
    }
    .status-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

# Data Configuration
DATA_FILE = 'nutrion_logistics_pro.json'
LOCATIONS_FILE = 'nutrion_locations.json'

# Product List
PRODUCT_LIST = [
    "Strophase G", "Strophase P", "Strozyme NSP", "SP200", "SP300",
    "SP300 Advance", "Monica", "Linco Magic", "Enra Magic", "InduceAcid Plus",
    "InduceAcid Buty", "Coxibac", "Strozyme XYL", "Super Ener Emusifier",
    "Antioxdant", "Toxin Binder Weilituo", "Toxin Clean", "GutPro 60 (Tributyrin)",
    "InduceAcid Liquid", "Syngrow"
]

# Default Pakistani Cities (for initial setup)
DEFAULT_CITIES = [
    "Karachi", "Lahore", "Faisalabad", "Rawalpindi", "Multan", "Gujranwala",
    "Peshawar", "Quetta", "Islamabad", "Sargodha", "Sialkot", "Bahawalpur"
]

# Status Options with colors
STATUS_CONFIG = {
    "Pending": {"color": "#ffc107", "icon": "⏳"},
    "Under Process": {"color": "#fd7e14", "icon": "🔄"},
    "Dispatched": {"color": "#17a2b8", "icon": "🚚"},
    "In Transit": {"color": "#20c997", "icon": "✈️"},
    "Delivered": {"color": "#28a745", "icon": "✅"},
    "Cancelled": {"color": "#dc3545", "icon": "❌"}
}

class AdvancedLogisticsManager:
    def __init__(self):
        self.data_file = DATA_FILE
        self.locations_file = LOCATIONS_FILE
        self.initialize_session_state()
        self.load_all_data()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        default_states = {
            'initialized': True,
            'edit_id': None,
            'quick_action': None,
            'last_added_id': None,
            'current_tab': "Dashboard"
        }
        
        for key, value in default_states.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    def load_all_data(self):
        """Load all data including locations"""
        self.load_locations()
        self.load_shipments()
    
    def load_locations(self):
        """Load locations from file or initialize with defaults"""
        try:
            if os.path.exists(self.locations_file):
                with open(self.locations_file, 'r', encoding='utf-8') as f:
                    st.session_state.locations = json.load(f)
            else:
                st.session_state.locations = DEFAULT_CITIES.copy()
                self.save_locations()
        except Exception as e:
            st.error(f"❌ Error loading locations: {str(e)}")
            st.session_state.locations = DEFAULT_CITIES.copy()
    
    def save_locations(self):
        """Save locations to file"""
        try:
            with open(self.locations_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.locations, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            st.error(f"❌ Error saving locations: {str(e)}")
            return False
    
    def add_location(self, new_location: str) -> bool:
        """Add new location to the list"""
        if new_location and new_location.strip() and new_location.strip() not in st.session_state.locations:
            st.session_state.locations.append(new_location.strip())
            st.session_state.locations.sort()
            return self.save_locations()
        return False
    
    def load_shipments(self):
        """Load shipments data"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                df = pd.DataFrame(data)
                
                # Data type conversions
                df['id'] = df['id'].astype(str)
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
                df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
                df['updated_at'] = pd.to_datetime(df['updated_at'], errors='coerce')
                
                st.session_state.shipments = df
            else:
                st.session_state.shipments = pd.DataFrame(columns=[
                    'id', 'departure_date', 'client_name', 'product_name', 'quantity',
                    'bilty_status', 'destination', 'received_date', 'status', 'receiver_number',
                    'created_at', 'updated_at', 'notes', 'priority'
                ])
                self.save_shipments()
                
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            st.session_state.shipments = pd.DataFrame(columns=[
                'id', 'departure_date', 'client_name', 'product_name', 'quantity',
                'bilty_status', 'destination', 'received_date', 'status', 'receiver_number',
                'created_at', 'updated_at', 'notes', 'priority'
            ])
    
    def save_shipments(self):
        """Save shipments data"""
        try:
            if not st.session_state.shipments.empty:
                data = st.session_state.shipments.to_dict('records')
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, default=str)
            return True
        except Exception as e:
            st.error(f"❌ Error saving data: {str(e)}")
            return False
    
    def generate_id(self):
        """Generate short unique ID"""
        return str(uuid.uuid4())[:6].upper()
    
    def add_shipment(self, shipment_data: Dict) -> bool:
        """Add new shipment with advanced automation"""
        try:
            new_id = self.generate_id()
            current_time = datetime.now()
            
            # Auto-determine status and priority
            status = self.auto_determine_status(
                shipment_data['departure_date'],
                shipment_data['received_date'],
                shipment_data.get('status', 'Pending')
            )
            
            priority = self.calculate_priority(
                status,
                shipment_data.get('quantity', 1),
                shipment_data.get('destination', '')
            )
            
            new_shipment = {
                'id': new_id,
                'departure_date': shipment_data['departure_date'].isoformat() if shipment_data['departure_date'] else None,
                'client_name': shipment_data['client_name'].strip(),
                'product_name': shipment_data['product_name'],
                'quantity': shipment_data['quantity'],
                'bilty_status': shipment_data['bilty_status'],
                'destination': shipment_data['destination'],
                'received_date': shipment_data['received_date'].isoformat() if shipment_data['received_date'] else None,
                'status': status,
                'receiver_number': shipment_data['receiver_number'].strip(),
                'notes': shipment_data.get('notes', ''),
                'priority': priority,
                'created_at': current_time.isoformat(),
                'updated_at': current_time.isoformat()
            }
            
            # Add to DataFrame
            new_df = pd.DataFrame([new_shipment])
            st.session_state.shipments = pd.concat([st.session_state.shipments, new_df], ignore_index=True)
            
            if self.save_shipments():
                st.session_state.last_added_id = new_id
                st.success(f"✅ Shipment **#{new_id}** added successfully! Status: **{status}**")
                return True
            return False
            
        except Exception as e:
            st.error(f"❌ Error adding shipment: {str(e)}")
            return False
    
    def auto_determine_status(self, departure_date, received_date, manual_status):
        """Intelligent status determination"""
        if received_date:
            return "Delivered"
        elif departure_date:
            if (datetime.now().date() - departure_date).days > 7:
                return "In Transit"
            else:
                return "Dispatched"
        else:
            return manual_status
    
    def calculate_priority(self, status, quantity, destination):
        """Calculate priority based on multiple factors"""
        priority_score = 0
        
        # Status-based priority
        status_priority = {
            "Under Process": 3,
            "Pending": 2,
            "Dispatched": 1,
            "In Transit": 1,
            "Delivered": 0,
            "Cancelled": 0
        }
        priority_score += status_priority.get(status, 1)
        
        # Quantity-based priority
        if quantity > 100:
            priority_score += 2
        elif quantity > 50:
            priority_score += 1
        
        # Remote location priority
        remote_cities = ["Quetta", "Gwadar", "Skardu", "Gilgit", "Turbat"]
        if destination in remote_cities:
            priority_score += 1
        
        return min(priority_score, 3)  # Cap at 3
    
    def quick_update_status(self, shipment_id: str, new_status: str) -> bool:
        """Quick status update with automation"""
        try:
            mask = st.session_state.shipments['id'] == shipment_id
            if mask.any():
                current_time = datetime.now().isoformat()
                
                st.session_state.shipments.loc[mask, 'status'] = new_status
                st.session_state.shipments.loc[mask, 'updated_at'] = current_time
                st.session_state.shipments.loc[mask, 'priority'] = self.calculate_priority(
                    new_status,
                    st.session_state.shipments.loc[mask, 'quantity'].iloc[0],
                    st.session_state.shipments.loc[mask, 'destination'].iloc[0]
                )
                
                if self.save_shipments():
                    return True
            return False
        except Exception as e:
            st.error(f"❌ Error updating status: {str(e)}")
            return False
    
    def get_shipment_stats(self):
        """Get comprehensive shipment statistics"""
        if st.session_state.shipments.empty:
            return {}
        
        df = st.session_state.shipments.copy()
        
        stats = {
            'total': len(df),
            'under_process': len(df[df['status'] == 'Under Process']),
            'in_transit': len(df[df['status'].isin(['Dispatched', 'In Transit'])]),
            'delivered': len(df[df['status'] == 'Delivered']),
            'pending': len(df[df['status'] == 'Pending']),
            'cancelled': len(df[df['status'] == 'Cancelled']),
            'paid': len(df[df['bilty_status'] == 'Paid']),
            'unpaid': len(df[df['bilty_status'] == 'Not Paid']),
            'total_quantity': df['quantity'].sum(),
            'avg_processing_time': self.calculate_avg_processing_time(df)
        }
        
        return stats
    
    def calculate_avg_processing_time(self, df):
        """Calculate average processing time for delivered shipments"""
        try:
            delivered = df[df['status'] == 'Delivered'].copy()
            if delivered.empty:
                return 0
            
            delivered['departure_date'] = pd.to_datetime(delivered['departure_date'])
            delivered['received_date'] = pd.to_datetime(delivered['received_date'])
            
            processing_times = (delivered['received_date'] - delivered['departure_date']).dt.days
            return processing_times.mean()
        except:
            return 0

def render_modern_sidebar(logistics_mgr: AdvancedLogisticsManager):
    """Render modern sidebar with quick actions"""
    with st.sidebar:
        # Header with logo
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    color: white; border-radius: 15px; margin-bottom: 2rem;'>
            <h2 style='margin: 0; font-size: 1.8rem;'>🏭 NUTRION</h2>
            <p style='margin: 0; opacity: 0.9;'>Logistics Pro</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Quick Stats
        stats = logistics_mgr.get_shipment_stats()
        st.metric("Total Shipments", stats.get('total', 0))
        
        # Navigation
        st.markdown("---")
        st.subheader("🧭 Navigation")
        
        nav_options = {
            "📊 Dashboard": "Dashboard",
            "🚀 Quick Add": "Quick Add", 
            "📦 Manage Shipments": "Manage",
            "📍 Locations": "Locations",
            "📈 Analytics": "Analytics",
            "⚙️ Settings": "Settings"
        }
        
        for label, key in nav_options.items():
            if st.button(label, use_container_width=True, key=f"nav_{key}"):
                st.session_state.current_tab = key
        
        st.markdown(f"**Current:** {st.session_state.current_tab}")
        st.markdown("---")
        
        # Quick Actions
        if st.session_state.current_tab == "Dashboard":
            render_quick_actions(logistics_mgr)

def render_quick_actions(logistics_mgr: AdvancedLogisticsManager):
    """Render quick action buttons in sidebar"""
    st.subheader("⚡ Quick Actions")
    
    if st.button("🔄 Refresh All Data", use_container_width=True):
        logistics_mgr.load_all_data()
        st.success("Data refreshed!")
        st.rerun()
    
    if st.button("📥 Export Report", use_container_width=True):
        export_data(logistics_mgr)
    
    if st.button("🧹 Clear Filters", use_container_width=True):
        st.session_state.quick_action = "clear_filters"
        st.rerun()

def render_dashboard(logistics_mgr: AdvancedLogisticsManager):
    """Render modern dashboard with analytics"""
    st.markdown('<div class="main-header">🚀 Nutrion Logistics Pro Dashboard</div>', unsafe_allow_html=True)
    
    stats = logistics_mgr.get_shipment_stats()
    
    # Top Metrics Row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>📦 Total</h3>
            <h2 style='color: #667eea;'>{stats['total']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="urgent-card">
            <h3>🔄 Under Process</h3>
            <h2 style='color: #ff6b6b;'>{stats['under_process']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>✈️ In Transit</h3>
            <h2 style='color: #17a2b8;'>{stats['in_transit']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="success-card">
            <h3>✅ Delivered</h3>
            <h2 style='color: #28a745;'>{stats['delivered']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💰 Paid</h3>
            <h2 style='color: #20c997;'>{stats['paid']}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts and Analytics
    col1, col2 = st.columns(2)
    
    with col1:
        render_status_chart(logistics_mgr)
    
    with col2:
        render_priority_shipments(logistics_mgr)
    
    # Recent Activity
    st.subheader("📋 Recent Shipments")
    render_recent_shipments(logistics_mgr)

def render_status_chart(logistics_mgr: AdvancedLogisticsManager):
    """Render status distribution chart"""
    if logistics_mgr.get_shipment_stats()['total'] > 0:
        df = st.session_state.shipments.copy()
        status_counts = df['status'].value_counts()
        
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="📊 Shipment Status Distribution",
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for charts")

def render_priority_shipments(logistics_mgr: AdvancedLogisticsManager):
    """Render high priority shipments"""
    if not st.session_state.shipments.empty:
        high_priority = st.session_state.shipments[
            st.session_state.shipments['priority'] == 3
        ].head(5)
        
        if not high_priority.empty:
            st.subheader("🚨 High Priority Attention Needed")
            for _, row in high_priority.iterrows():
                status_config = STATUS_CONFIG.get(row['status'], {"color": "#666", "icon": "📦"})
                
                st.markdown(f"""
                <div class="shipment-item" style="border-left-color: {status_config['color']};">
                    <div style="display: flex; justify-content: between; align-items: center;">
                        <strong>#{row['id']} - {row['client_name']}</strong>
                        <span class="status-badge" style="background-color: {status_config['color']}20; color: {status_config['color']};">
                            {status_config['icon']} {row['status']}
                        </span>
                    </div>
                    <div style="font-size: 0.9rem; color: #666;">
                        {row['product_name']} • {row['quantity']} units • {row['destination']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("🎉 No high priority shipments!")

def render_recent_shipments(logistics_mgr: AdvancedLogisticsManager):
    """Render recent shipments table"""
    if not st.session_state.shipments.empty:
        recent_df = st.session_state.shipments.sort_values('created_at', ascending=False).head(10)
        
        # Create a styled dataframe
        display_df = recent_df[['id', 'client_name', 'product_name', 'quantity', 'destination', 'status']].copy()
        
        # Add status icons
        display_df['status_display'] = display_df['status'].apply(
            lambda x: f"{STATUS_CONFIG.get(x, {}).get('icon', '📦')} {x}"
        )
        
        st.dataframe(
            display_df[['id', 'client_name', 'product_name', 'quantity', 'destination', 'status_display']],
            use_container_width=True,
            hide_index=True,
            column_config={
                'id': 'ID',
                'client_name': 'Client',
                'product_name': 'Product', 
                'quantity': 'Qty',
                'destination': 'Destination',
                'status_display': 'Status'
            }
        )
    else:
        st.info("No shipments yet. Add your first shipment!")

def render_quick_add(logistics_mgr: AdvancedLogisticsManager):
    """Render quick add form"""
    st.markdown('<div class="main-header">🚀 Quick Add Shipment</div>', unsafe_allow_html=True)
    
    with st.form("quick_shipment_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            client_name = st.text_input("🏢 Client Name *", placeholder="Enter client name")
            product_name = st.selectbox("📦 Product *", options=PRODUCT_LIST)
            quantity = st.number_input("🔢 Quantity *", min_value=1, value=1)
        
        with col2:
            # Location with add new option
            location_col1, location_col2 = st.columns([3, 1])
            with location_col1:
                selected_location = st.selectbox("📍 Destination *", options=st.session_state.locations)
            with location_col2:
                if st.button("➕ New", use_container_width=True):
                    st.session_state.show_location_adder = True
            
            if st.session_state.get('show_location_adder', False):
                new_location = st.text_input("Add New Location", placeholder="Enter new city/location")
                if new_location:
                    if logistics_mgr.add_location(new_location):
                        st.success(f"✅ Added {new_location}")
                        st.session_state.show_location_adder = False
                        st.rerun()
            
            receiver_number = st.text_input("📞 Contact Number *", placeholder="03XX-XXXXXXX")
            bilty_status = st.radio("💰 Payment Status *", options=["Paid", "Not Paid"], horizontal=True)
        
        # Quick date options
        st.subheader("📅 Quick Date Options")
        date_option = st.radio("Departure Date:", 
                             ["Today", "Tomorrow", "Custom", "Not Set"], 
                             horizontal=True)
        
        departure_date = None
        if date_option == "Today":
            departure_date = datetime.now().date()
        elif date_option == "Tomorrow":
            departure_date = datetime.now().date() + timedelta(days=1)
        elif date_option == "Custom":
            departure_date = st.date_input("Select Date")
        
        submit = st.form_submit_button("🚀 Create Shipment", type="primary", use_container_width=True)
        
        if submit:
            if not all([client_name, receiver_number]):
                st.error("❌ Please fill all required fields")
            else:
                shipment_data = {
                    'departure_date': departure_date,
                    'client_name': client_name,
                    'product_name': product_name,
                    'quantity': quantity,
                    'bilty_status': bilty_status,
                    'destination': selected_location,
                    'received_date': None,
                    'status': 'Pending',
                    'receiver_number': receiver_number,
                    'notes': ''
                }
                if logistics_mgr.add_shipment(shipment_data):
                    st.balloons()

def render_locations_management(logistics_mgr: AdvancedLogisticsManager):
    """Render locations management interface"""
    st.markdown('<div class="main-header">📍 Locations Management</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🏙️ Available Locations")
        if st.session_state.locations:
            # Display locations in a grid
            cols = st.columns(3)
            for idx, location in enumerate(sorted(st.session_state.locations)):
                with cols[idx % 3]:
                    location_col1, location_col2 = st.columns([3, 1])
                    with location_col1:
                        st.write(f"📍 {location}")
                    with location_col2:
                        if st.button("🗑️", key=f"del_{location}", help="Delete location"):
                            if location in st.session_state.locations:
                                st.session_state.locations.remove(location)
                                logistics_mgr.save_locations()
                                st.success(f"Removed {location}")
                                st.rerun()
        else:
            st.info("No locations added yet")
    
    with col2:
        st.subheader("➕ Add New Location")
        with st.form("add_location_form"):
            new_location = st.text_input("Location Name", placeholder="Enter city/location name")
            if st.form_submit_button("Add Location", use_container_width=True):
                if new_location and new_location.strip():
                    if logistics_mgr.add_location(new_location.strip()):
                        st.success(f"✅ Added {new_location}")
                        st.rerun()
                else:
                    st.error("Please enter a valid location name")

def render_analytics(logistics_mgr: AdvancedLogisticsManager):
    """Render advanced analytics"""
    st.markdown('<div class="main-header">📈 Advanced Analytics</div>', unsafe_allow_html=True)
    
    if logistics_mgr.get_shipment_stats()['total'] == 0:
        st.info("No data available for analytics")
        return
    
    df = st.session_state.shipments.copy()
    
    # Top row metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_value = df['quantity'].sum() * 1000  # Example calculation
        st.metric("Estimated Total Value", f"₹{total_value:,.0f}")
    
    with col2:
        avg_processing = logistics_mgr.calculate_avg_processing_time(df)
        st.metric("Avg Processing Days", f"{avg_processing:.1f}")
    
    with col3:
        delivery_rate = (len(df[df['status'] == 'Delivered']) / len(df)) * 100
        st.metric("Delivery Success Rate", f"{delivery_rate:.1f}%")
    
    with col4:
        paid_percentage = (len(df[df['bilty_status'] == 'Paid']) / len(df)) * 100
        st.metric("Payment Collection", f"{paid_percentage:.1f}%")
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        # Monthly trend
        df['month'] = pd.to_datetime(df['created_at']).dt.to_period('M')
        monthly_trend = df.groupby('month').size()
        
        if not monthly_trend.empty:
            fig = px.line(
                x=monthly_trend.index.astype(str),
                y=monthly_trend.values,
                title="📈 Monthly Shipment Trend",
                labels={'x': 'Month', 'y': 'Number of Shipments'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top products
        product_counts = df['product_name'].value_counts().head(8)
        fig = px.bar(
            x=product_counts.values,
            y=product_counts.index,
            orientation='h',
            title="📦 Top Products by Volume",
            labels={'x': 'Number of Shipments', 'y': 'Product'}
        )
        st.plotly_chart(fig, use_container_width=True)

def export_data(logistics_mgr: AdvancedLogisticsManager):
    """Export data functionality"""
    if not st.session_state.shipments.empty:
        csv_data = st.session_state.shipments.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Data (CSV)",
            data=csv_data,
            file_name=f"nutrion_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )

def main():
    """Main application function"""
    
    # Initialize logistics manager
    logistics_mgr = AdvancedLogisticsManager()
    
    # Render sidebar
    render_modern_sidebar(logistics_mgr)
    
    # Render main content based on current tab
    current_tab = st.session_state.get('current_tab', 'Dashboard')
    
    if current_tab == "Dashboard":
        render_dashboard(logistics_mgr)
    elif current_tab == "Quick Add":
        render_quick_add(logistics_mgr)
    elif current_tab == "Locations":
        render_locations_management(logistics_mgr)
    elif current_tab == "Analytics":
        render_analytics(logistics_mgr)
    elif current_tab == "Manage":
        # You can implement the full management interface here
        st.info("Management interface - Implement similar to previous versions")
    elif current_tab == "Settings":
        st.info("Settings interface - Implement configuration options here")

if __name__ == "__main__":
    main()
