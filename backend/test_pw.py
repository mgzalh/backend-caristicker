import requests, re
resp = requests.post('https://lite.duckduckgo.com/lite/', headers={'User-Agent': 'Mozilla/5.0'}, data={'q': 'ngantuk meme site:pinterest.com'})
if resp.status_code == 200:
    matches = re.findall(r'href=\"(.*?pinterest\.com.*?)\"', resp.text)
    print('Found links:', len(matches))
    print(matches[:5])
else:
    print('Failed', resp.status_code)
