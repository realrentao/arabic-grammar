#!/usr/bin/env python3
import urllib.request, json, os, base64

TOKEN = os.environ.get("GITHUB_TOKEN", "")
with open('test-audio.html', encoding='utf-8') as f:
    content = f.read()

data = {
    "message": "Add audio test page",
    "content": base64.b64encode(content.encode()).decode('ascii')
}

req = urllib.request.Request(
    "https://api.github.com/repos/realrentao/arabic-grammar/contents/test-audio.html",
    data=json.dumps(data).encode(), method="PUT")
req.add_header("Authorization", f"token {TOKEN}")
req.add_header("Content-Type", "application/json")

try:
    resp = urllib.request.urlopen(req)
    d = json.loads(resp.read())
    print(f"OK: {d['commit']['sha'][:12]}")
    print(f"https://realrentao.github.io/arabic-grammar/test-audio.html")
except Exception as e:
    print(f"FAIL: {e}")
