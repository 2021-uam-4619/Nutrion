import streamlit as st
import requests
import random
from datetime import datetime
from fpdf import FPDF
import os

# -------------------- Page config --------------------
st.set_page_config(
    page_title="Nutrion Logistics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------- CSS Styling --------------------
st.markdown("""
<style>
    .main-header { font-size:2.5rem; text-align:center; margin-bottom:1rem; padding:1rem;
                   background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color:white; border-radius:10px; }
    .card { padding:1.5rem; border-radius:10px; background:white; box-shadow:0 4px 6px rgba(0,0,0,0.1); margin:0.5rem 0; border-left:4px solid #2E8B57; }
    .btn-primary { background-color:#2E8B57; color:white; padding:0.5rem 1rem; border:none; border-radius:5px; cursor:pointer; }
    .status-delivered { border-left-color: #28a745; }
    .status-transit { border-left-color: #ffc107; }
    .status-pending { border-left-color: #dc3545; }
</style>
""", unsafe_allow_html=True)

# -------------------- WhatsApp API --------------------
class WhatsAppAPI:
    def __init__(self):
        self.base_url = "https://api.ultramsg.com/instance151638/"
        self.token = "xepte100yjisfzv4"
    
    def send_message(self, to, message):
        url = f"{self.base_url}messages/chat"
        payload = {'token': self.token, 'to': to, 'body': message}
        try:
            response = requests.post(url, data=payload)
            return response.status_code == 200
        except:
            return False
    
    def send_document(self, to, document_path, filename):
        url = f"{self.base_url}messages/document"
        files = {'document': (filename, open(document_path, 'rb'))}
        payload = {'token': self.token, 'to': to, 'filename': filename}
        try:
            response = requests.post(url, data=payload, files=files)
            return response.status_code == 200
        except:
            return False

# -------------------- PDF Generator --------------------
class PDFGenerator:
    def create_booking_pdf(self, booking_data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial','B',16)
        pdf.cell(0,10,'Nutrion Logistics - Booking Confirmation',0,1,'C')
        pdf.ln(10)
        pdf.set_font('Arial','B',14)
        pdf.cell(0,10,f'Tracking ID: {booking_data["tracking_id"]}',0,1)
        pdf.ln(5)
        pdf.set_font('Arial','B',12)
        pdf.cell(0,10,'Sender Details:',0,1)
        pdf.set_font('Arial','',11)
        pdf.cell(0,6,f'Name: {booking_data["sender_name"]}',0,1)
        pdf.cell(0,6,f'Phone: {booking_data["sender_phone"]}',0,1)
        if booking_data.get("sender_phone2"):
            pdf.cell(0,6,f'Alternate Phone: {booking_data["sender_phone2"]}',0,1)
        pdf.ln(5)
        pdf.set_font('Arial','B',12)
        pdf.cell(0,10,'Receiver Details:',0,1)
        pdf.set_font('Arial','',11)
        pdf.cell(0,6,f'Name: {booking_data["receiver_name"]}',0,1)
        pdf.cell(0,6,f'Phone: {booking_data["receiver_phone"]}',0,1)
        pdf.cell(0,6,f'Location: {booking_data["receiver_location"]}',0,1)
        pdf.cell(0,6,f'City: {booking_data["receiver_city"]}',0,1)
        pdf.ln(5)
        pdf.set_font('Arial','B',12)
        pdf.cell(0,10,'Service Details:',0,1)
        pdf.set_font('Arial','',11)
        pdf.cell(0,6,f'Booking Date: {booking_data["booking_date"].strftime("%Y-%m-%d %H:%M")}',0,1)
        pdf.cell(0,6,f'Delivery Type: {booking_data["delivery_type"]}',0,1)
        pdf.cell(0,6,f'Pickup Service: {booking_data["pickup_required"]}',0,1)
        pdf.ln(10)
        pdf.set_font('Arial','I',10)
        pdf.cell(0,10,'Thank you for choosing Nutrion Logistics!',0,1,'C')
        filename = f"booking_{booking_data['tracking_id']}.pdf"
        pdf.output(filename)
        return filename

# -------------------- Logistics System --------------------
class LogisticsSystem:
    def __init__(self):
        self.whatsapp = WhatsAppAPI()
        self.pdf_gen = PDFGenerator()
        self.load_data()
    
    def load_data(self):
        if 'bookings' not in st.session_state:
            st.session_state.bookings = []
        if 'tracking_data' not in st.session_state:
            st.session_state.tracking_data = {}
    
    def generate_tracking_id(self):
        return f"NT{random.randint(100000,999999)}"
    
    def add_booking(self, booking_data):
        tracking_id = self.generate_tracking_id()
        booking_data['tracking_id'] = tracking_id
        booking_data['booking_date'] = datetime.now()
        booking_data['status'] = 'Booking Confirmed'
        booking_data['current_location'] = 'Origin Branch'
        st.session_state.bookings.append(booking_data)
        st.session_state.tracking_data[tracking_id] = [{
            'timestamp': datetime.now(),
            'status': 'Booking Confirmed',
            'location': 'Origin Branch',
            'description': 'Parcel booking received and confirmed'
        }]
        self.send_booking_notifications(booking_data)
        return tracking_id
    
    # -------------------- WhatsApp workflow --------------------
    def send_booking_notifications(self, booking_data):
        # Step 1: Staff notification
        staff_msg = f"""🚚 *New Order Received!*
Product: {booking_data.get('product_name','N/A')}
Quantity: {booking_data.get('parcel_weight','N/A')}
Handled by: Sajjad +92 317 3037409"""
        self.whatsapp.send_message("923173037409", staff_msg)

        # Step 2: Client / TCS notification
        client_msg = f"""📦 *Parcel Ready for Dispatch*
Tracking ID: {booking_data['tracking_id']}
Destination: {booking_data['receiver_city']}
Delivery Type: {booking_data['delivery_type']}"""
        self.whatsapp.send_message(booking_data['receiver_phone'], client_msg)
        if booking_data.get('sender_phone2'):
            self.whatsapp.send_message(booking_data['sender_phone2'], client_msg)

        # Step 3: PDF generation
        pdf_file = self.pdf_gen.create_booking_pdf(booking_data)
        self.whatsapp.send_document(booking_data['sender_phone'], pdf_file, f"Booking_{booking_data['tracking_id']}.pdf")
        os.remove(pdf_file)
    
    def update_booking(self, tracking_id, updated_data):
        for i, booking in enumerate(st.session_state.bookings):
            if booking['tracking_id'] == tracking_id:
                st.session_state.bookings[i].update(updated_data)
                return True
        return False
    
    def delete_booking(self, tracking_id):
        st.session_state.bookings = [b for b in st.session_state.bookings if b['tracking_id'] != tracking_id]
        if tracking_id in st.session_state.tracking_data:
            del st.session_state.tracking_data[tracking_id]
    
    def update_status(self, tracking_id, status, location, description):
        if tracking_id in st.session_state.tracking_data:
            st.session_state.tracking_data[tracking_id].append({
                'timestamp': datetime.now(),
                'status': status,
                'location': location,
                'description': description
            })
            for booking in st.session_state.bookings:
                if booking['tracking_id'] == tracking_id:
                    booking['status'] = status
                    booking['current_location'] = location
                    break

# -------------------- Utility --------------------
def get_status_icon(status):
    icons = {
        "Booking Confirmed":"📦","Parcel Collected":"🚚","At Origin Hub":"🏢",
        "In Transit":"✈️","Arrived at Destination":"📍","Out for Delivery":"🚗",
        "Delivered":"✅","Attempted":"🔄"
    }
    for key, icon in icons.items():
        if key in status:
            return icon
    return "📦"

# -------------------- Streamlit Pages --------------------
def main():
    st.markdown('<div class="main-header">🚚 Nutrion Logistics System</div>', unsafe_allow_html=True)
    system = LogisticsSystem()
    
    st.sidebar.title("📋 Navigation")
    menu = st.sidebar.radio("", ["🏠 Dashboard","📦 New Booking","🔍 Track Parcel","📊 Manage Bookings","🔄 Update Status"])
    
    if menu=="🏠 Dashboard": show_dashboard(system)
    elif menu=="📦 New Booking": show_booking_form(system)
    elif menu=="🔍 Track Parcel": show_tracking(system)
    elif menu=="📊 Manage Bookings": show_management(system)
    elif menu=="🔄 Update Status": show_status_update(system)

# -------------------- Dashboard --------------------
def show_dashboard(system):
    st.subheader("📊 Quick Overview")
    total = len(st.session_state.bookings)
    delivered = len([b for b in st.session_state.bookings if 'Delivered' in b.get('status','')])
    in_transit = len([b for b in st.session_state.bookings if 'Transit' in b.get('status','') or 'Hub' in b.get('status','')])
    pending = total - delivered - in_transit
    col1,col2,col3,col4 = st.columns(4)
    col1.metric("Total Bookings", total)
    col2.metric("Delivered", delivered)
    col3.metric("In Transit", in_transit)
    col4.metric("Pending", pending)

# -------------------- Booking Form --------------------
def show_booking_form(system):
    st.subheader("📦 Create New Booking")
    with st.form("booking_form", clear_on_submit=True):
        sender_name = st.text_input("Sender Name*")
        sender_phone = st.text_input("Sender Phone*")
        sender_phone2 = st.text_input("Alternate Phone")
        sender_address = st.text_area("Sender Address")
        receiver_name = st.text_input("Receiver Name*")
        receiver_phone = st.text_input("Receiver Phone*")
        receiver_location = st.text_input("Delivery Address*")
        receiver_city = st.selectbox("Destination City", ["Karachi","Lahore","Islamabad","Rawalpindi","Faisalabad","Multan","Hyderabad","Peshawar","Quetta"])
        pickup_required = st.radio("Pickup Service", ["Customer will drop at branch","Schedule pickup"])
        delivery_type = st.selectbox("Delivery Speed", ["Standard (3-5 days)","Express (1-2 days)","Same Day"])
        parcel_weight = st.text_input("Parcel Weight*", placeholder="e.g. 50 kg or approx. 120 kg")
        product_name = st.text_input("Product Name*")
        special_instructions = st.text_area("Special Instructions")
        
        submitted = st.form_submit_button("🚀 Confirm Booking")
        if submitted:
            if all([sender_name,sender_phone,receiver_name,receiver_phone,receiver_location,product_name]):
                booking_data = {
                    'sender_name': sender_name,'sender_phone': sender_phone,'sender_phone2': sender_phone2,'sender_address': sender_address,
                    'receiver_name': receiver_name,'receiver_phone': receiver_phone,'receiver_location': receiver_location,'receiver_city': receiver_city,
                    'pickup_required': pickup_required,'delivery_type': delivery_type,'parcel_weight': parcel_weight,
                    'product_name': product_name,'special_instructions': special_instructions
                }
                tracking_id = system.add_booking(booking_data)
                st.success(f"✅ Booking Confirmed! Tracking ID: {tracking_id}")
            else:
                st.error("❌ Fill all required fields")

# -------------------- Tracking --------------------
def show_tracking(system):
    st.subheader("🔍 Track Your Parcel")
    tracking_id = st.text_input("Enter Tracking ID")
    if tracking_id and tracking_id in st.session_state.tracking_data:
        for update in st.session_state.tracking_data[tracking_id]:
            st.write(f"{update['timestamp'].strftime('%d %b %Y %I:%M %p')} - {update['status']} - {update['location']}")

# -------------------- Management / Update --------------------
def show_management(system): pass
def show_status_update(system): pass

# -------------------- Run --------------------
if __name__=="__main__":
    main()
