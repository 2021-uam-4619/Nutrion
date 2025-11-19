# nutrion_logistics_tracker.py
import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# ---------------------------
# Configuration
# ---------------------------
DATA_FILE = "shipments_data.csv"
PAGE_TITLE = "Nutrion Logistics Tracker | Professional Edition"
APP_LOGO = "https://placehold.co/150x50/1d4ed8/FFFFFF?text=NUTRION+LOGO"

PRODUCT_LIST = [
    "Strophase G", "Strophase P", "Strozyme NSP", "SP200", "SP300",
    "SP300 Advance", "Monica", "Linco Magic", "Enra Magic", "InduceAcid Plus",
    "InduceAcid Buty", "Coxibac", "Strozyme XYL", "Super Ener Emusifier",
    "Antioxdant", "Toxin Binder Weilituo", "Toxin Clean", "GutPro 60 (Tributyrin)",
    "InduceAcid Liquid", "Syngrow"
]

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

STATUS_OPTIONS = [
    "New Order",
    "Under Process",
    "Departed (Multan)",
    "Arrived at Destination Hub",
    "Out for Delivery",
    "Delivered",
    "Cancelled"
]

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
    "Receiver Contact"
]

REQUIRED_DTYPES = {
    "ID": "Int64",
    "Quantity (Units)": "Int64",
    # Dates will be stored as ISO strings or None
}

# ---------------------------
# Utility functions
# ---------------------------

