from flask import Flask, jsonify, request, render_template, g
import hashlib  # use hashing function
import json  # convert block dict to str
import sqlite3

app = Flask(__name__)
DATABASE = "blockchain.db"


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


"""impoting hash library"""

reward = 10.0  # reward, stores mining block reward that five miner
# for picking up block

"""
first block in blockchain
1: store hash of prev block, empty str as wont have prev hash
2: index of block in blockchain
3: transaction stored in blockchain
4: Nonce
"""
genesis_block = {
    'previous_hash': '',
    'index': 0,
    'transaction': [],
    'nonce': 23
}

# add gen block to blockchain
blockchain = [genesis_block]
# manages all outstanging trans in blockchain
open_transactions = []
owner = 'Beet'  # we are the owner


# Define functions to interact with the database
def insert_block(previous_hash, block_index, nonce):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO blocks (previous_hash, block_index, nonce)
        VALUES (?, ?, ?)
    ''', (previous_hash, block_index, nonce))
    db.commit()
    return cursor.lastrowid


def insert_transaction(block_id, sender, recipient, amount):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO transactions (block_id, sender, recipient, amount)
        VALUES (?, ?, ?, ?)
    ''', (block_id, sender, recipient, amount))
    db.commit()


def hash_block(block):
    """
    Using hashlib sha256 algo
    json.dumps convert block into json format str
    encode make json format str to UTF-8 str
    """
    poo = hashlib.sha256(json.dumps(block).encode()).hexdigest()
    return poo


def valid_proof(transactions, last_hash, nonce):
    """
    Validate proof of work by check if hash
    of block satisfy condition
    """
    guess = (str(transactions) + str(last_hash) + str(nonce)).encode()
    guess_hash = hashlib.sha256(guess).hexdigest()
    return guess_hash[0:2] == '00'


def pow():
    """
    Perform proof of work by increment nonce until valid
    hash found
    """
    last_block = blockchain[-1]
    last_hash = hash_block(last_block)
    nonce = 0
    while not valid_proof(open_transactions, last_hash, nonce):
        nonce += 1
    return nonce


def get_last_value():
    """ extracting the last element of the blockchain list """
    return blockchain[-1]


def add_value(recipient, sender=owner, amount=1.0):
    """
    add transaction to list of open transaction
    """
    transaction = {'sender': sender,
                   'recipient': recipient,
                   'amount': amount}
    open_transactions.append(transaction)


def mine_block():
    """
    Mine new block by calculating proof of work and add
    to blockchain
    """
    last_block = blockchain[-1]
    hashed_block = hash_block(last_block)
    nonce = pow()
    reward_transaction = {
        'sender': 'MINING',
        'recipient': owner,
        'amount': reward
    }
    open_transactions.append(reward_transaction)
    block = {
        'previous_hash': hashed_block,
        'index': len(blockchain),
        'transaction': open_transactions,
        'nonce': nonce
    }

    blockchain.append(block)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/transactions/new', methods=['GET', 'POST'])
def new_transaction():
    if request.method == 'POST':
        # Process the form data and add the transaction
        values = request.form
        print(values, "Values")
        add_value(values['recipient'], values['sender'], float(values['amount']))
        print(blockchain[-1], "Block")
        insert_transaction(blockchain[-1]["index"], values['sender'], values['recipient'], float(values["amount"]))
        return render_template('transaction_done.html')
    else:
        # Render the form for creating a new transaction
        return render_template('new_transaction.html')


@app.route('/mine')
def mine():
    mine_block()
    insert_block(blockchain[-1]["previous_hash"], blockchain[-1]["index"], blockchain[-1]["nonce"])
    response = {
        'message': "New Block Forged",
        'block': blockchain[-1]
    }
    print(blockchain[-1])
    return jsonify(response), 200


@app.route('/chain')
def full_chain():
    response = {
        'chain': blockchain,
        'length': len(blockchain)
    }
    return jsonify(response), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
