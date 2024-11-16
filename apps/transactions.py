# transactions.py
from apps.db import get_db_connection
from flask import flash

def add_transaction_to_db(transaction_type, denom_10000, denom_5000, denom_2000, denom_1000, denom_500, denom_coin, transaction_total):
    conn = get_db_connection()
    conn.execute(
        '''INSERT INTO transactions (transaction_type, total_10000, total_5000, total_2000, total_1000, total_500, total_coin, transaction_total)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (transaction_type, denom_10000, denom_5000, denom_2000, denom_1000, denom_500, denom_coin, transaction_total)
    )
    conn.commit()
    conn.close()

def delete_transaction_from_db(transaction_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()

def end_day_process():
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