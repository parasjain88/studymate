# 🚀 StudyMate Deployment Guide

StudyMate is engineered to be **100% self-contained** using Python's standard library with **zero external dependencies**. You can deploy it anywhere in less than 3 minutes.

---

## Option 1: Deploy on Render (Recommended — 100% Free)

Render allows you to host Python web services for free directly from GitHub.

### Steps:
1. **Push code to GitHub**:
   - Create a GitHub repository (e.g. `studymate`).
   - Push your project folder to GitHub:
     ```bash
     git init
     git add .
     git commit -m "Deploy StudyMate"
     git branch -M main
     git remote add origin https://github.com/<your-username>/studymate.git
     git push -u origin main
     ```
2. **Deploy on Render**:
   - Go to [render.com](https://render.com/) and sign in with GitHub.
   - Click **New +** $\rightarrow$ **Web Service**.
   - Select your `studymate` repository.
   - Configure the service:
     - **Name**: `studymate`
     - **Runtime**: `Python 3`
     - **Build Command**: *(leave empty)*
     - **Start Command**: `python web_app.py`
   - Click **Deploy Web Service**.
3. **Done!**
   Render will provide you with a live public URL (e.g., `https://studymate.onrender.com`).

---

## Option 2: Deploy on Railway

1. Go to [railway.app](https://railway.app/).
2. Click **New Project** $\rightarrow$ **Deploy from GitHub repo**.
3. Select your repository.
4. Railway automatically detects `Procfile` and deploys `python web_app.py`.
5. Under service settings, click **Generate Domain** to get your public URL.

---

## Option 3: Host on College Wi-Fi / Local Network (LAN)

You can run StudyMate on your laptop and let professors or classmates access it from their mobile phones or laptops on the same Wi-Fi network!

1. Find your laptop's local IP address:
   - Open Command Prompt and run:
     ```cmd
     ipconfig
     ```
   - Look for **IPv4 Address** (e.g., `192.168.1.45`).
2. Start the StudyMate server:
   ```cmd
   python web_app.py
   ```
3. Share the URL with anyone on the same Wi-Fi:
   ```text
   http://192.168.1.45:8000
   ```
   They can open it in Chrome or Safari on their phone or laptop and upload/view study materials!

---

## Option 4: Deploy using Docker

If you have Docker installed or are deploying to a VPS (DigitalOcean, AWS EC2, Linode):

1. **Build the Docker Image**:
   ```bash
   docker build -t studymate .
   ```
2. **Run the Container**:
   ```bash
   docker run -d -p 8000:8000 -v studymate_uploads:/app/uploads --name studymate-app studymate
   ```
3. Open `http://localhost:8000` in your browser.

---

## Summary of Deployment Files

| File | Purpose |
| :--- | :--- |
| `web_app.py` | Production HTTP server binding to `0.0.0.0`, reading `$PORT`, with mobile-first responsive UI |
| `Procfile` | Specifies `web: python web_app.py` for cloud platforms |
| `Dockerfile` | Containerized setup for cloud/VPS deployments |
| `render.yaml` | 1-click blueprint for Render.com |
| `requirements.txt`| Cloud build pack compatibility |

---

## 📱 Mobile Experience on Render

StudyMate is optimized for Android & iOS smartphones:

- **Mobile App Header**: Sticky top navigation bar with hamburger menu (☰) and profile avatar.
- **Slide-Out Off-Canvas Drawer**: Smooth slide-in sidebar with backdrop blur and touch dismiss.
- **Bottom Navigation Bar**: Fixed thumb-friendly app bar (Home, Upload, Search, Favorites) positioned within safe display areas.
- **Responsive Tables**: Touch-scrollable table containers with swipe indicators preventing horizontal layout shifts.
- **Native File Picker**: Tapping the upload zone opens the device's native file selector (Documents, Camera, Gallery, Files).
- **iOS & Android Form Optimization**: Inputs use `16px` font sizing to prevent automatic browser zoom on mobile focus.
- **In-Browser File Viewing**: Tapping **👁️ View** opens uploaded study materials directly inside mobile PDF/browser viewers.

### Updating Your Live Deployment on Render:
When you make changes locally, simply push them to your repository:
```bash
git add .
git commit -m "Update mobile responsive UI"
git push origin main
```
Render will automatically detect the commit and redeploy your service within 1–2 minutes!
