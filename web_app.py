"""
=============================================================================
StudyMate — Smart Study Material Management and Search System
Production Web Server with User Authentication (web_app.py)
=============================================================================
A complete, lightweight, cloud-deployable study material management system.
Built using ONLY Python's standard libraries:
- http.server / socketserver (Zero external web framework dependencies)
- sqlite3 (Embedded relational database)
- hashlib (Secure SHA-256 password hashing)
- base64 / mimetypes / urllib / json / os / sys

Features:
- Student Login & Registration system with SHA-256 security
- Real File Upload system with drag-and-drop & native file chooser
- Saves uploaded files safely into the 'uploads/' folder
- Direct In-Browser File Viewer (open PDFs, images, text files in new browser tabs)
- Desktop Application Launcher (launch files in default Windows software)
- Live Dashboard statistics and recently added materials
- Real-time search and multi-criteria filters
- Favorites bookmarking system
- Embedded Academic Project Report viewer
=============================================================================
"""

import http.server
import socketserver
import urllib.parse
import json
import os
import sys
import base64
import mimetypes
import webbrowser
import time
import secrets
import csv
import io
import database

# Deployment configuration
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "uploads")
ADMIN_HTML_PATH = os.path.join(BASE_DIR, "admin.html")
os.makedirs(UPLOADS_DIR, exist_ok=True)

