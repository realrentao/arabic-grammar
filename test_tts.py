#!/usr/bin/env python3
import asyncio
import edge_tts

async def test():
    voices = await edge_tts.list_voices()
    arabic_voices = [v for v in voices if 'ar-' in v.get('ShortName', '')]
    print(f"Found {len(arabic_voices)} Arabic voices:")
    for v in arabic_voices:
        print(f"  {v['ShortName']}: {v['FriendlyName']} - {v['Locale']}")
    
    if not arabic_voices:
        print("No Arabic voices found. Listing first 10 voices:")
        for v in voices[:10]:
            print(f"  {v['ShortName']}: {v['FriendlyName']} - {v['Locale']}")

asyncio.run(test())
