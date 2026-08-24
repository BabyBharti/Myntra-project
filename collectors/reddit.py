import os
import re
import logging
from datetime import datetime, timezone
import praw
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Config
SUBREDDITS = ["india", "IndianFashionAddicts", "femalefashionadvice", "shopping", "IndianBeautyDeals"]
QUERIES = ["wishlist", "cart", "size fit", "myntra", "ajio", "nykaa fashion", "purchase regret", "sizing uncertainty"]

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

def collect_reddit_data(max_items=300):
    """
    Collects posts and comments from relevant subreddits.
    Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in .env.
    """
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    user_agent = os.getenv("REDDIT_USER_AGENT")
    
    if not client_id or not client_secret or "here" in client_id.lower() or "here" in client_secret.lower():
        msg = "Reddit API credentials not configured or placeholder detected in .env"
        logger.warning(msg)
        print(f"Skipping Reddit: {msg}")
        return [], msg

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        reddit.read_only = True
        
        all_items = []
        seen_ids = set()
        
        print("Collecting Reddit posts and comments...")
        for sub_name in SUBREDDITS:
            logger.info(f"Searching r/{sub_name}...")
            subreddit = reddit.subreddit(sub_name)
            
            for query in QUERIES:
                if len(all_items) >= max_items:
                    break
                    
                try:
                    submissions = subreddit.search(query, limit=50)
                    for submission in submissions:
                        if len(all_items) >= max_items:
                            break
                            
                        sub_id = submission.id
                        if sub_id not in seen_ids:
                            seen_ids.add(sub_id)
                            
                            combined_text = f"{submission.title}\n{submission.selftext}"
                            if contains_keywords(combined_text):
                                dt = datetime.fromtimestamp(submission.created_utc, tz=timezone.utc)
                                all_items.append({
                                    "id": f"t3_{sub_id}",
                                    "source": "reddit",
                                    "platform": get_platform(combined_text),
                                    "date": dt.isoformat(),
                                    "raw_text": combined_text,
                                    "rating": submission.score,
                                    "url": f"https://www.reddit.com{submission.permalink}"
                                })
                        
                        submission.comment_sort = "top"
                        submission.comments.replace_more(limit=0)
                        for comment in submission.comments[:10]:
                            if len(all_items) >= max_items:
                                break
                            
                            comment_id = comment.id
                            if comment_id not in seen_ids:
                                seen_ids.add(comment_id)
                                
                                comment_text = comment.body
                                if contains_keywords(comment_text):
                                    dt = datetime.fromtimestamp(comment.created_utc, tz=timezone.utc)
                                    all_items.append({
                                        "id": f"t1_{comment_id}",
                                        "source": "reddit",
                                        "platform": get_platform(comment_text),
                                        "date": dt.isoformat(),
                                        "raw_text": comment_text,
                                        "rating": comment.score,
                                        "url": f"https://www.reddit.com{comment.permalink}"
                                    })
                                    
                except Exception as e:
                    logger.error(f"Error searching r/{sub_name} for query '{query}': {e}")
                    continue
                    
        print(f"Finished Reddit: collected {len(all_items)} relevant posts/comments.")
        return all_items, None
        
    except Exception as e:
        error_msg = f"Failed to initialize or connect to Reddit PRAW: {e}"
        logger.error(error_msg)
        return [], error_msg

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data, err = collect_reddit_data()
    print(f"Collected: {len(data)}, Error: {err}")
