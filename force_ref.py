#!/usr/bin/env python3
import urllib.request, json, os
TOKEN = os.environ.get("GITHUB_TOKEN", "")
data = json.dumps({"sha": "02f7e0ffd477843897ad3514a11a45f1a7439753", "force": True}).encode()
req = urllib.request.Request("https://api.github.com/repos/realrentao/arabic-grammar/git/refs/heads/main",
                            data=data, method="PATCH")
req.add_header("Authorization", f"token {TOKEN}")
req.add_header("Content-Type", "application/json")
try:
    resp = urllib.request.urlopen(req)
    print(f"OK: {json.loads(resp.read())['ref']}")
except Exception as e:
    print(f"FAIL: {e}")
