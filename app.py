from flask import Flask, render_template, redirect, request, session
import psutil
import socket
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import os
import logging

app = Flask(__name__)

app.secret_key = os.getenv("STATUS_SECRET", "change-me")
SESSION_TIMEOUT = timedelta(minutes=30)

STATUS_USER = os.getenv("STATUS_USER")
STATUS_PASS = os.getenv("STATUS_PASS")

log = logging.getLogger("status-page")
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(message)s")
handler.setFormatter(formatter)
log.addHandler(handler)

logging.getLogger("werkzeug").setLevel(logging.ERROR)

def format_disk(size_bytes):
    gb = size_bytes / (1024 ** 3)
    if gb >= 1024:
        return f"{gb / 1024:.1f} TB"
    return f"{gb:.1f} GB"

def get_os():
    try:
        data = Path("/host/etc/os-release").read_text()
        for line in data.splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "Unknown"

def get_ip():
    try:
        result = subprocess.check_output(
            ["ip", "route", "get", "1.1.1.1"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return result.split("src")[1].split()[0]
    except Exception:
        return "N/A"

def is_logged_in():
    last = session.get("last_activity")
    if not last:
        return False
    if datetime.utcnow() - datetime.fromisoformat(last) > SESSION_TIMEOUT:
        session.clear()
        return False
    session["last_activity"] = datetime.utcnow().isoformat()
    return True

def get_system_status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "hostname": socket.gethostname(),
        "os_info": get_os(),
        "ip_address": get_ip(),
        "uptime": str(
            datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        ).split(".")[0],
        "cpu_percent": psutil.cpu_percent(),
        "memory_used": round(memory.used / (1024 ** 3), 1),
        "memory_total": round(memory.total / (1024 ** 3), 1),
        "memory_percent": memory.percent,
        "disk_used": format_disk(disk.used),
        "disk_total": format_disk(disk.total),
        "disk_percent": disk.percent,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == STATUS_USER and request.form.get("password") == STATUS_PASS:
            session["logged_in"] = True
            session["last_activity"] = datetime.utcnow().isoformat()
            log.info(f"LOGIN OK user={STATUS_USER} ip={request.remote_addr}")
            return redirect("/")
        log.info(f"LOGIN FAIL user={request.form.get('username')} ip={request.remote_addr}")
    return render_template("login.html")

@app.route("/logout")
def logout():
    log.info(f"LOGOUT ip={request.remote_addr}")
    session.clear()
    return redirect("/login")

@app.route("/")
def index():
    if not is_logged_in():
        return redirect("/login")
    return render_template("index.html", status=get_system_status())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
