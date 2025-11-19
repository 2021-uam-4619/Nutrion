import streamlit as st
import pandas as pd
from datetime import datetime
import os 

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
    "Current Location", # New column for real-time tracking
    "Received Date",
    "Status",
    "Receiver Contact"
]


# --- Core Data Functions ---

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
    
    # Automated status logic for initial entry
    if data['rec_date']:
        initial_status = "Delivered"
        initial_location = data['location']
    elif data['dep_date']:
        initial_status = "Departed (Multan)"
        initial_location = "In Transit (From Multan)"
    else:
        # Default to 'New Order' if no dates provided, or use the manual selection
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
        "Receiver Contact": data['receiver_number']
    }])

    st.session_state.shipments = pd.concat([st.session_state.shipments, new_row], ignore_index=True)
    
    if save_data():
        st.success(f"Shipment #{new_id} added and saved successfully. Status: **{initial_status}**")

def delete_shipment(shipment_id):
    """Deletes a shipment record by ID and saves to file."""
    if st.session_state.shipments.empty:
        st.warning("No records to delete.")
        return False

    # Convert ID to the appropriate integer type for comparison
    shipment_id_int = int(shipment_id)

    if shipment_id_int in st.session_state.shipments['ID'].values:
        st.session_state.shipments = st.session_state.shipments[
            st.session_state.shipments['ID'] != shipment_id_int
        ].copy() 
        
        st.session_state.shipments.reset_index(drop=True, inplace=True)
        
        if save_data():
            st.success(f"Shipment ID #{shipment_id_int} permanently deleted.")
            return True
    else:
        st.error(f"Shipment ID #{shipment_id_int} not found.")
    return False

def apply_status_automation(df):
    """
    Applies the automatic status change logic and updates Current Location based on status changes.
    """
    df_copy = df.copy()
    
    # 1. Convert relevant date columns to datetime objects for comparison
    df_copy['Departure Date (Multan)'] = pd.to_datetime(df_copy['Departure Date (Multan)'], errors='coerce')
    df_copy['Received Date'] = pd.to_datetime(df_copy['Received Date'], errors='coerce')

    # Status precedence logic
    
    # 2. Automation: Received Date set -> Status is 'Delivered' (Highest priority)
    rec_mask = (pd.notna(df_copy['Received Date'])) & (~df_copy['Status'].isin(['Delivered', 'Cancelled']))
    df_copy.loc[rec_mask, 'Status'] = 'Delivered'
    df_copy.loc[rec_mask, 'Current Location'] = df_copy.loc[rec_mask, 'Destination Location'] + " (Delivered)"

    # 3. Automation: Departure Date set -> Status is 'Departed (Multan)'
    # Only applies if not already a post-departure status
    post_depart_statuses = ['Departed (Multan)', 'Arrived at Destination Hub', 'Out for Delivery', 'Delivered', 'Cancelled']
    dep_mask = (pd.notna(df_copy['Departure Date (Multan)'])) & (~df_copy['Status'].isin(post_depart_statuses))
    df_copy.loc[dep_mask, 'Status'] = 'Departed (Multan)'
    df_copy.loc[dep_mask, 'Current Location'] = "In Transit (From Multan)"
    
    # 4. Handle manual status progression updates (to update Current Location)
    
    # Arrived at Hub
    arrived_mask = (df_copy['Status'] == 'Arrived at Destination Hub')
    df_copy.loc[arrived_mask, 'Current Location'] = df_copy.loc[arrived_mask, 'Destination Location'] + " Hub"

    # Out for Delivery
    out_mask = (df_copy['Status'] == 'Out for Delivery')
    df_copy.loc[out_mask, 'Current Location'] = "Local Delivery in " + df_copy.loc[out_mask, 'Destination Location']
    
    # Pre-transit status
    pre_transit_mask = (df_copy['Status'].isin(['New Order', 'Under Process']))
    df_copy.loc[pre_transit_mask, 'Current Location'] = "Multan Warehouse"

    # 5. Convert dates back to string format for consistency
    df_copy['Departure Date (Multan)'] = df_copy['Departure Date (Multan)'].dt.strftime('%Y-%m-%d').where(pd.notna(df_copy['Departure Date (Multan)']))
    df_copy['Received Date'] = df_copy['Received Date'].dt.strftime('%Y-%m-%d').where(pd.notna(df_copy['Received Date']))
    
    return df_copy


