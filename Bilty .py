import streamlit as st
import pandas as pd
from datetime import datetime
import os 

# --- Configuration and Initialization ---

# Define the file path for persistent data storage
DATA_FILE = 'shipments_data.csv'

# Set page title and layout
st.set_page_config(
    page_title="Nutrion Logistics Tracker", # Updated company name
    layout="wide",
    initial_sidebar_state="expanded"
)

# List of all products as specified by the user
PRODUCT_LIST = [
    "Strophase G", "Strophase P", "Strozyme NSP", "SP200", "SP300",
    "SP300 Advance", "Monica", "Linco Magic", "Enra Magic", "InduceAcid Plus",
    "InduceAcid Buty", "Coxibac", "Strozyme XYL", "Super Ener Emusifier",
    "Antioxdant", "Toxin Binder Weilituo", "Toxin Clean", "GutPro 60 (Tributyrin)",
    "InduceAcid Liquid", "Syngrow"
]

# Define the expected columns for a clean DataFrame structure
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

# --- Main Functions ---

def save_data():
    """Saves the current shipment records DataFrame to a CSV file."""
    try:
        st.session_state.shipments.to_csv(DATA_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Failed to save data to file: {e}")
        return False

def add_shipment(data):
    """Adds a new shipment record to the session state DataFrame and saves to file."""
    max_id = st.session_state.shipments['ID'].max() if not st.session_state.shipments.empty else 0
    new_id = max_id + 1
    
    new_row = pd.DataFrame([{
        "ID": new_id,
        "Departure Date (Multan)": data['dep_date'].strftime('%Y-%m-%d'),
        "Client Name": data['client_name'],
        "Product Name": data['product_name'],
        "Quantity (Units)": data['quantity'],
        "Payment Status (Bilty)": data['bilty_status'],
        "Destination Location": data['location'],
        "Received Date": data['rec_date'].strftime('%Y-%m-%d') if data['rec_date'] else None,
        "Status": data['status'],
        "Receiver Contact": data['receiver_number']
    }])

    st.session_state.shipments = pd.concat([st.session_state.shipments, new_row], ignore_index=True)
    
    # Save the updated data to the CSV file for persistence
    if save_data():
        st.success(f"Shipment #{new_id} added and saved successfully for Client: {data['client_name']}")

def delete_shipment(shipment_id):
    """Deletes a shipment record by ID and saves to file."""
    if st.session_state.shipments.empty:
        st.warning("No records to delete.")
        return False

    if shipment_id in st.session_state.shipments['ID'].values:
        # Filter out the row with the given ID
        st.session_state.shipments = st.session_state.shipments[
            st.session_state.shipments['ID'] != shipment_id
        ].copy() # Use .copy() to avoid SettingWithCopyWarning
        
        # Reset index after deletion (optional, but good practice)
        st.session_state.shipments.reset_index(drop=True, inplace=True)
        
        if save_data():
            st.success(f"Shipment #{shipment_id} deleted and saved successfully.")
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
            st.session_state.shipments['ID'] = st.session_state.shipments['ID'].astype(int)
        except Exception as e:
            st.error(f"Error loading existing data from CSV: {e}. Starting with an empty table.")
            st.session_state.shipments = pd.DataFrame(columns=COLUMNS)
    else:
        st.session_state.shipments = pd.DataFrame(columns=COLUMNS)


# --- Data Entry Form (Sidebar) ---

with st.sidebar:
    # Company Logo and Info
    # NOTE: Since we cannot load local files like 'logo.png', we use a placeholder image URL.
    # Replace the URL below with your actual logo path or hosted URL.
    LOGO_URL = "logo.png"
    st.image(LOGO_URL, caption="Your Company Logo Here")
    st.markdown("---")
    st.caption("### Nutrion Company Details")
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
            value="today",
            max_value=datetime.today(),
            help="The date the shipment left Multan."
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

        location = st.text_input("Destination Location", placeholder="City/Region", key="location_input")

        rec_date = st.date_input(
            "Received Date",
            value=None,
            help="The date the shipment was received (leave blank if not yet delivered).",
        )

        status = st.selectbox(
            "Shipment Status",
            options=["In Transit", "Delivered", "Delayed", "Cancelled"],
            key="status_select"
        )

        receiver_number = st.text_input("Receiver Contact Number", placeholder="e.g., 03XX-XXXXXXX", key="receiver_number_input")

        st.markdown("---")
        submit_button = st.form_submit_button("💾 Save Shipment Record")

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
                    'status': status,
                    'receiver_number': receiver_number
                }
                add_shipment(shipment_data)


# --- Dashboard View (Main Content) ---

st.title("Nutrion Logistics Management Dashboard") # Updated company name
st.subheader("Current Shipment Records")

# Display key metrics using columns
col1, col2, col3 = st.columns(3)
total_shipments = len(st.session_state.shipments)
in_transit = st.session_state.shipments[st.session_state.shipments['Status'] == 'In Transit'].shape[0]
delivered = st.session_state.shipments[st.session_state.shipments['Status'] == 'Delivered'].shape[0]

col1.metric("Total Shipments", total_shipments)
col2.metric("In Transit", in_transit)
col3.metric("Delivered", delivered)

st.markdown("---")

# --- Record Deletion Section ---
if not st.session_state.shipments.empty:
    st.header("Remove Shipment Record")
    
    # Get list of existing IDs
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
            # Delete record and rerun to refresh the table and metrics
            if delete_shipment(id_to_delete):
                st.rerun()

    st.markdown("---")

# Display the main data table
if not st.session_state.shipments.empty:
    st.markdown("### All Shipments Detail")

    # Styling for visual emphasis on status
    def style_status(val):
        """Applies color coding based on the shipment status."""
        if val == 'Delivered':
            color = 'background-color: #d4edda; color: #155724'  # Green
        elif val == 'In Transit':
            color = 'background-color: #fff3cd; color: #856404'  # Yellow/Orange
        elif val == 'Delayed':
            color = 'background-color: #f8d7da; color: #721c24'  # Red
        else:
            color = ''
        return color

    # Display the data editor (allows editing)
    edited_df = st.data_editor(
        st.session_state.shipments,
        use_container_width=True,
        column_config={
            "Status": st.column_config.SelectboxColumn(
                "Status",
                options=["In Transit", "Delivered", "Delayed", "Cancelled"],
                required=True,
            ),
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

    # Check if the edited DataFrame is different from the stored one and save it
    if not st.session_state.shipments.equals(edited_df):
        st.session_state.shipments = edited_df
        if save_data():
            st.toast("Table changes saved successfully!", icon="✅")


    st.caption("Note: Changes made directly in the table above (Status, Dates, Payment) are automatically saved.")

    # Download button
    csv_data = st.session_state.shipments.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Data as CSV",
        data=csv_data,
        file_name='logistics_shipments_export.csv',
        mime='text/csv',
    )


else:
    st.info("No shipment records found. Use the sidebar to add a new entry!")
