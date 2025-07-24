# app.py

# --- 1. Import necessary libraries ---
from flask import Flask, request, redirect, url_for, render_template, flash
import os      # For the secret key

# --- Import our blockchain logic from the new file ---
from blockchain_utils import Blockchain, hash_email


# --- 2. Initialize Flask App and Blockchain ---
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Instantiate our Blockchain from the imported class
blockchain = Blockchain()
print("Blockchain simulation initialized.")


# --- 3. Define Application Routes ---

@app.route('/')
def index():
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password') # Note: Password is not stored

        if not name or not email or not password:
            flash("Please fill out all fields.", "warning")
            return redirect(url_for('signup'))

        user_email_hash = hash_email(email)

        # --- Check if user is already "registered" on the blockchain ---
        if blockchain.find_transaction(user_email_hash):
            flash("This email has already been registered. Please log in.", "danger")
            return redirect(url_for('login'))

        # --- Add the registration event to the blockchain ---
        # 1. Add a transaction
        blockchain.new_transaction(user_email_hash=user_email_hash)
        # 2. "Mine" a new block to confirm the transaction
        previous_hash = blockchain.hash(blockchain.last_block)
        # In a real blockchain, 'proof' comes from a complex mining process. Here we just use a placeholder.
        blockchain.new_block(proof=12345, previous_hash=previous_hash)

        print(f"Registration for email hash {user_email_hash} added to the blockchain.")
        flash("Registration successful! Your registration is now on the blockchain.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password') # Not used for validation here

        if not email or not password:
            flash("Please enter both email and password.", "warning")
            return redirect(url_for('login'))

        user_email_hash = hash_email(email)

        # --- "Login" by checking if the registration exists on the blockchain ---
        if blockchain.find_transaction(user_email_hash):
            print(f"Login successful for email hash: {user_email_hash}")
            return redirect(url_for('welcome'))
        else:
            print(f"Failed login attempt for email hash: {user_email_hash}")
            flash("This email is not registered on the blockchain.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/welcome')
def welcome():
    return render_template('welcome.html')

# --- 4. Run the Flask Application ---
if __name__ == '__main__':
    app.run(debug=True, port=5000)