# Initialize session state for storing shipment data (and load from file)
if 'shipments' not in st.session_state:
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            st.session_state.shipments = df
            st.session_state.shipments['ID'] = st.session_state.shipments['ID'].astype('Int64') 
            
            # Add missing 'Current Location' column if loading an old file
            if 'Current Location' not in st.session_state.shipments.columns:
                 st.session_state.shipments['Current Location'] = "Multan Warehouse"
                 # Run automation once to set initial locations based on dates
                 st.session_state.shipments = apply_status_automation(st.session_state.shipments)
                 save_data() # Save updated structure
            
        except Exception as e:
            st.warning(f"Error loading existing data from CSV: {e}. Starting with an empty table.")
            st.session_state.shipments = pd.DataFrame(columns=COLUMNS)
    else:
        st.session_state.shipments = pd.DataFrame(columns=COLUMNS)


# --- Sidebar: Data Entry (Simplified) ---

with st.sidebar:
    # Company Logo and Info
    LOGO_URL = "https://placehold.co/150x50/1d4ed8/FFFFFF?text=NUTRION+LOGO"
    st.image(LOGO_URL, caption="Nutrion Logo Placeholder")
    
    st.markdown("---")
    st.caption("### Contact Information")
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
        
        # User can add city name or location manually, but we offer suggestions
        location_input = st.text_input(
            "Destination City / Location",
            placeholder="Enter full city name (e.g., Lahore)",
            key="location_input"
        )
        
        # Allow user to pick from list or use their input
        location = location_input if location_input else "N/A"
        
        bilty_status = st.radio(
            "Payment Status (Bilty)",
            options=["Paid", "Not Paid"],
            horizontal=True,
            key="bilty_status_radio"
        )
        
        st.subheader("Dates & Process")

        dep_date = st.date_input(
            "Departure Date (from Multan)",
            value=None,
            max_value=datetime.today(),
            help="Sets status to 'Departed (Multan)'."
        )
        
        rec_date = st.date_input(
            "Received Date",
            value=None,
            help="Sets status to 'Delivered'."
        )

        status_manual = st.selectbox(
            "Initial Status (If not Departed)",
            options=["New Order", "Under Process", "Cancelled"],
            index=STATUS_OPTIONS.index("New Order"),
            key="status_select_manual"
        )
        
        receiver_number = st.text_input("Receiver Contact Number", placeholder="e.g., 03XX-XXXXXXX", key="receiver_number_input")

        st.markdown("---")
        submit_button = st.form_submit_button("💾 Save New Shipment Record", type="primary")

        if submit_button:
            if not client_name or not location or quantity < 1:
                st.error("Please fill in Client Name, Destination City, and Quantity.")
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


# --- Dashboard View (Main Content) ---

st.title("Nutrion Logistics Management Dashboard") 

# Display key metrics using columns
col1, col2, col3, col4, col5 = st.columns(5)
total_shipments = len(st.session_state.shipments)
new_orders = st.session_state.shipments[st.session_state.shipments['Status'] == 'New Order'].shape[0]
under_process = st.session_state.shipments[st.session_state.shipments['Status'] == 'Under Process'].shape[0]
in_transit_related = st.session_state.shipments[st.session_state.shipments['Status'].isin(["Departed (Multan)", "Arrived at Destination Hub", "Out for Delivery"])].shape[0]
delivered = st.session_state.shipments[st.session_state.shipments['Status'] == 'Delivered'].shape[0]


col1.metric("Total Shipments", total_shipments)
col2.metric("New Orders", new_orders)
col3.metric("Under Process", under_process, delta="Needs Action", delta_color="inverse")
col4.metric("In Transit / Delivery", in_transit_related)
col5.metric("Delivered", delivered, delta=f"{delivered/total_shipments*100 if total_shipments > 0 else 0:.1f}% success", delta_color="normal")

