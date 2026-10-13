# 🎓 StudyMate — College Viva Voce Questions & Answers
### B.Tech 3rd Semester Computer Science & Engineering (CSE)

This document contains 22 standard viva questions with simple, accurate, and easy-to-remember answers designed for your mini-project viva evaluation.

---

### Q1. What is StudyMate?
**Answer:**  
StudyMate is a desktop application developed in Python that helps college students organize, search, filter, bookmark, and directly open study materials such as PDFs, lecture PPTs, question banks, and lab manuals from a single, organized interface.

---

### Q2. Why did you choose to build this project? (Motivation/Problem Statement)
**Answer:**  
As engineering students, we collect notes and question papers from various subjects across WhatsApp groups, Google Drives, and download folders. Over time, these files get scattered and hard to locate before examinations. StudyMate solves this by allowing students to catalog their files by subject, semester, and topic so they can search and open them in seconds.

---

### Q3. Why did you choose Python for this project?
**Answer:**  
1. Python is beginner-friendly, clean, and readable.
2. It includes standard built-in libraries like `tkinter` for GUI and `sqlite3` for database management out-of-the-box.
3. It requires no complex compilers or external package installations.

---

### Q4. What is a GUI and why did you use Tkinter?
**Answer:**  
- **GUI (Graphical User Interface)** allows users to interact with software using visual elements like buttons, menus, windows, and input fields instead of typing commands in a terminal.
- **Tkinter** is Python's standard built-in GUI package. We also used `ttk` (themed Tkinter) to provide modern-looking buttons, comboboxes, and tables (`Treeview`).

---

### Q5. What is a Database?
**Answer:**  
A database is an organized collection of structured data stored electronically in a computer system, allowing data to be easily searched, inserted, updated, and deleted.

---

### Q6. What is SQLite and why is it used instead of MySQL or Oracle?
**Answer:**  
- SQLite is a self-contained, serverless, zero-configuration SQL database engine.
- Unlike MySQL or PostgreSQL, which require setting up a separate background server and port, SQLite stores the entire database inside a single local file (`studymate.db`).
- This makes it lightweight, portable, and ideal for a student desktop application.

---

### Q7. What does CRUD stand for, and how is it implemented in StudyMate?
**Answer:**  
CRUD stands for the four foundational database operations:
- **C - Create**: Adding a new study material using SQL `INSERT INTO`.
- **R - Read**: Displaying items on the Dashboard and searching using SQL `SELECT`.
- **U - Update**: Toggling favorite status using SQL `UPDATE`.
- **D - Delete**: Removing a record using SQL `DELETE FROM`.

---

### Q8. What is SQL?
**Answer:**  
SQL stands for **Structured Query Language**. It is the standard domain-specific language used for storing, manipulating, and retrieving data stored in relational database management systems (RDBMS).

---

### Q9. What is the SQL `LIKE` operator and how is it used in StudyMate?
**Answer:**  
The `LIKE` operator is used in a SQL `WHERE` clause to search for a specified pattern in a column.  
In StudyMate:
```sql
SELECT * FROM materials WHERE title LIKE '%DBMS%' OR subject LIKE '%DBMS%';
```
The `%` sign is a wildcard character that matches zero, one, or multiple characters. This allows partial search matches (e.g., searching "norm" matches "normalization").

---

### Q10. What is a Primary Key and why is the `id` column used?
**Answer:**  
A **Primary Key** is a column (or set of columns) that uniquely identifies each row in a database table. In our `materials` table, `id` is defined as:
```sql
id INTEGER PRIMARY KEY AUTOINCREMENT
```
It ensures every study material has a unique integer identifier, allowing us to accurately update, favorite, or delete that specific record without affecting other rows with similar names.

---

### Q11. How does StudyMate store files? Does it copy or upload them?
**Answer:**  
No, StudyMate does **not** copy, duplicate, or upload the file. It only stores the file's absolute path (e.g., `D:\College\Notes\DBMS_Unit1.pdf`) in the database. This saves disk storage space and avoids duplicate file copies.

---

### Q12. How does the application open files on the user's computer?
**Answer:**  
On Windows, we use Python's built-in `os.startfile(file_path)` function. This tells the Windows operating system to launch the file using its default registered software (for instance, Adobe Acrobat or Edge for PDFs, PowerPoint for PPTs, and Notepad for text files).

---

### Q13. What happens if a file has been moved or deleted from the hard drive?
**Answer:**  
Before attempting to open any file, StudyMate checks whether the file exists using `os.path.exists(file_path)`. If the file has been moved or deleted, it catches the condition and displays a friendly Tkinter alert:
> *"File not found. Please check whether the file has been moved or deleted."*  
This prevents the application from crashing.

