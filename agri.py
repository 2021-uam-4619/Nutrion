import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# Set page configuration
st.set_page_config(
    page_title="Farm Accounts Ledger 2023-25",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #2E8B57;
    }
    .sub-header {
        font-size: 1.8rem;
        color: #3CB371;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #2E8B57;
        margin-bottom: 1rem;
    }
    .positive {
        color: #28a745;
        font-weight: bold;
    }
    .negative {
        color: #dc3545;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Create sample data based on the Excel structure
@st.cache_data
def create_sample_data():
    """Create sample data based on the Excel structure"""
    data = []
    
    # Sample data based on the provided Excel rows
    sample_transactions = [
        # Format: [S.NO, MAIN HEAD, CROP YEAR, INDIVIDUAL, SUB HEAD, ITEM, DETAIL TAKEN, UNIT, Qty, RATE, AMOUNT, DESCRIPTION, DATE, INCOME, EXPENSE, BALANCE]
        [1, "Invest.", "2024-25", "Junaid", "Asset", "Tractor", "Acc. Group", "Each", 1, 800000, 800000, "FIAT 480 2012 Model", "2022-05-06", None, 800000, 800000],
        [2, "Invest.", "2024-25", "Junaid", "Asset", "Hall", "Acc. Group", "Each", 1, 60000, 60000, "Hall Frame", "2022-05-06", None, 60000, 1400000],
        [3, "Invest.", "2024-25", "Junaid", "Asset", "Insect", "Acc. Group", "Bundle", 6, 42500, 255000, "6 Bundle (1 Biggah) Insect @ Rs. 42500/Bundle", "2022-05-29", None, 255000, 1655000],
        [4, "Invest.", "2024-25", "Junaid", "Asset", "Pipe", "Acc. Group", "Each", 260, 1517, 394420, "260 Pipes @ Rs. 1517/Pipe", "2022-06-04", None, 394420, 2049420],
        [5, "Invest.", "2024-25", "Junaid", "Asset", "Pipe", "Acc. Group", "Each", 8, 1000, 8000, "8 Used Pipes From Riaz @ Rs. 1000/Pipe", "2022-06-09", None, 8000, 2057420],
        [6, "Invest.", "2024-25", "Junaid", "Asset", "Steel", "Acc. Group", None, None, None, None, "Steel For Pipes", "2022-06-12", None, 24000, 2081420],
        [7, "Invest.", "2024-25", "Junaid", "Asset", "Steel", "Acc. Group", None, None, None, None, "Steel For Pipes", "2022-06-15", None, 20000, 2101420],
        [8, "Invest.", "2024-25", "Junaid", "Asset", "Steel", "Acc. Group", None, None, None, None, "Steel For Pipes", "2022-06-18", None, 12000, 2113420],
        [9, "Invest.", "2023-24", "Junaid", "Kheera", "Rope", "Acc. Group", "Kg", 22.3, 330, 7400, "22.3 Kg Rope For Tunnel @ Rs. 330/Kg", "2022-06-26", None, 7400, 2120820],
        [10, "Invest.", "2023-24", "Junaid", "Kheera", "Jaal", "Acc. Group", "Each", 50, 320, 16000, "50 Jaal @ Rs. 320/Jaal", "2022-06-26", None, 16000, 2136820],
        [28, "Income", "2023-24", "Junaid", "Mustajri", "M. Bher", "Acc. Group", None, None, None, None, "Mustajri Received From M. Bher", "2023-05-16", 23000, None, 23000],
        [29, "Income", "2023-24", "Junaid", "Mustajri", "M. Bher", "Acc. Group", None, None, None, None, "Mustajri Received From M. Bher", "2023-05-19", 27000, None, 50000],
        [30, "Income", "2023-24", "Junaid", "Mustajri", "M. Bher", "Acc. Group", None, None, None, None, "Mustajri Received From M. Bher (Aslam)", "2023-06-05", 30000, None, 80000],
        [31, "Income", "2023-24", "Junaid", "Mustajri", "M. Bher", "Acc. Group", None, None, None, None, "Mustajri Received From M. Bher (Pathan)", "2023-06-05", 60000, None, 140000],
        [259, "Income", "2023-24", "Mannan", "Kheera", "Sale", "Inc. Group", "Shoppers", 150, 130, 19500, "A-6 Kheera Sale", "2023-09-17", 19500, None, 19500],
        [278, "Income", "2023-24", "Mannan", "Kheera", "Sale", "Inc. Group", "Shoppers", 575, 102, 58650, "A-6 Kheera Sale", "2023-09-20", 58650, None, 78150],
        [279, "Income", "2023-24", "Mannan", "Kheera", "Sale", "Inc. Group", "Shoppers", None, None, None, "A-4 Kheera Sale", "2023-09-21", 42280, None, 120430],
        [291, "Income", "2023-24", "Junaid", "Kheera", "Sale", "Inc. Group", "Shoppers", 554, 33.123, 18350, "A-6 Kheera Sale", "2023-09-23", 18350, None, 18350],
        [308, "Income", "2023-24", "Mannan", "Kheera", "Sale", "Inc. Group", "Shoppers", 525, 90, 47250, "A-6 Kheera Sale", "2023-09-29", 47250, None, 167680],
        [319, "Income", "2023-24", "Mannan", "Kheera", "Sale", "Inc. Group", "Shoppers", 485, 166, 80510, "A-6 Kheera Sale", "2023-10-02", 80510, None, 248190],
        [569, "Income", "2023-24", "Mannan", "Corn", "Sale", "Inc. Group", "Mun", 247, 1668.015, 412000, "Sale Of Corn To Asia Feed Mill", "2023-12-01", 412000, None, 660190],
        [646, "Income", "2023-24", "Mannan", "Corn", "Sale", "Inc. Group", "Mun", None, None, None, "Sale Of Corn", "2023-12-15", 200000, None, 860190],
    ]
    
    # Add more Mannan transactions
    for i in range(20, 25):
        sample_transactions.append([
            i+100, "Invest.", "2023-24", "Mannan", "Kheera", "Seed", "Inv. Group", "Pckt", np.random.randint(5, 20), 
            np.random.randint(3000, 5000), None, f"Seed Purchase {i}", 
            f"2023-{np.random.randint(8,12):02d}-{np.random.randint(1,28):02d}", 
            None, np.random.randint(5000, 20000), None
        ])
    
    # Add more Junaid transactions
    for i in range(25, 35):
        sample_transactions.append([
            i+200, "Invest.", "2023-24", "Junaid", "Corn", "Fertilizer", "Inv. Group", "Bag", 
            np.random.randint(1, 10), np.random.randint(2000, 5000), None, f"Fertilizer Purchase {i}", 
            f"2023-{np.random.randint(7,10):02d}-{np.random.randint(1,28):02d}", 
            None, np.random.randint(10000, 50000), None
        ])
    
    # Create DataFrame
    df = pd.DataFrame(sample_transactions, columns=[
        'S.NO', 'MAIN HEAD', 'CROP YEAR', 'INDIVIDUAL', 'SUB HEAD', 'ITEM', 
        'DETAIL TAKEN', 'UNIT', 'Qty', 'RATE', 'AMOUNT', 'DESCRIPTION', 
        'DATE', 'INCOME', 'EXPENSE', 'BALANCE'
    ])
    
    # Convert date column
    df['DATE'] = pd.to_datetime(df['DATE'], errors='coerce')
    
    # Fill missing AMOUNT values
    df['AMOUNT'] = df.apply(
        lambda row: row['Qty'] * row['RATE'] if pd.notna(row['Qty']) and pd.notna(row['RATE']) else row['AMOUNT'],
        axis=1
    )
    
    # Calculate BALANCE for rows where it's missing
    # This is simplified - in real scenario, balance would be cumulative
    for idx, row in df.iterrows():
        if pd.isna(row['BALANCE']):
            if pd.notna(row['INCOME']):
                df.at[idx, 'BALANCE'] = row['INCOME']
            elif pd.notna(row['EXPENSE']):
                df.at[idx, 'BALANCE'] = -row['EXPENSE']
    
    # Convert numeric columns
    numeric_cols = ['S.NO', 'Qty', 'RATE', 'AMOUNT', 'INCOME', 'EXPENSE', 'BALANCE']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    return df

# Load the data
df = create_sample_data()

# Title and description
st.markdown('<h1 class="main-header">🏪 Farm Accounts Ledger System 2023-25</h1>', unsafe_allow_html=True)
st.markdown("""
This dashboard provides a comprehensive view of agricultural investments, income, and expenses for multiple individuals
across different crop years. Explore the data using the filters and visualizations below.
""")

# Sidebar for filters
with st.sidebar:
    st.markdown("### 🎛️ Filters")
    
    # Date range filter
    if 'DATE' in df.columns:
        min_date = df['DATE'].min().date()
        max_date = df['DATE'].max().date()
        date_range = st.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_date=max_date
        )
    
    # Individual filter
    if 'INDIVIDUAL' in df.columns:
        individuals = ['All'] + sorted(df['INDIVIDUAL'].dropna().unique().tolist())
        selected_individual = st.selectbox("Select Individual", individuals)
    
    # Crop Year filter
    if 'CROP YEAR' in df.columns:
        crop_years = ['All'] + sorted(df['CROP YEAR'].dropna().unique().tolist())
        selected_crop_year = st.selectbox("Select Crop Year", crop_years)
    
    # Main Head filter
    if 'MAIN HEAD' in df.columns:
        main_heads = ['All'] + sorted(df['MAIN HEAD'].dropna().unique().tolist())
        selected_main_head = st.selectbox("Select Transaction Type", main_heads)
    
    # Sub Head filter
    if 'SUB HEAD' in df.columns:
        sub_heads = ['All'] + sorted(df['SUB HEAD'].dropna().unique().tolist())
        selected_sub_head = st.selectbox("Select Sub Category", sub_heads)
    
    st.markdown("---")
    st.markdown("### 💡 Tips")
    st.info("Use the filters to drill down into specific data. Click on charts to see more details.")

