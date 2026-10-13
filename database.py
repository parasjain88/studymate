"""
=============================================================================
StudyMate — Smart Study Material Management and Search System
Database Module (database.py)
=============================================================================
This module handles all database operations using Python's built-in sqlite3 library.
It follows standard CRUD operations and provides secure administrator management,
audit logging, session tokens, categories, reports, and storage analysis.

Zero external dependencies: built strictly with Python standard libraries.
=============================================================================
"""

import sqlite3
import os
import sys
import hashlib
import secrets
import math
from datetime import datetime, timedelta

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
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_column_exists(cursor, table_name, column_name, column_type, default_val=None):
    """
    Safely adds a column to an existing table if it does not already exist.
    Prevents SQLite schema errors while supporting non-destructive migrations.
    """
    cursor.execute(f"PRAGMA table_info({table_name})")
    cols = [col[1].lower() for col in cursor.fetchall()]
    if column_name.lower() not in cols:
        def_str = f" DEFAULT {default_val}" if default_val is not None else ""
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}{def_str}")


def init_db():
    """
    Creates and migrates all database tables and indexes safely.
    Ensures backwards compatibility with existing records.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Base Materials table
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

    # 2. Base Users table
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

    # 3. Add extended columns to materials if missing
    ensure_column_exists(cursor, "materials", "uploader_id", "INTEGER", "1")
    ensure_column_exists(cursor, "materials", "uploader_name", "TEXT", "'Student'")
    ensure_column_exists(cursor, "materials", "file_size", "INTEGER", "0")
    ensure_column_exists(cursor, "materials", "status", "TEXT", "'active'")
    ensure_column_exists(cursor, "materials", "download_count", "INTEGER", "0")
    ensure_column_exists(cursor, "materials", "description", "TEXT", "''")

    # 4. Add extended columns to users if missing
    ensure_column_exists(cursor, "users", "status", "TEXT", "'active'")
    ensure_column_exists(cursor, "users", "email", "TEXT", "''")
    ensure_column_exists(cursor, "users", "last_login", "TEXT", "''")

    # 5. Sessions table (server-side session tokens)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
    """)

    # 6. Categories / Subjects table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            code TEXT,
            description TEXT,
            semester INTEGER DEFAULT 3,
            created_at TEXT NOT NULL
        )
    """)

    # 7. Moderation Reports table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER NOT NULL,
            material_title TEXT,
            reporter_id INTEGER,
            reporter_name TEXT,
            reason TEXT NOT NULL,
            details TEXT,
            status TEXT DEFAULT 'pending',
            admin_notes TEXT,
            created_at TEXT NOT NULL,
            resolved_at TEXT
        )
    """)

    # 8. Admin Audit Logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER,
            admin_username TEXT,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            details TEXT,
            ip_address TEXT,
            status TEXT DEFAULT 'success',
            created_at TEXT NOT NULL
        )
    """)

    # 9. Application Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TEXT NOT NULL
        )
    """)

    # 10. Database Indexes for performance & quick filtering
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_status ON materials(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_subject ON materials(subject)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_materials_uploader ON materials(uploader_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_audit_created ON audit_logs(created_at)")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    # 11. Initial Administrator Setup via Environment Variables or Defaults
    admin_user = os.environ.get("ADMIN_USERNAME", "admin").strip().lower()
    admin_pass = os.environ.get("ADMIN_PASSWORD", "Admin@123").strip()
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@studymate.local").strip()

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (admin_user,))
    admin_row = cursor.fetchone()
    if not admin_row:
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, status, email, created_at)
            VALUES (?, ?, ?, 'Admin', 'active', ?, ?)
        """, (admin_user, hash_password(admin_pass), "Administrator", admin_email, now))
    else:
        # If ADMIN_PASSWORD was explicitly provided via env var, update it
        if "ADMIN_PASSWORD" in os.environ:
            cursor.execute("""
                UPDATE users SET password_hash = ?, role = 'Admin', status = 'active'
                WHERE LOWER(username) = ?
            """, (hash_password(admin_pass), admin_user))
        else:
            cursor.execute("""
                UPDATE users SET role = 'Admin', status = 'active'
                WHERE LOWER(username) = ?
            """, (admin_user,))

    # Ensure demo accounts exist
    cursor.execute("SELECT id FROM users WHERE LOWER(username) = 'paras jain'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, status, created_at)
            VALUES ('PARAS JAIN', ?, 'PARAS JAIN', 'Student', 'active', ?)
        """, (hash_password("Paras@123"), now))

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = 'student'")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, status, created_at)
            VALUES ('student', ?, 'Demo Student', 'Student', 'active', ?)
        """, (hash_password("password123"), now))

    # 12. Cross-Platform Migration: Normalize legacy Windows absolute paths to relative
    cursor.execute("SELECT id, file_path FROM materials")
    rows = cursor.fetchall()
    for r in rows:
        fpath = r["file_path"]
        if fpath and (":\\" in fpath or ":/" in fpath or "\\" in fpath or fpath.startswith("/")):
            norm_name = os.path.basename(fpath.replace("\\", "/"))
            cursor.execute("UPDATE materials SET file_path = ? WHERE id = ?", (f"uploads/{norm_name}", r["id"]))

    # 13. Backfill categories from materials if empty
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT DISTINCT subject FROM materials WHERE subject IS NOT NULL AND subject != ''")
        subjects = [row[0] for row in cursor.fetchall()]
        for sub in subjects:
            cursor.execute("""
                INSERT OR IGNORE INTO categories (name, code, description, created_at)
                VALUES (?, ?, ?, ?)
            """, (sub, sub.upper()[:6], f"Study materials for {sub}", now))

    # 14. Seed default settings if empty
    cursor.execute("SELECT COUNT(*) FROM settings")
    if cursor.fetchone()[0] == 0:
        defaults = [
            ("max_upload_size_mb", "25", "Maximum permitted upload size in megabytes"),
            ("allowed_extensions", "pdf,ppt,pptx,doc,docx,txt,zip,png,jpg,jpeg", "Comma-separated list of permitted extensions"),
            ("default_pagination", "10", "Number of items per page in management tables"),
            ("maintenance_mode", "0", "Set to 1 to enable maintenance mode for students"),
            ("allow_student_registration", "1", "Set to 1 to allow student registration"),
            ("require_moderation", "0", "Require admin approval before material is published")
        ]
        cursor.executemany("""
            INSERT OR IGNORE INTO settings (key, value, description, updated_at)
            VALUES (?, ?, ?, ?)
        """, [(k, v, d, now) for k, v, d in defaults])

    # 15. Backfill file sizes for existing records
    cursor.execute("SELECT id, file_path, file_size FROM materials")
    for r in cursor.fetchall():
        if not r["file_size"] or r["file_size"] == 0:
            full_p = os.path.join(BASE_DIR, r["file_path"])
            if os.path.isfile(full_p):
                sz = os.path.getsize(full_p)
                cursor.execute("UPDATE materials SET file_size = ? WHERE id = ?", (sz, r["id"]))

    conn.commit()
    conn.close()


# -----------------------------------------------------------------------------
# Materials CRUD (Student & Common Operations)
# -----------------------------------------------------------------------------
def add_material(title, subject, topic, semester, material_type, file_path,
                 uploader_id=1, uploader_name="Student", file_size=0, description="", status="active"):
    """
    Inserts a new study material record into the database.
    Returns the ID of the inserted record.
    """
    conn = get_connection()
    cursor = conn.cursor()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M")

    norm_path = file_path.strip().replace("\\", "/")
    if "uploads/" in norm_path or norm_path.startswith("uploads/"):
        norm_path = "uploads/" + os.path.basename(norm_path)

    # If file_size wasn't provided, calculate it if possible
    if file_size == 0:
        full_p = os.path.join(BASE_DIR, norm_path)
        if os.path.isfile(full_p):
            file_size = os.path.getsize(full_p)

    status_val = status.strip() if status else "active"

    cursor.execute("""
        INSERT INTO materials (
            title, subject, topic, semester, material_type, file_path, date_added,
            favorite, uploader_id, uploader_name, file_size, status, download_count, description
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, 0, ?)
    """, (
        title.strip(), subject.strip(), topic.strip(), int(semester),
        material_type.strip(), norm_path, current_time,
        int(uploader_id), str(uploader_name).strip(), int(file_size), status_val, str(description).strip()
    ))

    # Auto-add subject to categories table if not present
    cursor.execute("SELECT id FROM categories WHERE LOWER(name) = ?", (subject.strip().lower(),))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT OR IGNORE INTO categories (name, code, description, semester, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (subject.strip(), subject.strip().upper()[:6], f"Study materials for {subject.strip()}", int(semester), current_time))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def get_materials(search_query="", subject="All", semester="All", material_type="All", only_favorites=False):
    """
    Fetches active materials for student portal with search & filters.
    Excludes quarantined or deleted items.
    """
    conn = get_connection()
    cursor = conn.cursor()

    sql = """
        SELECT id, title, subject, topic, semester, material_type, file_path, date_added, favorite,
               uploader_id, uploader_name, file_size, status, download_count, description
        FROM materials
        WHERE status = 'active'
    """
    params = []

    if search_query and search_query.strip():
        term = f"%{search_query.strip()}%"
        sql += " AND (title LIKE ? OR subject LIKE ? OR topic LIKE ? OR material_type LIKE ?)"
        params.extend([term, term, term, term])

    if subject and subject != "All":
        sql += " AND subject = ?"
        params.append(subject)

    if semester and str(semester) != "All":
        sql += " AND semester = ?"
        params.append(int(semester))

    if material_type and material_type != "All":
        sql += " AND material_type = ?"
        params.append(material_type)

    if only_favorites:
        sql += " AND favorite = 1"

    sql += " ORDER BY id DESC"

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_material_by_id(material_id):
    """
    Retrieves a single study material record by its primary key.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, subject, topic, semester, material_type, file_path, date_added, favorite,
               uploader_id, uploader_name, file_size, status, download_count, description
        FROM materials
        WHERE id = ?
    """, (material_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def toggle_favorite(material_id):
    """
    Toggles favorite status between 1 and 0. Returns new status.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE materials
        SET favorite = (1 - favorite)
        WHERE id = ?
    """, (material_id,))
    conn.commit()
    cursor.execute("SELECT favorite FROM materials WHERE id = ?", (material_id,))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else 0


def increment_download_count(material_id):
    """
    Increments download count when a student or admin downloads a file.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE materials SET download_count = download_count + 1 WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()


