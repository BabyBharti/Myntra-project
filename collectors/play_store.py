import re
import logging
from datetime import datetime
import requests
from google_play_scraper import reviews, Sort

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

def search_and_collect_play_store(app_query, max_reviews=300):
    """
    Dynamically searches the Google Play Store for the app name,
    finds the app ID, and collects filtered reviews.
    """
    all_filtered_reviews = []
    
    try:
        # Search for the app manually since google_play_scraper search is broken
        logger.info(f"Searching Google Play Store for '{app_query}'...")
        html = requests.get(f"https://play.google.com/store/search?q={app_query}&c=apps", timeout=10).text
        ids = re.findall(r'href="/store/apps/details\?id=([^&"]+)"', html)
        
        if not ids:
            logger.warning(f"No Google Play Store apps found matching '{app_query}'")
            return []
            
        app_id = ids[0]
        app_title = app_query.capitalize()
        
        logger.info(f"Found Play Store app: {app_title} (ID: {app_id})")
        
        collected = 0
        all_unfiltered_reviews = []
        continuation_token = None
        iteration = 0
        max_iterations = 20
        
        while collected < max_reviews and iteration < max_iterations:
            iteration += 1
            try:
                result, continuation_token = reviews(
                    app_id,
                    lang='en',
                    country='in',
                    sort=Sort.NEWEST,
                    count=1000,
                    continuation_token=continuation_token
                )
                
                if not result:
                    break
                
                for rev in result:
                    raw_text = rev.get("content", "")
                    
                    review_id = rev.get("reviewId")
                    dt = rev.get("at")
                    date_str = dt.isoformat() if isinstance(dt, datetime) else str(dt)
                    
                    # Also keep unfiltered as fallback
                    all_unfiltered_reviews.append({
                        "id": review_id,
                        "source": "play_store",
                        "platform": app_title,
                        "date": date_str,
                        "raw_text": raw_text,
                        "rating": rev.get("score"),
                        "url": f"https://play.google.com/store/apps/details?id={app_id}&reviewId={review_id}"
                    })
                    
                    if contains_keywords(raw_text):
                        all_filtered_reviews.append({
                            "id": review_id,
                            "source": "play_store",
                            "platform": app_title,
                            "date": date_str,
                            "raw_text": raw_text,
                            "rating": rev.get("score"),
                            "url": f"https://play.google.com/store/apps/details?id={app_id}&reviewId={review_id}"
                        })
                        collected += 1
                        
                    if collected >= max_reviews:
                        break
                            
                if not continuation_token:
                    break
                    
            except Exception as e:
                logger.error(f"Error scraping Play Store reviews for {app_id}: {e}")
                break
                
        if collected == 0 and len(all_unfiltered_reviews) > 0:
            logger.info("No reviews matched keywords. Falling back to 50 most recent reviews.")
            return all_unfiltered_reviews[:50]
            
        logger.info(f"Finished Play Store: collected {collected} relevant reviews for {app_title}.")
        
    except Exception as e:
        logger.error(f"Google Play Store dynamic search/scraping failed: {e}")
        
    return all_filtered_reviews

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    data = search_and_collect_play_store("Myntra", max_reviews=10)
    print(f"Total collected: {len(data)}")