---

### Q14. What happens when a user clicks "Delete Record" in StudyMate?
**Answer:**  
Deleting a record only runs a `DELETE FROM materials WHERE id = ?` SQL query on the database.  
**Crucially, it does NOT delete the physical file from the user's hard drive.** A confirmation dialog asks the user before deleting to prevent accidental loss.

---

### Q15. Why do you use parameterized queries (`?`) in your SQL code?
**Answer:**  
We write queries like:
```python
cursor.execute("SELECT * FROM materials WHERE subject = ?", (subject,))
```
Using `?` placeholders prevents **SQL Injection attacks** and automatically escapes special characters (such as quotes or apostrophes in titles), ensuring data safety and stability.

---

### Q16. What is the role of `conn.commit()` and `conn.close()`?
**Answer:**  
- `conn.commit()` saves all changes made during a transaction (such as INSERT, UPDATE, or DELETE) permanently to the database file.
- `conn.close()` closes the connection to the database file, releasing system memory and preventing file locks.

---

### Q17. How does the Favorites feature work?
**Answer:**  
Each row has a `favorite` integer column (0 for normal, 1 for favorite). When the user clicks "Toggle Favorite", StudyMate executes:
```sql
UPDATE materials SET favorite = (1 - favorite) WHERE id = ?;
```
This mathematically flips 0 to 1, and 1 to 0 in one clean SQL statement. The Favorites view simply runs `SELECT ... WHERE favorite = 1`.

---

### Q18. What is Tkinter Treeview?
**Answer:**  
`ttk.Treeview` is a Tkinter widget used to display tabular data in rows and columns with headers. In StudyMate, we use it to show columns like Title, Subject, Topic, Semester, Type, Date Added, and Favorite status, complete with vertical and horizontal scrollbars.

---

### Q19. What are the current limitations of StudyMate?
**Answer:**  
1. It is a single-user desktop application and does not support multi-user network sharing.
2. It tracks files by path; if a user manually renames or moves a folder on disk, they need to update the path.
3. It does not perform full-text search inside PDF or Word file contents.

---

### Q20. What future enhancements can be added to this project?
**Answer:**  
1. **Cloud synchronization**: Syncing study materials across devices using Google Drive or Dropbox API.
2. **In-app preview**: A built-in PDF viewer panel.
3. **Automatic tagging**: Extracting subject keywords from file names automatically.
4. **Dark Mode**: Adding a theme switcher for night-time studying.

---

### Q21. What did you personally learn by building this mini project?
**Answer:**  
1. Connecting a GUI frontend with an SQLite database backend using Python.
2. Writing SQL queries with dynamic filters and parameterized inputs.
3. Handling file system operations using Python's `os` and `pathlib` modules.
4. Building modular software with clear separation between the user interface (`ui.py`) and database logic (`database.py`).
5. Designing defensive error handling so software doesn't crash during unexpected inputs.

---

### Q22. Can you demonstrate adding, searching, and opening a study material?
**Answer:**  
*(Action on screen)*:  
1. Log in with `student` / `password123` (or create a new student account).
2. Click **➕ Add Material**, fill Title: *"Operating System Notes"*, Subject: *"OS"*, choose Sem: *"3"*, Type: *"Notes"*, choose/upload file, and click **Save**.
3. Go to **🔍 Search & Filter**, type *"OS"*, and filter by Sem *"3"*.
4. Click **📂 Open** to preview the file in the browser or native viewer.
5. Click **⭐ Toggle Favorite**, then show it appearing under the **⭐ Favorites** tab.

---

### Q23. How is user authentication implemented in StudyMate?
**Answer:**  
1. A dedicated `users` table was added to the SQLite database with columns `(id, username, password_hash, full_name, role, created_at)`.
2. When a student registers, their password is encrypted using a cryptographic one-way hash algorithm (`SHA-256`) via Python's standard `hashlib` library before saving to the database.
3. During login, the entered password is hashed with SHA-256 and compared against the stored hash in the database.
4. If the hashes match, the user is authenticated and their session profile is loaded.

---

### Q24. Why do we hash passwords using SHA-256 instead of saving them as plain text?
**Answer:**  
1. **Security & Privacy**: Storing plain text passwords is a major security vulnerability. If someone inspects the database file or dumps the database, user passwords would be exposed.
2. **One-Way Function**: Cryptographic hash functions like SHA-256 are irreversible ("one-way"). It is computationally infeasible to reverse a SHA-256 hash back to the original password.
3. **Industry Standard**: Modern software engineering standards mandate that sensitive credentials must always be hashed before persistent storage.

