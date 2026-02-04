from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from datetime import datetime
import sqlite3
import json
import os

app = Flask(__name__)
app.config['DATABASE'] = '/data/viewings.db'

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

def get_db():
    db = sqlite3.connect(app.config['DATABASE'])
    db.row_factory = sqlite3.Row
    return db

def init_db():
    os.makedirs('/data', exist_ok=True)
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS viewings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            address TEXT NOT NULL,
            viewing_time TEXT,
            contact_name TEXT,
            checklist_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    db.commit()
    db.close()

@app.route('/')
def index():
    db = get_db()
    viewings = db.execute('SELECT * FROM viewings ORDER BY created_at DESC').fetchall()
    db.close()
    return render_template('index.html', viewings=viewings)

@app.route('/new')
def new_viewing():
    return render_template('checklist.html')

@app.route('/view/<int:viewing_id>')
def view_viewing(viewing_id):
    db = get_db()
    viewing = db.execute('SELECT * FROM viewings WHERE id = ?', (viewing_id,)).fetchone()
    db.close()
    if viewing:
        checklist_data = json.loads(viewing['checklist_data'])
        return render_template('view_checklist.html', viewing=viewing, checklist_data=checklist_data)
    return redirect(url_for('index'))

@app.route('/edit/<int:viewing_id>')
def edit_viewing(viewing_id):
    db = get_db()
    viewing = db.execute('SELECT * FROM viewings WHERE id = ?', (viewing_id,)).fetchone()
    db.close()
    if viewing:
        checklist_data = json.loads(viewing['checklist_data'])
        return render_template('checklist.html', viewing=viewing, checklist_data=checklist_data)
    return redirect(url_for('index'))

@app.route('/save', methods=['POST'])
def save_viewing():
    data = request.json
    
    db = get_db()
    
    viewing_id = data.get('viewing_id')
    
    if viewing_id:
        # Update existing viewing
        db.execute('''
            UPDATE viewings 
            SET address = ?, viewing_time = ?, contact_name = ?, checklist_data = ?
            WHERE id = ?
        ''', (data['address'], data['viewing_time'], data['contact_name'], 
              json.dumps(data['checklist']), viewing_id))
    else:
        # Create new viewing
        db.execute('''
            INSERT INTO viewings (address, viewing_time, contact_name, checklist_data)
            VALUES (?, ?, ?, ?)
        ''', (data['address'], data['viewing_time'], data['contact_name'], 
              json.dumps(data['checklist'])))
    
    db.commit()
    db.close()
    
    return jsonify({'success': True})

@app.route('/delete/<int:viewing_id>', methods=['POST'])
def delete_viewing(viewing_id):
    db = get_db()
    db.execute('DELETE FROM viewings WHERE id = ?', (viewing_id,))
    db.commit()
    db.close()
    return jsonify({'success': True})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
