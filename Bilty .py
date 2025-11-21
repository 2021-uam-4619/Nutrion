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
        color: #2E8B57;
        text-align: center;
        margin-bottom: 1rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
    }
    .card {
        padding: 1.5rem;
        border-radius: 10px;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
        border-left: 4px solid #2E8B57;
    }
    .btn-primary {
        background-color: #2E8B57;
        color: white;
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 5px;
        cursor: pointer;
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
    .limited-access {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

class WhatsAppAPI:
    def __init__(self):
        self.base_url = "https://api.ultramsg.com/instance151638/"
        self.token = "xepte100yjisfzv4"
    
    def send_message(self, to, message):
        """Send WhatsApp message"""
        url = f"{self.base_url}messages/chat"
        payload = {
            'token': self.token,
            'to': to,
            'body': message
        }
        try:
            response = requests.post(url, data=payload)
            return response.status_code == 200
        except:
            return False
    
    def send_document(self, to, document_path, filename):
        """Send PDF document via WhatsApp"""
        url = f"{self.base_url}messages/document"
        files = {
            'document': (filename, open(document_path, 'rb'))
        }
        payload = {
            'token': self.token,
            'to': to,
            'filename': filename
        }
        try:
            response = requests.post(url, data=payload, files=files)
            return response.status_code == 200
        except:
            return False

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
        
        # Product Details
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Product Details:', 0, 1)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 6, f'Product Name: {booking_data["product_name"]}', 0, 1)
        pdf.cell(0, 6, f'Quantity: {booking_data["quantity"]}', 0, 1)
        pdf.cell(0, 6, f'Weight: {booking_data["parcel_weight"]}', 0, 1)
        pdf.ln(5)
        
        # Service Details
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'Service Details:', 0, 1)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 6, f'Booking Date: {booking_data["booking_date"].strftime("%Y-%m-%d %H:%M")}', 0, 1)
        pdf.cell(0, 6, f'Delivery Type: {booking_data["delivery_type"]}', 0, 1)
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
        booking_data['status'] = 'Order Received'
        booking_data['current_location'] = 'Faisalabad Office'
        
        # Add to bookings
        st.session_state.bookings.append(booking_data)
        
        # Initialize tracking
        st.session_state.tracking_data[tracking_id] = [{
            'timestamp': datetime.now(),
            'status': 'Order Received',
            'location': 'Faisalabad Office',
            'description': 'New order received and processing started'
        }]
        
        # Send WhatsApp notifications to staff
        self.send_staff_notifications(booking_data)
        
        return tracking_id
    
    def send_staff_notifications(self, booking_data):
        """Send WhatsApp messages to staff with order details"""
        staff_message = f"""📦 *NEW ORDER - Nutrion Logistics*

🆔 *Tracking ID:* {booking_data['tracking_id']}
📅 *Order Date:* {booking_data['booking_date'].strftime('%d %b %Y %I:%M %p')}

📋 *Product Details:*
🏷️ *Product Name:* {booking_data['product_name']}
📊 *Quantity:* {booking_data['quantity']}
⚖️ *Weight:* {booking_data['parcel_weight']}

👤 *Customer Details:*
📛 *Name:* {booking_data['sender_name']}
📞 *Phone:* {booking_data['sender_phone']}
📍 *Location:* {booking_data['receiver_location']}
🏙️ *City:* {booking_data['receiver_city']}

🚚 *Next Steps:*
1. Prepare goods as per quantity
2. Generate bilty
3. Arrange transport to Multan warehouse
4. Update status in system

*TCS Process Starting Soon*"""

        # Send to Sajjad
        sajjad_number = "+923173037409"
        self.whatsapp.send_message(sajjad_number, staff_message)
        
        # Send customer confirmation
        customer_message = f"""✅ *Order Confirmed - Nutrion Logistics*

🆔 *Tracking ID:* {booking_data['tracking_id']}
📅 *Order Date:* {booking_data['booking_date'].strftime('%d %b %Y %I:%M %p')}

📋 *Your Order:*
🏷️ *Product:* {booking_data['product_name']}
📊 *Quantity:* {booking_data['quantity']}
⚖️ *Weight:* {booking_data['parcel_weight']}

📍 *Delivery To:* {booking_data['receiver_city']}

📊 *Track Your Order:*
http://localhost:8501/?tracking={booking_data['tracking_id']}

We'll update you at every step! Thank you for choosing us!"""

        # Send to customer
        if booking_data['sender_phone']:
            self.whatsapp.send_message(booking_data['sender_phone'], customer_message)
        
        # Generate and send PDF to staff
        pdf_file = self.pdf_gen.create_booking_pdf(booking_data)
        self.whatsapp.send_document(sajjad_number, pdf_file, f"Order_{booking_data['tracking_id']}.pdf")
        
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
                    
                    # Send status update to customer
                    self.send_status_update(booking, status, location, description)
                    break
    
    def send_status_update(self, booking, status, location, description):
        """Send status update to customer via WhatsApp"""
        message = f"""🔄 *Status Update - Nutrion Logistics*

📦 *Tracking ID:* {booking['tracking_id']}
🔄 *Status:* {status}
📍 *Location:* {location}
📝 *Update:* {description}

📋 *Product:* {booking['product_name']}
📊 *Quantity:* {booking['quantity']}

📊 *Track Your Order:*
http://localhost:8501/?tracking={booking['tracking_id']}

Thank you for choosing Nutrion Logistics!"""
        
        if booking['sender_phone']:
            self.whatsapp.send_message(booking['sender_phone'], message)

