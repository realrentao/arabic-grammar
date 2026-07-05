#!/usr/bin/env python3
"""Push local repo to GitHub - uses Contents API for initial commit, then Trees API."""

import os
import json
import base64
import urllib.request
import urllib.error
import sys

TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "realrentao"
REPO = "arabic-grammar"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_TREE = 300  # files per tree call - smaller batches are more reliable

def api(method, url, data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Content-Type", "application/json")
    if data is not None:
        req.data = json.dumps(data).encode('utf-8')
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            ct = resp.headers.get('Content-Type', '')
            body = resp.read()
            if 'application/json' in ct:
                result = json.loads(body)
                # Validate the result has a sha for tree responses
                if result and 'sha' in result:
                    return result
                return result
            return body
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if e.code == 422:
            print(f"  ⚠ 422: {body[:100]}")
        elif e.code != 409:
            print(f"  ⚠ {e.code}: {body[:100]}")
        return None

def walk_files():
    files = []
    for root, dirs, fnames in os.walk(REPO_DIR):
        if '.git' in dirs: dirs.remove('.git')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        for fn in sorted(fnames):
            fpath = os.path.join(root, fn)
            rel = os.path.relpath(fpath, REPO_DIR).replace('\\', '/')  # GitHub needs forward slashes
            files.append((rel, fpath))
    return files

def get_or_create_base():
    """Get existing tree SHA from main branch, or create via file upload."""
    # Check if main branch exists
    ref = api("GET", f"https://api.github.com/repos/{USERNAME}/{REPO}/git/ref/heads/main")
    if ref:
        cm = api("GET", ref["object"]["url"])
        if cm and cm.get("tree"):
            return cm["tree"]["sha"], ref["object"]["sha"]
    
    # Try to create initial file (repo might be empty or have a broken first commit)
    try:
        # Check if .gitkeep already exists
        existing = api("GET", f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/.gitkeep")
        if existing and existing.get("sha"):
            # Update it
            payload = {
                "message": "Init",
                "content": base64.b64encode(b"Arabic Grammar Interactive Platform").decode('ascii'),
                "sha": existing["sha"]
            }
            result = api("PUT", f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/.gitkeep", payload)
            if result and "commit" in result:
                cm = api("GET", result["commit"]["url"])
                if cm: return cm["tree"]["sha"], result["commit"]["sha"]
        else:
            # Create new file
            payload = {
                "message": "Initial commit",
                "content": base64.b64encode(b"Arabic Grammar Interactive Platform").decode('ascii')
            }
            result = api("PUT", f"https://api.github.com/repos/{USERNAME}/{REPO}/contents/.gitkeep", payload)
            if result and "commit" in result:
                cm = api("GET", result["commit"]["url"])
                if cm: return cm["tree"]["sha"], result["commit"]["sha"]
    except:
        pass
    
    return None, None

def main():
    print("🚀 Pushing to GitHub via hybrid API method...")
    
    # Ensure repo exists
    repo = api("GET", f"https://api.github.com/repos/{USERNAME}/{REPO}")
    if not repo:
        repo = api("POST", "https://api.github.com/user/repos", {"name": REPO, "private": False})
        if not repo: print("✗ Cannot create repo"); return
    
    print(f"✓ Repo: {repo.get('html_url', '')}")
    
    # Walk files
    all_files = walk_files()
    print(f"✓ {len(all_files)} files")
    
    # Get existing tree from branch or create initial file
    tree_sha, parent_sha = get_or_create_base()
    if not tree_sha:
        print("✗ Cannot get base tree")
        return
    parent = [parent_sha]
    print(f"✓ Base commit: {parent_sha[:10]}")
    
    # Verify base tree exists and has entries
    base_check = api("GET", f"https://api.github.com/repos/{USERNAME}/{REPO}/git/trees/{tree_sha}")
    if not base_check or len(base_check.get('tree', [])) == 0:
        print("  ⚠ Base tree invalid/empty, pushing without base_tree")
        tree_sha = None
    
    # Push files in batches using Trees API
    total = len(all_files)
    batches = (total + MAX_TREE - 1) // MAX_TREE
    
    for b in range(batches):
        start = b * MAX_TREE
        end = min(start + MAX_TREE, total)
        batch = all_files[start:end]
        
        print(f"\n📦 Batch {b+1}/{batches} ({len(batch)} files)...")
        
        entries = []
        for relpath, fpath in batch:
            with open(fpath, 'rb') as f:
                content = f.read()
            try:
                entries.append({"path": relpath, "mode": "100644", "type": "blob",
                               "content": content.decode('utf-8')})
            except:
                entries.append({"path": relpath, "mode": "100644", "type": "blob",
                               "content": content.decode('latin-1')})
        
        tree_payload = {"tree": entries, "base_tree": tree_sha}
        tree = api("POST", f"https://api.github.com/repos/{USERNAME}/{REPO}/git/trees", tree_payload)
        if not tree:
            print(f"  ✗ Failed at batch {b+1} (no response)")
            return
        if 'sha' not in tree:
            print(f"  ✗ Failed at batch {b+1} (no sha in response): {json.dumps(tree)[:100]}")
            return
        if 'tree' in tree and len(tree.get('tree', [])) == 0:
            print(f"  ✗ Batch {b+1} created empty tree!")
            return
        
        tree_sha = tree["sha"]
        print(f"  ✓ Tree: {tree_sha[:10]}")
    
    # Create commit with all changes
    print(f"\n📝 Creating commit...")
    cm = api("POST", f"https://api.github.com/repos/{USERNAME}/{REPO}/git/commits", {
        "message": "Add Arabic grammar interactive learning platform",
        "tree": tree_sha,
        "parents": [parent_sha]
    })
    if not cm: print("✗ Commit failed"); return
    cm_sha = cm["sha"]
    print(f"✓ Commit: {cm_sha[:10]}")
    
    # Update branch
    print(f"🔖 Updating main branch...")
    br = api("PATCH", f"https://api.github.com/repos/{USERNAME}/{REPO}/git/refs/heads/main",
             {"sha": cm_sha, "force": True})
    if br:
        print(f"\n✅ DONE! https://github.com/{USERNAME}/{REPO}")
    else:
        print("✗ Branch update failed")

if __name__ == '__main__':
    main()
