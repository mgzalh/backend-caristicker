import requests, json, urllib.parse, re
url = 'https://id.pinterest.com/search/pins/?q=' + urllib.parse.quote('ngantuk meme')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
resp = requests.get(url, headers=headers)
match = re.search(r'<script id=\"__PWS_DATA__\" type=\"application/json\">(.*?)</script>', resp.text, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    print("Found JSON, keys:", data.keys())
    # Save JSON to file
    with open('pws_data.json', 'w') as f:
        json.dump(data, f)
else:
    print("No PWS_DATA found")
