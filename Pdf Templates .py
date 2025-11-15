import streamlit as st
from fpdf import FPDF
from datetime import datetime
import io

# --- Constants based on your notes ---
COMPANY_NAME = "Nutriix"
COMPANY_ADDRESS = "Lower Ground Office #24, Real City, Main Sargodha Road, Faisalabad"
CEO_NAME = "Mansoor Javeed"
CEO_TITLE = "Chief Executive Officer"

# --- PDF Class with Header and Footer ---
class PDF(FPDF):
    def header(self):
        """Creates the letterhead for each page."""
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, COMPANY_NAME, 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, COMPANY_ADDRESS, 0, 1, 'C')
        # Add a line break
        self.ln(15)

    def footer(self):
        """Creates the signature block at the bottom of the page."""
        self.set_y(-60) # Position 6 cm from bottom
        self.set_font('Arial', '', 12)
        
        # Check if signature image object exists
        if hasattr(self, 'signature_img_obj') and self.signature_img_obj:
            try:
                # Use the in-memory image object
                # We save the current x/y to position text correctly
                x = self.get_x()
                y = self.get_y()
                # We must specify the type ('PNG') when using a file-like object
                self.image(self.signature_img_obj, x=x, y=y, w=40, type='PNG')
                # Move below the image for the text
                self.set_y(y + 25) 
            except Exception as e:
                st.warning(f"Could not load signature image. Error: {e}")
                self.cell(0, 10, "(Signature Placeholder)", 0, 1, 'L')
                self.set_y(self.get_y() + 25) # Move down anyway
        else:
            self.cell(0, 10, "(Signature Placeholder - Please upload)", 0, 1, 'L')
            self.ln(5)

        # Signature line
        self.line(self.get_x(), self.get_y(), self.get_x() + 70, self.get_y())
        self.ln(5)
        # CEO Name and Title
        self.cell(0, 5, CEO_NAME, 0, 1, 'L')
        self.cell(0, 5, f"{CEO_TITLE}, {COMPANY_NAME}", 0, 1, 'L')

# --- Helper function to create the base PDF ---
def create_base_pdf(signature_img):
    """Initializes the PDF object and adds the signature image to it."""
    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=25)
    pdf.add_page()
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.set_font('Arial', '', 12)
    
    # Pass the in-memory image object to the class instance
    pdf.signature_img_obj = signature_img
    return pdf

# --- Functions to generate specific PDFs ---

def generate_authority_letter(recipient, address, subject, body, sig_img):
    """Generates the Authority Letter PDF."""
    pdf = create_base_pdf(sig_img)
    date_str = datetime.now().strftime("%B %d, %Y")

    # Letter Date
    pdf.cell(0, 10, f"Date: {date_str}", 0, 1, 'R')
    pdf.ln(5)
    
    # Recipient Info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, recipient, 0, 1, 'L')
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 7, address, 0, 1, 'L')
    pdf.ln(10)

    # Subject
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Subject: {subject}", 0, 1, 'L')
    pdf.ln(5)
    
    # Body
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 5, body)
    
    return pdf.output() # Returns bytes

def generate_tax_exemption(client, invoice, ntn, body, sig_img):
    """Generates the Tax Exemption PDF."""
    pdf = create_base_pdf(sig_img)
    date_str = datetime.now().strftime("%B %d, %Y")

    # Title
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "Tax Exemption Certificate", 0, 1, 'C')
    pdf.ln(10)

    # Date
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Date: {date_str}", 0, 1, 'R')
    pdf.ln(5)
    
    # Details
    pdf.cell(0, 7, f"Client Name: {client}", 0, 1, 'L')
    pdf.cell(0, 7, f"Invoice #: {invoice}", 0, 1, 'L')
    pdf.cell(0, 7, f"NTN: {ntn}", 0, 1, 'L')
    pdf.ln(10)
    
    # Body
    pdf.multi_cell(0, 5, body)
    return pdf.output() # Returns bytes

def generate_generic_letter(subject, body, sig_img):
    """Generates a 'To Whom It May Concern' letter."""
    pdf = create_base_pdf(sig_img)
    date_str = datetime.now().strftime("%B %d, %Y")

    # Date
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Date: {date_str}", 0, 1, 'R')
    pdf.ln(5)
    
    # Recipient
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 7, "To Whom It May Concern", 0, 1, 'L')
    pdf.ln(10)

    # Subject
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Subject: {subject}", 0, 1, 'L')
    pdf.ln(5)
    
    # Body
    pdf.set_font('Arial', '', 12)
    pdf.multi_cell(0, 5, body)
    return pdf.output() # Returns bytes

# --- Streamlit App ---

st.set_page_config(layout="centered")
st.title("📄 PDF Template Generator")
st.header(f"Company: {COMPANY_NAME}")

# --- Sidebar for settings and template selection ---
st.sidebar.title("Settings")

# 1. Signature Uploader
st.sidebar.header("CEO Signature")
signature_image = st.sidebar.file_uploader(
    "Upload CEO Signature (PNG format preferred)", 
    type=["png"]
)
if signature_image:
    st.sidebar.image(signature_image, width=150)
