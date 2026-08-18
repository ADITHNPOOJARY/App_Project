from models import init_db
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import date

app = Flask(__name__)
app.secret_key = "your_secret_key_here"


def get_db_connection():
    conn = sqlite3.connect("trekking.db", timeout=10)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form.get("firstname")
        last_name = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")
            
        conn = get_db_connection()
        try:
            if  role == "staff":
                conn.execute('''
                    INSERT INTO staff (first_name, last_name, email, password)
                    VALUES (?, ?, ?, ?)
                ''', (first_name, last_name, email, password))
            else:
                conn.execute('''
                    INSERT INTO users (first_name, last_name, email, password)
                    VALUES (?, ?, ?, ?)
                ''', (first_name, last_name, email, password))
            conn.commit()
            return redirect(url_for('signin'))
            
        except sqlite3.IntegrityError:
            return render_template('signup.html', error="Email already exists!")
            
        finally:
            conn.close()

    return render_template('signup.html')

@app.route('/signin', methods=['GET', 'POST'])
def signin():
    error = None 

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        conn = get_db_connection()
        user = conn.execute(
            'SELECT * FROM users WHERE email = ? AND password = ?', 
            (email, password)
        ).fetchone()
        
        if user:
            print(f"SUCCESS: User '{user['first_name']}' logged in!")
            session['user_id'] = user['user_id']
            session['first_name'] = user['first_name']
            session['role'] = 'user'
            conn.close()
            
            return redirect(url_for('user_dashboard'))
            
        staff = conn.execute(
            'SELECT * FROM staff WHERE email = ? AND password = ?', 
            (email, password)
        ).fetchone()
        
        conn.close()

        if staff:
            if staff['status'] == 'Approved':
                session['staff_id'] = staff['id']
                session['first_name'] = staff['first_name']
                session['role'] = 'staff'
                return redirect(url_for('staff_dashboard'))
            else:
                error = f"Login failed. Your staff account status is currently: {staff['status']}."
                
        else:
            error = "Invalid email or password. Please try again."

    return render_template('signin.html', error=error)

@app.route('/admin/dashboard')
def admin_dashboard():
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM staff WHERE status = 'Approved'")
    total_staff = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM treks")
    total_treks = cursor.fetchone()[0]
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                           total_users=total_users,
                           total_staff=total_staff,
                           total_bookings=total_bookings,
                           total_treks=total_treks)


@app.route('/admin/treks', methods=['GET'])
def treks():
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 
            t.id, t.trek_name, t.location, t.duration_days, 
            t.available_slots, t.start_date, t.end_date,
            GROUP_CONCAT(s.id) as staff_ids
        FROM treks t
        LEFT JOIN staff s ON t.id = s.assigned_trek_id
        GROUP BY t.id
        ORDER BY t.id DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    all_treks = []
    for row in rows:
        trek_data = list(row)
        staff_ids_raw = trek_data[7]
        
        if staff_ids_raw:
            formatted_staff = ", ".join([f"S{int(sid):03d}" for sid in str(staff_ids_raw).split(',')])
            trek_data[7] = formatted_staff
        else:
            trek_data[7] = "Unassigned"
            
        all_treks.append(trek_data)
    
    return render_template('treks.html', treks=all_treks)

@app.route('/admin/add_trek', methods=['POST'])
def add_trek():
    trek_name = request.form['trek_name']
    location = request.form['location']
    duration = request.form['duration']
    slots = request.form['slots']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    description = request.form['description']

    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO treks (trek_name, location, duration_days, available_slots, start_date, end_date, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (trek_name, location, duration, slots, start_date, end_date, description))
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('treks'))

@app.route('/admin/staff')
def staff():
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()

    today = date.today().strftime('%Y-%m-%d')
    
    cursor.execute('''
        UPDATE staff 
        SET is_available = 1, assigned_trek_id = NULL 
        WHERE assigned_trek_id IN (
            SELECT id FROM treks WHERE end_date < ?
        )
    ''', (today,))
    conn.commit()
    cursor.execute("SELECT id, first_name, last_name, email, status FROM staff WHERE status = 'Pending'")
    pending_staff = cursor.fetchall()

    cursor.execute("SELECT id, first_name, last_name, email, status, is_available FROM staff WHERE status = 'Approved'")
    approved_staff = cursor.fetchall()

    cursor.execute("SELECT id, first_name, last_name, email, status FROM staff WHERE status = 'Blacklist'")
    blacklisted_staff = cursor.fetchall()

    cursor.execute("SELECT id, trek_name, start_date, end_date FROM treks WHERE end_date >= ?", (today,))
    treks = cursor.fetchall()

    conn.close()

    return render_template('staff.html', 
                           pending_staff=pending_staff, 
                           approved_staff=approved_staff, 
                           blacklisted_staff=blacklisted_staff,
                           treks=treks)


