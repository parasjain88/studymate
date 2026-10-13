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

---

## 9. Login Credentials & Demo Accounts

StudyMate includes pre-seeded demonstration accounts:

| Username | Password | Full Name | Role |
| :--- | :--- | :--- | :--- |
| `PARAS JAIN` | `Paras@123` | PARAS JAIN | Student |
| `student` | `password123` | Demo Student | Student |

> **Quick Demo**: Click the **"💡 Quick Demo: Click here to auto-fill PARAS JAIN / Paras@123"** badge on the login screen to instantly log in with one click!

---

## 10. Installation and Running Instructions

No third-party libraries need to be installed. Python comes pre-installed with `tkinter`, `sqlite3`, and `hashlib`.

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

---

## 11. How to Use During College Demonstration

1. **Sign In**: Launch the app and log in using `student` / `password123` or register a new student account.
2. **Upload Study Material**: Navigate to **➕ Add Material**, click **Choose File**, select a PDF/PPT from your computer, fill in Subject (e.g., `DBMS`), Topic (e.g., `Normalization`), and Semester, then click **Upload & Save Material**.
3. **Open & View**: On the Dashboard or Search page, click **📂 Open File** to view the document directly in your browser or native viewer.
4. **Search and Filter**: Navigate to **🔍 Search & Filter**.
   - Type `"DBMS"` in the search bar.
   - Filter by Semester `"3"` and Type `"Notes"`.
5. **Star a Favorite**: Click **⭐ Toggle Favorite** on an item to bookmark it for upcoming exams.
6. **View Favorites**: Switch to the **⭐ Favorites** tab to view your bookmarked items.
7. **Sign Out**: Click the **🚪 Sign Out** button in the sidebar to return to the secure login screen.

---

## 11. Future Enhancements
- Tagging system with multi-keyword labels.
- Automated file backup to an external drive or cloud storage.
- In-app PDF thumbnail preview.
- Dark mode theme toggle.
- Export material list to Excel or CSV.
