import streamlit as st
import pandas as pd
from datetime import datetime
import os 

# --- Configuration and Initialization ---

# Define the file path for persistent data storage
DATA_FILE = 'shipments_data.csv'

# Set page title and layout
st.set_page_config(
    page_title="Nutrion Logistics Tracker | Professional Edition", # Updated title
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
        # Convert date columns back to string/object before saving
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
    max_id = st.session_state.shipments['ID'].max() if not st.session_state.shipments.empty else 0
    new_id = max_id + 1
    
    # Determine initial status: If departure date is set on creation, it's already 'In Transit'
    initial_status = "In Transit" if data['dep_date'] else "New Order"

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
    
    # Save the updated data to the CSV file for persistence
    if save_data():
        st.success(f"Shipment #{new_id} added and saved successfully for Client: {data['client_name']}. Status: {initial_status}")

def delete_shipment(shipment_id):
    """Deletes a shipment record by ID and saves to file."""
    if st.session_state.shipments.empty:
        st.warning("No records to delete.")
        return False

    if shipment_id in st.session_state.shipments['ID'].values:
        # Filter out the row with the given ID
        st.session_state.shipments = st.session_state.shipments[
            st.session_state.shipments['ID'] != shipment_id
        ].copy() 
        
        st.session_state.shipments.reset_index(drop=True, inplace=True)
        
        if save_data():
            st.success(f"Shipment ID #{shipment_id} deleted and saved successfully.")
            return True
    else:
        st.error(f"Shipment ID #{shipment_id} not found.")
    return False

# Initialize session state for storing shipment data (and load from file)
if 'shipments' not in st.session_state:
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE)
            st.session_state.shipments = df
            # Ensure ID column is Int64 (allows NaN for better compatibility with data_editor in some cases)
            st.session_state.shipments['ID'] = st.session_state.shipments['ID'].astype('Int64') 
        except Exception as e:
            st.warning(f"Error loading existing data from CSV: {e}. Starting with an empty table.")
            st.session_state.shipments = pd.DataFrame(columns=COLUMNS)
    else:
        st.session_state.shipments = pd.DataFrame(columns=COLUMNS)


# --- Data Entry Form (Sidebar) ---

