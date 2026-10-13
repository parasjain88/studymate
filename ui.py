"""
=============================================================================
StudyMate — Smart Study Material Management and Search System
Graphical User Interface (ui.py)
=============================================================================
This module creates the desktop GUI using Python's built-in Tkinter and ttk.
Features implemented:
- Modern Sidebar navigation (Dashboard, Add Material, Search, Favorites)
- Interactive Dashboard with statistics cards and recently added items
- Add Material form with validation and native file browser
- Powerful search & multi-field filter combining Subject, Semester, and Type
- Treeview table with double-click-to-open and action buttons
- Safe file opening with os.startfile() and missing file error handling
- Confirmation dialog before deleting records
=============================================================================
"""

import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import database

# Primary color scheme
COLOR_PRIMARY = "#2563eb"       # Blue accent
COLOR_PRIMARY_DARK = "#1d4ed8"  # Darker blue for button hover
COLOR_BG = "#f8fafc"            # Light grey/blue background
COLOR_SIDEBAR = "#1e293b"       # Dark slate sidebar
COLOR_SIDEBAR_BTN = "#334155"   # Sidebar button background
COLOR_SIDEBAR_ACTIVE = "#2563eb"# Active sidebar button
COLOR_CARD_BG = "#ffffff"       # White for cards and containers
COLOR_TEXT = "#0f172a"          # Dark text
COLOR_TEXT_MUTED = "#64748b"    # Subdued grey text
COLOR_BORDER = "#e2e8f0"        # Light border

# Default dropdown choices
MATERIAL_TYPES = [
    "Notes",
    "Previous Year Paper",
    "Assignment",
    "PPT",
    "Book",
    "Lab Manual",
    "Other"
]

SEMESTERS = ["1", "2", "3", "4", "5", "6", "7", "8"]


