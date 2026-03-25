# database.py (Fixed - Proper Connection Management)
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os

def get_db_connection():
    """Get a fresh database connection (Streamlit-safe)"""
    conn = sqlite3.connect('maternalcare.db')
    # Set PRAGMA for better performance and safety
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn

def init_db():
    """Initialize SQLite database with all tables"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if mothers table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mothers';")
    table_exists = c.fetchone()
    
    if not table_exists:
        # Drop and recreate tables to ensure clean state with new schema
        c.execute("DROP TABLE IF EXISTS mothers")
        c.execute("DROP TABLE IF EXISTS vhws")
        c.execute("DROP TABLE IF EXISTS appointments")
        c.execute("DROP TABLE IF EXISTS follow_ups")
        c.execute("DROP TABLE IF EXISTS notifications")
        
        # Enhanced mothers table with real dataset fields
        c.execute('''
            CREATE TABLE mothers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                phone TEXT UNIQUE,
                village TEXT,
                risk_score DECIMAL(3,2) DEFAULT 0.00,
                risk_breakdown TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                assigned_vhw_id INTEGER,
                -- Real dataset fields
                bmi DECIMAL(4,2),
                blood_pressure INTEGER,
                gestational_age INTEGER,
                previous_c_section INTEGER,
                previous_miscarriages INTEGER,
                previous_preterm_birth INTEGER,
                chronic_hypertension INTEGER,
                diabetes INTEGER,
                gestational_diabetes INTEGER,
                preeclampsia_history INTEGER,
                multiple_pregnancy INTEGER,
                smoking INTEGER,
                alcohol_use INTEGER,
                family_history INTEGER,
                hb_level DECIMAL(4,2),
                urine_protein INTEGER,
                blood_glucose INTEGER,
                FOREIGN KEY(assigned_vhw_id) REFERENCES vhws(id)
            )
        ''')
        
        # VHWs table
        c.execute('''
            CREATE TABLE vhws (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                assigned_villages TEXT,
                phone TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Appointments table
        c.execute('''
            CREATE TABLE appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mother_id INTEGER,
                appointment_date DATE NOT NULL,
                appointment_type TEXT CHECK(appointment_type IN ('Antenatal', 'Postnatal')),
                status TEXT DEFAULT 'Scheduled' CHECK(status IN ('Scheduled', 'Attended', 'Missed')),
                reminder_sent BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(mother_id) REFERENCES mothers(id)
            )
        ''')
        
        # Follow-ups table
        c.execute('''
            CREATE TABLE follow_ups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mother_id INTEGER,
                vhw_id INTEGER,
                assigned_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'Completed', 'Failed')),
                notes TEXT,
                FOREIGN KEY(mother_id) REFERENCES mothers(id),
                FOREIGN KEY(vhw_id) REFERENCES vhws(id)
            )
        ''')
        
        # Notifications table
        c.execute('''
            CREATE TABLE notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                message TEXT,
                priority TEXT CHECK(priority IN ('low', 'medium', 'high', 'urgent')),
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                sent_at TIMESTAMP
            )
        ''')
        
        # Insert sample VHWs if not exists
        c.execute("SELECT COUNT(*) FROM vhws")
        vhw_count = c.fetchone()[0]
        if vhw_count == 0:
            sample_vhws = [
                ("John Doe", "Village A, Village B", "+1234567890"),
                ("Jane Smith", "Village C, Village D", "+1234567891"),
                ("Maria Garcia", "Village E, Village F", "+1234567892")
            ]
            c.executemany("INSERT INTO vhws (name, assigned_villages, phone) VALUES (?, ?, ?)", sample_vhws)
        
        conn.commit()
        print("✅ Database initialized with real dataset schema!")
    else:
        print("✅ Database already exists, using existing schema.")
    
    conn.close()
    return conn

if __name__ == "__main__":
    init_db()