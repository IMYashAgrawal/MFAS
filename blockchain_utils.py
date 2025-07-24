# blockchain_utils.py

import hashlib
import json
from time import time
import os
import bcrypt # For hashing and checking passwords

BLOCKCHAIN_FILE = 'blockchain.json'

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.load_chain()

    def load_chain(self):
        try:
            if os.path.exists(BLOCKCHAIN_FILE):
                with open(BLOCKCHAIN_FILE, 'r') as f:
                    self.chain = json.load(f)
                print(f"Blockchain data loaded successfully from {BLOCKCHAIN_FILE}.")
            else:
                print("No blockchain file found. Creating a new chain...")
                self.new_block(previous_hash='1', proof=100)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading blockchain file: {e}. Starting fresh.")
            self.new_block(previous_hash='1', proof=100)

    def save_chain(self):
        try:
            with open(BLOCKCHAIN_FILE, 'w') as f:
                json.dump(self.chain, f, indent=4)
            print(f"Blockchain data saved to {BLOCKCHAIN_FILE}.")
        except IOError as e:
            print(f"Could not save blockchain to file: {e}")

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_transactions = []
        self.chain.append(block)
        self.save_chain()
        return block

    # --- MODIFIED: Now accepts hashed_password ---
    def new_transaction(self, user_email_hash, hashed_password, face_data):
        """
        Adds a new registration transaction, including hashed password and face data.
        """
        self.current_transactions.append({
            'event': 'user_registration',
            'user_email_hash': user_email_hash,
            'password_hash': hashed_password.decode('utf-8'), # Store the hashed password as a string
            'face_data_b64': face_data,
            'timestamp': time(),
        })
        # Use last_block's index if chain is not empty, otherwise return 1
        return (self.last_block['index'] + 1) if self.last_block else 1


    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1] if self.chain else None

    def find_transaction(self, user_email_hash):
        """
        Searches the blockchain for a transaction and returns it if found.
        """
        for block in reversed(self.chain):
            for transaction in block['transactions']:
                if transaction['user_email_hash'] == user_email_hash:
                    return transaction
        return None

def hash_email(email):
    return hashlib.sha256(email.encode('utf-8')).hexdigest()
