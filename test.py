import youtube_transcript_api
import os
import sys

print("--- 🕵️ DIAGNOSTIC REPORT ---")

# 1. Where is Python running from?
print(f"Python Executable: {sys.executable}")

# 2. Where is the library coming from?
try:
    location = youtube_transcript_api.__file__
    print(f"Library Location: {location}")
except AttributeError:
    print("Library Location: [Unknown - Module has no __file__ attribute]")

# 3. What is inside it?
print(f"Available attributes: {dir(youtube_transcript_api)}")

# 4. Can we find the main class?
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    print("✅ YouTubeTranscriptApi class successfully imported.")
    print(f"Class methods: {dir(YouTubeTranscriptApi)}")
except ImportError as e:
    print(f"❌ Failed to import Main Class: {e}")

print("----------------------------")