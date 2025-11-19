import streamlit as st
import pandas as pd
from datetime import datetime, date
import os
import json
import uuid
from typing import Dict, List, Optional

# Page configuration
st.set_page_config(
    page_title="Nutrion Logistics Manager",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: bold;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .urgent-card {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .success-card {
        background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .warning-card {
        background: linear-gradient(135deg, #fdcb6e 0%, #e17055 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .info-card {
        background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .shipment-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .status-pending { background-color: #fff3cd; border-left-color: #ffc107; }
    .status-process { background-color: #ffeaa7; border-left-color: #fdcb6e; }
    .status-transit { background-color: #d1ecf1; border-left-color: #17a2b8; }
    .status-delivered { background-color: #d4edda; border-left-color: #28a745; }
    .status-cancelled { background-color: #f8d7da; border-left-color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# Data Configuration
DATA_FILE = 'nutrion_logistics_data.json'
BACKUP_FILE = 'nutrion_logistics_backup.json'

# Product List
PRODUCT_LIST = [
    "Strophase G", "Strophase P", "Strozyme NSP", "SP200", "SP300",
    "SP300 Advance", "Monica", "Linco Magic", "Enra Magic", "InduceAcid Plus",
    "InduceAcid Buty", "Coxibac", "Strozyme XYL", "Super Ener Emusifier",
    "Antioxdant", "Toxin Binder Weilituo", "Toxin Clean", "GutPro 60 (Tributyrin)",
    "InduceAcid Liquid", "Syngrow"
]

# Pakistani Cities
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

# Status Options with automatic progression
STATUS_OPTIONS = ["Pending", "Under Process", "Dispatched", "In Transit", "Delivered", "Cancelled"]

class LogisticsManager:
    def __init__(self):
        self.data_file = DATA_FILE
        self.backup_file = BACKUP_FILE
        self.initialize_session_state()
        self.load_data()
    
    def initialize_session_state(self):
        """Initialize session state variables"""
        if 'initialized' not in st.session_state:
            st.session_state.initialized = True
            st.session_state.edit_id = None
            st.session_state.filter_status = []
            st.session_state.filter_product = "All"
            st.session_state.filter_city = "All"
            st.session_state.search_term = ""
    
    def load_data(self):
        """Load data from JSON file or initialize empty DataFrame"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert to DataFrame
                df = pd.DataFrame(data)
                
                # Ensure proper data types
                df['id'] = df['id'].astype(str)
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce').fillna(0).astype(int)
                df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
                df['updated_at'] = pd.to_datetime(df['updated_at'], errors='coerce')
                
                st.session_state.shipments = df
            else:
                st.session_state.shipments = pd.DataFrame(columns=[
                    'id', 'departure_date', 'client_name', 'product_name', 'quantity',
                    'bilty_status', 'destination', 'received_date', 'status', 'receiver_number',
                    'created_at', 'updated_at', 'notes'
                ])
                self.save_data()
                
        except Exception as e:
            st.error(f"❌ Error loading data: {str(e)}")
            st.session_state.shipments = pd.DataFrame(columns=[
                'id', 'departure_date', 'client_name', 'product_name', 'quantity',
                'bilty_status', 'destination', 'received_date', 'status', 'receiver_number',
                'created_at', 'updated_at', 'notes'
            ])
    
    def save_data(self):
        """Save data to JSON file with backup"""
        try:
            if not st.session_state.shipments.empty:
                # Create backup
                if os.path.exists(self.data_file):
                    import shutil
                    shutil.copy2(self.data_file, self.backup_file)
                
                # Convert DataFrame to dictionary
                data = st.session_state.shipments.to_dict('records')
                
                # Save to file
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=4, default=str)
                    
            return True
        except Exception as e:
            st.error(f"❌ Error saving data: {str(e)}")
            return False
    
    def generate_id(self):
        """Generate unique ID for new shipment"""
        return str(uuid.uuid4())[:8].upper()
    
    def add_shipment(self, shipment_data: Dict) -> bool:
        """Add new shipment to the system"""
        try:
            new_id = self.generate_id()
            current_time = datetime.now()
            
            # Auto-determine status based on dates
            status = self.auto_determine_status(
                shipment_data['departure_date'],
                shipment_data['received_date'],
                shipment_data.get('status', 'Pending')
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
                'created_at': current_time.isoformat(),
                'updated_at': current_time.isoformat()
            }
            
            # Add to DataFrame
            new_df = pd.DataFrame([new_shipment])
            st.session_state.shipments = pd.concat([st.session_state.shipments, new_df], ignore_index=True)
            
            if self.save_data():
                st.success(f"✅ Shipment **#{new_id}** added successfully! Status: **{status}**")
                return True
            return False
            
        except Exception as e:
            st.error(f"❌ Error adding shipment: {str(e)}")
            return False
    
    def auto_determine_status(self, departure_date, received_date, manual_status):
        """Automatically determine status based on dates"""
        if received_date:
            return "Delivered"
        elif departure_date:
            return "Dispatched"
        else:
            return manual_status
    
    def update_shipment(self, shipment_id: str, updates: Dict) -> bool:
        """Update existing shipment"""
        try:
            mask = st.session_state.shipments['id'] == shipment_id
            if mask.any():
                # Handle date conversions
                for key, value in updates.items():
                    if key in ['departure_date', 'received_date'] and value:
                        updates[key] = value.isoformat()
                
                # Auto-update status if dates are changed
                if 'departure_date' in updates or 'received_date' in updates:
                    current_data = st.session_state.shipments.loc[mask].iloc[0]
                    dep_date = updates.get('departure_date') or current_data['departure_date']
                    rec_date = updates.get('received_date') or current_data['received_date']
                    
                    if rec_date:
                        updates['status'] = "Delivered"
                    elif dep_date:
                        updates['status'] = "Dispatched"
                
                updates['updated_at'] = datetime.now().isoformat()
                
                # Apply updates
                for key, value in updates.items():
                    st.session_state.shipments.loc[mask, key] = value
                
                if self.save_data():
                    st.success(f"✅ Shipment **#{shipment_id}** updated successfully!")
                    return True
            else:
                st.error(f"❌ Shipment **#{shipment_id}** not found!")
            return False
        except Exception as e:
            st.error(f"❌ Error updating shipment: {str(e)}")
            return False
    
    def delete_shipment(self, shipment_id: str) -> bool:
        """Delete shipment by ID"""
        try:
            initial_count = len(st.session_state.shipments)
            st.session_state.shipments = st.session_state.shipments[st.session_state.shipments['id'] != shipment_id]
            
            if len(st.session_state.shipments) < initial_count:
                if self.save_data():
                    st.success(f"✅ Shipment **#{shipment_id}** deleted successfully!")
                    return True
            else:
                st.error(f"❌ Shipment **#{shipment_id}** not found!")
            return False
        except Exception as e:
            st.error(f"❌ Error deleting shipment: {str(e)}")
            return False
    
    def get_shipment_by_id(self, shipment_id: str) -> Optional[Dict]:
        """Get shipment details by ID"""
        try:
            shipment = st.session_state.shipments[st.session_state.shipments['id'] == shipment_id]
            if not shipment.empty:
                return shipment.iloc[0].to_dict()
            return None
        except:
            return None
    
    def export_to_excel(self) -> bytes:
        """Export data to Excel format"""
        try:
            output = st.session_state.shipments.copy()
            # Convert date strings to readable format
            output['departure_date'] = pd.to_datetime(output['departure_date']).dt.strftime('%Y-%m-%d')
            output['received_date'] = pd.to_datetime(output['received_date']).dt.strftime('%Y-%m-%d')
            output['created_at'] = pd.to_datetime(output['created_at']).dt.strftime('%Y-%m-%d %H:%M')
            output['updated_at'] = pd.to_datetime(output['updated_at']).dt.strftime('%Y-%m-%d %H:%M')
            
            return output.to_csv(index=False).encode('utf-8')
        except Exception as e:
            st.error(f"❌ Error exporting data: {str(e)}")
            return None

def render_sidebar(logistics_mgr: LogisticsManager):
    """Render the sidebar with data entry form"""
    with st.sidebar:
        # Header
        st.markdown("""
        <div style='text-align: center; padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 15px; margin-bottom: 2rem;'>
            <h2 style='margin: 0;'>🏭 NUTRION</h2>
            <p style='margin: 0; font-size: 0.9rem;'><strong>Logistics Management System</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        st.subheader("📋 Navigation")
        nav_option = st.radio(
            "Go to:",
            ["Add New Shipment", "View/Edit Shipments", "Reports & Analytics"],
            label_visibility="collapsed"
        )
        
        if nav_option == "Add New Shipment":
            render_shipment_form(logistics_mgr)
        elif nav_option == "View/Edit Shipments":
            render_edit_section(logistics_mgr)
        else:
            render_reports_section(logistics_mgr)

def render_shipment_form(logistics_mgr: LogisticsManager):
    """Render the new shipment form"""
    st.subheader("➕ New Shipment Entry")
    
    with st.form("new_shipment_form", clear_on_submit=True):
        # Client Information
        client_name = st.text_input(
            "🏢 Client Name *",
            placeholder="Enter client/organization name",
            help="Full name of the client or company"
        )
        
        # Product Information
        col1, col2 = st.columns(2)
        with col1:
            product_name = st.selectbox(
                "📦 Product Name *",
                options=PRODUCT_LIST,
                help="Select product from the list"
            )
        with col2:
            quantity = st.number_input(
                "🔢 Quantity *",
                min_value=1,
                value=1,
                step=1,
                help="Number of units"
            )
        
        # Location Information
        destination = st.selectbox(
            "📍 Destination City *",
            options=PAKISTANI_CITIES,
            help="Select destination city"
        )
        
        # Contact Information
        receiver_number = st.text_input(
            "📞 Receiver Contact Number *",
            placeholder="03XX-XXXXXXX",
            help="Receiver's phone number"
        )
        
        # Dates Section
        st.subheader("📅 Dates Information")
        col3, col4 = st.columns(2)
        with col3:
            departure_date = st.date_input(
                "🚚 Departure Date (Multan)",
                value=None,
                max_value=date.today(),
                help="Date when shipment left Multan"
            )
        with col4:
            received_date = st.date_input(
                "📬 Received Date",
                value=None,
                max_value=date.today(),
                help="Date when shipment was delivered"
            )
        
        # Payment and Status
        col5, col6 = st.columns(2)
        with col5:
            bilty_status = st.radio(
                "💰 Bilty Status *",
                options=["Paid", "Not Paid"],
                horizontal=True
            )
        with col6:
            status = st.selectbox(
                "📊 Current Status *",
                options=STATUS_OPTIONS,
                index=0,
                disabled=True,  # Auto-determined
                help="Status is automatically determined based on dates"
            )
        
        # Additional Notes
        notes = st.text_area(
            "📝 Additional Notes",
            placeholder="Any additional information about this shipment...",
            height=80
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
                    'receiver_number': receiver_number,
                    'notes': notes
                }
                if logistics_mgr.add_shipment(shipment_data):
                    st.rerun()

def render_edit_section(logistics_mgr: LogisticsManager):
    """Render the edit shipments section"""
    st.subheader("✏️ Edit Existing Shipments")
    
    if st.session_state.shipments.empty:
        st.info("No shipments available for editing.")
        return
    
    # Quick search
    search_term = st.text_input("🔍 Search by Client Name or ID", placeholder="Enter client name or shipment ID...")
    
    # Filter shipments
    filtered_shipments = st.session_state.shipments.copy()
    if search_term:
        mask = (filtered_shipments['client_name'].str.contains(search_term, case=False, na=False)) | \
               (filtered_shipments['id'].str.contains(search_term, case=False, na=False))
        filtered_shipments = filtered_shipments[mask]
    
    if filtered_shipments.empty:
        st.warning("No shipments match your search criteria.")
        return
    
    # Select shipment to edit
    shipment_options = filtered_shipments.apply(
        lambda x: f"ID: {x['id']} - {x['client_name']} ({x['status']})", axis=1
    ).tolist()
    
    selected_shipment = st.selectbox("Select Shipment to Edit", options=shipment_options)
    
    if selected_shipment:
        shipment_id = selected_shipment.split("ID: ")[1].split(" -")[0]
        shipment_data = logistics_mgr.get_shipment_by_id(shipment_id)
        
        if shipment_data:
            with st.form("edit_shipment_form"):
                st.subheader(f"Editing Shipment #{shipment_id}")
                
                col1, col2 = st.columns(2)
                with col1:
                    new_client = st.text_input("Client Name", value=shipment_data['client_name'])
                    new_product = st.selectbox("Product", options=PRODUCT_LIST, 
                                            index=PRODUCT_LIST.index(shipment_data['product_name']) if shipment_data['product_name'] in PRODUCT_LIST else 0)
                    new_quantity = st.number_input("Quantity", value=int(shipment_data['quantity']), min_value=1)
                    new_destination = st.selectbox("Destination", options=PAKISTANI_CITIES,
                                                index=PAKISTANI_CITIES.index(shipment_data['destination']) if shipment_data['destination'] in PAKISTANI_CITIES else 0)
                
                with col2:
                    new_receiver = st.text_input("Receiver Number", value=shipment_data['receiver_number'])
                    new_bilty = st.radio("Bilty Status", options=["Paid", "Not Paid"],
                                      index=0 if shipment_data['bilty_status'] == "Paid" else 1,
                                      horizontal=True)
                    new_status = st.selectbox("Status", options=STATUS_OPTIONS,
                                           index=STATUS_OPTIONS.index(shipment_data['status']))
                    new_notes = st.text_area("Notes", value=shipment_data.get('notes', ''))
                
                # Date inputs
                col3, col4 = st.columns(2)
                with col3:
                    current_dep = pd.to_datetime(shipment_data['departure_date']) if shipment_data['departure_date'] else None
                    new_departure = st.date_input("Departure Date", value=current_dep)
                with col4:
                    current_rec = pd.to_datetime(shipment_data['received_date']) if shipment_data['received_date'] else None
                    new_received = st.date_input("Received Date", value=current_rec)
                
                update_button = st.form_submit_button("🔄 Update Shipment", use_container_width=True)
                
                if update_button:
                    updates = {
                        'client_name': new_client,
                        'product_name': new_product,
                        'quantity': new_quantity,
                        'destination': new_destination,
                        'receiver_number': new_receiver,
                        'bilty_status': new_bilty,
                        'status': new_status,
                        'notes': new_notes,
                        'departure_date': new_departure,
                        'received_date': new_received
                    }
                    if logistics_mgr.update_shipment(shipment_id, updates):
                        st.rerun()

def render_reports_section(logistics_mgr: LogisticsManager):
    """Render the reports and analytics section"""
    st.subheader("📈 Reports & Analytics")
    
    if st.session_state.shipments.empty:
        st.info("No data available for reports.")
        return
    
    # Quick Statistics
    col1, col2, col3, col4 = st.columns(4)
    
    total_shipments = len(st.session_state.shipments)
    under_process = len(st.session_state.shipments[st.session_state.shipments['status'] == 'Under Process'])
    delivered = len(st.session_state.shipments[st.session_state.shipments['status'] == 'Delivered'])
    revenue = len(st.session_state.shipments[st.session_state.shipments['bilty_status'] == 'Paid'])
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>Total Shipments</h3>
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
        <div class="success-card">
            <h3>Delivered</h3>
            <h2>{delivered}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="info-card">
            <h3>Paid Shipments</h3>
            <h2>{revenue}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # Export Data
    st.subheader("📊 Data Export")
    col5, col6 = st.columns(2)
    
    with col5:
        if st.button("📥 Export to Excel", use_container_width=True):
            csv_data = logistics_mgr.export_to_excel()
            if csv_data:
                st.download_button(
                    label="⬇️ Download CSV File",
                    data=csv_data,
                    file_name=f"nutrion_shipments_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    with col6:
        if st.button("🔄 Refresh Data", use_container_width=True):
            logistics_mgr.load_data()
            st.success("Data refreshed successfully!")
            st.rerun()

def render_dashboard(logistics_mgr: LogisticsManager):
    """Render the main dashboard"""
    st.markdown('<div class="main-header">🚚 Nutrion Logistics Dashboard</div>', unsafe_allow_html=True)
    
    # Key Metrics
    if not st.session_state.shipments.empty:
        total_shipments = len(st.session_state.shipments)
        under_process = len(st.session_state.shipments[st.session_state.shipments['status'] == 'Under Process'])
        in_transit = len(st.session_state.shipments[st.session_state.shipments['status'].isin(['Dispatched', 'In Transit'])])
        delivered = len(st.session_state.shipments[st.session_state.shipments['status'] == 'Delivered'])
        pending = len(st.session_state.shipments[st.session_state.shipments['status'] == 'Pending'])
        
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
            <div class="warning-card">
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
            <div class="info-card">
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
            
            # Display as cards in columns
            cols = st.columns(min(3, len(under_process_df)))
            for idx, (_, row) in enumerate(under_process_df.iterrows()):
                with cols[idx % len(cols)]:
                    status_class = f"status-{row['status'].lower().replace(' ', '-')}"
                    st.markdown(f"""
                    <div class="shipment-card {status_class}">
                        <h4>📦 Shipment #{row['id']}</h4>
                        <p><strong>👤 Client:</strong> {row['client_name']}</p>
                        <p><strong>📦 Product:</strong> {row['product_name']}</p>
                        <p><strong>📍 Destination:</strong> {row['destination']}</p>
                        <p><strong>🔢 Quantity:</strong> {row['quantity']}</p>
                        <p><strong>💰 Payment:</strong> {row['bilty_status']}</p>
                        <p><strong>📞 Contact:</strong> {row['receiver_number']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
    
    # Main Data Table
    st.subheader("📋 All Shipments")
    
    if st.session_state.shipments.empty:
        st.info("📋 No shipment records found. Add your first shipment using the sidebar form!")
        return
    
    # Filters
    col1, col2, col3, col4 = st.columns(4)
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
    with col4:
        payment_filter = st.selectbox(
            "Filter by Payment",
            options=["All", "Paid", "Not Paid"]
        )
    
    # Apply filters
    filtered_df = st.session_state.shipments.copy()
    if status_filter:
        filtered_df = filtered_df[filtered_df['status'].isin(status_filter)]
    if product_filter != "All":
        filtered_df = filtered_df[filtered_df['product_name'] == product_filter]
    if city_filter != "All":
        filtered_df = filtered_df[filtered_df['destination'] == city_filter]
    if payment_filter != "All":
        filtered_df = filtered_df[filtered_df['bilty_status'] == payment_filter]
    
    # Display data with better formatting
    if not filtered_df.empty:
        display_df = filtered_df[[
            'id', 'client_name', 'product_name', 'quantity', 'destination',
            'status', 'bilty_status', 'departure_date', 'received_date', 'receiver_number'
        ]].copy()
        
        # Format dates
        display_df['departure_date'] = pd.to_datetime(display_df['departure_date']).dt.strftime('%Y-%m-%d')
        display_df['received_date'] = pd.to_datetime(display_df['received_date']).dt.strftime('%Y-%m-%d')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'id': st.column_config.TextColumn('ID'),
                'client_name': st.column_config.TextColumn('Client'),
                'product_name': st.column_config.TextColumn('Product'),
                'quantity': st.column_config.NumberColumn('Qty'),
                'destination': st.column_config.TextColumn('Destination'),
                'status': st.column_config.TextColumn('Status'),
                'bilty_status': st.column_config.TextColumn('Payment'),
                'departure_date': st.column_config.TextColumn('Departure'),
                'received_date': st.column_config.TextColumn('Received'),
                'receiver_number': st.column_config.TextColumn('Contact')
            }
        )
        
        # Show record count
        st.caption(f"📊 Showing {len(filtered_df)} of {len(st.session_state.shipments)} shipments")
    else:
        st.warning("No shipments match the current filters.")

def main():
    """Main application function"""
    
    # Initialize logistics manager
    logistics_mgr = LogisticsManager()
    
    # Render sidebar
    render_sidebar(logistics_mgr)
    
    # Render main content
    render_dashboard(logistics_mgr)

if __name__ == "__main__":
    main()
