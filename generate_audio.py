#!/usr/bin/env python3
"""Generate edge-tts audio for key Arabic text items used in the web app."""

import asyncio
import edge_tts
import json
import os
import hashlib
import sys

AUDIO_DIR = "audio"
DATA_DIR = "data"

# Use standard modern Arabic voice (Saudi Arabia, female)
ARABIC_VOICE = "ar-SA-ZariyahNeural"

def arabic_hash(text):
    """Generate a consistent filename hash for Arabic text."""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:12]

def get_audio_path(text):
    """Get audio file path for a given Arabic text."""
    h = arabic_hash(text)
    return os.path.join(AUDIO_DIR, f"ar_{h}.mp3")

async def generate_audio(text, voice=ARABIC_VOICE, rate="+0%", pitch="+0Hz"):
    """Generate audio for a single Arabic text using edge-tts."""
    out_path = get_audio_path(text)
    
    if os.path.exists(out_path):
        return {"text": text, "path": out_path, "status": "cached"}
    
    try:
        communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await communicate.save(out_path)
        return {"text": text, "path": out_path, "status": "generated"}
    except Exception as e:
        return {"text": text, "path": None, "status": f"error: {str(e)}"}

async def batch_generate(items, concurrency=3):
    """Generate audio for a list of items with controlled concurrency."""
    semaphore = asyncio.Semaphore(concurrency)
    
    async def process(item):
        async with semaphore:
            result = await generate_audio(item['text'])
            if result['status'] == 'generated':
                print(f"  Generated: {item['text'][:30]}...")
            elif result['status'] == 'cached':
                pass  # Skip cached in output
            else:
                print(f"  ERROR: {result['status']} - {item['text'][:30]}...")
            return result
    
    tasks = [process(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results

def prioritize_items(audio_items):
    """Filter and prioritize important Arabic text items."""
    # Priority criteria:
    # 1. Short items (2-5 chars) - likely words, not sentences
    # 2. Items with source containing key sections
    # 3. Items that appear in tables
        
    # Remove duplicates by text
    seen = set()
    unique_items = []
    for item in audio_items:
        if item['text'] not in seen:
            seen.add(item['text'])
            unique_items.append(item)
    
    # Score priority
    def priority_score(item):
        text = item['text']
        source = item.get('source', '')
        score = 0
        
        # Shorter texts are more likely to be useful vocabulary items
        if 1 <= len(text) <= 10:
            score += 10
        elif len(text) <= 20:
            score += 5
        elif len(text) <= 40:
            score -= 5
        
        # Items from stage 1 (phonetics) and key grammar sections
        if '语音' in source or '发音' in source:
            score += 20
        if '字母' in source:
            score += 15
        
        # Items from noun/verb sections (vocabulary dense)
        if '名词' in source or '动词' in source:
            score += 5
        
        # Items from tables (example words)
        if '例' in source:
            score += 8
        
        return score
    
    # Sort by priority (highest first)
    sorted_items = sorted(unique_items, key=priority_score, reverse=True)
    
    # Take top 300 items (or all if less)
    limit = min(300, len(sorted_items))
    return sorted_items[:limit]

async def main():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # Read audio items
    audio_file = os.path.join(DATA_DIR, 'audio_items.json')
    if not os.path.exists(audio_file):
        print("No audio_items.json found. Run parse_data.py first.")
        return
    
    with open(audio_file, 'r', encoding='utf-8') as f:
        all_items = json.load(f)
    
    print(f"Total unique Arabic text items: {len(all_items)}")
    
    # Prioritize items
    items = prioritize_items(all_items)
    print(f"Selected top {len(items)} items for audio generation")
    
    # Count already cached
    cached = 0
    for item in items:
        if os.path.exists(get_audio_path(item['text'])):
            cached += 1
    print(f"Already cached: {cached}")
    
    to_generate = len(items) - cached
    if to_generate == 0:
        print("All audio files already generated!")
        return
    
    print(f"Generating {to_generate} audio files (concurrency=3)...")
    
    # Batch generate
    results = await batch_generate(items)
    
    generated = sum(1 for r in results if r['status'] == 'generated')
    cached_count = sum(1 for r in results if r['status'] == 'cached')
    errors = sum(1 for r in results if 'error' in r['status'])
    
    print(f"\nDone! Generated: {generated}, Cached: {cached_count}, Errors: {errors}")

if __name__ == '__main__':
    asyncio.run(main())
