# blockchain_utils.py

import hashlib
import json
from time import time
import os # Imported to check if the blockchain file exists

# Define a constant for our data file to avoid magic strings
BLOCKCHAIN_FILE = 'blockchain.json'

class Blockchain:
    """
    A simple class to simulate a blockchain for storing registration events.
    This version includes saving and loading the chain to a file for persistence.
    """
    def __init__(self):
        """
        Initializes the blockchain.
        It first tries to load the chain from a file. If no file is found,
        it creates a new chain with a genesis block.
        """
        self.chain = []
        self.current_transactions = []
        self.load_chain()

    def load_chain(self):
        """
        Loads the blockchain data from the JSON file. If the file doesn't exist,
        it creates the genesis block to start a new chain.
        """
        try:
            if os.path.exists(BLOCKCHAIN_FILE):
                with open(BLOCKCHAIN_FILE, 'r') as f:
                    self.chain = json.load(f)
                print(f"Blockchain data loaded successfully from {BLOCKCHAIN_FILE}.")
            else:
                # If no file exists, create the first block (genesis block)
                print("No blockchain file found. Creating a new chain...")
                self.new_block(previous_hash='1', proof=100)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading blockchain file: {e}. Starting fresh.")
            # If file is corrupt or unreadable, start with a genesis block
            self.new_block(previous_hash='1', proof=100)

    def save_chain(self):
        """Saves the current full blockchain to the JSON file."""
        try:
            with open(BLOCKCHAIN_FILE, 'w') as f:
                json.dump(self.chain, f, indent=4)
            print(f"Blockchain data saved to {BLOCKCHAIN_FILE}.")
        except IOError as e:
            print(f"Could not save blockchain to file: {e}")


    def new_block(self, proof, previous_hash=None):
        """
        Creates a new block, adds it to the chain, and then saves the entire chain.
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        
        # --- CRITICAL CHANGE: Save the chain every time a new block is added ---
        self.save_chain()
        
        return block

    def new_transaction(self, user_email_hash):
        """
        Adds a new transaction (a registration event) to the list of transactions.
        """
        self.current_transactions.append({
            'event': 'user_registration',
            'user_email_hash': user_email_hash,
            'timestamp': time(),
        })
        return self.last_block['index'] + 1

    @staticmethod
    def hash(block):
        """Creates a SHA-256 hash of a Block."""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        """Returns the last Block in the chain."""
        return self.chain[-1] if self.chain else None

    def find_transaction(self, user_email_hash):
        """Searches the entire blockchain for a registration transaction."""
        for block in self.chain:
            for transaction in block['transactions']:
                if transaction['user_email_hash'] == user_email_hash:
                    return True
        return False

def hash_email(email):
    """Hashes an email using SHA-256 for privacy."""
    return hashlib.sha256(email.encode('utf-8')).hexdigest()
