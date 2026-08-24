from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from collectors.play_store import search_and_collect_play_store
from collectors.app_store import search_and_collect_app_store

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/')
def index():
    return jsonify({"status": "online", "message": "Myntra Dashboard API is running."})

@app.route('/api/scrape', methods=['POST'])
def scrape():
    data = request.json
    app_query = data.get('app_name', '').strip()
    
    if not app_query:
        return jsonify({"error": "App name is required"}), 400
        
    logging.info(f"Received scrape request for app: {app_query}")
    
    try:
        # Scrape Play Store
        play_store_data = search_and_collect_play_store(app_query, max_reviews=150)
        
        # Scrape App Store
        app_store_data = search_and_collect_app_store(app_query, max_reviews=150)
        
        # Combine
        combined_data = play_store_data + app_store_data
        
        return jsonify({
            "status": "success",
            "app_query": app_query,
            "total_collected": len(combined_data),
            "sources": {
                "play_store_count": len(play_store_data),
                "app_store_count": len(app_store_data)
            },
            "data": combined_data
        })
        
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run the Flask app on port 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
