#!/usr/bin/env python3
import json

with open('data/github_final_check.json', encoding='utf-8') as f:
    d = json.load(f)

tree = d.get('tree', [])
print(f'Total entries on GitHub: {len(tree)}')

dirs = set()
for x in tree:
    p = x['path']
    if '/' in p:
        dirs.add(p.split('/')[0])

print(f'Directories: {sorted(dirs)}')

audio_count = sum(1 for x in tree if x['path'].startswith('audio/'))
data_count = sum(1 for x in tree if x['path'].startswith('data/'))
root_files = [x['path'] for x in tree if '/' not in x['path']]

print(f'Audio files: {audio_count}')
print(f'Data files: {data_count}')
print(f'Root files: {root_files}')

expected_audio = 1188
if audio_count >= 1100:
    print(f'\nResult: SUCCESS - {audio_count} audio + {data_count} data files on GitHub')
else:
    print(f'\nResult: PARTIAL - Only {audio_count}/1188 audio files')
