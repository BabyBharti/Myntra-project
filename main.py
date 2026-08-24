import os
import pandas as pd
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("main_pipeline")

def main():
    print("=" * 60)
    print("Fashion E-Commerce Wishlist Behavior Data Collection Pipeline")
    print("=" * 60)

    # 1. Play Store
    play_store_data = []
    play_store_status = "Not run"
    try:
        from collectors.play_store import collect_play_store_reviews
        print("\n--- Running Google Play Store Collector ---")
        play_store_data = collect_play_store_reviews(max_reviews_per_app=150)
        play_store_status = f"Success ({len(play_store_data)} items)"
    except ImportError as e:
        play_store_status = f"Failed (Dependency missing: {e})"
        print(f"\n[Warning] Play Store collector skipped: {play_store_status}")
    except Exception as e:
        play_store_status = f"Failed (Error: {e})"
        print(f"\n[Error] Play Store collector failed: {play_store_status}")

    # 2. App Store
    app_store_data = []
    app_store_status = "Not run"
    try:
        from collectors.app_store import collect_app_store_reviews
        print("\n--- Running Apple App Store Collector ---")
        app_store_data = collect_app_store_reviews(max_reviews_per_app=150)
        app_store_status = f"Success ({len(app_store_data)} items)"
    except ImportError as e:
        app_store_status = f"Failed (Dependency missing: {e})"
        print(f"\n[Warning] App Store collector skipped: {app_store_status}")
    except Exception as e:
        app_store_status = f"Failed (Error: {e})"
        print(f"\n[Error] App Store collector failed: {app_store_status}")

    # 3. Reddit
    reddit_data = []
    reddit_status = "Ignored"
    print("\n[Info] Reddit collector skipped (Ignored by user request).")

    # 4. YouTube
    youtube_data = []
    youtube_status = "Ignored"
    print("\n[Info] YouTube collector skipped (Ignored by user request).")

    # 5. Merge and Save
    print("\n" + "=" * 60)
    print("Merging Datasets")
    print("=" * 60)

    all_records = play_store_data + app_store_data + reddit_data + youtube_data
    
    summary_stats = {
        "play_store": {
            "status": play_store_status,
            "count": len(play_store_data)
        },
        "app_store": {
            "status": app_store_status,
            "count": len(app_store_data)
        },
        "reddit": {
            "status": reddit_status,
            "count": len(reddit_data)
        },
        "youtube": {
            "status": youtube_status,
            "count": len(youtube_data)
        }
    }

    if not all_records:
        print("\n[Warning] No records collected from any source. Output dataset was not created.")
        print("\nSource Collection Summary:")
        for source, info in summary_stats.items():
            print(f"- {source}: {info['status']}")
        return

    df = pd.DataFrame(all_records)
    columns_order = ["id", "source", "platform", "date", "raw_text", "rating", "url"]
    df = df.reindex(columns=columns_order)

    output_filename = "fashion_wishlist_behavior.csv"
    try:
        df.to_csv(output_filename, index=False, encoding="utf-8")
        # Also output JSON for the dashboard
        json_filename = "fashion_wishlist_behavior.json"
        df.to_json(json_filename, orient="records")
        print(f"\nSuccess! Merged dataset saved to: {os.path.abspath(output_filename)} and {json_filename}")
    except Exception as e:
        print(f"\n[Error] Failed to write files: {e}")

    # 6. Report
    print("\n" + "=" * 60)
    print("Collection Summary Report")
    print("=" * 60)
    
    print("\nItems Collected per Source:")
    for source, info in summary_stats.items():
        print(f"- {source.replace('_', ' ').title()}: {info['count']} items (Status: {info['status']})")
        
    print(f"\nTotal Items Collected: {len(df)}")
    
    if "platform" in df.columns:
        print("\nBreakdown by Platform:")
        platform_counts = df["platform"].value_counts()
        for plat, count in platform_counts.items():
            print(f"- {plat.title()}: {count} items")

    print("\n" + "=" * 60)
    print("Dataset Sample (First 5 Rows)")
    print("=" * 60)
    print(df.head(5).to_string(columns=["id", "source", "platform", "rating", "url"], max_colwidth=30))
    print("\nSample Raw Text snippets:")
    for idx, row in df.head(5).iterrows():
        snippet = str(row['raw_text']).replace('\n', ' ')
        if len(snippet) > 85:
            snippet = snippet[:82] + "..."
        print(f"{idx+1}. [{row['source']}/{row['platform']}] {snippet}")
        
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
