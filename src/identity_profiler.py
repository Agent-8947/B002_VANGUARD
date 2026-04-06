#!/usr/bin/env python3
"""NEXUS Module: identity_profiler  Username presence across 15 platforms."""
import urllib.request, json
from concurrent.futures import ThreadPoolExecutor, as_completed

PLATFORMS = {
    "GitHub": "https://github.com/{}","Twitter": "https://twitter.com/{}",
    "Instagram": "https://www.instagram.com/{}","Reddit": "https://www.reddit.com/user/{}",
    "TikTok": "https://www.tiktok.com/@{}","YouTube": "https://www.youtube.com/@{}",
    "Telegram": "https://t.me/{}","Twitch": "https://www.twitch.tv/{}",
    "Dev.to": "https://dev.to/{}","Medium": "https://medium.com/@{}",
    "Pinterest": "https://www.pinterest.com/{}","LinkedIn": "https://www.linkedin.com/in/{}",
    "HackerNews": "https://news.ycombinator.com/user?id={}",
    "ProductHunt": "https://www.producthunt.com/@{}","Mastodon": "https://mastodon.social/@{}",
}

# Advanced matching rules for specific platforms to avoid false 200 OK
PLATFORM_RULES = {
    "LinkedIn": "linkedin.com/authwall",
    "Instagram": "instagram.com/accounts/login",
    "TikTok": "tiktok.com/@", # Should contain the @username if found
    "Twitter": "twitter.com/search",
}

def _check(platform, url_tpl, username, timeout=5.0):
    url = url_tpl.format(username)
    try:
        req = urllib.request.Request(url, method="GET", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            res_url = r.geturl().lower()
            status = r.status
            
            # 1. Check generic "Not Found" patterns in URL
            if any(p in res_url for p in ["/login", "/notfound", "/404", "error"]):
                found = False
            # 2. Platform-specific AuthWall/Redirect checks
            elif platform in PLATFORM_RULES and PLATFORM_RULES[platform] in res_url:
                # If LinkedIn is redirecting to an authwall, the user presence is inconclusive (usually False)
                found = False if platform == "LinkedIn" else True
            else:
                found = status < 400
    except urllib.error.HTTPError as e:
        found = e.code < 400 and e.code != 404
    except:
        found = False
    return {"platform": platform, "url": url, "found": found}

def run(username: str) -> dict:
    if not username: return {"error": "empty target"}
    username = username.replace("https://", "").replace("http://", "").strip("/").split("/")[-1]
    if "@" in username: username = username.split("@")[0]
    if "." in username: username = username.split(".")[0]
    username = username.strip().replace(" ", "").lower()
    if not username: return {"error": "empty target after cleanup"}
    results = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for f in as_completed({ex.submit(_check, p, u, username): p for p, u in PLATFORMS.items()}):
            results.append(f.result())
    found = [r for r in results if r["found"]]
    results.sort(key=lambda x: (not x["found"], x["platform"]))
    return {"username": username, "checked": len(results), "found_count": len(found), "results": results}

if __name__ == "__main__":
    import sys
    print(json.dumps(run(sys.argv[1] if len(sys.argv) > 1 else "johndoe"), indent=2))
