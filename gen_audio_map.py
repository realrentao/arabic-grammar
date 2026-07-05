#!/usr/bin/env python3
"""Generate audio map JSON - mapping Arabic text to audio file paths,
and a hash-to-path map for JS fallback lookup."""

import json
import os
import hashlib
import re

AUDIO_DIR = "audio"
DATA_DIR = "data"

def arabic_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:12]

def extract_arabic(text):
    pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
    return pattern.findall(text)

def scan_arabic_in_data(obj):
    """Recursively scan data for Arabic text. Returns dict of {text: hash_path}."""
    items = {}
    hash_map = {}
    
    def _scan(o):
        if isinstance(o, dict):
            for v in o.values(): _scan(v)
        elif isinstance(o, list):
            for v in o: _scan(v)
        elif isinstance(o, str):
            for word in extract_arabic(o):
                h = arabic_hash(word)
                audio_file = os.path.join(AUDIO_DIR, f"ar_{h}.mp3")
                if os.path.exists(audio_file):
                    path = f"audio/ar_{h}.mp3"
                    items[word] = path
                    hash_map[h] = path
    
    _scan(obj)
    return items, hash_map

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    
    with open(os.path.join(DATA_DIR, 'grammar_data.json'), 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    audio_map, hash_map = scan_arabic_in_data(data)
    
    # Save text-to-path map
    with open(os.path.join(DATA_DIR, 'audio_map.json'), 'w', encoding='utf-8') as f:
        json.dump({"text": audio_map, "hash": hash_map}, f, ensure_ascii=False)
    
    print(f"Audio map: {len(audio_map)} text items, {len(hash_map)} hash items")

if __name__ == '__main__':
    main()
