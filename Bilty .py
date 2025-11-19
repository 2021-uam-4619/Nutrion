import streamlit as st
import pandas as pd
from datetime import datetime, date
import os 
import warnings
warnings.filterwarnings('ignore')

# --- Configuration and Initialization ---

# Define the file path for persistent data storage
DATA_FILE = 'shipments_data.csv'

# Set page title and layout
st.set_page_config(
    page_title="Nutrion Logistics Tracker | Professional Edition",
    layout="wide",
    initial_sidebar_state="expanded"
)

# List of all products (as provided by the user)
PRODUCT_LIST = [
    "Strophase G", "Strophase P", "Strozyme NSP", "SP200", "SP300",
    "SP300 Advance", "Monica", "Linco Magic", "Enra Magic", "InduceAcid Plus",
    "InduceAcid Buty", "Coxibac", "Strozyme XYL", "Super Ener Emusifier",
    "Antioxdant", "Toxin Binder Weilituo", "Toxin Clean", "GutPro 60 (Tributyrin)",
    "InduceAcid Liquid", "Syngrow"
]

# Comprehensive list of Pakistani cities for the destination dropdown
PAKISTAN_CITIES = [
    "Karachi", "Lahore", "Faisalabad", "Rawalpindi", "Multan", "Gujranwala",
    "Peshawar", "Quetta", "Islamabad", "Sargodha", "Sialkot", "Bahawalpur",
    "Sukkur", "Jhang", "Shekhupura", "Mardan", "Gujrat", "Kasur",
    "Rahim Yar Khan", "Sahiwal", "Okara", "Wah Cantonment", "Dera Ghazi Khan",
    "Mirpur Khas", "Nawabshah", "Mingora", "Chiniot", "Kohat", "Bannu",
    "Khuzdar", "Abbottabad", "Mansehra", "Gilgit", "Muzaffarabad", "Skardu",
    "Turbat", "Gwadar", "Dera Ismail Khan", "Hafizabad", "Lodhran", "Ghotki",
    "Kandhkot", "Larkana", "Jacobabad", "Shikarpur", "Khyber Agency (Landi Kotal)", 
    "Malakand Agency", "Tank", "Karak", "Hyderabad", "Bhimber", "Mirpur"
]

# List of available status options, reflecting the new, detailed flow
STATUS_OPTIONS = [
    "New Order", 
    "Under Process", 
    "Departed (Multan)", 
    "Arrived at Destination Hub", 
    "Out for Delivery", 
    "Delivered", 
    "Cancelled"
]

# Define the expected columns and their initial status for new entries
COLUMNS = [
    "ID",
    "Departure Date (Multan)",
    "Client Name",
    "Product Name",
    "Quantity (Units)",
    "Payment Status (Bilty)",
    "Destination Location",
    "Current Location",
    "Received Date",
    "Status",
    "Receiver Contact",
    "Created Date",
    "Last Updated"
]

# Define the required dtypes for persistent data integrity
REQUIRED_DTYPES = {
    "ID": 'Int64',
    "Quantity (Units)": 'Int64',
    "Departure Date (Multan)": 'object',
    "Received Date": 'object',
    "Created Date": 'object',
    "Last Updated": 'object'
}

# --- Core Data Functions ---

def enforce_dtypes(df):
    """Ensures critical columns maintain their required dtypes before displaying/editing."""
    df_copy = df.copy()
    for col, dtype in REQUIRED_DTYPES.items():
        if col in df_copy.columns:
            try:
                if dtype == 'Int64':
                    # Convert to numeric, coerce errors, then to nullable integer
                    df_copy[col] = pd.to_numeric(df_copy[col], errors='coerce').astype('Int64')
                else:
                    df_copy[col] = df_copy[col].astype(dtype)
            except Exception as e:
                st.warning(f"Data type conversion issue in column {col}: {e}")
                df_copy[col] = df_copy[col].astype('object')
    return df_copy