# Apply filters
filtered_df = df.copy()

if 'DATE' in filtered_df.columns:
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['DATE'].dt.date >= start_date) & 
            (filtered_df['DATE'].dt.date <= end_date)
        ]

if 'INDIVIDUAL' in filtered_df.columns and selected_individual != 'All':
    filtered_df = filtered_df[filtered_df['INDIVIDUAL'] == selected_individual]

if 'CROP YEAR' in filtered_df.columns and selected_crop_year != 'All':
    filtered_df = filtered_df[filtered_df['CROP YEAR'] == selected_crop_year]

if 'MAIN HEAD' in filtered_df.columns and selected_main_head != 'All':
    filtered_df = filtered_df[filtered_df['MAIN HEAD'] == selected_main_head]

if 'SUB HEAD' in filtered_df.columns and selected_sub_head != 'All':
    filtered_df = filtered_df[filtered_df['SUB HEAD'] == selected_sub_head]

# Main dashboard layout
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Overview", "💰 Transactions", "📈 Analysis", "👥 By Individual", "📤 Export"])

with tab1:
    st.markdown('<h2 class="sub-header">Dashboard Overview</h2>', unsafe_allow_html=True)
    
    # Key metrics - handle missing columns gracefully
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_income = filtered_df['INCOME'].sum() if 'INCOME' in filtered_df.columns else 0
        st.metric("Total Income", f"₹{total_income:,.0f}")
    
    with col2:
        total_expense = filtered_df['EXPENSE'].sum() if 'EXPENSE' in filtered_df.columns else 0
        st.metric("Total Expense", f"₹{total_expense:,.0f}")
    
    with col3:
        net_balance = total_income - total_expense
        st.metric("Net Balance", f"₹{net_balance:,.0f}")
    
    with col4:
        transaction_count = len(filtered_df)
        st.metric("Total Transactions", transaction_count)
    
    # Summary charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Income vs Expense by Month")
        if 'DATE' in filtered_df.columns and 'INCOME' in filtered_df.columns and 'EXPENSE' in filtered_df.columns:
            monthly_data = filtered_df.copy()
            monthly_data['Month'] = monthly_data['DATE'].dt.strftime('%Y-%m')
            monthly_summary = monthly_data.groupby('Month').agg({
                'INCOME': 'sum',
                'EXPENSE': 'sum'
            }).reset_index()
            
            if not monthly_summary.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=monthly_summary['Month'],
                    y=monthly_summary['INCOME'],
                    name='Income',
                    marker_color='#28a745'
                ))
                fig.add_trace(go.Bar(
                    x=monthly_summary['Month'],
                    y=monthly_summary['EXPENSE'],
                    name='Expense',
                    marker_color='#dc3545'
                ))
                fig.update_layout(
                    barmode='group',
                    xaxis_title='Month',
                    yaxis_title='Amount (₹)',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No data available for the selected filters.")
    
    with col2:
        st.markdown("#### Transaction Types")
        if 'MAIN HEAD' in filtered_df.columns:
            transaction_types = filtered_df['MAIN HEAD'].value_counts()
            if not transaction_types.empty:
                fig = px.pie(
                    values=transaction_types.values,
                    names=transaction_types.index,
                    title="Distribution by Transaction Type",
                    color_discrete_sequence=px.colors.sequential.Viridis
                )
                fig.update_traces(textposition='inside', textinfo='percent+label')
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No transaction type data available.")
    
    # Recent transactions
    st.markdown("#### Recent Transactions")
    if 'DATE' in filtered_df.columns:
        recent_transactions = filtered_df.sort_values('DATE', ascending=False).head(10)
        display_cols = []
        for col in ['DATE', 'INDIVIDUAL', 'MAIN HEAD', 'SUB HEAD', 'ITEM', 'INCOME', 'EXPENSE', 'BALANCE']:
            if col in filtered_df.columns:
                display_cols.append(col)
        
        if display_cols:
            st.dataframe(
                recent_transactions[display_cols],
                use_container_width=True
            )

with tab2:
    st.markdown('<h2 class="sub-header">Transaction Details</h2>', unsafe_allow_html=True)
    
    # Search functionality
    search_term = st.text_input("🔍 Search in Description", "")
    if search_term and 'DESCRIPTION' in filtered_df.columns:
        search_df = filtered_df[filtered_df['DESCRIPTION'].str.contains(search_term, case=False, na=False)]
    else:
        search_df = filtered_df
    
    # Detailed view with pagination
    if len(search_df) > 0:
        items_per_page = 20
        total_pages = max(1, (len(search_df) - 1) // items_per_page + 1)
        
        page_number = st.number_input("Page", min_value=1, max_value=total_pages, value=1)
        start_idx = (page_number - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(search_df))
        
        # Display the data
        display_df = search_df.iloc[start_idx:end_idx].copy()
        
        # Format numeric columns
        format_dict = {}
        for col in ['INCOME', 'EXPENSE', 'BALANCE', 'AMOUNT', 'RATE']:
            if col in display_df.columns:
                format_dict[col] = '₹{:,.0f}'
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600
        )
        
        # Pagination info
        st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(search_df)} transactions")
    else:
        st.info("No transactions found with the current filters.")

