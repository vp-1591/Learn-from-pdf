from youtube_transcript_api import YouTubeTranscriptApi
import re

def extract_video_id(url):
    regex = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(regex, url)
    if match:
        return match.group(1)
    return None

def get_youtube_transcript(video_url):
    video_id = extract_video_id(video_url)
    if not video_id:
        print("Invalid Video ID")
        return None
        
    try:
        ytt = YouTubeTranscriptApi()
        transcript = ytt.fetch(video_id, languages=['en', 'en-US', 'en-GB'])
        
        text_list = []
        for entry in transcript:
            if hasattr(entry, 'text'):
                text_list.append(entry.text)
            else:
                text_list.append(entry.get('text', ''))
                
        return " ".join(text_list)
        
    except Exception as e:
        print(f"Error: {e}")
        return None

url = "https://youtu.be/nTOVIGsqCuY?si=HgPAR8UhddC24pB0"
print(f"Testing URL: {url}")
transcript = get_youtube_transcript(url)
if transcript:
    print("Success! Transcript length:", len(transcript))
    print("Preview:", transcript[:100])
else:
    print("Failed to fetch transcript.")