---

### Q25. How are SQL Injection attacks prevented during Login and Registration?
**Answer:**  
We use **parameterized queries** (using `?` placeholders in `sqlite3.Cursor.execute`).  
For example:  
```python
cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
```
This ensures user input is strictly treated as literal data rather than executable SQL commands, completely eliminating SQL injection risks.

---

### Q26. How does the Web version maintain the user's login state?
**Answer:**  
When the `/api/login` endpoint responds with a successful authentication status, the frontend stores the user's basic profile and session token in the browser's `localStorage` and receives an `HttpOnly` session cookie. When the user refreshes or revisits the page, StudyMate validates the session token against the server-side `sessions` table and restores their session without asking them to log in again until they click **Sign Out**.

---

### Q27. What is Role-Based Access Control (RBAC) and how is it implemented in StudyMate?
**Answer:**  
1. **Definition**: Role-Based Access Control restricts system access to authorized users based on their assigned role (`Student` vs. `Admin`).
2. **Implementation**:
   - The `users` table stores a `role` column.
   - On every request to an administrative endpoint (such as `/admin`, `/api/admin/files`, `/api/admin/users`), the server invokes a backend authorization check (`require_admin()`).
   - If an unauthenticated user attempts access, the server returns `HTTP 401 Unauthorized`.
   - If an authenticated student attempts access, the server returns `HTTP 403 Forbidden`.
   - Crucially, access control is enforced on the server, not just by hiding UI buttons.

---

### Q28. How does StudyMate protect against Brute-Force Password Guessing Attacks?
**Answer:**  
1. We implemented an in-memory IP rate limiter (`check_rate_limit`) on the `/api/login` endpoint.
2. If an IP address fails login 5 times within a 60-second window, the server blocks further attempts from that IP and responds with `HTTP 429 Too Many Requests`.
3. This prevents automated dictionary attacks and password guessing scripts from compromising accounts.

---

### Q29. What is a Server-Side Session Token and why is it used?
**Answer:**  
1. After a user verifies their username and password, the server generates a cryptographically random 64-character hex token using Python's `secrets.token_hex(32)`.
2. This token is saved in the `sessions` table with an expiration timestamp (`expires_at`, 7 days).
3. The client sends this token in the `Authorization: Bearer <token>` header or session cookie for subsequent requests.
4. **Benefit**: The user's actual password hash is never repeatedly transmitted across HTTP requests, and sessions can be instantly revoked from the database if an account is suspended or logged out.

---

### Q30. How does StudyMate prevent Directory Traversal / Path Traversal attacks?
**Answer:**  
1. **The Vulnerability**: An attacker might attempt to upload or rename a file with names like `../../windows/system32/cmd.exe` or `../../secret.txt` to overwrite or escape to unauthorized system folders.
2. **Our Defense**:
   - We strictly pass every uploaded or renamed filename through `os.path.basename()`, which strips any leading directory separators (`/` or `\`) or `../` patterns.
   - We strip null bytes (`\0`) and sanitize the stem to alphanumeric and safe characters.
   - We verify that all file operations resolve strictly inside the application's designated `uploads/` folder.

---

### Q31. What is the "Last Active Administrator" protection rule?
**Answer:**  
1. A common administrative flaw is an admin accidentally deleting, demoting, or suspending their own account, locking everyone out of the system.
2. In `database.py`, before any user deletion, role demotion, or account suspension, the function `count_active_admins()` checks the total number of active administrators.
3. If only 1 active administrator remains, the action is rejected with a security error:
   > *"Security restriction: Cannot demote, suspend, or delete the last active administrator."*

---

### Q32. What is the Storage Consistency Scanner?
**Answer:**  
1. In production web applications, database records and filesystem storage can become out-of-sync if files are manually deleted from disk or if an upload crashes midway.
2. The Admin Panel includes an automated storage scanner (`scan_storage_consistency`):
   - **Missing files**: Study materials present in the SQLite database whose physical files have disappeared from disk.
   - **Orphaned files**: Physical files sitting in the `uploads/` directory that have no matching record in the database.
   - **Valid files**: Files perfectly synchronized in both disk and database.
3. Administrators can run this scan on demand and clean up inconsistencies with one click.

---

### Q33. How does the File Moderation & Reporting system work?
**Answer:**  
1. When a student finds a corrupt, broken, or inappropriate study material, they can click **🚩 Report File** and provide a reason and details.
2. This creates a record in the `reports` table with status `pending`.
3. In the Admin Panel under **Reports & Moderation**, administrators can view all reported files, preview the content, quarantine the file (hiding it from students while preserving evidence), or resolve/dismiss the report with notes.
