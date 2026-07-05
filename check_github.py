#!/usr/bin/env python3
"""Check what's on GitHub after push."""
import json

with open('D:/workbuddy工作区/2026-07-05-14-54-31/arabic-grammar/data/github_tree_check.json') as f:
    d = json.load(f)

tree = d.get('tree', [])
print(f'Total entries on GitHub: {len(tree)}')
dirs = set()
for t in tree:
    p = t['path']
    if '/' in p:
        dname = p.split('/')[0]
        dirs.add(dname)
    else:
        print(f'  /{p}')

print(f'\nDirectories: {sorted(dirs)}')

# Count audio files
audio_count = sum(1 for t in tree if t['path'].startswith('audio/'))
print(f'Audio files: {audio_count}')
