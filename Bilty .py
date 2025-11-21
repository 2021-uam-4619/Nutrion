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
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        text-align: center;
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

class LogisticsSystem:
    def __init__(self):
        self.whatsapp = WhatsAppAPI()
        self.staff_numbers = ["923173037409"]  # Sajjad + other staff numbers
        self.office_city = "Faisalabad"
        self.warehouse_city = "Multan"
        self.load_data()
    
    def load_data(self):
        """Load data from session state"""
        if 'bookings' not in st.session_state:
            st.session_state.bookings = []
        if 'tracking_data' not in st.session_state:
            st.session_state.tracking_data = {}
    
    def generate_tracking_id(self):
        return f"NT{random.randint(100000, 999999)}"
    
    def send_order_to_staff(self, booking_data):
        """Send order details to staff via WhatsApp"""
        message = f"""📦 *NEW ORDER - Nutrion Logistics*

🆔 *Tracking ID:* {booking_data['tracking_id']}
📅 *Order Date:* {booking_data['booking_date'].strftime('%d-%m-%Y %I:%M %p')}

📋 *Product Details:*
🏷️ *Product:* {booking_data['product_name']}
📊 *Quantity:* {booking_data['quantity']}
🏢 *From:* {self.office_city} Office
📭 *To:* {booking_data['receiver_city']}

👤 *Customer Details:*
📛 *Name:* {booking_data['sender_name']}
📞 *Phone:* {booking_data['sender_phone']}

🏠 *Delivery Address:*
{booking_data['receiver_location']}

📝 *Special Instructions:*
{booking_data.get('special_instructions', 'None')}

🚚 *Please prepare the bilty and confirm pickup.*"""

        # Send to all staff numbers
        for staff_number in self.staff_numbers:
            self.whatsapp.send_message(staff_number, message)
    
    def send_bilty_to_customer(self, booking_data, bilty_number):
        """Send bilty confirmation to customer"""
        message = f"""✅ *ORDER CONFIRMED - Nutrion Logistics*

🆔 *Tracking ID:* {booking_data['tracking_id']}
📦 *Bilty Number:* {bilty_number}
📅 *Order Date:* {booking_data['booking_date'].strftime('%d-%m-%Y %I:%M %p')}

📋 *Product:* {booking_data['product_name']}
📊 *Quantity:* {booking_data['quantity']}

🏢 *From:* {self.office_city}
📭 *To:* {booking_data['receiver_city']}

📞 *Contact for updates:* {booking_data['sender_phone']}

🔗 *Track Your Order:*
http://localhost:8501/?tracking={booking_data['tracking_id']}

*Thank you for choosing Nutrion Logistics!*"""

        # Send to customer
        self.whatsapp.send_message(booking_data['sender_phone'], message)
    
    def send_status_update(self, tracking_id, status, description):
        """Send status update to customer"""
        booking = self.get_booking_by_tracking(tracking_id)
        if booking:
            message = f"""🔄 *ORDER UPDATE - Nutrion Logistics*

🆔 *Tracking ID:* {tracking_id}
🔄 *Status:* {status}
📝 *Update:* {description}
📅 *Time:* {datetime.now().strftime('%d-%m-%Y %I:%M %p')}

🔗 *Track Your Order:*
http://localhost:8501/?tracking={tracking_id}"""

            self.whatsapp.send_message(booking['sender_phone'], message)
    
    def add_booking(self, booking_data):
        tracking_id = self.generate_tracking_id()
        booking_data['tracking_id'] = tracking_id
        booking_data['booking_date'] = datetime.now()
        booking_data['status'] = 'Order Received'
        booking_data['current_location'] = f'{self.office_city} Office'
        booking_data['bilty_number'] = None
        
        # Add to bookings
        st.session_state.bookings.append(booking_data)
        
        # Initialize tracking
        st.session_state.tracking_data[tracking_id] = [{
            'timestamp': datetime.now(),
            'status': 'Order Received',
            'location': f'{self.office_city} Office',
            'description': 'Order received at Faisalabad office'
        }]
        
        # Send order to staff
        self.send_order_to_staff(booking_data)
        
        return tracking_id
    
    def update_bilty_number(self, tracking_id, bilty_number):
        """Update bilty number and send confirmation"""
        for booking in st.session_state.bookings:
            if booking['tracking_id'] == tracking_id:
                booking['bilty_number'] = bilty_number
                booking['status'] = 'Bilty Created'
                break
        
        # Add to tracking
        st.session_state.tracking_data[tracking_id].append({
            'timestamp': datetime.now(),
            'status': 'Bilty Created',
            'location': f'{self.office_city} Office',
            'description': f'Bilty number {bilty_number} generated'
        })
        
        # Send bilty to customer
        booking = self.get_booking_by_tracking(tracking_id)
        if booking:
            self.send_bilty_to_customer(booking, bilty_number)
    
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
            
            # Send update to customer
            self.send_status_update(tracking_id, status, description)
    
    def get_booking_by_tracking(self, tracking_id):
        """Get booking by tracking ID"""
        for booking in st.session_state.bookings:
            if booking['tracking_id'] == tracking_id:
                return booking
        return None

