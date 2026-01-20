import os
import time
import socket
import logging
from pathlib import Path
from datetime import datetime, timedelta

import psutil
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)

app.secret_key = os.environ.get("STATUS_SECRET", "default_secret")
app.permanent_session_lifetime = timedelta(minutes=30)

logging.getLogger("werkzeug").disabled = True
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
)

STATUS_USER = os.environ.get("STATUS_USER", "admin")
STATUS_PASS = os.environ.get("STATUS_PASS", "admin")


def is_wsl():
    try:
        return "microsoft" in Path("/proc/sys/kernel/osrelease").read_text().lower()
    except Exception:
        return False


def get_os_info():
    try:
        data = Path("/etc/os-release").read_text()
        for line in data.splitlines():
            if line.startswith("PRETTY_NAME="):
                return line.split("=", 1)[1].replace('"', "")
    except Exception:
        pass
    return "Unknown"


def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "N/A"


def get_disk_usage():
    if not is_wsl():
        d = psutil.disk_usage("/")
        return (
            round(d.used / (1024 ** 3), 1),
            round(d.total / (1024 ** 3), 1),
            round(d.percent, 1),
        )

    total_used = 0
    total_size = 0

    try:
        for p in Path("/mnt").iterdir():
            if p.is_dir() and len(p.name) == 1:
                d = psutil.disk_usage(str(p))
                total_used += d.used
                total_size += d.total
    except Exception:
        pass

    if total_size == 0:
        return 0, 0, 0

    used_gb = round(total_used / (1024 ** 3), 1)
    total_gb = round(total_size / (1024 ** 3), 1)
    percent = round((total_used / total_size) * 100, 1)

    return used_gb, total_gb, percent


def get_system_status():
    uptime_seconds = int(time.time() - psutil.boot_time())

    mem = psutil.virtual_memory()
    disk_used, disk_total, disk_percent = get_disk_usage()

    return {
        "hostname": socket.gethostname(),
        "os_info": get_os_info(),
        "ip_address": get_ip_address(),
        "uptime": str(timedelta(seconds=uptime_seconds)),
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "memory_used": round(mem.used / (1024 ** 3), 1),
        "memory_total": round(mem.total / (1024 ** 3), 1),
        "memory_percent": round(mem.percent, 1),
        "disk_used": disk_used,
        "disk_total": disk_total,
        "disk_percent": disk_percent,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }


@app.before_request
def session_timeout():
    if "logged_in" in session:
        last_activity = session.get("last_activity")
        if last_activity and datetime.now() - last_activity > timedelta(minutes=30):
            session.clear()
            logging.info("LOGOUT timeout ip=%s", request.remote_addr)
            return redirect(url_for("login"))
        session["last_activity"] = datetime.now()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username")
        password = request.form.get("password")

        if user == STATUS_USER and password == STATUS_PASS:
            session["logged_in"] = True
            session["last_activity"] = datetime.now()
            logging.info("LOGIN OK user=%s ip=%s", user, request.remote_addr)
            return redirect(url_for("index"))

        logging.info("LOGIN FAIL user=%s ip=%s", user, request.remote_addr)
        return render_template("login.html", error=True)

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    logging.info("LOGOUT ip=%s", request.remote_addr)
    return redirect(url_for("login"))


@app.route("/")
def index():
    if not session.get("logged_in"):
        return redirect(url_for("login"))

    return render_template("index.html", status=get_system_status())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