with tab3:
    st.markdown('<h2 class="sub-header">Detailed Analysis</h2>', unsafe_allow_html=True)
    
    # Analysis options
    analysis_type = st.selectbox(
        "Select Analysis Type",
        ["Expense Breakdown", "Income Sources", "Monthly Trends", "Category Analysis"]
    )
    
    if analysis_type == "Expense Breakdown":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Expense by Individual")
            if 'EXPENSE' in filtered_df.columns and 'INDIVIDUAL' in filtered_df.columns:
                expense_data = filtered_df[filtered_df['EXPENSE'] > 0]
                if not expense_data.empty:
                    expense_by_individual = expense_data.groupby('INDIVIDUAL')['EXPENSE'].sum()
                    fig = px.bar(
                        x=expense_by_individual.index,
                        y=expense_by_individual.values,
                        title="Expense Distribution by Individual",
                        labels={'x': 'Individual', 'y': 'Total Expense (₹)'},
                        color=expense_by_individual.values,
                        color_continuous_scale='Reds'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No expense data available.")
        
        with col2:
            st.markdown("#### Expense by Category")
            if 'EXPENSE' in filtered_df.columns and 'SUB HEAD' in filtered_df.columns:
                expense_data = filtered_df[filtered_df['EXPENSE'] > 0]
                if not expense_data.empty:
                    expense_by_category = expense_data.groupby('SUB HEAD')['EXPENSE'].sum()
                    if not expense_by_category.empty:
                        fig = px.pie(
                            values=expense_by_category.values,
                            names=expense_by_category.index,
                            title="Expense by Category",
                            hole=0.3
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No expense categories available.")
                else:
                    st.info("No expense data available.")
    
    elif analysis_type == "Income Sources":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Income by Individual")
            if 'INCOME' in filtered_df.columns and 'INDIVIDUAL' in filtered_df.columns:
                income_data = filtered_df[filtered_df['INCOME'] > 0]
                if not income_data.empty:
                    income_by_individual = income_data.groupby('INDIVIDUAL')['INCOME'].sum()
                    fig = px.bar(
                        x=income_by_individual.index,
                        y=income_by_individual.values,
                        title="Income Distribution by Individual",
                        labels={'x': 'Individual', 'y': 'Total Income (₹)'},
                        color=income_by_individual.values,
                        color_continuous_scale='Greens'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No income data available.")
        
        with col2:
            st.markdown("#### Income Sources")
            if 'INCOME' in filtered_df.columns and 'SUB HEAD' in filtered_df.columns:
                income_data = filtered_df[filtered_df['INCOME'] > 0]
                if not income_data.empty:
                    income_sources = income_data.groupby('SUB HEAD')['INCOME'].sum()
                    if not income_sources.empty:
                        fig = px.pie(
                            values=income_sources.values,
                            names=income_sources.index,
                            title="Income by Source",
                            hole=0.3
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No income sources available.")
                else:
                    st.info("No income data available.")
    
    elif analysis_type == "Monthly Trends":
        st.markdown("#### Monthly Income & Expense Trends")
        if 'DATE' in filtered_df.columns and 'INCOME' in filtered_df.columns and 'EXPENSE' in filtered_df.columns:
            monthly_trends = filtered_df.copy()
            monthly_trends['Month'] = monthly_trends['DATE'].dt.strftime('%Y-%m')
            monthly_summary = monthly_trends.groupby('Month').agg({
                'INCOME': 'sum',
                'EXPENSE': 'sum'
            }).reset_index()
            
            if not monthly_summary.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=monthly_summary['Month'],
                    y=monthly_summary['INCOME'],
                    name='Income',
                    mode='lines+markers',
                    line=dict(color='#28a745', width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=monthly_summary['Month'],
                    y=monthly_summary['EXPENSE'],
                    name='Expense',
                    mode='lines+markers',
                    line=dict(color='#dc3545', width=3)
                ))
                fig.update_layout(
                    xaxis_title='Month',
                    yaxis_title='Amount (₹)',
                    height=500
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No monthly trend data available.")

with tab4:
    st.markdown('<h2 class="sub-header">Individual Performance</h2>', unsafe_allow_html=True)
    
    # Select individual for detailed view
    if 'INDIVIDUAL' in df.columns:
        individuals_list = df['INDIVIDUAL'].dropna().unique().tolist()
        selected_person = st.selectbox("Select Person to Analyze", individuals_list)
        
        person_data = df[df['INDIVIDUAL'] == selected_person].copy()
        
        # Individual metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            person_income = person_data['INCOME'].sum() if 'INCOME' in person_data.columns else 0
            st.metric(f"{selected_person}'s Total Income", f"₹{person_income:,.0f}")
        
        with col2:
            person_expense = person_data['EXPENSE'].sum() if 'EXPENSE' in person_data.columns else 0
            st.metric(f"{selected_person}'s Total Expense", f"₹{person_expense:,.0f}")
        
        with col3:
            person_net = person_income - person_expense
            st.metric(f"{selected_person}'s Net Balance", f"₹{person_net:,.0f}")
        
        # Individual analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {selected_person}'s Top Expenses")
            if 'EXPENSE' in person_data.columns and 'DESCRIPTION' in person_data.columns:
                expense_data = person_data[person_data['EXPENSE'] > 0]
                if not expense_data.empty:
                    top_expenses = expense_data.nlargest(10, 'EXPENSE')
                    fig = px.bar(
                        x=top_expenses['DESCRIPTION'].str[:50],
                        y=top_expenses['EXPENSE'],
                        title="Top 10 Expenses",
                        labels={'x': 'Description', 'y': 'Amount (₹)'},
                        color=top_expenses['EXPENSE'],
                        color_continuous_scale='Reds'
                    )
                    fig.update_layout(xaxis_tickangle=45, height=400)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info(f"{selected_person} has no recorded expenses.")
        
        with col2:
            st.markdown(f"#### {selected_person}'s Income Sources")
            if 'INCOME' in person_data.columns and 'SUB HEAD' in person_data.columns:
                income_data = person_data[person_data['INCOME'] > 0]
                if not income_data.empty:
                    income_sources = income_data.groupby('SUB HEAD')['INCOME'].sum()
                    if not income_sources.empty:
                        fig = px.pie(
                            values=income_sources.values,
                            names=income_sources.index,
                            title="Income Sources Distribution",
                            hole=0.3
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info(f"No income sources data for {selected_person}.")
                else:
                    st.info(f"{selected_person} has no recorded income.")

with tab5:
    st.markdown('<h2 class="sub-header">Export Data</h2>', unsafe_allow_html=True)
    
    # Export options
    export_format = st.radio(
        "Select Export Format",
        ["CSV", "Excel", "JSON"]
    )
    
    # Customize export
    st.markdown("#### Select Columns to Export")
    all_columns = filtered_df.columns.tolist()
    selected_columns = st.multiselect(
        "Choose columns (select all for full dataset)",
        all_columns,
        default=all_columns
    )
    
    export_df = filtered_df[selected_columns] if selected_columns else filtered_df
    
    if export_format == "CSV":
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"farm_ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    elif export_format == "Excel":
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df.to_excel(writer, index=False, sheet_name='Ledger')
        
        st.download_button(
            label="📥 Download Excel",
            data=output.getvalue(),
            file_name=f"farm_ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    elif export_format == "JSON":
        json_str = export_df.to_json(orient='records', indent=2)
        st.download_button(
            label="📥 Download JSON",
            data=json_str,
            file_name=f"farm_ledger_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    # Preview of export data
    st.markdown("#### Preview of Export Data")
    st.dataframe(export_df.head(10), use_container_width=True)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Farm Accounts Ledger System | Data from 2023-2025 | Last Updated: September 2025</p>
        <p>For queries, contact the farm administration</p>
    </div>
    """,
    unsafe_allow_html=True
)
