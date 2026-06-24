import requests, re
url = 'https://id.pinterest.com/search/pins/?q=ngantuk'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
resp = requests.get(url, headers=headers)
matches = set(re.findall(r'https://i\.pinimg\.com/.*?\.jpg', resp.text))
for m in list(matches)[:10]:
    print(m)
