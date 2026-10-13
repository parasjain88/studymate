"""
=============================================================================
StudyMate — Smart Study Material Management and Search System
Main Application Entry Point (main.py)
=============================================================================
College Mini Project: 3rd Semester B.Tech CSE

To run the application:
    python main.py

This file initializes the SQLite database, configures the main Tkinter window,
and starts the desktop application event loop.
=============================================================================
"""

import sys
import os
import tkinter as tk
import database
from ui import StudyMateApp, LoginDialog


def center_window(window, width=1060, height=660):
    """
    Centers the Tkinter window on the user's screen for a polished appearance.
    """
    window.update_idletasks()
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    # Ensure window coordinates are not negative on smaller screens
    x = max(0, x)
    y = max(0, y)

    window.geometry(f"{width}x{height}+{x}+{y}")


def main():
    print("=" * 60)
    print(" Starting StudyMate — Smart Study Material Finder ")
    print("=" * 60)

    # Step 1: Ensure SQLite database and tables exist
    try:
        database.init_db()
        print("[OK] SQLite Database initialized: studymate.db")
    except Exception as e:
        print(f"[ERROR] Could not initialize database: {e}", file=sys.stderr)
        return

    # Step 2: Initialize Root Tkinter Window (hidden during login prompt)
    root = tk.Tk()
    root.withdraw()

    # Step 3: Prompt for Student Sign In
    login_dialog = LoginDialog(root)
    root.wait_window(login_dialog.dialog)

    if not login_dialog.authenticated_user:
        print("[INFO] Sign in cancelled. Exiting StudyMate.")
        root.destroy()
        return

    user = login_dialog.authenticated_user
    print(f"[OK] Authenticated user: {user['full_name']} (@{user['username']})")

    # Step 4: Show and Center Main Application Window
    root.deiconify()
    center_window(root, width=1060, height=660)

    # Step 5: Launch Main Application with Active User Profile
    app = StudyMateApp(root, current_user=user)
    print("[OK] StudyMate GUI launched successfully.")

    # Step 6: Start Tkinter Event Loop
    root.mainloop()
    print("[INFO] StudyMate closed.")



if __name__ == "__main__":
    main()
