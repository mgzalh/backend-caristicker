import requests, re, json, urllib.parse
url = 'https://yandex.com/images/search?text=' + urllib.parse.quote('ngantuk meme pinterest')
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
resp = requests.get(url, headers=headers)
matches = re.findall(r'\"img_href\":\"(.*?)\"', resp.text)
for m in matches[:5]:
    print(m)
