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


def get_disk_path():
    if is_wsl() and Path("/mnt/c").exists():
        return "/mnt/c"
    return "/"


def get_ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "N/A"


def get_system_status():
    hostname = socket.gethostname()
    os_info = Path("/etc/os-release").read_text().split("PRETTY_NAME=")[1].split("\n")[0].replace('"', "")
    uptime_seconds = int(time.time() - psutil.boot_time())
    uptime = str(timedelta(seconds=uptime_seconds))

    cpu_percent = psutil.cpu_percent(interval=0.5)

    mem = psutil.virtual_memory()
    memory_used = round(mem.used / (1024 ** 3), 1)
    memory_total = round(mem.total / (1024 ** 3), 1)
    memory_percent = round(mem.percent, 1)

    disk = psutil.disk_usage(get_disk_path())
    disk_used = round(disk.used / (1024 ** 3), 1)
    disk_total = round(disk.total / (1024 ** 3), 1)
    disk_percent = round(disk.percent, 1)

    return {
        "hostname": hostname,
        "os_info": os_info,
        "ip_address": get_ip_address(),
        "uptime": uptime,
        "cpu_percent": cpu_percent,
        "memory_used": memory_used,
        "memory_total": memory_total,
        "memory_percent": memory_percent,
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

    status = get_system_status()
    return render_template("index.html", status=status)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