def save_data():
    """Saves the current shipment records DataFrame to a CSV file."""
    try:
        df_to_save = st.session_state.shipments.copy()
        
        # Ensure ID column is int before saving to prevent float storage
        if 'ID' in df_to_save.columns:
            df_to_save['ID'] = df_to_save['ID'].astype('Int64')
        
        df_to_save.to_csv(DATA_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Failed to save data to file: {e}")
        return False

def add_shipment(data):
    """Adds a new shipment record to the session state DataFrame and saves to file."""
    # Handle empty DataFrame case to find max ID safely
    max_id = st.session_state.shipments['ID'].max() if not st.session_state.shipments.empty else 0
    new_id = max_id + 1
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Automated status logic for initial entry
    if data['rec_date']:
        initial_status = "Delivered"
        initial_location = f"{data['location']} (Delivered)"
    elif data['dep_date']:
        initial_status = "Departed (Multan)"
        initial_location = "In Transit (From Multan)"
    else:
        initial_status = data['status']
        initial_location = "Multan Warehouse"

    new_row = pd.DataFrame([{
        "ID": new_id,
        "Departure Date (Multan)": data['dep_date'].strftime('%Y-%m-%d') if data['dep_date'] else None,
        "Client Name": data['client_name'],
        "Product Name": data['product_name'],
        "Quantity (Units)": data['quantity'],
        "Payment Status (Bilty)": data['bilty_status'],
        "Destination Location": data['location'],
        "Current Location": initial_location,
        "Received Date": data['rec_date'].strftime('%Y-%m-%d') if data['rec_date'] else None,
        "Status": initial_status,
        "Receiver Contact": data['receiver_number'],
        "Created Date": current_time,
        "Last Updated": current_time
    }])

    st.session_state.shipments = pd.concat([st.session_state.shipments, new_row], ignore_index=True)
    
    # Enforce dtypes after concatenation
    st.session_state.shipments = enforce_dtypes(st.session_state.shipments)
    
    if save_data():
        st.success(f"✅ Shipment #{new_id} added successfully! Status: **{initial_status}**")
        return True
    return False

def delete_shipment(shipment_id):
    """Deletes a shipment record by ID and saves to file."""
    if st.session_state.shipments.empty:
        st.warning("No records to delete.")
        return False

    shipment_id_int = int(shipment_id)

    if shipment_id_int in st.session_state.shipments['ID'].values:
        st.session_state.shipments = st.session_state.shipments[
            st.session_state.shipments['ID'] != shipment_id_int
        ].copy() 
        
        st.session_state.shipments.reset_index(drop=True, inplace=True)
        
        if save_data():
            st.success(f"🗑️ Shipment ID #{shipment_id_int} permanently deleted.")
            return True
    else:
        st.error(f"❌ Shipment ID #{shipment_id_int} not found.")
    return False

def update_shipment_status(shipment_id, new_status):
    """Updates the status of a specific shipment and its current location."""
    if st.session_state.shipments.empty:
        return False
        
    shipment_id_int = int(shipment_id)
    mask = st.session_state.shipments['ID'] == shipment_id_int
    
    if mask.any():
        # Update status
        st.session_state.shipments.loc[mask, 'Status'] = new_status
        st.session_state.shipments.loc[mask, 'Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Update current location based on status
        if new_status == "Under Process":
            st.session_state.shipments.loc[mask, 'Current Location'] = "Multan Warehouse"
        elif new_status == "Departed (Multan)":
            st.session_state.shipments.loc[mask, 'Current Location'] = "In Transit (From Multan)"
        elif new_status == "Arrived at Destination Hub":
            destination = st.session_state.shipments.loc[mask, 'Destination Location'].iloc[0]
            st.session_state.shipments.loc[mask, 'Current Location'] = f"{destination} Hub"
        elif new_status == "Out for Delivery":
            destination = st.session_state.shipments.loc[mask, 'Destination Location'].iloc[0]
            st.session_state.shipments.loc[mask, 'Current Location'] = f"Local Delivery in {destination}"
        elif new_status == "Delivered":
            destination = st.session_state.shipments.loc[mask, 'Destination Location'].iloc[0]
            st.session_state.shipments.loc[mask, 'Current Location'] = f"{destination} (Delivered)"
        elif new_status == "Cancelled":
            st.session_state.shipments.loc[mask, 'Current Location'] = "Cancelled Order"
        
        if save_data():
            st.success(f"✅ Shipment #{shipment_id_int} status updated to: {new_status}")
            return True
    
    return False

def apply_status_automation(df):
    """
    Applies the automatic status change logic and updates Current Location based on status changes.
    """
    df_copy = df.copy()
    
    # Convert relevant date columns to datetime objects for comparison
    df_copy['Departure Date (Multan)'] = pd.to_datetime(df_copy['Departure Date (Multan)'], errors='coerce')
    df_copy['Received Date'] = pd.to_datetime(df_copy['Received Date'], errors='coerce')

    # Status automation logic
    
    # 1. Received Date set -> Status is 'Delivered' (Highest priority)
    rec_mask = (pd.notna(df_copy['Received Date'])) & (df_copy['Status'] != 'Cancelled')
    df_copy.loc[rec_mask, 'Status'] = 'Delivered'
    df_copy.loc[rec_mask, 'Current Location'] = df_copy.loc[rec_mask, 'Destination Location'] + " (Delivered)"

    # 2. Departure Date set -> Status is 'Departed (Multan)'
    post_depart_statuses = ['Departed (Multan)', 'Arrived at Destination Hub', 'Out for Delivery', 'Delivered']
    dep_mask = (pd.notna(df_copy['Departure Date (Multan)'])) & (df_copy['Status'].isin(['New Order', 'Under Process']))
    df_copy.loc[dep_mask, 'Status'] = 'Departed (Multan)'
    df_copy.loc[dep_mask, 'Current Location'] = "In Transit (From Multan)"
    
    # Update Last Updated timestamp for automated changes
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    automation_mask = rec_mask | dep_mask
    df_copy.loc[automation_mask, 'Last Updated'] = current_time

    # Convert dates back to string format for consistency
    df_copy['Departure Date (Multan)'] = df_copy['Departure Date (Multan)'].dt.strftime('%Y-%m-%d').where(pd.notna(df_copy['Departure Date (Multan)']), None)
    df_copy['Received Date'] = df_copy['Received Date'].dt.strftime('%Y-%m-%d').where(pd.notna(df_copy['Received Date']), None)
    
    return df_copy

def initialize_data():
    """Initialize or load shipment data with proper structure."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            df = enforce_dtypes(df)
            
            # Add missing columns if loading an old file
            if 'Current Location' not in df.columns:
                df['Current Location'] = "Multan Warehouse"
            if 'Created Date' not in df.columns:
                df['Created Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if 'Last Updated' not in df.columns:
                df['Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
            # Run automation to ensure consistency
            df = apply_status_automation(df)
            save_data()
            
            return df
        except Exception as e:
            st.error(f"Error loading existing data: {e}")
            return pd.DataFrame(columns=COLUMNS)
    else:
        return pd.DataFrame(columns=COLUMNS)

# Initialize session state
if 'shipments' not in st.session_state:
    st.session_state.shipments = initialize_data()

# --- UI Components ---

def render_sidebar():
    """Render the sidebar with company info and shipment entry form."""
    with st.sidebar:
        # Company Logo and Info
        st.markdown("""
        <div style="text-align: center; padding: 10px; background: #1e3a8a; color: white; border-radius: 10px;">
            <h2>🏭 NUTRION</h2>
            <p><strong>Professional Logistics Tracker</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.caption("### 📞 Contact Information")
        st.markdown(
            """
            **Office:** # 34, Lower Ground, Pearl City Towers, Sargodha Road, Faisalabad
            
            **Email:** info@nutrion.pk
            """
        )
        st.markdown("---")
        
        st.header("➕ New Shipment Entry")
        st.markdown("---")

        with st.form("shipment_form", clear_on_submit=True):
            client_name = st.text_input("Client Name", placeholder="Enter full client name", key="client_name_input")
            product_name = st.selectbox("Product Name", options=PRODUCT_LIST, key="product_name_select")
            quantity = st.number_input("Quantity (Units)", min_value=1, step=1, key="quantity_input")
            
            location = st.selectbox(
                "Destination City",
                options=PAKISTAN_CITIES,
                index=None,
                placeholder="Select destination city...",
                key="location_select"
            )
            
            bilty_status = st.radio(
                "Payment Status (Bilty)",
                options=["Paid", "Not Paid"],
                horizontal=True,
                key="bilty_status_radio"
            )
            
            st.subheader("📅 Dates & Process")

            dep_date = st.date_input(
                "Departure Date (from Multan)",
                value=None,
                help="Leave empty if not yet departed"
            )
            
            rec_date = st.date_input(
                "Received Date",
                value=None,
                help="Leave empty if not yet delivered"
            )

            # Only show status selection if no dates are provided
            if not dep_date and not rec_date:
                status_manual = st.selectbox(
                    "Initial Status",
                    options=["New Order", "Under Process"],
                    index=0,
                    key="status_select_manual"
                )
            else:
                status_manual = "New Order"
                st.info("Status will be automatically set based on dates")
            
            receiver_number = st.text_input("Receiver Contact Number", placeholder="e.g., 03XX-XXXXXXX", key="receiver_number_input")

            st.markdown("---")
            submit_button = st.form_submit_button("💾 Save New Shipment Record", type="primary", use_container_width=True)

            if submit_button:
                if not client_name or not location or quantity < 1:
                    st.error("❌ Please fill in Client Name, Destination City, and Quantity.")
                else:
                    shipment_data = {
                        'dep_date': dep_date,
                        'client_name': client_name,
                        'product_name': product_name,
                        'quantity': quantity,
                        'bilty_status': bilty_status,
                        'location': location,
                        'rec_date': rec_date,
                        'status': status_manual,
                        'receiver_number': receiver_number
                    }
                    add_shipment(shipment_data)

def render_dashboard_metrics():
    """Render the main dashboard metrics."""
    st.title("🏭 Nutrion Logistics Management Dashboard")
    
    # Calculate metrics
    total_shipments = len(st.session_state.shipments)
    new_orders = len(st.session_state.shipments[st.session_state.shipments['Status'] == 'New Order'])
    under_process = len(st.session_state.shipments[st.session_state.shipments['Status'] == 'Under Process'])
    in_transit = len(st.session_state.shipments[st.session_state.shipments['Status'].isin(["Departed (Multan)", "Arrived at Destination Hub", "Out for Delivery"])])
    delivered = len(st.session_state.shipments[st.session_state.shipments['Status'] == 'Delivered'])
    cancelled = len(st.session_state.shipments[st.session_state.shipments['Status'] == 'Cancelled'])
    
    # Display metrics
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    col1.metric("Total Shipments", total_shipments)
    col2.metric("New Orders", new_orders, delta=f"{new_orders}" if new_orders > 0 else None)
    col3.metric("Under Process", under_process, delta="⚠️ Action Needed" if under_process > 0 else None, delta_color="inverse")
    col4.metric("In Transit", in_transit)
    col5.metric("Delivered", delivered, delta=f"{delivered}" if delivered > 0 else None)
    col6.metric("Cancelled", cancelled, delta=f"{cancelled}" if cancelled > 0 else None)

def render_under_process_section():
    """Render the urgent action section for Under Process orders."""
    st.header("⏳ Urgent Action Required: Under Process Orders")
    
    df_under_process = st.session_state.shipments[
        st.session_state.shipments['Status'] == 'Under Process'
    ].copy()
    
    if not df_under_process.empty:
        st.warning(f"🚨 You have **{len(df_under_process)}** orders currently under preparation that need attention!")
        
        # Display as cards
        cols = st.columns(min(4, len(df_under_process)))
        
        for idx, (_, row) in enumerate(df_under_process.iterrows()):
            with cols[idx % len(cols)]:
                with st.container(border=True):
                    st.markdown(f"**📦 Shipment ID:** `{row['ID']}`")
                    st.markdown(f"**👤 Client:** {row['Client Name']}")
                    st.markdown(f"**📍 Destination:** {row['Destination Location']}")
                    st.markdown(f"**📦 Product:** {row['Product Name']}")
                    st.markdown(f"**🔢 Quantity:** {row['Quantity (Units)']}")
                    st.markdown(f"**💰 Payment:** {row['Payment Status (Bilty)']}")
                    
                    # Quick action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🚚 Mark Departed", key=f"depart_{row['ID']}", use_container_width=True):
                            if update_shipment_status(row['ID'], "Departed (Multan)"):
                                st.rerun()
                    with col2:
                        if st.button("❌ Cancel", key=f"cancel_{row['ID']}", use_container_width=True):
                            if update_shipment_status(row['ID'], "Cancelled"):
                                st.rerun()
    else:
        st.success("✅ No orders currently under process. All caught up!")

def render_live_tracker():
    """Render the live tracking and update section."""
    st.header("🚚 Live Tracking & Updates")
    
    if st.session_state.shipments.empty:
        st.info("📋 No shipment records found. Use the sidebar to add a new entry!")
        return
    
    # Filtering Section
    col_f1, col_f2, col_f3 = st.columns(3)
    
    filter_status = col_f1.multiselect(
        "Filter by Status", 
        options=STATUS_OPTIONS, 
        default=STATUS_OPTIONS
    )
    
    filter_client = col_f2.text_input(
        "Search Client", 
        placeholder="Enter client name...",
        key="client_search_input"
    )

    filter_product = col_f3.selectbox("Filter by Product", options=["All"] + PRODUCT_LIST)

    # Apply Filters
    df_filtered = st.session_state.shipments.copy()

    if filter_status:
        df_filtered = df_filtered[df_filtered['Status'].isin(filter_status)]
        
    if filter_client:
        df_filtered = df_filtered[df_filtered['Client Name'].str.contains(filter_client, case=False, na=False)]

    if filter_product != "All":
        df_filtered = df_filtered[df_filtered['Product Name'] == filter_product]

    # Enforce data types
    df_filtered = enforce_dtypes(df_filtered)

    st.markdown("---")
    st.caption("💡 **Tip:** Editing dates will automatically update the status. Use status dropdown for manual updates.")
    
    # Display editable data table
    edited_df = st.data_editor(
        df_filtered,
        use_container_width=True,
        column_config={
            "ID": st.column_config.NumberColumn("ID", disabled=True),
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=STATUS_OPTIONS,
                required=True,
            ),
            "Current Location": st.column_config.TextColumn("Current Location", disabled=True),
            "Departure Date (Multan)": st.column_config.DateColumn("Departure Date"),
            "Received Date": st.column_config.DateColumn("Received Date"),
            "Payment Status (Bilty)": st.column_config.SelectboxColumn(
                "Payment Status",
                options=["Paid", "Not Paid"],
            ),
            "Created Date": st.column_config.DatetimeColumn("Created", disabled=True),
            "Last Updated": st.column_config.DatetimeColumn("Last Updated", disabled=True),
        },
        hide_index=True,
        key="live_data_editor"
    )

    # Save changes
    if not df_filtered.equals(edited_df):
        automated_edited_df = apply_status_automation(edited_df)
        
        for index, row in automated_edited_df.iterrows():
            st.session_state.shipments.loc[st.session_state.shipments['ID'] == row['ID']] = row
        
        if save_data():
            st.toast("✅ Changes saved successfully!", icon="✅")
            st.rerun()

def render_reports():
    """Render the reports and export section."""
    st.header("📊 Reports & Analytics")
    
    if st.session_state.shipments.empty:
        st.info("No data available for reports.")
        return
    
    # Quick statistics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Clients", st.session_state.shipments['Client Name'].nunique())
    with col2:
        st.metric("Total Products", st.session_state.shipments['Product Name'].nunique())
    with col3:
        st.metric("Total Cities", st.session_state.shipments['Destination Location'].nunique())
    
    st.markdown("---")
    
    # Report filters
    with st.expander("🔍 Advanced Report Filters", expanded=True):
        col_r1, col_r2, col_r3 = st.columns(3)
        
        report_status = col_r1.multiselect("Status Filter", options=STATUS_OPTIONS, default=STATUS_OPTIONS)
        report_client = col_r2.text_input("Client Filter", placeholder="Filter by client...")
        report_location = col_r3.multiselect("City Filter", options=PAKISTAN_CITIES)
        
        df_report = st.session_state.shipments.copy()

        if report_status:
            df_report = df_report[df_report['Status'].isin(report_status)]
        
        if report_client:
            df_report = df_report[df_report['Client Name'].str.contains(report_client, case=False, na=False)]

        if report_location:
            df_report = df_report[df_report['Destination Location'].isin(report_location)]
    
    # Display report
    st.subheader(f"📋 Report Results: {len(df_report)} Records")
    
    if not df_report.empty:
        st.dataframe(df_report, use_container_width=True, hide_index=True)
        
        # Export options
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = df_report.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"📥 Export CSV ({len(df_report)} records)",
                data=csv_data,
                file_name=f'nutrion_export_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                mime='text/csv',
                use_container_width=True
            )
        
        with col2:
            # Status distribution chart
            status_counts = df_report['Status'].value_counts()
            st.bar_chart(status_counts)
    else:
        st.warning("No records match the current filters.")

