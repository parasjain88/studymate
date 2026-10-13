# MINI PROJECT REPORT

## STUDYMATE: SMART STUDY MATERIAL MANAGEMENT AND SEARCH SYSTEM

**A Mini Project Submitted in Partial Fulfillment of the Requirements for the Degree of**  
**BACHELOR OF TECHNOLOGY (B.Tech)**  
**in**  
**COMPUTER SCIENCE AND ENGINEERING (CSE)**  
**Semester: 3rd Semester**

---

### Table of Contents
1. Title Page
2. Abstract
3. Introduction
4. Problem Statement
5. Objectives
6. Existing System vs. Proposed System
7. Proposed System Overview
8. Detailed Features
9. Technologies Used
10. System Requirements (Hardware & Software)
11. System Architecture & Flowchart
12. Database Design & Entity-Relationship Details
13. Implementation Details
14. Screenshots Placeholder & UI Flow
15. Software Testing & Verification
16. Advantages
17. Limitations
18. Future Scope
19. Conclusion
20. References

---

## 1. Title
**StudyMate: Smart Study Material Management and Search System**

---

## 2. Abstract
In higher education institutions, engineering students continually accumulate hundreds of digital educational assets—including lecture presentations, laboratory instruction manuals, syllabus copies, semester assignments, and previous years' examination papers. Managing these documents across local drives, flash memory, and social messaging downloads frequently results in disorganized file systems and substantial wasted study time prior to examinations. 

This project presents **StudyMate**, a lightweight, standalone desktop study material management and search application implemented in **Python 3**, **Tkinter**, and **SQLite3**. StudyMate indexes study materials with academic attributes (Subject, Topic, Semester, and Material Type) without duplicating physical files. It features full CRUD operations, multi-field SQL pattern searching via the `LIKE` operator, dynamic filter combinations, a one-click file launcher utilizing operating system hooks, a bookmarking ("Favorites") mechanism, and defensive error management. The project is designed with modularity and simplicity to serve as an accessible, high-utility tool for undergraduate computer science students.

---

## 3. Introduction
Modern academic learning heavily relies on digital materials. Students receive notes from faculty members in PDF, Microsoft Word, and PowerPoint formats. While modern operating systems provide native search utilities, these systems only match raw filenames and lack domain-specific academic categorization.

StudyMate bridges this gap by creating an academic layer over the user's filesystem. Students can register any file by linking its path while assigning academic context:
- Target Subject (e.g., DBMS, Operating Systems, Data Structures)
- Academic Semester (Semesters 1 through 8)
- Topic or Unit covered
- Material Classification (Notes, PPT, Lab Manual, PYQ, Assignment)

StudyMate enables instant retrieval via an intuitive graphical interface, ensuring students spend time studying rather than searching for study resources.

---

## 4. Problem Statement
Engineering students face several challenges when managing academic materials:
1. **Scattered Storage**: Files reside in disparate locations: browser download folders, Desktop shortcuts, and temporary messaging directories.
2. **Ambiguous Naming**: File titles such as `Doc1.pdf`, `Unit2_final_v3.pptx`, or `Scan_2024.pdf` do not indicate the subject or semester.
3. **Absence of Academic Metadata**: Operating system folder hierarchies do not easily support filtering across multiple dimensions simultaneously (e.g., "Show all *Semester 3* *Notes* for *DBMS*").
4. **Overly Complex Commercial Alternatives**: Commercial document management systems require cloud subscriptions, user logins, continuous internet connectivity, and heavy RAM overhead.

---

## 5. Objectives
The core objectives of the StudyMate project are:
1. **Centralization**: To provide a single dashboard interface for organizing all college study materials.
2. **Path-Based Indexing**: To record file locations in an SQLite database without duplicating physical files or consuming extra disk space.
3. **Multi-Parameter Search**: To implement flexible search functionality across Title, Subject, Topic, and Material Type using SQL `LIKE` queries.
4. **Direct File Execution**: To launch files in their default native desktop viewers with a single click.
5. **Rapid Prioritization**: To enable bookmarking of urgent materials into a dedicated "Favorites" view.
6. **Defensive Error Handling**: To prevent crashes caused by missing files, empty inputs, or deleted resources.

---

