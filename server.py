#!/usr/bin/env python3
"""HTTP Server for Arabic Grammar Web App - serves static files + on-demand TTS."""

import asyncio
import edge_tts
import hashlib
import json
import os
import re
from http.server import HTTPServer, SimpleHTTPRequestHandler
import socketserver
import urllib.parse

AUDIO_DIR = "audio"
ARABIC_VOICE = "ar-SA-ZariyahNeural"
PORT = 8765

class ArabicGrammarHandler(SimpleHTTPRequestHandler):
    """Custom handler with TTS API endpoint."""
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        # TTS API endpoint
        if path == '/api/tts':
            params = urllib.parse.parse_qs(parsed.query)
            text = params.get('text', [''])[0]
            if not text:
                self.send_error(400, "Missing 'text' parameter")
                return
            self.handle_tts(text)
            return
        
        # Default: serve static files
        super().do_GET()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()
    
    def handle_tts(self, text):
        """Generate TTS audio for Arabic text on demand."""
        text = text.strip()
        # edge-tts handles single Arabic chars fine (reads their letter names)
        
        h = hashlib.md5(text.encode('utf-8')).hexdigest()[:12]
        audio_path = os.path.join(AUDIO_DIR, f"ar_{h}.mp3")
        
        # If already generated, just return the cached file
        if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'max-age=86400')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'cached',
                'path': f'audio/ar_{h}.mp3'
            }).encode('utf-8'))
            return
        
        # Generate new audio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            communicate = edge_tts.Communicate(text, ARABIC_VOICE)
            loop.run_until_complete(communicate.save(audio_path))
            loop.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'generated',
                'path': f'audio/ar_{h}.mp3'
            }).encode('utf-8'))
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'status': 'error',
                'error': str(e)
            }).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Quieter logging."""
        msg = format % args
        if '/api/' in msg or '404' in msg:
            print(f"[Server] {self.address_string()} - {msg}")

def run_server():
    os.makedirs(AUDIO_DIR, exist_ok=True)
    
    # Change to script directory so relative paths work
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    server = HTTPServer(('0.0.0.0', PORT), ArabicGrammarHandler)
    print(f"🕌 Arabic Grammar Server")
    print(f"   Local:   http://localhost:{PORT}")
    print(f"   Press Ctrl+C to stop")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()

if __name__ == '__main__':
    run_server()
