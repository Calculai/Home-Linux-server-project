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

    # Read memory information from /proc/meminfo.
    mem = {
        line.split(":")[0]: int(line.split()[1])
        for line in read("/proc/meminfo").splitlines()
    }

    # Read disk usage information for the root filesystem.
    st = os.statvfs("/")

    return {
        "temp_c": round(temp, 1),
        "load_1m": float(read("/proc/loadavg").split()[0]),
        "cpus": os.cpu_count(),
        "mem_pct": round(
            (mem["MemTotal"] - mem["MemAvailable"]) / mem["MemTotal"] * 100, 1
        ),
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
    # The widget treats anything other than the exact status "ok" as offline.
    return {
        "status": "ok",
        **(mock_stats() if MOCK else real_stats()),
    }


PAGE = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pi status</title>
<style>
:root{color-scheme:dark}
*{box-sizing:border-box}
body{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;background:#0b0b0b;color:#e6e6e6;max-width:480px;margin:32px auto;padding:0 16px}
h1{font-size:1rem;letter-spacing:.08em;color:#bdbdbd}
.card{background:#151515;border:1px solid #303030;padding:12px 14px;margin:8px 0;display:flex;justify-content:space-between;gap:16px}
.v{font-weight:700}
small{color:#777}
#state{color:#ff3030}
</style>
</head>
<body>
<h1>CALCULAI.DEV / SYSTEM STATUS</h1>
<div class="card"><span>STATUS</span><span class="v" id="state">CHECKING</span></div>
<div class="card"><span>CPU temp</span><span class="v" id="temp">-</span></div>
<div class="card"><span>CPU load (1m)</span><span class="v" id="load">-</span></div>
<div class="card"><span>Memory used</span><span class="v" id="mem">-</span></div>
<div class="card"><span>Disk used</span><span class="v" id="disk">-</span></div>
<div class="card"><span>Uptime</span><span class="v" id="up">-</span></div>
<small id="upd">Last check: -</small>
<script>
const el = id => document.getElementById(id);
async function tick(){
  const checkedAt = new Date().toLocaleTimeString();
  try{
    const response = await fetch('/api', {cache:'no-store'});
    if (!response.ok) throw new Error('HTTP ' + response.status);
    const text = await response.text();
    if (!text.trim()) throw new Error('Empty response');
    const d = JSON.parse(text);
    if (d.status !== 'ok') throw new Error('Unhealthy status');

    el('state').textContent = '● ONLINE';
    el('state').style.color = '#ff3030';
    el('temp').textContent = d.temp_c + ' °C';
    el('load').textContent = d.load_1m + ' / ' + d.cpus + ' cores';
    el('mem').textContent = d.mem_pct + '%';
    el('disk').textContent = d.disk_pct + '%';
    const s = d.uptime_s;
    el('up').textContent = Math.floor(s/86400) + 'd ' + Math.floor(s%86400/3600) + 'h ' + Math.floor(s%3600/60) + 'm';
  }catch(e){
    el('state').textContent = '● OFFLINE';
    el('state').style.color = '#888';
    el('temp').textContent = '-';
    el('load').textContent = '-';
    el('mem').textContent = '-';
    el('disk').textContent = '-';
    el('up').textContent = '-';
  }
  el('upd').textContent = 'Last check: ' + checkedAt;
}
tick();
setInterval(tick, 5000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api":
            try:
                body = json.dumps(stats()).encode()
            except Exception:
                # Avoid returning a healthy-looking payload if collecting stats fails.
                body = json.dumps({"status": "error"}).encode()
            ctype = "application/json; charset=utf-8"
        elif self.path == "/":
            body = PAGE.encode()
            ctype = "text/html; charset=utf-8"
        else:
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
