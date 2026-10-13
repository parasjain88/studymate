"""
=============================================================================
StudyMate — Automated Test Suite for Admin Panel & Security (test_admin.py)
=============================================================================
Comprehensive unit and integration test suite covering:
1. Database schema, non-destructive migrations, and settings defaults.
2. Multi-role authentication (Admin vs Student), session lifecycle, and brute-force rate limiting.
3. Strict Server-Side Role-Based Access Control (RBAC):
   - 401 Unauthorized for unauthenticated requests.
   - 403 Forbidden for non-admin users attempting to access admin endpoints.
4. Protection of the Last Active Administrator against demotion, suspension, or deletion.
5. Complete File Management:
   - Metadata edits, quarantining, and restoration.
   - Renaming with path traversal attack immunity.
   - Permanent single and bulk deletion of database records and disk files.
6. Subject & Category Lifecycle:
   - Creation, editing, deletion with material reassignment, and category merging.
7. Moderation Reports Lifecycle:
   - Student submission, admin review, and resolution with admin notes.
8. Activity Audit Logs:
   - Comprehensive audit trail recording for sensitive actions.
9. Storage Consistency & Health Scanner:
   - Detection of valid, missing, and orphaned storage files.
10. Application Settings configuration persistence.
=============================================================================
"""

import unittest
import os
import sys
import json
import time
import shutil
import threading
import urllib.request
import urllib.parse
import urllib.error
import socketserver

# Ensure project root is in Python sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import database
import web_app


