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
from PIL import Image
import io

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
    .status-process { border-left-color: #17a2b8; }
    .status-bilty { border-left-color: #6f42c1; }
    .status-receiver { border-left-color: #fd7e14; }
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
    .logo-container {
        text-align: center;
        margin-bottom: 1rem;
    }
    .logo-img {
        max-width: 200px;
        max-height: 80px;
    }
    .download-btn {
        background-color: #28a745;
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 1rem;
        margin: 0.5rem;
        display: inline-block;
        text-decoration: none;
    }
    .download-btn:hover {
        background-color: #218838;
    }
    .phone-input {
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

class WhatsAppAPI:
    def __init__(self):
        self.base_url = "https://api.ultramsg.com/instance151638/"
        self.token = "xepte100yjisfzv4"
    
    def send_message(self, to, message):
        """Send WhatsApp message"""
        # Clean phone number
        to = self.clean_phone_number(to)
        
        url = f"{self.base_url}messages/chat"
        payload = {
            'token': self.token,
            'to': to,
            'body': message
        }
        try:
            response = requests.post(url, data=payload)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Failed to send WhatsApp message: {str(e)}")
            return False
    
    def send_document(self, to, document_path, filename):
        """Send PDF document via WhatsApp"""
        # Clean phone number
        to = self.clean_phone_number(to)
        
        url = f"{self.base_url}messages/document"
        try:
            files = {
                'document': (filename, open(document_path, 'rb'))
            }
            payload = {
                'token': self.token,
                'to': to,
                'filename': filename
            }
            response = requests.post(url, data=payload, files=files)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Failed to send document: {str(e)}")
            return False
    
    def send_image(self, to, image_path, caption=""):
        """Send image via WhatsApp"""
        # Clean phone number
        to = self.clean_phone_number(to)
        
        url = f"{self.base_url}messages/image"
        try:
            files = {
                'image': open(image_path, 'rb')
            }
            payload = {
                'token': self.token,
                'to': to,
                'caption': caption
            }
            response = requests.post(url, data=payload, files=files)
            return response.status_code == 200
        except Exception as e:
            st.error(f"Failed to send image: {str(e)}")
            return False
    
    def clean_phone_number(self, phone):
        """Clean and format phone number"""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # If starts with 0, replace with 92
        if phone.startswith('0'):
            phone = '92' + phone[1:]
        
        # If doesn't start with country code, add 92
        if not phone.startswith('92'):
            phone = '92' + phone
        
        # Add + prefix for WhatsApp
        return f"+{phone}"

class PDFGenerator:
    def create_bilty_pdf(self, bilty_data):
        """Create professional bilty PDF"""
        pdf = FPDF()
        pdf.add_page()
        
        # Title with border
        pdf.set_fill_color(46, 139, 87)  # Green color
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 18)
        pdf.cell(0, 15, 'Nutrion Logistics - Bilty Document', 1, 1, 'C', True)
        pdf.ln(10)
        
        # Reset text color
        pdf.set_text_color(0, 0, 0)
        
        # Bilty ID
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f'BILTY ID: {bilty_data["bilty_id"]}', 0, 1, 'C')
        pdf.ln(5)
        
        # Section 1: From Details
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'FROM (SENDER)', 1, 1, 'L', True)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f'Company: Nutrion Logistics', 0, 1)
        pdf.cell(0, 8, f'Product: {bilty_data["product_name"]}', 0, 1)
        pdf.cell(0, 8, f'Quantity: {bilty_data["quantity"]}', 0, 1)
        pdf.ln(5)
        
        # Section 2: To Details
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'TO (RECEIVER)', 1, 1, 'L', True)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f'Name: {bilty_data["receiver_name"]}', 0, 1)
        pdf.cell(0, 8, f'Phone: {bilty_data["receiver_phone"]}', 0, 1)
        pdf.cell(0, 8, f'Location: {bilty_data["receiver_location"]}', 0, 1)
        pdf.cell(0, 8, f'City: {bilty_data["receiver_city"]}', 0, 1)
        pdf.ln(5)
        
        # Section 3: Delivery Information
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'DELIVERY INFORMATION', 1, 1, 'L', True)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f'Approximate Delivery: {bilty_data["approx_delivery"]}', 0, 1)
        pdf.cell(0, 8, f'Bilty Created: {bilty_data["created_at"].strftime("%d-%m-%Y %H:%M")}', 0, 1)
        pdf.ln(5)
        
        # Section 4: Contact Information
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'CONTACT INFORMATION', 1, 1, 'L', True)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, f'Staff Contact: {bilty_data["staff_phone"]}', 0, 1)
        pdf.cell(0, 8, f'For Queries: Contact the above number', 0, 1)
        pdf.ln(10)
        
        # Terms and Conditions
        pdf.set_font('Arial', 'I', 10)
        pdf.multi_cell(0, 6, 'Terms & Conditions: This bilty is generated by Nutrion Logistics System. Please verify all details before acceptance. For any discrepancies, contact our staff immediately.')
        pdf.ln(5)
        
        # Footer
        pdf.set_font('Arial', 'I', 9)
        pdf.cell(0, 10, 'Generated by Nutrion Logistics System - Trusted Logistics Partner', 0, 1, 'C')
        
        # Save to bytes
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        return pdf_bytes
    
    def create_detailed_bilty_pdf(self, bilty_data, order_data):
        """Create a more detailed bilty PDF"""
        pdf = FPDF()
        pdf.add_page()
        
        # Header with logo space
        pdf.set_fill_color(46, 139, 87)  # Nutrion Green
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Arial', 'B', 20)
        pdf.cell(0, 20, 'NUTRION LOGISTICS', 1, 1, 'C', True)
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 12, 'OFFICIAL BILTY DOCUMENT', 1, 1, 'C', True)
        pdf.ln(5)
        
        # Reset text color
        pdf.set_text_color(0, 0, 0)
        
        # Document Details
        col_width = 95
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(col_width, 10, f'Bilty ID: {bilty_data["bilty_id"]}', 0, 0)
        pdf.cell(col_width, 10, f'Order ID: {bilty_data["order_id"]}', 0, 1)
        pdf.cell(col_width, 10, f'Date: {bilty_data["created_at"].strftime("%d-%m-%Y")}', 0, 0)
        pdf.cell(col_width, 10, f'Time: {bilty_data["created_at"].strftime("%H:%M")}', 0, 1)
        pdf.ln(10)
        
        # Sender Section
        self._add_section(pdf, "SENDER DETAILS", [
            "Company: Nutrion Logistics",
            f"Product: {order_data['product_name']}",
            f"Quantity: {order_data['quantity']}",
            "Status: Ready for Dispatch"
        ])
        
        # Receiver Section
        self._add_section(pdf, "RECEIVER DETAILS", [
            f"Name: {bilty_data['receiver_name']}",
            f"Phone: {bilty_data['receiver_phone']}",
            f"Address: {bilty_data['receiver_location']}",
            f"City: {bilty_data['receiver_city']}"
        ])
        
        # Delivery Information
        self._add_section(pdf, "DELIVERY INFORMATION", [
            f"Expected Delivery: {bilty_data['approx_delivery']}",
            f"Contact Person: {bilty_data['receiver_name']}",
            f"Contact Number: {bilty_data['receiver_phone']}",
            "Delivery Instructions: Contact before delivery"
        ])
        
        # Staff Contact
        self._add_section(pdf, "STAFF CONTACT", [
            f"Responsible Staff: {bilty_data.get('staff_name', 'Nutrion Staff')}",
            f"Contact Number: {bilty_data['staff_phone']}",
            "Department: Logistics & Dispatch",
            "Email: info@nutrion.com"
        ])
        
        # Signature Area
        pdf.ln(10)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, 'AUTHORIZED SIGNATURES', 0, 1)
        pdf.ln(8)
        
        # Sender Signature
        pdf.cell(85, 6, 'Sender Signature:', 0, 0)
        pdf.cell(85, 6, 'Receiver Signature:', 0, 1)
        pdf.cell(85, 20, '', 'B', 0)
        pdf.cell(85, 20, '', 'B', 1)
        
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 9)
        pdf.multi_cell(0, 5, 'This is a computer generated bilty. No physical signature is required. Please verify all details and contact staff for any corrections.')
        
        pdf_bytes = pdf.output(dest='S').encode('latin1')
        return pdf_bytes
    
    def _add_section(self, pdf, title, items):
        """Helper method to add consistent sections"""
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, title, 1, 1, 'L', True)
        pdf.set_font('Arial', '', 11)
        for item in items:
            pdf.cell(0, 7, item, 0, 1)
        pdf.ln(3)

