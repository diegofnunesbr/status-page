from flask import Flask, render_template
import psutil
import socket
from datetime import datetime
from pathlib import Path
import subprocess

app = Flask(__name__)

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

        "disk_used": round(disk.used / (1024 ** 3), 1),
        "disk_total": round(disk.total / (1024 ** 3), 1),
        "disk_percent": disk.percent,

        "updated_at": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
    }

@app.route("/")
def index():
    return render_template("index.html", status=get_system_status())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