def enforce_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce important dtypes and return a copy."""
    df = df.copy()
    for col, dtype in REQUIRED_DTYPES.items():
        if col in df.columns:
            try:
                if dtype == "Int64":
                    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
                else:
                    df[col] = df[col].astype(dtype)
            except Exception:
                df[col] = df[col].astype("object")
    # Ensure missing columns exist
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = None
    # Ensure column order
    df = df[COLUMNS]
    return df

def load_data() -> pd.DataFrame:
    """Load CSV into DataFrame safely, apply dtype fixes and automation."""
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype=str)
            # Convert numeric-ish columns back
            if "ID" in df.columns:
                df["ID"] = pd.to_numeric(df["ID"], errors="coerce").astype("Int64")
            if "Quantity (Units)" in df.columns:
                df["Quantity (Units)"] = pd.to_numeric(df["Quantity (Units)"], errors="coerce").astype("Int64")
            # Replace NaN with None for clarity
            df = df.where(pd.notna(df), None)
            df = enforce_dtypes(df)
            df = apply_status_automation(df)
            return df
        except Exception as e:
            st.warning(f"Failed reading data file: {e}. Starting fresh.")
            return pd.DataFrame(columns=COLUMNS)
    else:
        return pd.DataFrame(columns=COLUMNS)

def save_data(df: pd.DataFrame) -> bool:
    """Save DataFrame to CSV. Return True on success."""
    try:
        # Cast ID to numeric/integer for storage consistency
        df_to_save = df.copy()
        if "ID" in df_to_save.columns:
            df_to_save["ID"] = pd.to_numeric(df_to_save["ID"], errors="coerce").astype("Int64")
        # Replace None with empty strings for CSV stability
        df_to_save = df_to_save.where(pd.notna(df_to_save), "")
        df_to_save.to_csv(DATA_FILE, index=False)
        return True
    except Exception as e:
        st.error(f"Error saving data: {e}")
        return False

def apply_status_automation(df: pd.DataFrame) -> pd.DataFrame:
    """Update Status and Current Location based on Departure/Received dates and existing status."""
    df = df.copy()
    # Parse dates
    df["__dep_dt"] = pd.to_datetime(df["Departure Date (Multan)"], errors="coerce")
    df["__rec_dt"] = pd.to_datetime(df["Received Date"], errors="coerce")

    # Highest priority: Received Date -> Delivered
    rec_mask = df["__rec_dt"].notna()
    df.loc[rec_mask, "Status"] = "Delivered"
    df.loc[rec_mask, "Current Location"] = df.loc[rec_mask, "Destination Location"].fillna("") + " (Delivered)"

    # Departure but not yet delivered/cancelled -> Departed (Multan)
    post_departure_statuses = {"Departed (Multan)", "Arrived at Destination Hub", "Out for Delivery", "Delivered", "Cancelled"}
    dep_mask = df["__dep_dt"].notna() & (~df["Status"].isin(post_departure_statuses))
    df.loc[dep_mask, "Status"] = "Departed (Multan)"
    df.loc[dep_mask, "Current Location"] = "In Transit (From Multan)"

    # Manual statuses that should update current location
    arrived_mask = df["Status"] == "Arrived at Destination Hub"
    df.loc[arrived_mask, "Current Location"] = df.loc[arrived_mask, "Destination Location"].fillna("") + " Hub"

    out_mask = df["Status"] == "Out for Delivery"
    df.loc[out_mask, "Current Location"] = "Local Delivery in " + df.loc[out_mask, "Destination Location"].fillna("")

    pre_transit_mask = df["Status"].isin(["New Order", "Under Process"])
    df.loc[pre_transit_mask, "Current Location"] = "Multan Warehouse"

    # Clean temporary columns & ensure string dates
    df["Departure Date (Multan)"] = df["__dep_dt"].dt.strftime("%Y-%m-%d").where(df["__dep_dt"].notna(), None)
    df["Received Date"] = df["__rec_dt"].dt.strftime("%Y-%m-%d").where(df["__rec_dt"].notna(), None)
    df.drop(columns=["__dep_dt", "__rec_dt"], inplace=True, errors="ignore")

    # Enforce dtypes
    df = enforce_dtypes(df)
    return df

def next_id(df: pd.DataFrame) -> int:
    """Return next ID (1-based)."""
    if df.empty:
        return 1
    else:
        existing = pd.to_numeric(df["ID"], errors="coerce")
        max_id = int(existing.max()) if existing.notna().any() else 0
        return max_id + 1

def add_shipment(df: pd.DataFrame, payload: dict) -> pd.DataFrame:
    """Create new shipment row and return updated DataFrame."""
    new_id = next_id(df)
    dep_date = payload.get("dep_date")
    rec_date = payload.get("rec_date")

    # Prepare initial status and current location
    if rec_date:
        status = "Delivered"
        current_location = payload["location"]
    elif dep_date:
        status = "Departed (Multan)"
        current_location = "In Transit (From Multan)"
    else:
        status = payload.get("status", "New Order")
        current_location = "Multan Warehouse"

    new_row = {
        "ID": new_id,
        "Departure Date (Multan)": dep_date.strftime("%Y-%m-%d") if dep_date else None,
        "Client Name": payload.get("client_name"),
        "Product Name": payload.get("product_name"),
        "Quantity (Units)": int(payload.get("quantity") or 0),
        "Payment Status (Bilty)": payload.get("bilty_status"),
        "Destination Location": payload.get("location"),
        "Current Location": current_location,
        "Received Date": rec_date.strftime("%Y-%m-%d") if rec_date else None,
        "Status": status,
        "Receiver Contact": payload.get("receiver_number")
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df = enforce_dtypes(df)
    df = apply_status_automation(df)
    return df

def delete_shipment_by_id(df: pd.DataFrame, shipment_id: int) -> pd.DataFrame:
    """Return DataFrame with the specified ID removed."""
    if "ID" not in df.columns:
        return df
    df = df[df["ID"] != shipment_id].reset_index(drop=True)
    return df

# ---------------------------
# Initialize app state & page
# ---------------------------
st.set_page_config(page_title=PAGE_TITLE, layout="wide", initial_sidebar_state="expanded")
st.title("Nutrion Logistics Management Dashboard")
st.image(APP_LOGO, width=150)

if "shipments" not in st.session_state:
    st.session_state.shipments = load_data()

# ---------------------------
# Sidebar: New shipment entry
# ---------------------------
with st.sidebar:
    st.header("➕ New Shipment Entry")
    st.caption("Add a new bilty / shipment. Use the date toggles if no date yet.")
    with st.form("shipment_form", clear_on_submit=True):
        client_name = st.text_input("Client Name", placeholder="Enter full client name")
        product_name = st.selectbox("Product Name", options=PRODUCT_LIST)
        quantity = st.number_input("Quantity (Units)", min_value=1, step=1, value=1)
        # Destination: allow suggestion from list if user clicks
        use_suggestion = st.checkbox("Select Destination from common cities", value=False)
        if use_suggestion:
            location = st.selectbox("Destination City", options=PAKISTAN_CITIES)
        else:
            location = st.text_input("Destination City / Location", placeholder="e.g., Lahore").strip() or None

        bilty_status = st.radio("Payment Status (Bilty)", options=["Paid", "Not Paid"], horizontal=True)

        st.markdown("Dates (optional)")
        dep_toggle = st.checkbox("Set Departure Date (from Multan)?", value=False)
        if dep_toggle:
            dep_date = st.date_input("Departure Date (from Multan)", value=date.today(), max_value=date.today())
        else:
            dep_date = None

        rec_toggle = st.checkbox("Set Received Date (Delivered)?", value=False)
        if rec_toggle:
            rec_date = st.date_input("Received Date", value=date.today(), max_value=date.today())
        else:
            rec_date = None

        status_manual = st.selectbox("Initial Status (if not departed/delivered)", options=["New Order", "Under Process", "Cancelled"])
        receiver_number = st.text_input("Receiver Contact Number (optional)")

        submitted = st.form_submit_button("💾 Save New Shipment Record")
        if submitted:
            # Validation
            if not client_name or not location or quantity < 1:
                st.error("Please fill Client Name, Destination City, and Quantity.")
            else:
                payload = {
                    "dep_date": dep_date,
                    "client_name": client_name,
                    "product_name": product_name,
                    "quantity": quantity,
                    "bilty_status": bilty_status,
                    "location": location,
                    "rec_date": rec_date,
                    "status": status_manual,
                    "receiver_number": receiver_number
                }
                st.session_state.shipments = add_shipment(st.session_state.shipments, payload)
                if save_data(st.session_state.shipments):
                    st.success(f"Shipment added (ID: {st.session_state.shipments['ID'].iloc[-1]})")
                    st.experimental_rerun()
                else:
                    st.error("Failed to save new shipment. See logs.")

# ---------------------------
# Top metrics
# ---------------------------
total_shipments = len(st.session_state.shipments)
status_counts = st.session_state.shipments["Status"].value_counts(dropna=False).to_dict()

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Shipments", total_shipments)
col2.metric("New Orders", int(status_counts.get("New Order", 0)))
col3.metric("Under Process", int(status_counts.get("Under Process", 0)))
col4.metric("In Transit / Delivery", int(
    st.session_state.shipments["Status"].isin(["Departed (Multan)", "Arrived at Destination Hub", "Out for Delivery"]).sum()
))
delivered_count = int(status_counts.get("Delivered", 0))
col5.metric("Delivered", delivered_count, delta=f"{(delivered_count/total_shipments*100 if total_shipments else 0):.1f}%")

st.markdown("---")

# ---------------------------
# Tabs: Live Tracker, Reports, Manage
# ---------------------------
tab_live, tab_reports, tab_manage = st.tabs(["📊 Live Tracker & Update", "📋 Reports & Export", "🗑️ Record Management"])

# ---------- LIVE TAB ----------
with tab_live:
    st.header("⏳ Under Process — Quick Actions & Overview")

    df = st.session_state.shipments.copy()
    df = apply_status_automation(df)  # ensure automation run

    df_under = df[df["Status"] == "Under Process"].copy().reset_index(drop=True)
    count_under = len(df_under)

    cols = st.columns([1, 3])
    cols[0].metric("Under Process", count_under)
    cols[1].markdown("These are the bilty items currently being prepared. Assign a departure date to move them into transit.")

    # Card-style tiles (show up to 6)
    if count_under:
        n_show = min(6, count_under)
        tile_cols = st.columns(n_show)
        for i in range(n_show):
            row = df_under.iloc[i]
            with tile_cols[i]:
                st.markdown(f"**ID #{int(row['ID'])}**")
                st.write(row["Client Name"])
                st.write(row["Product Name"])
                st.write(f"Qty: {int(row['Quantity (Units)']) if pd.notna(row['Quantity (Units)']) else '—'}")
                st.write(f"Dest: {row['Destination Location'] or '—'}")
                # quick action to prefill filter below
                if st.button(f"Edit #{int(row['ID'])}", key=f"edit_under_{int(row['ID'])}"):
                    st.session_state._edit_target_id = int(row['ID'])
                    st.toast("Scroll to the Live Table to edit this shipment.", icon="🔧")
    else:
        st.info("No shipments are currently under process.")

    st.markdown("---")
    st.header("🚚 Live Tracking & Bulk Updates")

    # Filters
    col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
    filter_status = col_f1.multiselect("Filter by Status", options=STATUS_OPTIONS, default=["Departed (Multan)", "Arrived at Destination Hub", "Out for Delivery", "Under Process"])
    filter_client = col_f2.text_input("Search Client", value=st.session_state.get("_edit_target_client", ""))
    if "_edit_target_id" in st.session_state:
        # attempt to prefill client search when user clicked a tile
        tid = st.session_state._edit_target_id
        match = df[df["ID"] == tid]
        if not match.empty:
            filter_client = match.iloc[0]["Client Name"]
            st.session_state._edit_target_client = filter_client

    filter_product = col_f3.selectbox("Filter by Product", options=["All"] + PRODUCT_LIST)

    df_live = df.copy()
    if filter_status:
        df_live = df_live[df_live["Status"].isin(filter_status)]
    if filter_client:
        df_live = df_live[df_live["Client Name"].str.contains(filter_client, case=False, na=False)]
    if filter_product != "All":
        df_live = df_live[df_live["Product Name"] == filter_product]

    df_live = enforce_dtypes(df_live)

    st.caption("Edit the Status, Departure Date or Received Date directly. Changes will be saved and automation applied.")
    edited = st.data_editor(
        df_live,
        use_container_width=True,
        column_config={
            "Status": st.column_config.SelectboxColumn("Status", options=STATUS_OPTIONS),
            "Departure Date (Multan)": st.column_config.DateColumn("Departure Date (Multan)"),
            "Received Date": st.column_config.DateColumn("Received Date"),
            "Payment Status (Bilty)": st.column_config.SelectboxColumn("Payment Status (Bilty)", options=["Paid", "Not Paid"]),
            "ID": st.column_config.TextColumn("ID", disabled=True)
        },
        hide_index=True,
        key="live_editor"
    )

    # If editor changed compare by IDs and update main store
    def sync_edited(edited_df: pd.DataFrame):
        # edited_df contains only filtered rows; apply changes row-by-row into main DF by ID
        main_df = st.session_state.shipments.copy()
        # Coerce ID to numeric
        edited_df = edited_df.copy()
        if "ID" in edited_df.columns:
            edited_df["ID"] = pd.to_numeric(edited_df["ID"], errors="coerce").astype("Int64")
        for _, row in edited_df.iterrows():
            rid = int(row["ID"])
            # find index in main
            idx = main_df.index[main_df["ID"] == rid].tolist()
            if idx:
                i_main = idx[0]
                # Update row values in main_df
                for col in edited_df.columns:
                    main_df.at[i_main, col] = row[col]
        # re-run automation & save
        main_df = apply_status_automation(main_df)
        st.session_state.shipments = main_df
        saved = save_data(main_df)
        return saved

    # Save button to persist editor changes
    if st.button("Save Changes from Editor", type="primary"):
        saved = sync_edited(edited)
        if saved:
            st.toast("Changes saved and tracking updated.", icon="✅")
            st.experimental_rerun()
        else:
            st.error("Failed to save changes. Check logs.")

# ---------- REPORTS TAB ----------
with tab_reports:
    st.header("Generate Custom Reports")
    if st.session_state.shipments.empty:
        st.info("No data available to generate reports.")
    else:
        st.markdown("Choose filters and export a CSV of matching records.")
        with st.form("report_form"):
            r_col1, r_col2, r_col3 = st.columns(3)
            report_status = r_col1.multiselect("Status", options=STATUS_OPTIONS, default=["Delivered"])
            report_client = r_col2.text_input("Client name (optional)")
            report_location = r_col3.multiselect("Destination City", options=PAKISTAN_CITIES)
            run = st.form_submit_button("Preview Report")
        if run:
            df_report = st.session_state.shipments.copy()
            if report_status:
                df_report = df_report[df_report["Status"].isin(report_status)]
            if report_client:
                df_report = df_report[df_report["Client Name"].str.contains(report_client, case=False, na=False)]
            if report_location:
                df_report = df_report[df_report["Destination Location"].isin(report_location)]
            df_report = enforce_dtypes(df_report)
            st.write(f"Report: {len(df_report)} records")
            st.dataframe(df_report, use_container_width=True)
            if not df_report.empty:
                csv_bytes = df_report.to_csv(index=False).encode("utf-8")
                st.download_button("⬇️ Download CSV", csv_bytes, file_name=f"nutrion_report_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

# ---------- MANAGE TAB ----------
with tab_manage:
    st.header("Record Management & Deletion")
    if st.session_state.shipments.empty:
        st.info("No records to manage.")
    else:
        df_safe = enforce_dtypes(st.session_state.shipments.copy())
        st.dataframe(df_safe, use_container_width=True, height=300)
        st.markdown("### Delete a record by ID (permanent)")
        ids = df_safe["ID"].dropna().astype(int).tolist()
        id_choice = st.selectbox("Select Shipment ID to delete", options=ids, index=0)
        if id_choice:
            row = df_safe[df_safe["ID"] == int(id_choice)].iloc[0]
            st.warning(f"Confirm deletion of ID {row['ID']} — Client: {row['Client Name']}, Destination: {row['Destination Location']}, Status: {row['Status']}")
            if st.button("🚨 Delete Permanently"):
                st.session_state.shipments = delete_shipment_by_id(st.session_state.shipments, int(id_choice))
                if save_data(st.session_state.shipments):
                    st.success("Record deleted.")
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete record. Check logs.")
