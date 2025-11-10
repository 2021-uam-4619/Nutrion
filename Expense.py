# app.py
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date
from io import BytesIO
from reportlab.lib.pagesizes import A4, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import utils
import tempfile
import os

DB_PATH = "hr_expense.db"

# ---------- Database utilities ----------
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY,
        employee_code TEXT UNIQUE,
        name TEXT,
        designation TEXT,
        bank_name TEXT,
        account_number TEXT,
        account_title TEXT,
        base_salary REAL DEFAULT 0,
        joining_date TEXT,
        notes TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS expense_categories (
        name TEXT PRIMARY KEY,
        description TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY,
        employee_id INTEGER,
        category TEXT,
        description TEXT,
        amount REAL,
        date TEXT,
        is_reimbursed INTEGER DEFAULT 0,
        reimbursed_date TEXT,
        FOREIGN KEY(employee_id) REFERENCES employees(id)
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS employee_ledger_entries (
        id INTEGER PRIMARY KEY,
        employee_id INTEGER,
        date TEXT,
        description TEXT,
        amount REAL,
        linked_expense_id INTEGER,
        FOREIGN KEY(employee_id) REFERENCES employees(id),
        FOREIGN KEY(linked_expense_id) REFERENCES expenses(id)
    )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------- Helper functions ----------
def to_iso(d):
    if isinstance(d, str): return d
    if isinstance(d, date): return d.isoformat()
    return str(d)

def fetch_employees():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM employees ORDER BY name", conn)
    conn.close()
    return df

def add_or_update_employee(data):
    conn = get_conn()
    c = conn.cursor()
    if data.get("id"):
        c.execute("""
            UPDATE employees SET employee_code=?, name=?, designation=?, bank_name=?, account_number=?, account_title=?, base_salary=?, joining_date=?, notes=?
            WHERE id=?
        """, (data["employee_code"], data["name"], data["designation"], data["bank_name"], data["account_number"], data["account_title"], data["base_salary"], data["joining_date"], data["notes"], data["id"]))
    else:
        c.execute("""
            INSERT INTO employees (employee_code, name, designation, bank_name, account_number, account_title, base_salary, joining_date, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (data["employee_code"], data["name"], data["designation"], data["bank_name"], data["account_number"], data["account_title"], data["base_salary"], data["joining_date"], data["notes"]))
    conn.commit()
    conn.close()

def delete_employee(employee_id):
    conn = get_conn()
    c = conn.cursor()
    # optionally cascade: remove ledger entries and expenses or keep for history. Here: keep, but nullify employee_id references if needed.
    c.execute("DELETE FROM employees WHERE id=?", (employee_id,))
    conn.commit()
    conn.close()

def add_expense(employee_id, category, description, amount, date_str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO expenses (employee_id, category, description, amount, date)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, category, description, amount, date_str))
    expense_id = c.lastrowid
    # add ledger entry: employee is owed amount (credit to employee)
    if employee_id:
        c.execute("""
            INSERT INTO employee_ledger_entries (employee_id, date, description, amount, linked_expense_id)
            VALUES (?, ?, ?, ?, ?)
        """, (employee_id, date_str, f"Expense claimed: {description}", amount, expense_id))
    conn.commit()
    conn.close()
    return expense_id

def reimburse_expense(expense_id, reimbursed_date):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT employee_id, amount, is_reimbursed FROM expenses WHERE id=?", (expense_id,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise ValueError("Expense not found")
    if row["is_reimbursed"]:
        conn.close()
        return False
    employee_id = row["employee_id"]
    amount = row["amount"]
    # mark expense reimbursed
    c.execute("UPDATE expenses SET is_reimbursed=1, reimbursed_date=? WHERE id=?", (reimbursed_date, expense_id))
    # subtract from employee ledger by adding a negative entry (payment)
    if employee_id:
        c.execute("""
            INSERT INTO employee_ledger_entries (employee_id, date, description, amount, linked_expense_id)
            VALUES (?, ?, ?, ?, ?)
        """, (employee_id, reimbursed_date, f"Reimbursement for expense #{expense_id}", -amount, expense_id))
    conn.commit()
    conn.close()
    return True

def add_ledger_entry(employee_id, date_str, description, amount, linked_expense_id=None):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO employee_ledger_entries (employee_id, date, description, amount, linked_expense_id)
        VALUES (?, ?, ?, ?, ?)
    """, (employee_id, date_str, description, amount, linked_expense_id))
    conn.commit()
    conn.close()

def get_employee_ledger(employee_id, start_date=None, end_date=None):
    q = "SELECT * FROM employee_ledger_entries WHERE employee_id=?"
    params = [employee_id]
    if start_date:
        q += " AND date >= ?"
        params.append(start_date)
    if end_date:
        q += " AND date <= ?"
        params.append(end_date)
    q += " ORDER BY date"
    conn = get_conn()
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    if df.empty:
        return df
    df["running_balance"] = df["amount"].cumsum()
    return df

def fetch_expenses(start_date=None, end_date=None, category=None):
    q = "SELECT e.*, em.name as employee_name FROM expenses e LEFT JOIN employees em ON e.employee_id = em.id WHERE 1=1"
    params = []
    if start_date:
        q += " AND date >= ?"; params.append(start_date)
    if end_date:
        q += " AND date <= ?"; params.append(end_date)
    if category:
        q += " AND category = ?"; params.append(category)
    q += " ORDER BY date"
    conn = get_conn()
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df

def fetch_categories():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM expense_categories ORDER BY name", conn)
    conn.close()
    return df

def add_category(name, description=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO expense_categories (name, description) VALUES (?, ?)", (name, description))
    conn.commit()
    conn.close()

def delete_category(name):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM expense_categories WHERE name=?", (name,))
    conn.commit()
    conn.close()

# ---------- PDF Generators ----------
def generate_individual_salary_slip_pdf(employee_row, period_start, period_end, deductions=None):
    """
    employee_row: pandas Series or dict with keys: name, designation, account_number, account_title, bank_name, base_salary
    deductions: list of (label, amount)
    returns bytes
    """
    if deductions is None:
        deductions = []
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 25 * mm
    y = height - margin

    # Header
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Salary Slip")
    c.setFont("Helvetica", 10)
    y -= 12
    c.drawString(margin, y, f"Employee: {employee_row.get('name')} ({employee_row.get('employee_code','')})")
    c.drawRightString(width - margin, y, f"Period: {period_start} to {period_end}")
    y -= 18

    # Account details
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Bank / Account Details")
    y -= 12
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Account Title: {employee_row.get('account_title','')}")
    y -= 12
    c.drawString(margin, y, f"Account Number: {employee_row.get('account_number','')}")
    y -= 12
    c.drawString(margin, y, f"Bank Name: {employee_row.get('bank_name','')}")
    y -= 18

    # Salary breakdown
    basic = float(employee_row.get("base_salary") or 0.0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Earnings")
    c.drawString(width/2, y, "Amount")
    y -= 12
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, "Basic Salary")
    c.drawRightString(width - margin, y, f"{basic:,.2f}")
    y -= 12

    total_earnings = basic
    total_deductions = 0.0
    if deductions:
        y -= 6
        c.setFont("Helvetica-Bold", 10)
        c.drawString(margin, y, "Deductions")
        c.drawRightString(width - margin, y, "Amount")
        y -= 12
        c.setFont("Helvetica", 10)
        for label, amt in deductions:
            c.drawString(margin, y, label)
            c.drawRightString(width - margin, y, f"{amt:,.2f}")
            total_deductions += float(amt)
            y -= 12

    net = total_earnings - total_deductions
    y -= 12
    c.setFont("Helvetica-Bold", 11)
    c.drawString(margin, y, f"Net Payable")
    c.drawRightString(width - margin, y, f"{net:,.2f}")

    y -= 30
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def generate_salary_sheet_pdf(employees_df, period_start, period_end, deductions_map=None):
    """
    employees_df: DataFrame with employees & base_salary
    deductions_map: dict employee_id -> list of (label, amount) or global deductions list
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    margin = 18 * mm
    y = height - margin
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Salary Sheet")
    y -= 20
    c.setFont("Helvetica", 9)
    c.drawString(margin, y, f"Period: {period_start} to {period_end}")
    y -= 18

    # Header row
    c.setFont("Helvetica-Bold", 9)
    cols = ["Emp Code", "Name", "Designation", "Bank Name", "Acc Title", "Acc No", "Gross Salary", "Deductions", "Net Pay"]
    col_x = [margin, margin+55, margin+190, margin+300, margin+400, margin+480, margin+550, margin+630, margin+720]
    for i, col in enumerate(cols):
        c.drawString(col_x[i], y, col)
    y -= 12
    c.setFont("Helvetica", 9)
    grand_total = 0.0
    for _, row in employees_df.iterrows():
        if y < 40:
            c.showPage()
            y = height - margin
        emp_code = row.get("employee_code","")
        name = row.get("name","")
        desig = row.get("designation","")
        bank = row.get("bank_name","")
        acc_title = row.get("account_title","")
        acc_no = row.get("account_number","")
        gross = float(row.get("base_salary") or 0.0)
        deducts = 0.0
        if deductions_map and row.get("id") in deductions_map:
            deducts = sum([d[1] for d in deductions_map[row.get("id")]])
        net = gross - deducts
        grand_total += net
        # write values
        c.drawString(col_x[0], y, str(emp_code))
        c.drawString(col_x[1], y, str(name)[:28])
        c.drawString(col_x[2], y, str(desig)[:18])
        c.drawString(col_x[3], y, str(bank)[:18])
        c.drawString(col_x[4], y, str(acc_title)[:12])
        c.drawString(col_x[5], y, str(acc_no)[:12])
        c.drawRightString(col_x[6]+60, y, f"{gross:,.2f}")
        c.drawRightString(col_x[7]+60, y, f"{deducts:,.2f}")
        c.drawRightString(col_x[8]+80, y, f"{net:,.2f}")
        y -= 12
    y -= 12
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y, "Grand Total Net Pay")
    c.drawRightString(width - margin, y, f"{grand_total:,.2f}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

def generate_expense_report_pdf(expenses_df, period_start, period_end, group_by_category=True):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    margin = 20 * mm
    y = height - margin
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y, "Expense Report")
    y -= 16
    c.setFont("Helvetica", 10)
    c.drawString(margin, y, f"Period: {period_start} to {period_end}")
    y -= 16

    if expenses_df.empty:
        c.drawString(margin, y, "No expenses in selected range.")
        c.showPage()
        c.save()
        buffer.seek(0)
        return buffer.read()

    if group_by_category:
        grouped = expenses_df.groupby("category")
        for cat, group in grouped:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, y, f"Category: {cat} (Total: {group['amount'].sum():,.2f})")
            y -= 14
            c.setFont("Helvetica", 9)
            for _, r in group.iterrows():
                line = f"{r['date']} | {r.get('employee_name','-')} | {r['description']} | {r['amount']:,.2f} | Reimbursed: {bool(r['is_reimbursed'])}"
                if y < 40:
                    c.showPage()
                    y = height - margin
                c.drawString(margin, y, line[:110])
                y -= 12
            y -= 8
    else:
        c.setFont("Helvetica", 10)
        for _, r in expenses_df.iterrows():
            if y < 40:
                c.showPage()
                y = height - margin
            line = f"{r['date']} | {r.get('category','-')} | {r.get('employee_name','-')} | {r['description']} | {r['amount']:,.2f} | Reimbursed: {bool(r['is_reimbursed'])}"
            c.drawString(margin, y, line[:130])
            y -= 12

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()

# ---------- Streamlit UI ----------
st.set_page_config(page_title="HR & Expense System — DataNex", layout="wide")
st.title("HR & Expense Management — DataNex Solution")

st.sidebar.title("Navigation")
page = st.sidebar.selectbox("Select page", ["Dashboard", "Employees", "Payroll", "Expenses", "Reports & Exports", "Settings / Data Import"])

# Quick contact in sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("**Contact**: +92320 7429422")
st.sidebar.markdown("**Client**: Nutrion")

# ---------------- Dashboard ----------------
if page == "Dashboard":
    st.subheader("Dashboard")
    employees = fetch_employees()
    total_employees = len(employees)
    expenses_all = fetch_expenses()
    total_expenses = expenses_all['amount'].sum() if not expenses_all.empty else 0.0
    st.metric("Total employees", total_employees)
    st.metric("Total expenses (all time)", f"{total_expenses:,.2f}")
    st.markdown("#### Recent expenses")
    recent = expenses_all.sort_values("date", ascending=False).head(10)
    if recent.empty:
        st.write("No expenses yet")
    else:
        st.dataframe(recent)

# ---------------- Employees ----------------
elif page == "Employees":
    st.subheader("Employees (CRUD & Import)")
    cols = st.columns([3,1])
    with cols[0]:
        st.markdown("### Add / Edit Employee")
        with st.form("employee_form", clear_on_submit=False):
            emp_id = st.number_input("Employee ID (leave 0 for new)", value=0, step=1)
            code = st.text_input("Employee Code")
            name = st.text_input("Full Name")
            designation = st.text_input("Designation")
            bank_name = st.text_input("Bank Name")
            account_title = st.text_input("Account Title")
            account_number = st.text_input("Account Number")
            base_salary = st.number_input("Base Salary", value=0.0, format="%.2f")
            joining_date = st.date_input("Joining Date", value=date.today())
            notes = st.text_area("Notes", height=80)
            submitted = st.form_submit_button("Save Employee")
            if submitted:
                data = {
                    "id": emp_id if emp_id != 0 else None,
                    "employee_code": code,
                    "name": name,
                    "designation": designation,
                    "bank_name": bank_name,
                    "account_number": account_number,
                    "account_title": account_title,
                    "base_salary": base_salary,
                    "joining_date": to_iso(joining_date),
                    "notes": notes
                }
                add_or_update_employee(data)
                st.success("Saved.")
    with cols[1]:
        st.markdown("### Employee List")
        df = fetch_employees()
        st.dataframe(df)
        selected = st.selectbox("Select for actions", df["id"].tolist() if not df.empty else [], format_func=lambda x: df.set_index("id").loc[x]["name"] if len(df)>0 else None)
        if selected:
            if st.button("Delete selected"):
                delete_employee(selected)
                st.success("Deleted.")
        st.markdown("### Upload Employees from Excel")
        uploaded = st.file_uploader("Upload Excel (.xlsx) with columns: employee_code,name,designation,bank_name,account_title,account_number,base_salary,joining_date", type=["xlsx"])
        if uploaded:
            try:
                uploaded_df = pd.read_excel(uploaded, engine="openpyxl")
                required = {"employee_code","name"}
                if not required.issubset(uploaded_df.columns):
                    st.error(f"Excel missing required columns. Need at least: {required}")
                else:
                    count=0
                    for _, r in uploaded_df.iterrows():
                        data = {
                            "id": None,
                            "employee_code": r.get("employee_code"),
                            "name": r.get("name"),
                            "designation": r.get("designation",""),
                            "bank_name": r.get("bank_name",""),
                            "account_number": r.get("account_number",""),
                            "account_title": r.get("account_title",""),
                            "base_salary": float(r.get("base_salary") or 0),
                            "joining_date": to_iso(r.get("joining_date") if pd.notna(r.get("joining_date")) else date.today()),
                            "notes": ""
                        }
                        try:
                            add_or_update_employee(data)
                            count += 1
                        except Exception as e:
                            st.warning(f"Could not import row {r.get('employee_code')}: {e}")
                    st.success(f"Imported {count} rows.")
            except Exception as e:
                st.error(f"Error reading Excel: {e}")

# ---------------- Payroll ----------------
elif page == "Payroll":
    st.subheader("Payroll")
    st.markdown("Generate salary sheet and individual slips. All PDFs support date-range filtering.")
    employees_df = fetch_employees()
    start_date = st.date_input("Period start", value=date(date.today().year, date.today().month, 1))
    end_date = st.date_input("Period end", value=date.today())
    st.markdown("### Salary Sheet")
    st.write("This will generate salary sheet using base_salary stored in employees. Add deductions per-employee if needed (simple example).")
    # for demo: allow a global deduction percent or per-employee manual
    global_ded_pct = st.number_input("Global deduction % (applied to all as example)", min_value=0.0, max_value=100.0, value=0.0)
    if st.button("Generate Salary Sheet PDF"):
        # deductions map: simple percent deduction example
        deductions_map = {}
        for _, r in employees_df.iterrows():
            ded_amount = (float(r.get("base_salary") or 0.0) * (global_ded_pct/100.0))
            if ded_amount > 0:
                deductions_map[r["id"]] = [("Global deduction", ded_amount)]
        pdf_bytes = generate_salary_sheet_pdf(employees_df, start_date.isoformat(), end_date.isoformat(), deductions_map)
        st.download_button("Download Salary Sheet PDF", data=pdf_bytes, file_name=f"salary_sheet_{start_date}_{end_date}.pdf", mime="application/pdf")
    st.markdown("### Individual Salary Slip")
    emp_options = employees_df.set_index("id")["name"].to_dict() if not employees_df.empty else {}
    emp_choice = st.selectbox("Select employee", options=list(emp_options.keys()) if emp_options else [], format_func=lambda x: emp_options.get(x) if emp_options else "")
    if emp_choice:
        if st.button("Download Individual Salary Slip"):
            emp_row = employees_df[employees_df["id"]==emp_choice].iloc[0].to_dict()
            # example: no deductions by default
            pdf_bytes = generate_individual_salary_slip_pdf(emp_row, start_date.isoformat(), end_date.isoformat(), deductions=[])
            st.download_button("Download Slip", data=pdf_bytes, file_name=f"salary_slip_{emp_row.get('employee_code')}_{start_date}_{end_date}.pdf", mime="application/pdf")

# ---------------- Expenses ----------------
elif page == "Expenses":
    st.subheader("Expenses")
    st.markdown("Add expenses (company or employee added), mark reimbursement, manage categories.")
    categories = fetch_categories()
    employee_df = fetch_employees()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Add Expense")
        emp_map = {0: "Company"}  # allow company expenses with employee_id null/0
        if not employee_df.empty:
            emp_map.update(employee_df.set_index("id")["name"].to_dict())
        emp_choice = st.selectbox("Employee (choose Company for non-employee expense)", options=list(emp_map.keys()), format_func=lambda x: emp_map[x])
        cat = st.text_input("Category", value=(categories["name"].iloc[0] if not categories.empty else "General"))
        desc = st.text_input("Description")
        amt = st.number_input("Amount", value=0.0, format="%.2f")
        ex_date = st.date_input("Expense Date", value=date.today())
        if st.button("Add Expense"):
            emp_id = None if emp_choice==0 else emp_choice
            add_expense(emp_id, cat, desc, float(amt), to_iso(ex_date))
            st.success("Expense added.")
    with col2:
        st.markdown("### Expenses List / Reimburse")
        start = st.date_input("From", value=date(date.today().year, date.today().month, 1), key="exp_from")
        end = st.date_input("To", value=date.today(), key="exp_to")
        cat_filter = st.selectbox("Filter by category (optional)", options=["All"] + list(categories["name"].tolist()) if not categories.empty else ["All"])
        df = fetch_expenses(start.isoformat(), end.isoformat(), None if cat_filter=="All" else cat_filter)
        st.dataframe(df)
        sel = st.number_input("Select expense id to reimburse (enter id)", min_value=0, step=1)
        if st.button("Reimburse expense"):
            if sel > 0:
                success = reimburse_expense(sel, to_iso(date.today()))
                if success:
                    st.success("Reimbursed and ledger updated.")
                else:
                    st.warning("Already reimbursed or not found.")

    st.markdown("### Manage Categories")
    new_cat = st.text_input("New category name")
    new_cat_desc = st.text_area("Category description")
    if st.button("Add/Update Category"):
        if new_cat.strip() == "":
            st.error("Category name cannot be empty.")
        else:
            add_category(new_cat.strip(), new_cat_desc)
            st.success("Category saved.")
    st.write(fetch_categories())

# ---------------- Reports & Exports ----------------
elif page == "Reports & Exports":
    st.subheader("Reports & PDF Exports")
    start = st.date_input("From", value=date(date.today().year, date.today().month, 1), key="rep_from")
    end = st.date_input("To", value=date.today(), key="rep_to")
    group_by_cat = st.checkbox("Group by category", value=True)
    if st.button("Generate Expense Report PDF"):
        df = fetch_expenses(start.isoformat(), end.isoformat())
        pdf_bytes = generate_expense_report_pdf(df, start.isoformat(), end.isoformat(), group_by_category=group_by_cat)
        st.download_button("Download Expense Report PDF", data=pdf_bytes, file_name=f"expense_report_{start}_{end}.pdf", mime="application/pdf")
    if st.button("Download Expense Categories Sheet (PDF)"):
        cats = fetch_categories()
        # create a simple PDF listing categories
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        w,h = A4
        y = h - 30*mm
        c.setFont("Helvetica-Bold", 14)
        c.drawString(20*mm, y, "Expense Categories")
        y -= 12*mm
        c.setFont("Helvetica", 10)
        for _, r in cats.iterrows():
            if y < 30*mm:
                c.showPage()
                y = h - 30*mm
            c.drawString(25*mm, y, f"- {r['name']}: {r['description'] or ''}")
            y -= 8*mm
        c.showPage()
        c.save()
        buf.seek(0)
        st.download_button("Download Category Sheet PDF", data=buf.read(), file_name="expense_categories.pdf", mime="application/pdf")

# ---------------- Settings / Data Import ----------------
elif page == "Settings / Data Import":
    st.subheader("Settings & Data import/export")
    st.markdown("You can export DB or reset (use with caution).")
    if st.button("Export entire database to SQL dump"):
        conn = get_conn()
        with open("dump.sql", "w", encoding="utf-8") as f:
            for line in conn.iterdump():
                f.write("%s\n" % line)
        conn.close()
        with open("dump.sql", "rb") as f:
            st.download_button("Download SQL Dump", f, file_name="dump.sql", mime="application/sql")
    if st.button("Reset database (dropping tables) - DANGEROUS"):
        st.warning("This will delete all data.")
        if st.button("Confirm Reset DB"):
            conn = get_conn()
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS employee_ledger_entries")
            c.execute("DROP TABLE IF EXISTS expenses")
            c.execute("DROP TABLE IF EXISTS expense_categories")
            c.execute("DROP TABLE IF EXISTS employees")
            conn.commit()
            conn.close()
            init_db()
            st.success("Database reset.")

st.markdown("---")
st.markdown("**Datanex Solution** | For any query please contact 📞 +92320 7429422")