def render_management():
    """Render the record management section."""
    st.header("⚙️ Record Management")
    
    if st.session_state.shipments.empty:
        st.info("No records available for management.")
        return
    
    st.markdown("### 🗑️ Delete Records")
    
    # Display all records for selection
    df_display = st.session_state.shipments[['ID', 'Client Name', 'Destination Location', 'Status', 'Created Date']].copy()
    df_display = enforce_dtypes(df_display)
    
    # Multi-select for deletion
    records_to_delete = st.multiselect(
        "Select records to delete:",
        options=df_display.apply(lambda x: f"ID: {x['ID']} - {x['Client Name']} ({x['Status']})", axis=1).tolist(),
        placeholder="Select records to delete..."
    )
    
    if records_to_delete:
        st.warning(f"⚠️ You are about to delete {len(records_to_delete)} record(s). This action cannot be undone!")
        
        if st.button("🚨 Confirm Permanent Deletion", type="primary", use_container_width=True):
            deleted_count = 0
            for record_str in records_to_delete:
                record_id = int(record_str.split("ID: ")[1].split(" -")[0])
                if delete_shipment(record_id):
                    deleted_count += 1
            
            if deleted_count > 0:
                st.success(f"✅ Successfully deleted {deleted_count} record(s)!")
                st.rerun()

# --- Main Application Flow ---

def main():
    """Main application function."""
    
    # Render sidebar
    render_sidebar()
    
    # Render main dashboard
    render_dashboard_metrics()
    st.markdown("---")
    
    # Tabbed interface
    tab1, tab2, tab3 = st.tabs(["📊 Live Tracker", "📈 Reports", "⚙️ Management"])
    
    with tab1:
        render_under_process_section()
        st.markdown("---")
        render_live_tracker()
    
    with tab2:
        render_reports()
    
    with tab3:
        render_management()

if __name__ == "__main__":
    main()