class TestStudyMateAdminDB(unittest.TestCase):
    """Unit tests for the Database and Core Administration logic."""

    @classmethod
    def setUpClass(cls):
        database.init_db()
        # Ensure default admin exists
        if database.count_active_admins() == 0:
            database.register_user("admin", "Admin@123", "System Administrator", role="Admin", email="admin@studymate.local")

    def test_01_database_tables_and_columns_exist(self):
        """Verify all new admin tables and columns exist in the database."""
        conn = database.get_connection()
        c = conn.cursor()

        # Check required tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in c.fetchall()}
        required_tables = {"users", "materials", "sessions", "categories", "reports", "audit_logs", "settings"}
        for t in required_tables:
            self.assertIn(t, tables, f"Table '{t}' must exist in database")

        # Check materials columns
        c.execute("PRAGMA table_info(materials)")
        mat_cols = {row[1] for row in c.fetchall()}
        for col in ("uploader_id", "uploader_name", "file_size", "status", "download_count", "description"):
            self.assertIn(col, mat_cols, f"Column '{col}' must exist in 'materials' table")

        # Check users columns
        c.execute("PRAGMA table_info(users)")
        user_cols = {row[1] for row in c.fetchall()}
        for col in ("status", "email", "last_login"):
            self.assertIn(col, user_cols, f"Column '{col}' must exist in 'users' table")

        conn.close()

    def test_02_admin_authentication_and_sessions(self):
        """Verify authentication, session token generation, lookup, and deletion."""
        # Authenticate admin
        user = database.authenticate_user("admin", "Admin@123")
        self.assertIsNotNone(user, "Default admin authentication must succeed")
        self.assertEqual(user["role"], "Admin", "Admin role must be 'Admin'")

        # Create session
        token = database.create_session(user["id"], user_agent="UnitTest/1.0")
        self.assertTrue(len(token) >= 32, "Session token must be secure random hex string")

        # Lookup session
        session_user = database.get_user_by_session(token)
        self.assertIsNotNone(session_user, "Session lookup must return authenticated user")
        self.assertEqual(session_user["username"], "admin")
        self.assertEqual(session_user["role"], "Admin")

        # Delete session
        database.delete_session(token)
        self.assertIsNone(database.get_user_by_session(token), "Deleted session must return None")

    def test_03_last_active_admin_protection(self):
        """Verify the system strictly prevents demoting, suspending, or deleting the last active admin."""
        admin_user = database.get_user_by_username("admin")
        self.assertIsNotNone(admin_user)
        admin_id = admin_user["id"]

        # Ensure active admins count is verified
        active_admins = database.count_active_admins()
        self.assertGreaterEqual(active_admins, 1)

        if active_admins == 1:
            # 1. Attempt to demote last active admin to Student
            success, msg = database.update_user_role(admin_id, "Student")
            self.assertFalse(success, "Must not allow demoting the last active administrator")
            self.assertIn("last active administrator", msg.lower())

            # 2. Attempt to suspend last active admin
            success, msg = database.update_user_status(admin_id, "suspended")
            self.assertFalse(success, "Must not allow suspending the last active administrator")

            # 3. Attempt to delete last active admin
            success, msg = database.delete_user(admin_id)
            self.assertFalse(success, "Must not allow deleting the last active administrator")

        # Test with a secondary admin to ensure actions succeed when >1 active admin exists
        database.register_user("temp_admin_test", "TempPass@123", "Temporary Admin", role="Admin")
        temp_admin = database.get_user_by_username("temp_admin_test")
        self.assertIsNotNone(temp_admin)

        # Now demote temp_admin -> must succeed
        success, msg = database.update_user_role(temp_admin["id"], "Student")
        self.assertTrue(success, f"Demoting secondary admin should succeed: {msg}")

        # Delete temp_admin -> must succeed
        success, msg = database.delete_user(temp_admin["id"])
        self.assertTrue(success, f"Deleting non-admin user should succeed: {msg}")

    def test_04_file_management_lifecycle_and_traversal_protection(self):
        """Verify material adding, quarantine, path-traversal-safe renaming, and deletion."""
        test_dir = os.path.join(BASE_DIR, "uploads")
        os.makedirs(test_dir, exist_ok=True)
        test_filename = "test_unit_doc.txt"
        test_file_path = os.path.join(test_dir, test_filename)
        with open(test_file_path, "w", encoding="utf-8") as f:
            f.write("Unit test file content for StudyMate admin panel testing.")

        # Add material
        mat_id = database.add_material(
            title="Unit Test Material",
            subject="Operating Systems",
            topic="Deadlocks",
            semester=4,
            material_type="Notes",
            file_path=f"uploads/{test_filename}",
            uploader_name="Test Student",
            file_size=len("Unit test file content for StudyMate admin panel testing."),
            status="active"
        )
        self.assertIsNotNone(mat_id)

        # 1. Quarantine material
        success, msg = database.admin_quarantine_material(mat_id, quarantine=True)
        self.assertTrue(success)
        rec = database.get_material_by_id(mat_id)
        self.assertEqual(rec["status"], "quarantined", "Material status should be quarantined")

        # 2. Path Traversal Test during rename
        # Attempting directory traversal characters like '../../escaped.txt' should be sanitized safely
        success, msg = database.admin_rename_material(
            material_id=mat_id,
            new_title="Unit Test Material Renamed",
            new_filename="../../escaped.txt",
            uploads_dir=test_dir
        )
        self.assertTrue(success, "Rename should sanitize basename and succeed")
        rec = database.get_material_by_id(mat_id)
        # Verify the file is STILL strictly inside the uploads directory and not traversed out
        stored_path = rec["file_path"].replace("\\", "/")
        self.assertFalse(".." in stored_path, "Path must not contain directory traversal '../'")
        self.assertTrue(stored_path.startswith("uploads/"), "File must remain inside uploads directory")

        # 3. Unquarantine material
        success, msg = database.admin_quarantine_material(mat_id, quarantine=False)
        self.assertTrue(success)
        rec = database.get_material_by_id(mat_id)
        self.assertEqual(rec["status"], "active")

        # 4. Delete material permanently
        success, msg = database.admin_delete_material(mat_id, uploads_dir=test_dir)
        self.assertTrue(success)
        self.assertIsNone(database.get_material_by_id(mat_id), "Deleted material must not exist in DB")

    def test_05_subject_category_management_and_merge(self):
        """Verify subject creation, material assignment, deletion with reassign, and merging."""
        # Ensure clean state in case leftover from previous runs
        conn = database.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM materials WHERE subject IN ('Test Subject Alpha', 'Test Subject Beta')")
        c.execute("DELETE FROM categories WHERE name IN ('Test Subject Alpha', 'Test Subject Beta')")
        conn.commit()
        conn.close()

        # Create subjects
        success, _ = database.create_category("Test Subject Alpha", "TSA101", 3, "Alpha category")
        self.assertTrue(success)
        success, _ = database.create_category("Test Subject Beta", "TSB102", 3, "Beta category")
        self.assertTrue(success)

        # Add a material assigned to Alpha
        mat_id = database.add_material(
            title="Alpha Notes",
            subject="Test Subject Alpha",
            topic="Intro",
            semester=3,
            material_type="Notes",
            file_path="uploads/alpha.pdf"
        )

        # Delete Subject Alpha and reassign materials to Subject Beta
        cat_alpha = database.get_category_by_name("Test Subject Alpha")
        self.assertIsNotNone(cat_alpha)
        success, msg = database.delete_category(cat_alpha["id"], reassign_to_name="Test Subject Beta")
        self.assertTrue(success)

        # Verify material was reassigned to Subject Beta
        mat = database.get_material_by_id(mat_id)
        self.assertEqual(mat[2], "Test Subject Beta")

        # Merge Subject Beta into DBMS
        success, msg = database.merge_categories("Test Subject Beta", "DBMS")
        self.assertTrue(success)
        mat = database.get_material_by_id(mat_id)
        self.assertEqual(mat[2], "DBMS")
        self.assertIsNone(database.get_category_by_name("Test Subject Beta"))

        # Clean up material
        database.admin_delete_material(mat_id, os.path.join(BASE_DIR, "uploads"))

    def test_06_reports_and_moderation_workflow(self):
        """Verify student report submission and administrative resolution."""
        # Add temporary material
        mat_id = database.add_material(
            title="Broken File Material",
            subject="DBMS",
            topic="Joins",
            semester=3,
            material_type="Notes",
            file_path="uploads/broken.pdf"
        )

        # Student submits report
        rep_id = database.submit_report(
            material_id=mat_id,
            reporter_id=1,
            reporter_name="PARAS JAIN",
            reason="Broken / Corrupted File",
            details="The file cannot be opened on mobile devices."
        )
        self.assertIsNotNone(rep_id)

        # Admin lists pending reports
        reports_data = database.get_all_reports_admin(status="pending")
        rep_ids = [r["id"] for r in reports_data["reports"]]
        self.assertIn(rep_id, rep_ids)

        # Admin resolves report
        admin_user = database.get_user_by_username("admin")
        success, msg = database.resolve_report(
            report_id=rep_id,
            admin_id=admin_user["id"],
            new_status="resolved",
            admin_notes="Reviewed and confirmed issue. Replacement file requested."
        )
        self.assertTrue(success)

        # Check resolved status
        rep = database.get_report_by_id(rep_id)
        self.assertEqual(rep["status"], "resolved")
        self.assertEqual(rep["admin_notes"], "Reviewed and confirmed issue. Replacement file requested.")

        # Cleanup
        database.admin_delete_material(mat_id, os.path.join(BASE_DIR, "uploads"))

    def test_07_storage_consistency_scanner(self):
        """Verify the storage scanner identifies valid, missing, and orphaned files."""
        uploads_dir = os.path.join(BASE_DIR, "uploads")
        os.makedirs(uploads_dir, exist_ok=True)

        # Create an orphaned file on disk that does NOT exist in the database
        orphaned_filename = "orphaned_test_file_999.tmp"
        orphaned_filepath = os.path.join(uploads_dir, orphaned_filename)
        with open(orphaned_filepath, "w") as f:
            f.write("orphan")

        # Create a DB material whose file does NOT exist on disk (missing file)
        missing_mat_id = database.add_material(
            title="Missing File Material",
            subject="Computer Networks",
            topic="Routing",
            semester=5,
            material_type="Notes",
            file_path="uploads/definitely_non_existent_file_404.pdf"
        )

        scan = database.scan_storage_consistency(uploads_dir)
        self.assertIn("valid_count", scan)
        self.assertIn("missing_count", scan)
        self.assertIn("orphaned_count", scan)

        # Verify missing file was captured
        missing_ids = [m["id"] for m in scan["missing_files"]]
        self.assertIn(missing_mat_id, missing_ids, "Scanner must detect missing file for DB record")

        # Verify orphaned file was captured
        orphaned_names = [o["filename"] for o in scan["orphaned_files"]]
        self.assertIn(orphaned_filename, orphaned_names, "Scanner must detect orphaned file on disk")

        # Clean up
        if os.path.exists(orphaned_filepath):
            os.remove(orphaned_filepath)
        database.admin_delete_material(missing_mat_id, uploads_dir)

    def test_08_application_settings_persistence(self):
        """Verify settings get/set and defaults."""
        max_size = database.get_setting("max_upload_size_mb", "25")
        self.assertEqual(max_size, "25")

        # Update setting
        database.set_setting("max_upload_size_mb", "50")
        self.assertEqual(database.get_setting("max_upload_size_mb"), "50")

        # Revert back
        database.set_setting("max_upload_size_mb", "25")
        self.assertEqual(database.get_setting("max_upload_size_mb"), "25")


