import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import tempfile
import os
import base64
from fpdf import FPDF
import requests
import json

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'invoice_items' not in st.session_state:
    st.session_state.invoice_items = []
if 'stock_items' not in st.session_state:
    st.session_state.stock_items = []
if 'current_invoice_number' not in st.session_state:
    st.session_state.current_invoice_number = "1"
if 'parties' not in st.session_state:
    st.session_state.parties = []
if 'last_payment_details' not in st.session_state:
    st.session_state.last_payment_details = None
if 'current_ledger_data' not in st.session_state:
    st.session_state.current_ledger_data = None

# Product configuration
PRODUCTS = [
    "Strophase G", "Strophase P", "Strozyme NSP", "SP200", "SP300", 
    "SP300 Advance", "Monica", "Linco Magic", "Enra Magic", "InduceAcid Plus",
    "InduceAcid Buty", "Huntox", "Strozyme XYL", "Super Ener Emusifier", 
    "Antioxdant", "Toxin Binder Weilituo", "Toxin Clean", "GutPro 60 (Tributyrin)", 
    "InduceAcid Liquid"
]

PACKING_OPTIONS = ["Ltr", "Kg", "25 Ltr", "25 kg"]

# Utility functions for number formatting
def format_currency_indian(value):
    """Format currency in Indian numbering system with comma separation"""
    try:
        value = float(value)
        if value == 0:
            return "0.00"
        
        is_negative = value < 0
        value = abs(value)
        
        # Format with 2 decimal places
        formatted = "{:,.2f}".format(value)
        
        # Indian numbering system uses different comma placement
        parts = formatted.split(".")
        integer_part = parts[0]
        
        # For Indian system: 1,00,000 instead of 100,000
        if len(integer_part) > 3:
            last_three = integer_part[-3:]
            other = integer_part[:-3]
            if other:
                formatted_integer = other + "," + last_three
            else:
                formatted_integer = last_three
        else:
            formatted_integer = integer_part
        
        result = formatted_integer + "." + parts[1] if len(parts) > 1 else formatted_integer
        return f"-{result}" if is_negative else result
    except (ValueError, TypeError):
        return "0.00"

def format_number_indian(value):
    """Format numbers in Indian numbering system with comma separation"""
    try:
        value = float(value)
        if value == 0:
            return "0"
        
        is_negative = value < 0
        value = abs(value)
        
        # Check if it's a whole number
        if value.is_integer():
            formatted = "{:,.0f}".format(int(value))
        else:
            formatted = "{:,.2f}".format(value)
        
        # Indian numbering system uses different comma placement
        parts = formatted.split(".")
        integer_part = parts[0]
        
        # For Indian system: 1,00,000 instead of 100,000
        if len(integer_part) > 3:
            last_three = integer_part[-3:]
            other = integer_part[:-3]
            if other:
                formatted_integer = other + "," + last_three
            else:
                formatted_integer = last_three
        else:
            formatted_integer = integer_part
        
        result = formatted_integer + "." + parts[1] if len(parts) > 1 else formatted_integer
        return f"-{result}" if is_negative else result
    except (ValueError, TypeError):
        return "0"

