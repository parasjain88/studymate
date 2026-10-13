# 📚 StudyMate — Smart Study Material Management and Search System

A lightweight, beginner-friendly desktop application developed for college students to organize, search, filter, bookmark, and directly open study materials (PDFs, PPTs, DOC/DOCX, Lab Manuals, Assignments, etc.) from one central dashboard.

> **Course**: B.Tech Computer Science and Engineering (CSE)  
> **Target Academic Level**: 3rd Semester Mini Project  
> **Key Technologies**: Python 3, Tkinter GUI, SQLite3 Database  

---

## 1. Project Introduction
During college semesters, engineering students accumulate dozens of lecture notes, question banks, previous year question papers (PYQs), lab manuals, and assignments across different folders, WhatsApp downloads, and desktop directories. Finding a specific unit or topic before an exam or lab exam is often chaotic and time-consuming.

**StudyMate** solves this issue by serving as a dedicated personal study material manager. Rather than moving or duplicating large files on your hard drive, StudyMate indexes the files in a local SQLite database and lets you find and launch them instantly.

---

## 2. Problem Statement
- **Disorganized Files**: Notes and assignments are scattered across Downloads, Desktop, and cloud drives with arbitrary file names.
- **Wasted Time**: Students waste valuable exam preparation time hunting for specific PDF chapters or lab experiments.
- **No Subject Categorization**: Windows File Explorer does not provide academic metadata like semester, subject code, topic, or material type out-of-the-box.
- **Over-engineered Solutions**: Cloud apps require internet connectivity, student logins, complex setups, and monthly subscriptions.

---

## 3. Project Objectives
1. Build a 100% offline, local desktop application tailored for student needs.
2. Provide quick categorization of files by Title, Subject, Topic, Semester (1 to 8), and Material Type.
3. Enable multi-criteria search using SQL `LIKE` queries for instant retrieval.
4. Allow one-click opening of study materials using the operating system's default viewers.
5. Provide a "Favorites" bookmarking mechanism to highlight urgent exam preparation materials.
6. Ensure beginner-friendly, clean, well-commented Python code that any 3rd-semester B.Tech student can confidently explain in a viva.

---

## 4. Key Features

| Feature | Description |
| :--- | :--- |
| **🔐 Student Authentication** | Secure Login & Account Registration system with SHA-256 password hashing. Supports student & admin roles. |
| **🏠 Interactive Dashboard** | Displays real-time statistics (total files, unique subjects, starred materials) and authenticated user profile. |
| **📤 File Upload & Management** | Directly upload PDFs, PPTs, DOCs, and notes via browser or desktop into the dedicated `/uploads` storage. |
| **🔍 Search & Filter** | Real-time search across titles, subjects, and topics combined with dropdown filters for Subject, Semester, and Material Type. |
| **📂 In-Browser & Local Viewer** | Seamlessly preview or download uploaded files directly in the browser or via system default viewer. |
| **⭐ Favorites System** | Bookmark critical exam notes or PYQs with a single click and access them in a dedicated Favorites tab. |
| **🛡️ Graceful Error Handling** | Detects moved or missing files and displays helpful notices without crashing the program. |

---

## 5. Technologies Used

* **Programming Language**: Python 3 (Tested on Python 3.10+)
* **Graphical User Interface (GUI)**: Python's built-in `tkinter` and `tkinter.ttk`
* **Database Engine**: Python's built-in `sqlite3`
* **File Handling**: Built-in `os` and `os.path`
* **File Launcher**: Windows `os.startfile()`
* **External Dependencies**: **NONE** (Zero `pip install` required!)

---

## 6. System Requirements

### Hardware Requirements:
- **Processor**: Intel Core i3 / AMD Ryzen 3 or higher
- **RAM**: 2 GB minimum (4 GB recommended)
- **Storage**: 50 MB free disk space

### Software Requirements:
- **Operating System**: Windows 10 / Windows 11 (Supports Linux/macOS fallback)
- **Python**: Python 3.8 or higher installed and added to PATH

---

## 7. Project Structure

```text
StudyMate/
│
├── main.py                  # Entry point of the application
├── database.py              # SQLite database functions and CRUD logic
├── ui.py                    # Tkinter GUI implementation and event handling
├── studymate.db             # SQLite database file (auto-created on first launch)
│
├── sample_materials/        # Pre-packaged sample notes for demonstration
│   ├── DBMS_Unit1_Notes.txt
│   ├── OS_Memory_Management.txt
│   ├── DSA_Trees_Assignment.txt
│   ├── Computer_Networks_Unit4.txt
│   └── Python_Lab_Manual.txt
│
├── README.md                # Project documentation and guide
├── VIVA.md                  # 20+ Viva questions and answers for 3rd semester CSE
└── PROJECT_REPORT.md        # Academic mini-project report content
```

