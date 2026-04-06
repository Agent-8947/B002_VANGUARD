#!/usr/bin/env python3
"""NEXUS Module: network_recon  Subdomain discovery via crt.sh CT logs."""

import json, urllib.request, urllib.parse
from datetime import datetime, timezone

def run(domain: str, limit: int = 200) -> dict:
    if not domain: return {"error": "empty target"}
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0].split("@")[-1]
    url = f"https://crt.sh/?q=%25.{urllib.parse.quote(domain)}&output=json"
    req = urllib.request.Request(url, headers={"User-Agent": "nexus-recon/1.0", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            entries = json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e), "domain": domain, "subdomains": []}
    seen, results, now = set(), [], datetime.now(timezone.utc)
    for e in entries:
        exp = e.get("not_after", "")
        if exp:
            try:
                dt = datetime.strptime(exp[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
                if dt <= now:
                    continue
            except ValueError:
                pass
        for name in e.get("name_value", "").splitlines():
            name = name.strip().lower()
            if name and name not in seen:
                seen.add(name)
                results.append({"subdomain": name, "issuer": e.get("issuer_name", ""), "not_after": exp})
    results.sort(key=lambda x: (x["subdomain"].startswith("*"), x["subdomain"]))
    return {"domain": domain, "count": min(len(results), limit), "subdomains": results[:limit]}

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "example.com"), indent=2))
