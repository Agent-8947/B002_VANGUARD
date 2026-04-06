#!/usr/bin/env python3
"""NEXUS Module: web_crawler  Basic Web Crawler (Extracts Title & Links)."""
import urllib.request, re, json
from urllib.parse import urljoin

def run(url: str) -> dict:
    if not url: return {"error": "empty target"}
    if not url.startswith("http"): url = "https://" + url.split("@")[-1]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nexus-crawler/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            html = r.read().decode("utf-8", errors="ignore")
            title = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
            links = re.findall(r'href="(http[s]?://.*?)"', html) + re.findall(r"href='(http[s]?://.*?)'", html)
            return {"url": url, "title": title.group(1) if title else "No title",
                    "links_found": len(links), "unique_links": list(set(links))[:20]}
    except Exception as e:
        return {"error": str(e), "url": url}

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "example.com"), indent=2))
