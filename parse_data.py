#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Parse Arabic Grammar markdown into structured JSON data for the web app."""

import re
import json
import os

INPUT_FILE = r"C:/Users/迪丽希斯/OneDrive/Desktop/阿拉伯语语法大全.md"
OUTPUT_FILE = "data/grammar_data.json"
AUDIO_LIST_FILE = "data/audio_items.json"

def extract_arabic(text):
    """Extract Arabic script (Unicode range) from text."""
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]+')
    return arabic_pattern.findall(text)

def parse_stages(lines):
    """Parse markdown into stages and sections."""
    stages = []
    current_stage = None
    current_section = None
    current_subsection = None
    content_buffer = []
    
    # Track current heading levels
    def flush_content():
        nonlocal content_buffer
        if content_buffer:
            text = '\n'.join(content_buffer).strip()
            content_buffer = []
            return text
        return ''
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Stage headers: # 阶段X：...
        if stripped.startswith('# ') and ('阶段' in stripped or '阶段' in stripped):
            # Flush previous
            prev_text = flush_content()
            if current_subsection and prev_text:
                current_subsection['content'] = prev_text
            elif current_section and prev_text:
                current_section['content'] = prev_text
            
            if current_stage:
                if current_section:
                    stages.append(current_stage)
            
            current_stage = {
                'title': stripped.lstrip('# '),
                'sections': [],
                'content': ''
            }
            current_section = None
            current_subsection = None
            
        # Section headers: ## X.X
        elif stripped.startswith('## ') and current_stage:
            prev_text = flush_content()
            if current_subsection and prev_text:
                current_subsection['content'] = prev_text
            elif current_section and prev_text:
                current_section['content'] = prev_text
            
            section_title = stripped.lstrip('## ')
            current_section = {
                'title': section_title,
                'subsections': [],
                'content': ''
            }
            current_stage['sections'].append(current_section)
            current_subsection = None
            
        # Subsection headers: ### X.X.X
        elif stripped.startswith('### ') and current_section:
            prev_text = flush_content()
            if current_subsection and prev_text:
                current_subsection['content'] = prev_text
            elif current_section and prev_text:
                current_section['content'] = prev_text
            
            sub_title = stripped.lstrip('### ')
            current_subsection = {
                'title': sub_title,
                'content': ''
            }
            current_section['subsections'].append(current_subsection)
            
        else:
            if stripped or content_buffer:
                content_buffer.append(line)
    
    # Flush remaining
    prev_text = flush_content()
    if current_subsection and prev_text:
        current_subsection['content'] = prev_text
    elif current_section and prev_text:
        current_section['content'] = prev_text
    
    if current_stage:
        stages.append(current_stage)
    
    return stages

def collect_arabic_items(stages):
    """Collect all Arabic text items from the parsed data for audio generation."""
    items = []
    seen = set()
    item_id = 0
    
    for stage in stages:
        for section in stage.get('sections', []):
            text = section.get('content', '') + section.get('title', '')
            arabic_words = extract_arabic(text)
            for word in arabic_words:
                if word not in seen:
                    seen.add(word)
                    items.append({
                        'id': f"ar_{item_id}",
                        'text': word,
                        'source': f"{stage['title']} > {section['title']}"
                    })
                    item_id += 1
            
            for sub in section.get('subsections', []):
                text = sub.get('content', '') + sub.get('title', '')
                arabic_words = extract_arabic(text)
                for word in arabic_words:
                    if word not in seen:
                        seen.add(word)
                        items.append({
                            'id': f"ar_{item_id}",
                            'text': word,
                            'source': f"{stage['title']} > {section['title']} > {sub['title']}"
                        })
                        item_id += 1
    
    # Also collect stage titles
    for stage in stages:
        arabic_words = extract_arabic(stage['title'])
        for word in arabic_words:
            if word not in seen:
                seen.add(word)
                items.append({
                    'id': f"ar_{item_id}",
                    'text': word,
                    'source': stage['title']
                })
                item_id += 1
    
    return items

def main():
    os.makedirs('data', exist_ok=True)
    
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    stages = parse_stages(lines)
    
    # Save grammar data
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(stages, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Parsed {len(stages)} stages")
    total_sections = sum(len(s.get('sections', [])) for s in stages)
    print(f"✓ Total sections: {total_sections}")
    
    # Collect and save audio items
    audio_items = collect_arabic_items(stages)
    with open(AUDIO_LIST_FILE, 'w', encoding='utf-8') as f:
        json.dump(audio_items, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Collected {len(audio_items)} Arabic text items for audio generation")
    
    # Stats per stage
    for i, stage in enumerate(stages):
        secs = len(stage.get('sections', []))
        subs = sum(len(s.get('subsections', [])) for s in stage.get('sections', []))
        print(f"  Stage {i+1}: {stage['title'][:40]}... - {secs} sections, {subs} subsections")

if __name__ == '__main__':
    main()
