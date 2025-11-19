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

# Define the expected columns and their initial status for new entries
COLUMNS = [
    "ID",
    "Departure Date (Multan)",
    "Client Name",
    "Product Name",
    "Quantity (Units)",
    "Payment Status (Bilty)",
    "Destination Location",
    "Received Date",
    "Status",
    "Receiver Contact"
]

# List of available status options, reflecting the new flow
STATUS_OPTIONS = ["New Order", "Under Process", "In Transit", "Delivered", "Cancelled"]


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
    elif data['dep_date']:
        initial_status = "In Transit"
    else:
        initial_status = data['status'] # Use manual override (New Order/Under Process/etc.)

    new_row = pd.DataFrame([{
        "ID": new_id,
        "Departure Date (Multan)": data['dep_date'].strftime('%Y-%m-%d') if data['dep_date'] else None,
        "Client Name": data['client_name'],
        "Product Name": data['product_name'],
        "Quantity (Units)": data['quantity'],
        "Payment Status (Bilty)": data['bilty_status'],
        "Destination Location": data['location'],
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
    Applies the automatic status change logic to the DataFrame based on date fields.
    This function is called right before saving edits.
    """
    df_copy = df.copy()
    
    # 1. Convert relevant date columns to datetime objects for comparison
    df_copy['Departure Date (Multan)'] = pd.to_datetime(df_copy['Departure Date (Multan)'], errors='coerce')
    df_copy['Received Date'] = pd.to_datetime(df_copy['Received Date'], errors='coerce')

    # 2. Automation: Received Date set -> Status is 'Delivered' (Highest priority)
    # Only apply if status is not already Delivered or Cancelled
    rec_mask = (pd.notna(df_copy['Received Date'])) & (~df_copy['Status'].isin(['Delivered', 'Cancelled']))
    df_copy.loc[rec_mask, 'Status'] = 'Delivered'

    # 3. Automation: Departure Date set -> Status is 'In Transit'
    # Only apply if status is not already Delivered, In Transit, or Cancelled
    dep_mask = (pd.notna(df_copy['Departure Date (Multan)'])) & (~df_copy['Status'].isin(['In Transit', 'Delivered', 'Cancelled']))
    df_copy.loc[dep_mask, 'Status'] = 'In Transit'
    
    # 4. Convert dates back to string format for consistency
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
        
        location = st.selectbox(
            "Destination City",
            options=PAKISTAN_CITIES,
            placeholder="Select city...",
            key="location_select"
        )
        
        bilty_status = st.radio(
            "Payment Status (Bilty)",
            options=["Paid", "Not Paid"],
            horizontal=True,
            key="bilty_status_radio"
        )
        
        st.subheader("Dates & Status")

        dep_date = st.date_input(
            "Departure Date (from Multan)",
            value=None,
            max_value=datetime.today(),
            help="Sets status to 'In Transit'."
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
in_transit = st.session_state.shipments[st.session_state.shipments['Status'] == 'In Transit'].shape[0]
delivered = st.session_state.shipments[st.session_state.shipments['Status'] == 'Delivered'].shape[0]
paid = st.session_state.shipments[st.session_state.shipments['Payment Status (Bilty)'] == 'Paid'].shape[0]


col1.metric("Total Shipments", total_shipments)
col2.metric("New Orders", new_orders)
col3.metric("In Transit", in_transit)
col4.metric("Delivered", delivered, delta=f"{delivered/total_shipments*100 if total_shipments > 0 else 0:.1f}% success", delta_color="normal")
col5.metric("Bilty Paid", paid)

st.markdown("---")

# --- Tabbed Interface ---
tab_live, tab_reports, tab_manage = st.tabs(["📊 Live Tracker & Update", "📋 Reports & Export", "🗑️ Record Management"])


with tab_live:
    
    st.subheader("Filter and Update Shipments")
    
    if st.session_state.shipments.empty:
        st.info("No shipment records found. Use the sidebar to add a new entry!")
    else:
        # --- Filtering Section (Moved into the tab) ---
        col_f1, col_f2, col_f3 = st.columns(3)
        
        filter_status = col_f1.multiselect("Filter by Status", options=STATUS_OPTIONS, default=["In Transit", "Under Process"])
        filter_client = col_f2.text_input("Search by Client Name", placeholder="e.g., ABC Farms")
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
        st.markdown("### Editable Shipment Table (Edit Any Row)")
        st.caption("Editing the Departure Date or Received Date will **automatically update the Status**.")
        
        # Display the data editor (allows editing/updating)
        edited_df = st.data_editor(
            df_filtered,
            use_container_width=True,
            column_config={
                "Status": st.column_config.SelectboxColumn(
                    "Status",
                    options=STATUS_OPTIONS,
                    required=True,
                ),
                # Date columns for automation trigger
                "Departure Date (Multan)": st.column_config.DateColumn("Departure Date (Multan)"),
                "Received Date": st.column_config.DateColumn("Received Date"),
                "Payment Status (Bilty)": st.column_config.SelectboxColumn(
                    "Payment Status (Bilty)",
                    options=["Paid", "Not Paid"],
                ),
                "ID": st.column_config.TextColumn(disabled=True), # Prevent editing the ID
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
                st.toast("Table changes and automated status updates saved successfully!", icon="✅")
                # Rerun to refresh the display with new metrics/status
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
            
            report_status = col_r1.multiselect("Status(es) for Report", options=STATUS_OPTIONS, default=STATUS_OPTIONS)
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
        st.markdown("To delete a record, find its **Shipment ID** in the **Live Tracker** tab, select it below, and confirm deletion.")
        
        # Get list of existing IDs
        shipment_ids = st.session_state.shipments['ID'].tolist()

        with st.container(border=True):
            st.markdown("**⚠️ Warning: Deletion is Permanent**")
            
            col_del_1, col_del_2 = st.columns([0.7, 0.3])

            with col_del_1:
                id_to_delete = st.selectbox(
                    "Select Shipment ID to Permanently Delete",
                    options=shipment_ids,
                    index=None,
                    placeholder="Select an ID to delete...",
                    key="id_to_delete_select"
                )
            
            with col_del_2:
                # Add a vertical space to align the button
                st.markdown("<br>", unsafe_allow_html=True) 
                delete_button = st.button("🚨 Confirm Delete", type="primary", disabled=(id_to_delete is None), use_container_width=True)

            if delete_button and id_to_delete is not None:
                if delete_shipment(id_to_delete):
                    st.rerun() # Rerun to refresh the UI after deletion
