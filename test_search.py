import requests
import re
def get_app_id(query):
    html = requests.get(f'https://play.google.com/store/search?q={query}&c=apps').text
    ids = re.findall(r'href="/store/apps/details\?id=([^&"]+)"', html)
    # Filter out duplicates and keep order
    seen = set()
    result = []
    for app_id in ids:
        if app_id not in seen:
            seen.add(app_id)
            result.append(app_id)
    return result

print("Found Myntra:", get_app_id("Myntra"))
print("Found Ajio:", get_app_id("Ajio"))
print("Found Nykaa:", get_app_id("Nykaa"))
