import json
import logging
from engine.llm_analyzer import analyze_reviews_batch, synthesize_insights

def load_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def chunk_data(data, chunk_size=50):
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]

def generate_markdown_report(report_data, filename="discovery_report.md"):
    md_content = f"# AI Discovery Engine Report\n\n"
    md_content += f"## User Behavior Insights\n\n"
    md_content += f"**Q1. Why do users add fashion products to their wishlist?**\n{report_data.q1_wishlist_reasons}\n\n"
    md_content += f"**Q2. What prevents wishlisted products from eventually being purchased?**\n{report_data.q2_purchase_preventions}\n\n"
    md_content += f"**Q3. What uncertainties remain after users have identified a product they like?**\n{report_data.q3_remaining_uncertainties}\n\n"
    md_content += f"**Q4. What causes users to postpone a purchase?**\n{report_data.q4_postponement_causes}\n\n"
    md_content += f"**Q5. How do users compare multiple shortlisted products?**\n{report_data.q5_comparison_methods}\n\n"
    md_content += f"**Q6. What information do users seek outside Myntra before purchasing?**\n{report_data.q6_outside_info_sought}\n\n"
    md_content += f"**Q7. What role do fit, size, styling, price, reviews, occasion and social validation play?**\n{report_data.q7_role_of_factors}\n\n"
    md_content += f"**Q8. When do users use the wishlist as genuine purchase intent versus simply as a bookmarking mechanism?**\n{report_data.q8_genuine_intent_vs_bookmarking}\n\n"
    md_content += f"**Q9. How do these behaviors differ across user segments?**\n{report_data.q9_segment_differences}\n\n"
    md_content += f"**Q10. What unmet needs emerge consistently across user conversations?**\n{report_data.q10_unmet_needs}\n\n"
    
    md_content += f"## Top Identified Opportunities\n\n"
    # Sort opportunities by estimated frequency descending
    sorted_opps = sorted(report_data.identified_opportunities, key=lambda x: x.estimated_frequency, reverse=True)
    
    for idx, opp in enumerate(sorted_opps):
        md_content += f"### {idx+1}. {opp.opportunity_name} (Frequency: {opp.estimated_frequency})\n"
        md_content += f"{opp.description}\n\n"

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(md_content)
    logging.info(f"Markdown report generated: {filename}")

def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        data = load_data('fashion_wishlist_behavior.json')
    except Exception as e:
        logging.error(f"Error loading data: {e}")
        return
        
    total_reviews = len(data)
    logging.info(f"Total reviews to analyze: {total_reviews}")
    
    if total_reviews == 0:
        logging.warning("No data to analyze.")
        return

    # To save tokens and time during test, we'll take a subset or just chunk everything
    # Let's say we analyze up to 300 reviews max for cost efficiency in testing
    max_reviews_to_analyze = 300
    if total_reviews > max_reviews_to_analyze:
        logging.info(f"Capping analysis at {max_reviews_to_analyze} reviews for performance.")
        data = data[:max_reviews_to_analyze]
        
    chunks = list(chunk_data(data, chunk_size=50))
    logging.info(f"Data chunked into {len(chunks)} batches of ~50 reviews each.")
    
    batch_analyses = []
    
    for i, chunk in enumerate(chunks):
        logging.info(f"Analyzing batch {i+1}/{len(chunks)}...")
        try:
            batch_result = analyze_reviews_batch(chunk)
            batch_analyses.append(batch_result)
        except Exception as e:
            logging.error(f"Failed to analyze batch {i+1}: {e}")
            continue

    if not batch_analyses:
        logging.error("All batches failed to analyze. Exiting.")
        return
        
    logging.info("Synthesizing batch results into final report...")
    try:
        final_report = synthesize_insights(batch_analyses)
    except Exception as e:
        logging.error(f"Failed to synthesize insights: {e}")
        return
        
    # Write JSON output
    with open('discovery_analysis_llm.json', 'w', encoding='utf-8') as f:
        f.write(final_report.model_dump_json(indent=4))
        
    # Generate Markdown Report
    generate_markdown_report(final_report)
    logging.info("Analysis complete!")
    
if __name__ == "__main__":
    main()
