import sqlite3
import subprocess
import os
from flask import Flask, request, redirect, render_template, g, session
from datetime import date, datetime

# Check if the database file exists
if not os.path.exists('dentist.db'):
    # Run the database setup script if the file doesn't exist
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

@app.route('/login', methods=['POST'])
def login():
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
            return redirect('/adminIndex.html')
        else:
            return redirect('/appointment') 
    else:
        return "Invalid username or password!", 401


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

        # Convert the selected date to a date object
        selected_date_obj = datetime.strptime(selected_date, "%Y-%m-%d").date()
        today = date.today()

        # Check if the selected date is today or in the past
        if selected_date_obj <= today:
            return "Appointments must be made at least one day in advance. Please choose a future date.", 400

        db = get_db()
        cursor = db.cursor()

        # Check if the time slot on the selected date is already taken
        cursor.execute("SELECT id FROM appointments WHERE date = ? AND time = ?", (selected_date, time))
        existing_appointment = cursor.fetchone()

        if existing_appointment:
            return "This time slot is already booked. Please choose another time.", 400  # Error message
        else:
            cursor.execute("INSERT INTO appointments (user_id, date, time, created_at) VALUES (?, ?, ?, ?)", 
                           (user_id, selected_date, time, created_at))
            db.commit()
            return "Appointment made successfully!"  # Success message

    return render_template('appointment.html')

@app.route('/adminIndex.html')
def admin_index():
    return render_template('adminIndex.html')

@app.route('/futureAppointments.html')
def future_appointments():
    db = get_db()
    cursor = db.cursor()
    
    # Get today's date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch future appointments (date >= today)
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
    
    # Get today's date in YYYY-MM-DD format
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Fetch past appointments (date < today)
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
