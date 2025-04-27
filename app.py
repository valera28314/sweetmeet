from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Заменить на свой ключ

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

conn = sqlite3.connect('database.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, username TEXT, email TEXT, password TEXT, is_premium INTEGER, photo TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, sender_id INTEGER, receiver_id INTEGER, message TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        photo = request.files['photo']
        photo_filename = secure_filename(photo.filename)
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))
        c.execute("INSERT INTO users (username, email, password, is_premium, photo) VALUES (?, ?, ?, 0, ?)", (username, email, password, photo_filename))
        conn.commit()
        flash('Реєстрація пройшла успішно!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = c.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            session['is_premium'] = user[4]
            return redirect(url_for('dashboard'))
        else:
            flash('Невірні дані для входу', 'danger')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    users = c.execute("SELECT id, username, photo FROM users WHERE id != ?", (session['user_id'],)).fetchall()
    return render_template('dashboard.html', users=users)

@app.route('/message/<int:receiver_id>', methods=['GET', 'POST'])
def message(receiver_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        message = request.form['message']
        c.execute("INSERT INTO messages (sender_id, receiver_id, message) VALUES (?, ?, ?)", (session['user_id'], receiver_id, message))
        conn.commit()
        flash('Повідомлення надіслано!', 'success')
    receiver = c.execute("SELECT username FROM users WHERE id = ?", (receiver_id,)).fetchone()
    messages = c.execute("SELECT * FROM messages WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?) ORDER BY timestamp", (session['user_id'], receiver_id, receiver_id, session['user_id'])).fetchall()
    return render_template('message.html', receiver=receiver, messages=messages)

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
