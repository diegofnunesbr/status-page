from flask import Flask, render_template, redirect, request, session
import psutil, socket, subprocess, os, logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

app = Flask(__name__)
app.secret_key = os.getenv("STATUS_SECRET", "change-me")

SESSION_TIMEOUT = timedelta(minutes=30)
STATUS_USER = os.getenv("STATUS_USER")
STATUS_PASS = os.getenv("STATUS_PASS")

log = logging.getLogger("status-page")
log.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(message)s"))
log.addHandler(handler)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

now = lambda: datetime.now(timezone.utc)
gb = lambda b: round(b / (1024 ** 3), 1)

def format_disk(b):
    g = b / (1024 ** 3)
    return f"{g / 1024:.1f} TB" if g >= 1024 else f"{g:.1f} GB"

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

def client_ip():
    return (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP")
        or request.remote_addr
    )

def logged_in():
    last = session.get("last_activity")
    if not last or now() - datetime.fromisoformat(last) > SESSION_TIMEOUT:
        session.clear()
        return False
    session["last_activity"] = now().isoformat()
    return True

def get_disks():
    disks = []
    mnt = Path("/host/mnt")

    if (mnt / "c").exists():
        for p in sorted(mnt.iterdir()):
            if p.is_dir() and len(p.name) == 1 and p.name.isalpha():
                try:
                    d = psutil.disk_usage(str(p))
                    disks.append({
                        "label": f"Disco ({p.name.upper()}:)",
                        "used": format_disk(d.used),
                        "total": format_disk(d.total),
                        "percent": d.percent
                    })
                except Exception:
                    pass
    else:
        try:
            d = psutil.disk_usage("/host")
            disks.append({
                "label": "Disco",
                "used": format_disk(d.used),
                "total": format_disk(d.total),
                "percent": d.percent
            })
        except Exception:
            pass

    return disks

def status():
    mem = psutil.virtual_memory()
    return {
        "hostname": socket.gethostname(),
        "os_info": get_os(),
        "ip_address": get_ip(),
        "uptime": str(datetime.now() - datetime.fromtimestamp(psutil.boot_time())).split(".")[0],
        "cpu_percent": psutil.cpu_percent(),
        "memory_used": gb(mem.used),
        "memory_total": gb(mem.total),
        "memory_percent": mem.percent,
        "disks": get_disks(),
        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

@app.route("/login", methods=["GET", "POST"])
def login():
    error = False
    if request.method == "POST":
        if request.form.get("username") == STATUS_USER and request.form.get("password") == STATUS_PASS:
            session.update(logged_in=True, last_activity=now().isoformat())
            log.info(f"LOGIN OK user={STATUS_USER} ip={client_ip()}")
            return redirect("/")
        error = True
        log.info(f"LOGIN FAIL user={request.form.get('username')} ip={client_ip()}")
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    log.info(f"LOGOUT ip={client_ip()}")
    session.clear()
    return redirect("/login")

@app.route("/")
def index():
    return render_template("index.html", status=status()) if logged_in() else redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
