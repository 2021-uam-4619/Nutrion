import streamlit as st
import pandas as pd
import datetime
import random
import time
from datetime import datetime, timedelta

# Page configuration
st.set_page_config(
    page_title="Nutrion Logistics System",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2E8B57;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .status-card {
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        background-color: #f9f9f9;
        margin: 0.5rem 0;
    }
    .delivered {
        border-left-color: #28a745;
    }
    .in-transit {
        border-left-color: #ffc107;
    }
    .pending {
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

class NutrionLogisticsSystem:
    def __init__(self):
        self.bookings = []
        self.tracking_data = {}
        self.products = [
            "Vitamin A Premix", "Mineral Supplement", "Antioxidants", 
            "Probiotics", "Enzymes", "Amino Acids", "Antibiotics Alternative",
            "Growth Promoters", "Pellet Binders", "Flavor Enhancers"
        ]
        
    def generate_tracking_id(self):
        return f"NT{random.randint(100000, 999999)}"
    
    def add_booking(self, booking_data):
        tracking_id = self.generate_tracking_id()
        booking_data['tracking_id'] = tracking_id
        booking_data['booking_date'] = datetime.now()
        booking_data['status'] = 'Booked'
        booking_data['current_location'] = 'Origin Branch'
        
        # Initialize tracking history
        self.tracking_data[tracking_id] = [{
            'timestamp': datetime.now(),
            'status': 'Booking Confirmed',
            'location': 'Origin Branch',
            'description': 'Parcel booking received and confirmed'
        }]
        
        self.bookings.append(booking_data)
        return tracking_id
    
    def update_status(self, tracking_id, status, location, description):
        if tracking_id in self.tracking_data:
            self.tracking_data[tracking_id].append({
                'timestamp': datetime.now(),
                'status': status,
                'location': location,
                'description': description
            })
            
            # Update booking status
            for booking in self.bookings:
                if booking['tracking_id'] == tracking_id:
                    booking['status'] = status
                    booking['current_location'] = location
                    break
    
    def simulate_delivery_process(self, tracking_id):
        """Simulate the complete delivery process"""
        status_updates = [
            ("Parcel Collected", "Origin Branch", "Rider has collected the parcel"),
            ("At Origin Hub", "Origin Sorting Center", "Parcel scanned at origin hub"),
            ("In Transit", "Line Haul", "Parcel moving to destination city"),
            ("Arrived at Destination", "Destination Hub", "Parcel scanned at destination hub"),
            ("Out for Delivery", "Local Delivery", "Rider has parcel for final delivery"),
            ("Delivered", "Customer Location", "Parcel successfully delivered")
        ]
        
        current_time = datetime.now()
        for status, location, description in status_updates:
            time.sleep(1)  # Simulate time delay
            current_time += timedelta(hours=2)  # Add 2 hours between each update
            
            update_data = {
                'timestamp': current_time,
                'status': status,
                'location': location,
                'description': description
            }
            
            if tracking_id not in self.tracking_data:
                self.tracking_data[tracking_id] = []
            
            self.tracking_data[tracking_id].append(update_data)
            
            # Update booking status
            for booking in self.bookings:
                if booking['tracking_id'] == tracking_id:
                    booking['status'] = status
                    booking['current_location'] = location
                    break

# Initialize session state
if 'logistics_system' not in st.session_state:
    st.session_state.logistics_system = NutrionLogisticsSystem()

def main():
    # Header
    st.markdown('<div class="main-header">🚚 Nutrion Feed Additives Logistics System</div>', unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/1005/1005141.png", width=100)
    st.sidebar.title("Navigation")
    menu = st.sidebar.radio("Go to", ["New Booking", "Track Parcel", "Manage Deliveries", "Reports"])
    
    logistics_system = st.session_state.logistics_system
    
    if menu == "New Booking":
        show_booking_form(logistics_system)
    elif menu == "Track Parcel":
        show_tracking_system(logistics_system)
    elif menu == "Manage Deliveries":
        show_management_system(logistics_system)
    elif menu == "Reports":
        show_reports(logistics_system)

def show_booking_form(logistics_system):
    st.markdown('<div class="section-header">📦 New Parcel Booking</div>', unsafe_allow_html=True)
    
    with st.form("booking_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Sender Details")
            sender_name = st.text_input("Sender Name*")
            sender_phone = st.text_input("Phone No*")
            sender_phone2 = st.text_input("Alternate Phone No (Optional)")
            sender_address = st.text_area("Sender Address")
            
            st.subheader("Product Details")
            product_name = st.selectbox("Product Name*", logistics_system.products)
            quantity = st.number_input("Quantity (kg)*", min_value=1, max_value=1000, value=10)
            special_instructions = st.text_area("Special Handling Instructions")
        
        with col2:
            st.subheader("Receiver Details")
            receiver_name = st.text_input("Receiver Name*")
            receiver_phone = st.text_input("Receiver Phone No*")
            receiver_phone2 = st.text_input("Receiver Alternate Phone No")
            receiver_location = st.text_input("Delivery Location*")
            receiver_city = st.selectbox("City*", ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Hyderabad", "Peshawar", "Quetta"])
            
            st.subheader("Service Options")
            pickup_required = st.radio("Pickup Service", ["Customer will drop at branch", "Schedule pickup"])
            delivery_type = st.selectbox("Delivery Type", ["Standard (3-5 days)", "Express (1-2 days)", "Same Day"])
            insurance_required = st.checkbox("Add Insurance Coverage")
        
        # Form submission
        submitted = st.form_submit_button("Book Parcel")
        
        if submitted:
            if sender_name and sender_phone and receiver_name and receiver_phone and receiver_location:
                booking_data = {
                    'sender_name': sender_name,
                    'sender_phone': sender_phone,
                    'sender_phone2': sender_phone2,
                    'sender_address': sender_address,
                    'product_name': product_name,
                    'quantity': quantity,
                    'special_instructions': special_instructions,
                    'receiver_name': receiver_name,
                    'receiver_phone': receiver_phone,
                    'receiver_phone2': receiver_phone2,
                    'receiver_location': receiver_location,
                    'receiver_city': receiver_city,
                    'pickup_required': pickup_required,
                    'delivery_type': delivery_type,
                    'insurance_required': insurance_required
                }
                
                tracking_id = logistics_system.add_booking(booking_data)
                
                st.success(f"✅ Booking Confirmed! Tracking ID: {tracking_id}")
                
                # Show booking summary
                st.subheader("Booking Summary")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Sender:**", sender_name)
                    st.write("**Product:**", product_name)
                    st.write("**Quantity:**", f"{quantity} kg")
                    st.write("**From:**", sender_address or "Branch Drop-off")
                
                with col2:
                    st.write("**Receiver:**", receiver_name)
                    st.write("**Delivery To:**", receiver_location)
                    st.write("**City:**", receiver_city)
                    st.write("**Service:**", delivery_type)
                
                # Simulate sending WhatsApp notifications
                st.info("📱 WhatsApp notifications sent to:")
                if sender_phone:
                    st.write(f"- {sender_phone} (Sender)")
                if sender_phone2:
                    st.write(f"- {sender_phone2} (Sender Alternate)")
                if receiver_phone:
                    st.write(f"- {receiver_phone} (Receiver)")
                if receiver_phone2:
                    st.write(f"- {receiver_phone2} (Receiver Alternate)")
                
                st.warning("🔔 Parcel status updates will be sent via WhatsApp at each stage of delivery.")
                
            else:
                st.error("Please fill all required fields (*)")

def show_tracking_system(logistics_system):
    st.markdown('<div class="section-header">🔍 Track Your Parcel</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        tracking_id = st.text_input("Enter Tracking ID", placeholder="e.g., NT123456")
        track_btn = st.button("Track Parcel")
        
        if track_btn and tracking_id:
            if tracking_id in logistics_system.tracking_data:
                # Find booking details
                booking_details = None
                for booking in logistics_system.bookings:
                    if booking['tracking_id'] == tracking_id:
                        booking_details = booking
                        break
                
                if booking_details:
                    st.success("Parcel Found!")
                    
                    # Display current status
                    current_status = logistics_system.tracking_data[tracking_id][-1]
                    status_class = "delivered" if "Delivered" in current_status['status'] else "in-transit"
                    
                    st.markdown(f"""
                    <div class="status-card {status_class}">
                        <h4>Current Status: {current_status['status']}</h4>
                        <p><strong>Location:</strong> {current_status['location']}</p>
                        <p><strong>Last Update:</strong> {current_status['timestamp'].strftime('%Y-%m-%d %H:%M')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Booking details
                    st.subheader("Parcel Details")
                    st.write(f"**Product:** {booking_details['product_name']}")
                    st.write(f"**Quantity:** {booking_details['quantity']} kg")
                    st.write(f"**Sender:** {booking_details['sender_name']}")
                    st.write(f"**Receiver:** {booking_details['receiver_name']}")
                    st.write(f"**Destination:** {booking_details['receiver_city']}")
            
            else:
                st.error("Invalid Tracking ID. Please check and try again.")
    
    with col2:
        if track_btn and tracking_id and tracking_id in logistics_system.tracking_data:
            st.subheader("Delivery Timeline")
            
            # Display tracking history
            tracking_history = sorted(logistics_system.tracking_data[tracking_id], 
                                    key=lambda x: x['timestamp'])
            
            for i, update in enumerate(tracking_history):
                status_icon = "✅" if "Delivered" in update['status'] else "🔄"
                if "Booked" in update['status']:
                    status_icon = "📦"
                elif "Collected" in update['status']:
                    status_icon = "🚚"
                elif "In Transit" in update['status']:
                    status_icon = "✈️"
                
                st.markdown(f"""
                <div class="status-card">
                    <div style="display: flex; justify-content: between; align-items: center;">
                        <div>
                            <strong>{status_icon} {update['status']}</strong>
                            <br>
                            <small>{update['location']}</small>
                            <br>
                            <small>{update['description']}</small>
                        </div>
                        <div style="text-align: right;">
                            <small>{update['timestamp'].strftime('%b %d, %Y %H:%M')}</small>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

def show_management_system(logistics_system):
    st.markdown('<div class="section-header">📊 Delivery Management</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Active Deliveries", "Update Status", "Quick Actions"])
    
    with tab1:
        if logistics_system.bookings:
            st.subheader(f"Active Parcels ({len(logistics_system.bookings)})")
            
            # Create DataFrame for better display
            delivery_data = []
            for booking in logistics_system.bookings:
                delivery_data.append({
                    'Tracking ID': booking['tracking_id'],
                    'Product': booking['product_name'],
                    'Quantity': f"{booking['quantity']} kg",
                    'Sender': booking['sender_name'],
                    'Receiver': booking['receiver_name'],
                    'Destination': booking['receiver_city'],
                    'Status': booking['status'],
                    'Current Location': booking['current_location'],
                    'Booking Date': booking['booking_date'].strftime('%Y-%m-%d')
                })
            
            df = pd.DataFrame(delivery_data)
            st.dataframe(df, use_container_width=True)
            
            # Status summary
            st.subheader("Status Overview")
            status_counts = df['Status'].value_counts()
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Bookings", len(logistics_system.bookings))
            with col2:
                delivered_count = len([b for b in logistics_system.bookings if "Delivered" in b['status']])
                st.metric("Delivered", delivered_count)
            with col3:
                in_transit = len([b for b in logistics_system.bookings if "Transit" in b['status'] or "Hub" in b['status']])
                st.metric("In Transit", in_transit)
            with col4:
                pending = len([b for b in logistics_system.bookings if "Booked" in b['status'] or "Collected" in b['status']])
                st.metric("Pending", pending)
        
        else:
            st.info("No active deliveries found.")
    
    with tab2:
        st.subheader("Update Parcel Status")
        
        if logistics_system.bookings:
            tracking_ids = [booking['tracking_id'] for booking in logistics_system.bookings]
            selected_tracking = st.selectbox("Select Parcel", tracking_ids)
            
            # Get current status
            current_status = ""
            for booking in logistics_system.bookings:
                if booking['tracking_id'] == selected_tracking:
                    current_status = booking['status']
                    break
            
            st.write(f"Current Status: **{current_status}**")
            
            # Status update options
            new_status = st.selectbox("New Status", [
                "Parcel Collected",
                "At Origin Hub", 
                "In Transit",
                "Arrived at Destination",
                "Out for Delivery",
                "Delivered",
                "Attempted - Not Delivered"
            ])
            
            location = st.text_input("Current Location", value="Origin Branch")
            description = st.text_area("Status Description")
            
            if st.button("Update Status"):
                logistics_system.update_status(selected_tracking, new_status, location, description)
                st.success(f"Status updated for {selected_tracking}")
                
                # Show updated tracking info
                if selected_tracking in logistics_system.tracking_data:
                    latest = logistics_system.tracking_data[selected_tracking][-1]
                    st.info(f"Latest: {latest['status']} at {latest['location']}")
        
        else:
            st.info("No parcels to update.")
    
    with tab3:
        st.subheader("Quick Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Simulate All Deliveries"):
                for booking in logistics_system.bookings:
                    if "Delivered" not in booking['status']:
                        logistics_system.simulate_delivery_process(booking['tracking_id'])
                st.success("All deliveries simulation completed!")
            
            if st.button("📱 Send Status Updates"):
                st.info("WhatsApp notifications sent for all pending updates")
        
        with col2:
            if st.button("📊 Generate Daily Report"):
                st.info("Daily report generated and sent to management")
            
            if st.button("🔄 Refresh All Data"):
                st.experimental_rerun()

def show_reports(logistics_system):
    st.markdown('<div class="section-header">📈 Reports & Analytics</div>', unsafe_allow_html=True)
    
    if not logistics_system.bookings:
        st.info("No data available for reports.")
        return
    
    # Create analytics data
    delivery_data = []
    for booking in logistics_system.bookings:
        delivery_data.append({
            'tracking_id': booking['tracking_id'],
            'product': booking['product_name'],
            'quantity': booking['quantity'],
            'city': booking['receiver_city'],
            'status': booking['status'],
            'booking_date': booking['booking_date'].date()
        })
    
    df = pd.DataFrame(delivery_data)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Deliveries by City")
        city_counts = df['city'].value_counts()
        st.bar_chart(city_counts)
    
    with col2:
        st.subheader("Product Distribution")
        product_counts = df['product'].value_counts()
        st.bar_chart(product_counts)
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Status Distribution")
        status_counts = df['status'].value_counts()
        st.dataframe(status_counts)
    
    with col4:
        st.subheader("Daily Bookings")
        daily_bookings = df.groupby('booking_date').size()
        st.line_chart(daily_bookings)
    
    # Detailed report
    st.subheader("Detailed Delivery Report")
    report_df = df.copy()
    st.dataframe(report_df, use_container_width=True)
    
    # Export options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Export to CSV"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"nutrion_delivery_report_{datetime.now().date()}.csv",
                mime="text/csv"
            )
    
    with col2:
        if st.button("📊 Generate Performance Report"):
            st.success("Performance report generated!")
            total_deliveries = len(df)
            delivered = len(df[df['status'] == 'Delivered'])
            delivery_rate = (delivered / total_deliveries * 100) if total_deliveries > 0 else 0
            
            st.metric("Total Deliveries", total_deliveries)
            st.metric("Success Rate", f"{delivery_rate:.1f}%")
            st.metric("Average Quantity", f"{df['quantity'].mean():.1f} kg")
    
    with col3:
        if st.button("🔄 Refresh Reports"):
            st.experimental_rerun()

if __name__ == "__main__":
    main()
