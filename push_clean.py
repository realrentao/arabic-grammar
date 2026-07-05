#!/usr/bin/env python3
"""Push clean - creates initial .gitkeep, then builds tree and commit fresh."""
import urllib.request, json, os, base64, hashlib

TOKEN = os.environ.get("GITHUB_TOKEN", "")
BASE = os.path.dirname(os.path.abspath(__file__))

def api(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Content-Type", "application/json")
    if data: req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        print(f"  {e.code}: {e.read().decode()[:100]}")
        return None

# Step 1: Ensure repo exists
repo = api("GET", "https://api.github.com/repos/realrentao/arabic-grammar")
if not repo:
    repo = api("POST", "https://api.github.com/user/repos", {"name": "arabic-grammar", "private": False})
if not repo:
    print("Repo access failed"); exit(1)
print(f"Repo: {repo.get('html_url', '')}")

# Step 2: Create .gitkeep via Contents API to initialize the repo
init = api("PUT", "https://api.github.com/repos/realrentao/arabic-grammar/contents/.gitkeep", {
    "message": "init",
    "content": base64.b64encode(b"Arabic Grammar").decode('ascii')
})
if not init:
    # Maybe .gitkeep already exists - try updating
    existing = api("GET", "https://api.github.com/repos/realrentao/arabic-grammar/contents/.gitkeep")
    if existing and existing.get("sha"):
        init = api("PUT", "https://api.github.com/repos/realrentao/arabic-grammar/contents/.gitkeep", {
            "message": "init", "sha": existing["sha"],
            "content": base64.b64encode(b"Arabic Grammar").decode('ascii')
        })
if not init:
    print("Cannot init repo"); exit(1)
print(f"Init commit: {init['commit']['sha'][:12]}")

# Step 3: Create a BIG tree with all files
files = []
for root, dirs, fnames in os.walk(BASE):
    if '.git' in dirs: dirs.remove('.git')
    if '__pycache__' in dirs: dirs.remove('__pycache__')
    for fn in sorted(fnames):
        fpath = os.path.join(root, fn)
        rel = os.path.relpath(fpath, BASE).replace('\\', '/')
        with open(fpath, 'rb') as f:
            cont = f.read()
        try:
            # Text files: send as UTF-8
            files.append({"path": rel, "mode": "100644", "type": "blob", "content": cont.decode('utf-8')})
        except UnicodeDecodeError:
            # Binary files (MP3): send raw bytes decoded as latin-1
            # GitHub Tree API will base64-encode the content string to store it
            # DO NOT base64-encode ourselves — that would double-encode!
            files.append({"path": rel, "mode": "100644", "type": "blob",
                         "content": cont.decode('latin-1')})

print(f"Files to push: {len(files)}")

# Push files in batches of 300
BATCH = 300
base_tree = None

for i in range(0, len(files), BATCH):
    batch = files[i:i+BATCH]
    batch_num = i//BATCH + 1
    total_batches = (len(files)+BATCH-1)//BATCH
    print(f"Batch {batch_num}/{total_batches} ({len(batch)} files)...")
    
    tree_payload = {"tree": batch}
    if base_tree:
        tree_payload["base_tree"] = base_tree
    
    tree = api("POST", "https://api.github.com/repos/realrentao/arabic-grammar/git/trees", tree_payload)
    if not tree or 'sha' not in tree:
        print(f"  Tree creation failed for batch {batch_num}!")
        exit(1)
    base_tree = tree["sha"]
    print(f"  Tree: {base_tree[:12]}")

# Step 4: Create commit (orphan - no parents)
print("Creating commit...")
cm = api("POST", "https://api.github.com/repos/realrentao/arabic-grammar/git/commits", {
    "message": "Arabic grammar interactive learning platform",
    "tree": base_tree,
    "parents": []  # orphan commit - no parent
})
if not cm or 'sha' not in cm:
    print("Commit failed!"); exit(1)
cm_sha = cm['sha']
print(f"Commit: {cm_sha[:12]}")

# Step 5: Force update main branch
print("Updating main branch...")
br = api("PATCH", "https://api.github.com/repos/realrentao/arabic-grammar/git/refs/heads/main",
         {"sha": cm_sha, "force": True})
if not br:
    # Create ref if doesn't exist
    br = api("POST", "https://api.github.com/repos/realrentao/arabic-grammar/git/refs",
             {"ref": "refs/heads/main", "sha": cm_sha})
if br:
    print(f"\nSUCCESS! https://github.com/realrentao/arabic-grammar")
    
    # Verify
    v = api("GET", f"https://api.github.com/repos/realrentao/arabic-grammar/git/commits/{cm_sha}")
    if v and 'tree' in v:
        vt = api("GET", v['tree']['url'])
        if vt:
            total = len(vt.get('tree', []))
            print(f"Verified: {total} entries in tree")
else:
    print("Branch update failed!")
