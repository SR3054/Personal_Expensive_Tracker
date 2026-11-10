import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import date

# FastAPI backend URL
API_URL = "http://127.0.0.1:8000"

# Page configuration
st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# Dashboard title
st.title("💰 Personal Expense Tracker")
st.caption("Manage your income and expenses in one place.")

# Fetch transactions from FastAPI
def get_expenses():
    try:
        response = requests.get(f"{API_URL}/expenses", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        st.error("Cannot connect to FastAPI. Please check your backend.")
        return []


# Fetch summary from FastAPI
def get_summary():
    try:
        response = requests.get(f"{API_URL}/summary", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        st.error("Unable to fetch summary.")
        return None


# Load data
expenses = get_expenses()
summary = get_summary()

# Dashboard metrics
st.subheader("📊 Financial Overview")

if summary:
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Total Income",
        f"₹{summary['total_income']:,.2f}"
    )

    col2.metric(
        "Total Expenses",
        f"₹{summary['total_expenses']:,.2f}"
    )

    col3.metric(
        "Available Balance",
        f"₹{summary['balance']:,.2f}"
    )

    col4.metric(
        "Transactions",
        summary["total_transactions"]
    )

st.divider()

# Add transaction
st.subheader("➕ Add New Transaction")

with st.form("add_expense_form"):

    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Transaction Title")
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            step=100.0
        )
        category = st.text_input("Category")

    with col2:
        transaction_type = st.selectbox(
            "Transaction Type",
            ["Expense", "Income"]
        )

        transaction_date = st.date_input(
            "Transaction Date",
            value=date.today()
        )

    submitted = st.form_submit_button("Add Transaction")

    if submitted:

        if not title.strip() or not category.strip():
            st.warning("Please enter title and category.")

        else:
            new_expense = {
                "title": title,
                "amount": amount,
                "category": category,
                "type": transaction_type,
                "date": str(transaction_date)
            }

            try:
                response = requests.post(
                    f"{API_URL}/expenses",
                    json=new_expense,
                    timeout=5
                )

                if response.status_code == 200:
                    st.success("Transaction added successfully!")
                    st.rerun()
                else:
                    st.error(response.text)

            except requests.RequestException as e:
                st.error(f"API connection error: {e}")


st.divider()

# Transaction history
st.subheader("📋 Transaction History")

if expenses:

    df = pd.DataFrame(expenses)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("No transactions available. Add your first transaction!")


st.divider()

# Charts
st.subheader("📈 Expense Analysis")

if expenses:

    df = pd.DataFrame(expenses)

    expense_df = df[df["type"] == "Expense"]

    col1, col2 = st.columns(2)

    with col1:
        if not expense_df.empty:
            category_data = (
                expense_df.groupby("category")["amount"]
                .sum()
                .reset_index()
            )

            fig = px.pie(
                category_data,
                names="category",
                values="amount",
                title="Expenses by Category",
                hole=0.4
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No expense data available for the pie chart.")

    with col2:
        type_data = (
            df.groupby("type")["amount"]
            .sum()
            .reset_index()
        )

        fig = px.bar(
            type_data,
            x="type",
            y="amount",
            color="type",
            title="Income vs Expenses",
            labels={
                "type": "Transaction Type",
                "amount": "Amount (₹)"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

else:
    st.info("Add transactions to see your charts.")


st.divider()

# Update transaction
st.subheader("✏️ Update Transaction")

if expenses:

    expense_ids = [item["id"] for item in expenses]

    selected_id = st.selectbox(
        "Select transaction to update",
        expense_ids,
        format_func=lambda x: next(
            (
                f"{item['title']} - ₹{item['amount']}"
                for item in expenses
                if item["id"] == x
            ),
            x
        )
    )

    selected_expense = next(
        item for item in expenses
        if item["id"] == selected_id
    )

    with st.form("update_form"):

        new_title = st.text_input(
            "Title",
            value=selected_expense["title"]
        )

        new_amount = st.number_input(
            "Amount",
            min_value=0.01,
            value=float(selected_expense["amount"])
        )

        new_category = st.text_input(
            "Category",
            value=selected_expense["category"]
        )

        new_type = st.selectbox(
            "Type",
            ["Expense", "Income"],
            index=["Expense", "Income"].index(
                selected_expense["type"]
            )
        )

        new_date = st.date_input(
            "Date",
            value=date.fromisoformat(selected_expense["date"])
        )

        update_button = st.form_submit_button("Update Transaction")

        if update_button:

            updated_data = {
                "title": new_title,
                "amount": new_amount,
                "category": new_category,
                "type": new_type,
                "date": str(new_date)
            }

            try:
                response = requests.put(
                    f"{API_URL}/expenses/{selected_id}",
                    json=updated_data,
                    timeout=5
                )

                if response.status_code == 200:
                    st.success("Transaction updated successfully!")
                    st.rerun()
                else:
                    st.error(response.text)

            except requests.RequestException as e:
                st.error(f"API connection error: {e}")

else:
    st.info("Add a transaction before trying to update it.")


st.divider()

# Delete transaction
st.subheader("🗑️ Delete Transaction")

if expenses:

    delete_id = st.selectbox(
        "Select transaction to delete",
        [item["id"] for item in expenses],
        key="delete_selection",
        format_func=lambda x: next(
            (
                f"{item['title']} - ₹{item['amount']}"
                for item in expenses
                if item["id"] == x
            ),
            x
        )
    )

    if st.button("Delete Selected Transaction", type="primary"):

        try:
            response = requests.delete(
                f"{API_URL}/expenses/{delete_id}",
                timeout=5
            )

            if response.status_code == 200:
                st.success("Transaction deleted successfully!")
                st.rerun()
            else:
                st.error(response.text)

        except requests.RequestException as e:
            st.error(f"API connection error: {e}")

else:
    st.info("No transactions available to delete.")

# Footer
st.divider()
st.caption("Personal Expense Tracker | Built with FastAPI and Streamlit")
