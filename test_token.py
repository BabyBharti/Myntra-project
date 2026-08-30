import requests
import re
import urllib.parse

html = requests.get('https://apps.apple.com/in/app/myntra/id907394059').text
print("HTML length:", len(html))

# Try decoding
decoded = urllib.parse.unquote(html)

# Pattern 1: token="ey..."
p1 = re.search(r'"token"\s*:\s*"(ey[^"]+)"', decoded)
if p1:
    print("Found p1:", p1.group(1)[:20])
else:
    print("p1 not found")

# Pattern 2: token%22%3A%22ey...
p2 = re.search(r'token%22%3A%22(ey.+?)%22', html)
if p2:
    print("Found p2:", p2.group(1)[:20])
else:
    print("p2 not found")
    
# Pattern 3: general eyJ...
p3 = re.findall(r'(eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+)', decoded)
if p3:
    print("Found p3. Count:", len(p3))
    print(p3[0][:30])
else:
    print("p3 not found")
