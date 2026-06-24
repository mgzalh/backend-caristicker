import requests, re, json
url = 'https://images.search.yahoo.com/search/images;?p=ngantuk+meme+site:pinterest.com'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
resp = requests.get(url, headers=headers)
# In Yahoo, image data is usually in a JSON blob near the end or in <li> tags
matches = re.findall(r'imgurl=(.*?)&amp;', resp.text)
for m in matches[:5]:
    import urllib.parse
    print(urllib.parse.unquote(m))
