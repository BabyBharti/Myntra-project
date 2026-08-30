import os
import logging
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
else:
    logger.error("GEMINI_API_KEY not found in environment variables.")

def answer_user_question(question: str, context_data: dict) -> str:
    """
    Takes a user's question and answers it based strictly on the provided context_data.
    If the answer cannot be found, it declines to answer.
    """
    if not api_key:
        return "System Error: Gemini API key is not configured."
        
    try:
        # Switch back to gemini-3.5-flash as 1.5-flash is not available for this API key
        model = genai.GenerativeModel('gemini-3.5-flash')
        
        # Convert context data to a formatted string
        context_str = json.dumps(context_data, indent=2)
        
        system_prompt = f"""You are an AI assistant built into the Myntra Wishlist Analytics Dashboard. 
Your role is to answer the user's questions about the scraped Myntra app review data.

CRITICAL INSTRUCTIONS:
1. You MUST answer the user's question based ONLY on the Myntra data provided in the <CONTEXT> section below.
2. DO NOT use your outside knowledge, hallucinate facts, or make up answers. 
3. DO NOT mention competitors like AJIO. You are strictly analyzing Myntra.
4. If the answer to the user's question cannot be found or inferred from the <CONTEXT> data, you MUST reply EXACTLY with: "I'm sorry, but that information is not available in the currently analyzed Myntra data."
5. Be concise, direct, and helpful in your response.

<CONTEXT>
{context_str}
</CONTEXT>
"""
        
        user_prompt = f"User Question: {question}"
        
        logger.info(f"Sending chat question to Gemini: {question}")
        
        response = model.generate_content(
            system_prompt + "\n\n" + user_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1, # Low temperature for strict factual adherence
            )
        )
        
        return response.text.strip()
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error generating chat response: {error_msg}")
        
        # User-friendly message for 429 Quota Exceeded errors
        if "429" in error_msg or "Quota exceeded" in error_msg:
            return "Ah! I've been answering a lot of questions and hit my API quota limit. Please wait about a minute and try asking again!"
            
        return f"Sorry, I encountered an error while trying to process your request: {error_msg}"
