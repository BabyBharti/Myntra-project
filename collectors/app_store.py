import re
import requests
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

KEYWORDS = [
    # Core wishlist/save
    r"\bwishlist\b", r"\bwish list\b", r"\bsave for later\b", r"\bsaved item\b", r"\bfavorite\b", r"\bfavourited\b", r"\bbookmark\b", r"\bshortlist\b", r"\badd to wishlist\b",
    # Purchase-decision
    r"\bdidn't buy\b", r"\bhaven't bought\b", r"\bstill thinking\b", r"\bnot sure\b", r"\bunsure\b", r"\bhesitant\b", r"\bhesitate\b", r"\bsecond thoughts\b", r"\bstill deciding\b", r"\bdecide\b", r"\bdecision\b", r"\bwaiting to buy\b", r"\bthinking about buying\b", r"\bwill buy later\b", r"\bplanning to buy\b",
    # Fit/size
    r"\bsize\b", r"\bfit\b", r"\bsizing\b", r"\btrue to size\b", r"\bruns small\b", r"\bruns large\b", r"\bsize chart\b", r"\bsize guide\b", r"\btoo tight\b", r"\btoo loose\b", r"\bsize doubt\b",
    # Price/timing
    r"\bprice\b", r"\bexpensive\b", r"\bcheap\b", r"\bdiscount\b", r"\bsale\b", r"\boffer\b", r"\bwait for sale\b", r"\bprice drop\b", r"\btoo costly\b", r"\bbudget\b", r"\bafford\b",
    # Quality/trust
    r"\bquality\b", r"\bfabric\b", r"\bmaterial\b", r"\breview\b", r"\breviews\b", r"\brating\b", r"\btrust\b", r"\bdoubt\b", r"\bworried\b", r"\brisky\b", r"\breturn\b", r"\breturned\b", r"\bexchange\b", r"\brefund\b",
    # Styling/occasion
    r"\bstyling\b", r"\bstyle\b", r"\bpair with\b", r"\boccasion\b", r"\boutfit\b", r"\bwear it with\b", r"\bmatch\b", r"\bversatile\b", r"\beveryday wear\b",
    # Regret / abandonment
    r"\bforgot\b", r"\bregret\b", r"\bmissed out\b", r"\bout of stock\b", r"\bsold out\b", r"\bno longer available\b", r"\bchanged my mind\b", r"\bdon't need it anymore\b",
    # Comparison / alternatives
    r"\bcomparing\b", r"\bcompare\b", r"\balternative\b", r"\bsimilar\b", r"\bother options\b", r"\bbetter option\b", r"\bcheaper elsewhere\b", r"\bfound better\b",
    # Social validation
    r"\bfriend said\b", r"\bopinion\b", r"\bask\b", r"\brecommend\b", r"\bsuggested\b", r"\blooks good on\b", r"\bcomments\b"
]

KEYWORD_RE = re.compile("|".join(KEYWORDS), re.IGNORECASE)

def contains_keywords(text):
    if not text:
        return False
    return bool(KEYWORD_RE.search(text))

def search_and_collect_app_store(app_query, max_reviews=300):
    """
    Dynamically searches the Apple App Store for the app name,
    finds the app ID, and collects filtered reviews using the official iTunes RSS feed.
    This bypasses third-party scrapers and avoids dependency issues.
    """
    all_filtered_reviews = []
    all_unfiltered_reviews = []
    
    try:
        # Step 1: Search for the app ID
        logger.info(f"Searching Apple App Store for '{app_query}'...")
        search_url = f"https://itunes.apple.com/search?term={app_query}&entity=software&country=in&limit=1"
        response = requests.get(search_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        if not data.get("results") or len(data["results"]) == 0:
            logger.warning(f"No Apple App Store apps found matching '{app_query}'")
            return []
            
        top_app = data["results"][0]
        app_id = top_app.get("trackId")
        app_name = top_app.get("trackName", app_query)
        
        logger.info(f"Found App Store app: {app_name} (ID: {app_id})")
        
        # Step 2: Fetch reviews from iTunes RSS feed
        # We can try fetching multiple pages (1 to 10)
        collected = 0
        
        for page in range(1, 11):
            if collected >= max_reviews:
                break
                
            rss_url = f"https://itunes.apple.com/in/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
            rss_resp = requests.get(rss_url, timeout=10)
            
            if rss_resp.status_code != 200:
                break
                
            rss_data = rss_resp.json()
            feed = rss_data.get("feed", {})
            entries = feed.get("entry", [])
            
            # If no entries or only the app metadata entry, stop
            if not entries or (isinstance(entries, list) and len(entries) <= 1 and page > 1):
                break
                
            # iTunes RSS sometimes returns a single dict instead of list if there's only 1 review
            if isinstance(entries, dict):
                entries = [entries]
                
            for entry in entries:
                # Skip the first entry on page 1 if it's the app metadata itself (usually doesn't have author)
                if not entry.get("author"):
                    continue
                    
                title = entry.get("title", {}).get("label", "")
                content = entry.get("content", {}).get("label", "")
                combined_text = f"{title}\n{content}" if title else content
                
                rating = entry.get("im:rating", {}).get("label", "0")
                review_id = entry.get("id", {}).get("label", "")
                
                # Try to parse date, fallback to current iso format if not present
                date_str = ""
                updated = entry.get("updated", {}).get("label")
                if updated:
                    date_str = updated
                else:
                    date_str = datetime.utcnow().isoformat()
                
                # Also keep unfiltered as fallback
                all_unfiltered_reviews.append({
                    "id": review_id or f"as_{hash(combined_text)}",
                    "source": "app_store",
                    "platform": app_name,
                    "date": date_str,
                    "raw_text": combined_text,
                    "rating": int(rating),
                    "url": top_app.get("trackViewUrl", "")
                })
                    
                if contains_keywords(combined_text):
                    all_filtered_reviews.append({
                        "id": review_id or f"as_{hash(combined_text)}",
                        "source": "app_store",
                        "platform": app_name,
                        "date": date_str,
                        "raw_text": combined_text,
                        "rating": int(rating),
                        "url": top_app.get("trackViewUrl", "")
                    })
                    collected += 1
                    
                    if collected >= max_reviews:
                        break
                        
        if collected == 0 and len(all_unfiltered_reviews) > 0:
            logger.info("No reviews matched keywords. Falling back to 50 most recent reviews.")
            return all_unfiltered_reviews[:50]
            
        logger.info(f"Finished App Store: collected {collected} relevant reviews for {app_name}.")
        
    except Exception as e:
        logger.error(f"Apple App Store dynamic search/scraping failed: {e}")
        
    return all_filtered_reviews

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = search_and_collect_app_store("Myntra", max_reviews=10)
    print(f"Total collected: {len(data)}")
