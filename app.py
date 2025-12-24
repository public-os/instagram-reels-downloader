import os
import re
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import yt_dlp
import logging

# --- Configuration ---
DOWNLOADS_DIR = Path("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Needed for flash messages

# --- Download function ---
def download_instagram_reel(url: str, user_id: str):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"reel_{user_id}_{timestamp}.mp4"
    filepath = DOWNLOADS_DIR / filename

    ydl_opts = {
        'format': 'best[ext=mp4]',
        'outtmpl': str(filepath),
        'quiet': True,
        'no_warnings': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if filepath.exists():
                return {
                    "status": "success",
                    "file_path": str(filepath),
                    "file_name": filename,
                    "title": info.get('title', 'Instagram Reel')
                }
            else:
                return {"status": "error", "message": "Download failed"}
    except Exception as e:
        logger.error(f"Download error: {e}")
        return {"status": "error", "message": str(e)}

# --- Routes ---

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/instagram-downloader", methods=["GET", "POST"])
def instagram_downloader():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            flash("Please provide an Instagram link", "danger")
            return redirect(url_for("instagram_downloader"))

        # Validate Instagram URL
        pattern = r'https?://(www\.)?instagram\.com/(p|reel|tv)/[A-Za-z0-9_-]+/?'
        if not re.match(pattern, url):
            flash("Invalid Instagram URL", "danger")
            return redirect(url_for("instagram_downloader"))

        # Download
        result = download_instagram_reel(url, "webuser")
        if result["status"] == "success":
            flash(f"Downloaded: {result['title']}", "success")
            return send_file(result["file_path"], as_attachment=True)
        else:
            flash(f"Error: {result.get('message', 'Unknown error')}", "danger")
            return redirect(url_for("instagram_downloader"))

    return render_template("instagram_downloader.html")

@app.route("/profile")
def profile():
    # Placeholder user profile
    user_info = {
        "username": "webuser",
        "downloads_count": len(list(DOWNLOADS_DIR.glob("*.mp4")))
    }
    return render_template("profile.html", user=user_info)

@app.route("/history")
def history():
    files = list(DOWNLOADS_DIR.glob("*.mp4"))
    files_info = []
    for f in files:
        files_info.append({
            "name": f.name,
            "size_mb": f.stat().st_size / (1024*1024),
            "created": datetime.fromtimestamp(f.stat().st_ctime).strftime("%Y-%m-%d %H:%M:%S")
        })
    return render_template("history.html", files=files_info)

# --- Run app ---
if __name__ == "__main__":
    app.run(debug=True)
