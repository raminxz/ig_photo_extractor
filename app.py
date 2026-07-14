# -*- coding: utf-8 -*-
"""
استخراج‌کننده عکس‌های اینستاگرام
اپلیکیشن فلسک برای دانلود تمام عکس‌های یک پیج عمومی اینستاگرام
با قابلیت مکث/ادامه و نمایش پیشرفت زنده
"""

import os
import json
import time
import shutil
import threading
import zipfile
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file
import instaloader

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOWNLOADS_DIR = os.path.join(BASE_DIR, "downloads")
STATE_FILE = os.path.join(BASE_DIR, "state.json")

os.makedirs(DOWNLOADS_DIR, exist_ok=True)

# --------------------------------------------------------------------------
# وضعیت مشترک بین ترد پس‌زمینه و رابط وب
# --------------------------------------------------------------------------
lock = threading.Lock()

state = {
    "status": "idle",          # idle | running | paused | done | error | stopped
    "username": None,
    "total_posts_seen": 0,
    "photos_downloaded": 0,
    "videos_skipped": 0,
    "current_post": None,
    "log": [],
    "error": None,
    "downloaded_shortcodes": [],   # برای پشتیبانی از resume
    "started_at": None,
    "finished_at": None,
}

pause_event = threading.Event()   # وقتی ست باشه یعنی در حال اجراست
stop_event = threading.Event()    # وقتی ست باشه یعنی باید متوقف بشه
worker_thread = None


def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    with lock:
        state["log"].append(f"[{ts}] {msg}")
        state["log"] = state["log"][-200:]  # فقط ۲۰۰ خط آخر رو نگه دار