class LogisticsSystem:
    def __init__(self):
        self.whatsapp = WhatsAppAPI()
        self.pdf_gen = PDFGenerator()
        self.load_data()
    
    def load_data(self):
        """Load data from session state"""
        if 'orders' not in st.session_state:
            st.session_state.orders = []
        if 'bilty_data' not in st.session_state:
            st.session_state.bilty_data = {}
        if 'tracking_data' not in st.session_state:
            st.session_state.tracking_data = {}
    
    def generate_order_id(self):
        return f"ORD{random.randint(100000, 999999)}"
    
    def generate_bilty_id(self):
        return f"BIL{random.randint(100000, 999999)}"
    
    def add_order(self, order_data):
        """Step 1: Add new order"""
        order_id = self.generate_order_id()
        order_data['order_id'] = order_id
        order_data['created_at'] = datetime.now()
        order_data['status'] = 'Under Process'
        
        # Add to orders
        st.session_state.orders.append(order_data)
        
        # Initialize tracking
        st.session_state.tracking_data[order_id] = [{
            'timestamp': datetime.now(),
            'status': 'Under Process',
            'description': 'New order received and processing started'
        }]
        
        # Send WhatsApp to staff
        self.send_order_notification(order_data)
        
        return order_id
    
    def send_order_notification(self, order_data):
        """Send WhatsApp message to staff for new order"""
        staff_message = f"""📦 *NEW ORDER RECEIVED - Nutrion Logistics*

🆔 *Order ID:* {order_data['order_id']}
📅 *Order Date:* {order_data['created_at'].strftime('%d %b %Y %I:%M %p')}

📋 *Product Details:*
🏷️ *Product Name:* {order_data['product_name']}
📊 *Quantity:* {order_data['quantity']}

🔄 *Status:* Under Process
📍 *Next Step:* Proceed to Bilty Process

*Please prepare the goods and generate bilty.*"""

        # Ask user which staff to send to
        st.info("📤 Ready to send order notification to staff")
        col1, col2 = st.columns(2)
        with col1:
            staff_phone = st.text_input("Enter staff phone number to notify:", 
                                      value="+923207429422",
                                      key="staff_notify_phone")
        with col2:
            if st.button("📤 Send Order Notification", key="send_order_notif"):
                if staff_phone:
                    success = self.whatsapp.send_message(staff_phone, staff_message)
                    if success:
                        st.success(f"✅ Order notification sent to {staff_phone}")
                    else:
                        st.error("❌ Failed to send notification")
                else:
                    st.warning("⚠️ Please enter a phone number")
    
    def create_bilty(self, order_id, bilty_data):
        """Step 2: Create bilty process"""
        bilty_id = self.generate_bilty_id()
        bilty_data['bilty_id'] = bilty_id
        bilty_data['order_id'] = order_id
        bilty_data['created_at'] = datetime.now()
        bilty_data['status'] = 'Bilty Process'
        
        # Store bilty data
        st.session_state.bilty_data[order_id] = bilty_data
        
        # Update order status
        for order in st.session_state.orders:
            if order['order_id'] == order_id:
                order['status'] = 'Bilty Process'
                break
        
        # Update tracking
        st.session_state.tracking_data[order_id].append({
            'timestamp': datetime.now(),
            'status': 'Bilty Process',
            'description': 'Bilty document generated and ready for dispatch'
        })
        
        return bilty_id
    
    def send_bilty_to_staff(self, bilty_data, staff_phone):
        """Send bilty to specific staff member"""
        staff_message = f"""📄 *BILTY GENERATED - Nutrion Logistics*

🆔 *Bilty ID:* {bilty_data['bilty_id']}
📦 *Order ID:* {bilty_data['order_id']}
📅 *Created:* {bilty_data['created_at'].strftime('%d %b %Y %I:%M %p')}

📋 *Shipment Details:*
🏷️ *Product:* {bilty_data['product_name']}
📊 *Quantity:* {bilty_data['quantity']}

👤 *Receiver Details:*
📛 *Name:* {bilty_data['receiver_name']}
📞 *Phone:* {bilty_data['receiver_phone']}
📍 *Location:* {bilty_data['receiver_location']}
🏙️ *City:* {bilty_data['receiver_city']}
📅 *Approx Delivery:* {bilty_data['approx_delivery']}

📞 *Staff Contact:* {bilty_data['staff_phone']}

🔄 *Status:* Bilty Process
📍 *Next Step:* Send to Receiver"""

        success = self.whatsapp.send_message(staff_phone, staff_message)
        return success
    
    def send_to_receiver(self, order_id, receiver_phone, attached_files=None):
        """Step 3: Send details to receiver"""
        order = next((o for o in st.session_state.orders if o['order_id'] == order_id), None)
        bilty = st.session_state.bilty_data.get(order_id)
        
        if not order or not bilty:
            return False
        
        # Update status
        order['status'] = 'Receiver Process'
        st.session_state.tracking_data[order_id].append({
            'timestamp': datetime.now(),
            'status': 'Receiver Process',
            'description': 'Details sent to receiver via WhatsApp'
        })
        
        # Generate tracking link
        tracking_link = f"http://localhost:8501/?tracking={order_id}"
        
        # Send message to receiver
        receiver_message = f"""📦 *INCOMING SHIPMENT - Nutrion Logistics*

🆔 *Tracking ID:* {order_id}
📅 *Approx Delivery:* {bilty['approx_delivery']}

📋 *Shipment Details:*
*From:* Nutrion Logistics
🏷️ *Product:* {order['product_name']}
📊 *Quantity:* {order['quantity']}

👤 *Receiver:* {bilty['receiver_name']}
📍 *Location:* {bilty['receiver_location']}

📞 *For bilty information, contact:* {bilty['staff_phone']}

🔍 *Track Your Shipment:*
{tracking_link}

Thank you for choosing Nutrion Logistics!"""
        
        # Send to receiver
        success = self.whatsapp.send_message(receiver_phone, receiver_message)
        
        # Send attached files if any
        if attached_files and success:
            for file in attached_files:
                # Save uploaded file temporarily
                with open(file.name, "wb") as f:
                    f.write(file.getbuffer())
                
                # Send based on file type
                if file.name.lower().endswith(('.pdf')):
                    self.whatsapp.send_document(receiver_phone, file.name, file.name)
                elif file.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    self.whatsapp.send_image(receiver_phone, file.name, "Attached document")
                
                # Clean up
                try:
                    os.remove(file.name)
                except:
                    pass
        
        return success
    
    def update_delivery_status(self, order_id, status):
        """Step 4: Update delivery status"""
        order = next((o for o in st.session_state.orders if o['order_id'] == order_id), None)
        if order:
            order['status'] = status
            order['status_updated_at'] = datetime.now()
            
            st.session_state.tracking_data[order_id].append({
                'timestamp': datetime.now(),
                'status': status,
                'description': f'Delivery status updated to: {status}'
            })
            
            return True
        return False
    
    def send_status_update_notification(self, order, status, receiver_phone):
        """Send status update notification to specific receiver"""
        bilty = st.session_state.bilty_data.get(order['order_id'])
        if bilty:
            message = f"""🔄 *STATUS UPDATE - Nutrion Logistics*

🆔 *Tracking ID:* {order['order_id']}
🔄 *Status:* {status}
📅 *Updated:* {datetime.now().strftime('%d %b %Y %I:%M %p')}

📦 *Product:* {order['product_name']}
📊 *Quantity:* {order['quantity']}

🔍 *Track Your Shipment:*
http://localhost:8501/?tracking={order['order_id']}

Thank you for choosing Nutrion Logistics!"""
            
            # Send to receiver
            return self.whatsapp.send_message(receiver_phone, message)
        return False
    
    def update_order(self, order_id, updated_data):
        """Update order details"""
        for i, order in enumerate(st.session_state.orders):
            if order['order_id'] == order_id:
                st.session_state.orders[i].update(updated_data)
                return True
        return False
    
    def delete_order(self, order_id):
        """Delete order"""
        st.session_state.orders = [o for o in st.session_state.orders if o['order_id'] != order_id]
        if order_id in st.session_state.bilty_data:
            del st.session_state.bilty_data[order_id]
        if order_id in st.session_state.tracking_data:
            del st.session_state.tracking_data[order_id]

