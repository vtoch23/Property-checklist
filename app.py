from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory, session
from datetime import datetime
from functools import wraps
import sqlite3
import json
import os
import hashlib

app = Flask(__name__)
app.config['DATABASE'] = '/data/viewings.db'
app.secret_key = os.environ.get('SECRET_KEY')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.template_filter('from_json')
def from_json_filter(s):
    return json.loads(s) if s else {}

@app.template_filter('format_datetime')
def format_datetime_filter(s):
    if not s:
        return ''
    try:
        dt = datetime.fromisoformat(s.replace('Z', '+00:00'))
        return dt.strftime('%d %b %Y, %H:%M')
    except:
        return s

def login_required(f):
    @wraps(f)
    def authenticate_user(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return authenticate_user

def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    os.makedirs('/data', exist_ok=True)
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.execute('''
        CREATE TABLE IF NOT EXISTS viewings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            address TEXT NOT NULL,
            viewing_time TEXT,
            contact_name TEXT,
            photo TEXT,
            checklist_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    # Migration: add user_id if missing
    try:
        db.execute('SELECT user_id FROM viewings LIMIT 1')
    except sqlite3.OperationalError:
        db.execute('ALTER TABLE viewings ADD COLUMN user_id INTEGER DEFAULT 1')
    # Migration: add photo if missing
    try:
        db.execute('SELECT photo FROM viewings LIMIT 1')
    except sqlite3.OperationalError:
        db.execute('ALTER TABLE viewings ADD COLUMN photo TEXT')
    db.commit()
    db.close()

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = hashlib.sha256(request.form['new_password'].encode()).hexdigest()
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user:
            db.execute('UPDATE users SET password = ? WHERE email = ?', (new_password, email))
            db.commit()
            db.close()
            return redirect(url_for('login'))
        db.close()
        return render_template('reset_password.html', error='Email not found')
    return render_template('reset_password.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        db = get_db()
        try:
            db.execute('INSERT INTO users (email, password) VALUES (?, ?)', (email, password))
            db.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error='Email already exists')
        finally:
            db.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = hashlib.sha256(request.form['password'].encode()).hexdigest()
        
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ? AND password = ?', (email, password)).fetchone()
        db.close()
        
        if user:
            session['user_id'] = user['id']
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    db = get_db()
    viewings = db.execute('SELECT * FROM viewings WHERE user_id = ? ORDER BY viewing_time DESC', (session['user_id'],)).fetchall()
    db.close()
    return render_template('index.html', viewings=viewings)

@app.route('/new')
@login_required
def new_viewing():
    return render_template('checklist.html')

@app.route('/view/<int:viewing_id>')
@login_required
def view_viewing(viewing_id):
    db = get_db()
    viewing = db.execute('SELECT * FROM viewings WHERE id = ? AND user_id = ?', (viewing_id, session['user_id'])).fetchone()
    db.close()
    if viewing:
        checklist_data = json.loads(viewing['checklist_data'])
        return render_template('view_checklist.html', viewing=viewing, checklist_data=checklist_data)
    return redirect(url_for('index'))

@app.route('/edit/<int:viewing_id>')
@login_required
def edit_viewing(viewing_id):
    db = get_db()
    viewing = db.execute('SELECT * FROM viewings WHERE id = ? AND user_id = ?', (viewing_id, session['user_id'])).fetchone()
    db.close()
    if viewing:
        checklist_data = json.loads(viewing['checklist_data'])
        return render_template('checklist.html', viewing=viewing, checklist_data=checklist_data)
    return redirect(url_for('index'))

@app.route('/save', methods=['POST'])
@login_required
def save_viewing():
    data = request.json
    db = get_db()
    viewing_id = data.get('viewing_id')
    
    if viewing_id:
        db.execute('''
            UPDATE viewings 
            SET address = ?, viewing_time = ?, contact_name = ?, photo = ?, checklist_data = ?
            WHERE id = ? AND user_id = ?
        ''', (data['address'], data['viewing_time'], data['contact_name'], data.get('photo'),
              json.dumps(data['checklist']), viewing_id, session['user_id']))
    else:
        db.execute('''
            INSERT INTO viewings (user_id, address, viewing_time, contact_name, photo, checklist_data)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (session['user_id'], data['address'], data['viewing_time'], data['contact_name'], 
              data.get('photo'), json.dumps(data['checklist'])))
    
    db.commit()
    db.close()
    return jsonify({'success': True})

@app.route('/delete/<int:viewing_id>', methods=['POST'])
@login_required
def delete_viewing(viewing_id):
    db = get_db()
    db.execute('DELETE FROM viewings WHERE id = ? AND user_id = ?', (viewing_id, session['user_id']))
    db.commit()
    db.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
