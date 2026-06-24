import urllib.request, re, urllib.parse
url = 'https://html.duckduckgo.com/html/?q=' + urllib.parse.quote('ngantuk meme site:pinterest.com')
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
try:
    html = urllib.request.urlopen(req).read().decode('utf-8')
    # Extract titles and target URLs
    # Format in DuckDuckGo HTML: <a class="result__url" href="...">id.pinterest.com...</a>
    # We want the actual destination URLs to Pinterest
    urls = re.findall(r'href=\"(//duckduckgo\.com/l/\?uddg=.*?)\"', html)
    for u in urls[:5]:
        # URL decode the uddg parameter
        decoded = urllib.parse.unquote(u.split('uddg=')[1].split('&')[0])
        print(decoded)
except Exception as e:
    print(e)
