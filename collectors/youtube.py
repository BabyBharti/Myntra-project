import os
import re
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Config
QUERIES = [
    "Myntra haul",
    "Ajio shopping haul",
    "Nykaa Fashion try on haul",
    "online fashion shopping cart wishlist",
    "why I did not buy fashion cart",
    "fashion wishlist review",
    "Indian fashion shopping regret"
]

KEYWORDS = [
    r"\bwishlist\w*",
    r"\bsave\b", r"\bsaved\b", r"\bsaving\b",
    r"\bcart\w*",
    r"\bsize\w*", r"\bfit\w*", r"\bsizing\b",
    r"\bprice\w*", r"\bcost\w*", r"\bcheap\w*", r"\bexpensive\w*",
    r"\bbuy\b", r"\bbought\b", r"\bpurchase\w*", r"\bdecision\w*",
    r"\bregret\w*", r"\bhesitat\w*"
]

KEYWORD_RE = re.compile("|".join(KEYWORDS), re.IGNORECASE)

def contains_keywords(text):
    if not text:
        return False
    return bool(KEYWORD_RE.search(text))

def get_platform(text):
    text_lower = text.lower()
    if "myntra" in text_lower:
        return "myntra"
    elif "ajio" in text_lower:
        return "ajio"
    elif "nykaa" in text_lower:
        return "nykaa"
    else:
        return "general"

def collect_youtube_comments(max_items=300):
    """
    Collects YouTube comments from relevant videos.
    Requires YOUTUBE_API_KEY in .env.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")
    
    if not api_key or "here" in api_key.lower():
        msg = "YouTube API key not configured or placeholder detected in .env"
        logger.warning(msg)
        print(f"Skipping YouTube: {msg}")
        return [], msg
        
    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        
        all_comments = []
        seen_comment_ids = set()
        video_ids = set()
        
        print("Searching for relevant YouTube videos...")
        for query in QUERIES:
            if len(all_comments) >= max_items:
                break
                
            try:
                search_response = youtube.search().list(
                    q=query,
                    part="id,snippet",
                    maxResults=15,
                    type="video",
                    regionCode="IN",
                    relevanceLanguage="en"
                ).execute()
                
                for item in search_response.get("items", []):
                    video_id = item.get("id", {}).get("videoId")
                    if video_id:
                        video_ids.add(video_id)
            except HttpError as e:
                logger.error(f"YouTube search error for query '{query}': {e}")
                if e.resp.status in [400, 403]:
                    return [], f"YouTube API Error: {e.reason}"
                continue
                
        print(f"Found {len(video_ids)} videos to fetch comments from.")
        
        for video_id in video_ids:
            if len(all_comments) >= max_items:
                break
                
            try:
                comment_response = youtube.commentThreads().list(
                    part="id,snippet",
                    videoId=video_id,
                    maxResults=100,
                    textFormat="plainText"
                ).execute()
                
                for thread in comment_response.get("items", []):
                    if len(all_comments) >= max_items:
                        break
                        
                    top_comment = thread.get("snippet", {}).get("topLevelComment", {})
                    comment_id = top_comment.get("id")
                    
                    if comment_id and comment_id not in seen_comment_ids:
                        seen_comment_ids.add(comment_id)
                        snippet = top_comment.get("snippet", {})
                        raw_text = snippet.get("textOriginal", "")
                        
                        if contains_keywords(raw_text):
                            published_at = snippet.get("publishedAt")
                            like_count = snippet.get("likeCount", 0)
                            
                            all_comments.append({
                                "id": comment_id,
                                "source": "youtube",
                                "platform": get_platform(raw_text),
                                "date": published_at,
                                "raw_text": raw_text,
                                "rating": like_count,
                                "url": f"https://www.youtube.com/watch?v={video_id}&lc={comment_id}"
                            })
                            
            except HttpError as e:
                logger.debug(f"Could not retrieve comments for video {video_id}: {e}")
                continue
                
        print(f"Finished YouTube: collected {len(all_comments)} relevant comments.")
        return all_comments, None
        
    except Exception as e:
        error_msg = f"Failed to connect to YouTube Data API: {e}"
        logger.error(error_msg)
        return [], error_msg

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data, err = collect_youtube_comments()
    print(f"Collected: {len(data)}, Error: {err}")
