from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = '1234'  # Required for flash messages

# Database setup
DATABASE = 'cash_management.db'


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enables dict-like access
    return conn


def init_db():
    with get_db_connection() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            total_10000 INTEGER DEFAULT 0,
            total_5000 INTEGER DEFAULT 0,
            total_2000 INTEGER DEFAULT 0,
            total_1000 INTEGER DEFAULT 0,
            total_500 INTEGER DEFAULT 0,
            total_coin INTEGER DEFAULT 0,
            transaction_total INTEGER NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS history_txn (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_type TEXT NOT NULL,
            total_10000 INTEGER DEFAULT 0,
            total_5000 INTEGER DEFAULT 0,
            total_2000 INTEGER DEFAULT 0,
            total_1000 INTEGER DEFAULT 0,
            total_500 INTEGER DEFAULT 0,
            total_coin INTEGER DEFAULT 0,
            transaction_total INTEGER NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    print("Database initialized!")


@app.route('/')
def index():
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions ORDER BY transaction_date ASC').fetchall()
    conn.close()

    # Calculate sums
    totals = {'10000': 0, '5000': 0, '2000': 0, '1000': 0, '500': 0, 'coin': 0}
    for row in transactions:
        multiplier = -1 if row['transaction_type'] == 'out' else 1
        for denom in totals:
            totals[denom] += multiplier * row[f'total_{denom}']

    # Calculate total_sum
    total_sum = (
        totals['10000'] +
        totals['5000'] +
        totals['2000'] +
        totals['1000'] +
        totals['500'] +
        totals['coin']
    )

    closing_balance = sum(totals.values())

    return render_template('index.html', transactions=transactions, totals=totals, total_sum=total_sum, closing_balance=closing_balance)


@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    transaction_type = request.form['transactionType']
    denom_10000 = int(request.form.get('input-10000', 0))
    denom_5000 = int(request.form.get('input-5000', 0))
    denom_2000 = int(request.form.get('input-2000', 0))
    denom_1000 = int(request.form.get('input-1000', 0))
    denom_500 = int(request.form.get('input-500', 0))
    denom_coin = int(request.form.get('input-coin', 0))
    
    transaction_total = denom_10000 + denom_5000 + denom_2000 + denom_1000 + denom_500 + denom_coin

    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO transactions (transaction_type, total_10000, total_5000, total_2000, total_1000, total_500, total_coin, transaction_total)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (transaction_type, denom_10000, denom_5000, denom_2000, denom_1000, denom_500, denom_coin, transaction_total)
    )
    conn.commit()
    conn.close()
    flash("Transaction added successfully!")
    return redirect(url_for('index'))


@app.route('/end_day', methods=['POST'])
def end_day():
    conn = get_db_connection()
    transactions = conn.execute('SELECT * FROM transactions').fetchall()
    sums = {'10000': 0, '5000': 0, '2000': 0, '1000': 0, '500': 0, 'coin': 0}

    for row in transactions:
        multiplier = -1 if row['transaction_type'] == 'out' else 1
        for denom in sums:
            sums[denom] += multiplier * row[f'total_{denom}']

    current_balance = sum(sums.values())
    conn.execute('''INSERT INTO history_txn (transaction_type, total_10000, total_5000, total_2000, total_1000, total_500, total_coin, transaction_total)
                    SELECT transaction_type, total_10000, total_5000, total_2000, total_1000, total_500, total_coin, transaction_total FROM transactions''')
    conn.execute('DELETE FROM transactions')
    conn.execute('''INSERT INTO transactions (transaction_type, total_10000, total_5000, total_2000, total_1000, total_500, total_coin, transaction_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', ('Opening Balance', sums['10000'], sums['5000'], sums['2000'], sums['1000'], sums['500'], sums['coin'], current_balance))
    conn.commit()
    conn.close()
    flash("End day process completed!")
    return redirect(url_for('index'))


@app.route('/delete_transaction/<int:id>', methods=['POST'])
def delete_transaction(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM transactions WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    flash("Transaction deleted successfully!")
    return redirect(url_for('index'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True)