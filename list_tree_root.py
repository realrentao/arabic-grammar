#!/usr/bin/env python3
import json

with open('data/tree_check.json', encoding='utf-8') as f:
    d = json.load(f)

tree = d.get('tree', [])
print(f'Total entries in tree: {len(tree)}')
print(f'\nRoot-level entries (no "/" in path):')
for t in tree:
    if '/' not in t['path']:
        print(f'  {t["path"]} ({t["type"]})')

audio_count = sum(1 for t in tree if t['path'].startswith('audio/'))
data_count = sum(1 for t in tree if t['path'].startswith('data/'))
print(f'\nAudio files: {audio_count}')
print(f'Data files: {data_count}')