st.markdown("---")

# --- Tabbed Interface ---
tab_live, tab_reports, tab_manage = st.tabs(["📊 Live Tracker & Update", "📋 Reports & Export", "🗑️ Record Management"])


with tab_live:
    
    # 1. Dedicated Section for Under Process Orders
    st.header("⏳ Urgent Action Required: Under Process Orders")
    
    df_under_process = st.session_state.shipments[st.session_state.shipments['Status'] == 'Under Process'].copy()
    
    if not df_under_process.empty:
        st.info(f"You have **{len(df_under_process)}** orders currently under preparation. Please assign Departure Dates to move them to **In Transit**.")
        
        # Display as a clean list of tiles
        cols = st.columns(min(len(df_under_process), 4)) # Max 4 columns
        
        for i, row in df_under_process.head(4).iterrows(): # Show top 4 in columns for visual appeal
            with cols[i % len(cols)]:
                with st.container(border=True):
                    st.markdown(f"**Shipment ID:** {row['ID']}")
                    st.markdown(f"**Client:** {row['Client Name']}")
                    st.markdown(f"**Destination:** {row['Destination Location']}")
                    st.markdown(f"**Product:** {row['Product Name']}")
                    st.markdown(f"**Status:** :orange[**{row['Status']}**]")
                    
                    # Add a simple button to jump to the editor for this item
                    if st.button(f"Update #{row['ID']}", key=f"update_btn_{row['ID']}", use_container_width=True):
                        # Simply display a message directing them to the table below
                        st.session_state.filter_client_live = row['Client Name']
                        st.toast(f"Filter set for Client: {row['Client Name']}. Scroll down to the table.", icon="🔍")


    st.markdown("---")
    st.header("🚚 Active Tracking & Updates")
    
    if st.session_state.shipments.empty:
        st.info("No shipment records found. Use the sidebar to add a new entry!")
    else:
        # --- Filtering Section ---
        col_f1, col_f2, col_f3 = st.columns(3)
        
        filter_status = col_f1.multiselect(
            "Filter by Tracking Stage", 
            options=STATUS_OPTIONS, 
            default=["Departed (Multan)", "Arrived at Destination Hub", "Out for Delivery"]
        )
        
        # Initialize filter search term from button click, if any
        if 'filter_client_live' not in st.session_state:
            st.session_state.filter_client_live = ""
            
        filter_client = col_f2.text_input(
            "Search by Client Name", 
            placeholder="e.g., ABC Farms",
            value=st.session_state.filter_client_live,
            key="client_search_input"
        )
        # Reset filter state after use
        st.session_state.filter_client_live = filter_client 

        filter_product = col_f3.selectbox("Filter by Product", options=["All"] + PRODUCT_LIST, index=0)

        # Apply Filters
        df_filtered = st.session_state.shipments.copy()

        if filter_status:
            df_filtered = df_filtered[df_filtered['Status'].isin(filter_status)]
            
        if filter_client:
            df_filtered = df_filtered[df_filtered['Client Name'].str.contains(filter_client, case=False, na=False)]

        if filter_product != "All":
            df_filtered = df_filtered[df_filtered['Product Name'] == filter_product]


        st.markdown("---")
        st.caption("Editing the Departure or Received Date will **automatically update the Status**.")
        
        # Display the data editor (allows editing/updating)
        edited_df = st.data_editor(
            df_filtered,
            use_container_width=True,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status (Tracking Step)",
                    options=STATUS_OPTIONS,
                    required=True,
                ),
                "Current Location": st.column_config.TextColumn("Current Location", help="Updated automatically based on Status"),
                "Departure Date (Multan)": st.column_config.DateColumn("Departure Date (Multan)"),
                "Received Date": st.column_config.DateColumn("Received Date"),
                "Payment Status (Bilty)": st.column_config.SelectboxColumn(
                    "Payment Status (Bilty)",
                    options=["Paid", "Not Paid"],
                ),
                "ID": st.column_config.TextColumn(disabled=True),
            },
            hide_index=True,
            key="live_data_editor"
        )

        # Check if the edited DataFrame is different from the stored one and apply automation/save
        if not df_filtered.equals(edited_df):
            
            # Apply the automation logic to the edited data
            automated_edited_df = apply_status_automation(edited_df)
            
            # Merge the updated/automated rows back into the main shipment data
            for index, row in automated_edited_df.iterrows():
                # Locate the corresponding row in the main state by ID and update it
                st.session_state.shipments.loc[st.session_state.shipments['ID'] == row['ID']] = row
            
            if save_data():
                st.toast("Table changes and automated tracking updates saved successfully!", icon="✅")
                st.rerun()

