import requests
import xml.etree.ElementTree as ET

rss_url = 'https://itunes.apple.com/in/rss/customerreviews/page=1/id=907394059/sortby=mostrecent/xml'
rss_resp = requests.get(rss_url, timeout=10)

root = ET.fromstring(rss_resp.content)
ns = {'xmlns': 'http://www.w3.org/2005/Atom', 'im': 'http://itunes.apple.com/rss'}
entries = root.findall('xmlns:entry', ns)

print(f"Total entries found: {len(entries)}")

for entry in entries[:2]:
    author_el = entry.find('xmlns:author', ns)
    if author_el is None or author_el.find('xmlns:name', ns) is None:
        print("Skipped author/metadata")
        continue
    
    title_el = entry.find('xmlns:title', ns)
    title = title_el.text if title_el is not None else ""
    
    content_el = entry.find('xmlns:content[@type="text"]', ns)
    if content_el is None:
        content_el = entry.find('xmlns:content', ns)
    content = content_el.text if content_el is not None else ""
    
    rating_el = entry.find('im:rating', ns)
    rating = rating_el.text if rating_el is not None else "0"
    
    id_el = entry.find('xmlns:id', ns)
    review_id = id_el.text if id_el is not None else ""
    
    updated_el = entry.find('xmlns:updated', ns)
    updated = updated_el.text if updated_el is not None else ""
    
    print(f"Title: {title}")
    print(f"Rating: {rating}")
    print(f"Review ID: {review_id}")
    print(f"Updated: {updated}")
    print(f"Content length: {len(content)}")
    print("-" * 20)
