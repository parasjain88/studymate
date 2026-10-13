"""
=============================================================================
StudyMate — Smart Study Material Management and Search System
Database Module (database.py)
=============================================================================
This module handles all database operations using Python's built-in sqlite3 library.
It follows standard CRUD (Create, Read, Update, Delete) operations.

Features implemented:
1. Automatic database and table creation (materials table)
2. Adding new study material records
3. Searching materials using SQL LIKE operator
4. Filtering materials by Subject, Semester, and Material Type
5. Toggling favorite status
6. Deleting material records (leaves actual files safe on disk)
7. Fetching dashboard statistics (counts and recent materials)
8. Loading sample demo data for viva presentations
=============================================================================
"""

import sqlite3
import os
import hashlib
from datetime import datetime

# Define database file path in the same directory as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "studymate.db")


def hash_password(password):
    """
    Computes standard SHA-256 hash for secure password storage.
    """
    return hashlib.sha256(password.strip().encode("utf-8")).hexdigest()


def get_connection():
    """
    Establishes and returns a connection to the SQLite database.
    SQLite stores the entire database in a single file (studymate.db).
    """
    return sqlite3.connect(DB_FILE)


def init_db():
    """
    Creates the 'materials' and 'users' tables if they do not already exist.
    Called once when the application starts up.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Schema definition for materials:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            subject TEXT NOT NULL,
            topic TEXT,
            semester INTEGER NOT NULL,
            material_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            date_added TEXT NOT NULL,
            favorite INTEGER DEFAULT 0
        )
    """)

    # Schema definition for users:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'Student',
            created_at TEXT NOT NULL
        )
    """)

    # Seed or ensure PARAS JAIN account exists
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", ("paras jain",))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("PARAS JAIN", hash_password("Paras@123"), "PARAS JAIN", "Student", now))
    else:
        cursor.execute("""
            UPDATE users SET password_hash = ?, full_name = ? WHERE LOWER(username) = ?
        """, (hash_password("Paras@123"), "PARAS JAIN", "paras jain"))

    # Also ensure student and admin accounts exist if table was empty
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", ("student",))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, ("student", hash_password("password123"), "Demo Student", "Student", now))

    # Cross-Platform Migration: Normalize legacy Windows absolute paths to relative paths
    cursor.execute("SELECT id, file_path FROM materials")
    rows = cursor.fetchall()
    for row_id, fpath in rows:
        if fpath and (":\\" in fpath or ":/" in fpath or "\\" in fpath or fpath.startswith("/")):
            norm_name = os.path.basename(fpath.replace("\\", "/"))
            cursor.execute("UPDATE materials SET file_path = ? WHERE id = ?", (f"uploads/{norm_name}", row_id))

    conn.commit()
    conn.close()


def add_material(title, subject, topic, semester, material_type, file_path):
    """
    Inserts a new study material record into the database.
    Returns the ID of the inserted record.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Format current date and time as YYYY-MM-DD HH:MM
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Ensure file_path is stored as a clean relative path for cross-device/cross-platform compatibility
    norm_path = file_path.strip().replace("\\", "/")
    if "uploads/" in norm_path or norm_path.startswith("uploads/"):
        norm_path = "uploads/" + os.path.basename(norm_path)

    # Use parameterized query (?) to safely insert data and prevent SQL injection
    cursor.execute("""
        INSERT INTO materials (title, subject, topic, semester, material_type, file_path, date_added, favorite)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (title.strip(), subject.strip(), topic.strip(), int(semester), material_type.strip(), norm_path, current_time))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_materials(search_query="", subject="All", semester="All", material_type="All", only_favorites=False):
    """
    Fetches materials with optional search query and multiple filter conditions.
    - search_query: Matches title, subject, topic, or material type using LIKE.
    - subject: Filters by specific subject name.
    - semester: Filters by specific semester (1-8).
    - material_type: Filters by type (Notes, PPT, etc.).
    - only_favorites: If True, fetches only starred items.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Base query: 1=1 is a standard SQL technique allowing dynamic AND conditions
    sql = """
        SELECT id, title, subject, topic, semester, material_type, file_path, date_added, favorite
        FROM materials
        WHERE 1=1
    """
    params = []

    # 1. Search Query using LIKE operator (%term% matches anywhere in string)
    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        sql += " AND (title LIKE ? OR subject LIKE ? OR topic LIKE ? OR material_type LIKE ?)"
        params.extend([term, term, term, term])

    # 2. Filter by Subject
    if subject and subject != "All":
        sql += " AND subject = ?"
        params.append(subject)

    # 3. Filter by Semester
    if semester and str(semester) != "All":
        sql += " AND semester = ?"
        params.append(int(semester))

    # 4. Filter by Material Type
    if material_type and material_type != "All":
        sql += " AND material_type = ?"
        params.append(material_type)

    # 5. Filter for Favorites tab
    if only_favorites:
        sql += " AND favorite = 1"

    # Order newest materials first
    sql += " ORDER BY id DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_material_by_id(material_id):
    """
    Retrieves a single study material record by its primary key (ID).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, subject, topic, semester, material_type, file_path, date_added, favorite
        FROM materials
        WHERE id = ?
    """, (material_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def toggle_favorite(material_id):
    """
    Toggles the favorite status between 1 (Favorite) and 0 (Normal).
    Returns the new favorite status (0 or 1).
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1 - favorite flips 0 to 1, and 1 to 0
    cursor.execute("""
        UPDATE materials
        SET favorite = (1 - favorite)
        WHERE id = ?
    """, (material_id,))
    conn.commit()

    # Check updated value
    cursor.execute("SELECT favorite FROM materials WHERE id = ?", (material_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0


def delete_material(material_id):
    """
    Deletes a material record from the database.
    Note: The actual file on the hard drive is NOT deleted.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()


def get_dashboard_stats():
    """
    Returns high-level statistics for the Dashboard:
    - total_materials: Count of all study materials saved
    - total_subjects: Count of unique subjects
    - total_favorites: Count of favorited materials
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM materials")
    total_materials = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT subject) FROM materials")
    total_subjects = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM materials WHERE favorite = 1")
    total_favorites = cursor.fetchone()[0]

    conn.close()
    return {
        "total_materials": total_materials,
        "total_subjects": total_subjects,
        "total_favorites": total_favorites
    }


def get_recent_materials(limit=5):
    """
    Fetches the most recently added materials for display on the Dashboard.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, subject, topic, semester, material_type, file_path, date_added, favorite
        FROM materials
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_subjects():
    """
    Returns a sorted list of unique subject names currently in the database.
    Used to dynamically populate filter dropdowns.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT subject FROM materials ORDER BY subject ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows if row[0]]


def insert_sample_data():
    """
    Deprecated: Sample data has been removed for production deployment.
    """
    return 0


# -----------------------------------------------------------------------------
# User Authentication & Management
# -----------------------------------------------------------------------------
def register_user(username, password, full_name, role="Student"):
    """
    Registers a new student/user account.
    Returns (True, user_id) on success, or (False, error_message) on failure.
    """
    username = username.strip().lower()
    full_name = full_name.strip()
    if not username:
        return False, "Username is required."
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters long."
    if not full_name:
        return False, "Full name is required."

    conn = get_connection()
    cursor = conn.cursor()

    # Check if username already exists
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username is already taken. Please choose another."

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pw_hash = hash_password(password)

    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, pw_hash, full_name, role, now))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return True, new_id
    except Exception as e:
        conn.close()
        return False, str(e)


def authenticate_user(username, password):
    """
    Validates user credentials against the database.
    Returns a user dictionary if credentials match, else None.
    """
    username = username.strip().lower()
    pw_hash = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, role, created_at
        FROM users
        WHERE LOWER(username) = ? AND password_hash = ?
    """, (username, pw_hash))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "created_at": row[4]
        }
    return None


def get_user_by_username(username):
    """
    Fetches user profile by username.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, role, created_at
        FROM users
        WHERE LOWER(username) = ?
    """, (username.strip().lower(),))
    row = cursor.fetchone()
    conn.close()

    if row:
        return {
            "id": row[0],
            "username": row[1],
            "full_name": row[2],
            "role": row[3],
            "created_at": row[4]
        }
    return None


