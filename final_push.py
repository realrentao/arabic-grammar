#!/usr/bin/env python3
import urllib.request, json, os, base64

TOKEN = os.environ.get("GITHUB_TOKEN", "")
USER = "realrentao"
REPO = "arabic-grammar"

# Create tree with ALL files in one batch
files_to_add = []
for root, dirs, fnames in os.walk(os.path.dirname(os.path.abspath(__file__))):
    if '.git' in dirs: dirs.remove('.git')
    if '__pycache__' in dirs: dirs.remove('__pycache__')
    for fn in sorted(fnames):
        fpath = os.path.join(root, fn)
        rel = os.path.relpath(fpath, os.path.dirname(os.path.abspath(__file__)))
        rel = rel.replace('\\', '/')
        with open(fpath, 'rb') as f:
            cont = f.read()
        try:
            files_to_add.append({"path": rel, "mode": "100644", "type": "blob", "content": cont.decode('utf-8')})
        except:
                files_to_add.append({"path": rel, "mode": "100644", "type": "blob",
                               "content": cont.decode('latin-1')})

print(f"Total files: {len(files_to_add)}")

def api(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Content-Type", "application/json")
    if data: req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  ERROR {e.code}: {e.read().decode()[:100]}")
        return None

# Check repo exists
repo = api("GET", f"https://api.github.com/repos/{USER}/{REPO}")
if not repo:
    repo = api("POST", "https://api.github.com/user/repos", {"name": REPO, "private": False})
if not repo:
    print("Cannot access repo"); exit(1)

# Create ONE tree with all files
print(f"Creating tree with {len(files_to_add)} entries...")
tree = api("POST", f"https://api.github.com/repos/{USER}/{REPO}/git/trees", {"tree": files_to_add})
if not tree or 'sha' not in tree:
    print("Tree creation failed!"); exit(1)
tree_sha = tree['sha']
print(f"Tree: {tree_sha[:12]}")

# Create commit
print("Creating commit...")
cm = api("POST", f"https://api.github.com/repos/{USER}/{REPO}/git/commits", {
    "message": "Initial: Arabic grammar interactive learning platform",
    "tree": tree_sha, "parents": []
})
if not cm or 'sha' not in cm:
    print("Commit failed!"); exit(1)
cm_sha = cm['sha']
print(f"Commit: {cm_sha[:12]}")

# Create/update branch
print("Setting main branch...")
br = api("POST", f"https://api.github.com/repos/{USER}/{REPO}/git/refs", {
    "ref": "refs/heads/main", "sha": cm_sha
})
if not br:
    # Try PATCH instead
    br = api("PATCH", f"https://api.github.com/repos/{USER}/{REPO}/git/refs/heads/main",
             {"sha": cm_sha, "force": True})

if br:
    print(f"\nDONE! https://github.com/{USER}/{REPO}")

    # Verify
    print("\nVerifying...")
    v = api("GET", f"https://api.github.com/repos/{USER}/{REPO}/git/commits/{cm_sha}")
    if v and 'tree' in v:
        t = api("GET", v['tree']['url'])
        if t:
            root_files = [e['path'] for e in t.get('tree', []) if '/' not in e['path']]
            print(f"Root files: {root_files}")
            print(f"Total entries: {len(t.get('tree', []))}")
else:
    print("Branch update failed!")