def show_limited_tracking_view(tracking_id, system):
    """Show limited access view for customers"""
    st.markdown('<div class="limited-access">', unsafe_allow_html=True)
    st.markdown('<h1>🚚 Nutrion Logistics</h1>', unsafe_allow_html=True)
    st.markdown('<h3>Track Your Parcel</h3>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if tracking_id in st.session_state.tracking_data:
        booking = next((b for b in st.session_state.bookings if b['tracking_id'] == tracking_id), None)
        
        if booking:
            # Current status
            current_status = st.session_state.tracking_data[tracking_id][-1]
            
            st.success(f"✅ Parcel Found - {booking['tracking_id']}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"""
                <div class="card status-transit">
                    <h4>📊 Current Status</h4>
                    <p><strong>🔄 Status:</strong> {current_status['status']}</p>
                    <p><strong>📍 Location:</strong> {current_status['location']}</p>
                    <p><strong>🕒 Last Update:</strong> {current_status['timestamp'].strftime('%d %b %Y %I:%M %p')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Order Details
                st.markdown("### 📦 Order Details")
                st.write(f"**Product:** {booking['product_name']}")
                st.write(f"**Quantity:** {booking['quantity']}")
                st.write(f"**Weight:** {booking['parcel_weight']}")
                st.write(f"**Customer:** {booking['sender_name']}")
                st.write(f"**Destination:** {booking['receiver_city']}")
            
            with col2:
                st.markdown("### 📋 Delivery Timeline")
                timeline = sorted(st.session_state.tracking_data[tracking_id], key=lambda x: x['timestamp'])
                
                for update in reversed(timeline):
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
            st.error("❌ Parcel not found. Please check your Tracking ID.")
    else:
        st.error("❌ Parcel not found. Please check your Tracking ID.")
    
    # Only show tracking input, no other features
    st.markdown("---")
    st.subheader("🔍 Track Another Parcel")
    new_tracking_id = st.text_input("Enter another Tracking ID", key="limited_tracking")
    if new_tracking_id:
        st.experimental_set_query_params(tracking=new_tracking_id)
        st.experimental_rerun()

def main():
    # Check if limited access view is requested via query parameter
    query_params = st.experimental_get_query_params()
    if 'tracking' in query_params:
        tracking_id = query_params['tracking'][0]
        system = LogisticsSystem()
        show_limited_tracking_view(tracking_id, system)
        return
    
    # Full application view
    st.markdown('<div class="main-header">🚚 Nutrion Logistics System</div>', unsafe_allow_html=True)
    
    # Initialize system
    system = LogisticsSystem()
    
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
        st.metric("Pending", pending)
    
    # Sidebar Navigation
    st.sidebar.title("📋 Navigation")
    menu = st.sidebar.radio("", ["🏠 Dashboard", "📦 New Order", "🔍 Track Parcel", "📊 Manage Orders", "🔄 Update Status"])
    
    if menu == "🏠 Dashboard":
        show_dashboard(system)
    elif menu == "📦 New Order":
        show_booking_form(system)
    elif menu == "🔍 Track Parcel":
        show_tracking(system)
    elif menu == "📊 Manage Orders":
        show_management(system)
    elif menu == "🔄 Update Status":
        show_status_update(system)

def show_dashboard(system):
    st.subheader("📊 Quick Overview")
    
    if not st.session_state.bookings:
        st.info("No orders yet. Create your first order to get started!")
        return
    
    # Recent bookings
    st.subheader("Recent Orders")
    recent_bookings = sorted(st.session_state.bookings, key=lambda x: x['booking_date'], reverse=True)[:5]
    
    for booking in recent_bookings:
        with st.container():
            col1, col2, col3, col4 = st.columns([2,2,1,1])
            with col1:
                st.write(f"**{booking['tracking_id']}**")
                st.write(f"📦 {booking['product_name']} - {booking['quantity']}")
            with col2:
                st.write(f"👤 {booking['sender_name']}")
                st.write(f"📍 {booking['receiver_city']}")
            with col3:
                status_color = "status-delivered" if "Delivered" in booking['status'] else "status-transit" if "Transit" in booking['status'] else "status-pending"
                st.markdown(f'<div class="card {status_color}">{booking["status"]}</div>', unsafe_allow_html=True)
            with col4:
                if st.button("📋", key=f"view_{booking['tracking_id']}"):
                    st.session_state.current_tracking = booking['tracking_id']
    
    # Quick actions
    st.subheader("Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📦 Create New Order", use_container_width=True):
            st.session_state.current_page = "New Order"
            st.experimental_rerun()
    
    with col2:
        if st.button("🔍 Track Parcel", use_container_width=True):
            st.session_state.current_page = "Track Parcel"
            st.experimental_rerun()
    
    with col3:
        if st.button("📊 View All Orders", use_container_width=True):
            st.session_state.current_page = "Manage Orders"
            st.experimental_rerun()

def show_booking_form(system):
    st.subheader("📦 Create New Order")
    
    with st.form("booking_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 👤 Customer Details")
            sender_name = st.text_input("Full Name*", placeholder="Enter customer name")
            sender_phone = st.text_input("Phone Number*", placeholder="923001234567")
            sender_phone2 = st.text_input("Alternate Phone", placeholder="Optional alternate number")
            sender_address = st.text_area("Complete Address", placeholder="Full address with city")
        
        with col2:
            st.markdown("### 📍 Delivery Details")
            receiver_name = st.text_input("Receiver Name*", placeholder="Enter receiver name")
            receiver_phone = st.text_input("Receiver Phone*", placeholder="923001234567")
            receiver_location = st.text_input("Delivery Address*", placeholder="Complete delivery address")
            receiver_city = st.selectbox("Destination City*", 
                ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Hyderabad", "Peshawar", "Quetta"])
        
        st.markdown("### 📋 Product Details")
        col3, col4 = st.columns(2)
        with col3:
            product_name = st.text_input("Product Name*", placeholder="e.g., Rice, Flour, Sugar")
            quantity = st.text_input("Quantity*", placeholder="e.g., 50 bags, 1000 kg, 25 boxes")
        with col4:
            parcel_weight = st.text_input("Weight*", placeholder="e.g., 1000 kg, 500-600 kg, approx 750 kg")
            delivery_type = st.selectbox("Delivery Type", ["Standard (3-5 days)", "Express (1-2 days)", "Same Day"])
            special_instructions = st.text_area("Special Instructions", placeholder="Any special handling requirements")
        
        submitted = st.form_submit_button("🚀 Confirm Order", use_container_width=True)
        
        if submitted:
            if all([sender_name, sender_phone, receiver_name, receiver_phone, receiver_location, product_name, quantity, parcel_weight]):
                booking_data = {
                    'sender_name': sender_name,
                    'sender_phone': sender_phone,
                    'sender_phone2': sender_phone2,
                    'sender_address': sender_address,
                    'receiver_name': receiver_name,
                    'receiver_phone': receiver_phone,
                    'receiver_location': receiver_location,
                    'receiver_city': receiver_city,
                    'product_name': product_name,
                    'quantity': quantity,
                    'parcel_weight': parcel_weight,
                    'delivery_type': delivery_type,
                    'special_instructions': special_instructions
                }
                
                tracking_id = system.add_booking(booking_data)
                
                st.success(f"""
                ✅ **Order Confirmed Successfully!**
                
                **Tracking ID:** {tracking_id}
                **Status:** WhatsApp notifications sent to staff and customer
                **Staff Contact:** Sajjad (+92 317 3037409) has been notified
                **Customer Link:** Limited access tracking link sent to customer
                """)
                
                # Show quick summary
                with st.expander("📋 Order Summary", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Customer:**", sender_name)
                        st.write("**Product:**", product_name)
                        st.write("**Quantity:**", quantity)
                    with col2:
                        st.write("**Weight:**", parcel_weight)
                        st.write("**Destination:**", receiver_city)
                        st.write("**Tracking ID:**", tracking_id)
                
            else:
                st.error("❌ Please fill all required fields (*)")

def show_tracking(system):
    st.subheader("🔍 Track Your Parcel")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tracking_id = st.text_input("Enter Tracking ID", placeholder="NT123456")
        
        if tracking_id:
            if tracking_id in st.session_state.tracking_data:
                booking = next((b for b in st.session_state.bookings if b['tracking_id'] == tracking_id), None)
                
                if booking:
                    st.success("✅ Parcel Found!")
                    
                    # Current status
                    current_status = st.session_state.tracking_data[tracking_id][-1]
                    st.markdown(f"""
                    <div class="card status-transit">
                        <h4>📊 Current Status</h4>
                        <p><strong>🔄 Status:</strong> {current_status['status']}</p>
                        <p><strong>📍 Location:</strong> {current_status['location']}</p>
                        <p><strong>🕒 Last Update:</strong> {current_status['timestamp'].strftime('%d %b %Y %I:%M %p')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Order details
                    st.markdown("### 📦 Order Details")
                    st.write(f"**Product:** {booking['product_name']}")
                    st.write(f"**Quantity:** {booking['quantity']}")
                    st.write(f"**Weight:** {booking['parcel_weight']}")
                    st.write(f"**Customer:** {booking['sender_name']}")
                    st.write(f"**Destination:** {booking['receiver_city']}")
    
    with col2:
        if tracking_id and tracking_id in st.session_state.tracking_data:
            st.markdown("### 📋 Order Timeline")
            
            timeline = sorted(st.session_state.tracking_data[tracking_id], key=lambda x: x['timestamp'])
            
            for update in reversed(timeline):
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

def show_management(system):
    st.subheader("📊 Manage Orders")
    
    if not st.session_state.bookings:
        st.info("No orders available")
        return
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search by Tracking ID, Name, or Product")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Order Received", "Processing", "In Transit", "Delivered"])
    
    # Filter bookings
    filtered_bookings = st.session_state.bookings
    if search_term:
        filtered_bookings = [b for b in filtered_bookings if 
                           search_term.lower() in b['tracking_id'].lower() or
                           search_term.lower() in b['sender_name'].lower() or
                           search_term.lower() in b['product_name'].lower() or
                           search_term.lower() in b['sender_phone']]
    
    if status_filter != "All":
        filtered_bookings = [b for b in filtered_bookings if status_filter in b['status']]
    
    # Display bookings
    for booking in filtered_bookings:
        with st.expander(f"📦 {booking['tracking_id']} - {booking['product_name']} → {booking['receiver_city']}", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write("**Customer:**", booking['sender_name'])
                st.write("**Phone:**", booking['sender_phone'])
                st.write("**Product:**", booking['product_name'])
            
            with col2:
                st.write("**Quantity:**", booking['quantity'])
                st.write("**Weight:**", booking['parcel_weight'])
                st.write("**Destination:**", booking['receiver_city'])
            
            with col3:
                st.write("**Status:**", booking['status'])
                st.write("**Order Date:**", booking['booking_date'].strftime('%d %b %Y'))
                
                # Action buttons
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️ Edit", key=f"edit_{booking['tracking_id']}"):
                        st.session_state.editing = booking['tracking_id']
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_{booking['tracking_id']}"):
                        system.delete_booking(booking['tracking_id'])
                        st.success("Order deleted successfully!")
                        st.experimental_rerun()
    
    # Edit functionality
    if hasattr(st.session_state, 'editing'):
        editing_id = st.session_state.editing
        booking_to_edit = next((b for b in st.session_state.bookings if b['tracking_id'] == editing_id), None)
        
        if booking_to_edit:
            st.markdown("---")
            st.subheader(f"✏️ Edit Order: {editing_id}")
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_sender_name = st.text_input("Customer Name", value=booking_to_edit['sender_name'])
                    new_sender_phone = st.text_input("Customer Phone", value=booking_to_edit['sender_phone'])
                    new_product_name = st.text_input("Product Name", value=booking_to_edit['product_name'])
                
                with col2:
                    new_quantity = st.text_input("Quantity", value=booking_to_edit['quantity'])
                    new_weight = st.text_input("Weight", value=booking_to_edit['parcel_weight'])
                    new_receiver_city = st.text_input("Destination", value=booking_to_edit['receiver_city'])
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 Save Changes"):
                        updated_data = {
                            'sender_name': new_sender_name,
                            'sender_phone': new_sender_phone,
                            'product_name': new_product_name,
                            'quantity': new_quantity,
                            'parcel_weight': new_weight,
                            'receiver_city': new_receiver_city
                        }
                        system.update_booking(editing_id, updated_data)
                        del st.session_state.editing
                        st.success("✅ Order updated successfully!")
                        st.experimental_rerun()
                
                with col_cancel:
                    if st.form_submit_button("❌ Cancel"):
                        del st.session_state.editing
                        st.experimental_rerun()

def show_status_update(system):
    st.subheader("🔄 Update Order Status")
    
    if not st.session_state.bookings:
        st.info("No orders available")
        return
    
    # Select booking to update
    tracking_options = {f"{b['tracking_id']} - {b['product_name']} → {b['receiver_city']}": b['tracking_id'] 
                       for b in st.session_state.bookings}
    
    selected_display = st.selectbox("Select Order", list(tracking_options.keys()))
    tracking_id = tracking_options[selected_display]
    
    if tracking_id:
        booking = next((b for b in st.session_state.bookings if b['tracking_id'] == tracking_id), None)
        
        if booking:
            st.info(f"Current Status: **{booking['status']}**")
            
            # Status update form
            with st.form("status_update"):
                new_status = st.selectbox("New Status", [
                    "Order Received",
                    "Processing at Faisalabad",
                    "Goods Prepared",
                    "Bilty Generated", 
                    "Sent to Multan Warehouse",
                    "Received at Multan Warehouse",
                    "TCS Process Started",
                    "In Transit with TCS",
                    "Out for Delivery",
                    "Delivered",
                    "Attempted - Not Delivered"
                ])
                
                location = st.text_input("Current Location", value=booking.get('current_location', 'Faisalabad Office'))
                description = st.text_area("Status Description", placeholder="Enter detailed status description")
                
                if st.form_submit_button("🔄 Update Status"):
                    system.update_status(tracking_id, new_status, location, description)
                    st.success("✅ Status updated and customer notified!")

def get_status_icon(status):
    icons = {
        "Order Received": "📦",
        "Processing": "⚙️",
        "Goods Prepared": "📦",
        "Bilty Generated": "📄",
        "Sent to Multan": "🚚",
        "Received at Multan": "🏢",
        "TCS Process Started": "🚀",
        "In Transit": "✈️",
        "Out for Delivery": "🚗",
        "Delivered": "✅",
        "Attempted": "🔄"
    }
    for key, icon in icons.items():
        if key in status:
            return icon
    return "📦"

if __name__ == "__main__":
    main()