def show_limited_tracking(tracking_id):
    """Show limited tracking page for customers"""
    system = LogisticsSystem()
    
    st.markdown('<div class="main-header">🔍 Nutrion - Track Your Order</div>', unsafe_allow_html=True)
    
    booking = system.get_booking_by_tracking(tracking_id)
    
    if not booking:
        st.error("❌ Order not found. Please check your tracking ID.")
        return
    
    # Show basic order info
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📦 Order Information")
        st.write(f"**Tracking ID:** {tracking_id}")
        st.write(f"**Product:** {booking['product_name']}")
        st.write(f"**Quantity:** {booking['quantity']}")
        st.write(f"**Order Date:** {booking['booking_date'].strftime('%d-%m-%Y')}")
    
    with col2:
        st.subheader("👤 Customer Details")
        st.write(f"**Name:** {booking['sender_name']}")
        st.write(f"**Phone:** {booking['sender_phone']}")
        st.write(f"**Destination:** {booking['receiver_city']}")
    
    # Show current status
    current_status = st.session_state.tracking_data[tracking_id][-1]
    status_color = "status-delivered" if "Delivered" in current_status['status'] else "status-transit" if "Transit" in current_status['status'] else "status-pending"
    
    st.markdown(f"""
    <div class="card {status_color}">
        <h3>📊 Current Status</h3>
        <p><strong>🔄 Status:</strong> {current_status['status']}</p>
        <p><strong>📍 Location:</strong> {current_status['location']}</p>
        <p><strong>📝 Description:</strong> {current_status['description']}</p>
        <p><strong>🕒 Last Update:</strong> {current_status['timestamp'].strftime('%d %b %Y %I:%M %p')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Show tracking timeline
    st.subheader("📋 Order Timeline")
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
    
    # Contact information
    st.info("📞 **Contact Support:** +92 317 3037409")

def main_system():
    """Main admin system"""
    system = LogisticsSystem()
    
    st.markdown('<div class="main-header">🚚 Nutrion Logistics System</div>', unsafe_allow_html=True)
    
    # Quick Stats
    total_bookings = len(st.session_state.bookings)
    delivered = len([b for b in st.session_state.bookings if 'Delivered' in b.get('status', '')])
    in_transit = len([b for b in st.session_state.bookings if 'Transit' in b.get('status', '') or 'Hub' in b.get('status', '')])
    pending = total_bookings - delivered - in_transit
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Orders", total_bookings)
    with col2:
        st.metric("Delivered", delivered)
    with col3:
        st.metric("In Transit", in_transit)
    with col4:
        st.metric("Pending", pending)
    
    # Sidebar Navigation
    st.sidebar.title("📋 Navigation")
    menu = st.sidebar.radio("", ["🏠 Dashboard", "📦 New Order", "📋 Manage Orders", "🔄 Update Status", "👥 Staff Management"])
    
    if menu == "🏠 Dashboard":
        show_dashboard(system)
    elif menu == "📦 New Order":
        show_order_form(system)
    elif menu == "📋 Manage Orders":
        show_management(system)
    elif menu == "🔄 Update Status":
        show_status_update(system)
    elif menu == "👥 Staff Management":
        show_staff_management(system)

def show_dashboard(system):
    st.subheader("📊 Quick Overview")
    
    if not st.session_state.bookings:
        st.info("No orders yet. Create your first order to get started!")
        return
    
    # Recent orders
    st.subheader("Recent Orders")
    recent_orders = sorted(st.session_state.bookings, key=lambda x: x['booking_date'], reverse=True)[:5]
    
    for order in recent_orders:
        with st.container():
            col1, col2, col3, col4 = st.columns([2,2,1,1])
            with col1:
                st.write(f"**{order['tracking_id']}**")
                st.write(f"🏷️ {order['product_name']} - {order['quantity']}")
            with col2:
                st.write(f"👤 {order['sender_name']}")
                st.write(f"📍 {order['receiver_city']}")
            with col3:
                status_color = "status-delivered" if "Delivered" in order['status'] else "status-transit" if "Transit" in order['status'] else "status-pending"
                st.markdown(f'<div class="card {status_color}">{order["status"]}</div>', unsafe_allow_html=True)
            with col4:
                if st.button("📋", key=f"view_{order['tracking_id']}"):
                    st.session_state.current_tracking = order['tracking_id']

def show_order_form(system):
    st.subheader("📦 Create New Order")
    
    with st.form("order_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 👤 Customer Details")
            sender_name = st.text_input("Full Name*", placeholder="Enter customer name")
            sender_phone = st.text_input("Phone Number*", placeholder="923001234567")
            
            st.markdown("### 🏷️ Product Details")
            product_name = st.text_input("Product Name*", placeholder="Enter product name")
            quantity = st.text_input("Quantity*", placeholder="e.g., 50 kg, 2 bags, 100-120 kg")
        
        with col2:
            st.markdown("### 📍 Delivery Details")
            receiver_name = st.text_input("Receiver Name*", placeholder="Enter receiver name")
            receiver_phone = st.text_input("Receiver Phone", placeholder="Optional")
            receiver_location = st.text_area("Delivery Address*", placeholder="Complete delivery address with landmarks")
            receiver_city = st.selectbox("Destination City*", 
                ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Hyderabad", "Peshawar", "Quetta"])
        
        special_instructions = st.text_area("Special Instructions", placeholder="Any special handling requirements")
        
        submitted = st.form_submit_button("🚀 Create Order & Send to Staff", use_container_width=True)
        
        if submitted:
            if all([sender_name, sender_phone, product_name, quantity, receiver_name, receiver_location]):
                order_data = {
                    'sender_name': sender_name,
                    'sender_phone': sender_phone,
                    'product_name': product_name,
                    'quantity': quantity,
                    'receiver_name': receiver_name,
                    'receiver_phone': receiver_phone,
                    'receiver_location': receiver_location,
                    'receiver_city': receiver_city,
                    'special_instructions': special_instructions
                }
                
                tracking_id = system.add_booking(order_data)
                
                st.success(f"""
                ✅ **Order Created Successfully!**
                
                **Tracking ID:** {tracking_id}
                **Status:** Order details sent to staff via WhatsApp
                **Next Step:** Staff will prepare bilty and confirm
                """)
                
                # Show quick summary
                with st.expander("📋 Order Summary", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Customer:**", sender_name)
                        st.write("**Phone:**", sender_phone)
                        st.write("**Product:**", product_name)
                    with col2:
                        st.write("**Quantity:**", quantity)
                        st.write("**Destination:**", receiver_city)
                        st.write("**Staff Notified:**", "✅ Yes")
                
            else:
                st.error("❌ Please fill all required fields (*)")

def show_management(system):
    st.subheader("📋 Manage Orders")
    
    if not st.session_state.bookings:
        st.info("No orders available")
        return
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search by Tracking ID, Name, or Phone")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Order Received", "Bilty Created", "In Transit", "Delivered"])
    
    # Filter orders
    filtered_orders = st.session_state.bookings
    if search_term:
        filtered_orders = [b for b in filtered_orders if 
                         search_term.lower() in b['tracking_id'].lower() or
                         search_term.lower() in b['sender_name'].lower() or
                         search_term.lower() in b['sender_phone']]
    
    if status_filter != "All":
        filtered_orders = [b for b in filtered_orders if status_filter in b['status']]
    
    # Display orders
    for order in filtered_orders:
        with st.expander(f"📦 {order['tracking_id']} - {order['product_name']} → {order['receiver_city']}", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write("**Customer:**", order['sender_name'])
                st.write("**Phone:**", order['sender_phone'])
                st.write("**Product:**", order['product_name'])
            
            with col2:
                st.write("**Quantity:**", order['quantity'])
                st.write("**Destination:**", order['receiver_city'])
                st.write("**Bilty No:**", order.get('bilty_number', 'Not created'))
            
            with col3:
                st.write("**Status:**", order['status'])
                st.write("**Location:**", order.get('current_location', 'N/A'))
                
                # Add bilty number if not exists
                if not order.get('bilty_number'):
                    bilty_no = st.text_input("Enter Bilty No", key=f"bilty_{order['tracking_id']}")
                    if st.button("✅ Add Bilty", key=f"add_bilty_{order['tracking_id']}"):
                        if bilty_no:
                            system.update_bilty_number(order['tracking_id'], bilty_no)
                            st.success("Bilty number added!")
                            st.experimental_rerun()
                        else:
                            st.error("Please enter bilty number")

def show_status_update(system):
    st.subheader("🔄 Update Order Status")
    
    if not st.session_state.bookings:
        st.info("No orders available")
        return
    
    # Select order to update
    order_options = {f"{b['tracking_id']} - {b['product_name']} → {b['receiver_city']}": b['tracking_id'] 
                   for b in st.session_state.bookings}
    
    selected_display = st.selectbox("Select Order", list(order_options.keys()))
    tracking_id = order_options[selected_display]
    
    if tracking_id:
        order = system.get_booking_by_tracking(tracking_id)
        
        if order:
            st.info(f"Current Status: **{order['status']}**")
            
            # Status update form
            with st.form("status_update"):
                new_status = st.selectbox("New Status", [
                    "Order Received at Office",
                    "Sent to Multan Warehouse", 
                    "Bilty Created",
                    "Handed to TCS",
                    "In Transit with TCS",
                    "At TCS Destination Hub",
                    "Out for Delivery",
                    "Delivered Successfully",
                    "Delivery Attempted - Not Delivered"
                ])
                
                location = st.text_input("Current Location", value=order.get('current_location', 'Faisalabad Office'))
                description = st.text_area("Status Description", placeholder="Enter detailed status description")
                
                if st.form_submit_button("🔄 Update Status & Notify Customer"):
                    system.update_status(tracking_id, new_status, location, description)
                    st.success("✅ Status updated and customer notified!")

def show_staff_management(system):
    st.subheader("👥 Staff Management")
    
    st.info("**Current Staff Numbers for Order Notifications:**")
    for i, number in enumerate(system.staff_numbers, 1):
        st.write(f"{i}. {number}")
    
    # Add new staff number
    st.subheader("Add New Staff Number")
    new_number = st.text_input("Enter new staff number (with country code)", placeholder="923173037409")
    
    if st.button("Add Staff Number"):
        if new_number and new_number not in system.staff_numbers:
            system.staff_numbers.append(new_number)
            st.success(f"Staff number {new_number} added successfully!")
        else:
            st.error("Please enter a valid number")
    
    # Test WhatsApp
    st.subheader("Test WhatsApp Integration")
    test_number = st.text_input("Test number", placeholder="923001234567")
    test_message = st.text_area("Test message", value="Test message from Nutrion Logistics System")
    
    if st.button("Send Test Message"):
        if system.whatsapp.send_message(test_number, test_message):
            st.success("✅ Test message sent successfully!")
        else:
            st.error("❌ Failed to send test message")

def get_status_icon(status):
    icons = {
        "Order Received": "📦",
        "Bilty Created": "📄",
        "Sent to Warehouse": "🚚",
        "Handed to TCS": "📦",
        "In Transit": "✈️",
        "At Hub": "🏢",
        "Out for Delivery": "🚗",
        "Delivered": "✅",
        "Attempted": "🔄"
    }
    for key, icon in icons.items():
        if key in status:
            return icon
    return "📦"

def main():
    # Check if limited access (customer tracking)
    query_params = st.experimental_get_query_params()
    tracking_id = query_params.get("tracking", [None])[0]
    
    if tracking_id:
        # Show limited tracking page for customers
        show_limited_tracking(tracking_id)
    else:
        # Show full admin system
        main_system()

if __name__ == "__main__":
    main()
