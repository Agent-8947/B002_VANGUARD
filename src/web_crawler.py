#!/usr/bin/env python3
"""NEXUS Module: web_crawler  Reliable Web Crawler (html.parser)."""
import urllib.request, json
from html.parser import HTMLParser
from urllib.parse import urljoin

class NexusParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.title = ""
        self.links = []
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag == "title": self._in_title = True
        if tag == "a":
            for attr, val in attrs:
                if attr == "href" and val:
                    # Resolve relative links automatically
                    abs_link = urljoin(self.base_url, val)
                    if abs_link.startswith("http"):
                        self.links.append(abs_link)

    def handle_endtag(self, tag):
        if tag == "title": self._in_title = False

    def handle_data(self, data):
        if self._in_title: self.title += data.strip()

def run(url: str) -> dict:
    if not url: return {"error": "empty target"}
    if not url.startswith("http"): url = "https://" + url.split("@")[-1]
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "nexus-VANGUARD-crawler/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            charset = r.info().get_content_charset() or "utf-8"
            html_content = r.read().decode(charset, errors="ignore")
            
            parser = NexusParser(url)
            parser.feed(html_content)
            
            return {
                "url": url, 
                "title": parser.title or "No title",
                "links_found": len(parser.links), 
                "unique_links": list(dict.fromkeys(parser.links))[:20]
            }
    except Exception as e:
        return {"error": str(e), "url": url}

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "example.com"), indent=2))