class NutritionBackend:
    def __init__(self, db_path='invoice_app_v4.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database connection and create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parties (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                initial_opening_balance REAL DEFAULT 0.0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_number TEXT UNIQUE NOT NULL,
                party_name TEXT NOT NULL,
                date TEXT NOT NULL,
                total_amount REAL NOT NULL,
                previous_balance REAL NOT NULL,
                grand_total REAL NOT NULL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                qty REAL NOT NULL,
                packing TEXT,
                unit_price REAL NOT NULL,
                amount REAL NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                party_name TEXT NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                remarks TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stock (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                batch_no TEXT,
                date TEXT NOT NULL,
                quantity REAL NOT NULL DEFAULT 0
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS opening_balance_adjustments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                party_name TEXT NOT NULL,
                adjustment_date TEXT NOT NULL,
                old_balance REAL NOT NULL,
                new_balance REAL NOT NULL,
                reason TEXT,
                created_at TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def get_next_invoice_number(self):
        """Get next invoice number"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MAX(CAST(invoice_number AS INTEGER)) FROM invoices WHERE invoice_number GLOB '[0-9]*'")
            result = cursor.fetchone()
            next_num = result[0] + 1 if result and result[0] is not None else 1
            return {"nextInvoiceNumber": str(next_num)}
        except Exception as e:
            return {"nextInvoiceNumber": "1"}
        finally:
            conn.close()
    
    def get_parties(self):
        """Get all parties"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT name FROM parties")
            parties = [{"name": row[0]} for row in cursor.fetchall()]
            return parties
        except Exception as e:
            return []
        finally:
            conn.close()
    
    def get_party_balance(self, party_name):
        """Get party balance information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get initial balance
            cursor.execute("SELECT initial_opening_balance FROM parties WHERE name = ?", (party_name,))
            party_row = cursor.fetchone()
            initial_balance = party_row[0] if party_row else 0.0
            
            # Calculate current balance
            cursor.execute("SELECT SUM(total_amount) FROM invoices WHERE party_name = ?", (party_name,))
            total_invoices = cursor.fetchone()[0] or 0.0
            
            cursor.execute("SELECT SUM(amount) FROM payments WHERE party_name = ?", (party_name,))
            total_payments = cursor.fetchone()[0] or 0.0
            
            current_balance = initial_balance + total_invoices - total_payments
            
            return {
                "balance": current_balance,
                "initialOpeningBalance": initial_balance
            }
        except Exception as e:
            return {"balance": 0.0, "initialOpeningBalance": 0.0}
        finally:
            conn.close()
    
    def create_invoice(self, invoice_data):
        """Create a new invoice"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Ensure party exists
            cursor.execute("INSERT OR IGNORE INTO parties (name) VALUES (?)", (invoice_data['partyName'],))
            
            # Insert invoice
            cursor.execute('''
                INSERT INTO invoices (invoice_number, party_name, date, total_amount, previous_balance, grand_total)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                invoice_data['invoiceNumber'],
                invoice_data['partyName'],
                invoice_data['date'],
                invoice_data['totalAmount'],
                invoice_data['previousBalance'],
                invoice_data['grandTotal']
            ))
            
            invoice_id = cursor.lastrowid
            
            # Insert items
            for item in invoice_data['items']:
                cursor.execute('''
                    INSERT INTO invoice_items (invoice_id, product_name, qty, packing, unit_price, amount)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    invoice_id,
                    item['productName'],
                    item['qty'],
                    item['packing'],
                    item['unitPrice'],
                    item['amount']
                ))
            
            conn.commit()
            next_invoice = self.get_next_invoice_number()
            
            return {
                "message": "Invoice created successfully!",
                "invoiceNumber": invoice_data['invoiceNumber'],
                "nextInvoiceNumber": next_invoice['nextInvoiceNumber']
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def record_payment(self, payment_data):
        """Record a payment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("INSERT OR IGNORE INTO parties (name) VALUES (?)", (payment_data['partyName'],))
            
            cursor.execute('''
                INSERT INTO payments (party_name, amount, date, remarks)
                VALUES (?, ?, ?, ?)
            ''', (
                payment_data['partyName'],
                payment_data['amount'],
                payment_data['date'],
                payment_data.get('remarks', '')
            ))
            
            payment_id = cursor.lastrowid
            conn.commit()
            
            return {
                "message": "Payment recorded successfully!",
                "paymentId": payment_id
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def delete_payment(self, payment_id):
        """Delete a payment"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("DELETE FROM payments WHERE id = ?", (payment_id,))
            conn.commit()
            
            return {
                "message": "Payment deleted successfully!",
                "deleted": True
            }
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_payments(self, party_name=None, start_date=None, end_date=None):
        """Get payments with optional filters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = "SELECT id, party_name, amount, date, remarks FROM payments WHERE 1=1"
            params = []
            
            if party_name:
                query += " AND party_name = ?"
                params.append(party_name)
            
            if start_date:
                query += " AND date >= ?"
                params.append(start_date)
            
            if end_date:
                query += " AND date <= ?"
                params.append(end_date)
            
            query += " ORDER BY date DESC"
            
            cursor.execute(query, params)
            payments = []
            for row in cursor.fetchall():
                payments.append({
                    "paymentId": row[0],
                    "partyName": row[1],
                    "amount": row[2],
                    "date": row[3],
                    "remarks": row[4]
                })
            
            return payments
        except Exception as e:
            return []
        finally:
            conn.close()

    def get_invoices_by_date_range(self, start_date, end_date):
        """Get invoices within date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT i.invoice_number, i.party_name, i.date, i.total_amount, i.previous_balance, i.grand_total,
                       ii.product_name, ii.qty, ii.packing, ii.unit_price, ii.amount
                FROM invoices i
                JOIN invoice_items ii ON i.id = ii.invoice_id
                WHERE i.date BETWEEN ? AND ?
                ORDER BY i.date, i.invoice_number
            ''', (start_date, end_date))
            
            invoices = {}
            for row in cursor.fetchall():
                invoice_number = row[0]
                if invoice_number not in invoices:
                    invoices[invoice_number] = {
                        "invoiceNumber": invoice_number,
                        "partyName": row[1],
                        "date": row[2],
                        "totalAmount": row[3],
                        "previousBalance": row[4],
                        "grandTotal": row[5],
                        "items": []
                    }
                
                invoices[invoice_number]["items"].append({
                    "productName": row[6],
                    "qty": row[7],
                    "packing": row[8],
                    "unitPrice": row[9],
                    "amount": row[10]
                })
            
            return list(invoices.values())
        except Exception as e:
            return []
        finally:
            conn.close()

    def get_invoices_by_party_and_date_range(self, party_name, start_date, end_date):
        """Get invoices for specific party within date range"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT i.invoice_number, i.party_name, i.date, i.total_amount, i.previous_balance, i.grand_total,
                       ii.product_name, ii.qty, ii.packing, ii.unit_price, ii.amount
                FROM invoices i
                JOIN invoice_items ii ON i.id = ii.invoice_id
                WHERE i.party_name = ? AND i.date BETWEEN ? AND ?
                ORDER BY i.date, i.invoice_number
            ''', (party_name, start_date, end_date))
            
            invoices = {}
            for row in cursor.fetchall():
                invoice_number = row[0]
                if invoice_number not in invoices:
                    invoices[invoice_number] = {
                        "invoiceNumber": invoice_number,
                        "partyName": row[1],
                        "date": row[2],
                        "totalAmount": row[3],
                        "previousBalance": row[4],
                        "grandTotal": row[5],
                        "items": []
                    }
                
                invoices[invoice_number]["items"].append({
                    "productName": row[6],
                    "qty": row[7],
                    "packing": row[8],
                    "unitPrice": row[9],
                    "amount": row[10]
                })
            
            return list(invoices.values())
        except Exception as e:
            return []
        finally:
            conn.close()

    def get_product_sales_summary(self, start_date=None, end_date=None):
        """Get product sales summary"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            query = '''
                SELECT ii.product_name, ii.packing, SUM(ii.qty) as total_qty, SUM(ii.amount) as total_amount
                FROM invoice_items ii
                JOIN invoices i ON ii.invoice_id = i.id
            '''
            params = []
            
            if start_date and end_date:
                query += " WHERE i.date BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            
            query += " GROUP BY ii.product_name, ii.packing ORDER BY total_amount DESC"
            
            cursor.execute(query, params)
            
            summary = []
            for row in cursor.fetchall():
                summary.append({
                    "productName": row[0],
                    "packing": row[1],
                    "totalQty": row[2],
                    "totalAmount": row[3]
                })
            
            return summary
        except Exception as e:
            return []
        finally:
            conn.close()

    def get_all_party_ledgers(self):
        """Get all party ledgers"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT name FROM parties")
            parties = [row[0] for row in cursor.fetchall()]
            
            ledgers = []
            for party in parties:
                balance_info = self.get_party_balance(party)
                ledgers.append({
                    "partyName": party,
                    "currentBalance": balance_info['balance']
                })
            
            return ledgers
        except Exception as e:
            return []
        finally:
            conn.close()
    
    def get_ledger(self, party_name):
        """Get party ledger"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get party balance info
            balance_info = self.get_party_balance(party_name)
            
            # Get invoices and items
            cursor.execute('''
                SELECT i.invoice_number, i.date, ii.product_name, ii.qty, ii.packing, ii.unit_price, ii.amount
                FROM invoices i
                JOIN invoice_items ii ON i.id = ii.invoice_id
                WHERE i.party_name = ?
                ORDER BY i.date, i.invoice_number
            ''', (party_name,))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    'type': 'invoice_item',
                    'date': row[1],
                    'invoiceNumber': row[0],
                    'productName': row[2],
                    'qty': row[3],
                    'packing': row[4],
                    'unitPrice': row[5],
                    'amount': row[6]
                })
            
            # Get payments
            cursor.execute('''
                SELECT amount, date, remarks FROM payments 
                WHERE party_name = ? 
                ORDER BY date
            ''', (party_name,))
            
            for row in cursor.fetchall():
                transactions.append({
                    'type': 'payment',
                    'date': row[1],
                    'remarks': row[2],
                    'amount': row[0]
                })
            
            # Sort by date
            transactions.sort(key=lambda x: x['date'])
            
            return {
                "partyName": party_name,
                "openingBalance": balance_info['initialOpeningBalance'],
                "currentBalance": balance_info['balance'],
                "transactions": transactions
            }
        except Exception as e:
            return {"partyName": party_name, "openingBalance": 0, "currentBalance": 0, "transactions": []}
        finally:
            conn.close()
    
    def add_stock(self, stock_data):
        """Add stock items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            for item in stock_data['items']:
                cursor.execute('''
                    INSERT INTO stock (product_name, batch_no, date, quantity)
                    VALUES (?, ?, ?, ?)
                ''', (
                    item['productName'],
                    item.get('batchNo', ''),
                    item['date'],
                    item['quantity']
                ))
            
            conn.commit()
            return {"message": f"{len(stock_data['items'])} stock item(s) added successfully!"}
            
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_stock(self):
        """Get all stock items"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id, product_name, batch_no, date, quantity FROM stock ORDER BY product_name, date DESC")
            
            stock_items = []
            for row in cursor.fetchall():
                stock_items.append({
                    "id": row[0],
                    "productName": row[1],
                    "batchNo": row[2],
                    "date": row[3],
                    "quantity": row[4]
                })
            
            return stock_items
        except Exception as e:
            return []
        finally:
            conn.close()

# Create backend instance
backend = NutritionBackend('invoice_app_v4.db')

class PDFGenerator(FPDF):
    def __init__(self):
        super().__init__()
        # Use a font that supports basic characters
        self.add_page()
    
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'NUTRION', 0, 1, 'C')
        self.set_font('Arial', '', 12)
        self.cell(0, 10, 'Address: Pearl City Sargodha Road Faisalabad', 0, 1, 'C')
        self.cell(0, 10, 'Contact: +923007993003', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_invoice_pdf(invoice_data):
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Invoice header
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'TAX INVOICE', 0, 1, 'C')
    pdf.ln(10)
    
    # Party and invoice details
    pdf.set_font('Arial', '', 12)
    pdf.cell(40, 10, 'Bill To:', 0, 0)
    pdf.cell(0, 10, invoice_data['partyName'], 0, 1)
    
    pdf.cell(40, 10, 'Invoice #:', 0, 0)
    pdf.cell(0, 10, invoice_data['invoiceNumber'], 0, 1)
    
    pdf.cell(40, 10, 'Date:', 0, 0)
    pdf.cell(0, 10, invoice_data['date'], 0, 1)
    pdf.ln(10)
    
    # Items table header
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(10, 10, 'Sr', 1, 0, 'C', True)
    pdf.cell(80, 10, 'Product Name', 1, 0, 'C', True)
    pdf.cell(20, 10, 'Qty', 1, 0, 'C', True)
    pdf.cell(20, 10, 'Packing', 1, 0, 'C', True)
    pdf.cell(25, 10, 'Unit Price', 1, 0, 'C', True)
    pdf.cell(25, 10, 'Amount', 1, 1, 'C', True)
    
    # Items
    pdf.set_fill_color(255, 255, 255)
    for i, item in enumerate(invoice_data['items'], 1):
        pdf.cell(10, 10, str(i), 1, 0, 'C')
        pdf.cell(80, 10, item['productName'], 1, 0)
        pdf.cell(20, 10, str(item['qty']), 1, 0, 'C')
        pdf.cell(20, 10, item['packing'], 1, 0, 'C')
        pdf.cell(25, 10, f"PKR {format_currency_indian(item['unitPrice'])}", 1, 0, 'R')
        pdf.cell(25, 10, f"PKR {format_currency_indian(item['amount'])}", 1, 1, 'R')
    
    pdf.ln(10)
    
    # Totals
    pdf.cell(150, 10, 'Subtotal:', 0, 0, 'R')
    pdf.cell(30, 10, f"PKR {format_currency_indian(invoice_data['totalAmount'])}", 0, 1, 'R')
    
    pdf.cell(150, 10, 'Previous Balance:', 0, 0, 'R')
    pdf.cell(30, 10, f"PKR {format_currency_indian(invoice_data['previousBalance'])}", 0, 1, 'R')
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 10, 'Grand Total:', 0, 0, 'R')
    pdf.cell(30, 10, f"PKR {format_currency_indian(invoice_data['grandTotal'])}", 0, 1, 'R')
    
    return pdf

def generate_payment_receipt_pdf(payment_data):
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Payment receipt header
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'PAYMENT RECEIPT', 0, 1, 'C')
    pdf.ln(10)
    
    # Payment details
    pdf.set_font('Arial', '', 12)
    pdf.cell(40, 10, 'Received From:', 0, 0)
    pdf.cell(0, 10, payment_data['partyName'], 0, 1)
    
    pdf.cell(40, 10, 'Amount:', 0, 0)
    pdf.cell(0, 10, f"PKR {format_currency_indian(payment_data['amount'])}", 0, 1)
    
    pdf.cell(40, 10, 'Date:', 0, 0)
    pdf.cell(0, 10, payment_data['date'], 0, 1)
    
    if payment_data.get('remarks'):
        pdf.cell(40, 10, 'Remarks:', 0, 0)
        pdf.cell(0, 10, payment_data['remarks'], 0, 1)
    
    pdf.ln(10)
    pdf.set_font('Arial', 'I', 10)
    pdf.cell(0, 10, 'This is a computer generated receipt.', 0, 1, 'C')
    
    return pdf

def get_pdf_download_link(pdf, filename):
    """Generate a download link for PDF"""
    try:
        # Use latin1 encoding which is more compatible
        pdf_output = pdf.output(dest='S').encode('latin1', 'replace')
        b64 = base64.b64encode(pdf_output).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}">📄 Download {filename}</a>'
        return href
    except Exception as e:
        st.error(f"Error generating PDF download link: {str(e)}")
        return ""

def initialize_app():
    """Initialize application data"""
    if not st.session_state.initialized:
        try:
            # Get next invoice number
            result = backend.get_next_invoice_number()
            if result:
                st.session_state.current_invoice_number = result.get('nextInvoiceNumber', '1')
            
            # Get parties list
            result = backend.get_parties()
            if result:
                st.session_state.parties = [party['name'] for party in result]
            
            st.session_state.initialized = True
            st.success("✅ Application initialized successfully with existing database!")
        except Exception as e:
            st.error(f"Initialization error: {str(e)}")

# UI Components - Enhanced with better styling
def render_payment_section():
    """Payment Received Section"""
    st.markdown("""
    <style>
    .payment-header {
        background-color: #FFA500;
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="payment-header"><h2>💰 Payment Received</h2></div>', unsafe_allow_html=True)
    
    with st.form("payment_form", clear_on_submit=True):
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="payment_party")
        with col2:
            amount = st.number_input("Amount Received", min_value=0.0, step=0.01, key="payment_amount")
        with col3:
            remarks = st.text_input("Remarks", placeholder="e.g., Advance, Bill Clearance", key="payment_remarks")
        with col4:
            payment_date = st.date_input("Payment Date", value=date.today(), key="payment_date")
        
        submitted = st.form_submit_button("💾 Save Payment", use_container_width=True)
        if submitted:
            if not party_name:
                st.error("Party name is required")
                return
            if amount <= 0:
                st.error("Amount must be greater than 0")
                return
                
            payment_data = {
                "partyName": party_name,
                "amount": amount,
                "date": payment_date.isoformat(),
                "remarks": remarks
            }
            
            try:
                result = backend.record_payment(payment_data)
                if result:
                    st.success("✅ Payment recorded successfully!")
                    st.session_state.last_payment_details = payment_data
                    # Refresh parties list
                    parties = backend.get_parties()
                    st.session_state.parties = [party['name'] for party in parties]
                    
                    # Show download button
                    pdf = generate_payment_receipt_pdf(payment_data)
                    st.markdown(get_pdf_download_link(pdf, f"payment_receipt_{payment_date}.pdf"), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error recording payment: {str(e)}")

def render_payment_range_section():
    """Payments Range Download"""
    st.markdown('<div class="payment-header"><h2>📥 Payments Range Download</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", key="payment_range_start")
    with col2:
        end_date = st.date_input("End Date", key="payment_range_end")
    
    if st.button("📄 Download Payments PDF", use_container_width=True):
        if start_date and end_date:
            if start_date <= end_date:
                try:
                    payments = backend.get_payments(start_date=start_date.isoformat(), end_date=end_date.isoformat())
                    if payments:
                        # Generate PDF for payments
                        pdf = PDFGenerator()
                        pdf.add_page()
                        pdf.set_font('Arial', 'B', 16)
                        pdf.cell(0, 10, 'Payments Report', 0, 1, 'C')
                        pdf.ln(10)
                        
                        # Add payments table
                        pdf.set_fill_color(200, 220, 255)
                        pdf.cell(20, 10, 'ID', 1, 0, 'C', True)
                        pdf.cell(60, 10, 'Party Name', 1, 0, 'C', True)
                        pdf.cell(40, 10, 'Date', 1, 0, 'C', True)
                        pdf.cell(40, 10, 'Amount', 1, 1, 'C', True)
                        
                        pdf.set_fill_color(255, 255, 255)
                        total_amount = 0
                        for payment in payments:
                            pdf.cell(20, 10, str(payment['paymentId']), 1, 0)
                            pdf.cell(60, 10, payment['partyName'], 1, 0)
                            pdf.cell(40, 10, payment['date'], 1, 0)
                            pdf.cell(40, 10, f"PKR {format_currency_indian(payment['amount'])}", 1, 1, 'R')
                            total_amount += payment['amount']
                        
                        pdf.ln(10)
                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(120, 10, 'Total Amount:', 0, 0, 'R')
                        pdf.cell(40, 10, f"PKR {format_currency_indian(total_amount)}", 0, 1, 'R')
                        
                        st.markdown(get_pdf_download_link(pdf, f"payments_{start_date}_{end_date}.pdf"), unsafe_allow_html=True)
                    else:
                        st.info("No payments found in the selected date range")
                except Exception as e:
                    st.error(f"Error generating PDF: {str(e)}")
            else:
                st.error("Start date must be before end date")
        else:
            st.error("Please select both start and end dates")

def render_delete_payment_section():
    """Payment Delete Section"""
    st.markdown('<div class="payment-header"><h2>🗑️ Payment Management</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        party_name = st.selectbox("Select Party", [""] + st.session_state.parties, key="delete_payment_party")
    with col2:
        if st.button("🔍 View Payments", use_container_width=True):
            if party_name:
                try:
                    payments = backend.get_payments(party_name=party_name)
                    if payments:
                        display_payments_for_deletion(payments, party_name)
                    else:
                        st.info("No payments found for this party")
                except Exception as e:
                    st.error(f"Error fetching payments: {str(e)}")
            else:
                st.error("Please select a party name")

def display_payments_for_deletion(payments, party_name):
    """Display payments for deletion"""
    if payments:
        # Format amounts for display
        formatted_payments = []
        for payment in payments:
            formatted_payment = payment.copy()
            formatted_payment['amount_display'] = f"PKR {format_currency_indian(payment['amount'])}"
            formatted_payments.append(formatted_payment)
        
        df = pd.DataFrame(formatted_payments)
        # Display only relevant columns
        display_df = df[['paymentId', 'date', 'remarks', 'amount_display']]
        st.dataframe(display_df, use_container_width=True)
        
        # Show summary
        total_amount = sum(payment['amount'] for payment in payments)
        st.metric("Total Payments", f"PKR {format_currency_indian(total_amount)}")
        
        # Download button for party payments
        if st.button("📄 Download Party Payments PDF", use_container_width=True):
            pdf = generate_payment_receipt_pdf({
                "partyName": party_name,
                "amount": total_amount,
                "date": date.today().isoformat(),
                "remarks": f"Total payments for {party_name}"
            })
            st.markdown(get_pdf_download_link(pdf, f"payments_{party_name}.pdf"), unsafe_allow_html=True)
        
        # Delete individual payments
        st.subheader("Delete Payment")
        payment_ids = [p['paymentId'] for p in payments]
        selected_payment_id = st.selectbox("Select Payment ID to delete", payment_ids)
        
        if st.button("🗑️ Delete Selected Payment", type="secondary", use_container_width=True):
            try:
                result = backend.delete_payment(selected_payment_id)
                if result:
                    st.success("✅ Payment deleted successfully!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error deleting payment: {str(e)}")

def render_ledger_section():
    """Feed Mills Ledger Details"""
    st.markdown('<div class="payment-header"><h2>📊 Feed Mills Ledger Details</h2></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        party_name = st.selectbox("Select Party", [""] + st.session_state.parties, key="ledger_party")
    with col2:
        if st.button("👀 View Ledger", use_container_width=True):
            if party_name:
                try:
                    ledger_data = backend.get_ledger(party_name)
                    if ledger_data:
                        display_ledger(ledger_data)
                    else:
                        st.info("No ledger data found for this party")
                except Exception as e:
                    st.error(f"Error fetching ledger: {str(e)}")
            else:
                st.error("Please select a party name")

def display_ledger(ledger_data):
    """Display party ledger"""
    st.subheader(f"Ledger for: {ledger_data.get('partyName', '')}")
    
    transactions = ledger_data.get('transactions', [])
    if transactions:
        # Format amounts for display
        formatted_transactions = []
        for tx in transactions:
            formatted_tx = tx.copy()
            formatted_tx['amount_display'] = f"PKR {format_currency_indian(tx['amount'])}"
            if 'unitPrice' in tx:
                formatted_tx['unitPrice_display'] = f"PKR {format_currency_indian(tx['unitPrice'])}"
            formatted_transactions.append(formatted_tx)
        
        df = pd.DataFrame(formatted_transactions)
        st.dataframe(df, use_container_width=True)
        
        # Show opening and current balance
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Opening Balance", f"PKR {format_currency_indian(ledger_data.get('openingBalance', 0))}")
        with col2:
            st.metric("Current Balance", f"PKR {format_currency_indian(ledger_data.get('currentBalance', 0))}")
        with col3:
            total_transactions = len(transactions)
            st.metric("Total Transactions", total_transactions)
        
        # Store ledger data for PDF download
        st.session_state.current_ledger_data = ledger_data
        
        # Download ledger PDF
        if st.button("📄 Download Ledger PDF", use_container_width=True):
            pdf = generate_ledger_pdf(ledger_data)
            st.markdown(get_pdf_download_link(pdf, f"ledger_{ledger_data['partyName']}.pdf"), unsafe_allow_html=True)
    else:
        st.info("No transactions found for this party")

def generate_ledger_pdf(ledger_data):
    """Generate PDF for ledger"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f"Ledger for {ledger_data['partyName']}", 0, 1, 'C')
    pdf.ln(10)
    
    # Ledger details
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f"Opening Balance: PKR {format_currency_indian(ledger_data['openingBalance'])}", 0, 1)
    pdf.cell(0, 10, f"Current Balance: PKR {format_currency_indian(ledger_data['currentBalance'])}", 0, 1)
    pdf.ln(10)
    
    # Transactions table
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(30, 10, 'Date', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Type', 1, 0, 'C', True)
    pdf.cell(60, 10, 'Description', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Amount', 1, 1, 'C', True)
    
    pdf.set_fill_color(255, 255, 255)
    for tx in ledger_data['transactions']:
        pdf.cell(30, 10, tx['date'], 1, 0)
        pdf.cell(40, 10, tx['type'], 1, 0)
        
        if tx['type'] == 'invoice_item':
            desc = f"{tx['productName']} - {tx['qty']} {tx['packing']}"
        else:
            desc = f"Payment - {tx.get('remarks', '')}"
        
        pdf.cell(60, 10, desc[:35], 1, 0)  # Truncate long descriptions
        pdf.cell(40, 10, f"PKR {format_currency_indian(tx['amount'])}", 1, 1, 'R')
    
    return pdf

def render_stock_section():
    """Stock Management"""
    st.markdown('<div class="payment-header"><h2>📦 Stock Management</h2></div>', unsafe_allow_html=True)
    
    # Add stock form
    with st.form("stock_form", clear_on_submit=True):
        st.subheader("Add Stock Item")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            product_name = st.selectbox("Product Name", PRODUCTS, key="stock_product")
        with col2:
            batch_no = st.text_input("Batch No.", placeholder="e.g., B-12345", key="batch_no")
        with col3:
            stock_date = st.date_input("Date", value=date.today(), key="stock_date")
        with col4:
            quantity = st.number_input("Quantity", min_value=0, step=1, key="stock_quantity")
        
        submitted = st.form_submit_button("➕ Add Stock Item", use_container_width=True)
        if submitted:
            if product_name and quantity > 0:
                new_item = {
                    "productName": product_name,
                    "batchNo": batch_no,
                    "date": stock_date.isoformat(),
                    "quantity": quantity
                }
                st.session_state.stock_items.append(new_item)
                st.success("✅ Stock item added to list!")
            else:
                st.error("Please fill all required fields")
    
    # Display current stock items to be added
    if st.session_state.stock_items:
        st.subheader("📋 Stock Items to be Added")
        stock_df = pd.DataFrame(st.session_state.stock_items)
        st.dataframe(stock_df, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 Save All Stock Items", use_container_width=True):
                try:
                    result = backend.add_stock({"items": st.session_state.stock_items})
                    if result:
                        st.success(result.get('message', '✅ Stock items saved successfully!'))
                        st.session_state.stock_items = []
                except Exception as e:
                    st.error(f"Error saving stock: {str(e)}")
        with col2:
            if st.button("🗑️ Clear List", use_container_width=True):
                st.session_state.stock_items = []
                st.rerun()
    
    # Available stock
    st.subheader("📊 Available Stock")
    if st.button("🔄 Refresh Stock", use_container_width=True):
        try:
            stock_data = backend.get_stock()
            if stock_data:
                display_stock_data(stock_data)
            else:
                st.info("No stock data available")
        except Exception as e:
            st.error(f"Error fetching stock: {str(e)}")

def display_stock_data(stock_data):
    """Display available stock"""
    if stock_data:
        df = pd.DataFrame(stock_data)
        st.dataframe(df, use_container_width=True)
        
        # Show stock summary
        total_items = len(stock_data)
        total_quantity = sum(item['quantity'] for item in stock_data)
        unique_products = len(set(item['productName'] for item in stock_data))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Products", unique_products)
        with col2:
            st.metric("Total Stock Items", total_items)
        with col3:
            st.metric("Total Quantity", format_number_indian(total_quantity))
        
        # Download stock report
        if st.button("📄 Download Stock Report PDF", use_container_width=True):
            pdf = generate_stock_report_pdf(stock_data)
            st.markdown(get_pdf_download_link(pdf, "stock_report.pdf"), unsafe_allow_html=True)
    else:
        st.info("No stock data available")

def generate_stock_report_pdf(stock_data):
    """Generate stock report PDF"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Stock Report', 0, 1, 'C')
    pdf.ln(10)
    
    # Stock table
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(20, 10, 'ID', 1, 0, 'C', True)
    pdf.cell(60, 10, 'Product Name', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Batch No.', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Date', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Quantity', 1, 1, 'C', True)
    
    pdf.set_fill_color(255, 255, 255)
    for item in stock_data:
        pdf.cell(20, 10, str(item['id']), 1, 0)
        pdf.cell(60, 10, item['productName'], 1, 0)
        pdf.cell(40, 10, item.get('batchNo', 'N/A'), 1, 0)
        pdf.cell(40, 10, item['date'], 1, 0)
        pdf.cell(30, 10, format_number_indian(item['quantity']), 1, 1, 'C')
    
    return pdf

def render_invoice_creation_section():
    """Main Invoice Creation Section"""
    st.markdown('<div class="payment-header"><h2>📄 Create New Invoice</h2></div>', unsafe_allow_html=True)
    
    # Party and basic info
    col1, col2, col3 = st.columns(3)
    with col1:
        party_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="invoice_party")
    with col2:
        invoice_date = st.date_input("Date", value=date.today(), key="invoice_date")
    with col3:
        st.text_input("Invoice #", value=st.session_state.current_invoice_number, disabled=True, key="invoice_number")
    
    # Invoice items section
    st.subheader("🛒 Invoice Items")
    render_invoice_items()
    
    # Calculate totals
    subtotal = calculate_subtotal()
    
    # Get previous balance for the party
    previous_balance = 0.0
    if party_name:
        try:
            balance_info = backend.get_party_balance(party_name)
            previous_balance = balance_info['balance']
        except:
            pass
    
    gst_percentage = st.number_input("GST %", min_value=0.0, max_value=100.0, value=0.0, step=0.1, key="gst_percentage")
    grand_total = calculate_grand_total(subtotal, gst_percentage, previous_balance)
    
    # Display totals with formatted currency
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Subtotal", f"PKR {format_currency_indian(subtotal)}")
    with col2:
        st.metric("Previous Balance", f"PKR {format_currency_indian(previous_balance)}")
    with col3:
        gst_amount = subtotal * (gst_percentage / 100)
        st.metric("GST Amount", f"PKR {format_currency_indian(gst_amount)}")
    with col4:
        st.metric("Grand Total", f"PKR {format_currency_indian(grand_total)}", 
                 delta=f"PKR {format_currency_indian(grand_total - subtotal - previous_balance)}")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("💾 Save Invoice", type="primary", use_container_width=True):
            save_invoice(party_name, invoice_date, gst_percentage, previous_balance, grand_total)
    with col2:
        if st.button("📄 Download PDF", use_container_width=True):
            if st.session_state.invoice_items and party_name:
                invoice_data = {
                    "partyName": party_name,
                    "invoiceNumber": st.session_state.current_invoice_number,
                    "date": invoice_date.isoformat(),
                    "items": st.session_state.invoice_items,
                    "totalAmount": subtotal,
                    "previousBalance": previous_balance,
                    "grandTotal": grand_total
                }
                pdf = generate_invoice_pdf(invoice_data)
                st.markdown(get_pdf_download_link(pdf, f"invoice_{st.session_state.current_invoice_number}.pdf"), unsafe_allow_html=True)
            else:
                st.error("Please add items and select a party first")
    with col3:
        if st.button("🗑️ Clear Form", use_container_width=True):
            st.session_state.invoice_items = []
            st.rerun()
    with col4:
        if st.button("🔄 Refresh", use_container_width=True):
            st.rerun()

def render_invoice_items():
    """Render invoice items with add/remove functionality"""
    # Add new item controls
    st.write("### Add New Item")
    col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 1])
    
    with col1:
        new_product = st.selectbox("Product", [""] + PRODUCTS, key="new_product")
    with col2:
        new_qty = st.number_input("Qty", min_value=0.0, step=0.1, key="new_qty")
    with col3:
        new_packing = st.selectbox("Packing", PACKING_OPTIONS, key="new_packing")
    with col4:
        new_unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01, key="new_unit_price")
    with col5:
        new_amount = new_qty * new_unit_price
        st.text_input("Amount", value=f"PKR {format_currency_indian(new_amount)}", disabled=True, key="new_amount_display")
    
    # Add button
    with col6:
        st.write("")  # Spacer
        if st.button("➕ Add", key="add_item", use_container_width=True):
            if new_product and new_qty > 0 and new_unit_price > 0:
                new_item = {
                    "productName": new_product,
                    "qty": new_qty,
                    "packing": new_packing,
                    "unitPrice": new_unit_price,
                    "amount": new_amount
                }
                st.session_state.invoice_items.append(new_item)
                st.rerun()
            else:
                st.error("Please fill all item fields correctly")
    
    # Display current items
    if st.session_state.invoice_items:
        st.write("### Current Items")
        for i, item in enumerate(st.session_state.invoice_items):
            col1, col2, col3, col4, col5, col6 = st.columns([3, 2, 2, 2, 2, 1])
            with col1:
                st.text(item['productName'])
            with col2:
                st.text(str(item['qty']))
            with col3:
                st.text(item['packing'])
            with col4:
                st.text(f"PKR {format_currency_indian(item['unitPrice'])}")
            with col5:
                st.text(f"PKR {format_currency_indian(item['amount'])}")
            with col6:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.invoice_items.pop(i)
                    st.rerun()

def calculate_subtotal():
    """Calculate invoice subtotal"""
    return sum(item['amount'] for item in st.session_state.invoice_items)

def calculate_grand_total(subtotal, gst_percentage, previous_balance):
    """Calculate grand total"""
    gst_amount = subtotal * (gst_percentage / 100)
    return subtotal + gst_amount + previous_balance

def save_invoice(party_name, invoice_date, gst_percentage, previous_balance, grand_total):
    """Save invoice to backend"""
    if not party_name:
        st.error("Party name is required")
        return
        
    if not st.session_state.invoice_items:
        st.error("Please add at least one invoice item")
        return
    
    invoice_data = {
        "partyName": party_name,
        "date": invoice_date.isoformat(),
        "invoiceNumber": st.session_state.current_invoice_number,
        "items": st.session_state.invoice_items,
        "totalAmount": calculate_subtotal(),
        "previousBalance": previous_balance,
        "grandTotal": grand_total
    }
    
    try:
        result = backend.create_invoice(invoice_data)
        if result:
            st.success("✅ Invoice saved successfully!")
            # Update invoice number and clear items
            st.session_state.current_invoice_number = result.get('nextInvoiceNumber', str(int(st.session_state.current_invoice_number) + 1))
            st.session_state.invoice_items = []
            # Refresh parties list
            parties = backend.get_parties()
            st.session_state.parties = [party['name'] for party in parties]
    except Exception as e:
        st.error(f"Error saving invoice: {str(e)}")

def render_reports_section():
    """Enhanced Reports Section with all HTML features"""
    st.markdown('<div class="payment-header"><h2>📈 Reports & Analytics</h2></div>', unsafe_allow_html=True)
    
    # Invoice range report
    st.subheader("📋 Invoice Range Report")
    col1, col2 = st.columns(2)
    with col1:
        inv_start_date = st.date_input("Start Date", key="invoice_range_start")
    with col2:
        inv_end_date = st.date_input("End Date", key="invoice_range_end")
    
    if st.button("Download Invoices PDF", key="invoice_range_btn", use_container_width=True):
        if inv_start_date and inv_end_date:
            try:
                invoices = backend.get_invoices_by_date_range(inv_start_date.isoformat(), inv_end_date.isoformat())
                if invoices:
                    # Generate combined PDF
                    pdf = PDFGenerator()
                    for invoice in invoices:
                        pdf.add_page()
                        # Create a simple invoice representation for the report
                        pdf.set_font('Arial', 'B', 14)
                        pdf.cell(0, 10, f"Invoice #{invoice['invoiceNumber']}", 0, 1, 'C')
                        pdf.ln(5)
                        pdf.set_font('Arial', '', 12)
                        pdf.cell(0, 10, f"Party: {invoice['partyName']}", 0, 1)
                        pdf.cell(0, 10, f"Date: {invoice['date']}", 0, 1)
                        pdf.cell(0, 10, f"Total: PKR {format_currency_indian(invoice['totalAmount'])}", 0, 1)
                        pdf.ln(10)
                    st.markdown(get_pdf_download_link(pdf, f"invoices_{inv_start_date}_{inv_end_date}.pdf"), unsafe_allow_html=True)
                else:
                    st.info("No invoices found in the selected date range")
            except Exception as e:
                st.error(f"Error generating invoices PDF: {str(e)}")
    
    # Product sales report
    st.subheader("📊 Product Sales Summary")
    col1, col2 = st.columns(2)
    with col1:
        ps_start_date = st.date_input("Start Date", key="product_sales_start")
    with col2:
        ps_end_date = st.date_input("End Date", key="product_sales_end")
    
    if st.button("Product Sales Summary PDF", key="product_sales_btn", use_container_width=True):
        if ps_start_date and ps_end_date:
            try:
                sales_summary = backend.get_product_sales_summary(ps_start_date.isoformat(), ps_end_date.isoformat())
                if sales_summary:
                    pdf = generate_product_sales_pdf(sales_summary, ps_start_date, ps_end_date)
                    st.markdown(get_pdf_download_link(pdf, f"product_sales_{ps_start_date}_{ps_end_date}.pdf"), unsafe_allow_html=True)
                else:
                    st.info("No sales data found in the selected date range")
            except Exception as e:
                st.error(f"Error generating sales summary PDF: {str(e)}")
    
    # Party invoices
    st.subheader("👥 Party Invoices")
    col1, col2, col3 = st.columns(3)
    with col1:
        party_inv_name = st.selectbox("Party Name", [""] + st.session_state.parties, key="party_invoices")
    with col2:
        pi_start_date = st.date_input("Start Date", key="party_invoices_start")
    with col3:
        pi_end_date = st.date_input("End Date", key="party_invoices_end")
    
    if st.button("Download Party Invoices", key="party_invoices_btn", use_container_width=True):
        if party_inv_name and pi_start_date and pi_end_date:
            try:
                invoices = backend.get_invoices_by_party_and_date_range(party_inv_name, pi_start_date.isoformat(), pi_end_date.isoformat())
                if invoices:
                    # Generate combined PDF
                    pdf = PDFGenerator()
                    pdf.add_page()
                    pdf.set_font('Arial', 'B', 16)
                    pdf.cell(0, 10, f"Invoices for {party_inv_name}", 0, 1, 'C')
                    pdf.cell(0, 10, f"From {pi_start_date} to {pi_end_date}", 0, 1, 'C')
                    pdf.ln(10)
                    
                    for i, invoice in enumerate(invoices):
                        if i > 0:
                            pdf.ln(5)
                        pdf.set_font('Arial', 'B', 12)
                        pdf.cell(0, 10, f"Invoice #{invoice['invoiceNumber']} - {invoice['date']}", 0, 1)
                        pdf.set_font('Arial', '', 10)
                        pdf.cell(0, 10, f"Total: PKR {format_currency_indian(invoice['totalAmount'])} | Grand Total: PKR {format_currency_indian(invoice['grandTotal'])}", 0, 1)
                    
                    st.markdown(get_pdf_download_link(pdf, f"invoices_{party_inv_name}_{pi_start_date}_{pi_end_date}.pdf"), unsafe_allow_html=True)
                else:
                    st.info(f"No invoices found for {party_inv_name} in the selected date range")
            except Exception as e:
                st.error(f"Error generating party invoices PDF: {str(e)}")
    
    # All Party Balances
    st.subheader("💰 All Party Balances")
    if st.button("Download All Party Balances PDF", key="all_balances_btn", use_container_width=True):
        try:
            ledgers = backend.get_all_party_ledgers()
            if ledgers:
                pdf = generate_all_party_balances_pdf(ledgers)
                st.markdown(get_pdf_download_link(pdf, "all_party_balances.pdf"), unsafe_allow_html=True)
            else:
                st.info("No party data available")
        except Exception as e:
            st.error(f"Error generating all party balances PDF: {str(e)}")
    
    # Bilty Expense Report
    st.subheader("🚚 Bilty Expense Report")
    col1, col2 = st.columns(2)
    with col1:
        bilty_start_date = st.date_input("Start Date", key="bilty_start")
    with col2:
        bilty_end_date = st.date_input("End Date", key="bilty_end")
    
    if st.button("Download Bilty Expense Report", key="bilty_btn", use_container_width=True):
        if bilty_start_date and bilty_end_date:
            try:
                payments = backend.get_payments(start_date=bilty_start_date.isoformat(), end_date=bilty_end_date.isoformat())
                bilty_payments = [p for p in payments if p.get('remarks', '').lower().find('bilty') != -1]
                if bilty_payments:
                    pdf = generate_bilty_expense_pdf(bilty_payments, bilty_start_date, bilty_end_date)
                    st.markdown(get_pdf_download_link(pdf, f"bilty_expense_{bilty_start_date}_{bilty_end_date}.pdf"), unsafe_allow_html=True)
                else:
                    st.info("No bilty expense payments found in the selected date range")
            except Exception as e:
                st.error(f"Error generating bilty expense PDF: {str(e)}")

def generate_product_sales_pdf(sales_summary, start_date, end_date):
    """Generate product sales summary PDF"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Product Sales Summary', 0, 1, 'C')
    pdf.cell(0, 10, f'{start_date} to {end_date}', 0, 1, 'C')
    pdf.ln(10)
    
    # Sales table
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(80, 10, 'Product Name', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Packing', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Total Quantity', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Total Amount', 1, 1, 'C', True)
    
    pdf.set_fill_color(255, 255, 255)
    total_revenue = 0
    for item in sales_summary:
        pdf.cell(80, 10, item['productName'], 1, 0)
        pdf.cell(30, 10, item['packing'], 1, 0)
        pdf.cell(40, 10, format_number_indian(item['totalQty']), 1, 0, 'C')
        pdf.cell(40, 10, f"PKR {format_currency_indian(item['totalAmount'])}", 1, 1, 'R')
        total_revenue += item['totalAmount']
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 10, 'Total Revenue:', 0, 0, 'R')
    pdf.cell(40, 10, f"PKR {format_currency_indian(total_revenue)}", 0, 1, 'R')
    
    return pdf

def generate_all_party_balances_pdf(ledgers):
    """Generate PDF for all party balances"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'All Party Balances', 0, 1, 'C')
    pdf.ln(10)
    
    # Balances table
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(120, 10, 'Party Name', 1, 0, 'C', True)
    pdf.cell(60, 10, 'Current Balance', 1, 1, 'C', True)
    
    pdf.set_fill_color(255, 255, 255)
    total_balance = 0
    for ledger in ledgers:
        pdf.cell(120, 10, ledger['partyName'], 1, 0)
        pdf.cell(60, 10, f"PKR {format_currency_indian(ledger['currentBalance'])}", 1, 1, 'R')
        total_balance += ledger['currentBalance']
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(120, 10, 'Total Outstanding:', 0, 0, 'R')
    pdf.cell(60, 10, f"PKR {format_currency_indian(total_balance)}", 0, 1, 'R')
    
    return pdf

def generate_bilty_expense_pdf(payments, start_date, end_date):
    """Generate bilty expense report PDF"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Bilty Expense Report', 0, 1, 'C')
    pdf.cell(0, 10, f'{start_date} to {end_date}', 0, 1, 'C')
    pdf.ln(10)
    
    # Payments table
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(20, 10, 'ID', 1, 0, 'C', True)
    pdf.cell(50, 10, 'Party Name', 1, 0, 'C', True)
    pdf.cell(40, 10, 'Date', 1, 0, 'C', True)
    pdf.cell(50, 10, 'Remarks', 1, 0, 'C', True)
    pdf.cell(30, 10, 'Amount', 1, 1, 'C', True)
    
    pdf.set_fill_color(255, 255, 255)
    total_amount = 0
    for payment in payments:
        pdf.cell(20, 10, str(payment['paymentId']), 1, 0)
        pdf.cell(50, 10, payment['partyName'], 1, 0)
        pdf.cell(40, 10, payment['date'], 1, 0)
        pdf.cell(50, 10, payment.get('remarks', '')[:25], 1, 0)  # Truncate long remarks
        pdf.cell(30, 10, f"PKR {format_currency_indian(payment['amount'])}", 1, 1, 'R')
        total_amount += payment['amount']
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(160, 10, 'Total Bilty Expense:', 0, 0, 'R')
    pdf.cell(30, 10, f"PKR {format_currency_indian(total_amount)}", 0, 1, 'R')
    
    return pdf

def main():
    st.set_page_config(
        page_title="NUTRION - Invoice, Ledger & Stock",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #FFA500;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: white;
    }
    .section-header {
        background: linear-gradient(135deg, #FFA500, #FF8C00);
        color: white;
        padding: 15px;
        border-radius: 10px;
        margin-top: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #FFA500;
        margin-bottom: 10px;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">NUTRION - Invoice, Ledger & Stock Management</h1>', unsafe_allow_html=True)
    
    # Initialize app
    initialize_app()
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📄 Invoices", 
        "💰 Payments", 
        "📊 Ledger", 
        "📦 Stock", 
        "📈 Reports",
        "⚙️ Settings"
    ])
    
    with tab1:
        render_invoice_creation_section()
    
    with tab2:
        render_payment_section()
        st.markdown("---")
        render_payment_range_section()
        st.markdown("---")
        render_delete_payment_section()
    
    with tab3:
        render_ledger_section()
    
    with tab4:
        render_stock_section()
    
    with tab5:
        render_reports_section()
    
    with tab6:
        st.markdown('<div class="section-header"><h2>⚙️ System Settings</h2></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Database Management")
            if st.button("🔄 Refresh Application Data", use_container_width=True):
                initialize_app()
                st.success("Application data refreshed!")
            
            if st.button("🗑️ Clear All Session Data", use_container_width=True):
                st.session_state.invoice_items = []
                st.session_state.stock_items = []
                st.success("Session data cleared!")
        
        with col2:
            st.subheader("System Information")
            st.info(f"Current Invoice Number: {st.session_state.current_invoice_number}")
            st.info(f"Total Parties: {len(st.session_state.parties)}")
            st.info(f"Products Available: {len(PRODUCTS)}")
    
    # Footer
  def main():
    st.markdown("---", unsafe_allow_html=True)

    st.markdown(
        """
        <div style="text-align:center; font-size:16px;">
            <b>
                <span style="color:black;">Data</span><span style="color:#007BFF;">nex</span> 
                <span style="color:#28A745;">Solutions</span>
            </b>
            <br>
            <span style="color:#555;">For any query, please contact 📞 <b>+92 320 7429422</b></span>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
