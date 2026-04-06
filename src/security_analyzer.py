#!/usr/bin/env python3
"""
NEXUS Module: security_analyzer
Passive OSINT analyzer  IP resolution, HTTPS check, HTTP security headers audit.
stdlib only. Outputs structured JSON.
"""
import json, socket, ssl, urllib.request
from datetime import datetime, timezone

def _resolve_ip(host: str) -> list:
    try: return list(dict.fromkeys(i[4][0] for i in socket.getaddrinfo(host, None, socket.AF_INET)))
    except: return []

def _https_reachable(host: str, timeout: float = 5.0) -> bool:
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, 443), timeout=timeout) as s:
            with ctx.wrap_socket(s, server_hostname=host): return True
    except: return False

def _http_headers(host: str, timeout: float = 8.0) -> dict:
    try:
        req = urllib.request.Request(f"https://{host}", headers={"User-Agent": "nexus-SECURITY_ANALYZER/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r: return dict(r.headers)
    except: return {}

SECURITY_HEADERS = {
    "Strict-Transport-Security": "HSTS",
    "Content-Security-Policy": "CSP",
    "X-Frame-Options": "Clickjacking-Protection",
    "X-Content-Type-Options": "MIME-Sniffing-Protection",
    "Referrer-Policy": "Referrer-Policy",
    "Permissions-Policy": "Feature-Policy",
}

def run(target: str) -> dict:
    if not target: return {"error": "empty target"}
    target = target.replace("https://", "").replace("http://", "").split("/")[0].split("@")[-1]
    headers = {k.lower(): v for k, v in _http_headers(target).items()}
    if not headers: return {"error": "Network unreachable or host offline", "target": target}
    sec = {label: (header.lower() in headers) for header, label in SECURITY_HEADERS.items()}
    return {
        "target": target, "module": "security_analyzer",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ip_addresses": _resolve_ip(target),
        "https_reachable": _https_reachable(target),
        "security_headers": sec,
        "security_score": f"{sum(sec.values())}/{len(sec)}",
        "http_server": headers.get("Server", "unknown"),
        "powered_by": headers.get("X-Powered-By", "not disclosed"),
    }

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "example.com"), indent=2))
