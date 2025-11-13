import streamlit as st
import pandas as pd
import sqlite3
from datetime import date, datetime, timedelta
import os
from fpdf import FPDF
import io
import json
import uuid
import tempfile
from PIL import Image
import base64

# --- Constants ---
DB_FILE = "nutrion_app.db"
COMPANY_NAME = "Nutrion"
DEVELOPER_INFO = "Developed by DataNex Solution | +92320 7429422"

# [Keep all your existing database and helper functions exactly the same...]

# --- Improved PDF Class ---
class PDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.report_title = "Report"
        self.date_range_str = ""
        self.logo_path = "logo.png"
        self.set_auto_page_break(auto=True, margin=20)

    def header(self):
        # Increased logo size from 25 to 40
        try:
            if os.path.exists(self.logo_path):
                self.image(self.logo_path, 10, 8, 40)
        except:
            pass
        
        self.set_font('Arial', 'B', 16)
        self.cell(0, 12, COMPANY_NAME, 0, 1, 'C')
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, self.report_title, 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 8, self.date_range_str, 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-20)
        self.set_font('Arial', 'I', 9)
        
        # Removed signature and added system generated message
        self.cell(0, 6, "This PDF is system generated, not required any signature", 0, 1, 'C')
        
        self.set_font('Arial', 'I', 8)
        footer_width = self.w - self.l_margin - self.r_margin
        self.cell(footer_width / 2, 5, f'Page {self.page_no()}/{{nb}}', 0, 0, 'L')
        self.cell(footer_width / 2, 5, DEVELOPER_INFO, 0, 0, 'R')

    def add_table(self, df, totals_cols=None):
        if df.empty:
            self.set_font('Arial', 'I', 10)
            self.cell(0, 10, "No data found for the selected criteria.", 1, 1, 'C')
            return

        # Set table style
        self.set_font('Arial', 'B', 9)
        self.set_fill_color(224, 235, 255)
        
        # Calculate column widths dynamically
        col_widths = self.calculate_optimal_column_widths(df)
        
        # Draw header
        x_start = self.get_x()
        for i, col in enumerate(df.columns):
            self.cell(col_widths[i], 8, str(col).replace('_', ' ').title(), 1, 0, 'C', 1)
        self.ln()
        
        # Draw rows
        self.set_font('Arial', '', 8)
        fill = False
        
        for _, row in df.iterrows():
            # Check if we need a page break
            if self.get_y() + 10 > self.page_break_trigger:
                self.add_page()
                # Redraw header
                self.set_font('Arial', 'B', 9)
                self.set_fill_color(224, 235, 255)
                x_start = self.get_x()
                for i, col in enumerate(df.columns):
                    self.cell(col_widths[i], 8, str(col).replace('_', ' ').title(), 1, 0, 'C', 1)
                self.ln()
                self.set_font('Arial', '', 8)
            
            # Calculate row height for this row
            max_lines = 1
            cell_contents = []
            
            for i, col in enumerate(df.columns):
                cell_text = self.format_cell_value(row[col], df[col])
                lines = self.wrap_text(cell_text, col_widths[i] - 2)
                cell_contents.append(lines)
                max_lines = max(max_lines, len(lines))
            
            row_height = max(6, max_lines * 3.5)
            
            # Draw each cell in the row
            x_position = self.get_x()
            for i, (col, lines) in enumerate(zip(df.columns, cell_contents)):
                # Set fill color for alternating rows
                if fill:
                    self.set_fill_color(245, 245, 245)
                else:
                    self.set_fill_color(255, 255, 255)
                
                # Determine alignment
                align = 'L'
                if pd.api.types.is_numeric_dtype(df[col]) or any(x in str(col).lower() for x in ['amount', 'salary', 'debit', 'credit', 'balance']):
                    align = 'R'
                
                # Draw cell background
                self.cell(col_widths[i], row_height, '', 1, 0, 'L', 1)
                
                # Draw text content
                text_y = self.get_y()
                for j, line in enumerate(lines):
                    self.set_xy(x_position + 1, text_y + 1 + (j * 3.5))
                    self.cell(col_widths[i] - 2, 3.5, line, 0, 0, align)
                
                x_position += col_widths[i]
            
            self.ln(row_height)
            fill = not fill
        
        # Add totals row if specified
        if totals_cols:
            self.set_font('Arial', 'B', 9)
            self.set_fill_color(220, 220, 220)
            x_position = self.get_x()
            
            for i, col in enumerate(df.columns):
                if i == 0:
                    self.cell(col_widths[i], 8, "GRAND TOTAL", 1, 0, 'R', 1)
                elif col in totals_cols:
                    try:
                        col_total = pd.to_numeric(df[col], errors='coerce').sum()
                        self.cell(col_widths[i], 8, f"{col_total:,.2f}", 1, 0, 'R', 1)
                    except:
                        self.cell(col_widths[i], 8, "", 1, 0, 'C', 1)
                else:
                    self.cell(col_widths[i], 8, "", 1, 0, 'C', 1)
            self.ln()

    def calculate_optimal_column_widths(self, df):
        """Calculate optimal column widths based on content"""
        total_width = self.w - self.l_margin - self.r_margin - 10
        num_cols = len(df.columns)
        
        # Minimum and maximum column widths
        min_width = 15
        max_width = total_width / 2
        
        # Calculate required width for each column
        col_requirements = []
        for col in df.columns:
            # Header width requirement
            header_text = str(col).replace('_', ' ').title()
            header_width = len(header_text) * 1.8
            
            # Content width requirement
            if df.empty:
                content_width = header_width
            else:
                # Sample the data to find maximum width needed
                sample_size = min(20, len(df))
                sample_data = df[col].head(sample_size).astype(str)
                
                # For numeric columns, check formatted values
                if pd.api.types.is_numeric_dtype(df[col]):
                    formatted_samples = []
                    for val in df[col].head(sample_size):
                        if pd.notna(val):
                            try:
                                formatted_samples.append(f"{float(val):,.2f}")
                            except:
                                formatted_samples.append(str(val))
                    if formatted_samples:
                        max_content_len = max(len(str(s)) for s in formatted_samples)
                    else:
                        max_content_len = 0
                else:
                    max_content_len = sample_data.str.len().max()
                
                content_width = max_content_len * 1.4
            
            # Combine requirements
            required_width = max(header_width, content_width, min_width)
            required_width = min(required_width, max_width)
            col_requirements.append(required_width)
        
        # Adjust to fit total width
        total_required = sum(col_requirements)
        
        if total_required > total_width:
            # Scale down proportionally
            scale_factor = total_width / total_required
            col_widths = [max(min_width, w * scale_factor) for w in col_requirements]
        else:
            # Distribute extra space to columns that need it most
            col_widths = col_requirements.copy()
            extra_space = total_width - total_required
            if extra_space > 0:
                # Give more space to columns that are further from their max
                space_needs = [max_width - w for w in col_widths]
                total_need = sum(space_needs)
                if total_need > 0:
                    for i in range(len(col_widths)):
                        col_widths[i] += (space_needs[i] / total_need) * extra_space
        
        return [int(w) for w in col_widths]

    def format_cell_value(self, value, column):
        """Format cell value based on data type"""
        if pd.isna(value) or value is None:
            return ""
        
        if pd.api.types.is_numeric_dtype(column):
            try:
                return f"{float(value):,.2f}"
            except (ValueError, TypeError):
                return str(value)
        
        return str(value)

    def wrap_text(self, text, max_width):
        """Improved text wrapping that handles long words better"""
        if not text or text == "None" or pd.isna(text):
            return ['']
        
        text = str(text)
        
        # If text fits within max_width, return as single line
        if self.get_string_width(text) <= max_width:
            return [text]
        
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            # Test if adding this word exceeds width
            test_line = ' '.join(current_line + [word])
            if self.get_string_width(test_line) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                
                # If single word is too long, break it
                if self.get_string_width(word) > max_width:
                    broken_word = self.break_long_word(word, max_width)
                    lines.extend(broken_word[:-1])
                    current_line = [broken_word[-1]] if broken_word else []
                else:
                    current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else ['']

    def break_long_word(self, word, max_width):
        """Break a long word into chunks that fit within max_width"""
        chunks = []
        current_chunk = ""
        
        for char in word:
            test_chunk = current_chunk + char
            if self.get_string_width(test_chunk) <= max_width:
                current_chunk = test_chunk
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = char
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

# [Keep all your existing PDF generation functions exactly the same...]
# generate_employee_ledger_pdf, generate_individual_slip_pdf, generate_pdf_report

# [Keep all your existing page functions and main application exactly the same...]
# page_employee_expense_management, page_employee_management, page_expense_management, etc.
