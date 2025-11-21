import streamlit as st
import pandas as pd
import requests
import json
from datetime import datetime
import random
import time
from fpdf import FPDF
import base64
import os
import urllib.parse # For handling URL query parameters

# --- Configuration & Styling ---

# Page configuration
st.set_page_config(
    page_title="Nutrion Logistics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        /* Using your preferred green/purple gradient */
        background: linear-gradient(135deg, #2E8B57 0%, #006400 100%); 
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    }
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #2E8B57;
    }
    .status-delivered { border-left-color: #28a745; }
    .status-transit { border-left-color: #ffc107; }
    .status-pending { border-left-color: #dc3545; }
    .quick-stats {
        display: flex;
        justify-content: space-between;
        margin: 1rem 0;
    }
    .stat-card {
        flex: 1;
        padding: 1rem;
        margin: 0 0.5rem;
        text-align: center;
        background: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    h4 {
        color: #006400;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- Utility Classes ---

class WhatsAppAPI:
    # NOTE: Using dummy/placeholder values for the API key and base URL
    def __init__(self):
        self.base_url = "https://api.ultramsg.com/instance151638/"
        self.token = "xepte100yjisfzv4"
    
    def send_message(self, to, message):
        """Send WhatsApp message"""
        # In a real-world scenario, you would make the actual API call here.
        # For this demonstration, we simulate success.
        
        # url = f"{self.base_url}messages/chat"
        # payload = {'token': self.token, 'to': to, 'body': message}
        # try:
        #     response = requests.post(url, data=payload)
        #     return response.status_code == 200
        # except:
        #     return False
        
        # Simulation:
        time.sleep(0.1) 
        st.sidebar.success(f"SIMULATED: WhatsApp message sent to {to}")
        return True
    
    def send_document(self, to, document_path, filename):
        """Send PDF document via WhatsApp"""
        # Simulation:
        time.sleep(0.1)
        st.sidebar.success(f"SIMULATED: PDF '{filename}' sent to {to}")
        return True

class PDFGenerator:
    def create_booking_pdf(self, booking_data):
        pdf = FPDF()
        pdf.add_page()
        
        # Title
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Nutrion Logistics - Booking Confirmation', 0, 1, 'C')
        pdf.ln(10)
        
        # Tracking ID
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'Tracking ID: {booking_data["tracking_id"]}', 0, 1)
        pdf.ln(5)
        
        # Sender Details
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Sender Details:', 0, 1)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 6, f'Name: {booking_data["sender_name"]}', 0, 1)
        pdf.cell(0, 6, f'Phone: {booking_data["sender_phone"]}', 0, 1)
        if booking_data.get("sender_phone2"):
            pdf.cell(0, 6, f'Alternate Phone: {booking_data["sender_phone2"]}', 0, 1)
        pdf.ln(5)
        
        # Receiver Details
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Receiver Details:', 0, 1)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 6, f'Name: {booking_data["receiver_name"]}', 0, 1)
        pdf.cell(0, 6, f'Phone: {booking_data["receiver_phone"]}', 0, 1)
        pdf.cell(0, 6, f'Location: {booking_data["receiver_location"]}', 0, 1)
        pdf.cell(0, 6, f'City: {booking_data["receiver_city"]}', 0, 1)
        pdf.ln(5)
        
        # Service Details
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Service Details:', 0, 1)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 6, f'Booking Date: {booking_data["booking_date"].strftime("%Y-%m-%d %H:%M")}', 0, 1)
        pdf.cell(0, 6, f'Delivery Type: {booking_data["delivery_type"]}', 0, 1)
        # Handle string input for weight
        pdf.cell(0, 6, f'Parcel Weight: {booking_data["parcel_weight"]}', 0, 1)
        pdf.ln(10)
        
        # Footer
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 10, 'Thank you for choosing Nutrion Logistics!', 0, 1, 'C')
        
        filename = f"booking_{booking_data['tracking_id']}.pdf"
        pdf.output(filename)
        return filename

class LogisticsSystem:
    def __init__(self):
        self.whatsapp = WhatsAppAPI()
        self.pdf_gen = PDFGenerator()
        self.load_data()
        
    def load_data(self):
        """Load data from session state"""
        if 'bookings' not in st.session_state:
            st.session_state.bookings = []
        if 'tracking_data' not in st.session_state:
            st.session_state.tracking_data = {}
        
    def generate_tracking_id(self):
        return f"NT{random.randint(100000, 999999)}"
    
    def add_booking(self, booking_data):
        tracking_id = self.generate_tracking_id()
        booking_data['tracking_id'] = tracking_id
        booking_data['booking_date'] = datetime.now()
        booking_data['status'] = 'Booking Confirmed'
        booking_data['current_location'] = 'Origin Branch'
        
        # Add to bookings
        st.session_state.bookings.append(booking_data)
        
        # Initialize tracking
        st.session_state.tracking_data[tracking_id] = [{
            'timestamp': datetime.now(),
            'status': 'Booking Confirmed',
            'location': 'Origin Branch (Faisalabad)',
            'description': 'Parcel booking received and confirmed'
        }]
        
        # Send WhatsApp notifications
        self.send_booking_notifications(booking_data)
        
        return tracking_id
    
    def send_booking_notifications(self, booking_data):
        """Send WhatsApp messages and PDF to customer, including custom internal details"""
        
        # This is the base URL where the Streamlit app is hosted. 
        # For a hosted app, this would be the public URL. Since Streamlit is local/sandbox here, 
        # we'll use a placeholder URL and rely on the user to manually enter the Tracking ID.
        # We simulate the query parameter functionality for demonstration.
        
        # The new link format: App URL + ?track_id=TRACKING_ID
        tracking_url = f"http://nutrion-logistics.com/track?track_id={booking_data['tracking_id']}"

        message = f"""🚚 *Nutrion Logistics - Booking Confirmed!*

📦 *Tracking ID:* {booking_data['tracking_id']}
📅 *Booking Date:* {booking_data['booking_date'].strftime('%d %b %Y %I:%M %p')}

👤 *Sender:* {booking_data['sender_name']}
👤 *Receiver:* {booking_data['receiver_name']}
📍 *Destination:* {booking_data['receiver_city']}

---
*Internal Process Update:*
We are preparing your goods (Qty: {booking_data['parcel_weight']}) for transfer from our *Faisalabad Office* to our *Multan Warehouse* to begin the TCS process.

*Internal Contact:* Sajjad (+92 317 3037409)
---

*Track your parcel Status ONLY (Limited Access):* {tracking_url}

Thank you for choosing Nutrion Logistics!"""

        # Send to sender
        if booking_data['sender_phone']:
            self.whatsapp.send_message(booking_data['sender_phone'], message)
        
        # Send to alternate sender number
        if booking_data.get('sender_phone2'):
            self.whatsapp.send_message(booking_data['sender_phone2'], message)
        
        # Send to receiver
        if booking_data['receiver_phone']:
            self.whatsapp.send_message(booking_data['receiver_phone'], message)
        
        # Generate and send PDF
        pdf_file = self.pdf_gen.create_booking_pdf(booking_data)
        if booking_data['sender_phone']:
            self.whatsapp.send_document(booking_data['sender_phone'], pdf_file, f"Booking_{booking_data['tracking_id']}.pdf")
        
        # Clean up PDF file
        try:
            os.remove(pdf_file)
        except:
            pass
    
    def update_booking(self, tracking_id, updated_data):
        """Update booking details"""
        for i, booking in enumerate(st.session_state.bookings):
            if booking['tracking_id'] == tracking_id:
                st.session_state.bookings[i].update(updated_data)
                return True
        return False
    
    def delete_booking(self, tracking_id):
        """Delete booking"""
        st.session_state.bookings = [b for b in st.session_state.bookings if b['tracking_id'] != tracking_id]
        if tracking_id in st.session_state.tracking_data:
            del st.session_state.tracking_data[tracking_id]
    
    def update_status(self, tracking_id, status, location, description):
        """Update parcel status"""
        if tracking_id in st.session_state.tracking_data:
            st.session_state.tracking_data[tracking_id].append({
                'timestamp': datetime.now(),
                'status': status,
                'location': location,
                'description': description
            })
            
            # Update booking status
            for booking in st.session_state.bookings:
                if booking['tracking_id'] == tracking_id:
                    booking['status'] = status
                    booking['current_location'] = location
                    break

def get_status_icon(status):
    icons = {
        "Booking Confirmed": "📦",
        "Parcel Collected": "🚚",
        "At Origin Hub": "🏢",
        "In Transit": "✈️",
        "Arrived at Destination": "📍",
        "Out for Delivery": "🚗",
        "Delivered": "✅",
        "Attempted": "🔄"
    }
    for key, icon in icons.items():
        if key in status:
            return icon
    return "📦"

# --- Main App Pages (Internal Access) ---

def show_dashboard(system):
    st.subheader("📊 Quick Overview")
    
    if not st.session_state.bookings:
        st.info("No bookings yet. Create your first booking to get started!")
        return
    
    # Recent bookings
    st.subheader("Recent Bookings")
    recent_bookings = sorted(st.session_state.bookings, key=lambda x: x['booking_date'], reverse=True)[:5]
    
    for booking in recent_bookings:
        status_color = "status-delivered" if "Delivered" in booking['status'] else "status-transit" if "Transit" in booking['status'] or "Hub" in booking['status'] else "status-pending"
        
        st.markdown(f'<div class="card {status_color}" style="display: flex; justify-content: space-between; align-items: center;">', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
        with col1:
            st.write(f"**{booking['tracking_id']}**")
            st.write(f"👤 {booking['sender_name']} → {booking['receiver_name']}")
        with col2:
            st.write(f"📍 To: {booking['receiver_city']}")
            st.write(f"💼 Status: **{booking['status']}**")
        with col3:
            st.write(f"Weight:")
            st.markdown(f"**{booking.get('parcel_weight', 'N/A')}**")
        with col4:
            if st.button("👁️ View", key=f"view_{booking['tracking_id']}"):
                st.session_state.view_track_id = booking['tracking_id']
                st.session_state.current_page = "Track Parcel"
                st.experimental_rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
            
def show_booking_form(system):
    st.subheader("📦 Create New Booking")
    
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 👤 Sender Details")
            sender_name = st.text_input("Full Name*", placeholder="Enter sender name")
            sender_phone = st.text_input("Phone Number*", placeholder="923001234567")
            sender_phone2 = st.text_input("Alternate Phone", placeholder="Optional alternate number")
            sender_address = st.text_area("Complete Address", placeholder="Full address with city")
        
        with col2:
            st.markdown("### 👤 Receiver Details")
            receiver_name = st.text_input("Receiver Name*", placeholder="Enter receiver name")
            receiver_phone = st.text_input("Receiver Phone*", placeholder="923001234567")
            receiver_location = st.text_input("Delivery Address*", placeholder="Complete delivery address")
            receiver_city = st.selectbox("Destination City*", 
                ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Hyderabad", "Peshawar", "Quetta"])
        
        st.markdown("### 🚚 Service Details")
        col3, col4 = st.columns(2)
        with col3:
            # Modified to allow string input for weight
            parcel_weight = st.text_input("Parcel Weight (kg / bags / custom)*", placeholder="E.g., 50 kg, 12 bags, or 'approx. 120 kg'")
            delivery_type = st.selectbox("Delivery Speed", ["Standard (3-5 days)", "Express (1-2 days)", "Same Day"])
        with col4:
            special_instructions = st.text_area("Special Instructions", placeholder="Any special handling requirements")
        
        submitted = st.form_submit_button("🚀 Confirm Booking", type="primary", use_container_width=True)
        
        if submitted:
            if all([sender_name, sender_phone, receiver_name, receiver_phone, receiver_location, parcel_weight]):
                # Note: pickup_required is omitted as requested
                booking_data = {
                    'sender_name': sender_name,
                    'sender_phone': sender_phone,
                    'sender_phone2': sender_phone2,
                    'sender_address': sender_address,
                    'receiver_name': receiver_name,
                    'receiver_phone': receiver_phone,
                    'receiver_location': receiver_location,
                    'receiver_city': receiver_city,
                    # 'pickup_required': pickup_required, # Removed
                    'delivery_type': delivery_type,
                    'parcel_weight': parcel_weight, # Now accepts string
                    'special_instructions': special_instructions
                }
                
                tracking_id = system.add_booking(booking_data)
                
                st.success(f"""
                ✅ **Booking Confirmed Successfully!**
                
                **Tracking ID:** {tracking_id}
                **Status:** Notifications sent (Check sidebar for simulation details)
                **Next Step:** Goods prepared for shipment from Faisalabad Office.
                """)
                
                # Show quick summary
                with st.expander("📋 Booking Summary", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Sender:**", sender_name)
                        st.write("**Phone:**", sender_phone)
                        st.write("**From:**", sender_address or "Faisalabad")
                    with col2:
                        st.write("**Receiver:**", receiver_name)
                        st.write("**To:**", receiver_city)
                        st.write("**Service:**", delivery_type)
                        st.write("**Weight/Qty:**", parcel_weight)
                    
            else:
                st.error("❌ Please fill all required fields (*)")

def show_tracking(system):
    st.subheader("🔍 Track Your Parcel")
    
    # Check if a tracking ID was passed from another section
    if hasattr(st.session_state, 'view_track_id') and st.session_state.view_track_id:
        tracking_id_default = st.session_state.view_track_id
        del st.session_state.view_track_id
    else:
        tracking_id_default = ""
        
    tracking_id = st.text_input("Enter Tracking ID", value=tracking_id_default, placeholder="NT123456")
    
    if tracking_id:
        track_parcel(system, tracking_id)
        
def show_management(system):
    st.subheader("📊 Manage Bookings")
    
    if not st.session_state.bookings:
        st.info("No bookings available")
        return
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search by Tracking ID, Name, or Phone")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Booking Confirmed", "Parcel Collected", "In Transit", "Delivered"])
    
    # Filter bookings
    filtered_bookings = st.session_state.bookings
    if search_term:
        filtered_bookings = [b for b in filtered_bookings if 
                             search_term.lower() in b['tracking_id'].lower() or
                             search_term.lower() in b['sender_name'].lower() or
                             search_term.lower() in b['sender_phone']]
    
    if status_filter != "All":
        filtered_bookings = [b for b in filtered_bookings if status_filter in b['status']]
    
    # Display bookings
    for booking in filtered_bookings:
        with st.expander(f"📦 {booking['tracking_id']} - {booking['sender_name']} → {booking['receiver_name']} ({booking['status']})", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write("**Sender:**", booking['sender_name'])
                st.write("**Phone:**", booking['sender_phone'])
                st.write("**Address:**", booking.get('sender_address', 'N/A'))
            
            with col2:
                st.write("**Receiver:**", booking['receiver_name'])
                st.write("**Destination:**", booking['receiver_city'])
                st.write("**Service:**", booking['delivery_type'])
            
            with col3:
                st.write("**Status:**", booking['status'])
                st.write("**Weight/Qty:**", booking.get('parcel_weight', 'N/A'))
                
                # Action buttons
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️ Edit", key=f"edit_{booking['tracking_id']}", use_container_width=True):
                        st.session_state.editing = booking['tracking_id']
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_{booking['tracking_id']}", use_container_width=True):
                        system.delete_booking(booking['tracking_id'])
                        st.success("Booking deleted successfully!")
                        st.experimental_rerun()
            
    # Edit functionality
    if hasattr(st.session_state, 'editing') and st.session_state.editing:
        editing_id = st.session_state.editing
        booking_to_edit = next((b for b in st.session_state.bookings if b['tracking_id'] == editing_id), None)
        
        if booking_to_edit:
            st.markdown("---")
            st.subheader(f"✏️ Edit Booking: {editing_id}")
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_sender_name = st.text_input("Sender Name", value=booking_to_edit['sender_name'])
                    new_sender_phone = st.text_input("Sender Phone", value=booking_to_edit['sender_phone'])
                    new_sender_address = st.text_area("Sender Address", value=booking_to_edit.get('sender_address', ''))
                
                with col2:
                    new_receiver_name = st.text_input("Receiver Name", value=booking_to_edit['receiver_name'])
                    new_receiver_phone = st.text_input("Receiver Phone", value=booking_to_edit['receiver_phone'])
                    new_receiver_location = st.text_input("Delivery Address", value=booking_to_edit['receiver_location'])
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 Save Changes", type="primary"):
                        updated_data = {
                            'sender_name': new_sender_name,
                            'sender_phone': new_sender_phone,
                            'sender_address': new_sender_address,
                            'receiver_name': new_receiver_name,
                            'receiver_phone': new_receiver_phone,
                            'receiver_location': new_receiver_location
                        }
                        system.update_booking(editing_id, updated_data)
                        del st.session_state.editing
                        st.success("✅ Booking updated successfully!")
                        st.experimental_rerun()
                
                with col_cancel:
                    if st.form_submit_button("❌ Cancel"):
                        del st.session_state.editing
                        st.experimental_rerun()

def show_status_update(system):
    st.subheader("🔄 Update Parcel Status (Internal)")
    
    if not st.session_state.bookings:
        st.info("No bookings available")
        return
    
    # Select booking to update
    tracking_options = {f"{b['tracking_id']} - {b['sender_name']} → {b['receiver_name']}": b['tracking_id'] 
                        for b in st.session_state.bookings}
    
    if not tracking_options:
        st.info("No parcels to update.")
        return

    selected_display = st.selectbox("Select Parcel", list(tracking_options.keys()))
    tracking_id = tracking_options[selected_display]
    
    if tracking_id:
        booking = next((b for b in st.session_state.bookings if b['tracking_id'] == tracking_id), None)
        
        if booking:
            st.info(f"Current Status: **{booking['status']}**")
            
            # Status update form
            with st.form("status_update"):
                new_status = st.selectbox("New Status", [
                    "Parcel Collected",
                    "At Origin Hub (Multan Warehouse)", 
                    "In Transit",
                    "Arrived at Destination",
                    "Out for Delivery",
                    "Delivered",
                    "Attempted - Not Delivered"
                ])
                
                location = st.text_input("Current Location", value=booking.get('current_location', 'Origin Branch (Faisalabad)'))
                description = st.text_area("Status Description", placeholder="Enter detailed status description")
                
                if st.form_submit_button("🔄 Update Status", type="primary"):
                    system.update_status(tracking_id, new_status, location, description)
                    
                    # Send WhatsApp update
                    message = f"""🔄 *Status Update - Nutrion Logistics*

📦 *Tracking ID:* {tracking_id}
🔄 *New Status:* {new_status}
📍 *Location:* {location}
📝 *Remarks:* {description}

*Track your parcel Status ONLY (Limited Access):* http://nutrion-logistics.com/track?track_id={tracking_id}"""
                    
                    # Send to both sender and receiver
                    if booking['sender_phone']:
                        system.whatsapp.send_message(booking['sender_phone'], message)
                    if booking['receiver_phone']:
                        system.whatsapp.send_message(booking['receiver_phone'], message)
                    
                    st.success("✅ Status updated and notifications sent!")

# --- Common Tracking Logic (Used by Internal and External views) ---

def track_parcel(system, tracking_id):
    """Displays the tracking timeline and details for a given ID."""
    if tracking_id in st.session_state.tracking_data:
        booking = next((b for b in st.session_state.bookings if b['tracking_id'] == tracking_id), None)
        
        if booking:
            # Current status box
            current_status = st.session_state.tracking_data[tracking_id][-1]
            st.markdown(f"""
            <div class="card status-transit" style="margin-bottom: 2rem;">
                <h4>📊 Current Status for {tracking_id}</h4>
                <p><strong>🔄 Status:</strong> {current_status['status']}</p>
                <p><strong>📍 Location:</strong> {current_status['location']}</p>
                <p><strong>🕒 Last Update:</strong> {current_status['timestamp'].strftime('%d %b %Y %I:%M %p')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Timeline
            st.markdown("### 📋 Delivery Timeline")
            
            timeline = sorted(st.session_state.tracking_data[tracking_id], key=lambda x: x['timestamp'], reverse=True)
            
            for update in timeline:
                icon = get_status_icon(update['status'])
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <strong>{icon} {update['status']}</strong>
                            <br>
                            <small>📍 {update['location']}</small>
                            <br>
                            <small>📝 {update['description']}</small>
                        </div>
                        <div style="text-align: right;">
                            <small>{update['timestamp'].strftime('%d %b %Y')}</small>
                            <br>
                            <small>{update['timestamp'].strftime('%I:%M %p')}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    
    else:
        st.error(f"❌ Tracking ID **{tracking_id}** not found.")

# --- Restricted External Tracking View ---

def show_external_tracking(system, tracking_id):
    """
    Limited access page for external users (clients) to check status only.
    This page is shown when a tracking ID is passed via the URL query parameter.
    """
    st.markdown('<div class="main-header">Nutrion Logistics - Parcel Tracking</div>', unsafe_allow_html=True)
    st.subheader(f"Status for Tracking ID: {tracking_id}")
    track_parcel(system, tracking_id)
    st.markdown("---")
    st.info("For further inquiries, please contact our internal team. This view is restricted to status updates only.")

# --- Main Application Flow ---

def main():
    # Initialize system
    system = LogisticsSystem()
    
    # 1. Check for external tracking ID in URL query parameters
    query_params = st.experimental_get_query_params()
    external_track_id = query_params.get('track_id', [None])[0]
    
    if external_track_id:
        # If track_id is present in the URL, show ONLY the external tracking page
        show_external_tracking(system, external_track_id)
        return # Exit main function, do not show sidebar or other pages

    # 2. Normal Internal Application Flow
    st.markdown('<div class="main-header">🚚 Nutrion Logistics System</div>', unsafe_allow_html=True)
    
    # Quick Stats
    total_bookings = len(st.session_state.bookings)
    delivered = len([b for b in st.session_state.bookings if 'Delivered' in b.get('status', '')])
    in_transit = len([b for b in st.session_state.bookings if 'Transit' in b.get('status', '') or 'Hub' in b.get('status', '')])
    pending = total_bookings - delivered - in_transit
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Bookings", total_bookings)
    with col2:
        st.metric("Delivered", delivered)
    with col3:
        st.metric("In Transit", in_transit)
    with col4:
        st.metric("Pending/Confirmed", pending)
    
    # Sidebar Navigation
    st.sidebar.title("📋 Internal Navigation")
    
    # Use session state to manage current page if needed for reruns
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "🏠 Dashboard"
        
    menu = st.sidebar.radio("", ["🏠 Dashboard", "📦 New Booking", "🔍 Track Parcel", "📊 Manage Bookings", "🔄 Update Status"], index=["🏠 Dashboard", "📦 New Booking", "🔍 Track Parcel", "📊 Manage Bookings", "🔄 Update Status"].index(st.session_state.current_page))
    
    st.session_state.current_page = menu # Update state for next rerun
    
    if menu == "🏠 Dashboard":
        show_dashboard(system)
    elif menu == "📦 New Booking":
        show_booking_form(system)
    elif menu == "🔍 Track Parcel":
        show_tracking(system)
    elif menu == "📊 Manage Bookings":
        show_management(system)
    elif menu == "🔄 Update Status":
        show_status_update(system)

if __name__ == "__main__":
    main()