def show_limited_tracking_view(order_id, system):
    """Show limited access view for customers"""
    st.markdown('<div class="limited-access">', unsafe_allow_html=True)
    
    # Add company logo
    st.markdown("""
    <div class="logo-container">
        <div style="font-size: 2rem; font-weight: bold;">🚚 Nutrion Logistics</div>
        <div style="font-size: 1rem;">Track Your Shipment</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if order_id in st.session_state.tracking_data:
        order = next((o for o in st.session_state.orders if o['order_id'] == order_id), None)
        bilty = st.session_state.bilty_data.get(order_id)
        
        if order:
            # Current status
            current_status = st.session_state.tracking_data[order_id][-1]
            
            st.success(f"✅ Shipment Found - {order_id}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                status_color = get_status_color(current_status['status'])
                st.markdown(f"""
                <div class="card {status_color}">
                    <h4>📊 Current Status</h4>
                    <p><strong>🔄 Status:</strong> {current_status['status']}</p>
                    <p><strong>🕒 Last Update:</strong> {current_status['timestamp'].strftime('%d %b %Y %I:%M %p')}</p>
                </div>
                """, unsafe_allow_html=True)
                
                # Order Details
                st.markdown("### 📦 Order Details")
                st.write(f"**Product:** {order['product_name']}")
                st.write(f"**Quantity:** {order['quantity']}")
                
                if bilty:
                    st.markdown("### 📍 Delivery Details")
                    st.write(f"**Receiver:** {bilty['receiver_name']}")
                    st.write(f"**Location:** {bilty['receiver_location']}")
                    st.write(f"**Approx Delivery:** {bilty['approx_delivery']}")
            
            with col2:
                st.markdown("### 📋 Shipment Timeline")
                timeline = sorted(st.session_state.tracking_data[order_id], key=lambda x: x['timestamp'])
                
                for update in reversed(timeline):
                    icon = get_status_icon(update['status'])
                    status_color = get_status_color(update['status'])
                    st.markdown(f"""
                    <div class="card {status_color}">
                        <div style="display: flex; justify-content: space-between; align-items: start;">
                            <div>
                                <strong>{icon} {update['status']}</strong>
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
            st.error("❌ Shipment not found. Please check your Tracking ID.")
    else:
        st.error("❌ Shipment not found. Please check your Tracking ID.")
    
    # Only show tracking input, no other features
    st.markdown("---")
    st.subheader("🔍 Track Another Shipment")
    new_order_id = st.text_input("Enter another Tracking ID", key="limited_tracking")
    if new_order_id:
        st.experimental_set_query_params(tracking=new_order_id)
        st.experimental_rerun()

def create_download_link(pdf_bytes, filename):
    """Create a download link for PDF"""
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}" class="download-btn">📥 Download {filename}</a>'
    return href