# Brute-force rate limiting (in-memory)
FAILED_LOGIN_ATTEMPTS = {}
RATE_LIMIT_MAX_ATTEMPTS = 5
RATE_LIMIT_WINDOW_SECONDS = 300  # 5 minutes lockout window

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, viewport-fit=cover">
    <meta name="theme-color" content="#0f172a">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
    <meta name="format-detection" content="telephone=no">
    <title>StudyMate — Student Portal & Study Material Finder</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #2563eb;
            --primary-hover: #1d4ed8;
            --primary-light: #eff6ff;
            --sidebar: #0f172a;
            --sidebar-hover: #1e293b;
            --bg: #f8fafc;
            --card: #ffffff;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --border: #e2e8f0;
            --success: #10b981;
            --warning: #f59e0b;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
        html, body {
            height: 100%;
            overflow-x: hidden;
        }
        body {
            font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
            background: var(--bg);
            color: var(--text-main);
        }

        /* Toast Notifications */
        #toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 99999;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .toast {
            background: #0f172a;
            color: #ffffff;
            padding: 12px 20px;
            border-radius: 8px;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -4px rgba(0,0,0,0.1);
            font-size: 13px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            max-width: 360px;
        }
        .toast.success { background: #065f46; border-left: 4px solid #34d399; }
        .toast.error { background: #991b1b; border-left: 4px solid #f87171; }
        .toast.info { background: #1e3a8a; border-left: 4px solid #60a5fa; }
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }

        /* -------------------------------------------------------------
           AUTHENTICATION SCREEN (LOGIN / REGISTER)
           ------------------------------------------------------------- */
        #auth-screen {
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            width: 100vw;
            background: radial-gradient(circle at top, #1e293b, #0f172a);
            position: fixed;
            top: 0;
            left: 0;
            z-index: 10000;
        }
        .auth-card {
            background: #ffffff;
            width: 100%;
            max-width: 440px;
            border-radius: 16px;
            padding: 36px 32px;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.35);
        }
        .auth-header {
            text-align: center;
            margin-bottom: 24px;
        }
        .auth-header h1 {
            font-size: 24px;
            font-weight: 800;
            color: #0f172a;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        .auth-header p {
            font-size: 13px;
            color: #64748b;
            margin-top: 4px;
        }
        .auth-form-group {
            margin-bottom: 16px;
        }
        .auth-form-group label {
            display: block;
            font-size: 13px;
            font-weight: 700;
            color: #334155;
            margin-bottom: 6px;
        }
        .auth-input {
            width: 100%;
            padding: 11px 14px;
            border: 1.5px solid #cbd5e1;
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.2s;
        }
        .auth-input:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
        }
        .auth-btn {
            width: 100%;
            background: var(--primary);
            color: #ffffff;
            border: none;
            padding: 12px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            margin-top: 10px;
            font-family: inherit;
            transition: background 0.2s;
        }
        .auth-btn:hover {
            background: var(--primary-hover);
        }
        .demo-credentials-badge {
            margin-top: 20px;
            background: #eff6ff;
            border: 1px dashed #93c5fd;
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 12px;
            color: #1e40af;
            cursor: pointer;
            transition: background 0.2s;
            text-align: center;
        }
        .demo-credentials-badge:hover {
            background: #dbeafe;
        }

        /* -------------------------------------------------------------
           MAIN APPLICATION SHELL (AFTER LOGIN)
           ------------------------------------------------------------- */
        #app-shell {
            display: none;
            height: 100vh;
            width: 100vw;
            display: flex;
        }

        /* Sidebar */
        .sidebar {
            width: 255px;
            background: var(--sidebar);
            color: #fff;
            display: flex;
            flex-direction: column;
            padding: 22px 14px;
            flex-shrink: 0;
            border-right: 1px solid #1e293b;
        }
        .brand {
            margin-bottom: 20px;
            padding: 0 8px;
        }
        .brand h2 { font-size: 20px; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 8px; }
        .brand p { font-size: 12px; color: #94a3b8; margin-top: 2px; }

        /* User Profile Badge in Sidebar */
        .user-profile-badge {
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 10px 12px;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
        }
        .user-avatar {
            width: 36px;
            height: 36px;
            background: var(--primary);
            color: #fff;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            font-size: 15px;
            flex-shrink: 0;
        }
        .user-details {
            overflow: hidden;
            flex: 1;
        }
        .user-name {
            font-size: 13px;
            font-weight: 700;
            color: #f8fafc;
            white-space: nowrap;
            text-overflow: ellipsis;
            overflow: hidden;
        }
        .user-role {
            font-size: 11px;
            color: #38bdf8;
            font-weight: 600;
        }

        .nav-btn {
            background: transparent;
            border: none;
            color: #94a3b8;
            padding: 12px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            text-align: left;
            cursor: pointer;
            width: 100%;
            margin-bottom: 6px;
            display: flex;
            align-items: center;
            gap: 12px;
            transition: all 0.2s;
            font-family: inherit;
        }
        .nav-btn:hover { background: var(--sidebar-hover); color: #fff; }
        .nav-btn.active { background: var(--primary); color: #fff; }
        
        .sidebar-footer {
            margin-top: auto;
            border-top: 1px solid #1e293b;
            padding-top: 16px;
        }
        .report-btn {
            background: #1e293b;
            color: #38bdf8;
            border: 1px solid #334155;
            padding: 9px;
            border-radius: 8px;
            font-size: 12px;
            width: 100%;
            cursor: pointer;
            display: block;
            text-align: center;
            text-decoration: none;
            font-weight: 700;
            margin-bottom: 8px;
            transition: all 0.2s;
        }
        .report-btn:hover { background: #334155; color: #fff; }
        .logout-btn {
            background: transparent;
            color: #f87171;
            border: 1px solid #7f1d1d;
            padding: 8px;
            border-radius: 8px;
            font-size: 12px;
            width: 100%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 6px;
            font-weight: 700;
            font-family: inherit;
            transition: all 0.2s;
        }
        .logout-btn:hover { background: #991b1b; color: #fff; }

        /* Main Content */
        .content {
            flex: 1;
            padding: 30px 40px;
            overflow-y: auto;
        }
        .view-section { display: none; }
        .view-section.active { display: block; }
        
        .page-header {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.02em;
            margin-bottom: 22px;
        }

        /* Stats Cards */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 28px;
        }
        .stat-card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            border-top: 4px solid var(--primary);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .stat-card:hover { transform: translateY(-2px); box-shadow: 0 4px 6px -1px rgba(0,0,0,0.08); }
        .stat-card.green { border-top-color: var(--success); }
        .stat-card.amber { border-top-color: var(--warning); }
        .stat-title { font-size: 13px; font-weight: 600; color: var(--text-muted); margin-bottom: 8px; }
        .stat-val { font-size: 32px; font-weight: 800; color: var(--text-main); }

        /* Card Container */
        .card {
            background: var(--card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
            margin-bottom: 25px;
        }
        .card-title {
            font-size: 16px;
            font-weight: 700;
            margin-bottom: 18px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        /* Form */
        .form-group {
            margin-bottom: 18px;
        }
        .form-group label {
            display: block;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 6px;
            color: #334155;
        }
        .form-control {
            width: 100%;
            padding: 10px 14px;
            border: 1.5px solid var(--border);
            border-radius: 8px;
            font-size: 14px;
            font-family: inherit;
            transition: border-color 0.2s;
        }
        .form-control:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
        }
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
        }

        /* File Upload Zone */
        .upload-dropzone {
            border: 2px dashed #93c5fd;
            background: #eff6ff;
            border-radius: 10px;
            padding: 30px 20px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
        }
        .upload-dropzone:hover, .upload-dropzone.dragover {
            border-color: var(--primary);
            background: #dbeafe;
        }
        .upload-icon { font-size: 40px; margin-bottom: 8px; }
        .upload-text-main { font-size: 15px; font-weight: 700; color: #1e40af; margin-bottom: 4px; }
        .upload-text-sub { font-size: 12px; color: var(--text-muted); }

        .file-selected-box {
            display: none;
            margin-top: 12px;
            background: #ffffff;
            border: 1.5px solid #bfdbfe;
            padding: 12px 16px;
            border-radius: 8px;
            align-items: center;
            justify-content: space-between;
        }
        .file-info {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 13px;
            color: #1e3a8a;
            font-weight: 700;
        }
        .file-size-badge {
            font-size: 11px;
            background: #e0f2fe;
            color: #0369a1;
            padding: 3px 8px;
            border-radius: 6px;
        }

        .btn-submit {
            background: var(--primary);
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-weight: 700;
            font-size: 14px;
            font-family: inherit;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s;
        }
        .btn-submit:hover { background: var(--primary-hover); }
        .btn-submit:disabled { background: #94a3b8; cursor: not-allowed; }

        /* Filter Row */
        .filter-box {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        .filter-box input, .filter-box select {
            padding: 10px 14px;
            border: 1.5px solid var(--border);
            border-radius: 8px;
            font-size: 13px;
            font-family: inherit;
        }
        .filter-box input { flex: 1; min-width: 220px; }

        /* Table */
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            font-size: 13px;
        }
        th, td {
            padding: 12px 14px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }
        th {
            background: #f8fafc;
            color: var(--text-muted);
            font-weight: 700;
            border-top: 1px solid var(--border);
        }
        tr:hover td { background: #f8fafc; }
        
        .btn-action {
            padding: 6px 12px;
            border-radius: 6px;
            border: 1px solid var(--border);
            background: #fff;
            cursor: pointer;
            font-size: 12px;
            font-weight: 600;
            margin-right: 4px;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-family: inherit;
            transition: all 0.15s;
        }
        .btn-view { background: #eff6ff; color: #1e40af; border-color: #bfdbfe; }
        .btn-view:hover { background: #dbeafe; }
        .btn-down { background: #f0fdf4; color: #15803d; border-color: #bbf7d0; }
        .btn-down:hover { background: #dcfce7; }
        .btn-star { background: #fefce8; color: #854d0e; border-color: #fef08a; }
        .btn-star:hover { background: #fef08a; }
        .btn-report { background: #fff1f2; color: #be123c; border-color: #fecdd3; }
        .btn-report:hover { background: #ffe4e6; }
        .btn-pc { background: #f1f5f9; color: #334155; border-color: #cbd5e1; }
        .btn-pc:hover { background: #e2e8f0; }

        .badge {
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
        }
        .badge-type { background: #f1f5f9; color: #334155; border: 1px solid #e2e8f0; }
        
        /* Empty State */
        .empty-state {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-muted);
        }
        .empty-state-icon { font-size: 40px; margin-bottom: 10px; opacity: 0.8; }
        .empty-state-text { font-size: 14px; font-weight: 600; margin-bottom: 4px; color: #334155; }
        .empty-state-sub { font-size: 12px; }

        .progress-indicator {
            display: none;
            margin-top: 10px;
            font-size: 13px;
            color: var(--primary);
            font-weight: 700;
        }

        /* -------------------------------------------------------------
           MOBILE NAVIGATION & RESPONSIVE COMPONENTS
           ------------------------------------------------------------- */
        .mobile-top-bar { display: none; }
        .drawer-backdrop { display: none; }
        .sidebar-close-btn { display: none; }
        .mobile-bottom-nav { display: none; }
        .mobile-table-hint { display: none; }
        .table-responsive {
            width: 100%;
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }

        /* Tablet & Mobile Styles (<= 768px) */
        @media (max-width: 768px) {
            html, body {
                height: auto;
                min-height: 100%;
                overflow-x: hidden;
            }
            body.drawer-locked {
                overflow: hidden !important;
            }

            #app-shell {
                flex-direction: column;
                height: auto;
                min-height: 100vh;
                width: 100%;
                overflow-x: hidden;
            }

            /* Mobile Top App Bar */
            .mobile-top-bar {
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: #0f172a;
                color: #ffffff;
                padding: 12px 16px;
                position: sticky;
                top: 0;
                z-index: 9999;
                border-bottom: 1px solid #1e293b;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                padding-top: max(12px, env(safe-area-inset-top));
            }
            .mobile-menu-btn {
                background: #1e293b;
                border: 1px solid #334155;
                color: #ffffff;
                font-size: 20px;
                cursor: pointer;
                padding: 6px 12px;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                line-height: 1;
            }
            .mobile-menu-btn:active {
                background: #334155;
            }
            .mobile-brand {
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 17px;
                font-weight: 800;
                color: #ffffff;
            }
            .mobile-brand-icon {
                font-size: 19px;
            }
            .mobile-user-pill {
                display: flex;
                align-items: center;
                cursor: pointer;
            }
            .mobile-avatar {
                width: 34px;
                height: 34px;
                background: var(--primary);
                color: #ffffff;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 800;
                font-size: 14px;
                border: 2px solid #38bdf8;
            }

            /* Off-Canvas Drawer Sidebar */
            .sidebar {
                position: fixed;
                top: 0;
                left: 0;
                width: 290px;
                max-width: 85vw;
                height: 100%;
                z-index: 10002;
                transform: translateX(-100%);
                transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1);
                box-shadow: none;
                overflow-y: auto;
                padding: 20px 16px;
                padding-bottom: max(30px, env(safe-area-inset-bottom));
            }
            .sidebar.open {
                transform: translateX(0);
                box-shadow: 12px 0 30px rgba(0,0,0,0.5);
            }
            .sidebar-close-btn {
                display: block;
                background: #1e293b;
                color: #94a3b8;
                border: 1px solid #334155;
                border-radius: 8px;
                font-size: 14px;
                font-weight: 700;
                padding: 4px 10px;
                cursor: pointer;
                line-height: 1;
            }
            .sidebar-close-btn:active {
                background: #334155;
                color: #ffffff;
            }

            /* Backdrop Overlay */
            .drawer-backdrop {
                display: block;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(15, 23, 42, 0.7);
                backdrop-filter: blur(3px);
                -webkit-backdrop-filter: blur(3px);
                z-index: 10001;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.25s ease;
            }
            .drawer-backdrop.open {
                opacity: 1;
                pointer-events: auto;
            }

            /* Main Content on Mobile */
            .content {
                padding: 16px 14px;
                padding-bottom: max(88px, calc(74px + env(safe-area-inset-bottom)));
                overflow-y: visible;
                width: 100%;
            }
            .page-header {
                font-size: 20px;
                margin-bottom: 14px;
            }

            /* Mobile Bottom Navigation Bar */
            .mobile-bottom-nav {
                display: flex;
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                background: #ffffff;
                border-top: 1px solid #e2e8f0;
                box-shadow: 0 -4px 16px rgba(0,0,0,0.07);
                z-index: 9998;
                justify-content: space-around;
                align-items: center;
                height: 62px;
                padding-bottom: env(safe-area-inset-bottom);
            }
            .bottom-nav-item {
                flex: 1;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                background: transparent;
                border: none;
                color: #64748b;
                padding: 6px 0;
                cursor: pointer;
                font-family: inherit;
                transition: all 0.15s;
                height: 100%;
            }
            .bottom-nav-item:active {
                background: #f1f5f9;
            }
            .bottom-nav-icon {
                font-size: 19px;
                margin-bottom: 2px;
                transition: transform 0.15s;
            }
            .bottom-nav-label {
                font-size: 11px;
                font-weight: 700;
            }
            .bottom-nav-item.active {
                color: var(--primary);
            }
            .bottom-nav-item.active .bottom-nav-icon {
                transform: scale(1.15);
            }

            /* Mobile Stats Cards */
            .stats-grid {
                grid-template-columns: repeat(3, 1fr);
                gap: 8px;
                margin-bottom: 18px;
            }
            .stat-card {
                padding: 12px 8px;
                border-radius: 10px;
                text-align: center;
            }
            .stat-title {
                font-size: 11px;
                margin-bottom: 4px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            .stat-val {
                font-size: 22px;
            }

            /* Mobile Cards */
            .card {
                padding: 16px 14px;
                border-radius: 12px;
                margin-bottom: 16px;
            }
            .card-title {
                font-size: 15px;
                flex-direction: row;
                margin-bottom: 12px;
            }

            /* Forms & Inputs */
            .form-row {
                grid-template-columns: 1fr;
                gap: 12px;
            }
            .form-group {
                margin-bottom: 14px;
            }
            .form-control, .filter-box input, .filter-box select {
                font-size: 16px !important; /* Prevents auto-zoom in iOS Safari */
                padding: 11px 12px;
                border-radius: 8px;
                width: 100%;
            }
            .btn-submit {
                width: 100%;
                justify-content: center;
                padding: 13px;
                font-size: 15px;
            }

            /* Filter Box */
            .filter-box {
                flex-direction: column;
                gap: 10px;
                margin-bottom: 14px;
            }
            .filter-box input, .filter-box select, .filter-box .btn-action {
                width: 100%;
                margin-right: 0;
                justify-content: center;
                min-height: 42px;
                font-size: 14px;
            }

            /* Upload Dropzone */
            .upload-dropzone {
                padding: 22px 14px;
            }
            .upload-icon {
                font-size: 34px;
            }
            .upload-text-main {
                font-size: 14px;
            }
            .upload-text-sub {
                font-size: 11px;
            }

            /* Tables on Mobile */
            .table-responsive {
                width: 100%;
                overflow-x: auto;
                -webkit-overflow-scrolling: touch;
                margin: 0 -4px;
                padding: 0 4px 4px 4px;
                border-radius: 8px;
            }
            .mobile-table-hint {
                display: block;
                font-size: 11px;
                color: #64748b;
                background: #f1f5f9;
                padding: 6px 10px;
                border-radius: 6px;
                margin-bottom: 10px;
                text-align: center;
                font-weight: 600;
            }
            table {
                min-width: 520px;
                font-size: 12px;
            }
            th, td {
                padding: 10px 8px;
            }
            .btn-action {
                padding: 6px 10px;
                font-size: 11px;
                min-height: 34px;
            }
            .btn-pc {
                display: none !important; /* Hide 'Open on PC' on mobile */
            }

            /* Toast Notifications on Mobile */
            #toast-container {
                top: 10px;
                left: 10px;
                right: 10px;
            }
            .toast {
                max-width: 100%;
                padding: 10px 14px;
                font-size: 12px;
            }

            /* Auth Screen on Mobile */
            #auth-screen {
                padding: 16px;
                min-height: 100vh;
            }
            .auth-card {
                padding: 24px 18px;
                border-radius: 14px;
                width: 100%;
            }
            .auth-header h1 {
                font-size: 22px;
            }
            .auth-input {
                font-size: 16px !important; /* Prevents auto-zoom */
                padding: 12px 14px;
            }
            .auth-btn {
                padding: 13px;
                font-size: 15px;
            }
            .demo-credentials-badge {
                padding: 12px 10px;
                font-size: 12px;
                line-height: 1.4;
            }
        }

        /* Narrow Phones (<= 420px) */
        @media (max-width: 420px) {
            .stats-grid {
                gap: 6px;
            }
            .stat-card {
                padding: 10px 6px;
            }
            .stat-val {
                font-size: 20px;
            }
            .stat-title {
                font-size: 10px;
            }
            .page-header {
                font-size: 18px;
            }
        }
    </style>
</head>
<body>
    <!-- Toast notifications -->
    <div id="toast-container"></div>

    <!-- AUTHENTICATION SCREEN (LOGIN / REGISTER) -->
    <div id="auth-screen">
        <div class="auth-card">
            <div class="auth-header">
                <h1>📚 StudyMate</h1>
                <p>Student Portal & Study Material Management</p>
            </div>

            <!-- Sign In Form -->
            <form id="form-login" onsubmit="handleLogin(event)">
                <div class="auth-form-group">
                    <label>Username</label>
                    <input type="text" id="login-username" class="auth-input" placeholder="e.g. PARAS JAIN" required autofocus>
                </div>
                <div class="auth-form-group">
                    <label>Password</label>
                    <input type="password" id="login-password" class="auth-input" placeholder="Enter your password" required>
                </div>
                <button type="submit" class="auth-btn" id="btn-login">Sign In to StudyMate 🚀</button>

                <!-- One-click Demo Credentials Helper -->
                <div class="demo-credentials-badge" onclick="fillDemoCredentials()">
                    💡 <strong>Quick Demo:</strong> Click here to auto-fill <strong>PARAS JAIN / Paras@123</strong>
                </div>
            </form>
        </div>
    </div>

    <!-- MAIN APPLICATION SHELL (AFTER SUCCESSFUL LOGIN) -->
    <div id="app-shell">
        <!-- Mobile Top App Bar (visible on mobile only) -->
        <header class="mobile-top-bar" id="mobile-top-bar">
            <button class="mobile-menu-btn" id="btn-mobile-menu" onclick="toggleMobileDrawer()" aria-label="Open Navigation Menu">
                ☰
            </button>
            <div class="mobile-brand">
                <span class="mobile-brand-icon">📚</span>
                <span class="mobile-brand-text">StudyMate</span>
            </div>
            <a href="/admin" id="mobile-topbar-admin-link" style="display:none; color:#38bdf8; font-size:12px; font-weight:700; text-decoration:none; background:rgba(56,189,248,0.15); padding:4px 8px; border-radius:6px; border:1px solid rgba(56,189,248,0.3); margin-left:auto; margin-right:8px;">⚙️ Admin</a>
            <div class="mobile-user-pill" onclick="toggleMobileDrawer()" title="View Student Profile">
                <div class="mobile-avatar" id="mobile-avatar-initial">P</div>
            </div>
        </header>

        <!-- Drawer Backdrop Overlay for Mobile -->
        <div class="drawer-backdrop" id="drawer-backdrop" onclick="closeMobileDrawer()"></div>

        <!-- Sidebar (Desktop Sidebar & Mobile Drawer) -->
        <div class="sidebar">
            <div class="brand">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <h2>📚 StudyMate</h2>
                    <button class="sidebar-close-btn" onclick="closeMobileDrawer()" aria-label="Close menu">✕</button>
                </div>
                <p>Smart Material Finder</p>
            </div>

            <!-- Active User Profile Card -->
            <div class="user-profile-badge">
                <div class="user-avatar" id="avatar-initial">P</div>
                <div class="user-details">
                    <div class="user-name" id="display-user-name">PARAS JAIN</div>
                    <div class="user-role" id="display-user-role">Student</div>
                </div>
            </div>

            <button class="nav-btn active" data-view="dashboard" onclick="switchView('dashboard')">🏠 Dashboard</button>
            <button class="nav-btn" data-view="add" onclick="switchView('add')">➕ Add Material</button>
            <button class="nav-btn" data-view="search" onclick="switchView('search')">🔍 Search & Filter</button>
            <button class="nav-btn" data-view="favorites" onclick="switchView('favorites')">⭐ Favorites</button>
            <a href="/admin" id="sidebar-admin-link" class="nav-btn" style="display:none; color:#38bdf8; background:rgba(56,189,248,0.12); border:1px solid rgba(56,189,248,0.3); text-decoration:none; margin-top:8px;">⚙️ Admin Dashboard</a>

            <div class="sidebar-footer">
                <a href="/report" target="_blank" class="report-btn">📄 View Project Report</a>
                <button class="logout-btn" onclick="handleLogout()">🚪 Sign Out</button>
                <div style="font-size: 11px; color: #64748b; text-align: center; margin-top: 10px;">
                    B.Tech 3rd Sem Mini Project
                </div>
            </div>
        </div>

        <!-- Main Content Area -->
        <div class="content">
            <!-- View 1: Dashboard -->
            <div id="view-dashboard" class="view-section active">
                <h1 class="page-header">Dashboard Overview</h1>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-title">Total Study Materials</div>
                        <div class="stat-val" id="stat-materials">0</div>
                    </div>
                    <div class="stat-card green">
                        <div class="stat-title">Total Subjects</div>
                        <div class="stat-val" id="stat-subjects">0</div>
                    </div>
                    <div class="stat-card amber">
                        <div class="stat-title">Favorite Materials</div>
                        <div class="stat-val" id="stat-favorites">0</div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-title">
                        <span>🕒 Recently Added Materials</span>
                        <button class="btn-action" onclick="fetchRecentMaterials()">🔄 Refresh</button>
                    </div>
                    <div class="mobile-table-hint">👈 Swipe table horizontally to see all columns 👉</div>
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Subject</th>
                                    <th>Sem</th>
                                    <th>Type</th>
                                    <th>Date Added</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="recent-table-body"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- View 2: Add Material -->
            <div id="view-add" class="view-section">
                <h1 class="page-header">Upload Study Material</h1>
                <div class="card" style="max-width: 680px;">
                    
                    <!-- File Upload Dropzone -->
                    <div class="form-group">
                        <label>Select Study Material File *</label>
                        <div class="upload-dropzone" id="dropzone" onclick="document.getElementById('file-input').click()">
                            <div class="upload-icon">📁</div>
                            <div class="upload-text-main">Tap or click to choose study material</div>
                            <div class="upload-text-sub">Select PDF, PPT, Word, Notes or Images from your device</div>
                            <input type="file" id="file-input" style="display: none;" onchange="handleFileSelected(event)">
                        </div>

                        <!-- Selected file details bar -->
                        <div class="file-selected-box" id="file-selected-box">
                            <div class="file-info">
                                <span id="file-icon">📄</span>
                                <span id="file-name-display">No file chosen</span>
                                <span class="file-size-badge" id="file-size-display">0 KB</span>
                            </div>
                            <button class="btn-action" type="button" onclick="clearSelectedFile(event)" style="margin:0; font-size:11px;">✕ Remove</button>
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Material Title *</label>
                        <input type="text" id="add-title" class="form-control" placeholder="e.g. Unit 3 Discrete Mathematics Notes">
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Subject *</label>
                            <input type="text" id="add-subject" class="form-control" placeholder="e.g. DSTL, DBMS, Operating Systems, DSA">
                        </div>
                        <div class="form-group">
                            <label>Topic / Unit</label>
                            <input type="text" id="add-topic" class="form-control" placeholder="e.g. Relations, Normalization">
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label>Semester *</label>
                            <select id="add-sem" class="form-control">
                                <option value="1">Semester 1</option>
                                <option value="2">Semester 2</option>
                                <option value="3" selected>Semester 3</option>
                                <option value="4">Semester 4</option>
                                <option value="5">Semester 5</option>
                                <option value="6">Semester 6</option>
                                <option value="7">Semester 7</option>
                                <option value="8">Semester 8</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Material Type *</label>
                            <select id="add-type" class="form-control">
                                <option value="Notes" selected>Notes</option>
                                <option value="Previous Year Paper">Previous Year Paper</option>
                                <option value="Assignment">Assignment</option>
                                <option value="PPT">PPT</option>
                                <option value="Book">Book</option>
                                <option value="Lab Manual">Lab Manual</option>
                                <option value="Other">Other</option>
                            </select>
                        </div>
                    </div>

                    <div class="progress-indicator" id="upload-progress">
                        ⏳ Uploading and indexing study material...
                    </div>

                    <button class="btn-submit" id="btn-save" onclick="submitAddMaterial()" style="margin-top: 10px;">
                        💾 Upload & Save Study Material
                    </button>
                </div>
            </div>

            <!-- View 3: Search & Filter -->
            <div id="view-search" class="view-section">
                <h1 class="page-header">Search & Filter Materials</h1>
                <div class="card">
                    <div class="filter-box">
                        <input type="text" id="search-input" placeholder="🔍 Search by Title, Subject, Topic..." oninput="searchMaterials()">
                        <select id="filter-sem" onchange="searchMaterials()">
                            <option value="All">All Semesters</option>
                            <option value="1">Semester 1</option>
                            <option value="2">Semester 2</option>
                            <option value="3">Semester 3</option>
                            <option value="4">Semester 4</option>
                            <option value="5">Semester 5</option>
                            <option value="6">Semester 6</option>
                            <option value="7">Semester 7</option>
                            <option value="8">Semester 8</option>
                        </select>
                        <select id="filter-type" onchange="searchMaterials()">
                            <option value="All">All Material Types</option>
                            <option value="Notes">Notes</option>
                            <option value="Previous Year Paper">Previous Year Paper</option>
                            <option value="Assignment">Assignment</option>
                            <option value="PPT">PPT</option>
                            <option value="Book">Book</option>
                            <option value="Lab Manual">Lab Manual</option>
                            <option value="Other">Other</option>
                        </select>
                        <button class="btn-action" onclick="resetFilters()">🔄 Reset</button>
                    </div>

                    <div class="mobile-table-hint">👈 Swipe table horizontally to see all columns 👉</div>
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Subject</th>
                                    <th>Topic</th>
                                    <th>Sem</th>
                                    <th>Type</th>
                                    <th>Fav</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="search-table-body"></tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- View 4: Favorites -->
            <div id="view-favorites" class="view-section">
                <h1 class="page-header">⭐ Favorite Study Materials</h1>
                <div class="card">
                    <div class="mobile-table-hint">👈 Swipe table horizontally to see all columns 👉</div>
                    <div class="table-responsive">
                        <table>
                            <thead>
                                <tr>
                                    <th>Title</th>
                                    <th>Subject</th>
                                    <th>Topic</th>
                                    <th>Sem</th>
                                    <th>Type</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="fav-table-body"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>

        <!-- Mobile Bottom Navigation Bar (visible on mobile only) -->
        <nav class="mobile-bottom-nav" id="mobile-bottom-nav">
            <button class="bottom-nav-item active" data-view="dashboard" onclick="switchView('dashboard')">
                <span class="bottom-nav-icon">🏠</span>
                <span class="bottom-nav-label">Home</span>
            </button>
            <button class="bottom-nav-item" data-view="add" onclick="switchView('add')">
                <span class="bottom-nav-icon">➕</span>
                <span class="bottom-nav-label">Upload</span>
            </button>
            <button class="bottom-nav-item" data-view="search" onclick="switchView('search')">
                <span class="bottom-nav-icon">🔍</span>
                <span class="bottom-nav-label">Search</span>
            </button>
            <button class="bottom-nav-item" data-view="favorites" onclick="switchView('favorites')">
                <span class="bottom-nav-icon">⭐</span>
                <span class="bottom-nav-label">Favorites</span>
            </button>
        </nav>
    </div>

    <!-- Student Report Modal -->
    <div id="modal-report-material" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(15,23,42,0.6); z-index:99999; align-items:center; justify-content:center; backdrop-filter:blur(3px);">
        <div style="background:#fff; border-radius:12px; padding:24px; max-width:440px; width:90%; box-shadow:0 20px 25px -5px rgba(0,0,0,0.2);">
            <h3 style="font-size:18px; margin-bottom:8px; display:flex; align-items:center; gap:8px;">🚩 Report Study Material</h3>
            <p style="font-size:13px; color:#64748b; margin-bottom:14px;" id="report-modal-subtitle">Help moderators review broken or inappropriate files.</p>
            <input type="hidden" id="report-modal-mat-id">
            <div style="margin-bottom:12px;">
                <label style="display:block; font-size:12px; font-weight:700; margin-bottom:4px; color:#334155;">Reason</label>
                <select id="report-modal-reason" class="form-control" style="width:100%; padding:8px 12px; border:1.5px solid #e2e8f0; border-radius:6px; font-size:13px;">
                    <option value="Broken / Corrupted File">Broken / Corrupted File</option>
                    <option value="Incorrect Subject / Semester">Incorrect Subject / Semester</option>
                    <option value="Copyright Violation">Copyright Violation</option>
                    <option value="Inappropriate Content">Inappropriate Content</option>
                    <option value="Duplicate Material">Duplicate Material</option>
                    <option value="Other">Other Issue</option>
                </select>
            </div>
            <div style="margin-bottom:16px;">
                <label style="display:block; font-size:12px; font-weight:700; margin-bottom:4px; color:#334155;">Additional Details (Optional)</label>
                <textarea id="report-modal-details" rows="3" class="form-control" placeholder="Describe the issue with this material..." style="width:100%; padding:8px 12px; border:1.5px solid #e2e8f0; border-radius:6px; font-size:13px; resize:vertical;"></textarea>
            </div>
            <div style="display:flex; justify-content:flex-end; gap:8px;">
                <button type="button" onclick="closeReportModal()" style="padding:8px 16px; border:1px solid #cbd5e1; background:#f8fafc; border-radius:6px; font-size:13px; font-weight:600; cursor:pointer;">Cancel</button>
                <button type="button" onclick="submitStudentReport()" style="padding:8px 16px; border:none; background:#ef4444; color:#fff; border-radius:6px; font-size:13px; font-weight:700; cursor:pointer;">Submit Report 🚩</button>
            </div>
        </div>
    </div>

    <script>
        let currentFileObj = null;
        let currentUser = null;

        function showToast(msg, type = 'info') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.innerText = msg;
            container.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                toast.style.transition = 'all 0.3s ease';
                setTimeout(() => toast.remove(), 300);
            }, 3500);
        }

        function escapeHtml(str) {
            if (!str) return '';
            return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#039;');
        }

        function escapeAttr(str) {
            if (!str) return '';
            return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
        }

        /* -------------------------------------------------------------
           AUTHENTICATION LOGIC (LOGIN & LOGOUT)
           ------------------------------------------------------------- */
        function fillDemoCredentials() {
            document.getElementById('login-username').value = 'PARAS JAIN';
            document.getElementById('login-password').value = 'Paras@123';
            showToast('Auto-filled credentials for PARAS JAIN!', 'info');
        }

        async function handleLogin(event) {
            event.preventDefault();
            const u = document.getElementById('login-username').value.trim();
            const p = document.getElementById('login-password').value.trim();
            const btn = document.getElementById('btn-login');

            btn.disabled = true;
            btn.innerText = 'Signing In...';

            try {
                const res = await fetch('/api/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: u, password: p })
                });
                const data = await res.json();
                btn.disabled = false;
                btn.innerText = 'Sign In to StudyMate 🚀';

                if (data.success) {
                    currentUser = data.user;
                    localStorage.setItem('studymate_user', JSON.stringify(currentUser));
                    if (data.token) {
                        localStorage.setItem('studymate_token', data.token);
                    }
                    showToast(`Welcome back, ${currentUser.full_name}! 👋`, 'success');
                    renderApp();

                    if (currentUser.role && currentUser.role.toLowerCase() === 'admin') {
                        setTimeout(() => {
                            if (confirm(`Welcome Administrator ${currentUser.full_name}!\nWould you like to open the Admin Panel now?`)) {
                                window.location.href = '/admin';
                            }
                        }, 500);
                    }
                } else {
                    showToast(data.error || 'Invalid credentials.', 'error');
                }
            } catch (err) {
                btn.disabled = false;
                btn.innerText = 'Sign In to StudyMate 🚀';
                showToast('Network error during login: ' + err, 'error');
            }
        }

        function handleLogout() {
            closeMobileDrawer();
            const token = localStorage.getItem('studymate_token');
            if (token) {
                fetch('/api/logout', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }
                }).catch(() => {});
            }
            localStorage.removeItem('studymate_user');
            localStorage.removeItem('studymate_token');
            currentUser = null;
            document.getElementById('app-shell').style.display = 'none';
            document.getElementById('auth-screen').style.display = 'flex';
            document.getElementById('login-password').value = '';
            showToast('Signed out successfully.', 'info');
        }

        function checkAuth() {
            const saved = localStorage.getItem('studymate_user');
            if (saved) {
                try {
                    currentUser = JSON.parse(saved);
                    renderApp();
                    return;
                } catch(e) {
                    localStorage.removeItem('studymate_user');
                }
            }
            // Show Auth Screen
            document.getElementById('auth-screen').style.display = 'flex';
            document.getElementById('app-shell').style.display = 'none';
        }

        function renderApp() {
            document.getElementById('auth-screen').style.display = 'none';
            document.getElementById('app-shell').style.display = 'flex';

            if (currentUser) {
                document.getElementById('display-user-name').innerText = currentUser.full_name;
                document.getElementById('display-user-role').innerText = `@${currentUser.username} • ${currentUser.role}`;
                const initial = currentUser.full_name.charAt(0).toUpperCase();
                document.getElementById('avatar-initial').innerText = initial;
                const mobInitial = document.getElementById('mobile-avatar-initial');
                if (mobInitial) mobInitial.innerText = initial;

                const isAdmin = currentUser.role && currentUser.role.toLowerCase() === 'admin';
                const sbLink = document.getElementById('sidebar-admin-link');
                if (sbLink) sbLink.style.display = isAdmin ? 'flex' : 'none';
                const mobLink = document.getElementById('mobile-topbar-admin-link');
                if (mobLink) mobLink.style.display = isAdmin ? 'inline-block' : 'none';
            }

            fetchStats();
            fetchRecentMaterials();
        }

        /* -------------------------------------------------------------
           STUDENT REPORTING SYSTEM
           ------------------------------------------------------------- */
        function openReportModal(id, title) {
            document.getElementById('report-modal-mat-id').value = id;
            document.getElementById('report-modal-subtitle').innerText = `Reporting: "${title}"`;
            document.getElementById('report-modal-details').value = '';
            const m = document.getElementById('modal-report-material');
            if (m) m.style.display = 'flex';
        }

        function closeReportModal() {
            const m = document.getElementById('modal-report-material');
            if (m) m.style.display = 'none';
        }

        async function submitStudentReport() {
            const matId = document.getElementById('report-modal-mat-id').value;
            const reason = document.getElementById('report-modal-reason').value;
            const details = document.getElementById('report-modal-details').value.trim();
            const token = localStorage.getItem('studymate_token') || '';

            try {
                const res = await fetch('/api/reports/submit', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        material_id: matId,
                        reason: reason,
                        details: details
                    })
                });
                const data = await res.json();
                if (data.success) {
                    showToast('Report submitted! Moderators will review this material.', 'success');
                    closeReportModal();
                } else {
                    showToast(data.error || 'Failed submitting report.', 'error');
                }
            } catch(e) {
                showToast('Error submitting report: ' + e, 'error');
            }
        }

        /* -------------------------------------------------------------
           MOBILE DRAWER CONTROLS
           ------------------------------------------------------------- */
        function toggleMobileDrawer() {
            const sidebar = document.querySelector('.sidebar');
            const backdrop = document.getElementById('drawer-backdrop');
            if (!sidebar) return;
            const isOpen = sidebar.classList.contains('open');
            if (isOpen) {
                closeMobileDrawer();
            } else {
                sidebar.classList.add('open');
                if (backdrop) backdrop.classList.add('open');
                document.body.classList.add('drawer-locked');
            }
        }

        function closeMobileDrawer() {
            const sidebar = document.querySelector('.sidebar');
            const backdrop = document.getElementById('drawer-backdrop');
            if (sidebar) sidebar.classList.remove('open');
            if (backdrop) backdrop.classList.remove('open');
            document.body.classList.remove('drawer-locked');
        }

        /* -------------------------------------------------------------
           DRAG & DROP / FILE SELECTION
           ------------------------------------------------------------- */
        const dropzone = document.getElementById('dropzone');
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.add('dragover');
            }, false);
        });
        ['dragleave', 'drop'].forEach(eventName => {
            dropzone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
                dropzone.classList.remove('dragover');
            }, false);
        });
        dropzone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                processChosenFile(files[0]);
            }
        });

        function handleFileSelected(event) {
            const file = event.target.files[0];
            if (file) {
                processChosenFile(file);
            }
        }

        function processChosenFile(file) {
            currentFileObj = file;
            document.getElementById('file-selected-box').style.display = 'flex';
            document.getElementById('file-name-display').innerText = file.name;
            
            const sizeKB = (file.size / 1024).toFixed(1);
            const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
            document.getElementById('file-size-display').innerText = file.size > 1024 * 1024 ? sizeMB + ' MB' : sizeKB + ' KB';

            const ext = file.name.split('.').pop().toLowerCase();
            let icon = '📄';
            if (ext === 'pdf') icon = '📕';
            else if (['ppt', 'pptx'].includes(ext)) { icon = '📊'; document.getElementById('add-type').value = 'PPT'; }
            else if (['doc', 'docx'].includes(ext)) icon = '📝';
            else if (['zip', 'rar'].includes(ext)) icon = '📦';
            else if (['png', 'jpg', 'jpeg'].includes(ext)) icon = '🖼️';
            document.getElementById('file-icon').innerText = icon;

            const titleInput = document.getElementById('add-title');
            if (!titleInput.value.trim()) {
                const baseName = file.name.substring(0, file.name.lastIndexOf('.')) || file.name;
                titleInput.value = baseName.replace(/[_-]/g, ' ');
            }
        }

        function clearSelectedFile(event) {
            if(event) event.stopPropagation();
            currentFileObj = null;
            document.getElementById('file-input').value = '';
            document.getElementById('file-selected-box').style.display = 'none';
        }

        function switchView(viewName) {
            document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.nav-btn').forEach(el => {
                if (el.getAttribute('data-view') === viewName) {
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            });
            document.querySelectorAll('.bottom-nav-item').forEach(el => {
                if (el.getAttribute('data-view') === viewName) {
                    el.classList.add('active');
                } else {
                    el.classList.remove('active');
                }
            });
            
            const target = document.getElementById('view-' + viewName);
            if (target) target.classList.add('active');

            closeMobileDrawer();
            window.scrollTo({ top: 0, behavior: 'smooth' });
            const content = document.querySelector('.content');
            if (content) content.scrollTo({ top: 0, behavior: 'smooth' });

            if (viewName === 'dashboard') {
                fetchStats();
                fetchRecentMaterials();
            } else if (viewName === 'search') {
                searchMaterials();
            } else if (viewName === 'favorites') {
                fetchFavorites();
            }
        }

        async function fetchStats() {
            try {
                const res = await fetch('/api/stats');
                const data = await res.json();
                document.getElementById('stat-materials').innerText = data.total_materials;
                document.getElementById('stat-subjects').innerText = data.total_subjects;
                document.getElementById('stat-favorites').innerText = data.total_favorites;
            } catch(e) { console.error(e); }
        }

        async function fetchRecentMaterials() {
            try {
                const res = await fetch('/api/materials');
                const list = await res.json();
                const tbody = document.getElementById('recent-table-body');
                tbody.innerHTML = '';
                if(list.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="6">
                                <div class="empty-state">
                                    <div class="empty-state-icon">📚</div>
                                    <div class="empty-state-text">No study materials added yet</div>
                                    <div class="empty-state-sub">Click "Add Material" to upload your first study material!</div>
                                </div>
                            </td>
                        </tr>
                    `;
                    return;
                }
                const top5 = list.slice(0, 5);
                top5.forEach(m => {
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${escapeHtml(m.title)}</strong></td>
                            <td>${escapeHtml(m.subject)}</td>
                            <td>${m.semester}</td>
                            <td><span class="badge badge-type">${escapeHtml(m.material_type)}</span></td>
                            <td>${escapeHtml(m.date_added)}</td>
                            <td>
                                <a href="/api/view?id=${m.id}" target="_blank" class="btn-action btn-view">👁️ View</a>
                                <a href="/api/view?id=${m.id}&download=1" class="btn-action btn-down">⬇️ Download</a>
                                <button class="btn-action btn-pc" onclick="openFileDesktop(${m.id})">💻 Open on PC</button>
                                <button class="btn-action btn-report" onclick="openReportModal(${m.id}, '${escapeAttr(m.title)}')">🚩 Report</button>
                            </td>
                        </tr>
                    `;
                });
            } catch(e) { console.error(e); }
        }

        async function searchMaterials() {
            const q = document.getElementById('search-input').value;
            const sem = document.getElementById('filter-sem').value;
            const type = document.getElementById('filter-type').value;

            try {
                const res = await fetch(`/api/materials?search=${encodeURIComponent(q)}&semester=${sem}&type=${encodeURIComponent(type)}`);
                const list = await res.json();
                const tbody = document.getElementById('search-table-body');
                tbody.innerHTML = '';
                if(list.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="7">
                                <div class="empty-state">
                                    <div class="empty-state-icon">🔍</div>
                                    <div class="empty-state-text">No matching study materials found</div>
                                    <div class="empty-state-sub">Try searching with another keyword or resetting filters.</div>
                                </div>
                            </td>
                        </tr>
                    `;
                    return;
                }
                list.forEach(m => {
                    const isFav = m.favorite === 1;
                    const starIcon = isFav ? '⭐' : '☆';
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${escapeHtml(m.title)}</strong></td>
                            <td>${escapeHtml(m.subject)}</td>
                            <td>${escapeHtml(m.topic || '—')}</td>
                            <td>${m.semester}</td>
                            <td><span class="badge badge-type">${escapeHtml(m.material_type)}</span></td>
                            <td>${starIcon}</td>
                            <td>
                                <a href="/api/view?id=${m.id}" target="_blank" class="btn-action btn-view">👁️ View</a>
                                <a href="/api/view?id=${m.id}&download=1" class="btn-action btn-down">⬇️ Download</a>
                                <button class="btn-action btn-pc" onclick="openFileDesktop(${m.id})">💻 PC</button>
                                <button class="btn-action btn-star" onclick="toggleFav(${m.id})">${starIcon} ${isFav ? 'Unstar' : 'Star'}</button>
                                <button class="btn-action btn-report" onclick="openReportModal(${m.id}, '${escapeAttr(m.title)}')">🚩 Report</button>
                            </td>
                        </tr>
                    `;
                });
            } catch(e) { console.error(e); }
        }

        async function fetchFavorites() {
            try {
                const res = await fetch('/api/materials?favorites=1');
                const list = await res.json();
                const tbody = document.getElementById('fav-table-body');
                tbody.innerHTML = '';
                if(list.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="6">
                                <div class="empty-state">
                                    <div class="empty-state-icon">⭐</div>
                                    <div class="empty-state-text">No favorite materials yet</div>
                                    <div class="empty-state-sub">Star any notes or question papers in the Search tab to view them here!</div>
                                </div>
                            </td>
                        </tr>
                    `;
                    return;
                }
                list.forEach(m => {
                    tbody.innerHTML += `
                        <tr>
                            <td><strong>${escapeHtml(m.title)}</strong></td>
                            <td>${escapeHtml(m.subject)}</td>
                            <td>${escapeHtml(m.topic || '—')}</td>
                            <td>${m.semester}</td>
                            <td><span class="badge badge-type">${escapeHtml(m.material_type)}</span></td>
                            <td>
                                <a href="/api/view?id=${m.id}" target="_blank" class="btn-action btn-view">👁️ View</a>
                                <a href="/api/view?id=${m.id}&download=1" class="btn-action btn-down">⬇️ Download</a>
                                <button class="btn-action btn-pc" onclick="openFileDesktop(${m.id})">💻 PC</button>
                                <button class="btn-action btn-star" onclick="toggleFav(${m.id})">❌ Remove</button>
                                <button class="btn-action btn-report" onclick="openReportModal(${m.id}, '${escapeAttr(m.title)}')">🚩 Report</button>
                            </td>
                        </tr>
                    `;
                });
            } catch(e) { console.error(e); }
        }

        async function openFileDesktop(id) {
            try {
                const res = await fetch(`/api/open?id=${id}`);
                const data = await res.json();
                if(!data.success) {
                    showToast(data.message, 'error');
                } else {
                    showToast('Opening file on computer...', 'info');
                }
            } catch(e) {
                showToast('Could not open file: ' + e, 'error');
            }
        }

        async function toggleFav(id) {
            const res = await fetch('/api/toggle_favorite', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({id: id})
            });
            const data = await res.json();
            showToast(data.new_status === 1 ? 'Added to Favorites ⭐' : 'Removed from Favorites', 'info');
            fetchStats();
            searchMaterials();
            fetchFavorites();
        }

        async function submitAddMaterial() {
            const title = document.getElementById('add-title').value.trim();
            const subject = document.getElementById('add-subject').value.trim();
            const topic = document.getElementById('add-topic').value.trim();
            const sem = document.getElementById('add-sem').value;
            const type = document.getElementById('add-type').value;

            if(!currentFileObj) { showToast('Please choose or drag & drop a study material file.', 'error'); return; }
            if(!title) { showToast('Please enter material title.', 'error'); return; }
            if(!subject) { showToast('Please enter a subject name.', 'error'); return; }

            const progressEl = document.getElementById('upload-progress');
            const saveBtn = document.getElementById('btn-save');
            progressEl.style.display = 'block';
            saveBtn.disabled = true;

            try {
                const reader = new FileReader();
                reader.onload = async function(e) {
                    const base64Data = e.target.result.split(',')[1];
                    const payload = {
                        title: title,
                        subject: subject,
                        topic: topic,
                        semester: sem,
                        material_type: type,
                        filename: currentFileObj.name,
                        file_base64: base64Data
                    };

                    const token = localStorage.getItem('studymate_token') || '';
                    const res = await fetch('/api/upload', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify(payload)
                    });

                    const data = await res.json();
                    progressEl.style.display = 'none';
                    saveBtn.disabled = false;

                    if(data.success) {
                        showToast(`'${currentFileObj.name}' saved successfully!`, 'success');
                        clearSelectedFile();
                        document.getElementById('add-title').value = '';
                        document.getElementById('add-subject').value = '';
                        document.getElementById('add-topic').value = '';
                        switchView('search');
                    } else {
                        showToast('Upload failed: ' + data.error, 'error');
                    }
                };
                reader.readAsDataURL(currentFileObj);

            } catch (err) {
                progressEl.style.display = 'none';
                saveBtn.disabled = false;
                showToast('Error uploading file: ' + err, 'error');
            }
        }

        function resetFilters() {
            document.getElementById('search-input').value = '';
            document.getElementById('filter-sem').value = 'All';
            document.getElementById('filter-type').value = 'All';
            searchMaterials();
        }

        // Initialize Authentication on Page Load
        checkAuth();
    </script>
</body>
</html>
"""


def resolve_file_path(stored_path):
    """
    Robust cross-platform path resolver for StudyMate study materials.
    Guarantees files open reliably across Windows local machines,
    Linux cloud containers (such as Render), mobile browsers, and other devices.
    """
    if not stored_path:
        return None

    # Standardize backslashes to forward slashes for universal handling
    clean_p = str(stored_path).strip().replace("\\", "/")

    # Check 1: Relative path joined with BASE_DIR (e.g. "uploads/notes.pdf")
    c1 = os.path.normpath(os.path.join(BASE_DIR, clean_p))
    if os.path.isfile(c1):
        return c1

    # Check 2: Absolute file path if it exists directly on current operating system
    if os.path.isfile(stored_path):
        return stored_path

    # Check 3: Extract filename safely and look inside UPLOADS_DIR
    # (Handles Windows absolute paths stored in SQLite when running on Linux/Render)
    filename = os.path.basename(clean_p)
    if filename:
        c3 = os.path.join(UPLOADS_DIR, filename)
        if os.path.isfile(c3):
            return c3

        # Check 4: Look directly inside BASE_DIR
        c4 = os.path.join(BASE_DIR, filename)
        if os.path.isfile(c4):
            return c4

    return None


class StudyMateHTTPRequestHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    # -------------------------------------------------------------------------
    # Authentication, Session, and Rate-Limiting Helpers
    # -------------------------------------------------------------------------
    def get_client_ip(self):
        """Extract the true client IP from proxy headers or socket connection."""
        forwarded = self.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if self.client_address:
            return str(self.client_address[0])
        return "127.0.0.1"

    def check_rate_limit(self, ip):
        """Check if an IP address has exceeded failed login thresholds."""
        now = time.time()
        record = FAILED_LOGIN_ATTEMPTS.get(ip)
        if record:
            count, first_time, last_time = record
            if now - last_time > RATE_LIMIT_WINDOW_SECONDS:
                FAILED_LOGIN_ATTEMPTS.pop(ip, None)
                return True, 0
            if count >= RATE_LIMIT_MAX_ATTEMPTS:
                remaining = int(RATE_LIMIT_WINDOW_SECONDS - (now - last_time))
                return False, max(1, remaining)
        return True, 0

    def record_failed_login(self, ip):
        """Increment failed login attempt count for an IP address."""
        now = time.time()
        record = FAILED_LOGIN_ATTEMPTS.get(ip)
        if record:
            count, first_time, last_time = record
            if now - last_time > RATE_LIMIT_WINDOW_SECONDS:
                FAILED_LOGIN_ATTEMPTS[ip] = (1, now, now)
            else:
                FAILED_LOGIN_ATTEMPTS[ip] = (count + 1, first_time, now)
        else:
            FAILED_LOGIN_ATTEMPTS[ip] = (1, now, now)

    def reset_failed_logins(self, ip):
        """Clear rate limiting counter for an IP address upon successful sign-in."""
        FAILED_LOGIN_ATTEMPTS.pop(ip, None)

    def get_token_from_request(self):
        """Extract session token from Authorization header, Cookie, or Query parameter."""
        # 1. Bearer Token
        auth_hdr = self.headers.get("Authorization", "")
        if auth_hdr.startswith("Bearer "):
            return auth_hdr[7:].strip()

        # 2. Cookie header: session_token=<hex>
        cookie_hdr = self.headers.get("Cookie", "")
        if cookie_hdr:
            for part in cookie_hdr.split(";"):
                part = part.strip()
                if part.startswith("session_token="):
                    return part.split("=", 1)[1].strip()

        # 3. URL Query parameter ?token=<hex>
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        token_param = query.get("token", [None])[0]
        if token_param:
            return token_param.strip()

        return None

    def get_authenticated_user(self):
        """Validate request token against database sessions and return user dict."""
        token = self.get_token_from_request()
        if not token:
            return None
        return database.get_user_by_session(token)

    def require_admin(self):
        """
        Server-side role-based access control guard.
        Validates administrator session. Returns user dict on success,
        or sends HTTP 401/403 and returns None on failure.
        """
        user = self.get_authenticated_user()
        if not user:
            self.send_json({
                "success": False,
                "error": "Authentication required. Please log in as an administrator."
            }, status=401)
            return None

        if str(user.get("status", "")).lower() == "suspended":
            self.send_json({
                "success": False,
                "error": "Access denied: Your administrator account has been suspended."
            }, status=403)
            return None

        if str(user.get("role", "")).lower() != "admin":
            self.send_json({
                "success": False,
                "error": "Forbidden: Administrator privileges required to access this resource."
            }, status=403)
            return None

        return user

    def send_json(self, obj, status=200, extra_headers=None):
        """Helper to send JSON response with standard CORS & cache headers."""
        payload = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(payload)

    # -------------------------------------------------------------------------
    # HTTP GET Request Handler
    # -------------------------------------------------------------------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Main Student Portal & Login Screen
        if path in ("/", "/index.html", "/login"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode("utf-8"))

        # 2. Admin Dashboard Frontend
        elif path in ("/admin", "/admin/"):
            if os.path.exists(ADMIN_HTML_PATH):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(ADMIN_HTML_PATH, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "admin.html not found on server")

        # 3. View Academic Project Report HTML
        elif path in ("/report", "/PROJECT_REPORT.html"):
            report_file = os.path.join(BASE_DIR, "PROJECT_REPORT.html")
            if os.path.exists(report_file):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(report_file, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "Report not found")

        # 4. Direct In-Browser File Viewer & Mobile Downloader
        elif path == "/api/view":
            mat_id = query.get("id", [None])[0]
            if not mat_id:
                self.send_error(400, "Missing ID")
                return

            record = database.get_material_by_id(mat_id)
            if not record:
                self.send_error(404, "Material record not found")
                return

            # Check if material is quarantined
            mat_status = record[9] if len(record) > 9 else "active"
            if mat_status == "quarantined":
                req_user = self.get_authenticated_user()
                if not req_user or str(req_user.get("role", "")).lower() != "admin":
                    self.send_response(403)
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                    self.end_headers()
                    self.wfile.write(
                        b"<h2>Material Quarantined</h2><p>This study material is currently under administrative review.</p>"
                    )
                    return

            stored_path = record[6]
            resolved_path = resolve_file_path(stored_path)

            if not resolved_path:
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(
                    f"<h2>File not found on server</h2><p>Stored: {stored_path}</p><p>Please re-upload this material using the portal.</p>".encode("utf-8")
                )
                return

            # Track download metric
            database.increment_download_count(mat_id)

            # Determine MIME type accurately with office/pdf fallbacks
            content_type, _ = mimetypes.guess_type(resolved_path)
            if not content_type:
                ext = os.path.splitext(resolved_path)[1].lower()
                if ext == ".pdf":
                    content_type = "application/pdf"
                elif ext in (".ppt", ".pptx"):
                    content_type = "application/vnd.ms-powerpoint" if ext == ".ppt" else "application/vnd.openxmlformats-officedocument.presentationml.presentation"
                elif ext in (".doc", ".docx"):
                    content_type = "application/msword" if ext == ".doc" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                elif ext == ".zip":
                    content_type = "application/zip"
                else:
                    content_type = "application/octet-stream"

            filename = os.path.basename(resolved_path)
            file_size = os.path.getsize(resolved_path)

            download_param = query.get("download", ["0"])[0] == "1"
            is_previewable = content_type in (
                "application/pdf", "image/png", "image/jpeg", 
                "image/gif", "image/webp", "text/plain", "text/html"
            )

            if download_param or not is_previewable:
                disposition = f"attachment; filename=\"{filename}\""
            else:
                disposition = f"inline; filename=\"{filename}\""

            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Content-Disposition", disposition)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "public, max-age=3600")
            self.end_headers()

            try:
                with open(resolved_path, "rb") as f:
                    while True:
                        chunk = f.read(65536)
                        if not chunk:
                            break
                        self.wfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                pass

        # 5. API: Dashboard Stats (Public Student Portal)
        elif path == "/api/stats":
            stats = database.get_dashboard_stats()
            self.send_json(stats)

        # 6. API: Materials List (Public Student Portal - active materials only)
        elif path == "/api/materials":
            search_query = query.get("search", [""])[0]
            semester = query.get("semester", ["All"])[0]
            material_type = query.get("type", ["All"])[0]
            only_fav = query.get("favorites", ["0"])[0] == "1"

            rows = database.get_materials(
                search_query=search_query,
                semester=semester,
                material_type=material_type,
                only_favorites=only_fav
            )

            result = []
            for r in rows:
                status_val = r[9] if len(r) > 9 else "active"
                if status_val == "quarantined":
                    continue
                result.append({
                    "id": r[0],
                    "title": r[1],
                    "subject": r[2],
                    "topic": r[3],
                    "semester": r[4],
                    "material_type": r[5],
                    "file_path": r[6],
                    "date_added": r[7],
                    "favorite": r[8]
                })
            self.send_json(result)

        # 7. API: Launch on Desktop via Windows OS
        elif path == "/api/open":
            mat_id = query.get("id", [None])[0]
            if not mat_id:
                self.send_json({"success": False, "message": "Missing ID"})
                return

            record = database.get_material_by_id(mat_id)
            if not record:
                self.send_json({"success": False, "message": "Material not found in database"})
                return

            stored_path = record[6]
            resolved_path = resolve_file_path(stored_path)
            if not resolved_path:
                self.send_json({
                    "success": False,
                    "message": f"File not found on server or disk: {stored_path}"
                })
                return

            try:
                if hasattr(os, "startfile"):
                    os.startfile(resolved_path)
                else:
                    webbrowser.open(f"file://{os.path.abspath(resolved_path)}")
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"success": False, "message": f"Could not open file: {e}"})

        # ---------------------------------------------------------------------
        # ADMIN API ENDPOINTS (PROTECTED VIA require_admin)
        # ---------------------------------------------------------------------
        elif path == "/api/admin/overview":
            user = self.require_admin()
            if not user:
                return
            stats = database.get_admin_dashboard_stats()
            self.send_json({"success": True, "stats": stats})

        elif path == "/api/admin/files":
            user = self.require_admin()
            if not user:
                return
            q_str = query.get("search", [""])[0]
            subj = query.get("subject", ["All"])[0]
            m_type = query.get("type", ["All"])[0]
            status_f = query.get("status", ["All"])[0]
            sort_by = query.get("sort_by", ["id"])[0]
            sort_order = query.get("sort_order", ["desc"])[0]
            page = int(query.get("page", ["1"])[0] or 1)
            per_page = int(query.get("per_page", ["10"])[0] or 10)

            data = database.get_all_materials_admin(
                search_query=q_str,
                subject=subj,
                material_type=m_type,
                status=status_f,
                sort_by=sort_by,
                sort_order=sort_order,
                page=page,
                per_page=per_page
            )
            self.send_json({"success": True, **data})

        elif path == "/api/admin/files/export":
            user = self.require_admin()
            if not user:
                return
            q_str = query.get("search", [""])[0]
            subj = query.get("subject", ["All"])[0]

            data = database.get_all_materials_admin(
                search_query=q_str,
                subject=subj,
                per_page=10000
            )
            materials = data.get("materials", [])

            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["ID", "Title", "Subject", "Topic", "Semester", "Type", "File Size Bytes", "Uploader", "Status", "Downloads", "Date Added"])
            for m in materials:
                writer.writerow([
                    m.get("id"),
                    m.get("title"),
                    m.get("subject"),
                    m.get("topic") or "",
                    m.get("semester"),
                    m.get("material_type"),
                    m.get("file_size"),
                    m.get("uploader_name") or "Student",
                    m.get("status"),
                    m.get("download_count"),
                    m.get("date_added")
                ])

            csv_bytes = output.getvalue().encode("utf-8-sig")
            self.send_response(200)
            self.send_header("Content-Type", "text/csv; charset=utf-8")
            self.send_header("Content-Disposition", 'attachment; filename="studymate_materials_export.csv"')
            self.send_header("Content-Length", str(len(csv_bytes)))
            self.end_headers()
            self.wfile.write(csv_bytes)

        elif path == "/api/admin/users":
            user = self.require_admin()
            if not user:
                return
            q_str = query.get("search", [""])[0]
            role = query.get("role", ["All"])[0]
            status = query.get("status", ["All"])[0]
            page = int(query.get("page", ["1"])[0] or 1)
            per_page = int(query.get("per_page", ["10"])[0] or 10)

            data = database.get_all_users_admin(
                search_query=q_str,
                role=role,
                status=status,
                page=page,
                per_page=per_page
            )
            self.send_json({"success": True, **data})

        elif path == "/api/admin/categories":
            user = self.require_admin()
            if not user:
                return
            categories = database.get_all_categories()
            self.send_json({"success": True, "categories": categories})

        elif path == "/api/admin/reports":
            user = self.require_admin()
            if not user:
                return
            status = query.get("status", ["All"])[0]
            page = int(query.get("page", ["1"])[0] or 1)
            per_page = int(query.get("per_page", ["10"])[0] or 10)

            data = database.get_all_reports_admin(
                status=status,
                page=page,
                per_page=per_page
            )
            self.send_json({"success": True, **data})

        elif path == "/api/admin/audit_logs":
            user = self.require_admin()
            if not user:
                return
            q_str = query.get("search", [""])[0]
            action = query.get("action", ["All"])[0]
            page = int(query.get("page", ["1"])[0] or 1)
            per_page = int(query.get("per_page", ["15"])[0] or 15)

            data = database.get_audit_logs(
                search_query=q_str,
                action=action,
                page=page,
                per_page=per_page
            )
            self.send_json({"success": True, **data})

        elif path == "/api/admin/storage":
            user = self.require_admin()
            if not user:
                return
            info = database.get_storage_breakdown(UPLOADS_DIR)
            self.send_json({"success": True, "storage": info})

        elif path == "/api/admin/settings":
            user = self.require_admin()
            if not user:
                return
            settings = database.get_all_settings()
            self.send_json({"success": True, "settings": settings})

        else:
            self.send_error(404, "Page Not Found")

    # -------------------------------------------------------------------------
    # HTTP POST Request Handler
    # -------------------------------------------------------------------------
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        ip = self.get_client_ip()

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            data = json.loads(body) if body else {}
        except Exception:
            data = {}

        # 1. API: User / Admin Login (With Rate Limiting, Audit Logs, and Session Tokens)
        if path == "/api/login":
            allowed, wait_sec = self.check_rate_limit(ip)
            if not allowed:
                self.send_json({
                    "success": False,
                    "error": f"Too many failed login attempts. Please wait {wait_sec} seconds before trying again."
                }, status=429)
                return

            username = data.get("username", "").strip()
            password = data.get("password", "").strip()
            if not username or not password:
                self.send_json({"success": False, "error": "Username and password are required."}, status=400)
                return

            user = database.authenticate_user(username, password)
            if user:
                if str(user.get("status", "")).lower() == "suspended":
                    self.send_json({
                        "success": False,
                        "error": "Your account has been suspended by an administrator."
                    }, status=403)
                    return

                self.reset_failed_logins(ip)
                token = database.create_session(user["id"], user_agent=self.headers.get("User-Agent", ""))
                database.add_audit_log(
                    admin_id=user["id"],
                    admin_username=user["username"],
                    action="LOGIN_SUCCESS",
                    entity_type="auth",
                    entity_id=user["id"],
                    details=f"User signed in successfully with role '{user.get('role', 'Student')}'",
                    ip_address=ip,
                    status="success"
                )
                cookie_val = f"session_token={token}; Path=/; HttpOnly; SameSite=Lax"
                self.send_json(
                    {"success": True, "user": user, "token": token},
                    extra_headers={"Set-Cookie": cookie_val}
                )
            else:
                self.record_failed_login(ip)
                database.add_audit_log(
                    admin_id=None,
                    admin_username=username,
                    action="LOGIN_FAILED",
                    entity_type="auth",
                    details=f"Failed login attempt for username '{username}'",
                    ip_address=ip,
                    status="failed"
                )
                self.send_json({
                    "success": False,
                    "error": "Invalid username or password. Please try again."
                }, status=401)

        # 2. API: Logout
        elif path == "/api/logout":
            token = self.get_token_from_request()
            user = database.get_user_by_session(token) if token else None
            if token:
                database.delete_session(token)
            if user:
                database.add_audit_log(
                    admin_id=user["id"],
                    admin_username=user["username"],
                    action="LOGOUT",
                    entity_type="auth",
                    entity_id=user["id"],
                    details="User signed out",
                    ip_address=ip,
                    status="success"
                )
            clear_cookie = "session_token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:00 GMT; HttpOnly; SameSite=Lax"
            self.send_json({"success": True}, extra_headers={"Set-Cookie": clear_cookie})

        # 3. API: User Registration
        elif path == "/api/register":
            allow_reg = database.get_setting("allow_student_registration", "true")
            if str(allow_reg).lower() == "false":
                self.send_json({
                    "success": False,
                    "error": "Student self-registration is currently disabled by administrator."
                }, status=403)
                return

            username = data.get("username", "").strip()
            password = data.get("password", "").strip()
            full_name = data.get("full_name", "").strip()
            email = data.get("email", "").strip()

            success, result = database.register_user(username, password, full_name, role="Student", email=email)
            if success:
                user = database.authenticate_user(username, password)
                token = database.create_session(user["id"], user_agent=self.headers.get("User-Agent", ""))
                database.add_audit_log(
                    admin_id=user["id"],
                    admin_username=user["username"],
                    action="USER_REGISTER",
                    entity_type="user",
                    entity_id=user["id"],
                    details=f"New student registration for '{username}'",
                    ip_address=ip,
                    status="success"
                )
                cookie_val = f"session_token={token}; Path=/; HttpOnly; SameSite=Lax"
                self.send_json({
                    "success": True,
                    "user": user,
                    "token": token,
                    "message": "Account created successfully!"
                }, extra_headers={"Set-Cookie": cookie_val})
            else:
                self.send_json({"success": False, "error": result}, status=400)

        # 4. API: Upload & Save Material (Validates size, extensions, and maintenance mode)
        elif path == "/api/upload":
            user = self.get_authenticated_user()

            # Maintenance mode check
            maintenance = database.get_setting("maintenance_mode", "false")
            if str(maintenance).lower() == "true":
                if not user or str(user.get("role", "")).lower() != "admin":
                    self.send_json({
                        "success": False,
                        "error": "StudyMate is currently under maintenance. File uploads are temporarily paused."
                    }, status=503)
                    return

            try:
                title = data.get("title", "").strip()
                subject = data.get("subject", "").strip()
                topic = data.get("topic", "").strip()
                semester = int(data.get("semester", 3))
                material_type = data.get("material_type", "Notes").strip()
                raw_filename = data.get("filename", "uploaded_file.bin")
                file_b64 = data.get("file_base64", "")
                description = data.get("description", "").strip()

                if not title or not subject:
                    self.send_json({"success": False, "error": "Title and subject are required."}, status=400)
                    return

                # Extension validation
                f_ext = os.path.splitext(raw_filename)[1].lower().lstrip(".")
                allowed_ext_str = database.get_setting("allowed_extensions", "pdf,ppt,pptx,doc,docx,txt,zip,rar,png,jpg,jpeg")
                allowed_list = [x.strip().lower() for x in allowed_ext_str.split(",") if x.strip()]
                if f_ext not in allowed_list:
                    self.send_json({
                        "success": False,
                        "error": f"File type '.{f_ext}' is not allowed. Permitted types: {allowed_ext_str}"
                    }, status=400)
                    return

                # Decode file bytes
                file_bytes = base64.b64decode(file_b64)
                file_size = len(file_bytes)

                # Size validation
                max_mb = int(database.get_setting("max_upload_size_mb", "25"))
                if file_size > max_mb * 1024 * 1024:
                    self.send_json({
                        "success": False,
                        "error": f"File size ({file_size // (1024*1024)} MB) exceeds server limit of {max_mb} MB."
                    }, status=400)
                    return

                # Sanitize filename against directory traversal
                clean_name = os.path.basename(raw_filename.replace("\\", "/"))
                safe_name = "".join(c for c in clean_name if c.isalnum() or c in "._- ").strip().replace(" ", "_")
                if not safe_name:
                    safe_name = "upload.bin"

                dest_path = os.path.join(UPLOADS_DIR, safe_name)
                base_name, ext = os.path.splitext(safe_name)
                counter = 1
                while os.path.exists(dest_path):
                    dest_path = os.path.join(UPLOADS_DIR, f"{base_name}_{counter}{ext}")
                    counter += 1

                with open(dest_path, "wb") as f:
                    f.write(file_bytes)

                saved_filename = os.path.basename(dest_path)
                relative_path = f"uploads/{saved_filename}"

                uploader_id = user["id"] if user else None
                uploader_name = (user.get("full_name") or user.get("username")) if user else "Student"

                new_id = database.add_material(
                    title=title,
                    subject=subject,
                    topic=topic,
                    semester=semester,
                    material_type=material_type,
                    file_path=relative_path,
                    uploader_id=uploader_id,
                    uploader_name=uploader_name,
                    file_size=file_size,
                    status="active",
                    description=description
                )

                database.add_audit_log(
                    admin_id=uploader_id,
                    admin_username=uploader_name,
                    action="MATERIAL_UPLOAD",
                    entity_type="material",
                    entity_id=new_id,
                    details=f"Uploaded '{title}' ({saved_filename}, {file_size} bytes)",
                    ip_address=ip,
                    status="success"
                )

                self.send_json({"success": True, "id": new_id, "file_path": relative_path})

            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status=500)

        # 5. API: Toggle Favorite
        elif path == "/api/toggle_favorite":
            mat_id = data.get("id")
            new_status = database.toggle_favorite(mat_id)
            self.send_json({"success": True, "new_status": new_status})

        # 6. API: Student Issue Reporting
        elif path == "/api/reports/submit":
            user = self.get_authenticated_user()
            mat_id = data.get("material_id")
            reason = data.get("reason", "").strip()
            details = data.get("details", "").strip()

            if not mat_id or not reason:
                self.send_json({"success": False, "error": "Material ID and report reason are required."}, status=400)
                return

            rep_id = database.submit_report(
                material_id=int(mat_id),
                reporter_id=user["id"] if user else None,
                reporter_name=(user.get("full_name") or user.get("username")) if user else "Student",
                reason=reason,
                details=details
            )

            database.add_audit_log(
                admin_id=user["id"] if user else None,
                admin_username=(user.get("username") if user else "Student"),
                action="REPORT_SUBMITTED",
                entity_type="report",
                entity_id=rep_id,
                details=f"Reported material #{mat_id} for '{reason}'",
                ip_address=ip,
                status="success"
            )

            self.send_json({"success": True, "report_id": rep_id})

        # ---------------------------------------------------------------------
        # ADMIN POST ACTIONS (PROTECTED VIA require_admin)
        # ---------------------------------------------------------------------
        elif path == "/api/admin/files/rename":
            admin_user = self.require_admin()
            if not admin_user:
                return
            mat_id = data.get("id")
            new_title = data.get("new_title", "").strip()
            new_filename = data.get("new_filename", "").strip()
            success, msg = database.admin_rename_material(mat_id, new_title, new_filename, UPLOADS_DIR)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="FILE_RENAME",
                entity_type="material",
                entity_id=mat_id,
                details=f"Renamed material #{mat_id} -> Title: '{new_title}', File: '{new_filename}' ({msg})",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/files/edit":
            admin_user = self.require_admin()
            if not admin_user:
                return
            mat_id = data.get("id")
            success, msg = database.admin_edit_material_metadata(
                material_id=mat_id,
                title=data.get("title", "").strip(),
                subject=data.get("subject", "").strip(),
                topic=data.get("topic", "").strip(),
                semester=int(data.get("semester", 3)),
                material_type=data.get("material_type", "Notes").strip(),
                status=data.get("status", "active").strip(),
                description=data.get("description", "").strip()
            )
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="METADATA_EDIT",
                entity_type="material",
                entity_id=mat_id,
                details=f"Edited metadata for material #{mat_id}: {msg}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/files/quarantine":
            admin_user = self.require_admin()
            if not admin_user:
                return
            mat_id = data.get("id")
            action = data.get("action", "quarantine")
            is_quarantine = (action == "quarantine")
            success, msg = database.admin_quarantine_material(mat_id, quarantine=is_quarantine)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="FILE_QUARANTINE" if is_quarantine else "FILE_UNQUARANTINE",
                entity_type="material",
                entity_id=mat_id,
                details=f"{action.capitalize()} material #{mat_id}: {msg}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/files/delete":
            admin_user = self.require_admin()
            if not admin_user:
                return
            single_id = data.get("id")
            bulk_ids = data.get("ids", [])
            ids_to_delete = [single_id] if single_id else bulk_ids

            deleted_count = 0
            errors = []
            for mid in ids_to_delete:
                success, msg = database.admin_delete_material(mid, UPLOADS_DIR)
                if success:
                    deleted_count += 1
                else:
                    errors.append(f"#{mid}: {msg}")

            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="FILE_DELETE",
                entity_type="material",
                details=f"Deleted {deleted_count} material(s): {ids_to_delete}",
                ip_address=ip,
                status="success" if deleted_count > 0 else "failed"
            )

            if deleted_count > 0 or not errors:
                self.send_json({"success": True, "deleted_count": deleted_count, "errors": errors})
            else:
                self.send_json({"success": False, "error": "; ".join(errors)}, status=400)

        elif path == "/api/admin/users/status":
            admin_user = self.require_admin()
            if not admin_user:
                return
            user_id = data.get("user_id")
            new_status = data.get("status", "active")
            success, msg = database.update_user_status(user_id, new_status)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="USER_STATUS_CHANGE",
                entity_type="user",
                entity_id=user_id,
                details=f"Updated user #{user_id} status to '{new_status}': {msg}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/users/role":
            admin_user = self.require_admin()
            if not admin_user:
                return
            user_id = data.get("user_id")
            new_role = data.get("role", "Student")
            success, msg = database.update_user_role(user_id, new_role)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="USER_ROLE_CHANGE",
                entity_type="user",
                entity_id=user_id,
                details=f"Updated user #{user_id} role to '{new_role}': {msg}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/users/delete":
            admin_user = self.require_admin()
            if not admin_user:
                return
            user_id = data.get("user_id")
            success, msg = database.delete_user(user_id)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="USER_DELETE",
                entity_type="user",
                entity_id=user_id,
                details=f"Deleted user #{user_id}: {msg}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/categories/create":
            admin_user = self.require_admin()
            if not admin_user:
                return
            name = data.get("name", "").strip()
            code = data.get("code", "").strip()
            semester = int(data.get("semester", 3))
            desc = data.get("description", "").strip()
            success, msg = database.create_category(name, code, semester, desc)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="CATEGORY_CREATE",
                entity_type="category",
                details=f"Created subject '{name}' ({code})",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/categories/edit":
            admin_user = self.require_admin()
            if not admin_user:
                return
            cat_id = data.get("id")
            name = data.get("name", "").strip()
            code = data.get("code", "").strip()
            semester = int(data.get("semester", 3))
            desc = data.get("description", "").strip()
            success, msg = database.update_category(cat_id, name, code, semester, desc)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="CATEGORY_EDIT",
                entity_type="category",
                entity_id=cat_id,
                details=f"Updated subject #{cat_id} '{name}': {msg}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/categories/delete":
            admin_user = self.require_admin()
            if not admin_user:
                return
            cat_id = data.get("id")
            reassign_to = data.get("reassign_to")
            success, msg = database.delete_category(cat_id, reassign_to)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="CATEGORY_DELETE",
                entity_type="category",
                entity_id=cat_id,
                details=f"Deleted subject #{cat_id} (reassigned to '{reassign_to}'): {msg}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/categories/merge":
            admin_user = self.require_admin()
            if not admin_user:
                return
            src = data.get("source_name", "").strip()
            dst = data.get("target_name", "").strip()
            success, msg = database.merge_categories(src, dst)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="CATEGORY_MERGE",
                entity_type="category",
                details=f"Merged subject '{src}' into '{dst}': {msg}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/reports/resolve":
            admin_user = self.require_admin()
            if not admin_user:
                return
            rep_id = data.get("report_id")
            new_status = data.get("status", "resolved")
            admin_notes = data.get("admin_notes", "").strip()
            success, msg = database.resolve_report(rep_id, admin_user["id"], new_status, admin_notes)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="REPORT_RESOLVE",
                entity_type="report",
                entity_id=rep_id,
                details=f"Moderated report #{rep_id} as '{new_status}': {admin_notes}",
                ip_address=ip,
                status="success" if success else "failed"
            )
            if success:
                self.send_json({"success": True, "message": msg})
            else:
                self.send_json({"success": False, "error": msg}, status=400)

        elif path == "/api/admin/storage/scan":
            admin_user = self.require_admin()
            if not admin_user:
                return
            scan = database.scan_storage_consistency(UPLOADS_DIR)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="STORAGE_SCAN",
                entity_type="storage",
                details=f"Consistency scan: {scan['valid_count']} valid, {scan['missing_count']} missing, {scan['orphaned_count']} orphaned",
                ip_address=ip,
                status="success"
            )
            self.send_json({"success": True, "scan": scan})

        elif path == "/api/admin/settings/update":
            admin_user = self.require_admin()
            if not admin_user:
                return
            k = data.get("key", "").strip()
            v = str(data.get("value", "")).strip()
            if not k:
                self.send_json({"success": False, "error": "Setting key is required."}, status=400)
                return
            database.set_setting(k, v)
            database.add_audit_log(
                admin_id=admin_user["id"],
                admin_username=admin_user["username"],
                action="SETTING_UPDATE",
                entity_type="setting",
                details=f"Updated setting '{k}' = '{v}'",
                ip_address=ip,
                status="success"
            )
            self.send_json({"success": True, "message": f"Setting '{k}' updated successfully."})

        else:
            self.send_error(404, "Endpoint Not Found")


def start_server():
    """Start StudyMate production web server with admin control."""
    database.init_db()

    # 1. Automatic Environment Variable Administrator provisioning (Render / Cloud deployment)
    env_admin_user = os.environ.get("ADMIN_USERNAME", "").strip()
    env_admin_pass = os.environ.get("ADMIN_PASSWORD", "").strip()
    if env_admin_user and env_admin_pass:
        existing = database.get_user_by_username(env_admin_user)
        if not existing:
            database.register_user(env_admin_user, env_admin_pass, "System Administrator", role="Admin", email="admin@studymate.local")
            print(f"[Admin Setup] Created environment administrator: {env_admin_user}")

    # 2. Guarantee at least one active administrator exists for zero-friction evaluation
    if database.count_active_admins() == 0:
        database.register_user("admin", "Admin@123", "System Administrator", role="Admin", email="admin@studymate.local")
        print("[Admin Setup] Seeded default administrator account: admin / Admin@123")

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer((HOST, PORT), StudyMateHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 60)
        print(" StudyMate Production Server Running with Admin Control")
        print(f" Listening on: http://{HOST}:{PORT} (Local: {url})")
        print(f" Admin Panel URL: {url}/admin")
        print(f" Uploads directory: {UPLOADS_DIR}")
        print("=" * 60)
        
        # Only open browser if running locally on Windows desktop
        if os.environ.get("DEPLOY_ENV") != "production" and sys.platform.startswith("win"):
            try:
                webbrowser.open(url)
            except Exception:
                pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
            httpd.server_close()


if __name__ == "__main__":
    start_server()