def delete_material(material_id):
    """
    Soft deletes or removes material record. Leaves file safe unless admin requests permanent deletion.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()


def get_dashboard_stats():
    """
    Returns student dashboard stats.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM materials WHERE status = 'active'")
    total_materials = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(DISTINCT subject) FROM materials WHERE status = 'active'")
    total_subjects = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM materials WHERE favorite = 1 AND status = 'active'")
    total_favorites = cursor.fetchone()[0]
    conn.close()

    return {
        "total_materials": total_materials,
        "total_subjects": total_subjects,
        "total_favorites": total_favorites
    }


def get_recent_materials(limit=5):
    """
    Fetches the most recently added active materials.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, title, subject, topic, semester, material_type, file_path, date_added, favorite
        FROM materials
        WHERE status = 'active'
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_subjects():
    """
    Returns sorted list of distinct active subject names.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT subject FROM materials WHERE status = 'active' ORDER BY subject ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows if row[0]]


# -----------------------------------------------------------------------------
# User Authentication & Role Security
# -----------------------------------------------------------------------------
def register_user(username, password, full_name, email="", role="Student"):
    """
    Registers a new user account. Defaults to 'Student' role unless specified.
    """
    username = username.strip().lower()
    full_name = full_name.strip()
    email = email.strip()
    role_val = "Admin" if role and role.strip().lower() == "admin" else "Student"

    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not password or len(password) < 4:
        return False, "Password must be at least 4 characters."
    if not full_name:
        return False, "Full name is required."

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False, "Username is already taken. Please choose another."

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    pw_hash = hash_password(password)

    try:
        cursor.execute("""
            INSERT INTO users (username, password_hash, full_name, role, status, email, created_at)
            VALUES (?, ?, ?, ?, 'active', ?, ?)
        """, (username, pw_hash, full_name, role_val, email, now))
        conn.commit()
        new_id = cursor.lastrowid
        conn.close()
        return True, new_id
    except Exception as e:
        conn.close()
        return False, str(e)


