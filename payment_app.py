import pandas as pd
import matplotlib.pyplot as plt
from flask import Flask, request, jsonify, send_file
from datetime import datetime
import io

app = Flask(__name__)

# Class representing a user account with authentication
class User:
    def __init__(self, account_name, password, balance=0):
        self.account_name = account_name
        self.password = password
        self.balance = balance

    # Method to add money to the account
    def deposit(self, amount):
        self.balance += amount

    # Method to withdraw money from the account
    def withdraw(self, amount):
        if amount > self.balance:
            return False
        self.balance -= amount
        return True

# Payment handling system
class Payments:
    def __init__(self):
        self.accounts = {}  # Store user accounts
        self.transactions = []  # Store all transactions

    # Method to authenticate users
    def authenticate(self, account_name, password):
        return account_name in self.accounts and self.accounts[account_name].password == password

    # Create a new account
    def create_account(self, account_name, password, initial_deposit):
        if account_name in self.accounts:
            return {"message": "Account already exists"}, 400

        # Create new account and log the transaction
        new_account = User(account_name, password, initial_deposit)
        self.accounts[account_name] = new_account
        self.log_transaction('create_account', account_name, None, initial_deposit)
        return {"message": f"Account {account_name} created with Rs {initial_deposit}"}, 201

    # Method to handle payments between accounts
    def make_payment(self, sender, password, receiver, amount):
        if not self.authenticate(sender, password):
            return {"message": "Invalid login"}, 401

        if receiver not in self.accounts:
            return {"message": "Receiver account doesn't exist"}, 404

        # Process payment and log the transaction
        if self.accounts[sender].withdraw(amount):
            self.accounts[receiver].deposit(amount)
            self.log_transaction('payment', sender, receiver, amount)
            return {"message": f"Rs {amount} sent from {sender} to {receiver}"}, 200
        return {"message": "Insufficient funds"}, 400

    # Method to check balance after authentication
    def check_balance(self, account_name, password):
        if self.authenticate(account_name, password):
            balance = self.accounts[account_name].balance
            self.log_transaction('check_balance', account_name, None, None)
            return {"account": account_name, "balance": balance}, 200
        return {"message": "Invalid login"}, 401

    # Internal method to log transactions
    def log_transaction(self, transaction_type, sender, receiver, amount):
        transaction = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'transaction_type': transaction_type,
            'sender': sender,
            'receiver': receiver,
            'amount': amount
        }
        self.transactions.append(transaction)

    # Convert transaction logs into a Pandas DataFrame
    def get_transactions_df(self):
        return pd.DataFrame(self.transactions)

    # Analyze and summarize transactions by user
    def analyze_transactions(self):
        df = self.get_transactions_df()
        if df.empty:
            return {"message": "No transactions found"}, 200

        summary = df.groupby('sender')['amount'].sum().reset_index()
        return summary.to_dict(orient='records')

    # Generate a bar chart of total transactions for each user
    def transaction_chart(self):
        df = self.get_transactions_df()
        if df.empty:
            return None

        summary = df.groupby('sender')['amount'].sum().sort_values(ascending=False)
        plt.figure(figsize=(10, 6))
        summary.plot(kind='bar', color='lightblue')
        plt.title('Total Transactions by User')
        plt.xlabel('User')
        plt.ylabel('Total Amount (Rs)')
        plt.xticks(rotation=45)
        plt.tight_layout()

        img = io.BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        return img


# Instantiate the Payments system
payment_system = Payments()

# Create account API route
@app.route('/create_account', methods=['POST'])
def create_account():
    data = request.json
    return payment_system.create_account(data['account_name'], data['password'], data['initial_deposit'])

# Make a payment API route
@app.route('/make_payment', methods=['POST'])
def make_payment():
    data = request.json
    return payment_system.make_payment(data['sender'], data['password'], data['receiver'], data['amount'])

# Check balance API route
@app.route('/check_balance', methods=['POST'])
def check_balance():
    data = request.json
    return payment_system.check_balance(data['account_name'], data['password'])

# Analyze transactions API route
@app.route('/analyze_transactions', methods=['GET'])
def analyze_transactions():
    analysis = payment_system.analyze_transactions()
    return jsonify(analysis)

# Generate transaction visualization API route
@app.route('/transaction_chart', methods=['GET'])
def transaction_chart():
    img = payment_system.transaction_chart()
    if img:
        return send_file(img, mimetype='image/png')
    return {"message": "No transactions to visualize"}, 200

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)

       





