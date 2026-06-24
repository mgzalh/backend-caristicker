import requests, re, json, urllib.parse

def test_bing():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7'
    })
    
    # Get cookies
    session.get('https://www.bing.com/?cc=id', timeout=10)
    
    # Now search
    encoded = urllib.parse.quote_plus('ngantuk meme pinterest')
    url = f"https://www.bing.com/images/search?q={encoded}&form=HDRSC2&first=1"
    
    resp = session.get(url, timeout=10)
    matches = re.findall(r'm=\"({.*?})\"', resp.text)
    
    for m in matches[:5]:
        try:
            clean_json = m.replace('&quot;', '"')
            data = json.loads(clean_json)
            print(data.get('t'), '-', data.get('murl'))
        except Exception as e:
            pass

test_bing()
