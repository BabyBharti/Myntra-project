import os
import json
import logging
import google.generativeai as genai
from typing import List, Dict, Any
from dotenv import load_dotenv
from dataclasses import dataclass, field

# Load environment variables
load_dotenv()

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logging.warning("GEMINI_API_KEY not found in environment variables. LLM analysis will fail.")

@dataclass
class Opportunity:
    opportunity_name: str
    description: str
    estimated_frequency: int

@dataclass
class BatchAnalysis:
    q1_wishlist_reasons: str = ""
    q2_purchase_preventions: str = ""
    q3_remaining_uncertainties: str = ""
    q4_postponement_causes: str = ""
    q5_comparison_methods: str = ""
    q6_outside_info_sought: str = ""
    q7_role_of_factors: str = ""
    q8_genuine_intent_vs_bookmarking: str = ""
    q9_segment_differences: str = ""
    q10_unmet_needs: str = ""
    identified_opportunities: List[Opportunity] = field(default_factory=list)
    
    def model_dump_json(self, indent=4):
        # Convert to dict then to json
        d = self.__dict__.copy()
        d['identified_opportunities'] = [o.__dict__ for o in self.identified_opportunities]
        return json.dumps(d, indent=indent)

def parse_llm_response(text: str) -> BatchAnalysis:
    # Clean up markdown code blocks if any
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse JSON: {e}\nText: {text}")
        return BatchAnalysis() # Return empty on failure
        
    opps_raw = data.get("identified_opportunities", [])
    opps = []
    for o in opps_raw:
        opps.append(Opportunity(
            opportunity_name=o.get("opportunity_name", "Unknown"),
            description=o.get("description", ""),
            estimated_frequency=o.get("estimated_frequency", 1)
        ))
        
    return BatchAnalysis(
        q1_wishlist_reasons=data.get("q1_wishlist_reasons", ""),
        q2_purchase_preventions=data.get("q2_purchase_preventions", ""),
        q3_remaining_uncertainties=data.get("q3_remaining_uncertainties", ""),
        q4_postponement_causes=data.get("q4_postponement_causes", ""),
        q5_comparison_methods=data.get("q5_comparison_methods", ""),
        q6_outside_info_sought=data.get("q6_outside_info_sought", ""),
        q7_role_of_factors=data.get("q7_role_of_factors", ""),
        q8_genuine_intent_vs_bookmarking=data.get("q8_genuine_intent_vs_bookmarking", ""),
        q9_segment_differences=data.get("q9_segment_differences", ""),
        q10_unmet_needs=data.get("q10_unmet_needs", ""),
        identified_opportunities=opps
    )

def analyze_reviews_batch(reviews_batch: List[Dict]) -> BatchAnalysis:
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing.")
        
    model = genai.GenerativeModel("gemini-3.5-flash")
    
    reviews_text = ""
    for idx, r in enumerate(reviews_batch):
        rating = r.get("rating", "N/A")
        text = r.get("raw_text", "")
        reviews_text += f"Review {idx+1} (Rating: {rating}): {text}\n"

    prompt = f"""
    You are an expert UX Researcher and Product Analyst for Myntra.
    Analyze the following batch of Myntra user reviews and feedback.

    Your goal is to answer 10 specific questions about user behavior on Myntra, going beyond simple sentiment analysis.
    Do NOT mention competitors like AJIO. Your analysis must strictly be about Myntra.
    You must identify, quantify where possible (using estimated_frequency), and compare potential opportunity areas.
    
    Reviews Batch:
    {reviews_text}
    
    You MUST output valid JSON only. Do not include any other text.
    The JSON structure MUST exactly match this format:
    {{
        "q1_wishlist_reasons": "String answering the question.",
        "q2_purchase_preventions": "...",
        "q3_remaining_uncertainties": "...",
        "q4_postponement_causes": "...",
        "q5_comparison_methods": "...",
        "q6_outside_info_sought": "...",
        "q7_role_of_factors": "...",
        "q8_genuine_intent_vs_bookmarking": "...",
        "q9_segment_differences": "...",
        "q10_unmet_needs": "...",
        "identified_opportunities": [
            {{
                "opportunity_name": "Name of opportunity",
                "description": "Detailed explanation",
                "estimated_frequency": 5
            }}
        ]
    }}
    If there is insufficient data for a question, just put "Insufficient data in this batch to determine."
    """

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        return parse_llm_response(response.text)
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        raise

def synthesize_insights(batch_results: List[BatchAnalysis]) -> BatchAnalysis:
    if not api_key:
        raise ValueError("GEMINI_API_KEY is missing.")
        
    model = genai.GenerativeModel("gemini-3.5-flash")
    
    combined_text = "Here are the insights extracted from multiple batches of user feedback. Synthesize them into a single comprehensive report:\n\n"
    for idx, batch in enumerate(batch_results):
        combined_text += f"--- BATCH {idx+1} ---\n"
        combined_text += batch.model_dump_json() + "\n\n"
        
    prompt = f"""
    You are an expert UX Researcher and Product Analyst.
    I have processed thousands of user reviews in batches and extracted insights for 10 core questions, along with potential product opportunities.
    
    Your task is to synthesize these batch insights into one single, coherent, and highly detailed final report.
    Combine the answers for the 10 questions. Where the batches mention similar opportunities, merge them and SUM their estimated_frequency.
    
    You MUST output valid JSON only. Do not include any other text.
    The JSON structure MUST exactly match this format:
    {{
        "q1_wishlist_reasons": "Synthesized string.",
        "q2_purchase_preventions": "...",
        "q3_remaining_uncertainties": "...",
        "q4_postponement_causes": "...",
        "q5_comparison_methods": "...",
        "q6_outside_info_sought": "...",
        "q7_role_of_factors": "...",
        "q8_genuine_intent_vs_bookmarking": "...",
        "q9_segment_differences": "...",
        "q10_unmet_needs": "...",
        "identified_opportunities": [
            {{
                "opportunity_name": "Synthesized Name",
                "description": "Combined explanation",
                "estimated_frequency": 25
            }}
        ]
    }}
    """
    
    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        return parse_llm_response(response.text)
    except Exception as e:
        logging.error(f"Error calling Gemini API for synthesis: {e}")
        raise