with tab_reports:
    st.header("Generate Custom Reports")
    
    if st.session_state.shipments.empty:
        st.info("No data available to generate reports.")
    else:
        st.markdown("Use the filters below to select the specific data you want in your report.")
        
        # Filtering for Report Generation
        with st.container(border=True):
            col_r1, col_r2, col_r3 = st.columns(3)
            
            report_status = col_r1.multiselect("Status(es) for Report", options=STATUS_OPTIONS, default=["Delivered"])
            report_client = col_r2.text_input("Filter by Client Name (Optional)", placeholder="Client name")
            report_location = col_r3.multiselect("Filter by Destination City", options=PAKISTAN_CITIES)
            
            df_report = st.session_state.shipments.copy()

            if report_status:
                df_report = df_report[df_report['Status'].isin(report_status)]
            
            if report_client:
                df_report = df_report[df_report['Client Name'].str.contains(report_client, case=False, na=False)]

            if report_location:
                df_report = df_report[df_report['Destination Location'].isin(report_location)]

        st.markdown(f"### Report Preview: {len(df_report)} Records Selected")
        st.dataframe(df_report, use_container_width=True, hide_index=True)
        
        if not df_report.empty:
            # Download button for the filtered report
            csv_data = df_report.to_csv(index=False).encode('utf-8')
            st.download_button(
                label=f"⬇️ Download Report ({len(df_report)} records)",
                data=csv_data,
                file_name=f'nutrion_report_{datetime.now().strftime("%Y%m%d_%H%M")}.csv',
                mime='text/csv',
                type="primary"
            )
        else:
            st.warning("No records match the current report filters.")


with tab_manage:
    st.header("Record Management & Deletion")
    st.markdown("---")
    
    if st.session_state.shipments.empty:
        st.info("No records available to delete.")
    else:
        st.markdown("### 🗑️ Delete Record by ID")
        st.markdown("To delete a record, search for the **Shipment ID** below, verify the details, and confirm deletion.")
        
        shipment_ids = st.session_state.shipments['ID'].tolist()
        df_display = st.session_state.shipments[['ID', 'Client Name', 'Destination Location', 'Status']].copy()

        with st.container(border=True):
            st.markdown("**⚠️ Warning: Deletion is Permanent**")
            
            # Allow searching for the ID by selecting it
            id_to_delete = st.selectbox(
                "Search and Select Shipment ID to Permanently Delete",
                options=shipment_ids,
                index=None,
                placeholder="Select an ID to delete...",
                key="id_to_delete_select_manage"
            )
            
            # Show details of the selected record
            if id_to_delete is not None:
                selected_row = df_display[df_display['ID'] == int(id_to_delete)].iloc[0]
                
                st.warning(f"""
                **Confirm Deletion of:**
                - **ID:** {selected_row['ID']}
                - **Client:** {selected_row['Client Name']}
                - **Location:** {selected_row['Destination Location']}
                - **Status:** {selected_row['Status']}
                """)
                
                delete_button = st.button("🚨 Confirm Permanent Delete", type="primary", use_container_width=True)
            else:
                delete_button = st.button("🚨 Confirm Permanent Delete", type="primary", disabled=True, use_container_width=True)

            if delete_button and id_to_delete is not None:
                if delete_shipment(id_to_delete):
                    st.rerun()
