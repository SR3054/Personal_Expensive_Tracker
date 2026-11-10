
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from datetime import date
from pathlib import Path
import json
import uuid

app = FastAPI(
    title="Personal Expense Tracker",
    description="Expense Tracker API using FastAPI and JSON",
    version="1.0"
)

# JSON file location
DATA_FILE = Path(__file__).resolve().parent / "expenses.json"


# Transaction model
class Expense(BaseModel):
    title: str
    amount: float = Field(gt=0)
    category: str
    type: Literal["Income", "Expense"]
    date: date


# Read JSON data
def read_data():
    if not DATA_FILE.exists():
        return []

    with open(DATA_FILE, "r") as file:
        return json.load(file)


# Save JSON data
def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)


# Home API
@app.get("/")
def home():
    return {
        "message": "Welcome to Personal Expense Tracker",
        "status": "Running successfully"
    }


# GET: View all transactions
@app.get("/expenses")
def get_expenses():
    return read_data()


# POST: Add new transaction
@app.post("/expenses")
def add_expense(expense: Expense):

    expenses = read_data()

    new_expense = {
        "id": str(uuid.uuid4()),
        **expense.model_dump(mode="json")
    }

    expenses.append(new_expense)

    save_data(expenses)

    return {
        "message": "Transaction added successfully",
        "data": new_expense
    }


# PUT: Update transaction
@app.put("/expenses/{expense_id}")
def update_expense(expense_id: str, updated_expense: Expense):

    expenses = read_data()

    for index, expense in enumerate(expenses):

        if expense["id"] == expense_id:

            expenses[index] = {
                "id": expense_id,
                **updated_expense.model_dump(mode="json")
            }

            save_data(expenses)

            return {
                "message": "Transaction updated successfully",
                "data": expenses[index]
            }

    raise HTTPException(
        status_code=404,
        detail="Transaction not found"
    )


# DELETE: Delete transaction
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: str):

    expenses = read_data()

    updated_expenses = [
        expense for expense in expenses
        if expense["id"] != expense_id
    ]

    if len(expenses) == len(updated_expenses):
        raise HTTPException(
            status_code=404,
            detail="Transaction not found"
        )

    save_data(updated_expenses)

    return {
        "message": "Transaction deleted successfully"
    }


# GET: Expense summary
@app.get("/summary")
def get_summary():

    expenses = read_data()

    income = sum(
        item["amount"]
        for item in expenses
        if item["type"] == "Income"
    )

    total_expenses = sum(
        item["amount"]
        for item in expenses
        if item["type"] == "Expense"
    )

    return {
        "total_income": income,
        "total_expenses": total_expenses,
        "balance": income - total_expenses,
        "total_transactions": len(expenses)
    }
