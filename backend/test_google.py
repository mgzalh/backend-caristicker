import requests, re, json
url = 'https://www.google.com/search?tbm=isch&q=ngantuk+meme+site:pinterest.com'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp = requests.get(url, headers=headers)
matches = re.findall(r"\[\"(https://i\.pinimg\.com/.*?\.jpg)\",\d+,\d+\]", resp.text)
for m in list(set(matches))[:5]:
    print(m)
