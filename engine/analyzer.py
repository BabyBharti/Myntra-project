import re
import collections

# Regex Patterns for Themes
THEME_PATTERNS = {
    "Wishlist / Save": r"\bwishlist\b|\bwish list\b|\bsave for later\b|\bsaved item\b|\bfavorite\b|\bfavourited\b|\bbookmark\b|\bshortlist\b|\badd to wishlist\b",
    "Purchase decision": r"\bdidn't buy\b|\bhaven't bought\b|\bstill thinking\b|\bnot sure\b|\bunsure\b|\bhesitant\b|\bhesitate\b|\bsecond thoughts\b|\bstill deciding\b|\bdecide\b|\bdecision\b|\bwaiting to buy\b|\bthinking about buying\b|\bwill buy later\b|\bplanning to buy\b",
    "Fit / Size": r"\bsize\b|\bfit\b|\bsizing\b|\btrue to size\b|\bruns small\b|\bruns large\b|\bsize chart\b|\bsize guide\b|\btoo tight\b|\btoo loose\b|\bsize doubt\b",
    "Price / Timing": r"\bprice\b|\bexpensive\b|\bcheap\b|\bdiscount\b|\bsale\b|\boffer\b|\bwait for sale\b|\bprice drop\b|\btoo costly\b|\bbudget\b|\bafford\b",
    "Quality / Trust": r"\bquality\b|\bfabric\b|\bmaterial\b|\breview\b|\breviews\b|\brating\b|\btrust\b|\bdoubt\b|\bworried\b|\brisky\b|\breturn\b|\breturned\b|\bexchange\b|\brefund\b",
    "Styling / Occasion": r"\bstyling\b|\bstyle\b|\bpair with\b|\boccasion\b|\boutfit\b|\bwear it with\b|\bmatch\b|\bversatile\b|\beveryday wear\b",
    "Regret / Abandonment": r"\bforgot\b|\bregret\b|\bmissed out\b|\bout of stock\b|\bsold out\b|\bno longer available\b|\bchanged my mind\b|\bdon't need it anymore\b",
    "Comparison / Alternatives": r"\bcomparing\b|\bcompare\b|\balternative\b|\bsimilar\b|\bother options\b|\bbetter option\b|\bcheaper elsewhere\b|\bfound better\b",
    "Social Validation": r"\bfriend said\b|\bopinion\b|\bask\b|\brecommend\b|\bsuggested\b|\blooks good on\b|\bcomments\b"
}

# Regex Patterns for Barriers (maps to an opportunity)
BARRIER_PATTERNS = {
    "Price uncertainty": (r"\bexpensive\b|\btoo costly\b|\bbudget\b|\bafford\b|\bcannot afford\b", "Show price history or competitor comparison"),
    "Waiting for sale": (r"\bdiscount\b|\bsale\b|\boffer\b|\bwait for sale\b|\bprice drop\b", "Price drop alerts & customized discounts"),
    "Fit uncertainty": (r"\bsize\b|\bfit\b|\bsizing\b|\btrue to size\b|\bruns small\b|\bruns large\b|\bsize chart\b|\bsize doubt\b", "Improve sizing charts & add AR try-on"),
    "Quality uncertainty": (r"\bquality\b|\bfabric\b|\bmaterial\b|\btrust\b|\bdoubt\b|\bworried\b|\brisky\b", "Highlight verified purchase reviews & fabric details"),
    "Returns/exchange concern": (r"\breturn\b|\breturned\b|\bexchange\b|\brefund\b|\bpolicy\b", "Clearer return policies & easy-return badge"),
    "Product unavailable": (r"\bout of stock\b|\bsold out\b|\bno longer available\b", "Restock notification & similar item suggestions"),
    "Comparing alternatives": (r"\bcomparing\b|\bcompare\b|\balternative\b|\bsimilar\b|\bbetter option\b|\bcheaper elsewhere\b", "Side-by-side product comparison feature"),
    "Need for social validation": (r"\bfriend\b|\bopinion\b|\bask\b|\blooks good\b", "Show 'X people bought this' or styling community"),
    "Purchase postponement": (r"\bstill thinking\b|\bnot sure\b|\bunsure\b|\bhesitant\b|\bstill deciding\b", "Limited-time cart reservation"),
    "Lack of product information": (r"\binformation\b|\bdetails\b|\bdescription\b", "Add video reviews & detailed material specs")
}

# Intent Patterns
INTENT_PATTERNS = {
    "High": r"\bwill buy\b|\bplanning to buy\b|\bsaved\b|\bwishlist\b|\bwait for sale\b|\blove\b|\bperfect\b",
    "Medium": r"\bstill thinking\b|\bnot sure\b|\bunsure\b|\bhesitant\b|\bcomparing\b|\bdecide\b",
    "Low": r"\bdidn't buy\b|\babandoned\b|\bdeleted\b|\bterrible\b|\bregret\b|\bworst\b|\bbad\b"
}

