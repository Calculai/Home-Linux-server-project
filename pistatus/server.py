#!/usr/bin/env python3
"""Minimal public status page for a Raspberry Pi. Standard library only."""
import json
import os
import random
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOST = os.environ.get("PISTATUS_HOST", "127.0.0.1")
PORT = int(os.environ.get("PISTATUS_PORT", "8080"))
MOCK = os.environ.get("PISTATUS_MOCK") == "1"


def read(path):
    with open(path) as f:
        return f.read()


def real_stats():
    temp = int(read("/sys/class/thermal/thermal_zone0/temp")) / 1000 

    # read memory information from /proc/meminfo
    mem = {
        line.split(":")[0]: int(line.split()[1]) 
        for line in read("/proc/meminfo").splitlines()
    }

    # read disk usage information for the root filesystem
    st = os.statvfs("/")

    return {
        "temp_c": round(temp, 1),
        "load_1m": float(read("/proc/loadavg").split()[0]),
        "cpus": os.cpu_count(),
        "mem_pct": round((mem["MemTotal"] - mem["MemAvailable"]) / mem["MemTotal"] * 100, 1),
        "disk_pct": round((1 - st.f_bavail / st.f_blocks) * 100, 1),
        "uptime_s": int(float(read("/proc/uptime").split()[0])),
    }


def mock_stats():
    return {
        "temp_c": round(random.uniform(45, 65), 1),
        "load_1m": round(random.uniform(0.0, 1.5), 2),
        "cpus": 4,
        "mem_pct": round(random.uniform(20, 40), 1),
        "disk_pct": 13.0,
        "uptime_s": random.randint(3600, 900000),
    }


def stats():
    return mock_stats() if MOCK else real_stats()


PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pi status</title>
<style>
body{font-family:system-ui,sans-serif;background:#0f1115;color:#e6e6e6;max-width:480px;margin:40px auto;padding:0 16px}
h1{font-size:1.2rem;color:#9aa4b2}
.card{background:#1a1d24;border-radius:10px;padding:14px 18px;margin:10px 0;display:flex;justify-content:space-between}
.v{font-weight:600}
small{color:#6b7380}
</style>
</head>
<body>
<h1>&#9679; Pi status</h1>
<div class="card"><span>CPU temp</span><span class="v" id="temp">-</span></div>
<div class="card"><span>CPU load (1m)</span><span class="v" id="load">-</span></div>
<div class="card"><span>Memory used</span><span class="v" id="mem">-</span></div>
<div class="card"><span>Disk used</span><span class="v" id="disk">-</span></div>
<div class="card"><span>Uptime</span><span class="v" id="up">-</span></div>
<small id="upd"></small>
<script>
async function tick(){
  try{
    const d = await (await fetch('/api')).json();
    temp.textContent = d.temp_c + ' \u00b0C';
    load.textContent = d.load_1m + ' (' + d.cpus + ' cores)';
    mem.textContent = d.mem_pct + '%';
    disk.textContent = d.disk_pct + '%';
    const s = d.uptime_s;
    up.textContent = Math.floor(s/86400) + 'd ' + Math.floor(s%86400/3600) + 'h ' + Math.floor(s%3600/60) + 'm';
    upd.textContent = 'Updated ' + new Date().toLocaleTimeString();
  }catch(e){
    upd.textContent = 'Offline?';
  }
}
tick();
setInterval(tick, 5000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self): # handle GET requests
        if self.path == "/api": 
            body, ctype = json.dumps(stats()).encode(), "application/json" 
        elif self.path == "/":
            body, ctype = PAGE.encode(), "text/html; charset=utf-8" 
        else:
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype) 
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args): # override to suppress unnecessary logging
        pass 


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()