def authenticate_user(username, password):
    """
    Validates user credentials against database and checks account status.
    Returns user dict on success, None if invalid or suspended.
    """
    username = username.strip().lower()
    pw_hash = hash_password(password)

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, role, status, email, created_at, last_login
        FROM users
        WHERE LOWER(username) = ? AND password_hash = ?
    """, (username, pw_hash))
    row = cursor.fetchone()

    if row:
        if row["status"] == "suspended":
            conn.close()
            return {"suspended": True, "message": "Account suspended. Contact administrator."}

        # Update last login
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (now, row["id"]))
        conn.commit()
        user_dict = dict(row)
        user_dict["last_login"] = now
        conn.close()
        return user_dict

    conn.close()
    return None


def get_user_by_id(user_id):
    """
    Fetches user profile by ID (without password hash).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, role, status, email, created_at, last_login
        FROM users WHERE id = ?
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_by_username(username):
    """
    Fetches user profile by username.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, username, full_name, role, status, email, created_at, last_login
        FROM users WHERE LOWER(username) = ?
    """, (username.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


# -----------------------------------------------------------------------------
# Sessions Management (Tokens)
# -----------------------------------------------------------------------------
def create_session(user_id, username=None, role=None, hours=24, user_agent=None):
    """
    Generates a secure cryptographic session token stored in SQLite.
    Returns token string.
    """
    token = secrets.token_hex(32)
    now = datetime.now()
    expires_at = (now + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    created_at = now.strftime("%Y-%m-%d %H:%M:%S")

    if username is None or role is None:
        user = get_user_by_id(user_id)
        if user:
            username = user.get("username", "")
            role = user.get("role", "Student")
        else:
            username = ""
            role = "Student"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sessions (token, user_id, username, role, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (token, user_id, username, role, created_at, expires_at))
    conn.commit()
    conn.close()
    return token


def get_session(token):
    """
    Retrieves and validates an active session token.
    """
    if not token:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT s.token, s.user_id, s.username, s.role, s.expires_at,
               u.full_name, u.status, u.email
        FROM sessions s
        JOIN users u ON s.user_id = u.id
        WHERE s.token = ?
    """, (token,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Check expiration
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if row["expires_at"] < now_str:
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
        return None

    # Check if user suspended
    if row["status"] == "suspended":
        conn.close()
        return None

    user_info = dict(row)
    user_info["id"] = user_info["user_id"]
    conn.close()
    return user_info

# Alias for session user lookup
get_user_by_session = get_session


def delete_session(token):
    """
    Invalidates a session on logout.
    """
    if not token:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
    conn.commit()
    conn.close()


def clean_expired_sessions():
    """
    Garbage collector for expired session tokens.
    """
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sessions WHERE expires_at < ?", (now_str,))
    conn.commit()
    conn.close()


# -----------------------------------------------------------------------------
# Admin: Complete File Management
# -----------------------------------------------------------------------------
def get_admin_materials(search="", subject="All", material_type="All", status="All",
                        uploader="All", sort_by="id", sort_order="desc", page=1, per_page=10):
    """
    Retrieves paginated materials for admin dashboard with rich filtering and sorting.
    """
    conn = get_connection()
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if search and search.strip():
        term = f"%{search.strip()}%"
        where_clauses.append("(m.title LIKE ? OR m.subject LIKE ? OR m.topic LIKE ? OR m.file_path LIKE ? OR m.uploader_name LIKE ?)")
        params.extend([term, term, term, term, term])

    if subject and subject != "All":
        where_clauses.append("m.subject = ?")
        params.append(subject)

    if material_type and material_type != "All":
        where_clauses.append("m.material_type = ?")
        params.append(material_type)

    if status and status != "All":
        where_clauses.append("m.status = ?")
        params.append(status)

    if uploader and uploader != "All":
        where_clauses.append("m.uploader_name = ?")
        params.append(uploader)

    where_str = " AND ".join(where_clauses)

    # Count total matching
    count_sql = f"SELECT COUNT(*) FROM materials m WHERE {where_str}"
    cursor.execute(count_sql, params)
    total_count = cursor.fetchone()[0]

    # Validate sort columns to prevent SQL injection
    allowed_sort = {
        "id": "m.id",
        "title": "m.title",
        "size": "m.file_size",
        "date": "m.date_added",
        "downloads": "m.download_count",
        "subject": "m.subject"
    }
    col = allowed_sort.get(sort_by, "m.id")
    direction = "ASC" if sort_order.lower() == "asc" else "DESC"

    offset = max(0, (page - 1) * per_page)
    data_sql = f"""
        SELECT m.id, m.title, m.subject, m.topic, m.semester, m.material_type, m.file_path,
               m.date_added, m.favorite, m.uploader_id, m.uploader_name, m.file_size,
               m.status, m.download_count, m.description
        FROM materials m
        WHERE {where_str}
        ORDER BY {col} {direction}
        LIMIT ? OFFSET ?
    """
    cursor.execute(data_sql, params + [per_page, offset])
    rows = [dict(r) for r in cursor.fetchall()]

    conn.close()
    total_pages = max(1, math.ceil(total_count / per_page))
    return {
        "materials": rows,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


def rename_material_file(material_id, new_title, new_file_name=None, new_filename=None, uploads_dir=None):
    """
    Safely renames an uploaded material.
    - Updates display title in database.
    - If new_file_name / new_filename is provided:
        * Strips directory traversal using basename extraction and character sanitization.
        * Preserves original file extension.
        * Safely renames physical file inside uploads directory without escaping.
        * Updates file_path in database.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, file_path FROM materials WHERE id = ?", (material_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Material record not found."

    old_title = row["title"]
    old_path = row["file_path"]
    updated_path = old_path

    new_title = new_title.strip()
    if not new_title:
        conn.close()
        return False, "Title cannot be empty."

    # If physical filename rename requested
    target_name = new_file_name or new_filename
    if target_name and str(target_name).strip():
        # Security: Strip any path traversal characters by extracting basename
        clean_candidate = os.path.basename(str(target_name).strip().replace("\\", "/"))
        clean_candidate = clean_candidate.replace("\0", "").replace("/", "").replace("\\", "").replace("..", "")

        old_clean = old_path.replace("\\", "/")
        old_basename = os.path.basename(old_clean)
        _, old_ext = os.path.splitext(old_basename)

        # Sanitize new name and preserve extension
        clean_base = os.path.splitext(clean_candidate)[0].replace(" ", "_")
        clean_base = "".join(c for c in clean_base if c.isalnum() or c in ("-", "_", "."))
        if not clean_base:
            conn.close()
            return False, "Filename contains invalid characters."

        final_filename = clean_base + old_ext

        if uploads_dir:
            src_file = os.path.join(uploads_dir, old_basename)
            dst_file = os.path.join(uploads_dir, final_filename)

            # Prevent overwriting another file if name changed
            if final_filename != old_basename and os.path.exists(dst_file):
                conn.close()
                return False, f"A file named '{final_filename}' already exists."

            if os.path.exists(src_file) and final_filename != old_basename:
                try:
                    os.replace(src_file, dst_file)
                    updated_path = f"uploads/{final_filename}"
                except Exception as e:
                    conn.close()
                    return False, f"Filesystem rename failed: {str(e)}"
            elif final_filename != old_basename:
                updated_path = f"uploads/{final_filename}"

    cursor.execute("""
        UPDATE materials
        SET title = ?, file_path = ?
        WHERE id = ?
    """, (new_title, updated_path, material_id))
    conn.commit()
    conn.close()
    return True, {"id": material_id, "old_title": old_title, "new_title": new_title, "file_path": updated_path}


def update_material_metadata(material_id, title=None, subject=None, topic=None,
                             semester=None, material_type=None, description=None, status=None):
    """
    Updates editable metadata fields for a material.
    """
    conn = get_connection()
    cursor = conn.cursor()

    updates = []
    params = []

    if title is not None:
        updates.append("title = ?")
        params.append(title.strip())
    if subject is not None:
        updates.append("subject = ?")
        params.append(subject.strip())
    if topic is not None:
        updates.append("topic = ?")
        params.append(topic.strip())
    if semester is not None:
        updates.append("semester = ?")
        params.append(int(semester))
    if material_type is not None:
        updates.append("material_type = ?")
        params.append(material_type.strip())
    if description is not None:
        updates.append("description = ?")
        params.append(description.strip())
    if status is not None and status in ("active", "quarantined", "deleted"):
        updates.append("status = ?")
        params.append(status)

    if not updates:
        conn.close()
        return True, "No changes provided."

    params.append(material_id)
    sql = f"UPDATE materials SET {', '.join(updates)} WHERE id = ?"
    cursor.execute(sql, params)
    conn.commit()
    conn.close()
    return True, "Material updated successfully."


def quarantine_material(material_id, action="quarantine"):
    """
    Sets status to 'quarantined' or restores to 'active'.
    Quarantined materials are hidden from student portal without deleting file.
    """
    new_status = "quarantined" if action == "quarantine" else "active"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE materials SET status = ? WHERE id = ?", (new_status, material_id))
    conn.commit()
    conn.close()
    return True, new_status


def permanent_delete_material(material_id, uploads_dir=None):
    """
    Permanently deletes a material from database and safely removes its physical file.
    Strictly verifies that the file to delete resides within the uploads directory.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, file_path FROM materials WHERE id = ?", (material_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Material record not found."

    file_path = row["file_path"]
    filename = os.path.basename(file_path.replace("\\", "/"))

    # Remove physical file safely if uploads_dir provided
    if uploads_dir and filename:
        full_path = os.path.abspath(os.path.join(uploads_dir, filename))
        real_uploads = os.path.abspath(uploads_dir)
        # Security: verify path containment to prevent deletion outside uploads
        if full_path.startswith(real_uploads) and os.path.isfile(full_path):
            try:
                os.remove(full_path)
            except Exception as e:
                # Log but proceed with DB cleanup
                print(f"Warning: could not delete physical file {full_path}: {e}")

    # Remove associated reports and DB record
    cursor.execute("DELETE FROM reports WHERE material_id = ?", (material_id,))
    cursor.execute("DELETE FROM materials WHERE id = ?", (material_id,))
    conn.commit()
    conn.close()
    return True, {"id": material_id, "title": row["title"], "filename": filename}


def bulk_delete_materials(material_ids, uploads_dir=None):
    """
    Permanently deletes multiple materials safely.
    """
    results = []
    for mid in material_ids:
        ok, res = permanent_delete_material(mid, uploads_dir=uploads_dir)
        if ok:
            results.append(mid)
    return results


def bulk_update_subject(material_ids, new_subject):
    """
    Bulk reassigns multiple materials to a new subject / category.
    """
    if not material_ids or not new_subject:
        return 0
    conn = get_connection()
    cursor = conn.cursor()
    placeholders = ",".join("?" for _ in material_ids)
    cursor.execute(f"""
        UPDATE materials SET subject = ? WHERE id IN ({placeholders})
    """, [new_subject.strip()] + material_ids)
    conn.commit()
    count = cursor.rowcount
    conn.close()
    return count


# -----------------------------------------------------------------------------
# Admin: User Management & Role Security
# -----------------------------------------------------------------------------
def get_admin_users(search="", role="All", status="All", page=1, per_page=10):
    """
    Retrieves paginated user accounts with upload counts and activity metadata.
    Never exposes password hashes.
    """
    conn = get_connection()
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if search and search.strip():
        term = f"%{search.strip()}%"
        where_clauses.append("(u.username LIKE ? OR u.full_name LIKE ? OR u.email LIKE ?)")
        params.extend([term, term, term])

    if role and role != "All":
        where_clauses.append("LOWER(u.role) = ?")
        params.append(role.lower())

    if status and status != "All":
        where_clauses.append("u.status = ?")
        params.append(status.lower())

    where_str = " AND ".join(where_clauses)

    cursor.execute(f"SELECT COUNT(*) FROM users u WHERE {where_str}", params)
    total_count = cursor.fetchone()[0]

    offset = max(0, (page - 1) * per_page)
    cursor.execute(f"""
        SELECT u.id, u.username, u.full_name, u.role, u.status, u.email,
               u.created_at, u.last_login,
               (SELECT COUNT(*) FROM materials m WHERE m.uploader_id = u.id) AS upload_count
        FROM users u
        WHERE {where_str}
        ORDER BY u.id DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])

    users = [dict(r) for r in cursor.fetchall()]
    conn.close()

    total_pages = max(1, math.ceil(total_count / per_page))
    return {
        "users": users,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


def count_active_admins():
    """
    Counts active administrator accounts. Used to prevent removing last admin.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'admin' AND status = 'active'")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def update_user_status(user_id, new_status, current_admin_id=None):
    """
    Updates user account status ('active' or 'suspended').
    Protections:
    - Cannot suspend yourself.
    - Cannot suspend the last active administrator.
    """
    if current_admin_id and int(user_id) == int(current_admin_id):
        return False, "You cannot suspend your own administrator account."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, status FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        conn.close()
        return False, "User not found."

    if target["role"].lower() == "admin" and new_status == "suspended":
        if count_active_admins() <= 1:
            conn.close()
            return False, "Security restriction: Cannot suspend the last active administrator."

    cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    # If suspended, invalidate all active sessions for this user
    if new_status == "suspended":
        cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()
    return True, f"User status updated to {new_status}."


def update_user_role(user_id, new_role, current_admin_id=None):
    """
    Updates user role ('Student' or 'Admin').
    Protections:
    - Cannot demote yourself if you are the only admin.
    - Cannot demote the last active administrator.
    """
    new_role = "Admin" if new_role.lower() == "admin" else "Student"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, status FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        conn.close()
        return False, "User not found."

    if target["role"].lower() == "admin" and new_role == "Student":
        if count_active_admins() <= 1:
            conn.close()
            return False, "Security restriction: Cannot demote the last active administrator."

    cursor.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()
    return True, f"User role updated to {new_role}."


def delete_user(user_id, current_admin_id=None):
    """
    Deletes user account safely.
    Protections:
    - Cannot delete yourself.
    - Cannot delete the last active administrator.
    """
    if current_admin_id and int(user_id) == int(current_admin_id):
        return False, "You cannot delete your own active administrator account."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role, status FROM users WHERE id = ?", (user_id,))
    target = cursor.fetchone()
    if not target:
        conn.close()
        return False, "User not found."

    if target["role"].lower() == "admin":
        if count_active_admins() <= 1:
            conn.close()
            return False, "Security restriction: Cannot delete the last active administrator."

    # Invalidate sessions and delete
    cursor.execute("DELETE FROM sessions WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return True, "User deleted successfully."


# -----------------------------------------------------------------------------
# Admin: Categories & Subjects Management
# -----------------------------------------------------------------------------
def get_all_categories_with_counts():
    """
    Returns all categories with total materials count in each.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT c.id, c.name, c.code, c.description, c.semester, c.created_at,
               (SELECT COUNT(*) FROM materials m WHERE LOWER(m.subject) = LOWER(c.name)) AS material_count
        FROM categories c
        ORDER BY c.name ASC
    """)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def create_category(name, code="", description="", semester=3):
    """
    Creates a new category / subject.
    Supports either order of description and semester parameters.
    """
    name = name.strip()
    if not name:
        return False, "Category name cannot be empty."

    # If description and semester were passed in reverse order
    if isinstance(description, int) or (isinstance(description, str) and description.isdigit()):
        temp_sem = description
        temp_desc = semester if isinstance(semester, str) and not semester.isdigit() else ""
        semester = int(temp_sem)
        description = str(temp_desc)
    else:
        description = str(description).strip()
        semester = int(semester) if str(semester).isdigit() else 3

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM categories WHERE LOWER(name) = ?", (name.lower(),))
    if cursor.fetchone():
        conn.close()
        return False, "Category already exists."

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    code = (code.strip().upper() if code else name[:6].upper())
    cursor.execute("""
        INSERT INTO categories (name, code, description, semester, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (name, code, description.strip(), int(semester), now))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return True, {"id": new_id, "name": name, "code": code}


def get_category_by_name(name):
    """
    Retrieves category by name (case-insensitive).
    """
    if not name:
        return None
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, code, description, semester, created_at FROM categories WHERE LOWER(name) = ?", (name.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def update_category(cat_id, name, code="", description="", semester=3):
    """
    Updates category name and description, and synchronizes existing materials.
    """
    name = name.strip()
    if not name:
        return False, "Category name cannot be empty."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
    old_row = cursor.fetchone()
    if not old_row:
        conn.close()
        return False, "Category not found."

    old_name = old_row["name"]

    cursor.execute("""
        UPDATE categories
        SET name = ?, code = ?, description = ?, semester = ?
        WHERE id = ?
    """, (name, code.strip(), description.strip(), int(semester), cat_id))

    # Synchronize materials with new category name if it changed
    if old_name != name:
        cursor.execute("UPDATE materials SET subject = ? WHERE subject = ?", (name, old_name))

    conn.commit()
    conn.close()
    return True, "Category updated successfully."


def delete_category(cat_id, reassign_to=None, reassign_to_name=None):
    """
    Deletes category. If materials use it, requires reassign_to target.
    """
    target = (reassign_to or reassign_to_name or "").strip()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM categories WHERE id = ?", (cat_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False, "Category not found."

    cat_name = row["name"]
    cursor.execute("SELECT COUNT(*) FROM materials WHERE subject = ?", (cat_name,))
    mat_count = cursor.fetchone()[0]

    if mat_count > 0:
        if not target:
            conn.close()
            return False, f"Category has {mat_count} materials assigned. Choose a replacement category to reassign them."
        cursor.execute("UPDATE materials SET subject = ? WHERE subject = ?", (target, cat_name))

    cursor.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    conn.close()
    return True, "Category deleted successfully."


def merge_categories(source_name, target_name):
    """
    Merges source category into target category. Reassigns materials and removes source.
    """
    if source_name == target_name:
        return False, "Source and target categories must be different."

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE materials SET subject = ? WHERE subject = ?", (target_name, source_name))
    cursor.execute("DELETE FROM categories WHERE name = ?", (source_name,))
    conn.commit()
    conn.close()
    return True, f"Merged '{source_name}' into '{target_name}' successfully."


# -----------------------------------------------------------------------------
# Admin: Moderation Reports
# -----------------------------------------------------------------------------
def create_report(material_id, reporter_name, reason, details="", reporter_id=None):
    """
    Allows a student/user to report an issue with a study material.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM materials WHERE id = ?", (material_id,))
    mat = cursor.fetchone()
    if not mat:
        conn.close()
        return False, "Material record does not exist."

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    cursor.execute("""
        INSERT INTO reports (
            material_id, material_title, reporter_id, reporter_name,
            reason, details, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
    """, (
        material_id, mat["title"], reporter_id, str(reporter_name).strip() or "Student",
        str(reason).strip(), str(details).strip(), now
    ))
    conn.commit()
    rep_id = cursor.lastrowid
    conn.close()
    return True, rep_id


def submit_report(material_id, reporter_name="Student", reason="", details="", reporter_id=None, **kwargs):
    """
    Convenience method for submitting study material reports with flexible kwargs.
    Returns report ID on success or None on failure.
    """
    if "reporter_id" in kwargs:
        reporter_id = kwargs["reporter_id"]
    if isinstance(reporter_name, int):
        actual_reporter_id = reporter_name
        reporter_name = reason
        reason = details
        details = kwargs.get("details", "")
        reporter_id = actual_reporter_id
    success, rep_id = create_report(material_id, reporter_name, reason, details, reporter_id)
    return rep_id if success else None


def get_report_by_id(report_id):
    """
    Fetches a single report record by ID.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_reports(status="All", page=1, per_page=10):
    """
    Retrieves paginated moderation reports for administrator.
    """
    conn = get_connection()
    cursor = conn.cursor()

    where_str = "1=1"
    params = []
    if status and status != "All":
        where_str += " AND r.status = ?"
        params.append(status.lower())

    cursor.execute(f"SELECT COUNT(*) FROM reports r WHERE {where_str}", params)
    total_count = cursor.fetchone()[0]

    offset = max(0, (page - 1) * per_page)
    cursor.execute(f"""
        SELECT r.id, r.material_id, r.material_title, r.reporter_id, r.reporter_name,
               r.reason, r.details, r.status, r.admin_notes, r.created_at, r.resolved_at,
               m.file_path, m.status AS material_status
        FROM reports r
        LEFT JOIN materials m ON r.material_id = m.id
        WHERE {where_str}
        ORDER BY r.id DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    total_pages = max(1, math.ceil(total_count / per_page))
    return {
        "reports": rows,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


def resolve_report(report_id, *args, **kwargs):
    """
    Marks report as 'resolved' or 'dismissed'.
    Supports either:
      resolve_report(report_id, new_status, admin_notes, admin_username)
      resolve_report(report_id, admin_id, new_status, admin_notes)
    """
    new_status = kwargs.get("new_status") or kwargs.get("status")
    admin_notes = kwargs.get("admin_notes", "")
    admin_username = kwargs.get("admin_username", "")

    if args:
        if isinstance(args[0], int):
            # args[0] is admin_id
            admin_id = args[0]
            if len(args) > 1:
                new_status = args[1]
            if len(args) > 2:
                admin_notes = args[2]
            user = get_user_by_id(admin_id)
            if user:
                admin_username = user.get("username", "")
        else:
            new_status = args[0]
            if len(args) > 1:
                admin_notes = args[1]
            if len(args) > 2:
                admin_username = args[2]

    if not new_status or new_status not in ("resolved", "dismissed"):
        new_status = "resolved"

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    notes = f"[{admin_username}]: {admin_notes.strip()}" if admin_username else admin_notes.strip()

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE reports
        SET status = ?, admin_notes = ?, resolved_at = ?
        WHERE id = ?
    """, (new_status, notes, now, report_id))
    conn.commit()
    conn.close()
    return True, f"Report marked as {new_status}."


# -----------------------------------------------------------------------------
# Admin: Activity Audit Logging
# -----------------------------------------------------------------------------
def log_audit(admin_id, admin_username, action, entity_type, entity_id,
              details="", ip_address="", status="success"):
    """
    Appends an immutable audit record for administrative actions.
    Never stores sensitive passwords or auth tokens.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs (
            admin_id, admin_username, action, entity_type, entity_id,
            details, ip_address, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        admin_id, admin_username, action, entity_type,
        entity_id, details, ip_address, status, now
    ))
    conn.commit()
    conn.close()


def get_audit_logs(search="", action="All", page=1, per_page=15):
    """
    Retrieves paginated audit log events for authorized administrators.
    """
    conn = get_connection()
    cursor = conn.cursor()

    where_clauses = ["1=1"]
    params = []

    if search and search.strip():
        term = f"%{search.strip()}%"
        where_clauses.append("(admin_username LIKE ? OR action LIKE ? OR details LIKE ? OR entity_type LIKE ?)")
        params.extend([term, term, term, term])

    if action and action != "All":
        where_clauses.append("action = ?")
        params.append(action)

    where_str = " AND ".join(where_clauses)
    cursor.execute(f"SELECT COUNT(*) FROM audit_logs WHERE {where_str}", params)
    total_count = cursor.fetchone()[0]

    offset = max(0, (page - 1) * per_page)
    cursor.execute(f"""
        SELECT id, admin_id, admin_username, action, entity_type, entity_id,
               details, ip_address, status, created_at
        FROM audit_logs
        WHERE {where_str}
        ORDER BY id DESC
        LIMIT ? OFFSET ?
    """, params + [per_page, offset])

    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    total_pages = max(1, math.ceil(total_count / per_page))
    return {
        "logs": rows,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages
    }


# -----------------------------------------------------------------------------
# Admin: Storage Analysis & Consistency Scanner
# -----------------------------------------------------------------------------
def get_storage_stats(base_dir=None, uploads_dir=None):
    """
    Calculates detailed storage metrics from SQLite database and disk storage.
    """
    if base_dir and (os.path.basename(os.path.normpath(base_dir)).lower() == "uploads" or (uploads_dir is None and "uploads" in base_dir)):
        up_dir = base_dir
    else:
        base = base_dir or BASE_DIR
        up_dir = uploads_dir or os.path.join(base, "uploads")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM materials")
    total_materials = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(file_size) FROM materials")
    db_total_size = cursor.fetchone()[0] or 0

    # Physical disk size of uploads directory
    disk_total_size = 0
    file_count_disk = 0
    if os.path.isdir(up_dir):
        for entry in os.scandir(up_dir):
            if entry.is_file():
                disk_total_size += entry.stat().st_size
                file_count_disk += 1

    # Breakdown by file type extension from materials
    cursor.execute("SELECT file_path, file_size FROM materials")
    ext_breakdown = {}
    for r in cursor.fetchall():
        fpath = r["file_path"].replace("\\", "/")
        ext = os.path.splitext(os.path.basename(fpath))[1].lower() or "other"
        ext_breakdown[ext] = ext_breakdown.get(ext, 0) + (r["file_size"] or 0)

    # Largest 5 files
    cursor.execute("""
        SELECT id, title, subject, file_size, file_path, date_added
        FROM materials
        ORDER BY file_size DESC
        LIMIT 5
    """)
    largest_files = [dict(r) for r in cursor.fetchall()]

    conn.close()

    return {
        "total_materials_db": total_materials,
        "db_total_size_bytes": db_total_size,
        "disk_total_size_bytes": disk_total_size,
        "file_count_disk": file_count_disk,
        "ext_breakdown": ext_breakdown,
        "largest_files": largest_files
    }


def scan_storage_consistency(base_dir=None, uploads_dir=None):
    """
    Compares database records with actual filesystem in uploads/:
    - Missing files: present in SQLite database, but physical file is absent from disk.
    - Orphaned files: present in physical uploads/ folder, but no record exists in database.
    - Valid files: synchronized in both.
    """
    if base_dir and (os.path.basename(os.path.normpath(base_dir)).lower() == "uploads" or (uploads_dir is None and "uploads" in base_dir)):
        up_dir = base_dir
    else:
        base = base_dir or BASE_DIR
        up_dir = uploads_dir or os.path.join(base, "uploads")

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, file_path, file_size FROM materials")
    db_materials = cursor.fetchall()
    conn.close()

    disk_files = set()
    if os.path.isdir(up_dir):
        for entry in os.scandir(up_dir):
            if entry.is_file():
                disk_files.add(entry.name)

    missing = []
    valid = []
    db_referenced_basenames = set()

    for r in db_materials:
        clean_p = r["file_path"].replace("\\", "/")
        fname = os.path.basename(clean_p)
        db_referenced_basenames.add(fname)
        full_disk_path = os.path.join(up_dir, fname)

        if os.path.isfile(full_disk_path):
            valid.append({
                "id": r["id"],
                "title": r["title"],
                "filename": fname,
                "size": os.path.getsize(full_disk_path)
            })
        else:
            missing.append({
                "id": r["id"],
                "title": r["title"],
                "filename": fname,
                "expected_path": r["file_path"]
            })

    orphaned = []
    for disk_name in disk_files:
        if disk_name not in db_referenced_basenames:
            fpath = os.path.join(up_dir, disk_name)
            orphaned.append({
                "filename": disk_name,
                "size": os.path.getsize(fpath) if os.path.isfile(fpath) else 0
            })

    return {
        "scanned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_db_records": len(db_materials),
        "total_disk_files": len(disk_files),
        "valid_count": len(valid),
        "missing_count": len(missing),
        "orphaned_count": len(orphaned),
        "missing_files": missing,
        "orphaned_files": orphaned
    }


# -----------------------------------------------------------------------------
# Admin: Application Settings
# -----------------------------------------------------------------------------
def get_all_settings():
    """
    Returns dictionary of all application configuration settings.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value, description FROM settings")
    settings = {r["key"]: {"value": r["value"], "description": r["description"]} for r in cursor.fetchall()}
    conn.close()
    return settings


def get_setting(key, default=""):
    """
    Retrieves a single setting value.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default


def update_setting(key, value):
    """
    Updates or inserts an application setting safely.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
    """, (key, str(value).strip(), now))
    conn.commit()
    conn.close()
    return True


# -----------------------------------------------------------------------------
# Admin: Dashboard Overview Statistics (100% Real DB Backed)
# -----------------------------------------------------------------------------
def get_admin_overview_stats(base_dir=None, uploads_dir=None):
    """
    Aggregates comprehensive real metrics for the Admin Dashboard overview.
    Zero mock/hardcoded values.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM materials WHERE status = 'active'")
    total_materials = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM materials WHERE status = 'quarantined'")
    total_quarantined = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(file_size) FROM materials WHERE status = 'active'")
    total_storage = cursor.fetchone()[0] or 0

    today_str = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM materials WHERE date_added LIKE ?", (f"{today_str}%",))
    uploads_today = cursor.fetchone()[0]

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cursor.execute("SELECT COUNT(*) FROM materials WHERE date_added >= ?", (week_ago,))
    uploads_this_week = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'pending'")
    pending_reports = cursor.fetchone()[0]

    # Top popular materials (by download count + favorite weighting)
    cursor.execute("""
        SELECT id, title, subject, semester, material_type, download_count, favorite
        FROM materials
        WHERE status = 'active'
        ORDER BY (download_count + favorite * 3) DESC
        LIMIT 5
    """)
    popular = [dict(r) for r in cursor.fetchall()]

    # Most active users by uploaded files
    cursor.execute("""
        SELECT u.id, u.username, u.full_name, u.role, COUNT(m.id) AS upload_count
        FROM users u
        LEFT JOIN materials m ON u.id = m.uploader_id
        GROUP BY u.id
        ORDER BY upload_count DESC
        LIMIT 5
    """)
    active_users = [dict(r) for r in cursor.fetchall()]

    # Recent materials
    cursor.execute("""
        SELECT id, title, subject, semester, material_type, uploader_name, date_added, file_size
        FROM materials
        ORDER BY id DESC
        LIMIT 5
    """)
    recent_materials = [dict(r) for r in cursor.fetchall()]

    # Categories distribution
    cursor.execute("""
        SELECT subject, COUNT(*) as count
        FROM materials
        WHERE status = 'active'
        GROUP BY subject
        ORDER BY count DESC
    """)
    category_counts = [dict(r) for r in cursor.fetchall()]

    # Recent admin activity logs
    cursor.execute("""
        SELECT id, admin_username, action, entity_type, details, created_at
        FROM audit_logs
        ORDER BY id DESC
        LIMIT 5
    """)
    recent_audit = [dict(r) for r in cursor.fetchall()]

    conn.close()

    # Get storage check for missing files count
    consistency = scan_storage_consistency(base_dir, uploads_dir)

    return {
        "total_users": total_users,
        "total_materials": total_materials,
        "total_quarantined": total_quarantined,
        "total_storage_bytes": total_storage,
        "uploads_today": uploads_today,
        "uploads_this_week": uploads_this_week,
        "pending_reports": pending_reports,
        "missing_files_count": consistency["missing_count"],
        "popular_materials": popular,
        "active_users": active_users,
        "recent_materials": recent_materials,
        "category_counts": category_counts,
        "recent_audit": recent_audit
    }


# -----------------------------------------------------------------------------
# Administration Function Aliases for Full Compatibility
# -----------------------------------------------------------------------------
set_setting = update_setting
get_admin_dashboard_stats = get_admin_overview_stats
get_storage_breakdown = get_storage_stats
get_all_reports_admin = get_reports
admin_rename_material = rename_material_file
admin_edit_material_metadata = update_material_metadata

def admin_quarantine_material(material_id, quarantine=True, action=None):
    act = action if action is not None else ("quarantine" if quarantine else "unquarantine")
    return quarantine_material(material_id, act)

admin_delete_material = permanent_delete_material

def get_all_materials_admin(search="", search_query="", subject="All", material_type="All", status="All", uploader="All", sort_by="id", sort_order="desc", page=1, per_page=10):
    q = search_query or search
    return get_admin_materials(search=q, subject=subject, material_type=material_type, status=status, uploader=uploader, sort_by=sort_by, sort_order=sort_order, page=page, per_page=per_page)

def get_all_users_admin(search="", search_query="", role="All", status="All", page=1, per_page=10):
    q = search_query or search
    return get_admin_users(search=q, role=role, status=status, page=page, per_page=per_page)

get_all_categories = get_all_categories_with_counts

def add_audit_log(admin_id=None, admin_username="System", action="", entity_type="", entity_id=None, details="", ip_address="", status="success"):
    return log_audit(admin_id, admin_username, action, entity_type, entity_id, details, ip_address, status)


# -----------------------------------------------------------------------------
# CLI Entrypoint for Admin Setup
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--create-admin":
        init_db()
        username = sys.argv[2].strip().lower()
        password = sys.argv[3].strip()
        full_name = sys.argv[4].strip() if len(sys.argv) > 4 else "Administrator"
        email = sys.argv[5].strip() if len(sys.argv) > 5 else f"{username}@studymate.local"

        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        pw_hash = hash_password(password)

        cursor.execute("SELECT id FROM users WHERE LOWER(username) = ?", (username,))
        row = cursor.fetchone()
        if row:
            cursor.execute("""
                UPDATE users SET password_hash = ?, role = 'Admin', status = 'active', full_name = ?, email = ?
                WHERE id = ?
            """, (pw_hash, full_name, email, row["id"]))
            print(f"[StudyMate] Existing user '{username}' promoted to Administrator.")
        else:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, status, email, created_at)
                VALUES (?, ?, ?, 'Admin', 'active', ?, ?)
            """, (username, pw_hash, full_name, email, now))
            print(f"[StudyMate] New Administrator account '{username}' created successfully.")

        conn.commit()
        conn.close()
    else:
        print("[StudyMate Database] Initializing and migrating database...")
        init_db()
        print("[StudyMate Database] Database initialized and verified.")