## 6. Existing System
In the existing manual approach:
- Students store files in nested folders manually created on their hard drive (e.g., `D:\Sem3\DBMS\Notes\`).
- When looking for a document, the student must manually traverse directories.
- Searching via Windows Explorer is slow because it attempts to index entire drives and cannot filter by college semester or academic material type.
- There is no mechanism to star or bookmark important files across different subject directories.

---

## 7. Proposed System
The proposed **StudyMate** system introduces:
- A clean, modern desktop GUI built with Python's `Tkinter` and `ttk`.
- A serverless, local SQLite database (`studymate.db`) requiring zero configuration.
- Direct file path referencing: original files stay in their original folders.
- Instant search queries with instant keyword matching.
- Simultaneous multi-attribute dropdown filtering (Subject, Semester, Type).
- Safe deletion that cleans database records without deleting physical files from the computer.

---

## 8. Detailed Features
1. **Interactive Dashboard**:
   - Displays real-time summary cards: Total Materials, Unique Subjects, and Starred Favorites.
   - Shows a table of recently added materials with quick-open capability.
2. **Add Material**:
   - Streamlined input form with fields for Title, Subject, Topic, Semester (1-8), and Type.
   - Native file browser (`filedialog.askopenfilename`) for easy selection.
   - Input validation to ensure required fields are provided.
3. **Search & Multi-Filter**:
   - Case-insensitive pattern matching across multiple fields using SQLite `LIKE`.
   - Combined filters for Subject, Semester, and Material Type.
4. **One-Click File Opener**:
   - Launches documents using Windows `os.startfile()`.
   - Checks file existence with `os.path.exists()` to prevent runtime errors.
5. **Favorites Management**:
   - One-click toggle between standard and starred items.
   - Dedicated view for quick access to exam materials.
6. **Demo Data Ingestion**:
   - Built-in button to populate sample academic records for live demonstrations.

---

## 9. Technologies Used
- **Python 3.13 / 3.x**: Primary programming language chosen for readability and rich standard library.
- **Tkinter & ttk**: Standard Python GUI toolkit used for desktop presentation, widgets, and layout.
- **SQLite3**: Relational database engine embedded directly into Python for serverless data persistence.
- **OS & Pathlib**: Standard Python modules for path normalization and file status checks.
- **Windows Shell Integration**: Utilizes `os.startfile()` to launch associated viewers.

---

## 10. System Requirements

### Hardware Requirements
- Processor: Dual Core 2.0 GHz or higher (Intel Core i3 / AMD Ryzen 3)
- RAM: 2 GB RAM (4 GB recommended)
- Disk Space: 50 MB for Python installation and database

### Software Requirements
- Operating System: Microsoft Windows 10 / 11
- Runtime Environment: Python 3.8 or higher
- Document Viewers: Default system viewers (Adobe Acrobat, Microsoft PowerPoint, Word, Notepad, etc.)

---

## 11. System Architecture & Flowchart

```text
+--------------------------------------------------------------------+
|                         USER INTERFACE                             |
|                           (ui.py)                                  |
|                                                                    |
|  [Dashboard View]  [Add Material]  [Search & Filter]  [Favorites]  |
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                        BUSINESS LOGIC                              |
|                          (main.py)                                 |
|  - Input Validation  - Event Handling  - File Existence Validation |
+------------------+------------------------------+------------------+
                   |                              |
                   v                              v
+------------------------------------+  +----------------------------+
|          DATABASE LAYER            |  |      OPERATING SYSTEM      |
|           (database.py)            |  |                            |
|                                    |  | - File System Verification |
|  - SQLite Connection (studymate.db)|  | - Launch via os.startfile  |
|  - Parameterized CRUD Queries      |  | - Default Applications     |
+------------------------------------+  +----------------------------+
```

### Data Flow for File Search:
1. User enters search term (e.g. `"Normalization"`) and selects Semester `"3"`.
2. UI triggers `refresh_search_table()` and calls `database.get_materials()`.
3. Parameterized SQL query executes:
   `SELECT * FROM materials WHERE (title LIKE ? OR topic LIKE ?) AND semester = ?`
4. Matching rows are returned to the UI and rendered in the `ttk.Treeview` table.
5. User double-clicks a row $\rightarrow$ system checks `os.path.exists()` $\rightarrow$ file opens in native viewer.

---

## 12. Database Design

The system uses a single relational table named `materials`.

### Data Dictionary

| Column | Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique identifier for each material |
| `title` | TEXT | NOT NULL | Title of the study material |
| `subject` | TEXT | NOT NULL | Course / subject title |
| `topic` | TEXT | NULLABLE | Chapter or topic within subject |
| `semester` | INTEGER | NOT NULL | Semester number (1 to 8) |
| `material_type` | TEXT | NOT NULL | Notes, PPT, Assignment, etc. |
| `file_path` | TEXT | NOT NULL | Absolute file location on drive |
| `date_added` | TEXT | NOT NULL | Timestamp of record creation |
| `favorite` | INTEGER | DEFAULT 0 | 1 = Favorite, 0 = Standard |

---

## 13. Implementation Details

The implementation is structured into three clean, cohesive modules:

1. **`database.py`**:
   - `get_connection()`: Provides SQLite connection handles.
   - `init_db()`: Executes `CREATE TABLE IF NOT EXISTS`.
   - `add_material()`: Inserts records using parameterized queries.
   - `get_materials()`: Dynamically builds SQL `WHERE` clauses for search and filtering.
   - `toggle_favorite()`: Uses mathematical toggling: `favorite = 1 - favorite`.
   - `delete_material()`: Executes `DELETE FROM materials WHERE id = ?`.
   - `get_dashboard_stats()`: Computes real-time aggregation counts.

2. **`ui.py`**:
   - `StudyMateApp`: Master class controlling sidebar navigation and frame swapping.
   - `build_dashboard_view()`: Constructs summary cards and recent materials table.
   - `build_add_view()`: Form interface with native file browsing dialog.
   - `build_search_view()`: Treeview table with search and dynamic dropdown filters.
   - `build_favorites_view()`: Filtered view of starred materials.
   - `open_selected_material()`: Performs safety check with `os.path.exists()` before calling `os.startfile()`.

3. **`main.py`**:
   - Entry point that initializes database tables, calculates screen center coordinates, and starts the Tkinter event loop.

---

## 14. Screenshots Section (Placeholders for Submission)

*(Include the following screenshots in your printed/submitted report)*:

- **Screenshot 1: Dashboard Overview**  
  *Shows total materials, total subjects, favorites count, and recent materials table.*

- **Screenshot 2: Add New Study Material Form**  
  *Shows input fields, dropdown menus, and the file browser button.*

- **Screenshot 3: Search & Filter Interface**  
  *Shows keyword search for "DBMS" combined with semester dropdown filtering.*

- **Screenshot 4: Favorites Window**  
  *Shows starred items with quick-open and remove buttons.*

- **Screenshot 5: Missing File Friendly Error Dialog**  
  *Shows the alert message displayed when a file has been moved or deleted.*

---

## 15. Software Testing & Verification

Comprehensive test suites were implemented and executed:

| Test ID | Test Scenario | Expected Outcome | Result |
| :--- | :--- | :--- | :--- |
| **TC-01** | Database Initialization | `studymate.db` created with correct schema | **PASS** |
| **TC-02** | Sample Data Loading | 5 demo records inserted without duplicates | **PASS** |
| **TC-03** | Dashboard Statistics | Stats return accurate counts for materials, subjects, favorites | **PASS** |
| **TC-04** | Search with `LIKE` | Keyword "DBMS" returns only matching records | **PASS** |
| **TC-05** | Multi-attribute Filter | Semester=3 and Type=Notes returns filtered items | **PASS** |
| **TC-06** | Custom Record Insertion | New material saved and assigned incremental ID | **PASS** |
| **TC-07** | Toggle Favorite | Value flips from 0 to 1 and back to 0 | **PASS** |
| **TC-08** | Delete Confirmation | Record removed from DB; physical file on disk preserved | **PASS** |
| **TC-09** | Missing File Handling | Alert displayed when file path is invalid; app does not crash | **PASS** |
| **TC-10** | GUI View Switching | All 4 views render without layout or widget errors | **PASS** |

---

## 16. Advantages
1. **Zero External Dependencies**: Uses only standard Python libraries; runs on any standard Windows PC.
2. **Saves Disk Space**: Files are referenced by path rather than copied or duplicated.
3. **Academic-Specific Categorization**: Categorizes by Semester, Subject, and Material Type.
4. **Completely Offline**: Requires no internet connection or cloud account.
5. **Beginner-Friendly Codebase**: Clean, well-commented code that is easy to explain in an academic viva.

---

## 17. Limitations
1. **Local Desktop Only**: Cannot synchronize files across different physical computers.
2. **Path Dependency**: If a user renames an external folder, the stored path must be updated.
3. **No In-File Content Search**: Searches file metadata (Title, Subject, Topic) rather than full text inside PDFs.

---

## 18. Future Scope
1. **In-App Document Viewer**: Embedded PDF rendering tab directly inside the Tkinter window.
2. **Cloud Backup Sync**: Optional export/sync to Google Drive or OneDrive.
3. **Subject-Wise Analytics**: Graphical charts showing distribution of materials across subjects.
4. **Dark Mode UI**: Theme toggle for comfortable late-night studying.

---

## 19. Conclusion
The **StudyMate** project successfully demonstrates the design and development of an educational desktop tool tailored to engineering students. By combining Python, Tkinter, and SQLite3, the project provides an efficient, lightweight solution to study material organization and search. The system satisfies all requirements of a 3rd-semester B.Tech CSE mini-project, featuring clean modularity, robust error handling, and high practical utility.

---

## 20. References
1. Python Software Foundation. *Tkinter — Python interface to Tcl/Tk*. Official Python Documentation.
2. SQLite Consortium. *SQLite Documentation & SQL Syntax Guide*. https://www.sqlite.org/docs.html
3. Mark Summerfield. *Programming in Python 3: A Complete Introduction to the Python Language*. Addison-Wesley.
4. Allen B. Downey. *Think Python: How to Think Like a Computer Scientist*. Green Tea Press.
5. GeeksforGeeks. *Python GUI — Tkinter Tutorial & SQLite3 Integration*.