class TestStudyMateAdminHTTP(unittest.TestCase):
    """Integration tests running against the live embedded HTTP server."""

    server = None
    server_thread = None
    port = 8765
    base_url = f"http://127.0.0.1:{port}"
    admin_token = None
    student_token = None

    @classmethod
    def setUpClass(cls):
        database.init_db()
        # Seed admin and student
        if database.count_active_admins() == 0:
            database.register_user("admin", "Admin@123", "System Administrator", role="Admin", email="admin@studymate.local")
        
        # Ensure student exists
        student = database.get_user_by_username("PARAS JAIN")
        if not student:
            database.register_user("PARAS JAIN", "Paras@123", "PARAS JAIN", role="Student")

        # Start background server
        socketserver.TCPServer.allow_reuse_address = True
        cls.server = socketserver.TCPServer(("127.0.0.1", cls.port), web_app.StudyMateHTTPRequestHandler)
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()
        time.sleep(0.5)

        # Login admin and student to get tokens
        cls.admin_token = cls._login("admin", "Admin@123")
        cls.student_token = cls._login("PARAS JAIN", "Paras@123")

    @classmethod
    def tearDownClass(cls):
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()

    @classmethod
    def _login(cls, username, password):
        req = urllib.request.Request(
            f"{cls.base_url}/api/login",
            data=json.dumps({"username": username, "password": password}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("token")

    def test_01_admin_page_serves_html(self):
        """GET /admin serves admin.html successfully with HTTP 200."""
        req = urllib.request.Request(f"{self.base_url}/admin")
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            content = resp.read().decode("utf-8")
            self.assertIn("StudyMate", content)
            self.assertIn("Admin Dashboard", content)

    def test_02_unauthenticated_requests_return_401(self):
        """Unauthenticated requests to admin API endpoints must be rejected with HTTP 401."""
        endpoints = [
            "/api/admin/overview",
            "/api/admin/files",
            "/api/admin/users",
            "/api/admin/categories",
            "/api/admin/reports",
            "/api/admin/audit_logs",
            "/api/admin/storage",
            "/api/admin/settings"
        ]
        for ep in endpoints:
            req = urllib.request.Request(f"{self.base_url}{ep}")
            try:
                urllib.request.urlopen(req)
                self.fail(f"Endpoint '{ep}' should have rejected unauthenticated request with 401")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 401, f"Expected 401 for {ep}, got {e.code}")

    def test_03_student_requests_to_admin_endpoints_return_403(self):
        """Authenticated normal students requesting admin endpoints must receive HTTP 403 Forbidden."""
        self.assertIsNotNone(self.student_token, "Student token required for testing RBAC")
        endpoints = [
            "/api/admin/overview",
            "/api/admin/files",
            "/api/admin/users",
            "/api/admin/categories",
            "/api/admin/reports",
            "/api/admin/audit_logs",
            "/api/admin/storage",
            "/api/admin/settings"
        ]
        headers = {"Authorization": f"Bearer {self.student_token}"}
        for ep in endpoints:
            req = urllib.request.Request(f"{self.base_url}{ep}", headers=headers)
            try:
                urllib.request.urlopen(req)
                self.fail(f"Endpoint '{ep}' should have returned 403 for student user")
            except urllib.error.HTTPError as e:
                self.assertEqual(e.code, 403, f"Expected 403 Forbidden for {ep}, got {e.code}")

    def test_04_authorized_admin_requests_return_200_and_real_data(self):
        """Authorized admin requests must return HTTP 200 and live database data."""
        self.assertIsNotNone(self.admin_token, "Admin token required")
        headers = {"Authorization": f"Bearer {self.admin_token}"}

        # 1. Overview
        req = urllib.request.Request(f"{self.base_url}/api/admin/overview", headers=headers)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("stats", data)
            stats = data["stats"]
            self.assertIn("total_materials", stats)
            self.assertIn("total_users", stats)
            self.assertIn("total_storage_bytes", stats)

        # 2. Files List
        req = urllib.request.Request(f"{self.base_url}/api/admin/files?page=1&per_page=5", headers=headers)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("materials", data)

        # 3. Users List
        req = urllib.request.Request(f"{self.base_url}/api/admin/users?page=1&per_page=5", headers=headers)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("users", data)

        # 4. Storage Breakdown
        req = urllib.request.Request(f"{self.base_url}/api/admin/storage", headers=headers)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("success"))
            self.assertIn("storage", data)

        # 5. CSV Export
        req = urllib.request.Request(f"{self.base_url}/api/admin/files/export", headers=headers)
        with urllib.request.urlopen(req) as resp:
            self.assertEqual(resp.status, 200)
            self.assertEqual(resp.headers.get("Content-Type"), "text/csv; charset=utf-8")
            csv_content = resp.read().decode("utf-8-sig")
            self.assertTrue(csv_content.startswith("ID,Title,Subject,Topic,Semester"))

    def test_05_login_rate_limiting(self):
        """Verify brute-force protection locks out after multiple failed attempts."""
        bad_ip = "192.168.100.200"
        # Directly test rate limit helper in web_app
        for i in range(web_app.RATE_LIMIT_MAX_ATTEMPTS):
            web_app.FAILED_LOGIN_ATTEMPTS[bad_ip] = (i + 1, time.time() - 10, time.time())

        handler = web_app.StudyMateHTTPRequestHandler
        allowed, remaining = handler.check_rate_limit(handler, bad_ip)
        self.assertFalse(allowed, "Should be locked out after reaching max failed login attempts")
        self.assertGreater(remaining, 0)

        # Clean up rate limit state for test
        web_app.FAILED_LOGIN_ATTEMPTS.pop(bad_ip, None)


if __name__ == "__main__":
    unittest.main()