def main():
    # Check if limited access view is requested via query parameter
    query_params = st.experimental_get_query_params()
    if 'tracking' in query_params:
        order_id = query_params['tracking'][0]
        system = LogisticsSystem()
        show_limited_tracking_view(order_id, system)
        return
    
    # Full application view
    st.markdown("""
    <div class="logo-container">
        <div class="main-header">🚚 Nutrion Logistics System</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize system
    system = LogisticsSystem()
    
    # Quick Stats
    total_orders = len(st.session_state.orders)
    under_process = len([o for o in st.session_state.orders if o['status'] == 'Under Process'])
    bilty_process = len([o for o in st.session_state.orders if o['status'] == 'Bilty Process'])
    receiver_process = len([o for o in st.session_state.orders if o['status'] == 'Receiver Process'])
    delivered = len([o for o in st.session_state.orders if o['status'] == 'Delivered'])
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Orders", total_orders)
    with col2:
        st.metric("Under Process", under_process)
    with col3:
        st.metric("Bilty Process", bilty_process)
    with col4:
        st.metric("Receiver Process", receiver_process)
    with col5:
        st.metric("Delivered", delivered)
    
    # Sidebar Navigation
    st.sidebar.title("📋 Navigation")
    
    # Add logo in sidebar
    st.sidebar.markdown("""
    <div class="logo-container">
        <div style="font-size: 1.5rem; font-weight: bold; color: #2E8B57;">🚚 Nutrion</div>
        <div style="font-size: 0.8rem; color: #666;">Logistics System</div>
    </div>
    """, unsafe_allow_html=True)
    
    menu = st.sidebar.radio("", [
        "🏠 Dashboard", 
        "📦 Step 1: Add Order", 
        "📄 Step 2: Bilty Process", 
        "📤 Step 3: Send to Receiver",
        "🔄 Step 4: Update Status",
        "🔍 Track Order",
        "📊 Manage Orders"
    ])
    
    if menu == "🏠 Dashboard":
        show_dashboard(system)
    elif menu == "📦 Step 1: Add Order":
        show_order_form(system)
    elif menu == "📄 Step 2: Bilty Process":
        show_bilty_form(system)
    elif menu == "📤 Step 3: Send to Receiver":
        show_receiver_form(system)
    elif menu == "🔄 Step 4: Update Status":
        show_status_update(system)
    elif menu == "🔍 Track Order":
        show_tracking(system)
    elif menu == "📊 Manage Orders":
        show_management(system)

def show_dashboard(system):
    st.subheader("📊 Quick Overview")
    
    if not st.session_state.orders:
        st.info("No orders yet. Create your first order to get started!")
        return
    
    # Recent orders
    st.subheader("Recent Orders")
    recent_orders = sorted(st.session_state.orders, key=lambda x: x['created_at'], reverse=True)[:5]
    
    for order in recent_orders:
        with st.container():
            col1, col2, col3, col4 = st.columns([2,2,1,1])
            with col1:
                st.write(f"**{order['order_id']}**")
                st.write(f"📦 {order['product_name']} - {order['quantity']}")
            with col2:
                st.write(f"📅 {order['created_at'].strftime('%d %b %Y')}")
                bilty = st.session_state.bilty_data.get(order['order_id'])
                if bilty:
                    st.write(f"👤 {bilty['receiver_name']}")
            with col3:
                status_color = get_status_color(order['status'])
                st.markdown(f'<div class="card {status_color}">{order["status"]}</div>', unsafe_allow_html=True)
            with col4:
                if st.button("📋", key=f"view_{order['order_id']}"):
                    st.session_state.current_tracking = order['order_id']

def show_order_form(system):
    """Step 1: Add new order"""
    st.subheader("📦 Step 1: Add New Order")
    
    with st.form("order_form", clear_on_submit=True):
        st.markdown("### 📋 Product Details")
        
        col1, col2 = st.columns(2)
        
        with col1:
            product_name = st.text_input("Product Name*", placeholder="e.g., Rice, Flour, Sugar")
        
        with col2:
            quantity = st.text_input("Quantity (kg/bag)*", placeholder="e.g., 50 bags, 1000 kg")
        
        submitted = st.form_submit_button("🚀 Add Order", use_container_width=True)
        
        if submitted:
            if all([product_name, quantity]):
                order_data = {
                    'product_name': product_name,
                    'quantity': quantity
                }
                
                order_id = system.add_order(order_data)
                
                st.success(f"""
                ✅ **Order Added Successfully!**
                
                **Order ID:** {order_id}
                **Status:** Under Process
                
                **Next Step:** Proceed to Bilty Process
                """)
                
                # Show quick summary
                with st.expander("📋 Order Summary", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**Product:**", product_name)
                        st.write("**Quantity:**", quantity)
                    with col2:
                        st.write("**Order ID:**", order_id)
                        st.write("**Status:**", "Under Process")
            else:
                st.error("❌ Please fill all required fields (*)")

def show_bilty_form(system):
    """Step 2: Bilty Process"""
    st.subheader("📄 Step 2: Bilty Process")
    
    if not st.session_state.orders:
        st.info("No orders available. Please add an order first.")
        return
    
    # Filter orders that are in "Under Process" status
    available_orders = [o for o in st.session_state.orders if o['status'] == 'Under Process']
    
    if not available_orders:
        st.info("No orders available for bilty process. All orders are processed.")
        return
    
    # Select order
    order_options = {f"{o['order_id']} - {o['product_name']}": o['order_id'] for o in available_orders}
    selected_display = st.selectbox("Select Order for Bilty", list(order_options.keys()))
    order_id = order_options[selected_display]
    
    selected_order = next((o for o in st.session_state.orders if o['order_id'] == order_id), None)
    
    if selected_order:
        st.info(f"**Selected Order:** {selected_order['product_name']} - {selected_order['quantity']}")
        
        with st.form("bilty_form"):
            st.markdown("### 📋 Bilty Details")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📤 From:")
                st.write("**Company:** Nutrion Logistics")
                st.write(f"**Product:** {selected_order['product_name']}")
                st.write(f"**Quantity:** {selected_order['quantity']}")
            
            with col2:
                st.markdown("#### 📥 To:")
                receiver_name = st.text_input("Receiver Name*", placeholder="Enter receiver full name")
                receiver_phone = st.text_input("Receiver Phone*", placeholder="923001234567")
                receiver_location = st.text_input("Location*", placeholder="Complete delivery address")
                receiver_city = st.selectbox("City*", 
                    ["Karachi", "Lahore", "Islamabad", "Rawalpindi", "Faisalabad", "Multan", "Hyderabad", "Peshawar", "Quetta", "Other"])
                if receiver_city == "Other":
                    receiver_city = st.text_input("Enter City Name")
                approx_delivery = st.text_input("Approx Delivery Date & Time*", placeholder="e.g., 25 Dec 2024, 2:00 PM")
                staff_phone = st.text_input("Staff Phone Number*", placeholder="923001234567", value="+9232074294229")
                staff_name = st.text_input("Staff Name", placeholder="Optional: Enter staff name")
            
            submitted = st.form_submit_button("📄 Generate Bilty", use_container_width=True)
            
            if submitted:
                if all([receiver_name, receiver_phone, receiver_location, receiver_city, approx_delivery, staff_phone]):
                    bilty_data = {
                        'product_name': selected_order['product_name'],
                        'quantity': selected_order['quantity'],
                        'receiver_name': receiver_name,
                        'receiver_phone': receiver_phone,
                        'receiver_location': receiver_location,
                        'receiver_city': receiver_city,
                        'approx_delivery': approx_delivery,
                        'staff_phone': staff_phone,
                        'staff_name': staff_name
                    }
                    
                    bilty_id = system.create_bilty(order_id, bilty_data)
                    
                    st.success(f"""
                    ✅ **Bilty Generated Successfully!**
                    
                    **Bilty ID:** {bilty_id}
                    **Order ID:** {order_id}
                    **Status:** Bilty Process
                    
                    **Next Step:** Send details to receiver
                    """)
                    
                    # Generate and show PDF download options
                    with st.expander("📄 Download Bilty Documents", expanded=True):
                        st.markdown("### 📥 Download Bilty PDFs")
                        
                        # Simple Bilty PDF
                        simple_pdf_bytes = system.pdf_gen.create_bilty_pdf(bilty_data)
                        st.markdown(create_download_link(simple_pdf_bytes, f"Bilty_{bilty_id}_Simple.pdf"), unsafe_allow_html=True)
                        
                        # Detailed Bilty PDF
                        detailed_pdf_bytes = system.pdf_gen.create_detailed_bilty_pdf(bilty_data, selected_order)
                        st.markdown(create_download_link(detailed_pdf_bytes, f"Bilty_{bilty_id}_Detailed.pdf"), unsafe_allow_html=True)
                        
                        st.info("💡 Download both versions. Simple for quick reference, Detailed for complete documentation.")
                    
                    # Option to send bilty to staff
                    st.markdown("---")
                    st.markdown("### 📤 Send Bilty to Staff")
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        staff_phone_to_send = st.text_input("Enter staff phone number to send bilty:", 
                                                          value=staff_phone,
                                                          key="bilty_staff_phone")
                    with col2:
                        if st.button("📤 Send Bilty via WhatsApp", key="send_bilty_whatsapp"):
                            if staff_phone_to_send:
                                success = system.send_bilty_to_staff(bilty_data, staff_phone_to_send)
                                if success:
                                    st.success(f"✅ Bilty sent to {staff_phone_to_send}")
                                else:
                                    st.error("❌ Failed to send bilty")
                            else:
                                st.warning("⚠️ Please enter a phone number")
                    
                else:
                    st.error("❌ Please fill all required fields (*)")

def show_receiver_form(system):
    """Step 3: Send to Receiver"""
    st.subheader("📤 Step 3: Send to Receiver")
    
    if not st.session_state.bilty_data:
        st.info("No bilty data available. Please complete Step 2 first.")
        return
    
    # Filter orders that are in "Bilty Process" status
    available_orders = [o for o in st.session_state.orders if o['status'] == 'Bilty Process']
    
    if not available_orders:
        st.info("No orders available for receiver process. All orders are processed.")
        return
    
    # Select order
    order_options = {}
    for o in available_orders:
        bilty = st.session_state.bilty_data.get(o['order_id'])
        if bilty:
            order_options[f"{o['order_id']} - {bilty['receiver_name']}"] = o['order_id']
    
    if not order_options:
        st.info("No orders with bilty data available.")
        return
    
    selected_display = st.selectbox("Select Order for Receiver", list(order_options.keys()))
    order_id = order_options[selected_display]
    
    selected_order = next((o for o in st.session_state.orders if o['order_id'] == order_id), None)
    bilty_data = st.session_state.bilty_data.get(order_id)
    
    if selected_order and bilty_data:
        st.info(f"**Order:** {selected_order['product_name']} - {selected_order['quantity']}")
        st.info(f"**Receiver:** {bilty_data['receiver_name']} - {bilty_data['receiver_phone']}")
        
        with st.form("receiver_form"):
            st.markdown("### 📤 Send to Receiver")
            
            # Phone number input
            st.markdown("#### 📞 Receiver Phone Number")
            receiver_phone = st.text_input("Enter receiver phone number:", 
                                         value=bilty_data['receiver_phone'],
                                         key="receiver_phone_input")
            
            # File upload
            st.markdown("#### 📎 Attach Files (Optional)")
            st.write("You can attach PDF, JPG, PNG files to send to receiver")
            attached_files = st.file_uploader(
                "Choose files", 
                type=['pdf', 'jpg', 'jpeg', 'png'], 
                accept_multiple_files=True,
                key="receiver_files"
            )
            
            # Preview message
            tracking_link = f"http://localhost:8501/?tracking={order_id}"
            preview_message = f"""📦 *INCOMING SHIPMENT - Nutrion Logistics*

🆔 *Tracking ID:* {order_id}
📅 *Approx Delivery:* {bilty_data['approx_delivery']}

📋 *Shipment Details:*
*From:* Nutrion Logistics
🏷️ *Product:* {selected_order['product_name']}
📊 *Quantity:* {selected_order['quantity']}

👤 *Receiver:* {bilty_data['receiver_name']}
📍 *Location:* {bilty_data['receiver_location']}

📞 *For bilty information, contact:* {bilty_data['staff_phone']}

🔍 *Track Your Shipment:*
{tracking_link}

Thank you for choosing Nutrion Logistics!"""
            
            with st.expander("📝 Preview Message"):
                st.text(preview_message)
            
            submitted = st.form_submit_button("📤 Send to Receiver", use_container_width=True)
            
            if submitted:
                if receiver_phone:
                    success = system.send_to_receiver(order_id, receiver_phone, attached_files)
                    
                    if success:
                        st.success(f"""
                        ✅ **Message Sent to Receiver Successfully!**
                        
                        **Receiver:** {bilty_data['receiver_name']}
                        **Phone:** {receiver_phone}
                        **Status:** Receiver Process
                        **Tracking Link:** Sent to receiver
                        
                        **Next Step:** Update delivery status
                        """)
                    else:
                        st.error("❌ Failed to send message to receiver. Please check the phone number.")
                else:
                    st.error("❌ Please enter receiver phone number")

def show_status_update(system):
    """Step 4: Update Delivery Status"""
    st.subheader("🔄 Step 4: Update Delivery Status")
    
    if not st.session_state.orders:
        st.info("No orders available")
        return
    
    # Select order to update
    order_options = {}
    for o in st.session_state.orders:
        bilty = st.session_state.bilty_data.get(o['order_id'])
        if bilty:
            order_options[f"{o['order_id']} - {bilty['receiver_name']}"] = o['order_id']
    
    if not order_options:
        st.info("No orders with receiver data available.")
        return
    
    selected_display = st.selectbox("Select Order", list(order_options.keys()))
    order_id = order_options[selected_display]
    
    selected_order = next((o for o in st.session_state.orders if o['order_id'] == order_id), None)
    bilty_data = st.session_state.bilty_data.get(order_id)
    
    if selected_order and bilty_data:
        st.info(f"**Current Status:** {selected_order['status']}")
        st.info(f"**Receiver:** {bilty_data['receiver_name']}")
        
        # Status update form
        with st.form("status_update_form"):
            new_status = st.selectbox("Select New Status", [
                "Under Process",
                "Bilty Process", 
                "Receiver Process",
                "Delivered",
                "Not Delivered Yet"
            ])
            
            # Option to send notification
            st.markdown("### 📤 Send Status Update Notification")
            send_notification = st.checkbox("Send WhatsApp notification to receiver", value=True)
            notification_phone = st.text_input("Receiver phone for notification:", 
                                             value=bilty_data['receiver_phone'],
                                             key="status_notification_phone")
            
            submitted = st.form_submit_button("🔄 Update Status", use_container_width=True)
            
            if submitted:
                success = system.update_delivery_status(order_id, new_status)
                
                if success:
                    st.success(f"""
                    ✅ **Status Updated Successfully!**
                    
                    **Order ID:** {order_id}
                    **New Status:** {new_status}
                    """)
                    
                    # Send notification if requested
                    if send_notification and notification_phone:
                        notification_success = system.send_status_update_notification(
                            selected_order, new_status, notification_phone
                        )
                        if notification_success:
                            st.success(f"✅ Status notification sent to {notification_phone}")
                        else:
                            st.error("❌ Failed to send status notification")
                else:
                    st.error("❌ Failed to update status")

def show_tracking(system):
    st.subheader("🔍 Track Order")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        order_id = st.text_input("Enter Order ID", placeholder="ORD123456")
        
        if order_id:
            if order_id in st.session_state.tracking_data:
                order = next((o for o in st.session_state.orders if o['order_id'] == order_id), None)
                bilty = st.session_state.bilty_data.get(order_id)
                
                if order:
                    st.success("✅ Order Found!")
                    
                    # Current status
                    current_status = st.session_state.tracking_data[order_id][-1]
                    status_color = get_status_color(current_status['status'])
                    
                    st.markdown(f"""
                    <div class="card {status_color}">
                        <h4>📊 Current Status</h4>
                        <p><strong>🔄 Status:</strong> {current_status['status']}</p>
                        <p><strong>🕒 Last Update:</strong> {current_status['timestamp'].strftime('%d %b %Y %I:%M %p')}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Order details
                    st.markdown("### 📦 Order Details")
                    st.write(f"**Product:** {order['product_name']}")
                    st.write(f"**Quantity:** {order['quantity']}")
                    
                    if bilty:
                        st.markdown("### 👤 Receiver Details")
                        st.write(f"**Name:** {bilty['receiver_name']}")
                        st.write(f"**Location:** {bilty['receiver_location']}")
                        st.write(f"**Approx Delivery:** {bilty['approx_delivery']}")
    
    with col2:
        if order_id and order_id in st.session_state.tracking_data:
            st.markdown("### 📋 Order Timeline")
            
            timeline = sorted(st.session_state.tracking_data[order_id], key=lambda x: x['timestamp'])
            
            for update in reversed(timeline):
                icon = get_status_icon(update['status'])
                status_color = get_status_color(update['status'])
                
                st.markdown(f"""
                <div class="card {status_color}">
                    <div style="display: flex; justify-content: space-between; align-items: start;">
                        <div>
                            <strong>{icon} {update['status']}</strong>
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
    
    if not st.session_state.orders:
        st.info("No orders available")
        return
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_term = st.text_input("🔍 Search by Order ID, Product, or Receiver")
    with col2:
        status_filter = st.selectbox("Filter by Status", ["All", "Under Process", "Bilty Process", "Receiver Process", "Delivered", "Not Delivered Yet"])
    
    # Filter orders
    filtered_orders = st.session_state.orders
    if search_term:
        filtered_orders = [o for o in filtered_orders if 
                         search_term.lower() in o['order_id'].lower() or
                         search_term.lower() in o['product_name'].lower() or
                         (o['order_id'] in st.session_state.bilty_data and 
                          search_term.lower() in st.session_state.bilty_data[o['order_id']]['receiver_name'].lower())]
    
    if status_filter != "All":
        filtered_orders = [o for o in filtered_orders if status_filter == o['status']]
    
    # Display orders
    for order in filtered_orders:
        bilty = st.session_state.bilty_data.get(order['order_id'])
        
        with st.expander(f"📦 {order['order_id']} - {order['product_name']} → {bilty['receiver_name'] if bilty else 'No Receiver'}", expanded=False):
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                st.write("**Product:**", order['product_name'])
                st.write("**Quantity:**", order['quantity'])
                st.write("**Created:**", order['created_at'].strftime('%d %b %Y %H:%M'))
            
            with col2:
                if bilty:
                    st.write("**Receiver:**", bilty['receiver_name'])
                    st.write("**Location:**", bilty['receiver_location'])
                    st.write("**Phone:**", bilty['receiver_phone'])
                else:
                    st.write("**Receiver:** Not assigned")
            
            with col3:
                status_color = get_status_color(order['status'])
                st.markdown(f'<div class="card {status_color}">{order["status"]}</div>', unsafe_allow_html=True)
                
                # Action buttons
                col_edit, col_del = st.columns(2)
                with col_edit:
                    if st.button("✏️ Edit", key=f"edit_{order['order_id']}"):
                        st.session_state.editing = order['order_id']
                with col_del:
                    if st.button("🗑️ Delete", key=f"del_{order['order_id']}"):
                        system.delete_order(order['order_id'])
                        st.success("Order deleted successfully!")
                        st.experimental_rerun()
    
    # Edit functionality
    if hasattr(st.session_state, 'editing'):
        editing_id = st.session_state.editing
        order_to_edit = next((o for o in st.session_state.orders if o['order_id'] == editing_id), None)
        
        if order_to_edit:
            st.markdown("---")
            st.subheader(f"✏️ Edit Order: {editing_id}")
            
            with st.form("edit_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    new_product_name = st.text_input("Product Name", value=order_to_edit['product_name'])
                    new_quantity = st.text_input("Quantity", value=order_to_edit['quantity'])
                
                with col2:
                    new_status = st.selectbox("Status", [
                        "Under Process",
                        "Bilty Process", 
                        "Receiver Process",
                        "Delivered",
                        "Not Delivered Yet"
                    ], index=[
                        "Under Process",
                        "Bilty Process", 
                        "Receiver Process", 
                        "Delivered",
                        "Not Delivered Yet"
                    ].index(order_to_edit['status']))
                
                col_save, col_cancel = st.columns(2)
                with col_save:
                    if st.form_submit_button("💾 Save Changes"):
                        updated_data = {
                            'product_name': new_product_name,
                            'quantity': new_quantity,
                            'status': new_status
                        }
                        system.update_order(editing_id, updated_data)
                        del st.session_state.editing
                        st.success("✅ Order updated successfully!")
                        st.experimental_rerun()
                
                with col_cancel:
                    if st.form_submit_button("❌ Cancel"):
                        del st.session_state.editing
                        st.experimental_rerun()

def get_status_icon(status):
    icons = {
        "Under Process": "⚙️",
        "Bilty Process": "📄",
        "Receiver Process": "📤",
        "Delivered": "✅",
        "Not Delivered Yet": "❌"
    }
    return icons.get(status, "📦")

def get_status_color(status):
    colors = {
        "Under Process": "status-process",
        "Bilty Process": "status-bilty", 
        "Receiver Process": "status-receiver",
        "Delivered": "status-delivered",
        "Not Delivered Yet": "status-pending"
    }
    return colors.get(status, "status-pending")

if __name__ == "__main__":
    main()
