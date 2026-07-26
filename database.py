"""
Database Module for Scholarship Tracker
Handles SQLite connection, schema creation, csv dataset seeding, and CRUD operations with validation.
"""

import os
import sqlite3
import pandas as pd

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scholarship.db')
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dataset', 'scholarship_data.csv')

VALID_STAGES = [
    'Application Submitted',
    'Institute Verification',
    'District Verification',
    'Sanctioned',
    'Disbursed',
    'Rejected'
]

VALID_DOC_STATUSES = [
    'Verified',
    'Pending',
    'Rejected',
    'Under Resubmission'
]

def get_db_connection():
    """Returns a SQLite connection with Row factory enabled."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Creates tables if not present and seeds initial data from dataset/scholarship_data.csv if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id TEXT UNIQUE NOT NULL,
            student_id TEXT NOT NULL,
            student_name TEXT NOT NULL,
            scheme TEXT NOT NULL,
            applied_date TEXT NOT NULL,
            documents_status TEXT NOT NULL,
            stage TEXT NOT NULL,
            sanctioned_amount REAL NOT NULL DEFAULT 0.0,
            disbursed_date TEXT,
            outcome TEXT NOT NULL
        )
    ''')
    conn.commit()

    # Check if table is empty
    cursor.execute('SELECT COUNT(*) as count FROM applications')
    row_count = cursor.fetchone()['count']

    if row_count == 0 and os.path.exists(CSV_FILE):
        print(f"[DB] Seeding database from {CSV_FILE}...")
        df = pd.read_csv(CSV_FILE)
        for _, row in df.iterrows():
            doc_status = str(row['documents_status']) if pd.notna(row['documents_status']) else 'Pending'
            disbursed = str(row['disbursed_date']) if pd.notna(row['disbursed_date']) else ''
            amount = float(row['sanctioned_amount']) if pd.notna(row['sanctioned_amount']) and row['sanctioned_amount'] >= 0 else 0.0
            
            try:
                cursor.execute('''
                    INSERT INTO applications (
                        application_id, student_id, student_name, scheme,
                        applied_date, documents_status, stage, sanctioned_amount,
                        disbursed_date, outcome
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(row['application_id']).strip(),
                    str(row['student_id']).strip(),
                    str(row['student_name']).strip(),
                    str(row['scheme']).strip(),
                    str(row['applied_date']).strip(),
                    doc_status.strip(),
                    str(row['stage']).strip(),
                    amount,
                    disbursed.strip(),
                    str(row['outcome']).strip()
                ))
            except sqlite3.IntegrityError:
                pass
        conn.commit()
        print("[DB] Initial database seeding completed.")
    conn.close()

def validate_application_payload(data, is_update=False):
    """Validates application fields and returns (is_valid, error_message)."""
    if not is_update or 'application_id' in data:
        app_id = data.get('application_id')
        if not app_id or not str(app_id).strip():
            return False, "Application ID is required"

    if not is_update or 'student_name' in data:
        name = data.get('student_name')
        if not name or not str(name).strip():
            return False, "Student Name is required"

    if 'sanctioned_amount' in data:
        try:
            amt = float(data.get('sanctioned_amount', 0))
            if amt < 0:
                return False, "Sanctioned amount cannot be negative"
        except (ValueError, TypeError):
            return False, "Sanctioned amount must be a valid number"

    if 'stage' in data:
        stage = data.get('stage')
        if stage not in VALID_STAGES:
            return False, f"Stage must be one of: {', '.join(VALID_STAGES)}"

    if 'documents_status' in data:
        doc_status = data.get('documents_status')
        if doc_status not in VALID_DOC_STATUSES:
            return False, f"Document Status must be one of: {', '.join(VALID_DOC_STATUSES)}"

    return True, None

def get_applications(search=None, stage=None, documents_status=None):
    """Fetches applications with optional search and filter criteria."""
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM applications WHERE 1=1"
    params = []

    if search:
        search_pattern = f"%{search.strip()}%"
        query += " AND (student_name LIKE ? OR application_id LIKE ? OR student_id LIKE ?)"
        params.extend([search_pattern, search_pattern, search_pattern])

    if stage and stage.strip():
        query += " AND stage = ?"
        params.append(stage.strip())

    if documents_status and documents_status.strip():
        query += " AND documents_status = ?"
        params.append(documents_status.strip())

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    return [dict(row) for row in rows]

def get_application_by_id(app_db_id):
    """Fetches single application record by primary key id or application_id."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if isinstance(app_db_id, int) or str(app_db_id).isdigit():
        cursor.execute("SELECT * FROM applications WHERE id = ?", (app_db_id,))
    else:
        cursor.execute("SELECT * FROM applications WHERE application_id = ?", (app_db_id,))

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def create_application(data):
    """Inserts a new application into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT INTO applications (
            application_id, student_id, student_name, scheme,
            applied_date, documents_status, stage, sanctioned_amount,
            disbursed_date, outcome
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['application_id'].strip(),
        data.get('student_id', 'STU-NEW').strip(),
        data['student_name'].strip(),
        data.get('scheme', 'Post-Matric Scholarship').strip(),
        data.get('applied_date', '2026-07-26').strip(),
        data.get('documents_status', 'Pending').strip(),
        data.get('stage', 'Application Submitted').strip(),
        float(data.get('sanctioned_amount', 0.0)),
        data.get('disbursed_date', '').strip(),
        data.get('outcome', 'In Progress').strip()
    ))

    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return get_application_by_id(new_id)

def update_application(app_db_id, data):
    """Updates an existing application."""
    existing = get_application_by_id(app_db_id)
    if not existing:
        return None

    conn = get_db_connection()
    cursor = conn.cursor()

    updated_fields = {
        'application_id': data.get('application_id', existing['application_id']),
        'student_id': data.get('student_id', existing['student_id']),
        'student_name': data.get('student_name', existing['student_name']),
        'scheme': data.get('scheme', existing['scheme']),
        'applied_date': data.get('applied_date', existing['applied_date']),
        'documents_status': data.get('documents_status', existing['documents_status']),
        'stage': data.get('stage', existing['stage']),
        'sanctioned_amount': float(data.get('sanctioned_amount', existing['sanctioned_amount'])),
        'disbursed_date': data.get('disbursed_date', existing['disbursed_date']),
        'outcome': data.get('outcome', existing['outcome'])
    }

    cursor.execute('''
        UPDATE applications SET
            application_id = ?,
            student_id = ?,
            student_name = ?,
            scheme = ?,
            applied_date = ?,
            documents_status = ?,
            stage = ?,
            sanctioned_amount = ?,
            disbursed_date = ?,
            outcome = ?
        WHERE id = ?
    ''', (
        updated_fields['application_id'],
        updated_fields['student_id'],
        updated_fields['student_name'],
        updated_fields['scheme'],
        updated_fields['applied_date'],
        updated_fields['documents_status'],
        updated_fields['stage'],
        updated_fields['sanctioned_amount'],
        updated_fields['disbursed_date'],
        updated_fields['outcome'],
        existing['id']
    ))

    conn.commit()
    conn.close()
    return get_application_by_id(existing['id'])
