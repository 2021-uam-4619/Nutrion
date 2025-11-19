import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import json

# Page configuration
st.set_page_config(
    page_title="Nutrion Logistics Manager",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .urgent-card {
        background-color: #fff7e6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #ff4b4b;
    }
    .success-card {
        background-color: #e6f7e6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #00cc66;
    }
</style>
""", unsafe_allow_html=True)

# Data configuration
DATA_FILE = 'logistics_data.json'
PRODUCT_LIST = [
    "Strophase G", "Strophase P", "Strozyme NSP", "SP200", "SP300",
    "SP300 Advance", "Monica", "Linco Magic", "Enra Magic", "InduceAcid Plus",
    "InduceAcid Buty", "Coxibac", "Strozyme XYL", "Super Ener Emusifier",
    "Antioxdant", "Toxin Binder Weilituo", "Toxin Clean", "GutPro 60 (Tributyrin)",
    "InduceAcid Liquid", "Syngrow"
]

PAKISTANI_CITIES = [
    "Karachi", "Lahore", "Faisalabad", "Rawalpindi", "Multan", "Gujranwala",
    "Peshawar", "Quetta", "Islamabad", "Sargodha", "Sialkot", "Bahawalpur",
    "Sukkur", "Jhang", "Shekhupura", "Mardan", "Gujrat", "Kasur",
    "Rahim Yar Khan", "Sahiwal", "Okara", "Wah Cantonment", "Dera Ghazi Khan",
    "Mirpur Khas", "Nawabshah", "Mingora", "Chiniot", "Kohat", "Bannu",
    "Khuzdar", "Abbottabad", "Mansehra", "Gilgit", "Muzaffarabad", "Skardu",
    "Turbat", "Gwadar", "Dera Ismail Khan", "Hafizabad", "Lodhran", "Ghotki",
    "Kandhkot", "Larkana", "Jacobabad", "Shikarpur", "Hyderabad", "Bhimber", "Mirpur"
]

STATUS_OPTIONS = ["Pending", "Under Process", "Dispatched", "In Transit", "Delivered", "Cancelled"]

class LogisticsManager:
    def __init__(self):
        self.data_file = DATA_FILE
        self.load_data()
    
    def load_data(self):
        """Load data from JSON file or initialize empty DataFrame"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                st.session_state.shipments = pd.DataFrame(data)
            except Exception as e:
                st.error(f"Error loading data: {e}")
                st.session_state.shipments = pd.DataFrame(columns=[
                    'id', 'departure_date', 'client_name', 'product_name', 'quantity',
                    'bilty_status', 'destination', 'received_date', 'status', 'receiver_number',
                    'created_at', 'updated_at'
                ])
        else:
            st.session_state.shipments = pd.DataFrame(columns=[
                'id', 'departure_date', 'client_name', 'product_name', 'quantity',
                'bilty_status', 'destination', 'received_date', 'status', 'receiver_number',
                'created_at', 'updated_at'
            ])
    
    def save_data(self):
        """Save data to JSON file"""
        try:
            # Convert DataFrame to dictionary
            if not st.session_state.shipments.empty:
                data = st.session_state.shipments.to_dict('records')
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, default=str)
            return True
        except Exception as e:
            st.error(f"Error saving data: {e}")
            return False
    
    def generate_id(self):
        """Generate unique ID for new shipment"""
        if st.session_state.shipments.empty:
            return 1
        return st.session_state.shipments['id'].max() + 1
    
    def add_shipment(self, shipment_data):
        """Add new shipment to the system"""
        try:
            new_id = self.generate_id()
            current_time = datetime.now().isoformat()
            
            # Auto-set status based on dates
            status = shipment_data['status']
            if shipment_data['received_date']:
                status = "Delivered"
            elif shipment_data['departure_date']:
                status = "Dispatched"
            
            new_shipment = {
                'id': new_id,
                'departure_date': shipment_data['departure_date'].isoformat() if shipment_data['departure_date'] else None,
                'client_name': shipment_data['client_name'],
                'product_name': shipment_data['product_name'],
                'quantity': shipment_data['quantity'],
                'bilty_status': shipment_data['bilty_status'],
                'destination': shipment_data['destination'],
                'received_date': shipment_data['received_date'].isoformat() if shipment_data['received_date'] else None,
                'status': status,
                'receiver_number': shipment_data['receiver_number'],
                'created_at': current_time,
                'updated_at': current_time
            }
            
            # Add to DataFrame
            new_df = pd.DataFrame([new_shipment])
            st.session_state.shipments = pd.concat([st.session_state.shipments, new_df], ignore_index=True)
            
            if self.save_data():
                st.success(f"✅ Shipment #{new_id} added successfully!")
                return True
            return False
            
        except Exception as e:
            st.error(f"Error adding shipment: {e}")
            return False
    
    def update_shipment(self, shipment_id, updates):
        """Update existing shipment"""
        try:
            mask = st.session_state.shipments['id'] == shipment_id
            if mask.any():
                for key, value in updates.items():
                    if key in ['departure_date', 'received_date'] and value:
                        value = value.isoformat()
                    st.session_state.shipments.loc[mask, key] = value
                
                st.session_state.shipments.loc[mask, 'updated_at'] = datetime.now().isoformat()
                
                if self.save_data():
                    st.success(f"✅ Shipment #{shipment_id} updated successfully!")
                    return True
            return False
        except Exception as e:
            st.error(f"Error updating shipment: {e}")
            return False
    
    def delete_shipment(self, shipment_id):
        """Delete shipment by ID"""
        try:
            initial_count = len(st.session_state.shipments)
            st.session_state.shipments = st.session_state.shipments[st.session_state.shipments['id'] != shipment_id]
            
            if len(st.session_state.shipments) < initial_count:
                if self.save_data():
                    st.success(f"✅ Shipment #{shipment_id} deleted successfully!")
                    return True
            else:
                st.error(f"❌ Shipment #{shipment_id} not found!")
            return False
        except Exception as e:
            st.error(f"Error deleting shipment: {e}")
            return False