def save_state_to_disk():
    with lock:
        data = dict(state)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load_state_from_disk(username):
    """اگه قبلاً برای همین یوزرنیم دانلودی انجام شده، شورت‌کدهای دانلود شده رو برمی‌گردونه."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("username") == username:
                return data.get("downloaded_shortcodes", [])
        except Exception:
            pass
    return []


def scrape_worker(username, max_posts):
    global state

    target_dir = os.path.join(DOWNLOADS_DIR, username)
    os.makedirs(target_dir, exist_ok=True)

    already_done = set(load_state_from_disk(username))

    with lock:
        state["status"] = "running"
        state["username"] = username
        state["error"] = None
        state["downloaded_shortcodes"] = list(already_done)
        state["photos_downloaded"] = len(already_done)
        state["started_at"] = state["started_at"] or datetime.now().isoformat()

    log(f"شروع استخراج برای پیج: {username}")
    if already_done:
        log(f"{len(already_done)} عکس از دفعه قبل موجوده؛ ادامه از همون نقطه...")

    try:
        L = instaloader.Instaloader(
            dirname_pattern=target_dir,
            filename_pattern="{shortcode}",
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False,
            post_metadata_txt_pattern="",
            quiet=True,
        )

        profile = instaloader.Profile.from_username(L.context, username)

        with lock:
            state["total_posts_seen"] = profile.mediacount

        log(f"پیج پیدا شد. تعداد کل پست‌ها: {profile.mediacount}")

        count_seen = 0
        for post in profile.get_posts():
            # بررسی توقف کامل
            if stop_event.is_set():
                log("توقف توسط کاربر درخواست شد.")
                with lock:
                    state["status"] = "stopped"
                save_state_to_disk()
                return

            # بررسی مکث - منتظر می‌مونه تا کاربر ادامه بده
            while pause_event.is_set() and not stop_event.is_set():
                with lock:
                    state["status"] = "paused"
                time.sleep(0.5)

            if stop_event.is_set():
                with lock:
                    state["status"] = "stopped"
                save_state_to_disk()
                return

            with lock:
                state["status"] = "running"

            count_seen += 1
            if max_posts and count_seen > max_posts:
                log(f"به سقف {max_posts} پست رسیدیم. توقف.")
                break

            with lock:
                state["current_post"] = post.shortcode

            if post.shortcode in already_done:
                continue  # قبلاً دانلود شده، رد شو (resume)

            try:
                if post.typename == "GraphSidecar":
                    # پست چند تکه‌ای (آلبوم): فقط تکه‌های عکس رو نگه دار
                    for idx, node in enumerate(post.get_sidecar_nodes()):
                        if node.is_video:
                            with lock:
                                state["videos_skipped"] += 1
                            continue
                        L.download_pic(
                            filename=os.path.join(target_dir, f"{post.shortcode}_{idx+1}"),
                            url=node.display_url,
                            mtime=post.date_utc,
                        )
                elif post.is_video:
                    with lock:
                        state["videos_skipped"] += 1
                    continue
                else:
                    L.download_pic(
                        filename=os.path.join(target_dir, post.shortcode),
                        url=post.url,
                        mtime=post.date_utc,
                    )

                already_done.add(post.shortcode)
                with lock:
                    state["photos_downloaded"] += 1
                    state["downloaded_shortcodes"] = list(already_done)

                log(f"دانلود شد: {post.shortcode}")
                save_state_to_disk()

                # وقفه کوتاه برای جلوگیری از محدودیت نرخ اینستاگرام
                time.sleep(1.5)

            except Exception as e:
                log(f"خطا در دانلود پست {post.shortcode}: {e}")
                time.sleep(3)

        with lock:
            state["status"] = "done"
            state["finished_at"] = datetime.now().isoformat()
        log("استخراج کامل شد.")
        save_state_to_disk()

    except instaloader.exceptions.ProfileNotExistsException:
        with lock:
            state["status"] = "error"
            state["error"] = "این نام کاربری پیدا نشد."
        log("خطا: پیج پیدا نشد.")

    except instaloader.exceptions.ConnectionException as e:
        with lock:
            state["status"] = "error"
            state["error"] = f"خطای اتصال / احتمال محدودیت نرخ اینستاگرام: {e}"
        log(f"خطای اتصال: {e}")

    except Exception as e:
        with lock:
            state["status"] = "error"
            state["error"] = str(e)
        log(f"خطای غیرمنتظره: {e}")


# --------------------------------------------------------------------------
# مسیرهای وب
# --------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    global worker_thread

    with lock:
        if state["status"] == "running":
            return jsonify({"ok": False, "message": "یک استخراج در حال اجراست."})

    data = request.get_json(force=True)
    username = (data.get("username") or "").strip().lstrip("@")
    max_posts = data.get("max_posts")
    max_posts = int(max_posts) if max_posts else None

    if not username:
        return jsonify({"ok": False, "message": "نام کاربری وارد نشده."})

    # ریست وضعیت برای شروع جدید (مگر resume از همون یوزرنیم باشه)
    stop_event.clear()
    pause_event.clear()

    with lock:
        if state.get("username") != username:
            state["log"] = []
            state["photos_downloaded"] = 0
            state["videos_skipped"] = 0
            state["started_at"] = None
        state["status"] = "running"
        state["username"] = username

    worker_thread = threading.Thread(target=scrape_worker, args=(username, max_posts), daemon=True)
    worker_thread.start()

    return jsonify({"ok": True})


@app.route("/pause", methods=["POST"])
def pause():
    pause_event.set()
    with lock:
        state["status"] = "paused"
    log("مکث شد.")
    return jsonify({"ok": True})


@app.route("/resume", methods=["POST"])
def resume():
    pause_event.clear()
    with lock:
        state["status"] = "running"
    log("ادامه پیدا کرد.")
    return jsonify({"ok": True})


@app.route("/stop", methods=["POST"])
def stop():
    stop_event.set()
    pause_event.clear()
    return jsonify({"ok": True})


@app.route("/status")
def status():
    with lock:
        return jsonify(dict(state))


@app.route("/download-zip")
def download_zip():
    with lock:
        username = state.get("username")

    if not username:
        return jsonify({"ok": False, "message": "هنوز چیزی دانلود نشده."}), 400

    target_dir = os.path.join(DOWNLOADS_DIR, username)
    zip_path = os.path.join(BASE_DIR, f"{username}_photos.zip")

    if os.path.exists(zip_path):
        os.remove(zip_path)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(target_dir):
            for file in files:
                full_path = os.path.join(root, file)
                arcname = os.path.relpath(full_path, target_dir)
                zf.write(full_path, arcname)

    return send_file(zip_path, as_attachment=True, download_name=f"{username}_photos.zip")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
