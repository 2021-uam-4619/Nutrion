import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, date
import tempfile
import os
import base64
from fpdf import FPDF
import json
import math

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

# Product packing mapping
PRODUCT_PACKING_MAP = {
    "Strophase G": "Kg", "Strophase P": "Kg", "Strozyme NSP": "Kg", 
    "SP200": "Kg", "SP300": "Kg", "SP300 Advance": "Kg", "Monica": "Kg", 
    "Linco Magic": "Kg", "Enra Magic": "Kg", "InduceAcid Plus": "Kg", 
    "InduceAcid Buty": "Kg", "Huntox": "Kg", "Strozyme XYL": "Kg", 
    "Super Ener Emusifier": "Kg", "Antioxdant": "Kg", "Toxin Binder Weilituo": "Kg", 
    "Toxin Clean": "Kg", "GutPro 60 (Tributyrin)": "Kg", "InduceAcid Liquid": "Ltr"
}
# Utility functions for number formatting
def format_currency_indian(value):
    """Format currency in Pakistani bank number system (international format)"""
    try:
        value = float(value)
        if value == 0:
            return "0"
        
        is_negative = value < 0
        value = abs(value)

        # Format with thousand separator (international system)
        if value.is_integer():
            formatted = "{:,.0f}".format(int(value))
        else:
            formatted = "{:,.2f}".format(value)

        return f"-{formatted}" if is_negative else formatted

    except (ValueError, TypeError):
        return "0"


def format_number_indian(value):
    """Format numbers in Pakistani bank number system (international format)"""
    try:
        value = float(value)
        if value == 0:
            return "0"

        is_negative = value < 0
        value = abs(value)

        # Format with thousand separator (international system)
        if value.is_integer():
            formatted = "{:,.0f}".format(int(value))
        else:
            formatted = "{:,.2f}".format(value)

        return f"-{formatted}" if is_negative else formatted

    except (ValueError, TypeError):
        return "0"