---

## 8. Database Architecture

The application uses an SQLite database named `studymate.db`. It stores information inside two primary tables: `users` and `materials`.

### Table 1 Schema: `users` (Authentication)

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique User ID |
| `username` | TEXT | UNIQUE NOT NULL | Unique login handle (e.g. `student`) |
| `password_hash` | TEXT | NOT NULL | SHA-256 hashed password string |
| `full_name` | TEXT | NOT NULL | Student's full display name |
| `role` | TEXT | DEFAULT 'Student' | 'Student' or 'Admin' |
| `created_at` | TEXT | NOT NULL | Account creation timestamp |

### Table 2 Schema: `materials` (Study Files)

| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID for each record |
| `title` | TEXT | NOT NULL | Title of the study material |
| `subject` | TEXT | NOT NULL | Course or subject name (e.g. DBMS, OS) |
| `topic` | TEXT | NULLABLE | Specific chapter or unit |
| `semester` | INTEGER | NOT NULL | Semester number (1 to 8) |
| `material_type`| TEXT | NOT NULL | Notes, PPT, Assignment, Book, etc. |
| `file_path` | TEXT | NOT NULL | Relative path in `/uploads` or absolute path |
| `date_added` | TEXT | NOT NULL | Date & time added (YYYY-MM-DD HH:MM) |
| `favorite` | INTEGER | DEFAULT 0 | 1 = Favorite / Starred, 0 = Normal |
| `uploader_id` | INTEGER | DEFAULT 1 | User ID of the uploader |
| `uploader_name` | TEXT | DEFAULT 'Student' | Display name of uploader |
| `file_size` | INTEGER | DEFAULT 0 | File size in bytes |
| `status` | TEXT | DEFAULT 'active' | 'active', 'quarantined', or 'deleted' |
| `download_count` | INTEGER | DEFAULT 0 | Total times opened/downloaded |
| `description` | TEXT | DEFAULT '' | Description or notes |

### Table 3 Schema: `sessions` (Server-Side Session Tokens)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `token` | TEXT | PRIMARY KEY | 64-char cryptographically secure token |
| `user_id` | INTEGER | NOT NULL | Associated user ID |
| `username` | TEXT | NOT NULL | Username |
| `role` | TEXT | NOT NULL | 'Student' or 'Admin' |
| `created_at` | TEXT | NOT NULL | Session creation timestamp |
| `expires_at` | TEXT | NOT NULL | Session expiration timestamp (7 days) |

### Table 4 Schema: `categories` (Subjects & Syllabus)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Subject ID |
| `name` | TEXT | UNIQUE NOT NULL | Subject name (e.g. DBMS, OS) |
| `code` | TEXT | NULLABLE | Subject code (e.g. CS301) |
| `description` | TEXT | NULLABLE | Syllabus details |
| `semester` | INTEGER | DEFAULT 3 | Target semester |
| `created_at` | TEXT | NOT NULL | Creation timestamp |

### Table 5 Schema: `reports` (Moderation & Broken File Reports)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Report ID |
| `material_id` | INTEGER | NOT NULL | Target study material |
| `reporter_id` | INTEGER | NOT NULL | Student reporting the file |
| `reason` | TEXT | NOT NULL | Reason (e.g. Corrupted, Copyright, Wrong Subject) |
| `status` | TEXT | DEFAULT 'pending' | 'pending', 'resolved', or 'dismissed' |

### Table 6 Schema: `audit_logs` (Security & Administrative History)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Log entry ID |
| `admin_username` | TEXT | NOT NULL | Username of administrator |
| `action` | TEXT | NOT NULL | Action performed (DELETE_FILE, QUARANTINE, etc.) |
| `details` | TEXT | NOT NULL | Human-readable audit description |
| `ip_address` | TEXT | NOT NULL | Client IP address |
| `created_at` | TEXT | NOT NULL | Timestamp of action |

---

## 9. Login Credentials & Demo Accounts

StudyMate includes pre-seeded demonstration accounts:

| Username | Password | Full Name | Role | Access Level |
| :--- | :--- | :--- | :--- | :--- |
| `admin` | `Admin@123` | System Administrator | **Admin** | Full Admin Panel (`/admin`) + Student Portal |
| `PARAS JAIN` | `Paras@123` | PARAS JAIN | **Student** | Student Study Material Finder & Uploader |
| `student` | `password123` | Demo Student | **Student** | Student Study Material Finder & Uploader |