# Behavior Patterns
BEHAVIOR_PATTERNS = {
    "Saved item": r"\bwishlist\b|\bsave\b|\bbookmark\b|\bfavorite\b",
    "Delayed purchase": r"\bwait\b|\bthinking\b|\bplanning\b",
    "Compared alternatives": r"\bcompare\b|\balternative\b",
    "Abandoned purchase": r"\babandoned\b|\bforgot\b|\bchanged my mind\b",
    "Purchased": r"\bbought\b|\bpurchased\b|\border\b",
    "Returned/exchanged": r"\breturn\b|\bexchange\b"
}

def analyze_review(text, rating):
    text_lower = str(text).lower()
    
    # 1. Theme
    matched_themes = []
    for theme, pattern in THEME_PATTERNS.items():
        if re.search(pattern, text_lower):
            matched_themes.append(theme)
    theme = matched_themes[0] if matched_themes else "Other"
    
    # 2. User Barrier & Opportunity
    barrier = "None"
    opportunity = "None"
    for b_name, (pattern, opp) in BARRIER_PATTERNS.items():
        if re.search(pattern, text_lower):
            barrier = b_name
            opportunity = opp
            break  # Pick primary barrier
            
    # 3. User Behavior
    behavior = "Unknown"
    for b_name, pattern in BEHAVIOR_PATTERNS.items():
        if re.search(pattern, text_lower):
            behavior = b_name
            break
            
    # 4. Purchase Intent
    intent = "Unknown"
    for i_name, pattern in INTENT_PATTERNS.items():
        if re.search(pattern, text_lower):
            intent = i_name
            break
            
    # If no regex matched but rating is very low, infer low intent
    if intent == "Unknown":
        if rating <= 2:
            intent = "Low"
        elif rating >= 4:
            intent = "High"
            
    return {
        "theme": theme,
        "barrier": barrier,
        "behavior": behavior,
        "intent": intent,
        "opportunity": opportunity,
        "rating": rating
    }

def calculate_opportunity_score(frequency, intent_mix, avg_rating, wishlist_relevance):
    """
    Calculates a transparent opportunity score based on:
    - frequency: raw count of occurrences
    - intent_mix: list of intents for this barrier
    - avg_rating: average rating of reviews with this barrier
    - wishlist_relevance: float representing % of reviews that also hit a wishlist/decision theme
    """
    intent_weights = {"High": 3, "Medium": 2, "Unknown": 1, "Low": 0.5}
    avg_intent_weight = sum(intent_weights.get(i, 1) for i in intent_mix) / max(len(intent_mix), 1)
    
    severity = 1
    if avg_rating <= 2.5:
        severity = 2
    elif avg_rating <= 3.5:
        severity = 1.5
        
    relevance_multiplier = 1 + wishlist_relevance  # Between 1.0 and 2.0
    
    score = frequency * avg_intent_weight * severity * relevance_multiplier
    return round(score, 1)

def analyze_dataset(reviews):
    """
    Processes a list of raw review dictionaries, enriches them,
    and calculates aggregate discovery insights.
    """
    enriched_reviews = []
    
    # Aggregates
    theme_dist = collections.Counter()
    barrier_dist = collections.Counter()
    intent_dist = collections.Counter()
    
    # Data for opportunity scoring
    barrier_data = collections.defaultdict(lambda: {"intents": [], "ratings": [], "wishlist_hits": 0, "opportunity": ""})
    
    for r in reviews:
        raw_text = r.get("raw_text", "")
        rating = r.get("rating", 3)
        analysis = analyze_review(raw_text, rating)
        
        # Merge analysis back into review object
        r["ai_analysis"] = analysis
        enriched_reviews.append(r)
        
        # Update aggregates
        theme_dist[analysis["theme"]] += 1
        intent_dist[analysis["intent"]] += 1
        
        if analysis["barrier"] != "None":
            barrier_dist[analysis["barrier"]] += 1
            bd = barrier_data[analysis["barrier"]]
            bd["intents"].append(analysis["intent"])
            bd["ratings"].append(rating)
            bd["opportunity"] = analysis["opportunity"]
            if analysis["theme"] in ["Wishlist / Save", "Purchase decision"]:
                bd["wishlist_hits"] += 1

    # Calculate Opportunity Rankings
    opportunities = []
    for b_name, bd in barrier_data.items():
        freq = len(bd["intents"])
        avg_rating = sum(bd["ratings"]) / freq
        wishlist_relevance = bd["wishlist_hits"] / freq
        
        score = calculate_opportunity_score(freq, bd["intents"], avg_rating, wishlist_relevance)
        opportunities.append({
            "barrier": b_name,
            "opportunity": bd["opportunity"],
            "score": score,
            "frequency": freq,
            "avg_rating": round(avg_rating, 1)
        })
        
    # Sort opportunities by score descending
    opportunities.sort(key=lambda x: x["score"], reverse=True)
    
    insights = {
        "total_analyzed": len(reviews),
        "theme_distribution": dict(theme_dist),
        "barrier_distribution": dict(barrier_dist),
        "intent_distribution": dict(intent_dist),
        "top_opportunities": opportunities
    }
    
    return enriched_reviews, insights