def convert_to_words(num):
    """Convert number to words (Indian numbering system)"""
    if num == 0:
        return 'Zero'
    
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 
            'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 
            'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def convert_below_thousand(n):
        if n == 0:
            return ''
        elif n < 20:
            return ones[n]
        elif n < 100:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 != 0 else '')
        else:
            return ones[n // 100] + ' Hundred' + (' ' + convert_below_thousand(n % 100) if n % 100 != 0 else '')
    
    def convert_number(n):
        if n == 0:
            return 'Zero'
        
        result = ''
        
        # Crore
        if n >= 10000000:
            crore = n // 10000000
            result += convert_below_thousand(crore) + ' Crore '
            n %= 10000000
        
        # Lakh
        if n >= 100000:
            lakh = n // 100000
            result += convert_below_thousand(lakh) + ' Lakh '
            n %= 100000
        
        # Thousand
        if n >= 1000:
            thousand = n // 1000
            result += convert_below_thousand(thousand) + ' Thousand '
            n %= 1000
        
        # Hundreds and below
        if n > 0:
            result += convert_below_thousand(n)
        
        return result.strip()
    
    rupees = int(num)
    paise = int(round((num - rupees) * 100))
    
    result = convert_number(rupees) + ' Rupees'
    if paise > 0:
        result += ' and ' + convert_number(paise) + ' Paise'
    
    return result + ' Only'

class NutritionBackend:
    def __init__(self, db_path='invoice_app_v4.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database connection and create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Check if tables exist, if not create them with proper schema
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='parties'")
        if not cursor.fetchone():
            # Create parties table
            cursor.execute('''
                CREATE TABLE parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    initial_opening_balance REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoices'")
        if not cursor.fetchone():
            # Create invoices table
            cursor.execute('''
                CREATE TABLE invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    invoice_number TEXT UNIQUE NOT NULL,
                    party_name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    total_amount REAL NOT NULL,
                    gst_percentage REAL DEFAULT 0,
                    gst_amount REAL DEFAULT 0,
                    previous_balance REAL NOT NULL,
                    grand_total REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        else:
            # Check if gst_percentage column exists, if not add it
            cursor.execute("PRAGMA table_info(invoices)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'gst_percentage' not in columns:
                cursor.execute("ALTER TABLE invoices ADD COLUMN gst_percentage REAL DEFAULT 0")
            if 'gst_amount' not in columns:
                cursor.execute("ALTER TABLE invoices ADD COLUMN gst_amount REAL DEFAULT 0")
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='invoice_items'")
        if not cursor.fetchone():
            # Create invoice_items table
            cursor.execute('''
                CREATE TABLE invoice_items (
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
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='payments'")
        if not cursor.fetchone():
            # Create payments table
            cursor.execute('''
                CREATE TABLE payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_name TEXT NOT NULL,
                    amount REAL NOT NULL,
                    date TEXT NOT NULL,
                    remarks TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='stock'")
        if not cursor.fetchone():
            # Create stock table
            cursor.execute('''
                CREATE TABLE stock (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_name TEXT NOT NULL,
                    batch_no TEXT,
                    date TEXT NOT NULL,
                    quantity REAL NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='opening_balance_adjustments'")
        if not cursor.fetchone():
            # Create opening_balance_adjustments table
            cursor.execute('''
                CREATE TABLE opening_balance_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    party_name TEXT NOT NULL,
                    adjustment_date TEXT NOT NULL,
                    old_balance REAL NOT NULL,
                    new_balance REAL NOT NULL,
                    reason TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            cursor.execute("SELECT name FROM parties ORDER BY name")
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
    
    def set_party_balance(self, party_name, new_balance, reason=None):
        """Set party opening balance with history tracking"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get current balance
            current_balance_info = self.get_party_balance(party_name)
            old_balance = current_balance_info['initialOpeningBalance']
            
            # Update party initial balance
            cursor.execute('''
                INSERT OR REPLACE INTO parties (name, initial_opening_balance) 
                VALUES (?, ?)
            ''', (party_name, new_balance))
            
            # Record adjustment history
            cursor.execute('''
                INSERT INTO opening_balance_adjustments 
                (party_name, adjustment_date, old_balance, new_balance, reason)
                VALUES (?, datetime('now'), ?, ?, ?)
            ''', (party_name, old_balance, new_balance, reason))
            
            conn.commit()
            return {"message": f"Opening balance updated to {new_balance}"}
        except Exception as e:
            conn.rollback()
            raise e
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
                INSERT INTO invoices (invoice_number, party_name, date, total_amount, 
                gst_percentage, gst_amount, previous_balance, grand_total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                invoice_data['invoiceNumber'],
                invoice_data['partyName'],
                invoice_data['date'],
                invoice_data['totalAmount'],
                invoice_data.get('gstPercentage', 0),
                invoice_data.get('gstAmount', 0),
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
    
    def get_invoice(self, invoice_number):
        """Get invoice by number"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT i.invoice_number, i.party_name, i.date, i.total_amount, 
                       i.gst_percentage, i.gst_amount, i.previous_balance, i.grand_total
                FROM invoices i
                WHERE i.invoice_number = ?
            ''', (invoice_number,))
            
            invoice_row = cursor.fetchone()
            if not invoice_row:
                return None
            
            invoice_data = {
                "invoiceNumber": invoice_row[0],
                "partyName": invoice_row[1],
                "date": invoice_row[2],
                "totalAmount": invoice_row[3],
                "gstPercentage": invoice_row[4],
                "gstAmount": invoice_row[5],
                "previousBalance": invoice_row[6],
                "grandTotal": invoice_row[7],
                "items": []
            }
            
            # Get items
            cursor.execute('''
                SELECT product_name, qty, packing, unit_price, amount
                FROM invoice_items 
                WHERE invoice_id = (SELECT id FROM invoices WHERE invoice_number = ?)
            ''', (invoice_number,))
            
            for item_row in cursor.fetchall():
                invoice_data["items"].append({
                    "productName": item_row[0],
                    "qty": item_row[1],
                    "packing": item_row[2],
                    "unitPrice": item_row[3],
                    "amount": item_row[4]
                })
            
            return invoice_data
        except Exception as e:
            return None
        finally:
            conn.close()
    
    def update_invoice(self, invoice_number, invoice_data):
        """Update existing invoice"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Update invoice
            cursor.execute('''
                UPDATE invoices 
                SET party_name = ?, date = ?, total_amount = ?, gst_percentage = ?, 
                    gst_amount = ?, previous_balance = ?, grand_total = ?
                WHERE invoice_number = ?
            ''', (
                invoice_data['partyName'],
                invoice_data['date'],
                invoice_data['totalAmount'],
                invoice_data.get('gstPercentage', 0),
                invoice_data.get('gstAmount', 0),
                invoice_data['previousBalance'],
                invoice_data['grandTotal'],
                invoice_number
            ))
            
            # Delete old items
            cursor.execute('''
                DELETE FROM invoice_items 
                WHERE invoice_id = (SELECT id FROM invoices WHERE invoice_number = ?)
            ''', (invoice_number,))
            
            # Insert new items
            invoice_id = cursor.execute('SELECT id FROM invoices WHERE invoice_number = ?', (invoice_number,)).fetchone()[0]
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
            return {"message": "Invoice updated successfully!"}
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def delete_invoice(self, invoice_number):
        """Delete invoice"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Get party name before deletion for refresh purposes
            cursor.execute("SELECT party_name FROM invoices WHERE invoice_number = ?", (invoice_number,))
            party_row = cursor.fetchone()
            party_name = party_row[0] if party_row else None
            
            # Delete invoice (cascade will delete items)
            cursor.execute("DELETE FROM invoices WHERE invoice_number = ?", (invoice_number,))
            conn.commit()
            
            return {
                "message": "Invoice deleted successfully!",
                "partyName": party_name
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
            
            query += " ORDER BY date"
            
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
                SELECT i.invoice_number, i.party_name, i.date, i.total_amount, 
                       i.gst_percentage, i.gst_amount, i.previous_balance, i.grand_total,
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
                        "gstPercentage": row[4],
                        "gstAmount": row[5],
                        "previousBalance": row[6],
                        "grandTotal": row[7],
                        "items": []
                    }
                
                invoices[invoice_number]["items"].append({
                    "productName": row[8],
                    "qty": row[9],
                    "packing": row[10],
                    "unitPrice": row[11],
                    "amount": row[12]
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
                SELECT i.invoice_number, i.party_name, i.date, i.total_amount, 
                       i.gst_percentage, i.gst_amount, i.previous_balance, i.grand_total,
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
                        "gstPercentage": row[4],
                        "gstAmount": row[5],
                        "previousBalance": row[6],
                        "grandTotal": row[7],
                        "items": []
                    }
                
                invoices[invoice_number]["items"].append({
                    "productName": row[8],
                    "qty": row[9],
                    "packing": row[10],
                    "unitPrice": row[11],
                    "amount": row[12]
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
            cursor.execute("SELECT name FROM parties ORDER BY name")
            parties = [row[0] for row in cursor.fetchall()]
            
            ledgers = []
            for party in parties:
                balance_info = self.get_party_balance(party)
                # Only include parties with non-zero balance
                if balance_info['balance'] != 0:
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

    def get_opening_balance_history(self, party_name):
        """Get opening balance adjustment history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT adjustment_date, old_balance, new_balance, reason, created_at
                FROM opening_balance_adjustments
                WHERE party_name = ?
                ORDER BY created_at DESC
            ''', (party_name,))
            
            history = []
            for row in cursor.fetchall():
                history.append({
                    "adjustment_date": row[0],
                    "old_balance": row[1],
                    "new_balance": row[2],
                    "reason": row[3],
                    "created_at": row[4]
                })
            
            return history
        except Exception as e:
            return []
        finally:
            conn.close()

    def get_all_invoice_numbers(self):
        """Get all invoice numbers for search functionality"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT invoice_number FROM invoices ORDER BY CAST(invoice_number AS INTEGER) DESC")
            invoice_numbers = [row[0] for row in cursor.fetchall()]
            return invoice_numbers
        except Exception as e:
            return []
        finally:
            conn.close()

# Create backend instance with your existing database
backend = NutritionBackend('invoice_app_v4.db')

class PDFGenerator(FPDF):
    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation=orientation, unit=unit, format=format)
        self.set_auto_page_break(auto=True, margin=15)
        self.company_name = "NUTRION"
        self.company_address = "Address: Pearl City Sargodha Road Faisalabad"
        self.company_contact = "Contact: +923007993003"
        self.primary_color = (255, 165, 0)  # Orange color like HTML
        self.secondary_color = (40, 167, 69)  # Green color
    
    def header(self):
        # Only add header if we're on the first page and have content
        if self.page_no() == 1:
            # Company header with orange background like HTML
            self.set_fill_color(*self.primary_color)
            self.set_text_color(255, 255, 255)
            self.set_font('Arial', 'B', 20)
            self.cell(0, 15, self.company_name, 0, 1, 'C', True)
            
            self.set_font('Arial', '', 10)
            self.cell(0, 5, self.company_address, 0, 1, 'C', True)
            self.cell(0, 5, self.company_contact, 0, 1, 'C', True)
            
            # Line separator
            self.set_draw_color(*self.primary_color)
            self.set_line_width(0.5)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_invoice_pdf(invoice_data):
    """Generate invoice PDF matching HTML design"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Invoice header with orange background
    pdf.set_fill_color(*pdf.primary_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'TAX INVOICE', 0, 1, 'C', True)
    pdf.ln(5)
    
    # Party and invoice details - two column layout like HTML
    pdf.set_text_color(0, 0, 0)
    
    # Left column - Bill To
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(40, 8, 'Bill To:', 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, invoice_data["partyName"], 0, 1)
    pdf.ln(2)
    
    # Right column - Invoice details
    pdf.set_x(120)  # Move to right side
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(30, 8, 'Invoice #:', 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, invoice_data["invoiceNumber"], 0, 1)
    
    pdf.set_x(120)
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(30, 8, 'Date:', 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, invoice_data["date"], 0, 1)
    pdf.ln(8)
    
    # Items table header with green background like HTML
    pdf.set_fill_color(*pdf.secondary_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 10)
    
    col_widths = [10, 65, 15, 20, 25, 25, 20]  # Adjusted widths
    headers = ['Sr.', 'Product Name', 'Qty', 'Packing', 'Unit Price', 'Amount', '']
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
    pdf.ln()
    
    # Items with alternating background
    pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 9)
    
    for i, item in enumerate(invoice_data['items'], 1):
        # Alternate row background
        if i % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(col_widths[0], 8, str(i), 1, 0, 'C', True)
        pdf.cell(col_widths[1], 8, item['productName'][:30], 1, 0, 'L', True)  # Truncate long names
        pdf.cell(col_widths[2], 8, str(item['qty']), 1, 0, 'C', True)
        pdf.cell(col_widths[3], 8, item['packing'], 1, 0, 'C', True)
        pdf.cell(col_widths[4], 8, format_currency_indian(item['unitPrice']), 1, 0, 'R', True)
        pdf.cell(col_widths[5], 8, format_currency_indian(item['amount']), 1, 0, 'R', True)
        pdf.cell(col_widths[6], 8, '', 1, 1, 'C', True)  # Empty for action column
    
    pdf.ln(5)
    
    # Totals section with green highlight like HTML
    totals_x = 120
    amounts_x = 180
    
    pdf.set_font('Arial', '', 10)
    pdf.set_fill_color(230, 245, 233)  # Light green background
    
    # Subtotal
    pdf.cell(totals_x, 8, 'Subtotal:', 0, 0, 'R', True)
    pdf.cell(30, 8, format_currency_indian(invoice_data['totalAmount']), 0, 1, 'R', True)
    
    if invoice_data.get('gstPercentage', 0) > 0:
        pdf.cell(totals_x, 8, f'GST ({invoice_data["gstPercentage"]}%):', 0, 0, 'R', True)
        pdf.cell(30, 8, format_currency_indian(invoice_data.get('gstAmount', 0)), 0, 1, 'R', True)
    
    # Previous Balance
    pdf.cell(totals_x, 8, 'Previous Balance:', 0, 0, 'R', True)
    pdf.cell(30, 8, format_currency_indian(invoice_data['previousBalance']), 0, 1, 'R', True)
    
    # Grand Total with PKR
    pdf.set_font('Arial', 'B', 11)
    pdf.set_text_color(*pdf.secondary_color)
    pdf.cell(totals_x, 10, 'Grand Total:', 0, 0, 'R', True)
    pdf.cell(30, 10, f"PKR {format_currency_indian(invoice_data['grandTotal'])}", 0, 1, 'R', True)
    
    # Amount in words
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 9)
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(255, 255, 255)
    pdf.multi_cell(0, 5, f'Amount in Words: {convert_to_words(invoice_data["grandTotal"])}', 0, 'L')
    
    # Terms and conditions
    pdf.ln(5)
    pdf.set_font('Arial', 'I', 8)
    pdf.cell(0, 5, 'Terms & Conditions:', 0, 1)
    pdf.cell(0, 4, '1. Goods once sold will not be taken back or exchanged.', 0, 1)
    pdf.cell(0, 4, '2. All disputes subject to Multan jurisdiction.', 0, 1)
    
    return pdf

def generate_payment_receipt_pdf(payment_data):
    """Generate payment receipt PDF matching HTML design"""
    pdf = PDFGenerator(format='A5')
    pdf.add_page()
    
    # Payment receipt header with orange background
    pdf.set_fill_color(*pdf.primary_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 15, 'PAYMENT RECEIPT', 0, 1, 'C', True)
    pdf.ln(5)
    
    # Payment details with clean layout
    pdf.set_text_color(0, 0, 0)
    
    details = [
        ('Receipt No:', str(payment_data.get('paymentId', 'N/A'))),
        ('Date:', payment_data['date']),
        ('Received From:', payment_data['partyName']),
    ]
    
    if payment_data.get('remarks'):
        details.append(('Remarks:', payment_data['remarks']))
    
    pdf.set_font('Arial', 'B', 11)
    for label, value in details:
        pdf.cell(40, 8, label, 0, 0)
        pdf.set_font('Arial', '', 11)
        pdf.cell(0, 8, value, 0, 1)
        pdf.set_font('Arial', 'B', 11)
        pdf.ln(3)
    
    pdf.ln(5)
    
    # Amount section with highlight - Show PKR only here
    pdf.set_fill_color(230, 245, 233)  # Light green background
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(40, 10, 'Amount:', 0, 0)
    pdf.cell(0, 10, f"PKR {format_currency_indian(payment_data['amount'])}", 0, 1)
    
    pdf.set_font('Arial', 'I', 9)
    pdf.multi_cell(0, 5, f'Amount in Words: {convert_to_words(payment_data["amount"])}', 0, 'L')
    
    pdf.ln(10)
    
    # Footer note
    pdf.set_font('Arial', 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 5, 'This is a computer-generated receipt.', 0, 1, 'C')
    
    pdf.set_font('Arial', 'B', 10)
    pdf.set_text_color(*pdf.secondary_color)
    pdf.cell(0, 8, 'Thank you for your payment!', 0, 1, 'C')
    
    return pdf

def generate_ledger_pdf(ledger_data):
    """Generate ledger PDF matching HTML design"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    # Ledger header with orange background
    pdf.set_fill_color(*pdf.primary_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, f'Party Statement - {ledger_data["partyName"]}', 0, 1, 'C', True)
    pdf.ln(5)
    
    # Summary with green highlights
    pdf.set_text_color(0, 0, 0)
    pdf.set_fill_color(230, 245, 233)  # Light green background
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(50, 8, 'Opening Balance:', 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, format_currency_indian(ledger_data["openingBalance"]), 0, 1, 'L', True)
    
    pdf.set_font('Arial', 'B', 11)
    pdf.cell(50, 8, 'Current Balance:', 0, 0)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"PKR {format_currency_indian(ledger_data['currentBalance'])}", 0, 1, 'L', True)
    pdf.ln(5)
    
    # Transactions table header with green background
    pdf.set_fill_color(*pdf.secondary_color)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 9)
    
    col_widths = [20, 25, 45, 15, 15, 25, 25, 25]
    headers = ['Date', 'Invoice #', 'Description', 'Qty', 'Pack', 'Unit Price', 'Debit', 'Balance']
    
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
    pdf.ln()
    
    # Transactions with alternating background
    pdf.set_fill_color(255, 255, 255)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 8)
    
    running_balance = ledger_data["openingBalance"]
    
    # Opening balance row with highlight
    pdf.set_fill_color(230, 245, 233)
    pdf.cell(col_widths[0], 8, '', 1, 0, 'C', True)
    pdf.cell(col_widths[1], 8, '', 1, 0, 'C', True)
    pdf.cell(col_widths[2], 8, 'Opening Balance', 1, 0, 'L', True)
    pdf.cell(col_widths[3], 8, '', 1, 0, 'C', True)
    pdf.cell(col_widths[4], 8, '', 1, 0, 'C', True)
    pdf.cell(col_widths[5], 8, '', 1, 0, 'C', True)
    pdf.cell(col_widths[6], 8, '', 1, 0, 'C', True)
    pdf.cell(col_widths[7], 8, format_currency_indian(running_balance), 1, 1, 'R', True)
    pdf.set_fill_color(255, 255, 255)
    
    last_invoice_number = None
    for tx in ledger_data['transactions']:
        # Alternate row background
        if len(pdf.pages) % 2 == 0:
            pdf.set_fill_color(248, 249, 250)
        else:
            pdf.set_fill_color(255, 255, 255)
        
        if tx['type'] == 'invoice_item':
            # Show invoice number only for first item of each invoice
            display_invoice = tx['invoiceNumber'] if tx['invoiceNumber'] != last_invoice_number else ''
            display_date = tx['date'] if tx['invoiceNumber'] != last_invoice_number else ''
            
            running_balance += tx['amount']
            
            pdf.cell(col_widths[0], 8, display_date, 1, 0, 'C', True)
            pdf.cell(col_widths[1], 8, display_invoice, 1, 0, 'C', True)
            pdf.cell(col_widths[2], 8, tx['productName'][:25], 1, 0, 'L', True)  # Truncate long names
            pdf.cell(col_widths[3], 8, str(tx['qty']), 1, 0, 'C', True)
            pdf.cell(col_widths[4], 8, tx.get('packing', ''), 1, 0, 'C', True)
            pdf.cell(col_widths[5], 8, format_currency_indian(tx['unitPrice']), 1, 0, 'R', True)
            pdf.cell(col_widths[6], 8, format_currency_indian(tx['amount']), 1, 0, 'R', True)
            pdf.cell(col_widths[7], 8, format_currency_indian(running_balance), 1, 1, 'R', True)
            
            last_invoice_number = tx['invoiceNumber']
            
        elif tx['type'] == 'payment':
            running_balance -= tx['amount']
            desc = f"Payment - {tx.get('remarks', '')}" if tx.get('remarks') else "Payment Received"
            
            pdf.set_fill_color(255, 243, 205)  # Light orange for payments
            pdf.cell(col_widths[0], 8, tx['date'], 1, 0, 'C', True)
            pdf.cell(col_widths[1], 8, '', 1, 0, 'C', True)
            pdf.cell(col_widths[2], 8, desc[:25], 1, 0, 'L', True)
            pdf.cell(col_widths[3], 8, '', 1, 0, 'C', True)
            pdf.cell(col_widths[4], 8, '', 1, 0, 'C', True)
            pdf.cell(col_widths[5], 8, '', 1, 0, 'C', True)
            pdf.cell(col_widths[6], 8, format_currency_indian(tx['amount']), 1, 0, 'R', True)
            pdf.cell(col_widths[7], 8, format_currency_indian(running_balance), 1, 1, 'R', True)
            pdf.set_fill_color(255, 255, 255)
            
            last_invoice_number = None
    
    return pdf

def get_pdf_download_link(pdf, filename):
    """Generate a download link for PDF"""
    try:
        pdf_output = pdf.output(dest='S').encode('latin1')
        b64 = base64.b64encode(pdf_output).decode()
        href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="background-color: #FFA500; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px; margin: 5px;">📄 Download {filename}</a>'
        return href
    except Exception as e:
        return f"<p style='color: red;'>Error generating PDF: {str(e)}</p>"

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

# UI Components with HTML-like styling
def render_payment_section():
    """Payment Received Section"""
    st.markdown("""
    <style>
    .section-header {
        background-color: #FFA500;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="section-header"><h3>💰 Payment Received</h3></div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="section-header"><h3>📥 Payments Range Download</h3></div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="section-header"><h3>🗑️ Payment Management</h3></div>', unsafe_allow_html=True)
    
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
        
        # Download button for party payments - FIXED: This was missing
        if st.button("📄 Download Party Payments PDF", use_container_width=True):
            try:
                # Generate proper party payments PDF
                pdf = PDFGenerator()
                pdf.add_page()
                
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, f'Payments Report - {party_name}', 0, 1, 'C')
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
                
                st.markdown(get_pdf_download_link(pdf, f"payments_{party_name}.pdf"), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating PDF: {str(e)}")
        
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
    st.markdown('<div class="section-header"><h3>📊 Feed Mills Ledger Details</h3></div>', unsafe_allow_html=True)
    
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
            formatted_tx['amount_display'] = format_currency_indian(tx['amount'])  # Remove PKR from individual amounts
            if 'unitPrice' in tx:
                formatted_tx['unitPrice_display'] = format_currency_indian(tx['unitPrice'])
            formatted_transactions.append(formatted_tx)
        
        df = pd.DataFrame(formatted_transactions)
        st.dataframe(df, use_container_width=True)
        
        # Show opening and current balance - Only show PKR with totals
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Opening Balance", format_currency_indian(ledger_data.get('openingBalance', 0)))
        with col2:
            st.metric("Current Balance", f"PKR {format_currency_indian(ledger_data.get('currentBalance', 0))}")
        with col3:
            total_transactions = len(transactions)
            st.metric("Total Transactions", total_transactions)
        
        # Store ledger data for PDF download
        st.session_state.current_ledger_data = ledger_data
        
        # Download ledger PDF - FIXED: This button should work now
        if st.button("📄 Download Ledger PDF", use_container_width=True):
            try:
                pdf = generate_ledger_pdf(ledger_data)
                st.markdown(get_pdf_download_link(pdf, f"ledger_{ledger_data['partyName']}.pdf"), unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Error generating ledger PDF: {str(e)}")
    else:
        st.info("No transactions found for this party")

def render_stock_section():
    """Stock Management"""
    st.markdown('<div class="section-header"><h3>📦 Stock Management</h3></div>', unsafe_allow_html=True)
    
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
    st.markdown('<div class="section-header"><h3>📄 Create New Invoice</h3></div>', unsafe_allow_html=True)
    
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
    gst_amount = subtotal * (gst_percentage / 100)
    grand_total = subtotal + gst_amount + previous_balance
    
    # Display totals with formatted currency - Only show PKR with grand total
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Subtotal", format_currency_indian(subtotal))
    with col2:
        st.metric("Previous Balance", format_currency_indian(previous_balance))
    with col3:
        st.metric("GST Amount", format_currency_indian(gst_amount))
    with col4:
        st.metric("Grand Total", f"PKR {format_currency_indian(grand_total)}")
    
    # Action buttons
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("💾 Save Invoice", type="primary", use_container_width=True):
            save_invoice(party_name, invoice_date, gst_percentage, gst_amount, previous_balance, grand_total)
    with col2:
        if st.button("📄 Download PDF", use_container_width=True):
            if st.session_state.invoice_items and party_name:
                invoice_data = {
                    "partyName": party_name,
                    "invoiceNumber": st.session_state.current_invoice_number,
                    "date": invoice_date.isoformat(),
                    "items": st.session_state.invoice_items,
                    "totalAmount": subtotal,
                    "gstPercentage": gst_percentage,
                    "gstAmount": gst_amount,
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
        # Auto-select packing based on product
        default_packing = PRODUCT_PACKING_MAP.get(new_product, "Kg")
        new_packing = st.selectbox("Packing", PACKING_OPTIONS, index=PACKING_OPTIONS.index(default_packing) if default_packing in PACKING_OPTIONS else 0, key="new_packing")
    with col4:
        new_unit_price = st.number_input("Unit Price", min_value=0.0, step=0.01, key="new_unit_price")
    with col5:
        new_amount = new_qty * new_unit_price
        st.text_input("Amount", value=format_currency_indian(new_amount), disabled=True, key="new_amount_display")
    
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
                st.text(format_currency_indian(item['unitPrice']))
            with col5:
                st.text(format_currency_indian(item['amount']))
            with col6:
                if st.button("❌", key=f"remove_{i}"):
                    st.session_state.invoice_items.pop(i)
                    st.rerun()

def calculate_subtotal():
    """Calculate invoice subtotal"""
    return sum(item['amount'] for item in st.session_state.invoice_items)

def save_invoice(party_name, invoice_date, gst_percentage, gst_amount, previous_balance, grand_total):
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
        "gstPercentage": gst_percentage,
        "gstAmount": gst_amount,
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
    st.markdown('<div class="section-header"><h3>📈 Reports & Analytics</h3></div>', unsafe_allow_html=True)
    
    # Sales with Party functionality - FIXED: This was missing
    st.subheader("👥 Sales with Party")
    col1, col2, col3 = st.columns(3)
    with col1:
        sales_party = st.selectbox("Select Party", [""] + st.session_state.parties, key="sales_party")
    with col2:
        sales_start_date = st.date_input("Start Date", key="sales_start")
    with col3:
        sales_end_date = st.date_input("End Date", key="sales_end")
    
    if st.button("📊 View Sales with Party", key="sales_party_btn", use_container_width=True):
        if sales_party and sales_start_date and sales_end_date:
            try:
                invoices = backend.get_invoices_by_party_and_date_range(sales_party, sales_start_date.isoformat(), sales_end_date.isoformat())
                if invoices:
                    total_sales = sum(invoice['totalAmount'] for invoice in invoices)
                    st.success(f"Total sales for {sales_party}: PKR {format_currency_indian(total_sales)}")
                    
                    # Display sales summary
                    sales_df = pd.DataFrame([{
                        'Party': sales_party,
                        'Period': f"{sales_start_date} to {sales_end_date}",
                        'Total Invoices': len(invoices),
                        'Total Sales': f"PKR {format_currency_indian(total_sales)}"
                    }])
                    st.dataframe(sales_df, use_container_width=True)
                else:
                    st.info(f"No sales found for {sales_party} in the selected date range")
            except Exception as e:
                st.error(f"Error fetching sales data: {str(e)}")
        else:
            st.error("Please select party and date range")
    
    st.markdown("---")
    
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
                        pdf.cell(0, 10, f"Total: {format_currency_indian(invoice['totalAmount'])}", 0, 1)
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
    
    # All Party Balances - FIXED: Now excludes zero balance parties
    st.subheader("💰 All Party Balances")
    if st.button("Download All Party Balances PDF", key="all_balances_btn", use_container_width=True):
        try:
            ledgers = backend.get_all_party_ledgers()  # This now excludes zero balance
            if ledgers:
                pdf = generate_all_party_balances_pdf(ledgers)
                st.markdown(get_pdf_download_link(pdf, "all_party_balances.pdf"), unsafe_allow_html=True)
            else:
                st.info("No party data available with non-zero balance")
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
        pdf.cell(40, 10, format_currency_indian(item['totalAmount']), 1, 1, 'R')
        total_revenue += item['totalAmount']
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(150, 10, 'Total Revenue:', 0, 0, 'R')
    pdf.cell(40, 10, f"PKR {format_currency_indian(total_revenue)}", 0, 1, 'R')
    
    return pdf

def generate_all_party_balances_pdf(ledgers):
    """Generate PDF for all party balances - FIXED: Excludes zero balance"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', '', 16)
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
        pdf.cell(60, 10, f"Rs {format_currency_indian(ledger['currentBalance'])}", 1, 1, 'R')
        total_balance += ledger['currentBalance']
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(120, 10, 'Total Outstanding:', 0, 0, 'R')
    pdf.cell(60, 10, f"Rs {format_currency_indian(total_balance)}", 0, 1, 'R')
    
    return pdf

def generate_bilty_expense_pdf(payments, start_date, end_date):
    """Generate bilty expense report PDF"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', '', 16)
    pdf.cell(0, 10, 'Bilty Expense Report', 0, 1, 'C')
    pdf.cell(0, 10, f'{start_date} to {end_date}', 0, 1, 'C')
    pdf.ln(10)
    
    # Payments table
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(15, 10, 'ID', 1, 0, 'C', True)
    pdf.cell(80, 10, 'Party Name', 1, 0, 'C', True)
    pdf.cell(35, 10, 'Date', 1, 0, 'C', True)
    pdf.cell(50, 10, 'Amount', 1, 1, 'C', True)
    
    pdf.set_fill_color(255, 255, 255)
    total_amount = 0
    for payment in payments:
        pdf.cell(15, 10, str(payment['paymentId']), 1, 0)
        pdf.cell(80, 10, payment['partyName'], 1, 0)
        pdf.cell(35, 10, payment['date'], 1, 0)
        pdf.cell(50, 10, f"{format_currency_indian(payment['amount'])}", 1, 1, 'R')
        total_amount += payment['amount']
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(160, 10, 'Total Bilty Expense:', 0, 0, 'R')
    pdf.cell(30, 10, f"{format_currency_indian(total_amount)}", 0, 1, 'R')
    
    return pdf

def render_opening_balance_history():
    """Opening Balance History Section"""
    st.markdown('<div class="section-header"><h3>📜 Opening Balance History</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        party_name = st.selectbox("Select Party", [""] + st.session_state.parties, key="history_party")
    with col2:
        if st.button("📋 View History", use_container_width=True):
            if party_name:
                try:
                    history = backend.get_opening_balance_history(party_name)
                    if history:
                        display_opening_balance_history(history, party_name)
                    else:
                        st.info("No opening balance history found for this party")
                except Exception as e:
                    st.error(f"Error fetching history: {str(e)}")
            else:
                st.error("Please select a party name")

def display_opening_balance_history(history, party_name):
    """Display opening balance history"""
    st.subheader(f"Opening Balance History for: {party_name}")
    
    if history:
        # Format amounts for display
        formatted_history = []
        for record in history:
            formatted_record = record.copy()
            formatted_record['old_balance_display'] = format_currency_indian(record['old_balance'])
            formatted_record['new_balance_display'] = format_currency_indian(record['new_balance'])
            formatted_history.append(formatted_record)
        
        df = pd.DataFrame(formatted_history)
        # Display only relevant columns
        display_df = df[['adjustment_date', 'old_balance_display', 'new_balance_display', 'reason', 'created_at']]
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No history records found")

def render_edit_invoice_section():
    """Invoice Update & Delete Section - FIXED: Invoice search issue"""
    st.markdown('<div class="section-header"><h3>✏️ Invoice Update & Delete</h3></div>', unsafe_allow_html=True)
    
    # Get all invoice numbers for dropdown
    invoice_numbers = backend.get_all_invoice_numbers()
    
    col1, col2 = st.columns([3, 1])
    with col1:
        invoice_number = st.selectbox("Invoice Number", [""] + invoice_numbers, key="search_invoice")
    with col2:
        if st.button("🔍 Search & Load Invoice", use_container_width=True):
            if invoice_number:
                try:
                    invoice_data = backend.get_invoice(invoice_number)
                    if invoice_data:
                        load_invoice_for_editing(invoice_data)
                    else:
                        st.error(f"Invoice #{invoice_number} not found")
                except Exception as e:
                    st.error(f"Error loading invoice: {str(e)}")
            else:
                st.error("Please select an invoice number")

def load_invoice_for_editing(invoice_data):
    """Load invoice data for editing"""
    st.session_state.editing_invoice = invoice_data
    st.session_state.invoice_items = invoice_data["items"]
    
    st.success(f"Invoice #{invoice_data['invoiceNumber']} loaded successfully!")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Update Invoice", use_container_width=True):
            update_invoice(invoice_data['invoiceNumber'])
    with col2:
        if st.button("🗑️ Delete Invoice", type="secondary", use_container_width=True):
            delete_invoice(invoice_data['invoiceNumber'])

def update_invoice(invoice_number):
    """Update existing invoice"""
    if not st.session_state.get('editing_invoice'):
        st.error("No invoice loaded for editing")
        return
        
    if not st.session_state.invoice_items:
        st.error("Please add at least one invoice item")
        return
    
    invoice_data = st.session_state.editing_invoice.copy()
    invoice_data["items"] = st.session_state.invoice_items
    invoice_data["totalAmount"] = calculate_subtotal()
    invoice_data["grandTotal"] = invoice_data["totalAmount"] + invoice_data.get("gstAmount", 0) + invoice_data["previousBalance"]
    
    try:
        result = backend.update_invoice(invoice_number, invoice_data)
        if result:
            st.success("✅ Invoice updated successfully!")
            st.session_state.editing_invoice = None
            st.session_state.invoice_items = []
    except Exception as e:
        st.error(f"Error updating invoice: {str(e)}")

def delete_invoice(invoice_number):
    """Delete invoice"""
    if st.checkbox("Confirm deletion - this action cannot be undone"):
        try:
            result = backend.delete_invoice(invoice_number)
            if result:
                st.success("✅ Invoice deleted successfully!")
                st.session_state.editing_invoice = None
                st.session_state.invoice_items = []
                # Refresh parties list
                parties = backend.get_parties()
                st.session_state.parties = [party['name'] for party in parties]
        except Exception as e:
            st.error(f"Error deleting invoice: {str(e)}")

def render_party_exclude_section():
    """Party Exclude Report Section - FIXED: Overlapping issue"""
    st.markdown('<div class="section-header"><h3>🚫 Party Exclude Report</h3></div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        exclude_parties = st.multiselect("Parties to Exclude", st.session_state.parties, key="exclude_parties")
    with col2:
        exclude_start_date = st.date_input("Start Date", key="exclude_start")
    with col3:
        exclude_end_date = st.date_input("End Date", key="exclude_end")
    
    if st.button("📄 Download Party Exclude Report", use_container_width=True):
        if exclude_start_date and exclude_end_date:
            try:
                payments = backend.get_payments(start_date=exclude_start_date.isoformat(), end_date=exclude_end_date.isoformat())
                # Filter out excluded parties and bilty expense payments
                filtered_payments = [p for p in payments 
                                   if p['partyName'] not in exclude_parties 
                                   and not (p.get('remarks', '').lower().find('bilty') != -1)]
                
                if filtered_payments:
                    pdf = generate_party_exclude_pdf(filtered_payments, exclude_parties, exclude_start_date, exclude_end_date)
                    st.markdown(get_pdf_download_link(pdf, f"party_exclude_{exclude_start_date}_{exclude_end_date}.pdf"), unsafe_allow_html=True)
                else:
                    st.info("No payments found after filtering")
            except Exception as e:
                st.error(f"Error generating party exclude PDF: {str(e)}")
        else:
            st.error("Please select both start and end dates")

def generate_party_exclude_pdf(payments, excluded_parties, start_date, end_date):
    """Generate party exclude report PDF - FIXED: Overlapping issue"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Party Exclude Report', 0, 1, 'C')
    pdf.cell(0, 10, f'{start_date} to {end_date}', 0, 1, 'C')
    pdf.ln(5)
    
    # Excluded parties info
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f'Excluded Parties: {len(excluded_parties)}', 0, 1)
    pdf.set_font('Arial', '', 10)
    
    # List excluded parties in multiple columns if many
    if excluded_parties:
        parties_text = ", ".join(excluded_parties)
        # Use multi_cell to avoid text going beyond page width
        pdf.multi_cell(0, 5, parties_text)
    
    pdf.ln(5)
    
    # Payments table with adjusted column widths to prevent overlapping
    pdf.set_fill_color(200, 220, 255)
    col_widths = [15, 45, 35, 60, 35]  # Adjusted widths to fit page
    pdf.cell(col_widths[0], 10, 'ID', 1, 0, 'C', True)
    pdf.cell(col_widths[1], 10, 'Party Name', 1, 0, 'C', True)
    pdf.cell(col_widths[2], 10, 'Date', 1, 0, 'C', True)
    pdf.cell(col_widths[3], 10, 'Remarks', 1, 0, 'C', True)
    pdf.cell(col_widths[4], 10, 'Amount', 1, 1, 'C', True)
    
    pdf.set_fill_color(255, 255, 255)
    total_amount = 0
    for payment in payments:
        # Truncate long values to prevent overlapping
        party_name = payment['partyName'][:20] if len(payment['partyName']) > 20 else payment['partyName']
        remarks = payment.get('remarks', '')[:25] if payment.get('remarks') else ''
        
        pdf.cell(col_widths[0], 10, str(payment['paymentId']), 1, 0)
        pdf.cell(col_widths[1], 10, party_name, 1, 0)
        pdf.cell(col_widths[2], 10, payment['date'], 1, 0)
        pdf.cell(col_widths[3], 10, remarks, 1, 0)
        pdf.cell(col_widths[4], 10, f"PKR {format_currency_indian(payment['amount'])}", 1, 1, 'R')
        total_amount += payment['amount']
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    # Calculate total width for proper alignment
    total_width = sum(col_widths)
    pdf.cell(total_width - col_widths[4], 10, 'Total Amount (After Exclusion):', 0, 0, 'R')
    pdf.cell(col_widths[4], 10, f"PKR {format_currency_indian(total_amount)}", 0, 1, 'R')
    
    return pdf

def render_no_bilty_section():
    """Payments Without Bilty Expense Section"""
    st.markdown('<div class="section-header"><h3>📋 Payments Without Bilty Expense</h3></div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        no_bilty_start = st.date_input("Start Date", key="no_bilty_start")
    with col2:
        no_bilty_end = st.date_input("End Date", key="no_bilty_end")
    
    if st.button("📄 Download Payments Without Bilty PDF", use_container_width=True):
        if no_bilty_start and no_bilty_end:
            try:
                payments = backend.get_payments(start_date=no_bilty_start.isoformat(), end_date=no_bilty_end.isoformat())
                # Filter out bilty expense payments
                filtered_payments = [p for p in payments 
                                   if not (p.get('remarks', '').lower().find('bilty') != -1)]
                
                if filtered_payments:
                    pdf = generate_no_bilty_pdf(filtered_payments, no_bilty_start, no_bilty_end)
                    st.markdown(get_pdf_download_link(pdf, f"payments_no_bilty_{no_bilty_start}_{no_bilty_end}.pdf"), unsafe_allow_html=True)
                else:
                    st.info("No payments found without bilty expense")
            except Exception as e:
                st.error(f"Error generating no-bilty PDF: {str(e)}")
        else:
            st.error("Please select both start and end dates")

def generate_no_bilty_pdf(payments, start_date, end_date):
    """Generate no-bilty payments PDF"""
    pdf = PDFGenerator()
    pdf.add_page()
    
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Payments Without Bilty Expense', 0, 1, 'C')
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
        pdf.cell(50, 10, payment.get('remarks', '')[:25], 1, 0)
        pdf.cell(30, 10, f"PKR {format_currency_indian(payment['amount'])}", 1, 1, 'R')
        total_amount += payment['amount']
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(160, 10, 'Total Amount (No Bilty):', 0, 0, 'R')
    pdf.cell(30, 10, f"PKR {format_currency_indian(total_amount)}", 0, 1, 'R')
    
    return pdf

def main():
    st.set_page_config(
        page_title="NUTRION - Invoice, Ledger & Stock Management",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Enhanced Custom CSS matching HTML design
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #FFA500;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, #FFA500, #FF8C00);
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        color: white;
    }
    .section-header {
        background: linear-gradient(135deg, #FFA500, #FF8C00);
        color: white;
        padding: 12px;
        border-radius: 8px;
        margin-top: 1rem;
        margin-bottom: 1rem;
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
        background-color: #FFA500;
        color: white;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        background-color: #FF8C00;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="main-header">NUTRION - Invoice, Ledger & Stock Management</h1>', unsafe_allow_html=True)
    
    # Initialize app with existing database
    initialize_app()
    
    # Create tabs for better organization
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📄 Invoices", 
        "💰 Payments", 
        "📊 Ledger", 
        "📦 Stock", 
        "📈 Reports",
        "⚙️ Advanced",
        "ℹ️ About"
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
        st.markdown("---")
        render_opening_balance_history()
    
    with tab4:
        render_stock_section()
    
    with tab5:
        render_reports_section()
    
    with tab6:
        st.markdown('<div class="section-header"><h3>⚙️ Advanced Features</h3></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Invoice Management")
            render_edit_invoice_section()
        
        with col2:
            st.subheader("Special Reports")
            render_party_exclude_section()
            st.markdown("---")
            render_no_bilty_section()
    
    with tab7:
        st.markdown('<div class="section-header"><h3>ℹ️ About NUTRION System</h3></div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("System Information")
            st.info(f"Current Invoice Number: {st.session_state.current_invoice_number}")
            st.info(f"Total Parties: {len(st.session_state.parties)}")
            st.info(f"Products Available: {len(PRODUCTS)}")
            
            st.subheader("Database Management")
            if st.button("🔄 Refresh Application Data", use_container_width=True):
                initialize_app()
                st.success("Application data refreshed!")
            
            if st.button("🗑️ Clear All Session Data", use_container_width=True):
                st.session_state.invoice_items = []
                st.session_state.stock_items = []
                st.success("Session data cleared!")
        
        with col2:
            st.subheader("Features")
            st.success("✅ Complete Invoice Management")
            st.success("✅ Payment Tracking & Receipts")
            st.success("✅ Ledger & Balance Management")
            st.success("✅ Stock Inventory Management")
            st.success("✅ Advanced Reporting")
            st.success("✅ PDF Export for All Documents")
            st.success("✅ Indian Number Formatting")
            st.success("✅ GST Calculation")
            
            st.subheader("Database")
            st.info(f"Using: invoice_app_v4.db")
            st.info("All data is saved to your existing database")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        **NUTRION - Feed Mills Management System** | Developed with ❤️ using Streamlit | Database: invoice_app_v4.db
        """
    )

if __name__ == "__main__":
    main()
