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

# Parse the markdown table into a DataFrame
@st.cache_data
def parse_markdown_table(content):
    """Parse the markdown table from the provided content"""
    lines = content.split('\n')
    
    # Find the start of the table (line with | S.NO |)
    start_idx = 0
    for i, line in enumerate(lines):
        if '| S.NO |' in line:
            start_idx = i
            break
    
    # Extract table rows
    table_rows = []
    for line in lines[start_idx:]:
        if line.strip() and '|' in line:
            # Clean the line
            line = line.strip()
            if line.startswith('|'):
                line = line[1:]
            if line.endswith('|'):
                line = line[:-1]
            
            # Split and clean columns
            cols = [col.strip() for col in line.split('|')]
            table_rows.append(cols)
    
    # Create DataFrame
    if table_rows:
        df = pd.DataFrame(table_rows[1:], columns=table_rows[0])
        
        # Clean column names
        df.columns = [col.strip() for col in df.columns]
        
        # Convert data types
        numeric_cols = ['S.NO', 'Qty', 'RATE', 'AMOUNT', 'INCOME', 'EXPENSE', 'BALANCE']
        for col in numeric_cols:
            if col in df.columns:
                # Remove formula references and convert to numeric
                df[col] = pd.to_numeric(df[col].astype(str).str.replace('=.*', ''), errors='coerce')
        
        # Clean DATE column
        if 'DATE' in df.columns:
            df['DATE'] = pd.to_datetime(df['DATE'].astype(str).str.replace(' 00:00:00', ''), errors='coerce')
        
        # Clean other columns
        text_cols = ['MAIN HEAD', 'CROP YEAR', 'INDIVIDUAL', 'SUB HEAD', 'ITEM', 'DESCRIPTION']
        for col in text_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
        
        return df
    return pd.DataFrame()

# Load the data
file_content = """[Your entire file content from above]"""
df = parse_markdown_table(file_content)

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
            max_value=max_date
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
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_income = filtered_df['INCOME'].sum()
        st.metric("Total Income", f"₹{total_income:,.0f}")
    
    with col2:
        total_expense = filtered_df['EXPENSE'].sum()
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
        if 'DATE' in filtered_df.columns:
            monthly_data = filtered_df.copy()
            monthly_data['Month'] = monthly_data['DATE'].dt.strftime('%Y-%m')
            monthly_summary = monthly_data.groupby('Month').agg({
                'INCOME': 'sum',
                'EXPENSE': 'sum'
            }).reset_index()
            
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
    
    with col2:
        st.markdown("#### Transaction Types")
        if 'MAIN HEAD' in filtered_df.columns:
            transaction_types = filtered_df['MAIN HEAD'].value_counts()
            fig = px.pie(
                values=transaction_types.values,
                names=transaction_types.index,
                title="Distribution by Transaction Type",
                color_discrete_sequence=px.colors.sequential.Viridis
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    # Recent transactions
    st.markdown("#### Recent Transactions")
    if 'DATE' in filtered_df.columns:
        recent_transactions = filtered_df.sort_values('DATE', ascending=False).head(10)
        st.dataframe(
            recent_transactions[['DATE', 'INDIVIDUAL', 'MAIN HEAD', 'SUB HEAD', 'ITEM', 'INCOME', 'EXPENSE', 'BALANCE']],
            use_container_width=True
        )

with tab2:
    st.markdown('<h2 class="sub-header">Transaction Details</h2>', unsafe_allow_html=True)
    
    # Search functionality
    search_term = st.text_input("🔍 Search in Description", "")
    if search_term:
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
        st.dataframe(
            display_df.style.format({
                'INCOME': '₹{:,.0f}',
                'EXPENSE': '₹{:,.0f}',
                'BALANCE': '₹{:,.0f}',
                'AMOUNT': '₹{:,.0f}',
                'RATE': '₹{:,.0f}'
            }),
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
            expense_by_individual = filtered_df[filtered_df['EXPENSE'] > 0].groupby('INDIVIDUAL')['EXPENSE'].sum()
            fig = px.bar(
                x=expense_by_individual.index,
                y=expense_by_individual.values,
                title="Expense Distribution by Individual",
                labels={'x': 'Individual', 'y': 'Total Expense (₹)'},
                color=expense_by_individual.values,
                color_continuous_scale='Reds'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Expense by Category")
            expense_by_category = filtered_df[filtered_df['EXPENSE'] > 0].groupby('SUB HEAD')['EXPENSE'].sum()
            fig = px.pie(
                values=expense_by_category.values,
                names=expense_by_category.index,
                title="Expense by Category",
                hole=0.3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Income Sources":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Income by Individual")
            income_by_individual = filtered_df[filtered_df['INCOME'] > 0].groupby('INDIVIDUAL')['INCOME'].sum()
            fig = px.bar(
                x=income_by_individual.index,
                y=income_by_individual.values,
                title="Income Distribution by Individual",
                labels={'x': 'Individual', 'y': 'Total Income (₹)'},
                color=income_by_individual.values,
                color_continuous_scale='Greens'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### Income Sources")
            income_sources = filtered_df[filtered_df['INCOME'] > 0].groupby('SUB HEAD')['INCOME'].sum()
            fig = px.pie(
                values=income_sources.values,
                names=income_sources.index,
                title="Income by Source",
                hole=0.3
            )
            st.plotly_chart(fig, use_container_width=True)
    
    elif analysis_type == "Monthly Trends":
        st.markdown("#### Monthly Income & Expense Trends")
        if 'DATE' in filtered_df.columns:
            monthly_trends = filtered_df.copy()
            monthly_trends['Month'] = monthly_trends['DATE'].dt.strftime('%Y-%m')
            monthly_summary = monthly_trends.groupby('Month').agg({
                'INCOME': 'sum',
                'EXPENSE': 'sum'
            }).reset_index()
            
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
            person_income = person_data['INCOME'].sum()
            st.metric(f"{selected_person}'s Total Income", f"₹{person_income:,.0f}")
        
        with col2:
            person_expense = person_data['EXPENSE'].sum()
            st.metric(f"{selected_person}'s Total Expense", f"₹{person_expense:,.0f}")
        
        with col3:
            person_net = person_income - person_expense
            st.metric(f"{selected_person}'s Net Balance", f"₹{person_net:,.0f}")
        
        # Individual analysis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"#### {selected_person}'s Top Expenses")
            top_expenses = person_data[person_data['EXPENSE'] > 0].nlargest(10, 'EXPENSE')
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
        
        with col2:
            st.markdown(f"#### {selected_person}'s Income Sources")
            income_sources = person_data[person_data['INCOME'] > 0].groupby('SUB HEAD')['INCOME'].sum()
            if len(income_sources) > 0:
                fig = px.pie(
                    values=income_sources.values,
                    names=income_sources.index,
                    title="Income Sources Distribution",
                    hole=0.3
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info(f"{selected_person} has no recorded income in the selected period.")

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
