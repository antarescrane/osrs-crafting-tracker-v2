import urllib.request
import json

url = 'https://prices.runescape.wiki/osrs/latest'
req = urllib.request.Request(url, headers={'User-Agent': 'OSDSCraftingTracker/1.0 (contact@example.com)'})

try:
    with urllib.request.urlopen(req) as response:
        raw_data = response.read()
        data = json.loads(raw_data.decode('utf-8'))['data']
        print('API Connected successfully.')
        test_ids = [19547, 33636, 21043, 27681, 27684, 27687]
        for tid in test_ids:
            key = str(tid)
            if key in data:
                price = data[key].get('high', 'N/A')
                print(f'ID {tid}: Found (Price: {price} GP)')
            else:
                print(f'ID {tid}: Missing')
except Exception as e:
    print('API Error:', e)
