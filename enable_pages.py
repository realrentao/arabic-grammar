#!/usr/bin/env python3
import urllib.request, json, os
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def api(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Content-Type", "application/json")
    if data: req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  {e.code}: {e.read().decode()[:200]}")
        return None

# First ensure there's an index.html at root - it exists
# Enable Pages
pages = api("POST", "https://api.github.com/repos/realrentao/arabic-grammar/pages", {
    "source": {"branch": "main", "path": "/"}
})
if pages:
    url = pages.get("html_url", "")
    print(f"Pages enabled: {url}")
    print(f"Also at: https://realrentao.github.io/arabic-grammar")
else:
    print("Pages API failed - may need manual setup")
    print("Go to: https://github.com/realrentao/arabic-grammar/settings/pages")
    print("Set: Source → main branch, / (root)")
