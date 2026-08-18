import sqlite3

def init_db():
    conn = sqlite3.connect('trekking.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Approved', 'Blacklist')),
            is_available INTEGER DEFAULT 1,
            assigned_trek_id INTEGER DEFAULT NULL,
            FOREIGN KEY (assigned_trek_id) REFERENCES treks(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            booked_trek_id INTEGER,
            FOREIGN KEY (booked_trek_id) REFERENCES treks(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trek_name TEXT NOT NULL,
            location TEXT NOT NULL,
            duration_days INTEGER NOT NULL,
            available_slots INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            description TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            trek_id INTEGER NOT NULL,
            booking_date TEXT NOT NULL,
            status TEXT DEFAULT 'Booked',
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (trek_id) REFERENCES treks(id)
        )
    ''')
    
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()