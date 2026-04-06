#!/usr/bin/env python3
"""NEXUS Module: endpoint_monitor  HTTP endpoint monitor with concurrent probing."""
import urllib.request, urllib.error, json, time
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

def _probe(url: str, timeout: float = 10.0) -> dict:
    start = time.perf_counter()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nexus-monitor/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            ms = round((time.perf_counter() - start) * 1000, 1)
            return {"url": url, "status": r.status, "ok": True, "latency_ms": ms,
                    "checked_at": datetime.now(timezone.utc).isoformat()}
    except urllib.error.HTTPError as e:
        ms = round((time.perf_counter() - start) * 1000, 1)
        return {"url": url, "status": e.code, "ok": e.code < 400, "latency_ms": ms, "error": str(e)}
    except Exception as e:
        return {"url": url, "status": None, "ok": False, "latency_ms": None, "error": str(e)}

def run(targets) -> dict:
    if not targets: return {"error": "empty target"}
    if isinstance(targets, str): targets = [targets]
    targets = [t if t.startswith("http") else "https://" + t.split("@")[-1] for t in targets]
    results = []
    with ThreadPoolExecutor(max_workers=min(len(targets), 20)) as ex:
        for f in as_completed({ex.submit(_probe, u): u for u in targets}):
            results.append(f.result())
    up = sum(1 for r in results if r["ok"])
    return {"total": len(results), "up": up, "down": len(results) - up, "results": results}

if __name__ == "__main__":
    import sys
    targets = sys.argv[1:] if len(sys.argv) > 1 else ["https://example.com"]
    print(json.dumps(run(targets), indent=2))
