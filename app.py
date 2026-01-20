from flask import Flask, render_template, redirect, request, session
import psutil, socket, subprocess, os, logging
from datetime import datetime, timedelta
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.getenv("STATUS_SECRET", "change-me")

STATUS_USER = os.getenv("STATUS_USER")
STATUS_PASS = os.getenv("STATUS_PASS")
SESSION_TIMEOUT = timedelta(minutes=30)

log = logging.getLogger("status-page")
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(handler)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

def format_disk(b):
    g = b / (1024 ** 3)
    return f"{g / 1024:.1f} TB" if g >= 1024 else f"{g:.1f} GB"

def get_disk():
    return psutil.disk_usage("/host/mnt/c") if Path("/host/mnt/c").exists() else psutil.disk_usage("/host")

def get_os():
    try:
        for l in Path("/host/etc/os-release").read_text().splitlines():
            if l.startswith("PRETTY_NAME="):
                return l.split("=", 1)[1].strip('"')
    except Exception:
        pass
    return "Unknown"

def get_ip():
    try:
        out = subprocess.check_output(["ip", "route", "get", "1.1.1.1"], text=True)
        return out.split("src")[1].split()[0]
    except Exception:
        return "N/A"

def is_logged_in():
    last = session.get("last_activity")
    if not last or datetime.utcnow() - datetime.fromisoformat(last) > SESSION_TIMEOUT:
        session.clear()
        return False
    session["last_activity"] = datetime.utcnow().isoformat()
    return True

def get_system_status():
    m = psutil.virtual_memory()
    d = get_disk()
    return {
        "hostname": socket.gethostname(),
        "os_info": get_os(),
        "ip_address": get_ip(),
        "uptime": str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())).split(".")[0],
        "cpu_percent": psutil.cpu_percent(),
        "memory_used": round(m.used / (1024 ** 3), 1),
        "memory_total": round(m.total / (1024 ** 3), 1),
        "memory_percent": m.percent,
        "disk_used": format_disk(d.used),
        "disk_total": format_disk(d.total),
        "disk_percent": d.percent,
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == STATUS_USER and request.form.get("password") == STATUS_PASS:
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
    return redirect("/login") if not is_logged_in() else render_template("index.html", status=get_system_status())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
