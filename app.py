from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from apps.transactions import add_transaction_to_db, delete_transaction_from_db, end_day_process

DATABASE = 'cash_management.db'
USERS = 'users.db'

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flash messages

# Database connection helper functions
def get_db_connection():
    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row  # Enables dict-like access
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        return None

def get_user_db_connection():
    try:
        conn = sqlite3.connect(USERS)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        print(f"User database connection error: {e}")
        return None

# Initialize db
def init_db():
    try:
        # Initialize cash management database
        with get_db_connection() as conn:
            if conn:
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

        # Initialize users database
        with get_user_db_connection() as conn:
            if conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )''')
    except sqlite3.Error as e:
        print(f"Error during database initialization: {e}")

# Initialize the database on application startup
init_db()

@app.route('/')
def index():
    conn = get_db_connection()
    if not conn:
        flash("Database connection failed.", "danger")
        return render_template('error.html')

    transactions = conn.execute('SELECT * FROM transactions ORDER BY transaction_date ASC').fetchall()
    conn.close()

    # Calculate sums for each denomination
    totals = {'10000': 0, '5000': 0, '2000': 0, '1000': 0, '500': 0, 'coin': 0}
    for row in transactions:
        multiplier = -1 if row['transaction_type'] == 'out' else 1
        for denom in totals:
            totals[denom] += multiplier * row[f'total_{denom}']

    total_sum = sum(totals.values())
    closing_balance = total_sum

    return render_template('index.html', transactions=transactions, totals=totals, total_sum=total_sum, closing_balance=closing_balance)

# Other routes remain unchanged...

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if login_user(username, password):
            session['username'] = username  # Store the username in the session
            return redirect(url_for('index'))  # Redirect to index after successful login
        else:
            flash("Invalid username or password", "danger")

    return render_template('login_register.html', action='login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        if password != password_confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for('register'))

        if register_user(username, password):
            flash("Registration successful, please log in.", "success")
            return redirect(url_for('login'))
        else:
            flash("Username already taken", "danger")
            return redirect(url_for('register'))

    return render_template('login_register.html', action='register')

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None)  # Remove the user from the session
    flash("You have been logged out", "success")
    return redirect(url_for('login'))  # Redirect to the login page after logout

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

    add_transaction_to_db(transaction_type, denom_10000, denom_5000, denom_2000, denom_1000, denom_500, denom_coin, transaction_total)
    
    flash("Transaction added successfully!")
    return redirect(url_for('index'))  # Redirect to index after adding transaction

@app.route('/end_day', methods=['POST'])
def end_day():
    end_day_process()
    flash("End day process completed!")
    return redirect(url_for('index'))  # Redirect to index after end day process

@app.route('/delete_transaction/<int:id>', methods=['POST'])
def delete_transaction(id):
    delete_transaction_from_db(id)
    flash("Transaction deleted successfully!")
    return redirect(url_for('index'))  # Redirect to index after deleting transaction

# User-related functions for login and registration
def login_user(username, password):
    conn = get_user_db_connection()  # Corrected from get_db() to get_user_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return True
    return False

def register_user(username, password):
    conn = get_user_db_connection()  # Corrected from get_db() to get_user_db_connection()

    # Check if the username already exists
    if conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone():
        conn.close()
        return False

    hashed_password = generate_password_hash(password)
    conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
    conn.commit()
    conn.close()
    return True

# Custom filter to format numbers
def format_number(value):
    """Format numbers with commas and two decimal places."""
    if value is not None:
        return "{:,.2f}".format(value)  # Format as float with comma as thousand separator and 2 decimal places
    return value

# Register the custom filter
app.jinja_env.filters['format_number'] = format_number
if __name__ == '__main__':
    app.run(debug=True)