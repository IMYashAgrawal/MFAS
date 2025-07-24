# app.py

from flask import Flask, request, redirect, url_for, render_template, flash, jsonify, session
import os
import base64
from PIL import Image
import io
import numpy as np
from deepface import DeepFace
import bcrypt

from blockchain_utils import Blockchain, hash_email

app = Flask(__name__)
# A secret key is required for session management
app.secret_key = os.urandom(24)
blockchain = Blockchain()

def load_image_from_b64(b64_string):
    """Decodes a Base64 string and loads it into a numpy array for deepface."""
    # Remove the "data:image/jpeg;base64," header from the string
    img_data = base64.b64decode(b64_string.split(',')[1])
    img = Image.open(io.BytesIO(img_data))
    # Convert image from RGB (Pillow's default) to BGR (deepface's requirement)
    return np.array(img)[:, :, ::-1] 

# --- Application Routes ---

@app.route('/')
def index():
    """Redirects the base URL to the signup page."""
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Handles the first step of registration: collecting user details and password."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            flash("Email and password are required.", "warning")
            return redirect(url_for('signup'))

        user_email_hash = hash_email(email)

        if blockchain.find_transaction(user_email_hash):
            flash("This email has already been registered. Please log in.", "danger")
            return redirect(url_for('login'))

        # Hash the password for secure storage
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Temporarily store the hashes in the session to pass to the next step
        session['pending_email_hash'] = user_email_hash
        session['pending_password_hash'] = hashed_password.decode('utf-8')
        return redirect(url_for('enroll_face'))

    return render_template('signup.html')

@app.route('/enroll_face', methods=['GET'])
def enroll_face():
    """Displays the page for capturing the user's face for the first time."""
    email_hash = session.get('pending_email_hash')
    if not email_hash:
        flash("Session expired. Please start the signup process again.", "warning")
        return redirect(url_for('signup'))
    return render_template('enroll_face.html', email_hash=email_hash)

@app.route('/save_face', methods=['POST'])
def save_face():
    """Receives the captured face data and saves the complete user record to the blockchain."""
    email_hash = session.get('pending_email_hash')
    password_hash = session.get('pending_password_hash')
    face_data = request.form.get('face_data')

    if not email_hash or not password_hash or not face_data:
        flash("Session data is missing. Please try the signup process again.", "danger")
        return redirect(url_for('signup'))

    # Add the complete registration (email, password, face) to the blockchain
    blockchain.new_transaction(
        user_email_hash=email_hash, 
        hashed_password=password_hash.encode('utf-8'), 
        face_data=face_data
    )
    # Mine a new block to confirm the transaction
    blockchain.new_block(proof=12345, previous_hash=blockchain.hash(blockchain.last_block))

    print(f"2FA enrolled for email hash {email_hash} and added to the blockchain.")
    flash("Face enrolled successfully! Please log in with your new credentials.", "success")
    
    # Clear the temporary session data
    session.pop('pending_email_hash', None)
    session.pop('pending_password_hash', None)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Handles the first factor of authentication: email and password."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_email_hash = hash_email(email)
        
        transaction = blockchain.find_transaction(user_email_hash)
        
        # --- STEP 1: Verify Password ---
        if transaction and bcrypt.checkpw(password.encode('utf-8'), transaction['password_hash'].encode('utf-8')):
            # Password is correct, now proceed to face verification
            session['verifying_email_hash'] = user_email_hash
            return redirect(url_for('verify_face'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/verify_face', methods=['GET'])
def verify_face():
    """Displays the page for the second factor of authentication: face verification."""
    email_hash = session.get('verifying_email_hash')
    if not email_hash:
        flash("Session expired. Please start the login process again.", "warning")
        return redirect(url_for('login'))
    return render_template('verify_face.html', email_hash=email_hash)

@app.route('/check_face', methods=['POST'])
def check_face():
    """Compares the live face with the one stored on the blockchain."""
    email_hash = session.get('verifying_email_hash')
    live_face_data_b64 = request.form.get('face_data')

    if not email_hash or not live_face_data_b64:
        flash("Missing data for verification. Please try again.", "danger")
        return redirect(url_for('login'))

    transaction = blockchain.find_transaction(email_hash)
    if not transaction:
        flash("Could not find original registration. Please try again.", "danger")
        return redirect(url_for('login'))

    try:
        # --- STEP 2: Verify Face using deepface ---
        result = DeepFace.verify(
            img1_path = transaction['face_data_b64'], 
            img2_path = live_face_data_b64,
            enforce_detection=False # More lenient if face isn't perfectly clear
        )

        session.pop('verifying_email_hash', None)

        if result['verified']:
            print(f"2FA successful for {email_hash}")
            return redirect(url_for('welcome'))
        else:
            print(f"Face match failed for {email_hash}")
            flash("Face does not match. Please try again.", "danger")
            return redirect(url_for('login'))

    except Exception as e:
        print(f"An error occurred during face comparison: {e}")
        flash(f"Could not verify face. Please try again. Error: {e}", "danger")
        return redirect(url_for('login'))

@app.route('/welcome')
def welcome():
    """The success page after passing both authentication factors."""
    return render_template('welcome.html')

@app.route('/chain')
def get_chain():
    """An endpoint for developers to view the entire blockchain."""
    response = {'chain': blockchain.chain, 'length': len(blockchain.chain)}
    return jsonify(response), 200

if __name__ == '__main__':
    # On first run, deepface will download pre-trained models. This is normal.
    app.run(debug=True, port=5000)