def render_sidebar(logistics_mgr):
    """Render the sidebar with data entry form"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: #1f77b4; color: white; border-radius: 10px;'>
            <h2>🏭 NUTRION</h2>
            <p><strong>Logistics Management System</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("➕ New Shipment Entry")
        
        with st.form("new_shipment_form", clear_on_submit=True):
            # Client Information
            client_name = st.text_input(
                "Client Name *",
                placeholder="Enter client/organization name",
                help="Full name of the client or company"
            )
            
            # Product Information
            col1, col2 = st.columns(2)
            with col1:
                product_name = st.selectbox(
                    "Product Name *",
                    options=PRODUCT_LIST,
                    help="Select product from the list"
                )
            with col2:
                quantity = st.number_input(
                    "Quantity *",
                    min_value=1,
                    value=1,
                    help="Number of units"
                )
            
            # Location Information
            destination = st.selectbox(
                "Destination City *",
                options=PAKISTANI_CITIES,
                help="Select destination city"
            )
            
            # Contact Information
            receiver_number = st.text_input(
                "Receiver Contact Number *",
                placeholder="03XX-XXXXXXX",
                help="Receiver's phone number"
            )
            
            # Dates Section
            st.subheader("📅 Dates Information")
            col3, col4 = st.columns(2)
            with col3:
                departure_date = st.date_input(
                    "Departure Date (Multan)",
                    value=None,
                    max_value=date.today(),
                    help="Date when shipment left Multan"
                )
            with col4:
                received_date = st.date_input(
                    "Received Date",
                    value=None,
                    max_value=date.today(),
                    help="Date when shipment was delivered"
                )
            
            # Payment and Status
            col5, col6 = st.columns(2)
            with col5:
                bilty_status = st.radio(
                    "Bilty Status *",
                    options=["Paid", "Not Paid"],
                    horizontal=True
                )
            with col6:
                status = st.selectbox(
                    "Current Status *",
                    options=STATUS_OPTIONS,
                    index=0
                )
            
            st.markdown("---")
            submit_button = st.form_submit_button(
                "💾 Save Shipment Record",
                type="primary",
                use_container_width=True
            )
            
            if submit_button:
                if not client_name or not receiver_number:
                    st.error("❌ Please fill all required fields (Client Name and Receiver Number)")
                else:
                    shipment_data = {
                        'departure_date': departure_date,
                        'client_name': client_name,
                        'product_name': product_name,
                        'quantity': quantity,
                        'bilty_status': bilty_status,
                        'destination': destination,
                        'received_date': received_date,
                        'status': status,
                        'receiver_number': receiver_number
                    }
                    logistics_mgr.add_shipment(shipment_data)

def render_dashboard():
    """Render the main dashboard with metrics and data"""
    st.markdown('<div class="main-header">🚚 Nutrion Logistics Dashboard</div>', unsafe_allow_html=True)
    
    # Calculate metrics
    total_shipments = len(st.session_state.shipments)
    under_process = len(st.session_state.shipments[st.session_state.shipments['status'] == 'Under Process'])
    in_transit = len(st.session_state.shipments[st.session_state.shipments['status'] == 'In Transit'])
    delivered = len(st.session_state.shipments[st.session_state.shipments['status'] == 'Delivered'])
    pending = len(st.session_state.shipments[st.session_state.shipments['status'] == 'Pending'])
    
    # Display metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total</h3>
            <h2>{total_shipments}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="urgent-card">
            <h3>Under Process</h3>
            <h2>{under_process}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3>In Transit</h3>
            <h2>{in_transit}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="success-card">
            <h3>Delivered</h3>
            <h2>{delivered}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Pending</h3>
            <h2>{pending}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Under Process Orders - Priority Section
    if under_process > 0:
        st.subheader("⏳ Under Process Orders - Urgent Attention Required")
        under_process_df = st.session_state.shipments[
            st.session_state.shipments['status'] == 'Under Process'
        ]
        
        # Display as cards
        cols = st.columns(min(4, len(under_process_df)))
        for idx, (_, row) in enumerate(under_process_df.iterrows()):
            with cols[idx % len(cols)]:
                with st.container(border=True):
                    st.markdown(f"**ID:** `{int(row['id'])}`")
                    st.markdown(f"**Client:** {row['client_name']}")
                    st.markdown(f"**Product:** {row['product_name']}")
                    st.markdown(f"**Destination:** {row['destination']}")
                    st.markdown(f"**Quantity:** {row['quantity']}")
        
        st.markdown("---")
    
    # Main Data Display and Management
    st.subheader("📊 All Shipments")
    
    if st.session_state.shipments.empty:
        st.info("📋 No shipment records found. Add your first shipment using the sidebar form!")
        return
    
    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.multiselect(
            "Filter by Status",
            options=STATUS_OPTIONS,
            default=STATUS_OPTIONS
        )
    with col2:
        product_filter = st.selectbox(
            "Filter by Product",
            options=["All"] + PRODUCT_LIST
        )
    with col3:
        city_filter = st.selectbox(
            "Filter by City",
            options=["All"] + PAKISTANI_CITIES
        )
    
    # Apply filters
    filtered_df = st.session_state.shipments.copy()
    if status_filter:
        filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
    if product_filter != "All":
        filtered_df = filtered_df[filtered_df['product_name'] == product_filter]
    if city_filter != "All":
        filtered_df = filtered_df[filtered_df['destination'] == city_filter]
    
    # Display data
    st.dataframe(
        filtered_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            'id': 'ID',
            'departure_date': 'Departure Date',
            'client_name': 'Client Name',
            'product_name': 'Product',
            'quantity': 'Qty',
            'bilty_status': 'Bilty Status',
            'destination': 'Destination',
            'received_date': 'Received Date',
            'status': 'Status',
            'receiver_number': 'Receiver Number'
        }
    )
    
    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.expander("🔄 Update Status"):
            if not filtered_df.empty:
                shipment_id = st.selectbox(
                    "Select Shipment ID",
                    options=filtered_df['id'].tolist(),
                    format_func=lambda x: f"ID: {int(x)}"
                )
                new_status = st.selectbox("New Status", options=STATUS_OPTIONS)
                if st.button("Update Status", use_container_width=True):
                    logistics_mgr.update_shipment(shipment_id, {'status': new_status})
                    st.rerun()
    
    with col2:
        with st.expander("📅 Update Dates"):
            if not filtered_df.empty:
                shipment_id_date = st.selectbox(
                    "Select Shipment",
                    options=filtered_df['id'].tolist(),
                    key="date_update",
                    format_func=lambda x: f"ID: {int(x)}"
                )
                new_departure = st.date_input("New Departure Date", key="dep_date")
                new_received = st.date_input("New Received Date", key="rec_date")
                if st.button("Update Dates", use_container_width=True):
                    updates = {}
                    if new_departure:
                        updates['departure_date'] = new_departure
                    if new_received:
                        updates['received_date'] = new_received
                    if updates:
                        logistics_mgr.update_shipment(shipment_id_date, updates)
                        st.rerun()
    
    with col3:
        with st.expander("🗑️ Delete Shipment"):
            if not filtered_df.empty:
                shipment_id_del = st.selectbox(
                    "Select to Delete",
                    options=filtered_df['id'].tolist(),
                    key="delete_select",
                    format_func=lambda x: f"ID: {int(x)}"
                )
                if st.button("🚨 Delete Shipment", type="secondary", use_container_width=True):
                    logistics_mgr.delete_shipment(shipment_id_del)
                    st.rerun()

def main():
    """Main application function"""
    
    # Initialize logistics manager
    logistics_mgr = LogisticsManager()
    
    # Render sidebar
    render_sidebar(logistics_mgr)
    
    # Render main content
    render_dashboard()

if __name__ == "__main__":
    main()
