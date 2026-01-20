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

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(message)s"
)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
log = logging.getLogger("status-page")

def format_gb(v):
    return round(v / (1024 ** 3), 1)

def format_disk(v):
    gb = v / (1024 ** 3)
    return f"{gb / 1024:.1f} TB" if gb >= 1024 else f"{gb:.1f} GB"

def get_disk():
    return psutil.disk_usage("/host/mnt/c") if Path("/host/mnt/c").exists() else psutil.disk_usage("/host")

def get_os():
    try:
        return next(
            l.split("=", 1)[1].strip('"')
            for l in Path("/host/etc/os-release").read_text().splitlines()
            if l.startswith("PRETTY_NAME=")
        )
    except Exception:
        return "Unknown"

def get_ip():
    try:
        out = subprocess.check_output(
            ["ip", "route", "get", "1.1.1.1"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return out.split("src")[1].split()[0]
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
    mem = psutil.virtual_memory()
    disk = get_disk()

    return {
        "hostname": socket.gethostname(),
        "os_info": get_os(),
        "ip_address": get_ip(),
        "uptime": str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())).split(".")[0],
        "cpu_percent": psutil.cpu_percent(),
        "memory_used": format_gb(mem.used),
        "memory_total": format_gb(mem.total),
        "memory_percent": mem.percent,
        "disk_used": format_disk(disk.used),
        "disk_total": format_disk(disk.total),
        "disk_percent": disk.percent,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

@app.route("/login", methods=["GET", "POST"])
def login():
    error = False
    if request.method == "POST":
        if request.form.get("username") == STATUS_USER and request.form.get("password") == STATUS_PASS:
            session["logged_in"] = True
            session["last_activity"] = datetime.utcnow().isoformat()
            log.info(f"LOGIN OK user={STATUS_USER} ip={request.remote_addr}")
            return redirect("/")
        error = True
        log.info(f"LOGIN FAIL user={request.form.get('username')} ip={request.remote_addr}")
    return render_template("login.html", error=error)

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
