import sqlite3
import subprocess
import os
from flask import Flask, request, redirect, render_template, g, session, flash, url_for, jsonify
from datetime import date, datetime

# Check if the database file exists
if not os.path.exists('dentist.db'):
    subprocess.run(["python", "setup_db.py"], check=True)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for session management
DATABASE = 'dentist.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # Allows fetching columns by name
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    username = request.form['username']
    password = request.form['password']

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, role FROM users WHERE username = ? AND password = ?", (username, password))
    user = cursor.fetchone()

    if user:
        session['user_id'] = user["id"]
        session['username'] = username
        session['role'] = user["role"]
        if user["role"] == 'admin':
            return jsonify({"success": True, "redirect": "/adminIndex.html"})
        else:
            return jsonify({"success": True, "redirect": "/appointment"})
    else:
        return jsonify({"success": False, "message": "Invalid username or password!"})

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')

    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    phone = request.form['phone']
    role = request.form['role']

    db = get_db()
    cursor = db.cursor()

    # Check if the username already exists
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    existing_user = cursor.fetchone()

    if existing_user:
        return jsonify({"success": False, "message": "Username already exists! Choose a different one."})

    # Insert new user into database
    cursor.execute("INSERT INTO users (username, password, role, email, phone) VALUES (?, ?, ?, ?, ?)",
                   (username, password, role, email, phone))
    db.commit()

    return jsonify({"success": True, "redirect": "/"})  # Redirect to login after successful signup

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        if 'user_id' not in session:
            return redirect('/')

        user_id = session['user_id']
        selected_date = request.form['date']
        time = request.form['time']
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        today = date.today()

        if selected_date_obj <= today:
            flash("Appointments must be made at least one day in advance.", "danger")
            return redirect(url_for('appointment'))

        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id FROM appointments WHERE date = ? AND time = ?", (selected_date, time))
        existing_appointment = cursor.fetchone()

        if existing_appointment:
            flash("This time slot is already booked. Please choose another time.", "danger")
        else:
            cursor.execute("INSERT INTO appointments (user_id, date, time, created_at) VALUES (?, ?, ?, ?)", 
                           (user_id, selected_date, time, created_at))
            db.commit()
            flash("Appointment made successfully!", "success")

    return render_template('appointment.html')

@app.route('/adminIndex.html')
def admin_index():
    return render_template('adminIndex.html')

@app.route('/futureAppointments.html')
def future_appointments():
    db = get_db()
    cursor = db.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT users.username, appointments.date, appointments.time
        FROM appointments 
        JOIN users ON appointments.user_id = users.id
        WHERE date >= ?
        ORDER BY date ASC, time ASC
    """, (today,))
    
    appointments = cursor.fetchall()
    return render_template('futureAppointments.html', appointments=appointments)

@app.route('/pastAppointments.html')
def past_appointments():
    db = get_db()
    cursor = db.cursor()
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT users.username, appointments.date, appointments.time
        FROM appointments 
        JOIN users ON appointments.user_id = users.id
        WHERE date < ?
        ORDER BY date DESC, time ASC
    """, (today,))
    
    appointments = cursor.fetchall()
    return render_template('pastAppointments.html', appointments=appointments)

@app.route('/patientList.html')
def patient_list():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT username, email, phone FROM users WHERE role = 'patient'")
    patients = cursor.fetchall()
    return render_template('patientList.html', patients=patients)

if __name__ == '__main__':
    app.run(debug=True)