@app.route('/admin/staff/action/<int:staff_id>/<action>', methods=['POST'])
def staff_action(staff_id, action):
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()

    if action == 'approve':
        cursor.execute("UPDATE staff SET status = 'Approved', is_available = 1 WHERE id = ?", (staff_id,))
    elif action == 'reject':
        cursor.execute("UPDATE staff SET status = 'Blacklist' WHERE id = ?", (staff_id,))

    conn.commit()
    conn.close()
    return redirect(url_for('staff'))


@app.route('/admin/staff/assign', methods=['POST'])
def assign_staff():
    staff_email = request.form.get('staff_email')
    trek_id = request.form.get('trek_id')
    
    print(f"Trying to assign: Email={staff_email}, TrekID={trek_id}") 

    if staff_email and trek_id:
        conn = sqlite3.connect('trekking.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE staff 
            SET is_available = 0, assigned_trek_id = ? 
            WHERE email = ?
        ''', (trek_id, staff_email))
        
        conn.commit()
        print("Database updated successfully!") 
        conn.close()
    else:
        print("Missing email or trek_id!") 

    return redirect(url_for('staff'))


@app.route('/admin/users')
def users():
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            u.user_id, 
            u.first_name, 
            u.last_name, 
            u.email, 
            COUNT(b.booking_id) as total_bookings,
            GROUP_CONCAT(t.trek_name, ', ') as booked_treks
        FROM users u
        LEFT JOIN bookings b ON u.user_id = b.user_id
        LEFT JOIN treks t ON b.trek_id = t.id
        GROUP BY u.user_id
        ORDER BY total_bookings DESC, u.user_id ASC
    ''')
    all_users = cursor.fetchall()
    
    conn.close()
    
    return render_template('users.html', users=all_users)



@app.route('/staff/dashboard')
def staff_dashboard():
    if 'staff_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('signin'))

    staff_id = session['staff_id']
    staff_name = session['first_name']

    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()

    cursor.execute('SELECT assigned_trek_id FROM staff WHERE id = ?', (staff_id,))
    staff_record = cursor.fetchone()

    assigned_treks = []
    
    if staff_record and staff_record[0]:
        trek_id = staff_record[0]
        
        cursor.execute('''
            SELECT id, trek_name, location, available_slots, end_date
            FROM treks WHERE id = ?
        ''', (trek_id,))
        trek = cursor.fetchone()
        
        if trek:
            cursor.execute('SELECT COUNT(*) FROM bookings WHERE trek_id = ?', (trek_id,))
            participants_count = cursor.fetchone()[0]
            
            today = date.today().strftime('%Y-%m-%d')
            status = "Open" if trek[4] >= today else "Closed"
            
            assigned_treks.append({
                'id': trek[0],
                'name': trek[1],
                'location': trek[2],
                'participants': participants_count,
                'slots': trek[3],
                'status': status
            })

    conn.close()

    return render_template('staff_dashboard.html', 
                           staff_name=staff_name, 
                           assigned_treks=assigned_treks)
    
    

