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
        print(f"  {e.code}: {e.read().decode()[:100]}")
        return None

# Tree SHA from the successful creation
tree_sha = "a1681ed2722fcc8da1d8cccae5b6404a96e500ba"

# Create commit with this tree
cm = api("POST", "https://api.github.com/repos/realrentao/arabic-grammar/git/commits", {
    "message": "Arabic grammar interactive learning platform",
    "tree": tree_sha,
    "parents": []
})

if not cm:
    print("Commit failed!")
    exit(1)

print(f"Commit: {cm['sha'][:16]}")

# Force update branch
br = api("PATCH", "https://api.github.com/repos/realrentao/arabic-grammar/git/refs/heads/main",
         {"sha": cm["sha"], "force": True})

if br:
    print(f"Branch updated!")
    print(f"https://github.com/realrentao/arabic-grammar")
else:
    print("Branch update failed, trying POST...")
    br = api("POST", "https://api.github.com/repos/realrentao/arabic-grammar/git/refs",
             {"ref": "refs/heads/main", "sha": cm["sha"]})
    if br:
        print(f"Branch created!")
    else:
        print("Still failed")
