#!/usr/bin/env python3
"""Generate audio for ALL remaining Arabic items not yet cached."""

import asyncio
import edge_tts
import json
import os
import hashlib

AUDIO_DIR = "audio"
DATA_DIR = "data"
ARABIC_VOICE = "ar-SA-ZariyahNeural"

def arabic_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:12]

def get_audio_path(text):
    return os.path.join(AUDIO_DIR, f"ar_{arabic_hash(text)}.mp3")

async def generate_single(text, semaphore):
    async with semaphore:
        out_path = get_audio_path(text)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return {"text": text, "status": "cached"}
        try:
            communicate = edge_tts.Communicate(text, ARABIC_VOICE)
            await communicate.save(out_path)
            return {"text": text, "status": "generated"}
        except Exception as e:
            return {"text": text, "status": f"error: {str(e)}"}

async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    audio_file = os.path.join(DATA_DIR, 'audio_items.json')
    with open(audio_file, 'r', encoding='utf-8') as f:
        all_items = json.load(f)
    
    # Deduplicate by text
    seen = set()
    unique = []
    for item in all_items:
        if item['text'] not in seen:
            seen.add(item['text'])
            unique.append(item)
    
    # Already cached
    cached = 0
    to_generate = []
    for item in unique:
        p = get_audio_path(item['text'])
        if os.path.exists(p) and os.path.getsize(p) > 0:
            cached += 1
        else:
            to_generate.append(item)
    
    print(f"Total unique: {len(unique)}, Already cached: {cached}, To generate: {len(to_generate)}")
    
    if not to_generate:
        print("All audio files already generated!")
        return
    
    # Generate in batches of 60
    batch_size = 60
    concurrency = 3
    semaphore = asyncio.Semaphore(concurrency)
    
    for i in range(0, len(to_generate), batch_size):
        batch = to_generate[i:i+batch_size]
        print(f"\nBatch {i//batch_size + 1}/{(len(to_generate)-1)//batch_size + 1} ({i}-{i+len(batch)})...")
        
        results = await asyncio.gather(*[generate_single(item['text'], semaphore) for item in batch])
        
        gen_count = sum(1 for r in results if r['status'] == 'generated')
        err_count = sum(1 for r in results if 'error' in r['status'])
        if gen_count > 0:
            print(f"  Generated: {gen_count}, Errors: {err_count}")
    
    # Final full regen of audio map
    import subprocess
    subprocess.run(['python', 'gen_audio_map.py'], check=True)
    print(f"\nDone! Audio map updated.")

if __name__ == '__main__':
    asyncio.run(main())