@app.route('/staff/manage/<int:trek_id>')
def staff_manage_trek(trek_id):
    if 'staff_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('signin'))

    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, trek_name, location, duration_days, start_date, end_date, available_slots, description
        FROM treks
        WHERE id = ?
    ''', (trek_id,))
    trek = cursor.fetchone()

    cursor.execute('''
        SELECT u.user_id, u.first_name, u.last_name, u.email 
        FROM users u
        JOIN bookings b ON u.user_id = b.user_id
        WHERE b.trek_id = ?
    ''', (trek_id,))
    booked_users = cursor.fetchall()

    conn.close()

    if not trek:
        return redirect(url_for('staff_dashboard'))

    return render_template('staff_manage_trek.html', trek=trek, booked_users=booked_users)

@app.route('/staff/profile', methods=['GET', 'POST'])
def staff_profile():
    if 'staff_id' not in session or session.get('role') != 'staff':
        return redirect(url_for('signin'))
    
    staff_id = session['staff_id']
    conn = sqlite3.connect('trekking.db')
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        cursor.execute('''
            UPDATE staff 
            SET first_name = ?, last_name = ?, email = ?, password = ? 
            WHERE id = ?
        ''', (first_name, last_name, email, password, staff_id))
        
        conn.commit()
        
        session['first_name'] = first_name 
    
    staff_data = cursor.execute('SELECT * FROM staff WHERE id = ?', (staff_id,)).fetchone()
    conn.close()
    
    return render_template('staff_profile.html', staff=staff_data)

@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user_id']
    user_name = session['first_name']
    
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()
    
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT id, trek_name, location, duration_days, available_slots, start_date, end_date 
        FROM treks 
        WHERE end_date >= ? AND available_slots > 0
    ''', (today,))
    available_treks = cursor.fetchall()

    cursor.execute('''
        SELECT t.id, t.trek_name, b.booking_date, b.status 
        FROM bookings b
        JOIN treks t ON b.trek_id = t.id
        WHERE b.user_id = ?
        ORDER BY b.booking_id DESC
    ''', (user_id,))
    my_bookings = cursor.fetchall()
    
    conn.close()

    return render_template('user_dashboard.html', 
                           user_name=user_name, 
                           available_treks=available_treks,
                           my_bookings=my_bookings)
    
@app.route('/user/book_trek', methods=['POST'])
def book_trek():
    if 'user_id' not in session:
        return redirect(url_for('signin'))

    trek_id = request.form.get('trek_id')
    user_id = session['user_id']
    
    today = date.today().strftime('%Y-%m-%d')

    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO bookings (user_id, trek_id, booking_date)
        VALUES (?, ?, ?)
    ''', (user_id, trek_id, today))

    cursor.execute('''
        UPDATE treks 
        SET available_slots = available_slots - 1 
        WHERE id = ? AND available_slots > 0
    ''', (trek_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('user_dashboard'))

@app.route('/user/browse')
@app.route('/user/browse/<int:index>')
def browse_treks(index=0):
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()
    
    today = date.today().strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT id, trek_name, location, duration_days, start_date, end_date, available_slots, description
        FROM treks 
        WHERE end_date >= ? AND available_slots > 0
        ORDER BY start_date ASC
    ''', (today,))
    
    all_treks = cursor.fetchall()
    
    if not all_treks:
        conn.close()
        return render_template('user_browse_treks.html', trek=None)
        
    if index >= len(all_treks):
        index = 0
        
    current_trek = all_treks[index]
    
    has_next = (index < len(all_treks) - 1)
    next_index = index + 1
    
    cursor.execute('''
        SELECT id, first_name, last_name, email 
        FROM staff 
        WHERE assigned_trek_id = ?
    ''', (current_trek[0],))
    assigned_staff = cursor.fetchall()
    
    conn.close()
    
    return render_template('user_browse_treks.html', 
                           trek=current_trek, 
                           staff_list=assigned_staff, 
                           has_next=has_next, 
                           next_index=next_index)

@app.route('/user/history')
def user_history():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user_id']
    
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT t.trek_name, t.location, t.duration_days, b.booking_date, t.start_date, t.end_date, b.status
        FROM bookings b
        JOIN treks t ON b.trek_id = t.id
        WHERE b.user_id = ?
        ORDER BY b.booking_id DESC
    ''', (user_id,))
    
    history_data = cursor.fetchall()
    conn.close()
    
    return render_template('user_history.html', history=history_data)


@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    if 'user_id' not in session:
        return redirect(url_for('signin'))
    
    user_id = session['user_id']
    conn = sqlite3.connect('trekking.db')
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()
    
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        cursor.execute('''
            UPDATE users 
            SET first_name = ?, last_name = ?, email = ?, password = ? 
            WHERE user_id = ?
        ''', (first_name, last_name, email, password, user_id))
        
        conn.commit()
        
        session['first_name'] = first_name 
    
    user_data = cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,)).fetchone()
    conn.close()
    
    return render_template('user_profile.html', user=user_data)


if __name__ == '__main__':
    init_db()
    app.run(debug=True)