else:
    st.sidebar.warning("Please upload a signature to generate a PDF.")

# 2. Template Selection
st.sidebar.header("Choose Template")
template_options = [
    "Select a template...",
    "Authority Letter",
    "Tax Exemption Certificate",
    "To Whom It May Concern" # Added this one for you
]
template_choice = st.sidebar.selectbox("Select a document:", template_options)

# --- Main Page - Input Fields based on selection ---

if template_choice == 'Select a template...':
    st.info("Please choose a template from the sidebar to begin.")

# --- Template 1: Authority Letter ---
elif template_choice == 'Authority Letter':
    st.subheader("Authority Letter")
    
    with st.form("auth_form"):
        recipient_name = st.text_input("Recipient Name (e.g., 'The Branch Manager, HBL')")
        recipient_address = st.text_input("Recipient Address (e.g., 'Main Branch, Faisalabad')")
        subject = st.text_input("Subject:", "Authority Letter")
        authorized_person = st.text_input("Authorized Person's Name:")
        authorized_cnic = st.text_input("Authorized Person's CNIC:")
        
        default_body = (
            f"This is to certify that Mr./Ms. {authorized_person or '[Person Name]'} holding CNIC No. {authorized_cnic or '[CNIC Number]'} "
            f"is an employee of {COMPANY_NAME} and is hereby authorized to act on our behalf to "
            "[Specify reason, e.g., 'collect bank statements', 'submit documents', etc.].\n\n"
            "Any and all acts carried out by him/her on this behalf shall be binding on the company.\n\n"
            "This authority is valid until [Insert Date or 'further notice']."
        )
        body_text = st.text_area("Body:", value=default_body, height=250)
        
        submit_button = st.form_submit_button(label="Generate PDF")

    if submit_button:
        if not signature_image:
            st.error("Please upload the CEO's signature in the sidebar.")
        elif not recipient_name or not authorized_person:
            st.error("Please fill in at least the Recipient and Authorized Person fields.")
        else:
            pdf_bytes = generate_authority_letter(
                recipient_name,
                recipient_address,
                subject,
                body_text,
                signature_image
            )
            st.download_button(
                label="Download Authority Letter PDF",
                data=pdf_bytes,
                file_name=f"Authority_Letter_{authorized_person.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            st.success("PDF Generated!")

# --- Template 2: Tax Exemption ---
elif template_choice == 'Tax Exemption Certificate':
    st.subheader("Tax Exemption Certificate")

    with st.form("tax_form"):
        client_name = st.text_input("Client Name:")
        invoice_no = st.text_input("Invoice #:")
        ntn = st.text_input("Company NTN:", value="[Your NTN Here]")
        
        default_body = (
            f"This is to certify that {COMPANY_NAME}, holding National Tax Number (NTN) {ntn or '[Your NTN Here]'}, "
            f"has issued Invoice #{invoice_no or '[Invoice #]'} to {client_name or '[Client Name]'}.\n\n"
            "We declare that [State reason for exemption, e.g., 'our company is exempt from sales tax under schedule X of the Sales Tax Act, 1990', "
            "or 'the services provided are not subject to FED', etc.].\n\n"
            "Therefore, no tax has been charged or collected on the aforementioned invoice."
        )
        body_text = st.text_area("Certificate Body:", value=default_body, height=200)
        
        submit_button = st.form_submit_button(label="Generate PDF")
    
    if submit_button:
        if not signature_image:
            st.error("Please upload the CEO's signature in the sidebar.")
        elif not client_name or not invoice_no:
            st.error("Please fill in at least the Client Name and Invoice # fields.")
        else:
            pdf_bytes = generate_tax_exemption(
                client_name,
                invoice_no,
                ntn,
                body_text,
                signature_image
            )
            st.download_button(
                label="Download Tax Exemption PDF",
                data=pdf_bytes,
                file_name=f"Tax_Exemption_{client_name.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            st.success("PDF Generated!")

# --- Template 3: To Whom It May Concern ---
elif template_choice == 'To Whom It May Concern':
    st.subheader("To Whom It May Concern")

    with st.form("generic_form"):
        subject = st.text_input("Subject:", "Letter of Recommendation")
        
        default_body = (
            "This letter is to certify that [Name of Person] was employed at "
            f"{COMPANY_NAME} from [Start Date] to [End Date] as a [Job Title].\n\n"
            "During their tenure, [He/She/They] was/were responsible for [briefly describe duties].\n\n"
            "[Add performance details or recommendations here.]\n\n"
            "We wish [him/her/them] all the best in [his/her/their] future endeavors."
        )
        body_text = st.text_area("Body:", value=default_body, height=250)
        
        submit_button = st.form_submit_button(label="Generate PDF")

    if submit_button:
        if not signature_image:
            st.error("Please upload the CEO's signature in the sidebar.")
        elif not subject or not body_text:
            st.error("Please fill in all fields.")
        else:
            pdf_bytes = generate_generic_letter(
                subject,
                body_text,
                signature_image
            )
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=f"{subject.replace(' ', '_')}.pdf",
                mime="application/pdf"
            )
            st.success("PDF Generated!")