> **Quick Demo Login**: Click the **"💡 Quick Demo: PARAS JAIN / Paras@123"** badge on the login screen to auto-fill student credentials instantly!
>
> **Direct Admin URL**: Navigate directly to `http://localhost:8000/admin` (or `/admin` on your deployed server) when logged in as an Administrator (`admin` / `Admin@123`).

---

## 10. Installation and Running Instructions

No third-party libraries need to be installed. Python comes pre-installed with `tkinter`, `sqlite3`, `hashlib`, and `http.server`.

### Step 1: Open Command Prompt or PowerShell
Navigate to the project folder:
```powershell
cd "D:\mini project"
```

### Step 2: Run Application

**Option A — Browser Web Mode (Deployment & Web App):**
```powershell
python web_app.py
```
This starts the local Python server and automatically opens StudyMate in your default browser at `http://localhost:8000`.

**Option B — Desktop GUI Mode (Tkinter):**
```powershell
python main.py
```

### Step 3: Run Automated Test Suite
To verify database integrity, RBAC security, rate limiting, and all 13 unit/integration tests:
```powershell
python test_admin.py
```

### Creating Additional Admin Accounts via CLI
You can safely create or promote administrator accounts via the command line:
```powershell
python database.py --create-admin <username> <password> "<Full Name>" <email>
```
Example:
```powershell
python database.py --create-admin superadmin SecurePass@2026 "Super Admin" admin@college.edu
```

---

## 11. Cloud Deployment Configuration (Render)

When deploying to [Render](https://render.com), configure the following environment variables in your Render Dashboard:

| Variable | Recommended Value | Purpose |
| :--- | :--- | :--- |
| `PORT` | `10000` (set by Render) | Listening web port |
| `ADMIN_USERNAME` | `admin` | Initial admin username |
| `ADMIN_PASSWORD` | `Admin@123` (or custom secure password) | Initial admin password |
| `ADMIN_FULL_NAME` | `System Administrator` | Admin display name |

Upon startup, `web_app.py` checks these variables and automatically ensures an active administrator account exists without hardcoding credentials in source code.

---

## 12. Security & Architecture Defenses

1. **Role-Based Access Control (RBAC)**: All administrative endpoints (`/api/admin/*` and `/admin`) require an active session token belonging to an account with `role = 'Admin'`. Unauthorized users receive `HTTP 401 Unauthorized` or `HTTP 403 Forbidden`.
2. **Cryptographic Session Tokens**: Uses Python's `secrets.token_hex(32)` to generate 64-character unguessable session tokens stored server-side with a 7-day expiration.
3. **Brute-Force Rate Limiting**: IP-based rate limiter prevents password brute-forcing (5 failed attempts within 60 seconds triggers a temporary lockout with `HTTP 429 Too Many Requests`).
4. **Path Traversal Protection**: File operations and rename requests strictly extract the basename (`os.path.basename`) and reject `../` traversal sequences to prevent escaping the `/uploads` directory.
5. **Last Admin Protection**: The application prevents suspending, demoting, or deleting the last remaining active administrator account.
6. **Storage Consistency Scanner**: Admin panel includes an automated scan comparing SQLite database records with physical files in `/uploads` to detect missing files or orphaned disk files.
7. **Comprehensive Audit Logging**: All sensitive administrative actions (file deletions, role promotions, setting updates, quarantining) are recorded with timestamp, admin username, action type, and client IP address.

---

## 13. How to Use During College Demonstration

1. **Sign In as Student**: Log in using `PARAS JAIN` / `Paras@123`.
2. **Upload Study Material**: Navigate to **➕ Add Material**, click **Choose File**, select a PDF/PPT, enter Subject (e.g., `DBMS`), Topic (e.g., `Normalization`), Sem `"3"`, and click **Upload & Save Material**.
3. **Open & View**: On the Dashboard or Search page, click **📂 Open File** to view the document.
4. **Report a File**: Click **🚩 Report File** on any study material to simulate a student reporting broken content.
5. **Sign In as Administrator**: Sign out and log in with `admin` / `Admin@123`.
6. **Admin Dashboard Overview**: View live real-time statistics (total files, users, storage used, pending reports).
7. **File Management**: Rename a file safely, toggle quarantine status, or perform bulk category reassignments.
8. **Moderation**: Review student reports under **Reports & Moderation** and resolve or dismiss with notes.
9. **Storage Consistency Scanner**: Open **Storage Management** and run the scanner to see valid, missing, and orphaned files.
10. **Activity Logs**: Demonstrate the **Activity Logs** tab showing the audit trail of actions taken.
