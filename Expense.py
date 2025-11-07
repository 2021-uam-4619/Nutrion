import streamlit as st
import pandas as pd
import sqlite3
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Database setup
conn = sqlite3.connect('company_data.db', check_same_thread=False)
c = conn.cursor()

# Tables creation
c.execute('''CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                bank_details TEXT,
                designation TEXT,
                salary REAL
            )''')

c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                amount REAL,
                date TEXT,
                employee_id INTEGER,
                FOREIGN KEY(employee_id) REFERENCES employees(id)
            )''')
conn.commit()

# Streamlit layout
st.set_page_config(page_title="Expense & Employee Management", layout="wide")

st.title("🧾 Expense & Employee Management System")

left, right = st.columns(2)

# ---------------- EXPENSE MANAGEMENT ----------------
with left:
    st.header("Expense Management")

    menu = ["Add Expense", "View Expenses", "Import CSV/Excel"]
    choice = st.selectbox("Select Action", menu)

    if choice == "Add Expense":
        category = st.selectbox("Category", [
            "Guard", "Labour", "Bilty Expenses", "Office Rent", "Warehouse Rent",
            "Muhammad Asim Iqbal Salary", "Import Export", "Office Electricity", "FBR",
            "Abdul Manan Sb Salary", "Office Entertainment", "PSID", "Advance", "Commission",
            "Office Stationery Expense", "Employee Expenses", "Other Expense", "Company Expense",
            "Muhammad Abdullah Salary"
        ])
        amount = st.number_input("Amount", min_value=0.0, step=100.0)
        date = st.date_input("Date")
        employee_id = st.number_input("Employee ID (optional)", min_value=0, step=1)

        if st.button("Save Expense"):
            c.execute("INSERT INTO expenses (category, amount, date, employee_id) VALUES (?, ?, ?, ?)",
                      (category, amount, date.strftime('%Y-%m-%d'), employee_id if employee_id else None))
            conn.commit()
            st.success("Expense saved successfully!")

    elif choice == "View Expenses":
        data = pd.read_sql_query("SELECT * FROM expenses", conn)
        st.dataframe(data)

        if not data.empty:
            if st.button("Export as PDF"):
                buffer = BytesIO()
                p = canvas.Canvas(buffer, pagesize=letter)
                p.drawString(200, 750, "Expense Report")
                y = 700
                for i, row in data.iterrows():
                    p.drawString(50, y, f"{row['id']} | {row['category']} | {row['amount']} | {row['date']}")
                    y -= 20
                p.save()
                st.download_button("Download PDF", data=buffer.getvalue(), file_name="expenses_report.pdf")

    elif choice == "Import CSV/Excel":
        file = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
        if file:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            df.to_sql('expenses', conn, if_exists='append', index=False)
            conn.commit()
            st.success("Data imported successfully!")

# ---------------- EMPLOYEE MANAGEMENT ----------------
with right:
    st.header("Employee Management & Reporting")

    emp_menu = ["Add Employee", "View Employees", "Generate Salary Slip"]
    emp_choice = st.selectbox("Select Employee Action", emp_menu)

    if emp_choice == "Add Employee":
        name = st.text_input("Employee Name")
        bank = st.text_input("Bank Details")
        designation = st.text_input("Designation")
        salary = st.number_input("Salary", min_value=0.0, step=1000.0)

        if st.button("Save Employee"):
            c.execute("INSERT INTO employees (name, bank_details, designation, salary) VALUES (?, ?, ?, ?)",
                      (name, bank, designation, salary))
            conn.commit()
            st.success("Employee added successfully!")

    elif emp_choice == "View Employees":
        emp_data = pd.read_sql_query("SELECT * FROM employees", conn)
        st.dataframe(emp_data)

    elif emp_choice == "Generate Salary Slip":
        emp_id = st.number_input("Enter Employee ID", min_value=1, step=1)
        month = st.text_input("Month (e.g., October 2025)")

        if st.button("Generate Slip"):
            emp = c.execute("SELECT * FROM employees WHERE id=?", (emp_id,)).fetchone()
            if emp:
                buffer = BytesIO()
                p = canvas.Canvas(buffer, pagesize=letter)
                p.drawString(200, 750, "Salary Slip")
                p.drawString(50, 700, f"Name: {emp[1]}")
                p.drawString(50, 680, f"Designation: {emp[3]}")
                p.drawString(50, 660, f"Bank: {emp[2]}")
                p.drawString(50, 640, f"Salary: Rs. {emp[4]:,.2f}")
                p.drawString(50, 620, f"Month: {month}")
                p.save()
                st.download_button("Download Salary Slip", data=buffer.getvalue(), file_name=f"salary_slip_{emp[1]}.pdf")
            else:
                st.error("Employee not found!")
