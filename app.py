# app.py

# --- 1. Import necessary libraries ---
from flask import Flask, request, redirect, url_for, render_template, flash
import mysql.connector
import bcrypt
import os # Used to generate a secret key for session security

# --- 2. Initialize the Flask Application ---
app = Flask(__name__)
# A secret key is required to use flash messages for showing alerts to the user.
app.secret_key = os.urandom(24)

# --- 3. Database Configuration ---
# This block attempts to connect to your MySQL database.
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root", # IMPORTANT: Change this to your actual MySQL password
        database="MFAS"
    )
    db_cursor = db.cursor(dictionary=True) # dictionary=True lets us access results by column name
    print("Database connection successful.")
except mysql.connector.Error as err:
    print(f"Database Connection Error: {err}")
    # If connection fails, the app can't work, so we'll show an error on the pages.
    db = None
    db_cursor = None

# --- 4. Define Application Routes (The URLs of your website) ---

@app.route('/')
def index():
    """The default page, redirects to the signup page."""
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handles both displaying the signup page (GET) and processing the form (POST)."""
    if request.method == 'POST':
        # Check if the database connection is working
        if not db:
            flash("Database is not connected. Please check the server configuration.", "danger")
            return render_template('signup.html'), 503 # Service Unavailable

        # Get data from the submitted form
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')

        # --- Simple Validation ---
        if not name or not email or not password:
            flash("Please fill out all fields.", "warning")
            return redirect(url_for('signup'))

        try:
            # --- Check if a user with that email already exists ---
            db_cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
            if db_cursor.fetchone():
                flash("An account with this email already exists. Please log in.", "danger")
                return redirect(url_for('login'))

            # --- Hash the password for security ---
            # We encode the password to bytes before hashing
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

            # --- Insert the new user into the database ---
            insert_query = "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)"
            db_cursor.execute(insert_query, (name, email, hashed_password))
            db.commit() # Save the changes to the database

            print(f"User registered successfully: {email}")
            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for('login'))

        except mysql.connector.Error as err:
            print(f"Database Error during signup: {err}")
            flash("A database error occurred. Please try again later.", "danger")
            return redirect(url_for('signup'))

    # If the request method is GET, just show the signup page
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles both displaying the login page (GET) and processing the form (POST)."""
    if request.method == 'POST':
        if not db:
            flash("Database is not connected. Please check the server configuration.", "danger")
            return render_template('login.html'), 503

        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Please enter both email and password.", "warning")
            return redirect(url_for('login'))

        try:
            # --- Find the user by email ---
            db_cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = db_cursor.fetchone()

            # --- Check if user exists and if the password is correct ---
            # We compare the submitted password with the hashed password from the database
            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                print(f"Login successful for user: {email}")
                # If login is successful, redirect to the welcome page
                return redirect(url_for('welcome'))
            else:
                # If user not found or password incorrect
                print(f"Failed login attempt for user: {email}")
                flash("Invalid email or password. Please try again.", "danger")
                return redirect(url_for('login'))

        except mysql.connector.Error as err:
            print(f"Database Error during login: {err}")
            flash("A database error occurred. Please try again later.", "danger")
            return redirect(url_for('login'))

    # If the request method is GET, just show the login page
    return render_template('login.html')


@app.route('/welcome')
def welcome():
    """Displays the 'Access Granted' page."""
    return render_template('welcome.html')


# --- 5. Run the Flask Application ---
# This block makes the server run when you execute the script directly.
if __name__ == '__main__':
    # debug=True allows the server to auto-reload when you save changes to the file.
    # port=5000 specifies which port to run on.
    app.run(debug=True, port=5000)
