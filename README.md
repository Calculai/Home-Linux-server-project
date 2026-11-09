# Home Linux Server

A Raspberry Pi home server for experimenting with self-hosted services and remote access. The server uses the `calculai.dev` domain and Cloudflare Tunnels.

## Overview

SSH access is routed through Cloudflare and protected by an email-verification policy. A local SSH alias provides convenient access from my laptop via powershell:

ssh alias

The server also runs a custom status page, publicly available at [status.calculai.dev](https://status.calculai.dev).

## Hardware and software

- **Hardware:** Raspberry Pi 4 Model B Rev 1.5, 8 GB RAM
- **Operating system:** Debian GNU/Linux 13 (trixie)
- **Architecture:** 64-bit ARM (`aarch64`), 4 CPU cores
- **Python:** 3.13.5
- **Root filesystem:** 58 GB total 
- **Domain:** `calculai.dev`
- **Remote access:** Cloudflare Tunnel

## Services

| Service | Purpose | Access |
|---|---|---|
| Cloudflare Tunnel | Provides remote SSH access | `ssh.calculai.dev`, private |
| PiStatus | Custom server status page | [status.calculai.dev](https://status.calculai.dev), public |

## Repository layout

```text
.
└── pistatus/
    ├── server.py
    └── pistatus.service
```

## Requirements

- Raspberry Pi running Debian GNU/Linux 13 (trixie) on 64-bit ARM
- A domain managed through Cloudflare
- Cloudflare Tunnel configured for remote SSH access
- Python 3 (the status page uses only the Python standard library)

## Setup

PiStatus runs as a systemd service. The repository includes the status-page application and a systemd unit file.

## Configuration

Cloudflare Tunnel and an email-verification policy provide remote SSH access.

## Maintenance

- **Check PiStatus:** `sudo systemctl status pistatus`
- **View PiStatus logs:** `sudo journalctl -u pistatus`
- **Restart PiStatus:** `sudo systemctl restart pistatus`

PiStatus is enabled to start automatically and was running when last checked.


