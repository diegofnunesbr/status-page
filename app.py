from flask import Flask, render_template
import psutil
import platform
import socket
from datetime import datetime

app = Flask(__name__)

def get_system_status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return {
        "hostname": socket.gethostname(),
        "os_info": platform.platform(),
        "ip_address": socket.gethostbyname(socket.gethostname()),
        "uptime": str(
            datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        ).split(".")[0],

        "cpu_percent": psutil.cpu_percent(interval=1),

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