with st.sidebar:
    # Company Logo and Info (Professional Header)
    LOGO_URL = "logo.png"
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
    
    st.header("🚛 New Shipment Entry")
    st.markdown("---")

    with st.form("shipment_form", clear_on_submit=True):
        dep_date = st.date_input(
            "Departure Date (from Multan)",
            value=None,
            max_value=datetime.today(),
            help="The date the shipment left Multan. Setting this will automatically update status to 'In Transit'."
        )

        client_name = st.text_input("Client Name", placeholder="Enter full client name", key="client_name_input")

        product_name = st.selectbox(
            "Product Name",
            options=PRODUCT_LIST,
            key="product_name_select"
        )

        quantity = st.number_input(
            "Quantity (Units)",
            min_value=1,
            step=1,
            key="quantity_input",
            help="Total number of units or bags."
        )

        bilty_status = st.radio(
            "Payment Status (Bilty)",
            options=["Paid", "Not Paid"],
            horizontal=True,
            key="bilty_status_radio"
        )
        
        # Comprehensive Cities Dropdown
        location = st.selectbox(
            "Destination Location",
            options=PAKISTAN_CITIES,
            placeholder="Select or type city name...",
            key="location_select"
        )

        rec_date = st.date_input(
            "Received Date",
            value=None,
            help="The date the shipment was received. Setting this will automatically update status to 'Delivered'.",
        )

        # Status is automatically set on submission, but available for manual override if necessary
        status = st.selectbox(
            "Manual Status Override (Optional)",
            options=STATUS_OPTIONS,
            index=STATUS_OPTIONS.index("New Order"),
            key="status_select_manual"
        )

        receiver_number = st.text_input("Receiver Contact Number", placeholder="e.g., 03XX-XXXXXXX", key="receiver_number_input")

        st.markdown("---")
        submit_button = st.form_submit_button("💾 Save New Shipment Record", type="primary")

        if submit_button:
            if not client_name or not location:
                st.error("Please fill in Client Name and Destination Location.")
            else:
                shipment_data = {
                    'dep_date': dep_date,
                    'client_name': client_name,
                    'product_name': product_name,
                    'quantity': quantity,
                    'bilty_status': bilty_status,
                    'location': location,
                    'rec_date': rec_date,
                    'status': status, # Will be overridden by dep_date logic in add_shipment
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


col1.metric("Total Records", total_shipments)
col2.metric("New Orders", new_orders)
col3.metric("In Transit", in_transit)
col4.metric("Delivered", delivered, delta=f"{delivered/total_shipments*100 if total_shipments > 0 else 0:.1f}% success", delta_color="normal")
col5.metric("Bilty Paid", paid)

st.markdown("---")


# --- Filtering and Search Section ---
st.header("Filter Shipments")
with st.container(border=True):
    col_f1, col_f2, col_f3 = st.columns(3)
    
    filter_status = col_f1.multiselect("Filter by Status", options=STATUS_OPTIONS, default=STATUS_OPTIONS)
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


# --- Main Data Table (Editable) ---
if not df_filtered.empty:
    st.markdown("### Filtered Shipments Detail (Editable)")

    # Display the data editor (allows editing)
    edited_df = st.data_editor(
        df_filtered,
        use_container_width=True,
        column_config={
            # Status is now automated based on date fields but still editable
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
        key="data_editor"
    )

    # Check if the edited DataFrame is different from the stored one and apply automation/save
    if not df_filtered.equals(edited_df):
        
        # --- AUTOMATION LOGIC ---
        
        # 1. Convert relevant date columns to datetime objects for comparison
        # Important: Errors='coerce' converts invalid/non-date strings (like None or NaN) to NaT
        edited_df['Departure Date (Multan)'] = pd.to_datetime(edited_df['Departure Date (Multan)'], errors='coerce')
        edited_df['Received Date'] = pd.to_datetime(edited_df['Received Date'], errors='coerce')

        # 2. Automation: Departure Date set -> Status is 'In Transit'
        # Only apply if status is not already Delivered or Cancelled
        dep_mask = (pd.notna(edited_df['Departure Date (Multan)'])) & (~edited_df['Status'].isin(['In Transit', 'Delivered', 'Cancelled']))
        edited_df.loc[dep_mask, 'Status'] = 'In Transit'

        # 3. Automation: Received Date set -> Status is 'Delivered'
        # Only apply if status is not already Delivered or Cancelled
        rec_mask = (pd.notna(edited_df['Received Date'])) & (~edited_df['Status'].isin(['Delivered', 'Cancelled']))
        edited_df.loc[rec_mask, 'Status'] = 'Delivered'
        
        # 4. Convert dates back to string format for display consistency and CSV saving
        edited_df['Departure Date (Multan)'] = edited_df['Departure Date (Multan)'].dt.strftime('%Y-%m-%d').where(pd.notna(edited_df['Departure Date (Multan)']))
        edited_df['Received Date'] = edited_df['Received Date'].dt.strftime('%Y-%m-%d').where(pd.notna(edited_df['Received Date']))

        
        # 5. Merge the updated/automated rows back into the main shipment data
        # Get IDs of all currently filtered/edited rows
        edited_ids = edited_df['ID'].tolist()
        
        # Update main state by replacing rows that were in the filtered view
        # A bit complex due to filtering, so we'll just update the rows by ID
        for index, row in edited_df.iterrows():
            st.session_state.shipments.loc[st.session_state.shipments['ID'] == row['ID']] = row
        
        
        if save_data():
            st.toast("Table changes and status updates saved successfully!", icon="✅")
    

    st.caption("Note: Changes made directly in the table (Dates, Payment, etc.) automatically trigger status updates and are saved.")

    # Download button
    csv_data = st.session_state.shipments.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Full Data as CSV",
        data=csv_data,
        file_name='nutrion_logistics_shipments_export.csv',
        mime='text/csv',
    )


# --- Record Deletion Section ---
    st.markdown("---")
    st.header("Remove Shipment Record")
    
    shipment_ids = st.session_state.shipments['ID'].tolist()

    with st.container(border=True):
        st.markdown("**⚠️ Permanent Deletion**")
        
        col_del_1, col_del_2 = st.columns([0.7, 0.3])

        with col_del_1:
            id_to_delete = st.selectbox(
                "Select Shipment ID to Delete",
                options=shipment_ids,
                index=None,
                placeholder="Select an ID...",
                key="id_to_delete_select"
            )
        
        with col_del_2:
            st.markdown("<br>", unsafe_allow_html=True) 
            delete_button = st.button("🗑️ Confirm Delete", type="primary", disabled=(id_to_delete is None), use_container_width=True)

        if delete_button and id_to_delete is not None:
            if delete_shipment(id_to_delete):
                st.rerun() # Rerun to refresh the UI after deletion

else:
    st.info("No shipment records match the current filters. Use the sidebar to add a new entry!")
