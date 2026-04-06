#!/usr/bin/env python3
"""NEXUS Module: breach_intel  Breach detection via HIBP k-anonymity API."""
import hashlib, urllib.request, urllib.parse, os, json

def check_password(password: str) -> dict:
    sha1 = hashlib.sha1(password.encode()).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    req = urllib.request.Request(f"https://api.pwnedpasswords.com/range/{prefix}",
                                  headers={"User-Agent": "nexus-breach/1.0", "Add-Padding": "true"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            for line in r.read().decode().splitlines():
                h, count = line.split(":")
                if h == suffix:
                    return {"pwned": True, "count": int(count)}
        return {"pwned": False, "count": 0}
    except Exception as e:
        return {"error": str(e)}

def check_email(email: str) -> dict:
    key = os.environ.get("HIBP_API_KEY", "")
    if not key:
        return {"error": "Set HIBP_API_KEY env var (free at haveibeenpwned.com/API/Key)", "email": email}
    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}"
    req = urllib.request.Request(url, headers={"hibp-api-key": key, "User-Agent": "nexus-breach/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            breaches = json.loads(r.read())
        return {"email": email, "pwned": True, "count": len(breaches), "breaches": [b["Name"] for b in breaches]}
    except urllib.error.HTTPError as e:
        return {"email": email, "pwned": False, "count": 0} if e.code == 404 else {"error": str(e)}

def run(target: str) -> dict:
    if not target: return {"error": "empty target"}
    return check_email(target) if "@" in target else check_password(target)

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "password123"), indent=2))