class StudyMateApp:
    def __init__(self, root, current_user=None):
        self.root = root
        self.current_user = current_user
        self.root.title("StudyMate — Smart Study Material Finder")
        self.root.geometry("1060x660")
        self.root.minsize(920, 560)
        self.root.configure(bg=COLOR_BG)

        # Configure ttk styles for a clean, cohesive design
        self.setup_styles()

        # Build Main Layout: Left Sidebar + Right Content Area
        self.create_layout()

        # Start on the Dashboard
        self.show_view("dashboard")

    # -------------------------------------------------------------------------
    # Styling Configuration
    # -------------------------------------------------------------------------
    def setup_styles(self):
        style = ttk.Style()
        # Use 'clam' theme as base because it allows cross-platform custom colors
        if "clam" in style.theme_names():
            style.theme_use("clam")

        # Treeview (table) styling
        style.configure(
            "Treeview",
            background="#ffffff",
            foreground=COLOR_TEXT,
            rowheight=28,
            fieldbackground="#ffffff",
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#e2e8f0",
            foreground=COLOR_TEXT,
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        style.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", "#1e3a8a")])
        style.map("Treeview.Heading", background=[("active", "#cbd5e1")])

        # Combobox styling
        style.configure("TCombobox", padding=4, font=("Segoe UI", 10))

    # -------------------------------------------------------------------------
    # Master Layout (Sidebar + Content Container)
    # -------------------------------------------------------------------------
    def create_layout(self):
        # 1. Left Sidebar
        self.sidebar = tk.Frame(self.root, bg=COLOR_SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # App Brand Header in Sidebar
        brand_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR, pady=16)
        brand_frame.pack(fill="x")

        lbl_logo = tk.Label(
            brand_frame,
            text="📚 StudyMate",
            font=("Segoe UI", 16, "bold"),
            fg="#ffffff",
            bg=COLOR_SIDEBAR
        )
        lbl_logo.pack()

        lbl_sub = tk.Label(
            brand_frame,
            text="Study Material Finder",
            font=("Segoe UI", 9),
            fg="#94a3b8",
            bg=COLOR_SIDEBAR
        )
        lbl_sub.pack(pady=(2, 0))

        # Active User Badge
        if self.current_user:
            user_badge = tk.Frame(self.sidebar, bg="#0f172a", padx=10, pady=8)
            user_badge.pack(fill="x", padx=12, pady=(0, 12))
            lbl_uname = tk.Label(
                user_badge,
                text=f"👤 {self.current_user.get('full_name', 'Student')}",
                font=("Segoe UI", 9, "bold"),
                fg="#ffffff",
                bg="#0f172a",
                anchor="w"
            )
            lbl_uname.pack(fill="x")
            lbl_urole = tk.Label(
                user_badge,
                text=f"@{self.current_user.get('username', 'user')} • {self.current_user.get('role', 'Student')}",
                font=("Segoe UI", 8),
                fg="#38bdf8",
                bg="#0f172a",
                anchor="w"
            )
            lbl_urole.pack(fill="x")

        # Divider line
        tk.Frame(self.sidebar, bg="#334155", height=1).pack(fill="x", padx=15, pady=(0, 15))


        # Navigation Buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "🏠  Dashboard"),
            ("add", "➕  Add Material"),
            ("search", "🔍  Search & Filter"),
            ("favorites", "⭐  Favorites"),
        ]

        for view_key, label_text in nav_items:
            btn = tk.Button(
                self.sidebar,
                text=label_text,
                font=("Segoe UI", 11),
                fg="#f8fafc",
                bg=COLOR_SIDEBAR_BTN,
                activebackground=COLOR_PRIMARY,
                activeforeground="#ffffff",
                relief="flat",
                anchor="w",
                padx=18,
                pady=10,
                cursor="hand2",
                command=lambda k=view_key: self.show_view(k)
            )
            btn.pack(fill="x", padx=12, pady=4)
            self.nav_buttons[view_key] = btn


        # Footer in Sidebar
        footer_frame = tk.Frame(self.sidebar, bg=COLOR_SIDEBAR)
        footer_frame.pack(side="bottom", fill="x", pady=15, padx=12)
        tk.Label(
            footer_frame,
            text="B.Tech CSE Mini Project\n3rd Semester",
            font=("Segoe UI", 8),
            fg="#64748b",
            bg=COLOR_SIDEBAR,
            justify="center"
        ).pack()

        # 2. Right Main Content Area
        self.main_container = tk.Frame(self.root, bg=COLOR_BG)
        self.main_container.pack(side="right", fill="both", expand=True)

        # Dictionary to store view frame references
        self.views = {}

        # Initialize all views
        self.views["dashboard"] = self.build_dashboard_view()
        self.views["add"] = self.build_add_view()
        self.views["search"] = self.build_search_view()
        self.views["favorites"] = self.build_favorites_view()

    def show_view(self, view_key):
        """Switches visible frame to the requested view and updates active button."""
        for key, frame in self.views.items():
            frame.pack_forget()

        # Update sidebar button highlight
        for key, btn in self.nav_buttons.items():
            if key == view_key:
                btn.configure(bg=COLOR_SIDEBAR_ACTIVE, font=("Segoe UI", 11, "bold"))
            else:
                btn.configure(bg=COLOR_SIDEBAR_BTN, font=("Segoe UI", 11))

        # Show the chosen view frame
        self.views[view_key].pack(fill="both", expand=True, padx=20, pady=20)

        # Refresh data on view switch
        if view_key == "dashboard":
            self.refresh_dashboard()
        elif view_key == "search":
            self.refresh_search_table()
        elif view_key == "favorites":
            self.refresh_favorites_table()
        elif view_key == "add":
            self.update_add_view_subject_history()

    # -------------------------------------------------------------------------
    # VIEW 1: Dashboard
    # -------------------------------------------------------------------------
    def build_dashboard_view(self):
        view = tk.Frame(self.main_container, bg=COLOR_BG)

        # Header Title
        lbl_header = tk.Label(
            view,
            text="Dashboard Overview",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_BG
        )
        lbl_header.pack(anchor="w", pady=(0, 15))

        # Stats Cards Row
        cards_frame = tk.Frame(view, bg=COLOR_BG)
        cards_frame.pack(fill="x", pady=(0, 20))

        # Card 1: Total Materials
        self.card_total_mat, self.lbl_count_mat = self.create_stat_card(
            cards_frame, "Total Materials", "0", "#3b82f6"
        )
        self.card_total_mat.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Card 2: Total Subjects
        self.card_total_subj, self.lbl_count_subj = self.create_stat_card(
            cards_frame, "Total Subjects", "0", "#10b981"
        )
        self.card_total_subj.pack(side="left", fill="both", expand=True, padx=10)

        # Card 3: Total Favorites
        self.card_total_fav, self.lbl_count_fav = self.create_stat_card(
            cards_frame, "Favorite Materials", "0", "#f59e0b"
        )
        self.card_total_fav.pack(side="left", fill="both", expand=True, padx=(10, 0))

        # Quick Actions & Recent Materials Section
        recent_section = tk.LabelFrame(
            view,
            text=" 🕒 Recently Added Materials ",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG,
            padx=15,
            pady=12,
            relief="groove"
        )
        recent_section.pack(fill="both", expand=True)

        # Table for Recent Materials
        columns = ("id", "title", "subject", "semester", "type", "date")
        self.recent_tree = ttk.Treeview(
            recent_section,
            columns=columns,
            show="headings",
            selectmode="browse",
            height=8
        )
        self.recent_tree.heading("id", text="ID")
        self.recent_tree.heading("title", text="Material Title")
        self.recent_tree.heading("subject", text="Subject")
        self.recent_tree.heading("semester", text="Sem")
        self.recent_tree.heading("type", text="Type")
        self.recent_tree.heading("date", text="Date Added")

        self.recent_tree.column("id", width=40, anchor="center")
        self.recent_tree.column("title", width=260, anchor="w")
        self.recent_tree.column("subject", width=140, anchor="w")
        self.recent_tree.column("semester", width=50, anchor="center")
        self.recent_tree.column("type", width=110, anchor="center")
        self.recent_tree.column("date", width=140, anchor="center")

        # Scrollbar for recent table
        recent_scroll = ttk.Scrollbar(recent_section, orient="vertical", command=self.recent_tree.yview)
        self.recent_tree.configure(yscrollcommand=recent_scroll.set)

        self.recent_tree.pack(side="top", fill="both", expand=True)
        recent_scroll.pack(side="right", fill="y")

        # Double click to open
        self.recent_tree.bind("<Double-1>", lambda event: self.open_selected_material(self.recent_tree))

        # Bottom buttons for Dashboard
        dash_btn_bar = tk.Frame(recent_section, bg=COLOR_CARD_BG, pady=10)
        dash_btn_bar.pack(fill="x")

        btn_open = tk.Button(
            dash_btn_bar,
            text="📂  Open Selected File",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PRIMARY,
            fg="#ffffff",
            activebackground=COLOR_PRIMARY_DARK,
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self.open_selected_material(self.recent_tree)
        )
        btn_open.pack(side="left", padx=(0, 10))

        btn_go_add = tk.Button(
            dash_btn_bar,
            text="➕  Add New Material",
            font=("Segoe UI", 10),
            bg="#f1f5f9",
            fg=COLOR_TEXT,
            relief="solid",
            bd=1,
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self.show_view("add")
        )
        btn_go_add.pack(side="left")

        return view

    def create_stat_card(self, parent, title, initial_value, accent_color):
        """Helper to create a modern statistical card widget."""
        card = tk.Frame(parent, bg=COLOR_CARD_BG, relief="solid", bd=1, padx=16, pady=12)

        # Color bar indicator on top
        color_bar = tk.Frame(card, bg=accent_color, height=3)
        color_bar.pack(fill="x", pady=(0, 8))

        lbl_title = tk.Label(
            card,
            text=title,
            font=("Segoe UI", 10),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG
        )
        lbl_title.pack(anchor="w")

        lbl_value = tk.Label(
            card,
            text=initial_value,
            font=("Segoe UI", 22, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        )
        lbl_value.pack(anchor="w")

        return card, lbl_value

    def refresh_dashboard(self):
        """Updates dashboard cards and the recent materials table."""
        stats = database.get_dashboard_stats()
        self.lbl_count_mat.config(text=str(stats["total_materials"]))
        self.lbl_count_subj.config(text=str(stats["total_subjects"]))
        self.lbl_count_fav.config(text=str(stats["total_favorites"]))

        # Clear and repopulate recent materials
        for item in self.recent_tree.get_children():
            self.recent_tree.delete(item)

        recents = database.get_recent_materials(limit=8)
        for row in recents:
            # row: (id, title, subject, topic, semester, material_type, file_path, date_added, favorite)
            self.recent_tree.insert(
                "",
                "end",
                values=(row[0], row[1], row[2], row[4], row[5], row[7]),
                tags=(str(row[0]),)
            )

    # -------------------------------------------------------------------------
    # VIEW 2: Add Study Material
    # -------------------------------------------------------------------------
    def build_add_view(self):
        view = tk.Frame(self.main_container, bg=COLOR_BG)

        # Header Title
        lbl_header = tk.Label(
            view,
            text="Add New Study Material",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_BG
        )
        lbl_header.pack(anchor="w", pady=(0, 15))

        # Form Container Frame
        form_card = tk.LabelFrame(
            view,
            text=" Material Details ",
            font=("Segoe UI", 11, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG,
            padx=25,
            pady=20,
            relief="groove"
        )
        form_card.pack(fill="both", expand=True)

        # Grid configuration
        form_card.columnconfigure(1, weight=1)

        # Field 1: Material Title
        tk.Label(
            form_card,
            text="Material Title * :",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).grid(row=0, column=0, sticky="w", pady=10, padx=(0, 15))

        self.entry_title = ttk.Entry(form_card, font=("Segoe UI", 10))
        self.entry_title.grid(row=0, column=1, columnspan=2, sticky="ew", pady=10)

        # Field 2: Subject (Entry with history / combobox)
        tk.Label(
            form_card,
            text="Subject * :",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).grid(row=1, column=0, sticky="w", pady=10, padx=(0, 15))

        self.combo_add_subject = ttk.Combobox(form_card, font=("Segoe UI", 10))
        self.combo_add_subject.grid(row=1, column=1, columnspan=2, sticky="ew", pady=10)

        # Field 3: Topic / Unit (Optional)
        tk.Label(
            form_card,
            text="Topic / Unit :",
            font=("Segoe UI", 10),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).grid(row=2, column=0, sticky="w", pady=10, padx=(0, 15))

        self.entry_topic = ttk.Entry(form_card, font=("Segoe UI", 10))
        self.entry_topic.grid(row=2, column=1, columnspan=2, sticky="ew", pady=10)

        # Field 4: Semester (Dropdown 1-8)
        tk.Label(
            form_card,
            text="Semester * :",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).grid(row=3, column=0, sticky="w", pady=10, padx=(0, 15))

        self.combo_semester = ttk.Combobox(
            form_card,
            values=SEMESTERS,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.combo_semester.current(2)  # Default: 3rd Semester
        self.combo_semester.grid(row=3, column=1, sticky="w", pady=10)

        # Field 5: Material Type (Dropdown)
        tk.Label(
            form_card,
            text="Material Type * :",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).grid(row=4, column=0, sticky="w", pady=10, padx=(0, 15))

        self.combo_type = ttk.Combobox(
            form_card,
            values=MATERIAL_TYPES,
            state="readonly",
            font=("Segoe UI", 10)
        )
        self.combo_type.current(0)  # Default: Notes
        self.combo_type.grid(row=4, column=1, sticky="w", pady=10)

        # Field 6: Select File
        tk.Label(
            form_card,
            text="Select File * :",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).grid(row=5, column=0, sticky="w", pady=10, padx=(0, 15))

        self.entry_filepath = ttk.Entry(form_card, font=("Segoe UI", 10))
        self.entry_filepath.grid(row=5, column=1, sticky="ew", pady=10)

        btn_browse = tk.Button(
            form_card,
            text="📂 Browse File...",
            font=("Segoe UI", 9, "bold"),
            bg="#f1f5f9",
            fg=COLOR_TEXT,
            relief="solid",
            bd=1,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.browse_file
        )
        btn_browse.grid(row=5, column=2, padx=(10, 0), pady=10)

        # Buttons Row (Save & Clear)
        btn_container = tk.Frame(form_card, bg=COLOR_CARD_BG)
        btn_container.grid(row=6, column=1, sticky="w", pady=(20, 0))

        btn_save = tk.Button(
            btn_container,
            text="💾  Save Study Material",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PRIMARY,
            fg="#ffffff",
            activebackground=COLOR_PRIMARY_DARK,
            activeforeground="#ffffff",
            relief="flat",
            padx=18,
            pady=8,
            cursor="hand2",
            command=self.handle_save_material
        )
        btn_save.pack(side="left", padx=(0, 10))

        btn_clear = tk.Button(
            btn_container,
            text="🔄  Clear Fields",
            font=("Segoe UI", 10),
            bg="#f1f5f9",
            fg=COLOR_TEXT,
            relief="solid",
            bd=1,
            padx=14,
            pady=8,
            cursor="hand2",
            command=self.clear_add_form
        )
        btn_clear.pack(side="left")

        return view

    def browse_file(self):
        """Opens native file picker to choose study material."""
        file_selected = filedialog.askopenfilename(
            title="Select Study Material File",
            filetypes=[
                ("All Supported Files", "*.pdf;*.ppt;*.pptx;*.doc;*.docx;*.txt;*.zip;*.png;*.jpg"),
                ("PDF Documents", "*.pdf"),
                ("Presentations", "*.ppt;*.pptx"),
                ("Word Documents", "*.doc;*.docx"),
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        if file_selected:
            # Replace forward slashes with OS-standard path format
            normalized_path = os.path.normpath(file_selected)
            self.entry_filepath.delete(0, tk.END)
            self.entry_filepath.insert(0, normalized_path)

            # Auto-suggest Title if empty
            if not self.entry_title.get().strip():
                base_name = os.path.splitext(os.path.basename(normalized_path))[0]
                # Replace underscores/hyphens with spaces for readability
                suggested_title = base_name.replace("_", " ").replace("-", " ")
                self.entry_title.insert(0, suggested_title)

    def handle_save_material(self):
        """Validates input fields and saves new record into SQLite."""
        title = self.entry_title.get().strip()
        subject = self.combo_add_subject.get().strip()
        topic = self.entry_topic.get().strip()
        semester = self.combo_semester.get().strip()
        material_type = self.combo_type.get().strip()
        file_path = self.entry_filepath.get().strip()

        # Validation Rule 1: Title required
        if not title:
            messagebox.showwarning("Validation Error", "Please enter material title.")
            self.entry_title.focus_set()
            return

        # Validation Rule 2: Subject required
        if not subject:
            messagebox.showwarning("Validation Error", "Please select or enter a subject.")
            self.combo_add_subject.focus_set()
            return

        # Validation Rule 3: File required
        if not file_path:
            messagebox.showwarning("Validation Error", "Please select a file.")
            return

        # Save to database
        try:
            database.add_material(
                title=title,
                subject=subject,
                topic=topic,
                semester=semester,
                material_type=material_type,
                file_path=file_path
            )
            messagebox.showinfo("Success", f"Study material '{title}' saved successfully!")
            self.clear_add_form()
            # Navigate to search page so student sees the newly added item
            self.show_view("search")
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to save material:\n{str(e)}")

    def clear_add_form(self):
        """Resets the Add Material form fields."""
        self.entry_title.delete(0, tk.END)
        self.combo_add_subject.set("")
        self.entry_topic.delete(0, tk.END)
        self.combo_semester.current(2)  # Default back to 3
        self.combo_type.current(0)      # Default back to Notes
        self.entry_filepath.delete(0, tk.END)

    def update_add_view_subject_history(self):
        """Loads available subjects into the Add Material subject combobox."""
        subjects = database.get_all_subjects()
        self.combo_add_subject["values"] = subjects

    # -------------------------------------------------------------------------
    # VIEW 3: Search & Filter Materials
    # -------------------------------------------------------------------------
    def build_search_view(self):
        view = tk.Frame(self.main_container, bg=COLOR_BG)

        # Header Title
        lbl_header = tk.Label(
            view,
            text="Search & Filter Materials",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_BG
        )
        lbl_header.pack(anchor="w", pady=(0, 10))

        # Filter Control Panel
        filter_card = tk.LabelFrame(
            view,
            text=" Search & Filter Options ",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG,
            padx=15,
            pady=12,
            relief="groove"
        )
        filter_card.pack(fill="x", pady=(0, 12))

        # Row 1: Search Entry + Buttons
        search_row = tk.Frame(filter_card, bg=COLOR_CARD_BG)
        search_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            search_row,
            text="Search:",
            font=("Segoe UI", 10, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).pack(side="left", padx=(0, 8))

        self.entry_search = ttk.Entry(search_row, font=("Segoe UI", 10), width=35)
        self.entry_search.pack(side="left", fill="x", expand=True, padx=(0, 10))
        # Trigger search on Enter key
        self.entry_search.bind("<Return>", lambda event: self.refresh_search_table())

        btn_search = tk.Button(
            search_row,
            text="🔍 Search",
            font=("Segoe UI", 9, "bold"),
            bg=COLOR_PRIMARY,
            fg="#ffffff",
            activebackground=COLOR_PRIMARY_DARK,
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=4,
            cursor="hand2",
            command=self.refresh_search_table
        )
        btn_search.pack(side="left", padx=(0, 6))

        btn_reset = tk.Button(
            search_row,
            text="🔄 Reset Filters",
            font=("Segoe UI", 9),
            bg="#f1f5f9",
            fg=COLOR_TEXT,
            relief="solid",
            bd=1,
            padx=12,
            pady=4,
            cursor="hand2",
            command=self.reset_search_filters
        )
        btn_reset.pack(side="left")

        # Row 2: Dropdown Filters (Subject, Semester, Material Type)
        drop_row = tk.Frame(filter_card, bg=COLOR_CARD_BG)
        drop_row.pack(fill="x")

        # Subject Filter
        tk.Label(
            drop_row,
            text="Subject:",
            font=("Segoe UI", 9),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).pack(side="left", padx=(0, 5))

        self.combo_filter_subject = ttk.Combobox(drop_row, width=15, state="readonly")
        self.combo_filter_subject.pack(side="left", padx=(0, 15))
        self.combo_filter_subject.bind("<<ComboboxSelected>>", lambda e: self.refresh_search_table())

        # Semester Filter
        tk.Label(
            drop_row,
            text="Semester:",
            font=("Segoe UI", 9),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).pack(side="left", padx=(0, 5))

        self.combo_filter_sem = ttk.Combobox(
            drop_row,
            values=["All"] + SEMESTERS,
            width=8,
            state="readonly"
        )
        self.combo_filter_sem.current(0)
        self.combo_filter_sem.pack(side="left", padx=(0, 15))
        self.combo_filter_sem.bind("<<ComboboxSelected>>", lambda e: self.refresh_search_table())

        # Material Type Filter
        tk.Label(
            drop_row,
            text="Type:",
            font=("Segoe UI", 9),
            fg=COLOR_TEXT,
            bg=COLOR_CARD_BG
        ).pack(side="left", padx=(0, 5))

        self.combo_filter_type = ttk.Combobox(
            drop_row,
            values=["All"] + MATERIAL_TYPES,
            width=16,
            state="readonly"
        )
        self.combo_filter_type.current(0)
        self.combo_filter_type.pack(side="left", padx=(0, 10))
        self.combo_filter_type.bind("<<ComboboxSelected>>", lambda e: self.refresh_search_table())

        # Results Count Label
        self.lbl_search_count = tk.Label(
            drop_row,
            text="0 items found",
            font=("Segoe UI", 9, "italic"),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_CARD_BG
        )
        self.lbl_search_count.pack(side="right")

        # Table Container
        table_frame = tk.Frame(view, bg=COLOR_BG)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "title", "subject", "topic", "sem", "type", "date", "favorite")
        self.search_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.search_tree.heading("id", text="ID")
        self.search_tree.heading("title", text="Title")
        self.search_tree.heading("subject", text="Subject")
        self.search_tree.heading("topic", text="Topic")
        self.search_tree.heading("sem", text="Sem")
        self.search_tree.heading("type", text="Type")
        self.search_tree.heading("date", text="Date Added")
        self.search_tree.heading("favorite", text="Fav")

        self.search_tree.column("id", width=35, anchor="center")
        self.search_tree.column("title", width=220, anchor="w")
        self.search_tree.column("subject", width=120, anchor="w")
        self.search_tree.column("topic", width=140, anchor="w")
        self.search_tree.column("sem", width=45, anchor="center")
        self.search_tree.column("type", width=100, anchor="center")
        self.search_tree.column("date", width=120, anchor="center")
        self.search_tree.column("favorite", width=45, anchor="center")

        # Scrollbars
        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.search_tree.yview)
        h_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.search_tree.xview)
        self.search_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        self.search_tree.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")

        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Double click to open
        self.search_tree.bind("<Double-1>", lambda event: self.open_selected_material(self.search_tree))

        # Bottom Action Bar
        action_bar = tk.Frame(view, bg=COLOR_BG, pady=10)
        action_bar.pack(fill="x")

        btn_open = tk.Button(
            action_bar,
            text="📂  Open File",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PRIMARY,
            fg="#ffffff",
            activebackground=COLOR_PRIMARY_DARK,
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self.open_selected_material(self.search_tree)
        )
        btn_open.pack(side="left", padx=(0, 10))

        btn_fav = tk.Button(
            action_bar,
            text="⭐  Toggle Favorite",
            font=("Segoe UI", 10),
            bg="#fef3c7",
            fg="#92400e",
            relief="solid",
            bd=1,
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self.handle_toggle_favorite(self.search_tree)
        )
        btn_fav.pack(side="left", padx=(0, 10))


        btn_refresh = tk.Button(
            action_bar,
            text="🔄  Refresh",
            font=("Segoe UI", 10),
            bg="#f1f5f9",
            fg=COLOR_TEXT,
            relief="solid",
            bd=1,
            padx=12,
            pady=6,
            cursor="hand2",
            command=self.refresh_search_table
        )
        btn_refresh.pack(side="right")

        return view

    def reset_search_filters(self):
        """Clears search text and resets dropdown filters to All."""
        self.entry_search.delete(0, tk.END)
        self.combo_filter_sem.current(0)
        self.combo_filter_type.current(0)
        self.update_search_subject_dropdown()
        self.combo_filter_subject.current(0)
        self.refresh_search_table()

    def update_search_subject_dropdown(self):
        """Refreshes the Subject dropdown options in Search view."""
        subjects = database.get_all_subjects()
        options = ["All"] + subjects
        self.combo_filter_subject["values"] = options
        if not self.combo_filter_subject.get() or self.combo_filter_subject.get() not in options:
            self.combo_filter_subject.current(0)

    def refresh_search_table(self):
        """Queries SQLite with current search and filter selections and populates Treeview."""
        # Update subject options in dropdown
        self.update_search_subject_dropdown()

        query = self.entry_search.get().strip()
        subj = self.combo_filter_subject.get() or "All"
        sem = self.combo_filter_sem.get() or "All"
        m_type = self.combo_filter_type.get() or "All"

        # Clear existing items
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        rows = database.get_materials(
            search_query=query,
            subject=subj,
            semester=sem,
            material_type=m_type,
            only_favorites=False
        )

        for r in rows:
            # r: (id, title, subject, topic, semester, material_type, file_path, date_added, favorite)
            fav_icon = "⭐" if r[8] == 1 else "—"
            self.search_tree.insert(
                "",
                "end",
                values=(r[0], r[1], r[2], r[3] or "—", r[4], r[5], r[7], fav_icon)
            )

        self.lbl_search_count.config(text=f"{len(rows)} item(s) found")

    # -------------------------------------------------------------------------
    # VIEW 4: Favorites
    # -------------------------------------------------------------------------
    def build_favorites_view(self):
        view = tk.Frame(self.main_container, bg=COLOR_BG)

        # Header Title
        lbl_header = tk.Label(
            view,
            text="⭐ Favorite Study Materials",
            font=("Segoe UI", 18, "bold"),
            fg=COLOR_TEXT,
            bg=COLOR_BG
        )
        lbl_header.pack(anchor="w", pady=(0, 10))

        lbl_desc = tk.Label(
            view,
            text="Quickly access your starred study materials, important questions, and exam notes.",
            font=("Segoe UI", 10),
            fg=COLOR_TEXT_MUTED,
            bg=COLOR_BG
        )
        lbl_desc.pack(anchor="w", pady=(0, 15))

        # Favorites Table Container
        table_frame = tk.Frame(view, bg=COLOR_BG)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "title", "subject", "topic", "sem", "type", "date")
        self.fav_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )

        self.fav_tree.heading("id", text="ID")
        self.fav_tree.heading("title", text="Title")
        self.fav_tree.heading("subject", text="Subject")
        self.fav_tree.heading("topic", text="Topic")
        self.fav_tree.heading("sem", text="Sem")
        self.fav_tree.heading("type", text="Type")
        self.fav_tree.heading("date", text="Date Added")

        self.fav_tree.column("id", width=35, anchor="center")
        self.fav_tree.column("title", width=240, anchor="w")
        self.fav_tree.column("subject", width=130, anchor="w")
        self.fav_tree.column("topic", width=150, anchor="w")
        self.fav_tree.column("sem", width=45, anchor="center")
        self.fav_tree.column("type", width=110, anchor="center")
        self.fav_tree.column("date", width=130, anchor="center")

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.fav_tree.yview)
        self.fav_tree.configure(yscrollcommand=v_scroll.set)

        self.fav_tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        # Double click to open
        self.fav_tree.bind("<Double-1>", lambda event: self.open_selected_material(self.fav_tree))

        # Action Buttons
        action_bar = tk.Frame(view, bg=COLOR_BG, pady=12)
        action_bar.pack(fill="x")

        btn_open = tk.Button(
            action_bar,
            text="📂  Open File",
            font=("Segoe UI", 10, "bold"),
            bg=COLOR_PRIMARY,
            fg="#ffffff",
            activebackground=COLOR_PRIMARY_DARK,
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self.open_selected_material(self.fav_tree)
        )
        btn_open.pack(side="left", padx=(0, 10))

        btn_remove_fav = tk.Button(
            action_bar,
            text="❌  Remove from Favorites",
            font=("Segoe UI", 10),
            bg="#fef3c7",
            fg="#92400e",
            relief="solid",
            bd=1,
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self.handle_toggle_favorite(self.fav_tree)
        )
        btn_remove_fav.pack(side="left", padx=(0, 10))

        return view

    def refresh_favorites_table(self):
        """Loads only favorited materials into the Favorites Treeview."""
        for item in self.fav_tree.get_children():
            self.fav_tree.delete(item)

        fav_rows = database.get_materials(only_favorites=True)
        for r in fav_rows:
            self.fav_tree.insert(
                "",
                "end",
                values=(r[0], r[1], r[2], r[3] or "—", r[4], r[5], r[7])
            )

    # -------------------------------------------------------------------------
    # Actions (Open File, Toggle Favorite)
    # -------------------------------------------------------------------------
    def open_selected_material(self, tree):
        """
        Retrieves the selected material's file path from database,
        checks if the file exists on the computer, and launches it using
        the default Windows program (via os.startfile).
        """
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showinfo("Select Material", "Please select a material from the table first.")
            return

        item_values = tree.item(selected_item[0], "values")
        material_id = item_values[0]

        record = database.get_material_by_id(material_id)
        if not record:
            messagebox.showerror("Error", "Material record could not be found.")
            return

        file_path = record[6]  # Index 6 corresponds to file_path

        # Feature 6 & Error Handling: Verify file existence before opening
        if not os.path.exists(file_path):
            messagebox.showerror(
                "File Not Found",
                "File not found. Please check whether the file has been moved or deleted.\n\n"
                f"Path: {file_path}"
            )
            return

        try:
            # On Windows, os.startfile() opens any file with its default registered program
            if hasattr(os, "startfile"):
                os.startfile(file_path)
            else:
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(file_path)}")
        except Exception as e:
            messagebox.showerror("Open Error", f"Could not open file:\n{str(e)}")

    def handle_toggle_favorite(self, tree):
        """Toggles the favorite state of the selected row."""
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showinfo("Select Material", "Please select a material from the table first.")
            return

        material_id = tree.item(selected_item[0], "values")[0]
        new_status = database.toggle_favorite(material_id)

        status_text = "added to" if new_status == 1 else "removed from"
        # Refresh current view
        if tree == self.search_tree:
            self.refresh_search_table()
        elif tree == self.fav_tree:
            self.refresh_favorites_table()


