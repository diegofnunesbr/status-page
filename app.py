from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import datetime
import os

def cmd(c):
    return subprocess.check_output(c, shell=True, text=True).strip()

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        hostname = cmd("cat /host/etc/hostname")
        os_name = cmd("cat /host/etc/issue.net").strip()

        ip = cmd("ip -4 route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if ($i==\"src\") print $(i+1)}'")

        uptime_sec = int(float(cmd("awk '{print $1}' /host/proc/uptime")))
        h = uptime_sec // 3600
        m = (uptime_sec % 3600) // 60
        uptime = f"{h}h {m}min" if h > 0 else f"{m}min"

        cpu_pct = cmd("awk '/cpu / {u=($2+$4); t=($2+$4+$5)} END {printf \"%.0f\", u*100/t}' /host/proc/stat")
        cpu_count = cmd("grep -c '^processor' /host/proc/cpuinfo")

        mem_total = int(cmd("awk '/MemTotal/ {print $2}' /host/proc/meminfo"))
        mem_avail = int(cmd("awk '/MemAvailable/ {print $2}' /host/proc/meminfo"))
        mem_used = mem_total - mem_avail
        mem_pct = mem_used * 100 / mem_total

        mem_used_gb = mem_used / 1024 / 1024
        mem_total_gb = mem_total / 1024 / 1024

        if os.path.exists("/host/mnt/c"):
            disk_line = cmd("df -kP /host/mnt/c | tail -1")
        else:
            disk_line = cmd("df -kP /host | tail -1")

        parts = disk_line.split()
        disk_total_kb = int(parts[1])
        disk_used_kb = int(parts[2])
        disk_pct = disk_used_kb * 100 / disk_total_kb

        disk_total_gb = disk_total_kb / 1024 / 1024
        disk_used_gb = disk_used_kb / 1024 / 1024

        if disk_total_gb >= 1024:
            disk_total = f"{disk_total_gb/1024:.1f} TB"
            disk_used = f"{disk_used_gb/1024:.1f} TB"
        else:
            disk_total = f"{disk_total_gb:.1f} GB"
            disk_used = f"{disk_used_gb:.1f} GB"

        now = datetime.datetime.now().strftime("%a %b %d %H:%M:%S %Y")

        html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>Status</title>
<style>
body {{
  font-family: monospace;
  margin: 8px;
}}
pre {{
  margin: 0;
}}
</style>
</head>
<body>
<pre>
Hostname : {hostname}
SO       : {os_name}
IP       : {ip}
Uptime   : {uptime}
CPU      : {cpu_pct}% ({cpu_count} vCPU)
Memória  : {mem_used_gb:.1f} GB / {mem_total_gb:.1f} GB ({mem_pct:.0f}%)
Disco    : {disk_used} / {disk_total} ({disk_pct:.0f}%)

Atualizado em: {now}
</pre>
</body>
</html>
"""

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

HTTPServer(("0.0.0.0", 80), Handler).serve_forever()