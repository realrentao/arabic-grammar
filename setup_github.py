#!/usr/bin/env python3
"""Create GitHub repo and push the project."""

import os
import subprocess
import urllib.request
import json

TOKEN = os.environ.get("GITHUB_TOKEN", "")
USERNAME = "realrentao"
REPO_NAME = "arabic-grammar"
REPO_DIR = os.path.dirname(os.path.abspath(__file__))

def create_repo():
    """Create GitHub repo via API."""
    url = "https://api.github.com/user/repos"
    data = json.dumps({
        "name": REPO_NAME,
        "description": "阿拉伯语语法大全交互式自学平台 - Arabic Grammar Interactive Learning Platform",
        "private": False,
        "auto_init": False
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header("Authorization", f"token {TOKEN}")
    req.add_header("Content-Type", "application/json")
    
    try:
        resp = urllib.request.urlopen(req)
        result = json.loads(resp.read())
        print(f"✓ Repo created: {result['html_url']}")
        return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        if "already exists" in body:
            print(f"✓ Repo already exists: https://github.com/{USERNAME}/{REPO_NAME}")
            return True
        print(f"✗ Failed to create repo: {body}")
        return False

def push_repo():
    """Add remote, commit, and push."""
    os.chdir(REPO_DIR)
    
    # Remove existing .gitignore and re-add only necessary ones
    gitignore = """*.pyc
__pycache__/
.DS_Store
Thumbs.db
.vscode/
.idea/
"""
    with open('.gitignore', 'w') as f:
        f.write(gitignore)
    
    # Add all files
    subprocess.run(['git', 'add', '-A'], check=True)
    
    # Commit
    result = subprocess.run(['git', 'commit', '-m', 'Initial commit: Arabic grammar interactive learning platform'], 
                          capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0 and "nothing to commit" not in result.stderr:
        print(result.stderr.strip())
    
    # Set remote
    remote_url = f"https://{USERNAME}:{TOKEN}@github.com/{USERNAME}/{REPO_NAME}.git"
    subprocess.run(['git', 'remote', 'remove', 'origin'], capture_output=True)
    subprocess.run(['git', 'remote', 'add', 'origin', remote_url], check=True)
    
    # Push
    print("Pushing to GitHub... (this may take a while for audio files)")
    result = subprocess.run(['git', 'push', '-u', 'origin', 'master'], 
                          capture_output=True, text=True, timeout=300)
    print(result.stdout.strip())
    if result.returncode != 0:
        # Try main branch
        print("Trying 'main' branch...")
        subprocess.run(['git', 'branch', '-M', 'main'], check=True)
        result = subprocess.run(['git', 'push', '-u', 'origin', 'main'], 
                              capture_output=True, text=True, timeout=300)
        print(result.stdout.strip())
        if result.returncode != 0:
            print(f"Push error: {result.stderr.strip()}")
            return False
    
    print(f"\n✓ Success! https://github.com/{USERNAME}/{REPO_NAME}")
    return True

def main():
    print("🚀 Setting up GitHub repo for Arabic Grammar project...")
    print(f"   Local path: {REPO_DIR}")
    
    if create_repo():
        push_repo()

if __name__ == '__main__':
    main()