# -----------------------------------------------------------------------------
# Desktop Login & Registration Dialog
# -----------------------------------------------------------------------------
class LoginDialog:
    def __init__(self, parent):
        self.parent = parent
        self.authenticated_user = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("StudyMate — Student Sign In")
        self.dialog.geometry("420x460")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg="#0f172a")

        # Center dialog
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - 210
        y = (self.dialog.winfo_screenheight() // 2) - 230
        self.dialog.geometry(f"+{max(0, x)}+{max(0, y)}")

        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.build_ui()

    def build_ui(self):
        # Header
        hdr_frame = tk.Frame(self.dialog, bg="#0f172a", pady=15)
        hdr_frame.pack(fill="x")
        tk.Label(hdr_frame, text="📚 StudyMate", font=("Segoe UI", 18, "bold"), fg="#ffffff", bg="#0f172a").pack()
        tk.Label(hdr_frame, text="Student Portal Sign In", font=("Segoe UI", 10), fg="#94a3b8", bg="#0f172a").pack(pady=(2, 0))

        # Main Card
        self.card = tk.Frame(self.dialog, bg="#ffffff", padx=25, pady=20)
        self.card.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Mode Title
        self.lbl_mode = tk.Label(self.card, text="Sign In to Your Account", font=("Segoe UI", 12, "bold"), fg="#0f172a", bg="#ffffff")
        self.lbl_mode.pack(anchor="w", pady=(0, 15))

        # Username
        tk.Label(self.card, text="Username *", font=("Segoe UI", 9, "bold"), fg="#334155", bg="#ffffff").pack(anchor="w")
        self.entry_username = ttk.Entry(self.card, font=("Segoe UI", 10))
        self.entry_username.pack(fill="x", pady=(4, 12))
        self.entry_username.insert(0, "PARAS JAIN")

        # Password
        tk.Label(self.card, text="Password *", font=("Segoe UI", 9, "bold"), fg="#334155", bg="#ffffff").pack(anchor="w")
        self.entry_password = ttk.Entry(self.card, font=("Segoe UI", 10), show="•")
        self.entry_password.pack(fill="x", pady=(4, 15))
        self.entry_password.insert(0, "Paras@123")
        self.entry_password.bind("<Return>", lambda e: self.handle_submit())

        # Submit Button
        self.btn_submit = tk.Button(
            self.card,
            text="Sign In 🚀",
            font=("Segoe UI", 10, "bold"),
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            activeforeground="#ffffff",
            relief="flat",
            pady=8,
            cursor="hand2",
            command=self.handle_submit
        )
        self.btn_submit.pack(fill="x", pady=(5, 10))

        # Demo Helper
        lbl_hint = tk.Label(
            self.card,
            text="💡 Quick Demo: Click here to auto-fill PARAS JAIN / Paras@123",
            font=("Segoe UI", 8, "italic"),
            fg="#1e40af",
            bg="#eff6ff",
            cursor="hand2",
            padx=8,
            pady=8
        )
        lbl_hint.pack(fill="x", pady=(10, 0))
        lbl_hint.bind("<Button-1>", lambda e: self.fill_demo())

    def fill_demo(self):
        self.entry_username.delete(0, tk.END)
        self.entry_username.insert(0, "PARAS JAIN")
        self.entry_password.delete(0, tk.END)
        self.entry_password.insert(0, "Paras@123")

    def handle_submit(self):
        u = self.entry_username.get().strip()
        p = self.entry_password.get().strip()

        if not u or not p:
            messagebox.showwarning("Validation Error", "Please enter both username and password.", parent=self.dialog)
            return

        user = database.authenticate_user(u, p)
        if user:
            self.authenticated_user = user
            self.dialog.destroy()
        else:
            messagebox.showerror("Sign In Failed", "Invalid username or password.", parent=self.dialog)

    def on_close(self):
        self.authenticated_user = None
        self.dialog.destroy()

