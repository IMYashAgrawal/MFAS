from flask import Flask, request, redirect, url_for, render_template, flash, jsonify, session
import os
import base64
from PIL import Image
import io
import numpy as np
from deepface import DeepFace
import bcrypt

from blockchain_utils import Blockchain, hash_email
from crypto_utils import encrypt, decrypt

app = Flask(__name__)
app.secret_key = os.urandom(24)
blockchain = Blockchain()

def load_image_from_b64(b64_string):
    img_data = base64.b64decode(b64_string.split(',')[1])
    img = Image.open(io.BytesIO(img_data))
    return np.array(img)[:, :, ::-1]

@app.route('/')
def index():
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
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

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        session['pending_email_hash'] = user_email_hash
        session['pending_password_hash'] = hashed_password.decode('utf-8')
        return redirect(url_for('enroll_face'))

    return render_template('signup.html')

@app.route('/enroll_face', methods=['GET'])
def enroll_face():
    email_hash = session.get('pending_email_hash')
    if not email_hash:
        flash("Session expired. Please start the signup process again.", "warning")
        return redirect(url_for('signup'))
    return render_template('enroll_face.html', email_hash=email_hash)

@app.route('/save_face', methods=['POST'])
def save_face():
    email_hash = session.get('pending_email_hash')
    password_hash = session.get('pending_password_hash')
    face_data = request.form.get('face_data')

    if not email_hash or not password_hash or not face_data:
        flash("Session data is missing. Please try the signup process again.", "danger")
        return redirect(url_for('signup'))

    encrypted_face_data = encrypt(face_data.encode('utf-8'))

    blockchain.new_transaction(
        user_email_hash=email_hash,
        hashed_password=password_hash.encode('utf-8'),
        encrypted_face_data=encrypted_face_data
    )

    blockchain.new_block(proof=12345, previous_hash=blockchain.hash(blockchain.last_block))

    print(f"2FA enrolled for email hash {email_hash} and added to the blockchain.")
    flash("Face enrolled successfully! Please log in with your new credentials.", "success")
    
    session.pop('pending_email_hash', None)
    session.pop('pending_password_hash', None)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_email_hash = hash_email(email)
        
        transaction = blockchain.find_transaction(user_email_hash)
        
        if transaction and bcrypt.checkpw(password.encode('utf-8'), transaction['password_hash'].encode('utf-8')):
            session['verifying_email_hash'] = user_email_hash
            return redirect(url_for('verify_face'))
        else:
            flash("Invalid email or password.", "danger")
            return redirect(url_for('login'))
            
    return render_template('login.html')

@app.route('/verify_face', methods=['GET'])
def verify_face():
    email_hash = session.get('verifying_email_hash')
    if not email_hash:
        flash("Session expired. Please start the login process again.", "warning")
        return redirect(url_for('login'))
    return render_template('verify_face.html', email_hash=email_hash)

@app.route('/check_face', methods=['POST'])
def check_face():
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
        encrypted_stored_face = transaction['encrypted_face_data']
        decrypted_stored_face_bytes = decrypt(encrypted_stored_face)
        decrypted_stored_face_b64 = decrypted_stored_face_bytes.decode('utf-8')

        result = DeepFace.verify(
            img1_path=decrypted_stored_face_b64,
            img2_path=live_face_data_b64,
            enforce_detection=False
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
    return render_template('welcome.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash("You have been successfully logged out.", "success")
    return redirect(url_for('login'))

@app.route('/chain')
def get_chain():
    response = {'chain': blockchain.chain, 'length': len(blockchain.chain)}
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)
