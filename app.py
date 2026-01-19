from flask import Flask, render_template, request, redirect, session, url_for
import psutil
import socket
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import os
import logging

logging.getLogger("werkzeug").setLevel(logging.ERROR)

app = Flask(__name__)

app.secret_key = os.environ.get("STATUS_SECRET", "status-page-secret")
app.permanent_session_lifetime = timedelta(minutes=30)

STATUS_USER = os.environ.get("STATUS_USER", "admin")
STATUS_PASS = os.environ.get("STATUS_PASS", "admin")

def log_event(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def get_os():
    try:
        for line in Path("/host/etc/os-release").read_text().splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].strip('"')
    except Exception:
        pass
    return "Unknown"

def get_ip():
    try:
        output = subprocess.check_output(
            ["ip", "route", "get", "1.1.1.1"],
            stderr=subprocess.DEVNULL,
            text=True
        )
        return output.split("src")[1].split()[0]
    except Exception:
        return "N/A"

def gb(value):
    return round(value / (1024 ** 3), 1)

def get_system_status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())

    return {
        "hostname": socket.gethostname(),
        "os_info": get_os(),
        "ip_address": get_ip(),
        "uptime": str(uptime).split(".")[0],

        "cpu_percent": psutil.cpu_percent(),

        "memory_used": gb(memory.used),
        "memory_total": gb(memory.total),
        "memory_percent": memory.percent,

        "disk_used": gb(disk.used),
        "disk_total": gb(disk.total),
        "disk_percent": disk.percent,

        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        pwd = request.form.get("password")
        ip = request.remote_addr

        if user == STATUS_USER and pwd == STATUS_PASS:
            session.permanent = True
            session["auth"] = True
            log_event(f"LOGIN OK user={user} ip={ip}")
            return redirect(url_for("index"))

        log_event(f"LOGIN FAIL user={user} ip={ip}")
        return render_template("login.html", error=True)

    return render_template("login.html")

@app.route("/logout")
def logout():
    ip = request.remote_addr
    log_event(f"LOGOUT ip={ip}")
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
def index():
    if not session.get("auth"):
        return redirect(url_for("login"))

    return render_template("index.html", status=get_system_status())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
